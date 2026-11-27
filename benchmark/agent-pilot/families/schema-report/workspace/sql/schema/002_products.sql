CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    sku VARCHAR(40) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    discontinued BOOLEAN NOT NULL
);
