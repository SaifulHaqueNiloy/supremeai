import { db } from "@/lib/db";
import { getSettings, logActivity } from "@/lib/settings";
import { callTowerTool } from "@/lib/tower-client";
import type { ServiceStatus } from "@/lib/mission-types";

/**
 * Service-down watchdog — dynamic, zero-cost reliability alerting.
 *
 * Runs inside GET /api/dashboard on every refresh: compares fresh tower
 * service statuses against the latest local ServiceSnapshot per provider,
 * detects transitions (down/degraded/recovered) and:
 *   1. writes an ActivityEvent (visible in the Activity Stream + dashboard)
 *   2. optionally broadcasts via the tower notify channel (dynamic setting,
 *      best-effort — tower asleep or missing chat id never breaks the dashboard)
 *
 * Cooldown (dynamic, watchdogCooldownMin) prevents alert storms: repeated
 * notifications for the same provider+kind are suppressed, but every
 * transition is still recorded as an event for the audit trail.
 */

export interface ServiceTransition {
  provider: string;
  from: ServiceStatus["status"];
  to: ServiceStatus["status"];
  kind: "down" | "degraded" | "recovered";
  note: string | null;
}

/** Channels the tower exposes for operator notifications. */
export const NOTIFY_CHANNELS = ["none", "telegram", "discord"] as const;
export type NotifyChannel = (typeof NOTIFY_CHANNELS)[number];

async function latestSnapshotStatus(provider: string): Promise<string | null> {
  const snap = await db.serviceSnapshot.findFirst({
    where: { provider },
    orderBy: { checkedAt: "desc" },
    select: { status: true },
  });
  return snap?.status ?? null;
}

async function recentlyAlerted(provider: string, kind: string, cooldownMin: number): Promise<boolean> {
  if (cooldownMin <= 0) return false;
  // Only actual notify events count toward cooldown — transition journal entries
  // (which share provider/kind meta) must never suppress their own notify.
  const recent = await db.activityEvent.findMany({
    where: { type: "watchdog", createdAt: { gte: new Date(Date.now() - cooldownMin * 60_000) } },
    orderBy: { createdAt: "desc" },
    select: { meta: true },
    take: 20,
  });
  return recent.some((r) => {
    try {
      const meta = JSON.parse(r.meta ?? "") as { provider?: string; kind?: string; notified?: boolean };
      return meta.notified === true && meta.provider === provider && meta.kind === kind;
    } catch {
      return false;
    }
  });
}

/** Detect transitions BEFORE new snapshots are persisted. */
export async function detectServiceTransitions(services: ServiceStatus[]): Promise<ServiceTransition[]> {
  const transitions: ServiceTransition[] = [];
  for (const s of services.slice(0, 12)) {
    if (s.status === "unknown") continue;
    if (s.note === "cached") continue; // cached fallback isn't fresh evidence
    const prev = await latestSnapshotStatus(s.provider).catch(() => null);
    if (!prev || prev === s.status) continue;
    const kind: ServiceTransition["kind"] =
      s.status === "down" ? "down" : s.status === "degraded" ? "degraded" : prev === "down" || prev === "degraded" ? "recovered" : "recovered";
    transitions.push({ provider: s.provider, from: prev as ServiceStatus["status"], to: s.status, kind, note: s.note ?? null });
  }
  return transitions;
}

/** Handle transitions: journal + optional tower broadcast. Never throws. */
export async function handleServiceTransitions(transitions: ServiceTransition[]): Promise<void> {
  if (transitions.length === 0) return;
  let settings: Record<string, string>;
  try {
    settings = await getSettings();
  } catch {
    return;
  }
  if (settings.watchdogEnabled === "false") return;

  const channel = (settings.watchdogNotifyChannel ?? "none") as NotifyChannel;
  const cooldownMin = Math.max(0, Math.min(240, Number(settings.watchdogCooldownMin) || 15));

  for (const t of transitions) {
    const icon = t.kind === "down" ? "🔴" : t.kind === "degraded" ? "🟠" : "🟢";
    const title =
      t.kind === "down"
        ? `Watchdog: ${t.provider} is DOWN`
        : t.kind === "degraded"
          ? `Watchdog: ${t.provider} degraded`
          : `Watchdog: ${t.provider} recovered`;
    const detail = `${t.from} → ${t.to}${t.note ? ` · ${t.note}` : ""}`;

    // Always journal the transition (audit trail even when notify is off/cooled)
    await logActivity("watchdog", t.kind === "down" ? "error" : t.kind === "degraded" ? "warn" : "success", title, detail, {
      provider: t.provider,
      kind: t.kind,
      from: t.from,
      to: t.to,
    }).catch(() => undefined);

    // Broadcast only for actionable transitions + cooldown window
    if (channel === "none" || t.kind === "recovered") continue;
    if (await recentlyAlerted(t.provider, t.kind, cooldownMin)) continue;

    const message = `${icon} SupremeAI watchdog: ${t.provider} ${t.kind.toUpperCase()} (${t.from} → ${t.to}) at ${new Date().toISOString().slice(11, 19)} UTC${t.note ? ` — ${t.note}` : ""}`;
    try {
      const tool = channel === "telegram" ? "notify_send_telegram" : "notify_send_discord";
      const res = await callTowerTool(tool, { message: message.slice(0, channel === "telegram" ? 4000 : 1900) });
      await logActivity(
        "watchdog",
        res.ok ? "success" : "warn",
        `Watchdog notify via ${channel} ${res.ok ? "sent" : "failed"}`,
        res.ok ? `${t.provider} ${t.kind} broadcast delivered` : (res.error ?? "tower rejected").slice(0, 200),
        { provider: t.provider, kind: t.kind, channel, notified: res.ok },
      ).catch(() => undefined);
    } catch (err) {
      await logActivity("watchdog", "warn", `Watchdog notify via ${channel} errored`, String(err).slice(0, 200), {
        provider: t.provider,
        kind: t.kind,
        channel,
        notified: false,
      }).catch(() => undefined);
    }
  }
}
