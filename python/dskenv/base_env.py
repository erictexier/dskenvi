# -*- coding: utf-8 -*-
""" MODULE base_env """

import os
import re
import types
import getpass
import platform
from collections import namedtuple
from dskenv import dskenv_constants


class CANDPInfo(namedtuple('c_and_p_info', "full_path is_user is_pack valid")):
    __slots__ = ()

# just for info
inUse = ['_BASE_CURRENT_PACKAGES',
         '_BASE_CURRENT_CONFIGS',
         ':USERDIR_VERSION',
         '__BASE_PACKAGE_DIR',
         '_BASE_COMMAND',
         '_ENVI_CACHE'
         'MAIN']

extraKey = ['_UNDOC',
            '_UNDOP']

keyEnvi = ['_BASE_CURRENT_PACKAGES', '_BASE_CURRENT_CONFIGS', '_BASE_COMMAND']


def get_home_user():
    """Warning about none user login
    """
    ex = os.path.expanduser("~")
    return ex


def uname():
    return platform.uname()


def getOs():
    import sys
    pos = platform.system()
    if pos == 'Microsoft':
        if sys.platform == 'win32':
            return 'Windows'
    return pos

DIRTOPUSER = get_home_user()
DIRTOPUSER = os.path.split(DIRTOPUSER)[0]


class BaseEnv(object):
    """A dynamic configuration for basic file on the system
    Show specific are not handle (required a different tool set for now)
    """
    __STUDIO_ROOT = os.environ.get('DSK_STUDIO_ROOT', "")
    if __STUDIO_ROOT == "":
        __STUDIO_ROOT = "%s%s" % (os.sep, dskenv_constants.DSK_MOUNTED_ROOT)
    _CACHE_KEY = "_ENVI_CACHE"
    pathconfig = os.environ.get(dskenv_constants.DSK_ENV_PATH_KEY, None)
    if pathconfig in ['', None]:
        # second look for config in this repo root
        __BASE_PACKAGE_DIR = os.environ.get(dskenv_constants.DSK_PATH_KEY,
                                            None)
    else:
        __BASE_PACKAGE_DIR = pathconfig

    __INIT_VALUE = __BASE_PACKAGE_DIR

    if __BASE_PACKAGE_DIR in [None, ""]:
        raise Exception("Not supported")

    __DEV_AREA = os.path.join(__STUDIO_ROOT,
                              dskenv_constants.DSK_DEV_AREA)

    assert os.path.exists(__STUDIO_ROOT)
    commandsep = "@"
    __envi_root = dskenv_constants.DSK_ENVI_INFO_DIR
    __envi_file = dskenv_constants.DSK_ENVI_INFO_FILENAME
    __base_envi_file = os.path.join(os.environ.get(
                                        dskenv_constants.DSK_ENV_PATH_KEY),
                                    __envi_root,
                                    __envi_file)

    # project level
    project_path_root = os.environ.get('PROJECT_PATH', "")
    TD_OVERWRITE = "startup_overwrite.py"
    LIST_OF_KEY_EXCEPTION = set(['WINDOWID',
                                 'KONSOLE_DBUS_SESSION',
                                 'KONSOLE_DBUS_WINDOW',
                                 'SESSION_MANAGER',
                                 'SHELL_SESSION_ID',
                                 'GPG_TTY',
                                 'SSH_AGENT_PID',
                                 'HOSTNAME',
                                 'MAIL',
                                 'KDE_SESSION_VERSION',
                                 'KDE_SESSION_UID',
                                 'SSH_AUTH_SOCK',
                                 'KONSOLE_DBUS_SERVICE',
                                 'GTK2_RC_FILES',
                                 'WINDOWPATH',
                                 'DISPLAY'])

    LIST_OF_KEY = set(['PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH'])

    #  show dependent
    @classmethod
    def studio_root(cls):
        return cls.__STUDIO_ROOT

    @classmethod
    def get_dev_area(cls):
        return cls.__DEV_AREA

    @classmethod
    def envi_info_location(cls):
        return cls.__base_envi_file

    @classmethod
    def envi_file_name(cls):
        return cls.__envi_file

    @classmethod
    def envi_iddir(cls):
        return cls.__envi_root

    #  for config
    __packAndConfig = os.path.join(__BASE_PACKAGE_DIR, __envi_root)
    __configDir = "configs"
    __packDir = "packs"

    __UserPlacePatern = re.compile(r'^(%s/)([\w\d]*)(/\.%s/)' % (
                                DIRTOPUSER, dskenv_constants.DSK_ENVI_FOLDER))
    __endPlacePack = re.compile('%s$|%s/$' % (__packDir, __packDir))
    __endPlaceConfig = re.compile('%s$|%s/$' % (__configDir, __configDir))

    #  this 'config' is used below to build dev path(see  user_envi_home)
    __validDevConfig = re.compile(r'%s%s[\w\d/]*%s%s' % (__DEV_AREA,
                                                         os.sep,
                                                         os.sep,
                                                         __envi_root))
    _undoPackageKey = '_UNDOP'
    _undoConfigkey = '_UNDOC'
    _envKey = '_ENVI'

    COMPILED_PLACE = os.path.join(__BASE_PACKAGE_DIR, "compiledConfigs")
    COMPILED_JSON = ".metadata.json"
    COMPILED_ENVDATA = "envData"

    def __init__(self):
        pass

    @staticmethod
    def _reset(new_env_path):
        if new_env_path != "":
            """set with a user dev value"""
            BaseEnv.__BASE_PACKAGE_DIR = new_env_path
            os.environ.update({
                            dskenv_constants.DSK_ENV_PATH_KEY: new_env_path})
            BaseEnv.__base_envi_file = os.path.join(
                                        os.environ.get(
                                            dskenv_constants.DSK_ENV_PATH_KEY),
                                        BaseEnv.__envi_root,
                                        BaseEnv.__envi_file)
            BaseEnv.__packAndConfig = os.path.join(BaseEnv.__BASE_PACKAGE_DIR,
                                                   BaseEnv.__envi_root)
        else:
            """Reset with init value"""
            BaseEnv.__BASE_PACKAGE_DIR = BaseEnv.__INIT_VALUE
            BaseEnv.__packAndConfig = os.path.join(BaseEnv.__BASE_PACKAGE_DIR,
                                                   BaseEnv.__envi_root)
            os.environ.update({
                dskenv_constants.DSK_ENV_PATH_KEY: BaseEnv.__INIT_VALUE})
            BaseEnv.__base_envi_file = os.path.join(
                                        os.environ.get(
                                            dskenv_constants.DSK_ENV_PATH_KEY),
                                        BaseEnv.__envi_root,
                                        BaseEnv.__envi_file)

    @classmethod
    def get_package_dir(cls):
        return cls.__BASE_PACKAGE_DIR

    @classmethod
    def get_package_env_dir(cls):
        return os.path.join(cls.__BASE_PACKAGE_DIR, cls.__envi_root)

    @classmethod
    def clean(cls, PorCname):
        return PorCname.replace(':USERDIR_VERSION', "")

    @classmethod
    def shorten(cls, alist):
        clean = list()
        r = cls.base_pack()
        for i in alist:
            clean.append(i.replace(r, 'MAIN'))
        return clean

    @classmethod
    def base(cls):
        return cls.__packAndConfig

    @classmethod
    def config_tag(cls):
        return cls.__configDir

    @classmethod
    def compiled_json(cls, configName):
        return os.path.join(cls.COMPILED_PLACE, configName, cls.COMPILED_JSON)

    @classmethod
    def short_path(cls, configName, varname):
        return os.path.join(cls.COMPILED_PLACE, configName, varname)

    @classmethod
    def pack_tag(cls):
        return cls.__packDir

    @classmethod
    def base_config(cls):
        return os.path.join(cls.base(), cls.__configDir)

    @classmethod
    def base_pack(cls):
        return os.path.join(cls.base(), cls.__packDir)

    @classmethod
    def user_home(cls, user):
        return os.path.join(DIRTOPUSER,
                            user,
                            "." + dskenv_constants.DSK_ENVI_FOLDER)

    @classmethod
    def user_path_config(cls):
        def yload_data(a_file):

            data = {}
            try:
                import yaml
                with open(a_file, "rt") as fh:
                    data = yaml.load(fh, Loader=yaml.FullLoader)
            except Exception as e:
                raise Exception("Cannot parse yml file: %s" % e)
            return data

        afile = cls.envi_info_location()
        alldev = list()
        data = yload_data(afile)
        ALL = data["dev_user"]
        for a in ALL:
            # loop over all the found user in the file
            if 'dev_path_configs' in a:
                x = os.path.expandvars(os.path.expanduser(
                                                a['dev_path_configs']))
                alldev.append(x)
        return alldev

    @classmethod
    def user_envi_home(cls, user=""):
        """Build a dev area config place for dev
        """

        if user == "":
            user = getpass.getuser()
        keyuser = os.path.join(
                            user,
                            dskenv_constants.DSK_CONFIGURATION_FOLDER,
                            dskenv_constants.DSK_ENVI_FOLDER)
        default = [os.path.join(cls.__DEV_AREA, keyuser, cls.__envi_root)]
        return list(set(default + cls.user_path_config()))

    @classmethod
    def is_possible_user_dev(cls, apath):
        return apath.startswith(cls.__DEV_AREA)

    @classmethod
    def get_key_pack_info(cls):
        return '_BASE_CURRENT_PACKAGES'

    @classmethod
    def get_key_config_info(cls):
        return '_BASE_CURRENT_CONFIGS'

    @classmethod
    def get_command_info(cls):
        return '_BASE_COMMAND'

    @classmethod
    def pack_info(cls, replaceMain=True):
        """Return a list of tuple with the name of the variable and the file
           is come from. MAIN is replace with getBase('packs')
        """
        res = list()  # we need a list to keep the order
        currentPackage = os.environ.get('_BASE_CURRENT_PACKAGES')

        if currentPackage is None:
            return res
        currentPackage = currentPackage.split(os.pathsep)
        currentPackage = [_f for _f in currentPackage if _f]
        apath = cls.base_pack()

        for pack in currentPackage:
            if replaceMain:
                pack = pack.replace("MAIN", apath)
            res.append([os.path.split(pack)[1], pack])
        return res

    @classmethod
    def config_info(cls, replaceMain=True):
        """Same as getPackInfo for package
        """
        res = list()  # we need a list to keep the order
        currentConfig = os.environ.get('_BASE_CURRENT_CONFIGS')

        if currentConfig is None:
            return res
        currentConfig = currentConfig.split(os.pathsep)
        # remove empty string
        currentConfig = [_f for _f in currentConfig if _f]
        apath = cls.base_config()

        for config in currentConfig:
            if replaceMain:
                config = config.replace("MAIN", apath)
            res.append([os.path.split(config)[1], config])

        return res

    @classmethod
    def pack_history(cls, env_root):
        """Create a list of -p pack (option -D)"""
        res = list()  # we need a list to keep the order
        currentPackage = os.environ.get('_BASE_CURRENT_PACKAGES')

        if currentPackage is None:
            return res
        currentPackage = currentPackage.split(os.pathsep)
        currentPackage = [_f for _f in currentPackage if _f]

        for pack in currentPackage:
            pname = os.path.basename(pack)
            if cls.TD_OVERWRITE == pname:
                res.append(pack.replace(".py", ""))
            else:
                pname = pname.replace(".py", "")
                pdir = os.path.dirname(pack)
                if pdir == "MAIN" or env_root.startswith(pdir):
                    res.append(pname)
                else:
                    user = cls.is_env_user(pack)
                    if user != "":
                        res.append(pname + " -D %s" % user)
                    else:
                        res.append(os.path.join(pdir, pname))
        res = ["-p %s" % x for x in res]
        return res

    @classmethod
    def command_history(cls):
        """Create a list preview"""
        res = list()  # we need a list to keep the order
        currentcmd = os.environ.get('_BASE_COMMAND')

        if currentcmd is None:
            return res
        currentcmd = currentcmd.split(cls.commandsep)
        currentcmd = [_f for _f in currentcmd if _f]
        return currentcmd

    @classmethod
    def get_cleanup_cmd(cls):
        found = list()
        for var in os.environ:
            if var.startswith(BaseEnv._undoPackageKey):
                # has a hack to support partially the new interface remove
                # leading compiled config
                noCompile = os.environ[var]
                f = noCompile.find("|")
                if f != -1:
                    noCompile = noCompile[f+1:]
                found.extend(noCompile.split(";"))

        return found

    @classmethod
    def get_filter_var(cls, afilter):
        found = dict()
        for var in afilter:
            if var in os.environ:
                found[var] = os.environ[var].split(os.pathsep)
        return found

    @classmethod
    def is_release_path_config(cls, path):
        """hose test are strict,
            return false with any leading character
        """
        assert path not in (str,)
        return path == cls.base_config()

    @classmethod
    def is_release_path_pack(cls, path):
        assert path not in (str,)
        return path == cls.base_pack()

    @classmethod
    def is_env_user(cls, path):
        assert path not in (str,)
        m = BaseEnv.__UserPlacePatern.match(path)
        if m:
            return m.group(2)  # return user name
        return ""

    @classmethod
    def is_custom_path_config(cls, path):
        assert path not in (str,)
        return (not cls.is_release_path_config(path) and
                cls.is_env_user(path) == "")

    @classmethod
    def is_custom_path_pack(cls, path):
        assert path not in (str,)
        return (not cls.is_release_path_pack(path) and
                cls.is_env_user(path) == "")

    @classmethod
    def get_sgtk_place(cls):
        """Look for a sgtk config location
        """
        asgtk = os.environ.get('TANK_CURRENT_PC', None)
        if asgtk in ['', None]:
            return ""
        startup_path = os.path.join(asgtk, 'config')
        if not os.path.exists(startup_path):
            return ""
        return startup_path

    @classmethod
    def is_sgtk_place_dev(cls):
        """Look if sgtk location has dev
        """
        asgtk = os.environ.get('TANK_CURRENT_PC', None)
        if asgtk in ['', None]:
            return False
        return dskenv_constants.DSK_DEV_AREA in asgtk

    @classmethod
    def sgtk_context_to_json(cls):
        """Store the Sgtk Context serialize to go over some escape
           not supported by os
        """
        try:
            import sgtk
            import base64
            import json
            sgtk_ctx = os.environ.get("TANK_CONTEXT", None)
            os.environ['TANK_CONTEXT'] = ""
            context = sgtk.context.deserialize(sgtk_ctx)

            dict_context = dict()
            dict_context['project'] = context.project
            dict_context['entity'] = context.entity
            dict_context['step'] = context.step
            dict_context['task'] = context.task
            dict_context['user'] = context.user
            dict_context['additional_entities'] = context.additional_entities
            os.environ['TANK_CONTEXT_JSON'] = base64.encodestring(
                                                json.dumps(dict_context))
        except:
            pass

    @classmethod
    def sgtk_restaure_context(cls):
        """From json (in TANK_CONTEXT_JSON) to pickle (TANK_CONTEXT)
        """
        try:
            import sgtk
            import base64
            import json
            sgtk_ctx_env = os.environ.get("TANK_CONTEXT_JSON", None)
            if sgtk_ctx_env not in [None, ""]:
                x = base64.decodestring(sgtk_ctx_env)
                d_sgtk = json.loads(x)
                from sgtk.context import Context
                ctx = Context(d_sgtk)
                os.environ['TANK_CONTEXT'] = sgtk.context.serialize(ctx)

        except Exception as e:
            print((str(e)))

    @classmethod
    def __list_and_valid_cnp(cls, rootpath):
        from dskenv.mini_env import MiniEnv
        try:
            allfiles = os.listdir(rootpath)
        except:
            return list(), list()
        with_py = [x for x in allfiles if x.endswith(".py")]
        # later with can check if valid with miniEnv.load_config_or_pack
        full = [os.path.join(rootpath, x) for x in with_py]
        final_valid = list()
        final_notvalid = list()
        for f in full:
            m = MiniEnv()
            try:
                if m.load_config_or_pack(f):
                    final_valid.append(f)
            except:
                final_notvalid.append(f)
        return final_valid, final_notvalid

    @classmethod
    def get_all_valid_config_and_packs(cls):
        """
            :param None:
            :return: all the file config and packs found in
             release (ENVPATH) and user

        """
        saveos = dict()
        saveos.update(os.environ)
        confs = BaseEnv.base_config()
        fn, failed = cls.__list_and_valid_cnp(confs)
        all_found = [CANDPInfo(x, False, False, True) for x in fn]
        all_found.extend([CANDPInfo(x, False, False, False) for x in failed])

        packs = BaseEnv.base_pack()
        fn, failed = cls.__list_and_valid_cnp(packs)
        all_found.extend([CANDPInfo(x, False, True, True) for x in fn])
        all_found.extend([CANDPInfo(x, False, True, False) for x in failed])

        uh = BaseEnv.user_home(getpass.getuser())
        confs = os.path.join(uh, BaseEnv.config_tag())
        fn, failed = cls.__list_and_valid_cnp(confs)
        all_found.extend([CANDPInfo(x, True, False, True) for x in fn])
        all_found.extend([CANDPInfo(x, True, False, False) for x in failed])

        confs = os.path.join(uh, BaseEnv.pack_tag())
        fn, failed = cls.__list_and_valid_cnp(confs)
        all_found.extend([CANDPInfo(x, True, True, True) for x in fn])
        all_found.extend([CANDPInfo(x, True, True, False) for x in failed])

        dd = list(os.environ.keys())
        for i in dd:
            os.environ.pop(i)
        os.environ.update(saveos)
        return all_found

    @classmethod
    def release_confpack(cls, c):
        """
          :param c: from in user area
          :type CANDPInfo: see CANDPInfo
          :return CANDPInfo: to be copied to

        """
        if not c.is_user:
            return c
        ispack = True
        if c.is_pack:
            base = BaseEnv.base_pack()
        else:
            ispack = False
            base = BaseEnv.base_config()
        new_path = os.path.join(base, os.path.basename(c.full_path))
        if os.path.isfile(new_path):
            return CANDPInfo(new_path, False, ispack, True)
        else:
            return CANDPInfo(new_path, False, ispack, False)

    @classmethod
    def user_confpack(cls, c):
        """
          :param c: CANDPInfo in release area

          :return CANDPInfo: to be copied to

        """
        if c.is_user:
            return c
        ispack = True

        uh = BaseEnv.user_home(getpass.getuser())
        if c.is_pack:
            base = os.path.join(uh, BaseEnv.pack_tag())
        else:
            base = os.path.join(uh, BaseEnv.config_tag())
            ispack = False

        new_path = os.path.join(base, os.path.basename(c.full_path))
        if os.path.isfile(new_path):
            return CANDPInfo(new_path, True, ispack, True)
        else:
            return CANDPInfo(new_path, True, ispack, False)
