from eth_abi import encode_abi

EMPTY_BYTES = encode_abi(["uint8"], [int(0)])

def sayhello():
    print("HelloWorld")

def empty_bytes():
    return EMPTY_BYTES