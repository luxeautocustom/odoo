from lxml import etree

from odoo import tools


global tools
# Which attributes must be translated. This is a dict, where the value indicates
# a condition for a node to have the attribute translatable.
def _check_a_tag(node):
    if node.tag == 'a':
        node.set('href-origin', node.attrib.get('href', ''))
        return True
    return False


tools.TRANSLATED_ATTRS.update({
    'src': lambda node: node.tag in ('img', 'video', 'iframe'),
    'href': lambda node: _check_a_tag(node),
})


_locate_node = tools.template_inheritance.locate_node


def _locate_node_plus(arch, spec):
    node = _locate_node(arch, spec)

    if spec.tag == 'xpath' and node is None:
        expr = spec.get('expr')
        if '@href=' in expr:
            xPath = etree.ETXPath(expr.replace('@href=', '@href-origin='))
            nodes = xPath(arch)
            return nodes[0] if nodes else None
    return node


tools.template_inheritance.locate_node = _locate_node_plus


def post_init_hook(cr, registry):
    tools.template_inheritance.locate_node = _locate_node_plus
    tools.TRANSLATED_ATTRS.update({
        'src': lambda node: node.tag in ('img', 'video', 'iframe'),
        'href': lambda node: _check_a_tag(node),
    })


def uninstall_hook(cr, registry):
    tools.template_inheritance.locate_node = _locate_node
    if 'src':
        del tools.TRANSLATED_ATTRS['src']
    if 'href':
        del tools.TRANSLATED_ATTRS['href']
