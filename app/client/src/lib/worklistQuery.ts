// Pure helpers for the worklist filter state: query-string building, chip counts, and chip labels.
// Kept free of React and fetch so they can be unit-tested directly.
import type { WorklistSummary } from './api';

/** Recommendation filter values understood by GET /api/worklist (server contract). */
export type RecommendationFilter = 'ALL' | 'WARRANTED' | 'NOT_WARRANTED' | 'NEEDS_REVIEW' | 'NOT_GENERATED';

export const RECOMMENDATION_FILTERS: ReadonlyArray<{ value: RecommendationFilter; label: string }> = [
  { value: 'ALL', label: 'All' },
  { value: 'WARRANTED', label: 'Warranted' },
  { value: 'NOT_WARRANTED', label: 'Not warranted' },
  { value: 'NEEDS_REVIEW', label: 'Needs review' },
  { value: 'NOT_GENERATED', label: 'Not generated' },
];

/** Summary field that holds the count for each recommendation filter. */
const COUNT_KEY: Record<RecommendationFilter, keyof WorklistSummary> = {
  ALL: 'total',
  WARRANTED: 'warranted',
  NOT_WARRANTED: 'not_warranted',
  NEEDS_REVIEW: 'needs_review',
  NOT_GENERATED: 'not_generated',
};

/** The "≥ $10K expected" toggle sends this as min_expected. */
export const HIGH_VALUE_MIN_EXPECTED = 10000;

export interface WorklistQueryParams {
  search: string;
  sort: string;
  page: number;
  page_size: number;
  recommendation: RecommendationFilter;
  min_expected: number;
}

export function minExpectedFor(highValueOnly: boolean): number {
  return highValueOnly ? HIGH_VALUE_MIN_EXPECTED : 0;
}

/** Builds the query string for GET /api/worklist. URLSearchParams handles encoding of user search text. */
export function buildWorklistQuery(p: WorklistQueryParams): string {
  // Guard against NaN/negative so the server never receives an invalid min_expected.
  const minExpected = Number.isFinite(p.min_expected) && p.min_expected > 0 ? p.min_expected : 0;
  return new URLSearchParams({
    search: p.search,
    sort: p.sort,
    page: String(p.page),
    page_size: String(p.page_size),
    recommendation: p.recommendation,
    min_expected: String(minExpected),
  }).toString();
}

/** Count for a chip from the summary, or null while the summary is loading or unavailable. */
export function countForFilter(summary: WorklistSummary | null, filter: RecommendationFilter): number | null {
  if (!summary) return null;
  return summary[COUNT_KEY[filter]];
}

/** "Warranted 72"; shows an em dash while the count is unknown, matching the KPI strip. */
export function formatChipLabel(label: string, count: number | null): string {
  return `${label} ${count === null ? '—' : count.toLocaleString('en-US')}`;
}

/** True when any filter (search, recommendation chip, or high-value toggle) narrows the list. */
export function hasActiveFilters(state: { search: string; recommendation: RecommendationFilter; highValueOnly: boolean }): boolean {
  return state.search.trim() !== '' || state.recommendation !== 'ALL' || state.highValueOnly;
}
