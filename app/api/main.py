from fastapi import APIRouter
from app.api.routers import devices, alarms, work_orders

api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(alarms.router)
api_router.include_router(work_orders.router)
