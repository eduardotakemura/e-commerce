# Full-Stack Supplement E-Commerce
This web application is a fully-functional E-Commerce platform for selling supplements, built using Flask for the backend and templating, 
along with a PostgreSQL database for data storage.  
The frontend was developed using vanilla JavaScript, HTML, and CSS.

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Seeding Data](#seeding-data)
5. [Technologies](#technologies)
6. [Features](#features)
7. [Contributing](#contributing)
8. [License](#license)

## Overview
This page was designed as an online store for health and fitness supplements. Users can browse and 
filter products by categories such as type, brand, weight, price, and more. The app also features promotional tags like 
"Top Selling" to highlight trending products and boost user engagement.  
The app’s backend is powered by **Flask**, which handles routing, templating, and communication with the **PostgreSQL** database for 
performing CRUD operations (Create, Read, Update, Delete).  
This project also supports user authentication with roles (e.g., customer, admin) and includes features such as a shopping cart, 
user reviews, and an admin dashboard for order management.


## Installation
Instructions on how to install the project locally.

```bash
# Clone this repository
$ git clone https://github.com/eduardotakemura/e-commerce.git

# Go into the repository
$ cd e-commerce

# Install dependencies
$ pip install -r requirements.txt
```

## Usage

Instructions for running the project.

```bash
# Run the application
$ python main.py

```
This will start the Flask development server, and the application will be available at **http://localhost:5000/**.

## Seeding Data
The project includes seed scripts for populating the database with dummy data, which is helpful for testing and validating the 
functionality of the SQL database. You can use these scripts to pre-fill the database with products, categories, users, etc., during development. 

## Technologies
The project relies mostly on the following Technologies:
- **Flask**: A lightweight Python web framework used for backend development and templating.
- **Flask-JWT**: Provides JSON Web Token (JWT) support for user authentication and role-based access control.
- **Flask-Marshmallow**: Used for object serialization and schema validation.
- **Flask-SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) for interacting with the PostgreSQL database.
- **PostgreSQL**: A powerful, open-source relational database system used to store product, user, and order information.

## Features
- **SQL Database**: A PostgreSQL database ensures robust and scalable data management with validation and support for simultaneous user access.
- **Authentication and Role Management**: Supports JWT-based user authentication and role management (e.g., admin, customer) to control access to different parts of the application.
- **Product Filtering**: Users can filter products based on attributes such as brand, price range, weight, and categories.
- **Shopping Cart**: Users can add items to their cart, modify quantities, and proceed to checkout.
- **User Reviews and Ratings**: Registered users can leave reviews and ratings for products to provide feedback and improve the shopping experience.
- **Order Management**: Admins can view, update, and manage orders without direct access to the SQL database.
- **Product Management**: Admins can add, edit, or remove products and update the product catalog via the admin interface.
- **Promotional Tags**: Products can be tagged with special attributes like "Top Selling" to highlight popular items.

## Contributing
Contributions are welcome! Please read the contributing guidelines first.

1. Fork the repo
2. Create a new branch (git checkout -b feature/feature-name)
3. Commit your changes (git commit -m 'Add some feature')
4. Push to the branch (git push origin feature/feature-name)
5. Open a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
