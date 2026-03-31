-- Comprehensive Test Data for Emotion Analysis Pipeline
-- This file provides diverse test cases to thoroughly test the cleaning pipeline

-- ============================================================================
-- BATCH 1: Standard Emotion Test Cases (test-batch-basic)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- Happy/Positive Emotions
('test-batch-basic', 'reddit', 'renewable', 'I absolutely LOVE solar energy! 😊 It makes me so happy!', '{"upvotes": 120}'),
('test-batch-basic', 'reddit', 'renewable', 'Amazing news! Wind farms are expanding 🚀', '{"upvotes": 150}'),
('test-batch-basic', 'reddit', 'renewable', 'So excited about electric vehicles! 😄', '{"upvotes": 95}'),

-- Angry/Frustrated Emotions
('test-batch-basic', 'reddit', 'climate', 'I am FURIOUS about climate change inaction! 😡😡', '{"upvotes": 200}'),
('test-batch-basic', 'reddit', 'climate', 'This is absolutely disgusting! 🤮 No action taken', '{"upvotes": 180}'),
('test-batch-basic', 'reddit', 'climate', 'Angry at corporate greenwashing 😤', '{"upvotes": 165}'),

-- Sad/Worried Emotions
('test-batch-basic', 'reddit', 'future', 'I''m scared about the future 😨', '{"upvotes": 110}'),
('test-batch-basic', 'reddit', 'future', 'Deeply concerned about rising temperatures 😔', '{"upvotes": 140}'),
('test-batch-basic', 'reddit', 'future', 'Feeling devastated by environmental loss 😢', '{"upvotes": 125}'),

-- Surprise/Neutral
('test-batch-basic', 'reddit', 'tech', 'Surprised by new tech advancements 😲', '{"upvotes": 100}'),
('test-batch-basic', 'reddit', 'tech', 'This is interesting information', '{"upvotes": 70}'),
('test-batch-basic', 'reddit', 'tech', 'Battery technology improvements are remarkable', '{"upvotes": 155}'),

-- Multiple Emojis
('test-batch-basic', 'reddit', 'energy', 'Love ❤️ renewable energy! 😊😊😊', '{"upvotes": 135}'),
('test-batch-basic', 'reddit', 'energy', 'Heart 💙 for electric cars 🚗', '{"upvotes": 90}'),

-- ============================================================================
-- BATCH 2: Text Cleaning Edge Cases (test-batch-cleaning)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- URLs and Links
('test-batch-cleaning', 'reddit', 'research', 'Check out this link: https://example.com for more info', '{"upvotes": 80}'),
('test-batch-cleaning', 'reddit', 'research', 'Visit www.renewable-energy.org for details', '{"upvotes": 75}'),
('test-batch-cleaning', 'reddit', 'research', 'More info at http://bit.ly/climate-data', '{"upvotes": 65}'),

-- Mentions and Hashtags
('test-batch-cleaning', 'reddit', 'news', '@climate_action just posted important news #climate #action', '{"upvotes": 110}'),
('test-batch-cleaning', 'reddit', 'news', 'Thanks @EnergyMinistry! #renewable #future', '{"upvotes": 95}'),
('test-batch-cleaning', 'reddit', 'news', 'Follow #SustainDevelop and @GreenTech for updates', '{"upvotes": 85}'),

-- Repeated Punctuation
('test-batch-cleaning', 'reddit', 'feelings', 'This is amazing!!!', '{"upvotes": 100}'),
('test-batch-cleaning', 'reddit', 'feelings', 'Why??????? No action??????', '{"upvotes": 120}'),
('test-batch-cleaning', 'reddit', 'feelings', 'Yessss!!! Finally some progress..........', '{"upvotes": 110}'),
('test-batch-cleaning', 'reddit', 'feelings', 'Noooooo this is terrible....... 😞', '{"upvotes": 105}'),

-- HTML Entities & Special Characters
('test-batch-cleaning', 'reddit', 'text', 'This &amp; that is great', '{"upvotes": 60}'),
('test-batch-cleaning', 'reddit', 'text', 'Quotes &quot;are important&quot; for climate action', '{"upvotes": 70}'),
('test-batch-cleaning', 'reddit', 'text', 'Rights &copy; 2024 &lt;statement&gt;', '{"upvotes": 55}'),

-- CamelCase Hashtags
('test-batch-cleaning', 'reddit', 'tech', 'Love #ClimateAction and #RenewableEnergy', '{"upvotes": 135}'),
('test-batch-cleaning', 'reddit', 'tech', 'Support #ElectricVehicles and #SustainableFuture', '{"upvotes": 125}'),

-- Excessive Whitespace
('test-batch-cleaning', 'reddit', 'spaces', 'This     has    too   many    spaces', '{"upvotes": 50}'),
('test-batch-cleaning', 'reddit', 'spaces', 'Multiple  newlines  and  tabs  everywhere', '{"upvotes": 45}'),

-- Mixed Case Preservation (should NOT lowercase in final)
('test-batch-cleaning', 'reddit', 'names', 'I met Jane and JACK at the climate summit', '{"upvotes": 80}'),
('test-batch-cleaning', 'reddit', 'names', 'The USA and UK are leading climate action', '{"upvotes": 90}'),

-- ============================================================================
-- BATCH 3: Complex Emotional Content (test-batch-complex)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- Negation (should preserve)
('test-batch-complex', 'reddit', 'opinion', 'I don''t like this policy, but not for the reasons you think', '{"upvotes": 100}'),
('test-batch-complex', 'reddit', 'opinion', 'This isn''t bad, it''s actually not very good', '{"upvotes": 110}'),
('test-batch-complex', 'reddit', 'opinion', 'I cannot say this is terrible because it''s worse than that', '{"upvotes": 105}'),

-- Contractions (should preserve)
('test-batch-complex', 'reddit', 'speech', 'I''ve been thinking about this. You''re right to worry', '{"upvotes": 95}'),
('test-batch-complex', 'reddit', 'speech', 'They''ll never understand we''ve already seen the evidence', '{"upvotes": 115}'),
('test-batch-complex', 'reddit', 'speech', 'It''s what we''re looking for. That''d be great!', '{"upvotes": 85}'),

-- Sarcasm (marked with emoji)
('test-batch-complex', 'reddit', 'sarcasm', 'Oh great! Another delay! 😒 Just what we needed', '{"upvotes": 140}'),
('test-batch-complex', 'reddit', 'sarcasm', 'Yeah right, this will solve everything 🙄 Sure', '{"upvotes": 130}'),

-- Slang and Informal Language (should preserve)
('test-batch-complex', 'reddit', 'slang', 'Yo this renewable energy is lit! 🔥', '{"upvotes": 120}'),
('test-batch-complex', 'reddit', 'slang', 'This policy is bonkers tbh', '{"upvotes": 100}'),
('test-batch-complex', 'reddit', 'slang', 'Ngl renewable energy is lowkey awesome', '{"upvotes": 95}'),

-- Complex Sentence Structure
('test-batch-complex', 'reddit', 'complex', 'Although I appreciate the effort, which is commendable in many ways, I still think we need stronger action, don''t you agree?', '{"upvotes": 110}'),
('test-batch-complex', 'reddit', 'complex', 'When considering the impact on communities, specifically regarding jobs and growth, we must balance environmental needs with economic concerns.', '{"upvotes": 105}'),

-- Multiple Emojis with Text
('test-batch-complex', 'reddit', 'emojis', 'I love ❤️ renewable 💚 energy 🚀 so much 😊😊😊', '{"upvotes": 125}'),
('test-batch-complex', 'reddit', 'emojis', 'This makes me angry 😠 disgusted 🤮 and sad 😢 all at once!', '{"upvotes": 135}'),

-- Very Long Text
('test-batch-complex', 'reddit', 'long', 'This is a very long post that discusses multiple aspects of renewable energy including solar, wind, geothermal, and tidal systems. It covers the benefits such as sustainability, reduced carbon emissions, job creation, and technological innovation. It also addresses challenges like initial investment costs, land requirements, intermittency issues, and grid integration concerns. Overall it represents a comprehensive view on renewable energy transition. 😊', '{"upvotes": 200}'),

-- ============================================================================
-- BATCH 4: Problematic Content (test-batch-problematic)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- Too Short (should flag)
('test-batch-problematic', 'reddit', 'short', 'ok', '{"upvotes": 10}'),
('test-batch-problematic', 'reddit', 'short', 'a', '{"upvotes": 5}'),
('test-batch-problematic', 'reddit', 'short', 'no', '{"upvotes": 8}'),

-- Non-Latin Script (should detect)
('test-batch-problematic', 'reddit', 'chinese', '这是关于气候变化的中文文本', '{"upvotes": 50}'),
('test-batch-problematic', 'reddit', 'arabic', 'هذا نص عربي عن الطاقة المتجددة', '{"upvotes": 45}'),
('test-batch-problematic', 'reddit', 'cyrillic', 'Это русский текст о возобновляемой энергии', '{"upvotes": 40}'),

-- Gibberish / Spam (should detect)
('test-batch-problematic', 'reddit', 'gibberish', 'xyzabc qwerty asdfgh zxcvbn qwertyui', '{"upvotes": 15}'),
('test-batch-problematic', 'reddit', 'gibberish', 'qqqqq wwwww eeeeee rrrrrr tttttt', '{"upvotes": 10}'),
('test-batch-problematic', 'reddit', 'spam', 'Buy crypto now!!! Click here!!! FREE GOLD!!!', '{"upvotes": 25}'),

-- Mostly Symbols (should flag)
('test-batch-problematic', 'reddit', 'symbols', '!@#$%^&*()_+-=[]{}|;:,<>?', '{"upvotes": 5}'),
('test-batch-problematic', 'reddit', 'symbols', '~~~~~~~~~~~~~~~~~~~~~~~~', '{"upvotes": 3}'),

-- ============================================================================
-- BATCH 5: Real-World Examples (test-batch-real)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- Real Reddit-like posts
('test-batch-real', 'reddit', 'discussion', 'I''ve been following this issue for years and I must say, the progress has been encouraging! 😊 Though we still have a long way to go, seeing companies commit to net-zero targets fills me with hope. #ClimateAction #Renewable', '{"upvotes": 450, "comments": 128}'),

('test-batch-real', 'reddit', 'discussion', 'Fed up with all the greenwashing!!! Companies slap "green" labels on everything 🤮 but do nothing real. It''s infuriating. We need actual policy change not marketing BS 😤😤😤', '{"upvotes": 680, "comments": 234}'),

('test-batch-real', 'reddit', 'discussion', 'Just bought my first solar panels for my house. Can''t believe how affordable they''ve become! 💚 ROI looks great at 7 years. Highly recommend anyone considering this! 😄', '{"upvotes": 520, "comments": 156}'),

('test-batch-real', 'reddit', 'discussion', 'BREAKING: New study shows electric batteries are now cheaper than fossil fuels 📉⚡ This could be the tipping point we''ve been waiting for! 🚀', '{"upvotes": 890, "comments": 305}'),

('test-batch-real', 'reddit', 'discussion', 'I''m honestly scared about what we''re leaving for our kids 😨 Climate change impacts are accelerating faster than predictions. This should terrify us into action', '{"upvotes": 320, "comments": 89}'),

('test-batch-real', 'reddit', 'discussion', 'As a renewable energy engineer AMA! Happy to answer questions about solar, wind, hydro, etc. The infrastructure is more feasible than ever 💪⚡', '{"upvotes": 1200, "comments": 450}');

-- ============================================================================
-- BATCH 6: Sentence Structure Tests (test-batch-sentences)
-- ============================================================================

INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json) VALUES

-- Preserve word order and grammar
('test-batch-sentences', 'reddit', 'grammar', 'Climate change is not real, but we should act anyway', '{"upvotes": 85}'),
('test-batch-sentences', 'reddit', 'grammar', 'Renewable energy isn''t just good for the planet, it''s good for the economy', '{"upvotes": 95}'),
('test-batch-sentences', 'reddit', 'grammar', 'Though controversial, many believe nuclear is essential for decarbonization', '{"upvotes": 110}'),

-- Preserve capitalization (SHOULD NOT lowercase ALL CAPS words)
('test-batch-sentences', 'reddit', 'caps', 'The USA, UK, and EU are leading climate initiatives', '{"upvotes": 105}'),
('test-batch-sentences', 'reddit', 'caps', 'NASA CONFIRMS ice sheet retreat accelerating', '{"upvotes": 140}'),
('test-batch-sentences', 'reddit', 'caps', 'IPCC report: action needed by 2030 urgently', '{"upvotes": 155}'),

-- ============================================================================
-- Verify inserted data
-- ============================================================================

-- Show summary of inserted data
SELECT 'Total Raw Posts' as metric, COUNT(*) AS count FROM raw_posts
UNION ALL
SELECT 'Test Batch: Basic', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-basic'
UNION ALL
SELECT 'Test Batch: Cleaning', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-cleaning'
UNION ALL
SELECT 'Test Batch: Complex', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-complex'
UNION ALL
SELECT 'Test Batch: Problematic', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-problematic'
UNION ALL
SELECT 'Test Batch: Real', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-real'
UNION ALL
SELECT 'Test Batch: Sentences', COUNT(*) FROM raw_posts WHERE batch_id = 'test-batch-sentences';

-- Show sample data
SELECT '=== SAMPLE DATA ===' as info;
SELECT batch_id, keyword, raw_text FROM raw_posts LIMIT 20;
