import {
  Card,
  CardContent,
  GenieChat,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@databricks/appkit-ui/react';
import { CheckCircle2, ClipboardList, DollarSign, TriangleAlert } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Worklist } from './components/Worklist';
import { ChatPane, type AppealContext } from './components/ChatPane';
import { CaseFileDialog, type CaseTarget } from './components/CaseFileDialog';
import { ContentDialog, type ContentTarget } from './components/ContentDialog';
import { fetchConfig, fetchSummary, type WorklistSummary } from './lib/api';
import { formatCurrency } from './lib/formatters';

function KpiStrip({ refreshKey }: { refreshKey: number }) {
  // Keyed by refreshKey so "loading" means the stats are from an older refresh.
  const [result, setResult] = useState<{ key: number; stats: WorklistSummary | null } | null>(null);
  const loading = result?.key !== refreshKey;
  const stats = !loading && result ? result.stats : null;

  useEffect(() => {
    fetchSummary()
      .then((s) => setResult({ key: refreshKey, stats: s }))
      .catch(() => setResult({ key: refreshKey, stats: null }));
  }, [refreshKey]);

  const cards = [
    {
      label: 'Denials in worklist',
      value: stats ? stats.total.toLocaleString() : '—',
      icon: ClipboardList,
      color: 'var(--primary)',
    },
    {
      label: 'Warranted',
      value: stats ? stats.warranted.toLocaleString() : '—',
      icon: CheckCircle2,
      color: 'var(--success)',
    },
    {
      label: 'Needs review',
      value: stats ? stats.needs_review.toLocaleString() : '—',
      icon: TriangleAlert,
      color: 'var(--warning)',
    },
    {
      label: 'Expected $ (warranted)',
      value: stats ? formatCurrency(stats.warranted_expected) : '—',
      icon: DollarSign,
      color: 'var(--foreground)',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="flex items-center gap-3 p-4">
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
              style={{ backgroundColor: `color-mix(in oklab, ${c.color} 15%, transparent)` }}
            >
              <c.icon className="h-5 w-5" style={{ color: c.color }} />
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs text-muted-foreground">{c.label}</p>
              {loading ? (
                <Skeleton className="mt-1 h-6 w-16" />
              ) : (
                <p className="text-xl font-semibold text-foreground">{c.value}</p>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function App() {
  const [context, setContext] = useState<AppealContext | null>(null);
  const [contentTarget, setContentTarget] = useState<ContentTarget | null>(null);
  const [caseTarget, setCaseTarget] = useState<CaseTarget | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [genieEnabled, setGenieEnabled] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then((c) => setGenieEnabled(c.genieEnabled))
      .catch(() => setGenieEnabled(false));
  }, []);

  const bumpRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  const selectedKey = context
    ? `${context.facility_id}|${context.account}|${context.encounter_nbr}`
    : null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-4 py-4 md:px-6">
        <h1 className="text-xl font-semibold text-foreground">
          Medical-Necessity Appeals
        </h1>
        <p className="text-sm text-muted-foreground">
          Review AI-drafted appeals with their data sheets, record decisions, and ask the appeals agent.
          Worklist source: Lakebase <code className="text-xs">fe_bar_appeals.worklist_serving</code>
        </p>
      </header>

      <main className="mx-auto max-w-[1400px] space-y-4 px-4 py-6 md:px-6">
        <KpiStrip refreshKey={refreshKey} />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
          <Card>
            <CardContent className="p-4">
              <Worklist
                onSelect={setContext}
                onOpenContent={setContentTarget}
                onOpenCase={setCaseTarget}
                selectedKey={selectedKey}
                refreshKey={refreshKey}
              />
            </CardContent>
          </Card>

          {/* Sticky, viewport-height column (1440x900: top 24px + 852px height ends above the fold).
              Message lists scroll inside; the composer stays pinned at the bottom of the panel. */}
          <div className="h-[560px] lg:sticky lg:top-6 lg:h-[calc(100vh-3rem)]">
            {genieEnabled ? (
              <Tabs defaultValue="agent" className="flex h-full min-h-0 flex-col">
                <TabsList className="shrink-0">
                  <TabsTrigger value="agent">Appeals agent</TabsTrigger>
                  <TabsTrigger value="genie">Genie</TabsTrigger>
                </TabsList>
                <TabsContent value="agent" className="mt-2 flex min-h-0 flex-1 flex-col">
                  <ChatPane context={context} onClearContext={() => setContext(null)} />
                </TabsContent>
                <TabsContent value="genie" className="mt-2 flex min-h-0 flex-1 flex-col">
                  {/* GenieChat's root is flex-col h-full; it fills this column and its input is shrink-0. */}
                  <GenieChat alias="default" className="min-h-0 flex-1 overflow-hidden rounded-lg border bg-card" />
                </TabsContent>
              </Tabs>
            ) : (
              <ChatPane context={context} onClearContext={() => setContext(null)} />
            )}
          </div>
        </div>
      </main>

      {contentTarget && (
        <ContentDialog target={contentTarget} onClose={() => setContentTarget(null)} />
      )}
      {caseTarget && (
        <CaseFileDialog target={caseTarget} onClose={() => setCaseTarget(null)} onChanged={bumpRefresh} />
      )}
    </div>
  );
}
