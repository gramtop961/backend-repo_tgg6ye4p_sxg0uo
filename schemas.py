"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")


class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")


class BlogPost(BaseModel):
    """
    AI-generated blog posts
    Collection name: "blogpost"
    """
    title: str = Field(..., description="Generated blog title")
    topic: str = Field(..., description="User provided topic or prompt")
    tone: str = Field(..., description="Writing tone, e.g., Professional, Friendly, Technical")
    keywords: List[str] = Field(default_factory=list, description="Optional SEO keywords")
    outline: List[str] = Field(default_factory=list, description="Section headings for the post")
    content: str = Field(..., description="Full generated article content in Markdown")
    length: Optional[str] = Field(None, description="Requested length: short, medium, long")
    audience: Optional[str] = Field(None, description="Target audience if provided")
    status: str = Field("generated", description="Status of the post")
