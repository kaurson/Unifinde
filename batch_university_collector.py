#!/usr/bin/env python3
"""
Batch University Data Collection Script
A sophisticated script to collect university data from a CSV file using the university_data_collector.py
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
        logging.FileHandler('batch_university_collection.log'),
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

class BatchUniversityCollector:
    """Sophisticated batch university data collector with rich terminal interface"""
    
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
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    entry = UniversityEntry.from_csv_row(row)
                    
                    # Skip if no name
                    if not entry.name:
                        continue
                    
                    # Apply rank filters
                    if start_rank and entry.rank and entry.rank < start_rank:
                        continue
                    if end_rank and entry.rank and entry.rank > end_rank:
                        continue
                    
                    # Apply country filter
                    if countries and entry.country not in countries:
                        continue
                    
                    universities.append(entry)
                    
                    # Apply limit
                    if limit and len(universities) >= limit:
                        break
                        
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Skipping invalid row: {e}[/yellow]")
                    continue
        
        return universities
    
    def create_summary_table(self, universities: List[UniversityEntry]) -> Table:
        """Create a summary table of universities to be processed"""
        table = Table(title="Universities to Process", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Country", style="green")
        table.add_column("Students", style="yellow", no_wrap=True)
        table.add_column("Score", style="blue", no_wrap=True)
        
        for uni in universities:
            students = f"{uni.student_population:,.0f}" if uni.student_population else "N/A"
            score = f"{uni.overall_score:.1f}" if uni.overall_score else "N/A"
            rank = f"{uni.rank:.0f}" if uni.rank else "N/A"
            
            table.add_row(rank, uni.name, uni.country, students, score)
        
        return table
    
    def create_progress_layout(self) -> Layout:
        """Create the progress display layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=5),
            Layout(name="current", size=8),
            Layout(name="stats", size=6),
            Layout(name="footer", size=3)
        )
        
        return layout
    
    def update_progress_display(self, layout: Layout, current_uni: UniversityEntry, 
                              progress: Progress, current_index: int, total: int,
                              successful: int, failed: int, avg_confidence: float):
        """Update the progress display"""
        # Header
        header_text = Text("🎓 Batch University Data Collection", style="bold blue")
        header_text.append(f" | Processing: {current_index}/{total}", style="cyan")
        layout["header"].update(Panel(Align.center(header_text)))
        
        # Progress bar
        layout["progress"].update(Panel(progress))
        
        # Current university info
        current_info = Table.grid()
        current_info.add_column("Property", style="cyan", no_wrap=True)
        current_info.add_column("Value", style="white")
        
        current_info.add_row("Name", current_uni.name)
        current_info.add_row("Country", current_uni.country)
        current_info.add_row("Rank", f"{current_uni.rank:.0f}" if current_uni.rank else "N/A")
        current_info.add_row("Students", f"{current_uni.student_population:,.0f}" if current_uni.student_population else "N/A")
        current_info.add_row("Score", f"{current_uni.overall_score:.1f}" if current_uni.overall_score else "N/A")
        
        layout["current"].update(Panel(current_info, title="Current University", border_style="green"))
        
        # Statistics
        stats_info = Table.grid()
        stats_info.add_column("Metric", style="cyan", no_wrap=True)
        stats_info.add_column("Value", style="white")
        
        success_rate = (successful / (successful + failed)) * 100 if (successful + failed) > 0 else 0
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        avg_time_per_uni = elapsed_time / (successful + failed) if (successful + failed) > 0 else 0
        remaining_unis = total - (successful + failed)
        eta = remaining_unis * avg_time_per_uni if avg_time_per_uni > 0 else 0
        
        stats_info.add_row("Successful", f"{successful} ({success_rate:.1f}%)")
        stats_info.add_row("Failed", str(failed))
        stats_info.add_row("Avg Confidence", f"{avg_confidence:.2f}")
        stats_info.add_row("Elapsed Time", str(timedelta(seconds=int(elapsed_time))))
        stats_info.add_row("ETA", str(timedelta(seconds=int(eta))))
        
        layout["stats"].update(Panel(stats_info, title="Statistics", border_style="blue"))
        
        # Footer
        footer_text = Text("Press Ctrl+C to stop gracefully", style="yellow")
        layout["footer"].update(Panel(Align.center(footer_text)))
    
    async def collect_universities_batch(self, universities: List[UniversityEntry], 
                                       delay: int = 5, save_progress: bool = True, 
                                       skip_existing: bool = True, max_retries: int = 3,
                                       max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Collect data for a batch of universities with parallel processing"""
        self.start_time = time.time()
        results = []
        successful = 0
        failed = 0
        skipped = 0
        total_confidence = 0
        
        # Create a semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Print initial header
        self.console.print("\n[bold blue]🎓 Batch University Data Collection[/bold blue]")
        self.console.print(f"[cyan]Processing {len(universities)} universities with {delay}s delay[/cyan]")
        self.console.print(f"[cyan]🔄 Max concurrent operations: {max_concurrent}[/cyan]")
        if skip_existing:
            self.console.print("[yellow]⚠️  Skipping universities that already exist in database[/yellow]")
        self.console.print(f"[yellow]🔄 Max retries per university: {max_retries}[/yellow]")
        self.console.print()
        
        # Create tasks for all universities with staggered start
        async def process_university(university: UniversityEntry, index: int) -> Dict[str, Any]:
            async with semaphore:  # Limit concurrent operations
                return await self._process_single_university(university, index, len(universities), 
                                                           skip_existing, max_retries, delay)
        
        tasks = []
        for i, university in enumerate(universities, 1):
            task = asyncio.create_task(process_university(university, i))
            tasks.append(task)
            # Add a small delay between task creation to avoid overwhelming the network
            if i < len(universities):
                await asyncio.sleep(1)
        
        # Process all tasks and collect results
        completed = 0
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                completed += 1
                
                # Update statistics
                if result.get("success"):
                    if result.get("skipped"):
                        skipped += 1
                    else:
                        successful += 1
                        confidence = result.get('confidence_score', 0)
                        total_confidence += confidence
                else:
                    failed += 1
                
                # Print progress
                total_processed = successful + failed + skipped
                success_rate = (successful / total_processed) * 100 if total_processed > 0 else 0
                avg_confidence = total_confidence / successful if successful > 0 else 0
                elapsed_time = time.time() - self.start_time
                avg_time_per_uni = elapsed_time / total_processed if total_processed > 0 else 0
                remaining_unis = len(universities) - total_processed
                eta = remaining_unis * avg_time_per_uni if avg_time_per_uni > 0 else 0
                
                self.console.print(f"[blue]📊 Progress: {successful} successful, {failed} failed, {skipped} skipped ({success_rate:.1f}%) | Avg Confidence: {avg_confidence:.2f} | ETA: {timedelta(seconds=int(eta))} | Completed: {completed}/{len(universities)}[/blue]")
                
                # Save progress periodically
                if save_progress and completed % 10 == 0:
                    checkpoint_file = self.save_progress(results, f"progress_checkpoint_{completed}.json")
                    self.console.print(f"[yellow]💾 Progress saved to: {checkpoint_file}[/yellow]")
                
            except Exception as e:
                failed += 1
                error_result = {
                    "success": False,
                    "error": str(e),
                    "university_name": "Unknown",
                    "csv_data": {}
                }
                results.append(error_result)
                self.console.print(f"[red]❌ Task failed: {e}[/red]")
        
        return results
    
    async def _process_single_university(self, university: UniversityEntry, index: int, total: int,
                                       skip_existing: bool, max_retries: int, delay: int) -> Dict[str, Any]:
        """Process a single university with retry logic"""
        # Print current university info
        self.console.print(f"\n[bold cyan]📚 University {index}/{total}: {university.name}[/bold cyan]")
        self.console.print(f"   Country: {university.country} | Rank: {university.rank:.0f} | Students: {university.student_population:,.0f}")
        
        # Print progress bar manually
        progress_percent = (index - 1) / total * 100
        progress_bar = "█" * int(progress_percent / 5) + "░" * (20 - int(progress_percent / 5))
        self.console.print(f"[blue]Progress: [{progress_bar}] {progress_percent:.1f}% ({index}/{total})[/blue]")
        
        # Check if university already exists
        if skip_existing and self.check_university_exists(university.name):
            existing_info = self.get_existing_university_info(university.name)
            
            # Create a result entry for skipped university
            skip_result = {
                "success": True,
                "university_name": university.name,
                "confidence_score": existing_info.get("confidence_score", 0.0),
                "data_collection_id": existing_info.get("id", "existing"),
                "source_urls": [],
                "extracted_data": {
                    "name": existing_info.get("name", university.name),
                    "country": existing_info.get("country", university.country)
                },
                "csv_data": {
                    'rank': university.rank,
                    'country': university.country,
                    'student_population': university.student_population,
                    'overall_score': university.overall_score,
                    'year': university.year
                },
                "skipped": True,
                "existing_info": existing_info
            }
            
            # Log skip
            last_updated = existing_info.get("last_updated", "Unknown")
            self.console.print(f"[yellow]⏭️  Skipped (already exists) - Last updated: {last_updated}[/yellow]")
            
            return skip_result
        
        # Collect data for current university with retry logic
        result = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.console.print(f"[yellow]🔄 Retry attempt {attempt + 1}/{max_retries} for {university.name}[/yellow]")
                    # Add extra delay for retries
                    await asyncio.sleep(delay * 2)
                
                result = await self.collector.collect_single_university(university.name)
                
                if result.get("success"):
                    break  # Success, exit retry loop
                else:
                    error = result.get('error', 'Unknown error')
                    if "network" in error.lower() or "connection" in error.lower() or "dns" in error.lower():
                        self.console.print(f"[yellow]⚠️  Network error detected: {error}[/yellow]")
                        if attempt < max_retries - 1:
                            self.console.print(f"[yellow]⏳ Waiting before retry...[/yellow]")
                            continue
                    else:
                        # Non-network error, don't retry
                        break
                        
            except Exception as e:
                error_msg = str(e)
                self.console.print(f"[red]❌ Exception on attempt {attempt + 1}: {error_msg}[/red]")
                
                if "network" in error_msg.lower() or "connection" in error_msg.lower() or "dns" in error_msg.lower():
                    if attempt < max_retries - 1:
                        self.console.print(f"[yellow]⏳ Network issue detected, retrying...[/yellow]")
                        continue
                else:
                    # Non-network exception, don't retry
                    break
        
        # Process the result
        if result is None:
            result = {
                "success": False,
                "error": f"All {max_retries} attempts failed",
                "university_name": university.name
            }
        
        # Add metadata
        result['csv_data'] = {
            'rank': university.rank,
            'country': university.country,
            'student_population': university.student_population,
            'overall_score': university.overall_score,
            'year': university.year
        }
        
        if result.get("success"):
            confidence = result.get('confidence_score', 0)
            self.console.print(f"[green]✅ Success! Confidence: {confidence:.2f}[/green]")
        else:
            error = result.get('error', 'Unknown error')
            self.console.print(f"[red]❌ Failed after {max_retries} attempts: {error}[/red]")
        
        return result
    
    def save_progress(self, results: List[Dict[str, Any]], filename: str = None) -> str:
        """Save current progress to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_university_collection_{timestamp}.json"
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        
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
        
        return str(output_path)
    
    def print_final_summary(self, results: List[Dict[str, Any]], universities: List[UniversityEntry]):
        """Print a comprehensive final summary"""
        successful = [r for r in results if r.get("success") and not r.get("skipped")]
        failed = [r for r in results if not r.get("success")]
        skipped = [r for r in results if r.get("skipped")]
        
        # Create summary table
        summary_table = Table(title="Final Collection Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        success_rate = len(successful) / len(results) * 100 if results else 0
        avg_confidence = sum(r.get('confidence_score', 0) for r in successful) / len(successful) if successful else 0
        
        summary_table.add_row("Total Universities", str(len(universities)))
        summary_table.add_row("Processed", str(len(results)))
        summary_table.add_row("Successful", f"{len(successful)} ({success_rate:.1f}%)")
        summary_table.add_row("Failed", str(len(failed)))
        summary_table.add_row("Skipped (Already Exist)", str(len(skipped)))
        summary_table.add_row("Average Confidence", f"{avg_confidence:.2f}")
        
        if self.start_time:
            elapsed_time = time.time() - self.start_time
            avg_time_per_uni = elapsed_time / len(results) if results else 0
            summary_table.add_row("Total Time", str(timedelta(seconds=int(elapsed_time))))
            summary_table.add_row("Avg Time per University", f"{avg_time_per_uni:.1f}s")
        
        self.console.print(summary_table)
        
        # Show skipped universities
        if skipped:
            skipped_table = Table(title="Skipped Universities (Already Exist)", show_header=True, header_style="bold yellow")
            skipped_table.add_column("Name", style="white")
            skipped_table.add_column("Last Updated", style="yellow")
            skipped_table.add_column("Confidence", style="blue")
            
            for result in skipped:
                existing_info = result.get('existing_info', {})
                skipped_table.add_row(
                    existing_info.get('name', result.get('university_name', 'Unknown')),
                    existing_info.get('last_updated', 'Unknown'),
                    f"{existing_info.get('confidence_score', 0):.2f}"
                )
            
            self.console.print(skipped_table)
        
        # Show failed universities
        if failed:
            failed_table = Table(title="Failed Universities", show_header=True, header_style="bold red")
            failed_table.add_column("Name", style="white")
            failed_table.add_column("Error", style="red")
            
            for result in failed:
                failed_table.add_row(
                    result.get('university_name', 'Unknown'),
                    result.get('error', 'Unknown error')
                )
            
            self.console.print(failed_table)
    
    def close(self):
        """Close the collector and clean up resources"""
        if self.collector:
            self.collector.close()

    def check_university_exists(self, university_name: str) -> bool:
        """Check if a university already exists in the database"""
        try:
            from database.models import University
            from sqlalchemy import or_
            
            # Search for university by name (case-insensitive)
            existing_university = self.collector.db_session.query(University).filter(
                or_(
                    University.name.ilike(university_name),
                    University.name.ilike(f"%{university_name}%")
                )
            ).first()
            
            return existing_university is not None
            
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not check if university exists: {e}[/yellow]")
            return False
    
    def get_existing_university_info(self, university_name: str) -> Dict[str, Any]:
        """Get information about an existing university"""
        try:
            from database.models import University
            from sqlalchemy import or_
            
            existing_university = self.collector.db_session.query(University).filter(
                or_(
                    University.name.ilike(university_name),
                    University.name.ilike(f"%{university_name}%")
                )
            ).first()
            
            if existing_university:
                return {
                    "id": str(existing_university.id),
                    "name": existing_university.name,
                    "country": existing_university.country,
                    "confidence_score": existing_university.confidence_score,
                    "last_updated": existing_university.last_updated.isoformat() if existing_university.last_updated else None
                }
            
            return {}
            
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not get existing university info: {e}[/yellow]")
            return {}

    def check_network_connectivity(self) -> bool:
        """Check basic network connectivity"""
        import socket
        import urllib.request
        import urllib.error
        
        self.console.print("[blue]🔍 Checking network connectivity...[/blue]")
        
        # Test DNS resolution
        try:
            socket.gethostbyname("google.com")
            self.console.print("[green]✅ DNS resolution working[/green]")
        except socket.gaierror:
            self.console.print("[red]❌ DNS resolution failed[/red]")
            return False
        
        # Test HTTP connectivity
        try:
            urllib.request.urlopen("http://httpbin.org/get", timeout=10)
            self.console.print("[green]✅ HTTP connectivity working[/green]")
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            self.console.print(f"[red]❌ HTTP connectivity failed: {e}[/red]")
            return False
        
        # Test HTTPS connectivity
        try:
            urllib.request.urlopen("https://httpbin.org/get", timeout=10)
            self.console.print("[green]✅ HTTPS connectivity working[/green]")
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            self.console.print(f"[red]❌ HTTPS connectivity failed: {e}[/red]")
            return False
        
        self.console.print("[green]✅ Network connectivity check passed[/green]")
        return True

async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description="Batch University Data Collection Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all universities from the CSV file (skip existing)
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv"
  
  # Process only top 50 universities (skip existing)
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --limit 50
  
  # Force collection even if universities already exist
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --force
  
  # Check network connectivity before starting
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --check-network
  
  # Increase retry attempts for network issues
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --max-retries 5
  
  # Process with higher concurrency for faster collection
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --max-concurrent 10
  
  # Process universities ranked 1-100
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --start-rank 1 --end-rank 100
  
  # Process only US universities
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --countries "United States"
  
  # Process with custom delay and output file
  python batch_university_collector.py "THE World University Rankings 2016-2025.csv" --delay 10 --output my_results.json
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
        "--preview",
        action="store_true",
        help="Show preview of universities to be processed without starting collection"
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
        "--check-network",
        action="store_true",
        help="Run network connectivity check before starting collection"
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
        collector = BatchUniversityCollector(openai_api_key=args.openai_key)
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
        
        # Show preview if requested
        if args.preview:
            summary_table = collector.create_summary_table(universities)
            console.print(summary_table)
            return
        
        # Show summary table
        summary_table = collector.create_summary_table(universities[:10])  # Show first 10
        console.print(summary_table)
        if len(universities) > 10:
            console.print(f"[yellow]... and {len(universities) - 10} more universities[/yellow]")
        
        # Run network check if requested
        if args.check_network:
            if not collector.check_network_connectivity():
                console.print("[red]❌ Network connectivity check failed. Please check your internet connection.[/red]")
                console.print("[yellow]💡 Try running with --check-network to diagnose network issues.[/yellow]")
                sys.exit(1)
        
        # Confirm before starting
        console.print(f"\n[blue]🚀 Ready to process {len(universities)} universities with {args.delay}s delay between requests[/blue]")
        console.print(f"[blue]🔄 Max retries per university: {args.max_retries}[/blue]")
        console.print(f"[blue]⚡ Max concurrent operations: {args.max_concurrent}[/blue]")
        console.print("[yellow]Press Enter to start or Ctrl+C to cancel...[/yellow]")
        
        try:
            input()
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            return
        
        # Start collection
        console.print(f"\n[green]🎯 Starting batch collection...[/green]")
        
        results = await collector.collect_universities_batch(
            universities, 
            delay=args.delay,
            save_progress=not args.no_save_progress,
            skip_existing=not args.force, # Enable skipping existing universities
            max_retries=args.max_retries, # Use the command-line argument for max retries
            max_concurrent=args.max_concurrent # Use the command-line argument for max concurrent
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