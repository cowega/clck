from pydantic import BaseModel

class Movietop(BaseModel):
    name: str
    id: int
    cost: int
    director: str
    is_published: bool
    cover: str
