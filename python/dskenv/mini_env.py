# -*- coding: utf-8 -*-
import os
import sys
import types
import tempfile
import traceback
import getpass
import logging
import platform

from pprint import pformat
from collections import OrderedDict
from dskenv import base_env
from dskenv.base_env import BaseEnv
from dskenv.config_info import ConfigInfo
from dskenv.pack_info import PackInfo
from dskenv.version_helper import VersionHelper
from dskenv.envi_utils import EnviUtils

# don't remove, this is use for some config evaluation
BASE_PACKAGE_DIR = BaseEnv.get_package_dir()

# create a logger to csh comment out message
logFormat = logging.Formatter('#%(levelname)-10s: %(message)-10s')
h = logging.StreamHandler()
h.setFormatter(logFormat)
comment = logging.getLogger("comment")
comment.addHandler(h)
comment.setLevel(logging.DEBUG)
cmdout = sys.stdout


class MiniEnv(object):

    # csh and tcsh default to bash
    """Command to be use to build the evaluation dictionary
    """
    __Cache_Set = dict()

    _shellFormatSetEnv = 'export {}="{}";'
    _shellFormatUnset = 'unset {}'
    _shellFormatAlias = 'alias {}="{}";'
    _shellFormatUnAlias = 'unalias {};'
    _shellVariable = "bsh"
    _shellVariableArg = "$*"
    _filelogging = None
    _atempArea = ""
    _sepDateTime = os.sep
    _printall = False

    @staticmethod
    def set_bash():
        MiniEnv._shellFormatSetEnv = 'export {}="{}";'
        MiniEnv._shellFormatUnset = 'unset {}'
        MiniEnv._shellFormatAlias = 'alias {}="{}";'
        MiniEnv._shellFormatUnAlias = 'unalias {};'
        MiniEnv._shellFormatFunction = '%s() {\n    %s\n}\nexport -f %s;\n'
        MiniEnv._shellVariable = "bsh"
        MiniEnv._shellVariableArg = "$*"

    @staticmethod
    def set_csh():
        MiniEnv._shellFormatSetEnv = 'setenv {} "{}";'
        MiniEnv._shellFormatUnset = 'unsetenv {};'
        MiniEnv._shellFormatAlias = 'alias {} "{}";'
        MiniEnv._shellFormatUnAlias = 'unalias {};'
        MiniEnv._shellFormatFunction = 'alias %s "%s";'
        MiniEnv._shellVariable = "csh"
        MiniEnv._shellVariableArg = ""

    @staticmethod
    def set_debug(val):
        MiniEnv._printall = val
        # cls._printall = val

    @classmethod
    def _printdebug(cls, arg):

        if cls._printall is False:
            return
        sys.stderr.write(arg+"\n")

    def __init__(self):
        super(MiniEnv, self).__init__()
        self.reset()

    def reset(self):
        # do following are to keep track of an history,
        # specially during adding pack and path
        self._devName = ""
        self._searchPath = list()
        self._packListName = list()
        self._packFound = OrderedDict()
        self._configFound = OrderedDict()
        self._storeLocalEnv = OrderedDict()
        self._storeUnsetEnv = list()
        self._alias = list()
        self._echoCmd = list()  # for stuff like complete
        self._commands = list()
        self._function = list()

    @classmethod
    def reset_cache(cls):
        cls.__Cache_Set = dict()

    @classmethod
    def environ(cls, key):
        """Work only for setPath"""
        if key in cls.__Cache_Set:
            return cls.__Cache_Set[key]
        return ""

    @classmethod
    def Set_environ_cache(cls, key, value):
        """Work only for setPath

            This is a local cache mechanism to
            evaluate value with other environment
            The value is also cached in the os.environment
            to be readable from config and pack

            :param key: a key environment
            :param value: an environment value made of ${}
            :return thevalue:  the value expanded

        """
        vv = os.path.expandvars(value)
        cls.__Cache_Set[key] = vv
        os.environ[key] = vv
        return vv

    #  logging into a file
    @classmethod
    def startlog(cls, filename):
        """To start a log with append to stream

            :param filename: the name of the file to log to
            :return None:

        """
        try:
            mode = "w"
            if os.path.isfile(filename):
                mode = "a+"
            cls._filelogging = open(filename, mode)
            cls.logfile("Envi starting: pid %d" % os.getpid())
        except Exception as e:
            sys.stderr.write(str(e))

    #  logging into a file
    @classmethod
    def endlog(cls):
        """Flush and close the logfile if open
        """
        # no closing if open with a
        if cls._filelogging:
            # cls._filelogging.flush()
            # os.fsync(cls._filelogging.fileno())
            cls._filelogging.close()
            cls._filelogging = None

    @classmethod
    def logfile(cls, strdata):
        """The log function
            :param strdata: string to log
        """
        if cls._filelogging is None:
            return
        if isinstance(strdata, str):
            cls._filelogging.write("Envi: " + strdata + "\n")
        else:
            try:
                cls._filelogging.write("Envi: " + pformat(strdata) + "\n")
            except:
                pass

    @classmethod
    def getlog(cls):
        """Get the stream open for logging
        """
        return cls._filelogging

    @staticmethod
    def get_temp_dir(rev):
        """Create a temp area base on tag, keep result to further clean after

            :param rev: a tag, simple
            :return path: an existing temp directory

        """
        assert rev != ""
        if MiniEnv._atempArea == "":
            MiniEnv._atempArea = tempfile.mkdtemp()
        p = os.path.join(MiniEnv._atempArea, rev)
        if os.path.isdir(p):
            return p
        if EnviUtils.create_path(p) is False:
            comment.debug("cannot create %r" % p)
            return MiniEnv._atempArea
        return p

    @staticmethod
    def cleanup_temp_dir():
        """Remove the temp directory
        """
        import shutil
        if MiniEnv._atempArea != "" and os.path.isdir(MiniEnv._atempArea):
            shutil.rmtree(MiniEnv._atempArea)
        MiniEnv._atempArea = ""
        return

    def get_commands(self):
        return self._commands

    def add_command(self, command):
        self._commands.append(command)

    # setter getter
    def dev_name(self):
        return self._devName

    def set_dev_name(self, devName=""):
        self._devName = devName

    def get_pack_name_list(self):
        return self._packListName

    def set_init_pack_name_list(self, packListName):
        self._packListName = packListName

    def get_pack_found(self):
        return self._packFound

    def get_config_found(self):
        return self._configFound

    def get_local_env(self):
        return self._storeLocalEnv

    #####################
    # function that get evaluated/call for config/pack

    def addPath(self, k, v, at_end=False):
        """By default it actually prepend the path

            :param k: Environment variable
            :param v: path
            :param at_end: (bool)if true will append the new path
            :return None:
        """
        ks = "%s" % k
        vs = "%s" % v
        self._printdebug("add path: %s=%s" % (ks, vs))

        if ks not in self._storeLocalEnv:
            self._storeLocalEnv[ks] = list()
        # variables are prepend
        self.rmPath(k,  v)  # clean up if needed
        vss = vs.split(os.pathsep)
        for ve in reversed(vss):
            if at_end:
                if ks in self._storeLocalEnv:
                    resu = self._storeLocalEnv.pop(ks)
                    self._storeLocalEnv[ks] = resu
                self._storeLocalEnv[ks].append(ve)
            else:
                if ks in self._storeLocalEnv:
                    resu = self._storeLocalEnv.pop(ks)
                    self._storeLocalEnv[ks] = resu
                self._storeLocalEnv[ks].insert(0, ve)

    def addPaths(self, k, l, at_end=False):
        """By default it actually append the path in the same order

            :param k: Environment variable
            :param v: a list of path
            :param at_end: (bool)if true will append the new path
            :return None:
        """
        if isinstance(l, str):
            l = [l]
        if at_end:
            for v in l:
                self.addPath(k, v, at_end)
        else:
            for v in reversed(l):
                self.addPath(k, v, at_end)

    def setPath(self, k, v):
        """Reinitialize k with the value v

            :param k: Environment variable
            :param v: path
            :return None:

        """

        ks = "%s" % k
        vs = "%s" % v
        self._printdebug("set path: %s=%s" % (ks, vs))

        vv = self.Set_environ_cache(ks, vs)

        self._storeLocalEnv[ks] = list()
        self._storeLocalEnv[ks].append(vv)

    def unsetPath(self, k):
        """Unset the environment variable k

            :param k: a key

        """
        self._storeUnsetEnv.append("%s" % k)
        if k in self._storeLocalEnv:
            self._storeLocalEnv.pop(k)

    def unsetPathLocal(self, k):
        """Unset the environment variable k. This is a special function used by Reset

            :param k: a key

        """
        self._storeUnsetEnv = list()
        if k in self._storeLocalEnv:
            self._storeLocalEnv.pop(k)

    def rmPath(self, k, v):
        ks = "%s" % k
        vs = "%s" % v
        if ks not in self._storeLocalEnv:
            return
        vss = vs.split(os.pathsep)
        # something the : is use to actually remove more than one path
        for ve in vss:
            if ve in self._storeLocalEnv[ks]:
                self._storeLocalEnv[ks].remove(ve)

    #####################
    # PACK
    def addPack(self, apack):
        self._printdebug("add pack: %s" % (apack))
        self.rmPack(apack)
        self._packListName.append("%s" % apack)

    def rmPack(self, apack):
        p = VersionHelper(apack)
        for i, ip in enumerate([VersionHelper(x) for x in self._packListName]):
            if p.base == ip.base:
                self._packListName.pop(i)
                return

    def alias(self, k, v):
        ks = "%s" % k
        vs = "%s" % v
        self._printdebug("add alias: %s=%s" % (ks, vs))
        self._alias.append((ks, vs))

    def unalias(self, k):
        ks = "%s" % k
        self._alias.append((ks, ))

    def addFunction(self, k, v):
        ks = "%s" % k
        vs = "%s" % v

        vs = vs.replace("@shell", self._shellVariable)
        vs = vs.replace("@argshell", self._shellVariableArg)
        self._printdebug("add function: %s=%s" % (ks, vs))
        self._function.append((ks, vs))

    def printEcho(self, cmdToEcho):
        self._echoCmd.append(cmdToEcho)

    def _evalCmd(self, stringOrFiledesc):
        locals().update({'add_path': self.addPath,
                         'add_paths': self.addPaths,
                         'set_path': self.setPath,
                         'rm_path': self.rmPath,
                         'unset_path': self.unsetPath,
                         'add_pack': self.addPack,
                         'rm_pack': self.rmPack,
                         'add_unalias': self.unalias,
                         'add_alias': self.alias,
                         'add_function': self.addFunction,
                         'log_file': self.logfile,
                         'dir_platform': self.platform_subdir,
                         'echo': self.printEcho})
        # exec or execfile, may need more introspection
        try:
            exec(stringOrFiledesc)
            return True
        except Exception as e:
            sys.stderr.write(str(e))
            sys.stderr.write("trying to execute:\n %s\n" % stringOrFiledesc)
        return False

    def load_config_or_pack(self, fileName):
        """Usefull for config and pack
        """
        res = False
        try:
            self.logfile("opening %r" % fileName)
            code = open(fileName, "r").read()
            # put split line on single line
            code = code.replace("\\\n", "")
            lines = code.split("\n")
            cleancode = list()
            for line in lines:
                if line.startswith("print "):
                    cleancode.append("echo(" + line[6:] + ")")
                else:
                    if line.strip() != "":
                        cleancode.append(line)
            res = self._evalCmd("\n".join(cleancode))
        except Exception as e:
            comment.error("reading or evaluating %r" % fileName)
            self.logfile("load_config_or_pack: %r (abort file)" % fileName)
            self.logfile("Error excecuting:\n %s" % str(e))
            traceback.print_exc()
            return False
        return res

    def parse_cmd_base26(self, argListOrStr):
        """For Python26
        """
        from optparse import OptionParser

        # parser setup
        parser = OptionParser(add_help_option=False)
        parser.add_option("-c",
                          dest="configs",
                          action="append",
                          default=list(),
                          help="config(s) to load")
        parser.add_option("-p",
                          dest="packs",
                          action="append",
                          default=list(),
                          help="pack(s) to load")

        parser.add_option("-d",
                          dest="d",
                          action="store_true",
                          default=False,
                          help="first look in current area")
        parser.add_option("-D",
                          dest="D",
                          action="store",
                          default="",
                          help="other username")

        parser.add_option("-f",
                          dest="fromDir",
                          action="store",
                          default="",
                          help="from a given directory")

        parser.add_option("-r",
                          dest="revision",
                          action="store",
                          default="",
                          help="(not supported yet) a config revision")
        parser.add_option("-t",
                          dest="date",
                          action="store",
                          default="",
                          help="(not supported yet)")

        argList = argListOrStr
        if type(argListOrStr) in (str,):
            # split appropriately
            if argListOrStr.find(" ") == -1:
                argList = [argListOrStr]
            else:
                argList = argListOrStr.split()

        if type(argList) != list:
            return False

        (opt, args) = parser.parse_args(argList)
        opt.configs.extend(args)  # extra arguments are interpreted as configs
        baseSearch = BaseEnv.base()
        if opt.fromDir != "":
            baseSearch = opt.fromDir

        if opt.D != "":
            self._devName = opt.D
        elif opt.d is True:
            self._devName = getpass.getuser()

        if self._devName != "":
            self._searchPath = [BaseEnv.user_home(self._devName), baseSearch]
        else:
            self._searchPath = [baseSearch]
        opt.configs = [x for x in opt.configs if x != ""]
        opt.packs = [x for x in opt.packs if x != ""]
        return (opt, args)

    def parse_cmd_base(self, argListOrStr):
        from argparse import ArgumentParser

        # parser setup
        parser = ArgumentParser()
        parser.add_argument("-c",
                            dest="configs",
                            action="append",
                            default=list(), help="config(s) to load")
        parser.add_argument("-p",
                            dest="packs",
                            action="append",
                            default=list(), help="pack(s) to load")

        parser.add_argument("-d",
                            dest="d",
                            action="store_true",
                            default=False,
                            help="first look in current area")
        parser.add_argument("-D",
                            dest="D",
                            action="store",
                            default="",
                            help="other username")

        parser.add_argument("-f",
                            dest="fromDir",
                            action="store",
                            default="",
                            help="from a given directory")
        parser.add_argument("-r",
                            dest="revision",
                            action="store",
                            default="",
                            help="(not supported yet) for config")
        parser.add_argument("-t",
                            dest="date",
                            action="store",
                            default="",
                            help="use for packs")

        argList = argListOrStr
        if type(argListOrStr) in (str,):
            # split appropriately
            if argListOrStr.find(" ") == -1:
                argList = [argListOrStr]
            else:
                argList = argListOrStr.split()

        if type(argList) != list:
            return False

        (opt, args) = parser.parse_known_args(argList)
        # opt.configs.extend(args) # extra arguments
        # are interpreted as configs
        baseSearch = BaseEnv.base()
        if opt.fromDir != "":
            baseSearch = opt.fromDir

        if opt.D != "":
            self._devName = opt.D
        elif opt.d is True:
            self._devName = getpass.getuser()

        if self._devName != "":
            self._searchPath = [BaseEnv.user_home(self._devName),
                                baseSearch]
        else:
            self._searchPath = [baseSearch]
        opt.configs = [x for x in opt.configs if x != ""]
        opt.packs = [x for x in opt.packs if x != ""]
        return (opt, args)

    def parse_cmd(self, argListOrStr):
        # to support 2.6 and 2.7

        if sys.version_info.major > 2 or sys.version_info.minor >= 7:
            args = self.parse_cmd_base(argListOrStr)
        else:
            args = self.parse_cmd_base26(argListOrStr)

        # args = self.parse_cmd_base(argListOrStr)
        opt = args[0]

        clip_time = -1

        if opt.date != "":
            res = opt.date.split("%s" % MiniEnv._sepDateTime)  # separator /
            if len(res) == 2:
                clip_time = EnviUtils.convert_date_and_time_to_float_time(
                                                                res[0], res[1])
            else:
                clip_time = EnviUtils.convert_date_and_time_to_float_time(
                                                                opt.date)
        configDir = ""

        for c in opt.configs:
            # check if the file has been check out
            a = ConfigInfo(BaseEnv.clean(c), None)
            if configDir != "":
                rc = a.real_version_file(ConfigInfo, None)
            else:
                rc = a.real_version_file(ConfigInfo, self._searchPath)
            if rc is None or rc.is_valid() is False:
                if configDir != "":
                    comment.error("no config %r found in %s" % (c, configDir))
                    self.logfile("parse_cmd: no config %r found %s" % (
                                                        c, configDir))
                else:
                    comment.error("no config %r found in %s" % (
                                                        c, self._searchPath))
                    self.logfile("no config %r found in %s" % (
                                                        c, self._searchPath))
            else:
                if self.load_config_or_pack(rc.get_fullname()) is False:
                    comment.error("couldn't load successfully  %s" % (
                                                        rc.get_fullname()))
                    self.logfile("couldn't load successfully  %s" % (
                                                        rc.get_fullname()))
                else:
                    self._configFound[rc.name] = rc.path

        for p in opt.packs:
            # comment.error("----> pack %r" % p)
            self.addPack(BaseEnv.clean(p))

        for pc in self._packListName:
            # comment.error("----> pack %r %r" % (pc,self._searchPath))
            pf = PackInfo(pc, None)
            rc = pf.real_version_file(PackInfo,
                                      self._searchPath,
                                      clip_time)
            if rc is None or rc.is_valid() is False:
                # pc maybe with the all name
                try:
                    # comment.error("pc = %s" % (pc))
                    xx = BaseEnv.pack_info(replaceMain=False)
                    search = ""
                    for x in xx:
                        if x[0].startswith(pc):
                            search = os.path.dirname(x[1])
                            break
                    if search != "":
                        rc = PackInfo(pc, search)
                        if rc is None or rc.is_valid() is False:
                            comment.error("===>no pack %r found in %s" % (
                                                            pf, [search]))
                            self.logfile("===>no pack %r found in %s" % (
                                                            pf, [search]))
                        else:
                            self._packFound[rc.name] = rc.path
                    else:
                        comment.error("no pack1 %r found in %s" % (
                                                        pc, self._searchPath))
                        self.logfile("no pack %r found in %s" % (
                                                        pc, self._searchPath))
                except Exception as e:
                    comment.error("no pack2 %r found in %s" % (
                                                        pc, self._searchPath))
                    comment.error(str(e))
                    self.logfile("no pack %r found in %s" % (
                                                        pc, self._searchPath))
                    self.logfile(str(e))
            else:
                self._packFound[rc.name] = rc.path

    @staticmethod
    def expand_vars(adict):
        # cache dependency at least once for now
        for i in adict:
            adict[i] = os.path.expandvars(adict[i])
        # for i in adict:
        #    adict[i] = os.path.expandvars(adict[i])

    @staticmethod
    def load_key_environ():
        """from os.environ copy envi's special key
            here is could be a list since it's called to unset
            them so far (see echo_environ_undo)
            a dict is use just for uniformity
        """
        # import sys
        d = dict()
        for i in os.environ:
            if (i.startswith(BaseEnv._undoPackageKey) or
                    i.startswith(BaseEnv._undoConfigkey) or
                    i.startswith(BaseEnv._envKey)):
                d[i] = os.environ[i]
        return d

    def load_environ(self, removeList=None, exceptionStartwith=None):
        """Make a copy of the os.environ with some exception
        removeList: variable you don't want
        exceptionStartwith is a dictionary with
        environ key and a list of string to remove
        if any path that start with them
        """
        if removeList:
            assert type(removeList) == list
        if exceptionStartwith:
            assert type(exceptionStartwith) == dict

        self._storeLocalEnv.clear()
        if exceptionStartwith:
            exceptionStartwith = dict()
        for i in os.environ:
            if not (i.startswith(BaseEnv._undoPackageKey) or
                    i.startswith(BaseEnv._undoConfigkey) or
                    i.startswith(BaseEnv._envKey)):
                if removeList and i in removeList:
                    pass
                else:
                    ddd = os.environ[i].split(os.pathsep)
                    if i in exceptionStartwith:
                        d = list()
                        exceptionList = exceptionStartwith[i]
                        for vv in ddd:
                            doAdd = True
                            for anEx in exceptionList:
                                if vv.startswith(anEx):
                                    doAdd = False
                                    break
                            if doAdd:
                                d.append(vv)
                        self._storeLocalEnv[i] = d
                    else:
                        self._storeLocalEnv[i] = ddd

    def clean_environ(self, removeList=None, exceptionStartwith=None):
        # load environ with clean the _INDOP so we save them first
        self.load_environ(removeList, exceptionStartwith)
        cmdRemove = BaseEnv.get_cleanup_cmd()
        for cmd in cmdRemove:
            self._evalCmd(cmd)

    def get_env_as_dict(self):
        execEnv = dict()
        lenv = self.get_local_env()
        for i in lenv:
            execEnv[i] = os.pathsep.join(lenv[i])
        return execEnv

    def echo(self, alog, command=True):
        write = None
        ret = ""
        if hasattr(alog, "info"):
            write = alog.info
        else:
            if hasattr(alog, "write"):
                write = alog.write
                ret = "\n"
        if write is None:
            comment.error("cannot print this object in echo")
            return
        if command is True:
            for i in self.get_commands():
                write("%s" % i + ret)
            return

        for i in self._storeUnsetEnv:
            write(MiniEnv._shellFormatUnset.format(i))
            if ret != "":
                write(ret)

        for i in self._storeLocalEnv:
            if i.startswith('BASH_FUNC'):
                continue
            xclean = os.pathsep.join(self._storeLocalEnv[i])
            # write(MiniEnv._shellFormatSetEnv % (i,xclean))
            write(MiniEnv._shellFormatSetEnv.format(i, xclean))
            if ret != "":
                write(ret)

        # Question? Do we need to unAlias and than alias
        # or like here the order is respected
        for i in self._alias:
            if len(i) == 2:
                write(MiniEnv._shellFormatAlias.format(i[0], i[1]))
            else:
                # bash will generate and error if alias is not
                # defined so we set it be for unsetting
                write(MiniEnv._shellFormatAlias.format(i[0], ""))
                if ret != "":
                    write(ret)

                write(MiniEnv._shellFormatUnAlias.format(i[0]))
            if ret != "":
                write(ret)

        for i in self._function:
            if len(i) == 2:
                try:
                    write(MiniEnv._shellFormatFunction % (i[0], i[1], i[0]))
                except:
                    write(MiniEnv._shellFormatFunction % (i[0], i[1]))
                if ret != "":
                    write(ret)

        # echoing
        for i in self._echoCmd:
            write("%s" % i)
            if ret != "":
                write(ret)

    def echo_environ_undo(self, d, doset=True):
        """Undo history"""
        global cmdout
        if doset is True:
            for i in d:
                if i != "" and not i.startswith('BASH_FUNC'):
                    cmdout.write(
                        MiniEnv._shellFormatSetEnv.format(i, d[i]) + '\n')
        else:

            for i in d:
                if i != "":
                    cmdout.write(
                        MiniEnv._shellFormatUnset.format(i + '\n'))

    def echo_environ_diff_only(self, ori_os):
        global cmdout
        write = None
        ret = ""
        if hasattr(cmdout, "info"):
            write = cmdout.info
        else:
            if hasattr(cmdout, "write"):
                write = cmdout.write
                ret = "\n"
        if write is None:
            comment.error("cannot print this object in echo\n")
            return

        for i in self._storeUnsetEnv:
            write(MiniEnv._shellFormatUnset.format(i))
            if ret != "":
                write(ret)

        for i in self._storeLocalEnv:
            if i.startswith('BASH_FUNC'):
                continue
            xclean = os.pathsep.join(self._storeLocalEnv[i])

            if i not in ori_os:
                write(MiniEnv._shellFormatSetEnv.format(i, xclean))
                if ret != "":
                    write(ret)
            else:
                if xclean != ori_os[i]:
                    write(MiniEnv._shellFormatSetEnv.format(i, xclean))
                    if ret != "":
                        write(ret)

        # Question? Do we need to unAlias and than alias
        # or like here the order is respected
        for i in self._alias:
            if len(i) == 2:
                write(MiniEnv._shellFormatAlias.format(i[0], i[1]))
            else:
                # bash will generate and error
                # if alias is not defined so we set it be for unsetting
                write(MiniEnv._shellFormatAlias.format(i[0], ""))
                if ret != "":
                    write(ret)

                write(MiniEnv._shellFormatUnAlias.format(i[0]))
            if ret != "":
                write(ret)

        for i in self._function:
            if len(i) == 2:
                try:
                    write(MiniEnv._shellFormatFunction % (i[0], i[1], i[0]))
                except:
                    write(MiniEnv._shellFormatFunction % (i[0], i[1]))
                if ret != "":
                    write(ret)

        # echoing
        for i in self._echoCmd:
            write("%s" % i)
            if ret != "":
                write(ret)

    def write_bash_history(self):
        """Export only l'historic store in _BASE_COMMAND
        """
        global cmdout
        write = None
        ret = ""
        if hasattr(cmdout, "info"):
            write = cmdout.info
        else:
            if hasattr(cmdout, "write"):
                write = cmdout.write
                ret = "\n"
        if write is None:
            comment.error("cannot print this object in echo\n")
            return
        key = BaseEnv.get_command_info()
        if key in self._storeLocalEnv:
            if len(self._storeLocalEnv[key]) > 0:
                value = self._storeLocalEnv[key][0]
                write(MiniEnv._shellFormatSetEnv.format(key, value))
                if ret != "":
                    write(ret)
                return True
        return False

    def dump_os_as_shell(self, writefile):
        try:
            fout = open(writefile, "w")
            for i in os.environ:
                if i not in base_env.inUse:
                    if i.startswith('BASH_FUNC'):
                        continue
                    fout.write(
                        MiniEnv._shellFormatSetEnv.format(
                                            i,
                                            os.environ.get(i)) + "\n")
            fout.close()
        except Exception as e:
            sys.stderr.write(str(e))
            return False
        return True

    def write_environ(self, ori_os, writefile):
        global cmdout
        cmdssave = cmdout
        try:
            fout = open(writefile, "w")
            cmdout = fout
            self.echo_environ_diff_only(ori_os)
        except Exception as e:
            sys.stderr.write(str(e))
        pass
        cmdout = cmdssave

    def echo_environ(self, doPrint=True, doComment=False):
        if doPrint:
            self.echo(cmdout, False)
            # self.echo(sys.stdout,False)
        if doComment:
            self.echo(comment, False)

    def echo_command(self, doPrint=True, doComment=False):
        global cmdout
        if doPrint:
            self.echo(cmdout, True)
        if doComment:
            self.echo(comment, True)

    @staticmethod
    def platform_subdir():
        """Return platform  dependant directory

            Not Finished

        """
        plat = platform.system()
        xl = platform.dist()[:2]

        if plat == "Linux":
            if len(xl) == 2:
                a = xl[1]
                # remove the path number
                sa = a.split(".")
                if len(sa) == 3:
                    xl = [xl[0], ".".join(sa[:-1])]
            xx = "-".join(xl)
            xx = xx.lower()
            xx = xx.replace("suse", "opensuse")
            return os.path.join("linux", xx)
        if plat == "Darwin":
            # NOT DONE
            sys.stderr.write("platform_subdir mac: NOT DONE\n")
            xx = "-".join(xl)
            # return "mac",platform.mac_ver()
            return os.path.join("mac", xx)

        # NOT DONE
        sys.stderr.write("platform_subdir windows: NOT DONE\n")
        xx = "-".join(xl)
        return os.path.join("window", xx)
        # return "window","win64"

    @classmethod
    def pack_system(cls):
        return cls.platform_subdir().replace(os.sep, "_").replace("-", "_")

    def store(self):
        """Create an pack file with define environment
        """
        file_init = self.pack_system()
        file_init = file_init+".py"
        a_file = os.path.join(BaseEnv.base_pack(), file_init)
        try:
            with open(a_file, "w") as fh:
                for x in os.environ:
                    if x in BaseEnv.LIST_OF_KEY:
                        fh.write("set_path(%r,%r)\n" % (x, os.environ.get(x)))
        except Exception as e:
            raise Exception("Cannot store file: %s" % e)

    def __path_exists(self, val):
        # check if all the items are path
        result = list()
        for x in val:
            if not x.startswith(os.sep):
                return val
        for x in val:
            if '%' in x:
                result.append(x)
            else:
                if os.path.exists(x):
                    result.append(x)
        return result

    def main_cleanup(self, clean_double=True, exist_only=True):
        SAVE_OS = dict()
        SAVE_OS.update(os.environ)

        needdump = False
        for key in os.environ:
            if key in BaseEnv.LIST_OF_KEY_EXCEPTION:
                continue
            values = os.environ[key].split(os.pathsep)
            if clean_double is True:
                temp = []
                for x in values:
                    if x not in temp:
                        temp.append(x)
                if len(values) != len(temp):
                    needdump = True
                values = temp

            if exist_only is True:
                temp = self.__path_exists(values)
                if len(values) != len(temp):
                    needdump = True
                values = temp
            if needdump:
                if len(values) == 0:
                    self.unsetPath(key)

                for x in reversed(values):
                    self.addPath(key, x)
        self.echo_environ_diff_only(SAVE_OS)
        return True
"""
##############################################################
# this is convenient class to build the remove directive
class MiniEnvUndo(dict):
    def __init__(self):
        self._currentKey = ""

    def unalias(self,k):pass
    def rmPack(self,apack):pass
    def addPack(self,apack):pass
    def rmPath(self,k,v):pass
    def unsetPath(self,k):pass
    def printEcho(self,k):pass
    def logfile(self,k):pass

    def alias(self,k,v):
        self[self._currentKey].append("add_unalias(%r)"%k)

    def addPath(self,k,v,at_end=False):
        assert self._currentKey != ""
        self[self._currentKey].append("rm_path(%r,%r)" % (k,v))

    def setPath(self,k,v):
        assert self._currentKey != ""
        self[self._currentKey].append("unset_path(%r)" % (k))

    def _evalCmd(self,stringOrFiledesc):
        locals().update({'add_path':self.addPath,
                         'set_path':self.setPath,
                         'rm_path':self.rmPath,
                         'unset_path':self.unsetPath,
                         'add_pack':self.addPack,
                         'rm_pack':self.rmPack,
                         'add_unalias':self.unalias,
                         'add_alias':self.alias,
                         'log_file': self.logfile,
                         'echo':self.printEcho})
        # exec or execfile, may need more introspection
        exec(stringOrFiledesc)

    def buildUndo(self, key, fileName):

        if os.sep in key:
            # we need to remove this
            # some how to preserve history on external path
            raise Exception("no os.sep in environment")
        if not key in self:
            self[key]=list()
        self._currentKey = key
        try:
            # self._evalCmd(open(fileName,"r"))
            # --- this is what need to be use later
            # for now we need to replace print with something else
            code = open(fileName,"r").read()
            code = code.replace("\\\n","")      # put split line on single line
            lines = code.split("\n")
            cleancode = list()
            for line in lines:
                if line.startswith("print "):
                    cleancode.append("echo(" + line[6:] + ")")
                else:
                    if line.strip() != "":
                        cleancode.append(line)
            self._evalCmd("\n".join(cleancode))
        except:
            #comment.error("reading or evaluating %r" % fileName)
            sys.stderr.write("reading or evaluating %r\n" % fileName)
            traceback.print_exc()
            return False
        # make it as string
        self[self._currentKey] = ";"+";".join(self[self._currentKey])
        return True
"""
