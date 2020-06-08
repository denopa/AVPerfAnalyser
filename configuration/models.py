from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class BaseModel(db.Model):
# """Base data model for all objects"""
    __abstract__ = True
    # define here __repr__ and json methods or any common method
    # that you need for all your models
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self._to_dict().items()
        })

    def json(self):
        """
                Define a base way to jsonify models, dealing with datetime objects
        """
        return {
            column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
            for column, value in self._to_dict().items()
        }

class YourModel(BaseModel, db.Model):
# """model for one of your table"""
    __tablename__ = 'my_table'
    # define your model
    id = db.Column(db.Integer, primary_key = True)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)