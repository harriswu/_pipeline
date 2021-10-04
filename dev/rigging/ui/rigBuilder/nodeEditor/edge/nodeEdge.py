import os

import graphicsEdge

import utils.common.fileUtils.jsonUtils as jsonUtils

# load edge config file
import dev.rigging.ui.rigBuilder.nodeEditor.config as config
config_dir = os.path.dirname(config.__file__)
EDGE_CONFIG = jsonUtils.read(os.path.join(config_dir, 'EDGE.cfg'))


class NodeEdge(object):
    """
    edge object to handle connection between sockets
    TODO: 1. read socket type, can only connect between matching types
    """
    def __init__(self, scene, start_socket, end_socket, edge_type=EDGE_CONFIG['bezier']):
        # store scene object for easier access later
        self.scene = scene

        # store start socket object
        self._start_socket = start_socket
        # store end socket object
        self._end_socket = end_socket

        # connect start socket with current edge node object
        self._start_socket.connect_edge(self)
        if self._end_socket:
            # if end socket given, connect with end socket as well
            self._end_socket.connect_edge(self)

        # define the edge's visual type
        if edge_type == EDGE_CONFIG['direct']:
            self.gr_edge = graphicsEdge.GraphicsEdgeDirect(self)
        else:
            self.gr_edge = graphicsEdge.GraphicsEdgeBezier(self)

        # update the edge's position
        self.update_position()

        # add graphic edge object to scene's graphic node
        self.scene.gr_scene.addItem(self.gr_edge)
        # add current edge object to scene object
        self.scene.add_edge(self)

    def __str__(self):
        return '<NodeEdge {}>'.format(hex(id(self)))

    @property
    def start_socket(self):
        """
        get start socket object for the edge
        """
        return self._start_socket

    @start_socket.setter
    def start_socket(self, value):
        """
        set start socket object for the edge
        Args:
            value (NodeSocket): socket object node
        """
        self._start_socket = value
        self._start_socket.connect_edge(self)

    @property
    def end_socket(self):
        """
        get end socket object for the edge
        """
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value):
        """
        set end socket object for the edge
        Args:
            value (NodeSocket): socket object node
        """
        if value:
            # make sure start and end socket type are different
            if value.socket_type != self._start_socket.socket_type:
                # check start and end socket type, make start socket always output, end socket input
                if value.socket_type == value.INPUT_SOCKET:
                    # value is output socket, put in end socket
                    self._end_socket = value
                    self._end_socket.connect_edge(self)
                else:
                    # value is output, put in start socket, and put previous start socket in end socket
                    self._end_socket = self._start_socket
                    self._start_socket = value
                    self._start_socket.connect_edge(self)
                # update position
                self.update_position()
        else:
            self._end_socket = None

    def update_position(self):
        """
        update edge start and end point position
        """
        pos_source = [self._start_socket.position[0] + self._start_socket.node.position[0],
                      self._start_socket.position[1] + self._start_socket.node.position[1]]
        self.gr_edge.pos_source = pos_source
        if self._end_socket:
            pos_target = [self._end_socket.position[0] + self._end_socket.node.position[0],
                          self._end_socket.position[1] + self._end_socket.node.position[1]]
            self.gr_edge.pos_target = pos_target
        else:
            self.gr_edge.pos_target = pos_source
        self.gr_edge.update()

    def disconnect_sockets(self):
        """
        disconnect edge from start and end sockets
        """
        if self._start_socket:
            self._start_socket.remove_edge(self)
        if self._end_socket:
            self._end_socket.remove_edge(self)
        self._start_socket = None
        self._end_socket = None

    def remove(self):
        """
        remove current edge from scene
        """
        # disconnect edge from sockets
        self.disconnect_sockets()
        # remove graphic edge object from graphic scene
        self.scene.gr_scene.removeItem(self.gr_edge)
        # remove current edge object's graphic edge node
        self.gr_edge = None
        # remove current edge object from scene
        self.scene.remove_edge(self)
