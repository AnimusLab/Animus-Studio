"""
Daily Content Workflow — LangGraph state machine.

Pipeline: Research → Script → Review → [Human Gate] → Voice → Editor → Thumbnail → Publish → Analytics

Each node is an agent. The graph handles routing, retries, and human-in-the-loop approval.
"""
from __future__ import annotations
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.executive.agent import ExecutiveAgent
from agents.research.agent import ResearchAgent
from agents.script.agent import ScriptAgent
from agents.review.agent import ReviewAgent
from agents.voice.agent import VoiceAgent
from agents.editor.agent import EditorAgent
from agents.publisher.agent import PublisherAgent
from agents.analytics.agent import AnalyticsAgent
from agents.base import AgentContext


# ─── Workflow State ────────────────────────────────────────────
class WorkflowState(TypedDict):
    job_id: str
    mission_id: str
    mission: dict
    brand: dict
    channels: list[dict]

    # Agent outputs
    executive_plan: dict
    research_brief: dict
    script: dict
    review: dict
    audio_path: str
    video_path: str
    thumbnail_path: str
    publish_results: dict
    analytics_report: dict

    # Control
    requires_approval: bool
    approved: bool
    error: str | None
    retry_count: Annotated[int, operator.add]


# ─── Node Functions ────────────────────────────────────────────

def _make_context(state: WorkflowState) -> AgentContext:
    from providers.registry import registry
    ctx = AgentContext(
        job_id=state["job_id"],
        mission_id=state["mission_id"],
        brand=state["brand"],
        provider=registry,         # inject capability registry
    )
    # Restore artifacts from state
    for key in ["research_brief", "script", "review", "audio_path", "video_path"]:
        if key in state and state[key]:
            ctx.set(key, state[key])
    return ctx


async def executive_node(state: WorkflowState) -> dict:
    agent = ExecutiveAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {"workflow": "daily_content", "mission": state["mission"]})
    return {"executive_plan": result}


async def research_node(state: WorkflowState) -> dict:
    agent = ResearchAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {"mission": state["mission"]})
    return {"research_brief": result}


async def script_node(state: WorkflowState) -> dict:
    agent = ScriptAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {"mission": state["mission"]})
    return {"script": result}


async def review_node(state: WorkflowState) -> dict:
    agent = ReviewAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {})
    # If verdict is rewrite, increment retry_count via the operator.add reducer
    retry_increment = 1 if result.get("verdict") == "rewrite" else 0
    return {"review": result, "retry_count": retry_increment}


async def voice_node(state: WorkflowState) -> dict:
    agent = VoiceAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {})
    return {"audio_path": result.get("audio_path", "")}


async def editor_node(state: WorkflowState) -> dict:
    agent = EditorAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {})
    return {
        "video_path": result.get("video_path", ""),
        "error": result.get("error"),
    }


async def publish_node(state: WorkflowState) -> dict:
    agent = PublisherAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {"channels": state.get("channels", [])})
    return {"publish_results": result}


async def analytics_node(state: WorkflowState) -> dict:
    agent = AnalyticsAgent()
    ctx = _make_context(state)
    result = await agent.run(ctx, {})
    return {"analytics_report": result}


# ─── Routing Functions ─────────────────────────────────────────

def route_after_review(state: WorkflowState) -> str:
    review = state.get("review", {})
    verdict = review.get("verdict", "rewrite")

    if verdict == "approved":
        if state.get("requires_approval"):
            return "human_gate"
        return "voice"
    else:
        # retry_count is accumulated by operator.add reducer in review_node
        # Cap at 2 retries before giving up
        if state.get("retry_count", 0) <= 2:
            return "script"
        return "end_failed"


def route_after_human_gate(state: WorkflowState) -> str:
    return "voice" if state.get("approved") else "end_rejected"


# ─── Build Graph ───────────────────────────────────────────────

def build_daily_content_graph() -> StateGraph:
    graph = StateGraph(WorkflowState)

    graph.add_node("executive", executive_node)
    graph.add_node("research", research_node)
    graph.add_node("script", script_node)
    graph.add_node("review", review_node)
    graph.add_node("voice", voice_node)
    graph.add_node("editor", editor_node)
    graph.add_node("publish", publish_node)
    graph.add_node("analytics", analytics_node)

    graph.set_entry_point("executive")
    graph.add_edge("executive", "research")
    graph.add_edge("research", "script")
    graph.add_edge("script", "review")
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "human_gate": END,   # Pause here for human approval
            "voice": "voice",
            "script": "script",
            "end_failed": END,
        },
    )
    graph.add_edge("voice", "editor")
    graph.add_edge("editor", "publish")
    graph.add_edge("publish", "analytics")
    graph.add_edge("analytics", END)

    return graph


# ─── Public Runner ─────────────────────────────────────────────

async def run_workflow(
    job_id: str,
    mission_id: str,
    mission: dict,
    brand: dict,
    channels: list[dict] | None = None,
) -> WorkflowState:
    """Run the full daily content workflow."""
    graph = build_daily_content_graph()
    compiled = graph.compile(checkpointer=MemorySaver())

    initial_state: WorkflowState = {
        "job_id": job_id,
        "mission_id": mission_id,
        "mission": mission,
        "brand": brand,
        "channels": channels or [],
        "requires_approval": mission.get("requires_approval", True),
        "approved": False,
        "executive_plan": {},
        "research_brief": {},
        "script": {},
        "review": {},
        "audio_path": "",
        "video_path": "",
        "thumbnail_path": "",
        "publish_results": {},
        "analytics_report": {},
        "error": None,
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": job_id}}
    final_state = await compiled.ainvoke(initial_state, config=config)
    return final_state
