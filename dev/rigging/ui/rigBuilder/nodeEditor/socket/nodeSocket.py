import os

import graphicsSocket

import utils.common.fileUtils.jsonUtils as jsonUtils

# load socket config file
import dev.rigging.ui.rigBuilder.nodeEditor.config as config
config_dir = os.path.dirname(config.__file__)
SOCKET_CONFIG = jsonUtils.read(os.path.join(config_dir, 'SOCKET.cfg'))

UNCONNECTED = 0
SINGLE_CONNECTED = 1
MULTI_CONNECTED = 2
AVAILABLE = 3
UNAVAILABLE = 4


class NodeSocket(object):
    """
    node's socket object to handle how socket interact with each other in the viewport
    TODO: 1.add socket name
          2.different colors for states
          3.collapse compound type socket
    """
    INPUT_SOCKET = 0
    OUTPUT_SOCKET = 1

    def __init__(self, node, position=None):
        # store node object for easier access later
        self.node = node
        # socket's position in the node
        self._position = position if position else [0, 0]
        # create graphic socket object
        self.gr_socket = graphicsSocket.GraphicsSocket(self)
        # set graphic socket position
        self.gr_socket.setPos(*self._position)
        # store edges connected to the socket
        self._edge = []
        # socket connection state
        self._state = UNCONNECTED

    def __str__(self):
        return '<NodeSocket {}>'.format(hex(id(self)))

    @property
    def position(self):
        """
        get socket's position in the node
        """
        return self._position

    @property
    def state(self):
        """
        get socket connection state
        """
        return self._state

    @property
    def edge(self):
        """
        get edges connected to the socket
        """
        return self._edge

    @property
    def has_edge(self):
        """
        check if have edge connected to the socket

        Returns:
            True/False
        """
        if self._edge:
            return True
        else:
            return False

    def update_state(self):
        """
        update connection state
        """
        if not self._edge:
            self._state = SOCKET_CONFIG['unconnected']
        elif len(self._edge) == 1:
            self._state = SOCKET_CONFIG['single_connected']
        else:
            self._state = SOCKET_CONFIG['multi_connected']

    def connect_edge(self, edge=None):
        """
        connect given edge with current socket object

        Args:
            edge (nodeEdge): edge object
        """
        if edge and edge not in self._edge:
            self._edge.append(edge)
        # update state
        self.update_state()

    def remove_edge(self, edge=None):
        """
        remove given edge from current socket object

        Args:
            edge (nodeEdge): edge object
        """
        if edge in self._edge:
            self._edge.remove(edge)
        self.update_state()


class InputSocket(NodeSocket):
    """
    input socket object
    """
    def __str__(self):
        return '<InputSocket {}>'.format(hex(id(self)))

    @property
    def socket_type(self):
        """
        get socket type
        """
        return SOCKET_CONFIG['input']


class OutputSocket(NodeSocket):
    """
    output socket object
    """
    def __str__(self):
        return '<OutputSocket {}>'.format(hex(id(self)))

    @property
    def socket_type(self):
        """
        get socket type
        """
        return SOCKET_CONFIG['output']
