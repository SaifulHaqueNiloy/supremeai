import { RENDER_BACKENDS } from '../utils/api';

// বাংলা মন্তব্য: এটি একটি গ্লোবাল হার্টবিট সার্ভিস, যা প্রতি ১০ মিনিট অন্তর সার্ভারগুলোকে পিং করে স্লিপিং মোডে যাওয়া থেকে বিরত রাখে।
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
  RENDER_BACKENDS.forEach(async (url) => {
    try {
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        // Optional: keep it super light
        headers: { 'Cache-Control': 'no-cache' }
      });
      if (response.ok) {
        console.log(`[Heartbeat] Pinged: ${url}`);
      }
    } catch (err) {
      console.warn(`[Heartbeat] Could not reach: ${url}`);
    }
  });
};
