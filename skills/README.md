# Skills Directory

This directory contains GitHub Copilot agents and automation skills for the Stock Portfolio Analyzer project.

## Available Skills

### 🤖 Release Agent

Automates the complete release workflow ensuring no inconsistencies.

**Agent Name**: `@release-version`

**Script**: `release_agent.py`

**What it does**:
1. ✓ Validates version format (semver)
2. 🧪 Counts actual tests and verifies consistency
3. 📝 Updates version strings everywhere:
   - `__init__.py` and `pyproject.toml`
   - All README files (root, portfolio_analyzer, tests, skills)
   - Test module version comments
   - Badge shields.io URLs
4. 📊 Updates test count references in all docs
5. 📈 Regenerates all example reports:
   - `examples/example_report.txt`
   - `examples/example_report.pdf`
   - `examples/example_report.html` (with sortable table)
6. 📋 Creates release notes section template
7. 📌 Git operations: commit, tag, push
8. 🔗 Outputs GitHub release template

**Usage**:

```bash
# Dry-run (validate without changes)
python3 skills/release_agent.py --version v1.3.7 --dry-run

# Actual release (commit, tag, push)
python3 skills/release_agent.py --version v1.3.7

# Release without pushing to GitHub
python3 skills/release_agent.py --version v1.3.7 --no-push
```

**Or use via GitHub Copilot**:
```
@release-version prepare v1.3.7
```

**What gets updated automatically**:

| File | Change |
|------|--------|
| `portfolio_analyzer/__init__.py` | `__version__ = "X.Y.Z"` |
| `portfolio_analyzer/pyproject.toml` | `version = "X.Y.Z"` |
| `README.md` (root) | Badge `tests-XXX/XXX` + test count text |
| `portfolio_analyzer/README.md` | Badge + test count text + version |
| `portfolio_analyzer/tests/README.md` | Test count references |
| `portfolio_analyzer/RELEASE_NOTES.md` | Release template (guide only) |
| `portfolio_analyzer/examples/*.txt` | Regenerated |
| `portfolio_analyzer/examples/*.pdf` | Regenerated |
| `portfolio_analyzer/examples/*.html` | Regenerated with sortable table |
| All test module docstrings | `Version: X.Y.Z` |

**Safety features**:
- ✅ Validates semver format
- ✅ Counts actual test suite size
- ✅ Checks for uncommitted changes before git operations
- ✅ Dry-run mode to validate before committing
- ✅ Shows all changes before executing
- ✅ Detailed error reporting

**Example workflow**:

```bash
# Step 1: Dry-run to validate
python3 skills/release_agent.py --version v1.3.7 --dry-run

# Step 2: Review output and check git status
git status

# Step 3: Actually release
python3 skills/release_agent.py --version v1.3.7

# Step 4: Publish on GitHub using the provided template
```

### 🤖 Fidelity Portfolio Agent (Local Only)

Automates the complete workflow from Fidelity raw data to interactive HTML report.

**Agent Name**: `@fidelity-portfolio`

**Script**: `fidelity_portfolio_agent.py` (excluded from git; local-only)

**What it does**:
1. ✓ Checks for Fidelity raw data file
2. 📊 Parses Fidelity data → CSV
3. 📈 Generates HTML report with Portfolio Analyzer
4. 🌐 Opens report in browser

**Usage**:

```bash
# Run with default file (zhuo_personal_trade/fidelity_raw_data)
python3 skills/fidelity_portfolio_agent.py

# Run with custom input file
python3 skills/fidelity_portfolio_agent.py --input zhuo_personal_trade/A_B

# Check file status
python3 skills/fidelity_portfolio_agent.py --status

# Run without opening browser
python3 skills/fidelity_portfolio_agent.py --no-browser
```

**Or use via GitHub Copilot**:
```
# Default file
@fidelity-portfolio run

# Custom file
@fidelity-portfolio zhuo_personal_trade/A_B
```

**Programmatic Usage**:
```python
from skills.fidelity_portfolio_agent import FidelityPortfolioAgent

# Default file
agent = FidelityPortfolioAgent()
success = agent.run(open_browser=True)

# Custom file
agent = FidelityPortfolioAgent(input_file="zhuo_personal_trade/A_B")
success = agent.run(open_browser=True)
```

### Workflow Files

| File | Purpose | Location |
|------|---------|----------|
| **Input** | Fidelity raw data | `zhuo_personal_trade/fidelity_raw_data` |
| **Middle** | Parsed trades CSV | `zhuo_personal_trade/trades.csv` |
| **Output** | HTML dashboard | `zhuo_personal_trade/portfolio_report.html` |

### Adding New Skills

To add a new agent/skill:

1. Create a new Python file in this directory: `your_skill_name.py`
2. Implement a class with a clear interface (see `FidelityPortfolioAgent` as template)
3. Add CLI entry point with `argparse` if desired
4. Document the agent in `.github/copilot-instructions.md`
5. Add usage info to this README

**Template**:
```python
#!/usr/bin/env python3
"""Your skill description"""

class YourSkillAgent:
    def __init__(self):
        # Initialize paths and config
        pass
    
    def run(self) -> bool:
        """Execute the workflow."""
        # Implement logic
        return True

def main():
    """CLI entry point."""
    agent = YourSkillAgent()
    agent.run()

if __name__ == '__main__':
    main()
```

## Requirements

- Python 3.8+ (tested with 3.9.6 and 3.14.3)
- Portfolio Analyzer package installed
- All project dependencies installed
- Git configured (for release agent only)

## Documentation

Local documentation (excluded from git):
- `.github/copilot-instructions.md` - Complete agent documentation
- See agent docstrings for implementation details
