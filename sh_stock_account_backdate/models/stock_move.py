from odoo import api, fields, models, _
from datetime import date,datetime

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        date = self._context.get('force_period_date', fields.Date.context_today(self))
        return {
            'journal_id': journal_id,
            'line_ids': move_lines,
            'date': self.date if self.date.date() <= date.today() else date.today(),
            'ref': description,
            'stock_move_id': self.id,
            'stock_valuation_layer_ids': [(6, None, [svl_id])],
            'move_type': 'entry',
        }

class ScrapBackdateWizardInherit(models.TransientModel):
    _inherit = 'sh.scrap.backdate.wizard'

    def assign_backdate(self):

        super(ScrapBackdateWizardInherit,self).assign_backdate()

        if self.company_id.backdate_for_scrap:

            for stock_scrap in self.scrap_ids:

                stock_moves = self.env['stock.move'].search(['|',('scrap_id','=',stock_scrap.id),('origin','=',stock_scrap.name)])

                account_moves = self.env['account.move'].search([('stock_move_id','in',stock_moves.ids)])
                valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id','in',stock_moves.ids)])
                    
                for account_move in account_moves:
                    account_move.button_draft()
                    account_move.name = False
                    account_move.date = self.date_done
                    account_move.action_post()

                for layer in valuation_layers:
                    self.env.cr.execute("""
                        Update stock_valuation_layer set create_date='%s' where id=%s; 
                    """ %(self.date_done, layer.id))


class PickngBackdateWizardInherit(models.TransientModel):
    _inherit = 'sh.picking.backdate.wizard'

    def assign_backdate(self):
        
        super(PickngBackdateWizardInherit,self).assign_backdate()

        if self.company_id.backdate_for_picking:

            for stock_picking in self.stock_picking_ids:
                
                stock_moves = self.env['stock.move'].search([('picking_id','=',stock_picking.id)])
                account_moves = self.env['account.move'].search([('stock_move_id','in',stock_moves.ids)])
                valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id','in',stock_moves.ids)])
                    
                for account_move in account_moves:
                    account_move.button_draft()
                    account_move.name = False
                    account_move.date = self.scheduled_date
                    account_move.action_post()
                
                for layer in valuation_layers:
                    self.env.cr.execute("""
                        Update stock_valuation_layer set create_date='%s' where id=%s; 
                    """ %(self.scheduled_date, layer.id))