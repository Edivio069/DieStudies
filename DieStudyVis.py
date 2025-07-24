import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Wedge
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout,
    QWidget, QPushButton, QTableView, QLabel, QHBoxLayout,
    QMessageBox, QComboBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class DualColorCoinViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dual-Colored Coin Viewer")
        self.setGeometry(100, 100, 1000, 700)

        self.df = pd.DataFrame()

        self.canvas = FigureCanvas(plt.Figure())
        self.table = QTableView()
        self.load_button = QPushButton("Load CSV")
        self.plot_button = QPushButton("Plot Coins")
        self._suppress_next_drag = False


        self.x_column = QComboBox()
        self.y_column = QComboBox()
        self.obv_column = QComboBox()
        self.rev_column = QComboBox()

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("X:"))
        control_layout.addWidget(self.x_column)
        control_layout.addWidget(QLabel("Y:"))
        control_layout.addWidget(self.y_column)
        control_layout.addWidget(QLabel("Obverse:"))
        control_layout.addWidget(self.obv_column)
        control_layout.addWidget(QLabel("Reverse:"))
        control_layout.addWidget(self.rev_column)
        control_layout.addWidget(self.plot_button)

        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        
        self.load_button.clicked.connect(self.load_csv)
        self.plot_button.clicked.connect(self.plot_coins)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV files (*.csv)")
        if path:
            self.df = pd.read_csv(path)
            self.update_table()
            self.update_dropdowns()

    def update_table(self):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self.df.columns.tolist())
        for row in self.df.itertuples(index=False):
            items = [QStandardItem(str(val)) for val in row]
            model.appendRow(items)
        self.table.setModel(model)

    def update_dropdowns(self):
        self.x_column.clear()
        self.y_column.clear()
        self.obv_column.clear()
        self.rev_column.clear()

        self.x_column.addItems(self.df.columns)
        self.y_column.addItems(self.df.columns)
        self.obv_column.addItems(self.df.columns)
        self.rev_column.addItems(self.df.columns)

    def plot_coins(self):
        x_col = self.x_column.currentText()
        y_col = self.y_column.currentText()
        obv_col = self.obv_column.currentText()
        rev_col = self.rev_column.currentText()

        if not all([x_col, y_col, obv_col, rev_col]):
            return

        x = self.df[x_col]
        y = self.df[y_col]
        obv = self.df[obv_col]
        rev = self.df[rev_col]

        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.set_axis_off()

        # Color maps
        obv_unique = obv.unique()
        rev_unique = rev.unique()
        obv_palette = sns.color_palette("Set1", len(obv_unique))
        rev_palette = sns.color_palette("Set2", len(rev_unique))

        obv_map = {val: obv_palette[i] for i, val in enumerate(obv_unique)}
        rev_map = {val: rev_palette[i] for i, val in enumerate(rev_unique)}

        self.patches = []
        radius = 0.1
        for i, (xi, yi, o, r) in enumerate(zip(x, y, obv, rev)):
            # Left half (obverse)
            wedge1 = Wedge(center=(xi, yi), r=radius, theta1=90, theta2=270,
                           facecolor=obv_map[o], edgecolor='black', picker=True)
            wedge1.set_gid(i)  
            ax.add_patch(wedge1)

            # Right half (reverse)
            wedge2 = Wedge(center=(xi, yi), r=radius, theta1=270, theta2=90,
                           facecolor=rev_map[r], edgecolor='black', picker=True)
            wedge2.set_gid(i)
            ax.add_patch(wedge2)

            self.patches.append((wedge1, wedge2))

        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("pick_event", self.on_click)
        ax.relim()
        ax.autoscale_view()
        self.canvas.draw()

    def on_click(self, event):
        if event.mouseevent.button != 1:
            return

        self._suppress_next_drag = True  # prevent drag after click

        ind = event.artist.get_gid()
        row = self.df.iloc[ind]
        msg = (
            f"Name: {row['name']}\n"
            f"Obverse Group: {row['obverse_group']}\n"
            f"Reverse Group: {row['reverse_group']}"
        )
        QMessageBox.information(self, "Coin Info", msg)



    def on_scroll(self, event):
        base_scale = 1.2  
        ax = self.canvas.figure.axes[0]  

        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return  

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        x_left, x_right = cur_xlim
        y_bottom, y_top = cur_ylim

        x_range = (x_right - x_left)
        y_range = (y_top - y_bottom)

        if event.button == 'up':
            
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            
            scale_factor = base_scale
        else:
            
            scale_factor = 1

        new_xlim = [xdata - x_range * scale_factor / 2,
                    xdata + x_range * scale_factor / 2]
        new_ylim = [ydata - y_range * scale_factor / 2,
                    ydata + y_range * scale_factor / 2]

        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        self.canvas.draw_idle()
        
    def on_press(self, event):
        if getattr(self, "_suppress_next_drag", False):
            self._suppress_next_drag = False  # reset flag
            return  # skip starting drag

        if event.button == 1 and event.inaxes:
            self._is_dragging = True
            self._drag_start = (event.xdata, event.ydata)
            self._xlim_start = event.inaxes.get_xlim()
            self._ylim_start = event.inaxes.get_ylim()



    def on_motion(self, event):
        if getattr(self, "_is_dragging", False) and event.inaxes and event.xdata and event.ydata:
            dx = event.xdata - self._drag_start[0]
            dy = event.ydata - self._drag_start[1]
            ax = event.inaxes

            new_xlim = (self._xlim_start[0] - dx, self._xlim_start[1] - dx)
            new_ylim = (self._ylim_start[0] - dy, self._ylim_start[1] - dy)

            ax.set_xlim(new_xlim)
            ax.set_ylim(new_ylim)
            self.canvas.draw_idle()

    def on_release(self, event):
        self._is_dragging = False



if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = DualColorCoinViewer()
    viewer.show()
    sys.exit(app.exec())
