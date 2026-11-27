CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    status VARCHAR(20) NOT NULL,
    placed_at TIMESTAMP NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL
);
