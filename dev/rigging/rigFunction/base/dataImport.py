import os
import maya.cmds as cmds

import utils.common.fileUtils as fileUtils

import dev.rigging.rigFunction.core.rigData as rigData


SUPPORT_FORMAT = ['.mb', '.ma', '.obj']  # TODO: support other format especially usd


class DataImport(rigData.RigData):
    def __init__(self, **kwargs):
        super(DataImport, self).__init__(**kwargs)
        self._filter = None

    def get_build_kwargs(self, **kwargs):
        super(DataImport, self).get_build_kwargs(**kwargs)
        self._filter = kwargs.get('filter', None)

    def register_steps(self):
        super(DataImport, self).register_steps()
        self.add_build_step('load data', self.load_data, 'build')

    def get_data(self):
        super(DataImport, self).get_data()
        data_import_path = []

        if self._filter:
            for f in self._filter:
                if f in SUPPORT_FORMAT:
                    files_import = fileUtils.pathUtils.get_files_from_path(self._data_path, extension=f)
                    data_import_path += files_import
                elif not f.startswith('.'):
                    # filter is a file name
                    file_path = os.path.join(self._data_path, f)
                    if os.path.isfile(file_path):
                        data_import_path.append(file_path)
        else:
            # get all support files
            files_import = fileUtils.pathUtils.get_files_from_path(self._data_path, extension=SUPPORT_FORMAT)
            data_import_path += files_import

        self._data_import_path = list(set(data_import_path))

    def load_data(self):
        super(DataImport, self).load_data()
        for f in self._data_import_path:
            cmds.file(f, i=True)
