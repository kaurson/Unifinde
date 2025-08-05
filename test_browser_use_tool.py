#!/usr/bin/env python3
"""
Test script for BrowserUseTool

This script tests the basic functionality of the BrowserUseTool to ensure
it's properly installed and configured.
"""

import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tool.browser_use_tool import BrowserUseTool
from app.config import load_config


async def test_browser_tool_creation():
    """Test that the BrowserUseTool can be created"""
    print("Testing BrowserUseTool creation...")
    
    try:
        browser_tool = BrowserUseTool()
        print("✓ BrowserUseTool created successfully")
        return browser_tool
    except Exception as e:
        print(f"✗ Failed to create BrowserUseTool: {e}")
        return None


async def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        config = load_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - LLM Provider: {config.llm.provider}")
        print(f"  - Browser Use Enabled: {config.browser_config is not None}")
        
        if config.browser_config:
            print(f"  - Browser Headless: {config.browser_config.headless}")
            print(f"  - Browser Disable Security: {config.browser_config.disable_security}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False


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
    print("BrowserUseTool Test Suite")
    print("=" * 40)
    
    # Test configuration first
    config_ok = await test_configuration()
    if not config_ok:
        print("\nConfiguration test failed. Please check your .env file.")
        return
    
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
            ("Wait Action", test_wait_action),
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
            print("🎉 All tests passed! BrowserUseTool is working correctly.")
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