# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductionSheet(models.Model):
    """Fiche de production : liste des produits fabriqués."""
    _name = 'production.sheet'
    _description = 'Fiche de Production'

    production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production',
        required=True,
        ondelete='cascade',
    )
    date = fields.Date(
        string='Date de production',
        required=True,
        default=fields.Date.context_today,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Emplacement de destination',
        required=True,
        domain=[('usage', '=', 'internal')],
        help="Emplacement de stock où seront déposés les produits fabriqués.",
    )
    line_ids = fields.One2many(
        comodel_name='production.sheet.line',
        inverse_name='sheet_id',
        string='Lignes de production',
    )
    total_amount = fields.Float(
        string='Montant total (gros)',
        compute='_compute_total_amount',
        store=True,
        digits='Product Price',
    )

    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        for sheet in self:
            sheet.total_amount = sum(sheet.line_ids.mapped('amount'))

