"""
tools.py — The 4 tools your Finance Agent can call.

Each function is a real tool. The LLM doesn't run this code —
it decides WHICH tool to call and with WHAT arguments.
LangChain then actually executes the function.

Senior note: Keep tools small and single-purpose.
The LLM is better at combining tools than doing everything in one.
"""

import re
import pandas as pd
from langchain_core.tools import tool

# ── Load data once at module level (not on every tool call) ──────────────────
DATA_PATH = "data/transactions.csv"

def _parse_month(month):
    """Extract YYYY-MM from whatever the LLM passes (e.g. "month = '2024-01'")."""
    if not month or str(month).lower() == "none":
        return None
    match = re.search(r"\d{4}-\d{2}", str(month))
    return match.group() if match else str(month).strip()


def _parse_float(value, default: float) -> float:
    """Extract the first float from whatever the LLM passes (e.g. '2.0 (using default...)')."""
    match = re.search(r"\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else default


def _load_df() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    return df


# ── CATEGORY MAP ─────────────────────────────────────────────────────────────
# In production: this would be an ML classifier.
# For now: keyword-based — good enough to demonstrate the concept.
CATEGORY_MAP = {
    "Food & Dining":    ["swiggy", "zomato", "restaurant", "dinner", "lunch", "food"],
    "Transport":        ["uber", "ola", "petrol", "metro"],
    "Shopping":         ["amazon", "flipkart", "purchase"],
    "Bills & Utilities":["electricity", "internet", "mobile recharge", "bill"],
    "Entertainment":    ["netflix", "movie", "spotify"],
    "Health":           ["medical", "pharmacy", "doctor", "gym"],
    "Rent":             ["rent"],
    "Investments":      ["mutual fund", "sip", "investment"],
    "Income":           ["salary", "freelance", "payment received"],
    "ATM/Cash":         ["atm withdrawal"],
    "Other":            [],
}

def _categorize(description: str) -> str:
    desc_lower = description.lower()
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return "Other"


# ── TOOL 1: get_transactions ──────────────────────────────────────────────────
@tool
def get_transactions(month: str = None, category: str = None) -> str:
    """
    Fetch transactions from the CSV.
    Optionally filter by month (e.g. '2024-01') or category (e.g. 'Food & Dining').
    Returns a readable list of transactions.
    """
    print("\n\n************** calling get_transactions tool ********************\n\n")
    df = _load_df()
    df["category"] = df["description"].apply(_categorize)
    month = _parse_month(month)

    if month:
        df = df[df["date"].dt.to_period("M").astype(str) == month]

    if category:
        df = df[df["category"].str.lower() == category.lower()]

    if df.empty:
        return "No transactions found for the given filters."

    # Return as clean text — LLM reads this and reasons over it
    lines = []
    for _, row in df.iterrows():
        lines.append(
            f"{row['date'].date()} | {row['description']} | ₹{abs(row['amount'])} | {row['type'].upper()} | {row['category']}"
        )
    return "\n".join(lines)


# ── TOOL 2: categorize_spending ───────────────────────────────────────────────
@tool
def categorize_spending(month: str = None) -> str:
    """
    Break down total spending by category.
    Optionally filter by month (e.g. '2024-01').
    Returns category-wise spend totals, sorted by highest spend.
    """
    print("\n\n************** calling categorize_spending tool ********************\n\n")
    df = _load_df()
    df["category"] = df["description"].apply(_categorize)
    month = _parse_month(month)

    # Only look at debits (spending)
    debits = df[df["type"] == "debit"].copy()
    debits["amount"] = debits["amount"].abs()

    if month:
        debits = debits[debits["date"].dt.to_period("M").astype(str) == month]

    if debits.empty:
        return "No spending data found."

    summary = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    total = summary.sum()

    lines = [f"{'Category':<25} {'Amount':>12} {'% of Total':>12}"]
    lines.append("-" * 52)
    for cat, amt in summary.items():
        pct = (amt / total) * 100
        lines.append(f"{cat:<25} ₹{amt:>10,.0f} {pct:>10.1f}%")
    lines.append("-" * 52)
    lines.append(f"{'TOTAL':<25} ₹{total:>10,.0f}")

    return "\n".join(lines)


# ── TOOL 3: calculate_summary ─────────────────────────────────────────────────
@tool
def calculate_summary(month: str = None) -> str:
    """
    Calculate a financial summary: total income, total expenses, net savings, and savings rate.
    Optionally filter by month (e.g. '2024-01').
    """
    print("\n\n************** calling calculate_summary tool ********************\n\n")
    df = _load_df()
    month = _parse_month(month)
    if month:
        df = df[df["date"].dt.to_period("M").astype(str) == month]

    if df.empty:
        return "No data found for the given period."

    total_income   = df[df["type"] == "credit"]["amount"].sum()
    total_expenses = df[df["type"] == "debit"]["amount"].abs().sum()
    net_savings    = total_income - total_expenses
    savings_rate   = (net_savings / total_income * 100) if total_income > 0 else 0

    # Month-over-month if no filter given
    lines = [
        f"💰 Total Income   : ₹{total_income:,.0f}",
        f"💸 Total Expenses : ₹{total_expenses:,.0f}",
        f"🏦 Net Savings    : ₹{net_savings:,.0f}",
        f"📊 Savings Rate   : {savings_rate:.1f}%",
    ]

    if net_savings < 0:
        lines.append("⚠️  You spent more than you earned this period.")
    elif savings_rate < 20:
        lines.append("💡 Savings rate below 20%. Consider reviewing discretionary spend.")
    else:
        lines.append("✅ Good savings rate!")

    return "\n".join(lines)


# ── TOOL 4: flag_anomalies ────────────────────────────────────────────────────
@tool
def flag_anomalies(threshold_multiplier: str = "2.0") -> str:
    """
    Detect unusual transactions: amounts that are significantly higher than
    the average for that category. threshold_multiplier controls sensitivity
    (default 2.0 = flag anything 2x above category average).
    """
    print("\n\n************** calling flag_anomalies tool ********************\n\n")
    multiplier = _parse_float(threshold_multiplier, default=2.0)
    df = _load_df()
    df["category"] = df["description"].apply(_categorize)
    df["abs_amount"] = df["amount"].abs()

    debits = df[df["type"] == "debit"].copy()

    # Compute per-category mean and std
    stats = debits.groupby("category")["abs_amount"].agg(["mean", "std"]).reset_index()
    stats.columns = ["category", "mean", "std"]
    stats["std"] = stats["std"].fillna(0)

    debits = debits.merge(stats, on="category")
    debits["threshold"] = debits["mean"] + multiplier * debits["std"]
    anomalies = debits[debits["abs_amount"] > debits["threshold"]]

    if anomalies.empty:
        return "No anomalies detected. All transactions look normal."

    lines = ["🚨 Anomalous Transactions Detected:", ""]
    for _, row in anomalies.iterrows():
        lines.append(
            f"• {row['date'].date()} | {row['description']}"
            f"\n  Amount: ₹{row['abs_amount']:,.0f} | "
            f"Category avg: ₹{row['mean']:,.0f} | "
            f"Threshold: ₹{row['threshold']:,.0f}"
        )
    return "\n".join(lines)


# Export all tools as a list — agent.py imports this
TOOLS = [get_transactions, categorize_spending, calculate_summary, flag_anomalies]
