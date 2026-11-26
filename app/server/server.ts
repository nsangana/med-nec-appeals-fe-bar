import { analytics, createApp, files, genie, lakebase, server, serving, toPlugin } from '@databricks/appkit';
import type { Request } from 'express';
import { z } from 'zod';
import {
  ACTIONS_REQUIRING_WARRANTED,
  CASE_SQL,
  CaseKeySchema,
  HISTORY_SQL,
  INSERT_REVIEW_ACTION_SQL,
  LATEST_EDIT_SQL,
  REVIEW_STATE_SQL,
  ReviewActionBodySchema,
  SUMMARY_SQL,
  WORKLIST_COUNT_SQL,
  WorklistQuerySchema,
  buildWorklistQuery,
  num,
  pdfUrl,
  reviewActionAllowed,
  reviewStatusLabel,
  searchPattern,
  text,
  toHistory,
  toLatestEdit,
  toSummary,
  toWorklistItem,
  volumeFileName,
  type Row,
} from './worklist';

// ---- Chat request contract -------------------------------------------------
const chatSchema = z.object({
  // Bounded: every message is sent to a paid LLM endpoint, so cap turns and size.
  messages: z
    .array(
      z.object({
        role: z.enum(['user', 'assistant']),
        content: z.string().min(1).max(4_000),
      }),
    )
    .min(1)
    .max(20),
  // When a worklist row is selected we seed the agent with that appeal's
  // composite key so its get_appeal / get_encounter tools can resolve it.
  context: z
    .object({
      facility_id: z.string().max(20),
      account: z.string().max(20),
      encounter_nbr: z.string().max(20),
      patient_name: z.string().max(200),
    })
    .nullable()
    .optional(),
});

type ChatMessage = z.infer<typeof chatSchema>['messages'][number];

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? (value as unknown[]) : [];
}

// The serving plugin wraps the endpoint response as { ok, data: <response> }.
// The ResponsesAgent response then carries output items either top-level
// ({ output: [...] }) or under a predictions array. Handle every layer.
function extractAgentText(result: unknown): string {
  const wrapper = result as { data?: unknown };
  const root = (wrapper?.data ?? result) as {
    output?: unknown;
    predictions?: unknown;
  };

  const outputs: unknown[] = [];
  for (const item of asArray(root?.output)) outputs.push(item);
  if (outputs.length === 0) {
    for (const pred of asArray(root?.predictions)) {
      const p = pred as { output?: unknown };
      for (const item of asArray(p?.output)) outputs.push(item);
    }
  }

  const texts: string[] = [];
  for (const item of outputs) {
    const msg = item as {
      type?: string;
      content?: Array<{ type?: string; text?: string }>;
    };
    if (msg?.type === 'message' && Array.isArray(msg.content)) {
      for (const chunk of msg.content) {
        if (chunk?.type === 'output_text' && typeof chunk.text === 'string') {
          texts.push(chunk.text);
        }
      }
    }
  }

  return texts.join('\n').trim();
}

function upstreamFailure(result: unknown): string | null {
  if (result === null || typeof result !== 'object' || !('ok' in result) || result.ok !== false) return null;
  const status = 'status' in result ? text(result.status) : null;
  const message = 'message' in result ? text(result.message) : null;
  return `Agent endpoint error${status ? ` (${status})` : ''}: ${message ?? 'unknown error'}`;
}

// Reviewer identity comes from the platform-set request header (the signed-in user).
function reviewerFrom(req: Request): string | null {
  const raw = req.headers['x-forwarded-email'] ?? req.headers['x-forwarded-user'];
  const value = Array.isArray(raw) ? raw[0] : raw;
  return value && value.trim() ? value.trim() : null;
}

const genieEnabled = Boolean(process.env.DATABRICKS_GENIE_SPACE_ID);

// Genie runs as the APP SERVICE PRINCIPAL, not on behalf of the user (decision 2026-11-24).
// The stock plugin wraps every route in asUser(req), but the forwarded user token never carried the
// `genie` scope even after it was added to user_api_scopes and the app was redeployed
// ("Provided OAuth token does not have required scopes: genie"). This subclass keeps the plugin's
// routes, SSE format and <GenieChat> contract and just drops the asUser wrapper, so the plugin's
// getWorkspaceClient() resolves to the service principal. The SP has CAN_RUN on the space (genie-space
// resource) and SELECT on its 5 objects only (governance/04_app_sp_genie_grants.sql).
// Trade-off: answers reflect the app's access, not each reviewer's UC grants.
type GenieHandlers = {
  route: (router: unknown, def: { name: string; method: string; path: string; handler: (req: Request, res: unknown) => Promise<void> }) => void;
  _handleSendMessage: (req: Request, res: unknown) => Promise<void>;
  _handleGetConversation: (req: Request, res: unknown) => Promise<void>;
  _handleGetMessage: (req: Request, res: unknown) => Promise<void>;
};
const BaseGeniePlugin = genie().plugin;
class ServicePrincipalGeniePlugin extends BaseGeniePlugin {
  injectRoutes(router: unknown) {
    const self = this as unknown as GenieHandlers;
    self.route(router, { name: 'sendMessage', method: 'post', path: '/:alias/messages',
      handler: (req, res) => self._handleSendMessage(req, res) });
    self.route(router, { name: 'getConversation', method: 'get', path: '/:alias/conversations/:conversationId',
      handler: (req, res) => self._handleGetConversation(req, res) });
    self.route(router, { name: 'getMessage', method: 'get', path: '/:alias/conversations/:conversationId/messages/:messageId',
      handler: (req, res) => self._handleGetMessage(req, res) });
  }
}
const spGenie = toPlugin(ServicePrincipalGeniePlugin);

createApp({
  plugins: [
    analytics(),
    // Read-only access to the appeal PDF volume, executed on behalf of the
    // requesting user (OBO): each user must hold READ_VOLUME on the volume,
    // and every file API call is attributed to and authorized as that user.
    // publicRead still allows GET/raw/download and denies writes (the app
    // never mutates the volume).
    files({
      volumes: {
        files: {
          auth: 'on-behalf-of-user',
          policy: files.policy.publicRead(),
        },
      },
    }),
    // Worklist, review_actions and review_state live in Lakebase. The pool runs as the
    // app service principal (see lakebase/AUTH.md); LAKEBASE_ENDPOINT comes from the postgres resource.
    lakebase(),
    server(),
    serving(),
    // Genie is registered only when a space id is configured (DATABRICKS_GENIE_SPACE_ID,
    // bound via the genie-space resource). See app/README.md "Genie wiring".
    ...(genieEnabled ? [spGenie()] : []),
  ],
  onPluginsReady(appkit) {
    appkit.server.extend((app) => {
      app.get('/api/config', (req, res) => {
        res.json({ genieEnabled, reviewer: reviewerFrom(req) });
      });

      // ---- Worklist (Lakebase) -------------------------------------------
      app.get('/api/worklist', async (req, res) => {
        const parsed = WorklistQuerySchema.safeParse(req.query);
        if (!parsed.success) {
          res.status(400).json({ error: 'Invalid query parameters' });
          return;
        }
        const { search, sort, page, page_size, recommendation, min_expected } = parsed.data;
        // Filter params are shared by the page query and the count query ($1..$3).
        const filters = [searchPattern(search), recommendation, min_expected];
        try {
          const result = await appkit.lakebase.query<Row>(buildWorklistQuery(sort), [
            ...filters,
            page_size,
            page * page_size,
          ]);
          const items = result.rows.map((row) => toWorklistItem(row));
          let total = result.rows.length > 0 ? (num(result.rows[0].total_count) ?? 0) : 0;
          // A page past the end of the filtered set returns no rows, so the window count is unavailable.
          // Ask for the filtered total directly so pagination stays correct.
          if (result.rows.length === 0 && page > 0) {
            const countRes = await appkit.lakebase.query<Row>(WORKLIST_COUNT_SQL, filters);
            total = num(countRes.rows[0]?.total) ?? 0;
          }
          res.json({ items, total, page, page_size });
        } catch (err) {
          sendLakebaseError(res, 'worklist', err);
        }
      });

      app.get('/api/worklist/summary', async (_req, res) => {
        try {
          const result = await appkit.lakebase.query<Row>(SUMMARY_SQL);
          res.json(toSummary(result.rows[0]));
        } catch (err) {
          sendLakebaseError(res, 'summary', err);
        }
      });

      // ---- Case file: worklist row + review state + PDF URLs --------------
      app.get('/api/cases/:facility_id/:account/:encounter_nbr', async (req, res) => {
        const key = CaseKeySchema.safeParse(req.params);
        if (!key.success) {
          res.status(400).json({ error: 'Invalid case key' });
          return;
        }
        const { facility_id, account, encounter_nbr } = key.data;
        try {
          const [caseRes, editRes, historyRes] = await Promise.all([
            appkit.lakebase.query<Row>(CASE_SQL, [facility_id, account, encounter_nbr]),
            appkit.lakebase.query<Row>(LATEST_EDIT_SQL, [facility_id, account, encounter_nbr]),
            appkit.lakebase.query<Row>(HISTORY_SQL, [facility_id, account, encounter_nbr]),
          ]);
          const row = caseRes.rows[0];
          if (!row) {
            res.status(404).json({ error: 'Case not found' });
            return;
          }
          const item = toWorklistItem(row);
          res.json({
            item,
            review: {
              status: item.review_status,
              status_label: reviewStatusLabel(item.review_status),
              last_reviewer: item.last_reviewer,
              last_action_at: item.last_action_at,
              submitted_at: item.submitted_at,
              latest_edit: toLatestEdit(editRes.rows[0]),
              history: toHistory(historyRes.rows),
            },
            files: {
              letter: {
                name: volumeFileName(item.letter_pdf_path),
                url: pdfUrl(item.letter_pdf_path),
              },
              data_sheet: {
                name: volumeFileName(item.data_sheet_pdf_path),
                url: pdfUrl(item.data_sheet_pdf_path),
              },
              ai_worksheet: {
                name: volumeFileName(item.cheat_sheet_pdf_path),
                url: pdfUrl(item.cheat_sheet_pdf_path),
              },
            },
          });
        } catch (err) {
          sendLakebaseError(res, 'case', err);
        }
      });

      // ---- Reviewer actions: append-only INSERT into review_actions --------
      app.post('/api/review-actions', async (req, res) => {
        const reviewer = reviewerFrom(req);
        if (!reviewer) {
          res.status(401).json({ error: 'Reviewer identity missing (x-forwarded-email header)' });
          return;
        }
        const parsed = ReviewActionBodySchema.safeParse(req.body);
        if (!parsed.success) {
          res.status(400).json({ error: 'Invalid review action', issues: parsed.error.issues });
          return;
        }
        const body = parsed.data;
        // Only EDIT carries a letter; other actions store NULL there.
        const editedLetter = body.action === 'EDIT' ? (body.edited_letter ?? null) : null;
        try {
          // Server-side guard: EDIT / APPROVE / SUBMIT need a WARRANTED appeal (the UI does not gate these buttons).
          if (ACTIONS_REQUIRING_WARRANTED.includes(body.action)) {
            const caseRes = await appkit.lakebase.query<Row>(CASE_SQL, [
              body.facility_id,
              body.account,
              body.encounter_nbr,
            ]);
            if (!caseRes.rows[0]) {
              res.status(404).json({ error: 'Case not found' });
              return;
            }
            const current = toWorklistItem(caseRes.rows[0]).recommendation;
            if (!reviewActionAllowed(body.action, current)) {
              res.status(409).json({
                error: `${body.action} requires a WARRANTED appeal (current recommendation: ${current})`,
              });
              return;
            }
          }
          const inserted = await appkit.lakebase.query<Row>(INSERT_REVIEW_ACTION_SQL, [
            body.facility_id,
            body.account,
            body.encounter_nbr,
            body.action,
            editedLetter,
            reviewer,
            body.note ?? null,
          ]);
          const state = await appkit.lakebase.query<Row>(REVIEW_STATE_SQL, [
            body.facility_id,
            body.account,
            body.encounter_nbr,
          ]);
          const ins = inserted.rows[0];
          const st = state.rows[0];
          const status = text(st?.status) ?? body.action;
          res.status(201).json({
            ok: true,
            action_id: text(ins?.id),
            action: body.action,
            reviewer,
            created_at: text(ins?.created_at),
            status,
            status_label: reviewStatusLabel(status),
            submitted_at: text(st?.submitted_at),
          });
        } catch (err) {
          sendLakebaseError(res, 'review-action', err);
        }
      });

      // ---- Chat proxy to fe-bar-appeals-chat (ResponsesAgent) -------------
      // Runs on behalf of the requesting user (OBO) via .asUser(req), so the
      // endpoint's per-user CAN_QUERY permission is enforced and the call is
      // attributed to the end user rather than the app service principal.
      app.post('/api/appeals-chat', async (req, res) => {
        const parsed = chatSchema.safeParse(req.body);
        if (!parsed.success) {
          res.status(400).json({ error: 'Invalid request body' });
          return;
        }

        const { messages, context } = parsed.data;
        const input: ChatMessage[] = [];

        if (context) {
          input.push({
            role: 'user',
            content:
              `Context for this conversation: the user is reviewing a denied ` +
              `medical-necessity appeal with FACILITY_ID=${context.facility_id}, ` +
              `PATIENT_CONTROL_NUMBER=${context.account}, ` +
              `ENCOUNTER_NBR=${context.encounter_nbr} (patient ${context.patient_name}). ` +
              `When the user refers to "this appeal", "this patient", or "this encounter", ` +
              `use your get_appeal / get_encounter tools with these identifiers.`,
          });
        }
        input.push(...messages);

        try {
          const result: unknown = await appkit.serving('default').asUser(req).invoke({ input });
          // Failures can come back as { ok: false, status, message } instead of throwing (e.g. endpoint not found).
          const failure = upstreamFailure(result);
          if (failure) {
            console.error('appeals-chat upstream error:', failure);
            res.status(502).json({ error: failure });
            return;
          }
          const content = extractAgentText(result);
          res.json({
            content: content || 'The agent returned an empty response.',
          });
        } catch (err) {
          console.error('appeals-chat error:', err);
          res.status(502).json({
            error: err instanceof Error ? err.message : 'Agent request failed',
          });
        }
      });
    });
  },
}).catch(console.error);

// Lakebase errors are returned with their Postgres SQLSTATE so a missing grant
// (42501 permission denied) is visible to the operator without leaking internals.
function sendLakebaseError(
  res: { status: (code: number) => { json: (body: unknown) => void } },
  route: string,
  err: unknown,
) {
  const code = typeof err === 'object' && err !== null && 'code' in err ? String((err as { code: unknown }).code) : null;
  console.error(`lakebase ${route} error:`, err);
  res.status(503).json({ error: `Lakebase ${route} query failed`, code });
}
