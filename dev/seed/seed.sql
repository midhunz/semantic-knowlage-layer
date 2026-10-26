-- Run against Trino catalog "lake":  trino --server localhost:8080 --catalog lake -f dev/seed/seed.sql
CREATE SCHEMA IF NOT EXISTS sales;
CREATE TABLE IF NOT EXISTS sales.dim_customer (customer_id bigint, email varchar, country_code varchar, segment varchar);
CREATE TABLE IF NOT EXISTS sales.dim_product (product_id bigint, product_name varchar, category varchar, list_price double);
CREATE TABLE IF NOT EXISTS sales.dim_date (date_key date, year integer, month integer, is_weekend boolean);
CREATE TABLE IF NOT EXISTS sales.fact_orders (
  order_id bigint, order_line integer, customer_id bigint, product_id bigint, order_date date,
  quantity integer, gross_amount double, discount_amount double, net_amount double, status varchar
) WITH (partitioning = ARRAY['month(order_date)']);
INSERT INTO sales.dim_customer VALUES (1,'a@example.com','US','enterprise'),(2,'b@example.com','DE','smb');
INSERT INTO sales.dim_product VALUES (10,'Widget','hardware',9.99),(11,'Gadget','hardware',19.99);
INSERT INTO sales.dim_date VALUES (DATE '2026-01-05',2026,1,false),(DATE '2026-01-10',2026,1,true);
INSERT INTO sales.fact_orders VALUES
  (100,1,1,10,DATE '2026-01-05',2,19.98,0,19.98,'C'),
  (101,1,2,11,DATE '2026-01-10',1,19.99,2,17.99,'S');
