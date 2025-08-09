from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from models import TravelAssistantState
from nodes.chat import chat_node
from nodes.intent_router import intent_node
from nodes.preference import multi_turn_collector_node
from nodes.planner import generate_itinerary_node
from nodes.modify import modify_itinerary_node
from nodes.report import report_node
from typing import Literal
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "Travel Assistant"

def create_graph():
    builder = StateGraph(TravelAssistantState)
    builder.add_node("intent_router", intent_node)
    builder.add_node("collect_preferences", multi_turn_collector_node)
    builder.add_node("generate_itinerary", generate_itinerary_node)
    builder.add_node("modify_plan", modify_itinerary_node)
    builder.add_node("report_itinerary", report_node)
    builder.add_node("chat", chat_node)

    builder.set_entry_point("intent_router")

    builder.add_conditional_edges("intent_router", 
        _intent_router, 
        {
            "chat": "chat",
            "plan_trip": "collect_preferences",
            "modify_plan": "modify_plan",
            "collect_preferences": "collect_preferences" # 在聊天中收集偏好，直到收集完畢
        }
    )

    builder.add_conditional_edges("collect_preferences", 
        lambda x: True if x.get("user_preferences") and 
                          x.get("user_preferences")["complete"] else False, 
        {
            True: "generate_itinerary",
            False: END
        }
    )

    builder.add_edge("generate_itinerary", "modify_plan")
    builder.add_edge("modify_plan", "report_itinerary")

    return builder.compile(checkpointer=MemorySaver())

def _intent_router(state: TravelAssistantState) -> Literal["chat", "plan_trip", "modify_plan", "collect_preferences"]:
    intent = state.get("intent", "chat")

    if "plan_trip" in intent:
        return "plan_trip"
    elif "modify_plan" in intent:
        return "modify_plan"
    else:
        if _prefs_collect_router(state):
            return "collect_preferences"
        return "chat"
    
def _prefs_collect_router(state: TravelAssistantState) -> bool:
    # True: 收集偏好; False: 結束graph
    prefs = state.get("user_preferences")
    if not prefs or not prefs["preference_history"]: # 沒有偏好，可能還不需要規劃，所以不需要收集
        return False
    return  not prefs["complete"] and prefs["preference_history"] # 收集偏好中 (無法中斷)