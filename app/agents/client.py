from app.agents.retrieval.retrieval_agent import RetrievalAgent
from app.agents.retrieval.retrieval_schema import RetrievalRequest
from app.utils.model_loader import ModelLoader


def main() -> None:
    model_loader = ModelLoader(model_provider="openai")
    model = model_loader.load_llm()

    agent = RetrievalAgent(model)

    decision = agent.decide(
        RetrievalRequest(
            query="Explain LoginService API"
        )
    )

    print(decision)


if __name__ == "__main__":
    main()
