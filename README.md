Django E-commerce API Development

This Django REST Framework-based e-commerce API offers a comprehensive and seamless experience, providing all the essential functionalities you need from an e-commerce platform. The API is designed to be robust, secure, and scalable, ensuring that you can manage every aspect of your online store with ease.

Key Features:
    - User Management: Full support for user registration, authentication, and management, ensuring a secure and personalized experience.
    - Group and Permission Management: Granular control over user roles and permissions, allowing for precise access control for different user types such as admins, product managers, and              customers.
    - Secure Endpoints: All sensitive endpoints are protected with JWT authentication, ensuring that data is secure and accessible only to authorized users.
    - Product and Category Management: Easily manage your product listings and organize them into categories, allowing for a flexible and dynamic product catalog.
    - Search and Filter: Powerful search and filtering functionality for products, enabling customers to easily find items by price, category, brand, or other attributes.
    - Comment Management: Enable customers to leave feedback on products, helping to build engagement and trust within your platform.
    - Wishlist Management: Allow users to save products to a wishlist, enabling easy access to desired items for future purchases.
    - Product Stock Management: Explained in the next section
    - Cart Logic: A robust cart system that supports both authenticated and guest users, with seamless transitions between anonymous and logged-in sessions.
    - Order Management: Detailed order creation and management, including automatic expiration of unsubmitted orders, ensuring that your inventory is always up to date.
    - Payment Integration: Integration with the Zarinpal Sandbox Gateway for payment processing, enabling secure and reliable online transactions. This includes asynchronous updates to inventory       and order status upon successful payments.
    - Discount and Coupon Management: A feature currently under development that will allow users to apply discount codes to their cart for promotional offers, helping to drive sales and 
      customer engagement.
    - Customer Management: Every registered user automatically has a Customer instance created via signals. This ensures that user profiles are seamlessly linked to their customer information,         providing a personalized shopping experience.
    - Address Management: Each customer can have one address for shipping purposes, streamlining the checkout process and ensuring accurate delivery details.


Inventory Management Process (Celery Task)
    Overview:
        The inventory management system for the e-commerce platform ensures that product stock levels are appropriately adjusted when a user places an order. The following outlines the                  different scenarios involved in managing   inventory during the checkout and payment processes:
            1. Cart Creation and Inventory Management
                Cart Creation: When a user adds products to their cart, the items are stored without impacting inventory.
                No Immediate Inventory Adjustment: At this stage, no stock changes occur, as the user is still in the process of checkout and has not yet confirmed the order.
            2. Order Creation and Payment Process
                When the user proceeds to checkout, an order is created based on the cart. The following logic is triggered in the payment section:
                Inventory Check at Payment:
                    Once the user confirms payment, a real-time inventory check is performed for each product in the order.
                    If any product's inventory is insufficient, the entire order is canceled, and the user is notified, including details of which product(s) had inventory issues.
                Inventory Update:
                    If the payment is successful, the approve_order_status_after_successful_payment task is triggered asynchronously using Celery.
                    Inventory is updated by reducing the stock for the products included in the order.
                    The inventory update logic is handled directly in the payment process and Celery tasks, not through Django signals to avoid potential issues with repeated updates.
            3. Cart Expiry
                If a user fails to confirm payment within 15 minutes of creating the cart, the order is automatically deleted. This avoids holding inventory for unconfirmed orders.
            4. Successful Payment
                Once payment is successfully confirmed:
                    The order status is updated to "paid".
                    The inventory for each product in the order is updated by reducing the stock accordingly. This is done through the update_inventory Celery task, which is triggered by the                        payment approval process.
            5. Failure in Inventory Update
                In case of an inventory issue (e.g., insufficient stock), the order is canceled, and the user is notified to retry with available stock.
            6. Celery will take care of the orders that are not approved and expired. with cleaning them in the background so our Appilication will remain clean and robust.
            7. Order deletion is only possible for admins and order managers, if the order get deleted by their hands it means that order had a problem despite of its status (paid or unpaid)                 otherwise all of the orders should not get deleted, the tasks that is using for update inventory will take care of this process and increase the inventory from destory function in               OrderViewSet.


Technologies Used:
    - Python
    - Django
    - Django REST Framework
    - PostgreSQL
    - Docker: Used for containerization and deployment, ensuring consistent environments across development, testing, and production stages.
    - Redis: Implemented for caching endpoints like product details and categories, improving response times and reducing database load. Its also used as a message broker for asynchronous tasks. 
    - JWT Authentication: Used for secure token-based authentication, ensuring that only authorized users can access specific endpoints.
    - Celery: Used for asynchronous task processing, including managing cart transitions between session and authenticated user, handling order expiration, and managing inventory stock updates.
    - Celery-beat: Used to schedule and manage repeated tasks, such as automatically expiring unsubmitted orders after a set time.
    - Signals: Implemented to track users and customers, enabling reactive actions based on user activity and interactions.
    - Custom Throttling: Applied to manage different user roles, ensuring fair usage of the API by limiting requests based on user permissions and roles.
    - Pagination: Built-in pagination for efficient handling of large datasets, ensuring smooth and optimized loading of product and customer lists and some other enpoints.
    - Swagger Documentation: Integrated with Django REST Framework to automatically generate interactive API documentation, making it easy for developers to understand and test available         
      endpoints.
    - Unit Testing: Developed to ensure the correctness and reliability of all components. Currently outdated and requires redevelopment to align with the latest system features and improvements.
    - Secure Environment: Sensitive configurations managed through environment variables, improving security and maintainability.


Installation
    # Clone the repository and navigate to the project directory
    
    git clone https://github.com/shahdin-sh/Django_Ecommerce_API_Based.git
    cd <project-directory>

    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Build the Docker image
    docker build .

    # Start Docker containers
    docker-compose up --build

    # Apply database migrations
    docker-compose exec web python manage.py migrate

    # Create a superuser for admin access
    docker-compose exec web python manage.py createsuperuser

    # (Optional) Fill the database with test data
    docker-compose exec web python manage.py setup_fake_data

    # Access Swagger API documentation at:
    # http://0.0.0.0:8000/schema-swagger/
