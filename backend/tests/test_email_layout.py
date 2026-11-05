"""Тесты вёрстки писем: экранирование и ключевые элементы каркаса."""

from __future__ import annotations

from src.notifications.layout import (
    code_block,
    meta_block,
    render_email,
    route_block,
    status_badge,
)


def _render(**overrides) -> str:
    params = {
        "preheader": "Превью письма",
        "heading": "Заявка принята",
        "intro": "Здравствуйте, Иван.",
        "blocks": [],
        "footer": "Вы следите за заявкой.",
        "cta_text": "Открыть заявку",
        "cta_url": "https://example.com/ticket/1",
    }
    params.update(overrides)
    return render_email(**params)


def test_email_contains_brand_and_cta():
    html = _render()
    assert "CityBoost" in html
    assert "Заявка принята" in html
    assert "Открыть заявку" in html
    assert "https://example.com/ticket/1" in html


def test_user_content_is_escaped():
    html = _render(
        blocks=[
            meta_block([("Заявка", '<script>alert("x")</script>')]),
            route_block("NEW"),
        ],
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "Новая" in html


def test_cta_url_is_attribute_escaped():
    html = _render(cta_url="https://example.com/?a=1&b=2")
    assert 'href="https://example.com/?a=1&amp;b=2"' in html


def test_status_badge_and_code_block():
    html = _render(
        blocks=[status_badge("IN_WORK"), code_block("482915")],
    )
    assert "В работе" in html
    assert "482915" in html
    assert "dashed" in html
