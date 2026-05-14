import os
import time
import logging

from opensearchpy import AsyncOpenSearch

# =========================================
# LOGGING
# =========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("opensearch_init")

# =========================================
# CONFIG
# =========================================
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "opensearch")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 9200))

INDEX_NAME = "hybrid-search-documents"

# =========================================
# CLIENT
# =========================================
client = AsyncOpenSearch(
    hosts=[{
        "host": OPENSEARCH_HOST,
        "port": OPENSEARCH_PORT
    }],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

# =========================================
# WAIT FOR OPENSEARCH
# =========================================
def wait_for_opensearch(
    retries: int = 20,
    delay: int = 5
):
    for attempt in range(1, retries + 1):
        try:
            if client.ping():
                logger.info(
                    "OpenSearch is reachable."
                )
                return
        except Exception as e:
            logger.warning(
                f"Waiting for OpenSearch... "
                f"Attempt {attempt}/{retries} "
                f"failed: {e}"
            )

        time.sleep(delay)

    raise RuntimeError(
        "OpenSearch did not become ready in time."
    )

# =========================================
# CREATE INDEX
# =========================================
def create_index():
    if client.indices.exists(
        index=INDEX_NAME
    ):
        logger.info(
            f"Index '{INDEX_NAME}' already exists."
        )
        return

    index_body = {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        },
        "mappings": {
            "properties": {
                "document_id": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text"
                },
                "content": {
                    "type": "text"
                },
                "category": {
                    "type": "keyword"
                },
                "source": {
                    "type": "keyword"
                },
                "published_at": {
                    "type": "date"
                }
            }
        }
    }

    response = client.indices.create(
        index=INDEX_NAME,
        body=index_body
    )

    logger.info(
        f"Created index '{INDEX_NAME}': "
        f"{response}"
    )

# =========================================
# MAIN
# =========================================
def main():
    logger.info(
        "Starting OpenSearch bootstrap..."
    )

    wait_for_opensearch()

    create_index()

    logger.info(
        "OpenSearch bootstrap completed successfully."
    )

# =========================================
# ENTRYPOINT
# =========================================
if __name__ == "__main__":
    main()