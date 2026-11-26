import { Fragment, useMemo } from 'react';
import { diffStats, type DiffSegment } from '../lib/letterDiff';
import { parseLetterBlocks, type Inline, type LetterBlock } from '../lib/letterPreview';

// Letter-like sheet. Paper stays white in both themes so the preview reads like a printed letter.
const SHEET =
  'mx-auto w-full max-w-[44rem] rounded-sm bg-white px-10 py-8 font-serif text-[15px] leading-relaxed text-zinc-900 shadow-sm ring-1 ring-black/5';

function Inlines({ items }: { items: Inline[] }) {
  return (
    <>
      {items.map((seg) => {
        const key = `${seg.kind}-${seg.at}`;
        if (seg.kind === 'strong') return <strong key={key} className="font-bold">{seg.text}</strong>;
        if (seg.kind === 'em') return <em key={key}>{seg.text}</em>;
        return <Fragment key={key}>{seg.text}</Fragment>;
      })}
    </>
  );
}

function Block({ block }: { block: LetterBlock }) {
  switch (block.type) {
    case 'heading':
      if (block.level === 1) {
        return (
          <h3 className="mb-3 mt-6 text-xl font-bold text-zinc-950">
            <Inlines items={block.inlines} />
          </h3>
        );
      }
      if (block.level === 2) {
        return (
          <h4 className="mb-2 mt-5 text-base font-bold text-zinc-950">
            <Inlines items={block.inlines} />
          </h4>
        );
      }
      return (
        <h5 className="mb-2 mt-4 text-sm font-bold uppercase tracking-wide text-zinc-800">
          <Inlines items={block.inlines} />
        </h5>
      );
    case 're':
      // Subject line: set off with a rule so the RE block reads like a letter's subject.
      return (
        <p className="my-4 border-l-4 border-zinc-800 pl-3 font-semibold">
          <Inlines items={block.inlines} />
        </p>
      );
    case 'paragraph':
      return (
        <p className="my-3 whitespace-pre-line">
          <Inlines items={block.inlines} />
        </p>
      );
    case 'list': {
      const ListTag = block.ordered ? 'ol' : 'ul';
      return (
        <ListTag className={`my-3 space-y-1 pl-6 ${block.ordered ? 'list-decimal' : 'list-disc'}`}>
          {block.items.map((item, i) => (
            // Items come from one parsed block in fixed order and are never reordered.
            // eslint-disable-next-line react/no-array-index-key
            <li key={`${block.at}-${i}`}>
              <Inlines items={item} />
            </li>
          ))}
        </ListTag>
      );
    }
    case 'rule':
      return <hr className="my-5 border-zinc-300" />;
  }
}

/** The edited (or any) letter as a formatted preview. Markdown becomes React elements; no HTML is parsed. */
export function LetterDocument({ markdown, showLetterhead = true }: { markdown: string; showLetterhead?: boolean }) {
  const blocks = useMemo(() => parseLetterBlocks(markdown), [markdown]);
  return (
    <article className={SHEET} aria-label="Letter preview">
      {showLetterhead && (
        <div className="mb-6 flex h-14 items-center justify-center rounded border border-dashed border-zinc-300 font-sans text-[11px] uppercase tracking-wider text-zinc-400">
          Letterhead placeholder
        </div>
      )}
      {blocks.length === 0 ? (
        <p className="font-sans text-sm text-zinc-500">No letter text.</p>
      ) : (
        blocks.map((block) => <Block key={block.at} block={block} />)
      )}
    </article>
  );
}

/** Word-level inline diff: additions green and underlined, removals red and struck through. */
export function LetterChanges({ segments }: { segments: DiffSegment[] }) {
  const stats = diffStats(segments);
  const unchanged = stats.added === 0 && stats.removed === 0;
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-3 font-sans text-xs text-muted-foreground">
        <span className="rounded bg-[color-mix(in_oklab,var(--success)_28%,transparent)] px-1.5 py-0.5 text-zinc-900">
          Added
        </span>
        <span className="rounded bg-[color-mix(in_oklab,var(--destructive)_22%,transparent)] px-1.5 py-0.5 text-zinc-900 line-through">
          Removed
        </span>
        <span>
          {unchanged
            ? 'No differences from the AI draft.'
            : `+${stats.added} / −${stats.removed} words compared with the AI draft`}
        </span>
      </div>
      <article className={`${SHEET} whitespace-pre-wrap`} aria-label="Changes from the AI draft">
        {segments.map((seg) => {
          if (seg.type === 'insert') {
            return (
              <ins key={seg.at} className="rounded-sm bg-[color-mix(in_oklab,var(--success)_28%,transparent)] text-zinc-900 no-underline">
                {seg.text}
              </ins>
            );
          }
          if (seg.type === 'delete') {
            return (
              <del key={seg.at} className="rounded-sm bg-[color-mix(in_oklab,var(--destructive)_22%,transparent)] text-zinc-600">
                {seg.text}
              </del>
            );
          }
          return <Fragment key={seg.at}>{seg.text}</Fragment>;
        })}
      </article>
    </div>
  );
}
