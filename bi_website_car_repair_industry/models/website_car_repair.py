# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo import SUPERUSER_ID


class Website(models.Model):
    _inherit = 'website'

    def get_country_list(self):            
        country_ids=self.env['res.country'].search([])
        return country_ids
        
    def get_state_list(self):            
        state_ids=self.env['res.country.state'].search([])
        return state_ids
        
    def get_car_list(self):            
        car_ids=self.env['fleet.vehicle'].search([])
        return car_ids
    
    def get_model(self):            
        model_ids=self.env['fleet.vehicle.model'].search([])
        return model_ids
        
    def get_customer_list(self):            
        partners_ids=self.env['res.partner'].search([('customer','=','True')])
        return partners_ids
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
