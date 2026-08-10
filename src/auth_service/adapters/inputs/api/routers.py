from fastapi import APIRouter

users_router = APIRouter(prefix='/api/v1/users', tags=['users'])
auth_router = APIRouter(prefix='/api/v1/auth', tags=['auth'])
