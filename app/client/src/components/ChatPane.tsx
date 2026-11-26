import {
  Alert,
  AlertDescription,
  Badge,
  Button,
  Textarea,
} from '@databricks/appkit-ui/react';
import { Bot, Send, ShieldCheck, Sparkles, User, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export interface AppealContext {
  facility_id: string;
  account: string;
  encounter_nbr: string;
  patient_name: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const SUGGESTIONS = [
  'Why is this appeal warranted?',
  'Summarize the denial reason.',
  'What clinical evidence supports the appeal?',
];

export function ChatPane({
  context,
  onClearContext,
}: {
  context: AppealContext | null;
  onClearContext: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
    };
    const history = [...messages, userMessage];
    setMessages(history);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/appeals-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: history.map(({ role, content }) => ({ role, content })),
          context,
        }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { error?: string } | null;
        throw new Error(body?.error ?? `Request failed (${res.status})`);
      }
      const data = (await res.json()) as { content: string };
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: data.content },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="border-b p-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Appeals Assistant</h2>
        </div>
        {context ? (
          <div className="mt-2 flex items-center gap-2">
            <Badge variant="outline" className="gap-1 font-normal">
              {context.patient_name} · Acct {context.account}
            </Badge>
            <button
              type="button"
              onClick={onClearContext}
              className="text-muted-foreground hover:text-foreground"
              aria-label="Clear appeal context"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <p className="mt-1 text-xs text-muted-foreground">
            Select an appeal row to ask about a specific patient, or ask a general question.
          </p>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-3">
        {messages.length === 0 && !loading && (
          <div className="space-y-3 pt-2">
            <p className="text-xs text-muted-foreground">Try asking:</p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => void send(s)}
                className="block w-full rounded-md border bg-background px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-muted"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <Bot className="mt-1 h-4 w-4 shrink-0 text-primary" />
            )}
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-foreground'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
            {msg.role === 'user' && (
              <User className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Bot className="h-4 w-4 text-primary" />
            <span className="animate-pulse">Thinking…</span>
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Composer */}
      <div className="border-t p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void send(input);
          }}
          className="flex items-end gap-2"
        >
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                void send(input);
              }
            }}
            placeholder="Ask about an appeal…"
            rows={2}
            className="min-h-0 resize-none"
            disabled={loading}
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
            <span className="sr-only">Send</span>
          </Button>
        </form>
        <p className="mt-2 flex items-center gap-1 text-[11px] text-muted-foreground">
          <ShieldCheck className="h-3 w-3" />
          Runs as the app service principal · AI-generated — verify before acting.
        </p>
      </div>
    </div>
  );
}
