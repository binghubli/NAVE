import sys
import pytest
import numpy as np
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg

# 导入要测试的可视化组件
from visualization import ShipAttitudeWidget, AttitudePlot

# 创建一个 QApplication 实例用于所有测试
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def ship_widget(qapp):
    widget = ShipAttitudeWidget()
    yield widget

@pytest.fixture
def attitude_plot(qapp):
    plot_widget = pg.PlotWidget()
    plot = AttitudePlot(plot_widget)
    yield plot

def test_ship_widget_initialization(ship_widget):
    """测试船体姿态可视化组件的初始化"""
    assert hasattr(ship_widget, 'heading_angle')
    assert hasattr(ship_widget, 'ir_angle')
    assert ship_widget.minimumSize().width() > 0
    assert ship_widget.minimumSize().height() > 0

def test_ship_widget_update(ship_widget):
    """测试船体姿态可视化组件的更新功能"""
    # 更新角度
    ship_widget.update_angles(45, 90)
    assert ship_widget.heading_angle == 45
    assert ship_widget.ir_angle == 90
    
    # 再次更新
    ship_widget.update_angles(180, 270)
    assert ship_widget.heading_angle == 180
    assert ship_widget.ir_angle == 270

def test_attitude_plot_initialization(attitude_plot):
    """测试姿态曲线图组件的初始化"""
    assert hasattr(attitude_plot, 'heading_data')
    assert hasattr(attitude_plot, 'ir_data')
    assert hasattr(attitude_plot, 'time_data')
    
    # 检查数据数组是否已初始化
    assert len(attitude_plot.heading_data) > 0
    assert len(attitude_plot.ir_data) > 0
    assert len(attitude_plot.time_data) > 0

def test_attitude_plot_update(attitude_plot):
    """测试姿态曲线图组件的更新功能"""
    # 更新数据
    attitude_plot.update_data(45, 90)
    assert attitude_plot.heading_data[-1] == 45
    assert attitude_plot.ir_data[-1] == 90
    
    # 再次更新
    attitude_plot.update_data(180, 270)
    assert attitude_plot.heading_data[-1] == 180
    assert attitude_plot.ir_data[-1] == 270