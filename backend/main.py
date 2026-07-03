from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import Base, engine, get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "task-manager-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# SQLAlchemy Models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    tasks = relationship("TaskDB", back_populates="user")

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    status = Column(String, default="TODO")
    duedate = Column(Date)
    priority = Column(String, default="MEDIUM")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("UserDB", back_populates="tasks")

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: str
    status: str = "TODO"
    duedate: date
    priority: str = "MEDIUM"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    duedate: Optional[date] = None
    priority: Optional[str] = None

# Auth Endpoints
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing:
        return {"error": "Username already taken"}
    new_user = UserDB(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    return {"message": "User created"}

@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        return {"error": "Invalid username or password"}
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

# Task Endpoints
@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    current_user = db.query(UserDB).filter(UserDB.username == username).first()
    new_task = TaskDB(
        title=task.title,
        description=task.description,
        status=task.status,
        duedate=task.duedate,
        priority=task.priority,
        user_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    current_user = db.query(UserDB).filter(UserDB.username == username).first()
    return db.query(TaskDB).filter(TaskDB.user_id == current_user.id).all()

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    current_user = db.query(UserDB).filter(UserDB.username == username).first()
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not db_task:
        return {"error": "Task not found"}
    if task.title: db_task.title = task.title
    if task.description: db_task.description = task.description
    if task.status: db_task.status = task.status
    if task.duedate: db_task.duedate = task.duedate
    if task.priority: db_task.priority = task.priority
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    current_user = db.query(UserDB).filter(UserDB.username == username).first()
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not db_task:
        return {"error": "Task not found"}
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db), username: str = Depends(verify_token)):
    current_user = db.query(UserDB).filter(UserDB.username == username).first()
    tasks = db.query(TaskDB).filter(TaskDB.user_id == current_user.id).all()
    return {
        "total": len(tasks),
        "TODO": len([t for t in tasks if t.status == "TODO"]),
        "IN_PROGRESS": len([t for t in tasks if t.status == "IN_PROGRESS"]),
        "DONE": len([t for t in tasks if t.status == "DONE"])
    }