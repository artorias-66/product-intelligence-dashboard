"""Pydantic v2 schemas for all API request/response models."""

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


# ─── Job Schemas ────────────────────────────────────────────────────────────────

class JobBase(BaseModel):
    type: str
    file_name: Optional[str] = None
    enhance_titles: bool = False

class JobCreate(JobBase):
    pass

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    status: str
    progress: int
    file_name: Optional[str] = None
    enhance_titles: bool
    total_products: int
    processed_products: int
    error_message: Optional[str] = None
    draft_data: Optional[Any] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# ─── Product Issue Schemas ──────────────────────────────────────────────────────

class ProductIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    issue_type: str
    severity: str
    message: str
    suggested_fix: Optional[str] = None
    created_at: datetime


# ─── Enhanced Title Schemas ─────────────────────────────────────────────────────

class EnhancedTitleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    original_title: Optional[str] = None
    extracted_attributes: Optional[Any] = None
    suggested_keywords: Optional[Any] = None
    enhanced_title: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

class EnhanceTitleRequest(BaseModel):
    category: Optional[str] = None
    brand: Optional[str] = None
    attributes: Optional[dict] = None


# ─── Competitor Price Schemas ───────────────────────────────────────────────────

class CompetitorPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    sku_id: str
    platform: str
    product_name: Optional[str] = None
    competitor_url: Optional[str] = None
    competitor_price: float
    currency: str
    last_checked_at: datetime
    created_at: datetime

class CompetitorPriceUploadResponse(BaseModel):
    message: str
    total_uploaded: int
    product_id: uuid.UUID


# ─── Price History Schemas ──────────────────────────────────────────────────────

class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    platform: str
    price: float
    checked_at: datetime


# ─── Alert Schemas ──────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    type: str
    severity: str
    title: str
    message: Optional[str] = None
    is_read: bool
    created_at: datetime

class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    unread_count: int

class AlertRuleCreate(BaseModel):
    type: str = Field(..., description="Alert type: price_drop, listing_issue, competitor_price")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    title: str
    message: Optional[str] = None
    product_id: Optional[uuid.UUID] = None

class AlertMarkReadRequest(BaseModel):
    alert_ids: list[uuid.UUID]


# ─── Product Schemas ───────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    sku_id: str
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None

class ProductUpdate(BaseModel):
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    sku_id: str
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    availability: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class ProductDetailResponse(ProductResponse):
    issues: list[ProductIssueResponse] = []
    enhanced_titles: list[EnhancedTitleResponse] = []
    competitor_prices: list[CompetitorPriceResponse] = []

class ProductListResponse(BaseModel):
    products: list[ProductResponse]
    total: int
    page: int
    page_size: int


# ─── Dashboard Schemas ──────────────────────────────────────────────────────────

class IssueSeverityCount(BaseModel):
    severity: str
    count: int

class IssueTypeCount(BaseModel):
    issue_type: str
    count: int

class QualityDistribution(BaseModel):
    range_label: str
    count: int

class QualitySummaryResponse(BaseModel):
    total_products: int
    average_quality_score: float
    products_with_issues: int
    total_issues: int
    issues_by_severity: list[IssueSeverityCount]
    issues_by_type: list[IssueTypeCount]
    quality_distribution: list[QualityDistribution]
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int


# ─── Upload Schemas ─────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    job_id: uuid.UUID
    message: str
    status: str


# ─── Video Extraction Schemas ───────────────────────────────────────────────────

class VideoExtractionResult(BaseModel):
    sku_id: str
    product_title: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    mrp: Optional[float] = None
    image_url: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None


# ─── Generic Schemas ────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
