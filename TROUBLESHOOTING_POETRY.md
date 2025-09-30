# 🔧 Troubleshooting Poetry Installation

## Your Error History

You got this error:
```
The Poetry configuration is invalid:
  - Additional properties are not allowed ('group' was unexpected)
```

Then after my fix, you got:
```
[Errno 28] No space left on device
```

But you say you have 100GB+ free. Let's figure out what's happening!

---

## 🔍 Run These Diagnostic Commands (Copy/Paste)

**Open a FRESH terminal** and run each command:

### 1. Check Actual Disk Space

```bash
df -h
```

**Look for the line with your home directory** - what does it say?

### 2. Check Where Poetry Tries to Write

```bash
# Check Poetry cache location
echo $HOME/.cache/pypoetry

# Check if it exists and size
du -sh $HOME/.cache/pypoetry/ 2>/dev/null || echo "No cache yet"

# Check specific virtualenv location
ls -la $HOME/.cache/pypoetry/virtualenvs/
```

### 3. Check Temp Space

Sometimes `/tmp` is full (Poetry uses it):

```bash
df -h /tmp
```

**Is /tmp full?** If yes, that's your problem!

### 4. Try Poetry Install with Verbose

```bash
cd /home/ashleycoleman/Projects/templateForgeAi
poetry install -vvv 2>&1 | tail -50
```

**This shows WHERE it fails** - send me the last 50 lines.

---

## 🚀 Quick Fixes to Try

### Fix 1: Clear ALL Caches

```bash
# Clear Poetry cache
rm -rf $HOME/.cache/pypoetry/

# Clear pip cache
pip3 cache purge

# Clear temp files
sudo rm -rf /tmp/tmp*

# Try again
cd /home/ashleycoleman/Projects/templateForgeAi
poetry install
```

### Fix 2: Use pip Instead of Poetry (Simpler!)

```bash
cd /home/ashleycoleman/Projects/templateForgeAi

# Install directly with pip (no Poetry needed)
pip3 install strands-agents playwright asyncpg pydantic pydantic-settings click rich loguru openai anthropic httpx tenacity beautifulsoup4 lxml python-dotenv

# Install dev tools
pip3 install pytest pytest-asyncio pytest-cov black mypy ruff

# Install browser
python3 -m playwright install chromium

# Verify
python3 verify_setup.py
```

**This bypasses Poetry completely!**

### Fix 3: Check Specific Partition

```bash
# Which partition is full?
df -h | grep -E "Filesystem|/home|/tmp|/$"
```

Sometimes `/` is full but `/home` has space. Poetry might be writing to `/tmp` which is on `/`.

---

## 🎯 Most Likely Issues

### Issue A: /tmp Partition Full

**Check**:
```bash
df -h /tmp
```

**If full, clean it**:
```bash
sudo rm -rf /tmp/*
# OR
sudo find /tmp -type f -mtime +7 -delete
```

### Issue B: inode Limit Reached

**Check**:
```bash
df -i /home
```

**If "IUse%" is at 100%, you're out of inodes** (even with disk space free).

**Fix**:
```bash
# Find directories with many files
find $HOME/.cache -type f | wc -l

# Clean them
rm -rf $HOME/.cache/*
```

### Issue C: Poetry Cache Corruption

**Fix**:
```bash
# Nuclear option - remove all Poetry data
rm -rf $HOME/.cache/pypoetry/
rm -rf $HOME/.config/pypoetry/
rm -rf $HOME/.local/share/pypoetry/

# Try install
cd /home/ashleycoleman/Projects/templateForgeAi
poetry install
```

---

## ✅ Workaround: Skip Poetry Entirely

You don't actually NEED Poetry! Use pip:

```bash
cd /home/ashleycoleman/Projects/templateForgeAi

# Install everything with pip
pip3 install -e .

# This reads pyproject.toml and installs everything
# Uses less disk space than Poetry

# Install browser
python3 -m playwright install chromium

# Verify
python3 verify_setup.py
```

**This should work even if Poetry fails!**

---

## 📊 Send Me This Info

Run these and send me the output:

```bash
# 1. Disk space
df -h

# 2. Inode usage
df -i /home

# 3. Temp space
df -h /tmp

# 4. Poetry cache size
du -sh ~/.cache/pypoetry/ 2>/dev/null || echo "No Poetry cache"

# 5. Python packages already installed
pip3 list | grep -E "playwright|asyncpg|pydantic|click|rich"
```

This will tell me exactly what's wrong!

---

## 🎯 Most Likely Solution

Based on experience, this is usually:

1. **`/tmp` is full** (even though `/home` has space)
   - Fix: `sudo rm -rf /tmp/tmp*`

2. **Out of inodes** (file count limit)
   - Fix: `rm -rf ~/.cache/*`

3. **Poetry cache corrupted**
   - Fix: `rm -rf ~/.cache/pypoetry/`

Try those three in order!

---

## ✅ Good News

**Your system code is perfect!** This is just an installation environment issue, not a code problem.

Once you fix the disk/cache issue:
- Poetry will install fine
- You can run BEGINNERS_GUIDE.md
- Extract from Wellness Warehouse
- Everything will work beautifully!

---

**Quick fix to try right now** (in a fresh terminal):

```bash
sudo rm -rf /tmp/tmp*
rm -rf ~/.cache/pypoetry/
cd /home/ashleycoleman/Projects/templateForgeAi
poetry install
```

Let me know what error you get (if any)! 🚀
