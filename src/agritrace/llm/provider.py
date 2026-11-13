"""Chat completions against an OpenAI-compatible endpoint, or a local mock."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from agritrace.config import Settings

NARRATIVE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Phrase the grounded traceability answer in two sentences. "
            "Do not add lot, certificate, site, or shipment ids that are not already present.",
        ),
        ("human", "Question: {question}\nGrounded answer:\n{answer}"),
    ]
)


class LLMClient:
    kind = "base"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError

    def narrate(self, question: str, answer: str) -> str:
        prompt = NARRATIVE_PROMPT.format_messages(question=question, answer=answer)
        rendered = "\n".join(f"{message.type}: {message.content}" for message in prompt)
        return self.complete(
            "Phrase the grounded answer. Do not invent identifiers.",
            rendered,
        )


class MockLLM(LLMClient):
    """Deterministic stand-in. It never invents a lot id."""

    kind = "mock"

    def complete(self, system: str, user: str) -> str:
        return "Mock LLM: the grounded answer above is the system of record for this demo."


class OpenAICompatibleLLM(LLMClient):
    kind = "openai"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(self, system: str, user: str) -> str:
        import httpx

        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is empty while LLM_MODE=openai")
        response = httpx.post(
            f"{self.settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        content: str = response.json()["choices"][0]["message"]["content"]
        return content


def build_llm(settings: Settings) -> LLMClient:
    if settings.llm_mode == "openai":
        return OpenAICompatibleLLM(settings)
    if settings.llm_mode != "mock":
        raise RuntimeError(f"unknown LLM_MODE {settings.llm_mode}")
    return MockLLM()
