# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

TYPE2FIELD = {
    'char': 'value_text',
    'float': 'value_float',
    'boolean': 'value_integer',
    'integer': 'value_integer',
    'text': 'value_text',
    'binary': 'value_binary',
    'date': 'value_datetime',
    'datetime': 'value_datetime',
}

TYPE2CLEAN = {
    'boolean': bool,
    'integer': lambda val: val or False,
    'float': lambda val: val or False,
    'char': lambda val: val or False,
    'text': lambda val: val or False,
    'binary': lambda val: val or False,
    'date': lambda val: val.date() if val else False,
    'datetime': lambda val: val or False,
}


class ModelAttribute(models.Model):
    _name = 'model.attribute.eat'
    _description = 'Model Attribute'

    name = fields.Char(index=True, required=True)
    res_id = fields.Char(string='Resource', index=True, required=True,
                         help="If not set, acts as a default value for new resources",)
    value_float = fields.Float()
    value_integer = fields.Integer()
    value_text = fields.Text()  # will contain (char, text)
    value_binary = fields.Binary(attachment=False)
    value_reference = fields.Char()
    value_datetime = fields.Datetime()
    type = fields.Selection([('char', 'Char'), ('float', 'Float'), ('boolean', 'Boolean'), ('integer', 'Integer'),
                             ('text', 'Text'), ('binary', 'Binary'), ('date', 'Date'), ('datetime', 'DateTime'), ],
                            required=True, default='many2one', index=True)

    def _update_values(self, values):
        if 'value' not in values:
            return values
        value = values.pop('value')
        type_ = values.get('type')
        if not type_:
            if self:
                type_ = self[0].type
            else:
                type_ = 'text'
        field = TYPE2FIELD.get(type_)
        if not field:
            raise UserError(_('Invalid type'))
        values[field] = value
        return values

    def write(self, values):
        return super(ModelAttribute, self).write(self._update_values(values))

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._update_values(vals) for vals in vals_list]
        r = super(ModelAttribute, self).create(vals_list)
        return r

    def get_by_record(self):
        self.ensure_one()
        if self.type in ('char', 'text', 'selection'):
            return self.value_text
        elif self.type == 'float':
            return self.value_float
        elif self.type == 'boolean':
            return bool(self.value_integer)
        elif self.type == 'integer':
            return self.value_integer
        elif self.type == 'binary':
            return self.value_binary
        elif self.type == 'datetime':
            return self.value_datetime
        elif self.type == 'date':
            if not self.value_datetime:
                return False
            return fields.Date.to_string(fields.Datetime.from_string(self.value_datetime))
        return False

    def get(self, names, model, data_id):
        values = self.get_attributes(names, model, data_id)
        return (values.get(name, False) for name in names)

    def _get_property(self, names, model, res_id):
        domains = [('res_id', '=', res_id)]
        if not names:
            pass
        elif isinstance(names, str):
            domains += ('name', '=', names)
        else:
            domains += ('name', 'in', names)
        return self.search(domains)

    def get_attributes(self, names, model, data_id):
        """
        :param names: like name or (name1, name2)
        :param model: target model attribute
        :param data_id: model data id
        :return: get attribute dict
        """
        res_id = '{},{}'.format(model, data_id)
        if isinstance(names, str):
            p = self._get_property(names, model, res_id)
            if p:
                return {names: p.get_by_record()}
            else:
                return False
        else:
            ps = self._get_property(names, model, res_id)
            values = {}
            for p in ps:
                values[p.name] = p.get_by_record()
        return values
