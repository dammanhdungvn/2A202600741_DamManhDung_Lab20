"""Search client - mock implementation for offline/no-key usage."""

from multi_agent_research_lab.core.schemas import SourceDocument

_MOCK_CORPUS = [
    SourceDocument(
        title="Microsoft GraphRAG Documentation",
        url="https://github.com/microsoft/graphrag",
        snippet=(
            "GraphRAG is a structured, hierarchical approach to Retrieval-Augmented Generation. "
            "Unlike standard naive RAG which uses flat vector similarity, GraphRAG builds a "
            "knowledge graph from input text and detects communities. It then generates summaries "
            "for these communities to answer global, high-level questions about a dataset."
        ),
        metadata={"category": "GraphRAG"},
    ),
    SourceDocument(
        title="LangGraph: Building Agentic Graph Workflows",
        url="https://langchain-ai.github.io/langgraph/",
        snippet=(
            "LangGraph is a library for building stateful, multi-actor applications with LLMs. "
            "It extends LangChain by allowing developers to define cycles and state machines as "
            "graphs. This is crucial for agentic behaviors such as supervisor-worker routing, "
            "reflection loops, and multi-agent collaboration."
        ),
        metadata={"category": "LangGraph"},
    ),
    SourceDocument(
        title="Agentic Workflows and Design Patterns by Andrew Ng",
        url="https://www.deeplearning.ai/the-batch/how-agentic-workflows-will-drive-ai-progress/",
        snippet=(
            "Andrew Ng highlights that agentic design patterns such as reflection, tool use, "
            "planning, and multi-agent collaboration often produce better results than running "
            "a larger model in zero-shot mode. Multi-agent collaboration splits complex tasks "
            "among specialized personas with clear state handoffs."
        ),
        metadata={"category": "Agentic Workflows"},
    ),
    SourceDocument(
        title="GraphRAG vs Naive RAG Benchmarks",
        url="https://arxiv.org/abs/2404.16130",
        snippet=(
            "Recent research shows GraphRAG significantly outperforms vector-only Naive RAG "
            "on multi-hop reasoning and dataset-wide thematic queries. However, it incurs higher "
            "token costs and latency due to knowledge graph construction and community summary maps."
        ),
        metadata={"category": "GraphRAG"},
    ),
    SourceDocument(
        title="Multi-Agent Systems: Coordination and Handoffs",
        url="https://openai.com/research/multi-agent-coordination",
        snippet=(
            "Designing effective multi-agent systems requires establishing clear handoff rules, "
            "a centralized or distributed state representation, and guardrails to prevent infinite "
            "loop delegations. Centralized supervisors route tasks based on intent-matching prompts."
        ),
        metadata={"category": "Multi-Agent Systems"},
    ),
]


class SearchClient:
    """Provider-agnostic search client - mock implementation for offline usage."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query using static mock corpus."""
        q = query.lower()

        # Match docs where query keywords appear in category or title
        results = [
            doc
            for doc in _MOCK_CORPUS
            if doc.metadata.get("category", "").lower() in q
            or any(word in doc.title.lower() for word in q.split() if len(word) > 3)
        ]

        # Fall back to full corpus if no keyword matches
        if not results:
            results = list(_MOCK_CORPUS)

        return results[:max_results]
