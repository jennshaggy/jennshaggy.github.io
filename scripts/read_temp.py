from pymodbus.client import ModbusTcpClient

HOST = "TARGET_IP"
PORT = 502
DEVICE_ID = 1
REGISTER = 0      # Replace with the documented temperature register
SCALE = 10        # Common: raw 253 means 25.3°C

client = ModbusTcpClient(HOST, port=PORT, timeout=3)

try:
    if not client.connect():
        raise ConnectionError(f"Could not connect to {HOST}:{PORT}")

    result = client.read_holding_registers(
        address=REGISTER,
        count=1,
        device_id=DEVICE_ID,
    )

    if result.isError():
        print(f"Modbus error: {result}")
    else:
        raw = result.registers[0]
        print(f"Raw register value: {raw}")
        print(f"Temperature: {raw / SCALE:.1f} °C")
finally:
    client.close()
