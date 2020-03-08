# -*- coding: utf-8 -*-
import os
from dskenv.api.envi_api import EnviApi
from dskenv.base_env import BaseEnv
from dskenv.proxy_env import ProdEnv
from dskenv.envi import Envi


class DskNaming(EnviApi):
    """ Main api to name pack and config base on show/app etc...
    """

    DefaultShow = "studio"
    DefaultApp = "shell"
    DefaultTd = "dev_show"
    # main version file
    Base_Version_Config = "%(show)s"
    Base_Version_Pack = "%(show)s_startup"

    Base_App_Default_Config = "%(app)s_default"

    Base_App_Inhouse_Config = "%(app)s"
    Base_Td_Pack = "%(show)s_td"

    Base_App_Plugin_Pack = "%(app)s_plugin"

    # generic name to set value in front
    Base_Prepath_Pack = "clean_prepath"

    # generic pack to overwrite value from base_show
    Base_Dev_Pack = BaseEnv.TD_OVERWRITE.replace(".py", "")

    # for sgtk
    Base_Sgtk_Pack = "studio_sgtk"

    def __init__(self):
        super(DskNaming, self).__init__()

    # SHOW_CONFIG
    @classmethod
    def get_base_platform_config(cls):
        """Entry point for envi when it knows project_name

            :param project_name: (str) a project sgtk name

            :return str:  the base config for that project
                (default 'studio' if empty)

        """
        return Envi.pack_system()

    # SHOW_CONFIG
    @classmethod
    def get_base_project_config(cls, project_name=""):
        """Entry point for envi when it knows project_name

            :param project_name: (str) a project sgtk name

            :return str:  the base config for that project
                (default 'studio' if empty)

        """
        if project_name != "":
            return cls.Base_Version_Config % {'show': project_name}
        return cls.Base_Version_Config % {'show': cls.DefaultShow}

    # SHOW_PACK
    @classmethod
    def get_base_version_pack(cls, project_name="", ):
        """Hold most of all version information (not directly use.
           include from project_config

            :param project_name: (str) a project sgtk name

            :return str:  the base pack for that project

        """
        if project_name != "":
            return cls.Base_Version_Pack % {'show': project_name}
        return cls.Base_Version_Pack % {'show': cls.DefaultShow}

    @classmethod
    def get_default_app_config(cls, app_name=""):
        """Include dsk proprietary software

            :param app_name: (str) an app name like maya, Nuke

            :return str: the inhouse (release, rigrelease and sgtkrelease)
                    config for that app (default 'shell' app if empty)

        """

        if app_name != "":
            return cls.Base_App_Default_Config % {'app': app_name.lower()}
        return cls.Base_App_Default_Config % {'app': cls.DefaultApp}

    @classmethod
    def get_inhouse_app_config(cls, app_name=""):
        """Include dsk proprietary software

            :param app_name: (str) an app name like maya, Nuke

            :return str: the inhouse (release, rigrelease and sgtkrelease)
                    config for that app (default 'shell' app if empty)

        """

        if app_name != "":
            return cls.Base_App_Inhouse_Config % {'app': app_name.lower()}
        return cls.Base_App_Inhouse_Config % {'app': cls.DefaultApp}

    # pluging app
    @classmethod
    def get_app_plugin_pack(cls, app_name=""):
        """Include third party software

        :param app_name:  (str) an app name like maya, Nuke
        :return str: the base config for that app
                    (default 'shell' app if empty)

        """
        if app_name != "":
            return cls.Base_App_Plugin_Pack % {'app': app_name.lower()}
        return cls.Base_App_Plugin_Pack % {'app': cls.DefaultApp}

    # TD
    @classmethod
    def get_td_project_pack(cls, project_name=""):
        """TD repo
            :param project_name: (str) a project sgtk name
            :return str: the td pack name
        """

        if project_name != "":
            return cls.Base_Td_Pack % {'show': project_name}
        return cls.Base_Td_Pack % {'show': cls.DefaultShow}

    #  PRE PATH
    @classmethod
    def get_prepath_pack(cls, project_name=""):
        """Procedural pack to insert PRE_PATH
        (PYTHONPATH and MAYA_SCRIPT_PATH in front of the value

            :param project_name: (str) optional
            :return str: A default pack name to prepend ?_PRE_PATH to ?

        """
        return cls.Base_Prepath_Pack

    #  DEV PACK BELONG TO SGTK PIPE CONFIGURATION
    @classmethod
    def get_overwrite_pack(cls, pipeconfig=""):
        """Overwrite pack to give user specific in dev repo or version
        and possibly extra value
        if pipeconfig is "",

            :param pipeconfig: a config pack name
            :return str: A default pack name

        """
        if pipeconfig == "":
            return cls.Base_Dev_Pack
        return os.path.join(pipeconfig,
                            "config",
                            cls.Base_Dev_Pack)

    @classmethod
    def get_studio_sgtk(cls, project_name="", app_name=""):
        """basic pack for sgtk

            :param    project_name: (str)
            :param    app_name: (str)

        """
        return cls.Base_Sgtk_Pack

    @classmethod
    def _get_default_envi_config(cls,
                                 project_name="",
                                 app_name="",
                                 sgtk_path="",
                                 with_system=False,
                                 with_sgtk=False,
                                 with_base=False,
                                 with_td=True):
        """Build a list of list of envi config and pack
            base on optional project or pack

            :param    project_name: (str)
            :param    app_name: (str)
            :param    sgtk_path: (path)
            :param    with_base: (bool) default= False, start with
                    config base_${project_name}

            :returns list: list of list containing option and envi tag

        """

        result = list()

        if with_system:
            res = list()
            # platform reset
            res.extend(["-p", cls.get_base_platform_config()])
            result.append(res)

        res = list()
        if with_base:
            res.extend(["-c", cls.get_base_project_config(project_name)])

        if sgtk_path != "":
            res.extend(["-p", cls.get_overwrite_pack(sgtk_path)])
        result.append(res)

        res = list()
        # res.extend(["-c", cls.get_inhouse_app_config(app_name)])
        res.extend(["-c", cls.get_default_app_config(app_name)])
        # res.extend(["-p", cls.get_app_plugin_pack(app_name)])
        if with_td:
            res.extend(["-p", cls.get_td_project_pack(project_name)])
        # res.extend(["-p", cls.get_prepath_pack()])
        if with_sgtk:
            res.extend(["-p", cls.get_studio_sgtk(project_name, app_name)])
        result.append(res)

        return result

    @classmethod
    def _get_initshow_envi_config(cls,
                                  project_name="",
                                  with_system=False,
                                  user_file=""):
        """Build a list of list of envi config
            and pack base on optional project or pack

            :params    project_name: (str)

        """
        result = list()

        if with_system:
            res = list()
            # platform reset
            res.extend(["-p", cls.get_base_platform_config()])
            result.append(res)

        res = list()

        res.extend(["-c", cls.get_base_project_config(project_name)])

        if user_file != "":
            res.extend(["-p", user_file])
        result.append(res)
        return result

    @staticmethod
    def _pairwise(iterable):
        """Couple single list element into double
        """
        a = iter(iterable)
        return zip(a, a)

    @classmethod
    def project_configuration(cls,
                              dskenvpath,
                              project_name="",
                              with_system=False,
                              user_file="",
                              user_login=""):
        """This is a query to return the basic configuration for a show

            :param    dskenvpath: envi config root
            :param    project_name: (str)
            :param    user_login: (str) default= ""
            :param    with_system = False
            :param    user_file: an optional user config

        """

        result = list()
        pr = ProdEnv(dskenvpath)
        res = list()
        if pr.is_valid():
            confpacks_list = cls._get_initshow_envi_config(
                                                project_name=project_name,
                                                with_system=with_system,
                                                user_file=user_file)

            for confpacks in confpacks_list:
                valid_command = list()
                res = list()
                for c_or_p, cp in cls._pairwise(confpacks):
                    if user_login != "":
                        valid_command.append("%s %s -D %s" % (c_or_p,
                                                              cp,
                                                              user_login))
                    else:
                        valid_command.append("%s %s" % (c_or_p,
                                                        cp))

                envi = Envi()
                envi.init_with_cmd(valid_command)
                valid_names = [
                    pp.base for pp in envi.configsObject + envi.packsObject]

                for c_or_p, cp in cls._pairwise(confpacks):
                    if cp in valid_names:
                        res.extend([c_or_p, cp])
                if len(res) > 0:
                    if user_login != "":
                        res.extend(['-D', user_login])

                    result.append(res)

        cleanresult = list()
        # clear empty list
        for x in result:
            if len(x) > 0:
                cleanresult.append(x)

        pr.back_to_global()
        return cleanresult

    @classmethod
    def configuration(cls,
                      dskenvpath,
                      project_name="",
                      app_name="",
                      sgtk_path="",
                      user_login="",
                      with_system=False,
                      with_sgtk=False,
                      with_base=False,
                      with_td=True):
        """Same as get_default_envi_config but add configs
            if they exists only Also add user option

            :param    dskenvpath: envi config root
            :param    project_name: (str)
            :param    app_name: (str)
            :param    sgtk_path: (path) default = ""
            :param    user_login: (str) default = ""
            :param    with_base: (bool) default=False
                        start with config project_name
            :param    with_system: (bool) default=False
                        add platform specific default
            :param    with_sgtk: (bool) add the studio pack

        """

        pr = ProdEnv(dskenvpath)
        result = list()
        if pr.is_valid():
            confpacks_list = cls._get_default_envi_config(
                                                project_name=project_name,
                                                app_name=app_name,
                                                sgtk_path=sgtk_path,
                                                with_system=with_system,
                                                with_sgtk=with_sgtk,
                                                with_base=with_base,
                                                with_td=with_td)

            for confpacks in confpacks_list:
                valid_command = list()
                res = list()
                for c_or_p, cp in cls._pairwise(confpacks):
                    if user_login != "":
                        valid_command.append("%s %s -D %s" % (c_or_p,
                                                              cp,
                                                              user_login))
                    else:
                        valid_command.append("%s %s" % (c_or_p, cp))
                envi = Envi()
                envi.init_with_cmd(valid_command)
                valid_names = [
                    pp.base for pp in envi.configsObject + envi.packsObject]

                for c_or_p, cp in cls._pairwise(confpacks):
                    if cp in valid_names:
                        res.extend([c_or_p, cp])
                if user_login != "" and len(res) > 0:
                    res.extend(['-D', user_login])
                result.append(res)

        cleanresult = list()
        # clear empty list
        for x in result:
            if len(x) > 0:
                cleanresult.append(x)

        pr.back_to_global()
        return cleanresult
