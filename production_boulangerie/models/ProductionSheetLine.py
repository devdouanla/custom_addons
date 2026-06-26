from odoo import models, fields, api
from odoo.exceptions import ValidationError
class ProductionSheetLine(models.Model):
    """Ligne d'une fiche de production : un produit fini fabriqué."""
    _name = 'production.sheet.line'
    _description = 'Ligne de Fiche de Production'

    sheet_id = fields.Many2one(
        comodel_name='production.sheet',
        string='Fiche de production',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Produit fini',
        required=True,
        domain=[('bakery_product_type', '=', 'finished_product')],
    )
    quantity = fields.Float(
        string='Quantité produite',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
    )
    wholesale_price = fields.Float(
        string='Prix de gros',
        digits='Product Price',
        compute='_compute_wholesale_price',
        store=True,
        readonly=False,
        help="Récupéré depuis la fiche produit, modifiable si besoin.",
    )
    amount = fields.Float(
        string='Montant',
        compute='_compute_amount',
        store=True,
        digits='Product Price',
    )

    @api.depends('product_id')
    def _compute_wholesale_price(self):
        for line in self:
            if line.product_id and line.product_id.product_tag_ids:
                line.wholesale_price = line.product_id.product_tag_ids.wholesale_price
            else:
                line.wholesale_price = 0.0

    @api.depends('quantity', 'wholesale_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.wholesale_price
