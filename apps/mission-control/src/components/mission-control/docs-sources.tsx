"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ChevronDown, ExternalLink, RefreshCw, Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="group flex h-full items-start gap-2 rounded-lg border p-3 transition-colors hover:border-primary/40 hover:bg-primary/5"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="flex items-center gap-1.5 text-xs font-semibold">
                          <span className="truncate">{s.name}</span>
                          <MetricBadge>{s.category}</MetricBadge>
                          {s.relevance != null && <MetricBadge tone={s.relevance >= 0.5 ? "good" : "default"}>{Math.round(s.relevance * 100)}%</MetricBadge>}
                        </p>
                        <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">{s.description || s.url}</p>
                      </div>
                      <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground/50 transition-colors group-hover:text-primary" />
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
