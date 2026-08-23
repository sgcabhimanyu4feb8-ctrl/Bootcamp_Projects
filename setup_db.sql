-- ================================================================
-- VOYX DASHBOARD — DATABASE SETUP
-- Run this entire script once in DBeaver to:
--   1. Create the 4 tables
--   2. Import CSV data from C:/hack/
--   3. Create the orders_parsed view (handles mixed date formats)
-- ================================================================

-- Step 1: Drop existing objects (safe to re-run)
DROP VIEW  IF EXISTS orders_parsed   CASCADE;
DROP TABLE IF EXISTS orders          CASCADE;
DROP TABLE IF EXISTS products        CASCADE;
DROP TABLE IF EXISTS destinations    CASCADE;
DROP TABLE IF EXISTS users           CASCADE;

-- ================================================================
-- Step 2: Create Tables
-- ================================================================

CREATE TABLE users (
    user_id          INTEGER      PRIMARY KEY,
    name             VARCHAR(100),
    country_code     VARCHAR(10),
    mobile           VARCHAR(20),
    user_role        INTEGER,          -- 1 = customer, 2 = sales rep
    created_datetime VARCHAR(30)       -- stored as text; mixed format in CSV
);

CREATE TABLE products (
    prod_id                  INTEGER  PRIMARY KEY,
    add_on_id                VARCHAR(100),
    data_limit               INTEGER,
    sim_mode                 INTEGER,
    fup_limit                INTEGER,
    operator_id              INTEGER,
    additional_note          TEXT,
    amount                   NUMERIC(10,2),
    product_name             TEXT,
    post_fup_speed           INTEGER,
    validity                 INTEGER,
    coverage_destinations    TEXT,      -- e.g. "SGP,MYS"
    allocated_destinations   TEXT
);

CREATE TABLE destinations (
    destination_id      VARCHAR(20)  PRIMARY KEY,
    destination_type    INTEGER,
    destination_name    VARCHAR(200),
    flag_path           TEXT,
    included_destinations TEXT,
    is_active           INTEGER
);

CREATE TABLE orders (
    order_no         INTEGER      PRIMARY KEY,
    order_date_time  TEXT,              -- stored as text; two formats in CSV
    user_id          INTEGER,
    product_id       INTEGER,
    amount           NUMERIC(10,2),
    discount_amount  NUMERIC(10,2),
    created_by       INTEGER            -- references users.user_id (sales rep)
);

-- ================================================================
-- Step 3: Import CSV Data via COPY
-- NOTE: PostgreSQL reads files from the SERVER filesystem.
--       If your CSVs are elsewhere, update the paths below.
-- ================================================================

COPY users
    (user_id, name, country_code, mobile, user_role, created_datetime)
FROM 'C:/hack/users.csv'
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

COPY products
    (prod_id, add_on_id, data_limit, sim_mode, fup_limit, operator_id,
     additional_note, amount, product_name, post_fup_speed, validity,
     coverage_destinations, allocated_destinations)
FROM 'C:/hack/products.csv'
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

-- NOTE: the destinations file has a space in its name — keep the quotes
COPY destinations
    (destination_id, destination_type, destination_name, flag_path,
     included_destinations, is_active)
FROM 'C:/hack/destinations (1).csv'
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

COPY orders
    (order_no, order_date_time, user_id, product_id,
     amount, discount_amount, created_by)
FROM 'C:/hack/orders.csv'
WITH (FORMAT CSV, HEADER true, ENCODING 'UTF8');

-- ================================================================
-- Step 4: Create orders_parsed VIEW
-- Normalises two date formats found in orders.csv:
--   Format A: "MM-DD-YYYY"          e.g. "01-01-2026"
--   Format B: "MM/DD/YYYY HH:MI:SS" e.g. "01/13/2026 03:48:47"
-- ================================================================

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

-- ================================================================
-- Step 5: Verify row counts
-- ================================================================

SELECT 'users'                           AS table_name, COUNT(*) AS rows FROM users
UNION ALL
SELECT 'products',                                      COUNT(*) FROM products
UNION ALL
SELECT 'destinations',                                  COUNT(*) FROM destinations
UNION ALL
SELECT 'orders',                                        COUNT(*) FROM orders
UNION ALL
SELECT 'orders_parsed (valid dates)',                   COUNT(*) FROM orders_parsed
 WHERE order_date IS NOT NULL;
