from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import uvicorn
import shutil

from datetime import datetime

from models import Movietop

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
    "admin": {
        "password": "admin",
        "logins" : []
    }
}

app = FastAPI()

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
    <form action="/movietop/" method="post" enctype="multipart/form-data">
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
        
        <button type="submit">Добавить фильм</button>
    </form>
    """
    return html

@app.post("/movietop", response_class=RedirectResponse)
async def api_create_movie(
    request: Request,
    title: str = Form(...),
    cost: int = Form(...),
    director: str = Form(...),
    is_published: bool = Form(False),
    cover_file: UploadFile = File(None)
):
    with open(f"uploads/{cover_file.filename}", "wb") as buffer:
        shutil.copyfileobj(cover_file.file, buffer)
    
    movies[len(movies)] = Movietop(
        name=title,
        id=len(movies),
        cost=cost,
        director=director,
        is_published=is_published,
        cover=cover_file.filename
    )

    return RedirectResponse(f"/movietop/{len(movies) - 1}", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_user():
    html = """
    <form action="/login" method="post" enctype="multipart/form-data">
        <div class="form-group">
            <label for="login">Логин:</label>
            <input type="text" id="login" name="login" required>
        </div>

        <div class="form-group">
            <label for="password">Пароль:</label>
            <input type="text" id="password" name="password" required>
        </div>
        
        <button type="submit">Войти</button>
    </form>
    """
    return html

@app.post("/login")
def api_login_user(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
):
    if users.get(login, 0) and users[login]["password"] == password:
        users[login]["logins"].append(datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
        response = RedirectResponse("/user", status_code=303)
        response.set_cookie(key="session_token", value="admin", max_age=2*60)
    else:
        response = RedirectResponse("/login", status_code=303)
    return response

@app.get("/user")
def login_user(request: Request):
    token = request.cookies.get("session_token")
    if not token or token not in users:
        return {"message": "Unauthorized"}
    
    user_data = users[token]
    content = {
        "user": {
            "login": token,
            "password": user_data["password"],
            "logins": user_data["logins"]
        },
        "movies": {k: v.__dict__ for k, v in movies.items()}
    }
    response = JSONResponse(content=content)
    response.set_cookie(key="session_token", value=token, max_age=2*60)
    return response

@app.get("/movietop/{id}")
def get_movie_by_id(id: int):
    return movies[id]

if __name__ == "__main__":
    uvicorn.run("main:app", port=8165, reload=True)