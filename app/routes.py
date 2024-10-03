from flask import render_template, jsonify, request, redirect, url_for, flash, session, make_response
from sqlalchemy import desc, or_, and_
from sqlalchemy.orm import joinedload
from app import create_app
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, verify_jwt_in_request, get_jwt_identity
from app.models import Users, Products, Orders, OrdersItem, Reviews, db
from app.schemas import UserSchema, ProductSchema, OrderSchema, OrderItemSchema, ReviewSchema
import requests
from requests.auth import HTTPBasicAuth
import os
import shutil
import datetime

# ---------------------- AUXILIAR FUNCTIONS  ---------------------- #
def extract_filters_limits(items):
    brands = list(set([item['brand'] for item in items]))
    categories = list(set([item['category'] for item in items]))
    flavours = list({flavour for item in items for flavour in item['flavours']})
    weights = list(set([item['weight'] for item in items]))
    min_value = 10000
    max_value = 0
    for item in items:
        if item['current_value'] > max_value:
            max_value = round(item['current_value'],2)
        elif item['current_value'] < min_value:
            min_value = round(item['current_value'],2)
    brands.sort()
    categories.sort()
    flavours.sort()
    weights.sort()
    return {'brands': brands,
            'categories': categories,
            'flavours': flavours,
            'weights': weights,
            'min_value': min_value,
            'max_value': max_value
            }

def update_filters(filter_obj):
    return {
        'query_param': filter_obj.get("query"),
        'query_category': filter_obj.get("query_category"),
        'filter_brands': filter_obj.getlist('brand'),
        'filter_categories' : filter_obj.getlist('category'),
        'filter_flavours': filter_obj.getlist('flavour'),
        'filter_weights': filter_obj.getlist('weight'),
        'filter_price': filter_obj.get('price')
    }

# ---------------------- SCHEMAS DECLARATION  ---------------------- #
user_schema = UserSchema()
users_schema = UserSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
order_item_schema = OrderItemSchema()
order_items_schema = OrderItemSchema(many=True)
review_schema = ReviewSchema()
reviews_schema = ReviewSchema(many=True)

# ---------------------- PAYPAL CONFIG ---------------------- #
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_BASE_URL = 'https://api-m.sandbox.paypal.com'
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

def generate_access_token():
    auth_response = requests.post(
        f'{PAYPAL_BASE_URL}/v1/oauth2/token',
        headers={
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        },
        data={
            'grant_type': 'client_credentials',
        },
        auth=HTTPBasicAuth(PAYPAL_CLIENT_ID,
                           PAYPAL_CLIENT_SECRET),
    )
    auth_response.raise_for_status()

    os.environ['ACCESS_TOKEN'] = auth_response.json()['access_token']

def init_routes(app):
    # ---------------------- MIDDLEWARES  ---------------------- #
    @app.context_processor
    def inject_current_user():
        try:
            verify_jwt_in_request(optional=True)
            user = session.get('user')
            if user:
                session['is_authenticated'] = True
                return {"current_user": user}
        except Exception as e:
            # If the token is invalid or expired, remove user from session
            session.pop('user', None)
            session.pop('is_authenticated', None)

        return {}

    def roles_required(*roles):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                jwt_data = get_jwt()
                if 'role' not in jwt_data or jwt_data['role'] not in roles:
                    return jsonify({"msg": "Access denied"}), 403
                return func(*args, **kwargs)

            return wrapper

        return decorator

    # ---------------------- ROUTES  ---------------------- #
    @app.route('/')
    def home():
        carousel_brands = ['brand1', 'brand2', 'brand3', 'brand4', 'brand5']
        result = (
            Products.query
            .order_by(desc(Products.discount))
            .limit(12)
            .all()
        )
        products = products_schema.dump(result)
        return render_template("home.html",products=products,carousel_brands=carousel_brands)

    @app.route('/product/<int:id>')
    def product(id):
        # Getting the product by id #
        products_result = Products.query.filter(Products.id == id)
        product = products_schema.dump(products_result)[0]

        # Getting related products #
        related_result = (
            Products.query
            .filter(Products.category == product['category'])
            .limit(12)
            .all()
        )
        related_products = products_schema.dump(related_result)

        # Getting reviews for the products #
        reviews_result = (
            Reviews.query
            .join(Users, Reviews.user_id == Users.id)
            .filter(Reviews.product_id == id)
            .order_by(desc(Reviews.update_date))
            .add_columns(Users.fname, Users.lname)
            .all()
            )
        reviews_list = [
            {
                'id': review[0].id,
                'user_id': review[0].user_id,
                'product_id': review[0].product_id,
                'rating': review[0].rating,
                'review': review[0].review,
                'update_date': review[0].update_date,
                'fname': review[1],
                'lname': review[2]
            }
            for review in reviews_result
        ]
        users_review = [review[0].user_id for review in reviews_result]
        print(users_review)
        reviews = reviews_schema.dump(reviews_list)
        return render_template("product.html",
                               product = product,
                               related_products = related_products,
                               reviews = reviews,
                               users_review=users_review)

    @app.route('/search')
    def search():
        # Checking Args Sent #
        print(request.args)
        filters = update_filters(request.args)
        order_by = request.args.get('order_by', 'Most Relevant')
        pagination = {
            'current_page':int(request.args.get('page', 1)),
            'entries_per_page': 12,
            'results':f"{12*int(request.args.get('page', 1)) - 12}-{12*int(request.args.get('page', 1))}"
        }

        # Getting Base Query #
        if filters['query_category']:
            if filters['query_category'] == 'Hot':
                query = (
                    Products.query
                    .filter(Products.top_sale == True)
                )
            elif filters['query_category'] == 'Top':
                query = (
                    Products.query
                    .filter(Products.most_sold == True)
                )
            elif filters['query_category'] == 'Sales':
                query = (
                    Products.query
                    .order_by(desc(Products.discount))
                )
            else:
                query = (
                    Products.query
                    .filter(Products.category == filters['query_category'])
                    )
        else:
            query = Products.query.filter(
                or_(Products.name.ilike(f'%{filters["query_param"]}%'),
                    Products.category.ilike(f'%{filters["query_param"]}%'),
                    Products.brand.ilike(f'%{filters["query_param"]}%')
                    )
            )

        # Apply FILTER, if sent #
        if filters['filter_brands']:
            query = query.filter(Products.brand.in_(filters['filter_brands']))
        if filters['filter_categories']:
            query = query.filter(Products.category.in_(filters['filter_categories']))
        if filters['filter_flavours']:
            query = query.filter(and_(*[Products.flavours.any(flavour) for flavour in filters['filter_flavours']]))
        if filters['filter_weights']:
            query = query.filter(Products.weight.in_(filters['filter_weights']))
        if filters['filter_price']:
            query = query.filter(Products.current_value <= float(filters['filter_price']))

        # Apply ORDER BY, if sent #
        if order_by == 'Most Sold':
            query = query.order_by(Products.most_sold.desc())
        elif order_by == 'Higher Price':
            query = query.order_by(Products.current_value.desc())
        elif order_by == 'Lower Price':
            query = query.order_by(Products.current_value.asc())
        elif order_by == 'Discount':
            query = query.order_by(Products.discount.desc())

        # Handle Pagination #
        paginated_query = query.paginate(
            page=pagination['current_page'],
            per_page=pagination['entries_per_page'],
            error_out=False
        )
        pagination['total_pages'] = paginated_query.pages
        pagination['total_items'] = paginated_query.total
        pagination['object'] = paginated_query

        # Dump results #
        result = paginated_query.items
        products = products_schema.dump(result)
        filters_limits = extract_filters_limits(products)

        return render_template("search.html",
                               products=products,
                               filters_limits = filters_limits,
                               filters=filters,
                               order_by=order_by,
                               pagination=pagination)

    @app.route('/login',methods=['GET','POST'])
    def login():
        form_action = 'login'

        if request.method == 'GET':
            return render_template("sign.html",form_action=form_action)

        elif request.method == 'POST':
            # Check if email exist #
            check_email = Users.query.filter(Users.email == request.form['email']).first()
            if not check_email:
                flash("Email don't found. Register or try again.", 'danger')
                return redirect(url_for('login', form_action=form_action))

            user = user_schema.dump(check_email)

            # Check password, concede token and store user info into session #
            if check_password_hash(user['password'], request.form['password']):
                access_token = create_access_token(identity=user['id'], additional_claims = {"role": user['role']})
                session['user'] = {
                    'id': user['id'],
                    'fname': user['fname'],
                    'lname': user['lname'],
                    'email': user['email'],
                    'role': user['role'],
                    'phone': user['phone'],
                    'address': user['address'],
                    'join_date': user['join_date']
                }
                response = make_response(redirect(url_for('home')))
                response.set_cookie('access_token', access_token)
                return response

            # Wrong password #
            flash("Wrong password. Try again.", 'danger')
            return redirect(url_for('login', form_action=form_action))

    @app.route('/register',methods=['GET','POST'])
    def register():
        form_action = 'register'

        if request.method == 'GET':
            return render_template("sign.html",form_action=form_action)

        elif request.method == 'POST':
            # Check if email already registered #
            check_email = Users.query.filter(Users.email == request.form['email']).all()
            if check_email:
                flash('This email is already registered. Please login or try a different email.', 'danger')
                return redirect(url_for('register', form_action=form_action))

            # Hash password and add user #
            hash_password = generate_password_hash(request.form['password'], method="pbkdf2:sha256", salt_length=8)
            new_user = Users(
                fname=request.form['fname'],
                lname=request.form['lname'],
                email=request.form['email'],
                password=hash_password,
                phone=request.form['phone'],
                address=request.form['address']
            )
            db.session.add(new_user)
            db.session.commit()

            # Get created user id, concede token and store user info into session #
            query = Users.query.filter(Users.email == request.form['email']).first()
            user = user_schema.dump(query)

            access_token = create_access_token(identity=user['id'], additional_claims={"role": user['role']})
            session['user'] = {
                'id': user['id'],
                'fname': user['fname'],
                'lname': user['lname'],
                'email': user['email'],
                'role': user['role'],
                'phone': user['phone'],
                'address': user['address'],
                'join_date': user['join_date']
            }
            response = make_response(redirect(url_for('home')))
            response.set_cookie('access_token', access_token)
            return response

    @app.route('/profile',methods=['GET','POST'])
    @jwt_required()
    def profile():
        if request.method == 'GET':
            return render_template('profile.html')

        elif request.method == 'POST':
            # Update user info #
            user = Users.query.filter(Users.email == request.form['email']).first()
            user.fname = request.form['fname']
            user.lname = request.form['lname']
            user.phone = request.form['phone']
            user.address = request.form['address']
            db.session.commit()

            # Update session object #
            user = user_schema.dump(user)
            session['user'] = {
                'id': user['id'],
                'fname': request.form['fname'],
                'lname': request.form['lname'],
                'email': user['email'],
                'role': user['role'],
                'phone': request.form['phone'],
                'address': request.form['address'],
                'join_date': user['join_date']
            }
            flash('Profile updated successfully.', 'success')
            return redirect("/profile")

    @app.route('/logout')
    @jwt_required()
    def logout():
        response = make_response(redirect(url_for('home')))
        response.delete_cookie('access_token')
        session.pop('user', None)
        return response

    @app.route('/orders/<int:id>')
    @jwt_required()
    def orders(id):
        current_status = request.args.get('status', 'Open')  # Default to 'open' if no status provided

        # Find all order associated to the current user
        orders = Orders.query.filter(and_(Orders.user_id == id,Orders.status == current_status)).all()
        orders_with_products = []

        # Iterate through each order
        for order in orders:
            # Fetch order items for the current order
            order_items = OrdersItem.query.filter_by(order_id=order.id).all()

            # Initialize a list to hold product names for the current order
            product_names = []

            # Iterate through each order item to get product names
            for item in order_items:
                product = Products.query.get(item.product_id)
                product_names.append(product.name)

            # Append the order data with product names to the list
            orders_with_products.append({
                'id': order.id,
                'order_date': order.order_date.strftime("%Y-%m-%d"),
                'total_value': order.total_value,
                'status': order.status,
                'products': ', '.join(product_names)
            })

        return render_template('orders.html',
                               orders=orders_with_products,
                               current_status=current_status)

    @app.route('/order_details/<int:order_id>')
    @jwt_required()
    def order_details(order_id):
        # Join Query #
        query = (Orders.query.options
                 (joinedload(Orders.order_items)
                  .joinedload(OrdersItem.product))
                 .filter(Orders.id == order_id)
                 .first())

        # Order object #
        order = {
            'id': query.id,
            'order_date': query.order_date.strftime("%Y-%m-%d"),
            'total_value': query.total_value,
            'status': query.status,
            'address': query.address
        }

        # Order Items object #
        order_items = []
        for i, item in enumerate(query.order_items):
            product = item.product
            order_items.append({
                'pos': i+1,
                'id': item.id,
                'product_id': product.id,
                'name': product.name,
                'flavour': item.flavour,
                'unit_value': product.current_value,
                'quantity': item.amount,
                'value_item': item.amount * product.current_value
            })

        return render_template('order_details.html',order=order,order_items=order_items)

    @app.route('/checkout')
    def checkout():
        cart = session.get('cart', [])
        print(cart)
        order_value = 0
        for item in cart:
            order_value += (item['product_price'] * item['quantity'])
        return render_template("checkout.html",cart=cart,order_value=order_value)

    @app.route('/add_review/<int:product_id>',methods=['POST'])
    def add_review(product_id):
        review = Reviews(
            user_id=request.form['user_id'],
            product_id=product_id,
            rating=request.form['rating'],
            review=request.form['review'],
        )
        db.session.add(review)
        db.session.commit()
        return redirect(f"/product/{product_id}")

    @app.route('/edit_review/<int:product_id>', methods=['POST'])
    def edit_review(product_id):
        review = Reviews.query.filter(Reviews.id == request.form['review_id']).first()

        review.rating = request.form['rating']
        review.review = request.form['review']
        db.session.commit()

        return redirect(f"/product/{product_id}")

    @app.route('/delete_review/<int:review_id>', methods=['DELETE'])
    def delete_review(review_id):
        review = Reviews.query.filter(Reviews.id == review_id).first()
        db.session.delete(review)
        db.session.commit()
        return '', 204

    @app.route('/add_product')
    def add_product():
        return render_template('add_product.html')

    @app.route('/preview_product', methods=['POST'])
    def preview_product():
        # Define the temp folder path
        temp_folder = os.path.join(app.static_folder, 'images', 'temp')

        # Get the existing product data from the session if available
        existing_product_data = session.get('product_data', {})

        # Handle the form data
        product_name = request.form.get('product_name')
        category = request.form.get('category')
        brand = request.form.get('brand')
        base_price = float(request.form.get('base_price'))
        discount = int(request.form.get('discount'))
        selling_price = base_price * (1 - discount / 100)
        flavours = request.form.getlist('flavours')
        weight = request.form.get('weight')
        description = request.form.get('description')
        benefits = request.form.get('benefits')
        how_to_use = request.form.get('how_to_use')

        # Handle images
        cover_image = request.files.get('cover_image')
        nutrition_table_image = request.files.get('nutrition_table_image')
        more_images = request.files.getlist('more_images')

        # Clear the temp folder if new images are uploaded
        if cover_image or nutrition_table_image or any(img.filename != '' for img in more_images):
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
            os.makedirs(temp_folder)

        # Cover image
        if cover_image and cover_image.filename != '':
            cover_image.save(os.path.join(temp_folder, 'head.png'))
            cover_image_filename = 'head.png'
        else:
            cover_image_filename = existing_product_data.get('images', {}).get('cover_image', '')

        # Nutrition table image
        if nutrition_table_image and nutrition_table_image.filename != '':
            nutrition_table_image.save(os.path.join(temp_folder, 'nutrition.png'))
            nutrition_table_image_filename = 'nutrition.png'
        else:
            nutrition_table_image_filename = existing_product_data.get('images', {}).get('nutrition_table_image', '')

        # More images
        more_images_filenames = []
        if more_images and any(img.filename != '' for img in more_images):
            for idx, image in enumerate(more_images):
                if image.filename != '':
                    image.save(os.path.join(temp_folder, f'image_{idx}.png'))
                    more_images_filenames.append(f'image_{idx}.png')
        else:
            more_images_filenames = existing_product_data.get('images', {}).get('more_images', [])

        # Store the new or existing data in the session
        session['product_data'] = {
            'product_name': product_name,
            'category': category,
            'brand': brand,
            'base_value': base_price,
            'discount': discount,
            'current_value': selling_price,
            'flavours': flavours,
            'weight': weight,
            'description': description,
            'benefits': benefits,
            'how_to_use': how_to_use,
            'images': {
                'cover_image': cover_image_filename,
                'nutrition_table_image': nutrition_table_image_filename,
                'more_images': more_images_filenames
            }
        }

        # Render the preview page
        return render_template('preview_product.html', product=session['product_data'])

    @app.route('/confirm_product', methods=['POST'])
    def confirm_product():
        product_data = session.get('product_data')
        if not product_data:
            return redirect(url_for('add_product'))

        # Save the product to the database to get the product ID
        new_product = Products(
            name=product_data['product_name'],
            category=product_data['category'],
            brand=product_data['brand'],
            base_value=product_data['base_value'],
            current_value=product_data['current_value'],
            discount=product_data['discount'],
            flavours=product_data['flavours'],
            weight=product_data['weight'],
            description=product_data['description'],
            benefits=product_data['benefits'],
            how_to_use=product_data['how_to_use'],
            update_date=datetime.datetime.now()
        )
        db.session.add(new_product)
        db.session.commit()

        # Get the product ID after committing
        product_id = new_product.id

        # Create the final folder for the product images
        final_folder = os.path.join(app.static_folder, 'images', 'products', str(product_id))
        os.makedirs(final_folder, exist_ok=True)

        temp_folder = os.path.join(app.static_folder, 'images', 'temp')

        shutil.copy(os.path.join(temp_folder, 'head.png'), os.path.join(final_folder, 'head.png'))
        shutil.copy(os.path.join(temp_folder, 'nutrition.png'), os.path.join(final_folder, 'nutrition.png'))

        others_images_names = []
        for idx, _ in enumerate(product_data['images']['more_images']):
            shutil.copy(
                os.path.join(temp_folder, f'image_{idx}.png'),
                os.path.join(final_folder, f'image_{idx}.png')
            )
            others_images_names.append(f'image_{idx}.png')

        # Update the product images in the database
        new_product.images = ['head.png',  'nutrition.png'] + others_images_names

        db.session.commit()

        # Remove the temp folder after saving
        shutil.rmtree(temp_folder)

        # Clear session data after saving
        session.pop('product_data', None)

        # Flash message and redirect
        flash('Product successfully added!', 'success')
        return redirect(url_for('add_product'))

    @app.route('/edit_product')
    def edit_product():
        return render_template('add_product.html', product=session.get('product_data'))

    @app.route('/all_products')
    def all_products():
        result = Products.query.order_by(Products.id).all()
        products = products_schema.dump(result)

        return render_template('all_products.html', products=products)

    @app.route('/edit_product/<int:product_id>')
    def edit_existent_product(product_id):
        result = Products.query.filter(Products.id == product_id).first()
        product = {
            'id': product_id,
            'product_name': result.name,
            'category': result.category,
            'brand': result.brand,
            'base_value': result.base_value,
            'discount': result.discount,
            'current_value': result.current_value,
            'flavours': result.flavours,
            'weight': result.weight,
            'description': result.description,
            'benefits': result.benefits,
            'how_to_use': result.how_to_use,
            'images': {
                'cover_image': result.images[0],
                'nutrition_table_image': result.images[1],
                'more_images': result.images[2:]
            }
        }
        print(product)
        return render_template('add_product.html', product=product, exist=True)

    @app.route('/update_existent_product/<int:product_id>', methods=['POST'])
    def update_existent_product(product_id):
        product = Products.query.filter(Products.id == product_id).first()

        product.name = request.form['product_name'],
        product.category = request.form['category'],
        product.brand = request.form['brand'],
        product.base_value = request.form['base_price'],
        product.current_value = request.form['selling_price'],
        product.discount = request.form['discount'],
        product.flavours = request.form['flavours'],
        product.weight = request.form['weight'],
        product.description = request.form['description'],
        product.benefits = request.form['benefits'],
        product.how_to_use = request.form['how_to_use'],
        product.update_date = datetime.datetime.now()

        db.session.commit()
        return redirect(f"/product/{product_id}")

    @app.route('/delete_existent_product/<int:product_id>')
    def delete_existent_product(product_id):
        product = Products.query.filter(Products.id == product_id).first()
        db.session.delete(product)
        db.session.commit()
        return redirect('/all_products')

    @app.route('/all_orders')
    def all_orders():
        current_status = request.args.get('status', 'Open')  # Default to 'open' if no status provided

        # Find all order
        orders = Orders.query.filter(and_(Orders.status == current_status)).all()
        orders_with_products = []

        # Iterate through each order
        for order in orders:
            # Fetch order items for the current order
            order_items = OrdersItem.query.filter_by(order_id=order.id).all()

            # Initialize a list to hold product names for the current order
            product_names = []

            # Iterate through each order item to get product names
            for item in order_items:
                product = Products.query.get(item.product_id)
                product_names.append(product.name)

            # Append the order data with product names to the list
            orders_with_products.append({
                'id': order.id,
                'order_date': order.order_date.strftime("%Y-%m-%d"),
                'total_value': order.total_value,
                'status': order.status,
                'products': ', '.join(product_names)
            })

        return render_template('orders.html',
                               orders=orders_with_products,
                               current_status=current_status)
    @app.route('/orders/<int:order_id>/finish')
    def finish_order(order_id):
        order = Orders.query.filter(Orders.id == order_id).first()
        order.status = 'Finished'
        db.session.commit()
        return redirect('/all_orders')

    @app.route('/orders/<int:order_id>/cancel')
    def cancel_order(order_id):
        order = Orders.query.filter(Orders.id == order_id).first()
        order.status = 'Cancel'
        db.session.commit()
        return redirect('/all_orders')

    @app.route('/orders/<int:order_id>/open')
    def open_order(order_id):
        order = Orders.query.filter(Orders.id == order_id).first()
        order.status = 'Open'
        db.session.commit()
        return redirect('/all_orders')

    #### PAYPAL #####
    @app.route('/payment')
    def payment():
        return render_template("payment.html")

    @app.route('/api/orders', methods=['POST'])
    def create_order():
        generate_access_token()
        cart = session.get('cart', [])
        order_value = 0
        for item in cart:
            order_value += (item['product_price'] * item['quantity'])
        order_value = str(round(order_value,2))
        try:
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": "USD",
                        "value": order_value
                    }
                }]
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {ACCESS_TOKEN}'
            }

            response = requests.post(f'{PAYPAL_BASE_URL}/v2/checkout/orders', json=payload, headers=headers)
            response.raise_for_status()

            return jsonify(response.json())
        except Exception as e:
            print(e)
            return jsonify({'error': str(e)}), 500

    @app.route('/api/orders/<order_id>/capture', methods=['POST'])
    def capture_order(order_id):
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {ACCESS_TOKEN}'
            }

            response = requests.post(f'{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture', headers=headers)
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            print(e)
            return jsonify({'error': str(e)}), 500

    ################
    # Cart Request Handling #
    @app.route('/add_to_cart', methods=['POST'])
    def add_to_cart():
        item = request.json
        cart = session.get('cart', [])
        # Check if item already exists in cart
        existing_item = next(
            (i for i in cart if i['product_id'] == item['product_id'] and i['flavour'] == item['flavour']), None)
        if existing_item:
            existing_item['quantity'] += item['quantity']
        else:
            cart.append(item)
        session['cart'] = cart
        return jsonify(cart)

    @app.route('/remove_from_cart', methods=['POST'])
    def remove_from_cart():
        item_id = request.json['cart_id']
        cart = session.get('cart', [])
        cart = [item for item in cart if item['cart_id'] != item_id]
        session['cart'] = cart
        return jsonify(cart)

    @app.route('/clear_cart', methods=['POST'])
    def clear_cart():
        session.pop('cart', None)
        return jsonify({"status": "cart cleared"})

    @app.route('/view_cart')
    def view_cart():
        cart = session.get('cart', [])
        return jsonify({'cart': cart})

    @app.route('/update_cart_quantity', methods=['POST'])
    def update_cart_quantity():
        data = request.json
        cart = session.get('cart', [])
        for item in cart:
            if item['cart_id'] == data['cart_id']:
                item['quantity'] = data['quantity']
                break
        session['cart'] = cart
        return jsonify(cart)

