import os

from dev.package.ui.qt import *

import dev.rigging.ui.rigBuilder.nodeEditor.socket.graphicsSocket as graphicsSocket
import dev.rigging.ui.rigBuilder.nodeEditor.edge.nodeEdge as nodeEdge
import dev.rigging.ui.rigBuilder.nodeEditor.edge.graphicsEdge as graphicsEdge
import dev.rigging.ui.rigBuilder.nodeEditor.edge.graphicsCutLine as graphicsCutLine

import utils.common.fileUtils.jsonUtils as jsonUtils

# load edge config file
import config
config_dir = os.path.dirname(config.__file__)
EDGE_CONFIG = jsonUtils.read(os.path.join(config_dir, 'EDGE.cfg'))
SOCKET_CONFIG = jsonUtils.read(os.path.join(config_dir, 'SOCKET.cfg'))


class NodeGraphicsView(QGraphicsView):
    """
    graphic view object handle how everything should be visually present in the viewport
    """
    def __init__(self, scene, parent=None):
        super(NodeGraphicsView, self).__init__(parent)
        # store graphic scene node for eaiser access later
        self.gr_scene = scene
        # initialize ui
        self.init_ui()
        self.setScene(self.gr_scene)
        # set edge interact mode, by default should be no operation
        self.mode = EDGE_CONFIG['no_op']

        # zoom preset
        self._zoom_in_factor = 1.25
        self._zoom_clamp = False
        self._zoom = 0
        self._zoom_step = 1
        self._zoom_range = [-10, 10]

        # cut line
        self.cut_line = graphicsCutLine.GraphicsCutLine()
        self.gr_scene.addItem(self.cut_line)

        # store dragging edge while mouse is moving, by default should be None
        self.drag_edge = None

    @property
    def zoom_in_factor(self):
        return self._zoom_in_factor

    @property
    def zoom_clamp(self):
        return self._zoom_clamp

    @property
    def zoom(self):
        return self._zoom

    @property
    def zoom_step(self):
        return self._zoom_step

    @property
    def zoom_range(self):
        return self._zoom_range

    def init_ui(self):
        """
        initialize ui
        """
        self.setRenderHints(QPainter.Antialiasing | QPainter.HighQualityAntialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        # always update the full viewport
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # turn off scroll bar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # set the anchor point under mouse, basically when we zoom in/out, it starts from where the mouse is
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        # enable multi selection by dragging
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_press(event)
        elif event.button() == Qt.LeftButton:
            self.left_mouse_button_press(event)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button_press(event)
        else:
            super(NodeGraphicsView, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_release(event)
        elif event.button() == Qt.LeftButton:
            self.left_mouse_button_release(event)
        elif event.button() == Qt.RightButton:
            self.right_mouse_button_release(event)
        else:
            super(NodeGraphicsView, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == EDGE_CONFIG['drag']:
            # drag edge
            pos = self.mapToScene(event.pos())
            # set target socket and update the edge
            self.drag_edge.gr_edge.pos_target = [pos.x(), pos.y()]
            self.drag_edge.gr_edge.update()

        elif self.mode == EDGE_CONFIG['cut']:
            pos = self.mapToScene(event.pos())
            self.cut_line.line_points.append(pos)
            self.cut_line.update()

        super(NodeGraphicsView, self).mouseMoveEvent(event)

    def left_mouse_button_press(self, event):
        item = self.get_item_at_click(event)
        # shift select
        if hasattr(item, 'node') or isinstance(item, graphicsEdge.GraphicsEdge) or item is None:
            if event.modifiers() & Qt.ShiftModifier:
                event.ignore()
                fake_event = QMouseEvent(QEvent.MouseButtonPress, event.localPos(), event.screenPos(),
                                         Qt.LeftButton, event.buttons() | Qt.LeftButton,
                                         event.modifiers() | Qt.ControlModifier)
                super(NodeGraphicsView, self).mousePressEvent(fake_event)
                return

        if isinstance(item, graphicsSocket.GraphicsSocket):
            # if mouse clicked a socket, then check if need to drag an edge
            if self.mode == EDGE_CONFIG['no_op']:
                # start dragging
                self.mode = EDGE_CONFIG['drag']
                self.edge_drag_start(item)
                return

        if self.mode == EDGE_CONFIG['drag']:
            # edge dragging happens already when mouse click, check what's the mouse clicked, and end the dragging
            return_val = self.edge_drag_end(item)
            if return_val:
                return

        if item is None:
            # cut line only happens when nothing selected
            if event.modifiers() & Qt.ControlModifier:
                # trigger cut mode
                self.mode = EDGE_CONFIG['cut']
                fake_event = QMouseEvent(QEvent.MouseButtonRelease, event.localPos(), event.screenPos(),
                                         Qt.LeftButton, Qt.NoButton, event.modifiers())
                super(NodeGraphicsView, self).mouseReleaseEvent(fake_event)
                # override cursor
                QApplication.setOverrideCursor(Qt.CrossCursor)
                return

        super(NodeGraphicsView, self).mousePressEvent(event)

    def right_mouse_button_press(self, event):
        super(NodeGraphicsView, self).mousePressEvent(event)

    def middle_mouse_button_press(self, event):
        release_event = QMouseEvent(QEvent.MouseButtonRelease, event.localPos(), event.screenPos(), Qt.LeftButton,
                                    Qt.NoButton, event.modifiers())
        super(NodeGraphicsView, self).mouseReleaseEvent(release_event)
        # use middle mouse button to do pan move
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        fake_event = QMouseEvent(event.type(), event.localPos(), event.screenPos(), Qt.LeftButton,
                                 event.buttons() | Qt.LeftButton, event.modifiers())
        super(NodeGraphicsView, self).mousePressEvent(fake_event)

    def left_mouse_button_release(self, event):
        item = self.get_item_at_click(event)

        if hasattr(item, 'node') or isinstance(item, graphicsEdge.GraphicsEdge) or item is None:
            # multi selection
            if event.modifiers() & Qt.ShiftModifier:
                event.ignore()
                fake_event = QMouseEvent(event.type(), event.localPos(), event.screenPos(),
                                         Qt.LeftButton, Qt.NoButton,
                                         event.modifiers() | Qt.ControlModifier)
                super(NodeGraphicsView, self).mouseReleaseEvent(fake_event)
                return

        if self.mode == EDGE_CONFIG['cut']:
            # remove intersect edges
            self.cut_intersecting_edges()
            # reset cut line points
            self.cut_line.line_points = []
            self.cut_line.update()
            # set back cursor
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            # reset edge mode
            self.mode = EDGE_CONFIG['no_op']
            return

        super(NodeGraphicsView, self).mouseReleaseEvent(event)

    def right_mouse_button_release(self, event):
        super(NodeGraphicsView, self).mouseReleaseEvent(event)

    def middle_mouse_button_release(self, event):
        fake_event = QMouseEvent(event.type(), event.localPos(), event.screenPos(), Qt.LeftButton,
                                 event.buttons() | Qt.LeftButton, event.modifiers())
        super(NodeGraphicsView, self).mouseReleaseEvent(fake_event)
        self.setDragMode(QGraphicsView.NoDrag)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            super(NodeGraphicsView, self).keyPressEvent(event)

    def wheelEvent(self, event):
        # calculate out zoom factor
        zoom_out_factor = 1 / self._zoom_in_factor

        # calculate zoom
        if event.angleDelta().y() > 0:
            zoom_factor = self._zoom_in_factor
            self._zoom += self._zoom_step
        else:
            zoom_factor = zoom_out_factor
            self._zoom -= self._zoom_step

        clamp = False
        if self._zoom < self._zoom_range[0]:
            self._zoom = self._zoom_range[0]
            clamp = True
        elif self._zoom > self._zoom_range[1]:
            self._zoom = self._zoom_range[1]
            clamp = True

        # set scene scale
        if not clamp or not self._zoom_clamp:
            self.scale(zoom_factor, zoom_factor)

    def get_item_at_click(self, event):
        """
        get mouse clicked item object
        """
        pos = event.pos()
        obj = self.itemAt(pos)
        return obj

    def edge_drag_start(self, item):
        """
        start the edge dragging

        Args:
            item (GraphicsSocket): graphics socket object
        """
        self.drag_edge = nodeEdge.NodeEdge(self.gr_scene.scene, item.socket, None, EDGE_CONFIG['bezier'])

    def edge_drag_end(self, item):
        """
        end the edge dragging mode
        return True if skip the rest of the code
        """
        self.mode = EDGE_CONFIG['no_op']
        if isinstance(item, graphicsSocket.GraphicsSocket):
            # make sure two sockets are different type, it must be one input one output
            if self.drag_edge.start_socket.socket_type != item.socket.socket_type:
                # connect edge
                self.drag_edge.end_socket = item.socket
                # if the input socket already has previous edge connected, get the edge and remove it
                self.clear_previous_edge(self.drag_edge.start_socket)
                self.clear_previous_edge(self.drag_edge.end_socket)

                return True
        # remove the dragging edge
        self.drag_edge.remove()
        self.drag_edge = None

        return False

    def delete_selected(self):
        """
        remove selected items from scene
        """
        for item in self.gr_scene.selectedItems():
            if hasattr(item, 'node'):
                # if selected is a nodeItem, remove the node, it will remove connected edges as well
                item.node.remove()
            elif isinstance(item, graphicsEdge.GraphicsEdge) and item in self.gr_scene.items():
                # if selected is an edge, we need to check if the edge still in the scene or not
                # because if we delete the nodeItem first, it may delete the edge already
                item.edge.remove()

    def cut_intersecting_edges(self):
        """
        cut the edge if it's intersect with cut line
        """
        # loop into each two points in the cut line
        for x in range(len(self.cut_line.line_points[:-1])):
            p1 = self.cut_line.line_points[x]
            p2 = self.cut_line.line_points[x + 1]
            # loop into each edge in the scene
            for edge in self.gr_scene.scene.edges:
                if edge.gr_edge.intersect_with(p1, p2):
                    # remove the edge if intersect
                    edge.remove()

    @staticmethod
    def clear_previous_edge(socket):
        """
        clear given input socket's previous connected edges

        Args:
            socket (InputSocket):

        Returns:

        """
        if socket.socket_type == SOCKET_CONFIG['input']:
            # get all edges, clear all except the last one
            for edge in socket.edge[:-1]:
                edge.remove()
            # update socket state because edge number changed
            socket.update_state()
