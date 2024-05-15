from odoo import models, api
import csv
import requests
from datetime import datetime

class Desadv(models.Model):
    _name = 'my_module.stock_picking'

    def export_delivery_orders_to_csv(self):
        for order in self:
            filename = 'desadv_' + str(order.id) + '.csv'
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([order.name, order.date, order.partner_id.name, order.amount_total])

            self.send_to_destination(filename)

    @api.model
    def send_to_destination(self, filename):
        try:
            basename = filename.split('/')[-1]
            ch = requests.post("http://dmz.anexys.fr/as2?ediconnect", files={'file': open(filename, 'rb')})
            if ch.status_code != 200:
                print("[" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "] [ERROR] HTTP error: " + str(ch.status_code) + "\n\n")
            else:
                print("[" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "] [SUCCESS] DESADV file sent to destination successfully.\n\n")
        except Exception as e:
            print(e)
            print("[" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "] [ERROR] Exception in send_to_destination(): " + str(e) + "\n\n")
