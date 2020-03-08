# -*- coding: utf-8 -*-
import os
import glob
import re
# Semantic versioning


class DirVersioned(object):
    _parse = re.compile(r"(\d+)\.*(\d*)\.*(\d*)$")

    def __init__(self, name):

        self.name = name
        self.major = -1
        self.minor = -1
        self.patch = -1
        m = self._parse.search(self.name)
        if m:
            self.base = self.name.replace(m.group(0), "")
            if m.group(1) != '':
                self.major = int(m.group(1))
            if m.group(2) != '':
                self.minor = int(m.group(2))
            if m.group(3) != '':
                self.patch = int(m.group(3))

        else:
            # unversioned pattern
            self.base = self.name

    def is_versioned(self):
        return len(self.base) != len(self.name)

    def version_string(self):
        if self.is_versioned():
            if self.major == -1:
                return ""
            if self.minor == -1:
                return "%s" % self.major
            elif self.patch == -1:
                return "%s.%s" % (self.major, self.minor)
            else:
                return "%s.%s.%s" % (self.major, self.minor, self.patch)
        return ""

    def format(self):
        if self.is_versioned():
            return "{}{}".format(self.base, self.version_string())
        return self.name

    def is_valid(self):
        if self.is_versioned():
            return self.major != -1
        return self.name != ""

    def inc_major(self):
        if self.major > -1:
            self.major += 1
            return True
        return False

    def inc_minor(self):
        if self.major > -1:
            self.minor += 1
            return True
        return False

    def inc_patch(self):
        if self.major > -1 and self.minor > -1:
            self.patch += 1
            return True
        return False

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
            if o1.minor == o2.minor:
                if o1.patch > o2.patch:
                    return 1
                if o1.patch == o2.patch:
                    return 0
        return -1
