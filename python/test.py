import serial
import time
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

def read_gps_data_modbus(port, baudrate, slave_id):
    """
    通过Modbus-RTU协议从ZL-GPS-012模块读取经纬度信息。

    参数:
    port (str): 串口设备路径，例如 '/dev/ttyUSB0'。
    baudrate (int): 串口波特率。
    slave_id (int): Modbus从机地址。
    """
    # 初始化Modbus客户端
    # 请根据您的模块手册调整 baudrate, bytesize, parity, stopbits
    client = ModbusClient(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        parity='N',  # N: None (无校验)
        stopbits=1,
        timeout=5     # 读取超时时间
    )

    print(f"尝试连接串口: {port}，波特率: {baudrate}...")

    try:
        # 尝试连接
        if client.connect():
            print("成功连接到Modbus设备。")
        else:
            print(f"无法连接到串口 {port}。请检查串口是否正确，")
            print("或您的用户是否有权限访问串口（尝试 'sudo usermod -a -G dialout $USER' 后注销重新登录）。")
            return

        while True:
            # 读取纬度 (寄存器地址 150, 两个寄存器)
            # manual says "字节顺序：ABCD", which corresponds to big endian for both word and byte.
            # Using Endian.BIG for both for safety, but typically just word_order is needed if registers are consecutive.
            # pymodbus's default byte_order for BinaryPayloadDecoder is Endian.BIG
            # so we only explicitly set word_order.
            
            # 读取纬度
            try:
                # Modbus地址通常是从0开始计数，但手册中的150是保持寄存器的地址，
                # 对于ModbusClient的read_holding_registers，我们直接使用该十进制地址。
                # 读取2个寄存器，共4字节，用于一个float。
                result_lat_registers = client.read_holding_registers(address=150, count=2, slave=slave_id)
                if result_lat_registers.isError():
                    print(f"读取纬度寄存器失败: {result_lat_registers}")
                    continue

                decoder_lat = BinaryPayloadDecoder.fromRegisters(
                    result_lat_registers.registers,
                    byteorder=Endian.BIG, # For individual bytes within a word (usually not changed for standard configs)
                    wordorder=Endian.BIG   # For the order of 16-bit words
                )
                latitude = decoder_lat.decode_32bit_float()
                
            except Exception as e:
                print(f"解析纬度数据出错: {e}")
                latitude = None

            # 读取经度 (寄存器地址 152, 两个寄存器)
            try:
                result_lon_registers = client.read_holding_registers(address=152, count=2, slave=slave_id)
                if result_lon_registers.isError():
                    print(f"读取经度寄存器失败: {result_lon_registers}")
                    continue

                decoder_lon = BinaryPayloadDecoder.fromRegisters(
                    result_lon_registers.registers,
                    byteorder=Endian.BIG,
                    wordorder=Endian.BIG
                )
                longitude = decoder_lon.decode_32bit_float()
                
            except Exception as e:
                print(f"解析经度数据出错: {e}")
                longitude = None

            if latitude is not None and longitude is not None:
                print(f"接收到经纬度: 纬度={latitude:.6f}, 经度={longitude:.6f}")
            else:
                print("未成功获取经纬度数据。")
                
            time.sleep(1) # 每秒读取一次

    except Exception as e:
        print(f"Modbus通信错误: {e}")
        print(f"请检查以下事项:")
        print(f"  1. 串口 '{port}' 是否正确？您可以通过 'ls /dev/ttyUSB*' 或 'dmesg | grep tty' 确认。")
        print(f"  2. 您的用户是否有权限访问串口？尝试将您的用户添加到 'dialout' 组: 'sudo usermod -a -G dialout $USER'，然后注销并重新登录。")
        print(f"  3. 串口是否被其他程序占用？")
    except KeyboardInterrupt:
        print("\n程序终止。")
    finally:
        client.close()
        print("Modbus连接已关闭。")

if __name__ == "__main__":
    # --- 请根据您的实际情况修改以下参数 ---
    SERIAL_PORT = '/dev/ttyUSB0'  # 您的USB转RS485转接头对应的串口设备文件
    BAUD_RATE = 9600              # ZL-GPS-012模块的默认波特率
    SLAVE_ID = 1                 # ZL-GPS-012模块的默认Modbus从机地址

    read_gps_data_modbus(port=SERIAL_PORT, baudrate=BAUD_RATE, slave_id=SLAVE_ID)