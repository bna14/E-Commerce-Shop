# models.py

from extensions import db, ma  # Import from extensions
from marshmallow import validates, ValidationError

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum('food', 'clothes', 'accessories', 'electronics', name='category_enum'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    stock_count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Item {self.name}>'

class ItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Item
        load_instance = True
        include_fk = True

    @validates('price')
    def validate_price(self, value):
        if value <= 0:
            raise ValidationError('Price must be greater than zero.')

    @validates('stock_count')
    def validate_stock_count(self, value):
        if value < 0:
            raise ValidationError('Stock count cannot be negative.')

item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
