CREATE INDEX idx_orders_customer ON orders (customer_id, placed_at);
CREATE INDEX idx_order_items_order ON order_items (order_id);
CREATE INDEX idx_invoices_due ON invoices (due_on);
CREATE INDEX idx_shipments_order ON shipments (order_id);
