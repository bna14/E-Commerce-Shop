# models.py

from extensions import db, ma
from marshmallow import validates, ValidationError
import bcrypt

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    balance = db.Column(db.Float, default=0.0)
    age = db.Column(db.Integer)
    address = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    marital_status = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Customer {self.username}>'

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True
        exclude = ('password_hash',)  # Exclude password hash from serialization

    password = ma.String(load_only=True, required=True)  # For password input

    @validates('username')
    def validate_username(self, value):
        if Customer.query.filter_by(username=value).first():
            raise ValidationError('Username already exists.')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
