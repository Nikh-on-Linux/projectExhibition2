#!/usr/bin/env python3
"""
Python Client for Database & Cleaning API 

Easy way to:
- Insert test posts programmatically
- Make API requests
- Generate test reports
"""

import psycopg2
from psycopg2.extras import Json
import requests
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class DatabaseClient:
    """PostgreSQL database client for direct data insertion"""
    
    def __init__(self, user: str = "emotion_app", password: str = "emotion_password_123",
                 host: str = "localhost", port: int = 5432, database: str = "emotion_db"):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.conn = None
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database
            )
            print(f"✅ Connected to {self.database} on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Disconnected from database")
    
    def insert_raw_post(self, batch_id: str, platform: str, keyword: str, 
                       raw_text: str, json_data: Optional[Dict] = None) -> Optional[int]:
        """Insert a single raw post and return its ID"""
        if not self.conn:
            print("❌ Not connected to database")
            return None
        
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO raw_posts (batch_id, platform, keyword, raw_text, raw_json)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (batch_id, platform, keyword, raw_text, Json(json_data or {})))
            
            post_id = cur.fetchone()[0]
            self.conn.commit()
            return post_id
        except Exception as e:
            print(f"❌ Insert failed: {e}")
            self.conn.rollback()
            return None
    
    def insert_batch(self, batch_id: str, posts: List[Dict]) -> int:
        """Insert multiple posts for a batch"""
        inserted = 0
        for post in posts:
            post_id = self.insert_raw_post(
                batch_id=batch_id,
                platform=post.get('platform', 'reddit'),
                keyword=post.get('keyword', ''),
                raw_text=post['raw_text'],
                json_data={'upvotes': post.get('upvotes', 100)}
            )
            if post_id:
                inserted += 1
        
        print(f"✅ Inserted {inserted}/{len(posts)} posts for batch {batch_id}")
        return inserted
    
    def get_raw_posts(self, batch_id: str) -> List[Tuple]:
        """Get all raw posts for a batch"""
        if not self.conn:
            return []
        
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT id, batch_id, keyword, raw_text 
                FROM raw_posts 
                WHERE batch_id = %s
                ORDER BY id
            """, (batch_id,))
            return cur.fetchall()
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        if not self.conn:
            return {}
        
        try:
            cur = self.conn.cursor()
            
            stats = {}
            
            # Total posts
            cur.execute("SELECT COUNT(*) FROM raw_posts")
            stats['total_raw_posts'] = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM cleaned_posts")
            stats['total_cleaned_posts'] = cur.fetchone()[0]
            
            # Batches
            cur.execute("SELECT COUNT(DISTINCT batch_id) FROM raw_posts")
            stats['total_batches'] = cur.fetchone()[0]
            
            # Breakdown by batch
            cur.execute("""
                SELECT batch_id, COUNT(*) as count 
                FROM raw_posts 
                GROUP BY batch_id 
                ORDER BY batch_id
            """)
            stats['batches'] = {row[0]: row[1] for row in cur.fetchall()}
            
            return stats
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return {}
    
    def clear_batch(self, batch_id: str) -> bool:
        """Delete all posts in a batch (use with caution!)"""
        if not self.conn:
            return False
        
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM cleaned_posts WHERE batch_id = %s", (batch_id,))
            deleted_cleaned = cur.rowcount
            
            cur.execute("DELETE FROM raw_posts WHERE batch_id = %s", (batch_id,))
            deleted_raw = cur.rowcount
            
            self.conn.commit()
            print(f"✅ Deleted {deleted_raw} raw posts and {deleted_cleaned} cleaned posts")
            return True
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            self.conn.rollback()
            return False


class CleaningAPIClient:
    """Client for the cleaning API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
    
    def health_check(self) -> bool:
        """Check if API is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def clean_batch(self, batch_id: str) -> Optional[Dict]:
        """Clean a batch of posts"""
        try:
            response = requests.post(
                f"{self.base_url}/api/clean/{batch_id}",
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code} - {response.json()}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def get_stats(self, batch_id: str) -> Optional[Dict]:
        """Get cleaning stats for a batch"""
        try:
            response = requests.get(
                f"{self.base_url}/api/clean/stats/{batch_id}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None


def example_insert_custom_posts():
    """Example: Insert custom test posts"""
    print("\n" + "="*60)
    print("  📝 Example: Insert Custom Posts")
    print("="*60)
    
    db = DatabaseClient()
    if not db.connect():
        return
    
    custom_posts = [
        {
            "platform": "reddit",
            "keyword": "custom-test",
            "raw_text": "This is my custom test post! 😊",
            "upvotes": 42
        },
        {
            "platform": "reddit",
            "keyword": "custom-test",
            "raw_text": "Another test with emotions: angry 😡 and sad 😢",
            "upvotes": 12
        },
        {
            "platform": "reddit",
            "keyword": "custom-test",
            "raw_text": "Visit https://test.com for more info #testing",
            "upvotes": 7
        },
    ]
    
    batch_id = f"custom-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    db.insert_batch(batch_id, custom_posts)
    
    print(f"\n✅ Batch ID to use: {batch_id}")
    
    db.disconnect()


def example_clean_and_verify():
    """Example: Clean batch and verify results"""
    print("\n" + "="*60)
    print("  🔄 Example: Clean Batch and Verify")
    print("="*60)
    
    api = CleaningAPIClient()
    
    # Check server
    if not api.health_check():
        print("❌ API server not running. Start with: python main.py")
        return
    
    print("✅ API is running\n")
    
    # Clean a batch
    batch_id = "test-batch-basic"
    print(f"Cleaning batch: {batch_id}")
    result = api.clean_batch(batch_id)
    
    if result:
        print(f"✅ Cleaned {result['total_processed']} posts")
        
        # Show first result
        if result['results']:
            first = result['results'][0]
            print(f"\nFirst result:")
            print(f"  • Status: {first['status']}")
            print(f"  • Language: {first['language']}")
            print(f"  • Emoji converted: {first['emoji_converted']}")
            print(f"  • Flags: {first['flags']}")
            print(f"  • Text: {first['cleaned_text'][:60]}...")
        
        # Get stats
        stats = api.get_stats(batch_id)
        if stats:
            print(f"\nStats:")
            print(f"  • Total raw: {stats['total_raw']}")
            print(f"  • Cleaned: {stats['cleaned']}")
            print(f"  • Pending: {stats['pending']}")


def example_database_stats():
    """Example: Show database statistics"""
    print("\n" + "="*60)
    print("  📊 Database Statistics")
    print("="*60 + "\n")
    
    db = DatabaseClient()
    if not db.connect():
        return
    
    stats = db.get_stats()
    
    print(f"Total Raw Posts:     {stats.get('total_raw_posts', 0)}")
    print(f"Total Cleaned Posts: {stats.get('total_cleaned_posts', 0)}")
    print(f"Total Batches:       {stats.get('total_batches', 0)}")
    
    if stats.get('batches'):
        print(f"\nPosts per batch:")
        for batch_id, count in sorted(stats['batches'].items()):
            print(f"  • {batch_id:.<30} {count}")
    
    db.disconnect()


def main():
    """Main menu"""
    print("\n" + "="*60)
    print("  🐍 Python Client for Cleaning Pipeline")
    print("="*60)
    
    examples = {
        "1": ("View Database Statistics", example_database_stats),
        "2": ("Insert Custom Posts", example_insert_custom_posts),
        "3": ("Clean Batch and Verify", example_clean_and_verify),
    }
    
    print("\nExamples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  0. Exit")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "0":
        return
    elif choice in examples:
        _, func = examples[choice]
        func()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    # Uncomment to run specific examples
    # example_database_stats()
    # example_insert_custom_posts()
    # example_clean_and_verify()
    
    # Or run interactive menu
    main()
