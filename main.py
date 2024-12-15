"""No missing module docstring""" 
 
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey 
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import relationship, sessionmaker 
from sqlalchemy.orm import Session 
from fastapi import FastAPI, Depends, HTTPException 
from pydantic import BaseModel 
from typing import List 
 
Base = declarative_base() 
 
class User(Base): 
 __tablename__ = 'users' 
id = Column(Integer, primary_key=True, autoincrement=True) 
username = Column(String, unique=True, nullable=False) 
email = Column(String, unique=True, nullable=False) 
password = Column(String, nullable=False) 
posts = relationship("Post", back_populates="user") 
 
class Post(Base): 
    __tablename__ = 'posts' 
id = Column(Integer, primary_key=True, autoincrement=True) 
title = Column(String, nullable=False) 
content = Column(Text, nullable=False) 
user_id = Column(Integer, ForeignKey('users.id'), nullable=False) 
user = relationship("User", back_populates="posts") 
 
DATABASE_URL = "postgresql://postgres:localhost/8lab" 
 
engine = create_engine(DATABASE_URL) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 
 
Base.metadata.create_all(bind=engine) 
 
session = SessionLocal() 
 
users = [ 
    User(username="u1", email="u1@mail.ru", password="12345"), 
    User(username="u2", email="u2@mail.ru", password="67890") 
] 
session.add_all(users) 
session.commit() 
 
posts = [ 
    Post(title="p1", content="blabla", user_id=1), 
    Post(title="p2", content="pupupu", user_id=2) 
] 
session.add_all(posts) 
session.commit() 
session.close() 
 
users = session.query(User).all() # Извлечение всех записей из Users 
for user in users: 
    print(user.username, user.email) 
 
posts = session.query(Post).join(User).all() # Извлечение записей из Posts, включая информацию о Users 
for post in posts: 
    print(post.title, post.content, post.user.username) # Извлечение записей из Posts, созданные конкретным пользователем 
 
user_posts = session.query(Post).filter(Post.user_id == 1).all() 
for post in user_posts: 
    print(post.title, post.content) 
 
user = session.query(User).filter(User.id == 1).first() # Обновление email у пользователя 
user.email = "new@mail.ru" 
session.commit() 
 
post = session.query(Post).filter(Post.id == 1).first() # Обновление content у поста 
post.content = "Update" 
session.commit() 
 
post = session.query(Post).filter(Post.id == 1).first() # Удаление поста 
session.delete(post) 
session.commit() 
 
user = session.query(User).filter(User.id == 2).first() # Удаление пользователя и всех его постов 
session.delete(user) 
session.commit() 
 
app = FastAPI() 
 
def get_db(): 
    db = SessionLocal() 
    try: yield db 
    finally: db.close() 
 
class UserCreate(BaseModel): 
    username: str 
    email: str 
    password: str 
 
class PostCreate(BaseModel): 
    title: str 
    content: str 
    user_id: int 
 
"/users/", response_model=UserCreate 
def create_user(user: UserCreate, db: Session = Depends(get_db)):  
    db_user = User(**user.dict()) 
    db.add(db_user) 
    db.commit() 
    db.refresh(db_user) 
    return db_user 
 
@app.get("/users/", response_model=List[UserCreate]) 
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)): 
    users = db.query(User).offset(skip).limit(limit).all() 
    return users 
 
"/posts/", response_model=PostCreate 
def create_post(post: PostCreate, db: Session = Depends(get_db)): 
    db_post = Post(**post.dict()) 
    db.add(db_post) 
    db.commit() 
    db.refresh(db_post) 
    return db_post 
 
@app.get("/posts/", response_model=List[PostCreate]) 
def read_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):  
    posts = db.query(Post).offset(skip).limit(limit).all() 
    return posts

@app.put("/users/{user_id}", response_model=UserCreate) 
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):  
    db_user = db.query(User).filter(User.id == user_id).first() 
    if db_user is None: 
        raise HTTPException(status_code=404, detail="User not found") 
    for key, value in user.dict().items(): 
        setattr(db_user, key, value) 
        db.commit() 
        db.refresh(db_user) 
    return db_user 
 
@app.put("/posts/{post_id}", response_model=PostCreate) 
def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db)): 
    db_post = db.query(Post).filter(Post.id == post_id).first() 
    if db_post is None: 
        raise HTTPException(status_code=404, detail="Post not found") 
    for key, value in post.dict().items(): 
        setattr(db_post, key, value) 
        db.commit() 
        db.refresh(db_post) 
    return db_post 
 
@app.delete("/users/{user_id}", response_model=UserCreate) 
def delete_user(user_id: int, db: Session = Depends(get_db)):  
    db_user = db.query(User).filter(User.id == user_id).first() 
    if db_user is None: 
        raise HTTPException(status_code=404, detail="User not found") 
    db.delete(db_user) 
    db.commit() 
    return db_user 
 
@app.delete("/posts/{post_id}", response_model=PostCreate) 
def delete_post(post_id: int, db: Session = Depends(get_db)):  
    db_post = db.query(Post).filter(Post.id == post_id).first() 
    if db_post is None: 
        raise HTTPException(status_code=404, detail="Post not found") 
    db.delete(db_post) 
    db.commit() 
    return db_post