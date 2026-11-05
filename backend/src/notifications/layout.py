"""Общий HTML-каркас писем CityBoost.

Письма собраны таблицами и инлайн-стилями: так они одинаково выглядят
в Gmail, Outlook, Apple Mail и мобильных клиентах. Внешних картинок нет —
только типографика, цвет и линии, поэтому письмо не ломается при
отключённой загрузке изображений.

Визуальный язык — муниципальный бланк: тёмно-зелёная шапка, номер заявки
в правом верхнем углу, линейка данных и маршрутная полоса этапов.
"""

from __future__ import annotations

from html import escape as html_escape

# Палитра совпадает с токенами интерфейса CityBoost.
PINE = "#0E5A4A"
PINE_DEEP = "#072F27"
PINE_LIGHT = "#C9E0D7"
ORANGE = "#E4572E"
ORANGE_TEXT = "#A03519"
ORANGE_BADGE = "#C4431F"
CANVAS = "#EEF0EC"
PAPER = "#FFFFFF"
MUTED = "#F6F7F4"
INK = "#16201C"
INK_SOFT = "#4A554F"
INK_FAINT = "#6B756F"
INK_MUTED = "#5A645E"
LINE = "#D7DCD5"

DISPLAY_FONT = "'Unbounded', 'Trebuchet MS', 'Segoe UI', Arial, sans-serif"
BODY_FONT = "'Onest', 'Segoe UI', Helvetica, Arial, sans-serif"

STATUS_LABELS: dict[str, str] = {
    "NEW": "Новая",
    "IN_WORK": "В работе",
    "DONE": "Выполнена",
    "CLOSED": "Отклонена",
}

STATUS_COLORS: dict[str, str] = {
    "NEW": PINE,
    "IN_WORK": ORANGE_BADGE,
    "DONE": PINE,
    "CLOSED": INK_FAINT,
}

STATUS_STEPS: tuple[tuple[str, str], ...] = (
    ("NEW", "Новая"),
    ("IN_WORK", "В работе"),
    ("DONE", "Выполнена"),
)


def esc(value: object) -> str:
    """Экранировать пользовательские данные для HTML."""
    return html_escape(str(value or ""))


def status_badge(status: str) -> str:
    """Компактный статус-бейдж в цветах CityBoost."""
    label = STATUS_LABELS.get(status, status)
    color = STATUS_COLORS.get(status, INK_FAINT)
    return (
        f'<span style="display: inline-block; background: {color}; color: #FFFFFF; '
        f"font-family: {BODY_FONT}; font-size: 11px; font-weight: 600; "
        f"line-height: 1.4; padding: 3px 8px; border-radius: 3px; "
        f'white-space: nowrap;">{esc(label)}</span>'
    )


def route_block(current: str) -> str:
    """Маршрутная полоса этапов заявки — как схема линии городской службы."""
    index = next(
        (i for i, (key, _) in enumerate(STATUS_STEPS) if key == current),
        0,
    )
    cells: list[str] = []
    width = round(100 / len(STATUS_STEPS), 2)
    for i, (_, label) in enumerate(STATUS_STEPS):
        reached = i <= index
        is_current = i == index
        line_color = PINE if reached else LINE
        text_color = INK if is_current else (INK_SOFT if reached else INK_FAINT)
        weight = "600" if is_current else "400"
        cells.append(
            f'<td width="{width}%" valign="top" class="email-route-label" '
            f'style="border-top: 3px solid {line_color}; padding: 9px 6px 0 0; '
            f"font-family: {BODY_FONT}; font-size: 11px; line-height: 1.35; "
            f'font-weight: {weight}; color: {text_color};">{esc(label)}</td>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'border="0" style="border-collapse: collapse; margin-top: 24px;">'
        f'<tr>{"".join(cells)}</tr></table>'
    )


def meta_block(
    rows: list[tuple[str, str]],
    *,
    allow_html: bool = False,
) -> str:
    """Таблица данных с тонкими линейками вместо карточки."""
    body: list[str] = []
    for label, value in rows:
        safe_label = label if allow_html else esc(label)
        safe_value = value if allow_html else esc(value)
        body.append(
            "<tr>"
            f'<td width="118" valign="top" style="border-top: 1px solid {LINE}; '
            f"padding: 10px 12px 10px 0; font-family: {BODY_FONT}; font-size: 12px; "
            f'line-height: 1.5; color: {INK_FAINT};">{safe_label}</td>'
            f'<td valign="top" style="border-top: 1px solid {LINE}; padding: 10px 0; '
            f"font-family: {BODY_FONT}; font-size: 14px; line-height: 1.5; "
            f'color: {INK};">{safe_value}</td>'
            "</tr>"
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse: collapse; margin-top: 22px;">'
        f'{"".join(body)}</table>'
    )


def quote_block(author: str, text: str) -> str:
    """Цитата сообщения с оранжевой линейкой."""
    safe_text = esc(text).replace("\n", "<br>")
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'border="0" style="border-collapse: collapse; margin-top: 22px;">'
        "<tr>"
        f'<td width="3" style="background: {ORANGE}; font-size: 0; line-height: 0;">'
        "&nbsp;</td>"
        f'<td style="padding: 2px 0 2px 14px;">'
        f"<div style=\"font-family: {BODY_FONT}; font-size: 12px; font-weight: 600; "
        f'color: {ORANGE_TEXT};">{esc(author)}</div>'
        f"<div style=\"margin-top: 5px; font-family: {BODY_FONT}; font-size: 14px; "
        f'line-height: 1.6; color: {INK};">{safe_text}</div>'
        "</td></tr></table>"
    )


def note_block(text: str, *, accent: str = ORANGE) -> str:
    """Пояснение или причина отклонения на подложке."""
    return (
        f'<div style="margin-top: 20px; background: {MUTED}; '
        f"border-left: 3px solid {accent}; padding: 12px 14px; "
        f"font-family: {BODY_FONT}; font-size: 13px; line-height: 1.6; "
        f'color: {INK_SOFT};">{esc(text)}</div>'
    )


def code_block(code: str) -> str:
    """Код подтверждения как отрывной корешок бланка."""
    return (
        f'<div style="margin-top: 26px; padding: 20px 0; '
        f"border-top: 2px dashed {LINE}; border-bottom: 2px dashed {LINE}; "
        'text-align: center;">'
        f"<div class=\"email-code\" style=\"font-family: {DISPLAY_FONT}; "
        f"font-size: 34px; font-weight: 700; letter-spacing: 10px; "
        f'color: {PINE_DEEP}; padding-left: 10px;">{esc(code)}</div>'
        "</div>"
    )


def _button(text: str, url: str) -> str:
    safe_url = html_escape(url, quote=True)
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="border-collapse: separate; margin-top: 28px;">'
        "<tr>"
        f'<td align="center" style="background: {PINE}; border-radius: 3px;">'
        f'<a href="{safe_url}" target="_blank" '
        f"style=\"display: block; padding: 14px 26px; font-family: {BODY_FONT}; "
        "font-size: 14px; font-weight: 600; line-height: 1; color: #FFFFFF; "
        f'text-decoration: none;">{esc(text)}</a>'
        "</td></tr></table>"
    )


def render_email(
    *,
    preheader: str,
    heading: str,
    intro: str,
    blocks: list[str],
    footer: str,
    cta_text: str | None = None,
    cta_url: str | None = None,
    reference: str | None = None,
) -> str:
    """Собрать письмо из шапки, заголовка, блоков и подвала."""
    reference_html = (
        f"<br>№ {esc(reference)}" if reference else ""
    )
    cta_html = (
        _button(cta_text, cta_url or "")
        if cta_text and cta_url
        else ""
    )
    body_html = "".join(blocks)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{esc(heading)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600&amp;family=Unbounded:wght@600;700&amp;display=swap" rel="stylesheet">
<style>
  @media only screen and (max-width: 620px) {{
    .email-shell {{ width: 100% !important; max-width: 100% !important; }}
    .email-pad {{ padding-left: 20px !important; padding-right: 20px !important; }}
    .email-heading {{ font-size: 23px !important; }}
    .email-code {{ font-size: 28px !important; letter-spacing: 7px !important; padding-left: 7px !important; }}
    .email-route-label {{ font-size: 10px !important; }}
  }}
</style>
</head>
<body style="margin: 0; padding: 0; background: {CANVAS}; -webkit-text-size-adjust: 100%;">
  <div style="display: none; max-height: 0; max-width: 0; overflow: hidden; opacity: 0; mso-hide: all; font-size: 1px; line-height: 1px; color: {CANVAS};">{esc(preheader)}</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background: {CANVAS}; border-collapse: collapse;">
    <tr>
      <td align="center" style="padding: 30px 14px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" class="email-shell" style="width: 100%; max-width: 600px; background: {PAPER}; border: 1px solid {LINE}; border-collapse: collapse;">
          <tr>
            <td class="email-pad" style="background: {PINE}; padding: 22px 32px 20px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse: collapse;">
                <tr>
                  <td style="font-family: {DISPLAY_FONT}; font-size: 19px; font-weight: 700; line-height: 1.2; color: #FFFFFF; letter-spacing: -0.03em;">CityBoost</td>
                  <td align="right" style="font-family: {BODY_FONT}; font-size: 11px; line-height: 1.5; color: {PINE_LIGHT}; white-space: nowrap;">Витебск{reference_html}</td>
                </tr>
              </table>
              <div style="margin-top: 16px; width: 44px; height: 3px; background: {ORANGE}; font-size: 0; line-height: 0;">&nbsp;</div>
            </td>
          </tr>
          <tr>
            <td class="email-pad" style="background: {PAPER}; padding: 34px 32px 30px;">
              <h1 class="email-heading" style="margin: 0; font-family: {DISPLAY_FONT}; font-size: 26px; font-weight: 700; line-height: 1.25; color: {INK}; letter-spacing: -0.02em;">{esc(heading)}</h1>
              <p style="margin: 10px 0 0; font-family: {BODY_FONT}; font-size: 15px; line-height: 1.6; color: {INK_SOFT};">{intro}</p>
              {body_html}
              {cta_html}
              <div style="margin-top: 30px; border-top: 1px solid {LINE}; padding-top: 14px; font-family: {BODY_FONT}; font-size: 12px; line-height: 1.6; color: {INK_FAINT};">{footer}</div>
            </td>
          </tr>
        </table>
        <div style="max-width: 600px; margin: 12px auto 0; font-family: {BODY_FONT}; font-size: 11px; line-height: 1.5; color: {INK_MUTED}; text-align: center;">CityBoost — сервис городских заявок, Витебск</div>
      </td>
    </tr>
  </table>
</body>
</html>"""
