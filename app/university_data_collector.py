#!/usr/bin/env python3
"""
University Data Collection Script
A standalone script to collect university data using browser automation and LLM
"""

import asyncio
import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('../.env')

# Remove the hardcoded SQLite database URL - let it use the environment variable
# os.environ['DATABASE_URL'] = 'sqlite:///../universities.db'

from database.database import get_db
from browser_tools.university_scraper import UniversityDataScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('university_collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UniversityDataCollector:
    """Standalone university data collector"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.db_session = next(get_db())
        self.scraper = UniversityDataScraper(
            db_session=self.db_session
        )
    
    async def collect_single_university(self, university_name: str) -> Dict[str, Any]:
        """Collect data for a single university"""
        logger.info(f"Starting data collection for: {university_name}")
        
        try:
            result = await self.scraper.collect_university_data(university_name)
            
            if result.get("success"):
                logger.info(f"✅ Successfully collected data for {university_name}")
                logger.info(f"   Confidence Score: {result.get('confidence_score', 0):.2f}")
                logger.info(f"   Collection ID: {result.get('data_collection_id')}")
                logger.info(f"   Source URLs: {len(result.get('source_urls', []))}")
                
                # Log extracted data summary
                extracted_data = result.get("extracted_data", {})
                if extracted_data:
                    logger.info(f"   Name: {extracted_data.get('name', 'N/A')}")
                    logger.info(f"   Website: {extracted_data.get('website', 'N/A')}")
                    logger.info(f"   Location: {extracted_data.get('city', 'N/A')}, {extracted_data.get('state', 'N/A')}")
                    logger.info(f"   Student Population: {extracted_data.get('student_population', 'N/A')}")
                    logger.info(f"   Acceptance Rate: {extracted_data.get('acceptance_rate', 'N/A')}")
                    programs = extracted_data.get('programs', [])
                    if programs is not None:
                        logger.info(f"   Programs Found: {len(programs)}")
                    else:
                        logger.info(f"   Programs Found: 0")
            else:
                logger.error(f"❌ Failed to collect data for {university_name}")
                logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error collecting data for {university_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "university_name": university_name
            }
    
    async def collect_multiple_universities(self, university_names: List[str], delay: int = 5) -> List[Dict[str, Any]]:
        """Collect data for multiple universities with delay between requests"""
        results = []
        
        for i, university_name in enumerate(university_names, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing university {i}/{len(university_names)}: {university_name}")
            logger.info(f"{'='*60}")
            
            result = await self.collect_single_university(university_name)
            results.append(result)
            
            # Add delay between universities (except for the last one)
            if i < len(university_names):
                logger.info(f"Waiting {delay} seconds before next university...")
                await asyncio.sleep(delay)
        
        return results
    
    def save_results_to_json(self, results: List[Dict[str, Any]], output_file: str = None) -> str:
        """Save collection results to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"university_data_collection_{timestamp}.json"
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / output_file
        
        # Prepare data for JSON
        collection_data = {
            "metadata": {
                "total_universities": len(results),
                "successful_collections": len([r for r in results if r.get("success")]),
                "failed_collections": len([r for r in results if not r.get("success")]),
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0"
            },
            "results": results
        }
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ Results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print a summary of the collection results"""
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        logger.info(f"\n{'='*60}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Universities: {len(results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        logger.info(f"Success Rate: {len(successful)/len(results)*100:.1f}%")
        
        if successful:
            avg_confidence = sum(r.get('confidence_score', 0) for r in successful) / len(successful)
            logger.info(f"Average Confidence Score: {avg_confidence:.2f}")
        
        if failed:
            logger.info(f"\nFailed Universities:")
            for result in failed:
                logger.info(f"  - {result.get('university_name', 'Unknown')}: {result.get('error', 'Unknown error')}")
    
    def close(self):
        """Close the collector and clean up resources"""
        if self.db_session:
            self.db_session.close()

async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="University Data Collection Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect data for a single university
  python university_data_collector.py "Stanford University"
  
  # Collect data for multiple universities
  python university_data_collector.py "Stanford University" "MIT" "Harvard University"
  
  # Collect from a file with university names (one per line)
  python university_data_collector.py --file universities.txt
  
  # Save results to a specific file
  python university_data_collector.py --file universities.txt --output my_results.json
  
  # Set delay between universities (default: 5 seconds)
  python university_data_collector.py --file universities.txt --delay 10
        """
    )
    
    parser.add_argument(
        "universities", 
        nargs="*", 
        help="University names to collect data for"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="File containing university names (one per line)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file name (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=5,
        help="Delay between universities in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.universities and not args.file:
        parser.error("Must provide either university names or a file with --file")
    
    # Get university names
    university_names = []
    
    if args.universities:
        university_names.extend(args.universities)
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            parser.error(f"File not found: {args.file}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            file_universities = [line.strip() for line in f if line.strip()]
            university_names.extend(file_universities)
    
    # Remove duplicates while preserving order
    seen = set()
    university_names = [name for name in university_names if not (name in seen or seen.add(name))]
    
    if not university_names:
        parser.error("No valid university names found")
    
    logger.info(f"Found {len(university_names)} universities to process")
    logger.info(f"Universities: {', '.join(university_names)}")
    
    # Initialize collector
    try:
        collector = UniversityDataCollector(openai_api_key=args.openai_key)
    except ValueError as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    
    try:
        # Collect data
        if len(university_names) == 1:
            # Single university
            result = await collector.collect_single_university(university_names[0])
            results = [result]
        else:
            # Multiple universities
            results = await collector.collect_multiple_universities(university_names, args.delay)
        
        # Print summary
        collector.print_summary(results)
        
        # Save results
        if not args.no_save:
            output_file = collector.save_results_to_json(results, args.output)
            logger.info(f"Results saved to: {output_file}")
        
        # Exit with error code if any collections failed
        failed_count = len([r for r in results if not r.get("success")])
        if failed_count > 0:
            logger.warning(f"⚠️  {failed_count} collections failed")
            sys.exit(1)
        else:
            logger.info("✅ All collections completed successfully!")
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        collector.close()

def run_from_file(file_path: str, output_file: str = None, delay: int = 5):
    """Convenience function to run collection from a file"""
    async def run():
        # Read university names from file
        with open(file_path, 'r', encoding='utf-8') as f:
            university_names = [line.strip() for line in f if line.strip()]
        
        if not university_names:
            print("No university names found in file")
            return
        
        # Initialize collector
        collector = UniversityDataCollector()
        
        try:
            # Collect data
            results = await collector.collect_multiple_universities(university_names, delay)
            
            # Print summary
            collector.print_summary(results)
            
            # Save results
            if output_file:
                collector.save_results_to_json(results, output_file)
            
        finally:
            collector.close()
    
    asyncio.run(run())

if __name__ == "__main__":
    asyncio.run(main()) 