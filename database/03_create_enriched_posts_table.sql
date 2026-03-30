-- Create enriched_posts table
-- Stores posts with AI-powered emotion analysis

CREATE TABLE IF NOT EXISTS enriched_posts (
    id SERIAL PRIMARY KEY,
    cleaned_post_id INT NOT NULL,
    batch_id VARCHAR(255) NOT NULL,
    emotion_label VARCHAR(50),
    confidence DECIMAL(3, 2),
    emotion_intensity DECIMAL(3, 2),
    emotion_distribution_data JSONB,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cleaned_post_id) REFERENCES cleaned_posts(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX idx_enriched_posts_batch_id ON enriched_posts(batch_id);
CREATE INDEX idx_enriched_posts_cleaned_post_id ON enriched_posts(cleaned_post_id);
CREATE INDEX idx_enriched_posts_emotion_label ON enriched_posts(emotion_label);
CREATE INDEX idx_enriched_posts_analyzed_at ON enriched_posts(analyzed_at);
