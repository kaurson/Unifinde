#!/usr/bin/env python3
"""
Integration Example: BrowserUseTool with University Data Collection

This example shows how to integrate the BrowserUseTool with your existing
university data collection system.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any, Optional

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tool.browser_use_tool import BrowserUseTool
from app.config import load_config


class UniversityDataCollectorWithBrowser:
    """Enhanced university data collector using BrowserUseTool"""
    
    def __init__(self):
        self.browser_tool = BrowserUseTool()
        self.config = load_config()
    
    async def collect_university_data(self, university_name: str) -> Dict[str, Any]:
        """
        Collect comprehensive university data using browser automation
        
        Args:
            university_name: Name of the university to research
            
        Returns:
            Dictionary containing collected university data
        """
        try:
            print(f"🔍 Researching {university_name}...")
            
            # Step 1: Search for the university website
            print("  1. Searching for university website...")
            search_result = await self.browser_tool.execute(
                action="web_search",
                query=f"{university_name} official website"
            )
            
            if not search_result.is_success():
                return {
                    "university_name": university_name,
                    "status": "failed",
                    "error": "Failed to find university website",
                    "data": {}
                }
            
            # Step 2: Get current page information
            print("  2. Getting page information...")
            state_result = await self.browser_tool.get_current_state()
            
            if not state_result.is_success():
                return {
                    "university_name": university_name,
                    "status": "failed",
                    "error": "Failed to get page state",
                    "data": {}
                }
            
            state_data = json.loads(state_result.output)
            current_url = state_data.get('url', '')
            
            # Step 3: Wait for page to load and scroll to see more content
            print("  3. Loading page content...")
            await self.browser_tool.execute(action="wait", seconds=3)
            await self.browser_tool.execute(action="scroll_down", scroll_amount=800)
            await self.browser_tool.execute(action="wait", seconds=2)
            
            # Step 4: Extract content using LLM (if configured)
            print("  4. Extracting university information...")
            extraction_result = await self.browser_tool.execute(
                action="extract_content",
                goal=f"""Extract comprehensive information about {university_name} including:
                1. Basic information (name, location, type - public/private)
                2. Mission and vision statements
                3. Academic programs and schools/colleges
                4. Student population and statistics
                5. Contact information (phone, email, address)
                6. Notable achievements, rankings, or recognitions
                7. Campus facilities and resources
                8. Admission requirements and process
                9. Tuition and financial information
                10. Research areas and specializations"""
            )
            
            # Step 5: Take a screenshot for reference
            print("  5. Capturing screenshot...")
            final_state = await self.browser_tool.get_current_state()
            
            # Compile the collected data
            collected_data = {
                "university_name": university_name,
                "status": "success",
                "source_url": current_url,
                "page_title": state_data.get('title', ''),
                "extracted_content": extraction_result.output if extraction_result.is_success() else "Content extraction failed",
                "screenshot_available": final_state.base64_image is not None,
                "interactive_elements_count": len(state_data.get('interactive_elements', '').split('[')) - 1,
                "collected_at": asyncio.get_event_loop().time()
            }
            
            print(f"✅ Successfully collected data for {university_name}")
            return collected_data
            
        except Exception as e:
            print(f"❌ Error collecting data for {university_name}: {e}")
            return {
                "university_name": university_name,
                "status": "failed",
                "error": str(e),
                "data": {}
            }
    
    async def batch_collect_universities(self, university_names: list) -> list:
        """
        Collect data for multiple universities
        
        Args:
            university_names: List of university names to research
            
        Returns:
            List of collected data for each university
        """
        results = []
        
        for i, university_name in enumerate(university_names, 1):
            print(f"\n📚 Processing {i}/{len(university_names)}: {university_name}")
            
            result = await self.collect_university_data(university_name)
            results.append(result)
            
            # Small delay between universities
            if i < len(university_names):
                print("   ⏳ Waiting before next university...")
                await asyncio.sleep(2)
        
        return results
    
    async def cleanup(self):
        """Clean up browser resources"""
        await self.browser_tool.cleanup()


async def main():
    """Run the integration example"""
    print("🎓 University Data Collection with BrowserUseTool")
    print("=" * 55)
    
    # Check configuration
    config = load_config()
    print(f"Configuration:")
    print(f"  - LLM Provider: {config.llm.provider}")
    print(f"  - Browser Use Enabled: {config.browser_config is not None}")
    print(f"  - LLM API Key: {'Set' if config.llm.api_key else 'Not set'}")
    
    if not config.llm.api_key:
        print("\n⚠️  Note: LLM API key not set. Content extraction will be limited.")
        print("   Set LLM_API_KEY in your .env file for full functionality.")
    
    # Create collector
    collector = UniversityDataCollectorWithBrowser()
    
    try:
        # Example universities to research
        universities = [
            "Massachusetts Institute of Technology",
            "Stanford University"
        ]
        
        print(f"\n🔍 Starting data collection for {len(universities)} universities...")
        
        # Collect data
        results = await collector.batch_collect_universities(universities)
        
        # Display results
        print(f"\n📊 Collection Results:")
        print("=" * 30)
        
        for result in results:
            print(f"\n🏫 {result['university_name']}")
            print(f"   Status: {result['status']}")
            print(f"   Source: {result.get('source_url', 'N/A')}")
            
            if result['status'] == 'success':
                print(f"   Content Length: {len(result.get('extracted_content', ''))} characters")
                print(f"   Screenshot: {'Yes' if result.get('screenshot_available') else 'No'}")
                print(f"   Elements Found: {result.get('interactive_elements_count', 0)}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Save results to file
        output_file = "university_data_collection_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Integration example failed: {e}")
    finally:
        await collector.cleanup()
        print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main()) 