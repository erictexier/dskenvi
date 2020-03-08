# -*- coding: utf-8 -*-
import os
from dskenv.version_helper import VersionHelper
from dskenv.base_env import BaseEnv


class BaseConfigPack(VersionHelper):

    def __init__(self, name, path=None):
        super(BaseConfigPack, self).__init__(name)
        self.path = path
        if path:
            self.path = self.clean_path_dir(path)

    @staticmethod
    def get_label():
        return 'configOrPack'   # this need to be overwritten

    def owner(self):
        """Return the owner name
        """

        if self.path:
            return BaseEnv.is_env_user(self.path)
        return ""

    def is_dev(self):
        """Return True is the path is under envi userpath
        """
        if self.path:
            return BaseEnv.is_env_user(self.path) != ""
        return False

    def get_fullname(self):
        if self.path is None:
            return self.format()
        return os.path.join(self.path, self.format())

    def real_version_file(self, factory, placeAlt=None, clip_time=-1):
        """RealVersion is an existing version on disk
            and for versioned name they have no more
            unknown major or minor.
        - factory is a class or type config or pack
        - placeAlt a list of other place to consider
        - version can be not fully-formed to allow
            for getting the most recent file
        """
        assert factory is not None
        if self.path and self.path != "":
            pathname = self.get_file(self.path, clip_time)
            if pathname != "":
                apath, versionName = os.path.split(pathname)
                return factory(versionName, apath)

        # if not found let look other place
        otherPlaces = list()
        if placeAlt:
            for u in placeAlt:
                otherPlaces.append(os.path.join(u, self.get_label()))

        # first check for the exact name
        #  we try to get with the exact path
        if not self.is_versioned() and clip_time == -1:
            for newPath in otherPlaces:
                pathname = os.path.join(newPath, self.format())
                if os.path.isfile(pathname):
                    return factory(self.format(), newPath)

        for newPath in otherPlaces:
            pathname = self.get_file(newPath, clip_time)
            if pathname != "":
                apath, versionName = os.path.split(pathname)
                return factory(versionName, apath)
        return None
