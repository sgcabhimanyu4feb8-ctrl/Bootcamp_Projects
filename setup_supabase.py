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

def setup_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Create the view
    print("Creating view orders_parsed...")
    cur.execute("""
        CREATE OR REPLACE VIEW orders_parsed AS
        SELECT
            order_no,
            CASE
                WHEN order_date_time ~ '^\d{2}-\d{2}-\d{4}$'
                    THEN TO_DATE(order_date_time, 'MM-DD-YYYY')
                WHEN order_date_time ~ '^\d{2}/\d{2}/\d{4}'
                    THEN TO_TIMESTAMP(order_date_time, 'MM/DD/YYYY HH24:MI:SS')::DATE
                ELSE NULL
            END                 AS order_date,
            user_id,
            product_id,
            amount,
            discount_amount,
            created_by
        FROM orders;
    """)
    conn.commit()

    # Import products
    print("Importing products...")
    with open('c:\\hack\\products.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)
        # Double quote the headers
        cols = ', '.join([f'"{h}"' for h in headers])
        placeholders = ', '.join(['%s'] * len(headers))
        insert_query = f'INSERT INTO products ({cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'
        
        count = 0
        for row in reader:
            # handle empty strings for numeric cols, e.g., fupLimit, operatorId if empty
            processed_row = [val if val != '' else None for val in row]
            try:
                cur.execute(insert_query, processed_row)
                count += 1
            except Exception as e:
                print(f"Error inserting row: {row}")
                print(e)
                conn.rollback()
                break
        
        print(f"Inserted {count} products.")
        conn.commit()

    conn.close()
    print("Done!")

if __name__ == "__main__":
    setup_db()
