from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from makeitso.extensions import db


class BaseFactory[T](SQLAlchemyFactory[T]):
    __is_base_factory__ = True
    # create_sync() adds the row to this session and commits
    __session__ = db.session
    # Ids come from the database, so they follow creation order like real rows
    __set_primary_key__ = False
    # Parents are set through their relationship; a random id would point nowhere
    __set_foreign_keys__ = False
