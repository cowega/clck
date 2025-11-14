from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import shutil
import jwt

from models import Movietop

SECRET_KEY = "secret"
ALGORITHM = "HS256"

movies = {
    i: Movietop(
        name=f"movie{i}",
        id=i,
        cost=1000,
        director="ivan",
        is_published=True,
        cover="default.jpg"
    ) for i in range(10)
}

users = {
    "admin": "admin"
}

app = FastAPI()
security = HTTPBearer()

def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Токен истек"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Невалидный токен"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Невалидные учетные данные"
        )
    
    return payload

@app.get("/study", response_class=HTMLResponse)
def get_study_page():
    html = """
    <p>BGITU 2025</p>
    <img src='https://bgitu.ru/upload/iblock/b7f/b7f6432db000a9c863bec511569e36c8.jpg'>
    """
    return html

@app.get("/movietop", response_class=HTMLResponse)
def create_movie():
    html = """
    <body>
        <h2>Добавить фильм</h2>
        <div id="error" class="error"></div>
        <form id="movieForm">
            <div class="form-group">
                <label for="title">Название фильма:</label>
                <input type="text" id="title" name="title" required>
            </div>

            <div class="form-group">
                <label for="cost">Цена:</label>
                <input type="number" id="cost" name="cost" min="0" required>
            </div>
            
            <div class="form-group">
                <label for="director">Режиссер:</label>
                <input type="text" id="director" name="director" required>
            </div>
            
            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="is_published" name="is_published" value="true">
                    <label for="is_published">Опубликован</label>
                </div>
            </div>
            
            <div class="form-group">
                <label for="cover_file">Обложка фильма:</label>
                <input type="file" id="cover_file" name="cover_file" accept="image/*">
            </div>
            
            <button type="button" onclick="addMovie()">Добавить фильм</button>
        </form>

        <script>
            function addMovie() {
                const token = localStorage.getItem('jwt_token');
                if (!token) {
                    document.getElementById('error').textContent = 'Требуется авторизация. Сначала войдите в систему.';
                    return;
                }

                const formData = new FormData();
                formData.append('title', document.getElementById('title').value);
                formData.append('cost', document.getElementById('cost').value);
                formData.append('director', document.getElementById('director').value);
                formData.append('is_published', document.getElementById('is_published').checked);
                
                const coverFile = document.getElementById('cover_file').files[0];
                if (coverFile) {
                    formData.append('cover_file', coverFile);
                }

                fetch('/movietop', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + token
                    },
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        window.location.href = '/movietop/' + (Object.keys(movies).length - 1);
                    } else {
                        return response.json().then(err => {
                            document.getElementById('error').textContent = 'Ошибка: ' + err.detail;
                        });
                    }
                })
                .catch(error => {
                    document.getElementById('error').textContent = 'Ошибка: ' + error;
                });
            }

            window.onload = function() {
                const token = localStorage.getItem('jwt_token');
                if (!token) {
                    document.getElementById('error').textContent = 'Для добавления фильма требуется авторизация. Войдите в систему.';
                }
            };
        </script>
    </body>
    </html>
    """
    return html

@app.post("/movietop")
async def api_create_movie(
    request: Request,
    title: str = Form(...),
    cost: int = Form(...),
    director: str = Form(...),
    is_published: bool = Form(False),
    cover_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    cover_filename = "default.jpg"
    if cover_file:
        cover_filename = cover_file.filename
        with open(f"uploads/{cover_filename}", "wb") as buffer:
            shutil.copyfileobj(cover_file.file, buffer)
    
    new_id = len(movies)
    movies[new_id] = Movietop(
        name=title,
        id=new_id,
        cost=cost,
        director=director,
        is_published=is_published,
        cover=cover_filename
    )

    return RedirectResponse(f"/movietop/{new_id}", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_user():
    html = """
    <body>
        <h2>Вход в систему</h2>
        <div id="message"></div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Логин:</label>
                <input type="text" id="username" name="username" required>
            </div>

            <div class="form-group">
                <label for="password">Пароль:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="button" onclick="login()">Войти</button>
        </form>

        <script>
            function login() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.access_token) {
                        // Сохраняем JWT токен в localStorage
                        localStorage.setItem('jwt_token', data.access_token);
                        document.getElementById('message').innerHTML = '<div class="success">Успешный вход! Токен сохранен.</div>';
                        setTimeout(() => {
                            window.location.href = '/movietop';
                        }, 1000);
                    } else {
                        document.getElementById('message').innerHTML = '<div class="error">Ошибка: ' + data.detail + '</div>';
                    }
                })
                .catch(error => {
                    document.getElementById('message').innerHTML = '<div class="error">Ошибка сети: ' + error + '</div>';
                });
            }
        </script>
    </body>
    </html>
    """
    return html

@app.post("/login")
async def api_login_user(request: Request):
    """Endpoint для входа с JSON данными"""
    try:
        # Получаем JSON данные
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Требуется username и password")
        
        # Проверяем учетные данные
        if users.get(username) == password:
            token = create_jwt_token(username)
            
            return JSONResponse({
                "access_token": token,
                "token_type": "bearer",
                "username": username
            })
        else:
            raise HTTPException(status_code=401, detail="Неверные учетные данные")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail="Неверный формат данных")

@app.post("/login-form")
async def api_login_user_form(
    login: str = Form(...),
    password: str = Form(...),
):
    if users.get(login) == password:
        token = create_jwt_token(login)

        response = RedirectResponse("/movietop", status_code=303)
        response.set_cookie(key="session_token", value=token, max_age=2*60)
        return response
    else:
        response = RedirectResponse("/login", status_code=303)
        return response

@app.get("/user")
def get_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "user": {
            "username": current_user["sub"],
            "authenticated": True
        }
    }

@app.get("/movietop/{id}")
def get_movie_by_id(id: int):
    return movies[id]

if __name__ == "__main__":
    uvicorn.run("main:app", port=8165, reload=True)