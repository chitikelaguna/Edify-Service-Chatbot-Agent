from langgraph.graph import StateGraph, END
from app.langgraph.state import AgentState

# Import Nodes
from app.langgraph.nodes.validate_session import validate_session_node
from app.langgraph.nodes.load_memory import load_memory_node
from app.langgraph.nodes.decide_source import decide_source_node
from app.langgraph.nodes.fetch_crm import fetch_crm_node
from app.langgraph.nodes.fetch_lms import fetch_lms_node
from app.langgraph.nodes.fetch_rms import fetch_rms_node
from app.langgraph.nodes.fetch_rag import fetch_rag_node
from app.langgraph.nodes.check_context import check_context_node
from app.langgraph.nodes.call_llm import call_llm_node
from app.langgraph.nodes.save_memory import save_memory_node

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("validate_session", validate_session_node)
workflow.add_node("load_memory", load_memory_node)
workflow.add_node("decide_source", decide_source_node)
workflow.add_node("fetch_crm", fetch_crm_node)
workflow.add_node("fetch_lms", fetch_lms_node)
workflow.add_node("fetch_rms", fetch_rms_node)
workflow.add_node("fetch_rag", fetch_rag_node)
workflow.add_node("check_context", check_context_node)
workflow.add_node("call_llm", call_llm_node)
# workflow.add_node("fallback", fallback_node)
workflow.add_node("save_memory", save_memory_node)

# Set Entry Point
workflow.set_entry_point("validate_session")

# Edge: Validate Session -> Load Memory (or End)
def route_after_validation(state: AgentState):
    if state.get("response"): # Error occurred
        return "save_memory"
    return "load_memory"

workflow.add_conditional_edges(
    "validate_session",
    route_after_validation,
    {
        "save_memory": "save_memory",
        "load_memory": "load_memory"
    }
)

# Edge: Load Memory -> Decide Source
workflow.add_edge("load_memory", "decide_source")

# Edge: Decide Source -> Fetch ...
def route_source(state: AgentState):
    source = state.get("source_type", "general")
    
    # If response already set (e.g., greeting), skip to check_context
    if state.get("response"):
        return "check_context"
    
    if source == "crm":
        return "fetch_crm"
    elif source == "lms":
        return "fetch_lms"
    elif source == "rms":
        return "fetch_rms"
    elif source == "rag":
        return "fetch_rag"
    else:
        return "check_context" # Direct to check_context (which handles general/none)

workflow.add_conditional_edges(
    "decide_source",
    route_source,
    {
        "fetch_crm": "fetch_crm",
        "fetch_lms": "fetch_lms",
        "fetch_rms": "fetch_rms",
        "fetch_rag": "fetch_rag",
        "check_context": "check_context"
    }
)

# Edges: Fetch -> Check Context
workflow.add_edge("fetch_crm", "check_context")
workflow.add_edge("fetch_lms", "check_context")
workflow.add_edge("fetch_rms", "check_context")
workflow.add_edge("fetch_rag", "check_context")

# Edge: Check Context -> Call LLM or Save Memory (if empty/error)
def route_after_check(state: AgentState):
    if state.get("response"): # "No data found" or error set by check_context
        return "save_memory"
    return "call_llm"

workflow.add_conditional_edges(
    "check_context",
    route_after_check,
    {
        "save_memory": "save_memory",
        "call_llm": "call_llm"
    }
)

# Edge: Call LLM -> Save Memory
workflow.add_edge("call_llm", "save_memory")

# Fallback node removed as it was unreachable
# workflow.add_edge("fallback", "save_memory")

# Edge: Save Memory -> END
workflow.add_edge("save_memory", END)

# Compile
graph = workflow.compile()
