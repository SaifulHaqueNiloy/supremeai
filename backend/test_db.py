import os
import asyncio
from dotenv import load_dotenv
load_dotenv('.env')
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
async def check_db():
    try:
        url = os.getenv('SUPABASE_DATABASE_URL')
        if not url:
            print('No DB URL')
            return
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
        elif url.startswith('postgresql://'):
            url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        print('Connecting to', url)
        engine = create_async_engine(url, echo=False)
        async with engine.connect() as conn:
            res = await conn.execute(text('SELECT 1'))
            print('Result:', res.scalar())
    except Exception as e:
        print('DB Error:', e)

asyncio.run(check_db())
