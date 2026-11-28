# python/python-advanced/05 — ctypes (C 라이브러리 호출) — 정리 (힌트)

> 출처 — study-site 항목 `python/ctypes-basics`(항목 데이터 `data/python/advanced-techniques.json`) · 정답 코드 study-practice `python/python-advanced/reference/ctypes-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**ctypes 는 「외국 거래처에 보내는 주문서 양식」이다.**
외국 거래처(C 라이브러리)는 우리말(Python 객체)을 알아듣지 못한다.
그래서 「이 칸은 정수, 이 칸은 문자열의 주소」처럼 칸마다 형식을 정한 양식을 만들고, 그 양식에 맞춰 적어서 보낸다.
답장도 정해 둔 양식대로 받아서 우리말로 옮긴다.
ctypes 도 똑같은 구조다.
`CDLL` 로 거래처를 등록하고, `argtypes` · `restype` 로 양식을 정하고, `c_int` · `c_char_p` 같은 타입으로 칸의 형식을 맞춘다.

> **FFI (Foreign Function Interface)** — 한 언어에서 다른 언어로 만든 함수를 부르는 장치다.\
> 예: Python 코드에서 C 라이브러리의 `strlen` 을 부르는 것.

| 비유 | 실체 |
|---|---|
| 거래처 등록 | `ctypes.CDLL('libc.so.6')` 로 공유 라이브러리를 불러오기 |
| 주문서 양식 | `함수.argtypes` · `함수.restype` |
| 칸의 형식(정수 칸, 주소 칸) | `c_int` · `c_double` · `c_char_p` · `c_void_p` … |
| 규격이 정해진 묶음 상자 | `ctypes.Structure` 와 `_fields_` |
| 「다 되면 이 번호로 전화 주세요」 | `CFUNCTYPE` 으로 만든 콜백 |
| 빈 종이 묶음을 건네고 채워 받기 | `create_string_buffer` · `byref` |

```text
 Python 쪽                    경계(ctypes)                    C 쪽
 ─────────                    ───────────                    ────
  -42 (int)    ──argtypes──▶   c_int  -42      ──호출──▶    abs(int)
                                                               │
  42 (int)     ◀──restype───   c_int  42       ◀──반환──────┘
```

## 이 주제가 답하려는 질문

1. Python 에서 이미 컴파일된 C 라이브러리의 함수를 어떻게 불러오고 부르나?
2. Python 값과 C 타입은 어떻게 짝지어지나 — 정수 · 문자열 · 구조체 · 배열 · 포인터는 각각 무엇으로 나타내나?
3. C 함수가 거꾸로 Python 함수를 부르게(콜백) 하려면 무엇이 필요한가?
4. C 가 다루는 메모리(버퍼)를 Python 에서 직접 만들고 채우려면 어떻게 하나?

## 동작 방식

### (1) 라이브러리 로드 — `CDLL` 과 `find_library`

**언제 쓰나** — C 함수를 부르기 전에 그 함수가 들어 있는 공유 라이브러리 파일을 먼저 불러온다.
라이브러리 이름이 플랫폼마다 다르므로 `sys.platform` 으로 나눠 고른다.

```text
sys.platform == 'linux'   ──▶ CDLL('libc.so.6')
sys.platform == 'darwin'  ──▶ CDLL('libc.dylib')
그 밖(Windows)            ──▶ CDLL('msvcrt')
                                   │
                                   ▼
                     libc 객체 ── libc.abs, libc.strlen … 속성으로 C 함수에 접근

ctypes.util.find_library('c')  ──▶ 이름 'c' 에 해당하는 실제 라이브러리 경로(문자열)
ctypes.util.find_library('m')  ──▶ 수학 라이브러리 libm 의 경로
```

- `CDLL(이름)` 은 공유 라이브러리를 불러와 객체 하나로 돌려준다.
- 돌려받은 객체의 속성(`libc.abs`)이 곧 그 라이브러리 안의 C 함수다.
- `find_library` 는 라이브러리를 불러오지 않고, 짧은 이름으로 실제 파일 경로를 찾아 주기만 한다.
- 원본 주석은 `CDLL` 이 cdecl 호출 규약을 쓴다고 적는다.

> **공유 라이브러리** — 여러 프로그램이 실행 중에 불러다 쓰는 컴파일된 코드 파일이다.\
> 예: 리눅스의 `libc.so.6`, Windows 의 `.dll`.

> **호출 규약** — 함수를 부를 때 인자를 어디에 어떤 차례로 놓고 누가 정리하는지 정한 약속이다.\
> 예: cdecl.

### (2) 함수 시그니처 — `argtypes` 와 `restype`

**언제 쓰나** — C 함수를 부르기 전에, 그 함수가 받는 인자 타입과 돌려주는 타입을 ctypes 에 알려 줄 때 쓴다.
원본 팁은 이것을 **반드시** 설정해야 올바른 타입 변환이 된다고 말한다.

```text
libc.strlen.argtypes = [c_char_p]     ← 「첫 인자는 char* 다」
libc.strlen.restype  = c_size_t       ← 「돌아오는 값은 size_t 다」

libc.strlen(b"Hello, World!")
   b"Hello, World!" ──c_char_p 로 변환──▶ char* ──▶ strlen
   Python int       ◀──c_size_t 에서 변환── size_t 13
```

- `argtypes` 는 인자 타입의 리스트다 — ctypes 가 Python 값을 이 타입으로 바꿔 넘긴다.
- `restype` 은 반환 타입이다 — 지정하지 않으면 `int` 로 가정된다(원본 주석).
- 원본 주석은 설정하지 않으면 ctypes 가 인자를 `c_int` 로 가정해 64bit 환경에서 결과가 틀릴 수 있다고 적는다.
- `c_int` · `c_size_t` · `c_long` 처럼 단순한 타입으로 돌아온 값은 Python `int` 로 바뀌어 손에 들어온다.
- `libc.time` 처럼 인자가 포인터(`POINTER(c_long)`)인 자리에 `None` 을 넘기면 C 의 `NULL` 이 된다.
- `printf` 는 인자 개수가 정해지지 않은 가변 인자 함수라서 `argtypes` 를 다 적기 어렵다 — 원본은 `argtypes` 없이 `libc.printf(b"C printf: %d + %d = %d\n", 3, 4, 7)` 로 부른다.

> **시그니처** — 함수가 받는 인자 타입들과 반환 타입의 묶음이다.\
> 예: `size_t strlen(const char*)`.

> **NULL** — 아무것도 가리키지 않는 포인터 값이다.\
> 예: `libc.time(None)` 의 `None`.

### (3) 타입 매핑 — ctypes 타입과 C 타입

**언제 쓰나** — `argtypes` · `restype` · `_fields_` 에 무엇을 적을지 고를 때 이 짝을 본다.

| ctypes 타입 | C 타입 | 메모 |
|---|---|---|
| `c_bool` | `bool` | |
| `c_char` | `char` | 글자 하나(1바이트) |
| `c_int` | `int` | |
| `c_uint` | `unsigned int` | 비트필드에 쓰인다 |
| `c_long` | `long` | |
| `c_size_t` | `size_t` | `strlen` 의 반환 |
| `c_float` | `float` | |
| `c_double` | `double` | |
| `c_char_p` | `char*` | Python `bytes` 를 넘긴다 |
| `c_void_p` | `void*` | 아무 타입이나 가리키는 주소 |
| `POINTER(T)` | `T*` | 타입이 정해진 포인터 |

```text
for 각 (이름, ctypes 타입, C 이름):
    포인터 타입(c_char_p, c_void_p) 이면 크기 자리에 'ptr'
    아니면 ctypes.sizeof(타입) ──▶ 바이트 수
```

- `ctypes.sizeof(타입)` 은 그 타입이 메모리에서 차지하는 바이트 수를 돌려준다.
- 원본 예제는 포인터 타입 두 개만 크기 대신 `'ptr'` 로 찍는다.
- 원본 주석은 포인터 크기가 시스템에 따라 다르며 보통 8바이트라고 적는다.

### (4) 구조체 — `Structure` 와 `_fields_`

**언제 쓰나** — C 함수가 `struct` 를 받거나 돌려줄 때, 같은 메모리 모양의 Python 클래스를 만든다.

```text
class Point(ctypes.Structure):          C 쪽 대응
    _fields_ = [('x', c_double),        struct Point {
                ('y', c_double)]            double x;
                                            double y;
                                        };
p = Point(3.0, 4.0)        ──▶  메모리:  [ x = 3.0 ][ y = 4.0 ]
p.x, p.y                   ──▶  필드를 속성처럼 읽고 쓴다
ctypes.sizeof(p)           ──▶  double 두 개만큼 (정렬 패딩이 들어갈 수 있음)

class Rect(Structure): _fields_ = [('origin', Point), ('width', c_double), ('height', c_double)]
rect = Rect(Point(0, 0), 10.0, 5.0)
   메모리: [ origin.x ][ origin.y ][ width ][ height ]
```

- `Structure` 를 상속하고 `_fields_` 에 `(이름, 타입)` 튜플을 나열하면 C 의 `struct` 와 같은 메모리 배치가 된다.
- 필드는 **정의한 차례대로** 메모리에 놓이고, 정렬(align) 규칙이 적용된다.
- 생성자에 값을 차례대로 넘기거나(`Point(3.0, 4.0)`) 이름으로 넘긴다(`Flags(readable=1, …)`).
- 다른 `Structure` 를 필드 타입으로 쓰면 중첩 구조체가 된다(`Rect` 의 `origin`).
- 보통의 Python 클래스처럼 `__repr__` 이나 `@property`(`Rect.area`)를 덧붙일 수 있다.
- `c_double` 필드는 실수로 저장되므로 `Point(0, 0)` 의 필드를 읽으면 `0.0` 이다.
- 필드 튜플에 세 번째 값으로 정수를 주면 **비트필드**가 된다 — `('readable', c_uint, 1)` 은 C 의 `unsigned int readable : 1;` 이다.

> **정렬(alignment)** — CPU 가 빨리 읽도록 값을 특정 바이트 배수의 주소에 놓는 규칙이다.\
> 예: 8바이트 `double` 을 8의 배수 주소에 놓기.

> **비트필드** — 구조체 필드를 바이트가 아니라 비트 몇 개 단위로 잡는 것이다.\
> 예: 읽기·쓰기·실행 권한을 1비트씩.

### (5) 배열 — `타입 * N`

**언제 쓰나** — C 함수에 고정 길이 배열을 넘기거나 구조체의 묶음을 만들 때 쓴다.

```text
IntArray10 = ctypes.c_int * 10        ──▶ 「int[10]」이라는 새 타입
arr = IntArray10(*range(10))          ──▶ [0, 1, 2, … , 9] 로 채운 배열 객체
list(arr), sum(arr)                   ──▶ Python 의 반복처럼 다룬다

PointArray = Point * 3                ──▶ 「struct Point[3]」
points = PointArray(Point(0,0), Point(1,1), Point(2,4))
```

- ctypes 타입에 정수를 곱하면 배열 **타입**이 만들어진다 — 아직 값이 아니다.
- 그 타입을 부르면서 초기값을 넘기면 배열 값이 된다.
- 배열은 `list()` · `sum()` · `enumerate()` · 인덱싱으로 다룰 수 있다.
- 사용자 정의 `Structure` 도 같은 방식으로 배열을 만든다.
- 한 줄로 `(ctypes.c_int * 5)(5, 3, 1, 4, 2)` 처럼 타입 만들기와 값 만들기를 붙여 쓸 수도 있다.

### (6) 포인터 — `pointer` 와 `byref`

**언제 쓰나** — C 함수가 주소를 받아 그 자리에 값을 써 주는 「출력 파라미터」를 쓸 때, 또는 주소를 붙들고 역참조할 때 쓴다.

```text
i = c_int(42)          ──▶ C 의 int 변수 하나
p = pointer(i)         ──▶ 정식 포인터 객체(int*)
p.contents.value       ──▶ 42   (역참조해서 값 읽기)

value = c_int(0)
some_func(byref(value))  ──▶ C 가 value 자리에 값을 써 넣는다
value.value              ──▶ C 가 써 준 값
```

- `c_int(42)` 처럼 만든 ctypes 객체는 C 변수처럼 메모리를 가진다 — 값은 `.value` 로 읽는다.
- `pointer(x)` 는 정식 포인터 객체를 만들고, `.contents` 로 가리키는 대상에 닿는다.
- `byref(x)` 는 함수 인자로 넘길 때만 쓰는 가벼운 포인터다.
- 원본 팁: `byref()` 는 `pointer()` 보다 빠르지만 함수 인자 전달에만 쓸 수 있다.
- 원본 예제의 `get_by_ref_example` 은 출력 파라미터의 꼴만 보이고, 실제 C 함수 호출 줄은 주석으로 막혀 있다.

> **출력 파라미터** — 함수가 반환값 대신 인자로 받은 주소에 결과를 써 주는 방식이다.\
> 예: `int` 주소를 넘기면 그 자리에 결과 숫자가 채워진다.

> **역참조** — 포인터가 가리키는 곳의 값에 접근하는 것이다.\
> 예: `p.contents.value`.

### (7) 콜백 — `CFUNCTYPE`

**언제 쓰나** — C 함수가 함수 포인터를 인자로 받을 때(예: `qsort` 의 비교 함수), Python 함수를 그 자리에 넣는다.

```text
CMPFUNC = CFUNCTYPE(c_int, POINTER(c_int), POINTER(c_int))
          └ 반환 ┘  └── 인자 1 ──┘   └── 인자 2 ──┘       ← int (*)(int*, int*) 타입

def py_compare(a, b): return a[0] - b[0]     ← 포인터를 [0] 으로 인덱싱해 값 읽기
cmp_func = CMPFUNC(py_compare)               ← C 가 부를 수 있는 함수 포인터 객체

qsort(arr, 5, sizeof(c_int), cmp_func)
   C qsort ──두 원소의 주소──▶ cmp_func ──▶ py_compare ──음수/0/양수──▶ C qsort
   … 여러 번 되풀이 …
   arr 가 제자리에서 정렬된다:  5 3 1 4 2  ──▶  1 2 3 4 5
```

- `CFUNCTYPE(반환 타입, 인자 타입, …)` 은 C 함수 포인터 **타입**을 만드는 팩토리다 — 첫 인자가 반환 타입이다.
- 그 타입에 Python 함수를 넣어 부르면 C 가 호출할 수 있는 함수 포인터 객체가 된다.
- C 의 `qsort` 는 비교 함수가 음수를 돌려주면 첫 원소를 앞에, 양수면 뒤에 둔다 — `a[0] - b[0]` 은 오름차순이다.
- `qsort` 는 배열을 **제자리에서** 바꾸므로, 호출 뒤 `list(arr)` 를 보면 정렬된 차례가 보인다.
- 원본 주석: 만든 함수 포인터 객체는 GC 되지 않게 변수에 보관해야 한다.
- C 가 아직 그 함수 포인터를 쥐고 있는데 Python 쪽 객체가 사라지면, C 가 사라진 곳을 부르게 된다.

> **콜백** — 내가 부른 함수가 일하는 도중에 거꾸로 불러 주도록 넘겨 둔 함수다.\
> 예: `qsort` 가 두 원소를 비교할 때마다 부르는 `py_compare`.

> **GC (가비지 컬렉션)** — 더 이상 아무도 가리키지 않는 객체의 메모리를 자동으로 거두는 일이다.\
> 예: 변수에 담지 않은 `CMPFUNC(py_compare)` 가 호출 뒤 거둬지는 것.

### (8) 메모리 직접 다루기 — `create_string_buffer` · `memset` · `memmove`

**언제 쓰나** — C 함수가 바이트를 써 넣을 수 있는 버퍼가 필요하거나, 메모리를 직접 채우고 복사할 때 쓴다.

```text
buffer = create_string_buffer(20)        [00 00 00 … 00]          (20바이트, 0으로 채워짐)
memset(buffer, ord('A'), 10)             [A A A A A A A A A A 00 … 00]
buffer.value                             ──▶ 첫 0 바이트 앞까지 = b'AAAAAAAAAA'

src = create_string_buffer(b"Hello!")    [H e l l o ! 00]
len(src.value)                           ──▶ 6   (끝의 0 은 세지 않는다)
memmove(buffer, src, 6)                  [H e l l o ! A A A A 00 … 00]
buffer.value                             ──▶ b'Hello!AAAA'
```

- `create_string_buffer(n)` 은 크기 `n` 의 바꿀 수 있는 `char` 배열을 만든다 — 처음엔 0 바이트로 채워져 있다.
- `create_string_buffer(b"…")` 는 내용을 담고 끝에 0 바이트 하나를 더 둔다.
- `.value` 는 첫 0 바이트 **앞까지**를 `bytes` 로 돌려준다.
- `memset(dst, byte, n)` 은 `dst` 의 앞 `n` 바이트를 `byte` 값으로 채운다 — `ord('A')` 는 `'A'` 의 바이트 값이다.
- `memmove(dst, src, n)` 은 `n` 바이트를 복사하며, 원본 주석대로 영역이 겹쳐도 안전하다.
- 원본 예제는 `len(src.value)` 바이트만 복사하므로 끝의 0 바이트는 넘어가지 않고, 그 뒤에 원래 있던 `A` 가 남는다.

> **버퍼** — 데이터를 잠시 담아 두는 고정 크기 메모리 덩어리다.\
> 예: `create_string_buffer(20)` 이 만든 20바이트.

## 문법 — 형태와 규칙

```python
import ctypes

libc = ctypes.CDLL("libc.so.6")                      # 리눅스 기준

libc.strlen.argtypes = [ctypes.c_char_p]             # 인자 타입
libc.strlen.restype = ctypes.c_size_t                # 반환 타입
n = libc.strlen(b"abc")                              # bytes 를 넘긴다

class Pair(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int), ("b", ctypes.c_int)]

pairs = (Pair * 2)(Pair(1, 2), Pair(3, 4))           # 구조체 배열

out = ctypes.c_int(0)                                # 출력 파라미터 자리
# libc.some_func(ctypes.byref(out))                  # 함수 인자로만 byref

CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)    # int (*)(int)
keep = CB(lambda x: x * 2)                           # 변수에 붙들어 둔다
```

- `CDLL(이름)` → 라이브러리 객체 → `객체.함수이름` 이 C 함수다.
- `함수.argtypes = [타입, …]` · `함수.restype = 타입` 을 **부르기 전에** 정한다.
- C 의 `char*` 자리에는 `bytes`(`b"…"`) 를 넘긴다.
- `class X(ctypes.Structure): _fields_ = [(이름, 타입), …]` — 차례가 곧 메모리 배치다.
- 비트필드는 `(이름, 정수 타입, 비트 수)` 세 값 튜플이다.
- 배열 타입은 `타입 * N`, 배열 값은 `(타입 * N)(값, …)` 이다.
- `pointer(x)` 는 붙들어 두고 `.contents` 로 쓰는 포인터, `byref(x)` 는 함수 인자 전용 포인터다.
- `CFUNCTYPE(반환, 인자1, 인자2, …)` 으로 함수 포인터 타입을 만들고, Python 함수를 넣어 객체를 만든 뒤 변수에 담는다.
- `create_string_buffer(n 또는 bytes)` 로 바꿀 수 있는 `char` 배열을 만들고 `.value` 로 읽는다.

## 어디서 틀리나

### 1. `argtypes` · `restype` 를 빠뜨린다

원본 팁: 반드시 설정해야 올바른 타입 변환이 된다.
`restype` 을 정하지 않으면 반환값은 `int` 로 가정된다(원본 주석).
포인터나 `size_t` 처럼 `int` 보다 넓은 값을 돌려주는 함수라면 값이 잘릴 수 있다.

### 2. `c_char_p` 자리에 `str` 을 넘긴다

원본 팁: `c_char_p` 에는 `bytes` 를 넘긴다(`str` 이 아니다).
C 의 `char*` 는 바이트의 줄이고, Python `str` 은 글자(유니코드)의 줄이라 그대로 옮길 수 없다.
`argtypes` 가 `[c_char_p]` 로 정해진 함수에 `str` 을 넘기면 변환 단계에서 오류가 난다(정확한 예외 이름은 확인 필요).
`"…".encode()` 로 바꾸거나 처음부터 `b"…"` 로 쓴다.

### 3. `byref()` 를 포인터 객체처럼 쓴다

원본 팁: `byref()` 는 `pointer()` 보다 빠르지만 함수 인자 전달에만 쓸 수 있다.
변수에 담아 두고 `.contents` 로 역참조하거나 구조체 필드에 저장하려면 `pointer()` 를 쓴다.

### 4. 콜백 객체를 변수에 붙들지 않는다

원본 주석: `CMPFUNC(py_compare)` 로 만든 객체는 GC 되지 않게 변수에 보관해야 한다.
`libc.qsort(…, CMPFUNC(py_compare))` 처럼 그 자리에서 만들어 넘기면, C 가 그 함수 포인터를 계속 쥐고 있는 경우 Python 쪽 객체가 먼저 사라질 수 있다.
C 가 콜백을 쓰는 동안 내내 살아 있도록 붙들어야 한다.

### 5. 가변 인자 함수(`printf`) — 원본 주석이 의심스럽다

원본은 `printf` 를 `argtypes` 없이 부른다.
원본 주석의 주장: 「ctypes 는 첫 인자만 변환 후 나머지는 그대로 전달」.
의심스러운 까닭: `argtypes` 가 없을 때 ctypes 는 첫 인자만이 아니라 인자마다 기본 규칙(정수 → `int`, `bytes` → `char*`, `None` → `NULL`)으로 변환해 넘기는 것으로 알려져 있다(확인 필요).
「그대로 전달」이라는 말은 Python 객체가 날것으로 C 에 넘어가는 것처럼 읽혀 오해를 부른다.
또 가변 인자 함수의 인자 전달 방식이 고정 인자와 다른 플랫폼이 있어, 이 꼴이 어디서나 안전하다고 단정할 수 없다(확인 필요).

### 6. 비트필드 크기 — 원본 주석이 의심스럽다

원본 주석의 주장: 「비트필드는 1바이트(또는 정렬 단위)에 패킹됨」.
의심스러운 까닭: 필드 타입이 `c_uint` 이므로 비트들은 보통 `unsigned int` 하나 크기의 저장 단위에 담긴다 — 3비트를 써도 구조체 크기가 1바이트로 줄어든다고 보기 어렵다(확인 필요).
비트필드의 배치는 C 컴파일러마다 다를 수 있어, C 쪽과 비트 위치가 같은지 따로 확인해야 한다.

### 7. 라이브러리 이름과 위치는 플랫폼마다 다르다

원본은 `linux` · `darwin` · 그 밖으로 나눠 `libc.so.6` · `libc.dylib` · `msvcrt` 를 고른다.
`find_library` 는 찾지 못하면 경로 대신 `None` 을 돌려줄 수 있다(확인 필요).
원본 주석은 libm 을 「리눅스 한정」 별도 라이브러리라고 적는다 — 다른 플랫폼에서는 수학 함수가 다른 라이브러리에 들어 있을 수 있어 「한정」이라는 표현은 단정하기 어렵다(확인 필요).

### 8. `time` 의 인자를 `POINTER(c_long)` 으로 적었다

C 의 `time` 은 `time_t*` 를 받고 `time_t` 를 돌려준다.
원본은 이것을 `c_long` 으로 적었다.
`time_t` 가 `long` 과 같은 크기라는 보장은 C 표준에 없어, 플랫폼에 따라 맞지 않을 수 있다(확인 필요).

### 9. `qsort` · `memset` · `memmove` 에는 `argtypes` 가 없다

원본 팁은 `argtypes` 를 반드시 설정하라고 하지만, 원본 예제의 `qsort` · `memset` · `memmove` 호출에는 `argtypes` 가 없다.
예컨대 `qsort` 의 둘째 · 셋째 인자는 C 에서 `size_t` 인데, `argtypes` 없이 Python 정수를 넘기면 `int` 로 변환된다(5절의 기본 규칙).
작은 값이라 대개 문제가 드러나지 않겠지만, 팁을 지키려면 이 함수들에도 시그니처를 적는 편이 맞다(원본에 근거 없음 — 추론).

### 10. 규모가 커지면 ctypes 만 고집하지 않는다

원본 팁: 대규모 C 연동에는 cffi 나 Cython 이 더 적합할 수 있다.
ctypes 는 함수마다 `argtypes` · `restype` 와 구조체를 손으로 옮겨 적어야 하므로, 함수가 많아질수록 옮겨 적다 틀릴 자리가 늘어난다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `restype` 을 정하지 않으면 반환이 `int` 로 가정된다 | ctypes 모듈의 정해진 동작(원본 주석). Python 언어 문법이 아니라 라이브러리의 약속이다 |
| `c_long` · 포인터 타입의 바이트 수 | 플랫폼의 C ABI(운영체제 · CPU · 컴파일러). 원본도 「시스템에 따라 다름」이라 적는다 |
| `_fields_` 의 차례대로 배치되고 정렬 규칙이 적용된다 | ctypes 가 플랫폼 C 컴파일러의 구조체 배치 규칙을 따른다. 정렬 패딩의 크기는 플랫폼이 정한다 |
| 비트필드가 어떤 저장 단위에 어떤 차례로 담기나 | C 컴파일러 · 플랫폼마다 다르다(확인 필요). C 표준도 세부를 정하지 않는다 |
| `libc.so.6` · `libc.dylib` · `msvcrt` 라는 이름 | 각 운영체제의 배포 관례. Python 이 보장하지 않는다 |
| `CDLL` 이 cdecl 호출 규약을 쓴다 | ctypes 의 정해진 동작(원본 주석). 플랫폼에 따라 기본 규약이 하나뿐인 경우도 있다(확인 필요) |
| `byref()` 가 `pointer()` 보다 빠르다 | ctypes 구현의 성질(원본 팁). 얼마나 빠른지 수치는 원본에 없다 |
| 콜백 객체가 GC 되면 C 가 사라진 함수를 부를 수 있다 | 참조 계수 · GC 를 쓰는 구현(CPython)의 성질. 언제 거둬지는지는 구현이 정한다 |
| `qsort` 가 비교 결과의 부호로 차례를 정한다 | C 표준 라이브러리의 약속 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 이미 있는 C 라이브러리 함수 몇 개만 부른다 | `CDLL` + `argtypes` · `restype` | 확장 모듈을 새로 빌드하는 무거운 방법 |
| C 함수가 `struct` 를 주고받는다 | `ctypes.Structure` 와 `_fields_` | 바이트를 손으로 이어 붙이기 |
| C 함수가 결과를 인자 주소에 써 준다 | `byref(c_int(0))` 같은 출력 파라미터 | 함수 인자 말고 다른 데서 `byref` 결과를 쓰기 |
| 포인터를 붙들어 두고 나중에 역참조한다 | `pointer()` · `.contents` | `byref()` |
| C 가 비교 · 이벤트 함수를 받는다 | `CFUNCTYPE` + 변수에 보관한 콜백 | 그 자리에서 만들어 버리는 콜백 객체 |
| C 에 문자열을 넘긴다 | `bytes`(`b"…"`) | `str` |
| C 함수 수백 개를 감싸야 한다 | cffi 나 Cython(원본 팁) | 함수마다 손으로 적는 ctypes |

## 핵심 문장

1. **ctypes 는 Python 과 C 사이의 통역이다** — `CDLL` 로 라이브러리를 불러오고, 함수 속성으로 C 함수를 부른다.
2. **통역의 기준은 `argtypes` · `restype` 이다** — 정하지 않으면 `int` 로 가정되므로 부르기 전에 시그니처를 적는다.
3. **C 의 모양은 ctypes 타입으로 옮긴다** — 값은 `c_int` 류, 문자열은 `bytes` 와 `c_char_p`, `struct` 는 `Structure`, 배열은 `타입 * N`.
4. **주소를 넘기는 길은 둘이다** — 붙들어 두는 `pointer()` 와 함수 인자 전용인 가벼운 `byref()`.
5. **C 가 Python 을 부르게 하려면 `CFUNCTYPE` 으로 함수 포인터를 만들고, C 가 쓰는 동안 변수로 붙들어 둔다.**

## 관련 자료

- `memory-optimization` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `profiling` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/advanced-techniques.json` 의 `ctypes-basics`

## 용어 풀이

- **FFI** — 한 언어에서 다른 언어로 만든 함수를 부르는 장치.
- **ctypes** — Python 표준 라이브러리에 든 FFI 모듈.
- **공유 라이브러리** — 실행 중에 여러 프로그램이 불러다 쓰는 컴파일된 코드 파일(`.so` · `.dylib` · `.dll`).
- **DLL** — Windows 의 공유 라이브러리.
- **libc** — C 표준 라이브러리 함수(`abs` · `strlen` · `printf` · `qsort` …)가 든 라이브러리.
- **libm** — 수학 함수(`sin` · `cos` …)가 든 라이브러리.
- **`CDLL`** — 공유 라이브러리를 불러와 함수를 속성으로 꺼내 쓰게 하는 ctypes 클래스.
- **`find_library`** — 짧은 라이브러리 이름으로 실제 파일 경로를 찾는 헬퍼.
- **호출 규약** — 함수를 부를 때 인자를 놓는 자리와 차례, 정리 책임을 정한 약속(cdecl 등).
- **시그니처** — 함수의 인자 타입들과 반환 타입의 묶음.
- **`argtypes`** — C 함수의 인자 타입 리스트.
- **`restype`** — C 함수의 반환 타입.
- **가변 인자 함수** — 인자 개수가 정해지지 않은 함수(`printf`).
- **`sizeof`** — 타입이나 객체가 차지하는 바이트 수.
- **`Structure`** — C 의 `struct` 와 같은 메모리 배치를 만드는 ctypes 기반 클래스.
- **`_fields_`** — `Structure` 의 필드를 `(이름, 타입[, 비트 수])` 로 나열한 리스트.
- **정렬(alignment)** — 값을 특정 바이트 배수 주소에 놓는 규칙. 그 때문에 생기는 빈 바이트가 패딩이다.
- **비트필드** — 비트 몇 개 단위로 잡은 구조체 필드.
- **포인터** — 다른 값이 있는 메모리 주소를 담은 값.
- **`pointer()`** — 정식 포인터 객체를 만드는 함수.
- **`byref()`** — 함수 인자 전달 전용의 가벼운 포인터를 만드는 함수.
- **역참조** — 포인터가 가리키는 곳의 값에 닿는 것(`.contents`).
- **출력 파라미터** — 함수가 인자로 받은 주소에 결과를 써 주는 방식.
- **NULL** — 아무것도 가리키지 않는 포인터 값. ctypes 에서는 `None`.
- **콜백** — 다른 함수에 넘겨 두어 거꾸로 불리는 함수.
- **`CFUNCTYPE`** — C 함수 포인터 타입을 만드는 팩토리.
- **GC** — 쓰이지 않는 객체의 메모리를 자동으로 거두는 일.
- **`qsort`** — 비교 함수를 받아 배열을 제자리에서 정렬하는 C 함수.
- **버퍼** — 데이터를 담는 고정 크기 메모리 덩어리.
- **`create_string_buffer`** — 바꿀 수 있는 `char` 배열을 만드는 함수.
- **`memset`** · **`memmove`** — 메모리를 한 바이트 값으로 채우는 C 함수 · 메모리를 겹쳐도 안전하게 복사하는 C 함수.
- **cffi** · **Cython** — 규모가 큰 C 연동에 쓰이는 다른 도구.

## 더 들어가면

- 64bit Windows 에서는 `c_long` 이 4바이트이고 리눅스 · macOS 64bit 에서는 8바이트로 알려져 있다 — 원본의 `time` 선언이 플랫폼마다 다르게 맞거나 어긋나는 까닭이 된다(확인 필요).
- Windows 의 32bit 시절 API 는 stdcall 규약을 써서 `CDLL` 대신 `WinDLL` 을 썼다(확인 필요).
- `CDLL(이름, use_errno=True)` 와 `ctypes.get_errno()` 로 C 의 `errno` 를 안전하게 읽을 수 있다(확인 필요).
- 원본의 `Flags` 는 `ctypes.sizeof(Flags)` 를 찍어 보면 비트 3개가 아니라 `c_uint` 하나 크기가 나올 것으로 보인다(확인 필요).
- C 의 `printf` 는 C 쪽 표준 출력 버퍼에, Python 의 `print` 는 Python 쪽 버퍼에 쓴다 — 출력이 파이프로 이어질 때 두 출력의 차례가 코드 차례와 달라질 수 있다(확인 필요).
- 콜백 안에서 예외가 나면 C 쪽으로 전파되지 않고 출력만 되고 기본 반환값이 쓰인다는 설명이 있다(확인 필요).
- `ctypes` 객체는 `from_buffer` 로 `bytearray` 같은 Python 버퍼 위에 겹쳐 놓을 수도 있다(확인 필요).
- ctypes 는 내부적으로 libffi 라는 C 라이브러리로 인자를 맞춰 호출한다(확인 필요).
- 원본 예제는 `import struct` 를 하지만 쓰지 않는다 — `struct` 모듈은 바이트 패킹용으로, `Structure` 와는 다른 도구다.
