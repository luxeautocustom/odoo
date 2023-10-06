# -*- coding: utf-8 -*-

from odoo import models, fields


class CustomProject(models.Model):
    _inherit = 'project.task'

    check_box = fields.Boolean(string='Is Check List', default=False)
    info_checklist = fields.One2many(comodel_name="check.list", inverse_name="task_id", string="Checklist")
    progress_rate = fields.Integer(string='Checklist Progress', compute="check_rate")
    total = fields.Integer(string="Max")
    status = fields.Selection(string="Status", selection=[('done', 'Done'), ('progress', 'In Progress'), ('cancel', 'Cancel')], readonly=True)
    maximum_rate = fields.Integer(default=100)

    def check_rate(self):
        for rec in self:
            total = len(rec.info_checklist.ids)
            done = 0
            cancel = 0
            progress_rate = 0
            if total > 0:
                if rec.info_checklist:
                    for item in rec.info_checklist:
                        if item.status == 'done':
                            done += 1
                        if item.status == 'cancel':
                            cancel += 1
                    if cancel == total:
                        progress_rate = 0
                    else:
                        progress_rate = round(done / (total - cancel), 2) * 100
            rec.sudo().progress_rate = progress_rate
