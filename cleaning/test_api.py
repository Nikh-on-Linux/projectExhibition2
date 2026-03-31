#!/usr/bin/env python3
"""
Quick Test Examples for the Cleaning API

This shows practical examples of testing the cleaning pipeline locally.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:5000"


def print_separator(title: str = ""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print("-" * 60)


def test_health_check():
    """Test the health check endpoint"""
    print_separator("1️⃣  Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_clean_batch(batch_id: str = "test-batch-basic"):
    """Test cleaning a batch of posts"""
    print_separator(f"2️⃣  Clean Batch: {batch_id}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/clean/{batch_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nBatch ID: {data['batch_id']}")
            print(f"Status: {data['status']}")
            print(f"Total Processed: {data['total_processed']}")
            print(f"Signal: {data['signal']}")
            
            if data['results']:
                print(f"\nFirst Result:")
                result = data['results'][0]
                print(f"  • Post ID: {result['post_id']}")
                print(f"  • Status: {result['status']}")
                print(f"  • Language: {result['language']}")
                print(f"  • Emoji Converted: {result['emoji_converted']}")
                print(f"  • Flags: {result['flags']}")
                print(f"  • Cleaned Text: {result['cleaned_text'][:80]}...")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_cleaning_stats(batch_id: str = "test-batch-basic"):
    """Test getting cleaning stats for a batch"""
    print_separator(f"3️⃣  Cleaning Stats: {batch_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/clean/stats/{batch_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nBatch ID: {data['batch_id']}")
            print(f"Total Raw Posts: {data['total_raw']}")
            print(f"Already Cleaned: {data['cleaned']}")
            print(f"Pending Cleaning: {data['pending']}")
            print(f"Completion: {(data['cleaned']/data['total_raw']*100):.1f}%")
        else:
            print(f"Error: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_all_batches():
    """Test all available batches"""
    print_separator("4️⃣  Test All Batches")
    
    batches = [
        "test-batch-basic",
        "test-batch-cleaning",
        "test-batch-complex",
        "test-batch-problematic",
        "test-batch-real",
    ]
    
    results = {}
    for batch_id in batches:
        try:
            response = requests.post(f"{BASE_URL}/api/clean/{batch_id}")
            results[batch_id] = {
                "status": response.status_code,
                "success": response.status_code == 200,
                "message": "OK" if response.status_code == 200 else response.json().get("detail", "Failed")
            }
        except Exception as e:
            results[batch_id] = {
                "status": 0,
                "success": False,
                "message": str(e)
            }
    
    # Print summary
    print()
    for batch_id, result in results.items():
        status_icon = "✅" if result['success'] else "❌"
        print(f"  {status_icon} {batch_id:.<40} {result['status']}")
    
    return all(r['success'] for r in results.values())


def test_specific_post_types():
    """Test specific post types and their handling"""
    print_separator("5️⃣  Specific Post Type Tests")
    
    test_cases = [
        ("test-batch-basic", "Emotion Detection", "Should detect various emotions"),
        ("test-batch-cleaning", "Text Cleaning", "Should handle URLs, mentions, hashtags"),
        ("test-batch-complex", "Complex Patterns", "Should preserve negations, contractions"),
        ("test-batch-problematic", "Problem Detection", "Should detect gibberish, short text"),
        ("test-batch-real", "Real Examples", "Should handle real Reddit-like posts"),
    ]
    
    for batch_id, category, description in test_cases:
        print(f"\n📌 {category}")
        print(f"   Batch: {batch_id}")
        print(f"   Purpose: {description}")
        
        try:
            response = requests.post(f"{BASE_URL}/api/clean/{batch_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Processed {data['total_processed']} posts")
                
                # Count post statuses
                statuses = {}
                for result in data['results']:
                    status = result['status']
                    statuses[status] = statuses.get(status, 0) + 1
                
                print(f"   Status breakdown: {statuses}")
            else:
                print(f"   ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def show_example_responses():
    """Show what example responses look like"""
    print_separator("📋 Example Response Structures")
    
    print("\n✅ Successful Clean Batch Response:")
    example_response = {
        "status": "success",
        "batch_id": "test-batch-basic",
        "total_processed": 8,
        "signal": "BATCH_CLEAN_OK",
        "results": [
            {
                "post_id": 1,
                "batch_id": "test-batch-basic",
                "cleaned_text": "i absolutely love solar energy it makes me so happy",
                "language": "en",
                "emoji_converted": True,
                "status": "ok",
                "flags": ["had_emojis"]
            }
        ]
    }
    print(json.dumps(example_response, indent=2))
    
    print("\n✅ Statistics Response:")
    example_stats = {
        "batch_id": "test-batch-basic",
        "total_raw": 8,
        "cleaned": 6,
        "pending": 2
    }
    print(json.dumps(example_stats, indent=2))
    
    print("\n✅ Health Check Response:")
    example_health = {
        "status": "ok",
        "service": "cleaning",
        "port": 5000,
        "timestamp": datetime.utcnow().isoformat()
    }
    print(json.dumps(example_health, indent=2))


def show_curl_examples():
    """Show curl command examples"""
    print_separator("🔧 curl Command Examples")
    
    examples = [
        ("Health Check", "curl http://localhost:5000/health"),
        ("Clean Batch", "curl -X POST http://localhost:5000/api/clean/test-batch-basic"),
        ("Get Stats", "curl http://localhost:5000/api/clean/stats/test-batch-basic"),
        ("Clean Multiple", "for batch in test-batch-{basic,cleaning,complex}; do curl -X POST http://localhost:5000/api/clean/$batch; done"),
        ("With Pretty JSON", "curl -s http://localhost:5000/health | jq ."),
    ]
    
    for title, cmd in examples:
        print(f"\n📌 {title}:")
        print(f"   {cmd}")


def main():
    """Run all tests"""
    import sys
    
    print("\n" + "="*60)
    print("  🧪 Cleaning API Test Suite")
    print("="*60)
    print(f"\nTarget: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}\n")
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print("❌ ERROR: Server is not running!")
        print(f"Please start the server first:")
        print("  cd /home/aditya-mittal/Documents/ProjectExhibition2/projectExhibition2/cleaning")
        print("  python main.py")
        sys.exit(1)
    
    # Run tests
    test_results = {
        "Health Check": test_health_check(),
        "Clean Single Batch": test_clean_batch(),
        "Cleaning Stats": test_cleaning_stats(),
        "All Batches": test_all_batches(),
    }
    
    # Additional tests
    test_specific_post_types()
    
    # Show documentation
    show_example_responses()
    show_curl_examples()
    
    # Summary
    print_separator("📊 Test Summary")
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
