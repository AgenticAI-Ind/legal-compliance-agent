"""
Database configuration and management for Legal & Compliance Agent.
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.exc import SQLAlchemyError
import os

from src.models import Base


logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: Optional[str] = None, echo: bool = False):
        """
        Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/legal_compliance"
        )
        self.echo = echo or os.getenv("SQL_ECHO", "false").lower() == "true"

        # Configure engine with connection pooling
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Database manager initialized")

    def _create_engine(self):
        """Create SQLAlchemy engine with appropriate configuration."""
        # Parse URL to determine if it's SQLite
        is_sqlite = self.database_url.startswith("sqlite")

        engine_kwargs = {
            "echo": self.echo,
            "future": True,
        }

        if is_sqlite:
            # SQLite configuration
            engine_kwargs["poolclass"] = NullPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # PostgreSQL configuration
            engine_kwargs["poolclass"] = QueuePool
            engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "5"))
            engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "10"))
            engine_kwargs["pool_timeout"] = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "3600"))
            engine_kwargs["pool_pre_ping"] = True

        engine = create_engine(self.database_url, **engine_kwargs)

        # Set up event listeners
        self._setup_event_listeners(engine)

        return engine

    def _setup_event_listeners(self, engine):
        """Set up SQLAlchemy event listeners for monitoring."""
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Handle new database connections."""
            logger.debug("New database connection established")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Handle connection checkout from pool."""
            logger.debug("Connection checked out from pool")

    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def drop_tables(self):
        """Drop all database tables. Use with caution!"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {e}")
            raise

    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a database session.

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations.

        Yields:
            Database session with automatic commit/rollback
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Check database health.

        Returns:
            True if database is healthy, False otherwise
        """
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def close(self):
        """Close database connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get or create global database manager instance.

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to inject database sessions.

    Yields:
        Database session
    """
    db_manager = get_db_manager()
    yield from db_manager.get_session()


def init_db():
    """Initialize database (create tables)."""
    db_manager = get_db_manager()
    db_manager.create_tables()
    logger.info("Database initialized")


def close_db():
    """Close database connections."""
    global _db_manager
    if _db_manager is not None:
        _db_manager.close()
        _db_manager = None


# Repository pattern for database operations
class BaseRepository:
    """Base repository for database operations."""

    def __init__(self, session: Session):
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    def add(self, obj):
        """Add object to session."""
        self.session.add(obj)
        return obj

    def delete(self, obj):
        """Delete object from session."""
        self.session.delete(obj)

    def commit(self):
        """Commit current transaction."""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Commit error: {e}")
            self.session.rollback()
            raise

    def rollback(self):
        """Rollback current transaction."""
        self.session.rollback()

    def flush(self):
        """Flush pending changes."""
        self.session.flush()


class DocumentRepository(BaseRepository):
    """Repository for document operations."""

    def get_by_id(self, document_id: str):
        """Get document by ID."""
        from src.models import DocumentRecord
        return self.session.query(DocumentRecord).filter(
            DocumentRecord.document_id == document_id
        ).first()

    def get_by_content_hash(self, content_hash: str):
        """Get document by content hash."""
        from src.models import DocumentRecord
        return self.session.query(DocumentRecord).filter(
            DocumentRecord.content_hash == content_hash
        ).first()

    def get_all(self, limit: int = 100, offset: int = 0):
        """Get all documents with pagination."""
        from src.models import DocumentRecord
        return self.session.query(DocumentRecord).offset(offset).limit(limit).all()


class AnalysisRepository(BaseRepository):
    """Repository for analysis operations."""

    def get_by_document_id(self, document_id: str):
        """Get all analyses for a document."""
        from src.models import AnalysisRecord
        return self.session.query(AnalysisRecord).filter(
            AnalysisRecord.document_id == document_id
        ).all()

    def get_by_analysis_type(self, analysis_type: str, limit: int = 100):
        """Get analyses by type."""
        from src.models import AnalysisRecord
        return self.session.query(AnalysisRecord).filter(
            AnalysisRecord.analysis_type == analysis_type
        ).limit(limit).all()


class ComplianceCheckRepository(BaseRepository):
    """Repository for compliance check operations."""

    def get_by_document_id(self, document_id: str):
        """Get all compliance checks for a document."""
        from src.models import ComplianceCheckRecord
        return self.session.query(ComplianceCheckRecord).filter(
            ComplianceCheckRecord.document_id == document_id
        ).all()

    def get_by_framework(self, framework: str, limit: int = 100):
        """Get compliance checks by framework."""
        from src.models import ComplianceCheckRecord
        return self.session.query(ComplianceCheckRecord).filter(
            ComplianceCheckRecord.framework == framework
        ).limit(limit).all()


class RiskRepository(BaseRepository):
    """Repository for risk operations."""

    def get_by_document_id(self, document_id: str):
        """Get all risks for a document."""
        from src.models import RiskRecord
        return self.session.query(RiskRecord).filter(
            RiskRecord.document_id == document_id
        ).all()

    def get_by_risk_level(self, risk_level: str, limit: int = 100):
        """Get risks by level."""
        from src.models import RiskRecord
        return self.session.query(RiskRecord).filter(
            RiskRecord.risk_level == risk_level
        ).limit(limit).all()

    def get_unresolved_risks(self, limit: int = 100):
        """Get unresolved risks."""
        from src.models import RiskRecord
        return self.session.query(RiskRecord).filter(
            RiskRecord.resolved == False
        ).limit(limit).all()
