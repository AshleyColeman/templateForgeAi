#!/usr/bin/env python3
"""Quick test script to diagnose Ollama issues."""

import asyncio
import httpx
import time
from rich.console import Console
from rich.panel import Panel

console = Console()

async def test_ollama_basic():
    """Test basic Ollama connectivity."""
    console.print("\n[bold cyan]Test 1: Basic Ollama Connectivity[/bold cyan]")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                console.print(f"✅ Ollama is running")
                console.print(f"✅ Available models: {', '.join(models)}")
                return True
            else:
                console.print(f"❌ Ollama returned status {response.status_code}")
                return False
    except Exception as e:
        console.print(f"❌ Cannot connect to Ollama: {e}")
        return False

async def test_ollama_generate():
    """Test Ollama generate endpoint (simpler than chat)."""
    console.print("\n[bold cyan]Test 2: Ollama Generate API[/bold cyan]")
    
    try:
        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma2:2b",
                    "prompt": "Say hello in one word.",
                    "stream": False
                },
                timeout=30.0
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                console.print(f"✅ Generate API works")
                console.print(f"✅ Response time: {elapsed:.2f}s")
                console.print(f"✅ Response: {data.get('response', 'N/A')[:100]}")
                return True
            else:
                console.print(f"❌ Generate API returned {response.status_code}")
                console.print(f"Response: {response.text}")
                return False
    except httpx.ReadTimeout:
        console.print(f"❌ Generate API timed out after 30s")
        return False
    except Exception as e:
        console.print(f"❌ Generate API error: {e}")
        return False

async def test_ollama_chat():
    """Test Ollama chat endpoint (what the app uses)."""
    console.print("\n[bold cyan]Test 3: Ollama Chat API[/bold cyan]")
    
    try:
        async with httpx.AsyncClient() as client:
            start = time.time()
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "gemma2:2b",
                    "messages": [
                        {"role": "user", "content": "Say hello in one word."}
                    ],
                    "stream": False
                },
                timeout=30.0
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {}).get("content", "N/A")
                console.print(f"✅ Chat API works")
                console.print(f"✅ Response time: {elapsed:.2f}s")
                console.print(f"✅ Response: {message[:100]}")
                return True
            else:
                console.print(f"❌ Chat API returned {response.status_code}")
                console.print(f"Response: {response.text}")
                return False
    except httpx.ReadTimeout:
        console.print(f"❌ Chat API timed out after 30s")
        console.print(f"💡 Model might be too slow or not loaded")
        return False
    except Exception as e:
        console.print(f"❌ Chat API error: {e}")
        return False

async def test_ollama_with_long_prompt():
    """Test with a longer prompt similar to what the app sends."""
    console.print("\n[bold cyan]Test 4: Long Prompt (Similar to Real Usage)[/bold cyan]")
    
    long_prompt = """Analyze this e-commerce webpage to identify product category navigation patterns.
Look for navigation menus, category links, and hierarchical structures.
Return a JSON response with the following structure:

{
  "navigation_type": "sidebar",
  "selectors": {
    "nav_container": ".navigation",
    "category_links": "a.category"
  },
  "confidence": 0.8
}

URL: https://example.com
HTML snippet: <nav><a href="/cat1">Category 1</a></nav>
"""
    
    try:
        async with httpx.AsyncClient() as client:
            start = time.time()
            console.print("⏳ Sending long prompt (this may take 30-60 seconds)...")
            
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "gemma2:2b",
                    "messages": [
                        {"role": "user", "content": long_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 512
                    }
                },
                timeout=90.0  # Longer timeout for complex prompt
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {}).get("content", "N/A")
                console.print(f"✅ Long prompt works")
                console.print(f"✅ Response time: {elapsed:.2f}s")
                console.print(f"✅ Response length: {len(message)} chars")
                console.print(f"\n[dim]Response preview:[/dim]")
                console.print(Panel(message[:500], title="LLM Response"))
                return True
            else:
                console.print(f"❌ Long prompt returned {response.status_code}")
                return False
    except httpx.ReadTimeout:
        console.print(f"❌ Long prompt timed out after 90s")
        console.print(f"💡 Model is too slow for this task")
        console.print(f"💡 Consider using OpenAI or Anthropic instead")
        return False
    except Exception as e:
        console.print(f"❌ Long prompt error: {e}")
        return False

async def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold]Ollama Diagnostic Tests[/bold]\n"
        "Testing Ollama connectivity and performance",
        border_style="cyan"
    ))
    
    results = []
    
    # Test 1: Basic connectivity
    results.append(await test_ollama_basic())
    
    if not results[0]:
        console.print("\n[bold red]❌ Ollama is not running or not accessible[/bold red]")
        console.print("\n[yellow]Fix:[/yellow]")
        console.print("  1. Start Ollama: [cyan]ollama serve[/cyan]")
        console.print("  2. Verify: [cyan]ollama list[/cyan]")
        return
    
    # Test 2: Generate API
    results.append(await test_ollama_generate())
    
    # Test 3: Chat API
    results.append(await test_ollama_chat())
    
    # Test 4: Long prompt
    if results[2]:  # Only if chat API works
        results.append(await test_ollama_with_long_prompt())
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold]Test Summary:[/bold]")
    console.print(f"  Basic Connectivity: {'✅' if results[0] else '❌'}")
    console.print(f"  Generate API: {'✅' if results[1] else '❌'}")
    console.print(f"  Chat API: {'✅' if results[2] else '❌'}")
    if len(results) > 3:
        console.print(f"  Long Prompt: {'✅' if results[3] else '❌'}")
    
    # Recommendations
    console.print("\n[bold cyan]Recommendations:[/bold cyan]")
    
    if all(results[:3]):
        if len(results) > 3 and not results[3]:
            console.print("⚠️  [yellow]Ollama works but is too slow for complex prompts[/yellow]")
            console.print("\n[bold]Options:[/bold]")
            console.print("  1. Use OpenAI (faster, $0.10-0.30 per site)")
            console.print("     Edit .env: [cyan]LLM_PROVIDER=openai[/cyan]")
            console.print("     Add: [cyan]OPENAI_API_KEY=sk-...[/cyan]")
            console.print("\n  2. Use Anthropic (best quality, $1-2 per site)")
            console.print("     Edit .env: [cyan]LLM_PROVIDER=anthropic[/cyan]")
            console.print("     Add: [cyan]ANTHROPIC_API_KEY=sk-ant-...[/cyan]")
            console.print("\n  3. Try a smaller Ollama model")
            console.print("     [cyan]ollama pull qwen2.5:1.5b[/cyan]")
        else:
            console.print("✅ [green]Ollama is working correctly![/green]")
            console.print("   The extraction should work now.")
    elif results[0] and not results[2]:
        console.print("⚠️  [yellow]Ollama is running but Chat API has issues[/yellow]")
        console.print("\n[bold]Possible causes:[/bold]")
        console.print("  1. Model not loaded - try: [cyan]ollama run gemma2:2b[/cyan]")
        console.print("  2. Model too large for your system")
        console.print("  3. Ollama version incompatibility")
    else:
        console.print("❌ [red]Multiple issues detected[/red]")
        console.print("   Check Ollama installation and try restarting it")

if __name__ == "__main__":
    asyncio.run(main())
