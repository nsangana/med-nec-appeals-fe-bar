// Typed client for the app's own API routes (server/server.ts). Worklist and review data come from
// Lakebase through these routes; the UI never queries Lakebase directly.

export interface WorklistItem {
  facility_id: string;
  account: string;
  encounter_nbr: string;
  patient_name: string;
  payer_name: string;
  denial_code: string;
  dos: string | null;
  /** NEW | AT_RISK | PAST_DUE | OPEN */
  worklist_tag: string;
  priority_rank: number | null;
  days_remaining: number | null;
  deadline_status: string | null;
  appeal_deadline: string | null;
  expected_reimbursement: number;
  /** WARRANTED | NOT WARRANTED | NEEDS REVIEW | NOT GENERATED */
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

export interface WorklistPage {
  items: WorklistItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface WorklistSummary {
  total: number;
  new_count: number;
  at_risk: number;
  warranted: number;
  not_warranted: number;
  needs_review: number;
  warranted_expected: number;
}

export interface CaseKey {
  facility_id: string;
  account: string;
  encounter_nbr: string;
}

export interface CaseDetail {
  item: WorklistItem;
  review: {
    status: string | null;
    status_label: string;
    last_reviewer: string | null;
    last_action_at: string | null;
    submitted_at: string | null;
    latest_edit: {
      edited_letter: string | null;
      reviewer: string | null;
      created_at: string | null;
      /** Edit count for the case; the latest saved edit is version N. */
      version: number;
    } | null;
    history: Array<{ id: string; action: string; reviewer: string; note: string | null; created_at: string }>;
  };
  files: {
    letter: { name: string | null; url: string | null };
    data_sheet: { name: string | null; url: string | null };
    ai_worksheet: { name: string | null; url: string | null };
  };
}

export type ReviewActionName = 'EDIT' | 'APPROVE' | 'REJECT' | 'ROUTE_TO_REVIEW' | 'SUBMIT';

export interface ReviewActionResult {
  ok: boolean;
  action_id: string | null;
  action: ReviewActionName;
  reviewer: string;
  created_at: string | null;
  status: string;
  status_label: string;
  submitted_at: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { error?: string; code?: string | null } | null;
    const detail = body?.code ? `${body.error ?? 'Request failed'} (${body.code})` : (body?.error ?? `Request failed (${res.status})`);
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

export function fetchWorklist(params: { search: string; sort: string; page: number; page_size: number }, signal?: AbortSignal) {
  const qs = new URLSearchParams({
    search: params.search,
    sort: params.sort,
    page: String(params.page),
    page_size: String(params.page_size),
  });
  return fetch(`/api/worklist?${qs.toString()}`, { signal, headers: { Accept: 'application/json' } }).then(async (res) => {
    if (!res.ok) {
      const body = (await res.json().catch(() => null)) as { error?: string; code?: string | null } | null;
      throw new ApiError(body?.code ? `${body.error ?? 'Request failed'} (${body.code})` : (body?.error ?? `Request failed (${res.status})`), res.status);
    }
    return (await res.json()) as WorklistPage;
  });
}

export function fetchSummary() {
  return getJson<WorklistSummary>('/api/worklist/summary');
}

export function fetchCase(key: CaseKey) {
  return getJson<CaseDetail>(
    `/api/cases/${encodeURIComponent(key.facility_id)}/${encodeURIComponent(key.account)}/${encodeURIComponent(key.encounter_nbr)}`,
  );
}

export async function postReviewAction(
  key: CaseKey,
  action: ReviewActionName,
  extra: { edited_letter?: string; note?: string } = {},
): Promise<ReviewActionResult> {
  const res = await fetch('/api/review-actions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ ...key, action, ...extra }),
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { error?: string; code?: string | null } | null;
    throw new ApiError(body?.code ? `${body.error ?? 'Save failed'} (${body.code})` : (body?.error ?? `Save failed (${res.status})`), res.status);
  }
  return (await res.json()) as ReviewActionResult;
}

export function fetchConfig() {
  return getJson<{ genieEnabled: boolean; reviewer: string | null }>('/api/config');
}
