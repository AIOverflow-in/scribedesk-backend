import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.dependencies.auth import CurrentUserIdDep
from src.dependencies.infra import PubSubManagerDep

router = APIRouter()


@router.get("/events")
async def event_stream(
    user_id: CurrentUserIdDep,
    pubsub: PubSubManagerDep,
):
    async def event_generator():
        async for message in pubsub.subscribe(str(user_id)):
            yield f"data: {json.dumps(message)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
