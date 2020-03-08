# -*- coding: utf-8 -*-
import os

DSK_MOUNTED_ROOT = 'mnt'
DSK_DEV_AREA = 'dev'

DSK_CONFIGURATION_FOLDER = 'dsk_configuration'
DSK_ENVI_FOLDER = 'envi'

# environment KEY to look for python and configuration
DSK_PATH_KEY = "DSKENV"
DSK_ENV_PATH_KEY = "DSKENVPATH"

DSK_ENVI_INFO_DIR = "configs_and_packs"
DSK_ENVI_INFO_FILENAME = "envi_info.yml"

# default dev_show
DSK_DEV_SHOW_KEY = "DEV_SHOW"
DSK_DEV_SHOW = "dev_show"


DSK_MASTER_CONF = os.path.join(os.sep,
                               DSK_MOUNTED_ROOT,
                               DSK_DEV_AREA,
                               DSK_CONFIGURATION_FOLDER,
                               DSK_ENVI_FOLDER)
