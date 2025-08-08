from fastapi import Request
from backend.models import ChatRequest
from backend.config import logger
import json

class TravelPlanningService:
    def __init__(self, agent):
        self._travel_agent = agent

    async def handle_chat_stream(self, input: ChatRequest, request: Request):
        config = {"configurable": {"thread_id": input.user_id+"@"+input.plan_id}, "recursion_limit": 15}
        yield f"data: {json.dumps({'status': 'AI 正在思考中...'}, ensure_ascii=False)}\n\n"
        try:
            async for chunk in self._travel_agent.astream(
                {"messages": [input.message]},
                config=config,
                stream_mode=["updates", "messages"],
            ):
                if await request.is_disconnected():
                    logger.warning("客戶端斷開連接，停止服務層串流。")
                    break

                # chunk: (stream_mode, output)
                if chunk[0] == "messages":
                    # ("messages", (AIMessageChunk, dict))
                    if chunk[1][1]["langgraph_node"] in ["chat", "report_itinerary"]:
                        data = {"message": {"type": "ai", "content": chunk[1][0].content}}
                        # logger.info(f'==>\n{chunk}')
                        yield f'data: {json.dumps(data, ensure_ascii=False)}\n\n'
                else:
                    # ("updates", dict)
                    data = self._get_chunk_data(chunk[1])                
                    logger.info(f'data: {json.dumps(data, ensure_ascii=False)}\n\n')
                    yield f'data: {json.dumps(data, ensure_ascii=False)}\n\n'
        except Exception as e:
            logger.error(f"服務中調用 travel_agent 時發生錯誤: {e}")
            raise ValueError(f"無法從代理程式生成計畫: {e}")
        finally:
            yield "data: [DONE]\n\n"

    # 從chunk獲取data
    def _get_chunk_data(self, chunk: dict):
        if not chunk: return
        node, state = chunk.popitem()

        message = ""
        itinerary = None
    
        # 因為data是各節點的更新state的值，有些key不存在於其他節點
        # 所以檢查key是否在state中
        if node in ["collect_preferences", "modify_plan"]:
            # 此處message不是LLM相關事件，所以在updates模式送至前端
            message = {"type": "ai", "content": state["messages"][-1].content}

            itinerary = state["planning"].current_itinerary if "planning" in state else None
            itinerary = itinerary.model_dump_json() if itinerary else None

        return {
            "node": node,
            "message": message,
            "itinerary": itinerary,
        }

    def summary():
        ...

    def export():
        ...