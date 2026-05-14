from opensearchpy import OpenSearch

from app.core.config import settings


class OpenSearchSyncClient:

    _client = None

    @classmethod
    def get_client(cls):

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