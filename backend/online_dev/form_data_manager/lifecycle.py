"""Generic lifecycle hooks for online form data operations.

Hooks are intentionally registered by form code in Python.  They run inside
the caller's transaction and must not commit the session themselves.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class FormLifecycleContext:
    """Context passed to a form lifecycle hook."""

    db: AsyncSession
    form_code: str
    action: str
    record_id: Optional[str] = None
    old_data: Optional[Dict[str, Any]] = None
    data: Dict[str, Any] = field(default_factory=dict)
    operator_id: Optional[str] = None


class FormLifecycleHook:
    """Default no-op hook implementation."""

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


class FormLifecycleRegistry:
    """Maps a form code to its optional Python hook implementation."""

    def __init__(self) -> None:
        self._hooks: Dict[str, Type[FormLifecycleHook] | FormLifecycleHook] = {}

    def register(
        self,
        form_code: str,
        hook_class: Type[FormLifecycleHook] | FormLifecycleHook,
    ) -> None:
        if not form_code:
            raise ValueError("form_code 不能为空")
        self._hooks[form_code] = hook_class

    def unregister(self, form_code: str) -> None:
        self._hooks.pop(form_code, None)

    def get(self, form_code: str) -> Optional[FormLifecycleHook]:
        hook = self._hooks.get(form_code)
        if hook is None:
            return None
        return hook() if inspect.isclass(hook) else hook

    async def dispatch(
        self,
        form_code: str,
        event: str,
        context: FormLifecycleContext,
    ) -> None:
        hook = self.get(form_code)
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
    hook_class: Type[FormLifecycleHook] | FormLifecycleHook,
) -> None:
    """Convenience registration function for business modules."""

    hook_registry.register(form_code, hook_class)

