"""
Configuration constants for the testing system.
"""

from pathlib import Path

# Directory paths
ROOT_DIR = Path(__file__).parent.parent
TESTING_DIR = ROOT_DIR / "testing"
SKILLS_DIR = ROOT_DIR / "skills"
VARIANTS_DIR = TESTING_DIR / "variants"
FIXTURES_DIR = TESTING_DIR / "fixtures"
PROMPTS_DIR = FIXTURES_DIR / "prompts"
RUBRICS_DIR = FIXTURES_DIR / "rubrics"
REPORTS_DIR = TESTING_DIR / "reports"

# Database
METRICS_DB_PATH = TESTING_DIR / ".metrics.db"

# Model configuration
TRIGGER_MODEL = "claude-haiku-4-20250514"  # Fast/cheap for trigger testing
QUALITY_MODEL = "claude-sonnet-4-20250514"  # Better quality for evaluation

# Evaluation thresholds
TRIGGER_CONFIDENCE_THRESHOLD = 0.7
QUALITY_PASS_THRESHOLD = 0.70

# Default test parameters
DEFAULT_SAMPLE_SIZE = 10
DEFAULT_REPORT_DAYS = 30

# Available skills
SKILLS = ["langgraph", "langchain-rag", "langchain-chains"]
