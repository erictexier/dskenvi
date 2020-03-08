#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import types
import traceback
import re
from collections import OrderedDict

from dskenv.base_env import BaseEnv
from dskenv.version_helper import VersionHelper
from dskenv.pack_info import PackInfo
from dskenv.config_info import ConfigInfo
from dskenv.mini_env import MiniEnv
#  from dskenv.mini_env import MiniEnvUndo
from dskenv.launch_app import LaunchApp
from dskenv import dskenv_constants

import logging
log = logging.getLogger('envi')
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)


class Envi(MiniEnv):

    def __init__(self):
        super(Envi, self).__init__()
        self.reset()

    def reset(self):
        super(Envi, self).reset()

        self.configsObject = list()
        self.packsObject = list()

    def get_base_config_name(self):
        return dict(list(zip([x.base for x in self.configsObject],
                             [x for x in self.configsObject])))

    def get_base_pack_name(self):
        return dict(list(zip([x.base for x in self.packsObject],
                             [x for x in self.packsObject])))

    def build_command_history(self):
        cmdlist = self.get_commands()
        #  sys.stderr.write("commd %s\n" % cmdlist)
        cmd = " ".join(cmdlist)
        cmd = cmd.strip()
        prev = os.environ.get(BaseEnv.get_command_info(), "")
        if prev == "":
            self.setPath(BaseEnv.get_command_info(), cmd)
        else:
            # don't add if the last is the same
            sprev = prev.split(BaseEnv.commandsep)
            if len(sprev) > 0:
                if cmd != sprev[-1].replace("envi ", "").replace(";", ""):
                    # don't add if the last command is the same
                    self.setPath(BaseEnv.get_command_info(),
                                 prev + BaseEnv.commandsep + cmd)

    def build_history_variable(self, withRemoveCmd=False):

        self._storeLocalEnv[BaseEnv.get_key_pack_info()] = [
            os.path.join(x.path, x.format()) for x in self.packsObject]
        self._storeLocalEnv[BaseEnv.get_key_pack_info()] = BaseEnv.shorten(
            self._storeLocalEnv[BaseEnv.get_key_pack_info()])
        if withRemoveCmd is False:
            # since no history is of with don't rebuild
            # from scratch so here with merge with current
            older = os.environ.get(BaseEnv.get_key_pack_info(), "")
            older = older.split(os.pathsep)
            for o in reversed(older):
                if o not in self._storeLocalEnv[BaseEnv.get_key_pack_info()]:
                    self._storeLocalEnv[
                            BaseEnv.get_key_pack_info()].insert(0, o)

        self._storeLocalEnv[BaseEnv.get_key_config_info()] = [
            os.path.join(x.path, x.format()) for x in self.configsObject]
        self._storeLocalEnv[BaseEnv.get_key_config_info()] = BaseEnv.shorten(
            self._storeLocalEnv[BaseEnv.get_key_config_info()])
        if withRemoveCmd is False:
            # since no history is of with don't rebuild from scratch
            # so here with merge with current
            older = os.environ.get(BaseEnv.get_key_config_info(), "")
            older = older.split(os.pathsep)
            for o in reversed(older):
                if o not in self._storeLocalEnv[BaseEnv.get_key_config_info()]:
                    self._storeLocalEnv[
                        BaseEnv.get_key_config_info()].insert(0, o)

    #  def build_remove_cmd_dict(self):
    #    miniUndo = MiniEnvUndo()
    #    for p in self.packsObject:
    #        cleanp = p.name.replace(".","_").replace("-",
    #                                                 "_").replace(os.sep,"")
    #        miniUndo.buildUndo("%s_%s" % (BaseEnv._undoPackageKey,
    #                                      cleanp),p.get_fullname())
    #    return miniUndo

    def get_environ(self, withRemoveCmd=False):
        d = self.get_env_as_dict()
        #  if withRemoveCmd:
        #    d.update(self.build_remove_cmd_dict())
        return d

    def do_eval_pack(self):
        self.clean_environ()
        for rc in self.packsObject:
            if self.load_config_or_pack(rc.get_fullname()) is False:
                log.error("couldn't load %s" % (rc.get_fullname()))
                self.logfile("couldn't load %s" % (rc.get_fullname()))
        # call each config to see if they can reduce the path
        for rc in self.configsObject:
            rc.reduce_current(self._storeLocalEnv)

    def do_eval_pack_with_remove(self, removeList, exceptionStartwith):
        self.clean_environ(removeList, exceptionStartwith)
        for rc in self.packsObject:
            if self.load_config_or_pack(rc.get_fullname()) is False:
                log.error("couldn't load %s" % (rc.get_fullname()))
                self.logfile("couldn't load %s" % (rc.get_fullname()))
        for rc in self.configsObject:
            rc.reduce_current(self._storeLocalEnv)

    def init_with_cmd(self, listOfCmd, loginfo=None):
        """Get the environment from a command
        """
        # sys.stderr.write("list of command %s" % "X".join(listOfCmd))
        assert isinstance(listOfCmd, list)
        self.reset()
        rev = ""
        timeString = ""
        if loginfo:
            rev = loginfo.name
            # build a temp area to check out config
            timeString = "%s%s%s" % (loginfo.day,
                                     MiniEnv._sepDateTime,
                                     loginfo.time)

        allE = list()
        for cmdList in listOfCmd:
            e = MiniEnv()
            allE.insert(0, e)
            if timeString != "":
                # add the revision and the time
                e.parse_cmd(cmdList + " -r %s -t %s" % (rev, timeString))
            else:
                e.parse_cmd(cmdList)

            self._configFound.update(e.get_config_found())
            self.add_command(cmdList)

        inAllready = dict()
        for e in allE:
            #  loading the pack, and build the environment
            for k, v in reversed(list(e.get_pack_found().items())):
                rc = PackInfo(k, v)
                if rc.base not in inAllready:
                    self.packsObject.insert(0, rc)
                    inAllready[rc.base] = None

        self.set_init_pack_name_list([x.name for x in self.packsObject])
        self._commands = listOfCmd
        self.configsObject = [
                    ConfigInfo(x,
                               self._configFound[x]
                               ) for x in self._configFound]

        return True

    def info_from_environment(self):
        """Read the environment and find a sequence of cmd to create it
        the result is not unique
        """
        self.reset()

        ################################
        # read from environment
        helper = BaseEnv()
        # read configs from environment variable
        configsEnv = [ConfigInfo(x[0], x[1]) for x in helper.config_info()]
        # packs pack
        packsEnv = [PackInfo(x[0],
                             x[1]) for x in helper.pack_info(replaceMain=True)]
        initData = [[x, ] for x in packsEnv]
        packsDict = OrderedDict(list(zip([x.name for x in packsEnv],
                                         initData)))
        ################################

        # raw config dict
        rawConfig = OrderedDict()

        # loading empty config so we see the type of pack available
        # we also build a list of founded file to get the real version from
        # disk and deal with wild version in pack name -?.?
        for cfg in configsEnv:
            newC = MiniEnv()
            rawConfig[cfg.name] = newC
            fullPathName = cfg.get_file(cfg.path, -1)

            newC.set_dev_name(cfg.owner())
            if fullPathName != "":
                newC.load_config_or_pack(fullPathName)
            else:
                log.error("cannot figure out the path for %r" % cfg.name)

            for pa in newC.get_pack_name_list():
                v = VersionHelper(pa)
                for rv in packsDict:
                    rvp = packsDict[rv][0]
                    if v.is_similar(rvp):
                        pp = v.get_file(rvp.path, -1)
                        if pp != "":
                            p, realname = os.path.split(pp)
                            newC._packFound[realname.replace(".py", "")] = p
                        else:
                            # comment.debug("could not find the file %s" % pa)
                            # we take the name of the file
                            newC._packFound[rvp.name] = rvp.path
                        break

        # we read the config in reversed order and
        # mark the pack with the config that loaded them
        for rcn, conf in reversed(list(rawConfig.items())):
            llp = list()
            for x in conf.get_pack_name_list():
                llp.append(VersionHelper(x))
            for lp in llp:
                for i in packsDict:
                    if lp.is_similar(packsDict[i][0]):
                        packsDict[i].append(rcn)
                        break

        currentConfig = list()
        lateAddPack = list()

        # NOTES: it seems that when configs and pack get loaded at
        # the same time, the config take precedence
        # i don't think it should, but this code consider it
        # by adding extra command

        for keyPack in packsDict:
            theConfigs = packsDict[keyPack][1:]
            for c in theConfigs:
                if c not in currentConfig:
                    currentConfig.append(c)
            if len(theConfigs) == 0:  # no config where adding this
                lateAddPack.append(
                    ('', keyPack, packsDict[keyPack][0].owner()))
            else:
                # here we check the validity to detect late 'addPack'
                # check if the last enter current config is compatible:
                # check ownership
                needExtraPack = False
                curConfName = currentConfig[-1]
                aconf = rawConfig[curConfName]  # -1 for last in
                if keyPack not in aconf._packFound:
                    needExtraPack = True

                owner = packsDict[keyPack][0].owner()
                cowner = conf.dev_name()

                if owner != '':
                    if owner != cowner:
                        if cowner == '' and needExtraPack is False:
                            # we mark the config as needing the -d flag
                            # we don't do this for now, since we have
                            # to split the commandLine
                            # aconf.setDevName(owner)
                            lateAddPack.append((curConfName, keyPack, owner))
                        else:
                            lateAddPack.append((curConfName, keyPack, owner))
                elif needExtraPack:
                    lateAddPack.append((curConfName, keyPack, ''))

        # build the command line
        CmdLine = OrderedDict()

        for rcn, conf in list(rawConfig.items()):
            CmdLine[rcn] = list()
            dv = conf.dev_name()
            if dv != "":
                CmdLine[rcn].append('-D %s' % dv)
            CmdLine[rcn].append('-c %s' % rcn)
            # add the pack into a new command
            self.do_extra_pack(rcn, lateAddPack, CmdLine)

        if len(lateAddPack) > 0:
            # just to keep the orphane pack at the end
            self.do_extra_pack('', lateAddPack, CmdLine, pickup=True)

        CmdLineFinal = OrderedDict()
        for i in CmdLine:
            if len(CmdLine[i]) > 0:
                CmdLineFinal[i] = " ".join(CmdLine[i])

        # init the basic to stay consistent with a state
        self.configsObject = configsEnv
        # remove the dummy pack
        self.packsObject = packsEnv
        self._commands = list(CmdLineFinal.values())

        return True

    def do_extra_pack(self, rcn, lateAddPack, CmdLine, pickup=False):
        indexToPop = []
        if rcn == '':
            rcn = 'add'
        firstTime = True
        count = 1
        devName = ""
        for i, ll in enumerate(lateAddPack):
            if firstTime is True:
                firstTime = False
                rcnExtra = rcn+"%d" % count
                CmdLine[rcnExtra] = list()
                devName = ""
            if ll[0] == rcn:
                # we have to toggle when a change of user occur
                if ll[2] == "":  # no user
                    if devName != "":
                        count += 1
                        devName = ""
                        rcnExtra = rcn + "%d" % count
                        CmdLine[rcnExtra] = list()
                    CmdLine[rcnExtra].append('-p %s' % ll[1])
                    indexToPop.append(i)
                else:
                    if devName != "":
                        if devName != ll[2]:  # need for a new one
                            count += 1
                            devName = ll[2]
                            rcnExtra = rcn + "%d" % count
                            CmdLine[rcnExtra] = list()
                            CmdLine[rcnExtra].append(
                                '-D %s -p %s' % (devName, ll[1]))
                        else:
                            # the dev name is already there
                            CmdLine[rcnExtra].append('-p %s' % ll[1])
                    else:
                        count += 1
                        devName = ll[2]
                        rcnExtra = rcn+"%d" % count
                        CmdLine[rcnExtra] = list()
                        CmdLine[rcnExtra].append(
                            '-D %s -p %s' % (devName, ll[1]))
                    indexToPop.append(i)
            elif ll[0] == "" and pickup is True:  # no previous config
                if len(CmdLine[rcnExtra]) == 0:
                    if ll[2] == "":  # no user
                        CmdLine[rcnExtra].append('-p %s' % (ll[1]))
                        devName = ""
                    else:
                        devName = ll[2]
                        CmdLine[rcnExtra].append(
                            '-D %s -p %s' % (ll[2], ll[1]))
                    indexToPop.append(i)
                else:
                    if ll[2] == "":
                        if devName == ll[2]:
                            CmdLine[rcnExtra].append('-p %s' % (ll[1]))
                        else:
                            count += 1
                            rcnExtra = rcn + "%d" % count
                            CmdLine[rcnExtra] = list()
                            CmdLine[rcnExtra].append('-p %s' % ll[1])
                            devName = ""
                    else:
                        if devName == ll[2]:
                            CmdLine[rcnExtra].append('-p %s' % (ll[1]))
                        else:
                            count += 1
                            rcnExtra = rcn + "%d" % count
                            CmdLine[rcnExtra] = list()
                            devName = ll[2]
                            CmdLine[rcnExtra].append('-D %s -p %s' % (
                                                    devName, ll[1]))

                    indexToPop.append(i)
        for i in reversed(indexToPop):
            lateAddPack.pop(i)

    @staticmethod
    def dump_current_environ(fileName, filterList):
        try:
            f = open(fileName, "w")
        except:
            traceback.print_exc()
            return
        f.write("\n# raw environment\n")
        env = os.environ
        if filterList is None:  # dump everything
            for i in env:
                f.write(i + ":\n")
                f.write("\t%s\n" % env[i])

        else:
            for i in filterList:
                f.write(i + ":\n")
                f.write("\t%s\n" % env[i])
        f.close()

    def dump_to_file(self, fileName, dumpEval, filterList):
        try:
            f = open(fileName, "w")
        except:
            traceback.print_exc()
            return
        cbaseName = self.get_base_config_name()
        f.write("# configs\n")
        for obj in list(cbaseName.values()):
            f.write(obj.name+"\n")
        pbaseName = self.get_base_pack_name()
        f.write("\n# packs\n")
        for obj in list(pbaseName.values()):
            f.write(obj.name+"\n")
        if dumpEval is True:
            f.write("\n# environment\n")
            env = self.get_local_env()
            if filterList is None:  # dump everything
                for i in env:
                    f.write(i+":\n")
                    for k in env[i]:
                        if k != "":
                            f.write("\t%s\n" % k)
            else:
                for i in filterList:
                    #  for i in env:
                    f.write(i+":\n")
                    for k in env[i]:
                        if k != "":
                            f.write("\t%s\n" % k)
        f.close()

    @staticmethod
    def load_base_show(project_name, overwrite_pack=""):
        """ a simple overwrite for td show """
        Env = Envi()
        if overwrite_pack != "":
            Env.init_with_cmd(["-c {} -p {}".format(project_name,
                                                    overwrite_pack)])
        else:
            Env.init_with_cmd(["-c {}".format(project_name)])
        Env.do_eval_pack()
        dd = Env.get_environ(withRemoveCmd=False)
        os.environ.update(dd)
        Env.expand_vars(os.environ)

    def envi_context_to_var(self):
        """Store the Sgtk Context"""
        import json
        try:
            alist = list()
            if self.info_from_environment():
                for obj in self.get_commands():
                    alist.append("envi " + obj + ";")
            os.environ['ENVI_CONTEXT'] = json.dumps(alist)
        except:
            traceback.print_exc()

    def envi_context_from_var(self):
        """Store the Sgtk Context"""
        import json
        try:
            ctx = os.environ.get("ENVI_CONTEXT")
            return json.loads(ctx)
        except:
            traceback.print_exc()

    @staticmethod
    def copy_current_os(anenvdict):
        """Copy a dictionary with an exception key list

            :param anenvdict: a dictionary of environment key and value
            :return dict: copy of all the keys not listed

        """
        adict = dict()
        for x in anenvdict:
            if x not in BaseEnv.LIST_OF_KEY_EXCEPTION:
                adict[x] = anenvdict[x]
        return adict

    def execute_dict_only(self, argvs, envp=""):
        """This is a way to get the final result of couple envi command
            return as a dictionary. os.environ is fully restore

            :param argvs: a list of list envi command
            :returns dict: True if success
        """
        result = dict()
        # take a snapshot
        SAVE_OS = dict()
        SAVE_OS.update(os.environ)
        if envp != "":
            BaseEnv._reset(envp)
            os.environ[dskenv_constants.DSK_ENV_PATH_KEY] = envp
        for argv in argvs:
            dolist = ['dict_only']
            dolist.extend(argv)
            dolist.append("-Dodict")

            if self.execute(dolist, True):
                local_res = self.get_environ(withRemoveCmd=False)
                os.environ.update(local_res)
                self.expand_vars(os.environ)
                result.update(os.environ)
                self.reset()

        dd = list(os.environ.keys())
        for i in dd:
            os.environ.pop(i)
        # restore os.environ
        os.environ.update(SAVE_OS)
        BaseEnv._reset("")
        return result

    def get_help(self):
        helplist = list()
        hcmd = helplist.append

        hcmd("")
        hcmd("-"*30)
        hcmd("Envi general use in shell:")
        hcmd("\tenvi -c configname1 -c configname2 -p pack1 -p pack2")
        hcmd("\t this is not fully implemented, do run envi multiple time")
        hcmd("\tenvi -c configname1 -p pack1, -c configname2 -p pack2")
        hcmd("\tOtherwise it will execute pack1 after configname2")
        hcmd("-"*30)
        hcmd("")
        hcmd("Envi command options:")
        hcmd("*" * 4 + " -initialize- " + "*" * 4)
        hcmd("\t-c configname (one -c per configname)")
        hcmd("\t-p packname (one -c per pack name)")
        hcmd("\t-d: look first in ~/.envi for user config and pack)")
        hcmd("\t-D username: look first in ~/.envi for user config and pack)")
        hcmd("\t-f dirname (an alt directory formated as configs_or_packs.)")
        hcmd("\t-a executable name: (to launch executable)")
        hcmd("\t-l logfile: log execution (accept only full created path)")
        hcmd("\t-w writefile: create a shell to export/setenv environment")
        hcmd("\t-- (argument to the executable.")
        hcmd("")
        hcmd("*" * 4 + " -query- " + "*" * 4)
        hcmd("\t-h: list this description")
        hcmd("\t-L: list config and pack already executed")
        hcmd("\t-Reset: empty history")
        hcmd("\t-Deamon: fork envi to not have to wait for the end of process")
        hcmd("")

        hcmd("*" * 4 + "-- not fully implemented --" + "*" * 4)
        hcmd("\t-Debug: print the packs loaded and the path added")
        hcmd("\t-Print: print result (no change in environment)")
        hcmd("\t-Clean: remove all double path")
        hcmd("\t-ExistOnly: remove path that don't exist")
        # hcmd("\t (-r revision or tag)(-t time in history)
        # for possible retrieve from source control for later")
        hcmd("")

        hcmd("Config and Pack:")
        hcmd("*" * 4 + " -script command- " + "*" * 4)
        hcmd("Config:")
        hcmd('\t\tadd_pack(pack_name)')
        hcmd('\t\trm_pack(pack_name)')
        hcmd("Pack:")
        hcmd('\t\tset_path(env_var, value)')
        hcmd('\t\tunset_path(env_var)')
        hcmd('\t\tadd_path(env_var, value, at_end=False)')
        hcmd('\t\tadd_paths(env_var, [value,value2,value3], at_end=False)')
        hcmd('\t\trm_path(env_var, value)')
        hcmd('\t\tplatform_subdir()')
        hcmd('\t\tadd_function(function_name, core_function)')
        hcmd('\t\tadd_alias(aliasname, value)')
        hcmd('\t\tadd_unalias(aliasname)')
        hcmd('\t\tlog_file(aliasname, value)')
        hcmd("")

        return helplist

    def execute(self, argv, fromPython=True):
        """This module is mainly to be used from shell in progress

            :param argv: a list of envi command
            :param fromPython: default True.
                the result of the function is in os.environ
            :returns bool: True if success
        """

        import subprocess
        # argument to remove
        opt = dict()
        opt["List"] = ["-L", False]
        opt["Reset"] = ["-Reset", False]  # no undo implemented
        opt["Info"] = ["-h", False]
        opt["Deamon"] = ['-Deamon', False]
        opt['Print'] = ["-Print", False]
        opt['Debug'] = ["-Debug", False]
        opt['Store'] = ["-Store", False]
        opt['DictOnly'] = ["-Dodict", False]
        opt['Clean'] = ["-Clean", False]
        opt['ExistOnly'] = ["-ExistOnly", False]

        cmdLines = " ".join(argv[1:]).split("--")

        if len(cmdLines) > 2:
            sys.stderr.write("Envi.execute: don't support multiple launch\n")
            return False
        cmdLines = [x for x in cmdLines if x != '']  # remove the blank
        if len(cmdLines) == 0:
            sys.stderr.write("Envi.execute: no arguments\n")
            return False
        cleanArg = list()

        envCmd = cmdLines[0]
        for i in opt:
            tempLine = envCmd.replace(opt[i][0], "")
            if tempLine != envCmd:
                opt[i] = [opt[i][0], not opt[i][1]]  # toggle the opt
                envCmd = tempLine

            #  return False
        if opt["Debug"][1] is True:
            self.set_debug(True)
            #  self._printall = True
        else:
            self.set_debug(False)
            #  self._printall = False

        if opt["Print"][1] is True:
            for x in os.environ:
                sys.stderr.write(x+":\n")
                for y in os.environ[x].split(os.pathsep):
                    sys.stderr.write("\t"+y+"\n")
                #  sys.stdout.write("")
            return True

        if fromPython is False:
            if opt["Clean"][1] is True or opt["ExistOnly"][1] is True:
                self.main_cleanup(clean_double=opt["Clean"][1],
                                  exist_only=opt["ExistOnly"][1])
                return True

        if opt["Store"][1] is True:
            # build a pack file to store initial state
            self.store()
            return True

        if opt["Info"][1] is True:
            import dskenv
            c = BaseEnv.base_config()
            p = BaseEnv.base_pack()
            sys.stderr.write("config in: {}\npacks in: {}\n".format(c, p))
            if 'dev' in dskenv.__file__:
                sys.stderr.write("envi: dev dskenv\n")
            else:
                sys.stderr.write("envi: released code\n")
            sys.stderr.write("envi: released code\n")
            helplist = self.get_help()
            sys.stderr.write("\n".join(helplist))
            return True

        app = ""
        logfile = ""
        writefile = ""
        # search if app and logfile
        envArgs = envCmd.split(",")  # split per config
        paternapp = re.compile(r'-a\s*[\w\d\.\%s-]*' % os.sep)
        paternlog = re.compile(r'-l\s*[\w\d\.\%s-]*' % os.sep)
        paterncache = re.compile(r'-w\s*[\w\d\.\%s-]*' % os.sep)

        for envarg in envArgs:
            # app
            m = paternapp.search(envarg)
            if m:
                stringfound = m.group()
                envarg = envarg.replace(stringfound, "")
                app = stringfound.replace("-a", "")
                app = app.strip()

            # log
            aclean = envarg.strip()
            m = paternlog.search(aclean)
            if m:
                stringfound = m.group()
                envarg = envarg.replace(stringfound, "")
                logfile = stringfound.replace("-l", "")
                logfile = logfile.strip()

            # write
            aclean = envarg.strip()
            m = paterncache.search(aclean)

            if m:
                stringfound = m.group()
                envarg = envarg.replace(stringfound, "")
                writefile = stringfound.replace("-w", "")
                writefile = writefile.strip()

            aclean = envarg.strip()
            if aclean != "":
                cleanArg.append(aclean)

        if opt["List"][1] is True:
            import dskenv
            import getpass
            # if self.info_from_environment():
            #    for obj in self.get_commands():
            if writefile != "":
                is_d = False
                for x in cleanArg:
                    #  sys.stderr.write("---> %r\n" % x)
                    if '-d' in x:
                        #  sys.stderr.write("---> hellp\n")
                        is_d = True
                        break

                try:
                    f = open(writefile, "w")
                except:
                    traceback.print_exc()
                    return False

                #  for obj in BaseEnv.pack_history(
                # os.environ.get('DSKENVPATH')):
                for obj in BaseEnv.command_history():
                    if is_d is False:
                        # sys.stderr.write("---> %s\n" % obj)
                        """FOR LATER IF NEEDED"""
                        # paternd = re.compile("-D\s*[\w\d\.\-]*")
                        # m = paternd.search(obj)
                        # sys.stderr.write("-- %s" % m)
                        # if m:
                        #    obj = obj.replace(m.group(),"")
                        #    obj = obj.strip()
                        #  sys.stderr.write("envi "+ obj + ";\n")
                        f.write("envi " + obj + ";\n")
                    else:
                        #  sys.stderr.write("--------> %s\n" % obj)
                        f.write("envi " + obj + " -D %s;\n" % (
                            getpass.getuser()))

            else:
                for obj in BaseEnv.command_history():
                    sys.stderr.write("envi " + obj + ";\n")

                c = BaseEnv.base_config()
                p = BaseEnv.base_pack()
                sys.stderr.write("#config in {}\n#packs in {}\n".format(c, p))
                if 'dev' in dskenv.__file__:
                    sys.stderr.write("#envi code dev\n")
                else:
                    sys.stderr.write("#envi code released\n")

            return True

        if writefile != "" and len(cleanArg) == 0 and app == "":
            res = self.dump_os_as_shell(writefile)
            if res is True:
                sys.stderr.write("DONE\n")
            else:
                sys.stderr.write("ERROR: couldn't create %s\n" % writefile)
            return True

        if logfile != "" and os.path.exists(os.path.dirname(logfile)):
            self.startlog(logfile)
            self.setPath("ENVI_LOG", logfile)
        else:
            self.unsetPath("ENVI_LOG")

        # take a snapshot
        SAVE_OS = dict()
        SAVE_OS.update(os.environ)

        self.init_with_cmd(cleanArg)

        self.do_eval_pack()

        if opt["Reset"][1] is True:
            #  self.unsetPath(BaseEnv.get_key_pack_info())
            #  self.unsetPath(BaseEnv.get_key_config_info())
            self.unsetPath(BaseEnv.get_command_info())

        else:
            if app != "":
                self.add_command("-a %s" % app)
            self.build_command_history()

        if app == "":
            if writefile == "":
                if fromPython is True:
                    if opt['DictOnly'][1] is True:
                        self.reset_cache()
                        self.endlog()
                        return True

                    os.environ.update(self.get_environ(withRemoveCmd=False))
                    self.expand_vars(os.environ)

                    newpath = list()
                    for p in sys.path:
                        if p.startswith(sys.prefix):
                            newpath.append(p)

                    if 'PYTHONPATH' in os.environ:
                        newpath.extend(
                            os.environ['PYTHONPATH'].split(os.pathsep))
                    sys.path = newpath  # reset the sys.path
                    self.reset_cache()
                    self.endlog()
                    return True

                else:
                    self.echo_environ_diff_only(SAVE_OS)
                    self.endlog()
                    return True
            else:
                sys.stderr.write("write file %s\n" % writefile)
                self.write_environ(SAVE_OS, writefile)
                self.endlog()
                return True

        if fromPython is False:
            self.write_bash_history()
            # we still need to update the calling
            # shell with the command history

        cmd = [app]
        if len(cmdLines) == 2:
            apparg = cmdLines[1]
            cmd.extend(apparg.split())
        #  self.logfile("2")
        os.environ.update(self.get_environ(withRemoveCmd=False))
        self.expand_vars(os.environ)
        self.reset_cache()
        #  self.logfile("3")

        self.logfile("execute: %s" % " ".join(cmd))
        thelog = self.getlog()
        p = None
        if thelog and opt["Deamon"][1] is True:
            sys.stderr.write("IN SUBProcess start\n")
            self.endlog()
            thelog = open(logfile, "a+")
            x = LaunchApp(cmd, thelog)
            x.start()

        else:
            if thelog:
                sys.stderr.write("IN SUBProcess start2\n")
                p = subprocess.Popen(" ".join(cmd),
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     shell=True,
                                     close_fds=True)

                if p.wait() != 0:
                    self.logfile("ERROR: %s" % " ".join(cmd))

                result = p.stdout.readlines()
                p.stdout.close()
                thelog.write("\n".join(result))

            else:
                sys.stderr.write("IN SUBProcess start3\n")
                # sys.stderr.write("%s\n" % sys.stdout)
                # sys.stderr.write("err %s\n" % sys.stderr)
                p = subprocess.Popen(cmd,
                                     stdout=None,
                                     stderr=None,
                                     shell=True,
                                     close_fds=True)
                # import time
                # time.sleep(30)

        if p:
            self.logfile("Launched %r with processid %d" % (app, p.pid))
        self.endlog()
        # not finished
#############################################################
if __name__ == "__main__":
    a = Envi()
    a.set_csh()
    a.execute(sys.argv, False)
