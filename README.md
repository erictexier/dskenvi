
## Envi:

Envi est un utilitaire pour gerer les variables d'environnement en shell, cshell et python.


### Update history:
Fri Nov 17 - 2017:
   Improvement:
    - add wiki access to envi from gui envi_commit and zlaunch
    - history implemented in xenvi
    - enviswitch
   Problem found:
    - check to load only one plugin. Fixable in config




### dependencies:  python2.7.*


### install note envi code developer:

```bash
cd /u/beta/newEnv
git clone git@git.envi.git
```

### install note envi user:

```bash
envi -c dev_tools
```

  - To get setup with envi or update your envi environment:

```bash
envi_install -h
```

   - To manage your configs and packs:

```bash
envi_commit
```

### Example:

will set you up with the current show environment
in shell or cshell:

```bash
envi -c showname
```

in python:
```python
from dskenv.envi import Envi
Envi().execute("-c showname")
```
### Reference Documentation and Release Notes:

- in progress

### envi -h ###

config in: /u/..../configs_and_packs/configs

packs in: /u/..../configs_and_packs/packs

envi: dev dskenv

envi: released code

------------------------------
Envi general use in shell:

        envi -c configname1 -c configname2 -p pack1 -p pack2

------------------------------


####Envi command options:

* -initialize-

        -c configname: (one -c per configname)
        -p packname: (one -c per packname)
        -d: (to look first in ~/.envi for user config and pack)
        -D username: (to look first in /u/username/.envi for user config and pack)
        -f dirname: (an alternative directory formated as configs_or_packs... not really tested or pipeline friendly)
        -a executable name: (to launch executable)
        -l logfile: log execution information (parent directory must exists, accept only full path)
        -w writefile: create a shell to export/setenv the current environment.(if -c or -p in the command dump only difference)
        -- (argument to the executable. Ex: envi -c config -a maya -- -batch (only one per session after config and pack)

* -query-

        -h: list this description
        -L: list config and pack already executed
        -Debug: list at execution the pack that are getting loaded and the path set
        -Print: print result (no change in environment)


* - utils -

        -Deamon: fork envi to not wait for end of execution process an log the launch
        -Clean: remove all double path
        -ExistOnly: remove path that don't exist


####Config and Pack:

* -script command-

Config:

        add_pack(pack_name)
        rm_pack(pack_name)
Pack:

        set_path(env_var, value)
        unset_path(env_var)
        add_path(env_var, value, at_end=False)
        add_paths(env_var, [value1,value2], at_end=False)
        rm_path(env_var, value)
        add_function(function_name, core_function)
        dir_platform()  # return for example on suse13.1    linux/opensuse-13.1

Config/Pack:


        log_file(string)


