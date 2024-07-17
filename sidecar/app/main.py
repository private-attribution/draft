from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .query.base import QueryManager
from .routes import start, stop, websockets

app = FastAPI()
app.state.QUERY_MANAGER = QueryManager(max_parallel_queries=1)
app.include_router(websockets.router)
app.include_router(start.router)
app.include_router(stop.router)

origins = ["https://draft.test", "https://draft-mpc.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/status")
async def status():
    return {"status": "up"}
