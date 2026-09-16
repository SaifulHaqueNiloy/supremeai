"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ChevronDown, Copy, ExternalLink, FileText, RefreshCw, Search } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { callTowerTool } from "@/lib/tower-gateway";
import { MetricBadge } from "./widgets";
import { cn } from "@/lib/utils";

/**
 * Docs Sources — the tower's curated documentation registry (docs_list /
 * docs_search). Lazy + collapsed by default so it never costs a tower call
 * unless the operator opens it.
 */

interface DocSource {
  name: string;
  url: string;
  description: string;
  category: string;
  relevance?: number;
}

function normalizeSources(payload: unknown): DocSource[] {
  let list: unknown[] = [];
  if (Array.isArray(payload)) list = payload;
  else if (payload && typeof payload === "object") {
    const rec = payload as Record<string, unknown>;
    const inner = rec.sources ?? rec.items ?? rec.docs ?? rec.results;
    if (Array.isArray(inner)) list = inner;
  }
  return list
    .map((it) => {
      const r = (it ?? {}) as Record<string, unknown>;
      return {
        name: String(r.name ?? r.title ?? "unknown"),
        url: String(r.url ?? r.link ?? "#"),
        description: String(r.description ?? r.desc ?? "").slice(0, 140),
        category: String(r.category ?? r.cat ?? "general"),
        relevance: typeof r.relevance === "number" ? r.relevance : undefined,
      };
    })
    .filter((d) => d.name !== "unknown" || d.url !== "#");
}

export function DocsSources() {
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState("");
  const [reading, setReading] = React.useState<DocSource | null>(null);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["docs-sources", q],
    queryFn: async () => {
      const r = q.trim()
        ? await callTowerTool("docs_search", { query: q.trim() }, { silent: true })
        : await callTowerTool("docs_list", {}, { silent: true });
      return r;
    },
    enabled: open,
    staleTime: 5 * 60_000,
    retry: false,
  });

  const sources = React.useMemo(() => normalizeSources(data?.result), [data]);
  const categories = [...new Set(sources.map((s) => s.category))];

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className="min-w-0">
        <CollapsibleTrigger asChild>
          <button className="flex w-full items-center gap-2 p-4 text-left" aria-expanded={open}>
            <BookOpen className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">Docs Sources</span>
            <span className="text-xs text-muted-foreground">tower documentation registry — list & search</span>
            {sources.length > 0 && <Badge variant="secondary" className="text-[10px]">{sources.length} sources</Badge>}
            <ChevronDown className={cn("ml-auto h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")} />
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="mb-3 flex flex-col gap-2 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search docs sources — deploy, database, edge…"
                  className="pl-9 h-8"
                  aria-label="Search docs sources"
                />
              </div>
              {categories.length > 0 && (
                <div className="flex flex-wrap items-center gap-1">
                  {categories.slice(0, 6).map((c) => (
                    <Badge key={c} variant="outline" className="text-[10px] capitalize">{c}</Badge>
                  ))}
                </div>
              )}
              <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0" onClick={() => refetch()} disabled={isFetching} aria-label="Refresh docs sources">
                <RefreshCw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
              </Button>
            </div>

            {isLoading ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-16 animate-pulse rounded-lg bg-muted/40" />
                ))}
              </div>
            ) : isError || !data?.ok ? (
              <p className="py-4 text-xs text-muted-foreground">Docs registry unavailable ({(data?.error ?? "tower unreachable").slice(0, 80)}).</p>
            ) : sources.length === 0 ? (
              <p className="py-4 text-xs text-muted-foreground">No docs sources match “{q}”.</p>
            ) : (
              <ul className="grid gap-2 sm:grid-cols-2">
                {sources.map((s, i) => (
                  <li key={`${s.name}-${i}`}>
                    <div
                      className={cn(
                        "group flex h-full items-start gap-2 rounded-lg border p-3 transition-colors",
                        reading?.url === s.url ? "border-primary/40 bg-primary/5" : "hover:border-primary/40 hover:bg-primary/5",
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="flex items-center gap-1.5 text-xs font-semibold">
                          <span className="truncate">{s.name}</span>
                          <MetricBadge>{s.category}</MetricBadge>
                          {s.relevance != null && <MetricBadge tone={s.relevance >= 0.5 ? "good" : "default"}>{Math.round(s.relevance * 100)}%</MetricBadge>}
                        </p>
                        <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">{s.description || s.url}</p>
                      </div>
                      <div className="flex shrink-0 items-center gap-0.5">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-muted-foreground/70 hover:text-primary"
                          onClick={() => setReading(s)}
                          aria-label={`Read ${s.name} inline`}
                          title="Read inline (docs_fetch)"
                        >
                          <BookOpen className="h-3.5 w-3.5" />
                        </Button>
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground/50 transition-colors hover:bg-muted hover:text-primary"
                          aria-label={`Open ${s.name} in new tab`}
                          title="Open original"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>

      <DocReader doc={reading} onClose={() => setReading(null)} />
    </Collapsible>
  );
}

/* ── Inline doc reader — fetches full page content via docs_fetch ─── */

function extractDocText(payload: unknown): { text: string; title: string | null } {
  // Tower may return a plain string, {content}, {text}, {docs}, or nested JSON.
  let raw = payload;
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    const rec = raw as Record<string, unknown>;
    raw = rec.content ?? rec.text ?? rec.body ?? rec.docs ?? rec.result ?? rec.data ?? raw;
  }
  if (typeof raw === "string") {
    // Sometimes the string itself is JSON — try to unwrap once.
    if (raw.trimStart().startsWith("{") || raw.trimStart().startsWith("[")) {
      try {
        return extractDocText(JSON.parse(raw));
      } catch {
        /* keep as plain text */
      }
    }
    return { text: raw, title: null };
  }
  if (raw == null) return { text: "", title: null };
  return { text: JSON.stringify(raw, null, 2), title: null };
}

function DocReader({ doc, onClose }: { doc: DocSource | null; onClose: () => void }) {
  // Fetch only while a doc is selected; one-shot (no polling), fresh per open.
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["doc-fetch", doc?.url],
    queryFn: () => callTowerTool("docs_fetch", { url: doc!.url }),
    enabled: !!doc,
    staleTime: 10 * 60_000,
    retry: false,
  });

  const extracted = React.useMemo(() => (data?.result !== undefined ? extractDocText(data.result) : null), [data]);
  const words = extracted ? extracted.text.trim().split(/\s+/).filter(Boolean).length : 0;

  const copyDoc = async () => {
    if (!extracted?.text) return;
    try {
      await navigator.clipboard.writeText(extracted.text);
      toast.success("Doc content copied to clipboard");
    } catch {
      toast.error("Clipboard unavailable in this context");
    }
  };

  return (
    <Dialog open={!!doc} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="flex max-h-[85vh] flex-col gap-0 sm:max-w-2xl">
        <DialogHeader className="min-w-0 pr-8">
          <DialogTitle className="flex min-w-0 items-center gap-2 text-sm">
            <FileText className="h-4 w-4 shrink-0 text-primary" />
            <span className="truncate">{doc?.name ?? "Document"}</span>
            {words > 0 && <MetricBadge>{words.toLocaleString()} words</MetricBadge>}
          </DialogTitle>
          <DialogDescription className="truncate text-[11px]">{doc?.url}</DialogDescription>
        </DialogHeader>

        <ScrollArea className="min-h-0 flex-1 rounded-md border bg-muted/20">
          <div className="p-4">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-3 animate-pulse rounded bg-muted/60" style={{ width: `${72 + ((i * 13) % 28)}%` }} />
                ))}
                <p className="pt-2 text-[11px] text-muted-foreground">Fetching via tower docs_fetch…</p>
              </div>
            ) : isError || !data?.ok ? (
              <p className="text-xs text-muted-foreground">
                Could not fetch this page ({(data?.error ?? (error as Error)?.message ?? "tower unreachable").slice(0, 120)}).
              </p>
            ) : (
              <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-foreground/90">{extracted?.text}</pre>
            )}
          </div>
        </ScrollArea>

        <div className="flex items-center gap-2 pt-3">
          <span className="min-w-0 flex-1 truncate text-[10px] uppercase tracking-wide text-muted-foreground/60">
            tower tool · docs_fetch · silent off (journaled)
          </span>
          <Button variant="outline" size="sm" className="h-7 text-xs" onClick={copyDoc} disabled={!extracted?.text}>
            <Copy className="mr-1 h-3 w-3" /> Copy
          </Button>
          {doc && (
            <a href={doc.url} target="_blank" rel="noreferrer">
              <Button variant="outline" size="sm" className="h-7 text-xs">
                <ExternalLink className="mr-1 h-3 w-3" /> Original
              </Button>
            </a>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
