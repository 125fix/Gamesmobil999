import flet as ft
import asyncio
import os
import uuid
import time

# Общая база данных сервера (сохраняется, пока работает сервер)
# Формат: user_id -> {"score": 0, "power": 1, "name": "Игрок...", "last_active": timestamp}
global_db = {}

async def main(page: ft.Page):
    page.title = "Cloud Clicker & Admin"
    page.theme_mode = "dark"
    page.bgcolor = "#1E1E2E"

    # Регистрируем нового игрока
    user_id = str(uuid.uuid4())
    if user_id not in global_db:
        global_db[user_id] = {
            "score": 0, 
            "power": 1, 
            "name": f"Игрок {str(user_id)[:4]}",
            "last_active": time.time()
        }

    # ===============================
    # ЭКРАН 1: ОСНОВНАЯ ИГРА
    # ===============================
    def get_game_view():
        user_data = global_db[user_id]
        
        score_text = ft.Text(value=str(user_data["score"]), size=80, weight="bold", color="#FFFFFF")
        power_text = ft.Text(value=f"Сила клика: {user_data['power']}", size=16, color="#A6ACCD")
        
        async def on_click(e):
            user_data["score"] += user_data["power"]
            user_data["last_active"] = time.time()
            score_text.value = str(user_data["score"])
            
            # Анимация монетки
            coin.scale = 0.9
            page.update()
            await asyncio.sleep(0.05)
            coin.scale = 1.0
            page.update()

        async def buy_upgrade(e):
            cost = user_data["power"] * 50
            if user_data["score"] >= cost:
                user_data["score"] -= cost
                user_data["power"] += 1
                score_text.value = str(user_data["score"])
                power_text.value = f"Сила клика: {user_data['power']}"
                upgrade_btn.text = f"Улучшить силу (Цена: {user_data['power'] * 50} 💰)"
                page.update()

        coin = ft.Container(
            content=ft.Text("TAP", size=54, weight="w900", color="#FFFFFF"),
            alignment=ft.Alignment(0, 0),
            width=220,
            height=220,
            border_radius=110,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#FF0076", "#FF5900"]
            ),
            on_click=on_click,
            scale=1.0,
            animate_scale=100
        )

        upgrade_btn = ft.ElevatedButton(
            text=f"Улучшить силу (Цена: {user_data['power'] * 50} 💰)",
            color="#FFFFFF",
            bgcolor="#FF5900",
            on_click=buy_upgrade
        )

        return ft.View(
            "/",
            controls=[
                ft.Row([
                    ft.Text(f"Привет, {user_data['name']}!", size=20, weight="bold", color="#FFFFFF"),
                    ft.IconButton(icon="settings", on_click=lambda _: navigate("/admin"), tooltip="Админка")
                ], alignment="spaceBetween"),
                ft.Column(
                    [
                        ft.Text("СКОР", size=20, color="#A6ACCD", weight="w500"),
                        score_text,
                        power_text,
                        ft.Container(height=30),
                        coin,
                        ft.Container(height=40),
                        upgrade_btn
                    ],
                    horizontal_alignment="center",
                    alignment="center",
                    expand=True
                )
            ],
            bgcolor="#1E1E2E",
        )

    # ===============================
    # ЭКРАН 2: ПАНЕЛЬ АДМИНА
    # ===============================
    def get_admin_view():
        users_list = ft.ListView(expand=True, spacing=10)
        
        def refresh_data(e=None):
            users_list.controls.clear()
            # Сортируем игроков по очкам (Топ лидеров)
            sorted_users = sorted(global_db.items(), key=lambda x: x[1]['score'], reverse=True)
            
            for uid, data in sorted_users:
                users_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"👤 {data['name']}", color="#FFFFFF", weight="bold", size=18),
                            ft.Text(f"Очки: {data['score']} | Сила: {data['power']}", color="#FF0076", weight="bold")
                        ], alignment="spaceBetween"),
                        bgcolor="#292D3E",
                        padding=15,
                        border_radius=10
                    )
                )
            page.update()

        # Загружаем данные при открытии админки
        refresh_data() 

        return ft.View(
            "/admin",
            controls=[
                ft.Row([
                    ft.IconButton(icon="arrow_back", on_click=lambda _: navigate("/"), icon_color="#FFFFFF"),
                    ft.Text("Панель Администратора", size=22, weight="bold", color="#FFFFFF"),
                    ft.IconButton(icon="refresh", on_click=refresh_data, icon_color="#FF0076", tooltip="Обновить список")
                ], alignment="spaceBetween"),
                ft.Container(height=20),
                ft.Text("Рейтинг всех игроков на сервере:", color="#A6ACCD"),
                ft.Container(height=10),
                users_list
            ],
            bgcolor="#1E1E2E",
        )

    # ===============================
    # СИСТЕМА НАВИГАЦИИ (РОУТИНГ)
    # ===============================
    def navigate(route):
        page.route = route
        route_change(route)
        
    def route_change(route):
        page.views.clear()
        if page.route == "/admin":
            page.views.append(get_admin_view())
        else:
            page.views.append(get_game_view())
        page.update()

    page.on_route_change = route_change
    navigate(page.route) # Открываем нужный экран при старте

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # Удаляем view=... чтобы избежать багов с переименованными модулями,
    # указание host и port автоматически запустит веб-версию!
    ft.run(main, host="0.0.0.0", port=port)
