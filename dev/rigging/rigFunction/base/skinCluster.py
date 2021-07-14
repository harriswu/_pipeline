import utils.common.fileUtils as fileUtils

import utils.rigging.deformerUtils as deformerUtils

import dev.rigging.rigFunction.core.rigData as rigData

FORMAT = '.npy'


class SkinCluster(rigData.RigData):
    def __init__(self, **kwargs):
        super(SkinCluster, self).__init__(**kwargs)
        self._force = False

    def get_build_kwargs(self, **kwargs):
        super(SkinCluster, self).get_build_kwargs()
        self._force = kwargs.get('force', False)

    def register_steps(self):
        super(SkinCluster, self).register_steps()
        self.add_build_step('load data', self.get_data, 'connect')

    def get_data(self):
        super(SkinCluster, self).get_data()
        self._data_import_path += fileUtils.pathUtils.get_files_from_path(self._data_path, extension=FORMAT)

    def load_data(self):
        super(SkinCluster, self).load_data()
        for f in self._data_import_path:
            deformerUtils.skinCluster.import_data(f, flip=self._flip, force=self._force)
