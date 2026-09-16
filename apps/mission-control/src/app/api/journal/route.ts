import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

/**
 * Operations Journal — governed telemetry over every tool call the console made.
 * Zero tower dependency: reads the local ToolCallLog (SQLite) so it works even
 * while the tower sleeps.
 */

interface JournalEntry {
  id: string;
  tool: string;
  ok: boolean;
  durationMs: number;
  snippet: string | null;
  createdAt: string;
}

interface TopTool {
  tool: string;
  calls: number;
  failures: number;
  avgMs: number;
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const q = (url.searchParams.get("q") ?? "").trim().toLowerCase();
  const status = url.searchParams.get("status") ?? "all"; // all | ok | failed
  const limit = Math.min(Number(url.searchParams.get("limit") ?? 60) || 60, 200);

  try {
    const since24h = new Date(Date.now() - 24 * 3600_000);

    // ── Stats over the last 24h ──
    const grouped = await db.toolCallLog.groupBy({
      by: ["tool"],
      where: { createdAt: { gte: since24h } },
      _count: { _all: true },
      _avg: { durationMs: true },
    }).catch(() => []);

    let total24h = 0;
    let ok24h = 0;
    const failsByTool = new Map<string, number>();
    try {
      const [t, f] = await Promise.all([
        db.toolCallLog.count({ where: { createdAt: { gte: since24h } } }),
        db.toolCallLog.count({ where: { createdAt: { gte: since24h }, ok: false } }),
      ]);
      total24h = t;
      ok24h = t - f;
      const failGroups = await db.toolCallLog.groupBy({
        by: ["tool"],
        where: { createdAt: { gte: since24h }, ok: false },
        _count: { _all: true },
      });
      for (const g of failGroups) failsByTool.set(g.tool, g._count._all);
    } catch {
      /* best effort */
    }

    const topTools: TopTool[] = grouped
      .map((g) => ({
        tool: g.tool,
        calls: g._count._all,
        failures: failsByTool.get(g.tool) ?? 0,
        avgMs: Math.round(g._avg.durationMs ?? 0),
      }))
      .sort((a, b) => b.calls - a.calls)
      .slice(0, 6);

    const avgDurationMs = grouped.length
      ? Math.round(grouped.reduce((acc, g) => acc + (g._avg.durationMs ?? 0), 0) / grouped.length)
      : 0;

    // ── Filtered entries ──
    const where: Record<string, unknown> = {};
    if (status === "ok") where.ok = true;
    if (status === "failed") where.ok = false;
    if (q) where.tool = { contains: q };

    const rows = await db.toolCallLog.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take: limit,
    }).catch(() => []);

    const entries: JournalEntry[] = rows.map((r) => ({
      id: r.id,
      tool: r.tool,
      ok: r.ok,
      durationMs: r.durationMs,
      snippet: r.snippet,
      createdAt: r.createdAt.toISOString(),
    }));

    return NextResponse.json({
      ok: true,
      stats: {
        total24h,
        ok24h,
        failed24h: total24h - ok24h,
        successRate: total24h > 0 ? Math.round((ok24h / total24h) * 100) : 100,
        avgDurationMs,
        topTools,
      },
      entries,
      checkedAt: new Date().toISOString(),
    });
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err), stats: null, entries: [] }, { status: 500 });
  }
}
