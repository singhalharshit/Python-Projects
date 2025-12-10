from typing import Union,Dict
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


@app.post('/addtask',response_model=TaskResponse)
def add_task(task:TaskCreate):
    task_dict = task.dict()
    task_dict['id'] = len(task_db)+1
    task_dict['is_completed'] = False
    task_db.append(task_db)
    return task_dict

@app.get('/get_tasks')
def get_all_tasks():
    return task_db

@app.get('/get_task/{owner}')
def get_task(owner:str):
    for task in task_db:
        if task['owner']==owner:
            return task
    raise HTTPException(status_code=404,detail="Task not found")

@app.put('/complete_task/{id}')
def complete_task(id:int):
    for task in task_db:
        if task['id']==id:
            task['is_completed']=True
            return task
    raise HTTPException(status_code=404,detail='Task not found')