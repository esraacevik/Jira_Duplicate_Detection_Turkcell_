#!/usr/bin/env python3
"""
Test script for Hybrid Search System
"""

from hybrid_search import HybridSearch

def test_hybrid_search():
    """Test the hybrid search system with sample queries"""
    
    print("\n" + "=" * 100)
    print("🧪 HYBRID SEARCH SYSTEM - TEST")
    print("=" * 100)
    
    # Initialize search system
    print("\n1️⃣ Sistem başlatılıyor...")
    search = HybridSearch()
    
    # Test cases (language removed since dataset doesn't have language column)
    test_cases = [
        {
            'name': 'Test 1: BiP Android mesaj sorunu',
            'query': 'mesaj gönderilirken uygulama çöküyor',
            'application': 'BiP',
            'platform': 'android',
            'version': '3.70.19',
            'language': None,
            'top_k': 5
        },
        {
            'name': 'Test 2: iOS bildiri sorunu',
            'query': 'bildirim gelmiyor',
            'application': 'BiP',
            'platform': 'ios',
            'version': None,
            'language': None,
            'top_k': 5
        },
        {
            'name': 'Test 3: Genel arama (filtre yok)',
            'query': 'uygulama açılmıyor',
            'application': None,
            'platform': None,
            'version': None,
            'language': None,
            'top_k': 5
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print("\n" + "=" * 100)
        print(f"🧪 {test['name']}")
        print("=" * 100)
        
        results = search.search(
            query=test['query'],
            application=test['application'],
            platform=test['platform'],
            version=test['version'],
            language=test['language'],
            top_k=test['top_k']
        )
        
        search.display_results(
            results=results,
            query=test['query'],
            application=test['application'],
            platform=test['platform'],
            version=test['version'],
            language=test['language']
        )
        
        # Add separator between tests
        if i < len(test_cases):
            print("\n" + "-" * 100)
    
    print("\n" + "=" * 100)
    print("✅ Tüm testler tamamlandı!")
    print("=" * 100)


if __name__ == "__main__":
    test_hybrid_search()

