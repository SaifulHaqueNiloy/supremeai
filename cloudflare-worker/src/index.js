export default {
  // ==========================================
  // কাজ ১: Load Balancer (HTTP রিকোয়েস্ট হ্যান্ডেল করবে)
  // ==========================================
  async fetch(request, env, ctx) {
    // এখানে আপনার লোড ব্যালান্সিং-এর লজিক বসবে।
    // উদাহরণস্বরূপ, আমি একটি বেসিক রেসপন্স দিয়ে রাখলাম।
    // আপনার আগের আসল লজিকটি এখানে বসিয়ে নেবেন।
    return new Response("SupremeAI Load Balancer and Keep-Alive Worker is Active!", { status: 200 });
  },

  // ==========================================
  // কাজ ২: Keep-Alive Ping (প্রতি ১৪ মিনিটে চলবে)
  // ==========================================
  async scheduled(event, env, ctx) {
    const targetUrl = "https://supremeai-gzwe.onrender.com/health";

    try {
      const response = await fetch(targetUrl, {
        headers: { "User-Agent": "Cloudflare-KeepAlive-Worker" }
      });

      if (response.ok) {
        console.log(`✅ Ping successful: ${response.status} at ${new Date().toISOString()}`);
      } else {
        console.error(`❌ Ping failed: ${response.status}`);
      }
    } catch (error) {
      console.error(`🚨 Error pinging the server: ${error.message}`);
    }
  },
};
