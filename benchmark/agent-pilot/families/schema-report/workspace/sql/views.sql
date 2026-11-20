CREATE VIEW open_invoices AS
SELECT id, order_id, due_on FROM invoices WHERE paid_on IS NULL;
