import psycopg2
conn = psycopg2.connect(
    host='aws-1-ap-southeast-2.pooler.supabase.com', port=6543,
    dbname='postgres', user='postgres.slzxowwkgcksqcwnweut', password='Abhi@1234#56', sslmode='require'
)
cur = conn.cursor()
cur.execute('ALTER TABLE products ALTER COLUMN "coverageDestinations" TYPE TEXT;')
cur.execute('ALTER TABLE products ALTER COLUMN "additional_note" TYPE TEXT;')
cur.execute('ALTER TABLE products ALTER COLUMN "productName" TYPE TEXT;')
conn.commit()
conn.close()
