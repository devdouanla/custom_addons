from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ProductionSheetLine(models.Model):
    """Ligne d'une fiche de production : un produit fini fabrique."""
    _name = 'production.sheet.line'
    _description = 'Ligne de Fiche de Production'

    production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production',
        required=True,
        ondelete='cascade',
         store=True
    )
    product_id = fields.Many2one(
        comodel_name='bakery.product',
        string='Produit fini',
        required=True,
         store=True
    )
    quantity = fields.Float(
        string='Quantite produite',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
         store=True
    )
    wholesale_price = fields.Float(
        string='Prix de gros',
        digits='Product Price',
        compute='_compute_wholesale_price',
        store=True,
        readonly=True,
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
         # ── Verrouillage : bordereau de production approuvé ─────────────────────

    def _check_bordereau_not_locked(self, production=None):
        """Lève une erreur si le bordereau de production est déjà approuvé."""
        productions = production or self.mapped('production_id')
        for prod in productions:
            if prod.validerBordereauProduction:
                raise UserError(_(
                    "Le bordereau de production de '%s' a été approuvé : "
                    "il n'est plus possible de le modifier."
                ) % prod.name)
   # ── Verrouillage : bordereau de production approuvé ─────────────────────

    def _check_bordereau_not_locked(self, production=None):
        """Lève une erreur si le bordereau de production est verrouillé :
        soit parce que la production est déjà validée ('done'), soit parce
        que le bordereau a été explicitement approuvé."""
        productions = production or self.mapped('production_id')
        for prod in productions:
            if prod.state == 'done':
                raise UserError(_(
                    "Impossible de modifier une ligne d'une production déjà validée ('%s')."
                ) % prod.name)
            if prod.validerBordereauProduction:
                raise UserError(_(
                    "Le bordereau de production de '%s' a été approuvé : "
                    "il n'est plus possible de le modifier."
                ) % prod.name)

    @api.model_create_multi
    def create(self, vals_list):
        Production = self.env['production.production']
        for vals in vals_list:
            production_id = vals.get('production_id')
            if production_id:
                self._check_bordereau_not_locked(Production.browse(production_id))
        return super().create(vals_list)

    def write(self, vals):
        self._check_bordereau_not_locked()
        return super().write(vals)

    def unlink(self):
        self._check_bordereau_not_locked()
        return super().unlink()
