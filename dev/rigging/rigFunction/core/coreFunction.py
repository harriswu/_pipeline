import dev.rigging.rigBuild.core.coreBuild as coreBuild


class CoreFunction(coreBuild.CoreBuild):
    def __init__(self, **kwargs):
        super(CoreFunction, self).__init__()

    def get_build_kwargs(self, **kwargs):
        pass

    def get_build_setting(self):
        pass

    def get_connect_kwargs(self, **kwargs):
        pass

    def get_connect_setting(self):
        pass

    def register_build_kwargs(self, **kwargs):
        self.get_build_kwargs(**kwargs)

    def register_connect_kwargs(self, **kwargs):
        self.get_connect_kwargs(**kwargs)

    def build(self, **kwargs):
        self.register_build_kwargs(**kwargs)

        self.get_build_setting()

        for key in self._build_list['build']['keys']:
            self._build_list['build']['function'][key]()

    def connect(self, **kwargs):
        self.register_connect_kwargs(**kwargs)

        self.get_connect_setting()

        for key in self._build_list['connect']['keys']:
            self._build_list['connect']['function'][key]()
