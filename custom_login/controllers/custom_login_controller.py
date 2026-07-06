# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class CustomLoginController(http.Controller):

    def _get_databases(self):
        try:
            return http.db_list()
        except Exception as e:
            _logger.warning(
                "Impossible de lister les bases : %s",
                e
            )
            return []


    def _get_current_db(self):

        if request.db:
            return request.db

        try:
            db = http.db_monodb()
            if db:
                return db

        except Exception as e:
            _logger.warning(
                "db_monodb a échoué : %s",
                e
            )

        databases = self._get_databases()

        return databases[0] if databases else None



    def _default_redirect(self):
        return '/web'



    def _render_login_page(self, values):

        return request.render(
            'custom_login.custom_login_page',
            values
        )



    @http.route(
        '/web/login',
        type='http',
        auth='none',
        methods=['GET', 'POST'],
        csrf=True,
        sitemap=False,
        website=False,
    )
    def custom_login(self, redirect=None, **kw):

        databases = self._get_databases()
        current_db = self._get_current_db()


        values = {
            'databases': databases,
            'current_db': current_db,
            'redirect': redirect or self._default_redirect(),
            'login': kw.get('login', ''),
            'error': None,
        }



        # Déjà connecté
        if request.session.uid:
            return request.redirect(
                values['redirect']
            )



        if request.httprequest.method == 'POST':

            login = kw.get('login')
            password = kw.get('password')


            if not login or not password:

                values['error'] = (
                    "Veuillez renseigner l'identifiant "
                    "et le mot de passe."
                )

                values['login'] = login or ''

                return self._render_login_page(values)



            credential = {
                'login': login,
                'password': password,
                'type': 'password',
            }



            _logger.info(
                "Tentative d'authentification : login=%s db=%s",
                login,
                request.db
            )



            try:

                # Même logique que Odoo 19 natif
                if request.env.uid is None:

                    request.env[
                        "ir.http"
                    ]._auth_method_public()



                auth_info = request.session.authenticate(
                    request.env,
                    credential
                )



                _logger.info(
                    "Connexion réussie : login=%s uid=%s",
                    login,
                    auth_info.get('uid')
                )


                return request.redirect(
                    values['redirect']
                )



            except AccessDenied as e:

                _logger.warning(
                    "Connexion refusée pour %s : %s",
                    login,
                    e
                )


                values['error'] = (
                    "Identifiant ou mot de passe incorrect."
                )

                values['login'] = login


                return self._render_login_page(values)



            except Exception as e:

                _logger.exception(
                    "Erreur authentification personnalisée : %s",
                    e
                )


                values['error'] = (
                    "Une erreur est survenue "
                    "lors de la connexion."
                )

                values['login'] = login


                return self._render_login_page(values)



        return self._render_login_page(values)




    @http.route(
        '/web/custom_logout',
        type='http',
        auth='none',
        sitemap=False
    )
    def custom_logout(
        self,
        redirect='/web/login'
    ):

        request.session.logout(
            keep_db=True
        )

        return request.redirect(
            redirect
        )