# Databricks notebook source
# MAGIC %md
# MAGIC # 40_render_pdfs — render only the PDFs that are missing
# MAGIC
# MAGIC Three PDF families, all written to the `appeal_pdfs` volume:
# MAGIC 1. `<key>_datasheet.pdf` — DETERMINISTIC data sheet (no LLM) for EVERY grounded encounter in `data_sheet_facts`
# MAGIC    (not limited by the 60-per-run LLM cap). Path -> `data_sheet_facts.data_sheet_pdf_path`, copied to `appeals_output`.
# MAGIC 2. `<key>_cheatsheet.pdf` — the LLM decision worksheet, labelled "AI reasoning". Every row with a worksheet.
# MAGIC 3. `<key>_letter.pdf` — the appeal letter, WARRANTED rows only.
# MAGIC
# MAGIC Idempotent: only rows whose PDF path is NULL are rendered. Paths are written back with MERGE from a temp view
# MAGIC (no string-built SQL). Never CREATE OR REPLACE on `appeals_output` (it would drop the paths).

# COMMAND ----------
# MAGIC %pip install -q markdown xhtml2pdf

# COMMAND ----------

import html
import os
from io import BytesIO

import markdown
from xhtml2pdf import pisa

CATALOG = "appeals_hackathon_catalog"
SCHEMA = "fe_bar_appeals"
FQ = f"{CATALOG}.{SCHEMA}"
PDF_DIR = f"/Volumes/{CATALOG}/{SCHEMA}/appeal_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

CSS = """
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.4; margin: 18px; }
h1 { font-size: 15pt; margin-top: 0; }
h2 { font-size: 11.5pt; margin-top: 12pt; border-bottom: 1px solid #999; }
table { border-collapse: collapse; width: 100%; margin: 6px 0; }
th, td { border: 1px solid #bbb; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background-color: #f0f0f0; width: 28%; }
.notice { background-color: #fff4d6; border: 1px solid #d9b65c; padding: 6px; }
.small { font-size: 8.5pt; color: #555; }
"""


def esc_br(text):
    """HTML-escape plain text and keep its line breaks (no markdown interpretation: verbatim blocks)."""
    return html.escape(str(text if text is not None else "")).replace("\n", "<br/>")


def kv_table(pairs):
    return "<table>" + "".join(f"<tr><th>{html.escape(k)}</th><td>{esc_br(v)}</td></tr>" for k, v in pairs) + "</table>"


def wrap(title, body):
    return (f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
            f"<h1>{html.escape(title)}</h1>{body}</body></html>")


def html_to_pdf(doc, path):
    with open(path, "w+b") as fh:
        status = pisa.pisaDocument(BytesIO(doc.encode("utf-8")), fh)
    if status.err:
        print(f"  PDF error {path}: {status.err}")
        return False
    return True


def md_html(text):
    """Markdown -> HTML for LLM-written text. The text is HTML-escaped FIRST so that raw tags from the model
    (or from prompt-injected clinical notes) stay text. xhtml2pdf fetches <img>/<link> resources, so passing
    model HTML through would allow local-file reads and outbound fetches from the job."""
    return markdown.markdown(html.escape(text or ""), extensions=["tables"])


# COMMAND ----------
# MAGIC %md ## 1. Data sheets (deterministic, every grounded encounter)

# COMMAND ----------

def datasheet_body(r):
    claim = kv_table([
        ("Patient", r.patient_name), ("DOB", r.dob_text), ("Sex", r.sex), ("Member ID", r.member_id),
        ("Claim number", r.claim_number), ("Provider", r.provider_name), ("Payer", r.payer_name),
        ("Denial code", r.denial_code), ("Denial reason (CARC)", r.denial_reason),
        ("Must prove", r.what_to_prove), ("CARC category", r.carc_category),
        ("Date of service", r.dos_text), ("POS", r.pos), ("CPT/HCPCS", r.hcpcs_codes),
        ("Modifiers", r.modifiers), ("ICD-10 diagnoses", r.dx_codes),
    ])
    money = kv_table([
        ("Denial date", r.denial_date), ("Appeal limit (days) - ASSUMPTION by payer type", r.appeal_limit_days),
        ("Appeal deadline", r.appeal_deadline), ("Days remaining", r.days_remaining),
        ("Deadline status", r.deadline_status), ("Worklist tag", r.worklist_tag),
        ("Total charges", r.total_charges), ("Expected reimbursement", r.expected_reimbursement),
    ])
    return (
        "<h2>Claim and denial facts</h2>" + claim
        + "<h2>Payer and criteria routing</h2><p>" + esc_br(r.criteria_routing) + "</p>"
        + "<h2>Criteria passages (routed set, verbatim)</h2><p class='small'>" + esc_br(r.criteria_passages) + "</p>"
        + "<h2>Clinical notes (verbatim, dated)</h2><p>" + esc_br(r.notes_verbatim) + "</p>"
        + "<h2>MPFS coding context</h2><p class='small'>" + esc_br(r.mpfs_context) + "</p>"
        + "<h2>Deadline and dollars</h2>" + money
        + "<h2>Payer contract</h2><p><b>" + esc_br(r.payer_contract_terms) + "</b></p>"
        + "<p class='small'>Deterministic data sheet: no AI-generated content. Built from source tables by "
          "pipeline/25_data_sheet_facts.sql. Synthetic demo data.</p>"
    )


ds_rows = spark.sql(f"SELECT * FROM {FQ}.data_sheet_facts WHERE data_sheet_pdf_path IS NULL").collect()
print(f"data sheets to render: {len(ds_rows)}")
ds_updates = []
for r in ds_rows:
    key = f"{r.FACILITY_ID}_{r.PATIENT_CONTROL_NUMBER}_{r.ENCOUNTER_NBR}"
    path = f"{PDF_DIR}/{key}_datasheet.pdf"
    ok = html_to_pdf(wrap(f"Data sheet - {key}", datasheet_body(r)), path)
    ds_updates.append((r.FACILITY_ID, r.PATIENT_CONTROL_NUMBER, r.ENCOUNTER_NBR, path if ok else None))
print(f"data sheets rendered: {sum(1 for u in ds_updates if u[3])}")

if ds_updates:
    spark.createDataFrame(ds_updates,
        "FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT, data_sheet_pdf_path STRING") \
        .createOrReplaceTempView("ds_updates")
    spark.sql(f"""
        MERGE INTO {FQ}.data_sheet_facts t USING ds_updates s
        ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR
        WHEN MATCHED THEN UPDATE SET t.data_sheet_pdf_path = coalesce(s.data_sheet_pdf_path, t.data_sheet_pdf_path)
    """)

# COMMAND ----------
# MAGIC %md ## 2. AI worksheet (labelled "AI reasoning") and appeal letters (WARRANTED only)

# COMMAND ----------

ao_rows = spark.sql(f"""
    SELECT * FROM {FQ}.appeals_output
    WHERE (cheat_sheet IS NOT NULL AND cheat_sheet_pdf_path IS NULL)
       OR (recommendation = 'WARRANTED' AND appeal_letter IS NOT NULL AND letter_pdf_path IS NULL)
""").collect()
print(f"AI worksheets/letters to render: {len(ao_rows)}")

ao_updates = []
for r in ao_rows:
    key = f"{r.FACILITY_ID}_{r.PATIENT_CONTROL_NUMBER}_{r.ENCOUNTER_NBR}"
    ws_path = letter_path = None
    if r.cheat_sheet and r.cheat_sheet_pdf_path is None:
        notice = ("<p class='notice'><b>AI reasoning.</b> This worksheet was written by an LLM from the cited "
                  f"notes and criteria. Recommendation: <b>{html.escape(str(r.recommendation))}</b>. "
                  "Verify each citation against the data sheet.</p>")
        if r.needs_review_reason:
            notice += f"<p class='notice'><b>Needs review:</b> {esc_br(r.needs_review_reason)}</p>"
        ws_path = f"{PDF_DIR}/{key}_cheatsheet.pdf"
        if not html_to_pdf(wrap(f"AI reasoning worksheet - {key}", notice + md_html(r.cheat_sheet)), ws_path):
            ws_path = None
    if r.recommendation == "WARRANTED" and r.appeal_letter and r.letter_pdf_path is None:
        letter_path = f"{PDF_DIR}/{key}_letter.pdf"
        if not html_to_pdf(wrap(f"Appeal letter - {key}", md_html(r.appeal_letter)), letter_path):
            letter_path = None
    ao_updates.append((r.FACILITY_ID, r.PATIENT_CONTROL_NUMBER, r.ENCOUNTER_NBR, letter_path, ws_path))

if ao_updates:
    spark.createDataFrame(ao_updates,
        "FACILITY_ID BIGINT, PATIENT_CONTROL_NUMBER BIGINT, ENCOUNTER_NBR BIGINT, letter_pdf_path STRING, cheat_sheet_pdf_path STRING") \
        .createOrReplaceTempView("ao_pdf_updates")
    spark.sql(f"""
        MERGE INTO {FQ}.appeals_output t USING ao_pdf_updates s
        ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR
        WHEN MATCHED THEN UPDATE SET
          t.letter_pdf_path = coalesce(s.letter_pdf_path, t.letter_pdf_path),
          t.cheat_sheet_pdf_path = coalesce(s.cheat_sheet_pdf_path, t.cheat_sheet_pdf_path)
    """)

# COMMAND ----------
# MAGIC %md ## 3. Copy data-sheet paths onto appeals_output (rows that have a generated output)

# COMMAND ----------

spark.sql(f"""
    MERGE INTO {FQ}.appeals_output t
    USING (SELECT FACILITY_ID, PATIENT_CONTROL_NUMBER, ENCOUNTER_NBR, data_sheet_pdf_path
           FROM {FQ}.data_sheet_facts WHERE data_sheet_pdf_path IS NOT NULL) s
    ON t.FACILITY_ID = s.FACILITY_ID AND t.PATIENT_CONTROL_NUMBER = s.PATIENT_CONTROL_NUMBER AND t.ENCOUNTER_NBR = s.ENCOUNTER_NBR
    WHEN MATCHED THEN UPDATE SET t.data_sheet_pdf_path = s.data_sheet_pdf_path
""")

# COMMAND ----------
# MAGIC %md ## 4. Summary

# COMMAND ----------

summary = spark.sql(f"""
    SELECT count(*) AS output_rows,
           count(cheat_sheet_pdf_path) AS worksheet_pdfs,
           sum(CASE WHEN recommendation = 'WARRANTED' THEN 1 ELSE 0 END) AS warranted_rows,
           count(letter_pdf_path) AS letter_pdfs,
           count(data_sheet_pdf_path) AS datasheet_pdfs_on_output
    FROM {FQ}.appeals_output
""")
display(summary)
print("data sheets total with path:", spark.sql(f"SELECT count(data_sheet_pdf_path) n FROM {FQ}.data_sheet_facts").first().n)
