import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime

from database import create_document, get_documents, db
from schemas import BlogPost

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    topic: str = Field(..., description="Topic or prompt for the blog")
    tone: str = Field("Professional", description="Writing tone")
    keywords: Optional[List[str]] = Field(default=None, description="SEO keywords list")
    length: Optional[str] = Field("medium", description="short | medium | long")
    audience: Optional[str] = Field(default=None, description="Target audience")


class GenerateResponse(BaseModel):
    id: str
    title: str
    outline: List[str]
    content: str
    topic: str
    tone: str
    keywords: List[str]
    length: Optional[str]
    audience: Optional[str]
    created_at: datetime


@app.get("/")
def read_root():
    return {"message": "AI Blog Generator Backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, 'name', 'unknown')
            try:
                response["collections"] = db.list_collection_names()[:10]
            except Exception:
                pass
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Simple, deterministic content generator (no external APIs)
def generate_outline(topic: str, length: str) -> List[str]:
    base = [
        "Introduction",
        f"Why {topic} Matters",
        f"Key Principles of {topic}",
        f"Practical Tips for {topic}",
        "Common Mistakes to Avoid",
        "Conclusion",
    ]
    if length == "short":
        return base[:4]
    if length == "long":
        return base + [f"Case Study: {topic} in Action", "Resources & Next Steps"]
    return base


def generate_title(topic: str, tone: str) -> str:
    prefix = {
        "Professional": "A Practical Guide to",
        "Friendly": "Getting Started with",
        "Technical": "In-Depth Look at",
        "Persuasive": "Why You Should Care About",
    }.get(tone, "A Practical Guide to")
    return f"{prefix} {topic}"


def generate_paragraph(heading: str, topic: str, tone: str, audience: Optional[str], keywords: List[str]) -> str:
    style = {
        "Professional": "Clear and concise",
        "Friendly": "Conversational and approachable",
        "Technical": "Detailed and precise",
        "Persuasive": "Benefit-oriented and motivating",
    }.get(tone, "Clear and concise")
    kw = ", ".join(keywords[:3]) if keywords else topic
    aud = f" for {audience}" if audience else ""
    return (
        f"{heading}: {style} overview of {topic}{aud}. "
        f"This section explores key ideas, practical insights, and examples. "
        f"Keywords to focus on: {kw}."
    )


def generate_content(topic: str, tone: str, outline: List[str], audience: Optional[str], keywords: List[str]) -> str:
    paragraphs = []
    for h in outline:
        paragraphs.append(f"## {h}\n\n" + generate_paragraph(h, topic, tone, audience, keywords) + "\n")
    return "\n".join(paragraphs)


@app.post("/api/generate", response_model=GenerateResponse)
def generate_blog(req: GenerateRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    tone = req.tone.strip() if req.tone else "Professional"
    length = (req.length or "medium").lower()
    if length not in {"short", "medium", "long"}:
        length = "medium"
    keywords = [k.strip() for k in (req.keywords or []) if k.strip()]

    outline = generate_outline(topic, length)
    title = generate_title(topic, tone)
    content = generate_content(topic, tone, outline, req.audience, keywords)

    post = BlogPost(
        title=title,
        topic=topic,
        tone=tone,
        keywords=keywords,
        outline=outline,
        content=content,
        length=length,
        audience=req.audience,
    )

    new_id = create_document("blogpost", post)

    return GenerateResponse(
        id=new_id,
        title=title,
        outline=outline,
        content=content,
        topic=topic,
        tone=tone,
        keywords=keywords,
        length=length,
        audience=req.audience,
        created_at=datetime.utcnow(),
    )


@app.get("/api/posts")
def list_posts(limit: int = 10) -> List[Dict[str, Any]]:
    docs = get_documents("blogpost", {}, limit=limit)
    # newest first if created_at exists
    try:
        docs.sort(key=lambda d: d.get("created_at", datetime.min), reverse=True)
    except Exception:
        pass
    cleaned = []
    for d in docs:
        d = dict(d)
        if d.get("_id") is not None:
            d["id"] = str(d.pop("_id"))
        cleaned.append(d)
    return cleaned


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
