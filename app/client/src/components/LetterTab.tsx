import { Alert, AlertDescription, Badge, Button } from '@databricks/appkit-ui/react';
import { Download, ExternalLink, GitCompareArrows } from 'lucide-react';
import { useMemo } from 'react';
import { createPortal } from 'react-dom';
import { diffText } from '../lib/letterDiff';
import { letterFileName, versionChipLabel } from '../lib/letterPreview';
import { LetterChanges, LetterDocument } from './LetterViews';

export interface EditView {
  text: string;
  version: number;
  reviewer: string | null;
  createdAt: string | null;
}

export type LetterView = 'edited' | 'original';

// Print path: the final letter is printed from a body-level copy (see #final-letter-print in index.css).
// The browser's Save as PDF uses the document title as its default file name, so the title is set to the
// letter file name for the duration of the print and restored afterwards. The original title is captured
// once (a second click mid-print must not capture the file name), and a timeout restores it if
// afterprint never fires.
let originalTitle: string | null = null;
let restoreTimer: number | undefined;
function restoreTitle() {
  if (originalTitle !== null) document.title = originalTitle;
  originalTitle = null;
  if (restoreTimer !== undefined) window.clearTimeout(restoreTimer);
  restoreTimer = undefined;
}
function printFinalLetter(fileTitle: string) {
  if (originalTitle === null) originalTitle = document.title;
  document.title = fileTitle;
  window.addEventListener('afterprint', restoreTitle, { once: true });
  restoreTimer = window.setTimeout(restoreTitle, 60_000);
  window.print();
}

export function LetterTab({
  pdfUrl,
  patientName,
  account,
  encounterNbr,
  aiDraft,
  edit,
  view,
  onViewChange,
  showChanges,
  onShowChangesChange,
  now,
}: {
  pdfUrl: string | null;
  patientName: string;
  account: string;
  encounterNbr: string;
  /** The AI draft text (appeal_letter). Baseline for the diff. */
  aiDraft: string;
  edit: EditView | null;
  view: LetterView;
  onViewChange: (view: LetterView) => void;
  showChanges: boolean;
  onShowChangesChange: (value: boolean) => void;
  now: Date;
}) {
  const changes = useMemo(
    () => (edit && showChanges && aiDraft ? diffText(aiDraft, edit.text) : null),
    [edit, showChanges, aiDraft],
  );

  const pdf = pdfUrl ? (
    <iframe src={pdfUrl} title={`Appeal letter PDF for ${patientName}`} className="h-[55vh] w-full rounded-md border bg-muted" />
  ) : (
    <Alert>
      <AlertDescription>No PDF available for this item.</AlertDescription>
    </Alert>
  );

  // No saved edit: the AI draft PDF, as before.
  if (!edit) {
    return (
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">Model-drafted. Review against the data sheet.</p>
          {pdfUrl && (
            <Button variant="outline" size="sm" onClick={() => window.open(pdfUrl, '_blank', 'noopener,noreferrer')}>
              <ExternalLink className="mr-1.5 h-4 w-4" />
              Open in new tab
            </Button>
          )}
        </div>
        {pdf}
      </div>
    );
  }

  const fileTitle = letterFileName(account, encounterNbr, edit.version).replace(/\.pdf$/i, '');
  const chip = versionChipLabel({
    version: edit.version,
    reviewer: edit.reviewer,
    createdAt: edit.createdAt,
    now,
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary" className="font-normal">
          {chip}
        </Badge>
        <div role="group" aria-label="Letter view" className="inline-flex rounded-md border p-0.5">
          <Button
            size="sm"
            variant={view === 'original' ? 'secondary' : 'ghost'}
            aria-pressed={view === 'original'}
            onClick={() => onViewChange('original')}
          >
            Original AI draft (PDF)
          </Button>
          <Button
            size="sm"
            variant={view === 'edited' ? 'secondary' : 'ghost'}
            aria-pressed={view === 'edited'}
            onClick={() => onViewChange('edited')}
          >
            Edited letter
          </Button>
        </div>
        {view === 'edited' && (
          <Button
            size="sm"
            variant={showChanges ? 'secondary' : 'outline'}
            aria-pressed={showChanges}
            disabled={!aiDraft}
            onClick={() => onShowChangesChange(!showChanges)}
          >
            <GitCompareArrows className="mr-1.5 h-4 w-4" />
            {showChanges ? 'Hide changes' : 'Show changes'}
          </Button>
        )}
        <div className="ml-auto flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => printFinalLetter(fileTitle)}>
            <Download className="mr-1.5 h-4 w-4" />
            Download final letter (PDF)
          </Button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {view === 'original'
          ? 'Showing the AI-generated draft PDF. Saved edits do not change this file.'
          : `Preview of version ${edit.version}. The AI draft PDF is kept unchanged.`}
      </p>

      {view === 'original' && pdf}
      {view === 'edited' && showChanges && !changes && (
        <Alert>
          <AlertDescription>The AI draft text is not available, so no comparison can be shown.</AlertDescription>
        </Alert>
      )}
      {view === 'edited' && showChanges && changes && <LetterChanges segments={changes} />}
      {view === 'edited' && !showChanges && (
        <div className="h-[55vh] overflow-y-auto rounded-md border bg-muted/40 p-4">
          <LetterDocument markdown={edit.text} />
        </div>
      )}

      {createPortal(
        <div id="final-letter-print">
          <LetterDocument markdown={edit.text} showLetterhead={false} />
        </div>,
        document.body,
      )}
    </div>
  );
}
