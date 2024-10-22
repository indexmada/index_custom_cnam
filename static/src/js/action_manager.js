odoo.define('index_custom_cnam.action_manager', function (require) {
    "use strict";
    /**
     * The purpose of this file is to add the actions of type
     * 'ir_actions_xlsx_download' to the ActionManager.
     */
    var ActionManager = require('web.ActionManager');
    var framework = require('web.framework');
    var session = require('web.session');

    ActionManager.include({
        _executexlsxReportDownloadAction: function (action) {
            // Bloquer l'interface utilisateur pendant le téléchargement
            framework.blockUI();
            var def = $.Deferred();

            session.get_file({
                url: '/xlsx_reports',
                data: action.data,  // Les données nécessaires pour générer le rapport
                success: def.resolve.bind(def),  // Résolution si succès
                error: (error) => this.call('crash_manager', 'rpc_error', error),  // Gestion des erreurs
                complete: framework.unblockUI,  // Débloquer l'interface une fois terminé
            });

            return def;
        },

        _handleAction: function (action, options) {
            // Vérifier si l'action est définie et si elle a un type
            if (!action || !action.type) {
                console.error("Action ou type non défini", action);  // Log pour déboguer l'erreur
                return $.Deferred().reject();  // Rejetter l'action si elle est mal définie
            }

            // Vérifier si l'action est du type 'ir_actions_xlsx_download'
            if (action.type === 'ir_actions_xlsx_download') {
                return this._executexlsxReportDownloadAction(action, options);
            }

            // Appel à la méthode parente pour les autres types d'action
            return this._super.apply(this, arguments);
        },
    });
});
