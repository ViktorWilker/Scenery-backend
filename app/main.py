from fastapi import FastAPI
from app.routers.scene import router

app = FastAPI(title = "Scenery API")
app.include_router(router)