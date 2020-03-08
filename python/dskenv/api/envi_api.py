# -*- coding: utf-8 -*-
import os
import sys
import re
from datetime import datetime
import getpass
import subprocess

import platform
import dskenv
from dskenv import dskenv_constants

from dskenv.base_env import BaseEnv
from dskenv.proxy_env import ProdEnv
from dskenv.envi import Envi


class YamlUtils(object):
    @staticmethod
    def load_data(a_file, loader=None):
        """Very simple reader for yaml envi_info file
        """

        data = {}
        try:
            import yaml
            with open(a_file, "rt") as fh:
                if loader is None:
                    data = yaml.load(fh, Loader=yaml.FullLoader)
                else:
                    # note: save_data will not be suportted
                    data = yaml.load(fh, Loader=loader)
        except Exception as e:
            raise Exception("Cannot parse yml file: %s" % e)
        return data


def get_dict_environ_envi():
    display = os.environ.get("DISPLAY", "")
    if display in ["", None]:
        return {'DSKENV': os.environ.get('DSKENV'),
                'HOME': os.environ.get('HOME'),
                'PYTHONPATH': os.path.join(os.environ.get('DSKENV'), 'python')
                }
    return {'DSKENV': os.environ.get('DSKENV'),
            'HOME': os.environ.get('HOME'),
            'PYTHONPATH': os.path.join(os.environ.get('DSKENV'), 'python'),
            'DISPLAY': display
            }


def process_get_output(cmd):
    """cmd: list of what's make the command to run. wait until done

        :param cmd: cmd to pass to Popen
        :return list: output lines from process stdout (list)

    """

    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         close_fds=True,
                         shell=False,
                         env=get_dict_environ_envi())
    if sys.platform == "win32":
        p.stdin.close()
    if p.wait() != 0:
        return ["ERROR: %s" % " ".join(cmd)]
    res = p.stdout.readlines()
    p.stdout.close()
    return res

user_template = """  -  login: %(login)s
     email: %(email)s
     shotgun_name: %(shotgun_name)s
     dev_path: %(dev_path)s
     dev_path_configs: %(dev_path_configs)s
     projects: %(projects)s
"""


class DevUser(dict):
    """Dev info"""
    def __init__(self):
        super(DevUser, self).__init__()
        self.reset()

    def reset(self):
        self.shotgun_name = ""
        self.projects = list()
        self.login = ""
        self.email = ""
        self.dev_path = ""
        self.dev_path_configs = []

    def setdata(self, **adict):
        self.__dict__.update(adict)
        if self.dev_path_configs is None:
            self.dev_path_configs = []
        if isinstance(self.dev_path_configs, str):
            self.dev_path_configs = [self.dev_path_configs]
        self.dev_path_configs = [
            os.path.expandvars(
                os.path.expanduser(x))for x in self.dev_path_configs]

        if self.projects is None:
            self.projects = list()
        if isinstance(self.projects, str):
            self.projects = [self.projects]

        if self.dev_path == "":
            self.dev_path = '/tmp'
        else:
            self.dev_path = os.path.expandvars(
                os.path.expanduser(self.dev_path))
        return self.is_valid()

    def is_valid(self):
        """check if the basic requirement are met"""
        if (self.shotgun_name != "" and
                isinstance(self.projects, list) and
                isinstance(self.login, str) and
                self.login != "" and
                isinstance(self.dev_path, str) and
                self.dev_path != ""):
            return True
        return False

    def write(self, fstream):
        fstream.write(user_template % self.__dict__)


# ENVI API ###################################################
class EnviApi(object):
    """Read the main envi_info_location for query """
    __file_location = BaseEnv.envi_info_location()
    __devuser = "dev_user"

    def __init__(self):
        super(EnviApi, self).__init__()
        self.dev_user = list()

    def reset(self, envplace=""):
        """overwrite the class instance file_location
            :param envplace: path (str) to the envi location
            :return None:
        """
        if envplace != "":
            EnviApi.__file_location = os.path.join(envplace,
                                                   BaseEnv.envi_iddir(),
                                                   BaseEnv.envi_file_name())
        self.dev_user = list()

    def is_valid(self):
        """Basic method to overload """
        try:
            return len(self.site['name']) > 0
        except:
            pass
        return False

    def load_data(self):
        """Build object list DevUser (found in envi_info)
            :param None:
            :returns data: the content of the envi_info as dict
        """
        if not os.path.isfile(EnviApi.__file_location):
            return dict()
        data = YamlUtils.load_data(EnviApi.__file_location)

        if 'site' in data:
            self.site = data['site']

        if self.__devuser in data:
            for x in data[self.__devuser]:
                a = DevUser()
                a.setdata(**x)
                # only update valid dev_user
                if a.is_valid():
                    self.dev_user.append(a)
                else:
                    print("user not valid", a)
        return data

    @staticmethod
    def generic_launch_log_file(appname):
        """Create a generic logfile in tmp are with date, time and app name

            :param appname: appname used as tagname of the log
            :return log_file: str

        """
        day, hour = datetime.today().strftime("%Y-%m-%d %Hh%Mm%S").split(" ")
        log_dir = os.path.join(os.sep,
                               'tmp',
                               'envi_log',
                               appname,
                               day)
        log_file = os.path.join(
                        log_dir,
                        "log_%s_%s-%s_%s.log" % (
                                                appname,
                                                day,
                                                hour,
                                                getpass.getuser())
                                )
        # create log dir
        cmd = ['mkdir', '-p', log_dir]
        p = subprocess.Popen(cmd)
        error = ""
        if p.wait() != 0:
            import tempfile
            log_file = os.path.join("%s" % tempfile.mkdtemp(),
                                    "log_%s_%s-%s_%s.log" % (
                                        appname,
                                        day,
                                        hour,
                                        getpass.getuser()))
            sys.stderr.write("Couldn't create log directory: %s\n" % log_dir)
            sys.stderr.write("Using: %s\n" % log_file)
            error = "ERROR: %s" % " ".join(cmd)
            open(log_file, "w").write(error + "\n")

        else:
            open(log_file, "a").write("BEFORE LAUNCH\n")

        return log_file

    @staticmethod
    def _valid_command_syntax(x):
        """For ease to build envi command its use list of list of envi option
        and tag, this function check which form x is  and return the correct
        envi commands -- internally used
        """

        need_join = False
        for i in x:
            if isinstance(i, str):
                return x
            assert isinstance(i, list)
            for ii in i:
                if " " not in ii:
                    need_join = True
                    break
        if need_join:
            envi_command = list()
            for i in x:
                envi_command.append(" ".join(i))
            return envi_command
        return x

    @staticmethod
    def do_log(x, log_file=""):
        """Add log argument to all list of envi:

            :param x: list of envi command as single option or pack
            :param log_file: name of the log file
            :return x: the modified x
            :example: x = [['-c', 'dev_show'],['-c', 'inhouse_maya']]
                      return [['-c', 'dev_show','-l',log_file],
                      ['-c', 'inhouse_maya','-l',log_file]]

        """
        if log_file == "":
            return x
        for i in x:
            i.extend(["-l", log_file])
        return x

    @staticmethod
    def do_debug(x, loginname=""):
        """Add a user config lock up to all envi statement

            :param x: list of envi command as single option or pack
            :param loginname: a user login name. if "" set to the current user
            :return x: the modified x
            :example: Ex: x = [['-c', 'dev_show'],['-c', 'inhouse_maya']]
                      return  [['-c', 'dev_show',"D",loginname],
                                ['-c', 'inhouse_maya','-D',loginname]]
        """

        if loginname == "":
            loginname = getpass.getuser()
        for i in x:
            i.extend(["-D", loginname])
        return x

    @staticmethod
    def do_platform(x):
        x.insert(0, ['-p', Envi().pack_system()])
        return x

    @staticmethod
    def do_app(x, app_name, do_deamon=True):
        """Add an app statement to the last statement

            :param x: list of envi command as single option or pack
            :param app_name: app to launch
            :param do_deamon: bool (default True), to daemonize the process
            :example: Ex: x = [['-c', 'dev_show'],['-c', 'inhouse_maya']]
                      return [['-c', 'dev_show'],
                      ['-c', 'inhouse_maya','-a',app_name]]

            :return x: list of envi command as single option or pack

        """
        if app_name == "":
            return x
        x[-1].extend(["-a", app_name])
        if do_deamon:
            x[-1].append("-Deamon")
        return x

    @staticmethod
    def do_arguments(x, argument_list):
        """Add argument to x

            :param x: list of envi command as single option or pack
            :param argument_list: argument list to add
            :return x: list of envi command as single option or pack
        """

        x[-1].append("--")
        x[-1].extend(argument_list)
        return x

    @staticmethod
    def do_extrapackage(x, extra_package):
        """Add argument to x

            :param x: list of envi command as single option or pack
            :param argument_list: list of envi command as single option or pack
            :return x: list of envi command as single option or pack
        """
        if isinstance(extra_package, str):
            extra_package = [extra_package]
        if len(x) > 0 and isinstance(x, list):
            x[-1].extend(extra_package)
            return x
        return [extra_package]

    @staticmethod
    def do_execute(x, dskenvpath):
        """Execute envi command in a specific environment

            :param x: list of envi command as single option or pack
            :param    dskenvpath: envi config root

        """
        pr = ProdEnv(dskenvpath)
        for xx in x:
            xx.insert(0, "do_execute")
            Envi().execute(xx, True)
        pr.back_to_global()

    @classmethod
    def build_launch_bash(cls,
                          envicommands,
                          env_root=None,
                          app_tag="",
                          add_default_env=None,
                          add_history=True,
                          envi_dump_file="",
                          split_launch=False):
        """Dump the envicommands into a file, good for execution

            :param envicommands: is a list of valid envi command (list)
            :param app_tag: (str) use to document this launch.
             (store in DSK_ENGINE)
            :param add_default_env: (dict or list of key)support
             for extra export statement, ex: tank...
            :param add_history: bool default True, add the history envi config

            :returns launchfile: the name of the file ready for execution
                    see launch_batch_file and launch_batch_file_with_console

        """
        if env_root is None:
            env_root = os.environ.get(dskenv_constants.DSK_ENV_PATH_KEY)

        if envi_dump_file != "":
            launchfile = envi_dump_file
        else:
            launchpath = Envi.get_temp_dir("envizlaunch")
            launchfile = os.path.join(launchpath, "doenvi.sh")

        try:

            with open(launchfile, "w") as fh:
                scmd = list()
                scmd.append("#!/bin/bash -l")

                # reset the python path
                # ideally we will want to source system and init studio shell

                if add_default_env:
                    if isinstance(add_default_env, dict):
                        for x in add_default_env:
                            value = add_default_env[x]

                            if x == 'SGTK_CONTEXT' or x == 'TANK_CONTEXT':

                                value = value.replace('"', r'\"')
                                value = '"' + value + '"'
                                scmd.append('export %s=%s' % (x, value))
                            else:

                                if x in ['PYTHONPATH']:
                                    scmd.append("export %s=%s:${%s}" % (
                                                            x, value, x))
                                else:
                                    scmd.append("export %s=%s" % (x, value))

                    elif isinstance(add_default_env, list):
                        for x in add_default_env:
                            value = os.environ.get(x, "")

                            if x == 'SGTK_CONTEXT' or x == 'TANK_CONTEXT':
                                value = value.replace('"', r'\"')
                                value = '"' + value + '"'
                                # f.write("value %s\n" % value)
                                scmd.append('export %s=%s' % (x, value))
                            else:
                                if x in ['PYTHONPATH']:
                                    # we cannot erase this one
                                    scmd.append("export %s=%s:${%s}" % (
                                                            x, value, x))
                                else:
                                    scmd.append("export %s=%s" % (
                                                            x, value))

                scmd.append("unset PYTHONHOME")
                scmd.append("export %s=%s" % (
                                dskenv_constants.DSK_ENV_PATH_KEY,
                                env_root))

                scmd.append("export DSK_ENGINE=%s" % app_tag)

                scmd.append("type envi &> /dev/null")
                scmd.append("if [ ! -z $? ] ; then")

                scmd.append("\tenvi() {")
                scmd.append("\t\tsource $DSKENV/bin/linux/envi_bsh $*\n\t}")
                scmd.append("\texport -f envi")
                scmd.append("fi")

                if add_history:
                    for obj in cls.get_history_command(with_app=False,
                                                       remove_app=True):
                        # BaseEnv.command_history():
                        if obj and len(obj) > 0:
                            scmd.append("envi " + obj[0] + ";")

                envicommands = cls._valid_command_syntax(envicommands)
                if split_launch is False:
                    for cmds in envicommands:
                        scmd.append("envi %s" % cmds)
                else:
                    for cmds in envicommands:
                        if "-a" not in cmds:
                            scmd.append("envi %s" % cmds)
                        else:
                            X = cls.split_launch_command(cmds)
                            app, arg, cmds, alog = X
                            scmd.append("set -o pipefail")
                            scmd.append("envi %s" % cmds)
                            if alog != "":
                                scmd.append("%s %s |& tee -a %s" % (
                                            app, arg, alog))
                            else:
                                scmd.append("%s %s" % (app, arg))

                fh.write("\n".join(scmd))
            if sys.version_info[0] == 3:
                os.chmod(launchfile, 0o775)
            else:
                os.chmod(launchfile, 0o775)

        except Exception as e:
            print("ERROR: build_launch_bash: %s" % str(e))

        return launchfile

    @staticmethod
    def split_launch_command(cmd):
        """Extract the value to of an envi commnand with app, arg and log

        :param cmd: envi command
        :returns app,arg,cmd,alog

        """
        arg = ""
        app = ""
        alog = ""
        if "--" in cmd:
            cmd, arg = cmd.split("--")
            cmd = cmd.strip()
            arg = arg.strip()
        paternapp = re.compile(r'-a\s*[\w\d\.\%s-]*' % os.sep)
        paternlog = re.compile(r'-l\s*[\w\d\.\%s-]*' % os.sep)
        m = paternapp.search(cmd)
        if m:
            stringfound = m.group()
            cmd = cmd.replace(stringfound, "")
            app = stringfound.replace("-a", "")
            app = app.strip()
            cmd = cmd.replace("-Deamon", "")
            m = paternlog.search(cmd)
            if m:
                stringfound = m.group()
                alog = stringfound.replace("-l", "")
                alog = alog.strip()

            return app, arg, cmd, alog
        else:
            return "", "", cmd, ""

    @staticmethod
    def launch_batch_file(filetoexecute, clean_tmp_dir=False):
        """Exec the given file.

            :param filetoexecute: a valid batch file
            :type filetoexecute: a valid executable file on disk
            :param clean_tmp_dir: option to remove the file
            :type clean_tmp_dir: bool, default = False (NOT SUPPORTED, IGNORED)

            :return None:

        """
        if clean_tmp_dir:
            process_get_output(filetoexecute)
            Envi.cleanup_temp_dir()
        else:
            subprocess.Popen(filetoexecute,
                             close_fds=True,
                             env=get_dict_environ_envi())

    @staticmethod
    def launch_batch_file_with_console(filetoexecute,
                                       console='gnome-terminal',
                                       clean_tmp_dir=False,
                                       hold=True):
        """Same as launch_batch_file, with an optional console

            :param filetoexecute: a valid batch file
            :type filetoexecute: a valid executable file on disk
            :param console: (str) default = xterm
            :type console: (str) xterm or konsole or gnome-terminal
            :param clean_tmp_dir: option to remove the file
            :type clean_tmp_dir: bool, default = False
            :param hold: option keep the window up
            :type hold: bool, default = True
            :returns None: no return value

        """
        # console = 'gnome-terminal'
        # hold = False
        # assert console in ['xterm','konsole','gnome-terminal']
        '''
        cmds = list()
        cmds.append("gnome-terminal")
        cmds.append("-x")
        cmds.append("bash")
        cmds.append("-ic")
        #cmds.append("-e")
        cmds.append(filetoexecute)
        #cmds.append('-x bash')
        #cmds.append("-e %s" % filetoexecute)
        process_get_output(cmds)
        #subprocess.Popen(cmds,
        #                 close_fds=True,
        #                 env=get_dict_environ_envi())
        '''
        os.system("gnome-terminal -x bash -ic %r" % filetoexecute)
        return
        if hold:
            cmds = [console, '-hold', '-e', filetoexecute]
        else:
            cmds = [console, '-e', filetoexecute]
        if clean_tmp_dir:
            process_get_output(cmds)
            Envi.cleanup_temp_dir()
        else:
            subprocess.Popen(cmds,
                             close_fds=True,
                             env=get_dict_environ_envi())

    @staticmethod
    def get_history_from_key():
        return os.environ.get(BaseEnv.get_command_info(), "")

    @classmethod
    def get_history_command(cls, with_app=False, remove_app=True, index=0):
        """Return all the envi commands sent

            :param with_app: default=False if true don't
                add command containing '-a app'
            :param remove_app: default=False
            :param index: default 0. if 1 remove the last statement
                2 two last statement etc...
            :returns list: a list of envi command

        """
        x = BaseEnv.command_history()
        paternapp = re.compile(r'-a\s*[\w\d\.\%s-]*' % os.sep)
        envcmd = list()
        for xx in x:
            m = paternapp.search(xx)
            if with_app is True:
                # remove -a appname for cmd
                if m:
                    if remove_app is True:
                        stringfound = m.group()
                        envarg = xx.replace(stringfound, "")
                        xx = envarg.strip()
                    else:
                        continue  # no adding
            else:
                if m:
                    xx = []
            if len(xx) > 0:
                envcmd.append([xx])
        if index != 0:
            try:
                envcmd = envcmd[:-index]
            except:
                pass
            # remove  last indexes
        return envcmd

    ###########################################################################
    def get_userdev_path(self, user):
        """Each dev user can have a directory under which is clone its repo
            (found in envi_info)

            :param user:  (str) a login name
            :return user_path:  (str) not found = ""

        """
        for u in self.dev_user:
            if u.login == user:
                return u.dev_path
        return ""

    def get_userdev_project(self, user):
        """Each dev user can be on a list of current project
            (found in envi_info)

            :param user: (str) a login name
            :return project_list: (list). list of project,
            empty [] if not found

        """
        for u in self.dev_user:
            if u.login == user:
                return u.projects
        return []

    def get_userdev_config_path(self, user):
        """Each dev user can be on a list of envi config
        (found in envi_info)

            :param user: (str) a login name
            :return project_list: (list). list of directory with config
                    empty [] if not found

        """

        for u in self.dev_user:
            if u.login == user:
                return u.dev_path_configs
        return list()

    def get_all_user_login(self):
        """Return all user loginname (found in envi_info)

            :param None:
            :return list: list of login : (list). list of login name
                          empty [] if not found

        """

        return [u.login for u in self.dev_user]
