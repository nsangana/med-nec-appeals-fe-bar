import {
  Alert,
  AlertDescription,
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
  useAnalyticsQuery,
} from '@databricks/appkit-ui/react';
import { sql } from '@databricks/appkit-ui/js';
import { Download, ExternalLink, FileText } from 'lucide-react';
import { useMemo } from 'react';
import { fileBasename } from '../lib/formatters';
import { firstRow, stringField } from '../lib/rows';

export interface ContentTarget {
  type: 'letter' | 'cheatsheet';
  facility_id: string;
  account: string;
  encounter_nbr: string;
  patient_name: string;
  pdfPath: string;
}

export function ContentDialog({
  target,
  onClose,
}: {
  target: ContentTarget;
  onClose: () => void;
}) {
  const label = target.type === 'letter' ? 'Appeal Letter' : 'Cheat Sheet';
  const filename = fileBasename(target.pdfPath);
  const pdfUrl = filename
    ? `/api/files/files/raw?path=${encodeURIComponent(filename)}`
    : null;
  const downloadUrl = filename
    ? `/api/files/files/download?path=${encodeURIComponent(filename)}`
    : null;

  const params = useMemo(
    () => ({
      facility_id: sql.string(target.facility_id),
      account: sql.string(target.account),
      encounter_nbr: sql.string(target.encounter_nbr),
    }),
    [target.facility_id, target.account, target.encounter_nbr],
  );

  const { data, loading, error } = useAnalyticsQuery('appeal_content', params);
  const row = firstRow(data);
  const markdown = stringField(row, target.type === 'letter' ? 'appeal_letter' : 'cheat_sheet');

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="flex max-h-[92vh] w-[96vw] flex-col gap-3 overflow-hidden sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            {label} — {target.patient_name}
          </DialogTitle>
          <DialogDescription>
            Account {target.account} · Encounter {target.encounter_nbr} · served from the
            Unity Catalog volume
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="document" className="min-h-0 w-full flex-1">
          <TabsList>
            <TabsTrigger value="document">Document (PDF)</TabsTrigger>
            <TabsTrigger value="text">Text</TabsTrigger>
          </TabsList>

          <TabsContent value="document">
            {pdfUrl ? (
              <iframe
                src={pdfUrl}
                title={`${label} PDF for ${target.patient_name}`}
                className="h-[62vh] w-full rounded-md border bg-muted"
              />
            ) : (
              <Alert>
                <AlertDescription>No PDF available for this item.</AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="text">
            <div className="h-[62vh] overflow-y-auto rounded-md border bg-muted/40 p-4">
              {loading && (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              )}
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>Failed to load text: {error}</AlertDescription>
                </Alert>
              )}
              {!loading && !error && (
                <pre className="whitespace-pre-wrap font-sans text-sm text-foreground">
                  {markdown || 'No text content available.'}
                </pre>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="shrink-0 gap-2 sm:justify-start">
          {pdfUrl && (
            <Button
              variant="outline"
              onClick={() => window.open(pdfUrl, '_blank', 'noopener,noreferrer')}
            >
              <ExternalLink className="mr-1.5 h-4 w-4" />
              Open in new tab
            </Button>
          )}
          {downloadUrl && (
            <Button
              variant="outline"
              onClick={() => window.open(downloadUrl, '_blank', 'noopener,noreferrer')}
            >
              <Download className="mr-1.5 h-4 w-4" />
              Download PDF
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
