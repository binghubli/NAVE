import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal


class SerialThread(QThread):
    data_received = pyqtSignal(float, float)
    error_occurred = pyqtSignal(str)
    raw_data_received = pyqtSignal(str)  # 添加原始数据信号

    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.ser = None

    def run(self):
        try:
            # 修改：不在线程中创建新的串口连接，而是使用主程序传入的串口对象
            self.running = True
            print(f"串口线程已启动: {self.port}")

            while self.running:
                if self.ser and self.ser.is_open and self.ser.in_waiting:
                    # 读取原始二进制数据
                    raw_data = self.ser.readline()
                    print(f"接收到原始数据: {raw_data}")
                    
                    # 发送原始数据到UI显示
                    try:
                        # 尝试解码为文本
                        try:
                            text = raw_data.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                text = raw_data.decode('gbk')
                            except UnicodeDecodeError:
                                # 如果解码失败，显示十六进制
                                text = ' '.join([f'{b:02X}' for b in raw_data])
                        
                        # 发送到UI显示 - 确保数据不为空
                        if text.strip():
                            self.raw_data_received.emit(text)
                    except Exception as e:
                        print(f"处理原始数据显示时出错: {e}")
                        # 即使出错也尝试显示十六进制
                        try:
                            hex_text = ' '.join([f'{b:02X}' for b in raw_data])
                            self.raw_data_received.emit(f"[HEX] {hex_text}")
                        except:
                            pass
                    try:
                        # 尝试多种解码方式
                        try:
                            line = raw_data.decode('utf-8').strip()
                        except UnicodeDecodeError:
                            try:
                                line = raw_data.decode('gbk').strip()
                            except UnicodeDecodeError:
                                # 如果都失败，则使用十六进制显示
                                line = ' '.join([f'{b:02X}' for b in raw_data])
                                print(f"无法解码数据，十六进制: {line}")
                                # 尝试从二进制数据中提取数值
                                if len(raw_data) >= 8:  # 假设至少需要8字节数据
                                    # 这里需要根据实际数据格式调整
                                    import struct
                                    try:
                                        # 尝试将前4个字节解析为float，后4个字节解析为float
                                        heading_angle, ir_angle = struct.unpack('ff', raw_data[:8])
                                        self.data_received.emit(heading_angle, ir_angle)
                                        continue
                                    except struct.error:
                                        pass
                                continue

                        print(f"解码后数据: {line}")
                        # 尝试解析为两个浮点数
                        parts = line.split(',')
                        if len(parts) >= 2:
                            heading_angle = float(parts[0])
                            ir_angle = float(parts[1])
                            self.data_received.emit(heading_angle, ir_angle)
                    except (ValueError, IndexError) as e:
                        print(f"数据解析错误: {e}, 原始数据: {raw_data}")
                time.sleep(0.01)

        except Exception as e:
            error_msg = f"串口错误: {e}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            # 修改：不在线程中关闭串口，由主程序负责关闭
            print("串口线程已停止")

    def stop(self):
        self.running = False
        self.wait()
        
    def set_serial(self, ser):
        """设置串口对象"""
        self.ser = ser


def get_available_ports():
    """获取可用的串口列表"""
    ports = []
    try:
        from serial.tools import list_ports
        # 使用集合来避免重复
        ports = list(set([port.device for port in list_ports.comports()]))
        print(f"成功获取实际串口列表: {ports}")
    except ImportError as e:
        print(f"导入 serial.tools 失败: {e}")
        # 如果导入失败，使用备选方案
        ports = [f"COM{i + 1}" for i in range(10)]
    
    # 确保列表不为空
    if not ports:
        ports = [f"COM{i + 1}" for i in range(10)]
    
    # 对串口列表进行排序
    ports.sort()
    return ports