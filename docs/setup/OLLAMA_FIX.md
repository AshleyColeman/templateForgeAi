# 🔧 Ollama Model Configuration Fix

## ❌ Current Issue

**Error**: `404 Not Found` for `http://localhost:11434/api/chat`

**Root Cause**: Two problems:
1. The `.env` file specifies `OLLAMA_MODEL=gemma3:1b` but this model isn't installed
2. The Strands library is calling `/api/chat` endpoint with a model that doesn't exist

## ✅ Solutions

### Option 1: Use Gemma2:2b (Recommended - Better Quality)

I'm currently downloading `gemma2:2b` for you. Once complete:

```powershell
# Update .env file
notepad .env

# Change this line:
OLLAMA_MODEL=gemma2:2b
```

**Pros**:
- Better quality responses
- Supports vision tasks
- Still relatively small (1.6GB)

**Wait for download to complete** (check progress in background terminal)

---

### Option 2: Use Existing gemma3:270m (Fastest - Already Installed)

Use the model you already have:

```powershell
# Update .env file
notepad .env

# Change this line:
OLLAMA_MODEL=gemma3:270m
```

**Pros**:
- Already installed! No download needed
- Very fast
- Works immediately

**Cons**:
- Smaller model = less accurate
- May struggle with complex navigation patterns

---

### Option 3: Use Qwen (Alternative - Already Installed)

```powershell
# Update .env file
notepad .env

# Change this line:
OLLAMA_MODEL=goekdenizguelmez/josiefied-qwen3:1.7b
```

**Pros**:
- Already installed
- Larger model = better quality
- Good at following instructions

---

## 🚀 Quick Fix (Use What You Have)

**Fastest solution** - Use your existing gemma3:270m:

```powershell
# 1. Update .env
notepad .env

# 2. Find and change:
OLLAMA_MODEL=gemma3:1b
# To:
OLLAMA_MODEL=gemma3:270m

# 3. Save and close

# 4. Run extraction again
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless
```

---

## 📊 Model Comparison

| Model | Size | Quality | Speed | Already Installed? |
|-------|------|---------|-------|-------------------|
| **gemma3:270m** | 291 MB | ⭐⭐ | ⚡⚡⚡ | ✅ YES |
| **gemma2:2b** | 1.6 GB | ⭐⭐⭐⭐ | ⚡⚡ | ⏳ Downloading |
| **qwen3:1.7b** | 1.1 GB | ⭐⭐⭐ | ⚡⚡ | ✅ YES |
| **gemma3:1b** | ~700 MB | ⭐⭐⭐ | ⚡⚡⚡ | ❌ NO |

---

## 🎯 My Recommendation

### For RIGHT NOW (No Waiting):
**Use `gemma3:270m`** - Update .env and run immediately

### For BETTER QUALITY (Wait 5-10 min):
**Use `gemma2:2b`** - Wait for download, then update .env

---

## 🛠️ Detailed Steps

### Using gemma3:270m (Immediate):

1. **Open .env file:**
   ```powershell
   notepad .env
   ```

2. **Find line 25:**
   ```bash
   OLLAMA_MODEL=gemma3:1b
   ```

3. **Change to:**
   ```bash
   OLLAMA_MODEL=gemma3:270m
   ```

4. **Save** (Ctrl+S) and **Close**

5. **Run extraction:**
   ```powershell
   python -m src.ai_agents.category_extractor.cli extract `
       --url https://www.wellnesswarehouse.com/ `
       --retailer-id 99 `
       --no-headless
   ```

---

## 🔍 Verify Ollama is Working

```powershell
# Check running models
ollama list

# Test the model
ollama run gemma3:270m "Hello, how are you?"
# Press Ctrl+D to exit

# Check if server is responding
curl http://localhost:11434/api/tags
```

---

## 🐛 Why This Happened

The `.env.example` file specified `gemma3:1b` as the default model, but:
1. You never pulled that specific model
2. The Strands library tries to use the model from config
3. Ollama returns 404 when model doesn't exist

**This is a configuration issue, not a code issue.**

---

## 📝 After Fixing

Once you update `.env` with a valid model, you should see:

```
✅ Page loads successfully
✅ Ollama responds to API calls
✅ Categories get extracted
✅ Data saved to database
```

---

## 💡 Pro Tips

### Tip 1: Always Pull Models First
```powershell
# Before using Ollama, pull your model
ollama pull gemma2:2b
```

### Tip 2: Test Models Before Using
```powershell
# Test if a model works
ollama run gemma3:270m "Test message"
```

### Tip 3: Check What's Installed
```powershell
# See your installed models
ollama list
```

---

## 🎉 Ready to Continue?

1. **Choose your model** (gemma3:270m for immediate, gemma2:2b for quality)
2. **Update `.env` file** with the chosen model
3. **Run the extraction** again
4. **Watch it work!** 🚀

---

**Quick Update .env Command:**
```powershell
notepad .env
# Change line: OLLAMA_MODEL=gemma3:270m
# Save and close
```

**Then run:**
```powershell
python -m src.ai_agents.category_extractor.cli extract `
    --url https://www.wellnesswarehouse.com/ `
    --retailer-id 99 `
    --no-headless
```
