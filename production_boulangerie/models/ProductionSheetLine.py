from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class ProductionSheetLine(models.Model):
    """Ligne d'une fiche de production : un produit fini fabrique."""
    _name = 'production.sheet.line'
    _description = 'Ligne de Fiche de Production'

    production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='bakery.product',
        string='Produit fini',
        required=True,
    )
    quantity = fields.Float(
        string='Quantite produite',
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
        help="Recupere depuis la fiche produit (prix_en_gros), modifiable si besoin.",
    )
    amount = fields.Float(
        string='Montant',
        compute='_compute_amount',
        store=True,
        digits='Product Price',
    )

    # ── Compute ──────────────────────────────────────────────────────────

    @api.depends('product_id')
    def _compute_wholesale_price(self):
        for line in self:
            # prix_en_gros est le champ direct sur bakery.product
            if line.product_id:
                line.wholesale_price = line.product_id.prix_en_gros
            else:
                line.wholesale_price = 0.0

    @api.depends('quantity', 'wholesale_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.wholesale_price
    #----verification de ligne----------------------------------------------------
    @api.constrains('product_id', 'production_id')
    def _check_duplicate_product(self):
        for rec in self:
            duplicates = self.search([
                ('production_id', '=', rec.production_id.id),
                ('product_id', '=', rec.product_id.id),
                ('id', '!=', rec.id),
            ])
            if duplicates:
                raise ValidationError(
                    "Ce produit est déjà ajouté dans la production."
                )