from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db, init_db, HCP, Interaction
from schemas import (
    HCPResponse, InteractionCreate, InteractionUpdate,
    InteractionResponse, ChatInput, AgentResponse
)
from agent import run_agent

app = FastAPI(
    title="HCP CRM API",
    description="AI-First CRM for Healthcare Professional interaction logging",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


# ── HCP Routes ──────────────────────────────────────────────

@app.get("/api/hcps", response_model=List[HCPResponse], tags=["HCPs"])
def get_all_hcps(search: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all HCPs, optionally filtered by name/speciality search."""
    query = db.query(HCP)
    if search:
        query = query.filter(
            (HCP.name.ilike(f"%{search}%")) | (HCP.speciality.ilike(f"%{search}%"))
        )
    return query.all()


@app.get("/api/hcps/{hcp_id}", response_model=HCPResponse, tags=["HCPs"])
def get_hcp(hcp_id: int, db: Session = Depends(get_db)):
    """Get a single HCP by ID."""
    hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp


# ── Interaction Routes ───────────────────────────────────────

@app.get("/api/interactions", response_model=List[InteractionResponse], tags=["Interactions"])
def get_all_interactions(
    hcp_id: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get interactions, optionally filtered by HCP."""
    query = db.query(Interaction)
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.order_by(Interaction.created_at.desc()).limit(limit).all()


@app.post("/api/interactions", response_model=InteractionResponse, tags=["Interactions"])
def create_interaction(data: InteractionCreate, db: Session = Depends(get_db)):
    """Create a new interaction via structured form (no AI)."""
    hcp = db.query(HCP).filter(HCP.id == data.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    interaction = Interaction(**data.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@app.get("/api/interactions/{interaction_id}", response_model=InteractionResponse, tags=["Interactions"])
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    """Get a single interaction by ID."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@app.put("/api/interactions/{interaction_id}", response_model=InteractionResponse, tags=["Interactions"])
def update_interaction(interaction_id: int, data: InteractionUpdate, db: Session = Depends(get_db)):
    """Update an existing interaction."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


@app.delete("/api/interactions/{interaction_id}", tags=["Interactions"])
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    """Delete an interaction."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"message": "Interaction deleted successfully"}


# ── AI Agent Route ───────────────────────────────────────────

@app.post("/api/agent/chat", response_model=AgentResponse, tags=["AI Agent"])
async def agent_chat(data: ChatInput):
    """
    Send a natural language message to the LangGraph AI agent.
    The agent will understand intent and use the appropriate tools
    (log, edit, search, suggest follow-up, analyze sentiment).
    """
    try:
        result = await run_agent(data.message)
        return AgentResponse(
            tool_used=", ".join(result["tools_used"]) if result["tools_used"] else "none",
            result={"tools_used": result["tools_used"], "message_count": result["message_count"]},
            message=result["response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ── Direct Tool Routes (for demo/testing each tool) ──────────

@app.post("/api/tools/log", tags=["Tools Demo"])
async def tool_log(data: InteractionCreate):
    """Directly demonstrate the Log Interaction tool."""
    from tools import log_interaction
    result = log_interaction.invoke({
        "hcp_id": data.hcp_id,
        "topics_discussed": data.topics_discussed or "",
        "interaction_type": data.interaction_type or "Meeting",
        "date": data.date or "",
        "time": data.time or "",
        "attendees": data.attendees or "",
        "materials_shared": data.materials_shared or "",
        "samples_distributed": data.samples_distributed or "",
        "sentiment": data.sentiment or "Neutral",
        "outcomes": data.outcomes or "",
        "follow_up_actions": data.follow_up_actions or "",
    })
    return json.loads(result)


@app.post("/api/tools/analyze-sentiment", tags=["Tools Demo"])
async def tool_sentiment(text: str, hcp_id: Optional[int] = None):
    """Directly demonstrate the Analyze Sentiment tool."""
    from tools import analyze_sentiment
    result = analyze_sentiment.invoke({"text": text, "hcp_id": hcp_id})
    return json.loads(result)


@app.get("/api/tools/suggest-followup/{hcp_id}", tags=["Tools Demo"])
async def tool_suggest(hcp_id: int, summary: str = "general meeting"):
    """Directly demonstrate the Suggest Follow-up tool."""
    from tools import suggest_followup
    result = suggest_followup.invoke({"hcp_id": hcp_id, "last_interaction_summary": summary})
    return json.loads(result)


@app.get("/api/tools/search-hcp", tags=["Tools Demo"])
async def tool_search(query: str):
    """Directly demonstrate the Search HCP Profile tool."""
    from tools import search_hcp_profile
    result = search_hcp_profile.invoke({"query": query})
    return json.loads(result)


@app.get("/", tags=["Health"])
def root():
    return {"message": "HCP CRM API is running", "docs": "/docs"}
