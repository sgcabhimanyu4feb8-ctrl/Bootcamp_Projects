import re

with open('c:/hack/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix ROUND(SUM(amount),2)
content = re.sub(r'ROUND\(SUM\((op\.)?amount\),\s*2\)', r'ROUND(SUM(\1amount)::numeric, 2)', content)

# Fix ROUND(COALESCE(..., 0), 2)
content = re.sub(r'ROUND\(COALESCE\(([^,]+),\s*0\),\s*2\)', r'ROUND(COALESCE(\1, 0)::numeric, 2)', content)

# Fix ROUND(m.mtd_revenue / m.mtd_orders, 2)
content = re.sub(r'ROUND\(m\.mtd_revenue \/ m\.mtd_orders,\s*2\)', r'ROUND((m.mtd_revenue / m.mtd_orders)::numeric, 2)', content)

with open('c:/hack/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py patched!")
