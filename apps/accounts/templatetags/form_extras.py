from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def form_field(form, name: str):
    """Acessa um campo de Form dinamicamente pelo nome (ex.: form|form_field:'plan_1')."""
    try:
        return form[name]
    except Exception:
        return ""

