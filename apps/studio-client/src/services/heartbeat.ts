import { RENDER_BACKENDS } from '../utils/api';

// বাংলা মন্তব্য: এটি একটি গ্লোবাল হার্টবিট সার্ভিস, যা প্রতি ১০ মিনিট অন্তর /api/v1/live ইনফ্রাস্ট্রাকচার প্রোব দিয়ে
// সার্ভারগুলোকে স্লিপিং মোডে যাওয়া থেকে বিরত রাখে। /health থেকে /api/v1/live তে মাইগ্রেটেড
// কারণ /api/v1/live শুধু প্রসেস লাইভনেস চেক করে, Redis/DB ডিপেন্ডেন্সি টাচ করে না তাই আরো লাইটওয়েট
export const startAntiSleepHeartbeat = () => {
  // Initial ping 10 seconds after load
  setTimeout(() => {
    pingServers();
  }, 10_000);

  // Ping every 10 minutes
  setInterval(() => {
    pingServers();
  }, 10 * 60 * 1000);
};

const pingServers = () => {
  // বাংলা: শুধু বর্তমান origin-এর ব্যাকএন্ডে পিং করো — admin origin থেকে user backend-এ কল করলে
  // CORS preflight fail করে (USER_CORS_ORIGINS-এ admin origin নেই)। তাই cross-origin পিং বন্ধ করা হলো।
  const isAdmin =
    typeof window !== 'undefined' && window.location.hostname.includes('admin');
  const targets = isAdmin ? [RENDER_BACKENDS[1]] : [RENDER_BACKENDS[0]];
  targets.forEach(async (url) => {
    try {
      // বাংলা: /api/v1/live প্রোব ব্যাকেন্ডের নতুন Liveness Probe দিয়ে পিং করার জন্য মাইগ্রেটেড
      const response = await fetch(`${url}/api/v1/live`, {
        method: 'GET',
        headers: { 'Cache-Control': 'no-cache' }
      });
      if (response.ok) {
        console.warn(`[Heartbeat] ✅ Live: ${url}/api/v1/live`);
      } else {
        console.warn(`[Heartbeat] ⚠️ Non-ok response from: ${url}/api/v1/live (${response.status})`);
      }
    } catch (err) {
      console.warn(`[Heartbeat] ❌ Could not reach: ${url}/api/v1/live`);
    }
  });
};
