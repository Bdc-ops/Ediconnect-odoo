from odoo import http
from odoo.http import request
from datetime import datetime

class ImportOrderController(http.Controller):
    @http.route('/import/orders', type='json', auth='user', methods=['POST'])
    def import_orders(self):
        data = request.jsonrequest.get('params', {})
        orders = data.get('orders', [])
        if not orders:
            return {"error": "Invalid data format"}

        results = []
        for order in orders:
            try:
                date_order = datetime.strptime(order.get('date_order'), "%d/%m/%Y %H:%M:%S")
                effective_date = datetime.strptime(order.get('effective_date'), "%d/%m/%Y %H:%M:%S")
            except ValueError as e:
                return {"error": f"Date format error: {str(e)}"}

            result = self.create_order(order, date_order, effective_date)
            results.append(result)

        return {"message": "Orders processed successfully", "results": results}

    def create_order(self, order_data, date_order, effective_date):
        Order = request.env['sale.order']
        Product = request.env['product.product']

        # Formatage des dates pour les notes
        formatted_date_order = date_order.strftime('%d/%m/%Y')
        formatted_effective_date = effective_date.strftime('%d/%m/%Y')
        notes = f"Date de commande : {formatted_date_order}, Date de livraison prévue : {formatted_effective_date}"

        order_lines = []
        for line in order_data.get('lines', []):
            product = Product.search([('barcode', '=', line['barcode'])])
            if not product.exists():
                raise ValueError(f"Product with barcode {line['barcode']} not found")

            order_lines.append((0, 0, {
                'product_id': product.id,
                'product_uom_qty': line['quantity'],
                'price_unit': product.lst_price  # Standard selling price
            }))

        order_vals = {
            'partner_id': order_data.get('partner_id'),
            'date_order': date_order,
            'client_order_ref': order_data.get('client_order_ref'),
            'effective_date': effective_date,
            'note': notes,  # Ajout des notes avec les dates
            'order_line': order_lines
        }
        
        order = Order.create(order_vals)
        order.action_confirm()
        return {
            "order_id": order.id, 
            "state": order.state
        }
