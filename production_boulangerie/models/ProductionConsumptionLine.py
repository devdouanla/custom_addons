from odoo import models, fields, api
from odoo.exceptions import ValidationError
class ProductionConsumptionLine(models.Model):
    """Ligne de consommation : une matière première consommée."""
    _name = 'production.consumption.line'
    _description = 'Ligne de Consommation'

    consumption_id = fields.Many2one(
        comodel_name='production.consumption',
        string='Fiche de consommation',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Matière première',
        required=True,
        domain=[('bakery_product_type', '=', 'raw_material')],
    )
    purchase_price = fields.Float(
        string="Prix d'achat",
        digits='Product Price',
        required=True,
        default=0.0,
    )
    opening_stock = fields.Float(
        string='Stock initial',
        digits='Product Unit of Measure',
        required=True,
        default=0.0,
        help="Quantité disponible en début de journée/production.",
    )
    closing_stock = fields.Float(
        string='Stock final',
        digits='Product Unit of Measure',
        required=True,
        default=0.0,
        help="Quantité disponible en fin de journée/production.",
    )
    consumption = fields.Float(
        string='Consommation',
        compute='_compute_consumption',
        store=True,
        digits='Product Unit of Measure',
        help="Calculé : stock initial - stock final.",
    )
    consumption_cost = fields.Float(
        string='Coût de consommation',
        compute='_compute_consumption_cost',
        store=True,
        digits='Product Price',
    )

    @api.depends('opening_stock', 'closing_stock')
    def _compute_consumption(self):
        for line in self:
            line.consumption = line.opening_stock - line.closing_stock

    @api.depends('consumption', 'purchase_price')
    def _compute_consumption_cost(self):
        for line in self:
            line.consumption_cost = line.consumption * line.purchase_price
