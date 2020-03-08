# -*- coding: utf-8 -*-
# look at example "/u/etexier/plugin_env/plugin_info.yml"
import sys


class PackageApp(object):
    """A util to parse and extended environment with package yaml file

      example::

        Version: current

        components:
          environment:
            RenderManForMaya-21.4-maya2016.5:
                # if any new version, copy line above

            RenderManForMaya-21.4-maya2016.6:
              MAYA_SCRIPT_PATH: ['{Base}/{Version}/scripts',
              '{Base}/{Version}/scripts/mel']

            default:
              MAYA_PLUG_IN_PATH: '{Base}/{Version}/plug-ins'
              XBMLANGPATH: '{Base}/{Version}/icons'
              MAYA_SCRIPT_PATH: '{Base}/{Version}/scripts'
              PYTHONPATH: '{Base}/{Version}/scripts'
              LD_LIBRARY_PATH: '{Base}/{Version}/lib'

            current: RenderManForMaya-21.4-maya2016.5

    """
    def __init__(self, filename):
        """A valid yaml config file"""

        data = {}
        try:
            import yaml
        except:
            sys.stderr.write("Cannot import yaml")
            return data
        try:
            with open(filename, "rt") as fh:
                data = yaml.load(fh, Loader=yaml.FullLoader)
        except Exception as e:
            raise Exception("Cannot parse yml file: %s" % e)
        self._data = data
        self._filename = filename

    def query(self, release_path, version=None):
        """Query environment variable for a given version """
        if self._data is None:
            return dict()
        data_env = self._data['components']['environment']
        assert version != 'default'
        assert 'default' in data_env  # default is required
        if version is None:
            version = self._data['Version']
        if version == "current":  # update current
            version = data_env[version]
        if version not in data_env:
            raise Exception("No version found -%r- in %s\n" % (
                                        version, self._filename))
            return dict()

        field_dict = dict()
        field_dict['Base'] = release_path
        field_dict['Version'] = version

        default_data = dict()
        default_data.update(data_env['default'])
        if version != 'default' and isinstance(data_env[version], dict):
            # simple update for now
            default_data.update(data_env[version])

        # apply parameter
        eval_result = dict()
        for k in default_data:
            # Can be a string or a list of string
            value = default_data[k]
            if isinstance(value, list):
                new_list = list()
                for v in value:
                    new_list.append(v.format(**field_dict))
                eval_result[k] = new_list
            elif isinstance(value, str):
                eval_result[k] = list()
                eval_result[k].append(value.format(**field_dict))
        return eval_result

    def list_version(self):
        res = list()
        if self._data is None:
            return res
        data_env = self._data['components']['environment']
        for d in data_env:
            if d != 'default' and d != 'current':
                res.append(d)
        return res
