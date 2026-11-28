# python/python-advanced/05 — ctypes (C 라이브러리 호출) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `42 13` — 둘 다 Python `int` 로 돌아온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
42 13
```

**왜 그런가**
- `abs` 는 `c_int` 로 변환된 `-42` 를 받아 절댓값 `42` 를 돌려준다.
- `strlen` 은 `b"Hello, World!"` 의 바이트 수를 센다 — `Hello` 5 + `,` 1 + 빈칸 1 + `World` 5 + `!` 1 = 13 이다.
- `restype` 이 `c_int` · `c_size_t` 같은 단순 타입이면 돌아온 값은 Python `int` 로 바뀌어 들어온다.
- 근거: 2-summary 「동작 방식 (2)」.

### 2. `b'AAAAAAAAAA'` 다음 `b'Hello!AAAA'`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
b'AAAAAAAAAA'
b'Hello!AAAA'
```

**왜 그런가**
- `create_string_buffer(20)` 은 0 바이트로 채운 20바이트를 만든다.
- `memset` 이 앞 10바이트만 `A` 로 채우므로 11번째부터는 0 바이트다 — `.value` 는 첫 0 바이트 앞까지만 돌려주어 `A` 10개가 된다.
- `len(src.value)` 는 끝의 0 바이트를 세지 않아 6 이다.
- `memmove` 는 `Hello!` 6바이트만 덮어쓰고 0 바이트는 복사하지 않으므로, 7~10번째의 `A` 4개가 그대로 남는다.
- 근거: 2-summary 「동작 방식 (8)」.

### 3. `[5, 4, 3, 2, 1]` — 내림차순이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[5, 4, 3, 2, 1]
```

**왜 그런가**
- `qsort` 는 비교 함수가 음수를 돌려주면 첫 원소를 앞에, 양수면 뒤에 둔다.
- 원본의 `a[0] - b[0]` 은 작은 값을 앞으로 보내는 오름차순이다.
- `b[0] - a[0]` 은 부호가 뒤집혀 큰 값이 앞으로 간다.
- `qsort` 가 배열을 제자리에서 바꾸므로 `list(arr)` 에 정렬된 차례가 보인다.
- 근거: 2-summary 「동작 방식 (7)」.

### 4. ctypes 가 Python 값을 어떤 C 타입으로 바꿀지 알아야 하기 때문이다

- ctypes 는 C 함수의 시그니처를 스스로 알지 못하므로, 인자를 무엇으로 바꿔 넘기고 반환을 무엇으로 읽을지 사람이 알려 줘야 한다.
- 정하지 않으면 반환은 `int` 로 가정되고, 원본 주석대로 64bit 환경에서는 `int` 보다 넓은 값이 잘려 결과가 틀릴 수 있다.
- 원본 팁도 「반드시 설정해야 올바른 타입 변환이 된다」고 적는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. `bytes` 만 받는다 — `str` 은 변환 단계에서 오류가 난다

- C 의 `char*` 는 바이트의 줄이고 Python `str` 은 유니코드 글자의 줄이라 그대로 옮길 수 없다.
- 그래서 `c_char_p` 자리에는 `b"Hello"` 처럼 `bytes` 를 넘기고, `str` 이라면 `.encode()` 로 바꿔 넘긴다.
- 정확한 예외 이름은 정리에서도 확인 필요로 남겨 두었다.
- 근거: 2-summary 「어디서 틀리나 2」 · 원본 팁.

### 6. 쓸 수 없다 — `byref()` 는 함수 인자 전달 전용이다

- `byref()` 는 함수를 부르는 그 자리에서 주소를 넘기기 위한 가벼운 포인터다.
- 변수에 담아 두고 `.contents` 로 역참조하거나 구조체에 저장하려면 정식 포인터를 만드는 `pointer()` 를 써야 한다.
- 대신 `byref()` 는 `pointer()` 보다 빠르다(원본 팁).
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 7. C 가 그 함수 포인터를 쓰는 동안 Python 쪽 객체가 거둬지면 안 되기 때문이다

- `CMPFUNC(py_compare)` 객체는 C 가 부를 수 있는 함수 포인터를 품고 있다.
- 아무 변수도 그것을 가리키지 않으면 GC 가 거둬 갈 수 있고, C 가 아직 그 포인터를 쥐고 있으면 사라진 곳을 부르게 된다.
- 그래서 원본 주석은 「GC되지 않게 변수에 보관 필수」라고 적는다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 4」.

### 8. 인자 개수가 정해지지 않아서다 — 「첫 인자만 변환」은 의심스럽다

- `printf` 는 가변 인자 함수라 `argtypes` 리스트로 모든 인자를 미리 적기 어렵다.
- 원본 주석은 「첫 인자만 변환 후 나머지는 그대로 전달」이라 하지만, `argtypes` 가 없을 때 ctypes 는 인자마다 기본 규칙(정수 → `int`, `bytes` → `char*`, `None` → `NULL`)으로 변환하는 것으로 보인다(확인 필요).
- 가변 인자의 전달 방식이 플랫폼마다 다를 수 있어 이 꼴이 어디서나 안전하다고 단정할 수도 없다(확인 필요).
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 9. 메모리 배치가 같아서 둘이 같은 것이 된다 — 그래서 차례가 곧 배치다

- `Structure` 를 상속하고 `_fields_` 를 적으면 ctypes 가 C 의 `struct` 와 같은 메모리 배치를 만든다.
- 필드는 정의한 차례대로 놓이고 정렬 규칙이 적용되므로, `x` · `y` 의 차례와 타입이 C 선언과 어긋나면 C 함수는 엉뚱한 바이트를 엉뚱한 필드로 읽는다.
- 같은 원리로 `Rect` 처럼 구조체를 필드로 넣으면 중첩 `struct` 가 되고, `Point * 3` 은 C 의 `struct Point[3]` 이 된다.
- 근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

## 실습 정답

### 실습 1. libc 를 ctypes 로 두루 불러 보는 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 — 플랫폼별 libc 로드 | `if sys.platform == 'linux': libc = ctypes.CDLL('libc.so.6')` … `elif 'darwin'` … `else: ctypes.CDLL('msvcrt')` |
| 1단계 — 경로 찾기 | `ctypes.util.find_library('c')` · `ctypes.util.find_library('m')` |
| 2단계 — `abs` | `libc.abs.argtypes = [ctypes.c_int]` · `libc.abs.restype = ctypes.c_int` · `libc.abs(-42)` |
| 2단계 — `time` | `libc.time.argtypes = [ctypes.POINTER(ctypes.c_long)]` · `restype = ctypes.c_long` · `libc.time(None)` |
| 2단계 — `strlen` | `libc.strlen.argtypes = [ctypes.c_char_p]` · `restype = ctypes.c_size_t` · `libc.strlen(b"Hello, World!")` |
| 2단계 — `printf` | `libc.printf(b"C printf: %d + %d = %d\n", 3, 4, 7)` |
| 3단계 — 타입 매핑 | `type_info` 리스트 · `ctypes.sizeof(ctype) if ctype not in (ctypes.c_char_p, ctypes.c_void_p) else 'ptr'` |
| 4단계 — `Point` | `class Point(ctypes.Structure)` 의 `_fields_` · `__repr__` · `ctypes.sizeof(p)` |
| 4단계 — `Rect` | `class Rect` 의 `('origin', Point)` · `area` 속성 · `Rect(Point(0, 0), 10.0, 5.0)` |
| 4단계 — `Flags` | `('readable', ctypes.c_uint, 1)` … · `Flags(readable=1, writable=1, executable=0)` |
| 5단계 — 배열 | `IntArray10 = ctypes.c_int * 10` · `IntArray10(*range(10))` · `PointArray = Point * 3` |
| 6단계 — 포인터 | `ctypes.pointer(i)` · `p.contents.value` · `get_by_ref_example` 의 `byref` 주석 줄 |
| 7단계 — 콜백 | `CMPFUNC = ctypes.CFUNCTYPE(...)` · `py_compare` 의 `a[0] - b[0]` · `cmp_func = CMPFUNC(py_compare)` · `libc.qsort(...)` |
| 8단계 — 메모리 | `ctypes.create_string_buffer(20)` · `libc.memset(buffer, ord('A'), 10)` · `libc.memmove(buffer, src, len(src.value))` |
| 마무리 | 「ctypes 핵심 정리」 아래 `print` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-advanced/reference/ctypes-basics.py`

```python
# [고급 기법] ctypes (C 라이브러리 호출)
# 설명: ctypes로 C 공유 라이브러리 호출, 구조체 정의, 콜백 함수
# 팁: argtypes와 restype을 반드시 설정해야 올바른 타입 변환이 된다. c_char_p에는 bytes를 전달한다 (str이 아님). byref()는 pointer()보다 빠르지만 함수 인자 전달에만 사용 가능하다. 대규모 C 연동에는 cffi나 Cython이 더 적합할 수 있다.

# ctypes - Python에서 C 라이브러리 호출

# ctypes: Python 표준 FFI(Foreign Function Interface). CPython의 dlopen/LoadLibrary를 감싸 C 함수 호출을 가능하게 한다
import ctypes
# ctypes.util: 라이브러리 이름으로 실제 파일 경로를 찾는 헬퍼 (find_library)
import ctypes.util
# sys: 플랫폼 식별을 위해 sys.platform 사용
import sys
# struct: 바이너리 패킹/언패킹 (이 파일에서는 직접 사용 안 함)
import struct


# === 1. 시스템 라이브러리 로드 ===
print("=== C 라이브러리 로드 ===")

# 플랫폼별로 libc 위치가 다르므로 분기 처리한다
if sys.platform == 'linux':
    # 리눅스의 GNU C 라이브러리: libc.so.6 (cdecl 호출 규약, CDLL 사용)
    libc = ctypes.CDLL('libc.so.6')
elif sys.platform == 'darwin':
    # macOS의 C 라이브러리 동적 라이브러리
    libc = ctypes.CDLL('libc.dylib')
else:
    # Windows: msvcrt (Microsoft Visual C Runtime)
    libc = ctypes.CDLL('msvcrt')  # Windows

# find_library('c'): ldconfig/dyld가 인식하는 libc 경로를 자동 탐색
lib_path = ctypes.util.find_library('c')
print(f"libc 경로: {lib_path}")

# libm은 sin/cos 등 수학 함수가 들어있는 별도 라이브러리(리눅스 한정)
lib_m_path = ctypes.util.find_library('m')  # libm (수학)
print(f"libm 경로: {lib_m_path}")


# === 2. 기본 타입과 함수 호출 ===
print("\n=== 기본 함수 호출 ===")

# argtypes/restype 미설정 시 ctypes는 모든 인자를 c_int로 가정 -> 64bit 환경에서 잘못된 결과 가능
# argtypes: C 함수 시그니처에 대응하는 인자 타입 리스트 (ctypes가 변환 수행)
libc.abs.argtypes = [ctypes.c_int]    # 인자 타입
# restype: C 함수의 반환 타입을 명시. 미지정 시 int로 가정됨
libc.abs.restype = ctypes.c_int        # 반환 타입
# C의 abs(int) 호출 -> Python int로 자동 변환
result = libc.abs(-42)
print(f"abs(-42) = {result}")

# time(time_t*): 인자로 long 포인터, 반환은 long(epoch초). NULL 전달 가능
libc.time.argtypes = [ctypes.POINTER(ctypes.c_long)]
libc.time.restype = ctypes.c_long
# None을 전달하면 NULL 포인터로 변환됨
print(f"time() = {libc.time(None)}")

# strlen: char*를 받아 size_t 반환. Python str이 아닌 bytes를 전달해야 함
libc.strlen.argtypes = [ctypes.c_char_p]  # char*
libc.strlen.restype = ctypes.c_size_t
# b"..."로 bytes 리터럴 생성. ctypes가 char*로 자동 변환
result = libc.strlen(b"Hello, World!")
print(f"strlen('Hello, World!') = {result}")

# printf는 가변 인자 함수 -> argtypes 명시 어려움. ctypes는 첫 인자만 변환 후 나머지는 그대로 전달
libc.printf(b"C printf: %d + %d = %d\n", 3, 4, 7)


# === 3. ctypes 타입 매핑 ===
print("\n=== 타입 매핑 ===")
# Python ctypes 타입 <-> C 기본 타입 매핑 표
type_info = [
    ('c_bool',    ctypes.c_bool,    'bool'),
    ('c_char',    ctypes.c_char,    'char'),
    ('c_int',     ctypes.c_int,     'int'),
    ('c_long',    ctypes.c_long,    'long'),
    ('c_float',   ctypes.c_float,   'float'),
    ('c_double',  ctypes.c_double,  'double'),
    ('c_char_p',  ctypes.c_char_p,  'char*'),
    ('c_void_p',  ctypes.c_void_p,  'void*'),
]
for name, ctype, c_equiv in type_info:
    # sizeof(): 해당 타입이 차지하는 바이트 수. 포인터는 시스템에 따라 다름(보통 8바이트)
    size = ctypes.sizeof(ctype) if ctype not in (ctypes.c_char_p, ctypes.c_void_p) else 'ptr'
    print(f"  {name:12s} -> C {c_equiv:8s} ({size} bytes)")


# === 4. 구조체 ===
print("\n=== C 구조체 ===")

# Structure 상속 -> C struct 메모리 레이아웃 그대로 매핑
class Point(ctypes.Structure):
    # _fields_: (이름, 타입) 튜플 목록. 정의 순서대로 메모리에 배치되며 align 규칙 적용
    _fields_ = [
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
    ]

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

# 구조체 인스턴스 생성 (C에서 Point p = {3.0, 4.0})
p = Point(3.0, 4.0)
print(f"Point: {p}")
# sizeof: double 2개 = 16바이트 (정렬 패딩 포함될 수 있음)
print(f"sizeof(Point): {ctypes.sizeof(p)} bytes")

# 중첩 구조체: 다른 Structure를 필드로 포함 가능
class Rect(ctypes.Structure):
    _fields_ = [
        ('origin', Point),
        ('width', ctypes.c_double),
        ('height', ctypes.c_double),
    ]

    @property
    def area(self):
        return self.width * self.height

# 중첩 구조체 초기화
rect = Rect(Point(0, 0), 10.0, 5.0)
print(f"Rect: origin={rect.origin}, {rect.width}x{rect.height}, area={rect.area}")

# 비트필드: 필드 뒤 정수로 비트 수 지정. C의 unsigned int x : 1; 과 동일
class Flags(ctypes.Structure):
    _fields_ = [
        ('readable', ctypes.c_uint, 1),    # 1비트
        ('writable', ctypes.c_uint, 1),
        ('executable', ctypes.c_uint, 1),
    ]

# 비트필드는 1바이트(또는 정렬 단위)에 패킹됨
f = Flags(readable=1, writable=1, executable=0)
print(f"Flags: r={f.readable}, w={f.writable}, x={f.executable}")


# === 5. 배열 ===
print("\n=== 배열 ===")

# 타입 * N: ctypes 배열 타입 생성 (C의 int arr[10] 과 같음)
IntArray10 = ctypes.c_int * 10
# 가변 인자로 초기값 전달
arr = IntArray10(*range(10))
print(f"배열: {list(arr)}")
print(f"합계: {sum(arr)}")

# 사용자 정의 구조체 배열도 동일 방식
PointArray = Point * 3
points = PointArray(
    Point(0, 0), Point(1, 1), Point(2, 4)
)
for i, p in enumerate(points):
    print(f"  points[{i}] = {p}")


# === 6. 포인터 ===
print("\n=== 포인터 ===")

# c_int(42): C의 int 변수처럼 동작하는 ctypes 객체
i = ctypes.c_int(42)
# pointer(i): 정식 LP_c_int 객체 생성. .contents로 역참조 가능
p = ctypes.pointer(i)          # int*
print(f"값: {i.value}, 포인터 값: {p.contents.value}")

# byref: 임시 포인터로 함수 호출에만 사용. pointer보다 빠르고 가벼움
def get_by_ref_example():
    value = ctypes.c_int(0)
    # libc.some_func(ctypes.byref(value))  # 출력 파라미터
    return value.value


# === 7. 콜백 함수 ===
print("\n=== 콜백 함수 ===")

# CFUNCTYPE: Python 함수를 C가 호출 가능한 함수 포인터로 만드는 팩토리
# 시그니처: int(*)(const int*, const int*) 형태 (qsort 비교 함수)
CMPFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int,                 # 반환 타입
    ctypes.POINTER(ctypes.c_int), # 인자 1
    ctypes.POINTER(ctypes.c_int)  # 인자 2
)

# 콜백 본체: 포인터를 인덱싱하면 가리키는 값에 접근
def py_compare(a, b):
    """Python 비교 함수 (C에서 콜백으로 호출)"""
    return a[0] - b[0]

# 함수 포인터 객체 생성. GC되지 않게 변수에 보관 필수
cmp_func = CMPFUNC(py_compare)

# qsort 시그니처: void qsort(void* base, size_t n, size_t size, cmp)
arr = (ctypes.c_int * 5)(5, 3, 1, 4, 2)
print(f"정렬 전: {list(arr)}")
# C qsort가 우리 Python 함수를 콜백으로 호출하며 정렬
libc.qsort(
    arr,                          # 배열
    len(arr),                     # 요소 수
    ctypes.sizeof(ctypes.c_int),  # 요소 크기
    cmp_func                      # 비교 함수
)
print(f"정렬 후: {list(arr)}")


# === 8. 메모리 직접 접근 ===
print("\n=== 메모리 조작 ===")

# create_string_buffer: 가변 char 배열 (C의 char buf[20])
buffer = ctypes.create_string_buffer(20)  # char[20]
# memset(dst, byte, n): n바이트를 byte로 채움
libc.memset(buffer, ord('A'), 10)
print(f"memset 결과: {buffer.value}")

# 원본 버퍼 생성
src = ctypes.create_string_buffer(b"Hello!")
# memmove(dst, src, n): 영역 겹침 안전한 복사
libc.memmove(buffer, src, len(src.value))
print(f"memmove 결과: {buffer.value}")


print("\nctypes 핵심 정리")
print("="*50)
print("CDLL(): 공유 라이브러리(.so/.dll) 로드")
print("argtypes/restype: 함수 시그니처 정의")
print("Structure: C 구조체 매핑")
print("CFUNCTYPE: 콜백 함수 타입 정의")
print("pointer/byref: 포인터 전달")
print("c_char_p: 문자열은 bytes 타입 사용")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- 함수를 부르기 전에 `argtypes` · `restype` 를 먼저 적는 차례가 이 스크립트의 뼈대다.
- 문자열은 처음부터 `b"…"` 로 써서 `c_char_p` 와 맞춘다.
- 구조체 · 배열은 「타입을 먼저 만들고, 그 타입을 불러 값을 만든다」는 같은 꼴을 따른다.
- `cmp_func` 를 변수에 담아 두는 것은 꾸밈이 아니라 콜백이 사라지지 않게 하는 필수 줄이다.
- `memmove` 가 `len(src.value)` 만큼만 복사하므로 결과 뒤에 `A` 가 남는다는 점을 손으로 따라가 본다.
- 정답 코드의 `printf` · `qsort` · `memset` · `memmove` 에는 `argtypes` 가 없다 — 팁을 끝까지 지키려면 이 함수들에도 시그니처를 적어 보는 것이 다음 연습이 된다(원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
