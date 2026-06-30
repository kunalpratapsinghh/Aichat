import os
from dataclasses import dataclass
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    client: AsyncOpenAI
    model: str
    provider: str


def _build() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "ollama":
        return LLMConfig(
            client=AsyncOpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",  # Ollama ignores this but the client requires a value
            ),
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            provider="ollama",
        )

    if provider == "openai":
        return LLMConfig(
            client=AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            provider="openai",
        )

    raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Choose 'openai' or 'ollama'.")


llm = _build()
