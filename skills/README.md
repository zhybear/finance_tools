# Skills Directory

This directory contains GitHub Copilot agents and automation skills for the Stock Portfolio Analyzer project.

## Available Skills

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

## Documentation

Local documentation (excluded from git): `.github/copilot-instructions.md`.
