import { describe, expect, it } from 'vitest';
import {
  CaseKeySchema,
  ReviewActionBodySchema,
  WorklistQuerySchema,
  buildWorklistQuery,
  likePattern,
  pdfUrl,
  reviewActionAllowed,
  reviewStatusLabel,
  searchPattern,
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
    expect(sql).toContain('LIMIT $2 OFFSET $3');
    expect(sql).not.toContain('Marquez');
    expect(sql).toContain('fe_bar_appeals.worklist_serving');
    expect(sql).toContain('public.review_state');
  });

  it('puts NEW denials first, then priority rank, by default', () => {
    const sql = buildWorklistQuery('priority');
    expect(sql).toMatch(/ORDER BY CASE WHEN w\.worklist_tag = 'NEW' THEN 0 ELSE 1 END, w\.priority_rank ASC/);
  });

  it('selects a fixed ORDER BY for every sort key', () => {
    for (const sort of ['priority', 'dos_desc', 'dos_asc', 'account_asc', 'account_desc'] as const) {
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
    expect(parsed).toEqual({ search: '', sort: 'priority', page: 0, page_size: 10 });
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
