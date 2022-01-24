# -*- coding:utf-8 -*-
# Copyright 2020/12/8 BWP
# Created by yao <mryao.com@gmail.com> at '2020/12/8-6:32 下午'

from odoo import fields, models, api
import operator
import itertools


class IrTranslation(models.Model):
    _inherit = "ir.translation"
    _description = 'Translation'
    _log_access = False

    @api.model
    def get_translations_for_webclient(self, mods, lang):
        if not mods:
            mods = [x['name'] for x in self.env['ir.module.module'].sudo().search_read(
                [('state', '=', 'installed')], ['name'])]
        if not lang:
            lang = self._context["lang"]
        langs = self.env['res.lang']._lang_get(lang)
        lang_params = None
        if langs:
            lang_params = {
                "name": langs.name,
                "direction": langs.direction,
                "date_format": langs.date_format,
                "time_format": langs.time_format,
                "grouping": langs.grouping,
                "decimal_point": langs.decimal_point,
                "thousands_sep": langs.thousands_sep,
                "week_start": langs.week_start,
                "month_format": langs.month_format,
                "year_format": langs.year_format,
            }
            lang_params['week_start'] = int(lang_params['week_start'])
            lang_params['code'] = lang

        translations_per_module = {}
        messages = self.env['ir.translation'].sudo().search_read([
            ('module', 'in', mods), ('lang', '=', lang),
            ('comments', 'like', 'openerp-web'), ('value', '!=', False),
            ('value', '!=', '')],
            ['module', 'src', 'value', 'lang'], order='module')
        for mod, msg_group in itertools.groupby(messages, key=operator.itemgetter('module')):
            translations_per_module.setdefault(mod, {'messages': []})
            translations_per_module[mod]['messages'].extend({
                                                                'id': m['src'],
                                                                'string': m['value']}
                                                            for m in msg_group)

        return translations_per_module, lang_params
