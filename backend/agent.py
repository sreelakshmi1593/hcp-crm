"""
LangGraph agent for HCP CRM.
Orchestrates the 5 tools using a ReAct-style graph with Groq LLM (llama-3.3-70b-versatile).
"""

import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import log_interaction, edit_interaction, search_hcp_profile, suggest_followup, analyze_sentiment

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are an intelligent AI assistant embedded in a pharmaceutical CRM system. 
You help medical sales representatives log and manage their interactions with Healthcare Professionals (HCPs).

You have access to 5 tools:
1. log_interaction - Save a new HCP interaction to the database
2. edit_interaction - Update/modify an existing interaction record
3. search_hcp_profile - Look up HCP details and past interaction history
4. suggest_followup - Generate AI-powered follow-up recommendations
5. analyze_sentiment - Analyze the HCP sentiment from conversation notes

Always be concise and professional. When logging interactions from natural language,
extract all relevant fields before calling log_interaction."""

ALL_TOOLS = [log_interaction, edit_interaction, search_hcp_profile, suggest_followup, analyze_sentiment]


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_agent():
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tool_node = ToolNode(ALL_TOOLS)

    def call_model(state: AgentState):
        msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(msgs)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


async def run_agent(user_message: str) -> dict:
    agent = get_agent()

    messages = [HumanMessage(content=user_message)]
    result = agent.invoke({"messages": messages})

    final_messages = result["messages"]
    final_response = ""
    tools_used = []

    for msg in final_messages:
        # collect tool names
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])
        # get last non-empty text response
        if hasattr(msg, "content"):
            if isinstance(msg.content, str) and msg.content.strip():
                final_response = msg.content
            elif isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text" and block.get("text","").strip():
                        final_response = block["text"]

    if not final_response:
        final_response = "Done. I have completed the requested action."

    return {
        "response": final_response,
        "tools_used": tools_used,
        "message_count": len(final_messages),
    }
