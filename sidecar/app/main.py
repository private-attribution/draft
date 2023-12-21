from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import websockets
from .routes import start

app = FastAPI()
app.include_router(websockets.router)
app.include_router(start.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}