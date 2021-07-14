import dev.rigging.rigBuild.core.coreBuild as coreBuild


class CoreFunction(coreBuild):
    def __init__(self, **kwargs):
        self._flip = kwargs.get('flip', False)

    def get_build_kwargs(self, **kwargs):
        pass

    def flip_build_kwargs(self):
        pass

    def get_connect_kwargs(self, **kwargs):
        pass

    def flip_connect_kwargs(self):
        pass

    def build(self, **kwargs):
        self.get_build_kwargs(**kwargs)
        if self._flip:
            self.flip_build_kwargs()

        for key in self._build_list['build']['keys']:
            self._build_list['build']['functions'][key]()

    def connect(self, **kwargs):
        self.get_connect_kwargs(**kwargs)
        if self._flip:
            self.flip_connect_kwargs()

        for key in self._build_list['connect']['keys']:
            self._build_list['connect']['functions'][key]()
