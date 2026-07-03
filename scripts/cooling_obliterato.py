from pymodbus.client import ModbusTcpClient

HOST = "TARGET_IP"
UNIT = 1
COOLING_COIL = 15

client = ModbusTcpClient(HOST, port=502, timeout=3)

try:
    if not client.connect():
        raise SystemExit("Could not connect")

    before = client.read_coils(
        address=COOLING_COIL,
        count=1,
        device_id=UNIT,
    )

    print(f"Cooling before: {before.bits[0]}")

    result = client.write_coil(
        address=COOLING_COIL,
        value=False,
        device_id=UNIT,
    )

    print(f"Write result: {result}")

    after = client.read_coils(
        address=COOLING_COIL,
        count=1,
        device_id=UNIT,
    )

    print(f"Cooling after: {after.bits[0]}")

finally:
    client.close()
