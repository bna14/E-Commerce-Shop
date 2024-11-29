import cProfile
import pstats
from app import app, db

def profile_sales_service():
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            # Test the main endpoints
            client.get('/')
            client.get('/goods')
            client.post('/sales', json={
                'username': 'test_user',
                'item_id': 1,
                'quantity': 1
            })
            client.get('/sales/history/test_user')

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    profile_sales_service()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumtime')
    stats.print_stats(10)
