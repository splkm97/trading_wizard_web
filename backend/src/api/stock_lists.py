"""Stock list management API."""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user
from src.db.database import get_db
from src.models.user import User
from src.models.stock_list import StockList

router = APIRouter(prefix="/stock-lists", tags=["stock-lists"])


class StockListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    stock_count: int
    is_default: bool = False
    created_at: str

    class Config:
        from_attributes = True


class StockListDetailResponse(StockListResponse):
    """Stock list detail response with stock codes."""

    stock_codes: list[str]


class StockListCreateRequest(BaseModel):
    """Request to create stock list from text."""

    name: str
    description: Optional[str] = None
    stock_codes: str  # Newline-separated stock codes


@router.get("", response_model=list[StockListResponse])
async def get_stock_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_

    stock_lists = (
        db.query(StockList)
        .filter(
            or_(
                StockList.user_id == current_user.id,
                StockList.is_default == True,  # noqa: E712
            )
        )
        .order_by(StockList.is_default.desc(), StockList.created_at.desc())
        .all()
    )

    return [
        StockListResponse(
            id=sl.id,
            name=sl.name,
            description=sl.description,
            stock_count=int(sl.stock_count),
            is_default=sl.is_default or False,
            created_at=sl.created_at.isoformat(),
        )
        for sl in stock_lists
    ]


@router.get("/{list_id}", response_model=StockListDetailResponse)
async def get_stock_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_

    stock_list = (
        db.query(StockList)
        .filter(
            StockList.id == list_id,
            or_(
                StockList.user_id == current_user.id,
                StockList.is_default == True,  # noqa: E712
            ),
        )
        .first()
    )

    if not stock_list:
        raise HTTPException(status_code=404, detail="Stock list not found")

    return StockListDetailResponse(
        id=stock_list.id,
        name=stock_list.name,
        description=stock_list.description,
        stock_count=int(stock_list.stock_count),
        is_default=stock_list.is_default or False,
        created_at=stock_list.created_at.isoformat(),
        stock_codes=stock_list.get_stock_codes_list(),
    )


@router.post("/upload", response_model=StockListResponse)
async def upload_stock_list(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a stock list file (txt format, one stock code per line)."""
    # Validate file type
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")

    # Read and parse file content
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            text = content.decode("euc-kr")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400, detail="Failed to decode file. Use UTF-8 or EUC-KR encoding."
            )

    # Parse stock codes
    stock_codes = _parse_stock_codes(text)

    if not stock_codes:
        raise HTTPException(status_code=400, detail="No valid stock codes found in file")

    if len(stock_codes) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 stocks allowed per list")

    # Check for duplicate name
    existing = (
        db.query(StockList)
        .filter(
            StockList.user_id == current_user.id,
            StockList.name == name,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Stock list with this name already exists")

    # Create stock list
    stock_list = StockList(
        user_id=current_user.id,
        name=name,
        description=description,
        stock_codes="\n".join(stock_codes),
        stock_count=str(len(stock_codes)),
    )

    db.add(stock_list)
    db.commit()
    db.refresh(stock_list)

    return StockListResponse(
        id=stock_list.id,
        name=stock_list.name,
        description=stock_list.description,
        stock_count=int(stock_list.stock_count),
        created_at=stock_list.created_at.isoformat(),
    )


@router.post("", response_model=StockListResponse)
async def create_stock_list(
    request: StockListCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a stock list from text input."""
    # Parse stock codes
    stock_codes = _parse_stock_codes(request.stock_codes)

    if not stock_codes:
        raise HTTPException(status_code=400, detail="No valid stock codes provided")

    if len(stock_codes) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 stocks allowed per list")

    # Check for duplicate name
    existing = (
        db.query(StockList)
        .filter(
            StockList.user_id == current_user.id,
            StockList.name == request.name,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=400, detail="Stock list with this name already exists")

    # Create stock list
    stock_list = StockList(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        stock_codes="\n".join(stock_codes),
        stock_count=str(len(stock_codes)),
    )

    db.add(stock_list)
    db.commit()
    db.refresh(stock_list)

    return StockListResponse(
        id=stock_list.id,
        name=stock_list.name,
        description=stock_list.description,
        stock_count=int(stock_list.stock_count),
        created_at=stock_list.created_at.isoformat(),
    )


@router.delete("/{list_id}")
async def delete_stock_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a stock list."""
    stock_list = (
        db.query(StockList)
        .filter(
            StockList.id == list_id,
            StockList.user_id == current_user.id,
        )
        .first()
    )

    if not stock_list:
        raise HTTPException(status_code=404, detail="Stock list not found")

    db.delete(stock_list)
    db.commit()

    return {"message": "Stock list deleted successfully"}


def _parse_stock_codes(text: str) -> list[str]:
    """Parse stock codes from text (one per line or comma-separated)."""
    # Split by newlines or commas
    lines = text.replace(",", "\n").split("\n")

    stock_codes = []
    for line in lines:
        code = line.strip()
        # Skip empty lines and comments
        if not code or code.startswith("#"):
            continue
        # Valid stock code: 6 digits
        if code.isdigit() and len(code) == 6:
            stock_codes.append(code)
        # Handle codes with .KS suffix
        elif code.endswith(".KS") and code[:-3].isdigit():
            stock_codes.append(code[:-3])

    # Remove duplicates while preserving order
    seen = set()
    unique_codes = []
    for code in stock_codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)

    return unique_codes
