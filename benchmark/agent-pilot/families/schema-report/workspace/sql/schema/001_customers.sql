CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL,
    region_code CHAR(2) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
