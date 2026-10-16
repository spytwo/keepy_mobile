import re

import flet as ft
import httpx

API_URL = "https://keepy.mooo.com:8443"

URL_RE = re.compile(r'https?://[^\s<>"<>]+')

BG = "#F4F6FA"
SURFACE = "#FFFFFF"
PRIMARY = "#4568E8"
TEXT = "#202A44"
MUTED = "#7B8499"
BORDER = "#E5E9F2"

CONTENT_WIDTH = 620


def clean_url(url: str) -> str:
    return url.rstrip(".,!?;:)]}")


def main(page: ft.Page):
    page.title = "keepy"

    page.window.width = 700
    page.window.height = 800
    page.window.min_width = 700
    page.window.min_height = 600

    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG
    page.padding = 24
    page.spacing = 12
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    credentials = None

    username_input = ft.TextField(
        label="Логин",
        value="val",
        border_radius=12,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        bgcolor=SURFACE,
    )

    password_input = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        bgcolor=SURFACE,
    )

    login_status = ft.Text(
        size=13,
        color=MUTED,
    )

    entry_input = ft.TextField(
        multiline=True,
        min_lines=1,
        max_lines=6,
        expand=True,
        border_radius=12,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        bgcolor=SURFACE,
    )

    app_status = ft.Text(
        size=13,
        color=MUTED,
    )

    entries = ft.Column(
        spacing=6,
        width=CONTENT_WIDTH,
    )

    content_area = ft.Column(
        spacing=14,
        width=CONTENT_WIDTH,
    )

    def make_card(content, padding=14):
        return ft.Container(
            content=content,
            width=CONTENT_WIDTH,
            padding=padding,
            bgcolor=SURFACE,
            border=ft.Border(
                left=ft.BorderSide(1, BORDER),
                top=ft.BorderSide(1, BORDER),
                right=ft.BorderSide(1, BORDER),
                bottom=ft.BorderSide(1, BORDER),
            ),
            border_radius=12,
        )

    def make_button(text, icon, handler, expand=False):
        return ft.Button(
            text,
            icon=icon,
            on_click=handler,
            expand=expand,
            style=ft.ButtonStyle(
                bgcolor=PRIMARY,
                color=SURFACE,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=14,
            ),
        )

    async def request_entries():
        async with httpx.AsyncClient(
            auth=credentials,
            timeout=30,
        ) as client:
            response = await client.get(f"{API_URL}/entries")
            response.raise_for_status()
            return response.json()

    async def delete_entry(entry_id: int):
        try:
            async with httpx.AsyncClient(
                auth=credentials,
                timeout=10,
            ) as client:
                response = await client.delete(f"{API_URL}/entries/{entry_id}")
                response.raise_for_status()

            app_status.value = "Запись удалена."
            await refresh_entries()

        except httpx.HTTPError as error:
            app_status.value = f"Ошибка удаления: {error}"
            page.update()

    async def on_delete_click(e):
        await delete_entry(e.control.data)

    async def on_refresh_click(e):
        app_status.value = "Обновляем записи..."
        page.update()
        await refresh_entries()

    async def refresh_entries():
        try:
            data = await request_entries()
            entries.controls.clear()

            if not data:
                entries.controls.append(
                    make_card(
                        ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.INBOX_OUTLINED,
                                    size=30,
                                    color="#A3AEC2",
                                ),
                                ft.Text(
                                    "Пока здесь пусто",
                                    size=15,
                                    weight=ft.FontWeight.BOLD,
                                    color=TEXT,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    "Добавь первую заметку или ссылку.",
                                    size=12,
                                    color=MUTED,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=(ft.CrossAxisAlignment.CENTER),
                            spacing=6,
                        ),
                        padding=20,
                    )
                )

            for item in data:
                title = item.get("title")
                content = item["content"]
                entry_id = item["id"]

                matches = list(URL_RE.finditer(content))

                if matches:
                    spans = []
                    last_end = 0

                    for match in matches:
                        # Убираем конечную пунктуацию из URL.
                        url = clean_url(match.group())
                        url_end = match.start() + len(url)

                        # Текст перед ссылкой.
                        if match.start() > last_end:
                            spans.append(
                                ft.TextSpan(
                                    content[last_end : match.start()],
                                    style=ft.TextStyle(
                                        color=TEXT,
                                    ),
                                )
                            )

                        # Кликабельная ссылка без подчёркивания.
                        spans.append(
                            ft.TextSpan(
                                url,
                                url=url,
                                style=ft.TextStyle(
                                    color=PRIMARY,
                                    decoration=ft.TextDecoration.NONE,
                                ),
                            )
                        )

                        last_end = url_end

                    # Текст после последней ссылки.
                    if last_end < len(content):
                        spans.append(
                            ft.TextSpan(
                                content[last_end:],
                                style=ft.TextStyle(
                                    color=TEXT,
                                ),
                            )
                        )

                    note_text = ft.Text(
                        spans=spans,
                        size=14,
                        selectable=True,
                    )

                else:
                    note_text = ft.Text(
                        content,
                        size=14,
                        color=TEXT,
                        selectable=True,
                    )

                entries.controls.append(
                    make_card(
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=note_text,
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color="#929CB0",
                                    icon_size=19,
                                    tooltip="Удалить запись",
                                    data=entry_id,
                                    on_click=on_delete_click,
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=(ft.CrossAxisAlignment.CENTER),
                        ),
                        padding=ft.Padding(
                            left=12,
                            right=6,
                            top=4,
                            bottom=4,
                        ),
                    )
                )

            app_status.value = f"Всего записей: {len(data)}"

        except httpx.HTTPError as error:
            app_status.value = f"Не удалось загрузить записи: {error}"

        page.update()

    async def login(e):
        nonlocal credentials

        username = (username_input.value or "").strip()
        password = password_input.value or ""

        if not username or not password:
            login_status.value = "Введи логин и пароль."
            page.update()
            return

        login_status.value = "Подключаемся к серверу..."
        page.update()

        try:
            async with httpx.AsyncClient(
                auth=(username, password),
                timeout=10,
            ) as client:
                response = await client.get(f"{API_URL}/entries")

            if response.status_code == 401:
                login_status.value = "Неверный логин или пароль."
                page.update()
                return

            response.raise_for_status()
            credentials = (username, password)

            content_area.controls = [app_view]
            page.update()

            await refresh_entries()

        except httpx.HTTPError as error:
            login_status.value = f"Ошибка подключения: {error}"
            page.update()

    async def add_entry(e):
        content = (entry_input.value or "").strip()

        if not content:
            app_status.value = "Сначала введи текст или ссылку."
            page.update()
            return

        try:
            async with httpx.AsyncClient(
                auth=credentials,
                timeout=60,
            ) as client:
                response = await client.post(
                    f"{API_URL}/entries",
                    json={"content": content},
                )
                response.raise_for_status()

            entry_input.value = ""
            app_status.value = "Запись добавлена."

            await refresh_entries()

        except httpx.HTTPError as error:
            app_status.value = f"Ошибка добавления: {error}"
            page.update()

    login_view = make_card(
        ft.Column(
            controls=[
                username_input,
                password_input,
                make_button(
                    "Войти",
                    ft.Icons.ARROW_FORWARD_ROUNDED,
                    login,
                ),
                login_status,
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=22,
    )

    app_view = ft.Column(
        controls=[
            make_card(
                ft.Column(
                    controls=[
                        ft.Text(
                            "Новая запись",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT,
                        ),
                        ft.Row(
                            controls=[entry_input],
                            width=CONTENT_WIDTH - 30,
                        ),
                        ft.Row(
                            controls=[
                                make_button(
                                    "Добавить",
                                    ft.Icons.ADD_ROUNDED,
                                    add_entry,
                                    expand=True,
                                )
                            ],
                            width=CONTENT_WIDTH - 30,
                        ),
                        app_status,
                    ],
                    spacing=10,
                    horizontal_alignment=(ft.CrossAxisAlignment.STRETCH),
                    width=CONTENT_WIDTH - 30,
                )
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        "Записи",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH_ROUNDED,
                        icon_color=PRIMARY,
                        tooltip="Обновить записи",
                        on_click=on_refresh_click,
                    ),
                ],
                width=CONTENT_WIDTH,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            entries,
        ],
        spacing=12,
        width=CONTENT_WIDTH,
    )

    page.add(
        ft.Container(
            content=ft.Text(
                "keepy",
                size=30,
                weight=ft.FontWeight.BOLD,
                color=TEXT,
            ),
            width=CONTENT_WIDTH,
        ),
        content_area,
    )

    content_area.controls = [login_view]
    page.update()


ft.run(main)
