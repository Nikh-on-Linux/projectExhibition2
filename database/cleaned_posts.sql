-- Create cleaned_posts table
-- Stores cleaned and processed posts

CREATE TABLE IF NOT EXISTS cleaned_posts (
    id SERIAL PRIMARY KEY,
    raw_post_id INT NOT NULL,
    cleaned_text TEXT NOT NULL,
    language VARCHAR(50),
    emoji_converted BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_post_id) REFERENCES raw_posts(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX idx_cleaned_posts_raw_post_id ON cleaned_posts(raw_post_id);
CREATE INDEX idx_cleaned_posts_language ON cleaned_posts(language);
CREATE INDEX idx_cleaned_posts_processed_at ON cleaned_posts(processed_at);
