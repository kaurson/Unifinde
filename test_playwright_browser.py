#!/usr/bin/env python3
"""
Test script for the Playwright-based Browser Tool

This script tests the basic functionality of the BrowserToolPlaywright to ensure
it's properly working without the problematic browser-use library.
"""

import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tool.browser_tool_playwright import BrowserToolPlaywright


async def test_browser_tool_creation():
    """Test that the BrowserToolPlaywright can be created"""
    print("Testing BrowserToolPlaywright creation...")
    
    try:
        browser_tool = BrowserToolPlaywright()
        print("✓ BrowserToolPlaywright created successfully")
        return browser_tool
    except Exception as e:
        print(f"✗ Failed to create BrowserToolPlaywright: {e}")
        return None


async def test_basic_navigation(browser_tool):
    """Test basic navigation functionality"""
    print("\nTesting basic navigation...")
    
    try:
        # Test navigation to a simple page
        result = await browser_tool.execute(
            action="go_to_url",
            url="https://httpbin.org/html"
        )
        
        if result.is_success():
            print("✓ Navigation successful")
            print(f"  - Output: {result.output}")
            return True
        else:
            print(f"✗ Navigation failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Navigation test failed: {e}")
        return False


async def test_state_retrieval(browser_tool):
    """Test getting browser state"""
    print("\nTesting state retrieval...")
    
    try:
        state_result = await browser_tool.get_current_state()
        
        if state_result.is_success():
            print("✓ State retrieval successful")
            state_data = json.loads(state_result.output)
            print(f"  - URL: {state_data.get('url', 'N/A')}")
            print(f"  - Title: {state_data.get('title', 'N/A')}")
            print(f"  - Has screenshot: {state_result.base64_image is not None}")
            return True
        else:
            print(f"✗ State retrieval failed: {state_result.error}")
            return False
            
    except Exception as e:
        print(f"✗ State retrieval test failed: {e}")
        return False


async def test_scrolling(browser_tool):
    """Test scrolling functionality"""
    print("\nTesting scrolling...")
    
    try:
        result = await browser_tool.execute(action="scroll_down", scroll_amount=300)
        
        if result.is_success():
            print("✓ Scrolling successful")
            print(f"  - Output: {result.output}")
            return True
        else:
            print(f"✗ Scrolling failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Scrolling test failed: {e}")
        return False


async def test_wait_action(browser_tool):
    """Test wait action"""
    print("\nTesting wait action...")
    
    try:
        result = await browser_tool.execute(action="wait", seconds=1)
        
        if result.is_success():
            print("✓ Wait action successful")
            return True
        else:
            print(f"✗ Wait action failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Wait action test failed: {e}")
        return False


async def test_tab_management(browser_tool):
    """Test tab management"""
    print("\nTesting tab management...")
    
    try:
        # Open a new tab
        result = await browser_tool.execute(
            action="open_tab",
            url="https://httpbin.org/json"
        )
        
        if result.is_success():
            print("✓ Tab management successful")
            print(f"  - Output: {result.output}")
            
            # Get state to see tabs
            state_result = await browser_tool.get_current_state()
            if state_result.is_success():
                state_data = json.loads(state_result.output)
                tabs = state_data.get('tabs', [])
                print(f"  - Number of tabs: {len(tabs)}")
            
            return True
        else:
            print(f"✗ Tab management failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"✗ Tab management test failed: {e}")
        return False


async def test_cleanup(browser_tool):
    """Test cleanup functionality"""
    print("\nTesting cleanup...")
    
    try:
        await browser_tool.cleanup()
        print("✓ Cleanup successful")
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("BrowserToolPlaywright Test Suite")
    print("=" * 40)
    
    # Test tool creation
    browser_tool = await test_browser_tool_creation()
    if not browser_tool:
        print("\nTool creation failed. Please check your installation.")
        return
    
    try:
        # Run tests
        tests = [
            ("Basic Navigation", test_basic_navigation),
            ("State Retrieval", test_state_retrieval),
            ("Scrolling", test_scrolling),
            ("Wait Action", test_wait_action),
            ("Tab Management", test_tab_management),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func(browser_tool):
                    passed += 1
            except Exception as e:
                print(f"✗ {test_name} test failed with exception: {e}")
        
        # Test cleanup
        await test_cleanup(browser_tool)
        
        # Summary
        print(f"\nTest Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! BrowserToolPlaywright is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the configuration and dependencies.")
            
    except Exception as e:
        print(f"✗ Test suite failed: {e}")
    finally:
        # Ensure cleanup
        try:
            await browser_tool.cleanup()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main()) 