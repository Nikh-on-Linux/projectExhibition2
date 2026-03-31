#!/usr/bin/env python3
"""
Local Database Setup & Test Data Generator

This script helps you:
1. Create database and tables locally
2. Insert comprehensive test data
3. Verify the setup
4. Generate additional test data programmatically
"""

import asyncio
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test data samples organized by emotion and characteristics
TEST_DATA = {
    "test-batch-basic": [
        {
            "platform": "reddit",
            "keyword": "renewable",
            "raw_text": "I absolutely LOVE solar energy! 😊 It makes me so happy!",
            "emotion": "joy"
        },
        {
            "platform": "reddit",
            "keyword": "renewable",
            "raw_text": "Amazing news! Wind farms are expanding 🚀",
            "emotion": "joy"
        },
        {
            "platform": "reddit",
            "keyword": "climate",
            "raw_text": "I am FURIOUS about climate change inaction! 😡😡",
            "emotion": "anger"
        },
        {
            "platform": "reddit",
            "keyword": "climate",
            "raw_text": "This is absolutely disgusting! 🤮 No action taken",
            "emotion": "disgust"
        },
        {
            "platform": "reddit",
            "keyword": "future",
            "raw_text": "I'm scared about the future 😨",
            "emotion": "fear"
        },
        {
            "platform": "reddit",
            "keyword": "future",
            "raw_text": "Deeply concerned about rising temperatures 😔",
            "emotion": "sadness"
        },
        {
            "platform": "reddit",
            "keyword": "tech",
            "raw_text": "Surprised by new tech advancements 😲",
            "emotion": "surprise"
        },
        {
            "platform": "reddit",
            "keyword": "tech",
            "raw_text": "This is interesting information",
            "emotion": "neutral"
        },
    ],
    "test-batch-cleaning": [
        {
            "platform": "reddit",
            "keyword": "research",
            "raw_text": "Check out this link: https://example.com for more info",
            "characteristic": "has_urls"
        },
        {
            "platform": "reddit",
            "keyword": "news",
            "raw_text": "@climate_action just posted important news #climate #action",
            "characteristic": "has_mentions_hashtags"
        },
        {
            "platform": "reddit",
            "keyword": "feelings",
            "raw_text": "This is amazing!!!",
            "characteristic": "repeated_punctuation"
        },
        {
            "platform": "reddit",
            "keyword": "text",
            "raw_text": "This &amp; that is great",
            "characteristic": "html_entities"
        },
        {
            "platform": "reddit",
            "keyword": "tech",
            "raw_text": "Love #ClimateAction and #RenewableEnergy",
            "characteristic": "camelcase_hashtags"
        },
        {
            "platform": "reddit",
            "keyword": "spaces",
            "raw_text": "This     has    too   many    spaces",
            "characteristic": "excess_whitespace"
        },
    ],
    "test-batch-complex": [
        {
            "platform": "reddit",
            "keyword": "opinion",
            "raw_text": "I don't like this policy, but not for the reasons you think",
            "characteristic": "negation"
        },
        {
            "platform": "reddit",
            "keyword": "speech",
            "raw_text": "I've been thinking about this. You're right to worry",
            "characteristic": "contractions"
        },
        {
            "platform": "reddit",
            "keyword": "sarcasm",
            "raw_text": "Oh great! Another delay! 😒 Just what we needed",
            "characteristic": "sarcasm"
        },
        {
            "platform": "reddit",
            "keyword": "slang",
            "raw_text": "Yo this renewable energy is lit! 🔥",
            "characteristic": "slang"
        },
        {
            "platform": "reddit",
            "keyword": "emojis",
            "raw_text": "I love ❤️ renewable 💚 energy 🚀 so much 😊😊😊",
            "characteristic": "multiple_emojis"
        },
    ],
    "test-batch-problematic": [
        {
            "platform": "reddit",
            "keyword": "short",
            "raw_text": "ok",
            "characteristic": "too_short"
        },
        {
            "platform": "reddit",
            "keyword": "gibberish",
            "raw_text": "xyzabc qwerty asdfgh zxcvbn",
            "characteristic": "gibberish"
        },
        {
            "platform": "reddit",
            "keyword": "symbols",
            "raw_text": "!@#$%^&*()_+-=[]{}|;:,<>?",
            "characteristic": "mostly_symbols"
        },
    ],
    "test-batch-real": [
        {
            "platform": "reddit",
            "keyword": "discussion",
            "raw_text": "I've been following this issue for years and I must say, the progress has been encouraging! 😊 Though we still have a long way to go, seeing companies commit to net-zero targets fills me with hope. #ClimateAction #Renewable",
            "emotion": "joy",
            "upvotes": 450
        },
        {
            "platform": "reddit",
            "keyword": "discussion",
            "raw_text": "Fed up with all the greenwashing!!! Companies slap 'green' labels on everything 🤮 but do nothing real. It's infuriating. We need actual policy change not marketing BS 😤😤😤",
            "emotion": "anger",
            "upvotes": 680
        },
        {
            "platform": "reddit",
            "keyword": "discussion",
            "raw_text": "Just bought my first solar panels for my house. Can't believe how affordable they've become! 💚 ROI looks great at 7 years. Highly recommend anyone considering this! 😄",
            "emotion": "joy",
            "upvotes": 520
        },
        {
            "platform": "reddit",
            "keyword": "discussion",
            "raw_text": "I'm honestly scared about what we're leaving for our kids 😨 Climate change impacts are accelerating faster than predictions. This should terrify us into action",
            "emotion": "fear",
            "upvotes": 320
        },
    ]
}


def print_banner(title):
    """Print a formatted banner"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def get_connection_string():
    """Get database connection string from environment or use default"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://emotion_app:emotion_password_123@localhost:5432/emotion_db"
    )


async def async_insert_raw_posts(connection_string, batch_id, posts_list):
    """Insert raw posts into database using async"""
    try:
        # Convert to async connection string
        async_connection_string = connection_string.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        
        engine = create_async_engine(async_connection_string, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            for post_data in posts_list:
                # Prepare insert data
                insert_dict = {
                    "batch_id": batch_id,
                    "platform": post_data.get("platform", "reddit"),
                    "keyword": post_data.get("keyword", ""),
                    "raw_text": post_data.get("raw_text", ""),
                    "raw_json": {
                        "upvotes": post_data.get("upvotes", 100),
                        "emotion": post_data.get("emotion", "neutral"),
                        "characteristic": post_data.get("characteristic", "standard")
                    }
                }
                
                # Insert using raw SQL
                query = text("""
                    INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json)
                    VALUES (:batch_id, :platform, :keyword, :raw_text, :raw_json::jsonb)
                """)
                await session.execute(query, insert_dict)
            
            await session.commit()
            print(f"✓ Inserted {len(posts_list)} posts for batch: {batch_id}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Error inserting data: {e}")
        return False


def insert_raw_posts_sync(connection_string, batch_id, posts_list):
    """Insert raw posts using synchronous connection"""
    try:
        engine = create_engine(connection_string, echo=False)
        
        with engine.connect() as conn:
            for post_data in posts_list:
                insert_query = text("""
                    INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json, created_at, fetched_at)
                    VALUES (:batch_id, :platform, :keyword, :raw_text, :raw_json::jsonb, NOW(), NOW())
                """)
                
                params = {
                    "batch_id": batch_id,
                    "platform": post_data.get("platform", "reddit"),
                    "keyword": post_data.get("keyword", ""),
                    "raw_text": post_data.get("raw_text", ""),
                    "raw_json": {
                        "upvotes": post_data.get("upvotes", 100),
                        "emotion": post_data.get("emotion", "neutral"),
                        "characteristic": post_data.get("characteristic", "standard")
                    }
                }
                
                conn.execute(insert_query, params)
            
            conn.commit()
            print(f"✓ Inserted {len(posts_list)} posts for batch: {batch_id}")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Error inserting data: {e}")
        return False


def verify_database(connection_string):
    """Verify database tables and show statistics"""
    try:
        engine = create_engine(connection_string, echo=False)
        
        with engine.connect() as conn:
            # Check tables exist
            print("\n📊 Database Statistics:\n")
            
            queries = {
                "Total Raw Posts": "SELECT COUNT(*) FROM raw_posts",
                "Total Cleaned Posts": "SELECT COUNT(*) FROM cleaned_posts",
                "Unique Batches": "SELECT COUNT(DISTINCT batch_id) FROM raw_posts",
                "Unique Platforms": "SELECT COUNT(DISTINCT platform) FROM raw_posts",
                "Unique Keywords": "SELECT COUNT(DISTINCT keyword) FROM raw_posts",
            }
            
            for label, query in queries.items():
                result = conn.execute(text(query)).scalar()
                print(f"  {label:.<40} {result}")
            
            # Show sample posts
            print("\n📝 Sample Raw Posts (first 5):\n")
            sample_query = text("""
                SELECT id, batch_id, keyword, raw_text 
                FROM raw_posts 
                LIMIT 5
            """)
            
            results = conn.execute(sample_query).fetchall()
            for row in results:
                print(f"  ID: {row[0]} | Batch: {row[1]} | Keyword: {row[2]}")
                print(f"  Text: {row[3][:70]}...\\n")
        
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"✗ Error verifying database: {e}")
        return False


def main():
    """Main function"""
    print_banner("🗄️  Local Database Setup for Emotion Analysis Pipeline")
    
    connection_string = get_connection_string()
    print(f"Database: {connection_string.split('@')[1]}")
    
    # Insert test data
    print_banner("📥 Inserting Test Data")
    
    for batch_id, posts_list in TEST_DATA.items():
        result = insert_raw_posts_sync(connection_string, batch_id, posts_list)
        if not result:
            print(f"⚠️  Failed to insert batch: {batch_id}")
    
    # Verify
    print_banner("✅ Verification")
    verify_database(connection_string)
    
    print_banner("🎉 Setup Complete!")
    print("Next steps:")
    print("  1. Update .env file with DATABASE_URL")
    print("  2. Run: pytest tests/test_cleaner.py -v")
    print("  3. Start server: python main.py")
    print("  4. Test endpoints with curl or Python client")


if __name__ == "__main__":
    main()
