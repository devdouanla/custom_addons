from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import logging
logger = logging.getLogger(__name__)
class ProductionConsumptionLine(models.Model):
    """Ligne de consommation : une matiere premiere consommee."""
    _name = 'production.consumption.line'
    _description = 'Ligne de Consommation'

    production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production',
        required=True,
        ondelete='cascade',
         store=True
    )
    product_id = fields.Many2one(
        comodel_name='raw.material',        # ← remplace product.template
        string='Matiere premiere',
        required=True,
        store=True
    )
    standard_price = fields.Float(
        string="Prix d'achat",
        digits='Product Price',
        required=True,
        default=0.0,
        compute='_compute_standard_price',  # recupere depuis raw.material
        store=True,
        readonly=True,
        help="Recupere depuis la fiche matiere premiere, modifiable si besoin.",
    )
    opening_stock = fields.Float(
    string='Stock initial',
    compute='_compute_opening_stock',
    digits='Product Unit of Measure',
    help="Quantité disponible en début de journée/production.",
    store=True
)
    

    closing_stock = fields.Float(
        string='Stock final',
        digits='Product Unit of Measure',
        required=True,
        default=0.0,
        help="Quantite disponible en fin de journee/production.",
         store=True
    )
    consumption = fields.Float(
        string='Consommation',
        compute='_compute_consumption',
        store=True,
        digits='Product Unit of Measure',
        help="Calcule : stock initial - stock final.",
    )
    consumption_cost = fields.Float(
        string='Cout de consommation',
        compute='_compute_consumption_cost',
        store=True,
        digits='Product Price',
    )

    # ── Compute ──────────────────────────────────────────────────────────

    @api.depends('product_id')
    def _compute_standard_price(self):
        for line in self:
            if line.product_id:
                line.standard_price = line.product_id.standard_price
            else:
                line.standard_price = 0.0

    @api.depends('opening_stock', 'closing_stock')
    def _compute_consumption(self):
        for line in self:
            line.consumption = abs(line.opening_stock - line.closing_stock)

    @api.depends('consumption', 'standard_price')
    def _compute_consumption_cost(self):
        for line in self:
            line.consumption_cost = line.consumption * line.standard_price
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
                    "Ce produit est déjà ajouté dans la consommation."
                )


    @api.depends('product_id', 'production_id.location_id.stock_location_id')
    def _compute_opening_stock(self):
        for line in self:
            if line.product_id and line.production_id.location_id.stock_location_id:
                variant = line.product_id.product_variant_id
                line.opening_stock = self.env['stock.quant']._get_available_quantity(
                product_id=variant,
                    location_id=line.production_id.location_id.stock_location_id,
                )
            else:
                line.opening_stock = 0.0
    @api.constrains('product_id', 'production_id')
    def _check_location(self):
        for line in self:
            if line.product_id and not line.production_id.location_id.stock_location_id:
                raise ValidationError(
                "Aucun emplacement de stock trouvé pour la production %s." % (
                    line.production_id.name or line.production_id.display_name or _("(nouvelle)")
                )
                )
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            production_id = vals.get('production_id')
            if production_id:
                production = self.env['production.production'].browse(production_id)
                if production.state == 'done':
                    raise UserError((
                        "Impossible d'ajouter une ligne à une production déjà validée."
                    ))
        return super().create(vals_list)

    def write(self, vals):
        for line in self:
            if line.production_id.state == 'done':
                raise UserError((
                    "Impossible de modifier une ligne d'une production déjà validée."
                ))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.production_id.state == 'done':
                raise UserError((
                    "Impossible de supprimer une ligne d'une production déjà validée."
                ))
        return super().unlink()
                
