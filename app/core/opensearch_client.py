from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from app.core.config import settings


class OpenSearchClient:
    """
    Singleton OpenSearch client for production-grade sparse retrieval.

    Why:
    - Centralized connection management
    - Reusable across services
    - Better resource efficiency
    - Health validation
    - Scalable for 1M+ docs
    """

    _client = None

    @classmethod
    def get_client(cls) -> OpenSearch:
        """
        Returns singleton OpenSearch client instance.
        """
        if cls._client is None:
            cls._client = OpenSearch(
                hosts=[
                    {
                        "host": settings.OPENSEARCH_HOST,
                        "port": settings.OPENSEARCH_PORT,
                    }
                ],
                http_auth=(
                    settings.OPENSEARCH_USERNAME,
                    settings.OPENSEARCH_PASSWORD,
                ),
                use_ssl=settings.OPENSEARCH_USE_SSL,
                verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )

        return cls._client

    @classmethod
    def health_check(cls) -> bool:
        """
        Validates OpenSearch connectivity.

        Returns:
            bool: True if reachable, False otherwise
        """
        try:
            client = cls.get_client()
            return client.ping()
        except OpenSearchConnectionError:
            return False
        except Exception:
            return False

    @classmethod
    def get_cluster_info(cls) -> dict:
        """
        Returns OpenSearch cluster metadata.

        Useful for:
        - Debugging
        - Monitoring
        - Health endpoints
        """
        try:
            client = cls.get_client()
            return client.info()
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
            }