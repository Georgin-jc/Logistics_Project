from PyQt5 import QtWidgets, QtCore


def tile_page(parent: QtWidgets.QWidget):
    print("Opening Team Visualization Page")

    # Use existing layout
    #layout = parent.layout()
    layout = QtWidgets.QHBoxLayout(parent)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)

    scroll = QtWidgets.QScrollArea()
    scroll.setWidgetResizable(True)
    layout.addWidget(scroll)

    container = QtWidgets.QWidget()
    grid = QtWidgets.QGridLayout(container)
    scroll.setWidget(container)

    teams = [
        {"name": "Nord Bereich", "desc": "Plannung & Logistik"},
        {"name": "Süd Bereich", "desc": "Plannung & Logistik"},
    ]

    def create_tile(team):
        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)

        v = QtWidgets.QVBoxLayout(frame)
        title = QtWidgets.QLabel(team["name"])
        title.setStyleSheet("font-weight:bold; font-size:14px;")

        desc = QtWidgets.QLabel(team["desc"])
        btn = QtWidgets.QPushButton("Open")
        btn.clicked.connect(lambda: print("Opening:", team["name"]))

        v.addWidget(title)
        v.addWidget(desc)
        v.addWidget(btn, 0, QtCore.Qt.AlignRight)

        return frame

    for i, team in enumerate(teams):
        tile = create_tile(team)
        grid.addWidget(tile, i // 3, i % 3)

    for c in range(3):
        grid.setColumnStretch(c, 1)
