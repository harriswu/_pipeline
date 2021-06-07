import dev.rigging.rigNode.core.coreNode as coreNode


class CoreUtility(coreNode.CoreNode):
    def __init__(self, **kwargs):
        super(CoreUtility, self).__init__(**kwargs)
        self._node_type = 'rigUtility'
