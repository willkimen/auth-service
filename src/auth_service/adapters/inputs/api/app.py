from fastapi import FastAPI

from auth_service.adapters.inputs.api.routers import auth_router, users_router

app = FastAPI()

app.include_router(users_router)
app.include_router(auth_router)
