from PyQt5.QtWidgets import QMessageBox

def show_info_popup(parent, title, message):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()  # Blocks until OK is clicked
