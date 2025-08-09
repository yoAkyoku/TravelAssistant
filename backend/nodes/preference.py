from config import llm
from models import UserPreferencesState, UserPreferences, TravelAssistantState, CollectPreference
from prompts import PREF_PROMPT
from config import logger
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage


# 必要的欄位的詢問回覆
REQUIRED_FIELDS = [
    ("destination", "請問您想去哪個目的地？"),
    ("departure_location", "請問您的出發地是哪裡？"),
    ("departure_date", "請問您的出發日期是什麼？（YYYY‑MM‑DD）"),
    ("duration", "請問您的旅遊時間是多久？"),
    ("interests", "您這次旅行的重點是什麼？例如美食、文化、自然等等。")
]

# 多輪對話收集偏好
async def multi_turn_collector_node(state:TravelAssistantState):
    logger.info("Collect Preference.")
    user_preferences = state.get("user_preferences", UserPreferencesState())
    prefs = user_preferences["prefs"] if isinstance(user_preferences, dict) else user_preferences.prefs
    history = user_preferences["preference_history"] if isinstance(user_preferences, dict) else user_preferences.preference_history

    # 將用戶輸入添加到輸入歷史 (僅在偏好收集階段)
    user_input = state["messages"][-1]
    if isinstance(user_input, AIMessage):
        return state
        
    user_input = user_input.content
    history += "\n" + user_input
    
    chain = PREF_PROMPT | llm | PydanticOutputParser(pydantic_object=CollectPreference)
    resp = await chain.ainvoke({
        "prefs": prefs,
        "history": history
    })

    updated = resp.preferences
    updated_field = resp.updated_field

    # 進節點前有缺失，檢查經過LLM後是否所有欄位都有值
    if updated_field:
        missing = [f for f, _ in REQUIRED_FIELDS if getattr(updated, f) is None]
        if missing:
            # 追問下一個缺失欄
            ask = dict(REQUIRED_FIELDS)[missing[0]]
            return {
                "user_preferences": {
                    'prefs':updated,
                    "preference_history": history,
                    "complete": False
                },        
                "messages": [AIMessage(content=ask)]
            }

    logger.info(f"Collected prefs:\n{updated}")

    return {
        "user_preferences": {
            "prefs": updated,
            "preference_history": history,
            "complete": True
        },
        "messages": [AIMessage(content="好的，已收到您的所有偏好。為您準備行程中...")]
    }