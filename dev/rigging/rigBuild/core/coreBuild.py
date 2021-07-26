import inspect


class CoreBuild(object):
    def __init__(self):
        # get rig node's python path
        self._node_path = inspect.getmodule(self.__class__).__name__

        # build sections
        self._build_list = {'build': {'function': {},
                                      'keys': []},
                            'connect': {'function': {},
                                        'keys': []}}

    @property
    def node_path(self):
        return self._node_path

    # register steps to sections
    def register_steps(self):
        pass

    def add_build_step(self, name, function, section, after=None):
        """
        add build step to given section

        Args:
            name (str): build step's name
            function: in-class method
            section (str): add step to the given build section
            after (int/str): put step after the given step name / index
        """
        if after:
            if isinstance(after, basestring):
                # get index
                after = self._build_list[section]['keys'].index(after)
            # insert step after the given index
            self._build_list[section]['keys'].insert(after, name)
        else:
            self._build_list[section]['keys'].append(name)

        self._build_list[section]['function'].update({name: function})
