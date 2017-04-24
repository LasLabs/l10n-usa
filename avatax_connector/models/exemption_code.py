from odoo import api, fields, models


class ExemptionCode(models.Model):
    _name = 'exemption.code'
    _description = 'Exemption Code'

    name = fields.Char()
    code = fields.Char()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        return [(r.id, ('(' + r.code + ')' + ' ' + r.name)) for r in self]
