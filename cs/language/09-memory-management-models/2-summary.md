# language/09-memory-management-models — 메모리 관리 모델: 수동·참조 카운팅·추적 GC·소유권 — 정리 (힌트)

## 해결하는 문제

힙에 만든 객체는 언제 필요 없어지는지 컴파일 시점에 모르는 경우가 많다.

```text
  요청 처리 함수
   order = new Order(...)        ← 힙에 할당
   cache.put(id, order)          ← 다른 곳도 같은 객체를 가리킨다
   return                        ← 함수는 끝났지만 order는 아직 쓰인다
  → "언제 해제해도 되나"를 누군가 정해야 한다
```

- 누가 정하느냐에 따라 틀리는 모양이 다르다.
  - 너무 일찍 해제 → 해제된 자리를 계속 씀(use-after-free).
  - 두 번 해제 → 할당자 자료구조가 깨짐(double free).
  - 영영 해제 안 함 → 누수. 메모리가 계속 오른다.
- *메모리 관리 모델*: "해제 시점을 누가, 어떤 규칙으로 정하나"에 대한 언어·런타임의 답. 이 노트는 네 가지(수동·참조 카운팅·추적 GC·소유권)를 비교한다.

쉬운 예: 도서관 책 반납이다.
- 수동: 빌린 사람이 직접 반납한다. 잊으면 책이 영영 안 돌아오고, 반납한 책을 계속 읽겠다고 우기면 남의 책을 읽게 된다.
- 참조 카운팅: 책마다 "지금 읽는 사람 수"를 적어 두고 0이 되면 서가로 돌린다.
- 추적 GC: 사서가 가끔 돌며 "아직 누가 들고 있나"를 확인해 아무도 없는 책을 회수한다.
- 소유권: 책마다 주인이 한 명뿐이고, 주인이 자리를 뜨면 책이 자동으로 돌아간다. 규칙을 어기는 대출은 접수 단계에서 거부된다.

똑같은 구조다.\
실무 예:
- CPython 서비스에서 서로를 가리키는 객체 쌍이 쌓여 메모리가 오른다. 참조 카운트만으로는 순환이 해제되지 않는다.
- C 서버에서 해제한 구조체 포인터를 다시 읽어, 다른 요청의 데이터가 응답에 섞인다(아래 실험).
- Rust에서 값을 넘긴 뒤 다시 쓰는 코드가 컴파일 오류 `E0382`로 거부된다.

## 동작·원리

### 1. 스택과 힙 — 관리가 필요한 쪽은 힙이다

```text
  스택 (함수 호출마다 프레임)            힙 (수명이 호출과 무관)
  +------------------+
  | main 프레임       |
  |  order ──────────┼──────────────>  [Order 객체 header|amount|...]
  +------------------+                   ^
  | handle 프레임     |                   |
  |  tmp   ──────────┼───────────────────┘
  +------------------+
  함수가 끝나면 프레임은 자동으로 사라진다.   힙 객체는 누가 치우나? ← 이 노트의 질문
```

- 스택 프레임은 호출·반환이 수명을 정한다(호출 규약은 [architecture/10](../../architecture/10-calling-convention-and-stack-frame/2-summary.md)).
- 힙 블록은 할당자(`malloc`·JVM 힙)가 준다. 할당자 내부는 [os/11-heap-allocation](../../os/11-heap-allocation/2-summary.md)·[data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md).
  - *참조(reference)*: 힙 객체를 가리키는 값. 포인터일 수도, 런타임이 관리하는 핸들일 수도 있다. 값과 참조의 기초는 [06-values-references-passing](../06-values-references-passing/2-summary.md)(원고 [foundations/variables-and-memory §1·§4·§5](../../foundations/variables-and-memory/README.md)).

### 2. 네 모델 한눈에

| 모델 | 해제를 정하는 주체 | 해제 시점 | 대표 | 틀리면 |
|---|---|---|---|---|
| 수동 | 프로그래머 (`free`·`delete`) | 코드가 부른 순간 | C, C++(raw 포인터) | use-after-free, double free, 누수 — 실행 중 |
| 참조 카운팅 | 런타임이 객체마다 센 수 | 카운트가 0이 된 순간 | CPython, Rust `Rc`, C++ `shared_ptr` | **순환 누수** |
| 추적 GC | 런타임의 수집기 | 수집기가 돌 때 (지연) | JVM, Go, V8(JS) | 일시정지, "도달 가능한" 누수 |
| 소유권 | 컴파일러 규칙 | 소유자가 스코프를 벗어날 때 | Rust, C++ RAII(`unique_ptr`) | **컴파일 거부**, `Rc` 순환은 여전히 누수 |

- 위 네 칸은 섞여 쓰인다.
  - CPython: 참조 카운팅 + 순환 수집기(gc 모듈). Python 3.12 `gc` 문서: "the collector supplements the reference counting already used in Python".
  - Rust: 기본은 소유권, 공유가 필요하면 `Rc`(참조 카운팅)를 고른다.
- 판단 기준은 "언제 틀린 게 드러나나"다. 수동은 실행 중(그것도 한참 뒤), 소유권은 컴파일 때, 참조 카운팅·추적 GC는 대개 메모리 지표로 드러난다.

### 3. 참조 카운팅 — 0이 되는 순간 해제, 순환은 못 푼다

```text
  a ──> [X rc=1]                 a = None  →  [X rc=0] → 즉시 해제

  순환
  x ──> [A rc=2] ──peer──> [B rc=2] <── y
          ^                    |
          └──────peer──────────┘
  del x, y  →  [A rc=1] <──> [B rc=1]   ← 밖에서 아무도 안 가리키는데 1에서 안 내려간다
```

- *참조 카운트*: 객체마다 "나를 가리키는 참조 수"를 세는 정수. 참조가 생기면 +1, 사라지면 −1, 0이면 해제.
- 장점: 해제가 즉시다. 파일·소켓 같은 자원이 마지막 참조가 사라지는 순간 닫힌다.
- 비용: 참조를 복사·삭제할 때마다 카운트를 고친다. 여러 스레드가 공유하면 이 갱신이 스레드 안전해야 한다. PEP 703은 GIL을 없애려면 "plain non-atomic reference counting"을 바꿔야 한다고 적는다 — 지금까지는 GIL이 이 갱신을 지켜 왔다는 뜻이다([15-gil-and-runtime-constraints](../15-gil-and-runtime-constraints/2-summary.md)).
- 약점: 순환. 위 그림처럼 서로를 가리키면 카운트가 1에서 멈춘다.
  - CPython은 이것을 **순환 수집기**로 따로 찾는다. 세대 3개(0·1·2)는 Python 3.12 `gc` 문서에 있다. 기본 임계값 `(700, 10, 10)`은 문서가 아니라 아래 실험의 `gc.get_threshold()` 출력(3.12.3·3.12.14 둘 다)으로 확인했다.
  - *약한 참조(weak reference)*: 카운트를 올리지 않는 참조. 부모 ↔ 자식처럼 순환이 자연스러운 곳에서 한쪽을 약하게 두어 순환을 끊는다(Python `weakref`, Rust `Weak<T>`).

### 실험 1: 참조 카운트 순환 누수 (CPython 3.12)

```python
class Node:
    def __init__(self, name):
        self.peer = None
        self.payload = bytearray(10_000)   # 10 KB

gc.disable(); tracemalloc.start()
for i in range(1000):
    x, y = Node(f"x{i}"), Node(f"y{i}")
    x.peer, y.peer = y, x          # 순환
    del x, y
# 남은 메모리 확인 → gc.collect() → 다시 확인
```

`python:3.12-slim`(3.12.14), `--cpus=2 --network none`, 2회 실행 + 사실 점검 재실행 2회(모두 같은 값):

```text
  순환 없는 객체: del 직후 해제됐나: ['solo']          ← 카운트 0 → 즉시 해제(weakref.finalize로 확인)
  gc.disable() 상태, 순환 1000쌍 생성·del 후 남은 메모리: 20.4 MB
  gc.collect() 가 찾은 도달 불가 객체 수: 2011
  collect 후 남은 메모리: 0.0 MB
  gc thresholds: (700, 10, 10)
```

- 1000쌍 × 2개 × 10KB ≈ 20MB가 그대로 남았다. 카운트로는 못 푼다는 직접 증거다.
- `gc.collect()`가 도달 불가 객체 2,011개를 찾아 지우자 0으로 돌아왔다. 노드 2,000개 외 11개는 이 실행에서 함께 정리된 다른 객체라는 해석이다(내역은 확인하지 않음). 같은 스크립트를 호스트 Python 3.12.3으로 돌리면 20.4MB → 0.0MB는 같고 반환값은 2,000이었다.
- `gc.disable()`을 안 하면 임계값(700)마다 0세대 수집이 돌아 같은 쌍이 자동으로 회수된다. 순환 수집기를 끄거나, 순환이 수집 주기보다 빨리 쌓이면 메모리가 오른다.

### 4. 추적 GC — 루트에서 닿는가로 판정한다

```text
  루트(스택 지역 변수·static 필드·레지스터)
    │
    ├──> [A] ──> [B]          닿는다 → 산다
    │
    ×    [C] <──> [D]         루트에서 안 닿는다 → 순환이어도 죽는다
```

- *루트(root)*: 수집기가 탐색을 시작하는 참조들. 스레드 스택의 지역 변수, static 필드, JNI 핸들 등.
- *도달 가능성(reachability)*: 루트에서 참조를 따라가 닿으면 산 객체. 그래프 순회 그 자체다(10번에서 mark-sweep·복사·세대로 이어진다).
- 순환은 문제가 아니다. 루트에서 끊기면 순환째 죽는다(아래 실험 2).
- 대신 해제가 즉시가 아니다. 수집기가 돌 때까지 메모리가 남고, 수집 중에 앱을 멈추게 할 수 있다(10·11번).
- "추적 GC면 누수가 없다"는 틀렸다. 루트에서 **닿는데 다시 안 쓰는** 객체(지우지 않는 static 캐시)는 영원히 산다. 진단은 [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md).
  - 흔한 오해: "GC 언어에는 메모리 누수가 없다." GC가 지우는 것은 도달 불가 객체뿐이다. 도달 가능하지만 쓸모없는 객체가 쌓이는 누수는 그대로 생긴다(JVMS §2.5.3은 GC 방식을 정하지 않고 "objects are never explicitly deallocated"만 말한다).

### 실험 2: 같은 순환을 추적 GC는 회수한다 (Java 21)

```java
Node x = new Node(), y = new Node();
x.peer = y; y.peer = x;                         // 순환
WeakReference<Node> wx = new WeakReference<>(x);
x = null; y = null;                             // 루트에서만 끊는다
System.gc(); Thread.sleep(100);
System.out.println(wx.get() != null);
```

`eclipse-temurin:21-jdk`(21.0.12), `--cpus=2`, 기본 수집기:

```text
  루트에서 끊기 전 살아 있나: true
  System.gc() 후 살아 있나: false
```

- 순환이 그대로인데 회수됐다. 판정 기준이 "카운트"가 아니라 "루트에서 닿나"이기 때문이다.
- `System.gc()`는 수집을 "제안"한다(Java API `System.gc`: "suggests that the Java Virtual Machine expend effort", "has made a best effort"). 이 실행에서 회수됐다는 관찰이다.

### 5. 수동 관리 — 해제 후 사용은 실행 중에, 그것도 엉뚱하게 드러난다

```text
  a = malloc(20)  →  [user_001 | 100]
  free(a)         →  [  (빈 칸, free list로)  ]     a는 여전히 그 주소를 들고 있다 (dangling)
  b = malloc(20)  →  같은 크기 → 같은 칸을 재사용할 수 있다 → [user_002 | 999]
  a->user 읽기    →  "user_002"   ← 남의 데이터
```

- *dangling 포인터*: 해제된 메모리를 가리키는 포인터. C 표준상 이것을 통한 접근은 정의되지 않은 동작(UB)이다. C11 §6.2.4p2는 한발 더 나가 객체 수명이 끝나면 포인터 *값* 자체가 "indeterminate"가 된다고 적는다 — 그림의 "주소를 들고 있다"는 이 구현(gcc 13·glibc)에서 비트가 남아 보인 것이지 표준의 보장이 아니다. UB의 의미는 [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md).

### 실험 3: use-after-free와 AddressSanitizer (C)

```c
Account *a = malloc(sizeof *a);
strcpy(a->user, "user_001"); a->balance = 100;
free(a);
Account *b = malloc(sizeof *b);
strcpy(b->user, "user_002"); b->balance = 999;
printf("dangling a->user=%s balance=%d\n", a->user, a->balance);   /* UB */
```

호스트 gcc 13.3.0, glibc malloc:

```text
  gcc -O0 (3회 실행, 모두 같은 결과)
  a=0x5a48cd4952a0 b=0x5a48cd4952a0 same=1
  dangling a->user=user_002 balance=999        ← 크래시 없이 다른 사용자 데이터를 읽었다, exit 0

  gcc -O0 -g -fsanitize=address
  ==ERROR: AddressSanitizer: heap-use-after-free on address ... 
  READ of size 4 at ... thread T0  (uaf.c:12)
  freed by thread T0 here: ... uaf.c:8
  previously allocated by thread T0 here: ... uaf.c:6
  exit=1
```

- 이 컴파일러·옵션·glibc에서 관찰된 결과다. UB이므로 다른 환경에서 다르게 나와도 된다.
- 크래시가 아니라 **조용히 남의 데이터**가 나왔다. "남의 메모리가 응답에 섞인다"는 결과는 Cloudbleed·Heartbleed와 같다. 다만 그 두 사고의 원인은 해제 후 사용이 아니라 버퍼 경계 밖 읽기였다([20](../20-undefined-behavior-and-memory-safety/2-summary.md)·[27](../27-pl-incidents/2-summary.md)).
- `gcc -Wall`은 이 단순한 경우를 컴파일 때 경고했다(`-Wuse-after-free`, `-O0`·`-O2` 둘 다). 포인터가 함수·자료구조를 건너가면 정적 경고가 못 잡는다는 것이 일반적인 한계다.
- ASan 빌드에서는 해제 직후 같은 크기를 다시 할당해도 다른 주소가 나왔다(`a=0x503000000040 b=0x503000000070`, 2회). 해제된 블록에는 접근 금지 표시가 남아, 같은 코드가 "남의 데이터"가 아니라 "해제 후 읽기"로 보고됐다. 해제 블록을 묶어 두는 격리(quarantine) 크기는 google/sanitizers 위키 AddressSanitizerFlags 기준 기본 256MB(iOS·Android 16MB)다. 이 gcc 13 빌드에서 `ASAN_OPTIONS=help=1`은 현재 값을 -1(런타임이 정함)로만 보여 줬다.

### 6. 소유권 — 규칙을 컴파일러가 검사한다

```text
  let x = MyStruct{..};     x ──owns──> [값]
  let y = x;                x (무효)    y ──owns──> [값]     ← 이동(move)
  x.s = 6;                  ✗ 컴파일 오류 E0382: 이동된 값을 사용
  y가 스코프를 벗어남        → drop → 해제 (보통 한 번 — mem::forget·ManuallyDrop이면 생략)
```

- Rust 책 4.1 "Ownership Rules": 값마다 소유자가 있다. 소유자는 한 번에 하나다. 소유자가 스코프를 벗어나면 값이 drop된다.
- 소유자가 하나뿐이니 "누가 해제하나"가 정적으로 정해진다. 안전한(safe) Rust 코드에서는 double free·use-after-free가 컴파일 단계에서 거부된다. `unsafe` 블록 안의 원시 포인터 접근은 이 검사를 받지 않아, 그 안전성은 작성자가 책임진다(Rust 책 20.1 "Unsafe Rust").
- drop은 "보통" 스코프 끝에서 한 번 일어난다. `mem::forget`·`ManuallyDrop`은 소멸자 실행을 막으며, 이것도 safe다(Rust Reference "Not running destructors").
- 공유가 필요하면 *빌림(borrow)*(`&T`·`&mut T`)이나 `Rc<T>`를 쓴다. 빌림 규칙(공유 읽기 여럿 또는 쓰기 하나)은 [languages/rust/언어-특성 §2~4](../../../languages/rust/언어-특성/README.md).
- 한계: `Rc` 순환은 Rust에서도 샌다. Rust 책 15.6: "Preventing memory leaks entirely is not one of Rust's guarantees, meaning memory leaks are memory safe in Rust". 누수는 메모리 안전 위반이 아니다.
- 이 노트의 실험 환경에서는 Rust 컴파일러를 쓰지 않았다(호스트 도구 제한). 오류 `E0382`의 문구와 예제는 Rust 오류 코드 색인에서 확인했다.

### 7. 원고에서 이어받은 것과 바로잡은 것

- 기초(변수 = 이름 + 값 객체, `PyObject`에 참조 수·타입·값, 정수·문자열 인터닝, 상수 폴딩)는 원고 [foundations/variables-and-memory §1·§6](../../foundations/variables-and-memory/README.md)에 있다.
- 참고: 원고 §6의 "파이썬은 레퍼런스 카운팅으로 가비지 컬렉션을 구현한다"는 절반만 맞다. CPython은 참조 카운팅에 **순환 수집기**(gc 모듈)를 더한다(Python 3.12 `gc` 문서, 위 실험 1).
- 참고: 원고 §6의 `sys.getrefcount("abcde")` → `4294967295`는 **CPython 패치 버전에 따라 다르다.** 같은 스크립트가 호스트 Python 3.12.3(Ubuntu)에서는 `4294967295`, `python:3.12-slim`의 3.12.14에서는 `4`를 냈다(사실 점검 재실행에서도 같음). `"a" * 1000`(상수 폴딩)도 3.12.3은 `4294967295`, 3.12.14는 `4`였다. 실행 중 만든 문자열을 `sys.intern()`한 결과도 3.12.3은 `4294967295`, 3.12.14는 `1`이었다. `None`·`True`·작은 정수 `256`은 두 버전 모두 `4294967295`였다.
  - 큰 값은 PEP 683(3.12)의 *불멸 객체(immortal object)* 표시다. 이 객체들은 카운트를 바꾸지 않는다(C API 문서 "Changed in version 3.12: Immortal objects are not modified").
  - Python 3.12 `sys.getrefcount` 문서(와 C API `Py_REFCNT` 문서)는 이 값을 "0이나 1 말고는 정확하다고 믿지 말라"고 적는다.
  - 패치 사이에 달라진 이유: Python 3.12.7 체인지로그 gh-113993 — "Strings interned with sys.intern() are again garbage-collected when no longer used", 인터닝 내부 구조도 바뀌었다. 같은 체인지로그의 Core 항목은 "`PyUnicode_InternInPlace()`로 인터닝한 문자열은 여전히 불멸"이라 적지만, C API 항목과 3.12 C API 문서는 거꾸로 "`PyUnicode_InternInPlace()`는 더 이상 GC를 막지 않는다"·"interned strings are not immortal"이라 적고, `PyUnicode_InternFromString()` 등 `char *`를 받는 함수가 GC를 늦출 수 있다고 적는다(체인지로그 안에서 서로 어긋난다 — C API 문서 쪽을 따른다). 3.12.3은 이 변경 전, 3.12.14는 뒤다. 리터럴 `"abcde"`가 이 변경으로 불멸이 아니게 됐다는 것은 위 관찰과 체인지로그를 이은 해석이다(3.12.4~3.12.13을 하나씩 돌려 보지는 않았다).
- 참고: 원고 §6의 "Stop and Copy는 가장 빠르다고 알려진"은 근거가 없다. 복사 수집은 살아 있는 객체만 옮기므로 비용 구조가 다를 뿐, 어느 수집기가 "가장 빠르다"는 워크로드에 달렸다(10번 실험에서 같은 부하에도 수집기별 순위가 지표마다 갈렸다).

## 쓰이는 자료구조·알고리즘

- **참조 카운트** — 객체 헤더의 정수 하나. 갱신은 참조 복사·삭제마다 O(1), 0이 되면 연쇄 해제(가리키던 객체들의 카운트도 내린다).
- **참조 그래프(유향 그래프)** — 객체 = 정점, 참조 = 간선. 순환 = 그래프의 사이클. 표현은 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **도달성 = 그래프 순회** — 루트 집합에서 BFS/DFS. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)·[algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md). 세부 수집 알고리즘은 [10-garbage-collection](../10-garbage-collection/2-summary.md).
- **소유권 그래프 ≈ 트리** — 단독 소유 값만 보면 값마다 소유자가 하나라 소유 관계는 트리가 된다. `Rc<T>`는 한 할당을 여럿이 공유 소유하게 해(`std::rc` 문서 "shared ownership") 이 부분은 트리가 아니며, 위 한계처럼 순환도 생긴다. 소유자가 사라지면 그 아래 서브트리가 차례로 drop된다. 빌림은 이 트리 위에 수명이 제한된 간선을 잠깐 더하는 것이다.
- **free list·크기별 칸** — 수동 관리·`malloc`의 내부. 같은 크기 요청이 방금 해제한 칸을 받는 것(실험 3)이 여기서 나온다. [os/11](../../os/11-heap-allocation/2-summary.md)·[data-structure/35-allocator](../../data-structure/35-allocator/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 어느 모델의 실패인가

```text
  메모리가 계속 오른다
   ├─ CPython   → 순환? gc가 꺼졌나? / 아니면 도달 가능한 캐시?
   ├─ JVM·Go    → 도달 가능한 누수(static 컬렉션·리스너) → 힙 덤프 (reliability/37)
   └─ C/C++     → free 누락 → ASan의 LeakSanitizer / valgrind
  가끔 엉뚱한 값·크래시 (C/C++)
   └─ use-after-free·double free → ASan으로 재현
  컴파일이 안 된다 (Rust)
   └─ 소유권·빌림 규칙 위반 → 설계를 바꿔야 한다는 신호(복사·빌림·Rc 중 선택)
```

### 2. CPython — 순환인지 확인한다

```python
import gc, tracemalloc
print(gc.isenabled(), gc.get_threshold(), gc.get_count())   # 꺼져 있나, 0세대가 얼마나 쌓였나
n = gc.collect()                    # 도달 불가 객체 수를 돌려준다 (gc 문서)
print("unreachable:", n)
tracemalloc.start(); ...; print(tracemalloc.take_snapshot().statistics("lineno")[:5])  # 어디서 할당했나
```

- `gc.collect()`가 큰 수를 돌려주고 메모리가 크게 내려가면 순환이 유력하다(실험 1의 20.4MB → 0.0MB). 안 내려가면 도달 가능한 누수를 의심한다(전역 리스트·캐시 — 원고 §1의 "메모리 누수 케이스").
  - 이것은 단서다. 전체 수집은 내장 타입의 free list도 비우고(`gc` 문서), 순환 GC를 지원하지 않는 확장 타입의 순환은 수집 뒤에도 남는다. 확정은 `tracemalloc` 스냅샷·`gc.get_referrers()`로 무엇이 무엇을 붙잡는지 보고 한다.
- 부모 ↔ 자식 역참조가 필요하면 한쪽을 `weakref`로 둔다.

### 3. C — 해제 규칙을 도구로 강제한다

```bash
gcc -O0 -g -fsanitize=address,undefined -o app app.c && ./app    # 해제 후 사용·경계 밖 접근 보고
gcc -Wall -Wextra -O2 -c app.c                                   # -Wuse-after-free 등 정적 경고
```

- 해제 직후 포인터를 `NULL`로 두면 그 변수의 재사용이 흔한 플랫폼(Linux 등)에서는 대개 즉시 크래시(null 역참조)로 드러나 "조용한 오염"보다 낫다. 다만 C11 표준상 null 역참조도 UB라(§6.5.3.2 각주 102) 크래시가 보장되지는 않는다. 별칭(같은 블록을 가리키는 다른 포인터)은 이것으로 못 막는다.
- 소유자를 한 곳으로 정하는 관례(만든 함수가 해제, 또는 "소유권을 넘긴다"고 주석)를 둔다. 이것을 컴파일러가 검사하게 만든 것이 소유권 모델이다.

### 4. 모델을 고르는 기준 — "틀렸을 때 어떻게 틀리나"

| 원하는 것 | 맞는 모델 |
|---|---|
| 해제 시점이 예측 가능해야 한다(실시간·자원 핸들) | 소유권·RAII, 참조 카운팅 |
| 그래프 모양 데이터(순환이 자연스러움)를 쉽게 | 추적 GC |
| 실수가 운영 전에 드러나야 한다 | 소유권(컴파일 거부) |
| 일시정지가 없어야 한다 | 수동·소유권(대신 해제 비용이 호출 경로에 섞인다) |

- 언어 선택의 넓은 비교는 [21-language-choice-tradeoffs](../21-language-choice-tradeoffs/2-summary.md).

## 장애 시나리오와 대처

### 1. ⚠ 참조 카운팅 순환 → 메모리가 계단식으로 오른다 (CPython)

- **현상**: 배치 워커의 RSS가 작업마다 조금씩 오르고 내려가지 않는다.
- **보이는 형태**: `tracemalloc` 상위 항목이 특정 클래스 생성 줄. `gc.get_count()`의 0세대 값이 임계값(700)을 크게 넘어 있다면 `gc.disable()`이 호출된 상태일 수 있다(실험 1에서 2604).
- **원인**: 부모 ↔ 자식, 콜백이 자기 객체를 붙잡는 등의 순환. 순환 수집기가 꺼졌거나, 수집 주기보다 빨리 쌓인다.
- **대처**: 순환을 `weakref`로 끊는다. 성능 이유로 `gc.disable()`을 했다면 안전한 지점에서 `gc.collect()`를 주기적으로 부르거나 임계값을 조정한다.

### 2. ⚠ use-after-free → 크래시 대신 다른 요청의 데이터 (C)

- **현상**: 드물게 응답에 다른 사용자 이름이 섞인다. 크래시는 없다.
- **보이는 형태**: 재현이 들쭉날쭉하다. ASan 빌드로 돌리면 `heap-use-after-free`와 해제·할당 위치 스택이 나온다(실험 3).
- **원인**: 해제한 블록을 다른 할당이 재사용했는데, 옛 포인터로 읽었다.
- **대처**: ASan·UBSan을 CI 테스트에 상시로 건다. 소유자를 명확히 하고, 가능한 모듈은 메모리 안전 언어로 옮긴다([20](../20-undefined-behavior-and-memory-safety/2-summary.md), [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md)).

### 3. double free → `free(): double free detected` 후 `SIGABRT`

- **현상**: 프로세스가 exit 134로 죽는다.
- **원인**: 두 곳이 같은 블록을 각자 해제했다. "누가 소유자인가"가 정해지지 않았다.
- **대처**: 세부 모양과 glibc 메시지는 [os/11 장애 2](../../os/11-heap-allocation/2-summary.md). 소유권을 한쪽으로 정하고, 넘긴 쪽은 포인터를 비운다.

### 4. ⚠ 소유권 규칙 위반 → 컴파일 거부 (Rust)

- **현상**: 값을 함수나 다른 변수로 넘긴 뒤 다시 쓰는 코드가 빌드되지 않는다.
- **보이는 형태**: 오류 코드 `E0382`. 오류 색인의 설명은 "A variable was used after its contents have been moved elsewhere"다. 컴파일러가 출력하는 정확한 문구는 이 노트에서 실행으로 확인하지 않았다.
- **원인**: 소유자가 하나라는 규칙. 이동 뒤 원래 변수는 무효다.
- **대처**: 정말 둘이 가져야 하나를 먼저 묻는다. 읽기만 하면 빌림(`&`), 독립 사본이 필요하면 `clone`, 공유 소유가 필요하면 `Rc`/`Arc`. `Rc`로 바꿨다면 순환이 생기는지 다시 본다(장애 1과 같은 모양).

### 5. "GC 언어인데 누수" — 도달 가능한 쓰레기

- **현상**: JVM 힙의 GC 후 바닥선이 계속 오른다.
- **원인**: static 맵·리스너 목록이 객체를 붙잡고 있다. 추적 GC 기준으로는 산 객체다.
- **대처**: 힙 덤프의 지배자 트리로 붙잡는 쪽을 찾는다([reliability/37](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md)). 이 증상이 Full GC 반복으로 번지는 모양은 [10-garbage-collection](../10-garbage-collection/2-summary.md).

## 핵심 문장

- 메모리 관리 모델은 "힙 객체를 언제 해제해도 되나"를 누가 정하느냐의 차이다: 프로그래머, 카운터, 수집기, 컴파일러.
- 참조 카운팅은 0이 되는 순간 해제하지만 순환을 못 푼다. CPython은 그래서 순환 수집기를 따로 둔다.
- 추적 GC는 루트에서 닿는지로 판정해 순환도 회수하지만, 닿는데 안 쓰는 객체는 누수로 남는다.
- 수동 관리의 실수(use-after-free)는 크래시가 아니라 조용히 남의 데이터로 드러날 수 있다. ASan 같은 도구로 실행 중에 잡는다.
- 소유권은 (safe Rust에서) 같은 실수를 컴파일 단계의 거부로 바꾼다. 대신 `Rc` 순환 누수는 Rust에서도 막지 않는다.
- `sys.getrefcount` 같은 내부 값은 구현·패치 버전마다 다르다. 언어가 보장하는 것과 구현이 보여 주는 것을 나눠 읽는다.

## 관련 주제·근거

- 선행
  - [06-values-references-passing](../06-values-references-passing/2-summary.md) — 값·참조(원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md))
  - [os/11-heap-allocation](../../os/11-heap-allocation/2-summary.md) — malloc·free list·단편화·double free
- 후속·연결
  - [10-garbage-collection](../10-garbage-collection/2-summary.md) — 추적 GC 알고리즘(mark-sweep·복사·세대·동시)
  - [11-gc-tuning-and-gc-logs](../11-gc-tuning-and-gc-logs/2-summary.md) · [12-object-layout-and-allocation-reduction](../12-object-layout-and-allocation-reduction/2-summary.md)
  - [15-gil-and-runtime-constraints](../15-gil-and-runtime-constraints/2-summary.md)(참조 카운트와 GIL), [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md), [21-language-choice-tradeoffs](../21-language-choice-tradeoffs/2-summary.md)
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — 공격 관점
  - [reliability/37-memory-leak-and-heap-analysis](../../reliability/37-memory-leak-and-heap-analysis/2-summary.md) — 도달 가능한 누수 진단
  - [languages/rust/언어-특성](../../../languages/rust/언어-특성/README.md) — 소유권·빌림·수명
  - [languages/java/언어-특성 §7~8](../../../languages/java/언어-특성/README.md) — JVM이 GC를 고른 이유
  - [languages/python/syntax/02-is-vs-eq-interning](../../../languages/python/syntax/02-is-vs-eq-interning/) — 인터닝 경계 실측
- 교재
  - Jones·Hosking·Moss 『The Garbage Collection Handbook』 2판 — 1장 Introduction(1.1 Explicit deallocation, 1.2 Automatic dynamic memory management), 5장 Reference counting(5.5 Cyclic reference counting). 장·절 번호는 공식 목차 <https://gchandbook.org/contents.html>에서 확인, 본문은 열지 못했다.
- 문서
  - Python 3.12 `gc` — 순환 수집기가 참조 카운팅을 보충, 세대 3개, `set_threshold`, `collect()` 반환값 <https://docs.python.org/3.12/library/gc.html>
  - Python 3.12 C API "Reference Counting" — 불멸 객체, 반환값을 0·1 외에는 믿지 말 것 <https://docs.python.org/3.12/c-api/refcounting.html>, `sys.getrefcount` <https://docs.python.org/3.12/library/sys.html>
  - Python 3.12 체인지로그 3.12.7 gh-113993(`sys.intern` 문자열이 다시 GC 대상) <https://docs.python.org/3.12/whatsnew/changelog.html>
  - google/sanitizers 위키 AddressSanitizerFlags(`quarantine_size_mb` 기본 256) <https://github.com/google/sanitizers/wiki/AddressSanitizerFlags>
  - PEP 683 "Immortal Objects, Using a Fixed Refcount"(Python 3.12, Final) <https://peps.python.org/pep-0683/>
  - The Rust Programming Language 4.1 "What is Ownership?"(Ownership Rules) <https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html>, 15.6 "Reference Cycles Can Leak Memory" <https://doc.rust-lang.org/book/ch15-06-reference-cycles.html>, 오류 색인 E0382 <https://doc.rust-lang.org/error_codes/E0382.html>
  - JVMS SE21 §2.5.3 Heap <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html>
  - GCC 13 `-Wuse-after-free`, `-fsanitize=address` — 실행으로 확인
- 실험(호스트 i7-13700HX, 컨테이너 `--cpus=2 --network none`)
  - 실험 1: CPython 순환 누수 — `python:3.12-slim`(3.12.14), `gc.disable()` + 순환 1000쌍 → 20.4MB 잔류, `gc.collect()` 2,011개 → 0.0MB(2회 동일)
  - 실험 1 보조: `sys.getrefcount` — 호스트 Python 3.12.3 vs 3.12.14 비교(`"abcde"` 4294967295 vs 4, `sys.intern` 결과 4294967295 vs 1)
  - 실험 2: Java 21 순환 + `WeakReference` — `eclipse-temurin:21-jdk`(21.0.12), `System.gc()` 뒤 회수됨
  - 실험 3: C use-after-free — 호스트 gcc 13.3.0 `-O0`(같은 주소 재사용, 다른 사용자 데이터 읽기, 3회 동일), `-fsanitize=address`(heap-use-after-free, exit 1; 해제 직후 같은 크기 재할당이 다른 주소 0x…040 → 0x…070, 2회), `-Wall`(`-Wuse-after-free` 경고)
