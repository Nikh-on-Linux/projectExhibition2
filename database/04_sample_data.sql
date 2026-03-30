-- Sample Test Data for Emotion Analysis Pipeline
-- This file populates the database with sample data for testing

-- First, insert sample raw posts with batch_id for test-batch-001
INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES
('test-batch-001', 'reddit', 'climate change', 'I love climate solutions! ❤️ They make me so happy!', '{"upvotes": 120, "comments": 45}'),
('test-batch-001', 'reddit', 'climate change', 'Climate change makes me angry! 😠 We need action NOW!', '{"upvotes": 250, "comments": 89}'),
('test-batch-001', 'reddit', 'climate change', 'Im scared of climate change impact 😨 What will happen?', '{"upvotes": 180, "comments": 67}'),
('test-batch-001', 'reddit', 'renewable energy', 'Solar panels are amazing! Joy to see clean energy growing 😊', '{"upvotes": 95, "comments": 34}'),
('test-batch-001', 'reddit', 'renewable energy', 'Disgusting how slow renewable adoption is 🤢', '{"upvotes": 140, "comments": 52}'),
('test-batch-001', 'reddit', 'renewable energy', 'Surprised by how affordable solar became! 😲', '{"upvotes": 210, "comments": 71}'),
('test-batch-001', 'reddit', 'electric vehicles', 'Electric cars are wonderful! I am so happy with my Tesla! 😊😊', '{"upvotes": 165, "comments": 58}'),
('test-batch-001', 'reddit', 'electric vehicles', 'EV charging infrastructure is still terrible 😞', '{"upvotes": 200, "comments": 76}'),
('test-batch-001', 'reddit', 'electric vehicles', 'Concerned about battery production impact 😟', '{"upvotes": 130, "comments": 44}'),
('test-batch-001', 'reddit', 'green technology', 'Excited about new green tech innovations! 🚀😊', '{"upvotes": 175, "comments": 62}'),
('test-batch-001', 'reddit', 'green technology', 'Frustrated with greenwashing 😤', '{"upvotes": 220, "comments": 81}'),
('test-batch-001', 'reddit', 'green technology', 'Neutral opinion: green tech has pros and cons', '{"upvotes": 88, "comments": 31}'),
('test-batch-001', 'reddit', 'sustainability', 'Love sustainable practices! Makes me very happy 💚', '{"upvotes": 145, "comments": 48}'),
('test-batch-001', 'reddit', 'sustainability', 'Angry at corporate greenwashing 😠😠', '{"upvotes": 190, "comments": 72}'),
('test-batch-001', 'reddit', 'sustainability', 'Scared about water scarcity from unsustainable practices', '{"upvotes": 160, "comments": 55}'),
('test-batch-001', 'reddit', 'carbon neutral', 'Amazed and delighted with carbon neutral goals 😄', '{"upvotes": 125, "comments": 40}'),
('test-batch-001', 'reddit', 'carbon neutral', 'Disgusted by carbon emissions 🤮', '{"upvotes": 235, "comments": 84}'),
('test-batch-001', 'reddit', 'carbon neutral', 'Surprised by carbon offset effectiveness', '{"upvotes": 110, "comments": 38}'),
('test-batch-001', 'reddit', 'climate action', 'I am joyful about climate action initiatives! 🌍😊', '{"upvotes": 205, "comments": 69}'),
('test-batch-001', 'reddit', 'climate action', 'Furious about lack of real climate action 😡', '{"upvotes": 270, "comments": 95}');

-- Now insert cleaned posts with batch_id "test-batch-001"
-- These are the same posts but cleaned (lowercase, no emojis, etc.)
INSERT INTO cleaned_posts (raw_post_id, batch_id, cleaned_text, language, emoji_converted, processed_at) 
SELECT 
    id,
    'test-batch-001' as batch_id,
    LOWER(REGEXP_REPLACE(REGEXP_REPLACE(raw_text, '[😊😠😨🤢😲😞😟🚀💚🤮🌍❤️😤😄😡😂💔🔥✨]', ''), '\s+', ' ', 'g')) as cleaned_text,
    'en' as language,
    true as emoji_converted,
    CURRENT_TIMESTAMP
FROM raw_posts
WHERE id BETWEEN 1 AND 20;

-- Insert additional raw posts with batch_id for test-batch-002
-- These are different test cases for testing concurrent batch processing
INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES
('test-batch-002', 'reddit', 'net zero', 'Net zero goals are thrilling! 🎉', '{"upvotes": 105, "comments": 28}'),
('test-batch-002', 'reddit', 'net zero', 'Net zero is impossible and frustrating 😡', '{"upvotes": 180, "comments": 64}'),
('test-batch-002', 'reddit', 'net zero', 'Concerned about net zero timeline', '{"upvotes": 145, "comments": 45}'),
('test-batch-002', 'reddit', 'energy transition', 'Happy about energy transition progress! 😊', '{"upvotes": 160, "comments": 52}'),
('test-batch-002', 'reddit', 'energy transition', 'Angry at slow energy transition', '{"upvotes": 210, "comments": 73}'),
('test-batch-002', 'reddit', 'energy transition', 'Surprised by battery technology advances 😲', '{"upvotes": 175, "comments": 58}'),
('test-batch-002', 'reddit', 'climate policy', 'Delighted with new climate policies 😄', '{"upvotes": 185, "comments": 61}'),
('test-batch-002', 'reddit', 'climate policy', 'Furious about weak climate policies 😤', '{"upvotes": 240, "comments": 88}'),
('test-batch-002', 'reddit', 'climate policy', 'Fearful about policy implementation 😟', '{"upvotes": 120, "comments": 39}'),
('test-batch-002', 'reddit', 'conservation', 'Love wildlife conservation efforts! 💚', '{"upvotes": 170, "comments": 56}');

INSERT INTO cleaned_posts (raw_post_id, batch_id, cleaned_text, language, emoji_converted, processed_at) 
SELECT 
    id,
    'test-batch-002' as batch_id,
    LOWER(REGEXP_REPLACE(REGEXP_REPLACE(raw_text, '[😊😠😨🤢😲😞😟🚀💚🤮🌍❤️😤😄😡😂💔🔥✨🎉]', ''), '\s+', ' ', 'g')) as cleaned_text,
    'en' as language,
    true as emoji_converted,
    CURRENT_TIMESTAMP
FROM raw_posts
WHERE id BETWEEN 21 AND 30;

-- Test data for batch_id "test-batch-003" - Various emotions
INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES
('test-batch-003', 'reddit', 'renewable', 'This is absolutely wonderful and makes me joyful! 😊', '{"upvotes": 150}'),
('test-batch-003', 'reddit', 'renewable', 'I am very upset and angry about this! 😠', '{"upvotes": 200}'),
('test-batch-003', 'reddit', 'renewable', 'This scares me and I am afraid 😨', '{"upvotes": 110}'),
('test-batch-003', 'reddit', 'renewable', 'This is disgusting and repulsive 🤢', '{"upvotes": 180}'),
('test-batch-003', 'reddit', 'renewable', 'I feel sad and sorrowful 😢', '{"upvotes": 125}'),
('test-batch-003', 'reddit', 'renewable', 'Wow I am so surprised! 😲', '{"upvotes": 165}'),
('test-batch-003', 'reddit', 'renewable', 'This is just neutral information', '{"upvotes": 95}'),
('test-batch-003', 'reddit', 'renewable', 'Happy and excited about future! 🚀😊', '{"upvotes": 210}'),
('test-batch-003', 'reddit', 'renewable', 'Excellent clean energy innovation thrills me! 💚', '{"upvotes": 175}'),
('test-batch-003', 'reddit', 'renewable', 'Really furious at environmental destruction! 😡', '{"upvotes": 240}');

INSERT INTO cleaned_posts (raw_post_id, batch_id, cleaned_text, language, emoji_converted, processed_at) 
SELECT 
    id,
    'test-batch-003' as batch_id,
    LOWER(REGEXP_REPLACE(REGEXP_REPLACE(raw_text, '[😊😠😨🤢😲😞😟🚀💚🤮🌍❤️😤😄😡😂💔🔥✨🎉😢]', ''), '\s+', ' ', 'g')) as cleaned_text,
    'en' as language,
    true as emoji_converted,
    CURRENT_TIMESTAMP
FROM raw_posts
WHERE id BETWEEN 31 AND 40;

-- Verify the data was inserted
SELECT COUNT(*) as total_raw_posts FROM raw_posts;
SELECT COUNT(*) as total_cleaned_posts FROM cleaned_posts;
SELECT batch_id, COUNT(*) as count_per_batch FROM cleaned_posts GROUP BY batch_id;
SELECT batch_id, cleaned_text FROM cleaned_posts LIMIT 15;
