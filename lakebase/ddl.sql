-- FE Bar Lakebase DDL (database `appeals`). Idempotent. Synthetic data only.
-- Append-only reviewer events. Writes come from the app (app SP / OBO, see AUTH.md); nothing UPDATEs or DELETEs.
CREATE TABLE IF NOT EXISTS review_actions (
  id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_id            BIGINT      NOT NULL,
  patient_control_number BIGINT      NOT NULL,
  encounter_nbr          BIGINT      NOT NULL,
  action                 TEXT        NOT NULL CHECK (action IN ('EDIT','APPROVE','REJECT','ROUTE_TO_REVIEW','SUBMIT')),
  edited_letter          TEXT,
  reviewer               TEXT        NOT NULL,
  note                   TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS review_actions_enc_idx
  ON review_actions (facility_id, patient_control_number, encounter_nbr, created_at);
