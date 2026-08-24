"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./greenlit.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    try:
        from app.database.models import (
            Script, ScriptVersion, Scene, SceneRiskAnalysis,
            Character, CharacterAppearance, ContinuityIssue,
            Comment, TeamMember, ReviewStatus,
            NotificationSettings, Notification, ExportRequest,
            CostEstimate, UploadedFile, Analytics
        )

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def create_indexes():
    try:
        with engine.connect() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_scripts_user_id ON scripts(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status);",
                "CREATE INDEX IF NOT EXISTS idx_scripts_risk_score ON scripts(risk_score);",
                "CREATE INDEX IF NOT EXISTS idx_scenes_script_id ON scenes(script_id);",
                "CREATE INDEX IF NOT EXISTS idx_characters_script_id ON characters(script_id);",
                "CREATE INDEX IF NOT EXISTS idx_comments_script_id ON comments(script_id);",
                "CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);",
            ]

            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                except Exception as e:
                    logger.debug(f"Index creation skipped: {e}")

            conn.commit()
            logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error(f"Index creation failed: {e}")


VALID_TABLES = {
    'scripts', 'scenes', 'characters', 'comments',
    'notifications', 'export_requests'
}


class DatabaseManager:

    @staticmethod
    def health_check():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    def get_stats():
        try:
            with engine.connect() as conn:
                stats = {}
                for table in VALID_TABLES:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        stats[table] = result.scalar()
                    except Exception:
                        stats[table] = 0

                return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}


if __name__ != "__main__":
    try:
        init_db()
        create_indexes()
    except Exception as e:
        logger.warning(f"Database initialization delayed: {e}")
