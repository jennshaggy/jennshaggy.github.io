from pymodbus.client import ModbusTcpClient

HOST = "TARGET_IP"
UNIT = 1

client = ModbusTcpClient(HOST, port=502, timeout=3)

try:
    if not client.connect():
        raise SystemExit("Could not connect")

    before = client.read_holding_registers(
        address=0,
        count=1,
        device_id=UNIT,
    )

    print(f"Before: {before.registers[0]}")

    result = client.write_register(
        address=0,
        value=100,
        device_id=UNIT,
    )

    print(f"Write result: {result}")

    after = client.read_holding_registers(
        address=0,
        count=1,
        device_id=UNIT,
    )

    print(f"After: {after.registers[0]}")

finally:
    client.close()
