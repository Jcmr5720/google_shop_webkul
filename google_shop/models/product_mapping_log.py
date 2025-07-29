from odoo import models, fields

class ProductMappingLog(models.Model):
    _name = 'product.mapping.log'
    _description = 'Log for product mapping actions'

    mapping_id = fields.Many2one('product.mapping', required=True, ondelete='cascade')
    message = fields.Char(required=True)
    operation = fields.Selection([
        ('export', 'Export'),
        ('update', 'Update'),
        ('image', 'Image')
    ], string='Operation')
    date = fields.Datetime(default=fields.Datetime.now)
