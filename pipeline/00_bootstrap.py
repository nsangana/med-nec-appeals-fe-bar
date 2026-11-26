# Databricks notebook source
# MAGIC %md
# MAGIC # 00_bootstrap — FE Bar appeals: one-time, idempotent foundation
# MAGIC
# MAGIC Stands up the reference + grounding objects the generation stages depend on, in the `catalog`.`schema`
# MAGIC job parameters (live default `appeals_hackathon_catalog`.`fe_bar_appeals`):
# MAGIC - `denial_strategy` (CARC routing reference)
# MAGIC - `med_nec_criteria` (ai_parse_document over the 2 public criteria PDFs, CDF on) + VS Delta Sync index
# MAGIC - `mpfs_indicator_descriptors` (ai_parse_document -> ai_query extraction from the public Noridian PDF;
# MAGIC   there is no curated CSV in this build)
# MAGIC - UC SQL functions for the chatbot (`get_appeal`, `get_encounter`, `mpfs_lookup`, `descriptor_lookup`)
# MAGIC
# MAGIC **Idempotent.** Expensive AI steps are skipped when the target table already has rows.
# MAGIC A UC SQL function cannot be created until its source table exists (verified), so functions whose source
# MAGIC is produced by a later stage (`get_appeal` <- `appeals_output`, `get_encounter` <- `encounter_grounding`,
# MAGIC `mpfs_lookup` <- `mpfs_indicator_listing`) are created only when that source exists; otherwise they are logged
# MAGIC as DEFERRED and created on the next run.
# MAGIC
# MAGIC Source files (public references, already in `raw_references`): `BCBS_Med_Nec_Criteria.pdf`,
# MAGIC `Definition_of_Med_Nec.pdf`, `MPFS_Indicator_Descriptors_-_JE_Part_B_-_Noridian.pdf`, `2025_MPFS_Indicator_Listing.xlsx`.

# COMMAND ----------
import re


def _param(name, default):
    """Job base_parameters / widgets with a local default for interactive runs."""
    try:
        dbutils.widgets.text(name, default)  # noqa: F821 (provided by the Databricks runtime)
        return dbutils.widgets.get(name)  # noqa: F821
    except NameError:
        return default


CATALOG_DEFAULT = "appeals_hackathon_catalog"  # live value; the job passes the bundle target's catalog
SCHEMA_DEFAULT = "fe_bar_appeals"  # live value; the job passes the bundle target's schema
CATALOG = _param("catalog", CATALOG_DEFAULT).strip()
SCHEMA = _param("schema", SCHEMA_DEFAULT).strip()
for _name, _val in (("catalog", CATALOG), ("schema", SCHEMA)):
    # Object names (tables, views, functions, volumes, paths) are built from these two values only.
    # Plain identifiers only: no quotes, dots, spaces or SQL, so nothing user-supplied reaches SQL text.
    if not re.fullmatch(r"[A-Za-z0-9_]+", _val):
        raise ValueError(f"{_name} must be a plain identifier, got {_val!r}")
FQ = f"{CATALOG}.{SCHEMA}"
RAW = f"/Volumes/{CATALOG}/{SCHEMA}/raw_references"
VS_ENDPOINT = "appeals-vs-endpoint"
VS_INDEX = f"{FQ}.med_nec_criteria_index"
EMBED_MODEL = "databricks-gte-large-en"
EXTRACT_MODEL = "databricks-claude-sonnet-4-6"


def table_exists(name):
    return spark.catalog.tableExists(name)


def row_count(name):
    return spark.table(name).count() if table_exists(name) else 0


report = {}

# COMMAND ----------
# MAGIC %md ## 1. Schema + volumes

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {FQ} COMMENT 'FE Bar medical-necessity appeals (synthetic demo).'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {FQ}.raw_references COMMENT 'Public reference documents for grounding.'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {FQ}.appeal_pdfs COMMENT 'Rendered appeal letter + decision worksheet PDFs.'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {FQ}.landing COMMENT 'Raw generator JSON landed for Auto Loader.'")

# COMMAND ----------
# MAGIC %md ## 2. denial_strategy (CARC routing reference, static)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {FQ}.denial_strategy
COMMENT 'Denial-code routing + reason reference (X12 CARC, CO group). Drives deterministic batch routing.'
AS SELECT * FROM VALUES
 ('CO50','50','CO','These are non-covered services because this is not deemed a medical necessity by the payer.','medical_necessity','payer (BCBS else CMS)','Documentation supports that the service was proper and needed for diagnosis/treatment of the condition.'),
 ('CO55','55','CO','Procedure/treatment/drug is deemed experimental/investigational by the payer.','med_nec_experimental','payer (BCBS else CMS)','Service is FDA-approved / accepted standard of care with sufficient evidence, not investigational-setting-only.'),
 ('CO57','57','CO','Payment denied/reduced because the payer deems the information does not support this level of service, this many services, this length of service, this dosage, or this days supply.','level_of_service','payer (BCBS else CMS)','Clinical acuity/severity justifies the level, number, or duration of services billed.'),
 ('CO150','150','CO','Payer deems the information submitted does not support this level of service.','level_of_service','payer (BCBS else CMS)','Documented complexity and clinical findings support the level of service billed.'),
 ('CO186','186','CO','Level of care adjustment.','level_of_care','payer (BCBS else CMS)','The billed level of care was medically justified for the documented condition.')
 AS t(denial_code, carc_number, adjustment_grp, reason_text, category, criteria_filter, what_to_prove)
""")
report["denial_strategy"] = row_count(f"{FQ}.denial_strategy")

# COMMAND ----------
# MAGIC %md ## 3. med_nec_criteria — ai_parse_document over the 2 criteria PDFs (skipped if populated)

# COMMAND ----------

if row_count(f"{FQ}.med_nec_criteria") == 0:
    spark.sql(f"""
    CREATE OR REPLACE TABLE {FQ}.med_nec_criteria AS
    WITH pdfs AS (
      SELECT CASE WHEN path ILIKE '%BCBS%' THEN 'BCBS' ELSE 'CMS' END AS payer_type,
             regexp_extract(path,'([^/]+)$',1) AS source_file,
             ai_parse_document(content, map('version','2.0')) AS doc
      FROM read_files('{RAW}/', format => 'binaryFile')
      WHERE path ILIKE '%Med_Nec%'
    )
    SELECT md5(concat(source_file, ':', cast(elem_idx AS STRING))) AS chunk_id,
           payer_type, source_file,
           elem:content::STRING AS chunk_to_retrieve, elem:content::STRING AS chunk_to_embed
    FROM pdfs
    LATERAL VIEW posexplode(variant_get(doc,'$.document.elements','ARRAY<VARIANT>')) t AS elem_idx, elem
    WHERE length(trim(elem:content::STRING)) > 0
    """)
    spark.sql(f"ALTER TABLE {FQ}.med_nec_criteria SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    print("med_nec_criteria: built")
else:
    print("med_nec_criteria: already populated, skipped")
report["med_nec_criteria_chunks"] = row_count(f"{FQ}.med_nec_criteria")

# COMMAND ----------
# MAGIC %md ## 4. Vector Search Delta Sync index over med_nec_criteria

# COMMAND ----------

import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.vectorsearch import (
    DeltaSyncVectorIndexSpecRequest, EmbeddingSourceColumn, PipelineType, VectorIndexType,
)

w = WorkspaceClient()
try:
    w.vector_search_indexes.get_index(index_name=VS_INDEX)
    print("VS index exists:", VS_INDEX)
except NotFound:
    w.vector_search_indexes.create_index(
        name=VS_INDEX,
        endpoint_name=VS_ENDPOINT,
        primary_key="chunk_id",
        index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=f"{FQ}.med_nec_criteria",
            pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[EmbeddingSourceColumn(name="chunk_to_embed",
                                                            embedding_model_endpoint_name=EMBED_MODEL)],
        ),
    )
    print("VS index created (provisioning):", VS_INDEX)

# Bounded wait so the index is queryable before the chatbot / grounding stages; never fails the bootstrap.
deadline = time.time() + 900
state = None
while time.time() < deadline:
    idx = w.vector_search_indexes.get_index(index_name=VS_INDEX)
    status = idx.status.as_dict() if idx.status else {}
    state = status.get("detailed_state") or status.get("index_state") or status
    if status.get("ready"):
        break
    time.sleep(20)
print("VS index status:", state)
report["vs_index_state"] = str(state)

# COMMAND ----------
# MAGIC %md ## 5. mpfs_indicator_descriptors — extracted from the public Noridian PDF (skipped if populated)
# MAGIC `responseFormat` is unsupported on this endpoint, so the model is prompted for JSON and fences are stripped
# MAGIC before `from_json`. Group names must match the `'Status Code'` group used by `mpfs_lookup`.

# COMMAND ----------

if row_count(f"{FQ}.mpfs_indicator_descriptors") == 0:
    spark.sql(f"""
    CREATE OR REPLACE TABLE {FQ}.mpfs_indicator_descriptors
    COMMENT 'CMS MPFS indicator meanings, extracted from the Noridian JE Part B descriptor PDF via ai_parse_document + ai_query.'
    AS
    WITH parsed AS (
      SELECT concat_ws('\\n', transform(
               variant_get(ai_parse_document(content, map('version','2.0')), '$.document.elements','ARRAY<VARIANT>'),
               e -> variant_get(e,'$.content','STRING'))) AS txt
      FROM read_files('{RAW}/MPFS_Indicator_Descriptors_-_JE_Part_B_-_Noridian.pdf', format => 'binaryFile')
    ),
    extracted AS (
      SELECT regexp_replace(ai_query('{EXTRACT_MODEL}',
        concat('Extract the CMS MPFS indicator descriptor tables. Return ONLY JSON ',
          '{{"indicators":[{{"indicator_group":"...","indicator_code":"...","description":"..."}}]}} with no markdown. ',
          'Groups: Status Code; Global Surgery Package Days; Professional/Technical Component (P/T); Multiple Surgery (Modifier 51); ',
          'Bilateral Surgery (Modifier 50); Assistant at Surgery (Modifier 80); Co-Surgeons (Modifier 62); Team Surgery (Modifier 66); ',
          'Imaging Cap Indicator (ICI); Physician Supervision of Diagnostic Procedures (PSDP); Diagnostic Imaging Family (DIF). ',
          'Include every code row; do not invent codes.\\n\\nDOCUMENT:\\n', txt),
        modelParameters => named_struct('temperature', CAST(0.0 AS DOUBLE), 'max_tokens', 16000)),
        '```json|```', '') AS js
      FROM parsed
    )
    SELECT x.indicator_group, x.indicator_code, x.description
    FROM extracted
    LATERAL VIEW explode(from_json(js, 'STRUCT<indicators:ARRAY<STRUCT<indicator_group:STRING,indicator_code:STRING,description:STRING>>>').indicators) t AS x
    WHERE x.indicator_group IS NOT NULL AND x.indicator_code IS NOT NULL AND x.description IS NOT NULL
    """)
    print("mpfs_indicator_descriptors: extracted")
else:
    print("mpfs_indicator_descriptors: already populated, skipped")
report["mpfs_indicator_descriptors"] = row_count(f"{FQ}.mpfs_indicator_descriptors")

# COMMAND ----------
# MAGIC %md ## 6. UC SQL functions (chatbot tools)
# MAGIC Created only when the source table exists (see header). Parameter comments drive LLM tool-calling.
# MAGIC **CREATE IF NOT EXISTS, never OR REPLACE:** the chat endpoint's auth passthrough is bound to these function
# MAGIC objects; replacing them on every job run broke the endpoint (model load: System Service Principal lacks EXECUTE).
# MAGIC To change a definition: DROP FUNCTION, re-run this notebook, then update the endpoint config.
# MAGIC Grants are NOT issued here (least privilege): see governance/02_reviewer_grants.sql.

# COMMAND ----------

FUNCTIONS = {
    "get_appeal": (["appeals_output"], f"""
CREATE FUNCTION IF NOT EXISTS {FQ}.get_appeal(
  p_facility_id BIGINT COMMENT 'Facility ID (composite key part 1)',
  p_patient_control_number BIGINT COMMENT 'Patient control number = patient account number (composite key part 2)',
  p_encounter_nbr BIGINT COMMENT 'Encounter number (composite key part 3)')
RETURNS TABLE(recommendation STRING, needs_review_reason STRING, reason_text STRING, cheat_sheet STRING, appeal_letter STRING)
COMMENT 'Return the generated appeal recommendation (WARRANTED, NOT WARRANTED or NEEDS REVIEW), the reason if it needs review, the decision-worksheet cheat sheet, and the appeal letter for one denied encounter, keyed by facility id, patient control number, and encounter number.'
RETURN SELECT recommendation, needs_review_reason, reason_text, cheat_sheet, appeal_letter
       FROM {FQ}.appeals_output
       WHERE FACILITY_ID=p_facility_id AND PATIENT_CONTROL_NUMBER=p_patient_control_number AND ENCOUNTER_NBR=p_encounter_nbr
"""),
    "get_encounter": (["encounter_grounding"], f"""
CREATE FUNCTION IF NOT EXISTS {FQ}.get_encounter(
  p_facility_id BIGINT COMMENT 'Facility ID (composite key part 1)',
  p_patient_control_number BIGINT COMMENT 'Patient control number = patient account number (composite key part 2)',
  p_encounter_nbr BIGINT COMMENT 'Encounter number (composite key part 3)')
RETURNS TABLE(patient_name STRING, payer_name STRING, criteria_payer STRING, denial_code STRING,
              reason_text STRING, hcpcs_codes STRING, dx_codes STRING, clinical_digest STRING, mpfs_context STRING,
              expected_reimbursement DOUBLE, appeal_deadline DATE, days_remaining INT, deadline_status STRING)
COMMENT 'Return the claim facts, deadline status and clinical summary for one denied encounter (payer, denial code+reason, CPT/HCPCS codes, ICD-10 diagnoses, a clinical-notes digest, MPFS coding context), keyed by facility id, patient control number, and encounter number.'
RETURN SELECT patient_name, payer_name, criteria_payer, denial_code, reason_text,
              hcpcs_codes, dx_codes, clinical_digest, mpfs_context,
              expected_reimbursement, appeal_deadline, days_remaining, deadline_status
       FROM {FQ}.encounter_grounding
       WHERE FACILITY_ID=p_facility_id AND PATIENT_CONTROL_NUMBER=p_patient_control_number AND ENCOUNTER_NBR=p_encounter_nbr
"""),
    "mpfs_lookup": (["mpfs_indicator_listing", "mpfs_indicator_descriptors"], f"""
CREATE FUNCTION IF NOT EXISTS {FQ}.mpfs_lookup(
  p_code STRING COMMENT 'A 5-character CPT/HCPCS code, e.g. 99291 or 66984')
RETURNS TABLE(code STRING, status_code STRING, status_meaning STRING, global_days STRING, bilateral STRING, assistant STRING)
COMMENT 'Look up the 2025 MPFS indicators for a CPT/HCPCS code (status code + its plain-English meaning, global-surgery days, bilateral and assistant-at-surgery indicators). Use to explain the coding/billing status of a procedure. Returns only what is stored; it does NOT return RVUs or payment amounts.'
RETURN SELECT mp.`Code`, mp.`S`, sd.description, mp.`GLB`, mp.`B`, mp.`A`
       FROM {FQ}.mpfs_indicator_listing mp
       LEFT JOIN {FQ}.mpfs_indicator_descriptors sd
              ON sd.indicator_group='Status Code' AND sd.indicator_code = mp.`S`
       WHERE mp.`Code` = p_code AND coalesce(mp.`Modifier`,'') = ''
"""),
    "descriptor_lookup": (["mpfs_indicator_descriptors"], f"""
CREATE FUNCTION IF NOT EXISTS {FQ}.descriptor_lookup(
  p_term STRING COMMENT 'A search term: an indicator group name, an indicator code, or a concept like bilateral or assistant at surgery')
RETURNS TABLE(indicator_group STRING, indicator_code STRING, description STRING)
COMMENT 'Search the CMS MPFS indicator descriptor reference for the plain-English meaning of an indicator group, code, or concept (e.g. status code, global surgery, bilateral, assistant at surgery).'
RETURN SELECT indicator_group, indicator_code, description
       FROM {FQ}.mpfs_indicator_descriptors
       WHERE description ILIKE concat('%', p_term, '%') OR indicator_group ILIKE concat('%', p_term, '%') OR indicator_code = p_term
"""),
}

deferred = []
for fn, (sources, ddl) in FUNCTIONS.items():
    missing = [s for s in sources if not table_exists(f"{FQ}.{s}")]
    if missing:
        deferred.append(fn)
        print(f"DEFERRED {fn}: missing source table(s) {missing}")
        continue
    spark.sql(ddl)
    print(f"function ready: {fn}")
report["functions_deferred"] = deferred

# COMMAND ----------
# MAGIC %md ## 7. Bootstrap object summary

# COMMAND ----------

print("BOOTSTRAP SUMMARY:", report)
