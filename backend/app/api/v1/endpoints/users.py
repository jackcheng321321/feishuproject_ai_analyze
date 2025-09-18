from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user, UserResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    can_manage_config: Optional[bool] = None
    can_manage_webhooks: Optional[bool] = None
    can_manage_tasks: Optional[bool] = None
    can_view_logs: Optional[bool] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme: Optional[str] = None


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户列表（需要超级用户权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"获取用户列表，跳过: {skip}, 限制: {limit}")
        
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        
        users = query.offset(skip).limit(limit).all()
        
        logger.info(f"成功返回 {len(users)} 个用户")
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新用户（需要超级用户权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"创建新用户: {user_data.username}")
        
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="邮箱已存在")
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_superuser=user_data.is_superuser
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"用户创建成功: {db_user.id}")
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户资料"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户资料"""
    try:
        logger.info(f"更新用户资料: {current_user.username}")
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        
        # 移除权限相关字段（普通用户不能修改自己的权限）
        if not current_user.is_superuser:
            forbidden_fields = {
                "is_active", "can_manage_config", "can_manage_webhooks", 
                "can_manage_tasks", "can_view_logs"
            }
            for field in forbidden_fields:
                update_data.pop(field, None)
        
        # 检查邮箱是否已被其他用户使用
        if "email" in update_data:
            existing_user = db.query(User).filter(
                User.email == update_data["email"],
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        
        # 更新用户信息
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"用户资料更新成功: {current_user.username}")
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户资料失败: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息（需要超级用户权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.info(f"获取用户信息: {user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新指定用户信息（需要超级用户权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        logger.info(f"更新用户信息: {user.username}")
        
        # 更新字段
        update_data = user_data.dict(exclude_unset=True)
        
        # 检查邮箱是否已被其他用户使用
        if "email" in update_data:
            existing_user = db.query(User).filter(
                User.email == update_data["email"],
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        
        # 更新用户信息
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"用户信息更新成功: {user.username}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除用户（需要超级用户权限）"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不能删除自己
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己")
        
        logger.info(f"删除用户: {user.username}")
        
        db.delete(user)
        db.commit()
        
        logger.info(f"用户删除成功: {user.username}")
        return {"message": "用户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")