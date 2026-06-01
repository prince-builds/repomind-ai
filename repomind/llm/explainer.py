"""Groq-powered chat completion client."""

from groq import APIConnectionError, APIStatusError, Groq

from repomind.llm.prompts import SYSTEM_PROMPT
from repomind.utils.config import DEFAULT_GROQ_BASE_URL, get_settings, normalize_groq_base_url

DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = DEFAULT_GROQ_BASE_URL
MISSING_GROQ_KEY_MESSAGE = "Missing GROQ_API_KEY in .env"


class LLMConfigError(Exception):
    """Raised when LLM settings are missing or invalid."""


class LLMError(Exception):
    """Raised when the LLM API call fails."""


class LLMExplainer:
    """Send prompts to Groq chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        settings = get_settings()

        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.base_url = normalize_groq_base_url(
            base_url or settings.groq_base_url
        )

        if not self.api_key:
            raise LLMConfigError(MISSING_GROQ_KEY_MESSAGE)

        # Official SDK: default host is https://api.groq.com; resource paths
        # already include /openai/v1/... — do not pass base_url with /openai/v1.
        client_kwargs: dict[str, str] = {"api_key": self.api_key}
        if self.base_url != DEFAULT_GROQ_BASE_URL:
            client_kwargs["base_url"] = self.base_url

        self._client = Groq(**client_kwargs)

    def complete(
        self,
        user_prompt: str,
        system_prompt: str = SYSTEM_PROMPT,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

        except APIStatusError as exc:
            message = getattr(exc, "message", None) or str(exc)
            raise LLMError(f"Groq API error: {message}") from exc

        except APIConnectionError as exc:
            raise LLMError("Could not connect to Groq.") from exc

        except Exception as exc:
            raise LLMError(f"Unexpected Groq failure: {exc}") from exc

        choice = response.choices[0].message.content

        if not choice:
            raise LLMError("Groq returned an empty response.")

        return choice.strip()
