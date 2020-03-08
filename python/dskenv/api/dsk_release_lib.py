# -*- coding: utf-8 -*-
import os
import sys
from dskenv.api.envi_api import EnviApi


repo_template = """
  -  name: %(name)s
     new_version: %(new_version)s
     do_version: %(do_version)s
     pack_update: %(pack_update)s
     do_current: false
     alternative_release_areas: %(alternative_release_areas)s
     shortname: %(shortname)s
     location:
       path: %(path)r
       type: git
       branch: %(branch)r
"""


class RepoInstall(dict):
    """Repo description for self install """

    __mode_supported = ['tag']
    __repo_supported = ['git']

    def __init__(self):
        super(RepoInstall, self).__init__()
        self.reset()

    def setdata(self, **adict):
        self.__dict__.update(adict)
        if self.shortname == "":
            self.shortname = self.name
            self.shortname = self.shortname.replace(os.sep, "_")
        if self.location['branch'] is None:
            self.location['branch'] = ""
        if self.alternative_release_areas is None:
            self.alternative_release_areas = list()
        if isinstance(self.alternative_release_areas, str):
            self.alternative_release_areas = [self.alternative_release_areas]

        self.alternative_release_areas = [os.path.expandvars(
                os.path.expanduser(x))for x in self.alternative_release_areas]

    def reset(self):
        self.new_version = False   # to increment automatically the version
        self.do_version = False
        self.pack_update = False
        self.shortname = ""
        self.location = dict()
        self.location['path'] = ""
        self.location['type'] = ""
        self.location['branch'] = ""
        self.do_current = False
        self.alternative_release_areas = list()
        self.name = ""

    def is_valid(self):
        if(isinstance(self.new_version, bool) and
                isinstance(self.do_version, bool) and
                isinstance(self.pack_update, bool) and
                self.shortname != "" and
                isinstance(self.location['path'], str) and
                self.location['path'] != "" and
                self.location['type'] in self.__repo_supported and
                isinstance(self.location['branch'], str) and
                isinstance(self.name, str) and
                isinstance(self.alternative_release_areas, list) and
                self.name != ""):
            return True

    def get_alt_release(self):
        """Return the first alt release of now"""
        if len(self.alternative_release_areas) > 0:
            return self.alternative_release_areas[0]
        return ""

    def get_alt_releases(self):
        """Return all places to install repo"""
        if len(self.alternative_release_areas) > 0:
            return self.alternative_release_areas[0]
        return ""

    def write(self, fstream):
        astring = repo_template % self.__dict__
        astring = astring.replace(" False ", " false ")
        astring = astring.replace(" True ", " true ")
        fstream.write(astring)

    def do_current(self):
        return self.do_current


class DskReleaseLib(EnviApi):
    """Read the main envi_info_location for repo """

    __repo_info = "repo_info"

    def __init__(self):
        super(DskReleaseLib, self).__init__()
        self.mainrelease = ""
        self.site = {}
        self.repo_info = list()

    def reset(self, envplace=""):
        """ For testing only """
        super(DskReleaseLib, self).reset(envplace)
        self.mainrelease = ""
        self.site = {}
        self.repo_info = list()
        self.default_install = list()

    def is_valid(self):
        return (len(self.repo_info) > 0 and
                len(self.dev_user) > 0 and
                len(self.site['name']) and
                self.mainrelease != "" and
                os.path.isdir(self.mainrelease) and
                isinstance(self.default_install, list))

    def load_data(self):
        data = super(DskReleaseLib, self).load_data()

        if 'default_install' in data:
            self.default_install = data['default_install']
        # make sure is a list
        if isinstance(self.default_install, str):
            self.default_install = list(self.default_install)

        if 'mainrelease' in data:
            self.mainrelease = data['mainrelease']
        self.mainrelease = os.path.expandvars(
                            os.path.expanduser(self.mainrelease))
        if not os.path.isdir(self.mainrelease):
            sys.stderr.write("Directory {} needs to exists\n".format(
                                                            self.mainrelease))

        if self.__repo_info in data:
            # load repo_info
            for x in data[self.__repo_info]:

                a = RepoInstall()
                a.setdata(**x)
                # only update valid repo_info
                if a.is_valid():
                    self.repo_info.append(a)
                else:
                    print("not valid repo", a)
        return True

    # #########################################################################
    # QUERY

    def main_release_area(self):
        """Return the release area """
        return self.mainrelease

    def default_repo_to_install(self):
        """Return default repo name"""
        return self.default_install

    # #########################################################################
    # QUERY REPO
    def short_name_repo(self, repo_name):
        """Return the short name of a repo
        """
        for x in self.repo_info:
            if x.name == repo_name:
                return x.shortname
        return ""

    def name_repo(self, short_name):
        """Return the short name of a repo
        """
        for x in self.repo_info:
            if x.shortname == short_name:
                return x.name
        return ""

    def valid_name(self, aname):
        """Glue to locate repo_name with short name"""

        for x in self.repo_info:
            if x.name == aname or x.shortname == aname:
                return x.name
        return ""

    def descriptor_repo(self, short_or_long):
        """Return a descriptor (in sgtk language to the git)

            :param short_or_long:  (str). name of nick name for the repo
            :return location: (dict) ex: { path: 'git@gitlab...foo...git',
                                    type: 'git'
                                    branch: ''}
        """
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.location
        return dict()

    def repo_do_newversion(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long and hasattr(x, "new_version"):
                return x.new_version
            elif x.name == short_or_long and hasattr(x, "new_version"):
                return x.new_version
        return False

    def repo_do_pack(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.pack_update
        return False

    def repo_do_version(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.do_version
        return False

    def repo_do_current(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.do_current
        return False

    def get_alt_release_area(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.get_alt_release()
        return ""

    def get_alt_release_areas(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x.get_alt_releases()
        return list()

    def repo_obj(self, short_or_long):
        for x in self.repo_info:
            if x.shortname == short_or_long or x.name == short_or_long:
                return x
        return None
