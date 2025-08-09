from langchain.agents import initialize_agent, AgentType
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage
from config import llm, logger
from models import TravelAssistantState, ItineraryPlanning
from prompts import ITINERARY_MODIFY_PROMPT
from nodes.tools import ALL_TOOLS

agent = initialize_agent(ALL_TOOLS, llm, agent=AgentType.OPENAI_MULTI_FUNCTIONS, verbose=False)

async def modify_itinerary_node(state: TravelAssistantState):
    logger.info("Modify current itinerary.")

    if not state.get("planning"):
        state["messages"].append(AIMessage(content="很抱歉無法完成您的需求，請生成規劃再嘗試。"))
        return state
    state["messages"].append(AIMessage(content="即將完成行程規劃。"))

    try:
        itinerary = state["planning"].current_itinerary
        changed_request = state["messages"][-1].content

        prompt = ITINERARY_MODIFY_PROMPT.invoke({
            "current_itinerary": itinerary,
            "itinerary_changes_requested": changed_request
        })

        # resp = await agent.arun({"input": prompt})
        # resp: {"input": input_value, "output": output_value}
        # agent.arun(prompt) => 
        resp = await agent.arun(prompt)
        new_itinerary = PydanticOutputParser(pydantic_object=ItineraryPlanning).invoke(resp)
        state["planning"].current_itinerary = new_itinerary
    except Exception as e:
        logger.error(f"行程格式錯誤: {e}")
        state["messages"].append(AIMessage(content="行程調整失敗，請再嘗試。"))

    return state