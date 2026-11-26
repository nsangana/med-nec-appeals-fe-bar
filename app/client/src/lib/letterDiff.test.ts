import { describe, expect, it } from 'vitest';
import { diffStats, diffText, diffTokens, tokenize, type DiffSegment } from './letterDiff';

const join = (segs: DiffSegment[], keep: Array<DiffSegment['type']>) =>
  segs.filter((s) => keep.includes(s.type)).map((s) => s.text).join('');

describe('tokenize', () => {
  it('splits words with their leading spaces and keeps newlines as tokens', () => {
    expect(tokenize('Dear  Sir,\nThe claim')).toEqual(['Dear', '  Sir,', '\n', 'The', ' claim']);
  });

  it('reconstructs the input exactly, including trailing spaces and blank lines', () => {
    const samples = ['  lead', 'trail  ', 'a\n\n b\r\n c', '', '   '];
    for (const s of samples) expect(tokenize(s).join('')).toBe(s);
  });
});

describe('diffText', () => {
  it('returns one equal segment when nothing changed', () => {
    const segs = diffText('Same letter.', 'Same letter.');
    expect(segs).toEqual([{ type: 'equal', text: 'Same letter.', at: 0 }]);
  });

  it('marks a word replacement as one delete and one insert', () => {
    const segs = diffText('The claim is denied.', 'The claim is approved.');
    expect(segs.filter((s) => s.type === 'delete').map((s) => s.text)).toEqual([' denied.']);
    expect(segs.filter((s) => s.type === 'insert').map((s) => s.text)).toEqual([' approved.']);
    expect(join(segs, ['equal'])).toBe('The claim is');
  });

  it('shows pure insertions and deletions', () => {
    const added = diffText('Line one.', 'Line one. Line two.');
    expect(added.some((s) => s.type === 'insert' && s.text.includes('Line two.'))).toBe(true);
    expect(added.some((s) => s.type === 'delete')).toBe(false);

    const removed = diffText('Keep this. Drop this.', 'Keep this.');
    expect(removed.some((s) => s.type === 'delete' && s.text.includes('Drop this.'))).toBe(true);
    expect(removed.some((s) => s.type === 'insert')).toBe(false);
  });

  it('reproduces both inputs from its segments (property check on mixed edits)', () => {
    const before = 'Dear Payer,\n\nWe appeal the denial of claim 123.\n\nSincerely, Team';
    const after = 'Dear Payer,\n\nWe formally appeal the denial of claim 456 for review.\n\nRegards, Team';
    const segs = diffText(before, after);
    expect(join(segs, ['equal', 'delete'])).toBe(before);
    expect(join(segs, ['equal', 'insert'])).toBe(after);
  });

  it('gives every segment a running offset for stable keys', () => {
    const segs = diffText('a b c d', 'a x c y');
    let expected = 0;
    for (const s of segs) {
      expect(s.at).toBe(expected);
      expected += s.text.length;
    }
  });

  it('falls back to one replacement for very large rewrites instead of a huge table', () => {
    const before = Array.from({ length: 3000 }, (_, i) => `old${i}`).join(' ');
    const after = Array.from({ length: 3000 }, (_, i) => `new${i}`).join(' ');
    const segs = diffTokens(tokenize(before), tokenize(after));
    expect(join(segs, ['equal', 'delete'])).toBe(before);
    expect(join(segs, ['equal', 'insert'])).toBe(after);
  });
});

describe('diffStats', () => {
  it('counts changed words, not whitespace', () => {
    const segs = diffText('The claim is denied today.', 'The claim is approved on appeal today.');
    expect(diffStats(segs)).toEqual({ added: 3, removed: 1 });
  });

  it('is zero for identical text', () => {
    expect(diffStats(diffText('x y', 'x y'))).toEqual({ added: 0, removed: 0 });
  });
});
