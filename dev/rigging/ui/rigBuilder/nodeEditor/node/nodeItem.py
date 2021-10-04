import os

import dev.rigging.ui.rigBuilder.nodeEditor.socket.nodeSocket as nodeSocket
import graphicsNodeItem

import utils.common.fileUtils.jsonUtils as jsonUtils

# load socket config file
import dev.rigging.ui.rigBuilder.nodeEditor.config as config
config_dir = os.path.dirname(config.__file__)
SOCKET_CONFIG = jsonUtils.read(os.path.join(config_dir, 'SOCKET.cfg'))


class NodeItem(object):
    """
    node object to handle how node interact with each other in the viewport
    TODO: 1. collapse node like maya
          2. change title name
          3. read node preset from json file
          4. compound node, double click to access lower level
    """
    def __init__(self, scene, title='Undefined Node', inputs=None, outputs=None):
        # set inputs and outputs as empty list if not have anything
        if not inputs:
            inputs = []
        if not outputs:
            outputs = []

        # store scene object for easier access later
        self.scene = scene
        # store the title name
        self.title = title

        # create node's graphic node to visually present in the scene
        self.gr_node = graphicsNodeItem.GraphicsNodeItem(self)
        # add node object to the scene
        self.scene.add_node(self)
        # add node graphic object to graphic scene
        self.scene.gr_scene.addItem(self.gr_node)

        # create sockets for inputs and outputs
        self.socket_spacing = 22

        self.inputs = []
        self.outputs = []

        for i, item in enumerate(inputs):
            # loop into each input, and calculate the position
            socket_position = self.get_socket_position(i, SOCKET_CONFIG['input'])
            # create socket object
            socket = nodeSocket.InputSocket(node=self, position=socket_position)
            # append to input list
            self.inputs.append(socket)

        for i, item in enumerate(outputs):
            # loop into each output, and calculate the position
            socket_position = self.get_socket_position(i, SOCKET_CONFIG['output'])
            # create socket object
            socket = nodeSocket.OutputSocket(node=self, position=socket_position)
            # append to output list
            self.outputs.append(socket)

    def __str__(self):
        return '<NodeItem {}>'.format(hex(id(self)))

    @property
    def position(self):
        """
        get current node position in the scene
        """
        return self.gr_node.pos().x(), self.gr_node.pos().y()

    @position.setter
    def position(self, value):
        """
        set current node position in the scene

        Args:
            value (list): node's x and y position values
        """
        self.gr_node.setPos(value[0], value[1])

    def get_socket_position(self, index, socket_type):
        """
        calculate the socket position on the current node

        Args:
            index (int): the socket index on the current column (input/output)
            socket_type (int): the socket is input socket or output socket
        """
        if socket_type == SOCKET_CONFIG['input']:
            # input starts from left
            x = 0
            # input starts from bottom
            y = self.gr_node.height - self.gr_node.padding - self.gr_node.edge_size - index * self.socket_spacing
        else:
            # output starts from right
            x = self.gr_node.width
            # output starts from top
            y = self.gr_node.title_height + self.gr_node.padding + self.gr_node.edge_size + index * self.socket_spacing

        return x, y

    def update_connected_edges(self):
        """
        update all edges position connected to the current node
        """
        for socket in self.inputs + self.outputs:
            # loop into each socket in the node
            if socket.has_edge:
                # check if the socket has an edge
                for edge in socket.edge:
                    # if has the edge, update the position
                    edge.update_position()

    def remove(self):
        """
        remove current node from the scene
        """
        # remove all edges from sockets
        for socket in self.inputs + self.outputs:
            if socket.has_edge:
                for edge in socket.edge:
                    edge.remove()
        # remove graphic node
        self.scene.gr_scene.removeItem(self.gr_node)
        self.gr_node = None
        # remove node from scene
        self.scene.remove_node(self)
