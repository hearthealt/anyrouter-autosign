"""
账号分组 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AccountGroup, Account
from app.schemas import ApiResponse

router = APIRouter(prefix="/groups", tags=["分组"])


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "default"


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: str = "default"
    account_count: int = 0

    class Config:
        from_attributes = True


@router.get("", response_model=ApiResponse)
def get_groups(db: Session = Depends(get_db)):
    """获取所有分组"""
    groups = db.query(AccountGroup).all()
    result = []
    for group in groups:
        account_count = db.query(Account).filter(Account.group_id == group.id).count()
        result.append(GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color or "default",
            account_count=account_count
        ))
    return ApiResponse(success=True, data=result)


@router.post("", response_model=ApiResponse)
def create_group(data: GroupCreate, db: Session = Depends(get_db)):
    """创建分组"""
    # 检查名称是否已存在
    existing = db.query(AccountGroup).filter(AccountGroup.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="分组名称已存在")

    group = AccountGroup(
        name=data.name,
        description=data.description,
        color=data.color or "default"
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    return ApiResponse(
        success=True,
        message="分组创建成功",
        data=GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color or "default",
            account_count=0
        )
    )


@router.put("/{group_id}", response_model=ApiResponse)
def update_group(group_id: int, data: GroupUpdate, db: Session = Depends(get_db)):
    """更新分组"""
    group = db.query(AccountGroup).filter(AccountGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    if data.name is not None:
        # 检查名称是否已被其他分组使用
        existing = db.query(AccountGroup).filter(
            AccountGroup.name == data.name,
            AccountGroup.id != group_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="分组名称已存在")
        group.name = data.name

    if data.description is not None:
        group.description = data.description
    if data.color is not None:
        group.color = data.color

    db.commit()
    db.refresh(group)

    account_count = db.query(Account).filter(Account.group_id == group.id).count()
    return ApiResponse(
        success=True,
        message="分组更新成功",
        data=GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            color=group.color or "default",
            account_count=account_count
        )
    )


@router.delete("/{group_id}", response_model=ApiResponse)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """删除分组"""
    group = db.query(AccountGroup).filter(AccountGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    # 将该分组的账号移除分组
    db.query(Account).filter(Account.group_id == group_id).update({"group_id": None})

    db.delete(group)
    db.commit()

    return ApiResponse(success=True, message="分组删除成功")


@router.post("/{group_id}/accounts", response_model=ApiResponse)
def add_accounts_to_group(group_id: int, account_ids: list[int], db: Session = Depends(get_db)):
    """将账号添加到分组"""
    group = db.query(AccountGroup).filter(AccountGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    updated = db.query(Account).filter(Account.id.in_(account_ids)).update(
        {"group_id": group_id},
        synchronize_session=False
    )
    db.commit()

    return ApiResponse(success=True, message=f"已将 {updated} 个账号添加到分组")


@router.delete("/{group_id}/accounts", response_model=ApiResponse)
def remove_accounts_from_group(group_id: int, account_ids: list[int], db: Session = Depends(get_db)):
    """将账号从分组移除"""
    updated = db.query(Account).filter(
        Account.id.in_(account_ids),
        Account.group_id == group_id
    ).update({"group_id": None}, synchronize_session=False)
    db.commit()

    return ApiResponse(success=True, message=f"已将 {updated} 个账号从分组移除")
