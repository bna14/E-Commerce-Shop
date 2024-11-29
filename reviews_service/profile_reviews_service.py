from app import app
from models import db, Review
from memory_profiler import profile

def profile_reviews_service():
    with app.test_client() as client:
        with app.app_context():
            # Add a review to the database
            db.create_all()
            review = Review(item_id=1, username='test_user', rating=4, comment='Good product')
            db.session.add(review)
            db.session.commit()

            # Test submit review
            client.post('/reviews', json={
                'item_id': 2,
                'username': 'another_user',
                'rating': 5,
                'comment': 'Excellent product!'
            })

            # Test fetch reviews
            client.get('/reviews/product/1')

            # Test update review
            client.put(f'/reviews/{review.id}', json={
                'rating': 3,
                'comment': 'Changed my mind'
            })

            # Test delete review
            client.delete(f'/reviews/{review.id}')

if __name__ == "__main__":
    import cProfile
    import pstats

    profiler = cProfile.Profile()
    profiler.enable()
    profile_reviews_service()
    profiler.disable()

    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)  # Display top 10 cumulative results
