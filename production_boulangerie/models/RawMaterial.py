from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RawMaterial(models.Model):
    """Matiere premiere utilisee dans la production boulangerie."""
    _name = 'raw.material'
    _inherits = {'product.template': 'product_template_id'}
    _description = 'Matiere Premiere'

    product_template_id = fields.Many2one(
        comodel_name='product.template',
        string='Fiche produit',
        required=True,
        ondelete='cascade',
        
    )

    # ── Champs specifiques matieres premieres ────────────────────────────

    purchase_price = fields.Float(
        string="Prix d'achat unitaire",
        digits='Product Price',
        default=0.0,
        help="Prix d'achat par unite de mesure.",
    )
  
    stock_minimum = fields.Float(
        string='Stock minimum',
        digits='Product Unit of Measure',
        default=0.0,
        help="Seuil d'alerte de stock bas.",
    )
    stock_actuel = fields.Float(
        string='Stock actuel',
        digits='Product Unit of Measure',
        default=0.0,
        help="Quantite disponible en stock au moment de la saisie.",
    )
 
    unite_mesure = fields.Many2one(
    'uom.uom',
    string="Unité de mesure"
)
       
    # ── Constraintes ─────────────────────────────────────────────────────

    @api.constrains('purchase_price')
    def _check_purchase_price(self):
        for rec in self:
            if rec.purchase_price < 0:
                raise ValidationError(
                    "Le prix d'achat ne peut pas etre negatif."
                )

    @api.constrains('stock_minimum')
    def _check_stock_minimum(self):
        for rec in self:
            if rec.stock_minimum < 0:
                raise ValidationError(
                    "Le stock minimum ne peut pas etre negatif."
                )
