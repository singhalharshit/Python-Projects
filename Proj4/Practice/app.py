from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

app = FastAPI()


task_db = []


class TaskCreate(BaseModel):
    title:str
    description:str
    owner:str


class TaskResponse(TaskCreate):
    id:int
    is_completed:bool
    