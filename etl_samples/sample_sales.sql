INSERT INTO sales_summary
SELECT
    c.customer_name,
    SUM(o.amount) AS total_sales,
    COUNT(o.order_id) AS order_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'completed'
GROUP BY c.customer_name;