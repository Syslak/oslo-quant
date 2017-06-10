import sys
from PyQt4.QtGui import QApplication, QWidget, QVBoxLayout, QLabel
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from setproctitle import setproctitle
import datetime
from numpy.linalg import LinAlgError

class LinkedPlotWidget(pg.GraphicsLayoutWidget):
    """Widget for stacking several plots with linked x-axes vertically"""

    mouse_pressed_signal = QtCore.pyqtSignal()
    mouse_released_signal = QtCore.pyqtSignal()

    def __init__(self, inputs, window_title=''):
        """
        args:
           inputs: list of tuples: (numpy_array, data_column_name, plot_title).
                   It is assumed that numpy_array['date'] exists.
           window_title(str): Title of the window
        """
        super().__init__()

        self.setWindowTitle(window_title)

        # label for showing y/x values for crosshair
        self.label = pg.LabelItem(justify='right')
        self.label.setVisible(True)
        self.addItem(self.label)

        # strings for construction self.label, used by self.update_label()
        self.cursor_x_label = ''
        self.cursor_y_label = ''

        # install an event filter to detect that the mouse leaves the widget
        self.installEventFilter(self)

        self.plot_row_counter = 1
        self.first_plot = None
        self.plots = {}

        # create initial plots
        for numpy_array, data_column_name, plot_title in inputs:
            self.add_plot(numpy_array, data_column_name, plot_title)

        self.show()

    def add_plot(self, numpy_array, data_column_name, plot_title):
        """
        Replace plots with new data

        args:
           It is assumed that numpy_array['date'] exists.
        """
        pl = self.addPlot(row=self.plot_row_counter, col=0, title=plot_title,
                          y=numpy_array[data_column_name], x=numpy_array['date'])
        self.plots[plot_title] = pl
        self.plot_row_counter += 1

        # link the x-axes of all plots
        if self.first_plot:
            box = pl.getViewBox()
            box.setXLink(self.first_plot)
        else:
            self.first_plot = pl.getViewBox()

        # set fixed tick label width, to that the plots align vertically
        pl.getAxis('left').setWidth(60)

        # crosshair
        v_line = pg.InfiniteLine(angle=90, movable=False)
        h_line = pg.InfiniteLine(angle=0, movable=False)
        pl.addItem(v_line, ignoreBounds=True)
        pl.addItem(h_line, ignoreBounds=True)

        # vertical line for showing the time position of an event
        event_line = pg.InfiniteLine(angle=90, movable=False)
        event_line.setPen(QtGui.QColor(168, 34, 3))
        pl.addItem(event_line, ignoreBounds=True)

        pl.scene().sigMouseMoved.connect(self.mouse_moved)

        # store references to these things in the PlotView object
        pl.v_line = v_line
        pl.h_line = h_line
        pl.event_line = event_line

    def remove_plot(self, plot_title):
        pl = self.plots.pop(plot_title)
        self.removeItem(pl)

    def remove_all_plots(self):
        for pl_title in list(self.plots):
            self.remove_plot(pl_title)
        self.first_plot = None

    def leaveEvent(self, event):
        """Called when the mouse leaves this widget"""
        self.crosshair_visible(False)
        self.hide_label()

    def vertical_line(self, timestamp):
        """Draw a vertical line at timestamp"""

        for plot in self.plots.values():
            # get a reference to the x-axis numpy data (time column)
            time_col = plot.dataItems[0].xData

            plot.event_line.setPos(timestamp)
            plot.event_line.setVisible(True)

    def crosshair_visible(self, true_or_false):
        """Set closshair visibility"""
        for pl in self.plots.values():
            pl.h_line.setVisible(true_or_false)
            pl.v_line.setVisible(true_or_false)

    def update_label(self, cursor_x, cursor_y):
        """Change the labels. Arguments are floats"""
        timestamp = datetime.date.fromtimestamp(cursor_x)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        text = "<span style='color: Aqua'>x=%s</span>, " \
               "<span style='color: GreenYellow'>x=%0.1f</span>" % (timestamp_str, cursor_y)
        self.label.setText(text)

    def hide_label(self):
        """Hide labels"""
        self.label.setText('')

    def mouse_moved(self, pos):
        """Callback when mouse is moved"""
        mouse_is_over_a_plot = False

        for pl in self.plots.values():
            # ignore plots that are invisible
            if not pl.isVisible():
                continue

            try:
                mousePoint = pl.vb.mapSceneToView(pos)
            except LinAlgError:
                # probably, the plot was replaced, causing this error
                return

            # if the mouse pointer is over this plot
            if pl.sceneBoundingRect().contains(pos):
                mouse_is_over_a_plot = True
                pl.h_line.setVisible(True)
                pl.h_line.setPos(mousePoint.y())
                self.update_label(cursor_x=mousePoint.x(), cursor_y=mousePoint.y())
            else:
                pl.h_line.setVisible(False)

            # set the position of the vertical line
            pl.v_line.setPos(mousePoint.x())

        # if the mouse pointer is over any of the plots
        if mouse_is_over_a_plot:
            for pl in self.plots.values():
                pl.v_line.setVisible(True)
        else:
            self.hide_label()

    def eventFilter(self, widget, event):
        # if the mouse pointer exits the widget
        if event.type() == QtCore.QEvent.MouseMove:
            self.hide_label()
            for pl in self.plots.values():
                pl.h_line.setVisible(False)
                pl.v_line.setVisible(False)
        return False

    def mousePressEvent(self,event):
        super().mousePressEvent(event)
        self.mouse_pressed_signal.emit()

    def mouseReleaseEvent(self,event):
        super().mouseReleaseEvent(event)
        self.mouse_released_signal.emit()

def linked_plot(inputs, window_title=''):
    """Create a windows of linked plots using LinkedPlotWidget

        args:
           inputs: list of tuples: (numpy_array, data_column_name, plot_title).
                   It is assumed that numpy_array['date'] exists.
           window_title(str): Title of the window
    """
    setproctitle("nordnetbot-linkedplot")
    app = QApplication(sys.argv)
    lw = LinkedPlotWidget(inputs, window_title)
    sys.exit(app.exec_())