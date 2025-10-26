from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.game import Game
from app.schemas.game import Game as GameSchema, GameCreate, GameUpdate
from app.crud.game import game_crud

router = APIRouter()


@router.get("/", response_model=List[GameSchema])
async def get_games(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список игр с пагинацией и поиском."""
    if search:
        return game_crud.search(db, search, skip=skip, limit=limit)
    return game_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=GameSchema)
async def create_game(
    game: GameCreate,
    db: Session = Depends(get_db)
):
    """Создать новую игру."""
    return game_crud.create(db, obj_in=game)


@router.get("/{game_id}", response_model=GameSchema)
async def get_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Получить игру по ID."""
    game = game_crud.get(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return game


@router.put("/{game_id}", response_model=GameSchema)
async def update_game(
    game_id: str,
    game_update: GameUpdate,
    db: Session = Depends(get_db)
):
    """Обновить игру."""
    game = game_crud.get(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return game_crud.update(db, db_obj=game, obj_in=game_update)


@router.delete("/{game_id}")
async def delete_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Удалить игру."""
    game = game_crud.get(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    game_crud.remove(db, id=game_id)
    return {"message": "Игра удалена"}