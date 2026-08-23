import psycopg2
import csv

DB_CONFIG = {
    "host":     "aws-1-ap-southeast-2.pooler.supabase.com",
    "port":     6543,
    "dbname":   "postgres",
    "user":     "postgres.slzxowwkgcksqcwnweut",
    "password": "Abhi@1234#56",
    "sslmode":  "require"
}

def insert_products():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Importing products...")
    with open('c:\\hack\\products.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        cols = ', '.join([f'"{h}"' for h in headers])
        placeholders = ', '.join(['%s'] * len(headers))
        insert_query = f'INSERT INTO products ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
        
        count = 0
        for row in reader:
            processed_row = [val if val != '' else None for val in row]
            try:
                cur.execute(insert_query, processed_row)
                count += 1
            except Exception as e:
                print(f"Skipping row due to error: {row[0]}")
                # We don't need rollback because autocommit is true
        
        print(f"Successfully processed {count} products.")

    conn.close()
    print("Done!")

if __name__ == "__main__":
    insert_products()
