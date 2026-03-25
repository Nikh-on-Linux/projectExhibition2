-- Create raw_posts table
-- Stores original posts fetched from Reddit API

CREATE TABLE IF NOT EXISTS raw_posts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    keyword VARCHAR(255),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_json JSONB,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_raw_posts_platform ON raw_posts(platform);
CREATE INDEX idx_raw_posts_keyword ON raw_posts(keyword);
CREATE INDEX idx_raw_posts_created_at ON raw_posts(created_at);
