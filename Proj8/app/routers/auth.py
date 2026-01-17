from fastapi import APIRouter
from app.db.schema.user import UserInUpdate,userCreate,userInLogin,userOutput,userWithToken


authRouter = APIRouter()

@authRouter.post("/login")
def login(login_details:userInLogin):
    return {"data":login_details}


@authRouter.post("/signup")
def signUp(signUpDetails:userCreate):
    return {"data":signUpDetails}