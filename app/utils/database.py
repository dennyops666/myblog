from contextlib import contextmanager
from app.extensions import db

@contextmanager
def session_scope():
    """提供事务范围的会话"""
    session = db.create_scoped_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close() 