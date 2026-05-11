from src.schemas.api.chat import StreamChunk


def format_chunk(chunk: StreamChunk) -> str:
    return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
