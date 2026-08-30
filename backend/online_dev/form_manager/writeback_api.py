"""当前源表单范围内的回写规则 API。"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from online_dev.form_manager.schema import (
    FormWriteBackRuleCreateIn,
    FormWriteBackRuleListOut,
    FormWriteBackRuleOut,
    FormWriteBackRuleUpdateIn,
)
from online_dev.form_manager.writeback_service import (
    FormWriteBackException,
    FormWriteBackService,
    serialize_rule,
)

router = APIRouter(prefix="/form/{form_id}/writeback-rules", tags=["表单回写"])


def _user_id(request: Request) -> Optional[str]:
    return getattr(request.state, "user_id", None)


@router.get("", response_model=List[FormWriteBackRuleListOut], summary="查询当前表单回写规则")
async def list_writeback_rules(form_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await FormWriteBackService.list(db, form_id)
    except FormWriteBackException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{rule_id}", response_model=FormWriteBackRuleOut, summary="获取回写规则详情")
async def get_writeback_rule(form_id: str, rule_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return serialize_rule(await FormWriteBackService.get(db, form_id, rule_id))
    except FormWriteBackException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=FormWriteBackRuleOut, summary="创建回写规则")
async def create_writeback_rule(
    form_id: str,
    data: FormWriteBackRuleCreateIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        rule = await FormWriteBackService.create(db, form_id, data, _user_id(request))
        return serialize_rule(rule)
    except FormWriteBackException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{rule_id}", response_model=FormWriteBackRuleOut, summary="更新回写规则")
async def update_writeback_rule(
    form_id: str,
    rule_id: str,
    data: FormWriteBackRuleUpdateIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        rule = await FormWriteBackService.update(db, form_id, rule_id, data, _user_id(request))
        return serialize_rule(rule)
    except FormWriteBackException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{rule_id}", response_model=Dict[str, Any], summary="删除回写规则")
async def delete_writeback_rule(
    form_id: str,
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        await FormWriteBackService.delete(db, form_id, rule_id, _user_id(request))
        return {"success": True}
    except FormWriteBackException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{rule_id}/duplicate", response_model=FormWriteBackRuleOut, summary="复制回写规则")
async def duplicate_writeback_rule(
    form_id: str,
    rule_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        rule = await FormWriteBackService.duplicate(db, form_id, rule_id, _user_id(request))
        return serialize_rule(rule)
    except FormWriteBackException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
