"""
Import path validation.

Checks that import statements reference valid, current LangChain/LangGraph modules.
"""

import re
from dataclasses import dataclass

# Known valid import paths (2025 LangChain architecture)
VALID_IMPORTS = {
    # Core
    "langchain_core.prompts": ["ChatPromptTemplate", "PromptTemplate", "MessagesPlaceholder"],
    "langchain_core.output_parsers": ["StrOutputParser", "JsonOutputParser", "PydanticOutputParser"],
    "langchain_core.runnables": ["RunnablePassthrough", "RunnableParallel", "RunnableLambda", "RunnableBranch", "Runnable"],
    "langchain_core.messages": ["HumanMessage", "AIMessage", "SystemMessage", "ToolMessage", "AnyMessage"],
    "langchain_core.tools": ["tool", "Tool", "StructuredTool"],
    "langchain_core.vectorstores": ["InMemoryVectorStore", "VectorStore"],
    "langchain_core.documents": ["Document"],

    # Chat models
    "langchain_openai": ["ChatOpenAI", "OpenAIEmbeddings", "OpenAI"],
    "langchain_anthropic": ["ChatAnthropic"],
    "langchain_google_genai": ["ChatGoogleGenerativeAI"],

    # Community
    "langchain_community.document_loaders": ["WebBaseLoader", "PyPDFLoader", "DirectoryLoader", "TextLoader", "CSVLoader"],
    "langchain_community.vectorstores": ["FAISS", "Chroma", "Pinecone", "Qdrant", "Weaviate", "PGVector"],
    "langchain_community.embeddings": ["HuggingFaceEmbeddings"],

    # Text splitters
    "langchain_text_splitters": ["RecursiveCharacterTextSplitter", "CharacterTextSplitter", "TokenTextSplitter"],

    # LangGraph
    "langgraph.graph": ["StateGraph", "START", "END", "MessagesState"],
    "langgraph.graph.message": ["add_messages"],
    "langgraph.checkpoint.memory": ["InMemorySaver", "MemorySaver"],
    "langgraph.checkpoint.sqlite": ["SqliteSaver"],
    "langgraph.checkpoint.postgres": ["PostgresSaver"],
    "langgraph.prebuilt": ["create_react_agent", "ToolNode"],

    # LangChain agents (new style)
    "langchain.agents": ["create_agent", "AgentExecutor"],
    "langchain.tools": ["tool", "Tool"],
    "langchain.chat_models": ["init_chat_model"],
    "langchain.messages": ["HumanMessage", "AIMessage", "SystemMessage", "ToolMessage", "AnyMessage"],
}

# Deprecated imports that should be avoided
DEPRECATED_IMPORTS = {
    "langchain.prompts": "Use langchain_core.prompts instead",
    "langchain.schema": "Use langchain_core.messages instead",
    "langchain.llms": "Use langchain_openai or langchain_anthropic instead",
    "langchain.embeddings": "Use langchain_openai.OpenAIEmbeddings or langchain_community.embeddings",
    "langchain.vectorstores": "Use langchain_community.vectorstores or langchain_core.vectorstores",
    "langchain.document_loaders": "Use langchain_community.document_loaders",
    "langchain.text_splitter": "Use langchain_text_splitters",
    "langchain.chains": "Use LCEL (langchain_core.runnables) instead",
    "langchain.memory": "Use LangGraph checkpointers instead",
}


@dataclass
class ImportIssue:
    """An issue with an import statement."""

    import_path: str
    item: str | None
    message: str
    level: str  # "error" or "warning"
    suggestion: str | None = None


def extract_imports(code: str) -> list[tuple[str, list[str]]]:
    """Extract import statements from code.

    Returns list of (module_path, [imported_items])
    """
    imports = []

    # Match: from X import Y, Z
    from_pattern = r"from\s+([\w.]+)\s+import\s+(.+)"
    for match in re.finditer(from_pattern, code):
        module = match.group(1)
        items = [i.strip().split(" as ")[0] for i in match.group(2).split(",")]
        imports.append((module, items))

    # Match: import X
    import_pattern = r"^import\s+([\w.]+)"
    for match in re.finditer(import_pattern, code, re.MULTILINE):
        module = match.group(1)
        imports.append((module, []))

    return imports


def validate_imports(code: str) -> list[ImportIssue]:
    """Validate import statements in code."""
    issues = []
    imports = extract_imports(code)

    for module, items in imports:
        # Check for deprecated modules
        for deprecated, suggestion in DEPRECATED_IMPORTS.items():
            if module.startswith(deprecated):
                issues.append(ImportIssue(
                    import_path=module,
                    item=None,
                    message=f"Deprecated import path: {module}",
                    level="warning",
                    suggestion=suggestion,
                ))
                break

        # Check if module is in our known valid list
        if module in VALID_IMPORTS:
            valid_items = VALID_IMPORTS[module]
            for item in items:
                # Handle "X as Y" syntax
                item_name = item.split(" as ")[0].strip()
                if item_name not in valid_items and item_name != "*":
                    issues.append(ImportIssue(
                        import_path=module,
                        item=item_name,
                        message=f"Unknown import: {item_name} from {module}",
                        level="warning",
                        suggestion=f"Valid imports from {module}: {', '.join(valid_items[:5])}...",
                    ))

    return issues


def format_import_issues(issues: list[ImportIssue]) -> str:
    """Format import issues as readable output."""
    if not issues:
        return "  No import issues found"

    lines = []
    for issue in issues:
        icon = "ERROR" if issue.level == "error" else "WARN"
        if issue.item:
            lines.append(f"  [{icon}] {issue.item} from {issue.import_path}")
        else:
            lines.append(f"  [{icon}] {issue.import_path}")
        lines.append(f"          {issue.message}")
        if issue.suggestion:
            lines.append(f"          Suggestion: {issue.suggestion}")

    return "\n".join(lines)
