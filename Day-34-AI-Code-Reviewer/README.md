# Day 34 — AI Function Calling: Tool Use, Custom Registry & Code Reviewer

> **Phase 3 — AI & Machine Learning** | Week 6 | Day 34 of 180

---

## 📌 What I Learned Today

- Raw Anthropic tool_use API — no frameworks
- Tool definition schema: name, description, input_schema (JSON Schema)
- stop_reason "tool_use" vs "end_turn" — how to detect agent state
- block.type == "tool_use" — inspecting Claude's tool call intent
- block.id, block.name, block.input — extracting tool call details
- tool_use_id — MUST match block.id when returning results
- Feeding tool results back: role="user", type="tool_result"
- The complete agentic loop: messages → Claude → tool call → result → repeat
- Parallel tool calls — Claude can return multiple tool_use blocks
- tool_choice parameter: auto, any, specific tool, none
- Custom ToolRegistry class: register decorator, execute, get_schemas
- Tool docstrings are CRITICAL — Claude reads them to decide which to call
- Good tool descriptions: when to use, when NOT to use, what it returns
- input_schema validation using JSON Schema format
- Forcing specific tool calls with tool_choice={"type":"tool","name":"..."}
- MockAnthropicForReview — stateful mock for development
- AST analysis: ast.parse(), ast.walk(), ast.FunctionDef
- Security scanning: regex patterns for credentials, SQL injection, eval()
- Style checking: naming conventions, line length, docstrings, None comparison
- Performance scanning: nested loops via AST LoopVisitor, blocking sleep

## 🔨 Project Built

**AI Code Reviewer** — Raw tool calling pipeline:

**ToolRegistry** (custom, no LangChain):

- `register()` decorator registers Python functions as AI tools
- `execute()` runs tools with error handling, returns string
- `get_all_schemas()` formats tool definitions for Claude API
- `get_call_log()` tracks all tool calls for debugging

**5 Registered Tools:**

- `read_file`: validates path, reads content, returns metadata
- `compute_code_metrics`: AST analysis → line/func/class counts
- `find_security_issues`: regex scan for hardcoded creds, SQL injection, eval, bare except
- `find_style_issues`: PEP 8 violations, naming, docstrings, None comparisons
- `find_performance_issues`: nested loops (AST), blocking sleep, string concat

**AICodeReviewer** agentic loop:

- Multi-step: read → metrics → security → style → performance → synthesize
- Handles tool_use/end_turn stop reasons
- Collects tool results across iterations
- Builds structured CodeReview response

**Sample Code:**

- bad_code.py: hardcoded credentials, SQL injection, bare except, O(n²) loop,
  wrong naming, no docstrings, ZeroDivisionError, blocking sleep
- good_code.py: type hints, docstrings, async I/O, O(n) algorithm,
  proper error handling, named constants, clean structure

## 🚀 How to Run

```bash
cd Day-34-AI-Code-Reviewer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

# Review bad code
curl -X POST http://localhost:8000/review/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "sample_code/bad_code.py"}'
```

## 🧠 Raw Tool Use vs LangChain

|           | Raw Anthropic         | LangChain @tool      |
| --------- | --------------------- | -------------------- |
| Schema    | Manual JSON dict      | Auto from type hints |
| Loop      | Manual while loop     | AgentExecutor        |
| Results   | Manual message append | Automatic            |
| Control   | Complete              | Framework handles    |
| Debugging | Direct visibility     | Abstracted           |
| Use when  | Production, custom    | Rapid prototyping    |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
