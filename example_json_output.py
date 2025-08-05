#!/usr/bin/env python3
"""
Example script demonstrating JSON output functionality
for the University Data Collection System
"""

import asyncio
import json
from pathlib import Path
from app.main import UniversityDataCollector

async def example_single_university_json():
    """Example: Collect data for a single university and save to JSON"""
    print("=== Single University JSON Output Example ===")
    
    collector = UniversityDataCollector()
    
    try:
        # Collect data for MIT and save to JSON
        result = await collector.collect_and_save(
            university_name="Massachusetts Institute of Technology",
            fields=["basic_info", "contact", "academic", "statistics"],
            use_llm=True,
            output_dir="output"
        )
        
        print(f"✅ Data collected successfully!")
        print(f"📊 Status: {result['status']}")
        print(f"🎯 Confidence Score: {result['confidence_score']:.2f}")
        print(f"📁 JSON File: {result.get('json_file', 'Not saved')}")
        print(f"🤖 LLM Enhanced: {result.get('llm_enhanced', False)}")
        
        # Show a preview of the collected data
        if result.get('data'):
            print("\n📋 Data Preview:")
            for category, data in result['data'].items():
                print(f"\n  {category.upper()}:")
                if isinstance(data, dict):
                    for key, value in list(data.items())[:3]:  # Show first 3 items
                        print(f"    {key}: {value}")
                elif isinstance(data, list):
                    for item in data[:2]:  # Show first 2 items
                        print(f"    - {item}")
                else:
                    print(f"    {data}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        collector.close()

async def example_batch_collection_json():
    """Example: Collect data for multiple universities and save to JSON"""
    print("\n=== Batch Collection JSON Output Example ===")
    
    collector = UniversityDataCollector()
    
    try:
        # List of universities to collect data for
        universities = [
            "Harvard University"
        ]
        
        print(f"🎓 Collecting data for {len(universities)} universities...")
        
        # Collect data and save to JSON files
        result = await collector.batch_collect_and_save(
            university_list=universities,
            fields=["basic_info", "statistics", "academic"],
            use_llm=True,
            output_dir="output",
            save_individual=True,
            save_batch=True
        )
        
        print(f"✅ Batch collection completed!")
        print(f"📊 Summary:")
        print(f"   Total Universities: {result['total_universities']}")
        print(f"   ✅ Successful: {result['successful']}")
        print(f"   ❌ Failed: {result['failed']}")
        print(f"   📁 Individual Files: {len(result['individual_files'])}")
        print(f"   📦 Batch File: {result['batch_file']}")
        
        # Show individual file paths
        if result['individual_files']:
            print(f"\n📄 Individual JSON Files:")
            for file_path in result['individual_files']:
                print(f"   - {file_path}")
        
        # Show batch file details
        if result['batch_file']:
            print(f"\n📦 Batch File Details:")
            batch_file = Path(result['batch_file'])
            if batch_file.exists():
                with open(batch_file, 'r') as f:
                    batch_data = json.load(f)
                
                metadata = batch_data.get('metadata', {})
                print(f"   📊 Total Universities: {metadata.get('total_universities', 0)}")
                print(f"   ✅ Successful Collections: {metadata.get('successful_collections', 0)}")
                print(f"   ❌ Failed Collections: {metadata.get('failed_collections', 0)}")
                print(f"   🤖 LLM Enhanced: {metadata.get('llm_enhanced', False)}")
                print(f"   📅 Generated At: {metadata.get('generated_at', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        collector.close()

async def example_custom_json_output():
    """Example: Custom JSON output with specific filename"""
    print("\n=== Custom JSON Output Example ===")
    
    collector = UniversityDataCollector()
    
    try:
        # Collect data for Yale University
        result = await collector.collect_university_data(
            university_name="Yale University",
            fields=["basic_info", "contact", "about"],
            use_llm=True
        )
        
        # Save with custom filename
        custom_filename = "yale_university_detailed.json"
        file_path = collector.save_to_json(
            data=result,
            filename=custom_filename,
            output_dir="output"
        )
        
        print(f"✅ Custom JSON file created!")
        print(f"📁 File: {file_path}")
        print(f"📊 Status: {result['status']}")
        print(f"🎯 Confidence: {result['confidence_score']:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        collector.close()

async def example_read_json_output():
    """Example: Read and display JSON output files"""
    print("\n=== Reading JSON Output Files ===")
    
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ No output directory found. Run other examples first.")
        return
    
    # Find all JSON files
    json_files = list(output_dir.glob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found in output directory.")
        return
    
    print(f"📁 Found {len(json_files)} JSON file(s):")
    
    for json_file in json_files:
        print(f"\n📄 File: {json_file.name}")
        print(f"   Size: {json_file.stat().st_size} bytes")
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Check if it's a batch file or individual file
            if 'metadata' in data and 'universities' in data:
                # Batch file
                metadata = data['metadata']
                universities = data['universities']
                print(f"   📦 Type: Batch file")
                print(f"   🎓 Universities: {metadata.get('total_universities', 0)}")
                print(f"   ✅ Successful: {metadata.get('successful_collections', 0)}")
                print(f"   ❌ Failed: {metadata.get('failed_collections', 0)}")
                
                # Show first university as preview
                if universities:
                    first_uni = universities[0]
                    print(f"   👀 Preview: {first_uni.get('university_name', 'Unknown')} - {first_uni.get('status', 'Unknown')}")
            else:
                # Individual file
                print(f"   🎓 Type: Individual university file")
                print(f"   🏫 University: {data.get('university_name', 'Unknown')}")
                print(f"   📊 Status: {data.get('status', 'Unknown')}")
                print(f"   🎯 Confidence: {data.get('confidence_score', 0):.2f}")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

async def main():
    """Run all JSON output examples"""
    print("🚀 University Data Collection System - JSON Output Examples")
    print("=" * 60)
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Run examples
    await example_single_university_json()
    await example_batch_collection_json()
    await example_custom_json_output()
    await example_read_json_output()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("📁 Check the 'output' directory for generated JSON files.")

if __name__ == "__main__":
    asyncio.run(main()) 