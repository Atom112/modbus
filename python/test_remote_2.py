import time
import sys
from requests.exceptions import ConnectionError, Timeout, RequestException
from pymodbus.client import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import requests
from flask import Flask, jsonify, request
import threading

# ----------------------- 配置后端系统信息 -----------------------------
BACKEND_HOST = '192.168.3.23'
BACKEND_PORT = 8080
API_ENDPOINT = '/api/gps_data'
HEADERS = {'Content-Type': 'application/json'}

# 串口配置
PORT = '/dev/ttyUSB0'
BAUDRATE = 9600
BYTESIZE = 8
PARITY = 'N'
STOPBITS = 1
TIMEOUT = 5

# Modbus寄存器地址
LATITUDE_REG = 150
LONGITUDE_REG = 152
NUM_REGISTERS = 2

# **<font color="#0056b3">全局Modbus客户端实例，供整个应用使用</font>**
modbus_client = None

#---------------------------------------------------------------------------------------------------------
def read_gps_data_modbus() -> tuple[float | None, float | None]:
    global modbus_client

    if not modbus_client or not modbus_client.connected:
        print("Modbus客户端未连接或已断开，尝试重新连接...")
        try:
            modbus_client.close() # 尝试关闭可能存在的旧连接
            if modbus_client.connect():
                print("Modbus客户端重新连接成功。")
            else:
                print("Modbus客户端重新连接失败！")
                return None, None
        except Exception as e:
            print(f"Modbus重新连接时发生错误: {e}")
            return None, None

    latitude = None
    longitude = None

    try:
        
        result_lat_registers = modbus_client.read_holding_registers(address=LATITUDE_REG, count=NUM_REGISTERS, slave=1)
        if result_lat_registers.isError():
            print(f"读取纬度寄存器失败: {result_lat_registers}")
            return None, None 

        decoder_lat = BinaryPayloadDecoder.fromRegisters(
            result_lat_registers.registers,
            byteorder=Endian.BIG,
            wordorder=Endian.BIG
        )
        latitude = decoder_lat.decode_32bit_float()

        result_lon_registers = modbus_client.read_holding_registers(address=LONGITUDE_REG, count=NUM_REGISTERS, slave=1)
        if result_lon_registers.isError():
            print(f"读取经度寄存器失败: {result_lon_registers}")
            return None, None 

        decoder_lon = BinaryPayloadDecoder.fromRegisters(
            result_lon_registers.registers,
            byteorder=Endian.BIG,
            wordorder=Endian.BIG
        )
        longitude = decoder_lon.decode_32bit_float()

        if latitude is not None and longitude is not None:
            print(f"Moudle GPS: Latitude = {latitude:.6f}, Longitude = {longitude:.6f}")
        return latitude, longitude

    except Exception as e:
        print(f"读取或解析GPS数据出错: {e}")
        return None, None

#----------------------------------------------------------------------------------------------------
def test_http_connection(host: str, port: int, timeout: int = 5) -> tuple[bool, str]:
   
    url = f"http://{host}:{port}"
    try:
        response = requests.get(url, timeout=timeout, verify=False)
        return True, f"HTTP连接成功。URL: {url}, 状态码: {response.status_code}"
    except ConnectionError:
        return False, f"连接错误: 无法连接到 {host}:{port}。请检查地址、端口或网络连通性。"
    except Timeout:
        return False, f"连接超时: 在 {timeout} 秒内未能连接到 {host}:{port}。"
    except RequestException as e:
        return False, f"请求异常: 连接到 {host}:{port} 时发生未知错误: {e}"
    except Exception as e:
        return False, f"未知错误: {e}"

#-------------------------------------------------------------------------------------------
def send_to_backend(data):
    """
    **<font color="#36393b">将数据以 JSON 格式 POST 到后端系统。</font>**
    """
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}{API_ENDPOINT}"
    print(f"尝试向 {url} 发送数据: {data}")

    try:
        response = requests.post(url, json=data, headers=HEADERS, timeout=5)
        response.raise_for_status()

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

app = Flask(__name__)

#---------------------------------------------------------------------------------------------------------
def process_gps_request_in_thread():
    """
    **<font color="#36393b">在单独线程中执行Modbus数据读取和向后端发送数据的任务。</font>**
    **<font color="#36393b">该函数在Flask路由中被调用，以避免阻塞主线程。</font>**
    """
    lat, lon = read_gps_data_modbus() # **<font color="#36393b">无需传递client，因为modbus_client是全局的</font>**

    if lat is not None and lon is not None:
        payload = {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "device_id": "MyGPS_Device",
            "timestamp": time.time()
        }
        send_to_backend(payload)
    else:
        print("未获取到有效的GPS数据，跳过发送到后端。")

@app.route('/notify_request_received', methods=['POST', 'GET'])
def listen_and_send():

    print("收到后端请求，将在后台线程中处理GPS数据...")

    thread = threading.Thread(target=process_gps_request_in_thread)
    thread.start()


    return jsonify({"status": "acknowledged", "message": "请求已接收，GPS数据正在后台处理并发送中。"}), 200

if __name__ == "__main__":

    modbus_client = ModbusSerialClient(
        port=PORT,
        baudrate=BAUDRATE,
        bytesize=BYTESIZE,
        parity=PARITY,
        stopbits=STOPBITS,
        timeout=TIMEOUT
    )


    if not modbus_client.connect():
        print(f"错误：无法连接到串口 {PORT}。请检查设备是否连接或权限。")
        sys.exit(1)
    print(f"成功连接到Modbus RTU设备在 {PORT}")


    while True:
        if_http_isconnected, http_msg = test_http_connection(BACKEND_HOST, BACKEND_PORT)
        if not if_http_isconnected:
            print(f"与后端的http连接失败，请检查网络设置或后端服务状态，\n错误信息：{http_msg}")
            print("准备进行重试...")
            time.sleep(5)
        else:
            print("与后端连接成功，本地服务将监听后端位置请求。")
            break


    app.run(host='192.168.3.10', port=5000, debug=False)

    if modbus_client and modbus_client.connected:
        modbus_client.close()
        print("Modbus客户端已关闭。")