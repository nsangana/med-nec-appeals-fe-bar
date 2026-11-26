import { describe, expect, it } from 'vitest';
import { parseReason, summarizeReason } from './reason';

const SAMPLE =
  '• **FDA device approval/clearance pathway undocumented**: The consent form does not specify PMA or 510(k).\n\n' +
  '• **Protocol number conflicts with "standard care"**: Section 4 references a protocol number.\n\n' +
  '• **Evidence citations deferred**: Citations are "to be attached" but not included.';

describe('needs_review_reason parsing', () => {
  it('splits bulleted markdown into titled items', () => {
    const items = parseReason(SAMPLE);
    expect(items).toHaveLength(3);
    expect(items[0].title).toBe('FDA device approval/clearance pathway undocumented');
    expect(items[0].body).toBe('The consent form does not specify PMA or 510(k).');
    expect(items[1].title).toBe('Protocol number conflicts with "standard care"');
  });

  it('summarizes the list for the worklist cell with a count and the first title', () => {
    expect(summarizeReason(SAMPLE)).toBe('3 open items · FDA device approval/clearance pathway undocumented');
  });

  it('keeps a single plain reason as-is, without a count', () => {
    expect(parseReason('PARSE_FAILURE: model returned no JSON')).toEqual([
      { title: null, body: 'PARSE_FAILURE: model returned no JSON' },
    ]);
    expect(summarizeReason('PARSE_FAILURE: model returned no JSON')).toBe('PARSE_FAILURE: model returned no JSON');
  });

  it('returns nothing for empty input and truncates long summaries', () => {
    expect(parseReason(null)).toEqual([]);
    expect(summarizeReason('')).toBe('');
    const long = `• **${'x'.repeat(300)}**: y`;
    expect(summarizeReason(long, 40).length).toBeLessThanOrEqual(40);
  });

  it('never returns raw bold markers in plain bodies', () => {
    expect(parseReason('• no title here with **bold** inside')[0].body).toBe('no title here with bold inside');
  });
});
