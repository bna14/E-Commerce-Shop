import cProfile
import pstats
from app import app, db

def profile_inventory_service():
    """
    Profile the Inventory Service.
    """
    with app.app_context():
        db.create_all()  # Ensure the database is set up
        with app.test_client() as client:
            # Test endpoints
            client.get('/')
            client.post('/items', json={
                'name': 'Laptop',
                'category': 'electronics',
                'price': 1200.99,
                'description': 'High-end gaming laptop',
                'stock_count': 5
            }, headers={'x-api-key': 'your_api_key'})
            client.get('/items')
            client.put('/items/1', json={
                'price': 1000.00,
                'stock_count': 10
            }, headers={'x-api-key': 'your_api_key'})
            client.delete('/items/1', headers={'x-api-key': 'your_api_key'})

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    profile_inventory_service()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumtime')
    stats.print_stats(10)
