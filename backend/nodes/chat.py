from config import llm
from models import TravelAssistantState
from prompts import CHAT_PROMPT


async def chat_node(state: TravelAssistantState):
    return {'messages': [await llm.ainvoke(
        CHAT_PROMPT.format(
            history=state['messages'],
            message=state['messages'][-1].content
        )
    )]}