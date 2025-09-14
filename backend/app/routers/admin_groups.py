from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from .admin_base import admin_token_required
from ..utils import list_groups, save_group, delete_group, get_group

router = APIRouter(prefix="/api/admin/groups", tags=["admin:groups"])

Op = Literal["mul", "add", "sub", "div"]

class GroupItem(BaseModel):
    name: str = Field(min_length=1)
    op: Op = "mul"
    value: float = 0

class GroupPayload(BaseModel):
    name: str = Field(min_length=1)  # id == name
    mode: Literal["single", "multi"] = "single"
    items: List[GroupItem] = []

@router.get("", dependencies=[Depends(admin_token_required)])
def groups_list():
    return list_groups()

@router.post("", dependencies=[Depends(admin_token_required)])
def groups_create(payload: GroupPayload):
    return save_group(payload.name, payload.dict())

@router.put("/{group_id}", dependencies=[Depends(admin_token_required)])
def groups_update(group_id: str, payload: GroupPayload):
    if group_id != payload.name:
        # дозволяємо перейменування: видаляємо стару, зберігаємо нову
        try:
            delete_group(group_id)
        except Exception:
            pass
    return save_group(payload.name, payload.dict())

@router.delete("/{group_id}", dependencies=[Depends(admin_token_required)])
def groups_delete(group_id: str):
    delete_group(group_id)
    return {"ok": True}

@router.get("/{group_id}", dependencies=[Depends(admin_token_required)])
def groups_get(group_id: str):
    try:
        return get_group(group_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Not found")
