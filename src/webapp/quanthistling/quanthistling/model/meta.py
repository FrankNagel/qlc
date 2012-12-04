"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData
from sqlalchemy.orm import scoped_session, sessionmaker, Query

__all__ = ['Session', 'metadata']

filtered = False

class CustomQuery(Query):
    def __new__(cls, *args, **kwargs):
        if args and hasattr(args[0][0], "filtered"):
            return Query(*args, **kwargs).filter_by(filtered=False)
        else:
            return object.__new__(cls)

if filtered:
    Session = scoped_session(sessionmaker(query_cls=CustomQuery))
else:
    Session = scoped_session(sessionmaker())

# SQLAlchemy session manager. Updated by model.init_model()
#Session = scoped_session(sessionmaker())

# Global metadata. If you have multiple databases with overlapping table
# names, you'll need a metadata for each database
metadata = MetaData()
