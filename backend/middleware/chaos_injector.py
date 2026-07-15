"""Chaos Injector Middleware for fault injection testing.

বাংলা: ক্যাওস ইঞ্জেকশন মিডলওয়্যার।
"""
import asyncio
import os
import random

from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class ChaosInjectorMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Fault Injection & Chaos Engine.
    Simulates real-world network degradation, packet loss, and latency spikes.
    Active ONLY when LOCAL_CHAOS_MODE=true.
    """

    def __init__(self, app):
        super().__init__(app)
        from core.config import settings

        self.chaos_enabled = os.getenv("LOCAL_CHAOS_MODE", "false").lower() == "true" and settings.env.lower() != "production"
        # ক্যাওস প্যারামিটারস (প্রোডাকশন গ্রেড ফল্ট সিমুলেশন)
        # বাংলা: হার্ডকোডেড ভ্যালু না থাকায় env var থেকে নেওয়া হয়
        self.packet_drop_rate = float(os.getenv("CHAOS_PACKET_DROP_RATE", "0.20"))
        self.max_latency_spike = float(os.getenv("CHAOS_MAX_LATENCY_SPIKE", "3.5"))
        self.latency_spike_chance = float(os.getenv("CHAOS_LATENCY_SPIKE_CHANCE", "0.30"))

    async def dispatch(self, request: Request, call_next):
        if not self.chaos_enabled:
            return await call_next(request)

        # ১. কৃত্রিম ল্যাটেন্সি স্পাইক সিমুলেশন (Slow Network/API Gateway Latency)
        if random.random() < self.latency_spike_chance:
            delay = random.uniform(0.5, self.max_latency_spike)
            logger.warning(f"🔌 [CHAOS ENGINE] Injecting artificial network lag: {delay:.2f}s on {request.url.path}")
            await asyncio.sleep(delay)

        # ২. কৃত্রিম প্যাকেট ড্রপ/কানেকশন ফেইলর সিমুলেশন (Packet Loss / Upstream Outage)
        if random.random() < self.packet_drop_rate:
            logger.critical(f"💥 [CHAOS ENGINE] Simulated Packet Drop! Severing connection for {request.url.path}")
            return JSONResponse(
                status_code=504,
                content={
                    "title": "Gateway Timeout (Chaos Simulated)",
                    "detail": "Upstream connection dropped due to artificial network degradation.",
                    "instance": request.url.path,
                },
            )

        # ৩. যদি রিকোয়েস্ট ক্যাওস ফিল্টার সার্ভিভ করে, তবে নরমাল এক্সিকিউশন হবে
        return await call_next(request)
