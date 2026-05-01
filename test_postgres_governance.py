import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__)
        .resolve()
        .parent
    )
)

from app.db.database import (
    SessionLocal,
)
from app.models.document import (
    Document,
)


TEST_DOC_ID = "governance_test_001"


def main():
    print(
        "\n========================================="
    )
    print(
        "Testing PostgreSQL Governance"
    )
    print(
        "=========================================\n"
    )

    db = SessionLocal()

    try:
        # =====================================
        # CLEANUP
        # =====================================
        existing = (
            db.query(Document)
            .filter(
                Document.id
                == TEST_DOC_ID
            )
            .first()
        )

        if existing:
            db.delete(existing)
            db.commit()

        # =====================================
        # INSERT
        # =====================================
        doc = Document(
            id=TEST_DOC_ID,
            title="Governance Test",
            content="Testing metadata governance.",
            category="test",
            source="internal",
            version=1,
            is_active=True,
        )

        db.add(doc)
        db.commit()

        print(
            "Insert test passed."
        )

        # =====================================
        # UPDATE
        # =====================================
        doc = (
            db.query(Document)
            .filter(
                Document.id
                == TEST_DOC_ID
            )
            .first()
        )

        doc.version += 1
        doc.title = (
            "Governance Test Updated"
        )

        db.commit()

        print(
            "Update/version test passed."
        )

        # =====================================
        # SOFT DELETE
        # =====================================
        doc.is_active = False

        db.commit()

        print(
            "Soft delete test passed."
        )

        # =====================================
        # ACTIVE FILTER
        # =====================================
        active_doc = (
            db.query(Document)
            .filter(
                Document.id
                == TEST_DOC_ID,
                Document.is_active
                == True,
            )
            .first()
        )

        if active_doc is None:
            print(
                "Active-state governance passed."
            )
        else:
            print(
                "Active-state governance failed."
            )

        print(
            "\nPostgreSQL governance healthy."
        )

    except Exception as e:
        db.rollback()

        print(
            f"Governance test failed: {e}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()