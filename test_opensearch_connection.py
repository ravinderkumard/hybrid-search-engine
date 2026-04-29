from app.core.opensearch_client import OpenSearchClient


def main():
    print(
        "\nTesting OpenSearch connectivity...\n"
    )

    healthy = (
        OpenSearchClient.health_check()
    )

    if healthy:
        print(
            "OpenSearch connection successful."
        )

        info = (
            OpenSearchClient
            .get_cluster_info()
        )

        print(
            "\nCluster Info:"
        )

        print(info)

    else:
        print(
            "OpenSearch connection failed."
        )


if __name__ == "__main__":
    main()