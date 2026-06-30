# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Production(models.Model):
    """Production principale : regroupe fiche de production et fiche de consommation."""
    _name = 'production.production'
    _description = 'Production Boulangerie'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    production_day_id=fields.Many2one(
        comodel_name='production.day',
        string='le jour  de production',
        required=True,
        store=True,
        ondelete='cascade',
    )
    production_date = fields.Date(
    string="Date de production",
    related='production_day_id.date',
    store=True,
    readonly=True,
)
    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        index=True,
        readonly=True,
         store=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('production.production') or _('Nouveau')
        
    )
    responsable_id = fields.Many2one(
    comodel_name='res.partner',
    string='Responsable de production',
    required=False,           # Passez à True si vous voulez le rendre obligatoire
    tracking=True,
    help="Responsable en charge de ce bon de production.",
     store=True,
)

    state = fields.Selection(
        selection=[
            ('draft', 'Nouveau'),
            ('done', 'Validé'),
            ('cancelled', 'Annulé'),
        ],
        string='État',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
    )
    notes = fields.Text(string='Notes')

    # ── Fiches liées ────────────────────────────────────────────────────────────
    
# ── Bordereau de production (produits finis) ─────────────────────────────────
    sheet_line_ids = fields.One2many(
    comodel_name='production.sheet.line',
    inverse_name='production_id',
    string='Bordereau de production',
     store=True,
)

# ── Bordereau matières premières (consommation) ───────────────────────────────
    consumption_line_ids = fields.One2many(
    comodel_name='production.consumption.line',
    inverse_name='production_id',
    string='Bordereau matières premières',
     store=True,
)

    # ── KPIs rentabilité ────────────────────────────────────────────────────────
    production_value = fields.Float(
        string='Valeur de production',
        compute='_compute_kpis',
        store=True,
        digits='Product Price',
    )
    consumption_cost = fields.Float(
        string='Coût de consommation',
        compute='_compute_kpis',
        store=True,
        digits='Product Price',
    )
    profit = fields.Float(
        string='Profit',
        compute='_compute_kpis',
        store=True,
        digits='Product Price',
    )
    profit_rate = fields.Float(
        string='Taux de profit (%)',
        compute='_compute_kpis',
        store=True,
        digits=(16, 2),
    )
    
    # ── KPI Farine ───────────────────────────────────────────────────────────────
    
    farine_product_id = fields.Many2one(
        comodel_name='raw.material',
        string='matière stratégique',
        help="Sélectionner la farine pour calculer les indicateurs par sac.",
         store=True,
    )
    unite_mesure_farine_product = fields.Many2one(
    'uom.uom',
    string="unité de mesure",
    related='farine_product_id.unite_mesure',
    store=True,
    readonly=True,
    )

    farine_quantity = fields.Float(
        string='Quantité consommée',
    compute='_compute_farine_quantity',
    store=True,
    digits='Product Unit of Measure',
    default=0.0,
    )
    profit_per_bag = fields.Float(
        string='Profit par unite',
        compute='_compute_flour_kpis',
        store=True,
        digits='Product Price',
    )
    production_value_per_bag = fields.Float(
        string='Valeur production par unite',
        compute='_compute_flour_kpis',
        store=True,
        digits='Product Price',
    )
    currency_id = fields.Many2one(
    comodel_name='res.currency',
    string='Devise',
    default=lambda self: self.env.company.currency_id,
    readonly=True,
)
    location_id = fields.Many2one(
    comodel_name='stock.location',
    string='Emplacement de destination',
    domain=[('usage', 'in', ['internal', 'transit'])],
    required=False,
    readonly=False,
    store=True,
    help="Emplacement où seront stockés les produits finis après validation.",
)

    # ── Mouvements de stock générés ─────────────────────────────────────────────
    stock_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='bakery_production_id',
        string='Mouvements de stock',
        readonly=True,
    )
    stock_move_count = fields.Integer(
        string='Nb mouvements',
        compute='_compute_stock_move_count',
    )

    # ── Compute ──────────────────────────────────────────────────────────────────

    @api.depends(
    'sheet_line_ids.amount',
    'consumption_line_ids.consumption_cost',
)
    def _compute_kpis(self):
        for prod in self:
            prod.production_value = sum(prod.sheet_line_ids.mapped('amount'))
            prod.consumption_cost = sum(prod.consumption_line_ids.mapped('consumption_cost'))
            prod.profit = prod.production_value - prod.consumption_cost
            if prod.consumption_cost:
                prod.profit_rate = (prod.profit / prod.consumption_cost) * 100.0
            else:
                prod.profit_rate = 0.0

    @api.depends('profit', 'production_value', 'farine_quantity')
    def _compute_flour_kpis(self):
        for prod in self:
            if prod.farine_quantity:
                prod.profit_per_bag = prod.profit / prod.farine_quantity
                prod.production_value_per_bag = prod.production_value / prod.farine_quantity
            else:
                prod.profit_per_bag = 0.0
                prod.production_value_per_bag = 0.0

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for prod in self:
            prod.stock_move_count = len(prod.stock_move_ids)
    
    @api.depends('consumption_line_ids.product_id', 'consumption_line_ids.consumption', 'farine_product_id')
    def _compute_farine_quantity(self):
        for rec in self:
            if rec.farine_product_id:
                rec.farine_quantity =abs(sum(
                    rec.consumption_line_ids.filtered(
                    lambda l: l.product_id == rec.farine_product_id
                    ).mapped('consumption')
                ))
                
            else:
                rec.farine_quantity = 0.0
    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code('production.production')
            
            # Vous pouvez ajouter d'autres initialisations ici (date, etc.)
        
        return super().create(vals_list)
    # ── Actions ──────────────────────────────────────────────────────────────────

    def action_validate(self):
     """Valide la production : crée les mouvements de stock et passe en 'done'."""
     self.ensure_one()

     if self.state != 'draft':
         raise UserError(_("Seules les productions en brouillon peuvent être validées."))

     if not self.sheet_line_ids:
         raise UserError(_("Veuillez ajouter au moins un produit fini dans le bordereau de production."))
     if not self.consumption_line_ids:
         raise UserError(_("Veuillez ajouter au moins une matière première dans le bordereau matières premières."))

    # Emplacement de destination : récupéré depuis le premier champ location_id
    # si vous avez conservé un location_id sur production.production, sinon adaptez
     location_id = self.location_id
     if not location_id:
        raise UserError(_("L'emplacement de destination est requis."))

     production_location = self._get_production_location()

    # Valider les consommations
     for line in self.consumption_line_ids:
         if line.consumption <= 0:
             raise ValidationError(_(
                "La consommation de '%s' est nulle ou négative. "
                "Vérifiez les stocks initial et final.",
                line.product_id.display_name,
             ))

     moves_to_confirm = self.env['stock.move']

    # A. Produits fabriqués
     for line in self.sheet_line_ids:
         if line.quantity <= 0:
             continue
         moves_to_confirm |= self._create_finished_product_move(
            line=line,
            src_location=production_location,
            dest_location=location_id,
        )

    # B. Matières premières consommées
     for line in self.consumption_line_ids:
         if line.consumption <= 0:
             continue
         moves_to_confirm |= self._create_raw_material_move(
            line=line,
            src_location=location_id,
            dest_location=production_location,
        )

     if moves_to_confirm:
         moves_to_confirm._action_confirm()
         moves_to_confirm._action_assign()
         for move in moves_to_confirm:
             for move_line in move.move_line_ids:
                 move_line.quantity = move.product_uom_qty
         moves_to_confirm._action_done()

     self.write({'state': 'done'})
     return True

    def action_cancel(self):
        """Annule la production (uniquement en brouillon)."""
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Impossible d'annuler une production validée."))
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        """Repasse en brouillon (uniquement si annulé)."""
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError(_("Seules les productions annulées peuvent être réinitialisées."))
        self.write({'state': 'draft'})

    def action_view_stock_moves(self):
        """Ouvre la liste des mouvements de stock liés."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mouvements de stock'),
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.stock_move_ids.ids)],
            'context': {'create': False},
        }

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _get_production_location(self):
        """Retourne l'emplacement virtuel de production (Production/Input)."""
        location = self.env['stock.location'].search(
            [('usage', '=', 'production')], limit=1
        )
        if not location:
            raise UserError(_(
                "Aucun emplacement de type 'Production' trouvé. "
                "Veuillez vérifier la configuration de votre inventaire."
            ))
        return location

    def _create_finished_product_move(self, line, src_location, dest_location):
        """Crée un stock.move pour un produit fini fabriqué."""
        return self.env['stock.move'].create({
            'name': _('Production: %s', line.product_id.display_name),
            'product_id': line.product_id.id,
            'product_uom_qty': line.quantity,
            'product_uom': line.product_id.uom_id.id,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'bakery_production_id': self.id,
            'origin': self.name,
        })

    def _create_raw_material_move(self, line, src_location, dest_location):
        """Crée un stock.move pour une matière première consommée."""
        return self.env['stock.move'].create({
            'name': _('Consommation: %s', line.product_id.display_name),
            'product_id': line.product_id.id,
            'product_uom_qty': line.consumption,
            'product_uom': line.product_id.uom_id.id,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'bakery_production_id': self.id,
            'origin': self.name,
        })

    used_finished_product_ids = fields.Many2many(
    comodel_name='bakery.product',
    compute='_compute_used_products',
    string='Produits finis déjà utilisés',
)
    used_raw_material_ids = fields.Many2many(
    comodel_name='raw.material',
    compute='_compute_used_products',
    string='Matières premières déjà utilisées',
)

    @api.depends('sheet_line_ids.product_id', 'consumption_line_ids.product_id')
    def _compute_used_products(self):
        for prod in self:
            prod.used_finished_product_ids = prod.sheet_line_ids.mapped('product_id')
            prod.used_raw_material_ids = prod.consumption_line_ids.mapped('product_id')
class StockMove(models.Model):
    """Extension de stock.move pour lier aux productions boulangerie."""
    _inherit = 'stock.move'

    bakery_production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production boulangerie',
        ondelete='set null',
        index=True,
    )
