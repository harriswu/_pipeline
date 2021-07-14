import os

import utils.rigging.controlUtils as controlUtils

import dev.rigging.rigFunction.core.rigData as rigData

NAME = 'controlShape'
FORMAT = '.ctrlShape'


class ControlShape(rigData.RigData):
    def __init__(self, **kwargs):
        super(ControlShape, self).__init__(**kwargs)
        self._size = 1

    def get_build_kwargs(self, **kwargs):
        super(ControlShape, self).get_build_kwargs()
        self._size = kwargs.get('size', 1)

    def register_steps(self):
        super(ControlShape, self).register_steps()
        self.add_build_step('load data', self.get_data, 'connect')

    def get_data(self):
        super(ControlShape, self).get_data()
        # get control shape file
        ctrl_shape_path = os.path.join(self._data_path, NAME + FORMAT)
        if os.path.isfile(ctrl_shape_path):
            self._data_import_path.append(ctrl_shape_path)

    def load_data(self):
        super(ControlShape, self).load_data()
        for f in self._data_import_path:
            controlUtils.import_data(f, size=self._size)
