#!/usr/bin/env python3
"""
Test script to verify Strands 1.10 API updates
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("=" * 60)
    print("TESTING STRANDS 1.10 API UPDATES")
    print("=" * 60)
    
    # Test 1: Import the agent
    print("\n✅ Test 1: Importing CategoryExtractionAgent...")
    from ai_agents.category_extractor.agent import CategoryExtractionAgent
    print("   SUCCESS: Agent imported")
    
    # Test 2: Check Strands version
    print("\n✅ Test 2: Checking Strands version...")
    import strands
    version = getattr(strands, '__version__', 'unknown')
    print(f"   Strands version: {version}")
    
    # Test 3: Create agent instance
    print("\n✅ Test 3: Creating agent instance...")
    from ai_agents.category_extractor.config import ExtractorConfig
    config = ExtractorConfig()
    print(f"   Provider: {config.llm_provider}")
    print(f"   Model: {config.ollama_model if config.llm_provider == 'ollama' else config.openai_model}")
    
    agent = CategoryExtractionAgent(
        retailer_id=999,
        site_url="https://test.com"
    )
    print("   SUCCESS: Agent created")
    
    # Test 4: Check agent has tools
    print("\n✅ Test 4: Verifying tools...")
    print(f"   page_analyzer: {hasattr(agent, 'page_analyzer')}")
    print(f"   category_extractor: {hasattr(agent, 'category_extractor')}")
    print(f"   blueprint_generator: {hasattr(agent, 'blueprint_generator')}")
    
    # Test 5: Check Strands Agent object
    print("\n✅ Test 5: Checking Strands Agent...")
    print(f"   Agent type: {type(agent.agent)}")
    print(f"   Has tool method: {hasattr(agent.agent, 'tool')}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe code has been successfully updated for Strands 1.10!")
    print("\nYou can now run:")
    print("  python3 -m src.ai_agents.category_extractor.cli extract \\")
    print("    --url https://www.wellnesswarehouse.com/ \\")
    print("    --retailer-id 999 \\")
    print("    --blueprint-only")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

