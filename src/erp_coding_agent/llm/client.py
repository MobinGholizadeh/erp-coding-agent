from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
import json
import asyncio
import logging

from .models import LLMRequest, LLMResponse, TokenUsage, Message
from ..config.settings import LLMSettings
from ..error_handling.exceptions import LLMAPIError, LLMTimeoutError

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        pass

class QwenClient(LLMClient):
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.base_url = settings.base_url.rstrip("/")
        self.api_key = settings.api_key or "sk-no-key"
        self.timeout = settings.timeout_seconds
        self.max_retries = settings.max_retries
        self.default_model = settings.model

    def _prepare_payload(self, request: LLMRequest) -> Dict[str, Any]:
        payload = {
            "model": request.model or self.default_model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "temperature": request.temperature if request.temperature is not None else self.settings.temperature,
            "max_tokens": request.max_tokens if request.max_tokens is not None else self.settings.max_tokens,
        }
        
        if request.response_format:
            # Check if using the official structured output way or just expecting JSON
            # For Qwen via compatible API, usually response_format={"type": "json_object"}
            payload["response_format"] = {"type": "json_object"}
            # Optionally embed the schema in the system prompt if needed, 
            # but here we rely on the caller to have structured the prompt correctly.
            
        return {k: v for k, v in payload.items() if v is not None}

    async def _execute_with_retries(self, client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
        attempt = 0
        while attempt <= self.max_retries:
            try:
                response = await client.request(method, url, **kwargs)
                if response.status_code == 200:
                    return response
                
                # If rate limited or server error, we retry
                if response.status_code in [429, 500, 502, 503, 504]:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise LLMAPIError(f"LLM API failed after {self.max_retries} retries: {response.status_code} {response.text}")
                    
                    delay = 2 ** attempt
                    logger.warning(f"LLM API error {response.status_code}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                
                # Other errors are not retried
                raise LLMAPIError(f"LLM API error: {response.status_code} {response.text}")
                
            except httpx.TimeoutException as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise LLMTimeoutError(f"LLM API request timed out after {self.max_retries} retries") from e
                
                delay = 2 ** attempt
                logger.warning(f"LLM API timeout, retrying in {delay}s...")
                await asyncio.sleep(delay)
            except httpx.RequestError as e:
                raise LLMAPIError(f"LLM API request error: {str(e)}") from e

    async def generate(self, request: LLMRequest) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._prepare_payload(request)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await self._execute_with_retries(
                client, 
                "POST", 
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            data = response.json()
            message = data["choices"][0]["message"]
            content = message.get("content", "")
            
            usage_data = data.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )
            
            structured_data = None
            if request.response_format and content:
                try:
                    structured_data = json.loads(content)
                except json.JSONDecodeError:
                    # Depending on strictness, we might log a warning or raise an exception
                    logger.warning("Failed to decode structured output as JSON")
            
            return LLMResponse(content=content, usage=usage, structured_data=structured_data)

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = self._prepare_payload(request)
        payload["stream"] = True
        
        # We don't use _execute_with_retries for streaming because it's harder to retry cleanly mid-stream
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST", 
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status_code != 200:
                        text = await response.aread()
                        raise LLMAPIError(f"LLM streaming API error: {response.status_code} {text.decode('utf-8')}")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            data_str = line[len("data: "):]
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
            except httpx.TimeoutException as e:
                raise LLMTimeoutError("LLM API request timed out during stream") from e

class MockLLM(LLMClient):
    def __init__(self):
        self.responses: List[LLMResponse] = []
        self.stream_responses: List[List[str]] = []
        
    def queue_response(self, response: LLMResponse):
        self.responses.append(response)
        
    def queue_stream(self, chunks: List[str]):
        self.stream_responses.append(chunks)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.responses:
            return LLMResponse(content="Default mock response")
        return self.responses.pop(0)

    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        if not self.stream_responses:
            yield "Default mock stream chunk"
            return
            
        chunks = self.stream_responses.pop(0)
        for chunk in chunks:
            yield chunk
