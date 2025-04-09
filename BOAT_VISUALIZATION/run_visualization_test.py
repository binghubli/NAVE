import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QSlider, QLabel, QGroupBox)
from PyQt5.QtCore import Qt, QTimer

# 导入要测试的可视化组件
from visualization import ShipAttitudeWidget, AttitudePlot
import pyqtgraph as pg

class VisualizationTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("船体姿态可视化测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建控制面板
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)
        
        # 航向角控制
        heading_group = QGroupBox("航向角")
        heading_layout = QVBoxLayout(heading_group)
        
        self.heading_slider = QSlider(Qt.Horizontal)
        self.heading_slider.setRange(0, 360)
        self.heading_slider.setValue(0)
        self.heading_slider.setTickPosition(QSlider.TicksBelow)
        self.heading_slider.setTickInterval(30)
        self.heading_slider.valueChanged.connect(self.update_visualization)
        
        self.heading_label = QLabel("当前值: 0°")
        heading_layout.addWidget(self.heading_label)
        heading_layout.addWidget(self.heading_slider)
        
        control_layout.addWidget(heading_group)
        
        # 红外方位角控制
        ir_group = QGroupBox("红外方位角")
        ir_layout = QVBoxLayout(ir_group)
        
        self.ir_slider = QSlider(Qt.Horizontal)
        self.ir_slider.setRange(0, 360)
        self.ir_slider.setValue(90)
        self.ir_slider.setTickPosition(QSlider.TicksBelow)
        self.ir_slider.setTickInterval(30)
        self.ir_slider.valueChanged.connect(self.update_visualization)
        
        self.ir_label = QLabel("当前值: 90°")
        ir_layout.addWidget(self.ir_label)
        ir_layout.addWidget(self.ir_slider)
        
        control_layout.addWidget(ir_group)
        
        # 自动演示控制
        demo_group = QGroupBox("自动演示")
        demo_layout = QVBoxLayout(demo_group)
        
        self.auto_btn = QPushButton("开始自动演示")
        self.auto_btn.setCheckable(True)
        self.auto_btn.clicked.connect(self.toggle_auto_demo)
        demo_layout.addWidget(self.auto_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_visualization)
        demo_layout.addWidget(reset_btn)
        
        control_layout.addWidget(demo_group)
        
        main_layout.addWidget(control_group)
        
        # 创建可视化区域
        viz_container = QWidget()
        viz_layout = QHBoxLayout(viz_container)
        
        # 船体姿态可视化
        ship_group = QGroupBox("船体姿态")
        ship_layout = QVBoxLayout(ship_group)
        
        self.ship_widget = ShipAttitudeWidget()
        self.ship_widget.setMinimumSize(400, 400)
        ship_layout.addWidget(self.ship_widget)
        
        viz_layout.addWidget(ship_group)
        
        # 曲线图
        plot_group = QGroupBox("姿态曲线")
        plot_layout = QVBoxLayout(plot_group)
        
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('w')
        plot_widget.setLabel('left', '角度', units='°')
        plot_widget.setLabel('bottom', '时间', units='s')
        plot_widget.addLegend()
        plot_widget.showGrid(x=True, y=True)
        
        # 设置曲线图显示范围和滚动功能
        plot_widget.setXRange(-100, 0)  # 初始显示最近100个时间点
        plot_widget.setYRange(-10, 370)  # 设置Y轴范围略大于0-360度
        plot_widget.setAutoVisible(y=False)  # 禁用Y轴自动调整
        plot_widget.enableAutoRange(axis='x', enable=False)  # 禁用X轴自动调整
        
        # 添加滚动控制按钮
        scroll_layout = QHBoxLayout()
        
        zoom_in_btn = QPushButton("放大")
        zoom_in_btn.clicked.connect(lambda: self.zoom_plot(factor=0.8))
        scroll_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("缩小")
        zoom_out_btn.clicked.connect(lambda: self.zoom_plot(factor=1.2))
        scroll_layout.addWidget(zoom_out_btn)
        
        scroll_left_btn = QPushButton("←")
        scroll_left_btn.clicked.connect(lambda: self.scroll_plot(direction=-1))
        scroll_layout.addWidget(scroll_left_btn)
        
        scroll_right_btn = QPushButton("→")
        scroll_right_btn.clicked.connect(lambda: self.scroll_plot(direction=1))
        scroll_layout.addWidget(scroll_right_btn)
        
        auto_scroll_btn = QPushButton("自动滚动")
        auto_scroll_btn.setCheckable(True)
        auto_scroll_btn.setChecked(True)
        auto_scroll_btn.clicked.connect(self.toggle_auto_scroll)
        scroll_layout.addWidget(auto_scroll_btn)
        
        self.auto_scroll = True  # 默认启用自动滚动
        self.plot_widget = plot_widget  # 保存引用以便在其他方法中使用
        self.auto_scroll_btn = auto_scroll_btn  # 保存引用以便在其他方法中使用
        
        plot_layout.addWidget(plot_widget)
        plot_layout.addLayout(scroll_layout)
        
        self.attitude_plot = AttitudePlot(plot_widget)
        
        viz_layout.addWidget(plot_group)
        
        main_layout.addWidget(viz_container, 1)  # 1表示拉伸因子
        
        # 设置定时器
        self.auto_timer = QTimer()
        self.auto_timer.timeout.connect(self.auto_update)
        
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(100)  # 100ms更新一次图表
        
        # 初始化时间计数器
        self.time_counter = 0
        
        # 初始化可视化
        self.update_visualization()
    
    def update_visualization(self):
        """根据滑块值更新可视化组件"""
        heading = self.heading_slider.value()
        ir = self.ir_slider.value()
        
        # 更新标签
        self.heading_label.setText(f"当前值: {heading}°")
        self.ir_label.setText(f"当前值: {ir}°")
        
        # 更新船体姿态可视化
        self.ship_widget.update_angles(heading, ir)
        
        # 更新曲线图数据
        self.attitude_plot.update_data(heading, ir)
    
    def update_plot(self):
        """更新曲线图显示"""
        self.attitude_plot.update_plot()
        
        # 如果启用了自动滚动，则调整X轴范围以显示最新数据
        if self.auto_scroll and len(self.attitude_plot.time_data) > 0:
            x_min = max(-100, -len(self.attitude_plot.time_data))
            self.plot_widget.setXRange(x_min, 0)
    
    def zoom_plot(self, factor):
        """缩放曲线图"""
        # 获取当前X轴范围
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        x_min, x_max = x_range
        
        # 计算中心点
        center = (x_min + x_max) / 2
        
        # 计算新的范围
        half_width = (x_max - x_min) / 2 * factor
        
        # 设置新的范围
        self.plot_widget.setXRange(center - half_width, center + half_width)
        
        # 如果缩放，则禁用自动滚动
        if factor != 1.0:
            self.auto_scroll = False
            self.auto_scroll_btn.setChecked(False)
    
    def scroll_plot(self, direction):
        """滚动曲线图"""
        # 获取当前X轴范围
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        x_min, x_max = x_range
        
        # 计算滚动量（当前视图宽度的20%）
        scroll_amount = (x_max - x_min) * 0.2 * direction
        
        # 设置新的范围
        self.plot_widget.setXRange(x_min + scroll_amount, x_max + scroll_amount)
        
        # 如果手动滚动，则禁用自动滚动
        self.auto_scroll = False
        self.auto_scroll_btn.setChecked(False)
    
    def toggle_auto_scroll(self, checked):
        """切换自动滚动状态"""
        self.auto_scroll = checked
        
        # 如果启用了自动滚动，立即滚动到最新数据
        if checked and len(self.attitude_plot.time_data) > 0:
            x_min = max(-100, -len(self.attitude_plot.time_data))
            self.plot_widget.setXRange(x_min, 0)
    
    def toggle_auto_demo(self, checked):
        """切换自动演示状态"""
        if checked:
            self.auto_btn.setText("停止自动演示")
            self.auto_timer.start(50)  # 50ms更新一次
            # 禁用滑块
            self.heading_slider.setEnabled(False)
            self.ir_slider.setEnabled(False)
        else:
            self.auto_btn.setText("开始自动演示")
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
    
    def reset_visualization(self):
        """重置可视化组件"""
        # 重置滑块
        self.heading_slider.setValue(0)
        self.ir_slider.setValue(90)
        
        # 如果在自动模式，停止它
        if self.auto_btn.isChecked():
            self.auto_btn.setChecked(False)
            self.toggle_auto_demo(False)
        
        # 重置时间计数器
        self.time_counter = 0


if __name__ == "__main__":
    print("正在启动可视化测试窗口...")
    app = QApplication(sys.argv)
    window = VisualizationTestWindow()
    print("窗口已创建，正在显示...")
    window.show()
    print("窗口已显示，开始事件循环...")
    sys.exit(app.exec_())