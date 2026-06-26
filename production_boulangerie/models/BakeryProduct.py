from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BakeryProduct(models.Model):
    _inherit = 'product.template'

    # ==================================================================
    # Champs personnalisés
    # ==================================================================
    bakery_product_type = fields.Selection(
        selection=[
            ('finished_product', 'Produit fini'),
            ('raw_material', 'Matière première'),
        ],
        string='Type (Boulangerie)',
        default=False,
        help="Catégorisation boulangerie : produit fini ou matière première.",
    )
    type_tarification = fields.Selection(
        [('caisse', 'Produit caisse'),
         ('livraison', 'Produit livraison')],
        string="Type de produit",
        default='caisse'
    )
    list_price = fields.Monetary(
        
        help="Prix de vente lorsque le client  souhaite  garder de ristourne.",
    )
    prix_en_gros = fields.Monetary(
        string='Prix de Gros',
        currency_field='currency_id',
        default=0.0,
        help="Prix de vente lorsque le client ne souhaite pas garder de ristourne.",
    )
    property_stock_production = fields.Many2one(
        string='Dépôt de Production')
   
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