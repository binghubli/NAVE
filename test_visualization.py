import sys
import numpy as np
import pytest
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg

# 导入要测试的可视化组件
from visualization import ShipAttitudeWidget, AttitudePlot


class VisualizationTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("可视化组件测试")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # 航向角滑块
        heading_layout = QVBoxLayout()
        heading_layout.addWidget(QLabel("航向角 (0-360°)"))
        self.heading_slider = QSlider(Qt.Horizontal)
        self.heading_slider.setRange(0, 360)
        self.heading_slider.setValue(0)
        self.heading_slider.valueChanged.connect(self.update_visualization)
        heading_layout.addWidget(self.heading_slider)
        self.heading_label = QLabel("0°")
        heading_layout.addWidget(self.heading_label)
        control_layout.addLayout(heading_layout)
        
        # 红外方位角滑块
        ir_layout = QVBoxLayout()
        ir_layout.addWidget(QLabel("红外方位角 (0-360°)"))
        self.ir_slider = QSlider(Qt.Horizontal)
        self.ir_slider.setRange(0, 360)
        self.ir_slider.setValue(90)
        self.ir_slider.valueChanged.connect(self.update_visualization)
        ir_layout.addWidget(self.ir_slider)
        self.ir_label = QLabel("90°")
        ir_layout.addWidget(self.ir_label)
        control_layout.addLayout(ir_layout)
        
        # 添加自动模拟按钮
        self.auto_btn = QPushButton("开始自动模拟")
        self.auto_btn.setCheckable(True)
        self.auto_btn.clicked.connect(self.toggle_auto_simulation)
        control_layout.addWidget(self.auto_btn)
        
        # 添加重置按钮
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_visualization)
        control_layout.addWidget(reset_btn)
        
        main_layout.addWidget(control_panel)
        
        # 创建可视化区域
        viz_container = QWidget()
        viz_layout = QHBoxLayout(viz_container)
        
        # 添加船体姿态可视化组件
        self.ship_widget = ShipAttitudeWidget()
        self.ship_widget.setMinimumSize(400, 400)
        viz_layout.addWidget(self.ship_widget)
        
        # 添加曲线图组件
        plot_widget = pg.PlotWidget()
        self.attitude_plot = AttitudePlot(plot_widget)
        viz_layout.addWidget(plot_widget)
        
        main_layout.addWidget(viz_container)
        
        # 设置定时器用于自动模拟和更新图表
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_update)
        
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)  # 100ms更新一次图表
        
        # 初始化时间计数器
        self.time_counter = 0
        
    def update_visualization(self):
        """根据滑块值更新可视化组件"""
        heading = self.heading_slider.value()
        ir = self.ir_slider.value()
        
        # 更新标签
        self.heading_label.setText(f"{heading}°")
        self.ir_label.setText(f"{ir}°")
        
        # 更新船体姿态可视化
        self.ship_widget.update_angles(heading, ir)
        
        # 更新曲线图数据
        self.attitude_plot.update_data(heading, ir)
    
    def update_plot(self):
        """更新曲线图显示"""
        self.attitude_plot.update_plot()
    
    def toggle_auto_simulation(self, checked):
        """切换自动模拟状态"""
        if checked:
            self.auto_btn.setText("停止自动模拟")
            self.auto_timer.start(50)  # 50ms更新一次
            # 禁用滑块
            self.heading_slider.setEnabled(False)
            self.ir_slider.setEnabled(False)
        else:
            self.auto_btn.setText("开始自动模拟")
            self.auto_timer.stop()
            # 启用滑块
            self.heading_slider.setEnabled(True)
            self.ir_slider.setEnabled(True)
    
    def auto_update(self):
        """自动更新数据"""
        self.time_counter += 1
        
        # 生成模拟数据 - 航向角在0-360之间缓慢变化
        heading = (self.time_counter % 360)
        
        # 红外方位角做正弦波变化
        ir = 180 + 90 * np.sin(self.time_counter * 0.05)
        
        # 更新滑块位置
        self.heading_slider.setValue(int(heading))
        self.ir_slider.setValue(int(ir))
        
        # 直接更新可视化（不通过滑块的valueChanged信号）
        self.heading_label.setText(f"{int(heading)}°")
        self.ir_label.setText(f"{int(ir)}°")
        self.ship_widget.update_angles(heading, ir)
        self.attitude_plot.update_data(heading, ir)
    
    def reset_visualization(self):
        """重置可视化组件"""
        # 重置滑块
        self.heading_slider.setValue(0)
        self.ir_slider.setValue(90)
        
        # 如果在自动模式，停止它
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.toggle_auto_simulation(False)
        
        # 重置时间计数器
        self.time_counter = 0


# 添加 PyTest 测试函数
# 修改 PyTest 测试部分
@pytest.fixture(scope="session")
def qapp():
    """创建一个 QApplication 实例用于所有测试"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def ship_widget(qapp):  # 注意这里添加了 qapp 依赖
    """创建一个船体姿态可视化组件用于测试"""
    widget = ShipAttitudeWidget()
    yield widget

@pytest.fixture
def attitude_plot(qapp):  # 注意这里添加了 qapp 依赖
    """创建一个姿态曲线图组件用于测试"""
    plot_widget = pg.PlotWidget()
    plot = AttitudePlot(plot_widget)
    yield plot

def test_ship_widget_initialization(ship_widget):
    """测试船体姿态可视化组件的初始化"""
    assert ship_widget.heading_angle == 0
    assert ship_widget.ir_angle == 0
    assert ship_widget.minimumSize().width() >= 300
    assert ship_widget.minimumSize().height() >= 300

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
    assert len(attitude_plot.heading_data) == 100  # 默认数据长度
    assert len(attitude_plot.ir_data) == 100
    assert len(attitude_plot.time_data) == 100
    
    # 检查初始数据是否为零
    assert all(attitude_plot.heading_data == 0)
    assert all(attitude_plot.ir_data == 0)

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


# 如果直接运行此文件，则启动可视化测试窗口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VisualizationTestWindow()
    window.show()
    sys.exit(app.exec_())