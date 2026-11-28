# python/python-stdlib/20 — struct (바이너리 데이터) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 12바이트 — `h` 와 `f` 사이에 패딩 2바이트

**출력**

```text
hex: 2a00000000010000c3f54840
크기: 12 bytes
```

**왜 그런가**
칸 너비만 더하면 `i`(4) + `h`(2) + `f`(4) = 10 이다.
접두사가 없으면 기본 `@` 이고, `@` 는 네이티브 정렬을 써서 `f` 를 4의 배수 위치에서 시작시키려고 `h` 뒤에 빈 바이트 2개를 넣는다.
hex 를 칸으로 나누면 `2a000000 | 0001 | 0000 | c3f54840` 이고, 세 번째 칸 `0000` 이 패딩이다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 2. 빅 엔디안은 `01020304`, 리틀 엔디안은 `04030201`

**출력**

```text
빅 엔디안:    01020304
리틀 엔디안:  04030201
```

**왜 그런가**
`>` 는 가장 큰 자리 바이트 `01` 부터 놓는다.
`<` 는 가장 작은 자리 바이트 `04` 부터 놓는다.
같은 수가 순서만 뒤집혀 놓인다.
근거: 2-summary 「동작 방식 (2)」.

### 3. `01000f` 로 시작하는 18바이트

**출력**

```text
패킷: 01000f48656c6c6f2c204e6574776f726b21
크기: 18 bytes
```

**왜 그런가**
`'Hello, Network!'` 는 UTF-8 로 15바이트다.
헤더 `'!BH'` 는 `B` 에 타입 `1` → `01`, `H` 에 길이 `15` → 빅 엔디안 `000f` 로 3바이트다.
3 + 15 = 18 이고, 헤더 뒤로 본문 바이트가 이어진다.
근거: 2-summary 「동작 방식 (5)」.

### 4. `f` 는 4바이트 실수라 3.14 를 정확히 담지 못한다

`f` 칸은 4바이트 실수로, `3.14` 를 그 형식에서 가장 가까운 값으로 바꿔 저장한다.
되돌릴 때 그 근삿값이 Python 의 `float` 로 나오므로 `3.140000104904175` 가 된다.
정밀도가 필요하면 8바이트 `d` 를 쓴다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 6」.

### 5. 양쪽이 같은 바이트 순서로 읽어야 하기 때문이다

네트워크 바이트 순서는 빅 엔디안으로 정해져 있어, 보내는 쪽과 받는 쪽이 같은 약속을 따라야 같은 수로 읽는다.
기본 `@` 는 실행 플랫폼의 순서와 정렬 패딩을 따르므로 기계마다 바이트가 달라질 수 있다.
`!` · `>` 는 순서를 빅 엔디안으로 못박고 패딩도 넣지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1 · 2」.

### 6. 길이가 다르면 `unpack` 이 오류를 낸다 — `calcsize` 로 헤더만 자른다

`unpack` 은 정확히 `calcsize` 만큼의 바이트를 요구하므로, 길거나 짧으면 실패한다.
`parse_packet` 은 `struct.calcsize('!BH')` 로 헤더 크기 3을 구해 `packet[:header_size]` 만 `unpack` 에 넘긴다.
본문은 헤더에서 읽은 길이로 따로 잘라 `decode` 한다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 7. 패딩 `\x00` 까지 10바이트가 돌아온다 — `rstrip(b'\x00')` 으로 걷어 낸다

`'10s'` 는 정확히 10바이트 칸이라, 5바이트를 넣으면 나머지 5칸이 `\x00` 으로 채워진다.
`unpack` 은 패딩을 지워 주지 않아 `(b'Hello\x00\x00\x00\x00\x00',)` 처럼 10바이트짜리 값이 튜플에 담겨 돌아온다.
첫 값에 `rstrip(b'\x00')` 을 하면 `b'Hello'` 가 된다.
반대로 칸보다 긴 바이트를 넣으면 잘린다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 8. 아니다 — `=` 는 플랫폼의 순서를 따른다

`=` 는 패딩 없는 네이티브 순서라, 리틀 엔디안 플랫폼(x86/x64 등)에서만 `<` 와 같은 결과가 된다.
빅 엔디안 플랫폼에서는 `>` 와 같은 결과가 된다.
그래서 주고받는 데이터에는 `<` · `>` · `!` 처럼 순서를 명시한다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 9. `s` 는 바이트 칸이고 `str` 은 글자이기 때문이다

`s` 는 바이트 단위로 동작하고 유니코드 글자를 모른다.
그래서 넣을 때는 `str` 을 `encode` 해 `bytes` 로 만들고, 꺼낸 `bytes` 는 `decode` 해 글자로 돌린다.
패킷 예제의 `data.encode('utf-8')` 와 `tag.decode()` · `sig.decode()` 가 그 다리다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 10. 둘 다 같은 크기의 레코드를 차례로 하나씩 다룬다

`Struct('>ff')` 의 `.size`(8)를 단위로 `i * size` 오프셋마다 `pack_into` 로 쓰고 `unpack_from` 으로 읽는다.
`iter_unpack` 은 같은 포맷이 되풀이되는 바이트를 처음부터 한 레코드씩 풀어 튜플을 내준다.
즉 `iter_unpack` 은 「오프셋을 레코드 크기만큼 늘려 가며 `unpack_from` 하는 반복」을 대신해 주는 셈이다.
차이는 `pack_into` / `unpack_from` 은 가변 버퍼의 아무 위치나 고를 수 있고, `iter_unpack` 은 처음부터 순서대로만 읽는다는 것이다.
근거: 2-summary 「동작 방식 (6)」 (두 흐름을 견준 것은 원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. `struct` 로 바이너리 데이터 한 바퀴 돌기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `'ihf'` pack · hex · 길이 · unpack | `struct.pack('ihf', 42, 256, 3.14)` · `data.hex()` · `len(data)` · `struct.unpack('ihf', data)` |
| 2. 포맷 문자 표 출력 | `for fmt, (desc, size) in formats.items():` |
| 3. 세 바이트 순서 | `struct.pack('>I', value)` · `'<I'` · `'=I'` |
| 4. 10바이트 문자열 칸 | `struct.pack('10s', b'Hello')` · `struct.unpack('10s', packed)` · `rstrip(b'\x00')` |
| 5. 숫자 + 문자열 혼합 | `struct.pack('>H 4s f', 1001, b'TEMP', 36.5)` · `tag.decode()` · `{value:.1f}` |
| 6. 크기 계산 | `struct.calcsize(fmt)` (`fmt = '>HH4sf'`) |
| 7. 패킷 만들기 | `create_packet` 의 `data.encode('utf-8')` · `struct.pack('!BH', msg_type, len(body))` |
| 8. 패킷 파싱 | `parse_packet` 의 `struct.calcsize('!BH')` · `packet[:header_size]` · `.decode('utf-8')` |
| 9. BMP 헤더 | `bmp_header_fmt = '<2sIHHI'` · `struct.pack(bmp_header_fmt, b'BM', 1024, 0, 0, 54)` |
| 10. Struct 재사용 | `struct.Struct('>ff')` · `bytearray(...)` · `pack_into(buffer, i * point_struct.size, x, y)` · `unpack_from` |
| 11. iter_unpack | `struct.pack('>3i', 10, 20, 30)` · `struct.iter_unpack('>i', data)` · `values[0]` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-stdlib/reference/struct-pack.py`

```python
# [표준 라이브러리] struct (바이너리 데이터)
# 설명: struct.pack/unpack으로 바이너리 데이터 처리, 네트워크 프로토콜, 파일 포맷 파싱
# 팁: 네트워크 프로토콜에는 항상 빅 엔디안('>'' 또는 '!')을 사용한다. calcsize()로 포맷의 바이트 크기를 미리 확인한다. 반복적으로 같은 포맷을 사용하면 struct.Struct 객체를 생성하여 재사용하는 것이 빠르다. pack_into/unpack_from은 버퍼를 직접 조작할 때 유용하다.
# 함정: 기본 '@'는 네이티브 정렬/패딩이 들어가 크기가 예상과 다를 수 있음. 문자열 's'는 바이트 단위 (유니코드 X) → encode/decode 필요. unpack은 정확히 calcsize 만큼의 바이트를 요구.

# 바이너리 ↔ Python 값 변환 모듈
import struct

# === 기본 pack / unpack ===
print("=== 기본 pack / unpack ===")
# pack: Python 값들을 포맷에 맞춰 bytes로 변환
# 'ihf': int(4) + short(2) + float(4) = 네이티브에서 패딩 포함 12바이트
data = struct.pack('ihf', 42, 256, 3.14)
print(f"packed: {data}")
print(f"hex: {data.hex()}")
print(f"크기: {len(data)} bytes")

# unpack: bytes → 튜플로 복원 (포맷이 정확히 일치해야 함)
values = struct.unpack('ihf', data)
print(f"unpacked: {values}")
# (42, 256, 3.140000104904175) - float 정밀도 한계로 약간 차이

# === 포맷 문자 ===
print("\n=== 포맷 문자 ===")
# 자주 쓰는 포맷 문자: 대문자=unsigned, 소문자=signed
formats = {
    'b': ('signed char', 1),
    'B': ('unsigned char', 1),
    'h': ('short', 2),
    'H': ('unsigned short', 2),
    'i': ('int', 4),
    'I': ('unsigned int', 4),
    'q': ('long long', 8),
    'Q': ('unsigned long long', 8),
    'f': ('float', 4),
    'd': ('double', 8),
    '?': ('bool', 1),
    's': ('char[]', 'N bytes'),
}
for fmt, (desc, size) in formats.items():
    print(f"  '{fmt}': {desc} ({size} bytes)")

# === 바이트 순서 (Endianness) ===
print("\n=== 바이트 순서 ===")
value = 0x01020304

# 빅 엔디안 '>': 가장 큰 바이트부터 (네트워크 표준)
big = struct.pack('>I', value)
print(f"빅 엔디안:    {big.hex()}")

# 리틀 엔디안 '<': 가장 작은 바이트부터 (x86/x64 네이티브)
little = struct.pack('<I', value)
print(f"리틀 엔디안:  {little.hex()}")

# 네이티브 '=': 패딩 없는 시스템 기본 순서
native = struct.pack('=I', value)
print(f"네이티브:     {native.hex()}")

# 접두사 정리
print("\n바이트 순서 접두사:")
print("  '@': 네이티브 (기본, 패딩 있음)")
print("  '=': 네이티브 (패딩 없음)")
print("  '<': 리틀 엔디안")
print("  '>': 빅 엔디안 (네트워크)")
print("  '!': 네트워크 (= 빅 엔디안)")

# === 문자열 처리 ===
print("\n=== 문자열 ===")
# '10s': 정확히 10바이트 (부족하면 \x00 패딩, 넘치면 잘림)
packed = struct.pack('10s', b'Hello')
print(f"'10s' pack: {packed}")  # b'Hello\x00\x00\x00\x00\x00'

unpacked = struct.unpack('10s', packed)
print(f"unpack: {unpacked}")  # (b'Hello\x00\x00\x00\x00\x00',)
# rstrip(b'\x00')으로 패딩 제거
print(f"strip: {unpacked[0].rstrip(b'\x00')}")

# 숫자 + 문자열 혼합 패킷 - 공백은 가독성용 (struct가 무시)
packet = struct.pack('>H 4s f', 1001, b'TEMP', 36.5)
seq, tag, value = struct.unpack('>H 4s f', packet)
print(f"\n혼합: seq={seq}, tag={tag.decode()}, value={value:.1f}")

# === calcsize ===
print("\n=== calcsize ===")
# calcsize: 포맷의 정확한 바이트 크기 계산 (패딩 포함)
fmt = '>HH4sf'
print(f"'{fmt}' 크기: {struct.calcsize(fmt)} bytes")

# === 네트워크 프로토콜 예제 ===
print("\n=== 네트워크 패킷 ===")

# 간단한 메시지 프로토콜
# Header: [type(1B), length(2B)] + Body: [data(NB)]
# !는 네트워크 바이트 순서 (빅 엔디안)
def create_packet(msg_type, data):
    # body는 UTF-8 인코딩된 바이트
    body = data.encode('utf-8')
    # 헤더: 1바이트 타입 + 2바이트 길이
    header = struct.pack('!BH', msg_type, len(body))
    return header + body

def parse_packet(packet):
    # 헤더 크기 미리 계산
    header_size = struct.calcsize('!BH')
    # 앞 헤더만 unpack
    msg_type, length = struct.unpack('!BH', packet[:header_size])
    # length만큼 본문 추출
    body = packet[header_size:header_size + length].decode('utf-8')
    return msg_type, body

# 패킷 생성
packet = create_packet(1, 'Hello, Network!')
print(f"패킷: {packet.hex()}")
print(f"크기: {len(packet)} bytes")

# 패킷 파싱 - 왕복 검증
msg_type, body = parse_packet(packet)
print(f"타입: {msg_type}, 내용: '{body}'")

# === BMP 파일 헤더 파싱 예제 ===
print("\n=== BMP 헤더 구조 ===")
# BMP는 리틀 엔디안 (< 사용)
bmp_header_fmt = '<2sIHHI'
print(f"BMP Header 크기: {struct.calcsize(bmp_header_fmt)} bytes")
print("필드: signature(2s), filesize(I), reserved(H,H), dataoffset(I)")

# 가짜 BMP 헤더 생성 후 즉시 파싱
bmp_header = struct.pack(bmp_header_fmt, b'BM', 1024, 0, 0, 54)
sig, size, r1, r2, offset = struct.unpack(bmp_header_fmt, bmp_header)
print(f"Signature: {sig.decode()}")
print(f"File size: {size} bytes")
print(f"Data offset: {offset} bytes")

# === struct.Struct (재사용) ===
print("\n=== struct.Struct ===")
# Struct 객체: 포맷을 한번 컴파일해 재사용 (반복 호출 시 빠름)
point_struct = struct.Struct('>ff')  # 2D 좌표
print(f"포맷: {point_struct.format}, 크기: {point_struct.size} bytes")

# 여러 포인트를 하나의 버퍼에 패킹
points = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
# bytearray: 가변 바이트 버퍼 (pack_into용)
buffer = bytearray(point_struct.size * len(points))

# pack_into: 버퍼의 특정 오프셋에 직접 쓰기 (메모리 복사 최소화)
for i, (x, y) in enumerate(points):
    point_struct.pack_into(buffer, i * point_struct.size, x, y)

print(f"버퍼: {buffer.hex()}")

# unpack_from: 버퍼의 특정 오프셋에서 직접 읽기
for i in range(len(points)):
    x, y = point_struct.unpack_from(buffer, i * point_struct.size)
    print(f"  Point {i}: ({x}, {y})")

# === iter_unpack (Python 3.4+) ===
print("\n=== iter_unpack ===")
# 같은 포맷이 반복되는 바이트 스트림을 이터레이터로 풀어줌
data = struct.pack('>3i', 10, 20, 30)
for values in struct.iter_unpack('>i', data):
    print(f"  값: {values[0]}")

# 출력:
# === 기본 pack / unpack ===
# packed: (hex 출력)
# unpacked: (42, 256, 3.14...)
# === 바이트 순서 ===
# 빅 엔디안:    01020304
# 리틀 엔디안:  04030201
# === 네트워크 패킷 ===
# 타입: 1, 내용: 'Hello, Network!'
# === BMP 헤더 구조 ===
# Signature: BM
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 기본 pack / unpack ===
packed: b'*\x00\x00\x00\x00\x01\x00\x00\xc3\xf5H@'
hex: 2a00000000010000c3f54840
크기: 12 bytes
unpacked: (42, 256, 3.140000104904175)

=== 포맷 문자 ===
  'b': signed char (1 bytes)
  'B': unsigned char (1 bytes)
  'h': short (2 bytes)
  'H': unsigned short (2 bytes)
  'i': int (4 bytes)
  'I': unsigned int (4 bytes)
  'q': long long (8 bytes)
  'Q': unsigned long long (8 bytes)
  'f': float (4 bytes)
  'd': double (8 bytes)
  '?': bool (1 bytes)
  's': char[] (N bytes bytes)

=== 바이트 순서 ===
빅 엔디안:    01020304
리틀 엔디안:  04030201
네이티브:     04030201

바이트 순서 접두사:
  '@': 네이티브 (기본, 패딩 있음)
  '=': 네이티브 (패딩 없음)
  '<': 리틀 엔디안
  '>': 빅 엔디안 (네트워크)
  '!': 네트워크 (= 빅 엔디안)

=== 문자열 ===
'10s' pack: b'Hello\x00\x00\x00\x00\x00'
unpack: (b'Hello\x00\x00\x00\x00\x00',)
strip: b'Hello'

혼합: seq=1001, tag=TEMP, value=36.5

=== calcsize ===
'>HH4sf' 크기: 12 bytes

=== 네트워크 패킷 ===
패킷: 01000f48656c6c6f2c204e6574776f726b21
크기: 18 bytes
타입: 1, 내용: 'Hello, Network!'

=== BMP 헤더 구조 ===
BMP Header 크기: 14 bytes
필드: signature(2s), filesize(I), reserved(H,H), dataoffset(I)
Signature: BM
File size: 1024 bytes
Data offset: 54 bytes

=== struct.Struct ===
포맷: >ff, 크기: 8 bytes
버퍼: 3f80000040000000404000004080000040a0000040c00000
  Point 0: (1.0, 2.0)
  Point 1: (3.0, 4.0)
  Point 2: (5.0, 6.0)

=== iter_unpack ===
  값: 10
  값: 20
  값: 30
````

**풀이 요점**

- 접두사를 뺀 `'ihf'` 만 12바이트이고, 접두사를 단 나머지 포맷은 칸 너비를 그대로 더한 크기(`>HH4sf` 12 · `<2sIHHI` 14 · `!BH` 3)다.
- 패킷 파싱은 `calcsize` 로 헤더 크기를 구해 그만큼만 `unpack` 한다 — `unpack` 이 정확한 길이를 요구하기 때문이다.
- `s` 칸은 `bytes` 를 받으므로 글자는 `encode` 로 넣고 `decode` 로 꺼낸다.
- `Struct` 의 `.size` 를 레코드 단위로 삼아 `i * size` 오프셋으로 `pack_into` · `unpack_from` 한다.
- `unpack` · `unpack_from` · `iter_unpack` 은 모두 튜플을 돌려주므로 값 하나는 `[0]` 이나 풀어 넣기로 꺼낸다.
- 포맷 표의 `s` 줄이 `N bytes bytes` 로 찍히는 것은 출력 문구의 흠이며 `struct` 동작과는 무관하다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
