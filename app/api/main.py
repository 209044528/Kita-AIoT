from fastapi import APIRouter
from app.api.routers import alarms, devices, documents, operations, work_orders

api_router = APIRouter()
api_router.include_router(devices.router)
api_router.include_router(alarms.router)
api_router.include_router(work_orders.router)
api_router.include_router(documents.router)
api_router.include_router(operations.router)
