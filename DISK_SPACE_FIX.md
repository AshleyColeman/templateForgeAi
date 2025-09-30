# 🔧 Fix: No Space Left on Device

## ⚠️ Problem

Your disk is full, preventing Poetry from installing packages.

**Error**: `[Errno 28] No space left on device`

---

## ✅ Quick Fix (Choose One)

### Option 1: Clean Poetry Cache (Fastest - Recommended)

```bash
# Clear Poetry's cache (safe - will re-download if needed)
rm -rf ~/.cache/pypoetry/

# Check space freed
du -sh ~/.cache/

# Now try again
cd /home/ashleycoleman/Projects/templateForgeAi
poetry install
```

**This usually frees 500MB-2GB**

---

### Option 2: Clean System Package Cache

```bash
# Clean apt cache (if on Ubuntu/Debian)
sudo apt clean
sudo apt autoclean
sudo apt autoremove

# Clean pip cache
pip cache purge

# Clean Python cache files
find ~/Projects -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Check space freed
df -h /home
```

**This can free 1-5GB**

---

### Option 3: Find Large Files

```bash
# Find largest directories in home
du -sh ~/.* ~/Projects/* 2>/dev/null | sort -h | tail -20

# Common culprits:
# - ~/.cache/ (safe to delete)
# - ~/Downloads/ (move old files)
# - ~/.local/share/Trash/ (empty trash)
# - Docker images (if you use Docker)
```

---

## 🔍 Check Disk Space

```bash
# Check overall disk usage
df -h

# Check home directory usage
du -sh ~

# Check current directory
du -sh .
```

**You need at least 2-3GB free** for Poetry to install all packages.

---

## 🚀 After Freeing Space

### Step 1: Verify Space Available

```bash
df -h /home
# Should show at least 2GB available
```

### Step 2: Clean and Retry

```bash
cd /home/ashleycoleman/Projects/templateForgeAi

# Clear any partial Poetry installation
rm -rf ~/.cache/pypoetry/virtualenvs/ai-category-extractor-*

# Try install again
poetry install
```

### Step 3: If Still Fails

Use system Python instead of Poetry:

```bash
# Install directly with pip
pip3 install -e .
python3 -m playwright install chromium

# Verify
python3 verify_setup.py
```

---

## 💡 Quick Space Cleaning Commands

```bash
# Clean Poetry cache (safest)
rm -rf ~/.cache/pypoetry/

# Clean pip cache
pip cache purge

# Clean apt cache (Ubuntu/Debian)
sudo apt clean

# Empty trash
rm -rf ~/.local/share/Trash/*

# Remove old logs (if any)
find ~/Projects -name "*.log" -mtime +30 -delete

# Clean Python cache
find ~/Projects -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

---

## 📊 Expected Space Usage

### This Project Needs:

- **Source code**: ~5MB
- **Poetry virtualenv**: ~500MB
- **Playwright browsers**: ~300MB
- **Python packages**: ~200MB
- **Total**: ~1GB

### Check What's Taking Space:

```bash
# In your project
cd /home/ashleycoleman/Projects/templateForgeAi
du -sh *

# Common findings:
# .venv/          500MB (Poetry virtualenv)
# logs/           varies (can grow)
# __pycache__/    small (~1MB)
```

---

## ✅ After Fix

Once you have space:

```bash
# Go back to project
cd /home/ashleycoleman/Projects/templateForgeAi

# Install with Poetry
poetry install

# OR install with pip (simpler)
pip3 install -e .

# Install browser
python3 -m playwright install chromium

# Verify everything
python3 verify_setup.py

# Should show:
# ✅ All checks passed! Environment is ready.
```

---

## 🎯 Then Continue with Beginner's Guide

Once installed, continue with:

```bash
cat BEGINNERS_GUIDE.md
# Follow from Step 3 onwards (configuration)
```

---

**Quick Fix**: `rm -rf ~/.cache/pypoetry/ && poetry install`

---

