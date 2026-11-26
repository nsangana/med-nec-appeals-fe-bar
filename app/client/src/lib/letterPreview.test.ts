import { describe, expect, it } from 'vitest';
import {
  approveLabel,
  letterFileName,
  parseInline,
  parseLetterBlocks,
  parseTimestamp,
  relativeTime,
  submitLabel,
  versionChipLabel,
  type LetterBlock,
} from './letterPreview';

const SAMPLE = [
  '# Appeal of denied claim',
  '',
  '**RE:** Claim 123, medical necessity',
  '',
  'Dear Medical Director,',
  '',
  'We request reconsideration of the denial.',
  'The patient met the criteria.',
  '',
  '## Clinical basis',
  '',
  '- **Criterion 1:** documented symptoms',
  '- Criterion 2: prior therapy failed',
  '',
  '1. First enclosure',
  '2. Second enclosure',
  '',
  '---',
  '',
  'Sincerely, [Clinic](https://example.test/clinic)',
].join('\n');

describe('parseLetterBlocks', () => {
  const blocks = parseLetterBlocks(SAMPLE);

  it('builds headings, RE block, paragraphs, lists and rules in order', () => {
    expect(blocks.map((b) => b.type)).toEqual([
      'heading',
      're',
      'paragraph', // "Dear Medical Director,"
      'paragraph', // the body paragraph
      'heading',
      'list',
      'list',
      'rule',
      'paragraph',
    ]);
  });

  it('keeps heading levels and the RE subject as its own block', () => {
    const [h1, re] = blocks;
    expect(h1).toMatchObject({ type: 'heading', level: 1 });
    expect(re.type).toBe('re');
  });

  it('keeps single newlines inside a paragraph so address lines do not merge', () => {
    const para = blocks[3];
    expect(para.type).toBe('paragraph');
    if (para.type !== 'paragraph') return;
    const text = para.inlines.map((i) => i.text).join('');
    expect(text).toBe('We request reconsideration of the denial.\nThe patient met the criteria.');
  });

  it('separates bullet and numbered lists', () => {
    const lists = blocks.filter((b): b is Extract<LetterBlock, { type: 'list' }> => b.type === 'list');
    expect(lists.map((l) => l.ordered)).toEqual([false, true]);
    expect(lists[0].items).toHaveLength(2);
    expect(lists[1].items).toHaveLength(2);
  });

  it('parses an empty letter to no blocks and never throws on odd input', () => {
    expect(parseLetterBlocks('')).toEqual([]);
    expect(parseLetterBlocks('\r\n\r\n')).toEqual([]);
    expect(() => parseLetterBlocks('**unclosed * star [link](')).not.toThrow();
  });
});

describe('parseInline', () => {
  it('splits bold and italic runs and keeps the rest as text', () => {
    expect(parseInline('a **b** c *d* e')).toEqual([
      { kind: 'text', text: 'a ', at: 0 },
      { kind: 'strong', text: 'b', at: 2 },
      { kind: 'text', text: ' c ', at: 7 },
      { kind: 'em', text: 'd', at: 10 },
      { kind: 'text', text: ' e', at: 13 },
    ]);
  });

  it('drops link URLs so nothing in the letter is clickable', () => {
    const out = parseInline('see [the form](javascript:alert(1)) now');
    expect(out.map((s) => s.text).join('')).toBe('see the form now');
    expect(out.some((s) => s.kind !== 'text')).toBe(false);
  });

  it('renders image syntax as its alt text, not a stray bang', () => {
    expect(parseInline('see ![logo](https://example.test/x.png) here').map((s) => s.text).join('')).toBe('see logo here');
  });

  it('keeps deep headings as the smallest heading level, without raw hashes', () => {
    const [block] = parseLetterBlocks('#### Deep heading');
    expect(block).toMatchObject({ type: 'heading', level: 3 });
    expect(block.type === 'heading' && block.inlines.map((i) => i.text).join('')).toBe('Deep heading');
  });

  it('does not mangle identifiers with underscores', () => {
    expect(parseInline('ENCOUNTER_NBR and FACILITY_ID')).toEqual([
      { kind: 'text', text: 'ENCOUNTER_NBR and FACILITY_ID', at: 0 },
    ]);
  });

  it('treats HTML as literal text (no markup is ever interpreted)', () => {
    const out = parseInline('<img src=x onerror=alert(1)>');
    expect(out).toEqual([{ kind: 'text', text: '<img src=x onerror=alert(1)>', at: 0 }]);
  });
});

describe('version copy', () => {
  const now = new Date('2026-11-25T20:30:00Z');

  it('builds the chip with version, reviewer and relative time', () => {
    expect(
      versionChipLabel({ version: 2, reviewer: 'reviewer@example.test', createdAt: '2026-11-25 20:25:00.123456+00', now }),
    ).toBe('Version 2 · edited by reviewer@example.test · 5 min ago');
  });

  it('falls back to unknown reviewer and drops the time when it is missing', () => {
    expect(versionChipLabel({ version: 1, reviewer: null, createdAt: null, now })).toBe(
      'Version 1 · edited by unknown',
    );
  });

  it('labels approve and submit with the version they apply to', () => {
    expect(approveLabel(3)).toBe('Approve version 3');
    expect(submitLabel(3)).toBe('Mark version 3 submitted');
    expect(approveLabel(0)).toBe('Approve AI draft');
    expect(submitLabel(0)).toBe('Mark AI draft submitted');
  });

  it('names the final letter file with account, encounter and version', () => {
    expect(letterFileName('1234567', '987654', 2)).toBe('1234567_987654_letter_v2.pdf');
    expect(letterFileName('12/3', 'a b', 1)).toBe('12_3_a_b_letter_v1.pdf');
  });
});

describe('relativeTime and parseTimestamp', () => {
  const now = new Date('2026-11-25T12:00:00Z');
  it('steps through seconds, minutes, hours, days, then a date', () => {
    expect(relativeTime(new Date('2026-11-25T11:59:30Z'), now)).toBe('just now');
    expect(relativeTime(new Date('2026-11-25T11:30:00Z'), now)).toBe('30 min ago');
    expect(relativeTime(new Date('2026-11-25T09:00:00Z'), now)).toBe('3 h ago');
    expect(relativeTime(new Date('2026-11-23T12:00:00Z'), now)).toBe('2 d ago');
    expect(relativeTime(new Date('2026-06-01T12:00:00Z'), now)).toMatch(/Jun 1, 2026/);
  });

  it('parses Postgres text timestamps and returns null for garbage', () => {
    expect(parseTimestamp('2026-11-25 10:00:00.999999+00')?.toISOString()).toBe('2026-11-25T10:00:00.999Z');
    expect(parseTimestamp('not a date')).toBeNull();
  });
});
