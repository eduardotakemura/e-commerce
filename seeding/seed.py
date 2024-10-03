from app import create_app, db
from app.models import Products, Users, Reviews
import random
import lorem

def seed():
    """ Seeding script used to populate all tables from the database with dummies data. """
    app = create_app()
    with app.app_context():
        # Clear current products table #
        db.session.query(Products).delete()
        db.session.commit()

        # Adding dummies users #
        users = [
            Users(
                fname="John",
                lname="Doe",
                email="admin@email.com",
                password="12345",
                phone="11998745632",
                address="Times Square Avenue, 10",
                role="admin"
            ),
            Users(
                fname="Jane",
                lname="Smith",
                email="email@email.com",
                password="12345",
                phone="1139987845",
                address="White House, 1"
            )
        ]
        db.session.bulk_save_objects(users)

        # Setting products configs #
        categories = ['Whey', 'Creatine', 'Pre-Workout', 'Hyper Caloric', 'Caffeine', 'Vitamins']
        flavours = ['Chocolate', 'Strawberry', 'Vanilla', 'Coffee', 'Lemon', 'Cookie']
        weights = [900, 1200, 2000, 300, 250, 100]

        # Adding dummies products(50) #
        products = []
        for item in range(50):
            discount = random.randint(0, 35)
            base_value = random.uniform(50, 200)
            current_value = base_value * (1 - discount / 100)
            product = Products(
                name=f"Product{item}",
                discount=discount,
                category=random.choice(categories),
                brand=f"Brand{random.randint(1, 10)}",
                base_value=base_value,
                current_value=current_value,
                flavours=random.sample(flavours, k=random.randint(1, len(flavours))),
                weight=random.choice(weights),
                images=['head.png','nutrition.png'],
                description=lorem.text(),
                benefits=lorem.text(),
                how_to_use=lorem.text(),
                top_sale=bool(random.getrandbits(1)),
                most_sold=bool(random.getrandbits(1))
            )
            products.append(product)

        # Adding dummies comments #
        reviews = []
        for item in range(50):
            review = Reviews(
                user_id = random.randint(2,3),
                product_id = random.randint(51,100),
                rating = random.uniform(0.0, 5.1),
                review = lorem.paragraph()
            )
            reviews.append(review)

        db.session.bulk_save_objects(products)
        db.session.bulk_save_objects(reviews)
        db.session.commit()


if __name__ == '__main__':
    seed()
