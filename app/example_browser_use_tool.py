"""
Example usage of the BrowserUseTool

This script demonstrates how to use the BrowserUseTool for web automation
and content extraction in the University Data Collection System.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from .tool.browser_use_tool import BrowserUseTool
from .config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_navigation():
    """Example of basic browser navigation"""
    print("=== Basic Navigation Example ===")
    
    # Create browser tool instance
    browser_tool = BrowserUseTool()
    
    try:
        # Navigate to a website
        result = await browser_tool.execute(
            action="go_to_url",
            url="https://www.example.com"
        )
        print(f"Navigation result: {result.output}")
        
        # Get current state
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            print(f"Current URL: {state_data.get('url')}")
            print(f"Page title: {state_data.get('title')}")
        else:
            print(f"Failed to get state: {state_result.error}")
            
    except Exception as e:
        logger.error(f"Error in basic navigation: {e}")
    finally:
        await browser_tool.cleanup()


async def example_content_extraction():
    """Example of content extraction from a webpage"""
    print("\n=== Content Extraction Example ===")
    
    browser_tool = BrowserUseTool()
    
    try:
        # Navigate to a university website
        await browser_tool.execute(
            action="go_to_url",
            url="https://www.mit.edu"
        )
        
        # Wait for page to load
        await browser_tool.execute(action="wait", seconds=3)
        
        # Extract content about the university
        result = await browser_tool.execute(
            action="extract_content",
            goal="Extract basic information about MIT including its mission, location, and key facts"
        )
        
        if result.is_success():
            print("Extracted content:")
            print(result.output)
        else:
            print(f"Extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Error in content extraction: {e}")
    finally:
        await browser_tool.cleanup()


async def example_form_interaction():
    """Example of form interaction"""
    print("\n=== Form Interaction Example ===")
    
    browser_tool = BrowserUseTool()
    
    try:
        # Navigate to a search page
        await browser_tool.execute(
            action="go_to_url",
            url="https://www.google.com"
        )
        
        # Wait for page to load
        await browser_tool.execute(action="wait", seconds=2)
        
        # Get current state to see available elements
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            print("Available interactive elements:")
            print(state_data.get('interactive_elements', 'No elements found'))
            
            # Try to input text (this is a simplified example)
            # In practice, you'd need to identify the correct element index
            result = await browser_tool.execute(
                action="input_text",
                index=0,  # This would need to be the correct index for the search box
                text="MIT university"
            )
            print(f"Input result: {result.output}")
        else:
            print(f"Failed to get state: {state_result.error}")
            
    except Exception as e:
        logger.error(f"Error in form interaction: {e}")
    finally:
        await browser_tool.cleanup()


async def example_tab_management():
    """Example of tab management"""
    print("\n=== Tab Management Example ===")
    
    browser_tool = BrowserUseTool()
    
    try:
        # Open first tab
        await browser_tool.execute(
            action="go_to_url",
            url="https://www.example.com"
        )
        
        # Open second tab
        await browser_tool.execute(
            action="open_tab",
            url="https://www.google.com"
        )
        
        # Get current state to see tabs
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            tabs = state_data.get('tabs', [])
            print(f"Number of tabs: {len(tabs)}")
            
            for i, tab in enumerate(tabs):
                print(f"Tab {i}: {tab.get('title', 'No title')} - {tab.get('url', 'No URL')}")
                
            # Switch to first tab
            if len(tabs) > 1:
                await browser_tool.execute(action="switch_tab", tab_id=0)
                print("Switched to first tab")
                
        else:
            print(f"Failed to get state: {state_result.error}")
            
    except Exception as e:
        logger.error(f"Error in tab management: {e}")
    finally:
        await browser_tool.cleanup()


async def example_university_data_collection():
    """Example of collecting university data using the browser tool"""
    print("\n=== University Data Collection Example ===")
    
    browser_tool = BrowserUseTool()
    
    try:
        # Navigate to a university website
        await browser_tool.execute(
            action="go_to_url",
            url="https://www.stanford.edu"
        )
        
        # Wait for page to load
        await browser_tool.execute(action="wait", seconds=3)
        
        # Extract comprehensive university information
        result = await browser_tool.execute(
            action="extract_content",
            goal="""Extract comprehensive information about Stanford University including:
            1. Basic information (name, location, type)
            2. Mission and vision
            3. Academic programs and schools
            4. Student population and statistics
            5. Contact information
            6. Notable achievements or rankings
            7. Campus facilities and resources"""
        )
        
        if result.is_success():
            print("Stanford University Information:")
            print(result.output)
            
            # Parse the extracted content
            try:
                # The output might be JSON or text, depending on the LLM response
                content_data = json.loads(result.output)
                print("\nStructured data extracted successfully!")
            except json.JSONDecodeError:
                print("\nContent extracted as text format")
                
        else:
            print(f"Extraction failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Error in university data collection: {e}")
    finally:
        await browser_tool.cleanup()


async def main():
    """Run all examples"""
    print("BrowserUseTool Examples")
    print("=" * 50)
    
    # Check if browser use is enabled in config
    config = load_config()
    if not config.browser_config:
        print("Warning: Browser configuration not enabled.")
        print("Set BROWSER_USE_ENABLED=true in your .env file to enable browser automation.")
        print("Continuing with examples anyway...")
    
    try:
        # Run examples
        await example_basic_navigation()
        await example_content_extraction()
        await example_form_interaction()
        await example_tab_management()
        await example_university_data_collection()
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main()) 