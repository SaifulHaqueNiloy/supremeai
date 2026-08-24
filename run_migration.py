import asyncio
import os
import asyncpg

async def run_migration():
    # Setup database url
    db_url = 'postgresql://postgres.xtvkltzmberxekoamala:NjelComBd_2026_Prod!@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
    
    # Read sql file
    with open('../migrations/phase3_multi_tenant_schema.sql', 'r') as f:
        sql = f.read()
        
    print('Connecting to database...')
    conn = await asyncpg.connect(db_url)
    try:
        print('Executing migration...')
        await conn.execute(sql)
        print('Migration applied successfully!')
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
