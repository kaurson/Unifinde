#!/usr/bin/env python3
"""
LLM Configuration Example for University Data Collection System
"""

import asyncio
import os
from app.main import UniversityDataCollector
from app.mcp_server import LLMConfig

async def example_openai_config():
    """Example with OpenAI configuration"""
    print("=== OpenAI Configuration Example ===")
    
    # Method 1: Using environment variables (recommended)
    # Set these in your .env file or environment:
    # LLM_PROVIDER=openai
    # LLM_API_KEY=your-openai-api-key
    # LLM_MODEL=gpt-4
    
    collector = UniversityDataCollector()
    
    try:
        result = await collector.collect_university_data(
            "Harvard University",
            fields=["basic_info", "academic"],
            use_llm=True
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
    finally:
        collector.close()

async def example_programmatic_config():
    """Example with programmatic configuration"""
    print("\n=== Programmatic Configuration Example ===")
    
    # Method 2: Programmatic configuration
    llm_config = LLMConfig(
        provider="openai",
        api_key="your-openai-api-key-here",  # Replace with your actual key
        model="gpt-4",
        temperature=0.1,
        max_tokens=1000
    )
    
    collector = UniversityDataCollector(llm_config=llm_config)
    
    try:
        result = await collector.collect_university_data(
            "Stanford University",
            fields=["statistics", "programs"],
            use_llm=True
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
    finally:
        collector.close()

async def example_anthropic_config():
    """Example with Anthropic configuration"""
    print("\n=== Anthropic Configuration Example ===")
    
    llm_config = LLMConfig(
        provider="anthropic",
        api_key="your-anthropic-api-key-here",  # Replace with your actual key
        model="claude-3-sonnet-20240229",
        temperature=0.1,
        max_tokens=1000
    )
    
    collector = UniversityDataCollector(llm_config=llm_config)
    
    try:
        result = await collector.collect_university_data(
            "MIT",
            fields=["basic_info", "contact"],
            use_llm=True
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
    finally:
        collector.close()

async def example_ollama_config():
    """Example with Ollama (local) configuration"""
    print("\n=== Ollama Configuration Example ===")
    
    llm_config = LLMConfig(
        provider="local",
        api_key="not-needed",
        model="llama2",
        base_url="http://localhost:11434/v1",
        temperature=0.1,
        max_tokens=1000
    )
    
    collector = UniversityDataCollector(llm_config=llm_config)
    
    try:
        result = await collector.collect_university_data(
            "Yale University",
            fields=["basic_info"],
            use_llm=True
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
    finally:
        collector.close()

async def example_without_llm():
    """Example without LLM enhancement"""
    print("\n=== Without LLM Enhancement Example ===")
    
    collector = UniversityDataCollector()
    
    try:
        result = await collector.collect_university_data(
            "Princeton University",
            fields=["basic_info", "academic"],
            use_llm=False  # Disable LLM enhancement
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        
    finally:
        collector.close()

async def example_configuration_management():
    """Example of managing configuration"""
    print("\n=== Configuration Management Example ===")
    
    collector = UniversityDataCollector()
    
    try:
        # Get current configuration
        current_config = collector.get_llm_config()
        print(f"Current provider: {current_config.provider}")
        print(f"Current model: {current_config.model}")
        
        # Update configuration
        new_config = LLMConfig(
            provider="openai",
            api_key="new-api-key",
            model="gpt-3.5-turbo",
            temperature=0.2
        )
        
        collector.update_llm_config(new_config)
        print("Configuration updated!")
        
        # Test with new configuration
        result = await collector.collect_university_data(
            "Columbia University",
            fields=["basic_info"],
            use_llm=True
        )
        
        print(f"Status: {result['status']}")
        print(f"LLM Enhanced: {result['llm_enhanced']}")
        
    finally:
        collector.close()

def setup_environment():
    """Setup environment for examples"""
    print("Setting up environment for LLM examples...")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("Creating .env template file...")
        os.system("python -m app.main --setup")
        print("Please edit the .env file with your API keys before running examples.")
        return False
    
    return True

async def main():
    """Main function to run examples"""
    print("LLM Configuration Examples")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("\nPlease set up your .env file first:")
        print("1. Run: python -m app.main --setup")
        print("2. Edit .env file with your API keys")
        print("3. Run this example again")
        return
    
    # Run examples (comment out the ones you don't want to test)
    
    # Example 1: Environment-based configuration
    # await example_openai_config()
    
    # Example 2: Programmatic configuration
    # await example_programmatic_config()
    
    # Example 3: Anthropic configuration
    # await example_anthropic_config()
    
    # Example 4: Ollama configuration
    # await example_ollama_config()
    
    # Example 5: Without LLM
    await example_without_llm()
    
    # Example 6: Configuration management
    # await example_configuration_management()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run specific examples:")
    print("1. Uncomment the example you want to run")
    print("2. Add your API keys to the .env file")
    print("3. Run: python app/llm_example.py")

if __name__ == "__main__":
    asyncio.run(main()) 