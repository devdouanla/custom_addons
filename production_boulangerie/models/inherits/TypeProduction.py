from odoo import models, fields, api

class TypeProduction(models.Model):
    _name = "type.production"
    _inherits= {"stock.location": "stock_location_id"}
    _description = "Type de production"
    _order = "name"
    stock_location_id= fields.Many2one('stock.location', required=True, ondelete='cascade')

    
   
    code = fields.Char(
        string="Code",
        required=True,
        help="Généré automatiquement, modifiable si nécessaire",
    )

    def _generate_code_from_name(self, name):
        """Génère le code à partir du nom"""
        if not name:
            return ''
        words = name.strip().split()
        if len(words) > 1:
            return ''.join(w[0] for w in words if w).upper()
        else:
            clean = name.strip().upper()
            return clean[:2] if len(clean) >= 2 else clean

    @api.onchange('name')
    def _onchange_name_generate_code(self):
        """Génère le code si vide"""
        if self.name:
            self.code = self._generate_code_from_name(self.name)

    def action_generate_code(self):
        """Bouton : Régénère le code à partir du nom"""
        for record in self:
            record.code = record._generate_code_from_name(record.name)
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            type_production_id = vals.get('type_production_id')
            if not type_production_id:
                vals['complete_name'] = False
                continue
            type_production = self.env['type.production'].browse(type_production_id)
            if vals.get('date'):
                date = fields.Date.to_date(vals['date'])
                vals['complete_name'] = f"{type_production.code}/{date.strftime('%d/%m/%Y')}"
        return super().create(vals_list)
     