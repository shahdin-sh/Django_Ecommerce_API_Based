Inventory Management Process (Celery Task)
Overview:
The inventory management system for the e-commerce platform ensures that product stock levels are appropriately adjusted when a user places an order. The following outlines the different scenarios involved in managing   inventory during the checkout and payment processes:

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
        The inventory for each product in the order is updated by reducing the stock accordingly. This is done through the update_inventory Celery task, which is triggered by the payment approval process.

5. Failure in Inventory Update
    In case of an inventory issue (e.g., insufficient stock), the order is canceled, and the user is notified to retry with available stock.

6. Celery will take care of the orders that are not approved and expired. with cleaning them in the background so our Appilication will remain clean and robust.

7. Order deletion is only possible for admins and order managers, if the order get deleted by their hands it means that order had a problem despite of its status (paid or unpaid) otherwise all of the orders should not get deleted, the tasks that is using for update inventory will take care of this process and increase the inventory from destory function in OrderViewSet.