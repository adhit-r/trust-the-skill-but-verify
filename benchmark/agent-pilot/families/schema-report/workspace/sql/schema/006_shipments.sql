CREATE TABLE shipments (
    id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    carrier VARCHAR(40) NOT NULL,
    tracking_code VARCHAR(60),
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);
