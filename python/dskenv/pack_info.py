# -*- coding: utf-8 -*-
from dskenv.base_configpack import BaseConfigPack
from dskenv.base_env import BaseEnv


class PackInfo(BaseConfigPack):

    def __init__(self, name, path=None):
        super(PackInfo, self).__init__(name, path)

    @staticmethod
    def get_label():
        return BaseEnv.pack_tag()
