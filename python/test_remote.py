import time                                         # 时间库，获取时间戳
from pymodbus.client import ModbusSerialClient      # 用于处理 modbus 协议相关
from pymodbus.constants import Endian               # 用于指定在 Modbus 通信中处理多字节数据（如 16 位或 32 位寄存器）时的字节顺序
from pymodbus.payload import BinaryPayloadDecoder   # 用于解码 Modbus 设备返回的二进制数据
import requests                                     # 用于发送各种 HTTP 请求并处理响应

# ----------------------- 配置后端系统信息 -----------------------------
BACKEND_HOST = '192.168.3.23'               # 替换为后端系统的 IP 地址或域名
BACKEND_PORT = 8080                         # 替换为后端系统监听的特定端口
API_ENDPOINT = '/api/gps_data'              # 替换为接收 GPS 数据的 API 端点

# 如果后端需要认证，例如 API Key，可以添加到这里
'''
API_KEY = 'your_api_key_here'
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}' # 示例：如果使用 Bearer Token
}
'''
HEADERS = {'Content-Type': 'application/json'} # 默认的 Content-Type，头数据说明位置信息以JSON格式传输

# 串口配置
PORT = '/dev/ttyUSB0'   # 替换为您的RS485转接器对应的串口设备名
BAUDRATE = 9600         # 串口波特率
BYTESIZE = 8            # 8位数据位
PARITY = 'N'            # 无校验
STOPBITS = 1            # 1位停止位
TIMEOUT = 5             # Modbus通信超时时间

# Modbus寄存器地址
LATITUDE_REG = 150      # 纬度寄存器地址（由定位模块决定）
LONGITUDE_REG = 152     # 经度寄存器地址（由定位模块决定）
NUM_REGISTERS = 2       # 经纬度都是32位浮点数，需要读取两个16位寄存器

#---------------连接RS485北斗定位模块，读取经纬度并发送到后端------------------
def read_gps_data_modbus():
    
# ------（根据定位模块使用的的协议）创建一个 Modbus RTU 串口客户端对象用于执行后续的串口通信--------
    client = ModbusSerialClient(
        port=PORT,
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=TIMEOUT
    )
    
# ----------------判断串口是否成功连接--------------------
    if not client.connect():            
        print(f"错误：无法连接到串口 {PORT}。请检查设备是否连接或权限。")
        return
    print(f"成功连接到Modbus RTU设备在 {PORT}")

# ----------------主循环，用于不断获取位置信息----------------
    try:
        while True:    
            # 读取纬度数据
            try:
                # 从 Modbus 从站读取保持寄存器的值（寄存器地址 150, 读取 2 个寄存器，slave默认为1 ）
                result_lat_registers = client.read_holding_registers(address=LATITUDE_REG, count=NUM_REGISTERS, slave=1)
                if result_lat_registers.isError():
                    print(f"读取纬度寄存器失败: {result_lat_registers}")
                    continue

                decoder_lat = BinaryPayloadDecoder.fromRegisters(
                    result_lat_registers.registers,
                    byteorder=Endian.BIG, 
                    wordorder=Endian.BIG  
                )
                latitude = decoder_lat.decode_32bit_float()
                
            except Exception as e:
                print(f"解析纬度数据出错: {e}")
                latitude = None
            

            # 读取经度数据
            try:
                # 从 Modbus 从站读取保持寄存器的值（寄存器地址 152, 读取 2 个寄存器，slave默认为1 ）
                result_lon_registers = client.read_holding_registers(address=LONGITUDE_REG, count=NUM_REGISTERS, slave=1)
                if result_lon_registers.isError():
                    print(f"读取经度寄存器失败: {result_lon_registers}")
                    continue
                # 从 Modbus 寄存器中读取到的原始二进制数据中解码（解析）出经度
                decoder_lon = BinaryPayloadDecoder.fromRegisters(
                    result_lon_registers.registers,
                    byteorder=Endian.BIG,                   # 字节顺序
                    wordorder=Endian.BIG                    # 字顺序
                )
                longitude = decoder_lon.decode_32bit_float()    # 提取并解释为浮点数
                
            except Exception as e:
                print(f"解析经度数据出错: {e}")
                longitude = None

            # 如果成功获取经纬度，则发送到后端
            if latitude is not None and longitude is not None:
                print(f"Moudle GPS: Latitude = {latitude:.6f}, Longitude = {longitude:.6f}")

                # 构建 JSON 数据
                payload = {
                    "latitude": round(latitude, 6),             # 保留6位小数
                    "longitude": round(longitude, 6),           # 保留6位小数
                    "device_id": "MyGPS_Device",                # 可选：添加设备ID
                    "timestamp": time.time()                    # 可选：添加时间戳
                }

                
                send_to_backend(payload)        # 发送到云端后端
            else:
                print("未成功获取经纬度，跳过数据发送。")

            time.sleep(5)              # 每隔5秒读取一次

    except KeyboardInterrupt:
        print("\n程序终止。")
    except Exception as e:
        print(f"程序运行中发生错误: {e}")
    finally:
        if client.connected:
            client.close()
            print("Modbus连接已关闭。")

def send_to_backend(data):
    """
    将数据以 JSON 格式 POST 到后端系统。
    """
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}{API_ENDPOINT}"
    print(f"尝试向 {url} 发送数据: {data}")

    try:
        response = requests.post(url, json=data, headers=HEADERS, timeout=5) # timeout 防止长时间阻塞

        response.raise_for_status()  # 检查HTTP状态码，如果不是2xx，则抛出异常

        print(f"数据发送成功！Backend响应: {response.status_code} {response.text}")

    except requests.exceptions.ConnectionError as e:
        print(f"发送数据失败，无法连接到后端 {url}: {e}")
    except requests.exceptions.Timeout as e:
        print(f"发送数据失败，请求超时到后端 {url}: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"发送数据失败，后端返回HTTP错误 {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"发送数据时发生未知错误: {e}")
    except Exception as e:
        print(f"发送数据时发生异常: {e}")

if __name__ == "__main__":
    read_gps_data_modbus()
