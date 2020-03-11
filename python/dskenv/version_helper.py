# -*- coding: utf-8 -*-
import os
import re
from dskenv.envi_utils import EnviUtils
import functools

class VersionHelper(object):
    _parse = re.compile(r"(.*)-(\d+)\.*(\d*)$")

    def __init__(self, name, ext=".py"):

        self._ext = ext
        self.name = name.replace(self._ext, "")
        self.major = -1
        self.minor = -1
        m = VersionHelper._parse.search(self.name)
        if m:
            self.base = m.group(1)
            if m.group(2) != '':
                self.major = int(m.group(2))
            if m.group(3) != '':
                self.minor = int(m.group(3))
        elif self.name.endswith("-"):
            # version 0.0
            self.base = self.name[:-1]
        else:
            # unversioned pattern
            self.base = self.name

    def is_versioned(self):
        return len(self.base) != len(self.name)

    def version_string(self):
        if self.is_versioned():
            if self.major == -1:
                return "-"
            else:
                if self.minor != -1:
                    return "%s.%s" % (self.major, self.minor)
                else:
                    return "%s" % (self.major)
        return ""

    def format(self):
        if self.is_versioned():
            if self.minor == -1 and self.major != -1:
                return "%s-%d%s" % (self.base, self.major, self._ext)
            if self.major == -1:
                return self.name + self._ext
            return "%s-%d.%d%s" % (self.base,
                                   self.major, self.minor, self._ext)
        return self.name + self._ext

    def is_valid(self):
        if self.is_versioned():
            return self.major != -1
        return self.name != ""

    def is_similar(self, realVersion):
        """
        realVersion means that the name exist on disk
        a version with none define major-minor
        """
        if self.name == realVersion.name:
            return True
        if self.base != realVersion.base:
            return False
        if not realVersion.is_versioned():
            return True
        if self.major != -1 and self.major != realVersion.major:
            return False
        if self.minor != -1 and self.minor != realVersion.minor:
            return False
        return True

    @staticmethod
    def compare_version(o1, o2):
        """C like compare if equal-> 0, > -> 1 else -1
        """
        # too slow: return cmp(float("%d.%d" % (o1.major,o2.minor)),
        # float("%d.%d" % (o2.major,o2.minor)))
        if o1.major > o2.major:
            return 1
        if o1.major == o2.major:
            if o1.minor > o2.minor:
                return 1
            elif o1.minor == o2.minor:
                return 0
        return -1

    @staticmethod
    def clean_path_dir(path):
        """Convenience to get the path directory
        """
        if not os.path.isdir(path):
            path = os.path.split(path)[0]
        # remove potential sep at the end
        if path[-1] == os.sep:
            return path[:-1]
        return path

    def get_file(self, path, clip_time=-1):
        """When a version has wild version clip_time (a timestamp), let you
        filter the research to only the file that are old enough
        """
        import glob

        if path == "":
            return ""
        if not self.is_versioned():
            pathname = os.path.join(path, self.name)
            # no search
            pathnametest = pathname + self._ext
            if os.path.isfile(pathnametest):
                return pathnametest

        elif self.major != -1:
            pathname = os.path.join(path, self.base + "-%d" % self.major)
            if self.minor != -1:
                pathnametest = pathname + ".%d%s" % (self.minor, self._ext)
                if os.path.isfile(pathnametest):
                    return pathnametest
                return ""
        else:
            # both are unknown
            pathname = os.path.join(path, "%s-" % self.base)

        allFile = glob.glob(pathname+"*%s" % self._ext)
        if clip_time != -1:
            allFile = EnviUtils.clip_time_files(allFile, clip_time)
        if len(allFile) == 0:
            return ""
        verList = list()
        for f in allFile:
            verList.append(VersionHelper(os.path.split(f)[1]))

        verList = sorted(verList, key=functools.cmp_to_key(
                                        VersionHelper.compare_version))
        return os.path.join(path, verList[-1].name + self._ext)

    def version_up(self):
        if self.is_versioned():
            self.major += 1
            self.minor = 0
        else:
            self.name = self.name+"-0.0"
            self.major = 0
            self.minor = 0

    def version_up_minor(self):
        if self.is_versioned():
            self.minor += 1
        else:
            self.major = 0
            self.minor = 0
            self.name = self.name+"-0.0"

    def unversioned(self):
        self.name = self.base
