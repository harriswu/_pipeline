from dev.package.ui.qt import *

import dev.rigging.ui.rigBuilder.nodeEditor.scene.nodeScene as nodeScene
import nodeGraphicsView
import node.nodeItem as nodeItem
import dev.rigging.ui.rigBuilder.nodeEditor.edge.nodeEdge as nodeEdge


class NodeEditorWindow(QWidget):
    """
    node editor window widget
    """
    def __init__(self, parent=None):
        super(NodeEditorWindow, self).__init__(parent)

        self.window_title = 'Node Editor'

        self.layout = None
        self.scene = None
        self.gr_scene = None
        self.view = None
        # initialize ui
        self.init_ui()

    def init_ui(self):
        """
        initialize ui
        """
        # set title
        self.setWindowTitle(self.window_title)
        self.setGeometry(200, 200, 800, 600)
        # set layout
        self.layout = QVBoxLayout()
        # remove boarder edge
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # create graphic scene
        self.scene = nodeScene.NodeScene()

        self.add_nodes()

        # create graphic view
        self.view = nodeGraphicsView.NodeGraphicsView(self.scene.gr_scene, self)
        self.layout.addWidget(self.view)

    def add_nodes(self):
        node1 = nodeItem.NodeItem(self.scene, 'Test Node 1', inputs=[1, 2, 3], outputs=[1, 2])
        node2 = nodeItem.NodeItem(self.scene, 'Test Node 2', inputs=[1, 2, 3], outputs=[1, 2])
        node3 = nodeItem.NodeItem(self.scene, 'Test Node 3', inputs=[1, 2, 3], outputs=[1, 2])
        node1.position = [-350, -250]
        node2.position = [-75, 0]
        node3.position = [200, -150]

        edge1 = nodeEdge.NodeEdge(self.scene, node1.outputs[0], node2.inputs[0])
        edge2 = nodeEdge.NodeEdge(self.scene, node2.outputs[0], node3.inputs[0])
