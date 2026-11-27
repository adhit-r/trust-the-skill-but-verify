CREATE TABLE invoices (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    issued_on DATE NOT NULL,
    due_on DATE NOT NULL,
    paid_on DATE
);
