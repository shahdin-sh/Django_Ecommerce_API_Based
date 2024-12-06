from .imports import *


class PaymentProcessView(APIView):
    http_method_names = ['get', 'post', 'head', 'options']
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authority = request.GET.get('Authority')
        payment_request_status = request.GET.get('Status')

        if payment_request_status == 'OK':
            # payment verification request to zarinpal 
            verify_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
           
            request_header = {
                'accept': 'application/json',
                'content-type': 'application/json' 
            }

            payment_data = request.session['payment_data']
            # get order from session
            order_id = payment_data['order_id']
            order = Order.objects.select_related('customer').prefetch_related('items').get(id=order_id)

            data_body = {
                'merchant_id': payment_data['merchant_id'],
                'amount': payment_data['amount'],
                'authority': authority
            }

            response = requests.post(url=verify_request_url, data=json.dumps(data_body), headers=request_header)
        
            try: 
                data = response.json()
            except json.JSONDecodeError as e:
                print(response.json())
                return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)
            
            if data['data']['code'] == 100:
                # Trigger the Celery task to approve order status asynchronously
                approve_order_status_after_successful_payment.delay(order_id)

                # Trigger the Celery task to reduce products inventory asynchronously
                task_list = group(
                    update_inventory.s(orderitem.product.id, orderitem.quantity, True) for orderitem in order.items.all()
                )
                task_list.apply_async()

                return Response(f"Transaction success. | ref_id: {data['data']['ref_id']}.", status=status.HTTP_200_OK)
            
            elif data['data']['code'] == 101:
                return Response(f"Transaction is submitted before. | ref_id: {data['data']['ref_id']}", status=status.HTTP_200_OK)
            
            else:
                return Response(f"Transaction failed. | Status: {data['code']}", status=status.HTTP_400_BAD_REQUEST)
                        
        elif payment_request_status == 'NOK':
            return Response('Transaction failed or canceled by user.', status=status.HTTP_400_BAD_REQUEST)
        
        return Response('Enter your OrderId to initiate the payment process.', status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        order_id = request.data['order_id']
        order_obj = Order.objects.select_related('customer').prefetch_related('items').get(id=order_id)

        # check the inventory to make sure the product stock is avaliable if not guide the user to update his order
        has_sufficient_stock, insufficient_products =  order_obj.check_stock()

        if not has_sufficient_stock:
            order_obj.delete()
            return Response(f'Your order items has not enough stock please submit your order again. | detail: {insufficient_products}', status=status.HTTP_400_BAD_REQUEST)
        
        # payment data request to zarinpal
        zarinpal_request_url = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'

        request_header = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        data_body = {
            'merchant_id': '1344b5d5-0048-11e8-94db-005056a205be',
            'amount': order_obj.total_items_price,
            'description': f'Transaction for {order_obj.customer} customer | OrderID: {order_obj.id}',
            'callback_url': 'http://0.0.0.0:8000/store/payment'
        }

        response = requests.post(url=zarinpal_request_url, data=json.dumps(data_body), headers=request_header)

        try: 
            data = response.json()
        except json.JSONDecodeError as e:
            return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)
        
        if data['data'] and  data['data']['code'] == 100 and data['data']['message'] == 'Success' and not data['errors']:
            # delete the session about previous transaction
            if request.session.get('payment_data'):
                del request.session['payment_data']

            # if post request to zarinpal was successful store payment data in session in order to have them in GET request
            request.session['payment_data'] = {
                'merchant_id' : data_body['merchant_id'],
                'amount': data_body['amount'],
                'order_id': order_id,
            }

            authority = data['data']['authority']

            payment_url = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'.format(authority=authority)
            return Response(f'paymant_url: {payment_url}', status=status.HTTP_200_OK)
        else:
            return Response(f"request failed, errors : {data.get('errors')}", status=status.HTTP_400_BAD_REQUEST)
    
    def get_throttles(self):
        self.throttle_scope = 'payment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope)