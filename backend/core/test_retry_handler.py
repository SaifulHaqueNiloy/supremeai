from __future__ import annotations

import asyncio
import random
from loguru import logger

from .retry_handler import retry_handler, retry_with_budget


# Callback functions for demonstration
def on_retry_callback(attempt: int, exception: Exception):
    logger.info(f"কলব্যাক: চেষ্টা #{attempt} ব্যর্থ হয়েছে - {exception}")


def on_max_retries_callback(exception: Exception):
    logger.error(f"কলব্যাক: সর্বাধিক রিট্রাই সম্পন্ন - চূড়ান্ত এক্সেপশন: {exception}")


@retry_handler(
    max_retries=3,
    delay=0.5,
    backoff=2.0,
    on_retry_callback=on_retry_callback,
    on_max_retries_callback=on_max_retries_callback,
)
async def unreliable_async_api_call(simulate_failure: bool = True) -> str:
    """
    বাংলা মন্তব্য: অস্থায়ী অ্যাপিআই কল যেটি ব্যর্থ হতে পারে, রিট্রাই হ্যান্ডলার টেস্ট করার জন্য।
    """
    logger.info("অ্যাপিআই কল চলছে...")

    if simulate_failure and random.random() < 0.7:  # 70% সম্ভাবনায় ব্যর্থ হবে
        raise ConnectionError("অ্যাপিআই কল ব্যর্থ হয়েছে: কানেকশন টাইমআউট")

    return "সফল রেসপন্স"


@retry_with_budget(max_retries=2, delay=0.3, backoff=1.5)
async def budgeted_api_call(simulate_failure: bool = True) -> str:
    """
    বাংলা মন্তব্য: রিট্রাই বাজেট সিস্টেম সহ অ্যাপিআই কল।
    """
    logger.info("বাজেট সহ অ্যাপিআই কল চলছে...")

    if simulate_failure and random.random() < 0.8:  # 80% সম্ভাবনায় ব্যর্থ হবে
        raise ConnectionError("অ্যাপিআই কল ব্যর্থ হয়েছে: কানেকশন টাইমআউট")

    return "সফল রেসপন্স"


async def main():
    """
    বাংলা মন্তব্য: রিট্রাই হ্যান্ডলার ডেমোনস্ট্রেশন ফাংশন।
    """
    logger.info("রিট্রাই হ্যান্ডলার ডেমোনস্ট্রেশন শুরু হচ্ছে...")

    # Test basic retry handler
    logger.info("\n1. বেসিক রিট্রাই হ্যান্ডলার টেস্ট করা হচ্ছে:")
    try:
        result = await unreliable_async_api_call(simulate_failure=True)
        logger.info(f"অ্যাসিঙ্ক ফাংশন থেকে রেসপন্স: {result}")
    except Exception as e:
        logger.error(f"অ্যাসিঙ্ক ফাংশন চূড়ান্তভাবে ব্যর্থ হয়েছে: {e}")

    # Test budgeted retry handler
    logger.info("\n2. বাজেট সহ রিট্রাই হ্যান্ডলার টেস্ট করা হচ্ছে:")
    try:
        result = await budgeted_api_call(simulate_failure=True)
        logger.info(f"বাজেট সহ ফাংশন থেকে রেসপন্স: {result}")
    except Exception as e:
        logger.error(f"বাজেট সহ ফাংশন চূড়ান্তভাবে ব্যর্থ হয়েছে: {e}")

    # Test with a function that will eventually succeed
    logger.info("\n3. সফল হওয়ার সম্ভাবনা সহ টেস্ট করা হচ্ছে:")
    attempt_count = 0

    @retry_handler(max_retries=3, delay=0.1, backoff=1.5)
    async def eventually_successful_call():
        nonlocal attempt_count
        attempt_count += 1
        logger.info(f"চেষ্টা #{attempt_count}")

        if attempt_count < 3:  # First 2 attempts fail, 3rd succeeds
            raise TimeoutError("টাইমআউট এরর")

        return f"সফল! #{attempt_count} চেষ্টায়"

    try:
        result = await eventually_successful_call()
        logger.info(f"ফাইনাল রেসপন্স: {result}")
    except Exception as e:
        logger.error(f"ফাইনাল রেসপন্স টেস্ট চূড়ান্তভাবে ব্যর্থ হয়েছে: {e}")


if __name__ == "__main__":
    asyncio.run(main())
