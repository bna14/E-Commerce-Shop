# models.py

from extensions import db, ma
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Sale {self.id}>'

class SaleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Sale
        load_instance = True

sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)
