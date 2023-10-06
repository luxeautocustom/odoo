# -*- coding: utf-8 -*-

from odoo import models, fields


class CheckList(models.Model):
    _name = 'check.list'

    task_id = fields.Many2one('project.task', string='Task')
    name = fields.Char('Name')
    name_work = fields.Text('Name Work', track_visibility='onchange')
    description = fields.Text('Description')
    status = fields.Selection(string="Status", selection=[('done', 'Done'), ('progress', 'In Progress'), ('cancel', 'Cancel')], readonly=True, track_visibility='onchange')

    def do_accept(self):
        for rec in self:
            rec.write({
                'status': 'done',
            })

    def do_cancel(self):
        for rec in self:
            rec.write({
                'status': 'cancel',
            })

    def do_progress(self):
        for rec in self:
            rec.write({
                'status': 'progress',
            })

    def do_set_to(self):
        for rec in self:
            rec.write({
                'status': ''
            })
