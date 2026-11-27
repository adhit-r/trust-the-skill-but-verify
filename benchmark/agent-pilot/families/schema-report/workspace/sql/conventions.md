# Schema conventions

Table names are plural snake_case. Every table has a BIGINT primary key named id. Foreign key columns are named after the referenced table in the singular followed by _id. Columns that hold optional data are nullable; everything else is NOT NULL.
