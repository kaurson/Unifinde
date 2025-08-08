-- Create collection_result_vectors table
CREATE TABLE IF NOT EXISTS collection_result_vectors (
    id VARCHAR(36) PRIMARY KEY,
    collection_result_id VARCHAR(36) NOT NULL UNIQUE,
    embedding LONGBLOB NOT NULL,
    embedding_dimension INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    source_text TEXT NOT NULL,
    specialized_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_result_id) REFERENCES university_data_collection_results(id)
);

-- Create index for faster lookups
CREATE INDEX idx_collection_result_vectors_collection_id ON collection_result_vectors(collection_result_id);
CREATE INDEX idx_collection_result_vectors_model ON collection_result_vectors(embedding_model); 