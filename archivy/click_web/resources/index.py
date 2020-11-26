from collections import OrderedDict

import click
from flask import render_template

from archivy import click_web


def index():
    with click.Context(click_web.click_root_cmd,
                       info_name=click_web.click_root_cmd.name, parent=None) as ctx:
        return render_template('click_web/show_tree.html',
                               ctx=ctx, tree=_click_to_tree(ctx, click_web.click_root_cmd),
                               title="Plugins")


def _click_to_tree(ctx: click.Context, node: click.BaseCommand, ancestors=[]):
    '''
    Convert a click root command to a tree of dicts and lists
    :return: a json like tree
    '''
    res_childs = []
    res = OrderedDict()
    res['is_group'] = isinstance(node, click.core.MultiCommand)
    omitted = ["shell", "run", "routes", "create-admin"]
    if res['is_group']:
        # a group, recurse for e    very child
        subcommand_names = set(click.Group.list_commands(node, ctx))
        children = [node.get_command(ctx, key) for key in subcommand_names
                    if key not in omitted]
        # Sort so commands comes before groups
        children = sorted(children, key=lambda c: isinstance(c, click.core.MultiCommand))
        for child in children:
            res_childs.append(_click_to_tree(ctx, child, ancestors[:] + [node, ]))

    res['name'] = node.name

    # Do not include any preformatted block (\b) for the short help.
    res['short_help'] = node.get_short_help_str().split('\b')[0]
    res['help'] = node.help
    path_parts = ancestors + [node]
    res['path'] = '/' + '/'.join(p.name for p in path_parts)
    if res_childs:
        res['childs'] = res_childs
    return res
