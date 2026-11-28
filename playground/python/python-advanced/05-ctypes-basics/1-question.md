# python/python-advanced/05 — ctypes (C 라이브러리 호출) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 시그니처를 적은 `abs` 와 `strlen` (예측)

```python
# 질문용 발췌
libc.abs.argtypes = [ctypes.c_int]
libc.abs.restype = ctypes.c_int
libc.strlen.argtypes = [ctypes.c_char_p]
libc.strlen.restype = ctypes.c_size_t
print(libc.abs(-42), libc.strlen(b"Hello, World!"))
```

- 찍히는 두 값은 무엇이고, 각각 어떤 Python 타입으로 손에 들어오나?

### 2. `memset` 다음 `memmove` (예측)

```python
# 질문용 발췌
buffer = ctypes.create_string_buffer(20)
libc.memset(buffer, ord('A'), 10)
print(buffer.value)
src = ctypes.create_string_buffer(b"Hello!")
libc.memmove(buffer, src, len(src.value))
print(buffer.value)
```

- 두 번의 `print` 는 각각 어떤 `bytes` 를 찍나?

### 3. 비교 함수를 뒤집은 `qsort` (예측)

```python
# 질문용 발췌
CMPFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
def py_compare(a, b):
    return b[0] - a[0]
cmp_func = CMPFUNC(py_compare)
arr = (ctypes.c_int * 5)(5, 3, 1, 4, 2)
libc.qsort(arr, len(arr), ctypes.sizeof(ctypes.c_int), cmp_func)
print(list(arr))
```

- 마지막 줄은 어떤 리스트를 찍나?

### 4. `argtypes` · `restype` 를 굳이 적는 까닭 (왜)

- C 함수를 부르기 전에 왜 `argtypes` 와 `restype` 를 정해 두나?

### 5. `char*` 자리에 넘길 수 있는 것 (경계)

- `argtypes = [c_char_p]` 인 `strlen` 에 `"Hello"`(str) 를 넘기는 것과 `b"Hello"`(bytes) 를 넘기는 것은 어떻게 다른가?

### 6. `byref()` 가 쓰일 수 있는 자리 (경계)

- `byref()` 가 돌려준 것을 변수에 담아 두었다가 역참조하는 데 쓸 수 있나?

### 7. 콜백 객체 `cmp_func` 를 변수에 담는 까닭 (왜)

- `CMPFUNC(py_compare)` 로 만든 객체를 왜 `cmp_func` 라는 변수에 붙들어 두어야 하나?

### 8. 가변 인자 함수 `printf` 를 부르는 방식 (경계)

- `printf` 에는 왜 `argtypes` 를 적지 않았고, 원본 주석의 「첫 인자만 변환 후 나머지는 그대로 전달」이라는 설명은 어디까지 믿을 수 있나?

### 9. `Structure` 와 C 의 `struct` 를 잇는 것 (연결)

- `class Point(ctypes.Structure)` 와 C 의 `struct Point { double x; double y; }` 를 같은 것으로 만들어 주는 것은 무엇이고, 그래서 `_fields_` 의 차례가 왜 중요한가?

## 실습

### 실습 1. libc 를 ctypes 로 두루 불러 보는 스크립트

**만들 것** — 플랫폼에 맞는 C 표준 라이브러리를 불러와, 함수 호출 · 타입 매핑 · 구조체 · 배열 · 포인터 · 콜백 · 메모리 조작을 차례로 보여 주는 Python 스크립트 하나.

**준비물** — Python 표준 라이브러리만 쓴다(`ctypes` · `ctypes.util` · `sys`). 리눅스 · macOS · Windows 중 하나에서 libc 를 불러올 수 있어야 한다.

**요구 조건**

1. **1단계 — 라이브러리 로드.** `sys.platform` 이 `'linux'` 면 `libc.so.6`, `'darwin'` 이면 `libc.dylib`, 그 밖이면 `msvcrt` 를 `ctypes.CDLL` 로 불러 `libc` 에 담는다. `ctypes.util.find_library` 로 `'c'` 와 `'m'` 의 경로를 찾아 찍는다.
2. **2단계 — 기본 함수 호출.** `abs` 의 인자 · 반환 타입을 `c_int` 로 정하고 `abs(-42)` 를 찍는다. `time` 의 인자를 `POINTER(c_long)`, 반환을 `c_long` 으로 정하고 `None` 을 넘긴 결과를 찍는다. `strlen` 의 인자를 `c_char_p`, 반환을 `c_size_t` 로 정하고 `b"Hello, World!"` 의 길이를 찍는다. `printf` 로 `3 + 4 = 7` 을 C 쪽에서 찍는다.
3. **3단계 — 타입 매핑.** `c_bool` · `c_char` · `c_int` · `c_long` · `c_float` · `c_double` · `c_char_p` · `c_void_p` 와 대응하는 C 타입 이름을 짝지은 목록을 돌며, 이름 · C 타입 · 바이트 수를 한 줄씩 찍는다. 포인터 타입 둘은 바이트 수 대신 `'ptr'` 를 찍는다.
4. **4단계 — 구조체.** `double` 필드 `x` · `y` 를 가진 `Point` 를 만들고 `Point(x, y)` 꼴로 보이게 한 뒤, `Point(3.0, 4.0)` 과 그 크기를 찍는다. `Point` 필드 `origin` 과 `double` 필드 `width` · `height` 를 가진 `Rect` 를 만들고 넓이를 돌려주는 `area` 속성을 둔다. 1비트 `unsigned int` 필드 `readable` · `writable` · `executable` 를 가진 `Flags` 를 이름 인자로 만들어 세 값을 찍는다.
5. **5단계 — 배열.** `int` 10칸 배열 타입을 만들어 0~9 로 채우고, 리스트와 합계를 찍는다. `Point` 3칸 배열을 만들어 원소마다 번호와 함께 찍는다.
6. **6단계 — 포인터.** `c_int(42)` 의 포인터를 `pointer` 로 만들어 원래 값과 역참조한 값을 함께 찍는다. `byref` 를 출력 파라미터로 넘기는 꼴을 보이는 함수 `get_by_ref_example` 을 둔다(C 함수 호출 줄은 주석으로 둔다).
7. **7단계 — 콜백.** `int (*)(int*, int*)` 꼴의 함수 포인터 타입을 `CFUNCTYPE` 으로 만들고, 오름차순 비교를 하는 Python 함수를 넣어 변수에 담는다. `5, 3, 1, 4, 2` 를 담은 `int` 배열을 `qsort` 로 정렬하고 앞뒤를 찍는다.
8. **8단계 — 메모리 조작.** 20바이트 버퍼를 만들어 `memset` 으로 앞 10바이트를 `'A'` 로 채운 뒤 내용을 찍는다. `b"Hello!"` 버퍼의 내용만큼을 `memmove` 로 앞 버퍼에 복사한 뒤 다시 찍는다.
9. **마무리.** 「ctypes 핵심 정리」 제목과 구분선, 그리고 `CDLL` · `argtypes/restype` · `Structure` · `CFUNCTYPE` · `pointer/byref` · `c_char_p` 를 한 줄씩 요약해 찍는다.

**시작 코드**

```python
# ctypes - Python에서 C 라이브러리 호출

import ctypes
import ctypes.util
import sys


# === 1. 시스템 라이브러리 로드 ===
print("=== C 라이브러리 로드 ===")
# TODO: sys.platform 에 따라 libc 를 CDLL 로 불러 libc 에 담는다

lib_path = None      # TODO: 'c' 의 경로 찾기
print(f"libc 경로: {lib_path}")
lib_m_path = None    # TODO: 'm' 의 경로 찾기
print(f"libm 경로: {lib_m_path}")


# === 2. 기본 타입과 함수 호출 ===
print("\n=== 기본 함수 호출 ===")
# TODO: abs 의 argtypes / restype
result = None        # TODO: abs(-42)
print(f"abs(-42) = {result}")

# TODO: time 의 argtypes / restype
print(f"time() = {None}")   # TODO: NULL 을 넘겨 time 호출

# TODO: strlen 의 argtypes / restype
result = None        # TODO: strlen 에 bytes 넘기기
print(f"strlen('Hello, World!') = {result}")

# TODO: printf 로 "C printf: %d + %d = %d\n" 에 3, 4, 7


# === 3. ctypes 타입 매핑 ===
print("\n=== 타입 매핑 ===")
type_info = [
    # TODO: ('c_bool', ctypes.c_bool, 'bool') 꼴로 여덟 개
]
for name, ctype, c_equiv in type_info:
    size = None      # TODO: 포인터 타입이면 'ptr', 아니면 바이트 수
    print(f"  {name:12s} -> C {c_equiv:8s} ({size} bytes)")


# === 4. 구조체 ===
print("\n=== C 구조체 ===")

class Point(ctypes.Structure):
    # TODO: _fields_ (x, y 는 double)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

p = None             # TODO: Point(3.0, 4.0)
print(f"Point: {p}")
print(f"sizeof(Point): {None} bytes")   # TODO: 크기

class Rect(ctypes.Structure):
    # TODO: _fields_ (origin 은 Point, width / height 는 double)

    @property
    def area(self):
        return self.width * self.height

rect = None          # TODO: 원점 Point, 10.0 x 5.0
print(f"Rect: origin={rect.origin}, {rect.width}x{rect.height}, area={rect.area}")

class Flags(ctypes.Structure):
    # TODO: _fields_ (1비트 unsigned int 셋)
    pass

f = None             # TODO: readable=1, writable=1, executable=0
print(f"Flags: r={f.readable}, w={f.writable}, x={f.executable}")


# === 5. 배열 ===
print("\n=== 배열 ===")
IntArray10 = None    # TODO: int 10칸 배열 타입
arr = None           # TODO: 0~9 로 채우기
print(f"배열: {list(arr)}")
print(f"합계: {sum(arr)}")

PointArray = None    # TODO: Point 3칸 배열 타입
points = None        # TODO: Point(0, 0), Point(1, 1), Point(2, 4)
for i, p in enumerate(points):
    print(f"  points[{i}] = {p}")


# === 6. 포인터 ===
print("\n=== 포인터 ===")
i = ctypes.c_int(42)
p = None             # TODO: i 의 포인터
print(f"값: {i.value}, 포인터 값: {None}")   # TODO: 역참조한 값

def get_by_ref_example():
    value = ctypes.c_int(0)
    # TODO: (주석으로) byref 로 출력 파라미터를 넘기는 호출
    return value.value


# === 7. 콜백 함수 ===
print("\n=== 콜백 함수 ===")
CMPFUNC = None       # TODO: CFUNCTYPE(반환, 인자1, 인자2)

def py_compare(a, b):
    """Python 비교 함수 (C에서 콜백으로 호출)"""
    # TODO: 오름차순 비교
    pass

cmp_func = None      # TODO: 함수 포인터 객체 (변수에 보관)

arr = (ctypes.c_int * 5)(5, 3, 1, 4, 2)
print(f"정렬 전: {list(arr)}")
# TODO: qsort(배열, 요소 수, 요소 크기, 비교 함수)
print(f"정렬 후: {list(arr)}")


# === 8. 메모리 직접 접근 ===
print("\n=== 메모리 조작 ===")
buffer = None        # TODO: 20바이트 버퍼
# TODO: memset 으로 앞 10바이트를 'A' 로
print(f"memset 결과: {buffer.value}")

src = None           # TODO: b"Hello!" 버퍼
# TODO: memmove 로 src 내용만큼 복사
print(f"memmove 결과: {buffer.value}")


print("\nctypes 핵심 정리")
print("="*50)
# TODO: 여섯 줄 요약
```

**확인 방법** — `python ctypes_basics.py` 로 돌려, 여덟 절의 머리 줄(`=== … ===`)이 차례로 찍히고 `abs` · `strlen` · 배열 합계 · `qsort` 정렬 후 · `memmove` 결과가 정리에서 따라간 값과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
