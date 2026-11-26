// needs_review_reason is model-written markdown: "• **Title**: explanation" bullets separated by blank lines
// (sometimes a plain sentence such as "PARSE_FAILURE: ..."). These helpers turn it into plain data that React
// renders as text nodes. Nothing is injected as HTML.

export interface ReasonItem {
  title: string | null;
  body: string;
}

/** Splits the reason into bullets. A reason without bullets is one item with no title. */
export function parseReason(text: string | null | undefined): ReasonItem[] {
  if (!text) return [];
  const pieces = text
    .split(/\n\s*\n|\n(?=•)|(?=•)/)
    .map((p) => p.replace(/^\s*•\s*/, '').trim())
    .filter((p) => p.length > 0);
  if (pieces.length === 0) return [];

  return pieces.map((piece) => {
    const bold = /^\*\*(.+?)\*\*\s*:?\s*([\s\S]*)$/.exec(piece);
    if (bold) return { title: bold[1].trim(), body: bold[2].trim() };
    return { title: null, body: piece.replace(/\*\*/g, '') };
  });
}

/** One line for the worklist cell: "8 open items · <first title>". */
export function summarizeReason(text: string | null | undefined, maxLength = 110): string {
  const items = parseReason(text);
  if (items.length === 0) return '';
  const first = items[0].title ?? items[0].body;
  const head = items.length > 1 ? `${items.length} open items · ${first}` : first;
  return head.length > maxLength ? `${head.slice(0, maxLength - 1).trimEnd()}…` : head;
}
