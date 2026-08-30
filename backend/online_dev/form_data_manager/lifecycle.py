"""Table-level lifecycle hooks for online form data operations.

Hooks are registered by form code and table key. They run inside the
caller's transaction and must not commit the session themselves.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class FormLifecycleContext:
    """Context passed to a main-table or sub-table lifecycle hook."""

    db: AsyncSession
    form_code: str
    table_name: str
    table_type: str
    action: str
    record_id: Optional[str] = None
    main_record_id: Optional[str] = None
    old_data: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    parent_old_data: Dict[str, Any] = field(default_factory=dict)
    parent_data: Dict[str, Any] = field(default_factory=dict)
    operator_id: Optional[str] = None


class FormLifecycleHook:
    """Default no-op table hook implementation."""

    async def before_create(self, context: FormLifecycleContext) -> None:
        pass

    async def after_create(self, context: FormLifecycleContext) -> None:
        pass

    async def before_update(self, context: FormLifecycleContext) -> None:
        pass

    async def after_update(self, context: FormLifecycleContext) -> None:
        pass

    async def before_approve(self, context: FormLifecycleContext) -> None:
        pass

    async def after_approve(self, context: FormLifecycleContext) -> None:
        pass

    async def before_unapprove(self, context: FormLifecycleContext) -> None:
        pass

    async def after_unapprove(self, context: FormLifecycleContext) -> None:
        pass

    async def before_delete(self, context: FormLifecycleContext) -> None:
        pass

    async def after_delete(self, context: FormLifecycleContext) -> None:
        pass


class FormLifecycleRegistry:
    """Maps ``(form_code, table_name)`` to a Python hook implementation."""

    def __init__(self) -> None:
        self._hooks: Dict[
            Tuple[str, str], Type[FormLifecycleHook] | FormLifecycleHook
        ] = {}

    def register(
        self,
        form_code: str,
        table_name: str,
        hook_class: Type[FormLifecycleHook] | FormLifecycleHook,
    ) -> None:
        if not form_code:
            raise ValueError("form_code 不能为空")
        if not table_name:
            raise ValueError("table_name 不能为空")
        self._hooks[(form_code, table_name)] = hook_class

    def unregister(self, form_code: str, table_name: str) -> None:
        self._hooks.pop((form_code, table_name), None)

    def get(self, form_code: str, table_name: str) -> Optional[FormLifecycleHook]:
        hook = self._hooks.get((form_code, table_name))
        if hook is None:
            return None
        return hook() if inspect.isclass(hook) else hook

    async def dispatch(
        self,
        form_code: str,
        table_name: str,
        event: str,
        context: FormLifecycleContext,
    ) -> None:
        hook = self.get(form_code, table_name)
        if hook is None:
            return

        callback = getattr(hook, event, None)
        if callback is None:
            return

        result = callback(context)
        if inspect.isawaitable(result):
            await result


hook_registry = FormLifecycleRegistry()


def register_form_hook(
    form_code: str,
    table_name: str,
    hook_class: Type[FormLifecycleHook] | FormLifecycleHook,
) -> None:
    """Register a hook for the main table or a configured sub-table."""

    hook_registry.register(form_code, table_name, hook_class)
