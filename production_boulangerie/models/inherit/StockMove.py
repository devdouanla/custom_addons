from odoo import models, fields, api

class StockMove(models.Model):
    """Extension de stock.move pour lier aux productions boulangerie."""
    _inherit = 'stock.move'

    bakery_production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production boulangerie',
        ondelete='set null',
        index=True,
    )
    # On surcharge le compute standard de "reference" pour y ajouter
    # une nouvelle dépendance : bakery_production_id.name
    @api.depends('picking_id.name', 'bakery_production_id.name')
    def _compute_reference(self):
        for move in self:
            # Ordre de priorité :
            # 1. Si le mouvement est rattaché à un picking (transfert standard Odoo) -> on garde son nom
            # 2. Sinon, si le mouvement vient d'une production Blé d'Or -> on utilise la référence de la production
            # 3. En dernier recours -> on retombe sur le nom du mouvement lui-même (comportement Odoo de base)
            move.reference = (
                move.picking_id.name
                or move.bakery_production_id.name
                or move.name
            )