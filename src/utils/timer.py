import time
import functools
from typing import Callable, Any
from src.core.logging import get_logger

logger = get_logger(__name__)

def measure_time(operation_name: str = None):
    """
    Async decorator to log execution time and track operation metrics.

    Logs both successful and failed operations with structured data for monitoring.
    Uses perf_counter() for high-precision timing measurements.
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            op_name = operation_name or func.__name__

            try:
                result = await func(*args, **kwargs)

                # Log successful operation with timing in milliseconds
                duration = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"{op_name} finished",
                    extra={
                        "event": "metric",
                        "operation": op_name,
                        "duration_ms": round(duration, 2),
                        "status": "success"
                    }
                )
                return result

            except Exception as e:
                # Still log timing for failed operations to identify bottlenecks
                duration = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"{op_name} failed",
                    extra={
                        "event": "metric",
                        "operation": op_name,
                        "duration_ms": round(duration, 2),
                        "status": "error",
                        "error_type": type(e).__name__
                    }
                )
                raise e

        return wrapper
    return decorator