# -*- coding: utf-8 -*-
import os

from collections import namedtuple
from dskenv.base_env import BaseEnv
from dskenv.dskenv_constants import DSK_DEV_SHOW
from dskenv.api.envi_api import EnviApi


class ResultConfigInstall(namedtuple('confinstall', "path isdev default")):
    __slots__ = ()


class ApplicationData(namedtuple('appdata', "realexec label extstring")):
    """example "Nuke nukestudio"""
    __slots__ = ()


class ProjectShow(dict):
    """project config_and_pack info"""
    def __init__(self):
        super(ProjectShow, self).__init__()
        self.reset()

    def reset(self):
        self.project_name = ""
        self.path_configs = list()
        self.applications = list()

    def setdata(self, **adict):
        self.__dict__.update(adict)
        if isinstance(self.path_configs, str):
            self.path_configs = [self.path_configs]
        if self.project_name is None:
            self.project_name = ""
        if self.project_name != "":
            self.name = self.project_name
        # convert to application data
        try:
            self.applications = [
                ApplicationData(x[0], x[1], x[2]) for x in self.applications]
        except:
            self.applications = [
                ApplicationData(x[0], x[1], "") for x in self.applications]
        return self.is_valid()

    def get_name(self):
        return self.name

    def is_valid(self):
        """check if the basic requirement are met"""
        if (self.project_name != "" and
                isinstance(self.project_name, str) and
                isinstance(self.path_configs, list) and
                len(self.path_configs) > 0 and
                isinstance(self.applications, list)):
            for x in self.applications:
                if not isinstance(x, ApplicationData):
                    return False
            return True
        return False

    def get_applications(self):
        return [x.label for x in self.applications]

    def get_base_applications(self):
        return [x.realexec for x in self.applications]

    def get_applications_list(self):
        return self.applications


class DskStudio(EnviApi):
    """Read the main envi_info_location show
    This class is to regroup few definition that can be show dependent
    """

    __project_info = "projects"
    __app = "main_app"

    def __init__(self):
        super(DskStudio, self).__init__()
        self.project_list = list()
        self.application_list = list()

    def is_valid(self):
        return (len(self.project_list) > 0 and
                isinstance(self.application_list, list))

    def reset(self, envplace=""):
        """ For testing only """
        super(DskStudio, self).reset(envplace)
        self.project_list = list()
        self.application_list = list()

    def load_data(self):
        """Build object application (found in envi_info)
            :param None:
            :return None:
        """
        data = super(DskStudio, self).load_data()
        if self.__project_info in data:
            for x in data[self.__project_info]:
                a = ProjectShow()
                a.setdata(**x)
                # only update valid show_info
                if a.is_valid():
                    self.project_list.append(a)
        if self.__app in data:
            try:
                self.application_list = [
                    ApplicationData(
                        x[0], x[1], x[2]) for x in data[self.__app]]
            except:
                # case when application don't have extention
                self.application_list = [
                    ApplicationData(
                        x[0], x[1], "") for x in data[self.__app]]

        return data

    def get_projects(self):
        """list  (found in envi_info)
            :param None:
            :return list: application name list
        """

        return [x.get_name() for x in self.project_list]

    def get_applications(self, show_name=""):
        """Returns all application listed"""

        if show_name == "":
            return [x.label for x in self.application_list]
        for ch in self.project_list:
            if ch.get_name() == show_name:
                return ch.get_applications()
        return [x.label for x in self.application_list]

    def get_main_applications(self, show_name=""):
        """Returns all application root listed"""

        if show_name == "":
            return [x.realexec for x in self.application_list]
        for ch in self.project_list:
            if ch.get_name() == show_name:
                return ch.get_base_applications()
        return list(set([x.realexec for x in self.application_list]))

    def get_applications_list(self, show_name=""):
        """Returns all application root listed"""

        if show_name == "":
            return self.application_list
        for ch in self.project_list:
            if ch.get_name() == show_name:
                return ch.get_applications_list()
        return list(set(self.application_list))

    def get_application_obj(self, label):
        """Get application as object filter with label"""
        for x in self.get_applications_list():
            if x.label == label:
                return x
        return None

    def get_all_envlaunch(self, project_name="", users=None):
        """Return all possible config path

            :param project_name: str default ""
            :param users: default None
            :return config launch information:
            :rtype: ResultConfigInstall

        """
        result = list()

        if project_name == "":
            for ch in self.project_list:
                for pp in ch.path_configs:
                        if os.path.isdir(pp):
                            result.append(ResultConfigInstall(
                                pp, False, ch.get_name()))

        else:
            for ch in self.project_list:
                if ch.get_name() == DSK_DEV_SHOW:
                    for pp in ch.path_configs:
                        if os.path.isdir(pp):
                            result.append(ResultConfigInstall(
                                pp, False, "studio"))
                elif project_name == ch.get_name():
                    for pp in ch.path_configs:
                        if os.path.isdir(pp):
                            result.append(ResultConfigInstall(
                                pp, False, ch.get_name()))
        all_users = list()
        if users:
            if users == "all":
                all_users = self.get_all_user_login()
            else:
                if isinstance(users, str):
                    users = [users]
                all_users = users

        for user in all_users:
            pprojets = self.get_userdev_project(user)
            ppaths = self.get_userdev_config_path(user)
            if project_name in pprojets or project_name == "":
                for index, pp in enumerate(ppaths):
                    pp = os.path.expandvars(os.path.expanduser(pp))
                    if os.path.isdir(pp):
                        result.append(ResultConfigInstall(
                                        pp,
                                        True,
                                        user + "_xonfig%d" % index))

        if len(result) == 0:
            for x in BaseEnv.user_envi_home():
                result.append(ResultConfigInstall(x, True, "dev"))

        return result
