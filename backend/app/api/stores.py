from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.store import Store
from app.schemas.store import Store as StoreSchema, StoreCreate, StoreUpdate
from app.crud.store import store_crud

router = APIRouter()


@router.get("/", response_model=List[StoreSchema])
async def get_stores(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список магазинов."""
    return store_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=StoreSchema)
async def create_store(
    store: StoreCreate,
    db: Session = Depends(get_db)
):
    """Создать новый магазин."""
    return store_crud.create(db, obj_in=store)


@router.get("/{store_id}", response_model=StoreSchema)
async def get_store(
    store_id: str,
    db: Session = Depends(get_db)
):
    """Получить магазин по ID."""
    store = store_crud.get(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    return store


@router.put("/{store_id}", response_model=StoreSchema)
async def update_store(
    store_id: str,
    store_update: StoreUpdate,
    db: Session = Depends(get_db)
):
    """Обновить магазин."""
    store = store_crud.get(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    return store_crud.update(db, db_obj=store, obj_in=store_update)


@router.delete("/{store_id}")
async def delete_store(
    store_id: str,
    db: Session = Depends(get_db)
):
    """Удалить магазин."""
    store = store_crud.get(db, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Магазин не найден")
    store_crud.remove(db, id=store_id)
    return {"message": "Магазин удален"}