from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.orm import decorators as api
class ProductionDay(models.Model):
    _name = 'production.day'
    _description = 'Production Day'
    _order = 'date desc, id desc'

    reference = fields.Char(
    string="Référence",
    compute="_compute_reference",
    store=True,
    readonly=True,
)
   
    date = fields.Date(string='Date', required=True)
    type_production_id = fields.Many2one(
        comodel_name="type.production",
        string="Type de production",
            store=True,

        required=False,
    )
    type_production_id = fields.Many2one(
        comodel_name="type.production",
        string="Type de production",
        store=True,

        required=False,
    )
    type_production_name = fields.Char(
    compute="_compute_type_name",
    store=True,
    readonly=True,
)
    @api.depends('type_production_id')
    def _compute_type_name(self):
        for rec in self:
            rec.type_production_name = rec.type_production_id.name or ''
    production_ids = fields.One2many('production.production', 'production_day_id', )
    @api.constrains('date')
    def _check_unique_date(self):
        """Vérifie que la date est unique pour éviter les doublons."""
        for rec in self:
            if rec.date:
                existing = self.search([('date', '=', rec.date), ('id', '!=', rec.id)])
                if existing:
                    raise ValidationError(
                        "Une journée de production existe déjà pour la date %s." % rec.date
                    )
    @api.depends('type_production_id', 'date')
    def _compute_reference(self):
            for rec in self:
                if rec.type_production_id and rec.date:
                    rec.reference = "%s/%s" % (
                    rec.type_production_id.code,
                    rec.date.strftime("%d/%m/%Y")
                    )
                else:
                    rec.reference = False
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si aucun type de production n'est renseigné,
        # on ne génère pas de référence.
            if not vals.get('type_production_id'):
                vals['reference'] = False
            continue

        type_production = self.env['type.production'].browse(vals['type_production_id'])

        if vals.get('date'):
            date = fields.Date.to_date(vals['date'])
            reference = f"{type_production.code}/{date.strftime('%d/%m/%Y')}"
            vals['reference'] = reference

        return super().create(vals_list)