from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from models import ChatRequest, ItineraryPlanning, PlanResponse, PlanUpdate
from graph import create_graph
from services.planning_service import TravelPlanningService
from config import logger
from schema import Plan, PlanDay, PlanSegment, Activity, Accommodation
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List

_travel_agent = None

@asynccontextmanager
async def lifespan(app: APIRouter):
    global _travel_agent
    logger.info("[Planning Router Lifespan] 啟動中: 初始化 TravelPlannerAgnet...")
    try:
        _travel_agent = create_graph()
        logger.info("[Planning Router Lifespan] TravelPlannerAgnet 初始化完成。")
        yield
    finally:
        logger.info("[Planning Router Lifespan] 關閉中：清理 TravelPlannerAgent 資源...")
        _travel_agent = None
        logger.info("[Planning Router Lifespan] TravelPlannerAgent 資源清理完成。")

router = APIRouter(lifespan=lifespan)

async def get_travel_agent():
    if not _travel_agent:
        raise HTTPException(status_code=503, detail="服務正在啟動中，旅行代理程式尚未準備好。")
    return _travel_agent

async def get_travel_service(agent = Depends(get_travel_agent)):
    return TravelPlanningService(agent)

@router.post("/chat/stream")
async def chat(
    input: ChatRequest, 
    request: Request,
    planning_service:TravelPlanningService = Depends(get_travel_service)
):
    try:
        event_generator = planning_service.handle_chat_stream(input, request)
        return StreamingResponse(event_generator, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"API 路由 /api/travel/chat/stream 發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(plan_data: ItineraryPlanning, db: Session = Depends(get_db)):
    """創建一個新的旅遊計畫及其所有相關的每日行程、時間段、活動和住宿。"""
    logger.info(plan_data)
    try:
        plan = Plan(
            travel_theme=plan_data.travel_theme,
            departure_location=plan_data.departure_location,
            destination=plan_data.destination,
            num_peoples=plan_data.num_peoples,
            duration=plan_data.duration,
            start_date=plan_data.start_date,
            end_date=plan_data.end_date,
            features=plan_data.features
        )
        db.add(plan)
        await db.flush()

        for day_data in plan_data.days:
            plan_day = PlanDay(
                plan_id=plan.id,
                daily_theme=day_data.daily_theme,
                itinerary_location=day_data.itinerary_location,
                date=day_data.date,
                transportation=day_data.transportation
            )
            db.add(plan_day)
            await db.flush()

            for seg_data in day_data.segments:
                segment = PlanSegment(
                    day_id=plan_day.id,
                    time_slot=seg_data.time_slot
                )
                db.add(segment)
                await db.flush()

                for act_data in seg_data.activities:
                    activity = Activity(
                        segment_id=segment.id,
                        activity_name=act_data.activity_name,
                        type=act_data.type,
                        activity_location=act_data.activity_location,
                        description=act_data.description,
                        estimated_duration=act_data.estimated_duration,
                        notes=act_data.notes
                    )
                    db.add(activity)

            if day_data.accommodation:
                acc_data = day_data.accommodation
                accommodation = Accommodation(
                    day_id=plan_day.id,
                    hotel_id=acc_data.hotel_id,
                    name=acc_data.name,
                    url=acc_data.url,
                    address=acc_data.address,
                    price=acc_data.price,
                    currency=acc_data.currency,
                    review_score=acc_data.review_score,
                    review_count=acc_data.review_count,
                    arrival_date=acc_data.arrival_date,
                    departure_date=acc_data.departure_date
                )
                db.add(accommodation)

        await db.commit()
        await db.refresh(
            plan,
            attribute_names=["days"], # 刷新 Plan 的 'days' 關係
            with_for_update=None # 防止加鎖
        )

        result = await db.execute(
            select(Plan)
            .options(
                selectinload(Plan.days)
                    .selectinload(PlanDay.segments)
                    .selectinload(PlanSegment.activities),
                selectinload(Plan.days)
                    .selectinload(PlanDay.accommodation)
            )
            .filter(Plan.id == plan.id)
        )
        loaded_plan = result.scalars().first()

        return loaded_plan

    except Exception as e:
        db.rollback()
        logger.error(f"創建計畫時發生錯誤: {e}")
        raise HTTPException(status_code=400, detail=f"創建計畫失敗: {e}")

# @router.put("/plans/{plan_id}", response_model=PlanResponse)
# async def update_plan(plan_id: int, plan_data: ItineraryPlanning, db: Session = Depends(get_db)):
#     """更新現有的旅遊計畫及其所有相關的每日行程、時間段、活動和住宿。"""
#     plan = db.query(Plan).filter_by(id=plan_id).first()
#     if not plan:
#         raise HTTPException(status_code=404, detail="Plan not found")

#     try:
#         # 更新主表 Plan 的欄位
#         for field, value in plan_data.model_dump(exclude_unset=True).items():
#             if field != "days": # days 另外處理
#                 setattr(plan, field, value)

#         # 清除現有的相關聯資料
#         day_ids = [d.id for d in plan.days]
#         if day_ids:
#             # 刪除 Accommodation (如果 day_id 在 day_ids 中)
#             db.query(Accommodation).filter(Accommodation.day_id.in_(day_ids)).delete(synchronize_session=False)
            
#             segment_ids = [s.id for d in plan.days for s in d.segments]
#             if segment_ids:
#                 # 刪除 Activity (如果 segment_id 在 segment_ids 中)
#                 db.query(Activity).filter(Activity.segment_id.in_(segment_ids)).delete(synchronize_session=False)
#                 # 刪除 PlanSegment (如果 day_id 在 day_ids 中)
#                 db.query(PlanSegment).filter(PlanSegment.day_id.in_(day_ids)).delete(synchronize_session=False)
            
#             # 刪除 PlanDay
#             db.query(PlanDay).filter(PlanDay.plan_id == plan.id).delete(synchronize_session=False)

#         db.flush() # 確保刪除操作在新增之前完成

#         # 儲存新的 PlanDay、PlanSegment、Activity 和 Accommodation 條目
#         for day_data in plan_data.days:
#             plan_day = PlanDay(
#                 plan_id=plan.id,
#                 daily_theme=day_data.daily_theme,
#                 itinerary_location=day_data.itinerary_location,
#                 date=day_data.date,
#                 transportation=day_data.transportation
#             )
#             db.add(plan_day)
#             db.flush() # 提前取得 plan_day.id

#             for seg_data in day_data.segments:
#                 segment = PlanSegment(
#                     day_id=plan_day.id,
#                     time_slot=seg_data.time_slot
#                 )
#                 db.add(segment)
#                 db.flush() # 提前取得 segment.id

#                 for act_data in seg_data.activities:
#                     activity = Activity(
#                         segment_id=segment.id,
#                         activity_name=act_data.activity_name,
#                         type=act_data.type,
#                         activity_location=act_data.activity_location,
#                         description=act_data.description,
#                         estimated_duration=act_data.estimated_duration,
#                         notes=act_data.notes
#                     )
#                     db.add(activity)

#             if day_data.accommodation:
#                 acc_data = day_data.accommodation
#                 accommodation = Accommodation(
#                     day_id=plan_day.id,
#                     hotel_id=acc_data.hotel_id,
#                     name=acc_data.name,
#                     url=acc_data.url,
#                     address=acc_data.address,
#                     price=acc_data.price,
#                     currency=acc_data.currency,
#                     review_score=acc_data.review_score,
#                     review_count=acc_data.review_count,
#                     arrival_date=acc_data.arrival_date,
#                     departure_date=acc_data.departure_date
#                 )
#                 db.add(accommodation)

#         db.commit()
#         # 重新查詢並載入所有關聯資料以確保響應是最新的狀態
#         updated_plan = db.query(Plan).options(
#             joinedload(Plan.days).joinedload(PlanDay.segments).joinedload(PlanSegment.activities),
#             joinedload(Plan.days).joinedload(PlanDay.accommodation)
#         ).filter(Plan.id == plan_id).first()

#         return updated_plan

#     except Exception as e:
#         db.rollback()
#         logger.error(f"更新計畫 {plan_id} 時發生錯誤: {e}")
#         raise HTTPException(status_code=400, detail=f"更新計畫失敗: {e}")

@router.patch("/plans/{plan_id}/status", response_model=PlanResponse)
async def update_plan_status(
    plan_id: int,
    update_data: PlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新指定旅遊計畫的屬性，包括狀態和/或行程細節。
    """
    # 載入所有層級的關係，以便更新或替換
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.days)
                    .selectinload(PlanDay.segments)
                    .selectinload(PlanSegment.activities),
                 selectinload(Plan.days)
                    .selectinload(PlanDay.accommodation))
        .filter_by(id=plan_id)
    )
    plan = result.scalars().first()

    if not plan:
        logger.warning(f"計畫 {plan_id} 未找到，無法更新。")
        raise HTTPException(status_code=404, detail="Plan not found")

    try:
        # 更新頂層屬性
        update_dict = update_data.model_dump(exclude_unset=True) # 只獲取有設置的字段
        for key, value in update_dict.items():
            if key != "days": # days 需要單獨處理
                setattr(plan, key, value)
        
        # 處理巢狀的 days (行程細節) 的更新
        if update_data.days is not None:
            # 策略：完全替換現有的 days
            # 由於 cascade="all, delete-orphan", 移除舊的會自動刪除數據庫中的記錄
            plan.days.clear() # 清空現有的 days 關係

            for day_data in update_data.days:
                new_day = PlanDay(
                    daily_theme=day_data.daily_theme,
                    itinerary_location=day_data.itinerary_location,
                    day=day_data.day,
                    transportation=day_data.transportation
                )
                for segment_data in day_data.segments:
                    new_segment = PlanSegment(
                        time_slot=segment_data.time_slot
                    )
                    for activity_data in segment_data.activities:
                        new_segment.activities.append(Activity(**activity_data.model_dump()))
                    new_day.segments.append(new_segment)
                
                if day_data.accommodation:
                    new_day.accommodation = Accommodation(**day_data.accommodation.model_dump())
                
                plan.days.append(new_day) # 添加新的 days

        db.add(plan) # 標記為待更新 (雖然通常不是必須，但安全起見)
        await db.commit() # 提交更改
        await db.refresh(plan) # 重新整理，確保獲取所有最新狀態
        logger.info(f"計畫 {plan_id} 更新成功。")
        result = await db.execute(
            select(Plan)
            .options(selectinload(Plan.days)
                        .selectinload(PlanDay.segments)
                        .selectinload(PlanSegment.activities),
                    selectinload(Plan.days)
                        .selectinload(PlanDay.accommodation))
            .filter_by(id=plan_id)
        )
        plan = result.scalars().first()
        return plan
    except Exception as e:
        await db.rollback()
        logger.error(f"更新計畫 {plan_id} 狀態時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新計畫狀態失敗: {e}")

@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """根據 ID 獲取一個旅遊計畫及其所有相關的每日行程、時間段、活動和住宿。"""
    # 使用 joinedload 預先載入所有關聯的資料，避免 N+1 查詢問題
    result = await db.execute(
        select(Plan)
        .options(
            joinedload(Plan.days).joinedload(PlanDay.segments).joinedload(PlanSegment.activities),
            joinedload(Plan.days).joinedload(PlanDay.accommodation)
        )
        .filter(Plan.id == plan_id)
    )
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.get("/plans", response_model=List[PlanResponse])
async def get_all_plans(db: Session = Depends(get_db)):
    """獲取所有旅遊計畫的列表。"""
    result = await db.execute(
        select(Plan)
        .options(
            joinedload(Plan.days).joinedload(PlanDay.segments).joinedload(PlanSegment.activities),
            joinedload(Plan.days).joinedload(PlanDay.accommodation)
        )
    )
    plans = result.scalars().unique().all()
    return plans

@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """根據 ID 刪除一個旅遊計畫及其所有相關的子實體。"""
    try:
        # 只選擇 Plan 物件，不需要預加載所有子關係，因為 cascade 會處理刪除
        result = await db.execute(select(Plan).filter_by(id=plan_id))
        plan = result.scalars().first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        await db.delete(plan)
        await db.commit()
        return {} # 返回空響應表示成功刪除
    except Exception as e:
        await db.rollback()
        logger.error(f"刪除計畫 {plan_id} 時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"刪除計畫失敗: {e}")