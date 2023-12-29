from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import start, stop, websockets

app = FastAPI()
app.include_router(websockets.router)
app.include_router(start.router)
app.include_router(stop.router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}
