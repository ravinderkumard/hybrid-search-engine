import logging

from app.pipeline.stackoverflow_pipeline import (
    StackOverflowPipeline,
)

logging.basicConfig(
    level=logging.INFO
)


if __name__ == "__main__":

    pipeline = StackOverflowPipeline(
        xml_path="/Users/ravinderkumar/Downloads/Posts.xml",
        batch_size=50,
        limit=1000,
    )

    pipeline.run()