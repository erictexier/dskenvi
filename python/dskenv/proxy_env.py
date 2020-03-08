# -*- coding: utf-8 -*-
import os
import sys
import errno
import functools
import getpass
import traceback

from dskenv.base_env import BaseEnv


def get_user_dev():
    result = list()
    try:
        import grp
    except:
        return result
    groups = grp.getgrnam('dev')
    return groups.gr_mem


def with_cleared_umask(func):
    """
    Decorator which clears the umask for a method.

    The umask is a permissions mask that gets applied
    whenever new files or folders are created. For I/O methods
    that have a permissions parameter, it is important that the
    umask is cleared prior to execution, otherwise the default
    umask may alter the resulting permissions, for example::

        def create_folders(path, permissions=0777):
            log.debug("Creating folder %s..." % path)
            os.makedirs(path, permissions)

    The 0777 permissions indicate that we want folders to be
    completely open for all users (a+rwx). However, the umask
    overrides this, so if the umask for example is set to 0777,
    meaning that I/O operations are not allowed to create files
    that are readable, executable or writable for users, groups
    or others, the resulting permissions on folders created
    by create folders will be 0, despite passing in 0777 permissions.

    By adding this decorator to the method, we temporarily reset
    the umask to 0, thereby giving full control to
    any permissions operation to take place without any restriction
    by the umask::

        @with_cleared_umask
        def create_folders(path, permissions=0777):
            # Creates folders with the given permissions,
            # regardless of umask setting.
            log.debug("Creating folder %s..." % path)
            os.makedirs(path, permissions)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # set umask to zero, store old umask
        old_umask = os.umask(0)
        try:
            # execute method payload
            return func(*args, **kwargs)
        finally:
            # set mask back to previous value
            os.umask(old_umask)
    return wrapper


@with_cleared_umask
def ensure_folder_exists(path, permissions=0o775):
    """
    Helper method - creates a folder and parent folders
    if such do not already exist.

    :param path: path to create
    :param permissions: Permissions to use when
      folder is created
    :param create_placeholder_file: If true,
      a placeholder file will be generated.

    :raises: OSError - if there was a problem creating the folder
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path, permissions)
        except OSError as e:
            # Race conditions are perfectly possible
            # on some network storage setups
            # so make sure that we ignore any file
            # already exists errors, as they
            # are not really errors!
            if e.errno != errno.EEXIST:
                # re-raise
                raise


class ProxyEnv(BaseEnv):
    """Restrict access to dev workspace
       This is the context switch
    """
    def __init__(self, new_env_path=""):
        super(ProxyEnv, self).__init__()
        if (new_env_path != "" and
                self.is_possible_user_dev(new_env_path)):
            self.__initialize(new_env_path)
        else:
            self.back_to_global()

    def __initialize(self, new_env_path):
        self._reset(new_env_path)
        if getpass.getuser() in get_user_dev():
            self.__ensure_userenv_exist()

    def back_to_global(self):
        self._reset("")

    def __ensure_userenv_exist(self):

        ensure_folder_exists(self.base(), permissions=0o775)
        ensure_folder_exists(self.base_pack(), permissions=0o775)
        ensure_folder_exists(self.base_config(), permissions=0o775)

    def is_valid(self):
        return (os.path.isdir(self.base_pack()) and
                os.path.isdir(self.base_config()))


class ProdEnv(BaseEnv):
    """Api to a valid prod config place
    """
    def __init__(self, new_env_path=""):
        super(ProdEnv, self).__init__()
        if new_env_path != "":
            self.__initialize(new_env_path)
        else:
            self.back_to_global()

    def __initialize(self, new_env_path):
        self._reset(new_env_path)

    def back_to_global(self):
        self._reset("")

    def is_valid(self):
        return (os.path.isdir(self.base_pack()) and
                os.path.isdir(self.base_config()))

    @staticmethod
    def test_if_prod_access(apath):
        """Return if the directory is readeable by group 'teams'
        """
        try:
            import os
            import grp
            stat_info = os.stat(apath)
            gid = stat_info.st_gid
            return grp.getgrgid(gid)[0] in ['teams']

        except:
            traceback.print_exc()
            pass
        return False
