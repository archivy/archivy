import pprint
from collections import OrderedDict
from pathlib import Path

import click
import pytest

from archivy import click_web, cli
from archivy.click_web.resources import cmd_form, input_fields
from archivy.click_web.resources.cmd_exec import RequestToCommandArgs


@pytest.mark.parametrize(
    'param, command_index, expected',
    [
        (click.Argument(["an_argument", ]), 0,
         {'checked': '',
          'click_type': 'text',
          'help': '',
          'human_readable_name': 'AN ARGUMENT',
          'name': '0.0.argument.text.1.text.an-argument',
          'nargs': 1,
          'param': 'argument',
          'required': True,
          'type': 'text',
          'value': None}),
        (click.Argument(["an_argument", ], nargs=2), 1,
         {'checked': '',
          'click_type': 'text',
          'help': '',
          'human_readable_name': 'AN ARGUMENT',
          'name': '1.0.argument.text.2.text.an-argument',
          'nargs': 2,
          'param': 'argument',
          'required': True,
          'type': 'text',
          'value': None}),
        (click.Option(["--an_option", ]), 0,
         {'checked': '',
          'click_type': 'text',
          'desc': None,
          'help': ('--an_option TEXT', ''),
          'human_readable_name': 'an option',
          'name': '0.0.option.text.1.text.--an-option',
          'nargs': 1,
          'param': 'option',
          'required': False,
          'type': 'text',
          'value': ''}),
        (click.Option(["--an_option", ], nargs=2), 1,
         {'checked': '',
          'click_type': 'text',
          'desc': None,
          'help': ('--an_option TEXT...', ''),
          'human_readable_name': 'an option',
          'name': '1.0.option.text.2.text.--an-option',
          'nargs': 2,
          'param': 'option',
          'required': False,
          'type': 'text',
          'value': ''}),
        (click.Option(["--flag/--no-flag", ], default=True, help='help'), 3,
         {'checked': 'checked="checked"',
          'click_type': 'bool_flag',
          'desc': 'help',
          'help': ('--flag / --no-flag', 'help'),
          'human_readable_name': 'flag',
          'name': '3.0.flag.bool_flag.1.checkbox.--flag',
          'nargs': 1,
          'off_flag': '--no-flag',
          'on_flag': '--flag',
          'param': 'option',
          'required': False,
          'type': 'checkbox',
          'value': '--flag'}),
    ])
def test_get_input_field(ctx, click_cli, param, expected, command_index):
    res = input_fields.get_input_field(ctx, param, command_index, 0)
    pprint.pprint(res)
    assert res == expected


@pytest.mark.parametrize(
    'param, command_index, expected',
    [
        (click.Argument(["an_argument", ], nargs=-1), 0,
         {'checked': '',
          'click_type': 'text',
          'help': '',
          'human_readable_name': 'AN ARGUMENT',
          'name': '0.0.argument.text.-1.text.an-argument',
          'nargs': -1,
          'param': 'argument',
          'required': False,
          'type': 'text',
          'value': None}),
    ])
def test_variadic_arguments(ctx, click_cli, param, expected, command_index):
    res = input_fields.get_input_field(ctx, param, command_index, 0)
    pprint.pprint(res)
    assert res == expected


@pytest.mark.parametrize(
    'param, command_index, expected',
    [
        (click.Argument(["a_file_argument", ], type=click.File('rb')), 0,
         {'checked': '',
          'click_type': 'file[rb]',
          'help': '',
          'human_readable_name': 'A FILE ARGUMENT',
          'name': '0.0.argument.file[rb].1.file.a-file-argument',
          'nargs': 1,
          'param': 'argument',
          'required': True,
          'type': 'file',
          'value': None}),
        (click.Option(["--a_file_option", ], type=click.File('rb')), 0,
         {'checked': '',
          'click_type': 'file[rb]',
          'desc': None,
          'help': ('--a_file_option FILENAME', ''),
          'human_readable_name': 'a file option',
          'name': '0.0.option.file[rb].1.file.--a-file-option',
          'nargs': 1,
          'param': 'option',
          'required': False,
          'type': 'file',
          'value': ''}),
    ])
def test_get_file_input_field(ctx, click_cli, param, expected, command_index):
    res = input_fields.get_input_field(ctx, param, command_index, 0)
    pprint.pprint(res)
    assert res == expected


@pytest.mark.parametrize(
    'param, command_index, expected',
    [
        (click.Argument(["a_file_argument", ], type=click.File('wb')), 0,
         {'checked': '',
          'click_type': 'file[wb]',
          'help': '',
          'human_readable_name': 'A FILE ARGUMENT',
          'name': '0.0.argument.file[wb].1.hidden.a-file-argument',
          'nargs': 1,
          'param': 'argument',
          'required': True,
          'type': 'hidden',
          'value': None}),
        (click.Option(["--a_file_option", ], type=click.File('wb')), 0,
         {'checked': '',
          'click_type': 'file[wb]',
          'desc': None,
          'help': ('--a_file_option FILENAME', ''),
          'human_readable_name': 'a file option',
          'name': '0.0.option.file[wb].1.text.--a-file-option',
          'nargs': 1,
          'param': 'option',
          'required': False,
          'type': 'text',
          'value': ''}),
    ])
def test_get_output_file_input_field(ctx, click_cli, param, expected, command_index):
    res = input_fields.get_input_field(ctx, param, command_index, 0)
    pprint.pprint(res)
    assert res == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        ({
             '0.0.option.text.1.text.--an-option': 'option-value',
             '0.1.option.text.1.text.--another-option': 'another-option-value',
             '1.0.option.text.1.text.--option-for-other-command': 'some value'
         }, (['--an-option', 'option-value', '--another-option', 'another-option-value'],
             ['--option-for-other-command', 'some value']),
        ), # noqa
        (OrderedDict((
                ('0.1.option.text.1.text.--another-option', 'another-option-value'),
                ('0.0.option.text.1.text.--an-option', 'option-value'),
                ('1.0.option.text.1.text.--option-for-other-command', 'some value')
        )), (['--an-option', 'option-value', '--another-option', 'another-option-value'],
             ['--option-for-other-command', 'some value']),
        ),
    ])
def test_form_post_to_commandline_arguments(data, expected, test_app):
    with test_app.test_request_context(f'/command', data=data):
        r = RequestToCommandArgs()
        for i, expect in enumerate(expected):
            assert r.command_args(i) == expected[i]
