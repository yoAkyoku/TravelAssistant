from langchain_core.runnables import RunnableParallel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage
from backend.config import llm, logger
from backend.models import TravelAssistantState, PlanningState, ItineraryPlanning
from backend.prompts import ITINERARY_PLANNER_PROMPT, ITINERARY_MERGE_PROMPT
import operator

async def planning_draft(state: TravelAssistantState):
    """
    Agent for planning travel itineraries based on user preferences.
    """
    logger.info("Planning itinerary drafts.")
    
    prefs = state.get("user_preferences")["prefs"]

    chain = (
        RunnableParallel(
            prefs=operator.itemgetter("prefs"),
            theme=operator.itemgetter("theme")
        )
        | ITINERARY_PLANNER_PROMPT
        | llm
        | PydanticOutputParser(pydantic_object=ItineraryPlanning)
    )

    default_themes = ["美食", "文化", "自然"]
    themes = prefs.interests if prefs and prefs.interests else default_themes
    inputs = []
    for theme in themes:
        inputs.append({"prefs": prefs, "theme": theme})

    drafts = await chain.abatch(inputs)

    if not state.get("planning", None):
        state["planning"] = PlanningState()

    state["planning"].planning_options = drafts
    logger.info(f"\n===Before merge===\n {drafts}")

    return state

async def merge_draft(state: TravelAssistantState):
    """
    Merge multiple drafts into a single itinerary.
    """
    logger.info("Merging itinerary drafts.")
    prefs = state.get("user_preferences")["prefs"]
    options = state["planning"].planning_options
    if not options:
        logger.warning("No planning options available to merge.")
        return state
    
    merged_draf = None
    if len(options) > 1:        
        drafts = "\n---\n".join([f"第{i}個草案:\n{item}" for i, item in enumerate(options, 1)])

        chain =  (
            ITINERARY_MERGE_PROMPT
            | llm
            | PydanticOutputParser(pydantic_object=ItineraryPlanning)
        )
        
        merged_draf = await chain.ainvoke({"prefs": prefs, "drafts": drafts})
    else:
        merged_draf = options[0]

    state["planning"].current_itinerary = merged_draf
    state["messages"].append(AIMessage(content="調整行程住宿"))
    logger.info(f"\n===After merge===\n {merged_draf}")

    return state

async def generate_itinerary_node(state: TravelAssistantState):
    state = await planning_draft(state)
    state = await merge_draft(state)
    return state