# FPLGaffer Project Flow & Architecture Reference

### **Entry Point & Main Flow**
**File: `FPLGaffer.py`** (Main entry point)

```
1. Load environment variables (.env)
2. Validate team ID from settings
3. Initialize AI clients (free/paid fallback)
4. Fetch FPL data (bootstrap, fixtures, team data)
5. Get user mode selection (Transfer/Wildcard)
6. Set weights based on mode
7. Setup file output (Tee class for dual output)
8. Compute player ratings
9. Sort players by position
10. Execute mode-specific logic
11. Get AI recommendations
12. Restore stdout
```

### **Core Data Flow**

#### **Phase 1: Data Acquisition & Processing**
```
settings.fetch_bootstrap_data() → FPL API
settings.fetch_fixture_data() → FPL API  
settings.team_stats() → Calculate team strengths & fixture difficulties
settings.format_all_players() → Combine player + team data
settings.my_picks() → User's current team
```

#### **Phase 2: Player Rating System**
```
ratings.compute_ml_ratings() → ML scaling with QuantileTransformer
sort.sort_players() → Position-based sorting + rating normalization
sort.sort_current_team() → Extract user's players from sorted list
```

#### **Phase 3: Mode Execution**
```
Transfer Mode: transfer_mode.transfer() → Replacement analysis
Wildcard Mode: wildcard_mode.wildcard() → Optimal squad building
```

#### **Phase 4: AI Integration**
```
ai_prompt.ai_transfer_prompt() / ai_wildcard_prompt() → System prompts
ai_advisor.ai_fpl_helper() → API calls with fallback logic
print_output.print_ai_response() → Display results
```

### **File-by-File Breakdown**

#### **📁 config/ - Configuration & Constants**
- **`constants.py`**: Global constants, API URLs, position mappings, AI weights
  - `BOOTSTRAP_URL`, `FIXTURE_URL` - FPL API endpoints
  - `POS_MAP`, `STATUS_MAP` - Position/status translations
  - `TRANSFER_WEIGHTS`, `WC_WEIGHTS` - ML rating weights by mode
  - Environment variable handling for API keys

- **`settings.py`**: Core data fetching and validation
  - `validate_team_id()` - Environment validation
  - `ai_client()` - OpenAI client setup with free/paid fallback
  - `fetch_bootstrap_data()` - Main FPL data fetch
  - `fetch_fixture_data()` - Fixture information
  - `team_stats()` - Team strength calculations
  - `format_all_players()` - Player data enrichment
  - `get_current_gameweek()` - Current GW detection
  - `my_picks()` - User's team data

#### **📁 models/ - Data Processing & Business Logic**
- **`ratings.py`**: ML-based player rating system
  - `compute_ml_ratings()` - Core rating algorithm using QuantileTransformer
  - Weighted scoring with positive/negative weights
  - Multiplier application (availability, fixtures, team strength)
  - Final 0-100 rating normalization

- **`sort.py`**: Player organization and sorting
  - `sort_players()` - Position categorization + per-position rating normalization
  - `sort_current_team()` - Extract user's players from sorted data
  - Data cleaning and formatting transformations

- **`replacements.py`**: Transfer candidate analysis
  - `find_replacements()` - Budget-aware replacement filtering
  - Position, availability, and team constraint checking

#### **📁 modes/ - Application Logic**
- **`transfer_mode.py`**: Transfer mode execution
  - `transfer()` - Main transfer workflow
  - User input handling for number of replacements
  - Team assessment display
  - Replacement generation and AI prompt preparation

- **`wildcard_mode.py`**: Wildcard mode execution
  - `wildcard()` - Main wildcard workflow
  - Top players display by position
  - AI prompt preparation for squad optimization

#### **📁 ai/ - AI Integration**
- **`ai_advisor.py`**: AI API communication
  - `ai_fpl_helper()` - Main AI interaction with fallback logic
  - Error handling and retry mechanisms
  - Response cleaning and formatting

- **`ai_prompt.py`**: AI prompt templates
  - `ai_transfer_prompt()` - Transfer analysis system prompt
  - `ai_wildcard_prompt()` - Squad building system prompt with constraints

#### **📁 utils/ - Utilities**
- **`print_output.py`**: Display formatting
  - `print_players()` - Tabulated player display
  - `print_replacement_impact()` - Cost impact analysis
  - `print_ai_response()` - AI response formatting

- **`file_handlers.py`**: File I/O operations
  - `Tee` class - Dual output (terminal + file)
  - `get_unique_filename()` - Unique report naming

- **`format_date.py`**: Date formatting
  - `format_date_with_ordinal()` - Ordinal date strings

### **Key Data Structures**

#### **Player Dictionary Structure**
```python
{
    "web_name": str,           # Display name
    "id": int,                 # FPL player ID
    "pos": str,                # Position (GKP/DEF/MID/FWD)
    "rating": float,           # 0-100 performance rating
    "now_cost(m)": float,      # Cost in millions
    "team_name": str,          # Team short name
    "team_strength": int,      # Team strength rating
    "team_fix_dif": float,     # Average fixture difficulty
    "status": str,             # Availability status
    "chance_of_playing_next_round": float,  # Playing probability
    # ... additional FPL stats
}
```

#### **Sorted Players Structure**
```python
{
    "GKP": [player_dict, ...],  # Sorted by rating (high to low)
    "DEF": [player_dict, ...],
    "MID": [player_dict, ...],
    "FWD": [player_dict, ...]
}
```

### **Adding New Features: Key Integration Points**

#### **1. New Data Sources**
- Add to `settings.py` fetch functions
- Update `constants.py` with new URLs/mappings
- Extend player dict structure in `format_all_players()`

#### **2. New Rating Metrics**
- Add weights to `TRANSFER_WEIGHTS`/`WC_WEIGHTS` in `constants.py`
- Update `compute_ml_ratings()` if special handling needed
- Modify `sort_players()` for additional transformations

#### **3. New Modes**
- Create new file in `modes/` directory
- Follow existing pattern: user input → data processing → AI integration
- Add mode selection logic in `FPLGaffer.py`

#### **4. New AI Features**
- Add prompt templates in `ai_prompt.py`
- Extend `ai_advisor.py` for new API interactions
- Update `print_output.py` for new display formats

#### **5. New Output Formats**
- Extend `print_output.py` with new display functions
- Update `file_handlers.py` for new file types
- Modify Tee class usage in main flow

### **Error Handling Patterns**
- API calls: `response.raise_for_status()` with try/except
- AI calls: Free → Paid fallback with specific error detection
- User input: Validation loops with clear error messages
- Data processing: Safe conversion functions with fallbacks

### **Configuration Management**
- Environment variables via `.env` file
- Constants centralized in `constants.py`
- Mode-specific weights for different analysis types
- AI model configuration with fallback options

### **Development Workflow for New Features**

1. **Planning Phase**
   - Identify integration points (data source, rating, mode, AI, output)
   - Review existing patterns in relevant modules
   - Plan data structure extensions

2. **Implementation Phase**
   - Add configuration constants/mappings
   - Implement core logic in appropriate module
   - Add display/output functions
   - Integrate with main flow in `FPLGaffer.py`

3. **Testing Phase**
   - Test with sample data
   - Verify error handling
   - Check AI integration (if applicable)
   - Validate output formatting

This architecture supports modular development where new features can be added by extending existing modules or creating new mode-specific modules while maintaining consistent data flow and error handling patterns.
