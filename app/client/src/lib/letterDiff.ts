// Word-level diff between the AI draft and the latest edit. A small LCS over tokens, no dependency.
// Tokens are words (with their leading spaces) and newlines, so concatenating the tokens reproduces the
// input exactly and paragraph breaks survive into the diff view.

export type DiffType = 'equal' | 'insert' | 'delete';

export interface DiffSegment {
  type: DiffType;
  text: string;
  /** Running offset in the output, used as a stable React key. */
  at: number;
}

export interface DiffStats {
  added: number;
  removed: number;
}

/** Above this many table cells the middle is shown as one replacement instead of an LCS (memory guard). */
const MAX_LCS_CELLS = 6_000_000;

export function tokenize(text: string): string[] {
  return text.match(/\n|[^\S\n]*\S+|[^\S\n]+/g) ?? [];
}

/** Diffs two token lists. Concatenating the `equal` and `delete` segments gives `a`; `equal` and `insert` give `b`. */
export function diffTokens(a: string[], b: string[]): DiffSegment[] {
  let start = 0;
  while (start < a.length && start < b.length && a[start] === b[start]) start++;
  let endA = a.length;
  let endB = b.length;
  while (endA > start && endB > start && a[endA - 1] === b[endB - 1]) {
    endA--;
    endB--;
  }

  const ops: Array<{ type: DiffType; text: string }> = [];
  const push = (type: DiffType, tokens: string[]) => {
    if (tokens.length > 0) ops.push({ type, text: tokens.join('') });
  };

  push('equal', a.slice(0, start));
  const midA = a.slice(start, endA);
  const midB = b.slice(start, endB);
  if (midA.length * midB.length > MAX_LCS_CELLS) {
    push('delete', midA);
    push('insert', midB);
  } else {
    lcsOps(midA, midB, push);
  }
  push('equal', a.slice(endA));

  // Merge neighbouring ops of the same type and stamp offsets.
  const segments: DiffSegment[] = [];
  let at = 0;
  for (const op of ops) {
    const prev = segments[segments.length - 1];
    if (prev && prev.type === op.type) {
      prev.text += op.text;
    } else {
      segments.push({ type: op.type, text: op.text, at });
    }
    at += op.text.length;
  }
  return segments;
}

function lcsOps(a: string[], b: string[], push: (type: DiffType, tokens: string[]) => void) {
  const n = a.length;
  const m = b.length;
  const w = m + 1;
  // table[i * w + j] = LCS length of a[i..] and b[j..]
  const table = new Uint32Array((n + 1) * w);
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      table[i * w + j] =
        a[i] === b[j]
          ? table[(i + 1) * w + (j + 1)] + 1
          : Math.max(table[(i + 1) * w + j], table[i * w + (j + 1)]);
    }
  }
  let i = 0;
  let j = 0;
  let eq: string[] = [];
  let del: string[] = [];
  let ins: string[] = [];
  const flush = () => {
    if (del.length) push('delete', del);
    if (ins.length) push('insert', ins);
    del = [];
    ins = [];
  };
  while (i < n || j < m) {
    if (i < n && j < m && a[i] === b[j]) {
      if (del.length || ins.length) {
        flush();
      }
      eq.push(a[i]);
      i++;
      j++;
      continue;
    }
    if (eq.length) {
      push('equal', eq);
      eq = [];
    }
    if (j >= m || (i < n && table[(i + 1) * w + j] >= table[i * w + (j + 1)])) {
      del.push(a[i]);
      i++;
    } else {
      ins.push(b[j]);
      j++;
    }
  }
  if (eq.length) push('equal', eq);
  flush();
}

export function diffText(before: string, after: string): DiffSegment[] {
  return diffTokens(tokenize(before), tokenize(after));
}

/** Counts changed words (non-blank tokens) for the legend. */
export function diffStats(segments: DiffSegment[]): DiffStats {
  let added = 0;
  let removed = 0;
  for (const seg of segments) {
    const words = seg.text.split(/\s+/).filter((w) => w.length > 0).length;
    if (seg.type === 'insert') added += words;
    if (seg.type === 'delete') removed += words;
  }
  return { added, removed };
}
