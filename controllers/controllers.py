from odoo import http
import json
import requests

class EdiConnect(http.Controller):
    @http.route('/edi-connect/export_json/<int:invoice_id>', auth='user', type='http')
    def export_json(self, invoice_id, **kw):
        try:
            invoice = http.request.env['account.move'].browse(invoice_id)
            if not invoice.exists():
                return http.request.make_response(
                    'Invoice not found',
                    headers=[('Content-Type', 'text/plain;charset=utf-8')]
                )

            # Obtenir toutes les données de la facture
            invoice_data = invoice.read(fields=None)[0]  # Lecture sans spécifier les champs pour obtenir tous les champs stockés

            # Exclure les champs d'image et d'avatar
            image_fields = ["image_1920", "image_1024", "image_512", "image_256", "image_128", "avatar_1920"]
            for field in image_fields:
                invoice_data.pop(field, None)  # Utiliser pop pour supprimer les champs si présents

            # Récupérer les données du client
            client_data = invoice.partner_id.read(fields=None)[0]

            # Exclure les champs d'image pour le client
            for field in image_fields:
                client_data.pop(field, None)

            # Mettre à jour les données de la facture avec les informations du client
            invoice_data['client_info'] = client_data
            partner = invoice.partner_id
            partner_data = partner.read([
                    'parent_id', 'street', 'street2', 'city', 'zip', 'country_id', 'vat',
                    'phone', 'mobile', 'email', 'website', 'lang', 'category_id'
            ])[0]
    
                # Formatage des informations du partenaire pour inclure des détails supplémentaires
            partner_data_formatted = {
                    'Nom du Parent': partner_data['parent_id'][1] if partner_data['parent_id'] else '',
                    'Adresse': f"{partner_data.get('street', '')} {partner_data.get('street2', '')}\n{partner_data.get('zip', '')} {partner_data.get('city',                       '')}, {partner_data['country_id'][1] if partner_data['country_id'] else ''}",
                    'TVA': partner_data['vat'],
                    'Téléphone': partner_data['phone'],
                    'Mobile': partner_data['mobile'],
                    'Email': partner_data['email'],
                    'Site Web': partner_data['website'],
                    'Langue': partner_data['lang'],
                    'Étiquettes': ', '.join([label.name for label in partner.category_id]),
            }
            # Ajouter les détails des produits pour chaque ligne de facture
            product_lines = []
            for line in invoice.invoice_line_ids:
                product_data = line.product_id.read(fields=None)[0]
                # Exclure les champs d'image pour chaque produit
                for field in image_fields:
                    product_data.pop(field, None)
                product_lines.append(product_data)

            invoice_data['product_lines'] = product_lines
            invoice_data['partner'] = partner_data_formatted
            # Convertir les données en JSON
            json_output = json.dumps(invoice_data, ensure_ascii=False, default=str)  # Utiliser default=str pour gérer les types non sérialisables
            json_output_encoded = json_output.encode('utf-8')

            # Envoyer les données JSON à l'URL spécifiée
            response = requests.post('https://dmz.anexys.fr/as2?odoo?json', data=json_output_encoded, headers={'Content-Type': 'application/json'})

            # Vérifier la réponse de la requête
            if response.status_code == 200:
                return http.request.make_response(
                    'Successfully sent JSON to external server',
                    headers=[('Content-Type', 'text/plain;charset=utf-8')]
                )
            else:
                return http.request.make_response(
                    f'Failed to send JSON, status code: {response.status_code}',
                    headers=[('Content-Type', 'text/plain;charset=utf-8')]
                )

        except Exception as e:
            # Log l'exception au logger Odoo
            http.request.env.cr.rollback()
            http.request.env['ir.logging'].create({
                'name': "EDI-Connect",
                'type': 'server',
                'dbname': http.request.env.cr.dbname,
                'level': 'ERROR',
                'message': str(e),
                'path': 'controller',
                'line': 'JSON Export',
                'func': 'export_json'
            })
            # Retourner un message d'erreur
            return http.request.make_response(
                f'An error occurred: {str(e)}',
                headers=[('Content-Type', 'text/plain;charset=utf-8')]
            )
