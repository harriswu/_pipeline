from dev.package.ui.qt import *


class GraphicsNodeItem(QGraphicsItem):
    """
    node's graphic object, handle how node should visually behave in viewport
    """
    def __init__(self, node, parent=None):
        super(GraphicsNodeItem, self).__init__(parent)
        # store node edge class for easier access later
        self.node = node

        # visual preset
        self._title_color = Qt.white
        self._title_font = QFont('Arial', 10)
        self.title_item = None

        self._width = 180
        self._height = 240
        self._edge_size = 10.0
        self._title_height = 24.0
        self._padding = 5.0

        self._pen_default = QPen(QColor('#7F000000'))
        self._pen_selected = QPen(QColor('#FFFFA637'))

        self._brush_title = QBrush(QColor('#FF313131'))
        self._brush_background = QBrush(QColor('#E3212121'))

        # init title
        self.init_title()
        self.title = self.node.title

        # init sockets
        self.init_socket()

        # init ui
        self.init_ui()

    @property
    def title(self):
        """
        get node's name
        """
        return self._title

    @title.setter
    def title(self, value):
        """
        set node's title with given name

        Args:
            value (str): node's title name
        """
        self._title = value
        self.title_item.setPlainText(self._title)

    @property
    def width(self):
        """
        get node's width value
        """
        return self._width

    @property
    def height(self):
        """
        get node's height value
        """
        return self._height

    @property
    def edge_size(self):
        """
        get node's edge size
        """
        return self._edge_size

    @property
    def title_height(self):
        """
        get title's height
        """
        return self._title_height

    @property
    def padding(self):
        """
        get padding value
        """
        return self._padding

    def mouseMoveEvent(self, event):
        """
        event occurs when mouse moving
        """
        super(GraphicsNodeItem, self).mouseMoveEvent(event)
        # need optimize, just update the selected nodes
        for node in self.scene().scene.nodes:
            if node.gr_node.isSelected():
                node.update_connected_edges()

    def init_title(self):
        """
        initialize title
        """
        self.title_item = QGraphicsTextItem(self)
        self.title_item.node = self.node
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)
        self.title_item.setPos(self._padding, 0)
        self.title_item.setTextWidth(self._width - 2 * self._padding)

    def init_socket(self):
        """
        initialize sockets
        """
        pass

    def init_ui(self):
        """
        initialize node's ui
        """
        # make node selectable in the scene
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        # make node movable in the scene
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def boundingRect(self):
        """
        defines the outer bounds of the item as a rectangle
        """
        return QRectF(0, 0, self._width, self._height).normalized()

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        """
        paint node in viewport
        """
        # content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundRect(0, 0, self._width, self._height, self._edge_size, self._edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.WindingFill)
        path_title.addRoundRect(0, 0, self._width, self._title_height, self._edge_size, self._edge_size)
        path_title.addRect(0, self._title_height - self._edge_size, self._edge_size, self._edge_size)
        path_title.addRect(self._width - self._edge_size, 0, self._edge_size, self._edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # outline
        path_outline = QPainterPath()
        path_outline.addRoundRect(0, 0, self._width, self._height, self._edge_size, self._edge_size)
        painter.setPen(self._pen_default if not self.isSelected() else self._pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_outline.simplified())
