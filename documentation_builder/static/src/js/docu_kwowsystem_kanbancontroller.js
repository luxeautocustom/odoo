/** @odoo-module **/

import KnowSystemKanbanController from "@knowsystem/js/kwowsystem_kanbancontroller";
import dialogs from "web.view_dialogs";
import { _lt } from "web.core"

KnowSystemKanbanController.include({
    events: _.extend({}, KnowSystemKanbanController.prototype.events, {
        "click .documentation_articles_add": "_onAddToDocumentation",
    }),
    /**
    * param {MouseEvent} event
    * The method to add articles to documentation
    */
    async _onAddToDocumentation(event) {
        event.stopPropagation();
        var self = this;
        var view_id = await this._rpc({
            model: "documentation.section",
            method: "return_add_to_documentation_wizard",
            args: [this.selectedRecords],
            context: {},
        });
        var onSaved = function(record) {
            var docuID = record.data.section_id.res_id;
            self._rpc({
                model: "documentation.section",
                method: "return_form_view",
                args: [[docuID]]}).then(function (action) {
                    self.do_action(action);
                });
        };
        new dialogs.FormViewDialog(self, {
            res_model: "add.to.documentation",
            context: {"default_articles": self.selectedRecords.join()},
            title: _lt("Add to Documentation"),
            view_id: view_id,
            readonly: false,
            shouldSaveLocally: false,
            on_saved: onSaved,
        }).open();
    },
});

