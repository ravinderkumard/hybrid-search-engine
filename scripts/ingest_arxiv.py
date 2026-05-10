from app.pipeline.arxiv_pipeline import (
    ArxivPipeline,
)


if __name__ == "__main__":

    pipeline = ArxivPipeline(
        batch_size=50,
        limit=1000,
    )

    pipeline.run()