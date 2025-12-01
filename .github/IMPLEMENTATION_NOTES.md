# Three-Tier Configuration System Implementation

## Overview
Implemented a flexible three-tier configuration precedence system for API endpoints, allowing users to customize server and LLM endpoints at multiple levels.

## Configuration Precedence
1. 🔵 **Defaults** - Built-in codebase defaults (lowest priority)
2. 🟢 **Environment Variables** - Values from `.env` file (medium priority)  
3. 🟡 **UI Settings** - Custom values set in Settings page (highest priority)

## Key Components

### 1. ConfigManager (`src/config.py`)
Central configuration management class that:
- Defines default values for all configurable settings
- Loads environment variables from `.env` file
- Implements precedence logic via `get()` method
- Provides `get_display_value()` to show configuration source
- Helper methods: `is_using_default()`, `is_using_env()`, `is_using_ui()`

**Configurable Settings:**
- `API_BASE_URL`: Flask API server endpoint
- `LLM_API_BASE_URL`: LLM API endpoint for summarization
- `LLM_MODEL`: LLM model name
- `OPENAI_API_KEY`: API key for authentication
- `HUGGINGFACE_TOKEN`: Token for PyAnnote models

### 2. Session State Management (`src/ui/app_new.py`)
- Uses `ui_*` prefixed keys for UI overrides:
  - `ui_api_base_url`
  - `ui_llm_api_base_url`
  - `ui_llm_model`
  - `ui_llm_api_key`
- Empty string (`""`) means "not overridden by UI" → falls back to env/defaults
- Non-empty string means "UI override active"

### 3. Helper Functions
- `get_effective_config(key)`: Gets final resolved value for any config key
- `get_api_base_url()`: Returns effective API server URL
- `get_llm_config()`: Returns dict with LLM configuration (base_url, model, api_key)

### 4. Enhanced Settings Page
- Visual indicators showing configuration source for each setting
- Smart placeholders showing fallback values
- Apply/Cancel buttons for configuration changes
- "Current Effective Configuration" summary section

## Benefits

1. **Flexibility**: Users can override any configuration without modifying code or .env files
2. **Development/Production**: Easy switching between environments
3. **On-Premises Support**: Can use custom LLM endpoints (vLLM, Ollama, etc.)
4. **Transparency**: UI clearly shows where each value comes from
5. **Fallback Safety**: Empty UI fields automatically use env/default values

## Files Modified

- `src/config.py` - New file with ConfigManager class
- `src/ui/app_new.py` - Updated to use three-tier configuration system
  - `initialize_session_state()` - Added ui_* keys
  - `settings_page()` - Complete rewrite with visual indicators
  - `recording_page()`, `jobs_page()`, `transcript_page()` - Updated to use helper functions
  - All API client initialization uses dynamic configuration
- `README.md` - Documented new configuration system and client-server architecture

## Usage Examples

**Example 1: Use defaults (no configuration needed)**
```python
# Just run the app - uses http://localhost:5001 and OpenAI API
```

**Example 2: Configure via .env**
```bash
# .env
API_BASE_URL=http://production-server:5001
LLM_API_BASE_URL=https://custom-llm.company.com/v1
LLM_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-...
```

**Example 3: Override in UI**
- Open Settings page
- Enter custom values
- Leave empty to use env/defaults
- See real-time which source is being used

## Testing Checklist
- ✅ Defaults work without .env or UI settings
- ✅ .env overrides defaults
- ✅ UI settings override .env  
- ✅ Empty string in UI falls back properly
- ✅ LLM config passes correctly to server
- ✅ API client reinitializes when endpoint changes
- ✅ Settings page shows correct source indicators
