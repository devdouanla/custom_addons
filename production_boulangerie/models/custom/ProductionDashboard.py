from odoo import fields, models, tools
class ProductionDashboard(models.Model):
    """Tableau de bord destine au directeur : une ligne par journee de
    production, avec les indicateurs cles agreges (valeur produite,
    cout matieres, profit, taux de profit, nombre de fiches par etat).

    Modele base sur une vue SQL (_auto = False) : lecture seule, jamais
    de create/write/unlink directs. Les donnees viennent des champs deja
    calcules et stockes sur production.production (production_value,
    consumption_cost, profit, profit_rate), donc pas de recalcul ici.
    """
    _name = 'production.dashboard'
    _description = 'Tableau de Bord Production'
    _auto = False
    _order = 'date desc'

    date = fields.Date(string='Date', readonly=True)
    reference = fields.Char(string='Journee', readonly=True)
    type_production_id = fields.Many2one(
        comodel_name='type.production',
        string='Type de production',
        readonly=True,
    )
    nb_productions = fields.Integer(string='Nb fiches', readonly=True)
    nb_validees = fields.Integer(string='Validees', readonly=True)
    nb_brouillon = fields.Integer(string='Brouillon', readonly=True)
    nb_annulees = fields.Integer(string='Annulees', readonly=True)
    production_value = fields.Float(string='Valeur production', readonly=True)
    consumption_cost = fields.Float(string='Cout matieres', readonly=True)
    profit = fields.Float(string='Profit', readonly=True)
    profit_rate = fields.Float(string='Taux de profit (%)', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    pd.id AS id,
                    pd.date AS date,
                    pd.reference AS reference,
                    pd.type_production_id AS type_production_id,
                    COUNT(pp.id) AS nb_productions,
                    COUNT(pp.id) FILTER (WHERE pp.state = 'done') AS nb_validees,
                    COUNT(pp.id) FILTER (WHERE pp.state = 'draft') AS nb_brouillon,
                    COUNT(pp.id) FILTER (WHERE pp.state = 'cancelled') AS nb_annulees,
                    COALESCE(SUM(pp.production_value), 0) AS production_value,
                    COALESCE(SUM(pp.consumption_cost), 0) AS consumption_cost,
                    COALESCE(SUM(pp.profit), 0) AS profit,
                    CASE WHEN SUM(pp.consumption_cost) > 0
                         THEN (SUM(pp.profit) / SUM(pp.consumption_cost)) * 100.0
                         ELSE 0
                    END AS profit_rate,
                    (SELECT rc.currency_id FROM res_company rc ORDER BY rc.id LIMIT 1) AS currency_id
                FROM production_day pd
                LEFT JOIN production_production pp ON pp.production_day_id = pd.id
                GROUP BY pd.id, pd.date, pd.reference, pd.type_production_id
            )
        """ % self._table)
