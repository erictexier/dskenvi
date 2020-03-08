# -*- coding: utf-8 -*-
import os
import sys
import stat
import datetime
import time


class EnviUtils(object):
    """A collection of util for this module
    """
    @staticmethod
    def create_path(fullPath):
        try:
            os.mkdir(fullPath)
            return True
        except:
            return False

    @classmethod
    def create_path_rec(cls, fullPath):
        """ create all the needed directory
        if an extension exist will not considered
        the last field as a dir but as a filename
        """
        if os.path.exists(fullPath):
            return True
        p, ext = os.path.splitext(fullPath)
        toCreate = ""
        if ext != "":
            # the last field is file we will not create it as a directory
            toCreate = os.path.split(p)[0]
        else:
            toCreate = p

        # build the parent directory
        par = os.path.split(toCreate)[0]
        if cls.create_path_rec(par):
            if not os.path.exists(toCreate):
                cls.create_path(toCreate)
        return True

    @classmethod
    def clip_time_files(cls, listOfFile, atime):
        """ list of for file on disk
        """
        return [x for x in listOfFile if cls.get_time(x) < atime]

    ##################
    @classmethod
    def clip_time_files_sorted(cls, listOfFile, atime):
        """ list of for file on disk
        """
        a = [(cls.get_time(x), x) for x in listOfFile]
        b = sorted(a, reverse=False)
        res = list()
        for i in b:
            if i[0] <= atime:
                res.append(i[1])
            else:
                break
        return res

    ##################
    @staticmethod
    def get_time(aFile):
        try:
            return os.stat(aFile)[stat.ST_MTIME]
        except:
            return -sys.maxsize

    @staticmethod
    def convert_date_and_time_to_float_time(adate="", atime=""):
        """Convert string to long time
            adate must be a string formated as
            year-mo-da as "2010-09-28"
            atime format as "14:23:57"
            support also the / format
        """
        adate = adate.replace("/", "-")
        if adate == "":
            sdate = list()
        else:
            sdate = adate.split("-")
        # if not specify, we fill out the blank with today's date
        if len(sdate) == 0:
            now = datetime.datetime.today()
            sdate.append("%s" % now.year)
            sdate.append("%s" % now.month)
            sdate.append("%s" % now.day)

        elif len(sdate) == 1:
            now = datetime.datetime.today()
            sdate.append("%s" % now.month)
            sdate.append("%s" % now.day)

        elif len(sdate) == 2:
            now = datetime.datetime.today()
            sdate.append("%s" % now.day)

        if atime == "":
            stime = list()
        else:
            stime = atime.split(":")
        # if not specify, we fill out the blank with today's date
        if len(stime) == 0:
            now = datetime.datetime.today()
            stime.append("%s" % now.hour)
            stime.append("%s" % now.minute)
            stime.append("%s" % now.second)

        elif len(stime) == 1:
            now = datetime.datetime.today()
            stime.append("%s" % now.minute)
            stime.append("%s" % now.second)

        elif len(stime) == 2:
            now = datetime.datetime.today()
            stime.append("%s" % now.second)

        assert len(sdate) == 3
        assert len(stime) == 3
        sdate = [int(x) for x in sdate]
        stime = [int(x) for x in stime]
        a = datetime.datetime(sdate[0], sdate[1], sdate[2],
                              stime[0], stime[1], stime[2], 0)
        a = time.mktime(a.timetuple())
        return a
