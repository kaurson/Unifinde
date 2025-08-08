#!/usr/bin/env python3
"""
Automated Batch University Data Collection Script
A version that runs without user input for background processing
"""

import asyncio
import csv
import json
import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
import signal

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('.env')

from app.university_data_collector import UniversityDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_university_collection_auto.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class UniversityEntry:
    """Represents a university entry from the CSV"""
    rank: Optional[float]
    name: str
    country: str
    student_population: Optional[float]
    students_to_staff_ratio: Optional[float]
    international_students: Optional[str]
    female_to_male_ratio: Optional[str]
    overall_score: Optional[float]
    year: Optional[int]
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'UniversityEntry':
        """Create UniversityEntry from CSV row"""
        return cls(
            rank=float(row.get('Rank', 0)) if row.get('Rank') else None,
            name=row.get('Name', '').strip(),
            country=row.get('Country', '').strip(),
            student_population=float(row.get('Student Population', 0)) if row.get('Student Population') else None,
            students_to_staff_ratio=float(row.get('Students to Staff Ratio', 0)) if row.get('Students to Staff Ratio') else None,
            international_students=row.get('International Students', '').strip(),
            female_to_male_ratio=row.get('Female to Male Ratio', '').strip(),
            overall_score=float(row.get('Overall Score', 0)) if row.get('Overall Score') else None,
            year=int(row.get('Year', 0)) if row.get('Year') else None
        )

class AutomatedBatchUniversityCollector:
    """Automated batch university data collector that runs without user input"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        
        self.console = Console()
        self.collector = UniversityDataCollector(openai_api_key=self.openai_api_key)
        self.results = []
        self.current_university = None
        self.start_time = None
        self.interrupted = False
        
        # Set up signal handler for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.interrupted = True
        self.console.print("\n[red]⚠️  Interruption detected. Finishing current university and stopping gracefully...[/red]")
    
    def load_universities_from_csv(self, csv_file: str, limit: Optional[int] = None, 
                                 start_rank: Optional[int] = None, 
                                 end_rank: Optional[int] = None,
                                 countries: Optional[List[str]] = None) -> List[UniversityEntry]:
        """Load universities from CSV file with filtering options"""
        universities = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Apply rank filters
                    if start_rank is not None:
                        try:
                            rank = float(row.get('Rank', 0))
                            if rank < start_rank:
                                continue
                        except (ValueError, TypeError):
                            continue
                    
                    if end_rank is not None:
                        try:
                            rank = float(row.get('Rank', 0))
                            if rank > end_rank:
                                continue
                        except (ValueError, TypeError):
                            continue
                    
                    # Apply country filter
                    if countries and row.get('Country', '').strip() not in countries:
                        continue
                    
                    # Create university entry
                    university = UniversityEntry.from_csv_row(row)
                    universities.append(university)
                    
                    # Apply limit
                    if limit and len(universities) >= limit:
                        break
        
        except Exception as e:
            self.console.print(f"[red]❌ Error loading CSV file: {e}[/red]")
            return []
        
        return universities
    
    def create_summary_table(self, universities: List[UniversityEntry]) -> Table:
        """Create a summary table of universities to be processed"""
        table = Table(title="Universities to Process")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Country", style="green")
        table.add_column("Students", style="yellow", no_wrap=True)
        table.add_column("Score", style="blue", no_wrap=True)
        
        for uni in universities:
            table.add_row(
                str(uni.rank) if uni.rank else "N/A",
                uni.name,
                uni.country,
                f"{uni.student_population:,}" if uni.student_population else "N/A",
                f"{uni.overall_score:.1f}" if uni.overall_score else "N/A"
            )
        
        return table
    
    async def collect_universities_batch(self, universities: List[UniversityEntry], 
                                       delay: int = 5, save_progress: bool = True, 
                                       skip_existing: bool = True, max_retries: int = 3,
                                       max_concurrent: int = 2) -> List[Dict[str, Any]]:
        """Collect data for multiple universities with parallel processing"""
        
        self.start_time = time.time()
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        self.console.print(f"\n🎓 Automated Batch University Data Collection")
        self.console.print(f"Processing {len(universities)} universities with {delay}s delay")
        self.console.print(f"🔄 Max concurrent operations: {max_concurrent}")
        if skip_existing:
            self.console.print(f"⚠️  Skipping universities that already exist in database")
        self.console.print(f"🔄 Max retries per university: {max_retries}")
        
        # Create tasks for all universities
        tasks = []
        for i, university in enumerate(universities):
            task = asyncio.create_task(
                self._process_single_university_with_semaphore(
                    university, i + 1, len(universities), skip_existing, max_retries, delay, semaphore
                )
            )
            tasks.append(task)
            # Small delay between task creation to stagger starts
            await asyncio.sleep(1)
        
        # Process results as they complete
        completed = 0
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                completed += 1
                
                if result.get("success"):
                    successful += 1
                elif result.get("skipped"):
                    skipped += 1
                else:
                    failed += 1
                
                # Update progress
                avg_confidence = sum(r.get("confidence_score", 0) for r in results if r.get("success")) / max(successful, 1)
                eta_seconds = (len(universities) - completed) * (delay + 30) / max_concurrent  # Rough estimate
                eta = timedelta(seconds=int(eta_seconds))
                
                self.console.print(f"📊 Progress: {successful} successful, {failed} failed, {skipped} skipped ({completed/len(universities)*100:.1f}%) | Avg Confidence: {avg_confidence:.2f} | ETA: {eta} | Completed: {completed}/{len(universities)}")
                
            except Exception as e:
                self.console.print(f"❌ Task failed: {e}")
                failed += 1
                completed += 1
        
        return results
    
    async def _process_single_university_with_semaphore(self, university: UniversityEntry, index: int, total: int,
                                                       skip_existing: bool, max_retries: int, delay: int, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        """Process a single university with semaphore control"""
        async with semaphore:
            return await self._process_single_university(university, index, total, skip_existing, max_retries, delay)
    
    async def _process_single_university(self, university: UniversityEntry, index: int, total: int,
                                       skip_existing: bool, max_retries: int, delay: int) -> Dict[str, Any]:
        """Process a single university with retry logic"""
        
        self.console.print(f"\n📚 University {index}/{total}: {university.name}")
        self.console.print(f"   Country: {university.country} | Rank: {university.rank} | Students: {university.student_population:,}" if university.student_population else f"   Country: {university.country} | Rank: {university.rank} | Students: N/A")
        
        # Check if university already exists
        if skip_existing and self.check_university_exists(university.name):
            existing_info = self.get_existing_university_info(university.name)
            self.console.print(f"   ⏭️  Skipping {university.name} (already exists in database)")
            self.console.print(f"   📊 Existing data: Confidence: {existing_info.get('confidence_score', 'N/A')}, Website: {existing_info.get('website', 'N/A')}")
            return {
                "success": True,
                "skipped": True,
                "university_name": university.name,
                "reason": "Already exists in database",
                "existing_data": existing_info
            }
        
        # Retry logic for network issues
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting data collection for: {university.name}")
                
                # Collect data using the university data collector
                result = await self.collector.collect_single_university(university.name)
                
                if result.get("success"):
                    confidence_score = result.get("confidence_score", 0.0)
                    self.console.print(f"✅ Success! Confidence: {confidence_score:.2f}")
                    
                    # Log detailed information
                    extracted_data = result.get("extracted_data", {})
                    logger.info(f"✅ Successfully collected data for {university.name}")
                    logger.info(f"   Confidence Score: {confidence_score:.2f}")
                    logger.info(f"   Collection ID: {result.get('result_record_id')}")
                    logger.info(f"   Source URLs: {len(result.get('source_urls', []))}")
                    logger.info(f"   Name: {extracted_data.get('name', 'N/A')}")
                    logger.info(f"   Website: {extracted_data.get('website', 'N/A')}")
                    logger.info(f"   Location: {extracted_data.get('city', 'N/A')}, {extracted_data.get('state', 'N/A')}")
                    logger.info(f"   Student Population: {extracted_data.get('student_population', 'N/A')}")
                    logger.info(f"   Acceptance Rate: {extracted_data.get('acceptance_rate', 'N/A')}")
                    logger.info(f"   Programs Found: {len(extracted_data.get('programs', []))}")
                    
                    return {
                        "success": True,
                        "university_name": university.name,
                        "confidence_score": confidence_score,
                        "result_record_id": result.get("result_record_id"),
                        "source_urls": result.get("source_urls", []),
                        "extracted_data": extracted_data,
                        "csv_data": {
                            "rank": university.rank,
                            "country": university.country,
                            "student_population": university.student_population,
                            "overall_score": university.overall_score,
                            "year": university.year
                        }
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.console.print(f"❌ Failed: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        self.console.print(f"⚠️  Network error detected: {error_msg}")
                        self.console.print(f"⏳ Waiting before retry...")
                        await asyncio.sleep(delay * 2)  # Longer delay for retries
                        self.console.print(f"🔄 Retry attempt {attempt + 2}/{max_retries} for {university.name}")
                    else:
                        logger.error(f"❌ Error collecting data for {university.name}: {error_msg}")
                        return {
                            "success": False,
                            "university_name": university.name,
                            "error": error_msg,
                            "attempts": attempt + 1
                        }
                        
            except Exception as e:
                error_msg = str(e)
                self.console.print(f"❌ Unexpected error: {error_msg}")
                
                if attempt < max_retries - 1:
                    self.console.print(f"⏳ Waiting before retry...")
                    await asyncio.sleep(delay * 2)
                    self.console.print(f"🔄 Retry attempt {attempt + 2}/{max_retries} for {university.name}")
                else:
                    logger.error(f"❌ Error collecting data for {university.name}: {error_msg}")
                    return {
                        "success": False,
                        "university_name": university.name,
                        "error": error_msg,
                        "attempts": attempt + 1
                    }
        
        # If we get here, all retries failed
        return {
            "success": False,
            "university_name": university.name,
            "error": "All retry attempts failed",
            "attempts": max_retries
        }
    
    def save_progress(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Save progress to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/batch_university_collection_auto_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Calculate statistics
        successful = len([r for r in results if r.get("success") and not r.get("skipped")])
        failed = len([r for r in results if not r.get("success")])
        skipped = len([r for r in results if r.get("skipped")])
        
        # Create output structure
        output_data = {
            "metadata": {
                "total_universities": len(results),
                "successful_collections": successful,
                "failed_collections": failed,
                "skipped_collections": skipped,
                "generated_at": datetime.now().isoformat(),
                "script_version": "1.0.0-auto"
            },
            "results": results
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        return filename
    
    def print_final_summary(self, results: List[Dict[str, Any]], universities: List[UniversityEntry]):
        """Print final summary of the collection process"""
        
        # Calculate statistics
        successful = len([r for r in results if r.get("success") and not r.get("skipped")])
        failed = len([r for r in results if not r.get("success")])
        skipped = len([r for r in results if r.get("skipped")])
        
        # Calculate average confidence
        confidence_scores = [r.get("confidence_score", 0) for r in results if r.get("success") and not r.get("skipped")]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Calculate timing
        total_time = time.time() - self.start_time if self.start_time else 0
        avg_time_per_uni = total_time / len(universities) if universities else 0
        
        # Create summary table
        summary_table = Table(title="Final Collection Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Universities", str(len(universities)))
        summary_table.add_row("Processed", str(len(results)))
        summary_table.add_row("Successful", f"{successful} ({successful/len(universities)*100:.1f}%)" if universities else "0")
        summary_table.add_row("Failed", str(failed))
        summary_table.add_row("Skipped (Already Exist)", str(skipped))
        summary_table.add_row("Average Confidence", f"{avg_confidence:.2f}")
        summary_table.add_row("Total Time", str(timedelta(seconds=int(total_time))))
        summary_table.add_row("Avg Time per University", f"{avg_time_per_uni:.1f}s")
        
        self.console.print(summary_table)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self.collector, 'close'):
            self.collector.close()
    
    def check_university_exists(self, university_name: str) -> bool:
        """Check if university already exists in database"""
        try:
            # This would need to be implemented based on your database structure
            # For now, return False to process all universities
            return False
        except Exception as e:
            logger.error(f"Error checking if university exists: {e}")
            return False
    
    def get_existing_university_info(self, university_name: str) -> Dict[str, Any]:
        """Get information about existing university"""
        try:
            # This would need to be implemented based on your database structure
            return {
                "confidence_score": 0.0,
                "website": "N/A"
            }
        except Exception as e:
            logger.error(f"Error getting existing university info: {e}")
            return {}

async def main():
    """Main function for automated command-line usage"""
    parser = argparse.ArgumentParser(
        description="Automated Batch University Data Collection Script (No User Input Required)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process top 20 universities automatically
  python batch_university_collector_auto.py "THE World University Rankings 2016-2025.csv" --limit 20
  
  # Process with higher concurrency
  python batch_university_collector_auto.py "THE World University Rankings 2016-2025.csv" --limit 50 --max-concurrent 3
  
  # Process specific countries
  python batch_university_collector_auto.py "THE World University Rankings 2016-2025.csv" --countries "United States" "United Kingdom"
        """
    )
    
    parser.add_argument(
        "csv_file",
        help="CSV file containing university data"
    )
    
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of universities to process"
    )
    
    parser.add_argument(
        "--start-rank", "-s",
        type=int,
        help="Start processing from this rank (inclusive)"
    )
    
    parser.add_argument(
        "--end-rank", "-e",
        type=int,
        help="End processing at this rank (inclusive)"
    )
    
    parser.add_argument(
        "--countries", "-c",
        nargs="+",
        help="Only process universities from these countries"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=5,
        help="Delay between universities in seconds (default: 5)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file name (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--openai-key",
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--no-save-progress",
        action="store_true",
        help="Don't save progress checkpoints"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force collection even if university already exists in database"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts per university (default: 3)"
    )
    
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=2,
        help="Maximum number of concurrent university processing operations (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Validate CSV file
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        parser.error(f"CSV file not found: {args.csv_file}")
    
    # Initialize collector
    try:
        collector = AutomatedBatchUniversityCollector(openai_api_key=args.openai_key)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    try:
        # Load universities from CSV
        console = Console()
        console.print(f"[blue]📖 Loading universities from: {args.csv_file}[/blue]")
        
        universities = collector.load_universities_from_csv(
            args.csv_file,
            limit=args.limit,
            start_rank=args.start_rank,
            end_rank=args.end_rank,
            countries=args.countries
        )
        
        if not universities:
            console.print("[red]❌ No universities found matching the criteria[/red]")
            sys.exit(1)
        
        console.print(f"[green]✅ Loaded {len(universities)} universities[/green]")
        
        # Show summary table
        summary_table = collector.create_summary_table(universities[:10])  # Show first 10
        console.print(summary_table)
        if len(universities) > 10:
            console.print(f"[yellow]... and {len(universities) - 10} more universities[/yellow]")
        
        # Start collection immediately (no user input required)
        console.print(f"\n[green]🎯 Starting automated batch collection...[/green]")
        console.print(f"[blue]🔄 Max retries per university: {args.max_retries}[/blue]")
        console.print(f"[blue]⚡ Max concurrent operations: {args.max_concurrent}[/blue]")
        
        results = await collector.collect_universities_batch(
            universities, 
            delay=args.delay,
            save_progress=not args.no_save_progress,
            skip_existing=not args.force,
            max_retries=args.max_retries,
            max_concurrent=args.max_concurrent
        )
        
        # Print final summary
        collector.print_final_summary(results, universities)
        
        # Save results
        if args.output:
            output_file = collector.save_progress(results, args.output)
            console.print(f"[green]✅ Results saved to: {output_file}[/green]")
        else:
            output_file = collector.save_progress(results)
            console.print(f"[green]✅ Results saved to: {output_file}[/green]")
        
        # Exit with error code if any collections failed
        failed_count = len([r for r in results if not r.get("success")])
        if failed_count > 0:
            console.print(f"[yellow]⚠️  {failed_count} collections failed[/yellow]")
            sys.exit(1)
        else:
            console.print("[green]✅ All collections completed successfully![/green]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Collection interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        sys.exit(1)
    finally:
        collector.close()

if __name__ == "__main__":
    asyncio.run(main()) 