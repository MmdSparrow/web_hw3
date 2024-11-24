CREATE TABLE file_metadata (
    file_id SERIAL PRIMARY KEY,
    file_address TEXT NOT NULL,
    bucket_name TEXT NOT NULL,
    object_name TEXT NOT NULL,
    eTag TEXT,
    file_size integer
);
