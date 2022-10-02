# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup

from odoo import api, models, _
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.addons.website.models.website import SEARCH_TYPE_MODELS
from odoo.osv.expression import AND, OR

SEARCH_TYPE_MODELS['blogs'] |= 'blog.blog', 'blog.post'
SEARCH_TYPE_MODELS['blogs_only'] |= 'blog.blog',
SEARCH_TYPE_MODELS['blog_posts_only'] |= 'blog.post',


class Website(models.Model):
    _inherit = "website"

    @api.model
    def search_url_dependencies(self, res_ids, res_model):
        dep = super().search_url_dependencies(res_ids, res_model)

        domain = []
        for record in self.env[res_model].browse([int(res_id) for res_id in res_ids]):
            url = getattr(record, 'website_url', False) or record.url
            domain.append(AND([[('content', 'ilike', url)]]))

        posts = self.env['blog.post'].search(OR(domain))
        if posts:
            page_key = _('Blog Post') if len(posts) == 1 else _('Blog Posts')
            dep[page_key] = [{
                'content': Markup(_('Blog Post <b>%s</b> seems to have a link to this page !', post.name)),
                'item': post.name,
                'link': post.website_url,
            } for post in posts]

        return dep

    def get_suggested_controllers(self):
        suggested_controllers = super(Website, self).get_suggested_controllers()
        suggested_controllers.append((_('Blog'), url_for('/blog'), 'website_blog'))
        return suggested_controllers

    def configurator_set_menu_links(self, menu_company, module_data):
        blogs = module_data.get('#blog', [])
        for idx, blog in enumerate(blogs):
            new_blog = self.env['blog.blog'].create({
                'name': blog['name'],
                'website_id': self.id,
            })
            blog_menu_values = {
                'name': blog['name'],
                'url': '/blog/%s' % new_blog.id,
                'sequence': blog['sequence'],
                'parent_id': menu_company.id if menu_company else self.menu_id.id,
                'website_id': self.id,
            }
            if idx == 0:
                blog_menu = self.env['website.menu'].search([('url', '=', '/blog'), ('website_id', '=', self.id)])
                blog_menu.write(blog_menu_values)
            else:
                self.env['website.menu'].create(blog_menu_values)
        super().configurator_set_menu_links(menu_company, module_data)
