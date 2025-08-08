from backend.config import llm
from backend.prompts import INTENT_PROMPT
from backend.models import TravelAssistantState
from backend.config import logger


async def intent_node(state: TravelAssistantState):
    logger.info("Intent user input.")
    history = state["messages"]
    message = state["messages"][-1].content

    intent_chain = (
        INTENT_PROMPT 
        | llm 
        | (lambda x: x.content.strip())
    )

    intent = await intent_chain.ainvoke({"message": message, "history": history})
    logger.info(f"Intent: {intent}")
    return {"intent": intent}