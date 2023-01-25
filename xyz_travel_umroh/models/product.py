# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TravelPackage(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(copy=False, index=True)
    departure_date = fields.Date(string='Departure Date')
    return_date = fields.Date(string='Return Date')
    quota = fields.Integer('Quota')
    remaining_seats = fields.Integer(compute='_get_manifest_count', readonly=True)
    quota_progress = fields.Float(compute='_compute_quota_progress')
    jamaah_count = fields.Integer('Jamaah', compute='_compute_get_price_total')
    subtotal = fields.Monetary('Subtotal', compute='_compute_get_price_total')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_get_price_total')
    company_id = fields.Many2one('res.company', string='Company', default=1)
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", readonly=True)
    
    hotel_line = fields.One2many('hotel.lines', 'product_id', string='Hotel')
    airlines_line = fields.One2many('airline.lines', 'product_id', string='Airline')
    schedule_line = fields.One2many('schedule.lines', 'product_id', string='Schedule')
    manifest_line = fields.One2many('manifest.lines', 'product_id', readonly=True, string='Manifest')
    hpp_line = fields.One2many('hpp.lines', 'product_id', string='HPP')
    option_inv = fields.Boolean(default=False)
    gather_product = fields.Selection([
        ('airline', 'Airline'),
        ('hotel', 'Hotel'),
    ], string='Gather Product', default=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reschedule', 'Reschedule'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='draft', string='Status')

    @api.depends('quota', 'manifest_line')
    def _compute_quota_progress(self):
        for r in self:
            r.quota_progress = 0
            if len(r.manifest_line) <= r.quota and r.quota > 0:
                r.quota_progress = 100.0 * (len(r.manifest_line) / r.quota)

    @api.depends('manifest_line', 'quota')
    def _get_manifest_count(self):
        for r in self:
            r.remaining_seats = r.quota - len(r.manifest_line)

    # def create_default_product(self, name):
    #     cap_name = name[0].upper() + name[1:]
    #     product_id = self.sudo().create({
    #         'name': cap_name,
    #         'gather_product': name,
    #         'type': 'service',
    #         'invoice_policy': 'order',
    #         'company_id': self.company_id.id,
    #         'option_inv': False
    #     })
    #     return product_id

    def action_update_hpp(self):
        self.ensure_one()
        hpp_list = [(5, 0, 0)]
        if len(self.bom_ids.ids) > 0:
            for bom_id in self.bom_ids:
                for line in bom_id.bom_line_ids:
                    hpp_list.append((0, 0, {
                        'name': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_id.uom_id.id,
                        'price': line.product_id.standard_price,
                        'price_subtotal': line.product_id.standard_price * line.product_qty
                    }))

        if len(self.airlines_line.ids) > 0:
            name = 'airline'
            product_id = self.env['product.product'].search([('gather_product', '=', name)])
            if not product_id:
                raise UserError('System did not find product with %s in gather product field' %name)
            product_id = product_id[0]
            product_qty = 1
            price = 0
            for airline_id in self.airlines_line:
                price += airline_id.price

            hpp_list.append((0, 0, {
                'name': product_id.id,
                'product_qty': product_qty,
                'product_uom': product_id.uom_id.id,
                'price': price,
                'price_subtotal': price * product_qty
            }))

        if len(self.hotel_line.ids) > 0:
            name = 'hotel'
            product_id = self.env['product.product'].search([('gather_product', '=', name)])
            # if not product_id:
            #     product_id = self.create_default_product(name)
            if not product_id:
               raise UserError('System did not find product with %s in gather product field' %name)
            product_id = product_id[0]
            product_qty = 1
            price = 0
            for hotel_id in self.hotel_line:
                price += hotel_id.price

            hpp_list.append((0, 0, {
                'name': product_id.id,
                'product_qty': product_qty,
                'product_uom': product_id.uom_id.id,
                'price': price,
                'price_subtotal': price * product_qty
            }))

        self.hpp_line = hpp_list
        subtotal = sum(self.hpp_line.mapped('price_subtotal'))
        self.subtotal = subtotal
        self.standard_price = subtotal
    
    @api.model
    def create(self, vals):
        if vals.get('default_code',  _('/')) == _('/'):
            vals['default_code'] = self.env['ir.sequence'].next_by_code('product.template') or _('/')
        result = super(TravelPackage, self).create(vals)
        return result
    
    def action_confirm(self):
        return self.write({'state': 'confirm'})

    def action_done(self):
        return self.write({'state': 'done'})
    
    def action_update(self):
        for rec in self:
            for line in rec.env['sale.order.line'].search([('product_id', '=', rec.id)]):
                for manifest in line.order_id.manifest_line:
                    manifest.write({
                        'agent': line.order_id.user_id,
                        'product_id': rec.id
                    })
    
    def action_to_draft(self):
        return self.write({'state': 'draft'})
    
    @api.depends('subtotal', 'jamaah_count')
    def _compute_get_price_total(self):
        for rec in self:
            subtotal = 0
            for hpp in rec.hpp_line:
                subtotal += hpp.price_subtotal
            rec.subtotal = subtotal
            rec.standard_price = rec.subtotal
            rec.jamaah_count = len(rec.manifest_line.ids)
            rec.amount_total = rec.subtotal * rec.jamaah_count

    