# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from datetime import datetime, date


class WebsiteCarRepair(http.Controller):

	@http.route(['/car-repair'], type='http', auth="public", website=True)
	def car_repair(self, **post):
		
		return request.render("bi_website_car_repair_industry.bi_portal_car_repair")
	
	@http.route(['/car-repair/thankyou'], type='http', auth="public", website=True)
	def car_thankyou(self, **post):
		if post.get('debug'):
			return request.render("bi_website_car_repair_industry.repair_thankyou")        
		if post.get('fw'):
			return request.render("bi_website_car_repair_industry.repair_thankyou")        

		car_repair_obj = request.env['fleet.repair']
		car_repair_line_obj = request.env['fleet.repair.line']

		gr_y = []
		gr_pay = []
		if post.get('under_guarantee') == 'yes':
			gr_y = 'yes'
		else:
			gr_y = 'no'
			
		if post.get('type') == 'free':
			gr_pay = 'free'
		else:
			gr_pay = 'paid'

		if post.get('name') == '':
			return request.redirect("/car-repair?name=1")

		if post.get('mobile') == '':
			return request.redirect("/car-repair?mobile=1")

		if post.get('email') == '':
			return request.redirect("/car-repair?email=1")

		if post.get('subject') == '':
			return request.redirect("/car-repair?subject=1")

		if post.get('car') == '':
			return request.redirect("/car-repair?car=1")

		client_obj = False	
		if post.get("id"):
			client_obj = request.env['res.partner'].sudo().search([('id','=', post.get("id",False))])

		if not client_obj:
			client_obj = request.env['res.partner'].sudo().create({
				'name': post.get("name"),
				'company_name':  post.get("company_name"),
				'street':  post.get("street") ,
				'street2':  post.get("street2"),
				'city':  post.get("city"),
				'phone':  post.get("phone"),
				'mobile':  post.get("mobile"),
				'state_id': int(post.get("state_id")) if post.get("state_id") else False,
				'country_id': int(post.get("country_id")) if post.get("country_id") else False,
				'email':  post.get("email"),
			})
				
		repair_id = car_repair_obj.sudo().create({
			'client_id': client_obj.id,
			'name': post.get("subject"),
		})
		
		car_repair_line_obj.sudo().create({
			'fleet_id':  post.get("car"),
			'fleet_repair_id': repair_id.id,
			'model_id':  post.get("model"),
			'guarantee': gr_y,
			'guarantee_type': gr_pay
		
		})

		return request.render("bi_website_car_repair_industry.repair_thankyou")
				
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
