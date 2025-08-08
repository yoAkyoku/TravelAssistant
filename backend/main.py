from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routers import travel_api
from backend.schema import Base
from backend.database import engine
from backend.config import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # 使用異步方式獲取連接並執行 DDL
        async with engine.begin() as conn: # <--- 這裡是關鍵修改
            await conn.run_sync(Base.metadata.create_all) # <--- 這裡也是關鍵修改
        logger.info("Database tables created (if not already existing).")
    except Exception as e:
        print(f"Error during database startup: {e}")
        raise # 重新拋出異常，讓 FastAPI 知道啟動失敗

    yield
    print("Application shutdown.")

app = FastAPI(lifespan=lifespan)
app.include_router(travel_api.router, prefix="/api/travel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    from backend.graph import create_graph
    graph = create_graph()

    with open("workflow.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())