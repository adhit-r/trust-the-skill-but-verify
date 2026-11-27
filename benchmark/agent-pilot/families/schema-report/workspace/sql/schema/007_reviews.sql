CREATE TABLE reviews (
    id BIGINT PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(id),
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    rating SMALLINT NOT NULL,
    body TEXT
);
