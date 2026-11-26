// Lakebase worklist contract for the FE Bar app (SPEC: Lakebase + App, owner C; app owner E).
//
// Reads: synced table `fe_bar_appeals.worklist_serving` (Postgres schema fe_bar_appeals, lower-case columns)
//        and view `public.review_state` (latest review action per encounter).
// Writes: append-only `public.review_actions` (INSERT only).
//
// Every value reaches Postgres as a bound `$n` parameter. The only text composed into SQL is the ORDER BY
// clause, which is picked from the fixed WORKLIST_ORDER_BY map (sort is a validated enum, not user text).
import { z } from 'zod';

export const REVIEW_ACTIONS = ['EDIT', 'APPROVE', 'REJECT', 'ROUTE_TO_REVIEW', 'SUBMIT'] as const;
export type ReviewAction = (typeof REVIEW_ACTIONS)[number];

/** Actions that presuppose a generated appeal letter. A NOT WARRANTED / NEEDS REVIEW / NOT GENERATED case has no
 *  letter, so it can still be routed to review or rejected, but never edited, approved or submitted.
 *  The UI does not gate these buttons, so the server enforces this (never-fabricate rule). */
export const ACTIONS_REQUIRING_WARRANTED: readonly ReviewAction[] = ['EDIT', 'APPROVE', 'SUBMIT'];

export function reviewActionAllowed(action: ReviewAction, recommendation: string | null | undefined): boolean {
  if (!ACTIONS_REQUIRING_WARRANTED.includes(action)) return true;
  return recommendation === 'WARRANTED';
}

export const WORKLIST_SORTS = ['priority', 'dos_desc', 'dos_asc', 'account_asc', 'account_desc'] as const;
export type WorklistSort = (typeof WORKLIST_SORTS)[number];

const WORKLIST_ORDER_BY: Record<WorklistSort, string> = {
  // Denied yesterday (NEW) first, then priority rank. This is the default worklist order.
  priority: `CASE WHEN w.worklist_tag = 'NEW' THEN 0 ELSE 1 END, w.priority_rank ASC`,
  dos_desc: `w.dos DESC NULLS LAST, w.priority_rank ASC`,
  dos_asc: `w.dos ASC NULLS LAST, w.priority_rank ASC`,
  account_asc: `w."PATIENT_CONTROL_NUMBER" ASC, w."ENCOUNTER_NBR" ASC`,
  account_desc: `w."PATIENT_CONTROL_NUMBER" DESC, w."ENCOUNTER_NBR" DESC`,
};

export const CaseKeySchema = z.object({
  facility_id: z.string().regex(/^\d{1,20}$/),
  account: z.string().regex(/^\d{1,20}$/),
  encounter_nbr: z.string().regex(/^\d{1,20}$/),
});
export type CaseKey = z.infer<typeof CaseKeySchema>;

export const WorklistQuerySchema = z.object({
  search: z.string().max(100).default(''),
  sort: z.enum(WORKLIST_SORTS).default('priority'),
  page: z.coerce.number().int().min(0).max(100_000).default(0),
  page_size: z.coerce.number().int().min(1).max(100).default(10),
});

export const ReviewActionBodySchema = CaseKeySchema.extend({
  action: z.enum(REVIEW_ACTIONS),
  edited_letter: z.string().max(100_000).optional(),
  note: z.string().max(2_000).optional(),
}).superRefine((body, ctx) => {
  if (body.action === 'EDIT' && !body.edited_letter?.trim()) {
    ctx.addIssue({ code: 'custom', path: ['edited_letter'], message: 'EDIT requires edited_letter' });
  }
});
export type ReviewActionBody = z.infer<typeof ReviewActionBodySchema>;

/** ILIKE pattern for a user search term. Wildcards in the term are escaped; the pattern itself is a bound param. */
export function likePattern(term: string): string {
  const escaped = term.replace(/[\\%_]/g, (m) => `\\${m}`);
  return `%${escaped}%`;
}

/** Empty search matches everything. The pattern '%%' is the sentinel checked in SQL. */
export function searchPattern(term: string): string {
  const trimmed = term.trim();
  return trimmed === '' ? '%%' : likePattern(trimmed);
}

export const WORKLIST_SELECT = `
SELECT
  w."FACILITY_ID"::text                  AS facility_id,
  w."PATIENT_CONTROL_NUMBER"::text       AS account,
  w."ENCOUNTER_NBR"::text                AS encounter_nbr,
  w.patient_name,
  w.payer_name,
  w.denial_code,
  w.dos::text                            AS dos,
  w.worklist_tag,
  w.priority_rank,
  w.days_remaining,
  w.deadline_status,
  w.appeal_deadline::text                AS appeal_deadline,
  w.expected_reimbursement::float8       AS expected_reimbursement,
  w.recommendation,
  w.needs_review_reason,
  w.letter_pdf_path,
  w.cheat_sheet_pdf_path,
  w.data_sheet_pdf_path,
  r.status                               AS review_status,
  r.last_reviewer,
  r.last_action_at::text                 AS last_action_at,
  r.submitted_at::text                   AS submitted_at,
  COUNT(*) OVER ()                       AS total_count
FROM fe_bar_appeals.worklist_serving w
LEFT JOIN public.review_state r
  ON r.facility_id = w."FACILITY_ID"
 AND r.patient_control_number = w."PATIENT_CONTROL_NUMBER"
 AND r.encounter_nbr = w."ENCOUNTER_NBR"`;

/** Worklist page. $1 = search pattern, $2 = page size, $3 = offset. ORDER BY is a fixed map entry (see above). */
export function buildWorklistQuery(sort: WorklistSort): string {
  return `${WORKLIST_SELECT}
WHERE ($1 = '%%' OR w.patient_name ILIKE $1 OR w.denial_code ILIKE $1 OR w."PATIENT_CONTROL_NUMBER"::text ILIKE $1)
ORDER BY ${WORKLIST_ORDER_BY[sort]}
LIMIT $2 OFFSET $3`;
}

/** Single case. $1 = FACILITY_ID, $2 = PATIENT_CONTROL_NUMBER, $3 = ENCOUNTER_NBR (bigint params, sent as text). */
export const CASE_SQL = `${WORKLIST_SELECT}
WHERE w."FACILITY_ID" = $1 AND w."PATIENT_CONTROL_NUMBER" = $2 AND w."ENCOUNTER_NBR" = $3`;

/** KPI strip over the whole worklist (not just the page). No parameters. */
export const SUMMARY_SQL = `
SELECT
  COUNT(*)::int                                                            AS total,
  COUNT(*) FILTER (WHERE worklist_tag = 'NEW')::int                        AS new_count,
  COUNT(*) FILTER (WHERE worklist_tag = 'AT_RISK')::int                    AS at_risk,
  COUNT(*) FILTER (WHERE recommendation = 'WARRANTED')::int                AS warranted,
  COUNT(*) FILTER (WHERE recommendation = 'NOT WARRANTED')::int            AS not_warranted,
  COUNT(*) FILTER (WHERE recommendation = 'NEEDS REVIEW')::int             AS needs_review,
  COALESCE(SUM(expected_reimbursement) FILTER (WHERE recommendation = 'WARRANTED'), 0)::float8 AS warranted_expected
FROM fe_bar_appeals.worklist_serving`;

/** Latest EDIT for a case (its edited letter), plus the last 20 review actions. $1..$3 = key. */
export const LATEST_EDIT_SQL = `
SELECT edited_letter, reviewer, created_at::text AS created_at
FROM public.review_actions
WHERE facility_id = $1 AND patient_control_number = $2 AND encounter_nbr = $3 AND action = 'EDIT'
ORDER BY created_at DESC, id DESC
LIMIT 1`;

export const HISTORY_SQL = `
SELECT id::text AS id, action, reviewer, note, created_at::text AS created_at
FROM public.review_actions
WHERE facility_id = $1 AND patient_control_number = $2 AND encounter_nbr = $3
ORDER BY created_at DESC, id DESC
LIMIT 20`;

/** Append-only insert. $1..$7 = facility_id, account, encounter_nbr, action, edited_letter, reviewer, note. */
export const INSERT_REVIEW_ACTION_SQL = `
INSERT INTO public.review_actions
  (facility_id, patient_control_number, encounter_nbr, action, edited_letter, reviewer, note)
VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING id::text AS id, action, reviewer, created_at::text AS created_at`;

/** Review status after an action. $1..$3 = key. */
export const REVIEW_STATE_SQL = `
SELECT status, last_reviewer, last_action_at::text AS last_action_at, submitted_at::text AS submitted_at
FROM public.review_state
WHERE facility_id = $1 AND patient_control_number = $2 AND encounter_nbr = $3`;

export interface WorklistItem {
  facility_id: string;
  account: string;
  encounter_nbr: string;
  patient_name: string;
  payer_name: string;
  denial_code: string;
  dos: string | null;
  worklist_tag: string;
  priority_rank: number | null;
  days_remaining: number | null;
  deadline_status: string | null;
  appeal_deadline: string | null;
  expected_reimbursement: number;
  recommendation: string;
  needs_review_reason: string | null;
  letter_pdf_path: string | null;
  cheat_sheet_pdf_path: string | null;
  data_sheet_pdf_path: string | null;
  review_status: string | null;
  last_reviewer: string | null;
  last_action_at: string | null;
  submitted_at: string | null;
}

export type Row = Record<string, unknown>;

/** Narrowing helpers: pg returns bigint/numeric as strings; NULL stays null. */
export function text(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  if (typeof v === 'string') return v;
  if (typeof v === 'number' || typeof v === 'bigint' || typeof v === 'boolean') return `${v}`;
  return null;
}

export function num(v: unknown): number | null {
  if (v === null || v === undefined || v === '') return null;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'string' || typeof v === 'bigint') {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

/** Maps a worklist_serving row (bigint/numeric arrive as strings) to the API shape. */
export function toWorklistItem(row: Row): WorklistItem {
  return {
    facility_id: text(row.facility_id) ?? '',
    account: text(row.account) ?? '',
    encounter_nbr: text(row.encounter_nbr) ?? '',
    patient_name: text(row.patient_name) ?? '',
    payer_name: text(row.payer_name) ?? '',
    denial_code: text(row.denial_code) ?? '',
    dos: text(row.dos),
    worklist_tag: text(row.worklist_tag) ?? 'OPEN',
    priority_rank: num(row.priority_rank),
    days_remaining: num(row.days_remaining),
    deadline_status: text(row.deadline_status),
    appeal_deadline: text(row.appeal_deadline),
    expected_reimbursement: num(row.expected_reimbursement) ?? 0,
    // NULL = the encounter has no appeals_output row yet (not generated); NEEDS REVIEW is a real model outcome.
    recommendation: text(row.recommendation) ?? 'NOT GENERATED',
    needs_review_reason: text(row.needs_review_reason),
    letter_pdf_path: text(row.letter_pdf_path),
    cheat_sheet_pdf_path: text(row.cheat_sheet_pdf_path),
    data_sheet_pdf_path: text(row.data_sheet_pdf_path),
    review_status: text(row.review_status),
    last_reviewer: text(row.last_reviewer),
    last_action_at: text(row.last_action_at),
    submitted_at: text(row.submitted_at),
  };
}

export function toSummary(row: Row | undefined) {
  return {
    total: num(row?.total) ?? 0,
    new_count: num(row?.new_count) ?? 0,
    at_risk: num(row?.at_risk) ?? 0,
    warranted: num(row?.warranted) ?? 0,
    not_warranted: num(row?.not_warranted) ?? 0,
    needs_review: num(row?.needs_review) ?? 0,
    warranted_expected: num(row?.warranted_expected) ?? 0,
  };
}

export function toLatestEdit(row: Row | undefined) {
  if (!row) return null;
  return { edited_letter: text(row.edited_letter), reviewer: text(row.reviewer), created_at: text(row.created_at) };
}

export function toHistory(rows: Row[]) {
  return rows.map((r) => ({
    id: text(r.id) ?? '',
    action: text(r.action) ?? '',
    reviewer: text(r.reviewer) ?? '',
    note: text(r.note),
    created_at: text(r.created_at) ?? '',
  }));
}

/** Basename of a volume path. Files routes take the path relative to the volume root. */
export function volumeFileName(path: string | null | undefined): string | null {
  if (!path) return null;
  const parts = path.split('/').filter(Boolean);
  return parts.length ? parts[parts.length - 1] : null;
}

/** Relative URL for the files plugin's inline PDF route (OBO, served from the UC volume). */
export function pdfUrl(path: string | null | undefined): string | null {
  const name = volumeFileName(path);
  return name ? `/api/files/files/raw?path=${encodeURIComponent(name)}` : null;
}

export const REVIEW_STATUS_LABELS: Record<string, string> = {
  EDIT: 'Edited',
  APPROVE: 'Approved',
  REJECT: 'Rejected',
  ROUTE_TO_REVIEW: 'Routed to review',
  SUBMIT: 'Submitted',
};

export function reviewStatusLabel(status: string | null): string {
  if (!status) return 'Not started';
  return REVIEW_STATUS_LABELS[status] ?? status;
}
