import nodeGraphicsScene


class NodeScene(object):
    """
    scene object to handle how components should interact with each other in the viewport
    """
    def __init__(self):
        # store nodes and edges for further usage
        self.nodes = []
        self.edges = []

        # scene size
        self.width = 64000
        self.height = 64000

        # store graphic scene object
        self.gr_scene = None

        # initialize ui
        self.init_ui()

    def init_ui(self):
        """
        initialize ui, create graphic scene object
        """
        self.gr_scene = nodeGraphicsScene.NodeGraphicsScene(self)
        self.gr_scene.set_gr_scene(self.width, self.height)

    def add_node(self, node):
        """
        add node to the scene

        Args:
            node (nodeItem): node's object
        """
        self.nodes.append(node)

    def add_edge(self, edge):
        """
        add edge to the scene

        Args:
            edge (nodeEdge): edge's object
        """
        self.edges.append(edge)

    def remove_node(self, node):
        """
        remove node from the scene

        Args:
            node (nodeItem): node's object
        """
        self.nodes.remove(node)

    def remove_edge(self, edge):
        """
        remove edge from the scene

        Args:
            edge (nodeEdge): edge's object
        """
        self.edges.remove(edge)
