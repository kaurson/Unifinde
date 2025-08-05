#!/usr/bin/env python3
"""
Simple example demonstrating the University Data Collection System
"""

import asyncio
import json
from main import UniversityDataCollector

async def simple_example():
    """Simple example of collecting university data"""
    print("University Data Collection System - Simple Example")
    print("=" * 50)
    
    # Initialize the collector
    collector = UniversityDataCollector()
    
    try:
        # Example 1: Collect basic information about MIT
        print("\n1. Collecting basic information about MIT...")
        mit_result = await collector.collect_university_data(
            "Massachusetts Institute of Technology",
            fields=["basic_info", "contact"]
        )
        
        print(f"Status: {mit_result['status']}")
        print(f"Confidence: {mit_result['confidence_score']:.2f}")
        print(f"Source: {mit_result['source_url']}")
        
        if mit_result.get('data'):
            print("Collected data:")
            for category, data in mit_result['data'].items():
                print(f"  {category}: {len(data) if isinstance(data, (list, dict)) else 1} items")
        
        # Example 2: Collect academic statistics
        print("\n2. Collecting academic statistics for Stanford...")
        stanford_result = await collector.collect_university_data(
            "Stanford University",
            fields=["academic", "statistics"]
        )
        
        print(f"Status: {stanford_result['status']}")
        print(f"Confidence: {stanford_result['confidence_score']:.2f}")
        
        if stanford_result.get('data'):
            print("Collected data:")
            for category, data in stanford_result['data'].items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"    {key}: {value}")
                else:
                    print(f"    {data}")
        
        # Example 3: Collect all available information
        print("\n3. Collecting all information for Harvard...")
        harvard_result = await collector.collect_university_data(
            "Harvard University",
            fields=["all"]
        )
        
        print(f"Status: {harvard_result['status']}")
        print(f"Confidence: {harvard_result['confidence_score']:.2f}")
        
        if harvard_result.get('data'):
            print("Data categories collected:")
            for category in harvard_result['data'].keys():
                print(f"  - {category}")
        
        print("\n✅ Examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during example: {e}")
    
    finally:
        collector.close()

async def mcp_example():
    """Example of MCP-style field requests"""
    print("\n" + "=" * 50)
    print("MCP-Style Field Requests Example")
    print("=" * 50)
    
    collector = UniversityDataCollector()
    
    try:
        # Simulate an LLM making specific field requests
        requests = [
            {
                "university": "University of California Berkeley",
                "fields": ["basic_info", "academic"],
                "description": "LLM needs basic info and academic details for UC Berkeley"
            },
            {
                "university": "Yale University",
                "fields": ["statistics", "programs"],
                "description": "LLM needs statistics and program information for Yale"
            }
        ]
        
        for i, req in enumerate(requests, 1):
            print(f"\nRequest {i}: {req['description']}")
            print(f"University: {req['university']}")
            print(f"Requested fields: {req['fields']}")
            
            result = await collector.collect_university_data(
                req['university'],
                fields=req['fields']
            )
            
            print(f"Result: {result['status']} (confidence: {result['confidence_score']:.2f})")
            
            # Show what was collected
            if result.get('data'):
                for field_category in req['fields']:
                    if field_category in result['data']:
                        data = result['data'][field_category]
                        if isinstance(data, dict):
                            print(f"  {field_category}: {len(data)} fields collected")
                        elif isinstance(data, list):
                            print(f"  {field_category}: {len(data)} items collected")
                        else:
                            print(f"  {field_category}: data collected")
            
            # Add delay between requests
            await asyncio.sleep(1)
        
        print("\n✅ MCP examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during MCP example: {e}")
    
    finally:
        collector.close()

async def batch_example():
    """Example of batch collection"""
    print("\n" + "=" * 50)
    print("Batch Collection Example")
    print("=" * 50)
    
    collector = UniversityDataCollector()
    
    try:
        # List of universities to collect data for
        universities = [
            "Princeton University",
            "Columbia University",
            "University of Pennsylvania"
        ]
        
        print(f"Collecting basic information for {len(universities)} universities...")
        
        results = await collector.batch_collect(
            universities,
            fields=["basic_info", "contact"]
        )
        
        print("\nBatch Collection Results:")
        for result in results:
            print(f"\n{result['university_name']}:")
            print(f"  Status: {result['status']}")
            print(f"  Confidence: {result['confidence_score']:.2f}")
            print(f"  Source: {result['source_url']}")
            
            if result.get('data'):
                for category, data in result['data'].items():
                    if isinstance(data, dict):
                        print(f"  {category}: {len(data)} fields")
                    elif isinstance(data, list):
                        print(f"  {category}: {len(data)} items")
                    else:
                        print(f"  {category}: data collected")
        
        print("\n✅ Batch collection completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during batch example: {e}")
    
    finally:
        collector.close()

async def main():
    """Run all examples"""
    print("University Data Collection System - Examples")
    print("=" * 60)
    
    # Run examples
    await simple_example()
    await mcp_example()
    await batch_example()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    
    print("\nTo run more examples or customize the system:")
    print("1. Check the README.md for detailed documentation")
    print("2. Run 'python app/test_system.py' for comprehensive tests")
    print("3. Use 'python -m app.main --help' for command-line options")

if __name__ == "__main__":
    asyncio.run(main()) 