# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductionConsumption(models.Model):
    """Fiche de consommation : matières premières utilisées."""
    _name = 'production.consumption'
    _description = 'Fiche de Consommation'

    production_id = fields.Many2one(
        comodel_name='production.production',
        string='Production',
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        comodel_name='production.consumption.line',
        inverse_name='consumption_id',
        string='Lignes de consommation',
    )
    total_consumption_cost = fields.Float(
        string='Coût total de consommation',
        compute='_compute_total_cost',
        store=True,
        digits='Product Price',
    )

    @api.depends('line_ids.consumption_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_consumption_cost = sum(rec.line_ids.mapped('consumption_cost'))

