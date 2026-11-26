-- Lakeflow SDP (SQL) | FE Bar appeals | Reference: 2025 CMS Part B MPFS Indicator Listing (public xlsx).
-- Logic carried over from the legacy pipeline/00_setup.py section 2: header on row 4 is skipped by the
-- data address, trailing */** 2025 change markers are stripped from Code, and only 5-character codes are kept.

CREATE OR REFRESH MATERIALIZED VIEW mpfs_indicator_listing
COMMENT 'Real 2025 CMS Part B MPFS Indicator Listing (HCPCS/CPT codes), loaded natively from the public xlsx in the raw_references volume. Source: CMS MPFS indicator listing (see data/SOURCES.md).'
TBLPROPERTIES ('delta.columnMapping.mode' = 'name')
AS
WITH raw AS (
  SELECT regexp_replace(_c0, '[*]+$', '') AS code_clean,
         _c1, _c2, _c3, _c4, _c5, _c6, _c7, _c8, _c9, _c10, _c11, _c12, _c13, _c14, _c15, _c16, _c17
  FROM read_files(
    '${refs_root}/2025_MPFS_Indicator_Listing.xlsx',
    format => 'excel', headerRows => 0, dataAddress => '2025 MPFS Indicators')
)
SELECT code_clean AS `Code`, _c1 AS `Modifier`, _c2 AS `S`, _c3 AS `GLB`,
  _c4 AS `Pre-Op %`, _c5 AS `Intra-Op %`, _c6 AS `Post-Op %`, _c7 AS `P/T`,
  _c8 AS `M`, _c9 AS `B`, _c10 AS `A`, _c11 AS `C`, _c12 AS `T`,
  _c13 AS `ICI`, _c14 AS `PSDP`, _c15 AS `ENDO Base`, _c16 AS `Effective Date`,
  coalesce(try_to_timestamp(_c17, 'M/d/yy'), try_to_timestamp(_c17, 'MM/dd/yyyy'),
           try_to_timestamp(_c17, 'M/d/yyyy'), try_to_timestamp(_c17)) AS `Update Date`
FROM raw
WHERE length(code_clean) = 5 AND code_clean <> 'Code';
