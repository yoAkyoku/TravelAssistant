from langchain_core.messages import AIMessage
from backend.prompts import ITINERARY_REPORT_PROMPT
from backend.models import TravelAssistantState
from backend.config import llm, logger

async def report_node(state: TravelAssistantState):
    logger.info("Report itinerary.")
    if not state.get("planning"):
        return state
    
    itinerary = state["planning"].current_itinerary

    report = await llm.ainvoke(
        ITINERARY_REPORT_PROMPT.format(
            intent=state["intent"],
            itinerary=itinerary
        )
    )
    logger.info(f"Report: \n{report}")
    return {"messages": [report]}
