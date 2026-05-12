"""
agent.py — The ReAct Agent

ReAct = Reason + Act
The loop:
  1. LLM THINKS about what to do  (Thought)
  2. LLM DECIDES which tool to call (Action)
  3. Tool runs, returns result     (Observation)
  4. LLM reads result, thinks again
  5. Repeat until LLM has enough to answer

Senior note: You don't write the loop — LangChain runs it.
Your job is to give the LLM good tools and a clear system prompt.
The quality of your system prompt directly determines agent quality.
"""

from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from tools import TOOLS


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
# This is the most important part. Be explicit about:
# - Who the agent is
# - What data it has access to
# - How it should behave
# - What format to respond in

SYSTEM_PROMPT = """You are a Personal Finance Advisor Agent with access to a user's bank transaction data.

You have 4 tools:
- get_transactions: Fetch raw transactions, optionally filtered by month or category
- categorize_spending: Get a breakdown of spending by category
- calculate_summary: Get income, expenses, savings, and savings rate
- flag_anomalies: Detect unusually large transactions

IMPORTANT RULES:
1. Always use tools to fetch real data — never make up numbers
2. For month filters, use format YYYY-MM (e.g. 2024-01 for January 2024)
3. After getting data, provide clear insights — not just raw numbers
4. If asked to compare months, call the tool twice with different month filters
5. Be concise but insightful. You are a financial advisor, not just a data fetcher.

Available data: January 2024 and February 2024 transactions.

{tools}

Use this format strictly:

Question: the input question you must answer
Thought: reason about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


# ── BUILD THE AGENT ───────────────────────────────────────────────────────────
def build_agent(api_key: str, verbose: bool = False) -> AgentExecutor:
    """
    Builds and returns the AgentExecutor.

    AgentExecutor is the runtime that:
    - feeds the LLM the prompt + tools
    - parses the LLM output to find Action/Action Input
    - calls the actual tool function
    - feeds the result back as Observation
    - stops when LLM outputs "Final Answer:"
    """

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",   # Best free model on Groq — fast + capable
        groq_api_key=api_key,
        temperature=0,                     # 0 = deterministic, good for data tasks
        max_tokens=2048,
    )

    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)

    # create_react_agent wires: llm + tools + prompt → a runnable agent
    agent = create_react_agent(llm=llm, tools=TOOLS, prompt=prompt)

    # AgentExecutor is the loop runner
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=verbose,          # True = prints Thought/Action/Observation to console
        max_iterations=6,         # Safety: stop after 6 tool calls max
        handle_parsing_errors=True,  # Don't crash on malformed LLM output
        return_intermediate_steps=True,  # Capture the full ReAct trace
    )

    return executor


def run_query(executor: AgentExecutor, query: str) -> dict:
    """
    Run a single query through the agent.
    Returns both the final answer and the intermediate steps (the ReAct trace).
    """
    result = executor.invoke({"input": query})

    return {
        "query": query,
        "answer": result["output"],
        "steps": [
            {
                "thought_action": str(step[0]),
                "observation": str(step[1])
            }
            for step in result.get("intermediate_steps", [])
        ]
    }
