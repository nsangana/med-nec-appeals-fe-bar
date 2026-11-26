import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
  useAnalyticsQuery,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { CheckCircle2, ExternalLink, FolderOpen, Send, ShieldAlert, Undo2, Save } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import {
  fetchCase,
  postReviewAction,
  type CaseDetail,
  type ReviewActionName,
} from '../lib/api';
import { formatCurrency, formatDate } from '../lib/formatters';
import { RecommendationBadge } from './RecommendationBadge';
import { parseReason } from '../lib/reason';
import { firstRow, stringField } from '../lib/rows';
import { approveLabel, submitLabel } from '../lib/letterPreview';
import { LetterTab, type EditView, type LetterView } from './LetterTab';

export interface CaseTarget {
  facility_id: string;
  account: string;
  encounter_nbr: string;
  patient_name: string;
}

// Full NEEDS REVIEW reason as a list. Text nodes only; no HTML from the model.
function ReasonList({ text }: { text: string }) {
  const items = parseReason(text);
  return (
    <div className="max-h-40 w-full overflow-y-auto break-words rounded-md border bg-muted/40 p-3 text-sm">
      <p className="mb-2 font-medium text-foreground">
        Why this needs review ({items.length} item{items.length === 1 ? '' : 's'})
      </p>
      <ul className="list-disc space-y-2 pl-5">
        {items.map((it) => (
          <li key={`${it.title ?? ''}|${it.body.slice(0, 60)}`} className="break-words">
            {it.title && <strong className="font-semibold text-foreground">{it.title}: </strong>}
            <span className="text-muted-foreground">{it.body}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// The case file puts the three documents for one claim side by side in one view:
// the appeal letter, the deterministic data sheet (rule-built, reproducible), and the AI reasoning worksheet.
export function CaseFileDialog({
  target,
  onClose,
  onChanged,
}: {
  target: CaseTarget;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [draftTouched, setDraftTouched] = useState(false);
  const [busy, setBusy] = useState<ReviewActionName | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<string | null>(null);
  // Letter tab state. The preview shows the latest saved edit by default.
  const [letterView, setLetterView] = useState<LetterView>('edited');
  const [showChanges, setShowChanges] = useState(false);
  // Shown the moment Save edit is clicked, before the re-read confirms it.
  const [optimisticEdit, setOptimisticEdit] = useState<EditView | null>(null);
  const [now, setNow] = useState<Date>(() => new Date());

  const keyParams = useMemo(
    () => ({
      facility_id: sql.string(target.facility_id),
      account: sql.string(target.account),
      encounter_nbr: sql.string(target.encounter_nbr),
    }),
    [target.facility_id, target.account, target.encounter_nbr],
  );
  const { data: contentRows } = useAnalyticsQuery('appeal_content', keyParams);
  const letterText = stringField(firstRow(contentRows), 'appeal_letter');

  const key = useMemo(
    () => ({ facility_id: target.facility_id, account: target.account, encounter_nbr: target.encounter_nbr }),
    [target.facility_id, target.account, target.encounter_nbr],
  );

  useEffect(() => {
    let cancelled = false;
    fetchCase(key)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Unknown error');
      });
    return () => {
      cancelled = true;
    };
  }, [key]);

  // Seed the editor once with the latest saved edit, else the generated letter.
  useEffect(() => {
    if (draftTouched) return;
    const saved = detail?.review.latest_edit?.edited_letter;
    if (saved) setDraft(saved);
    else if (letterText) setDraft(letterText);
  }, [detail, letterText, draftTouched]);

  const item = detail?.item;
  const status = lastResult ?? detail?.review.status_label ?? '';

  // The saved edit (from Lakebase), or the optimistic copy while a save is in flight.
  const latest = detail?.review.latest_edit ?? null;
  const savedEdit: EditView | null = latest?.edited_letter
    ? {
        text: latest.edited_letter,
        version: latest.version,
        reviewer: latest.reviewer,
        createdAt: latest.created_at,
      }
    : null;
  const edit = optimisticEdit ?? savedEdit;
  const version = edit?.version ?? 0;

  async function act(action: ReviewActionName) {
    const isEdit = action === 'EDIT';
    setBusy(action);
    setActionError(null);
    if (isEdit) {
      setOptimisticEdit({
        text: draft,
        version: (savedEdit?.version ?? 0) + 1,
        reviewer: 'you',
        createdAt: new Date().toISOString(),
      });
      setLetterView('edited');
    }
    try {
      const res = await postReviewAction(key, action, isEdit ? { edited_letter: draft } : {});
      setLastResult(res.status_label);
      // Keep the editor's text as saved: draftTouched stays true, so the seed effect does not overwrite it.
      onChanged();
      // Re-read so history and the saved-edit view stay in sync with Lakebase.
      fetchCase(key)
        .then((d) => {
          setDetail(d);
          setOptimisticEdit(null);
          setNow(new Date());
        })
        .catch(() => {
          // The save succeeded; only the refresh failed. The optimistic copy stays as the saved text.
          setActionError('Saved, but the case could not be refreshed. Reopen the case to confirm the latest version.');
        });
    } catch (err) {
      setOptimisticEdit(null);
      setActionError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusy(null);
    }
  }

  const docs: Array<{ key: string; title: string; note: string; url: string | null | undefined }> = [
    {
      key: 'letter',
      title: 'Appeal letter',
      note: 'Model-drafted. Review against the data sheet.',
      url: detail?.files.letter.url,
    },
    {
      key: 'data_sheet',
      title: 'Data sheet',
      note: 'Rule-built from the source rows. Same inputs every run.',
      url: detail?.files.data_sheet.url,
    },
    {
      key: 'ai_worksheet',
      title: 'AI reasoning worksheet',
      note: 'AI reasoning (model-generated, not verified).',
      url: detail?.files.ai_worksheet.url,
    },
  ];

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      {/* Base DialogContent caps width with sm:max-w-lg, so the override must also be sm:-prefixed.
          Fixed header + footer, scrolling body; capped at 92vh so it always fits the window. */}
      <DialogContent className="flex max-h-[92vh] w-[96vw] flex-col gap-3 overflow-hidden sm:max-w-6xl">
        <DialogHeader className="shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-primary" />
            Case file — {target.patient_name}
          </DialogTitle>
          <DialogDescription>
            Account {target.account} · Encounter {target.encounter_nbr} · documents from the Unity Catalog volume
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {loadError && (
          <Alert variant="destructive">
            <AlertDescription>Failed to load case: {loadError}</AlertDescription>
          </Alert>
        )}

        {!detail && !loadError && <Skeleton className="h-16 w-full" />}

        {item && item.recommendation === 'NEEDS REVIEW' && item.needs_review_reason && (
          <ReasonList text={item.needs_review_reason} />
        )}

        {item && (
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <RecommendationBadge recommendation={item.recommendation} />
            <Badge variant="outline">{item.worklist_tag.replace('_', ' ')}</Badge>
            <span>
              Expected {formatCurrency(item.expected_reimbursement)} · Appeal deadline {formatDate(item.appeal_deadline)}
              {item.days_remaining !== null && ` (${item.days_remaining < 0 ? 'past due' : `${item.days_remaining} days left`})`}
            </span>
            <span className="ml-auto text-muted-foreground">Review status: {status || 'Not started'}</span>
          </div>
        )}

        {/* The three documents as tabs: one PDF viewer at a time avoids nested scroll traps. */}
        <Tabs defaultValue="letter" className="w-full">
          <TabsList>
            {docs.map((d) => (
              <TabsTrigger key={d.key} value={d.key}>
                {d.title}
              </TabsTrigger>
            ))}
          </TabsList>
          {docs.map((d) => (
            <TabsContent key={d.key} value={d.key} className="space-y-2">
              {d.key === 'letter' ? (
                <LetterTab
                  pdfUrl={d.url ?? null}
                  patientName={target.patient_name}
                  account={target.account}
                  encounterNbr={target.encounter_nbr}
                  aiDraft={letterText}
                  edit={edit}
                  view={letterView}
                  onViewChange={setLetterView}
                  showChanges={showChanges}
                  onShowChangesChange={setShowChanges}
                  now={now}
                />
              ) : (
                <>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs text-muted-foreground">{d.note}</p>
                    {d.url && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(d.url ?? '', '_blank', 'noopener,noreferrer')}
                      >
                        <ExternalLink className="mr-1.5 h-4 w-4" />
                        Open in new tab
                      </Button>
                    )}
                  </div>
                  {d.url ? (
                    <iframe
                      src={d.url}
                      title={`${d.title} for ${target.patient_name}`}
                      className="h-[55vh] w-full rounded-md border bg-muted"
                    />
                  ) : (
                    <Alert>
                      <AlertDescription>No PDF available for this item.</AlertDescription>
                    </Alert>
                  )}
                </>
              )}
            </TabsContent>
          ))}
        </Tabs>

        {/* Reviewer edit + decision. Writes are append-only events in Lakebase review_actions. */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-foreground">Letter edit</p>
          <Textarea
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value);
              setDraftTouched(true);
            }}
            rows={8}
            className="h-48 max-h-48 resize-y overflow-y-auto [field-sizing:fixed] font-mono text-xs"
            placeholder="Edit the appeal letter text, then save the edit."
          />
          {detail?.review.latest_edit && (
            <p className="text-xs text-muted-foreground">
              Last edit by {detail.review.latest_edit.reviewer ?? 'unknown'}
              {detail.review.latest_edit.created_at ? ` on ${formatDate(detail.review.latest_edit.created_at)}` : ''}
            </p>
          )}
          {actionError && (
            <Alert variant="destructive">
              <AlertDescription>{actionError}</AlertDescription>
            </Alert>
          )}
        </div>
        </div>

        <DialogFooter className="shrink-0 flex-col items-stretch gap-2 border-t pt-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-start">
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={busy !== null || !draft.trim()} onClick={() => void act('EDIT')}>
              <Save className="mr-1.5 h-4 w-4" />
              {busy === 'EDIT' ? 'Saving…' : 'Save edit'}
            </Button>
            <Button disabled={busy !== null} onClick={() => void act('APPROVE')}>
              <CheckCircle2 className="mr-1.5 h-4 w-4" />
              {approveLabel(version)}
            </Button>
            <Button variant="outline" disabled={busy !== null} onClick={() => void act('REJECT')}>
              <Undo2 className="mr-1.5 h-4 w-4" />
              Reject
            </Button>
            <Button variant="outline" disabled={busy !== null} onClick={() => void act('ROUTE_TO_REVIEW')}>
              <ShieldAlert className="mr-1.5 h-4 w-4" />
              Route to review
            </Button>
            <Button variant="outline" disabled={busy !== null} onClick={() => void act('SUBMIT')}>
              <Send className="mr-1.5 h-4 w-4" />
              {submitLabel(version)}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {version > 0
              ? `Approve and Mark submitted apply to version ${version}, the latest saved edit.`
              : 'Approve and Mark submitted apply to the AI draft. No edit is saved yet.'}
          </p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
