import flet as ft
import asyncio
import os

# База данных счета (хранится в оперативной памяти сервера)
global_scores = {}

async def main(page: ft.Page):
    # Настройки страницы
    page.title = "Cloud Clicker"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1E1E2E"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Уникальный ID пользователя (сессия)
    user_id = page.session_id
    if user_id not in global_scores:
        global_scores[user_id] = 0

    score_text = ft.Text(
        value=str(global_scores[user_id]),
        size=80,
        weight=ft.FontWeight.BOLD,
        color=ft.colors.WHITE
    )

    title_text = ft.Text(
        value="СКОР",
        size=20,
        color="#A6ACCD",
        weight=ft.FontWeight.W_500
    )

    # Анимация монеты
    async def animate_coin():
        coin.scale = 0.85
        page.update()
        await asyncio.sleep(0.1)
        coin.scale = 1.0
        page.update()

    # Логика клика
    async def on_click(e):
        global_scores[user_id] += 1
        score_text.value = str(global_scores[user_id])
        page.run_task(animate_coin)
        page.update()

    coin = ft.Container(
        content=ft.Text("TAP", size=54, weight=ft.FontWeight.W_900, color=ft.colors.WHITE),
        alignment=ft.alignment.center,
        width=220,
        height=220,
        border_radius=110,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#FF0076", "#FF5900"]
        ),
        on_click=on_click,
        scale=ft.transform.Scale(1.0),
        animate_scale=ft.animation.Animation(150, ft.AnimationCurve.EASE_OUT_BACK)
    )

    page.add(
        ft.Column(
            controls=[
                title_text,
                score_text,
                ft.Container(height=50),
                coin
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

# Запускаем Flet в режиме Веб-Сервера!
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
