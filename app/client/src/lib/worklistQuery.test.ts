import { describe, expect, it } from 'vitest';
import type { WorklistSummary } from './api';
import {
  buildWorklistQuery,
  countForFilter,
  formatChipLabel,
  hasActiveFilters,
  HIGH_VALUE_MIN_EXPECTED,
  minExpectedFor,
  RECOMMENDATION_FILTERS,
} from './worklistQuery';

const SUMMARY: WorklistSummary = {
  total: 120,
  new_count: 4,
  at_risk: 9,
  warranted: 72,
  not_warranted: 20,
  needs_review: 18,
  not_generated: 10,
  warranted_expected: 500000,
};

const BASE = { search: '', sort: 'priority', page: 0, page_size: 10, recommendation: 'ALL' as const, min_expected: 0 };

describe('buildWorklistQuery', () => {
  it('sends the default filter state explicitly', () => {
    const qs = new URLSearchParams(buildWorklistQuery(BASE));
    expect(qs.get('recommendation')).toBe('ALL');
    expect(qs.get('min_expected')).toBe('0');
    expect(qs.get('sort')).toBe('priority');
    expect(qs.get('page')).toBe('0');
    expect(qs.get('page_size')).toBe('10');
  });

  it('encodes search text safely so it cannot inject extra params', () => {
    const qs = new URLSearchParams(buildWorklistQuery({ ...BASE, search: 'a&sort=evil #1' }));
    expect(qs.get('search')).toBe('a&sort=evil #1');
    expect(qs.get('sort')).toBe('priority');
  });

  it('passes the recommendation filter and high-value threshold through', () => {
    const qs = new URLSearchParams(
      buildWorklistQuery({ ...BASE, sort: 'expected_desc', recommendation: 'NEEDS_REVIEW', min_expected: HIGH_VALUE_MIN_EXPECTED }),
    );
    expect(qs.get('sort')).toBe('expected_desc');
    expect(qs.get('recommendation')).toBe('NEEDS_REVIEW');
    expect(qs.get('min_expected')).toBe('10000');
  });

  it('never sends a NaN or negative min_expected', () => {
    expect(new URLSearchParams(buildWorklistQuery({ ...BASE, min_expected: Number.NaN })).get('min_expected')).toBe('0');
    expect(new URLSearchParams(buildWorklistQuery({ ...BASE, min_expected: -5 })).get('min_expected')).toBe('0');
  });
});

describe('filter helpers', () => {
  it('maps the high-value toggle to the 10K threshold', () => {
    expect(minExpectedFor(true)).toBe(10000);
    expect(minExpectedFor(false)).toBe(0);
  });

  it('reads each chip count from the matching summary field', () => {
    expect(countForFilter(SUMMARY, 'ALL')).toBe(120);
    expect(countForFilter(SUMMARY, 'WARRANTED')).toBe(72);
    expect(countForFilter(SUMMARY, 'NOT_WARRANTED')).toBe(20);
    expect(countForFilter(SUMMARY, 'NEEDS_REVIEW')).toBe(18);
    expect(countForFilter(SUMMARY, 'NOT_GENERATED')).toBe(10);
  });

  it('returns null counts while the summary is unavailable', () => {
    expect(countForFilter(null, 'WARRANTED')).toBeNull();
  });

  it('formats chip labels with counts, or an em dash while loading', () => {
    expect(formatChipLabel('Warranted', 72)).toBe('Warranted 72');
    expect(formatChipLabel('Warranted', 1234)).toBe('Warranted 1,234');
    expect(formatChipLabel('Warranted', null)).toBe('Warranted —');
  });

  it('detects when any filter is active', () => {
    const none = { search: '', recommendation: 'ALL' as const, highValueOnly: false };
    expect(hasActiveFilters(none)).toBe(false);
    expect(hasActiveFilters({ ...none, search: '  ' })).toBe(false);
    expect(hasActiveFilters({ ...none, search: 'smith' })).toBe(true);
    expect(hasActiveFilters({ ...none, recommendation: 'WARRANTED' })).toBe(true);
    expect(hasActiveFilters({ ...none, highValueOnly: true })).toBe(true);
  });

  it('lists the five recommendation chips in contract order', () => {
    expect(RECOMMENDATION_FILTERS.map((f) => f.value)).toEqual([
      'ALL',
      'WARRANTED',
      'NOT_WARRANTED',
      'NEEDS_REVIEW',
      'NOT_GENERATED',
    ]);
  });
});
