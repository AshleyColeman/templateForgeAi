# Task 2: Configuration Management

**Status**: 🔒 Blocked (depends on Task 1)  
**Estimated Time**: 3-4 hours  
**Dependencies**: Task 1 (Environment Setup)  
**Priority**: Critical

---

## 📋 Objective

Create a robust configuration system using Pydantic that loads settings from environment variables and provides type-safe access to configuration values throughout the application.

## 🎯 Success Criteria

- [ ] Configuration class created with Pydantic
- [ ] All settings loaded from environment variables
- [ ] Type validation working
- [ ] Singleton pattern implemented
- [ ] Default values provided for optional settings
- [ ] Configuration can be imported and used
- [ ] `.env` file properly structured

## 📝 Specifications

### File: `src/ai_agents/category_extractor/config.py`

```python
"""Configuration management using Pydantic."""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractorConfig(BaseSettings):
    """Configuration for AI category extractor.
    
    All settings can be overridden via environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="products", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="", description="Database password")
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    
    # Model Configuration
    model_id: str = Field(
        default="gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)",
        description="Ollama/OpenAI/Anthropic model ID"
    )
    model_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model temperature (0.0-1.0)"
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        le=200000,
        description="Maximum tokens per request"
    )
    
    # Browser Configuration
    browser_headless: bool = Field(
        default=True,
        description="Run browser in headless mode"
    )
    browser_timeout: int = Field(
        default=60000,
        gt=0,
        description="Browser timeout in milliseconds"
    )
    browser_width: int = Field(default=1920, gt=0, description="Browser viewport width")
    browser_height: int = Field(default=1080, gt=0, description="Browser viewport height")
    
    # Extraction Configuration
    max_depth: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Maximum category hierarchy depth"
    )
    max_categories: int = Field(
        default=10000,
        gt=0,
        description="Maximum categories to extract"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    retry_delay: int = Field(
        default=2000,
        gt=0,
        description="Retry delay in milliseconds"
    )
    
    # Blueprint Configuration
    blueprint_dir: str = Field(
        default="./src/ai_agents/category_extractor/blueprints",
        description="Directory for storing blueprints"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Optional[str] = Field(
        default="logs/category_extractor.log",
        description="Log file path (None for console only)"
    )
    log_rotation: str = Field(
        default="10 MB",
        description="Log file rotation size"
    )
    log_retention: str = Field(
        default="30 days",
        description="Log file retention period"
    )
    
    def validate_config(self) -> None:
        """Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Check database password is set
        if not self.db_password:
            raise ValueError("DB_PASSWORD must be set in environment")
        
        # Check AWS credentials if using Bedrock
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS credentials must be set in environment")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
    
    def display_config(self) -> dict:
        """Get displayable configuration (hiding sensitive values).
        
        Returns:
            Dict with configuration (passwords masked)
        """
        config_dict = self.model_dump()
        
        # Mask sensitive fields
        sensitive_fields = ["db_password", "aws_access_key_id", "aws_secret_access_key"]
        for field in sensitive_fields:
            if field in config_dict and config_dict[field]:
                config_dict[field] = "***MASKED***"
        
        return config_dict


# Singleton instance
_config: Optional[ExtractorConfig] = None


def get_config() -> ExtractorConfig:
    """Get configuration instance (singleton pattern).
    
    Returns:
        ExtractorConfig: Configuration instance
    """
    global _config
    if _config is None:
        _config = ExtractorConfig()
    return _config


def reload_config() -> ExtractorConfig:
    """Reload configuration from environment.
    
    Useful for testing or when environment changes.
    
    Returns:
        ExtractorConfig: New configuration instance
    """
    global _config
    _config = ExtractorConfig()
    return _config


# Export
__all__ = ["ExtractorConfig", "get_config", "reload_config"]
```

## 🔧 Implementation Steps

### Step 1: Create config.py File

Create the file at:
```
/home/ashleycoleman/Projects/product_scraper/src/ai_agents/category_extractor/config.py
```

Copy the code from the specifications above.

### Step 2: Update .env File

Ensure your `.env` file has all required variables:

```bash
# Required
DB_PASSWORD=your_actual_password
OPENAI_API_KEY (if using OpenAI)=your_actual_key
ANTHROPIC_API_KEY (if using Anthropic)=your_actual_secret

# Optional (defaults will be used if not set)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=products
DB_USER=postgres
LLM_PROVIDER=ollama
MODEL_ID=gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)
BROWSER_HEADLESS=true
LOG_LEVEL=INFO
```

### Step 3: Create Test Script

Create `/home/ashleycoleman/Projects/product_scraper/test_config.py`:

```python
"""Test configuration loading."""
import sys
from src.ai_agents.category_extractor.config import get_config, reload_config


def test_config_loading():
    """Test that configuration loads correctly."""
    print("🔍 Testing Configuration Loading\n")
    
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Display configuration (sensitive values masked)
    print("\n📋 Configuration Values:")
    display = config.display_config()
    for key, value in display.items():
        print(f"  {key}: {value}")
    
    return True


def test_singleton_pattern():
    """Test that get_config returns same instance."""
    print("\n🔍 Testing Singleton Pattern\n")
    
    config1 = get_config()
    config2 = get_config()
    
    if config1 is config2:
        print("✅ Singleton pattern working (same instance)")
        return True
    else:
        print("❌ Singleton pattern broken (different instances)")
        return False


def test_database_url():
    """Test database URL construction."""
    print("\n🔍 Testing Database URL\n")
    
    config = get_config()
    url = config.database_url
    
    print(f"Database URL: {url}")
    
    # Check format
    if url.startswith("postgresql://") and "@" in url:
        print("✅ Database URL format correct")
        return True
    else:
        print("❌ Database URL format incorrect")
        return False


def test_validation():
    """Test configuration validation."""
    print("\n🔍 Testing Configuration Validation\n")
    
    try:
        config = get_config()
        config.validate_config()
        print("✅ Configuration validation passed")
        return True
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return False


def test_type_safety():
    """Test that types are correct."""
    print("\n🔍 Testing Type Safety\n")
    
    config = get_config()
    
    checks = [
        (isinstance(config.db_port, int), "db_port is integer"),
        (isinstance(config.browser_headless, bool), "browser_headless is boolean"),
        (isinstance(config.model_temperature, float), "model_temperature is float"),
        (isinstance(config.max_depth, int), "max_depth is integer"),
    ]
    
    all_passed = True
    for check, description in checks:
        if check:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Configuration Management Test Suite")
    print("="*60 + "\n")
    
    tests = [
        test_config_loading,
        test_singleton_pattern,
        test_database_url,
        test_validation,
        test_type_safety,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*60)
    if all(results):
        print("✅ All configuration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some configuration tests failed")
        sys.exit(1)
```

Run the test:
```bash
poetry run python test_config.py
```

### Step 4: Test in Interactive Python

```bash
poetry shell
python
```

```python
>>> from src.ai_agents.category_extractor.config import get_config
>>> config = get_config()
>>> print(config.db_host)
localhost
>>> print(config.model_id)
gemma3:1b (Ollama) or gpt-4o-mini (OpenAI)
>>> print(config.database_url)
postgresql://postgres:***@localhost:5432/products
>>> config.display_config()
{...}  # Should show all config with passwords masked
```

## ✅ Validation Checklist

- [ ] `config.py` file created
- [ ] All imports work without errors
- [ ] Can instantiate `ExtractorConfig` class
- [ ] Environment variables loaded correctly
- [ ] Default values work when env vars not set
- [ ] `database_url` property constructs correct URL
- [ ] `validate_config()` catches missing required values
- [ ] `display_config()` masks sensitive values
- [ ] `get_config()` returns same instance (singleton)
- [ ] `reload_config()` creates new instance
- [ ] Test script passes all tests
- [ ] Type hints are correct (mypy passes)

## 🧪 Manual Testing

```python
# Test 1: Load config
from src.ai_agents.category_extractor.config import get_config
config = get_config()
assert config.db_host == "localhost"

# Test 2: Validate database URL
url = config.database_url
assert url.startswith("postgresql://")

# Test 3: Test singleton
config2 = get_config()
assert config is config2

# Test 4: Test display (sensitive values masked)
display = config.display_config()
assert display["db_password"] == "***MASKED***"

# Test 5: Test validation
config.validate_config()  # Should not raise if .env is correct
```

## 📝 Deliverables

1. ✅ `config.py` file with complete implementation
2. ✅ Pydantic models with type validation
3. ✅ Singleton pattern working
4. ✅ `.env` file properly configured
5. ✅ Test script passing
6. ✅ Documentation in docstrings

## 🚨 Common Issues & Solutions

### Issue: pydantic_settings not found
**Solution**:
```bash
poetry add pydantic-settings@^2.1.0
```

### Issue: .env file not being loaded
**Solution**: Check file location and format:
```bash
ls -la .env  # Must be in project root
cat .env  # Check format (KEY=value, no spaces around =)
```

### Issue: Validation errors
**Solution**: Check required environment variables are set:
```bash
grep -E "DB_PASSWORD|OPENAI_API_KEY (if using OpenAI)|ANTHROPIC_API_KEY (if using Anthropic)" .env
```

### Issue: Type errors
**Solution**: Ensure correct types in .env:
```bash
# Good
DB_PORT=5432
BROWSER_HEADLESS=true

# Bad
DB_PORT="5432"  # No quotes for integers
BROWSER_HEADLESS=True  # Use lowercase true/false
```

## 📚 Next Steps

Once complete:
1. Mark task as ✅ Complete in MASTER_TASKLIST.md
2. Commit to git: `git add . && git commit -m "Add configuration management"`
3. Proceed to **Task 3: Database Integration**

## 🎯 Time Tracking

**Estimated**: 3-4 hours  
**Actual**: ___ hours  
**Notes**: ___

---

**Status**: Complete before Task 3!
**Last Updated**: 2025-09-30
