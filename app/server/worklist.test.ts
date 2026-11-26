import { describe, expect, it } from 'vitest';
import {
  CaseKeySchema,
  ReviewActionBodySchema,
  WorklistQuerySchema,
  LATEST_EDIT_SQL,
  SUMMARY_SQL,
  WORKLIST_COUNT_SQL,
  WORKLIST_SORTS,
  buildWorklistQuery,
  toSummary,
  likePattern,
  pdfUrl,
  reviewActionAllowed,
  reviewStatusLabel,
  searchPattern,
  toLatestEdit,
  toWorklistItem,
  volumeFileName,
} from './worklist';

describe('review action guard (never-fabricate rule)', () => {
  it('lets EDIT, APPROVE and SUBMIT through only for a WARRANTED appeal', () => {
    for (const action of ['EDIT', 'APPROVE', 'SUBMIT'] as const) {
      expect(reviewActionAllowed(action, 'WARRANTED')).toBe(true);
      expect(reviewActionAllowed(action, 'NOT WARRANTED')).toBe(false);
      expect(reviewActionAllowed(action, 'NEEDS REVIEW')).toBe(false);
      expect(reviewActionAllowed(action, 'NOT GENERATED')).toBe(false);
      expect(reviewActionAllowed(action, null)).toBe(false);
    }
  });

  it('always allows routing to review and rejection', () => {
    for (const rec of ['WARRANTED', 'NOT WARRANTED', 'NEEDS REVIEW', 'NOT GENERATED']) {
      expect(reviewActionAllowed('ROUTE_TO_REVIEW', rec)).toBe(true);
      expect(reviewActionAllowed('REJECT', rec)).toBe(true);
    }
  });
});

describe('search patterns', () => {
  it('uses the sentinel for an empty search', () => {
    expect(searchPattern('')).toBe('%%');
    expect(searchPattern('   ')).toBe('%%');
  });

  it('escapes LIKE wildcards in the user term', () => {
    expect(likePattern('50%_a\\b')).toBe('%50\\%\\_a\\\\b%');
    expect(searchPattern('Marquez')).toBe('%Marquez%');
  });
});

describe('worklist SQL', () => {
  it('binds every value as a parameter and never embeds the search term', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toContain('$1');
    expect(sql).toContain('LIMIT $4 OFFSET $5');
    expect(sql).not.toContain('Marquez');
    expect(sql).toContain('fe_bar_appeals.worklist_serving');
    expect(sql).toContain('public.review_state');
  });

  it('puts NEW denials first, then priority rank, by default', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toMatch(/ORDER BY CASE WHEN w\.worklist_tag = 'NEW' THEN 0 ELSE 1 END, w\.priority_rank ASC/);
  });

  it('selects a fixed ORDER BY for every sort key', () => {
    for (const sort of ['priority', 'dos_desc', 'dos_asc', 'account_asc', 'account_desc', 'expected_desc'] as const) {
      expect(buildWorklistQuery(sort)).toContain('ORDER BY');
    }
    expect(buildWorklistQuery('account_desc')).toContain('w."PATIENT_CONTROL_NUMBER" DESC');
  });

  it('joins the synced table on its upper-case key columns', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toContain('r.facility_id = w."FACILITY_ID"');
    expect(sql).toContain('w."ENCOUNTER_NBR"::text');
  });

  it('does not reference the retired agent schema or endpoint', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).not.toContain('appeals_agent');
    expect(sql).not.toContain('appeals-chat-agent-endpoint');
  });
});

describe('request validation', () => {
  it('defaults the worklist query to priority order, first page, 10 rows', () => {
    const parsed = WorklistQuerySchema.parse({});
    expect(parsed).toEqual({
      search: '',
      sort: 'priority',
      page: 0,
      page_size: 10,
      recommendation: 'ALL',
      min_expected: 0,
    });
  });

  it('rejects an oversized page and an unknown sort key', () => {
    expect(WorklistQuerySchema.safeParse({ page_size: '1000' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ sort: 'drop_table' }).success).toBe(false);
  });

  it('accepts only numeric composite keys', () => {
    expect(CaseKeySchema.safeParse({ facility_id: '101', account: '770000001', encounter_nbr: '50000001' }).success).toBe(true);
    expect(CaseKeySchema.safeParse({ facility_id: "101' OR 1=1", account: '1', encounter_nbr: '1' }).success).toBe(false);
  });

  it('requires edited_letter for EDIT and nothing extra for APPROVE', () => {
    const key = { facility_id: '101', account: '770000001', encounter_nbr: '50000001' };
    expect(ReviewActionBodySchema.safeParse({ ...key, action: 'EDIT' }).success).toBe(false);
    expect(ReviewActionBodySchema.safeParse({ ...key, action: 'EDIT', edited_letter: '   ' }).success).toBe(false);
    expect(ReviewActionBodySchema.safeParse({ ...key, action: 'EDIT', edited_letter: 'Dear reviewer' }).success).toBe(true);
    expect(ReviewActionBodySchema.safeParse({ ...key, action: 'APPROVE' }).success).toBe(true);
  });

  it('rejects action names outside the append-only event set', () => {
    const key = { facility_id: '101', account: '770000001', encounter_nbr: '50000001' };
    expect(ReviewActionBodySchema.safeParse({ ...key, action: 'DELETE' }).success).toBe(false);
  });
});

describe('recommendation and expected-reimbursement filters', () => {
  it('accepts every recommendation filter code and defaults to ALL', () => {
    for (const recommendation of ['ALL', 'WARRANTED', 'NOT_WARRANTED', 'NEEDS_REVIEW', 'NOT_GENERATED']) {
      expect(WorklistQuerySchema.safeParse({ recommendation }).success).toBe(true);
    }
    expect(WorklistQuerySchema.parse({}).recommendation).toBe('ALL');
  });

  it('rejects unknown or DB-style recommendation values', () => {
    expect(WorklistQuerySchema.safeParse({ recommendation: 'WARRANTED; DROP TABLE x' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ recommendation: 'NOT WARRANTED' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ recommendation: 'warranted' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ recommendation: ['WARRANTED', 'ALL'] }).success).toBe(false);
  });

  it('accepts non-negative numeric min_expected and rejects negative, non-numeric or oversized values', () => {
    expect(WorklistQuerySchema.parse({ min_expected: '10000' }).min_expected).toBe(10000);
    expect(WorklistQuerySchema.parse({ min_expected: '0' }).min_expected).toBe(0);
    expect(WorklistQuerySchema.parse({ min_expected: '2500.5' }).min_expected).toBe(2500.5);
    expect(WorklistQuerySchema.safeParse({ min_expected: '-1' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ min_expected: 'abc' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ min_expected: 'Infinity' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ min_expected: '1e30' }).success).toBe(false);
    expect(WorklistQuerySchema.safeParse({ min_expected: ['1', '2'] }).success).toBe(false);
  });

  it('binds recommendation and min_expected as $2 and $3, never inline', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toContain('$2::text');
    expect(sql).toContain('COALESCE(w.expected_reimbursement, 0) >= $3::float8');
    expect(sql).toContain("$2::text = 'ALL'");
    expect(sql).toContain("$2::text = 'NOT_GENERATED' AND w.recommendation IS NULL");
  });

  it('maps each filter code to its DB value inside fixed SQL literals', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toContain("$2::text = 'WARRANTED' AND w.recommendation = 'WARRANTED'");
    expect(sql).toContain("$2::text = 'NOT_WARRANTED' AND w.recommendation = 'NOT WARRANTED'");
    expect(sql).toContain("$2::text = 'NEEDS_REVIEW' AND w.recommendation = 'NEEDS REVIEW'");
  });

  it('keeps the count query on the same filters ($1..$3 only)', () => {
    expect(WORKLIST_COUNT_SQL).toContain('COUNT(*)');
    expect(WORKLIST_COUNT_SQL).toContain('$2::text');
    expect(WORKLIST_COUNT_SQL).toContain('>= $3::float8');
    expect(WORKLIST_COUNT_SQL).not.toMatch(/\$[4-9]/);
    expect(WORKLIST_COUNT_SQL).not.toMatch(/\b(INSERT|UPDATE|DELETE)\b/i);
  });

  it('adds expected_desc with NULLS LAST and the priority tie-break', () => {
    expect(WORKLIST_SORTS).toContain('expected_desc');
    expect(WORKLIST_SORTS).toContain('priority');
    expect(WORKLIST_SORTS).toContain('dos_desc');
    expect(buildWorklistQuery('expected_desc')).toMatch(
      /ORDER BY w\.expected_reimbursement DESC NULLS LAST, w\.priority_rank ASC/,
    );
    expect(WorklistQuerySchema.parse({ sort: 'expected_desc' }).sort).toBe('expected_desc');
    expect(WorklistQuerySchema.safeParse({ sort: 'expected_asc' }).success).toBe(false);
  });
});

describe('summary counts', () => {
  it('counts NULL recommendations as not_generated', () => {
    expect(SUMMARY_SQL).toMatch(/COUNT\(\*\) FILTER \(WHERE recommendation IS NULL\)::int\s+AS not_generated/);
    expect(SUMMARY_SQL).not.toMatch(/\$\d/);
  });

  it('maps not_generated into the summary response, defaulting to 0', () => {
    expect(toSummary({ total: '5', not_generated: '2', warranted: '3' })).toMatchObject({
      total: 5,
      not_generated: 2,
      warranted: 3,
    });
    expect(toSummary(undefined).not_generated).toBe(0);
  });
});

describe('row mapping', () => {
  const row = {
    facility_id: '101',
    account: '770000001',
    encounter_nbr: '50000001',
    patient_name: 'Elena Marquez',
    payer_name: 'BCBS of Arizona',
    denial_code: 'CO50',
    dos: '2026-08-01',
    worklist_tag: 'AT_RISK',
    priority_rank: 1,
    days_remaining: 9,
    deadline_status: 'AT_RISK',
    appeal_deadline: '2026-12-03',
    expected_reimbursement: 24850,
    recommendation: 'WARRANTED',
    needs_review_reason: null,
    letter_pdf_path: '/Volumes/appeals_hackathon_catalog/fe_bar_appeals/appeal_pdfs/letter_101_770000001_50000001.pdf',
    cheat_sheet_pdf_path: null,
    data_sheet_pdf_path: '/Volumes/appeals_hackathon_catalog/fe_bar_appeals/appeal_pdfs/ds_101_770000001_50000001.pdf',
    review_status: null,
    last_reviewer: null,
    last_action_at: null,
    submitted_at: null,
  };

  it('maps keys, numbers and nulls to the API shape', () => {
    const item = toWorklistItem(row);
    expect(item.account).toBe('770000001');
    expect(item.priority_rank).toBe(1);
    expect(item.days_remaining).toBe(9);
    expect(item.expected_reimbursement).toBe(24850);
    expect(item.needs_review_reason).toBeNull();
    expect(item.review_status).toBeNull();
  });

  it('turns numeric strings from Postgres into numbers and keeps null as null', () => {
    const item = toWorklistItem({ ...row, expected_reimbursement: '24850.00', priority_rank: null });
    expect(item.expected_reimbursement).toBe(24850);
    expect(item.priority_rank).toBeNull();
  });

  it('shows a missing recommendation as not generated, not as NEEDS REVIEW', () => {
    expect(toWorklistItem({ ...row, recommendation: null }).recommendation).toBe('NOT GENERATED');
  });

  it('builds relative file URLs from the volume basename', () => {
    expect(volumeFileName(row.letter_pdf_path)).toBe('letter_101_770000001_50000001.pdf');
    expect(pdfUrl(row.data_sheet_pdf_path)).toBe(
      '/api/files/files/raw?path=ds_101_770000001_50000001.pdf',
    );
    expect(pdfUrl(null)).toBeNull();
  });

  it('labels review statuses', () => {
    expect(reviewStatusLabel(null)).toBe('Not started');
    expect(reviewStatusLabel('ROUTE_TO_REVIEW')).toBe('Routed to review');
    expect(reviewStatusLabel('SUBMIT')).toBe('Submitted');
  });
});

describe('latest edit (edit version)', () => {
  it('reports the edit count as version N for the latest saved edit', () => {
    expect(
      toLatestEdit({ edited_letter: 'v2 text', reviewer: 'a@example.test', created_at: '2026-11-25 10:00:00+00', version: '2' }),
    ).toEqual({ edited_letter: 'v2 text', reviewer: 'a@example.test', created_at: '2026-11-25 10:00:00+00', version: 2 });
  });

  it('is null with no edit and never reports a negative or missing version', () => {
    expect(toLatestEdit(undefined)).toBeNull();
    expect(toLatestEdit({ edited_letter: 'x' })?.version).toBe(0);
  });

  it('counts EDIT events only, scoped to the same key, and reads without writing', () => {
    expect(LATEST_EDIT_SQL).toMatch(/COUNT\(\*\)/);
    expect(LATEST_EDIT_SQL).toMatch(/action = 'EDIT'/);
    expect(LATEST_EDIT_SQL).not.toMatch(/\b(INSERT|UPDATE|DELETE)\b/i);
    expect(LATEST_EDIT_SQL).toMatch(/\$1[\s\S]*\$2[\s\S]*\$3/);
  });
});
