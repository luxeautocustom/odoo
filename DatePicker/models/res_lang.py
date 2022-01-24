# -*- coding:utf-8 -*-
# Copyright 2020/12/8 BWP
# Created by yao <mryao.com@gmail.com> at '2020/12/8-6:32 下午'

from odoo import fields, models

DEFAULT_YEAR_FORMAT = '%Y'
DEFAULT_MONTH_FORMAT = '%m/%Y'

class Lang(models.Model):
    _inherit = "res.lang"

    year_format = fields.Char(string='Year Format', required=True, default=DEFAULT_YEAR_FORMAT)
    month_format = fields.Char(string='Month Format', required=True, default=DEFAULT_MONTH_FORMAT)
