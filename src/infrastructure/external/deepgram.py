from deepgram import DeepgramClient as DGClient
from deepgram.core.api_error import ApiError

from src.core.logging import get_logger
from src.core.config import settings
from src.core.exceptions import BadRequestException

logger = get_logger(__name__)


class DeepgramClient:
    """Deepgram Wrapper for speech-to-text. Handles temporary token generation."""

    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self._client: DGClient | None = None

    @property
    def client(self) -> DGClient:
        if self._client is None:
            self._client = DGClient(api_key=self.api_key)
        return self._client

    async def generate_temporary_token(self) -> str:
        """Generates temporary access token for frontend WebSocket."""
        try:
            response = self.client.auth.v1.tokens.grant()
            token = response.access_token

            if not token:
                raise BadRequestException("Deepgram returned empty token")

            logger.debug("Successfully generated Deepgram temporary token")
            return token

        except ApiError as e:
            logger.error(f"Deepgram token generation failed: {str(e)}")
            raise BadRequestException(f"Failed to generate Deepgram token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating Deepgram token: {str(e)}")
            raise BadRequestException("Failed to generate Deepgram token")