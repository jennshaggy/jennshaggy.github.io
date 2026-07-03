from pymodbus.client import ModbusTcpClient

HOST = "TARGET_IP"
UNIT = 1

client = ModbusTcpClient(HOST, port=502, timeout=3)

if not client.connect():
    raise SystemExit("Could not connect")

for kind, reader in (
    ("holding", client.read_holding_registers),
    ("input", client.read_input_registers),
):
    print(f"\n[{kind} registers]")

    for address in range(0, 21):
        result = reader(
            address=address,
            count=1,
            device_id=UNIT,
        )

        if not result.isError():
            print(f"{address}: {result.registers[0]}")

print("\n[coils]")

for address in range(0, 24):
    result = client.read_coils(
        address=address,
        count=1,
        device_id=UNIT,
    )

    if not result.isError():
        print(f"{address}: {result.bits[0]}")

print("\n[discrete inputs]")

for address in range(0, 24):
    result = client.read_discrete_inputs(
        address=address,
        count=1,
        device_id=UNIT,
    )

    if not result.isError():
        print(f"{address}: {result.bits[0]}")

client.close()
