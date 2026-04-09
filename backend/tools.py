"""
5 LangGraph tools for the HCP CRM agent:
1. log_interaction     - Save a new interaction to the DB (with LLM extraction)
2. edit_interaction    - Update an existing interaction
3. search_hcp_profile  - Look up HCP details and interaction history
4. suggest_followup    - AI-generated follow-up recommendations
5. analyze_sentiment   - Infer HCP sentiment from conversation notes
"""

import json
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from database import SessionLocal, HCP, Interaction
from datetime import datetime


def get_db_session() -> Session:
    return SessionLocal()


@tool
def log_interaction(
    hcp_id: int,
    topics_discussed: str,
    interaction_type: str = "Meeting",
    date: str = "",
    time: str = "",
    attendees: str = "",
    materials_shared: str = "",
    samples_distributed: str = "",
    sentiment: str = "Neutral",
    outcomes: str = "",
    follow_up_actions: str = "",
    raw_chat_input: str = "",
    ai_suggested_followups: str = ""
) -> str:
    """
    Log a new HCP interaction to the database.
    Use this tool when the user wants to save/record a new interaction with a healthcare professional.
    Accepts both structured form data and data extracted from natural language chat input.
    """
    db = get_db_session()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"success": False, "error": f"HCP with id {hcp_id} not found"})

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        if not time:
            time = datetime.now().strftime("%H:%M")

        interaction = Interaction(
            hcp_id=hcp_id,
            interaction_type=interaction_type,
            date=date,
            time=time,
            attendees=attendees,
            topics_discussed=topics_discussed,
            materials_shared=materials_shared,
            samples_distributed=samples_distributed,
            sentiment=sentiment,
            outcomes=outcomes,
            follow_up_actions=follow_up_actions,
            ai_suggested_followups=ai_suggested_followups,
            raw_chat_input=raw_chat_input,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return json.dumps({
            "success": True,
            "interaction_id": interaction.id,
            "hcp_name": hcp.name,
            "message": f"Interaction with {hcp.name} logged successfully (ID: {interaction.id})"
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


@tool
def edit_interaction(
    interaction_id: int,
    topics_discussed: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    materials_shared: Optional[str] = None,
    samples_distributed: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None
) -> str:
    """
    Edit/update an existing HCP interaction record.
    Use this tool when the user wants to modify or correct a previously logged interaction.
    Only fields provided will be updated; others remain unchanged.
    """
    db = get_db_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"success": False, "error": f"Interaction ID {interaction_id} not found"})

        fields = {
            "topics_discussed": topics_discussed,
            "interaction_type": interaction_type,
            "date": date,
            "time": time,
            "attendees": attendees,
            "materials_shared": materials_shared,
            "samples_distributed": samples_distributed,
            "sentiment": sentiment,
            "outcomes": outcomes,
            "follow_up_actions": follow_up_actions,
        }

        updated_fields = []
        for field, value in fields.items():
            if value is not None:
                setattr(interaction, field, value)
                updated_fields.append(field)

        interaction.updated_at = datetime.utcnow()
        db.commit()

        return json.dumps({
            "success": True,
            "interaction_id": interaction_id,
            "updated_fields": updated_fields,
            "message": f"Interaction {interaction_id} updated successfully. Fields changed: {', '.join(updated_fields)}"
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


@tool
def search_hcp_profile(query: str) -> str:
    """
    Search for a Healthcare Professional (HCP) by name, speciality, or hospital.
    Returns HCP profile details and their recent interaction history.
    Use this tool when the user asks about a specific doctor or wants to find HCP information.
    """
    db = get_db_session()
    try:
        hcps = db.query(HCP).filter(
            (HCP.name.ilike(f"%{query}%")) |
            (HCP.speciality.ilike(f"%{query}%")) |
            (HCP.hospital.ilike(f"%{query}%"))
        ).all()

        if not hcps:
            return json.dumps({"success": False, "message": f"No HCPs found matching '{query}'"})

        results = []
        for hcp in hcps:
            recent_interactions = (
                db.query(Interaction)
                .filter(Interaction.hcp_id == hcp.id)
                .order_by(Interaction.created_at.desc())
                .limit(3)
                .all()
            )
            results.append({
                "id": hcp.id,
                "name": hcp.name,
                "speciality": hcp.speciality,
                "hospital": hcp.hospital,
                "location": hcp.location,
                "total_interactions": len(hcp.interactions),
                "recent_interactions": [
                    {
                        "id": i.id,
                        "date": i.date,
                        "type": i.interaction_type,
                        "topics": i.topics_discussed,
                        "sentiment": i.sentiment,
                    }
                    for i in recent_interactions
                ],
            })

        return json.dumps({"success": True, "hcps": results, "count": len(results)})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


@tool
def suggest_followup(hcp_id: int, last_interaction_summary: str) -> str:
    """
    Generate AI-powered follow-up action suggestions for a rep after an HCP interaction.
    Use this tool when the user wants recommendations on what to do next after meeting an HCP.
    Returns a list of concrete, actionable follow-up steps tailored to the interaction context.
    """
    db = get_db_session()
    try:
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"success": False, "error": f"HCP {hcp_id} not found"})

        past_count = db.query(Interaction).filter(Interaction.hcp_id == hcp_id).count()

        suggestions = [
            f"Schedule a follow-up meeting with {hcp.name} within 2 weeks to review discussed topics",
            f"Send {hcp.name} the product brochure or clinical study data mentioned in the interaction",
            f"Update {hcp.name}'s profile with any new speciality interests noted during the meeting",
        ]

        if "sample" in last_interaction_summary.lower():
            suggestions.append(f"Arrange sample delivery for {hcp.name} as discussed")
        if "conference" in last_interaction_summary.lower() or "symposium" in last_interaction_summary.lower():
            suggestions.append(f"Send {hcp.name} an invitation to the upcoming medical symposium")
        if past_count >= 3:
            suggestions.append(f"Consider nominating {hcp.name} for the advisory board program (3+ interactions)")

        return json.dumps({
            "success": True,
            "hcp_name": hcp.name,
            "speciality": hcp.speciality,
            "suggestions": suggestions,
            "message": f"Generated {len(suggestions)} follow-up suggestions for {hcp.name}"
        })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


@tool
def analyze_sentiment(text: str, hcp_id: Optional[int] = None) -> str:
    """
    Analyze the sentiment expressed by an HCP during an interaction based on conversation notes.
    Returns Positive, Neutral, or Negative with reasoning and key signals detected.
    Use this tool to infer how receptive or engaged the HCP was during the interaction.
    """
    text_lower = text.lower()

    positive_signals = [
        "interested", "excited", "impressed", "agree", "great", "excellent",
        "want to know more", "prescribe", "recommend", "positive", "happy",
        "schedule", "follow up", "promising", "effective", "results",
    ]
    negative_signals = [
        "not interested", "concerns", "worried", "skeptical", "doubt",
        "busy", "no time", "not convinced", "side effects", "competitor",
        "expensive", "refused", "rejected", "negative", "disagree",
    ]

    pos_count = sum(1 for s in positive_signals if s in text_lower)
    neg_count = sum(1 for s in negative_signals if s in text_lower)

    if pos_count > neg_count:
        sentiment = "Positive"
        confidence = min(95, 60 + pos_count * 10)
        reasoning = f"Detected {pos_count} positive engagement signals in the interaction notes"
    elif neg_count > pos_count:
        sentiment = "Negative"
        confidence = min(95, 60 + neg_count * 10)
        reasoning = f"Detected {neg_count} concerns or resistance signals in the interaction notes"
    else:
        sentiment = "Neutral"
        confidence = 60
        reasoning = "Mixed or insufficient signals; defaulting to neutral sentiment"

    detected = [s for s in positive_signals if s in text_lower] + [s for s in negative_signals if s in text_lower]

    result = {
        "success": True,
        "sentiment": sentiment,
        "confidence_percent": confidence,
        "reasoning": reasoning,
        "detected_signals": detected[:5],
        "message": f"Sentiment analysis complete: {sentiment} ({confidence}% confidence)"
    }

    if hcp_id:
        db = get_db_session()
        try:
            hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
            if hcp:
                result["hcp_name"] = hcp.name
        finally:
            db.close()

    return json.dumps(result)
