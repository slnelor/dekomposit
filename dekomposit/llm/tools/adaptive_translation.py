import asyncio
import logging
import os
import subprocess
from typing import Any, cast

import httpx
from dotenv import load_dotenv

from dekomposit.llm.tools.base import BaseTool


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()

DEFAULT_LOCATION = "us-central1"
TRANSLATION_SCOPE = "https://www.googleapis.com/auth/cloud-translation"


class AdaptiveTranslationTool(BaseTool):
    """Tool for Cloud Translation Adaptive MT datasets."""

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        dataset_id: str | None = None,
        dataset_name: str | None = None,
    ) -> None:
        super().__init__(
            name="adaptive_translation",
            description="Translate text using Cloud Translation Adaptive MT datasets",
        )
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("ADAPTIVE_MT_LOCATION", DEFAULT_LOCATION)
        self.dataset_id = dataset_id or os.getenv("ADAPTIVE_MT_DATASET_ID")
        self.dataset_name = dataset_name or os.getenv("ADAPTIVE_MT_DATASET_NAME")

    async def __call__(
        self,
        text: str | list[str],
        source_lang: str | None = None,
        target_lang: str | None = None,
        dataset_id: str | None = None,
        dataset_name: str | None = None,
        mime_type: str | None = None,
        access_token: str | None = None,
        timeout: float = 30.0,
        retry_on_unauthorized: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        project_id = self.project_id or os.getenv("PROJECT_ID")
        location = self.location or DEFAULT_LOCATION

        dataset_id = dataset_id or self.dataset_id
        dataset_name = dataset_name or self.dataset_name

        if not dataset_id and source_lang and target_lang:
            dataset_id = f"adaptive-{source_lang.lower()}-{target_lang.lower()}"

        if not self.validate_input(text, project_id, location, dataset_id, dataset_name):
            raise ValueError("Invalid input for AdaptiveTranslationTool")

        if project_id is None or location is None:
            raise ValueError("Project id and location are required")

        resolved_dataset = self._resolve_dataset_name(
            project_id=project_id,
            location=location,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
        )
        if not resolved_dataset:
            raise ValueError("Dataset name or dataset id is required")

        content = [text] if isinstance(text, str) else list(text)

        payload: dict[str, Any] = {
            "dataset": resolved_dataset,
            "content": content,
        }
        if mime_type:
            payload["mimeType"] = mime_type

        token = await self._get_access_token(access_token)

        headers = {
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": project_id,
            "Content-Type": "application/json; charset=utf-8",
        }

        url = (
            f"https://translation.googleapis.com/v3/projects/{project_id}"
            f"/locations/{location}:adaptiveMtTranslate"
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 401 and retry_on_unauthorized:
                logger.warning("Unauthorized; refreshing token and retrying")
                token = await self._get_access_token(None, allow_env=False)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        logger.info(
            "Adaptive MT translate: %s (%s -> %s)",
            resolved_dataset,
            source_lang or "dataset",
            target_lang or "dataset",
        )

        return {
            "request": {
                "dataset": resolved_dataset,
                "content": content,
                "mime_type": mime_type,
            },
            "response": data,
        }

    def validate_input(
        self,
        text: str | list[str],
        project_id: str | None,
        location: str | None,
        dataset_id: str | None,
        dataset_name: str | None,
        **kwargs: Any,
    ) -> bool:
        if not text:
            logger.error("Text is empty")
            return False
        if isinstance(text, list) and not any(item.strip() for item in text if item):
            logger.error("All content entries are empty")
            return False
        if not project_id:
            logger.error("Project id is required")
            return False
        if not location:
            logger.error("Location is required")
            return False
        if not dataset_id and not dataset_name:
            logger.error("Dataset id or dataset name is required")
            return False
        return True

    def _resolve_dataset_name(
        self,
        project_id: str,
        location: str,
        dataset_id: str | None,
        dataset_name: str | None,
    ) -> str | None:
        if dataset_name:
            return dataset_name
        if dataset_id:
            return (
                f"projects/{project_id}/locations/{location}"
                f"/adaptiveMtDatasets/{dataset_id}"
            )
        return None

    async def _get_access_token(
        self, access_token: str | None, allow_env: bool = True
    ) -> str:
        if access_token:
            return access_token

        prefer_adc = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        if not prefer_adc:
            env_token = os.getenv("GOOGLE_OAUTH_ACCESS_TOKEN") if allow_env else None
            if env_token:
                return env_token

        try:
            import google.auth  # type: ignore[import-not-found]
            from google.auth.transport.requests import Request  # type: ignore[import-not-found]

            def refresh_token() -> str:
                credentials, _ = google.auth.default(scopes=[TRANSLATION_SCOPE])
                credentials = cast(Any, credentials)
                credentials.refresh(Request())
                if not credentials.token:
                    raise RuntimeError("Failed to obtain access token")
                return credentials.token

            return await asyncio.to_thread(refresh_token)
        except Exception as exc:
            logger.warning("ADC unavailable, falling back to gcloud: %s", exc)
            return await asyncio.to_thread(self._get_gcloud_token)

    @staticmethod
    def _get_gcloud_token() -> str:
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "gcloud CLI not found; install it or set GOOGLE_OAUTH_ACCESS_TOKEN"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else ""
            raise RuntimeError(
                f"gcloud auth print-access-token failed: {stderr}"
            ) from exc

        token = result.stdout.strip()
        if not token:
            raise RuntimeError("gcloud returned an empty access token")
        return token
