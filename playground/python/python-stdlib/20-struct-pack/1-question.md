# python/python-stdlib/20 — struct (바이너리 데이터) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `'ihf'` 세 값을 접두사 없이 pack 하면 (예측)

```python
# 질문용 발췌
data = struct.pack('ihf', 42, 256, 3.14)
print(f"hex: {data.hex()}")
print(f"크기: {len(data)} bytes")
```

- `len(data)` 는 몇인가?
- 칸 너비를 그냥 더한 값과 다르다면, hex 의 어느 자리에 무엇이 끼어 있나?

### 2. `0x01020304` 를 `'>I'` 와 `'<I'` 로 (예측)

```python
# 질문용 발췌
value = 0x01020304
print(f"빅 엔디안:    {struct.pack('>I', value).hex()}")
print(f"리틀 엔디안:  {struct.pack('<I', value).hex()}")
```

- 두 줄은 각각 어떻게 찍히나?

### 3. 헤더 + 본문 패킷의 길이와 hex (예측)

```python
# 질문용 발췌
def create_packet(msg_type, data):
    body = data.encode('utf-8')
    header = struct.pack('!BH', msg_type, len(body))
    return header + body

packet = create_packet(1, 'Hello, Network!')
print(f"패킷: {packet.hex()}")
print(f"크기: {len(packet)} bytes")
```

- 패킷의 hex 앞 여섯 자리와 전체 크기는 무엇인가?

### 4. `'f'` 로 담은 3.14 가 3.14 로 돌아오지 않는 까닭 (왜)

- `unpack` 결과가 `3.140000104904175` 가 되는 까닭은 무엇인가?

### 5. 네트워크 프로토콜에 `!` 나 `>` 를 쓰는 까닭 (왜)

- 접두사 없는 기본 포맷 대신 `!` · `>` 를 쓰는 까닭은 무엇인가?

### 6. `unpack` 에 넘기는 바이트의 길이 (경계)

- 포맷 크기와 길이가 다른 바이트를 `unpack` 에 주면 어떻게 되나?
- `parse_packet` 은 18바이트 패킷에서 헤더를 읽을 때 이 문제를 어떻게 피하나?

### 7. 고정 길이 `s` 칸에 길이가 다른 바이트를 넣을 때 (경계)

- `'10s'` 에 5바이트를 넣고 다시 `unpack` 하면 무엇이 돌아오며, 원래 5바이트를 얻으려면 무엇을 하나?

### 8. `'=I'` 와 `'<I'` 의 결과 (경계)

- `'=I'` 로 pack 한 결과는 어느 플랫폼에서나 `'<I'` 의 결과와 같은가?

### 9. `s` 포맷과 Python 의 `str` (연결)

- `s` 칸을 쓰는 코드에 `encode` 와 `decode` 가 따라붙는 까닭은 무엇인가?

### 10. `Struct` · `pack_into` · `unpack_from` 과 `iter_unpack` (연결)

- 점 세 개를 한 버퍼에 쓰고 읽는 흐름은 `iter_unpack` 과 어떤 점에서 닮았나?

## 실습

### 실습 1. `struct` 로 바이너리 데이터 한 바퀴 돌기

**만들 것** — 기본 pack/unpack, 포맷 문자 표, 바이트 순서, 문자열 칸, 크기 계산, 네트워크 패킷, BMP 헤더, `Struct` 재사용, `iter_unpack` 을 차례로 보여 주는 스크립트 하나.

**요구 조건**

1. 1단계(기본) — `42`, `256`, `3.14` 를 접두사 없는 `'ihf'` 로 pack 해 그 `bytes`, hex, 길이를 찍고, 같은 포맷으로 unpack 한 튜플을 찍는다.
2. 2단계(포맷 문자) — 미리 주어진 `formats` 사전을 돌며 문자 · 설명 · 크기를 한 줄씩 찍는다.
3. 3단계(바이트 순서) — `0x01020304` 를 빅 엔디안 · 리틀 엔디안 · 패딩 없는 네이티브의 4바이트 unsigned int 로 각각 pack 해 hex 를 찍는다.
4. 4단계(문자열) — `b'Hello'` 를 10바이트 고정 칸으로 pack 하고, unpack 한 튜플을 찍고, 뒤쪽 `\x00` 을 걷어 낸 값을 찍는다.
5. 4단계 이어서 — `1001`, `b'TEMP'`, `36.5` 를 빅 엔디안 `H` · `4s` · `f` 로 pack 했다가 unpack 해, 태그는 글자로 바꾸고 값은 소수 한 자리로 찍는다.
6. 5단계(크기) — `'>HH4sf'` 의 바이트 크기를 계산해 찍는다.
7. 6단계(패킷) — `create_packet(msg_type, data)` 는 본문을 UTF-8 로 인코딩하고, 네트워크 순서의 1바이트 타입 + 2바이트 길이 헤더를 앞에 붙여 돌려준다.
8. 6단계 이어서 — `parse_packet(packet)` 은 헤더 크기를 계산해 헤더만 unpack 하고, 읽은 길이만큼 본문을 잘라 디코딩해 `(타입, 본문)` 을 돌려준다. `'Hello, Network!'` 로 만든 패킷의 hex · 크기와 파싱 결과를 찍는다.
9. 7단계(BMP) — 리틀 엔디안의 서명(2바이트 문자열) · 파일 크기(4바이트 unsigned) · 예약 칸 둘(2바이트 unsigned) · 데이터 오프셋(4바이트 unsigned) 포맷을 만들고, 그 크기를 찍고, `b'BM'`, `1024`, `0`, `0`, `54` 로 pack 한 뒤 unpack 해 서명 · 파일 크기 · 데이터 오프셋을 찍는다.
10. 8단계(Struct) — 빅 엔디안 실수 두 개짜리 `Struct` 를 만들어 포맷과 크기를 찍고, 점 세 개가 들어갈 `bytearray` 에 `pack_into` 로 `i * 크기` 오프셋마다 쓴 뒤 hex 를 찍고, `unpack_from` 으로 같은 오프셋에서 읽어 점마다 찍는다.
11. 9단계(iter_unpack) — `10`, `20`, `30` 을 빅 엔디안 int 세 개로 pack 하고, `iter_unpack` 으로 4바이트씩 풀어 값마다 찍는다.

**시작 코드**

```python
import struct

# === 기본 pack / unpack ===
print("=== 기본 pack / unpack ===")
data = None  # TODO: 42, 256, 3.14 를 접두사 없는 'ihf' 로 pack
print(f"packed: {data}")
print(f"hex: {data.hex()}")
print(f"크기: {len(data)} bytes")

values = None  # TODO: data 를 같은 포맷으로 unpack
print(f"unpacked: {values}")

# === 포맷 문자 ===
print("\n=== 포맷 문자 ===")
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
# TODO: formats 를 돌며 "  'b': signed char (1 bytes)" 꼴로 찍는다

# === 바이트 순서 (Endianness) ===
print("\n=== 바이트 순서 ===")
value = 0x01020304
big = None     # TODO: 빅 엔디안 unsigned int
little = None  # TODO: 리틀 엔디안 unsigned int
native = None  # TODO: 패딩 없는 네이티브 unsigned int
print(f"빅 엔디안:    {big.hex()}")
print(f"리틀 엔디안:  {little.hex()}")
print(f"네이티브:     {native.hex()}")

print("\n바이트 순서 접두사:")
print("  '@': 네이티브 (기본, 패딩 있음)")
print("  '=': 네이티브 (패딩 없음)")
print("  '<': 리틀 엔디안")
print("  '>': 빅 엔디안 (네트워크)")
print("  '!': 네트워크 (= 빅 엔디안)")

# === 문자열 처리 ===
print("\n=== 문자열 ===")
packed = None    # TODO: b'Hello' 를 10바이트 고정 칸으로 pack
print(f"'10s' pack: {packed}")
unpacked = None  # TODO: 같은 포맷으로 unpack
print(f"unpack: {unpacked}")
stripped = None  # TODO: unpacked 의 첫 값에서 뒤쪽 \x00 을 걷어 낸다
print(f"strip: {stripped}")

packet = None    # TODO: 1001, b'TEMP', 36.5 를 빅 엔디안 H · 4s · f 로 pack
seq, tag, value = None, None, None  # TODO: 같은 포맷으로 unpack
print(f"\n혼합: seq={seq}, tag={tag.decode()}, value={value:.1f}")

# === calcsize ===
print("\n=== calcsize ===")
fmt = '>HH4sf'
size = None  # TODO: fmt 의 바이트 크기
print(f"'{fmt}' 크기: {size} bytes")

# === 네트워크 프로토콜 예제 ===
print("\n=== 네트워크 패킷 ===")

def create_packet(msg_type, data):
    # TODO: 본문을 UTF-8 로 인코딩하고, '!' 순서의 1바이트 타입 + 2바이트 길이 헤더를 앞에 붙여 돌려준다
    pass

def parse_packet(packet):
    # TODO: 헤더 크기를 계산해 헤더만 unpack 하고, 길이만큼 본문을 잘라 decode 해 (타입, 본문) 을 돌려준다
    pass

packet = create_packet(1, 'Hello, Network!')
print(f"패킷: {packet.hex()}")
print(f"크기: {len(packet)} bytes")

msg_type, body = parse_packet(packet)
print(f"타입: {msg_type}, 내용: '{body}'")

# === BMP 파일 헤더 파싱 예제 ===
print("\n=== BMP 헤더 구조 ===")
bmp_header_fmt = None  # TODO: 리틀 엔디안 서명(2s) · filesize · reserved 둘 · dataoffset
print(f"BMP Header 크기: {None} bytes")  # TODO: None 자리에 포맷 크기
print("필드: signature(2s), filesize(I), reserved(H,H), dataoffset(I)")

bmp_header = None  # TODO: b'BM', 1024, 0, 0, 54 로 pack
sig, size, r1, r2, offset = None, None, None, None, None  # TODO: unpack
print(f"Signature: {sig.decode()}")
print(f"File size: {size} bytes")
print(f"Data offset: {offset} bytes")

# === struct.Struct (재사용) ===
print("\n=== struct.Struct ===")
point_struct = None  # TODO: 빅 엔디안 실수 두 개짜리 Struct
print(f"포맷: {point_struct.format}, 크기: {point_struct.size} bytes")

points = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
buffer = None  # TODO: 점 세 개가 들어갈 bytearray

# TODO: 점마다 pack_into 로 i * 크기 오프셋에 쓴다

print(f"버퍼: {buffer.hex()}")

# TODO: 점마다 unpack_from 으로 읽어 "  Point 0: (1.0, 2.0)" 꼴로 찍는다

# === iter_unpack ===
print("\n=== iter_unpack ===")
data = None  # TODO: 10, 20, 30 을 빅 엔디안 int 세 개로 pack
# TODO: iter_unpack 으로 4바이트씩 풀어 "  값: 10" 꼴로 찍는다
```

**확인 방법** — `python struct-pack.py` 로 돌려, 정답의 실행 결과와 줄마다 같은지 본다(특히 `크기: 12 bytes` · 엔디안 hex · 패킷 hex · `BMP Header 크기: 14 bytes` · 버퍼 hex).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
