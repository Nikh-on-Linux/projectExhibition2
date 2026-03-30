#!/bin/bash

echo "🔍 Verifying Database Data"
echo "=========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Table Counts:${NC}"
psql -h localhost -p 5432 -U emotion_app -d emotion_db -c "
SELECT 'raw_posts' as table_name, COUNT(*) as count FROM raw_posts
UNION ALL
SELECT 'cleaned_posts', COUNT(*) FROM cleaned_posts
UNION ALL
SELECT 'enriched_posts', COUNT(*) FROM enriched_posts;"

echo ""
echo -e "${YELLOW}Data by Batch:${NC}"
psql -h localhost -p 5432 -U emotion_app -d emotion_db -c "
SELECT batch_id, COUNT(*) as posts FROM cleaned_posts GROUP BY batch_id ORDER BY batch_id;"

echo ""
echo -e "${YELLOW}Sample Cleaned Posts:${NC}"
psql -h localhost -p 5432 -U emotion_app -d emotion_db -c "
SELECT batch_id, id, cleaned_text FROM cleaned_posts LIMIT 5;"

echo ""
echo -e "${GREEN}✅ Verification complete!${NC}"
