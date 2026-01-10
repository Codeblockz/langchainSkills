"""
Skill content validator.

Checks skill files for:
- Valid Python syntax in code blocks
- Correct import paths
- Known anti-patterns (Pydantic for state, missing checkpointer, etc.)
- Deprecated APIs
"""

import re
import ast
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Issue:
    """A validation issue found in a skill."""

    level: str  # "error" or "warning"
    rule: str  # Rule ID like "langgraph/typeddict-state"
    message: str
    line: int | None = None
    code_block: int | None = None  # Which code block (1-indexed)
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """Result of validating a skill file."""

    skill_name: str
    file_path: Path
    issues: list[Issue] = field(default_factory=list)
    code_blocks_checked: int = 0

    @property
    def passed(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warning")


class SkillValidator:
    """Validates skill content for correctness."""

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict]:
        """Load validation rules."""
        return [
            # LangGraph rules
            {
                "id": "langgraph/typeddict-state",
                "pattern": r"class\s+\w+\(BaseModel\):",
                "context": r"(State|state|graph|Graph|langgraph)",
                "message": "LangGraph state must use TypedDict, not Pydantic BaseModel",
                "level": "error",
                "suggestion": "Change to: class State(TypedDict):",
            },
            {
                "id": "langgraph/missing-reducer",
                "pattern": r"messages:\s*list\[",
                "negative_pattern": r"messages:\s*Annotated\[list\[",
                "context": r"(TypedDict|State)",
                "message": "List fields in state need Annotated with a reducer or they'll be replaced",
                "level": "error",
                "suggestion": "Use: messages: Annotated[list[AnyMessage], add_messages]",
            },
            {
                "id": "langgraph/wrong-recursion-limit",
                "pattern": r'["\']configurable["\']\s*:\s*\{[^}]*["\']recursion_limit["\']',
                "message": "recursion_limit should be a top-level config key, not inside configurable",
                "level": "error",
                "suggestion": 'Use: graph.invoke(inputs, {"recursion_limit": 50})',
            },
            # Deprecated imports
            {
                "id": "deprecated/langchain-agents",
                "pattern": r"from\s+langchain\.agents\s+import\s+AgentExecutor",
                "message": "AgentExecutor is deprecated, use LangGraph agents instead",
                "level": "warning",
                "suggestion": "Use create_agent from langchain.agents or build with StateGraph",
            },
            {
                "id": "deprecated/old-react-agent",
                "pattern": r"from\s+langchain\.agents\s+import\s+create_react_agent",
                "message": "create_react_agent is the old pattern, use create_agent instead",
                "level": "warning",
                "suggestion": "Use: from langchain.agents import create_agent",
            },
            # RAG rules
            {
                "id": "rag/faiss-deserialization",
                "pattern": r"FAISS\.load_local\([^)]+\)",
                "negative_pattern": r"allow_dangerous_deserialization\s*=\s*True",
                "message": "FAISS.load_local requires allow_dangerous_deserialization=True",
                "level": "error",
                "suggestion": "Add: allow_dangerous_deserialization=True",
            },
            {
                "id": "rag/missing-chunk-overlap",
                "pattern": r"RecursiveCharacterTextSplitter\([^)]*chunk_size",
                "negative_pattern": r"chunk_overlap",
                "message": "Text splitter should include chunk_overlap to prevent context loss",
                "level": "warning",
                "suggestion": "Add: chunk_overlap=200",
            },
            # General code quality
            {
                "id": "code/placeholder-todo",
                "pattern": r"#\s*(TODO|FIXME|XXX|HACK)",
                "message": "Code contains TODO/FIXME placeholder",
                "level": "warning",
            },
            {
                "id": "code/ellipsis-placeholder",
                "pattern": r"^\s*\.\.\.\s*$",
                "message": "Code contains ... placeholder - examples should be complete",
                "level": "warning",
            },
            {
                "id": "code/pass-placeholder",
                "pattern": r"^\s*pass\s*#",
                "message": "Code contains pass with comment - likely placeholder",
                "level": "warning",
            },
        ]

    def validate_skill(self, skill_path: Path) -> ValidationResult:
        """Validate a single skill file."""
        content = skill_path.read_text()
        skill_name = skill_path.parent.name

        result = ValidationResult(
            skill_name=skill_name,
            file_path=skill_path,
        )

        # Extract code blocks
        code_blocks = self._extract_code_blocks(content)
        result.code_blocks_checked = len(code_blocks)

        # Check each code block
        for i, (code, lang) in enumerate(code_blocks, 1):
            # Syntax check for Python
            if lang in ("python", "py", ""):
                syntax_issues = self._check_syntax(code, i)
                result.issues.extend(syntax_issues)

            # Pattern-based rules
            pattern_issues = self._check_patterns(code, i)
            result.issues.extend(pattern_issues)

        # Check full content for some rules
        full_content_issues = self._check_full_content(content)
        result.issues.extend(full_content_issues)

        return result

    def _extract_code_blocks(self, content: str) -> list[tuple[str, str]]:
        """Extract code blocks from markdown content."""
        pattern = r"```(\w*)\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        return [(code.strip(), lang) for lang, code in matches]

    def _check_syntax(self, code: str, block_num: int) -> list[Issue]:
        """Check Python syntax validity."""
        issues = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(Issue(
                level="error",
                rule="syntax/invalid-python",
                message=f"Invalid Python syntax: {e.msg}",
                line=e.lineno,
                code_block=block_num,
            ))
        return issues

    def _check_patterns(self, code: str, block_num: int) -> list[Issue]:
        """Check code against pattern rules."""
        issues = []

        # Skip blocks that are intentionally showing wrong examples
        if re.search(r"#\s*(WRONG|BAD|DON'T|INCORRECT)", code, re.IGNORECASE):
            return issues

        for rule in self.rules:
            # Check if pattern matches
            if not re.search(rule["pattern"], code, re.MULTILINE):
                continue

            # Check context requirement if present
            if "context" in rule:
                if not re.search(rule["context"], code, re.IGNORECASE):
                    continue

            # Check negative pattern (should NOT be present)
            if "negative_pattern" in rule:
                if re.search(rule["negative_pattern"], code, re.MULTILINE):
                    continue

            # Find line number
            line_num = None
            for i, line in enumerate(code.split("\n"), 1):
                if re.search(rule["pattern"], line):
                    line_num = i
                    break

            issues.append(Issue(
                level=rule["level"],
                rule=rule["id"],
                message=rule["message"],
                line=line_num,
                code_block=block_num,
                suggestion=rule.get("suggestion"),
            ))

        return issues

    def _check_full_content(self, content: str) -> list[Issue]:
        """Check full file content for issues."""
        issues = []

        # Check for missing critical sections
        if "## Critical Rules" not in content and "## Critical" not in content:
            issues.append(Issue(
                level="warning",
                rule="structure/missing-critical-rules",
                message="Skill should have a 'Critical Rules' section",
            ))

        if "## Common Gotchas" not in content and "## Gotchas" not in content:
            issues.append(Issue(
                level="warning",
                rule="structure/missing-gotchas",
                message="Skill should have a 'Common Gotchas' section",
            ))

        return issues

    def validate_all_skills(self, skills_dir: Path) -> list[ValidationResult]:
        """Validate all skills in a directory."""
        results = []
        for skill_path in skills_dir.glob("*/SKILL.md"):
            results.append(self.validate_skill(skill_path))
        return results


def format_result(result: ValidationResult) -> str:
    """Format validation result as readable output."""
    lines = [
        f"\n{'='*60}",
        f"Skill: {result.skill_name}",
        f"{'='*60}",
        f"Code blocks checked: {result.code_blocks_checked}",
    ]

    if result.passed and result.warning_count == 0:
        lines.append("Status: PASSED (no issues)")
    elif result.passed:
        lines.append(f"Status: PASSED ({result.warning_count} warnings)")
    else:
        lines.append(f"Status: FAILED ({result.error_count} errors, {result.warning_count} warnings)")

    if result.issues:
        lines.append("\nIssues:")
        for issue in result.issues:
            icon = "ERROR" if issue.level == "error" else "WARN"
            loc = ""
            if issue.code_block:
                loc = f"[block {issue.code_block}"
                if issue.line:
                    loc += f", line {issue.line}"
                loc += "] "

            lines.append(f"  [{icon}] {loc}{issue.message}")
            lines.append(f"          Rule: {issue.rule}")
            if issue.suggestion:
                lines.append(f"          Fix: {issue.suggestion}")

    return "\n".join(lines)
