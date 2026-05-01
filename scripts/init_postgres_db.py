import sys
from pathlib import Path

# =========================================
# PROJECT ROOT FIX
# =========================================
sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parent.parent
    )
)

from app.db.database import (
    engine,
    Base,
)

# Import models so metadata registers
from app.models.document import (
    Document,
)


def main():
    print(
        "\n========================================="
    )
    print(
        "Initializing PostgreSQL Schema"
    )
    print(
        "=========================================\n"
    )

    try:
        # =================================
        # CREATE TABLES
        # =================================
        Base.metadata.create_all(
            bind=engine
        )

        print(
            "PostgreSQL tables created successfully."
        )

        print(
            "\nCreated tables:"
        )

        for table in (
            Base.metadata.tables.keys()
        ):
            print(
                f"- {table}"
            )

    except Exception as e:
        print(
            f"Schema initialization failed: {e}"
        )


if __name__ == "__main__":
    main()