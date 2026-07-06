# from odoo import models, fields, api


# class custom_login(models.Model):
#     _name = 'custom_login.custom_login'
#     _description = 'custom_login.custom_login'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

