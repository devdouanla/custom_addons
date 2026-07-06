# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class Production(models.Model):
    """Production principale : regroupe fiche de production et fiche de consommation."""
    _name = 'production.production'
    _description = 'Production Boulangerie'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    production_day_id = fields.Many2one(
        comodel_name='production.day',
        string='Le jour de production',
        required=True,
        store=True,
        ondelete='cascade',
        default=lambda self: self._default_production_day_id(),
    )
    production_date = fields.Date(
        string="Date de production",
        related='production_day_id.date',
        store=True,
        readonly=True,
    )
    name = fields.Char(
        string="Référence",
        compute='_compute_reference',
        store=True,
        readonly=True,
        copy=False,
    )
    responsable_id = fields.Many2one(
        comodel_name='res.partner',
        string='Responsable de production',
        required=False,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        readonly=True,
        help="Responsable en charge de ce bon de production.",
        store=True,
    )

    # ── Verrous indépendants par bordereau ───────────────────────────────────
    validerBordereauProduction = fields.Boolean(
        string="Bordereau de production approuvé",
        default=False,
        copy=False,
        tracking=True,
        help="Une fois activé, le bordereau de production (produits finis) "
             "ne peut plus être modifié.",
    )
    validerBordereauConsommation = fields.Boolean(
        string="Bordereau de consommation approuvé",
        default=False,
        copy=False,
        tracking=True,
        help="Une fois activé, le bordereau matières premières "
             "ne peut plus être modifié.",
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Nouveau'),
            ('ondoing', 'En cours'),
            ('waiting', 'En attente'),
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

    # ── Fiches liées ──────────────────────────────────────────────────────────
    sheet_line_ids = fields.One2many(
        comodel_name='production.sheet.line',
        inverse_name='production_id',
        string='Bordereau de production',
        store=True,
    )
    consumption_line_ids = fields.One2many(
        comodel_name='production.consumption.line',
        inverse_name='production_id',
        string='Bordereau matières premières',
        store=True,
    )

    # ── KPIs rentabilité ──────────────────────────────────────────────────────
    production_value = fields.Float(
        string='Valeur de production', compute='_compute_kpis',
        store=True, digits='Product Price',
    )
    consumption_cost = fields.Float(
        string='Coût de consommation', compute='_compute_kpis',
        store=True, digits='Product Price',
    )
    profit = fields.Float(
        string='Profit', compute='_compute_kpis',
        store=True, digits='Product Price',
    )
    profit_rate = fields.Float(
        string='Taux de profit (%)', compute='_compute_kpis',
        store=True, digits=(16, 2),
    )

    # ── KPI Farine ────────────────────────────────────────────────────────────
    farine_product_id = fields.Many2one(
        comodel_name='raw.material',
        string='Matière stratégique',
        help="Sélectionner la farine pour calculer les indicateurs par sac.",
        store=True,
    )
    unite_mesure_farine_product = fields.Many2one(
        'uom.uom',
        string="Unité de base",
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
        string='Profit par unité de mesure', compute='_compute_flour_kpis',
        store=True, digits='Product Price',
    )
    production_value_per_bag = fields.Float(
        string='Valeur production par unité de mesure', compute='_compute_flour_kpis',
        store=True, digits='Product Price',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    display_uom_id = fields.Many2one('uom.uom', string="Unité d'affichage")
    location_id = fields.Many2one(
        comodel_name='type.production',
        related='production_day_id.type_production_id',
        string='Emplacement de destination',
        required=False,
        readonly=False,
        store=True,
        help="Emplacement où seront stockés les produits finis après validation.",
    )

    # ── Mouvements de stock générés ──────────────────────────────────────────
    stock_move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='bakery_production_id',
        string='Mouvements de stock',
        readonly=True,
    )
    stock_move_count = fields.Integer(
        string='Nb mouvements', compute='_compute_stock_move_count',
    )

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

    # ── Compute ───────────────────────────────────────────────────────────────

    @api.depends('sheet_line_ids.amount', 'consumption_line_ids.consumption_cost')
    def _compute_kpis(self):
        for prod in self:
            prod.production_value = sum(prod.sheet_line_ids.mapped('amount'))
            prod.consumption_cost = sum(prod.consumption_line_ids.mapped('consumption_cost'))
            prod.profit = prod.production_value - prod.consumption_cost
            prod.profit_rate = (prod.profit / prod.consumption_cost * 100.0) if prod.consumption_cost else 0.0

    @api.depends('profit', 'production_value', 'farine_quantity',
                 'unite_mesure_farine_product', 'display_uom_id')
    def _compute_flour_kpis(self):
        for prod in self:
            prod.profit_per_bag = 0.0
            prod.production_value_per_bag = 0.0
            if not prod.farine_quantity:
                continue
            qty = prod.farine_quantity
            if (prod.unite_mesure_farine_product and prod.display_uom_id
                    and prod.unite_mesure_farine_product != prod.display_uom_id):
                qty = prod.unite_mesure_farine_product._compute_quantity(
                    prod.farine_quantity, prod.display_uom_id
                )
            if qty > 0:
                prod.profit_per_bag = prod.profit / qty
                prod.production_value_per_bag = prod.production_value / qty

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for prod in self:
            prod.stock_move_count = len(prod.stock_move_ids)

    @api.depends('consumption_line_ids.product_id', 'consumption_line_ids.consumption', 'farine_product_id')
    def _compute_farine_quantity(self):
        for rec in self:
            if rec.farine_product_id:
                rec.farine_quantity = abs(sum(
                    rec.consumption_line_ids.filtered(
                        lambda l: l.product_id == rec.farine_product_id
                    ).mapped('consumption')
                ))
            else:
                rec.farine_quantity = 0.0

    @api.depends('sheet_line_ids.product_id', 'consumption_line_ids.product_id')
    def _compute_used_products(self):
        for prod in self:
            prod.used_finished_product_ids = prod.sheet_line_ids.mapped('product_id')
            prod.used_raw_material_ids = prod.consumption_line_ids.mapped('product_id')

    @api.onchange('farine_product_id')
    def _onchange_farine_product_id(self):
        if self.farine_product_id:
            self.display_uom_id = self.farine_product_id.unite_mesure

    @api.depends('location_id', 'production_date')
    def _compute_reference(self):
        for rec in self:
            if rec.name:
                continue
            if rec.location_id and rec.production_date:
                date_value = rec.production_date
                if isinstance(date_value, str):
                    date_value = fields.Date.from_string(date_value)
                date_str = date_value.strftime('%d/%m/%Y')
                location_code = rec.location_id.code or "UNK"
                sequence_number = self.env['ir.sequence'].next_by_code('production.production') or '000'
                rec.name = "%s/PROD/%s%s" % (location_code, date_str, sequence_number)
            else:
                rec.name = False

    # ── Verrouillage de l'écriture ───────────────────────────────────────────
    # Champs "techniques" : recalculs internes qui ne doivent jamais être
    # bloqués ni déclencher de changement d'état.
    _TECHNICAL_FIELDS = {
        'state', 'production_value', 'consumption_cost', 'profit', 'profit_rate',
        'farine_quantity', 'profit_per_bag', 'production_value_per_bag',
        'stock_move_count', 'used_finished_product_ids', 'used_raw_material_ids',
        'name', 'production_date', 'unite_mesure_farine_product',
    }

    def write(self, vals):
        # Aucune restriction sur "le reste" des champs : seuls les bordereaux
        # sont verrouillés, et ce verrouillage est géré par les modèles de
        # lignes eux-mêmes (production.sheet.line / production.consumption.line).
        is_technical_only = set(vals.keys()) <= self._TECHNICAL_FIELDS

        if 'state' not in vals and not is_technical_only:
            drafts = self.filtered(lambda r: r.state == 'draft')
            others = self - drafts
            if drafts:
                super(Production, drafts).write(dict(vals, state='ondoing'))
            if others:
                super(Production, others).write(vals)
            return True

        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered(lambda r: r.state == 'draft').write({'state': 'ondoing'})
        return records

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_approve_bordereau_production(self):
        """Verrouille le bordereau de production (produits finis)."""
        self.ensure_one()
        if self.state != 'ondoing':
            raise UserError(_("Le bordereau de production ne peut être approuvé qu'en cours de saisie."))
        if not self.sheet_line_ids:
            raise UserError(_("Le bordereau de production est vide."))
        self.write({'validerBordereauProduction': True})

    def action_reopen_bordereau_production(self):
        """Déverrouille le bordereau de production (avant soumission uniquement)."""
        self.ensure_one()
        if self.state != 'ondoing':
            raise UserError(_("Impossible de rouvrir le bordereau de production à ce stade."))
        self.write({'validerBordereauProduction': False})

    def action_approve_bordereau_consommation(self):
        """Verrouille le bordereau matières premières."""
        self.ensure_one()
        if self.state != 'ondoing':
            raise UserError(_("Le bordereau de consommation ne peut être approuvé qu'en cours de saisie."))
        if not self.consumption_line_ids:
            raise UserError(_("Le bordereau matières premières est vide."))
        self.write({'validerBordereauConsommation': True})

    def action_reopen_bordereau_consommation(self):
        """Déverrouille le bordereau matières premières (avant soumission uniquement)."""
        self.ensure_one()
        if self.state != 'ondoing':
            raise UserError(_("Impossible de rouvrir le bordereau de consommation à ce stade."))
        self.write({'validerBordereauConsommation': False})

    def action_soumettre(self):
        """Soumet la production pour validation : passe en 'waiting'."""
        self.ensure_one()
        if self.state != 'ondoing':
            raise UserError(_("Seules les fiches de production en cours peuvent être soumises."))
        if not self.validerBordereauProduction:
            raise UserError(_("Veuillez approuver le bordereau de production avant de soumettre."))
        if not self.validerBordereauConsommation:
            raise UserError(_("Veuillez approuver le bordereau de consommation avant de soumettre."))
        self.write({'state': 'waiting'})

    def action_validate(self):
        """Valide la production : crée les mouvements de stock et passe en 'done'."""
        self.ensure_one()

        if self.state != 'waiting':
            raise UserError(_("Seules les fiches de production en attente peuvent être validées."))

        if not self.sheet_line_ids:
            raise UserError(_("Veuillez ajouter au moins un produit fini dans le bordereau de production."))
        if not self.consumption_line_ids:
            raise UserError(_("Veuillez ajouter au moins une matière première dans le bordereau matières premières."))

        location_id = self.location_id
        if not location_id:
            raise UserError(_("L'emplacement de destination est requis."))

        production_location = self._get_production_location()

        for line in self.consumption_line_ids:
            if line.consumption <= 0:
                raise ValidationError(_(
                    "La consommation de '%s' est nulle ou négative. "
                    "Vérifiez les stocks initial et final.",
                    line.product_id.display_name,
                ))

        moves_to_confirm = self.env['stock.move']

        for line in self.sheet_line_ids:
            if line.quantity <= 0:
                continue
            moves_to_confirm |= self._create_finished_product_move(
                line=line,
                src_location=production_location,
                dest_location=location_id.stock_location_id,
            )

        for line_consumption in self.consumption_line_ids:
            if line_consumption.consumption <= 0:
                continue
            moves_to_confirm |= self._create_raw_material_move(
                line=line_consumption,
                src_location=location_id.stock_location_id,
                dest_location=production_location,
            )

        if moves_to_confirm:
            try:
                moves_to_confirm._action_confirm()
                moves_to_confirm._action_assign()

                for move in moves_to_confirm:
                    if not move.move_line_ids:
                        _logger.warning(
                            "Aucune move_line créée pour le move %s (produit %s, qty %s) "
                            "- stock probablement insuffisant à la source %s",
                            move.id, move.product_id.display_name,
                            move.product_uom_qty, move.location_id.display_name,
                        )
                    for move_line in move.move_line_ids:
                        move_line.quantity = move.product_uom_qty
                        move_line.picked = True  # <-- indispensable en Odoo 17+/19

                moves_to_confirm._action_done()

            except (UserError, ValidationError) as e:
                _logger.exception("Échec de la validation des mouvements de stock")
                raise UserError(_(
                    "Erreur lors de la validation des mouvements de stock : %s"
                ) % str(e))

        self.write({'state': 'done'})
        return True

    def action_cancel(self):
        """Annule la production (impossible si déjà validée)."""
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Impossible d'annuler une production validée."))
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        """Repasse en brouillon (uniquement si annulé) et rouvre les bordereaux."""
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError(_("Seules les productions annulées peuvent être réinitialisées."))
        self.write({
            'state': 'draft',
            'validerBordereauProduction': False,
            'validerBordereauConsommation': False,
        })

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

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_production_location(self):
        location = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
        if not location:
            raise UserError(_(
                "Aucun emplacement de type 'Production' trouvé. "
                "Veuillez vérifier la configuration de votre inventaire."
            ))
        return location

    def _create_finished_product_move(self, line, src_location, dest_location):
        finished_product = line.product_id
        variant = finished_product.product_variant_id
        if not variant:
            raise UserError(_(
                "Impossible de trouver la variante produit pour '%s'.",
                finished_product.display_name,
            ))
        return self.env['stock.move'].create({
            'reference': self.name,
            'product_id': variant.id,
            'product_uom_qty': line.quantity,
            'product_uom': variant.uom_id.id,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'company_id': self.env.company.id,
            'bakery_production_id': self.id,
            'origin': self.name,
        })

    def _create_raw_material_move(self, line, src_location, dest_location):
        raw_material = line.product_id
        variant = raw_material.product_variant_id
        if not variant:
            raise UserError(_(
                "Impossible de trouver la variante produit pour '%s'.",
                raw_material.display_name,
            ))
        return self.env['stock.move'].create({
            'reference': self.name,
            'product_id': variant.id,
            'product_uom_qty': line.consumption,
            'product_uom': variant.uom_id.id,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'company_id': self.env.company.id,
            'bakery_production_id': self.id,
            'origin': self.name,
        })

    def _default_production_day_id(self):
        """Récupère le production.day du jour, le crée automatiquement s'il n'existe pas."""
        today = fields.Date.context_today(self)
        ProductionDay = self.env['production.day']
        day = ProductionDay.search([('date', '=', today)], limit=1)
        if not day:
            default_type_id = self.env['production.day']._default_type_production_id()
            if not default_type_id:
                return False
            day = ProductionDay.create({
                'date': today,
                'type_production_id': default_type_id,
            })
        return day.id