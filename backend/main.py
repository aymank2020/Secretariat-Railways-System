from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

from database import engine, get_db, Base, SessionLocal
from models import User, Document, DocumentHistory
from security import hash_password, verify_password, create_access_token, decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Railways Secretariat System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: str = "user"

class DocumentCreate(BaseModel):
    doc_number: str
    doc_type: str
    subject: str
    sender: str = ""
    receiver: str = ""
    content: str = ""
    status: str = "pending"
    notes: str = ""

class DocumentUpdate(BaseModel):
    doc_number: Optional[str] = None
    doc_type: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def seed_users():
    db = SessionLocal()
    try:
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
        if db.query(User).count() == 0 and password:
            h, s = hash_password(password)
            db.add(User(username=os.getenv("INITIAL_ADMIN_USERNAME", "admin"), password_hash=h, password_salt=s, full_name="المدير", role="admin"))
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed_users()


@app.get("/")
def health():
    return {"status": "ok", "message": "نظام إدارة المراسلات - السكك الحديدية"}


@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash, user.password_salt):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}}


@app.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    h, s = hash_password(req.password)
    user = User(username=req.username, password_hash=h, password_salt=s, full_name=req.full_name, role=req.role if req.role in {"admin", "user"} else "user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}


@app.get("/documents/search")
def search_documents(q: str = Query(""), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Document)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Document.subject.like(like)) | (Document.doc_number.like(like)) |
            (Document.sender.like(like)) | (Document.receiver.like(like)) | (Document.content.like(like))
        )
    docs = query.order_by(Document.created_at.desc()).all()
    return [_doc_dict(d) for d in docs]


@app.get("/documents/")
def list_documents(doc_type: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Document)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if status:
        query = query.filter(Document.status == status)
    docs = query.order_by(Document.created_at.desc()).all()
    return [_doc_dict(d) for d in docs]


@app.post("/documents/")
def create_document(doc: DocumentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = Document(**doc.model_dump(), created_by=user.username)
    db.add(d)
    db.commit()
    db.refresh(d)
    db.add(DocumentHistory(document_id=d.id, action="created", details=f"Document created: {d.subject}", performed_by=user.username))
    db.commit()
    return _doc_dict(d)


@app.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = db.query(Document).filter(Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_dict(d)


@app.put("/documents/{doc_id}")
def update_document(doc_id: int, doc: DocumentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = db.query(Document).filter(Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    changes = []
    for field, value in doc.model_dump(exclude_unset=True).items():
        if value is not None:
            old = getattr(d, field)
            setattr(d, field, value)
            changes.append(f"{field}: {old} -> {value}")
    d.updated_at = datetime.utcnow()
    db.commit()
    if changes:
        db.add(DocumentHistory(document_id=d.id, action="updated", details="; ".join(changes), performed_by=user.username))
        db.commit()
    db.refresh(d)
    return _doc_dict(d)


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    d = db.query(Document).filter(Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(d)
    db.commit()
    return {"message": "Document deleted"}


@app.get("/documents/{doc_id}/history")
def get_document_history(doc_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    d = db.query(Document).filter(Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Document not found")
    history = db.query(DocumentHistory).filter(DocumentHistory.document_id == doc_id).order_by(DocumentHistory.performed_at.desc()).all()
    return [{"id": h.id, "document_id": h.document_id, "action": h.action, "details": h.details, "performed_by": h.performed_by, "performed_at": str(h.performed_at)} for h in history]


@app.get("/users/")
def list_users(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role, "created_at": str(u.created_at)} for u in users]


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin")
    db.delete(target)
    db.commit()
    return {"message": "User deleted"}


def _doc_dict(d):
    return {"id": d.id, "doc_number": d.doc_number, "doc_type": d.doc_type, "subject": d.subject,
            "sender": d.sender, "receiver": d.receiver, "content": d.content, "status": d.status,
            "notes": d.notes, "created_by": d.created_by, "created_at": str(d.created_at), "updated_at": str(d.updated_at)}
