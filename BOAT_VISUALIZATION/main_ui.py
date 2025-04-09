import sys
import serial
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QComboBox,
                             QGroupBox, QGridLayout, QLineEdit, QMessageBox,
                             QTextEdit)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

# 导入自定义模块
from serial_handler import SerialThread, get_available_ports
from visualization import ShipAttitudeWidget, AttitudePlot


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("船体姿态可视化")
        self.setGeometry(100, 100, 1000, 600)

        self.serial_thread = None
        self.ser = None
        
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        control_panel = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_panel)

        # 串口设置
        serial_group = QGroupBox("串口设置")
        serial_layout = QGridLayout(serial_group)

        serial_layout.addWidget(QLabel("串口:"), 0, 0)
        self.port_combo = QComboBox()
        self.update_ports()
        serial_layout.addWidget(self.port_combo, 0, 1)

        serial_layout.addWidget(QLabel("波特率:"), 1, 0)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")
        serial_layout.addWidget(self.baud_combo, 1, 1)

        refresh_btn = QPushButton("刷新串口")
        refresh_btn.clicked.connect(self.update_ports)
        serial_layout.addWidget(refresh_btn, 2, 0)

        # 添加打开串口按钮
        self.open_port_btn = QPushButton("打开串口")
        self.open_port_btn.clicked.connect(self.open_port)
        serial_layout.addWidget(self.open_port_btn, 2, 1)

        self.connect_btn = QPushButton("开始接收")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setEnabled(False)  # 初始禁用，直到串口打开
        serial_layout.addWidget(self.connect_btn, 3, 0, 1, 2)

        control_layout.addWidget(serial_group)

        # 数据显示
        data_group = QGroupBox("数据显示")
        data_layout = QGridLayout(data_group)

        data_layout.addWidget(QLabel("航向角:"), 0, 0)
        self.heading_edit = QLineEdit("0.0")
        self.heading_edit.setReadOnly(True)
        data_layout.addWidget(self.heading_edit, 0, 1)

        data_layout.addWidget(QLabel("红外方位角:"), 1, 0)
        self.ir_edit = QLineEdit("0.0")
        self.ir_edit.setReadOnly(True)
        data_layout.addWidget(self.ir_edit, 1, 1)

        control_layout.addWidget(data_group)

        # 添加接收数据显示区域
        receive_group = QGroupBox("接收区")
        receive_layout = QVBoxLayout(receive_group)
        
        # 创建文本显示区域
        self.receive_text = QTextEdit()
        self.receive_text.setReadOnly(True)
        self.receive_text.setMinimumHeight(150)
        receive_layout.addWidget(self.receive_text)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        
        # 添加清空按钮
        clear_receive_btn = QPushButton("清空接收区")
        clear_receive_btn.clicked.connect(self.clear_receive_text)
        btn_layout.addWidget(clear_receive_btn)
        
        # 添加测试按钮
        test_receive_btn = QPushButton("测试接收区")
        test_receive_btn.clicked.connect(self.test_receive_area)
        btn_layout.addWidget(test_receive_btn)
        
        receive_layout.addLayout(btn_layout)
        
        control_layout.addWidget(receive_group)

        # 添加数据发送区域
        send_group = QGroupBox("数据发送")
        send_layout = QGridLayout(send_group)
        
        self.send_text = QLineEdit()
        send_layout.addWidget(self.send_text, 0, 0, 1, 2)

        # 添加发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_data)
        self.send_btn.setEnabled(False)  # 初始禁用，直到串口打开
        send_layout.addWidget(self.send_btn, 1, 0)
        
        # 添加清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_send_text)
        send_layout.addWidget(clear_btn, 1, 1)
        
        # 添加换行选项
        self.newline_combo = QComboBox()
        self.newline_combo.addItems(["无", "\\r", "\\n", "\\r\\n"])
        self.newline_combo.setCurrentText("\\r\\n")
        send_layout.addWidget(QLabel("换行符:"), 2, 0)
        send_layout.addWidget(self.newline_combo, 2, 1)
        
        control_layout.addWidget(send_group)

        # 添加一些空白空间
        control_layout.addStretch(1)

        main_layout.addWidget(control_panel, 1)

        # 右侧可视化区域
        viz_panel = QWidget()
        viz_layout = QVBoxLayout(viz_panel)

        # 船体姿态可视化
        self.ship_widget = ShipAttitudeWidget()
        viz_layout.addWidget(self.ship_widget, 1)

        # 曲线图
        plot_group = QGroupBox("姿态曲线")
        plot_layout = QVBoxLayout(plot_group)

        self.plot_widget = pg.PlotWidget()
        plot_layout.addWidget(self.plot_widget)
        
        # 初始化姿态图表
        self.attitude_plot = AttitudePlot(self.plot_widget)
        
        viz_layout.addWidget(plot_group, 1)

        main_layout.addWidget(viz_panel, 3)

        # 设置定时器更新图表
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # 100ms更新一次

    def update_ports(self):
        # 保存当前选中的串口（如果有的话）
        current_port = self.port_combo.currentText() if self.port_combo.count() > 0 else ""

        # 清空下拉菜单
        self.port_combo.clear()

        # 获取可用串口列表
        ports = get_available_ports()

        # 添加到下拉菜单
        self.port_combo.addItems(ports)

        # 如果之前选中的串口仍然存在，则重新选中它
        index = self.port_combo.findText(current_port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)

        print(f"可用串口列表: {ports}")

    def toggle_connection(self):
        if self.serial_thread is None or not self.serial_thread.running:
            if not hasattr(self, 'ser') or not self.ser or not self.ser.is_open:
                QMessageBox.warning(self, "警告", "请先打开串口")
                return

            port = self.port_combo.currentText()
            baudrate = int(self.baud_combo.currentText())

            try:
                # 修改：使用已打开的串口对象
                self.serial_thread = SerialThread(port, baudrate)
                self.serial_thread.set_serial(self.ser)  # 传递串口对象
                
                # 确保先连接信号，再启动线程
                self.serial_thread.data_received.connect(self.update_data)
                self.serial_thread.raw_data_received.connect(self.update_receive_text)
                self.serial_thread.error_occurred.connect(self.show_error)
                
                # 清空接收区，准备接收新数据
                self.receive_text.clear()
                
                # 启动线程
                self.serial_thread.start()

                self.connect_btn.setText("停止接收")
                print(f"开始接收数据，串口 {port}, 波特率 {baudrate}")
            except Exception as e:
                QMessageBox.critical(self, "连接错误", f"无法开始接收数据: {str(e)}")
                print(f"连接错误: {e}")
        else:
            self.serial_thread.stop()
            self.connect_btn.setText("开始接收")
            print("已停止接收数据")

    def update_data(self, heading, ir):
        # 更新数据显示
        self.heading_edit.setText(f"{heading:.1f}")
        self.ir_edit.setText(f"{ir:.1f}")

        # 更新船体姿态可视化
        self.ship_widget.update_angles(heading, ir)

        # 更新数据数组
        self.attitude_plot.update_data(heading, ir)

    def update_plot(self):
        # 更新曲线图
        self.attitude_plot.update_plot()

    def clear_receive_text(self):
        """清空接收文本区域"""
        self.receive_text.clear()

    def update_receive_text(self, text):
        """更新接收区文本"""
        # 将文本添加到接收区，确保每条数据后面有换行符
        if not text.endswith('\n'):
            text += '\n'
            
        # 将文本添加到接收区
        self.receive_text.append(text.strip())  # 使用append方法自动处理光标和滚动
        
        # 确保滚动到底部
        try:
            scrollbar = self.receive_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"滚动接收区时出错: {e}")

    def closeEvent(self, event):
        # 关闭串口线程
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            print("已停止串口线程")

        # 关闭串口
        if hasattr(self, 'ser') and self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
                    print("程序关闭时已关闭串口")
            except Exception as e:
                print(f"关闭串口时出错: {e}")

        event.accept()

    def open_port(self):
        """打开串口但不开始接收数据"""
        # 先关闭已有的串口连接
        self.close_existing_port()
        
        port = self.port_combo.currentText()
        baudrate = int(self.baud_combo.currentText())

        try:
            # 添加更多串口参数以确保兼容性
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # 确保串口确实打开了
            if not self.ser.is_open:
                self.ser.open()
                
            self.open_port_btn.setText("关闭串口")
            self.open_port_btn.clicked.disconnect(self.open_port)
            self.open_port_btn.clicked.connect(self.close_port)
            self.connect_btn.setEnabled(True)  # 启用接收按钮
            self.send_btn.setEnabled(True)     # 启用发送按钮

            # 禁用串口和波特率选择
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)

            print(f"已打开串口 {port}, 波特率 {baudrate}")
            QMessageBox.information(self, "成功", f"已成功打开串口 {port}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开串口 {port}: {str(e)}")
            print(f"打开串口错误: {e}")
            # 确保清理任何可能部分创建的资源
            if hasattr(self, 'ser') and self.ser:
                try:
                    self.ser.close()
                except:
                    pass
                self.ser = None
    
    def close_existing_port(self):
        """关闭任何可能已经打开的串口"""
        # 如果有接收线程在运行，先停止
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            self.connect_btn.setText("开始接收")

        # 关闭串口
        if hasattr(self, 'ser') and self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception as e:
                print(f"关闭串口时出错: {e}")
            self.ser = None

    def close_port(self):
        """关闭串口"""
        # 如果有接收线程在运行，先停止
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
            self.connect_btn.setText("开始接收")

        # 关闭串口
        if hasattr(self, 'ser') and self.ser:
            try:
                if self.ser.is_open:
                    self.ser.close()
            except Exception as e:
                print(f"关闭串口时出错: {e}")
            self.ser = None

        self.open_port_btn.setText("打开串口")
        self.open_port_btn.clicked.disconnect(self.close_port)
        self.open_port_btn.clicked.connect(self.open_port)
        self.connect_btn.setEnabled(False)
        self.send_btn.setEnabled(False)     # 禁用发送按钮

        # 启用串口和波特率选择
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

        print("已关闭串口")

    def show_error(self, message):
        QMessageBox.critical(self, "串口错误", message)
        # 如果发生错误，重置按钮状态
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
        self.connect_btn.setText("开始接收")
    
    def test_receive_area(self):
        """测试接收区是否正常工作"""
        test_data = "这是一条测试数据，用于验证接收区是否正常工作。"
        self.update_receive_text(test_data)
        print("已发送测试数据到接收区")
    
    def send_data(self):
        """向串口发送数据"""
        if not hasattr(self, 'ser') or not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "警告", "串口未打开")
            return
            
        text = self.send_text.text()
        if not text:
            return
            
        # 添加换行符
        newline = self.newline_combo.currentText()
        if newline == "\\r":
            text += '\r'
        elif newline == "\\n":
            text += '\n'
        elif newline == "\\r\\n":
            text += '\r\n'
            
        try:
            # 发送数据
            self.ser.write(text.encode('utf-8'))
            print(f"已发送数据: {text}")
        except Exception as e:
            QMessageBox.critical(self, "发送错误", f"发送数据失败: {str(e)}")
            print(f"发送错误: {e}")
    
    def clear_send_text(self):
        """清空发送文本框"""
        self.send_text.clear()