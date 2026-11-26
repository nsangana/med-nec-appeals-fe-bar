import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@databricks/appkit-ui/react';
import { ChevronLeft, ChevronRight, FileText, FolderOpen, Inbox, Search, ScrollText } from 'lucide-react';
import { useEffect, useState } from 'react';
import { fetchWorklist, type WorklistItem, type WorklistSummary } from '../lib/api';
import { formatCurrency, formatDate } from '../lib/formatters';
import { summarizeReason } from '../lib/reason';
import {
  countForFilter,
  formatChipLabel,
  hasActiveFilters,
  minExpectedFor,
  RECOMMENDATION_FILTERS,
  type RecommendationFilter,
} from '../lib/worklistQuery';
import { RecommendationBadge } from './RecommendationBadge';
import type { AppealContext } from './ChatPane';
import type { ContentTarget } from './ContentDialog';
import type { CaseTarget } from './CaseFileDialog';

const PAGE_SIZE = 10;
const SKELETON_KEYS = Array.from({ length: PAGE_SIZE }, (_, i) => `skeleton-${i}`);

type SortKey = 'priority' | 'dos_desc' | 'dos_asc' | 'account_desc' | 'account_asc' | 'expected_desc';

const REVIEW_LABEL: Record<string, string> = {
  EDIT: 'Edited',
  APPROVE: 'Approved',
  REJECT: 'Rejected',
  ROUTE_TO_REVIEW: 'Routed to review',
  SUBMIT: 'Submitted',
};

function rowKey(r: { facility_id: string; account: string; encounter_nbr: string }) {
  return `${r.facility_id}|${r.account}|${r.encounter_nbr}`;
}

// Worklist tag chips. NEW = denied yesterday (the nightly run's new arrivals).
function TagChip({ tag }: { tag: string }) {
  const style =
    tag === 'NEW'
      ? { backgroundColor: 'var(--primary)', color: 'var(--primary-foreground)' }
      : tag === 'PAST_DUE'
        ? { backgroundColor: 'var(--destructive)', color: 'var(--destructive-foreground)' }
        : tag === 'AT_RISK'
          ? { backgroundColor: 'var(--warning)', color: 'var(--warning-foreground)' }
          : undefined;
  return (
    <Badge variant={style ? undefined : 'outline'} className="border-transparent" style={style}>
      {tag.replace('_', ' ')}
    </Badge>
  );
}

export function Worklist({
  onSelect,
  onOpenContent,
  onOpenCase,
  selectedKey,
  refreshKey,
  counts,
}: {
  onSelect: (ctx: AppealContext) => void;
  onOpenContent: (target: ContentTarget) => void;
  onOpenCase: (target: CaseTarget) => void;
  selectedKey: string | null;
  refreshKey: number;
  /** Summary from the parent (shared with the KPI strip); null while loading or unavailable. */
  counts: WorklistSummary | null;
}) {
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('priority');
  const [recommendation, setRecommendation] = useState<RecommendationFilter>('ALL');
  const [highValueOnly, setHighValueOnly] = useState(false);
  const [page, setPage] = useState(0);
  const minExpected = minExpectedFor(highValueOnly);
  const filtered = hasActiveFilters({ search, recommendation, highValueOnly });
  // The fetched page is keyed by its request, so "loading" is simply "the result is for an older request".
  const requestKey = `${search}|${sortKey}|${recommendation}|${minExpected}|${page}|${refreshKey}`;
  const [result, setResult] = useState<{ key: string; items: WorklistItem[]; total: number; error: string | null } | null>(null);
  const loading = result?.key !== requestKey;
  const items = !loading && result ? result.items : [];
  const total = !loading && result ? result.total : 0;
  const error = !loading && result ? result.error : null;

  // Debounce the search box so we don't refetch on every keystroke.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  // Fetch the page from the app's Lakebase-backed route. Re-runs on filter change and after review actions.
  useEffect(() => {
    const controller = new AbortController();
    fetchWorklist(
      { search, sort: sortKey, page, page_size: PAGE_SIZE, recommendation, min_expected: minExpected },
      controller.signal,
    )
      .then((data) => {
        setResult({ key: requestKey, items: data.items, total: data.total, error: null });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setResult({
          key: requestKey,
          items: [],
          total: 0,
          error: err instanceof Error ? err.message : 'Unknown error',
        });
      });
    return () => controller.abort();
    // requestKey encodes search/sortKey/page/refreshKey
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestKey]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const rangeEnd = page * PAGE_SIZE + items.length;

  // Every filter change goes back to the first page so the user never lands on an empty page.
  const selectRecommendation = (value: RecommendationFilter) => {
    setRecommendation(value);
    setPage(0);
  };
  const toggleHighValue = () => {
    setHighValueOnly((v) => !v);
    setPage(0);
  };
  const clearFilters = () => {
    setSearchInput('');
    setSearch('');
    setRecommendation('ALL');
    setHighValueOnly(false);
    setPage(0);
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Controls */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-xs">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              setPage(0);
            }}
            placeholder="Search account, patient, or denial code…"
            className="pl-8"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Sort by</span>
          <Select
            value={sortKey}
            onValueChange={(v) => {
              setSortKey(v as SortKey);
              setPage(0);
            }}
          >
            <SelectTrigger className="w-[220px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="priority">Priority (NEW first)</SelectItem>
              <SelectItem value="dos_desc">Date of service (newest)</SelectItem>
              <SelectItem value="dos_asc">Date of service (oldest)</SelectItem>
              <SelectItem value="account_desc">Account (high → low)</SelectItem>
              <SelectItem value="account_asc">Account (low → high)</SelectItem>
              <SelectItem value="expected_desc">Expected $ (high → low)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Filter chips: one row, wraps on narrow widths. aria-pressed marks the active chip for screen readers. */}
      <div role="group" aria-label="Filter appeals" className="flex flex-wrap items-center gap-2">
        {RECOMMENDATION_FILTERS.map((f) => {
          const active = recommendation === f.value;
          return (
            <Button
              key={f.value}
              type="button"
              size="sm"
              variant={active ? 'default' : 'outline'}
              aria-pressed={active}
              className="rounded-full"
              onClick={() => selectRecommendation(f.value)}
            >
              {formatChipLabel(f.label, countForFilter(counts, f.value))}
            </Button>
          );
        })}
        <Button
          type="button"
          size="sm"
          variant={highValueOnly ? 'default' : 'outline'}
          aria-pressed={highValueOnly}
          className="rounded-full"
          onClick={toggleHighValue}
        >
          ≥ $10K expected
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load worklist: {error}</AlertDescription>
        </Alert>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Priority</TableHead>
              <TableHead>Tag</TableHead>
              <TableHead>Account</TableHead>
              <TableHead>Patient</TableHead>
              <TableHead>Date of Service</TableHead>
              <TableHead>Days left</TableHead>
              <TableHead className="text-right">Expected $</TableHead>
              <TableHead>Denial</TableHead>
              <TableHead>Payer</TableHead>
              <TableHead>Recommendation</TableHead>
              <TableHead>Review</TableHead>
              <TableHead className="text-right">Documents</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading &&
              SKELETON_KEYS.map((k) => (
                <TableRow key={k}>
                  <TableCell colSpan={12}>
                    <Skeleton className="h-6 w-full" />
                  </TableCell>
                </TableRow>
              ))}

            {!loading &&
              items.map((row) => {
                const key = rowKey(row);
                const isSelected = key === selectedKey;
                const hasLetter = Boolean(row.letter_pdf_path);
                const reviewLabel = row.review_status ? (REVIEW_LABEL[row.review_status] ?? row.review_status) : 'Not started';
                return (
                  <TableRow
                    key={key}
                    onClick={() =>
                      onSelect({
                        facility_id: row.facility_id,
                        account: row.account,
                        encounter_nbr: row.encounter_nbr,
                        patient_name: row.patient_name,
                      })
                    }
                    className={`cursor-pointer ${isSelected ? 'bg-accent' : ''}`}
                  >
                    <TableCell className="font-medium">{row.priority_rank ?? '—'}</TableCell>
                    <TableCell>
                      <TagChip tag={row.worklist_tag} />
                    </TableCell>
                    <TableCell className="font-medium">{row.account}</TableCell>
                    <TableCell>{row.patient_name}</TableCell>
                    <TableCell className="whitespace-nowrap">{formatDate(row.dos)}</TableCell>
                    <TableCell className="whitespace-nowrap">
                      {row.days_remaining === null ? '—' : row.days_remaining < 0 ? 'Past due' : `${row.days_remaining} d`}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-right">{formatCurrency(row.expected_reimbursement)}</TableCell>
                    <TableCell>{row.denial_code}</TableCell>
                    <TableCell className="max-w-[200px] truncate" title={row.payer_name}>
                      {row.payer_name}
                    </TableCell>
                    <TableCell className="max-w-[240px]">
                      <div className="flex flex-col items-start gap-1">
                        <RecommendationBadge recommendation={row.recommendation} />
                        {row.recommendation === 'NEEDS REVIEW' && row.needs_review_reason && (
                          // One-line summary; the full reason is in the case file and the hover title.
                          <span
                            className="line-clamp-2 break-words whitespace-normal text-xs text-muted-foreground"
                            title={row.needs_review_reason}
                          >
                            {summarizeReason(row.needs_review_reason)}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      <div className="flex flex-col">
                        <span>{reviewLabel}</span>
                        {row.last_reviewer && (
                          <span className="text-xs text-muted-foreground">{row.last_reviewer}</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenCase({
                              facility_id: row.facility_id,
                              account: row.account,
                              encounter_nbr: row.encounter_nbr,
                              patient_name: row.patient_name,
                            });
                          }}
                        >
                          <FolderOpen className="mr-1 h-3.5 w-3.5" />
                          Case file
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={!hasLetter}
                          title={hasLetter ? 'Open the appeal letter' : 'No appeal letter (NOT WARRANTED)'}
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenContent({
                              type: 'letter',
                              facility_id: row.facility_id,
                              account: row.account,
                              encounter_nbr: row.encounter_nbr,
                              patient_name: row.patient_name,
                              pdfPath: row.letter_pdf_path ?? '',
                            });
                          }}
                        >
                          <FileText className="mr-1 h-3.5 w-3.5" />
                          Letter
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={!row.cheat_sheet_pdf_path}
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenContent({
                              type: 'cheatsheet',
                              facility_id: row.facility_id,
                              account: row.account,
                              encounter_nbr: row.encounter_nbr,
                              patient_name: row.patient_name,
                              pdfPath: row.cheat_sheet_pdf_path ?? '',
                            });
                          }}
                        >
                          <ScrollText className="mr-1 h-3.5 w-3.5" />
                          AI worksheet
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}

            {!loading && !error && items.length === 0 && (
              <TableRow>
                <TableCell colSpan={12}>
                  <Empty>
                    <EmptyHeader>
                      <EmptyMedia variant="icon">
                        <Inbox className="h-6 w-6" />
                      </EmptyMedia>
                      <EmptyTitle>{filtered ? 'No appeals match these filters' : 'No appeals found'}</EmptyTitle>
                      <EmptyDescription>
                        {filtered
                          ? 'Try a different filter, search term, or expected-$ threshold.'
                          : 'There are no appeals to review.'}
                      </EmptyDescription>
                    </EmptyHeader>
                    {filtered && (
                      <EmptyContent>
                        <Button variant="outline" size="sm" onClick={clearFilters}>
                          Clear filters
                        </Button>
                      </EmptyContent>
                    )}
                  </Empty>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {total === 0 ? 'No results' : `Showing ${rangeStart}–${rangeEnd} of ${total} appeals`}
        </p>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled={page === 0 || loading} onClick={() => setPage((p) => Math.max(0, p - 1))}>
            <ChevronLeft className="h-4 w-4" />
            Prev
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= totalPages || loading}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
