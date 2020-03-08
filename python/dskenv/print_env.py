# -*- coding: utf-8 -*-
"""Helper to print environment
"""

import os
import sys
import fnmatch
mainEnvList = ['PATH',
               'LD_LIBRARY_PATH',
               'PYTHONPATH',
               'PYTHON_PRE_PATH']

mayaEnvListBase = ['MAYA_PLUG_IN_PATH',
                   'MAYA_SCRIPT_PATH'
                   ]


def print_grep(expres):
    """Grep through os.environ.  Key and Value
    """
    for x in os.environ:
        if expres in x or expres.upper() in x:
            print((x, os.environ.get(x)))
        elif expres in os.environ[x] or expres.upper() in os.environ[x]:
            print((x, os.environ.get(x)))
# turn mel on


def doItsimple(someEnv):
    """List the content of all the variable in the environment
    """
    res = list()
    for i in someEnv:
        envValue = os.environ.get(i, None)
        res.append("*" * 10 + " " + i + " " + "*" * 10)
        if envValue:
            res.append(i)
            envValue = envValue.split(":")
            for env in envValue:
                res.append("\t%s=%s" % (i, env))

        else:
            res.append(i + ": not defined")
    return res


def doIt(someEnv=mainEnvList):
    """List the content of all the path in the environment
    """
    res = list()
    for i in someEnv:
        envValue = os.environ.get(i, None)
        res.append("*" * 10 + " " + i + " " + "*" * 10)
        if envValue:
            envValue = envValue.split(":")
            for env in envValue:
                res.append(env + " (%s)" % i)
                if os.path.isdir(env):
                    fs = os.listdir(env)
                    fs.sort()
                    for f in fs:
                        res.append("\t" * 4 + f)
                else:
                    res.append("not a dir: " + env)
        else:
            res.append(i + ": not defined")
    return res


def filedump(afile, doreport=True, list_of_env=[], mode="w"):

    f = open(afile, mode)
    if doreport is True:
        f.write("\n".join(doReport()))
    else:
        f.write("\n".join(doItsimple(list_of_env)))

    f.close()


def infodump(afile, astr):
    f = open(afile, "w")
    f.write(astr)
    f.close()


def dumpall(afile):
    from pprint import pformat
    f = open(afile, "w")
    for x in os.environ:
        y = os.environ[x].split(os.pathsep)
        for yy in y:
            f.write("%s %s\n" % (x, yy))

GREPED = None
GRAPED_ITEMS = {}


def HasGrepped(t, g, topicName):
    global GRAPED_ITEMS
    ret = False
    if '*' in g:
        ret = fnmatch.fnmatch(t, g)
    else:
        ret = g in t
    if ret:
        l = GRAPED_ITEMS.get(topicName, [])
        l.append(t)
        GRAPED_ITEMS[topicName] = l
    return ret


def ReportList(name, paths):
    nb = len(paths)
    if nb:
        eff = len(set(paths))*1.0 / nb * 100
    else:
        eff = 100.00

    print(('\n#--', name+':', nb, 'item(s), '+str(eff)[:5] + '% unic.'))

    seen = {}
    for p in paths:
        seen[p] = occI = p in seen and seen[p] + 1 or 1
        s = paths.count(p)
        if s > 1:
            ptr = str(occI)+'/'+str(s)
        else:
            ptr = ' '
        lb = rb = ' '
        if GREPED and HasGrepped(p, GREPED, name):
            lb = '['
            rb = ']'
        x = ' '
        if not os.path.exists(p):
            x = '!'
        print((ptr, '\t', x, lb + p + rb))


def ReportList_asList(name, paths):
    result = list()
    nb = len(paths)
    if nb:
        eff = len(set(paths)) / nb * 100
    else:
        eff = 100.00

    aline = '\n#-- {}: {} item(s), {} % unic.'.format(name,
                                                      nb,
                                                      str(eff)[:5])
    result.append(aline)
    seen = {}
    for p in paths:
        seen[p] = occI = p in seen and seen[p]+1 or 1
        s = paths.count(p)
        if s > 1:
            ptr = str(occI)+'/'+str(s)
        else:
            ptr = ' '
        lb = rb = ' '
        if GREPED and HasGrepped(p, GREPED, name):
            lb = '['
            rb = ']'
        x = ' '
        if not os.path.exists(p):
            x = '!'
        # print ptr, '\t', x, lb+p+rb
        result.append("{} \t {} {}".format(ptr, x, lb+p+rb))
    return result


def ReportEnvPath(envName, sep=':'):
    ev = os.environ.get(envName, None)
    if not ev:
        pl = []
    else:
        pl = ev.split(sep)
    ReportList(envName, pl)


def ReportEnvPath_asList(envName, sep=':'):
    result = list()
    ev = os.environ.get(envName, None)
    if not ev:
        pl = []
    else:
        pl = ev.split(sep)
    res = ReportList_asList(envName, pl)
    result.extend(res)
    return result


def doReport():
    result = list()
    result.extend(ReportEnvPath_asList('PATH'))
    result.extend(ReportEnvPath_asList('LD_LIBRARY_PATH'))
    result.extend(ReportEnvPath_asList('PYTHON_PRE_PATH'))
    result.extend(ReportEnvPath_asList('PYTHONPATH'))
    result.extend(ReportEnvPath_asList('MAYA_MODULE_PATH'))
    result.extend(ReportEnvPath_asList('MAYA_PLUG_IN_PATH'))
    result.extend(ReportEnvPath_asList('MAYA_SCRIPT_PRE_PATH'))
    result.extend(ReportEnvPath_asList('MAYA_SCRIPT_PATH'))
    result.extend(ReportEnvPath_asList('MAYA_PRESET_PATH'))
    result.extend(ReportEnvPath_asList('XBMLANGPATH'))
    return result

if __name__ == "__main__":

    print(("\n".join(doReport())))

    if '-h' in sys.argv:
        print(__doc__)
        sys.exit(1)

    if '-g' in sys.argv:
        i = sys.argv.index('-g')
        sys.argv.pop(i)
        GREPED = sys.argv.pop(i)
        print(('Hilighting', repr(GREPED)))

    if len(sys.argv) > 1:
        ReportEnvPath(sys.argv[1])
    else:
        ReportEnvPath('PATH')
        ReportEnvPath('LD_LIBRARY_PATH')
        ReportEnvPath('PYTHON_PRE_PATH')
        ReportEnvPath('PYTHONPATH')
        ReportEnvPath('MAYA_MODULE_PATH')
        ReportEnvPath('MAYA_PLUG_IN_PATH')
        ReportEnvPath('MAYA_SCRIPT_PRE_PATH')
        ReportEnvPath('MAYA_SCRIPT_PATH')
        ReportEnvPath('MAYA_PRESET_PATH')
        ReportEnvPath('XBMLANGPATH')

    if GREPED is not None:
        print(('\n#==== Greped:', len(GRAPED_ITEMS), 'item(s) ===='))
        for name, items in list(GRAPED_ITEMS.items()):
            print(('#-- ', name))
            for i in items:
                print(('   ', i))
