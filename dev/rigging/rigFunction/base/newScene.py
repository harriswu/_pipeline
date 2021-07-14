import maya.cmds as cmds

import dev.rigging.rigFunction.core.coreFunction as coreFunction


class NewScene(coreFunction.CoreFunction):
    def __init__(self, **kwargs):
        super(NewScene, self).__init__(**kwargs)

    def register_steps(self):
        super(NewScene, self).register_steps()
        self.add_build_step('new scene', self.new_scene, 'build')

    @staticmethod
    def new_scene():
        cmds.file(f=True, new=True)
