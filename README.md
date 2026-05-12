# Personal Finance Agent

A ReAct agent that answers questions about your finances using real tool calls.

## Architecture

```
User Query
    │
    ▼
AgentExecutor (LangChain)
    │
    ├─► Thought: "I need to categorize spending for January"
    ├─► Action: categorize_spending(month="2024-01")
    ├─► Observation: <actual data from your CSV>
    ├─► Thought: "Now I can answer the question"
    └─► Final Answer: <response with real numbers>
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Groq API key (get one free at console.groq.com)
export GROQ_API_KEY=gsk_...

# 3. Start the Django server
python manage.py runserver 8000

# 4. Open the UI
open index.html   # or just open in your browser

# Server runs at http://localhost:8000
```

## Project Structure

```
finance-agent/
├── data/
│   └── transactions.csv     # Mock bank transactions (Jan–Feb 2024)
├── tools.py                 # The 4 tools the agent can call
├── agent.py                 # ReAct agent setup (LangChain + Groq)
├── api/
│   ├── views.py             # Django views (POST /query, GET /health)
│   └── middleware.py        # CORS middleware
├── settings.py              # Django settings (minimal, no DB)
├── urls.py                  # URL routing
├── manage.py                # Django entry point
├── index.html               # Frontend UI
└── requirements.txt
```

## The 4 Tools

| Tool | What it does | When the agent calls it |
|------|-------------|------------------------|
| `get_transactions` | Fetch raw transactions filtered by month/category | "Show me my Uber rides in January" |
| `categorize_spending` | Category-wise spend breakdown | "Where am I spending the most?" |
| `calculate_summary` | Income, expenses, savings rate | "What's my savings rate?" |
| `flag_anomalies` | Detect unusually large transactions | "Any weird charges?" |

## Interview Questions You Should Know Cold

**Q: Why did you use ReAct instead of just chaining prompts?**
A: ReAct allows the agent to dynamically decide which tools to call based on the query. 
A static chain would require knowing upfront which tools to call. ReAct handles 
multi-step reasoning where each step depends on the previous observation.

**Q: How does the agent decide which tool to call?**
A: The LLM reads the system prompt which describes each tool, then in the Thought step 
it reasons about which tool fits the current need. LangChain parses the Action/Action Input 
from the LLM output and executes the actual function.

**Q: What would you do differently in production?**
A: (1) Stream responses instead of waiting for full completion, (2) Add Langfuse for 
observability, (3) Use async tool execution, (4) Add caching for repeated queries, 
(5) Replace keyword categorization with an ML classifier.

**Q: How do you handle tool failures?**
A: handle_parsing_errors=True in AgentExecutor prevents crashes on malformed LLM output. 
In production I'd add try/catch in each tool function and return structured error messages 
the agent can reason about.

**Q: What's the max_iterations parameter for?**
A: Safety guard. Without it, a confused agent could loop forever. 6 iterations means 
at most 6 tool calls per query, which is enough for any reasonable finance question.
