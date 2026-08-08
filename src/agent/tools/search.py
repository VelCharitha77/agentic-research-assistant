from abc import ABC, abstractmethod

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from agent.config import settings
from agent.state import Citation


class SearchToolError(Exception):
    """Raised when the underlying search provider fails."""


class SearchTool(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[Citation]:
        """Return a list of citations relevant to the query."""


class TavilySearchTool(SearchTool):
    def __init__(self):
        import tavily

        self._client = tavily.TavilyClient(api_key=settings.tavily_api_key)

    def search(self, query: str, max_results: int = 5) -> list[Citation]:
        try:
            response = self._client.search(query=query, max_results=max_results)
        except Exception as exc:
            raise SearchToolError(f"Tavily search failed for query={query!r}") from exc

        return [
            Citation(url=r["url"], title=r.get("title", ""), snippet=r.get("content", ""))
            for r in response.get("results", [])
        ]


class FakeSearchTool(SearchTool):
    """Test double. `fail_times` simulates N transient failures before succeeding."""

    def __init__(self, results: list[Citation] | None = None, fail_times: int = 0):
        self._results = results if results is not None else []
        self._fail_times = fail_times
        self.calls: list[str] = []

    def search(self, query: str, max_results: int = 5) -> list[Citation]:
        self.calls.append(query)
        if self._fail_times > 0:
            self._fail_times -= 1
            raise SearchToolError(f"Simulated failure for query={query!r}")
        return list(self._results)


class RetryingSearchTool(SearchTool):
    """Wraps any SearchTool with exponential-backoff retries on transient failures."""

    def __init__(self, wrapped: SearchTool, max_attempts: int = 3, wait_seconds: float = 0.5):
        self._wrapped = wrapped
        self._max_attempts = max_attempts
        self._wait_seconds = wait_seconds

    def search(self, query: str, max_results: int = 5) -> list[Citation]:
        for attempt in Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(
                multiplier=self._wait_seconds, min=self._wait_seconds, max=self._wait_seconds * 8
            ),
            retry=retry_if_exception_type(SearchToolError),
            reraise=True,
        ):
            with attempt:
                return self._wrapped.search(query, max_results)
