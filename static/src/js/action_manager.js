odoo.define('module_name.your_class', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var YourClass = AbstractAction.extend({
        _handleAction: function (action, options) {
            // Vérification de l'action avant d'accéder à ses propriétés
            if (action && action.type === 'ir_actions_xlsx_download') {
                return this._executexlsxReportDownloadAction(action, options);
            }
            return this._super.apply(this, arguments);
        },

        _executexlsxReportDownloadAction: function (action, options) {
            // Logique pour exécuter l'action de téléchargement XLSX
            // Ajoutez ici votre code pour gérer le téléchargement
            console.log('Téléchargement en cours pour l\'action:', action);
            // Ajoutez ici la logique de téléchargement
        },
    });

    core.action_registry.add('module_name.your_class', YourClass);
});
