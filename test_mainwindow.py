import pytest
from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow

@pytest.fixture
def app():
    app = QApplication([])
    yield app

@pytest.fixture
def window(app):
    window = MainWindow()
    yield window
    
def test_receive_area(window):
    """测试接收区是否正常工作"""
    test_data = "这是一条测试数据，用于验证接收区是否正常工作。"
    window.update_receive_text(test_data)
    assert "测试数据" in window.receive_text.toPlainText()