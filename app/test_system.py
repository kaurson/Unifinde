#!/usr/bin/env python3
"""
Test script for the University Data Collection System
"""

import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import UniversityDataCollector

async def test_basic_functionality():
    """Test basic functionality of the system"""
    print("Testing University Data Collection System")
    print("=" * 50)
    
    collector = UniversityDataCollector()
    
    try:
        # Test 1: Get available fields
        print("\n1. Available Fields:")
        fields = collector.get_available_fields()
        for category, field_dict in fields.items():
            print(f"  {category}: {len(field_dict)} fields")
        
        # Test 2: Collect data for a single university
        print("\n2. Collecting data for MIT...")
        result = await collector.collect_university_data(
            "Massachusetts Institute of Technology",
            fields=["basic_info", "contact"]
        )
        
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        print(f"Source: {result['source_url']}")
        
        if result.get('data'):
            print("Collected data:")
            for category, data in result['data'].items():
                print(f"  {category}: {len(data) if isinstance(data, (list, dict)) else 1} items")
        
        # Test 3: Test with different fields
        print("\n3. Collecting academic information...")
        academic_result = await collector.collect_university_data(
            "Stanford University",
            fields=["academic", "statistics"]
        )
        
        print(f"Status: {academic_result['status']}")
        print(f"Confidence: {academic_result['confidence_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
    
    finally:
        collector.close()

async def test_mcp_style():
    """Test MCP-style field requests"""
    print("\nTesting MCP-Style Requests")
    print("=" * 30)
    
    collector = UniversityDataCollector()
    
    try:
        # Simulate LLM making specific field requests
        requests = [
            {
                "university": "Harvard University",
                "fields": ["basic_info", "academic"],
                "description": "LLM needs basic info and academic details"
            },
            {
                "university": "University of California Berkeley",
                "fields": ["statistics", "programs"],
                "description": "LLM needs statistics and program information"
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
        
        return True
        
    except Exception as e:
        print(f"Error during MCP testing: {e}")
        return False
    
    finally:
        collector.close()

async def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\nTesting Error Handling")
    print("=" * 20)
    
    collector = UniversityDataCollector()
    
    try:
        # Test with non-existent university
        print("\n1. Testing with non-existent university...")
        result = await collector.collect_university_data(
            "NonExistentUniversity12345",
            fields=["basic_info"]
        )
        
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
        # Test with invalid fields
        print("\n2. Testing with invalid fields...")
        result = await collector.collect_university_data(
            "MIT",
            fields=["invalid_field_1", "invalid_field_2"]
        )
        
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Error during error handling test: {e}")
        return False
    
    finally:
        collector.close()

async def main():
    """Run all tests"""
    print("University Data Collection System - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("MCP-Style Requests", test_mcp_style),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")

if __name__ == "__main__":
    asyncio.run(main()) 