// Pure model for the formatted letter preview and the version copy. No React and no HTML here: the
// markdown from the model (or a reviewer's edit) is parsed into plain blocks and inline segments, and the
// component renders each segment as a React text node. Nothing is ever injected as HTML.

export interface Inline {
  kind: 'text' | 'strong' | 'em';
  text: string;
  /** Offset of the segment inside its parent string. Used as a stable React key. */
  at: number;
}

export type LetterBlock =
  | { type: 'heading'; level: 1 | 2 | 3; inlines: Inline[]; at: number }
  | { type: 'paragraph'; inlines: Inline[]; at: number }
  | { type: 're'; inlines: Inline[]; at: number }
  | { type: 'list'; ordered: boolean; items: Inline[][]; at: number }
  | { type: 'rule'; at: number };

// **bold**, *italic*, and [text](url). Links keep their text only; the URL is dropped so nothing is clickable.
// Underscore italics are deliberately not supported: identifiers like ENCOUNTER_NBR would be mangled.
const INLINE_RE = /\*\*([^*\n]+?)\*\*|\*([^*\n]+?)\*|!?\[([^\]\n]+)\]\(((?:[^()\s]|\([^()\s]*\))*)\)/g;

export function parseInline(src: string): Inline[] {
  const out: Inline[] = [];
  const re = new RegExp(INLINE_RE.source, 'g');
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src)) !== null) {
    if (m.index > last) out.push({ kind: 'text', text: src.slice(last, m.index), at: last });
    if (m[1] !== undefined) out.push({ kind: 'strong', text: m[1], at: m.index });
    else if (m[2] !== undefined) out.push({ kind: 'em', text: m[2], at: m.index });
    else if (m[3] !== undefined) out.push({ kind: 'text', text: m[3], at: m.index });
    last = m.index + m[0].length;
  }
  if (last < src.length) out.push({ kind: 'text', text: src.slice(last), at: last });
  return out;
}

const HEADING_RE = /^(#{1,6})\s+(.*)$/;
const RULE_RE = /^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/;
const BULLET_RE = /^\s*[-*•]\s+(.*)$/;
const ORDERED_RE = /^\s*\d+[.)]\s+(.*)$/;
// "RE:" (case-sensitive, at line start) opens the subject line; "**RE:**" is the markdown form the model writes.
const RE_LINE_RE = /^\s*(?:\*\*)?RE\s*:/;

/** Splits letter markdown into blocks. Blank lines separate blocks; single newlines inside a paragraph are kept
 *  (address lines stay on their own lines). */
export function parseLetterBlocks(markdown: string): LetterBlock[] {
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  const blocks: LetterBlock[] = [];
  let paragraph: string[] = [];
  let paragraphAt = 0;
  let list: { ordered: boolean; items: string[]; at: number } | null = null;

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    blocks.push({ type: 'paragraph', inlines: parseInline(paragraph.join('\n')), at: paragraphAt });
    paragraph = [];
  };
  const flushList = () => {
    if (!list) return;
    blocks.push({
      type: 'list',
      ordered: list.ordered,
      items: list.items.map((item) => parseInline(item)),
      at: list.at,
    });
    list = null;
  };
  const flushAll = () => {
    flushParagraph();
    flushList();
  };

  lines.forEach((line, index) => {
    if (line.trim() === '') {
      flushAll();
      return;
    }
    const heading = HEADING_RE.exec(line);
    if (heading) {
      flushAll();
      blocks.push({
        type: 'heading',
        // Levels 4-6 render as the smallest heading style instead of printing raw hashes.
        level: Math.min(heading[1].length, 3) as 1 | 2 | 3,
        inlines: parseInline(heading[2].trim()),
        at: index,
      });
      return;
    }
    if (RULE_RE.test(line)) {
      flushAll();
      blocks.push({ type: 'rule', at: index });
      return;
    }
    if (RE_LINE_RE.test(line)) {
      flushAll();
      blocks.push({ type: 're', inlines: parseInline(line.trim()), at: index });
      return;
    }
    const bullet = BULLET_RE.exec(line);
    const numbered = bullet ? null : ORDERED_RE.exec(line);
    if (bullet || numbered) {
      const ordered = numbered !== null;
      const text = (bullet ?? numbered)?.[1].trim() ?? '';
      flushParagraph();
      if (list && list.ordered !== ordered) flushList();
      if (!list) list = { ordered, items: [], at: index };
      list.items.push(text);
      return;
    }
    flushList();
    if (paragraph.length === 0) paragraphAt = index;
    paragraph.push(line.trim());
  });
  flushAll();
  return blocks;
}

/** Reads a Postgres timestamp text ("2026-11-25 20:14:03.123456+00") or an ISO string. Null when unparseable. */
export function parseTimestamp(value: string): Date | null {
  const normalized = value
    .trim()
    .replace(' ', 'T')
    .replace(/(\.\d{3})\d+/, '$1')
    .replace(/([+-]\d{2})$/, '$1:00');
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "just now", "12 min ago", "3 h ago", "2 d ago", then a short date. */
export function relativeTime(date: Date, now: Date): string {
  const sec = Math.round((now.getTime() - date.getTime()) / 1000);
  if (sec < 45) return 'just now';
  const min = Math.round(sec / 60);
  if (min < 60) return `${min} min ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr} h ago`;
  const day = Math.round(hr / 24);
  if (day < 30) return `${day} d ago`;
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export interface VersionChipInput {
  version: number;
  reviewer: string | null;
  createdAt: string | null;
  now: Date;
}

/** "Version 2 · edited by <reviewer> · 5 min ago". */
export function versionChipLabel({ version, reviewer, createdAt, now }: VersionChipInput): string {
  const when = createdAt ? parseTimestamp(createdAt) : null;
  const time = when ? relativeTime(when, now) : null;
  return [`Version ${version}`, `edited by ${reviewer ?? 'unknown'}`, time].filter(Boolean).join(' · ');
}

/** Action labels say which version they apply to. Version 0 means no saved edit: the AI draft. */
export function approveLabel(version: number): string {
  return version > 0 ? `Approve version ${version}` : 'Approve AI draft';
}

export function submitLabel(version: number): string {
  return version > 0 ? `Mark version ${version} submitted` : 'Mark AI draft submitted';
}

/** `<account>_<encounter>_letter_v<N>.pdf`. Keys are digit strings from the API; anything else is replaced. */
export function letterFileName(account: string, encounterNbr: string, version: number): string {
  const safe = (v: string) => v.replace(/[^A-Za-z0-9_-]/g, '_');
  return `${safe(account)}_${safe(encounterNbr)}_letter_v${version}.pdf`;
}
