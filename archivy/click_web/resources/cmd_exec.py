import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import List

from flask import Response, request
from werkzeug.utils import secure_filename

from archivy import click_web

from .input_fields import FieldId

logger = None


def exec(command_path):
    """
    Execute the command and stream the output from it as response
    :param command_path:
    """
    command_path = "cli/" + command_path
    global logger
    logger = click_web.logger

    omitted = ["shell", "run", "routes"]
    root_command, *commands = command_path.split('/')
    cmd = ["archivy"]
    req_to_args = RequestToCommandArgs()
    # root command_index should not add a command
    cmd.extend(req_to_args.command_args(0))
    for i, command in enumerate(commands):
        if command in omitted:
            return Response(status=400)
        cmd.append(command)
        cmd.extend(req_to_args.command_args(i + 1))

    def _generate_output():
        yield _create_cmd_header(commands)
        try:
            yield from _run_script_and_generate_stream(req_to_args, cmd)
        except Exception as e:
            # exited prematurely, show the error to user
            yield f"\nERROR: Got exception when reading output from script: {type(e)}\n"
            yield traceback.format_exc()
            raise

    return Response(_generate_output(),
                    mimetype='text/plain')


def _run_script_and_generate_stream(req_to_args: 'RequestToCommandArgs', cmd: List[str]):
    """
    Execute the command the via Popen and yield output
    """
    logger.info('Executing: %s', cmd)
    if not os.environ.get('PYTHONIOENCODING'):
        # Fix unicode on windows
        os.environ['PYTHONIOENCODING'] = 'UTF-8'

    process = subprocess.Popen(cmd,
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    logger.info('script running Pid: %d', process.pid)

    encoding = sys.getdefaultencoding()
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            yield line.decode(encoding)

    process.wait()  # wait for the subprocess to exit
    logger.info('script finished Pid: %d', process.pid)
    for fi in req_to_args.field_infos:
        fi.after_script_executed()


def _create_cmd_header(commands: List[str]):
    """
    Generate a command header.
    Note:
        here we always allow to generate HTML as long as we have it between CLICK-WEB comments.
        This way the JS frontend can insert it in the correct place in the DOM.
    """

    def generate():
        yield '<!-- CLICK_WEB START HEADER -->'
        yield '<div class="command-line">Executing: {}</div>'.format('/'.join(commands))
        yield '<!-- CLICK_WEB END HEADER -->'

    # important yield this block as one string so it pushed to client in one go.
    # so the whole block can be treated as html.
    html_str = '\n'.join(generate())
    return html_str


def _create_result_footer(req_to_args: 'RequestToCommandArgs'):
    """
    Generate a footer.
    Note:
        here we always allow to generate HTML as long as we have it between CLICK-WEB comments.
        This way the JS frontend can insert it in the correct place in the DOM.
    """
    to_download = [fi for fi in req_to_args.field_infos
                   if fi.generate_download_link and fi.link_name]
    # important yield this block as one string so it pushed to client in one go.
    # This is so the whole block can be treated as html if JS frontend.
    lines = []
    lines.append('<!-- CLICK_WEB START FOOTER -->')
    if to_download:
        lines.append('<b>Result files:</b><br>')
        for fi in to_download:
            lines.append('<ul> ')
            lines.append(f'<li>{_get_download_link(fi)}<br>')
            lines.append('</ul>')

    else:
        lines.append('<b>DONE</b>')
    lines.append('<!-- CLICK_WEB END FOOTER -->')
    html_str = '\n'.join(lines)
    yield html_str


def _get_download_link(field_info):
    """Hack as url_for need request context"""

    rel_file_path = Path(field_info.file_path).relative_to(click_web.OUTPUT_FOLDER)
    uri = f'/static/results/{rel_file_path.as_posix()}'
    return f'<a href="{uri}">{field_info.link_name}</a>'


class RequestToCommandArgs:

    def __init__(self):
        field_infos = [FieldInfo.factory(key) for key in
                       list(request.form.keys()) + list(request.files.keys())]
        # important to sort them so they will be in expected order on command line
        self.field_infos = list(sorted(field_infos))

    def command_args(self, command_index) -> List[str]:
        """
        Convert the post request into a list of command line arguments

        :param command_index: (int) the index for the command to get arguments for.
        :return: list of command line arguments for command at that cmd_index
        """
        args = []

        # only include relevant fields for this command index
        commands_field_infos = [fi for fi in self.field_infos
                                if fi.param.command_index == command_index]
        commands_field_infos = sorted(commands_field_infos)

        for fi in commands_field_infos:

            # must be called mostly for saving and preparing file output.
            fi.before_script_execute()

            if fi.cmd_opt.startswith('--'):
                # it's an option
                args.extend(self._process_option(fi))

            else:
                # argument(s)
                if isinstance(fi, FieldFileInfo):
                    # it's a file, append the written temp file path
                    # TODO: does file upload support multiple keys? In that case support it.
                    args.append(fi.file_path)
                else:
                    arg_values = request.form.getlist(fi.key)
                    has_values = bool(''.join(arg_values))
                    if has_values:
                        if fi.param.nargs == -1:
                            # Variadic argument, in html form each argument
                            # is a separate line in a textarea.
                            # treat each line we get from text area as a separate argument.
                            for value in arg_values:
                                values = value.splitlines()
                                logger.info(f'variadic arguments, split into: "{values}"')
                                args.extend(values)
                        else:
                            logger.info(f'arg_value: "{arg_values}"')
                            args.extend(arg_values)
        return args

    def _process_option(self, field_info):
        vals = request.form.getlist(field_info.key)
        if field_info.is_file:
            if field_info.link_name:
                # it's a file, append the file path
                yield field_info.cmd_opt
                yield field_info.file_path
        elif field_info.param.param_type == 'flag':
            # To work with flag that is default True
            # a hidden field with same name is also sent by form.
            # This is to detect if checkbox was not checked as then
            # we will get the field anyway with the "off flag" as value.
            if len(vals) == 1:
                off_flag = vals[0]
                flag_on_cmd_line = off_flag
            else:
                # we got both off and on flags, checkbox is checked.
                on_flag = vals[1]
                flag_on_cmd_line = on_flag

            yield flag_on_cmd_line
        elif ''.join(vals):
            # opt with value, if option was given multiple times get the values for each.
            # flag options should always be set if we get them
            # for normal options they must have a non empty value
            yield field_info.cmd_opt
            for val in vals:
                if val:
                    yield val
        else:
            # option with empty values, should not be added to command line.
            pass


class FieldInfo:
    """
    Extract information from the encoded form input field name
    the parts:
        [command_index].[opt_or_arg_index].[click_type].[html_input_type].[opt_or_arg_name]
    e.g.
        "0.0.option.text.text.--an-option"
        "0.1.argument.file[rb].text.an-argument"
    """

    @staticmethod
    def factory(key):
        field_id = FieldId.from_string(key)
        is_file = field_id.click_type.startswith('file')
        is_path = field_id.click_type.startswith('path')
        is_uploaded = key in request.files
        if is_file:
            if is_uploaded:
                field_info = FieldFileInfo(field_id)
            else:
                field_info = FieldOutFileInfo(field_id)
        elif is_path:
            if is_uploaded:
                field_info = FieldPathInfo(field_id)
            else:
                field_info = FieldPathOutInfo(field_id)
        else:
            field_info = FieldInfo(field_id)
        return field_info

    def __init__(self, param: FieldId):
        self.param = param
        self.key = param.key

        'Type of option (file, text)'
        self.is_file = self.param.click_type.startswith('file')

        'The actual command line option (--debug)'
        self.cmd_opt = param.name

        self.generate_download_link = False

    def before_script_execute(self):
        pass

    def after_script_executed(self):
        pass

    def __str__(self):
        return str(self.param)

    def __lt__(self, other):
        "Make class sortable"
        return (self.param.command_index, self.param.param_index) < \
               (other.param.command_index, other.param.param_index)

    def __eq__(self, other):
        return self.key == other.key


class FieldFileInfo(FieldInfo):
    """
    Use for processing input fields of file type.
    Saves the posted data to a temp file.
    """
    'temp dir is on class in order to be uniqe for each request'
    _temp_dir = None

    def __init__(self, fimeta):
        super().__init__(fimeta)
        # Extract the file mode that is in the type e.g file[rw]
        self.mode = self.param.click_type.split('[')[1][:-1]
        self.generate_download_link = True if 'w' in self.mode else False
        self.link_name = f'{self.cmd_opt}.out'

        logger.info(f'File mode for {self.key} is {self.mode}')

    def before_script_execute(self):
        self.save()

    @classmethod
    def temp_dir(cls):
        if not cls._temp_dir:
            cls._temp_dir = tempfile.mkdtemp(dir=click_web.OUTPUT_FOLDER)
        logger.info(f'Temp dir: {cls._temp_dir}')
        return cls._temp_dir

    def save(self):
        logger.info('Saving...')

        logger.info('field value is a file! %s', self.key)
        file = request.files[self.key]
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            raise ValueError('No selected file')
        elif file and file.filename:
            filename = secure_filename(file.filename)
            name, suffix = os.path.splitext(filename)

            fd, filename = tempfile.mkstemp(dir=self.temp_dir(), prefix=name, suffix=suffix)
            self.file_path = filename
            logger.info(f'Saving {self.key} to {filename}')
            file.save(filename)

    def __str__(self):

        res = [super().__str__()]
        res.append(f'file_path: {self.file_path}')
        return ', '.join(res)


class FieldOutFileInfo(FieldFileInfo):
    """
    Used when file option is just for output and form posted it as hidden or text field.
    Just create a empty temp file to give it's path to command.
    """

    def __init__(self, fimeta):
        super().__init__(fimeta)
        if self.param.form_type == 'text':
            self.link_name = request.form[self.key]
            # set the postfix to name name provided from form
            # this way it will at least have the same extension when downloaded
            self.file_suffix = request.form[self.key]
        else:
            # hidden no preferred file name can be provided by user
            self.file_suffix = '.out'

    def save(self):
        name = secure_filename(self.key)

        filename = tempfile.mkstemp(dir=self.temp_dir(), prefix=name, suffix=self.file_suffix)
        logger.info(f'Creating empty file for {self.key} as {filename}')
        self.file_path = filename


class FieldPathInfo(FieldFileInfo):
    """
    Use for processing input fields of path type.
    Extracts the posted data to a temp folder.
    When script finished zip that folder and provide download link to zip file.
    """

    def save(self):
        super().save()
        zip_extract_dir = tempfile.mkdtemp(dir=self.temp_dir())

        logger.info(f'Extracting: {self.file_path} to {zip_extract_dir}')
        shutil.unpack_archive(self.file_path, zip_extract_dir, 'zip')
        self.file_path = zip_extract_dir

    def after_script_executed(self):
        super().after_script_executed()
        fd, filename = tempfile.mkstemp(dir=self.temp_dir(), prefix=self.key)
        folder_path = self.file_path
        self.file_path = filename

        logger.info(f'Zipping {self.key} to {filename}')
        self.file_path = shutil.make_archive(self.file_path, 'zip', folder_path)
        logger.info(f'Zip file created {self.file_path}')
        self.generate_download_link = True


class FieldPathOutInfo(FieldOutFileInfo):
    """
    Use for processing output fields of path type.
    Create a folder and use as path to script.
    When script finished zip that folder and provide download link to zip file.
    """

    def save(self):
        super().save()
        self.file_path = tempfile.mkdtemp(dir=self.temp_dir())

    def after_script_executed(self):
        super().after_script_executed()
        fd, filename = tempfile.mkstemp(dir=self.temp_dir(), prefix=self.key)
        folder_path = self.file_path
        self.file_path = filename
        logger.info(f'Zipping {self.key} to {filename}')
        self.file_path = shutil.make_archive(self.file_path, 'zip', folder_path)
        logger.info(f'Zip file created {self.file_path}')
        self.generate_download_link = True
