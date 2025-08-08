from backend.config import llm
from backend.models import TravelAssistantState
from backend.prompts import CHAT_PROMPT


async def chat_node(state: TravelAssistantState):
    return {'messages': [await llm.ainvoke(
        CHAT_PROMPT.format(
            history=state['messages'],
            message=state['messages'][-1].content
        )
    )]}