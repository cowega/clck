from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from models import Movietop

movies = {
    i: Movietop(
        name=f"movie{i}",
        id=i,
        cost=1000,
        director="ivan"
    ) for i in range(10)
}

app = FastAPI()

@app.get("/study", response_class=HTMLResponse)
def get_study_page():
    html = """
    <p>BGITU 2025</p>
    <img src='https://bgitu.ru/upload/iblock/b7f/b7f6432db000a9c863bec511569e36c8.jpg'>
    """
    return html

@app.get("/movietop/{id}")
def get_movie_by_id(id: int):
    return movies[id]

if __name__ == "__main__":
    uvicorn.run("main:app", port=8165, reload=True)
