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
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    },
    _handleAction: function (action, options) {
        if (action.type === 'ir_actions_xlsx_download') {
            return this._executexlsxReportDownloadAction(action, options);
        }
        return this._super.apply(this, arguments);
    	},
    });
  });odoo.define('module_name.your_class', function (require) {
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
