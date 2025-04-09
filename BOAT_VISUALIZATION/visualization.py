from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPolygon
from PyQt5.QtCore import QPoint
import math
import numpy as np
import pyqtgraph as pg


class ShipAttitudeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.heading_angle = 0
        self.ir_angle = 0
        self.initUI()

    def initUI(self):
        self.setMinimumSize(300, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 设置坐标系中心
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 20

        # 绘制圆形背景
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 绘制刻度
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(0, 360, 10):
            angle = math.radians(i)
            start_x = center_x + int((radius - 10) * math.sin(angle))
            start_y = center_y - int((radius - 10) * math.cos(angle))
            end_x = center_x + int(radius * math.sin(angle))
            end_y = center_y - int(radius * math.cos(angle))
            painter.drawLine(start_x, start_y, end_x, end_y)

            # 每30度绘制数字
            if i % 30 == 0:
                text_x = center_x + int((radius - 30) * math.sin(angle)) - 10
                text_y = center_y - int((radius - 30) * math.cos(angle)) + 5
                painter.drawText(text_x, text_y, str(i))

        # 绘制船体（航向角）
        painter.setPen(QPen(QColor(0, 0, 255), 3))
        heading_rad = math.radians(self.heading_angle)
        ship_length = radius * 0.8

        # 船体多边形
        ship_points = QPolygon([
            QPoint(center_x + int(ship_length * math.sin(heading_rad)),
                   center_y - int(ship_length * math.cos(heading_rad))),
            QPoint(center_x + int(0.3 * ship_length * math.sin(heading_rad + math.pi / 2)),
                   center_y - int(0.3 * ship_length * math.cos(heading_rad + math.pi / 2))),
            QPoint(center_x - int(0.5 * ship_length * math.sin(heading_rad)),
                   center_y + int(0.5 * ship_length * math.cos(heading_rad))),
            QPoint(center_x + int(0.3 * ship_length * math.sin(heading_rad - math.pi / 2)),
                   center_y - int(0.3 * ship_length * math.cos(heading_rad - math.pi / 2)))
        ])

        painter.setBrush(QBrush(QColor(200, 200, 255)))
        painter.drawPolygon(ship_points)

        # 绘制红外信号方位角
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        ir_rad = math.radians(self.ir_angle)
        ir_length = radius * 0.7
        ir_x = center_x + int(ir_length * math.sin(ir_rad))
        ir_y = center_y - int(ir_length * math.cos(ir_rad))

        painter.drawLine(center_x, center_y, ir_x, ir_y)

        # 绘制箭头
        arrow_size = 10
        arrow_angle1 = ir_rad + math.pi - math.pi / 6
        arrow_angle2 = ir_rad + math.pi + math.pi / 6

        arrow_x1 = ir_x + int(arrow_size * math.sin(arrow_angle1))
        arrow_y1 = ir_y - int(arrow_size * math.cos(arrow_angle1))
        arrow_x2 = ir_x + int(arrow_size * math.sin(arrow_angle2))
        arrow_y2 = ir_y - int(arrow_size * math.cos(arrow_angle2))

        painter.drawLine(ir_x, ir_y, arrow_x1, arrow_y1)
        painter.drawLine(ir_x, ir_y, arrow_x2, arrow_y2)

        # 绘制角度文本
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(10, 20, f"航向角: {self.heading_angle:.1f}°")
        painter.drawText(10, 40, f"红外方位角: {self.ir_angle:.1f}°")

    def update_angles(self, heading, ir):
        self.heading_angle = heading
        self.ir_angle = ir
        self.update()


class AttitudePlot:
    def __init__(self, plot_widget, data_length=1000):  # 增加默认数据长度
        self.plot_widget = plot_widget
        self.data_length = data_length
        self.display_length = 10000  # 默认显示最近100个数据点
        
        # 初始化数据
        self.heading_data = np.zeros(data_length)
        self.ir_data = np.zeros(data_length)
        self.time_data = np.linspace(-data_length, 0, data_length)
        
        # 设置图表
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', '角度', units='°')
        self.plot_widget.setLabel('bottom', '时间', units='s')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        
        # 设置显示范围
        self.plot_widget.setXRange(-self.display_length, 0)
        self.plot_widget.setYRange(-10, 370)  # 设置Y轴范围略大于0-360度
        
        # 创建曲线
        self.heading_curve = self.plot_widget.plot(
            self.time_data, 
            self.heading_data,
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            name="航向角"
        )
        
        self.ir_curve = self.plot_widget.plot(
            self.time_data, 
            self.ir_data,
            pen=pg.mkPen(color=(255, 0, 0), width=2),
            name="红外方位角"
        )
        
        # 数据计数器
        self.data_counter = 0
    
    def update_data(self, heading, ir):
        """更新数据"""
        self.heading_data = np.roll(self.heading_data, -1)
        self.heading_data[-1] = heading
        
        self.ir_data = np.roll(self.ir_data, -1)
        self.ir_data[-1] = ir
        
        self.data_counter += 1
        
        # 更新时间数据
        if self.data_counter > self.data_length:
            self.time_data = np.linspace(-self.data_length, 0, self.data_length)
    
    def update_plot(self):
        """更新图表显示"""
        # 只显示实际有数据的部分
        valid_length = min(self.data_counter, self.data_length)
        display_start = max(-valid_length, -self.data_length)
        
        self.heading_curve.setData(
            self.time_data[display_start:],
            self.heading_data[display_start:]
        )
        self.ir_curve.setData(
            self.time_data[display_start:],
            self.ir_data[display_start:]
        )
    
    def set_display_range(self, start, end):
        """设置显示范围"""
        self.plot_widget.setXRange(start, end)
    
    def get_data_range(self):
        """获取当前数据范围"""
        return (-min(self.data_counter, self.data_length), 0)