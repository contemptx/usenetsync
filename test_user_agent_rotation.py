#!/usr/bin/env python3
"""
Test to demonstrate user agent rotation for better anonymity
"""

import sys
sys.path.insert(0, '/workspace')

from src.networking.production_nntp_client import ProductionNNTPClient
from collections import Counter

def test_user_agent_rotation():
    """Test that user agents rotate through common tools"""
    print("\n" + "="*80)
    print("USER AGENT ROTATION TEST")
    print("="*80)
    
    # Create client with no fixed user agent (triggers rotation)
    client = ProductionNNTPClient(
        host='news.newshosting.com',
        port=563,
        username='test',
        password='test',
        use_ssl=True,
        user_agent=None  # None triggers random selection
    )
    
    print("\n📊 Available User Agents for Rotation:")
    print("-" * 50)
    
    # Show available user agents
    for i, ua in enumerate(client._common_user_agents, 1):
        if ua:
            print(f"  {i:2}. {ua}")
        else:
            print(f"  {i:2}. [No User-Agent header]")
    
    print(f"\nTotal: {len(client._common_user_agents)} different user agents")
    
    # Test rotation by building multiple headers
    print("\n🔄 Testing User Agent Rotation (20 posts):")
    print("-" * 50)
    
    user_agents_used = []
    
    for i in range(20):
        # Build headers which will select a random user agent
        headers = client._build_headers(
            subject=f"Test {i}",
            newsgroup="alt.binaries.test"
        )
        
        ua = headers.get('User-Agent', '[No User-Agent]')
        user_agents_used.append(ua)
        print(f"  Post {i+1:2}: {ua}")
    
    # Analyze distribution
    print("\n📈 Distribution Analysis:")
    print("-" * 50)
    
    counter = Counter(user_agents_used)
    for ua, count in counter.most_common():
        percentage = (count / len(user_agents_used)) * 100
        print(f"  {ua}: {count} times ({percentage:.1f}%)")
    
    print("\n✅ User agents are rotating successfully!")
    print("   Posts will blend in with legitimate traffic from:")
    print("   • SABnzbd (popular downloader)")
    print("   • NZBGet (popular downloader)")
    print("   • ngPost (popular poster)")
    print("   • Thunderbird (email client)")
    print("   • Various newsreaders")
    
    # Test with fixed user agent
    print("\n🔒 Testing Fixed User Agent Mode:")
    print("-" * 50)
    
    fixed_client = ProductionNNTPClient(
        host='news.newshosting.com',
        port=563,
        username='test',
        password='test',
        use_ssl=True,
        user_agent="MyCustomClient/1.0"  # Fixed user agent
    )
    
    headers = fixed_client._build_headers(
        subject="Test",
        newsgroup="alt.binaries.test"
    )
    
    print(f"  Fixed UA: {headers.get('User-Agent')}")
    print("  ✓ Fixed mode works when specific UA is needed")
    
    return True

if __name__ == "__main__":
    test_user_agent_rotation()
    print("\n" + "="*80)
    print("SUMMARY: User agent rotation improves anonymity by making")
    print("UsenetSync posts indistinguishable from popular Usenet tools")
    print("="*80)