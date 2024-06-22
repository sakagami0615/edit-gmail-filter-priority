import sys

from PyQt5.QtWidgets import QApplication

from app.ui.viewer import Viewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = Viewer()
    view.show()
    sys.exit(app.exec_())
