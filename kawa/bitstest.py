print("hello world")
print(bin(0xFF))

a = b'abc'

print(bin(a[0]))
print(bin(a[0] << 1))
print(bin(a[1]))

print(bin( a[0] << 8 | a[1]))

b = int.from_bytes(a[0:1],byteorder='big',signed=True)
print(b)

b = int.from_bytes(a[0:1],byteorder='big',signed=False)
print(b)

b = int.from_bytes(b'\xFF',byteorder='big',signed=False)
print(b)

print(a[0])
print(a[1])
print(a[0] + a[1])

print(bin(a[0]))
print(bin(a[0] >> 4))

print(hex(a[1]))

