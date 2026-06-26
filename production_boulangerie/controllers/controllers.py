# from odoo import http


# class ProductionBoulangerie(http.Controller):
#     @http.route('/production_boulangerie/production_boulangerie', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/production_boulangerie/production_boulangerie/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('production_boulangerie.listing', {
#             'root': '/production_boulangerie/production_boulangerie',
#             'objects': http.request.env['production_boulangerie.production_boulangerie'].search([]),
#         })

#     @http.route('/production_boulangerie/production_boulangerie/objects/<model("production_boulangerie.production_boulangerie"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('production_boulangerie.object', {
#             'object': obj
#         })

