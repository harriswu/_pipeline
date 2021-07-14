import coreFunction


class RigData(coreFunction.CoreFunction):
    def __init__(self, **kwargs):
        super(RigData, self).__init__(**kwargs)
        self._data_path = None
        self._file_filter = None

        self._data_import_path = []

    def get_build_kwargs(self, **kwargs):
        super(RigData, self).get_build_kwargs(**kwargs)
        # TODO: change it to a more asset manage friendly way to compose data path, and able to support multiple paths
        self._data_path = kwargs.get('data_path', None)

    def register_steps(self):
        super(RigData, self).register_steps()
        self.add_build_step('get data', self.get_data, 'build')

    def get_data(self):
        pass

    def load_data(self):
        """
        function to load data, all sub class should use this function to load data to nodes,
        then attach it to the section need to load
        """
        pass
