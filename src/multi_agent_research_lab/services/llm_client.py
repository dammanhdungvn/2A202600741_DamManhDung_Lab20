import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

# Global rate limiter state to ensure < 40 RPM (1 call every 1.5 seconds)
_rate_limit_lock = threading.Lock()
_last_call_time = 0.0

def _wait_for_rate_limit() -> None:
    global _last_call_time
    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_call_time
        spacing = 1.6  # Safe gap to respect 40 RPM
        if elapsed < spacing:
            sleep_time = spacing - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        _last_call_time = time.time()


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client implementation."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model
        
        # Check that we have credentials
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured in environment or .env file.")
            
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _call_api_with_retry(self, system_prompt: str, user_prompt: str) -> Any:
        # Enforce rate limit before calling API
        _wait_for_rate_limit()
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            top_p=1.0,
            max_tokens=4096,
            stream=False
        )
        return completion

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""
        try:
            completion = self._call_api_with_retry(system_prompt, user_prompt)
            content = completion.choices[0].message.content or ""
            
            # Extract token usage if available
            input_tokens = None
            output_tokens = None
            cost_usd = None
            if completion.usage:
                input_tokens = completion.usage.prompt_tokens
                output_tokens = completion.usage.completion_tokens
                # Nvidia/OpenAI pricing estimate (e.g. $0.15/1M input, $0.60/1M output tokens)
                cost_usd = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
                
            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd
            )
        except Exception as e:
            logger.error(f"Error during LLMClient.complete call: {e}")
            raise e

