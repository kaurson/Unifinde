#!/usr/bin/env python3
"""
University Data Collection System
Main application for collecting university information using headless browser scraping
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
import argparse
from pathlib import Path
from datetime import datetime
import os

from .mcp_server import UniversityMCPServer, FieldType, FieldRequest, LLMConfig
from .scraper import UniversityScraper
from .config import load_config, create_env_template, get_example_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UniversityDataCollector:
    """Main class for university data collection"""
    
    def __init__(self, database_url: str = None, llm_config: LLMConfig = None):
        # Load configuration
        config = load_config()
        
        # Use provided config or default
        self.database_url = database_url or config.database.url
        self.llm_config = llm_config or config.llm
        self.config = config
        
        # Initialize MCP server with LLM config (no database_url since we removed database functionality)
        self.mcp_server = UniversityMCPServer(
            llm_config=self.llm_config
        )
    
    async def collect_university_data(self, university_name: str, fields: List[str] = None, use_llm: bool = True) -> Dict[str, Any]:
        """
        Collect data for a specific university
        
        Args:
            university_name: Name of the university to research
            fields: List of field categories to collect (if None, collects all)
            use_llm: Whether to use LLM for data enhancement
            
        Returns:
            Dictionary with collected university data
        """
        if fields is None:
            fields = ["all"]
        
        # Convert field names to FieldType enums
        field_types = []
        for field in fields:
            try:
                field_types.append(FieldType(field))
            except ValueError:
                logger.warning(f"Unknown field type: {field}")
        
        if not field_types:
            field_types = [FieldType.ALL]
        
        # Create field request
        request = FieldRequest(
            university_name=university_name,
            fields=field_types,
            priority=1
        )
        
        # Process request with or without LLM
        if use_llm and self.llm_config.api_key:
            response = await self.mcp_server.process_field_request_with_llm(request)
        else:
            response = await self.mcp_server.process_field_request(request)
        
        return {
            "university_name": response.university_name,
            "status": response.status,
            "confidence_score": response.confidence_score,
            "source_url": response.source_url,
            "scraped_at": response.scraped_at,
            "data": response.fields,
            "llm_enhanced": use_llm and self.llm_config.api_key
        }
    
    async def batch_collect(self, university_list: List[str], fields: List[str] = None, use_llm: bool = True) -> List[Dict[str, Any]]:
        """
        Collect data for multiple universities
        
        Args:
            university_list: List of university names
            fields: List of field categories to collect
            use_llm: Whether to use LLM for data enhancement
            
        Returns:
            List of results for each university
        """
        results = []
        
        for i, university_name in enumerate(university_list, 1):
            logger.info(f"Processing university {i}/{len(university_list)}: {university_name}")
            
            try:
                result = await self.collect_university_data(university_name, fields, use_llm)
                results.append(result)
                
                # Add delay between requests to be respectful
                await asyncio.sleep(self.config.scraper.delay_between_requests)
                
            except Exception as e:
                logger.error(f"Error collecting data for {university_name}: {e}")
                results.append({
                    "university_name": university_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def get_available_fields(self) -> Dict[str, Dict[str, str]]:
        """Get list of available fields that can be collected"""
        return self.mcp_server.get_available_fields()
    
    def get_llm_config(self) -> LLMConfig:
        """Get current LLM configuration"""
        return self.mcp_server.get_llm_config()
    
    def update_llm_config(self, config: LLMConfig):
        """Update LLM configuration"""
        self.mcp_server.update_llm_config(config)
        self.llm_config = config
    
    def close(self):
        """Close the data collector"""
        self.mcp_server.close()
    
    def save_to_json(self, data: Dict[str, Any], filename: str = None, output_dir: str = "output") -> str:
        """
        Save university data to a JSON file
        
        Args:
            data: University data dictionary
            filename: Custom filename (if None, auto-generates based on university name)
            output_dir: Directory to save the JSON file
            
        Returns:
            Path to the saved JSON file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            university_name = data.get("university_name", "unknown")
            # Clean filename by removing special characters
            safe_name = "".join(c for c in university_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = output_path / filename
        
        # Save data to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Data saved to: {file_path}")
        return str(file_path)
    
    def save_batch_to_json(self, results: List[Dict[str, Any]], filename: str = None, output_dir: str = "output") -> str:
        """
        Save batch collection results to a JSON file
        
        Args:
            results: List of university data dictionaries
            filename: Custom filename (if None, auto-generates with timestamp)
            output_dir: Directory to save the JSON file
            
        Returns:
            Path to the saved JSON file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universities_batch_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = output_path / filename
        
        # Create batch data structure
        batch_data = {
            "metadata": {
                "total_universities": len(results),
                "successful_collections": len([r for r in results if r.get("status") == "success"]),
                "failed_collections": len([r for r in results if r.get("status") == "failed"]),
                "generated_at": datetime.now().isoformat(),
                "llm_enhanced": any(r.get("llm_enhanced", False) for r in results)
            },
            "universities": results
        }
        
        # Save data to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Batch data saved to: {file_path}")
        return str(file_path)
    
    async def collect_and_save(self, university_name: str, fields: List[str] = None, use_llm: bool = True, 
                              output_dir: str = "output", save_individual: bool = True) -> Dict[str, Any]:
        """
        Collect university data and save to JSON file
        
        Args:
            university_name: Name of the university to research
            fields: List of field categories to collect
            use_llm: Whether to use LLM for data enhancement
            output_dir: Directory to save the JSON file
            save_individual: Whether to save individual university file
            
        Returns:
            Dictionary with collected data and file path
        """
        # Collect data
        result = await self.collect_university_data(university_name, fields, use_llm)
        
        # Save to JSON file if requested
        if save_individual:
            file_path = self.save_to_json(result, output_dir=output_dir)
            result["json_file"] = file_path
        
        return result
    
    async def batch_collect_and_save(self, university_list: List[str], fields: List[str] = None, 
                                   use_llm: bool = True, output_dir: str = "output", 
                                   save_individual: bool = True, save_batch: bool = True) -> Dict[str, Any]:
        """
        Collect data for multiple universities and save to JSON files
        
        Args:
            university_list: List of university names
            fields: List of field categories to collect
            use_llm: Whether to use LLM for data enhancement
            output_dir: Directory to save JSON files
            save_individual: Whether to save individual university files
            save_batch: Whether to save combined batch file
            
        Returns:
            Dictionary with results and file paths
        """
        results = []
        individual_files = []
        
        for i, university_name in enumerate(university_list, 1):
            logger.info(f"Processing university {i}/{len(university_list)}: {university_name}")
            
            try:
                if save_individual:
                    result = await self.collect_and_save(university_name, fields, use_llm, output_dir, True)
                    individual_files.append(result.get("json_file"))
                else:
                    result = await self.collect_university_data(university_name, fields, use_llm)
                
                results.append(result)
                
                # Add delay between requests to be respectful
                await asyncio.sleep(self.config.scraper.delay_between_requests)
                
            except Exception as e:
                logger.error(f"Error collecting data for {university_name}: {e}")
                error_result = {
                    "university_name": university_name,
                    "status": "failed",
                    "error": str(e)
                }
                results.append(error_result)
        
        # Save batch file if requested
        batch_file = None
        if save_batch:
            batch_file = self.save_batch_to_json(results, output_dir=output_dir)
        
        return {
            "total_universities": len(university_list),
            "successful": len([r for r in results if r.get("status") == "success"]),
            "failed": len([r for r in results if r.get("status") == "failed"]),
            "individual_files": individual_files if save_individual else [],
            "batch_file": batch_file,
            "results": results
        }

async def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="University Data Collection System")
    parser.add_argument("--university", "-u", help="University name to research")
    parser.add_argument("--file", "-f", help="File containing list of universities (one per line)")
    parser.add_argument("--fields", "-F", nargs="+", help="Fields to collect", 
                       choices=["basic_info", "contact", "academic", "statistics", "programs", "facilities", "about", "all"])
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument("--output-dir", help="Directory to save JSON files (default: output)")
    parser.add_argument("--save-individual", action="store_true", help="Save individual university files")
    parser.add_argument("--save-batch", action="store_true", help="Save combined batch file")
    parser.add_argument("--database", "-d", help="Database URL")
    parser.add_argument("--list-fields", action="store_true", help="List available fields and exit")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM enhancement")
    parser.add_argument("--setup", action="store_true", help="Setup configuration and create .env file")
    parser.add_argument("--llm-provider", help="LLM provider (openai, anthropic, ollama, local_openai)")
    
    args = parser.parse_args()
    
    # Setup configuration
    if args.setup:
        print("Setting up University Data Collection System...")
        create_env_template()
        
        if args.llm_provider:
            example_config = get_example_config(args.llm_provider)
            print(f"\nExample configuration for {args.llm_provider}:")
            for key, value in example_config.items():
                print(f"{key}={value}")
        
        print("\nPlease edit the .env file with your actual API keys and settings.")
        return
    
    # Initialize collector
    collector = UniversityDataCollector(args.database)
    
    try:
        # List available fields
        if args.list_fields:
            fields = collector.get_available_fields()
            print("Available fields for collection:")
            for category, field_dict in fields.items():
                print(f"\n{category.upper()}:")
                for field_name, description in field_dict.items():
                    print(f"  - {field_name}: {description}")
            
            # Show LLM configuration
            llm_config = collector.get_llm_config()
            print(f"\nLLM Configuration:")
            print(f"  Provider: {llm_config.provider}")
            print(f"  Model: {llm_config.model}")
            print(f"  API Key: {'Set' if llm_config.api_key else 'Not set'}")
            return
        
        # Set output directory
        output_dir = args.output_dir or "output"
        
        # Collect data
        if args.university:
            # Single university
            if args.save_individual or args.output:
                result = await collector.collect_and_save(
                    args.university, 
                    args.fields, 
                    use_llm=not args.no_llm,
                    output_dir=output_dir
                )
                results = [result]
                print(f"Data saved to: {result.get('json_file', 'Not saved')}")
            else:
                result = await collector.collect_university_data(
                    args.university, 
                    args.fields, 
                    use_llm=not args.no_llm
                )
                results = [result]
            
        elif args.file:
            # Multiple universities from file
            if not Path(args.file).exists():
                print(f"Error: File {args.file} not found")
                return
            
            with open(args.file, 'r') as f:
                university_list = [line.strip() for line in f if line.strip()]
            
            if args.save_individual or args.save_batch:
                result = await collector.batch_collect_and_save(
                    university_list, 
                    args.fields, 
                    use_llm=not args.no_llm,
                    output_dir=output_dir,
                    save_individual=args.save_individual,
                    save_batch=args.save_batch
                )
                results = result['results']
                print(f"Batch collection completed:")
                print(f"  Total: {result['total_universities']}")
                print(f"  Successful: {result['successful']}")
                print(f"  Failed: {result['failed']}")
                if result['individual_files']:
                    print(f"  Individual files: {len(result['individual_files'])}")
                if result['batch_file']:
                    print(f"  Batch file: {result['batch_file']}")
            else:
                results = await collector.batch_collect(
                    university_list, 
                    args.fields, 
                    use_llm=not args.no_llm
                )
            
        else:
            print("Error: Must specify either --university or --file")
            print("Use --setup to create configuration file")
            return
        
        # Output results
        if args.output and not args.save_individual:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {args.output}")
        elif not args.save_individual and not args.save_batch:
            # Print results to console
            for result in results:
                print(f"\n{'='*50}")
                print(f"University: {result.get('university_name', 'Unknown')}")
                print(f"Status: {result.get('status', 'Unknown')}")
                print(f"Confidence: {result.get('confidence_score', 0):.2f}")
                print(f"Source: {result.get('source_url', 'Unknown')}")
                print(f"LLM Enhanced: {result.get('llm_enhanced', False)}")
                
                if result.get('data'):
                    print("\nCollected Data:")
                    for category, data in result['data'].items():
                        print(f"\n{category.upper()}:")
                        if isinstance(data, dict):
                            for key, value in data.items():
                                print(f"  {key}: {value}")
                        elif isinstance(data, list):
                            for item in data[:5]:  # Show first 5 items
                                print(f"  - {item}")
                        else:
                            print(f"  {data}")
                
                if 'error' in result:
                    print(f"Error: {result['error']}")
    
    finally:
        collector.close()

if __name__ == "__main__":
    asyncio.run(main())

# Example usage functions
async def example_single_university():
    """Example: Collect data for a single university and save to JSON"""
    collector = UniversityDataCollector()
    
    try:
        # Collect basic information about MIT with LLM enhancement and save to JSON
        result = await collector.collect_and_save(
            "Massachusetts Institute of Technology",
            fields=["basic_info", "contact", "academic"],
            use_llm=True,
            output_dir="output"
        )
        
        print("MIT Data Collection Result:")
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence_score']}")
        print(f"JSON File: {result.get('json_file', 'Not saved')}")
        
        if result.get('data'):
            print("\nCollected Data Preview:")
            for category, data in list(result['data'].items())[:2]:  # Show first 2 categories
                print(f"\n{category.upper()}:")
                if isinstance(data, dict):
                    for key, value in list(data.items())[:3]:  # Show first 3 items
                        print(f"  {key}: {value}")
        
    finally:
        collector.close()

async def example_batch_collection():
    """Example: Collect data for multiple universities and save to JSON"""
    collector = UniversityDataCollector()
    
    try:
        universities = [
            "Harvard University",
            "Stanford University",
            "MIT",
            "UC Berkeley"
        ]
        
        # Collect data for multiple universities and save to JSON files
        result = await collector.batch_collect_and_save(
            university_list=universities,
            fields=["basic_info", "statistics"],
            use_llm=True,
            output_dir="output",
            save_individual=True,
            save_batch=True
        )
        
        print("Batch Collection Results:")
        print(f"Total Universities: {result['total_universities']}")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
        print(f"Individual Files: {len(result['individual_files'])}")
        print(f"Batch File: {result['batch_file']}")
        
        # Show individual file paths
        if result['individual_files']:
            print("\nIndividual JSON Files:")
            for file_path in result['individual_files']:
                print(f"  - {file_path}")
        
    finally:
        collector.close()

async def example_mcp_style():
    """Example: Direct MCP server usage with JSON output"""
    from .mcp_server import UniversityMCPServer, FieldRequest, FieldType
    
    server = UniversityMCPServer()
    
    try:
        # Create a field request
        request = FieldRequest(
            university_name="Yale University",
            fields=[FieldType.BASIC_INFO, FieldType.CONTACT, FieldType.ABOUT],
            priority=1
        )
        
        # Process request with LLM enhancement
        response = await server.process_field_request_with_llm(request)
        
        # Convert to dictionary format
        result = {
            "university_name": response.university_name,
            "status": response.status,
            "confidence_score": response.confidence_score,
            "source_url": response.source_url,
            "scraped_at": response.scraped_at,
            "data": response.fields,
            "llm_enhanced": True
        }
        
        # Save to JSON file
        output_dir = "output"
        Path(output_dir).mkdir(exist_ok=True)
        
        filename = f"yale_university_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = Path(output_dir) / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Yale University data saved to: {file_path}")
        print(f"Status: {result['status']}")
        print(f"Confidence: {result['confidence_score']}")
        
    finally:
        server.close()

if __name__ == "__main__":
    # Run examples if called directly
    print("University Data Collection System Examples")
    print("=" * 50)
    
    # Uncomment to run examples:
    # asyncio.run(example_single_university())
    # asyncio.run(example_batch_collection())
    # asyncio.run(example_mcp_style()) 