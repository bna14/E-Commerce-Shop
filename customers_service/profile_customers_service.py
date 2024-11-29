import cProfile
import pstats
from app import app, db

def profile_customers_service():
    """
    Profile the Customers Service.
    """
    with app.app_context():
        db.create_all()  # Ensure the database is set up
        with app.test_client() as client:
            client.get('/')  # Profile the index endpoint
            client.post('/customers', json={
                'username': 'testuser',
                'password': 'password123',
                'first_name': 'John',
                'last_name': 'Doe',
                'age': 30,
                'address': '123 Elm St',
                'gender': 'Male',
                'marital_status': False
            })
            client.get('/customers/testuser')

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    profile_customers_service()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumtime')
    stats.print_stats(10)
