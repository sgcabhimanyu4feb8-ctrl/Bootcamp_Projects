import psycopg2
conn = psycopg2.connect(
    host='aws-1-ap-southeast-2.pooler.supabase.com', port=6543,
    dbname='postgres', user='postgres.slzxowwkgcksqcwnweut', password='Abhi@1234#56', sslmode='require'
)
cur = conn.cursor()
cur.execute('ALTER TABLE products ALTER COLUMN "addOnId" TYPE VARCHAR(255);')
conn.commit()
conn.close()
