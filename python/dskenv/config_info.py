# -*- coding: utf-8 -*-
import os
import json
from dskenv.base_configpack import BaseConfigPack
from dskenv.base_env import BaseEnv


class ConfigInfo(BaseConfigPack):
    def __init__(self, name, path=None):
        super(ConfigInfo, self).__init__(name, path)

    @staticmethod
    def get_label():
        return BaseEnv.config_tag()

    def reduce_current(self, envDic):
        """Use the meta to shorten the path
        # should manage a date... for now use current
        """
        metafile = BaseEnv.compiled_json(self.name)
        if not os.path.isfile(metafile):
            return False
        try:
            f = open(metafile, "r")
        except:
            return False
        try:
            metadata = json.load(f)
        except:
            f.close()
            return False
        f.close()
        if BaseEnv.COMPILED_ENVDATA not in metadata:
            return False
        envData = metadata[BaseEnv.COMPILED_ENVDATA]
        for envKey in envData:
            if envKey in envDic:
                lensaveLen = len(envDic[envKey])
                for p in envData[envKey]:
                    envDic[envKey] = [x for x in envDic[envKey] if x != p]
                if lensaveLen != len(envDic[envKey]):
                    insertPath = BaseEnv.short_path(self.name, envKey)
                    if insertPath not in envDic[envKey]:
                        envDic[envKey].insert(0, insertPath)

        return True
