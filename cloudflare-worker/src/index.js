export default {
  // ==========================================
  // কাজ ১: Load Balancer + Health Dashboard
  // ==========================================
  async fetch(request, env, ctx) {
    const services = {
      primary: env.PRIMARY_URL || "https://supremeai-backend.onrender.com",
      admin: env.ADMIN_URL || "https://supremeai-admin.onrender.com",
      backup: env.BACKUP_URL || "https://supremeai-studio-client.onrender.com",
    };

    const results = await Promise.allSettled(
      Object.entries(services).map(async ([name, url]) => {
        const alive = await this.pingWithRetry(url, 2);
        return { name, url, alive };
      })
    );

    const statuses = results.map(r =>
      r.status === "fulfilled" ? r.value : { alive: false, error: r.reason?.message }
    );
    const allAlive = statuses.every(s => s.alive);

    return new Response(JSON.stringify({
      status: allAlive ? "UP" : "DEGRADED",
      timestamp: new Date().toISOString(),
      services: statuses,
    }), {
      status: allAlive ? 200 : 503,
      headers: { "Content-Type": "application/json" },
    });
  },

  // ==========================================
  // কাজ ২: Keep-Alive Ping (প্রতি ১০ মিনিটে একাধিক সার্ভিস)
  // ==========================================
  async scheduled(event, env, ctx) {
    const targets = [
      env.PRIMARY_URL || "https://supremeai-backend.onrender.com/health",
      env.ADMIN_URL || "https://supremeai-admin.onrender.com/health",
      env.BACKUP_HEALTH || "https://supremeai-studio-client-qb34.onrender.com/api/v1/health",
    ];

    const results = await Promise.allSettled(
      targets.map(url => this.pingWithRetry(url, 3))
    );

    const alive = results.filter(r => r.status === "fulfilled" && r.value).length;
    console.log(`✅ KeepAlive: ${alive}/${targets.length} services alive at ${new Date().toISOString()}`);
  },

  // ==========================================
  // Helper: Retry logic with exponential backoff
  // ==========================================
  async pingWithRetry(url, maxRetries = 2) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(url, {
          headers: { "User-Agent": "Cloudflare-KeepAlive-Worker/2.0" },
          signal: AbortSignal.timeout(10000),
        });
        if (response.ok) return true;
        console.warn(`⚠️ Ping ${url} returned ${response.status}, retry ${i + 1}/${maxRetries}`);
      } catch (error) {
        console.error(`❌ Ping ${url} failed: ${error.message}, retry ${i + 1}/${maxRetries}`);
      }
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, 1000 * (i + 1)));
      }
    }
    return false;
  },
};
