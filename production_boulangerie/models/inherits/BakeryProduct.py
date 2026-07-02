from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BakeryProduct(models.Model):
    _name = 'bakery.product'
    _inherits= {"product.template": "product_template_id"}
    _description = 'Produit Boulangerie'

    product_template_id = fields.Many2one('product.template', required=True, ondelete='cascade')
    # ==================================================================
    # Champs personnalisés
    # ==================================================================
    
    type_tarification = fields.Selection(
        [('caisse', 'Produit caisse'),
         ('livraison', 'Produit livraison')],
        string="Type de produit",
        default='caisse'
    )
  
    prix_en_gros = fields.Monetary(
        string='Prix de Gros',
        currency_field='currency_id',
        default=0.0,
        help="Prix de vente lorsque le client ne souhaite pas garder de ristourne.",
    )
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['is_storable'] = True
        return super().create(vals_list)
   
    @api.constrains('prix_en_gros', 'list_price')
    def _check_prices(self):
        """Vérifie que les prix ne sont pas négatifs."""
        for rec in self:
            if rec.prix_en_gros < 0:
                raise ValidationError(
                    "Le prix de gros ne peut pas être négatif."
                )
            if rec.list_price < 0:
                raise ValidationError(
                    "Le prix de détail ne peut pas être négatif."
                )

    @api.constrains('prix_en_gros', 'list_price')
    def _check_prix_gros_vs_detail(self):
        """Le prix de gros doit être inférieur ou égal au prix de détail."""
        for rec in self:
            if rec.prix_en_gros and rec.list_price:
                if rec.prix_en_gros > rec.list_price:
                    raise ValidationError(
                        "Le prix de gros (%.2f) ne peut pas être supérieur "
                        "au prix de détail (%.2f)." % (
                            rec.prix_en_gros, rec.list_price
                        )
                    )