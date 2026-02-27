#!/usr/bin/env python3
"""
Release Agent for Portfolio Analyzer

Automates the complete release workflow:
1. Validates version format
2. Updates version everywhere (init, pyproject, readmes, release notes)
3. Verifies test count consistency
4. Regenerates example reports (txt, pdf, html)
5. Creates release notes section
6. Git operations (commit, tag, push)
7. Outputs GitHub release template

Usage:
    python3 skills/release_agent.py --version v1.3.7 [--dry-run] [--no-push]
"""

import os
import sys
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class ReleaseAgent:
    """Manages the complete release workflow for Portfolio Analyzer."""
    
    def __init__(self, version: str, dry_run: bool = False, no_push: bool = False):
        """Initialize release agent.
        
        Args:
            version: Target version (e.g., "v1.3.7" or "1.3.7")
            dry_run: Validate without making changes
            no_push: Don't push to GitHub
        """
        self.version = self._normalize_version(version)
        self.dry_run = dry_run
        self.no_push = no_push
        self.root_dir = Path(__file__).parent.parent
        self.portfolio_dir = self.root_dir / "portfolio_analyzer"
        
        self.changes = []  # Track all changes made
        self.errors = []   # Track validation errors
        
    def _normalize_version(self, version: str) -> str:
        """Normalize version to vX.Y.Z format."""
        if version.startswith("v"):
            return version
        return f"v{version}"
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
        """Run shell command and return exit code and output."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes for full test suite
            )
            # Return combined stdout + stderr
            output = result.stdout + result.stderr
            return result.returncode, output.strip()
        except Exception as e:
            return 1, str(e)
    
    def _read_file(self, path: Path) -> str:
        """Read file contents."""
        try:
            return path.read_text()
        except Exception as e:
            self.errors.append(f"Failed to read {path}: {e}")
            return ""
    
    def _write_file(self, path: Path, content: str) -> bool:
        """Write file contents."""
        if self.dry_run:
            self.changes.append(f"  [DRY-RUN] Would write {path.relative_to(self.root_dir)}")
            return True
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self.changes.append(f"  ✓ Updated {path.relative_to(self.root_dir)}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to write {path}: {e}")
            return False
    
    def validate_version_format(self) -> bool:
        """Validate version format (vX.Y.Z or vX.Y.Z-suffix)."""
        print("\n📋 Validating version format...")
        
        pattern = r"^v\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
        if not re.match(pattern, self.version):
            self.errors.append(f"Invalid version format: {self.version}. Use vX.Y.Z")
            return False
        
        print(f"  ✓ Version format valid: {self.version}")
        return True
    
    def get_test_count(self) -> Optional[int]:
        """Get actual test count from test suite."""
        print("\n📊 Counting tests in test suite...")
        
        code, output = self._run_command(
            ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=self.portfolio_dir
        )
        
        # Parse output like "Ran 216 tests in 88.763s" (get the LAST occurrence)
        matches = re.findall(r"Ran (\d+) tests", output)
        if matches:
            # Get the last match (final count)
            count = int(matches[-1])
            if count > 0:
                print(f"  ✓ Found {count} tests")
                return count
        
        self.errors.append("Could not determine test count from test suite")
        return None
    
    def find_files_to_update(self) -> Dict[str, List[Path]]:
        """Find all files that need version/test count updates."""
        print("\n🔍 Finding files to update...")
        
        files = {
            'version': [],
            'readme': [],
            'release_notes': [],
            'test_comments': []
        }
        
        # Version files
        files['version'].extend([
            self.portfolio_dir / "portfolio_analyzer" / "__init__.py",
            self.portfolio_dir / "pyproject.toml",
        ])
        
        # README files
        files['readme'].extend([
            self.root_dir / "README.md",
            self.portfolio_dir / "README.md",
            self.portfolio_dir / "tests" / "README.md",
            self.root_dir / "skills" / "README.md",
        ])
        
        # Release notes
        files['release_notes'].append(self.portfolio_dir / "RELEASE_NOTES.md")
        
        # Test module files with version comments
        files['test_comments'].extend([
            self.portfolio_dir / "tests" / "conftest.py",
            self.portfolio_dir / "tests" / "test_html_sorting.py",
        ])
        
        # Verify files exist
        all_files = []
        for category, paths in files.items():
            for path in paths:
                if path.exists():
                    all_files.append(path)
                    print(f"  ✓ Found {path.relative_to(self.root_dir)}")
                else:
                    self.errors.append(f"File not found: {path}")
        
        return files
    
    def update_version_strings(self, files: Dict[str, List[Path]]) -> bool:
        """Update version in __init__.py and pyproject.toml."""
        print("\n📝 Updating version strings...")
        
        version_no_v = self.version.lstrip("v")
        
        for path in files['version']:
            content = self._read_file(path)
            if not content:
                continue
            
            if "__init__.py" in str(path):
                # Update __version__ = "X.Y.Z"
                updated = re.sub(
                    r'__version__ = "[^"]+"',
                    f'__version__ = "{version_no_v}"',
                    content
                )
            elif "pyproject.toml" in str(path):
                # Update version = "X.Y.Z"
                updated = re.sub(
                    r'version = "[^"]+"',
                    f'version = "{version_no_v}"',
                    content
                )
            else:
                continue
            
            if updated != content:
                self._write_file(path, updated)
        
        return len(self.errors) == 0
    
    def update_test_count_references(self, test_count: int, files: Dict[str, List[Path]]) -> bool:
        """Update test count in README and release notes."""
        print(f"\n🔢 Updating test count references to {test_count}...")
        
        test_pattern_old = r"(\d{3,4})\s+tests?(?:\s|,|%)"
        test_replacement = f"{test_count} tests "
        
        for path in files['readme'] + files['release_notes']:
            content = self._read_file(path)
            if not content:
                continue
            
            # Replace test count references
            updated = re.sub(
                test_pattern_old,
                test_replacement,
                content
            )
            
            # Replace test badges
            updated = re.sub(
                r'badge/tests-\d+%2F\d+-',
                f'badge/tests-{test_count}%2F{test_count}-',
                updated
            )
            
            if updated != content:
                self._write_file(path, updated)
        
        return len(self.errors) == 0
    
    def update_version_comments(self, files: Dict[str, List[Path]]) -> bool:
        """Update version in test module comments."""
        print("\n💬 Updating version comments in test modules...")
        
        version_no_v = self.version.lstrip("v")
        
        for path in files['test_comments']:
            content = self._read_file(path)
            if not content:
                continue
            
            # Update "Version: X.Y.Z" in docstrings
            updated = re.sub(
                r'Version:\s+[\d.]+',
                f'Version: {version_no_v}',
                content
            )
            
            if updated != content:
                self._write_file(path, updated)
        
        return len(self.errors) == 0
    
    def regenerate_examples(self) -> bool:
        """Regenerate txt, pdf, and html example reports."""
        print("\n📊 Regenerating example reports...")
        
        examples_dir = self.portfolio_dir / "examples"
        example_csv = examples_dir / "example_trades.csv"
        
        if not example_csv.exists():
            self.errors.append(f"Example CSV not found: {example_csv}")
            return False
        
        cmd = [
            "python3", "-m", "portfolio_analyzer.cli",
            "--csv", str(example_csv),
            "--output", str(examples_dir / "example_report.txt"),
            "--pdf", str(examples_dir / "example_report.pdf"),
            "--html", str(examples_dir / "example_report.html"),
        ]
        
        if self.dry_run:
            self.changes.append(f"  [DRY-RUN] Would regenerate examples")
            return True
        
        code, output = self._run_command(cmd)
        
        if code == 0:
            self.changes.append("  ✓ Regenerated example reports (txt, pdf, html)")
            return True
        else:
            self.errors.append(f"Failed to regenerate examples: {output}")
            return False
    
    def create_release_notes_section(self, test_count: int) -> str:
        """Generate release notes section for new version."""
        version_no_v = self.version.lstrip("v")
        today = datetime.now().strftime("%Y-%m-%d")
        
        return f"""## {version_no_v} ({today}) - [Release Title]

### New Features
- Feature 1 description
- Feature 2 description

### Improvements
- Improvement 1
- Improvement 2

### Tests and Coverage
- Added N new tests (test_module.py)
- Total test count: {test_count} (94% coverage)

### Bug Fixes
- Bug fix 1
- Bug fix 2
"""
    
    def git_status_clean(self) -> bool:
        """Check if git working directory is clean."""
        print("\n🔐 Checking git status...")
        
        code, output = self._run_command(["git", "status", "--porcelain"])
        
        # Filter out egg-info and other ignored files
        uncommitted = [
            line for line in output.split('\n')
            if line and not 'egg-info' in line and not '.DS_Store' in line
        ]
        
        if uncommitted:
            print("  ⚠️  Uncommitted changes found:")
            for line in uncommitted:
                print(f"    {line}")
            return False
        
        print("  ✓ Git working directory is clean")
        return True
    
    def git_commit_and_tag(self) -> bool:
        """Commit changes and create git tag."""
        print(f"\n📌 Git operations...")
        
        if self.dry_run:
            self.changes.append(f"  [DRY-RUN] Would commit and tag {self.version}")
            return True
        
        # Stage files
        code, _ = self._run_command(["git", "add", "-A"])
        if code != 0:
            self.errors.append("Failed to stage files")
            return False
        
        # Commit
        msg = f"Release {self.version}: Update version and examples"
        code, _ = self._run_command(["git", "commit", "-m", msg])
        if code != 0:
            self.errors.append("Failed to commit changes")
            return False
        self.changes.append(f"  ✓ Committed: {msg}")
        
        # Tag
        code, _ = self._run_command([
            "git", "tag", "-a", self.version,
            "-m", f"{self.version}: Portfolio Analyzer release"
        ])
        if code != 0:
            self.errors.append(f"Failed to create tag {self.version}")
            return False
        self.changes.append(f"  ✓ Tagged: {self.version}")
        
        return True
    
    def git_push(self) -> bool:
        """Push commit and tag to GitHub."""
        if self.no_push or self.dry_run:
            self.changes.append(f"  [SKIPPED] Git push (--no-push or --dry-run)")
            return True
        
        print("\n📤 Pushing to GitHub...")
        
        # Push main
        code, _ = self._run_command(["git", "push", "origin", "main"])
        if code != 0:
            self.errors.append("Failed to push main branch")
            return False
        self.changes.append("  ✓ Pushed main branch")
        
        # Push tag
        code, _ = self._run_command(["git", "push", "origin", self.version])
        if code != 0:
            self.errors.append(f"Failed to push tag {self.version}")
            return False
        self.changes.append(f"  ✓ Pushed tag {self.version}")
        
        return True
    
    def print_github_release_template(self, test_count: int) -> None:
        """Print GitHub release notes template."""
        version_no_v = self.version.lstrip("v")
        
        template = f"""
============================================================
📋 GitHub Release Template
============================================================

Go to: https://github.com/zhybear/finance_tools/releases/new

**Tag version**: {self.version}
**Release title**: v{version_no_v}: [Your release title]
**Description**:

## Sortable Holdings Table

### New Features
- **Interactive sortable holdings table**: Click any column header to sort Detailed Holdings
- **Smart sorting logic**: Numeric columns sort high→low or low→high, text sorts A→Z
- **Visual sort indicators**: Up/down arrows (▲/▼) show current sort direction
- **Nested trades preservation**: Expanding symbol trades keeps attached during sorting

### Tests and Coverage
- **Test count**: {test_count} tests (94% coverage)
- **Example report**: https://rawcdn.githack.com/zhybear/finance_tools/main/portfolio_analyzer/examples/example_report.html

Then click "Publish release"

============================================================
"""
        print(template)
    
    def run(self) -> bool:
        """Execute complete release workflow."""
        print("=" * 60)
        print("🚀 Portfolio Analyzer Release Agent")
        print("=" * 60)
        
        if self.dry_run:
            print("\n⚠️  DRY-RUN MODE: Changes will NOT be saved to disk")
        
        # Validation
        if not self.validate_version_format():
            self.print_summary()
            return False
        
        test_count = self.get_test_count()
        if test_count is None:
            self.print_summary()
            return False
        
        # Find files
        files = self.find_files_to_update()
        if self.errors:
            self.print_summary()
            return False
        
        # Update files
        if not self.update_version_strings(files):
            self.print_summary()
            return False
        
        if not self.update_test_count_references(test_count, files):
            self.print_summary()
            return False
        
        if not self.update_version_comments(files):
            self.print_summary()
            return False
        
        # Regenerate examples
        if not self.regenerate_examples():
            self.print_summary()
            return False
        
        # Git operations
        if not self.dry_run:
            if not self.git_status_clean():
                self.print_summary()
                return False
            
            if not self.git_commit_and_tag():
                self.print_summary()
                return False
            
            if not self.git_push():
                self.print_summary()
                return False
        
        # Success
        self.print_summary()
        self.print_github_release_template(test_count)
        return True
    
    def print_summary(self) -> None:
        """Print summary of changes and errors."""
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        if self.changes:
            print("\n✅ Changes:")
            for change in self.changes:
                print(change)
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  {error}")
        
        if not self.changes and not self.errors:
            print("\n(No changes)")
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Release Agent for Portfolio Analyzer"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Target version (e.g., v1.3.7 or 1.3.7)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without making changes"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Don't push to GitHub"
    )
    
    args = parser.parse_args()
    
    agent = ReleaseAgent(
        version=args.version,
        dry_run=args.dry_run,
        no_push=args.no_push
    )
    
    success = agent.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
