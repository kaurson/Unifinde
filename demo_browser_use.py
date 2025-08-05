#!/usr/bin/env python3
"""
Simple demonstration of the BrowserUseTool

This script shows how to use the BrowserUseTool for basic web automation.
"""

import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tool.browser_use_tool import BrowserUseTool


async def demo_basic_usage():
    """Demonstrate basic browser automation"""
    print("🌐 BrowserUseTool Demo")
    print("=" * 40)
    
    # Create browser tool instance
    browser_tool = BrowserUseTool()
    
    try:
        print("1. Navigating to a website...")
        result = await browser_tool.execute(
            action="go_to_url",
            url="https://httpbin.org/html"
        )
        print(f"   ✓ {result.output}")
        
        print("\n2. Getting page state...")
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            print(f"   ✓ Current URL: {state_data.get('url')}")
            print(f"   ✓ Page title: {state_data.get('title', 'No title')}")
            print(f"   ✓ Screenshot captured: {'Yes' if state_result.base64_image else 'No'}")
        else:
            print(f"   ✗ Failed to get state: {state_result.error}")
        
        print("\n3. Waiting for 2 seconds...")
        wait_result = await browser_tool.execute(action="wait", seconds=2)
        print(f"   ✓ {wait_result.output}")
        
        print("\n4. Opening a new tab...")
        tab_result = await browser_tool.execute(
            action="open_tab",
            url="https://httpbin.org/json"
        )
        print(f"   ✓ {tab_result.output}")
        
        print("\n5. Getting updated state with multiple tabs...")
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            tabs = state_data.get('tabs', [])
            print(f"   ✓ Number of tabs: {len(tabs)}")
            for i, tab in enumerate(tabs):
                print(f"     Tab {i}: {tab.get('title', 'No title')} - {tab.get('url', 'No URL')}")
        
        print("\n6. Switching back to first tab...")
        switch_result = await browser_tool.execute(action="switch_tab", tab_id=0)
        print(f"   ✓ {switch_result.output}")
        
        print("\n7. Scrolling down...")
        scroll_result = await browser_tool.execute(action="scroll_down", scroll_amount=300)
        print(f"   ✓ {scroll_result.output}")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        print("\n🧹 Cleaning up...")
        await browser_tool.cleanup()
        print("   ✓ Cleanup completed")


async def demo_university_search():
    """Demonstrate university website search"""
    print("\n🎓 University Search Demo")
    print("=" * 40)
    
    browser_tool = BrowserUseTool()
    
    try:
        print("1. Searching for MIT website...")
        search_result = await browser_tool.execute(
            action="web_search",
            query="MIT university official website"
        )
        print(f"   ✓ {search_result.output}")
        
        print("\n2. Getting current page info...")
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            print(f"   ✓ Current URL: {state_data.get('url')}")
            print(f"   ✓ Page title: {state_data.get('title', 'No title')}")
            
            # Show some interactive elements
            elements = state_data.get('interactive_elements', '')
            if elements:
                print(f"   ✓ Found {len(elements.split('[')) - 1} interactive elements")
            else:
                print("   ✓ No interactive elements found")
        
        print("\n3. Waiting for page to load...")
        await browser_tool.execute(action="wait", seconds=3)
        
        print("\n4. Scrolling down to see more content...")
        await browser_tool.execute(action="scroll_down", scroll_amount=500)
        
        print("\n5. Taking a final screenshot...")
        final_state = await browser_tool.get_current_state()
        if final_state.is_success():
            print("   ✓ Screenshot captured successfully")
        
        print("\n🎉 University search demo completed!")
        
    except Exception as e:
        print(f"❌ University search demo failed: {e}")
    finally:
        await browser_tool.cleanup()


async def main():
    """Run all demos"""
    print("🚀 Starting BrowserUseTool Demonstrations")
    print("=" * 50)
    
    # Run basic usage demo
    await demo_basic_usage()
    
    # Run university search demo
    await demo_university_search()
    
    print("\n✨ All demonstrations completed!")
    print("\nTo enable LLM-powered content extraction, set up your .env file with:")
    print("  LLM_PROVIDER=openai")
    print("  LLM_API_KEY=your_api_key_here")
    print("  BROWSER_USE_ENABLED=true")


if __name__ == "__main__":
    asyncio.run(main()) 