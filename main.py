from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import os
import json

app = FastAPI()

# База данных сервера
global_db = {}
connections = []

HTML_GAME = """
<!DOCTYPE html>
<html>
<head>
    <title>Cloud Clicker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        body { background-color: #1E1E2E; color: white; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin: 0; padding: 20px; touch-action: manipulation; }
        #score { font-size: 80px; font-weight: bold; margin: 10px 0; text-shadow: 0 0 20px rgba(255, 0, 118, 0.5); transition: transform 0.1s; }
        .coin { width: 220px; height: 220px; background: linear-gradient(135deg, #FF0076, #FF5900); border-radius: 50%; margin: 40px auto; display: flex; align-items: center; justify-content: center; font-size: 54px; font-weight: 900; box-shadow: 0 10px 30px rgba(255, 0, 118, 0.4); user-select: none; transition: transform 0.05s ease-out; cursor: pointer; }
        .coin:active { transform: scale(0.9); }
        .btn { background: #FF5900; border: none; padding: 15px 30px; color: white; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; box-shadow: 0 5px 15px rgba(255, 89, 0, 0.3); transition: transform 0.1s; }
        .btn:active { transform: scale(0.95); }
        .header { display: flex; justify-content: space-between; align-items: center; }
        a { color: white; text-decoration: none; font-size: 24px; transition: opacity 0.2s; }
        a:active { opacity: 0.5; }
    </style>
</head>
<body>
    <div class="header">
        <div id="username" style="font-size:20px; font-weight:bold; color: #FFFFFF;">Загрузка...</div>
        <a href="/admin">⚙️</a>
    </div>
    <div style="color: #A6ACCD; font-weight: 500; margin-top: 40px;">СКОР</div>
    <div id="score">0</div>
    <div id="power" style="color: #A6ACCD; font-size: 16px;">Сила клика: 1</div>
    
    <div class="coin" onclick="clickCoin()">TAP</div>
    
    <button class="btn" id="upgradeBtn" onclick="buyUpgrade()">Улучшить силу (Цена: 50 💰)</button>

    <script>
        // Подключаемся к серверу по WebSocket
        let ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws');
        
        // Получаем уникальный ID устройства из памяти браузера, чтобы не терять прогресс при обновлении страницы!
        let myId = localStorage.getItem('user_id');
        if (!myId) {
            myId = Math.random().toString(36).substr(2, 9);
            localStorage.setItem('user_id', myId);
        }

        ws.onopen = () => {
            ws.send(JSON.stringify({action: "login", id: myId}));
        };

        ws.onmessage = (event) => {
            let data = JSON.parse(event.data);
            if (data.type === "state") {
                document.getElementById('username').innerText = "Привет, " + data.name + "!";
                document.getElementById('score').innerText = data.score;
                document.getElementById('power').innerText = "Сила клика: " + data.power;
                document.getElementById('upgradeBtn').innerText = "Улучшить силу (Цена: " + (data.power * 50) + " 💰)";
            }
        };

        function clickCoin() {
            ws.send(JSON.stringify({action: "click"}));
            // Микро-анимация счета
            let scoreEl = document.getElementById('score');
            scoreEl.style.transform = "scale(1.1)";
            setTimeout(() => scoreEl.style.transform = "scale(1)", 100);
        }

        function buyUpgrade() {
            ws.send(JSON.stringify({action: "upgrade"}));
        }
    </script>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Панель Администратора</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        body { background-color: #1E1E2E; color: white; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .header a { color: white; text-decoration: none; font-size: 24px; }
        .user-card { background: #292D3E; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .stats { color: #FF0076; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/">⬅ Назад</a>
        <h2 style="margin:0;">Админка</h2>
        <a href="#" onclick="loadAdmin()">🔄</a>
    </div>
    <div style="color: #A6ACCD; margin-bottom: 20px;">Рейтинг игроков в реальном времени:</div>
    <div id="users">Загрузка данных...</div>

    <script>
        async function loadAdmin() {
            let res = await fetch('/api/admin_data');
            let data = await res.json();
            let html = "";
            data.forEach(user => {
                html += `<div class="user-card">
                    <div><strong>👤 ${user.name}</strong></div>
                    <div class="stats">Очки: ${user.score} | Сила: ${user.power}</div>
                </div>`;
            });
            document.getElementById('users').innerHTML = html;
        }
        loadAdmin();
        // Автообновление таблицы рекордов каждую секунду!
        setInterval(loadAdmin, 1000); 
    </script>
</body>
</html>
"""

@app.get("/")
async def get_game():
    return HTMLResponse(HTML_GAME)

@app.get("/admin")
async def get_admin():
    return HTMLResponse(HTML_ADMIN)

@app.get("/api/admin_data")
async def api_admin():
    # Сортируем игроков по очкам
    sorted_users = sorted(global_db.values(), key=lambda x: x['score'], reverse=True)
    return sorted_users

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    user_id = None
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg["action"] == "login":
                user_id = msg["id"]
                if user_id not in global_db:
                    global_db[user_id] = {"score": 0, "power": 1, "name": f"Игрок {user_id[:4]}"}
                await websocket.send_text(json.dumps({"type": "state", **global_db[user_id]}))
                
            elif msg["action"] == "click" and user_id:
                global_db[user_id]["score"] += global_db[user_id]["power"]
                await websocket.send_text(json.dumps({"type": "state", **global_db[user_id]}))
                
            elif msg["action"] == "upgrade" and user_id:
                cost = global_db[user_id]["power"] * 50
                if global_db[user_id]["score"] >= cost:
                    global_db[user_id]["score"] -= cost
                    global_db[user_id]["power"] += 1
                await websocket.send_text(json.dumps({"type": "state", **global_db[user_id]}))
                
    except WebSocketDisconnect:
        connections.remove(websocket)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
