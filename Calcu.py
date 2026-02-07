from PyQt5 import QtWidgets, QtCore


def calculator_page(parent: QtWidgets.QWidget):
    #layout = parent.layout()
    layout = QtWidgets.QHBoxLayout(parent)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(10)

    # ============================
    # CALCULATOR FRAME (BOX)
    # ============================
    calc_frame = QtWidgets.QFrame()
    calc_frame.setFrameShape(QtWidgets.QFrame.Box)
    calc_frame.setLineWidth(2)

    calc_frame.setStyleSheet("""
        QFrame {
            background-color: #f0f0f0;
            border: 2px solid #888;
            border-radius: 10px;
        }
        QPushButton {
            font-size: 16px;
        }
    """)

    calc_layout = QtWidgets.QVBoxLayout(calc_frame)
    calc_layout.setContentsMargins(15, 15, 15, 15)
    calc_layout.setSpacing(10)

    # ============================
    # DISPLAY ENTRY
    # ============================
    entry = QtWidgets.QLineEdit()
    entry.setAlignment(QtCore.Qt.AlignRight)
    entry.setFixedHeight(45)
    entry.setFixedWidth(260)
    entry.setStyleSheet("font-size: 20px; padding: 5px;")
    calc_layout.addWidget(entry)

    # ============================
    # GRID OF BUTTONS
    # ============================
    grid = QtWidgets.QGridLayout()
    grid.setSpacing(8)
    calc_layout.addLayout(grid)

    def click_button(value):
        entry.insert(value)

    def clear():
        entry.clear()

    def calculate():
        try:
            result = str(eval(entry.text()))
            entry.setText(result)
        except Exception:
            entry.setText("Error")

    buttons = [
        "7", "8", "9", "/",
        "4", "5", "6", "*",
        "1", "2", "3", "-",
        "0", ".", "=", "+"
    ]

    row, col = 0, 0
    for button in buttons:
        btn = QtWidgets.QPushButton(button)
        btn.setFixedSize(60, 45)

        if button == "=":
            btn.clicked.connect(calculate)
        else:
            btn.clicked.connect(lambda _, b=button: click_button(b))

        grid.addWidget(btn, row, col)

        col += 1
        if col > 3:
            col = 0
            row += 1

    # ============================
    # CLEAR BUTTON
    # ============================
    clear_btn = QtWidgets.QPushButton("C")
    clear_btn.setFixedSize(260, 40)
    clear_btn.setStyleSheet("background-color: #ffcccc; font-weight: bold;")
    clear_btn.clicked.connect(clear)
    calc_layout.addWidget(clear_btn)

    # ============================
    # ADD CALCULATOR TO RIGHT SIDE
    # ============================
    layout.setContentsMargins(10, 0, 10, 0)
    layout.addWidget(calc_frame, alignment=QtCore.Qt.AlignRight)

