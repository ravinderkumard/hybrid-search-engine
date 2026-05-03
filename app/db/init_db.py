from app.db.database import Base, engine

# Import models so SQLAlchemy registers them
from app.models.document import Document


def init_db():
    Base.metadata.create_all(bind=engine)