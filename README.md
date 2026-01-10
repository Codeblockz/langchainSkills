# LangChain Community Plugin for Claude Code

> **Unofficial** community plugin - not affiliated with LangChain, Inc.

Build AI applications with LangChain and LangGraph. This plugin provides comprehensive guidance for agents, RAG pipelines, and LCEL chains with best practices baked in.

## Features

| Skill | Use Case | Triggers |
|-------|----------|----------|
| **langgraph** | AI agents with tools, state, HITL | "build an agent", "add tools to agent" |
| **langchain-rag** | RAG pipelines with vector stores | "build RAG pipeline", "set up vector store" |
| **langchain-chains** | LCEL chains for summarization, extraction | "create summarization chain", "extract data" |

## Installation

### Via Marketplace (Recommended)

```bash
# Add the marketplace
/plugin marketplace add github:Codeblockz/langchain-community-plugin

# Install the plugin
/plugin install langchain-community
```

### Direct Installation

```bash
# Install from GitHub (supports updates)
claude plugins add https://github.com/Codeblockz/langchain-community-plugin
```

To update the plugin later:
```bash
claude plugins update langchain-community
```

Alternatively, install from a local path:
```bash
claude plugins add /path/to/langchain-community-plugin
```

## Local Development

To test the plugin during development without installing:

```bash
claude --plugin-dir /path/to/langchain-community-plugin
```

This loads your plugin directly. Restart Claude Code to pick up changes as you develop.

**Verifying the plugin loaded:**
- Run `/help` to see commands listed under `langchain-community:`
- Run `/agents` to see the reviewer agents
- Ask Claude to "build an agent" to trigger the langgraph skill

**Debugging:**
- Use `claude --debug` to see plugin loading errors
- Check YAML frontmatter syntax in skill/command files

## Skills

### langgraph (Agents)

Build AI agents that can use tools, maintain state, and interact with humans.

**When to use:**
- Autonomous agents that decide which tools to call
- Multi-step reasoning with tool use
- Human-in-the-loop approval workflows
- Stateful conversations with memory

**Example triggers:**
- "Build an agent that can search the web and write files"
- "Create a ReAct agent with custom tools"
- "Add human approval before tool execution"

### langchain-rag (RAG Pipelines)

Build retrieval-augmented generation pipelines with any vector store.

**Supported vector stores:**
- InMemoryVectorStore (prototyping)
- FAISS (local, file-based)
- Chroma (local with server option)
- pgvector (PostgreSQL)
- Pinecone (managed cloud)
- Qdrant (open source, cloud)
- Weaviate (open source, cloud)

**When to use:**
- Question answering over documents
- Semantic search applications
- Knowledge bases with retrieval
- Document-grounded chatbots

**Example triggers:**
- "Build a RAG pipeline to answer questions about my docs"
- "Set up FAISS vector store with persistence"
- "Load PDFs and create searchable index"

### langchain-chains (LCEL Chains)

Build data processing pipelines using LangChain Expression Language.

**When to use:**
- Summarization (single doc or multiple)
- Data extraction with structured output
- Text classification
- Translation
- Any prompt → LLM → parser workflow

**Example triggers:**
- "Create a summarization chain for long documents"
- "Extract entities from text into Pydantic models"
- "Build a classification pipeline with confidence scores"

## Commands

### Agents

| Command | Description |
|---------|-------------|
| `/langchain-community:new-agent` | Scaffold a new agent (create_agent or StateGraph) |
| `/langchain-community:add-tool` | Add a tool to an existing agent |

### RAG

| Command | Description |
|---------|-------------|
| `/langchain-community:new-rag` | Scaffold a RAG pipeline with your choice of vector store |

### Chains

| Command | Description |
|---------|-------------|
| `/langchain-community:new-chain` | Scaffold a chain (summarization, extraction, classification, translation) |

## Agents (Code Reviewers)

### langgraph-reviewer

Automatically reviews LangGraph agent code for common mistakes:
- Missing checkpointers for persistence
- Wrong state annotation types
- Missing reducers for list fields
- Recursion limit issues
- Incorrect interrupt placement

**Triggers proactively** after writing agent code, or invoke explicitly: "Review my agent code"

### rag-reviewer

Automatically reviews RAG pipeline code for common mistakes:
- Embedding dimension mismatches
- Missing metadata preservation
- Unhandled empty results
- Suboptimal chunk sizes
- Missing FAISS deserialization flag

**Triggers proactively** after writing RAG code, or invoke explicitly: "Review my RAG pipeline"

## Quick Start Examples

### Create an Agent

```
You: Build an agent that can search Wikipedia and save notes

Claude: [Uses langgraph skill, scaffolds agent with tools]
```

### Create a RAG Pipeline

```
You: I need to build a Q&A system over my company docs using FAISS

Claude: [Uses langchain-rag skill, creates pipeline with FAISS persistence]
```

### Create a Chain

```
You: Create a chain to extract contact info from emails

Claude: [Uses langchain-chains skill, creates extraction chain with Pydantic]
```

## Requirements

- Python 3.10+ (3.11 recommended)
- Core: `pip install "langchain>=1.0" "langchain-openai>=1.0"`
- Agents: `pip install langgraph`
- RAG: Vector store specific (see skill docs)
  - FAISS: `pip install faiss-cpu`
  - Chroma: `pip install langchain-chroma`
  - pgvector: `pip install langchain-postgres psycopg[binary]`
  - Pinecone: `pip install langchain-pinecone pinecone-client`

## Plugin Structure

```
langchain-community-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── langgraph/           # Agent patterns
│   ├── langchain-rag/       # RAG pipelines
│   └── langchain-chains/    # LCEL chains
├── commands/
│   ├── new-agent.md
│   ├── add-tool.md
│   ├── new-rag.md
│   └── new-chain.md
├── agents/
│   ├── langgraph-reviewer.md
│   └── rag-reviewer.md
└── LICENSE
```

## Version

v2.0.0 - Added RAG and Chains skills, renamed to `langchain-community`
