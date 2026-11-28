# python/python-interview/13 — Python 메모리 관리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 2 → 3 → 6 → 5 → 2 — 이름 · 칸마다 하나씩, 인자분 하나 더

**출력**

```text
  생성 직후:     refcount = 2
  b = a 후:      refcount = 3
  리스트에 3번:  refcount = 6
  del b 후:      refcount = 5
  del c 후:      refcount = 2
```

**왜 그런가**
실제 참조는 `a` 하나로 시작해 `b` 로 하나, 리스트 c 의 칸 셋으로 셋이 늘어 5 가 된다.
화면의 숫자는 `getrefcount` 인자분 1 이 더해진 값이다.
`del b` 는 이름 하나를 지워 1 내린다.
`del c` 는 리스트 c 의 마지막 참조를 끊어 c 를 해제시키고, c 의 칸 셋이 들고 있던 참조도 함께 사라져 3 이 내려간다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 인자로 넘기는 순간 참조가 하나 더 생긴다

`sys.getrefcount(a)` 를 부르면 `a` 가 가리키는 객체가 함수의 인자로 넘어가며 그 동안 참조가 하나 더 생긴다.
그래서 이름 하나뿐인 리스트도 2 로 보인다.
원본의 `- 1` 은 이 인자분 1 을 빼서 「프로그램이 실제로 들고 있는 참조 수」를 보이려는 보정이다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 1」.

### 3. 2 · 2, 그리고 `[GC]` 줄은 `gc.collect()` 안에서 — 반환값 2

**출력**

```text
  A -> B -> A 순환 생성
  A refcount: 2
  B refcount: 2
  del a, b 후에도 순환 참조로 메모리 남아있음

  gc.collect() 호출:
  [GC] Node(A) 해제됨
  [GC] Node(B) 해제됨
  수집된 객체: 2개
```

**왜 그런가**
A 는 이름 `a` 와 B 의 `ref` 속성, B 는 이름 `b` 와 A 의 `ref` 속성이 가리켜 각각 2 다.
`del a, b` 는 이름 둘만 지워 각자 1 이 남고, 0 이 아니라서 참조 카운팅은 해제하지 않는다 — 그래서 `del` 직후에는 `[GC]` 줄이 없다.
`gc.collect()` 가 도달 불가능한 고리를 찾아 두 객체의 `__del__` 을 부르고 해제한 뒤, 수집한 객체 수 2 를 돌려준다.
근거: 2-summary 「동작 방식 (3)」 · 「(4)」.
반환값이 2 인 것은 CPython 구현의 세부다(2-summary 「구현 세부사항 대 언어 보장」).

### 4. 2, 여전히 `Cache(data)`, 그리고 「del strong_ref 후:」 앞에서 해제 → `None`

**출력**

```text
  strong ref: Cache(data)
  weak ref(): Cache(data)
  refcount:   2
  del obj 후:
  strong ref: Cache(data)
  weak ref(): Cache(data)
  Cache(data) 해제
  del strong_ref 후:
  weak ref(): None
```

**왜 그런가**
강한 참조는 `obj` 와 `strong_ref` 둘이고, `weak_ref` 는 세지 않으므로 인자분을 뺀 참조 수는 2 다.
`del obj` 뒤에도 `strong_ref` 가 객체를 붙잡고 있어 `weak_ref()` 는 여전히 객체를 돌려준다.
`del strong_ref` 로 마지막 강한 참조가 끊기는 순간 객체가 해제되며 `__del__` 이 그 자리에서 불린다 — 그래서 「Cache(data) 해제」 가 「del strong_ref 후:」 보다 먼저 찍힌다.
그 뒤의 `weak_ref()` 는 대상이 사라졌으므로 `None` 이다.
근거: 2-summary 「동작 방식 (5)」.

### 5. 순환 없는 객체는 그대로 즉시 해제 · 고리는 다시 켜고 수집할 때까지 남는다

`gc.disable()` 이 멈추는 것은 자동 순환 수집뿐이다.
참조 카운팅은 별개의 장치라, 순환이 없는 객체는 꺼진 동안에도 마지막 참조가 끊기는 순간 해제된다. (원본에 근거 없음 — 추론: 원본은 꺼진 동안 순환 없는 객체를 지우지 않는다)
끈 동안 만든 X ⇄ Y 고리는 아무도 치우지 않고 남아 있다가, `gc.enable()` 뒤 `gc.collect()` 가 돌 때 해제됐다(그때 `[GC] Node(X)`, `[GC] Node(Y)` 가 찍히고 2개가 수집됐다).
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 3」.

### 6. `__del__` 이 불리는 시점을 코드가 통제하지 못한다

`__del__` 은 객체가 어떻게 버려지느냐에 따라 마지막 참조가 끊기는 순간일 수도, 순환에 걸려 `gc` 가 돌 때까지 미뤄질 수도 있다.
언어는 그 시점을 보장하지도 않는다.
그러면 파일 · 연결이 언제 닫힐지 알 수 없고, 고리에 걸린 채 수집이 꺼져 있으면 한참 열려 있을 수도 있다.
`with` 는 블록을 벗어나는 순간 정리가 일어나는 것을 언어가 보장하므로 「지금 반드시 닫혀야 하는」 자원에 맞다.
근거: 2-summary 「어디서 틀리나 4」, 「구현 세부사항 대 언어 보장」.

### 7. 바깥 강한 참조가 다 사라지면 항목도 저절로 빠진다 — 대신 오래 기억하지 못한다

`WeakValueDictionary` 는 값을 약하게 쥐므로, 바깥 강한 참조(`d1`, `d2`)가 모두 사라지면 값 객체가 해제되고 그 키의 항목도 캐시에서 사라진다(크기 1 → 0).
그래서 캐시가 객체를 영원히 붙잡는 누수는 없다.
대가는 아무도 안 쓰는 동안 항목이 곧 빠진다는 것이다 — 잠깐씩 놓이는 값은 다음에 다시 「캐시 미스」 가 나서 새로 만들어진다.
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 6」.

### 8. 자식→부모를 약하게 — 고리가 강한 참조만으로 닫히지 않기 때문이다

부모→자식은 강한 참조로, 자식→부모는 약한 참조로 둔다.
약한 참조는 카운트에 세지 않으므로 강한 참조만 보면 고리가 생기지 않는다.
바깥 이름이 루트를 놓으면 루트의 카운트가 0 이 되어 즉시 해제되고, 루트가 들고 있던 자식 참조가 사라져 자식들의 카운트도 차례로 0 이 된다.
그래서 순환 수집기를 기다리지 않고 참조 카운팅만으로 트리 전체가 치워진다.
근거: 2-summary 「동작 방식 (5)」 끝 두 불릿, 「언제 쓰고 언제 안 쓰나」.

### 9. 모두 CPython 구현의 몫이고, `__del__` 시점은 아무도 보장하지 않는다

세 세대와 `(700, 10, 10)` 은 언어가 아니라 CPython 구현의 설정이며 버전에 따라 달라질 수 있다. (확인 필요)
`getrefcount` 의 숫자와 `gc.collect()` 의 반환값도 CPython 구현의 세부다.
`__del__` 이 불리는 시점은 언어가 보장하지 않고, CPython 에서는 참조 카운트 0 순간이거나 순환 수집 때다.
근거: 2-summary 「구현 세부사항 대 언어 보장」, 「어디서 틀리나 8」.

## 실습 정답

### 실습 1. 참조 카운팅 · 순환 참조 · gc · weakref 를 한 파일로 추적하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 시점의 참조 카운트 | `b = a`, `c = [a, a, a]`, `del b`, `del c` 와 각 줄의 `sys.getrefcount(a)` |
| 2. 즉시 해제와 `__del__` | `Tracked.__del__`, `del t` |
| 3. A ⇄ B 와 보정한 참조 수 | `a.ref = b`, `b.ref = a`, `sys.getrefcount(a) - 1`, `sys.getrefcount(b) - 1` |
| 4. 이름 지우고 수동 수집 | `aid = id(a)`, `bid = id(b)`, `del a, b`, `collected = gc.collect()` |
| 5. gc 상태 조회 | `gc.isenabled()`, `gc.get_threshold()`, `gc.get_count()` |
| 6. 끄고 X ⇄ Y 만들기 | `gc.disable()`, `x.ref = y`, `y.ref = x`, `del x, y` |
| 7. 다시 켜고 수집 | `gc.enable()`, `collected = gc.collect()` |
| 8. 강한 · 약한 참조와 참조 수 | `strong_ref = obj`, `weak_ref = weakref.ref(obj)`, `weak_ref()`, `sys.getrefcount(obj) - 1` |
| 9. 차례로 지우며 보기 | `del obj`, `del strong_ref`, 그 뒤의 `weak_ref()` |
| 10. 약한 값 캐시와 `get_data` | `cache = weakref.WeakValueDictionary()`, `get_data` 의 `if key in cache:` 분기 · `cache[key] = data` |
| 11. 캐시 크기 1 → 0 | `len(cache)`, `del d1, d2`, `gc.collect()` |
| 12. 핵심 정리 다섯 줄 | 끝의 `print("1. …")` ~ `print("5. …")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-interview/reference/memory-management.py`

```python
# [면접 대비 핵심] Python 메모리 관리
# 설명: 참조 카운팅, 순환 참조, gc 모듈로 Python 메모리 관리 메커니즘 확인
# 팁: CPython은 참조 카운팅 + 세대별 GC를 조합한다. 참조 카운트가 0이 되면 즉시 해제되지만, 순환 참조는 GC가 주기적으로 수집한다. 리소스 해제는 __del__보다 컨텍스트 매니저(with문)가 안전하다. weakref로 캐시를 구현하면 메모리 누수를 방지할 수 있다.

"""Python 메모리 관리: 참조 카운팅, 순환 참조, gc"""
# sys: 참조 카운트 조회
import sys
# gc: 가비지 컬렉터 제어
import gc
# weakref: 참조 카운트에 잡히지 않는 약한 참조
import weakref

# === 1. 참조 카운팅 ===
print("=== 1. 참조 카운팅 (sys.getrefcount) ===")

# CPython의 즉시 메모리 해제 메커니즘
a = [1, 2, 3]
# getrefcount는 인자 전달 자체로 카운트 +1되므로 항상 +1된 값이 보임
print(f"  생성 직후:     refcount = {sys.getrefcount(a)}")  # 2 (a + getrefcount 인자)

b = a  # 참조 추가
print(f"  b = a 후:      refcount = {sys.getrefcount(a)}")  # 3

# 리스트가 a를 3번 참조 → 카운트 +3
c = [a, a, a]  # 리스트에서 참조
print(f"  리스트에 3번:  refcount = {sys.getrefcount(a)}")  # 6

# del로 참조 끊기 → 카운트 감소
del b
print(f"  del b 후:      refcount = {sys.getrefcount(a)}")  # 5

del c
print(f"  del c 후:      refcount = {sys.getrefcount(a)}")  # 2 (원래대로)

# === 2. 참조 카운트 0 -> 즉시 해제 ===
print("\n=== 2. 참조 카운트 0 -> 즉시 해제 ===")

# __del__: 객체가 해제될 때 호출되는 finalizer
class Tracked:
    def __init__(self, name):
        self.name = name
        print(f"  생성: {name}")

    def __del__(self):
        print(f"  해제: {self.name}")

print("객체 생성:")
t = Tracked("obj1")
print("del t:")
# 마지막 강한 참조 제거 → 참조 카운트 0 → 즉시 __del__ 호출 (GC 안 거침)
del t  # refcount 0 -> 즉시 __del__ 호출
print("해제 완료\n")

# === 3. 순환 참조: 참조 카운팅으로 해제 불가 ===
print("=== 3. 순환 참조 ===")

class Node:
    def __init__(self, name):
        self.name = name
        self.ref = None

    def __repr__(self):
        return f"Node({self.name})"

    def __del__(self):
        print(f"  [GC] Node({self.name}) 해제됨")

# 순환 참조 생성
# A ↔ B 형태로 서로를 참조 → 변수 삭제해도 카운트가 0이 안 됨
a = Node("A")
b = Node("B")
a.ref = b  # A -> B
b.ref = a  # B -> A (순환!)

print(f"  A -> B -> A 순환 생성")
# -1은 getrefcount의 임시 인자분 보정
print(f"  A refcount: {sys.getrefcount(a) - 1}")  # 2 (a, b.ref)
print(f"  B refcount: {sys.getrefcount(b) - 1}")  # 2 (b, a.ref)

# del해도 refcount가 0이 되지 않음
aid = id(a)
bid = id(b)
# a, b 변수만 사라졌을 뿐 a.ref와 b.ref가 서로 참조 중
del a, b  # refcount 1씩 감소, 하지만 0이 아님
print("  del a, b 후에도 순환 참조로 메모리 남아있음")

# GC가 순환 참조 수집
print("\n  gc.collect() 호출:")
# gc.collect: 도달 불가능한 순환 참조를 찾아 수집
collected = gc.collect()
print(f"  수집된 객체: {collected}개")

# === 4. gc 모듈 활용 ===
print("\n=== 4. gc 모듈 ===")

# gc 상태 확인
print(f"  gc 활성화: {gc.isenabled()}")
# 세대별 GC 임계값 (gen0, gen1, gen2)
print(f"  gc 세대별 임계값: {gc.get_threshold()}")
# 현재 세대별 객체 수
print(f"  gc 세대별 카운트: {gc.get_count()}")

# 수동 gc 제어
# 성능 크리티컬한 구간에서 gc 일시 중지 가능
gc.disable()
print(f"\n  gc 비활성화: {gc.isenabled()}")

# 순환 참조 생성 (gc 없이)
x = Node("X")
y = Node("Y")
x.ref = y
y.ref = x
del x, y
print("  순환 참조 생성 (gc 꺼짐)")

# 다시 활성화 후 수동 collect
gc.enable()
collected = gc.collect()
print(f"  gc 재활성화 후 collect: {collected}개 수집")

# === 5. weakref: 참조 카운트에 영향 없는 참조 ===
print("\n=== 5. weakref ===")

class Cache:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Cache({self.name})"
    def __del__(self):
        print(f"  Cache({self.name}) 해제")

obj = Cache("data")
# 강한 참조: 카운트 증가
strong_ref = obj
# 약한 참조: 카운트에 잡히지 않음 → 객체 생존을 막지 않음
weak_ref = weakref.ref(obj)

print(f"  strong ref: {strong_ref}")
# 약한 참조 호출로 실제 객체 가져오기 (살아있으면 객체, 죽었으면 None)
print(f"  weak ref(): {weak_ref()}")
print(f"  refcount:   {sys.getrefcount(obj) - 1}")  # weak_ref는 카운트에 포함 안 됨

del obj
print(f"  del obj 후:")
# strong_ref가 아직 객체를 참조 → 살아있음
print(f"  strong ref: {strong_ref}")  # 아직 살아있음 (strong_ref가 참조)
print(f"  weak ref(): {weak_ref()}")

del strong_ref
print(f"  del strong_ref 후:")
# 모든 강한 참조 사라짐 → 객체 해제 → 약한 참조는 None 반환
print(f"  weak ref(): {weak_ref()}")  # None (해제됨)

# === 6. WeakValueDictionary: 캐시에 활용 ===
print("\n=== 6. WeakValueDictionary ===")

# 값을 약한 참조로 들고 있는 dict (값이 다른 곳에서 해제되면 자동으로 사라짐)
cache = weakref.WeakValueDictionary()

def get_data(key):
    if key in cache:
        print(f"  캐시 히트: {key}")
        return cache[key]
    print(f"  캐시 미스: {key}")
    data = Cache(key)
    cache[key] = data
    return data

d1 = get_data("user:1")  # 미스
d2 = get_data("user:1")  # 히트
print(f"  캐시 크기: {len(cache)}")

# 강한 참조를 모두 없애면 캐시도 자동으로 비워짐 (메모리 누수 방지)
del d1, d2  # 강한 참조 제거 -> 자동으로 캐시에서도 제거
gc.collect()
print(f"  강한 참조 제거 후 캐시 크기: {len(cache)}")

print("\n=== 핵심 정리 ===")
print("1. CPython 기본: 참조 카운팅 (즉시 해제)")
print("2. 순환 참조: 참조 카운팅으로 해제 불가 -> gc가 처리")
print("3. gc: 3세대 가비지 컬렉터, 주기적으로 순환 참조 수집")
print("4. weakref: 참조 카운트에 영향 없는 참조 (캐시에 유용)")
print("5. __del__은 GC 타이밍에 따라 호출 -> 리소스 해제는 with문 사용")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. 참조 카운팅 (sys.getrefcount) ===
  생성 직후:     refcount = 2
  b = a 후:      refcount = 3
  리스트에 3번:  refcount = 6
  del b 후:      refcount = 5
  del c 후:      refcount = 2

=== 2. 참조 카운트 0 -> 즉시 해제 ===
객체 생성:
  생성: obj1
del t:
  해제: obj1
해제 완료

=== 3. 순환 참조 ===
  A -> B -> A 순환 생성
  A refcount: 2
  B refcount: 2
  del a, b 후에도 순환 참조로 메모리 남아있음

  gc.collect() 호출:
  [GC] Node(A) 해제됨
  [GC] Node(B) 해제됨
  수집된 객체: 2개

=== 4. gc 모듈 ===
  gc 활성화: True
  gc 세대별 임계값: (700, 10, 10)
  gc 세대별 카운트: (4, 0, 0)

  gc 비활성화: False
  순환 참조 생성 (gc 꺼짐)
  [GC] Node(X) 해제됨
  [GC] Node(Y) 해제됨
  gc 재활성화 후 collect: 2개 수집

=== 5. weakref ===
  strong ref: Cache(data)
  weak ref(): Cache(data)
  refcount:   2
  del obj 후:
  strong ref: Cache(data)
  weak ref(): Cache(data)
  Cache(data) 해제
  del strong_ref 후:
  weak ref(): None

=== 6. WeakValueDictionary ===
  캐시 미스: user:1
  캐시 히트: user:1
  캐시 크기: 1
  Cache(user:1) 해제
  강한 참조 제거 후 캐시 크기: 0

=== 핵심 정리 ===
1. CPython 기본: 참조 카운팅 (즉시 해제)
2. 순환 참조: 참조 카운팅으로 해제 불가 -> gc가 처리
3. gc: 3세대 가비지 컬렉터, 주기적으로 순환 참조 수집
4. weakref: 참조 카운트에 영향 없는 참조 (캐시에 유용)
5. __del__은 GC 타이밍에 따라 호출 -> 리소스 해제는 with문 사용
````

**풀이 요점**

- `getrefcount` 는 인자분 1 이 늘 더해져 보이므로, 실제 참조 수가 필요한 자리(3 · 5단계)에는 `- 1` 을 붙인다.
- `del` 은 이름만 지운다 — 2단계에서 즉시 해제가 보이는 것은 `t` 가 유일한 참조였기 때문이다.
- 3 · 4단계의 `[GC]` 줄은 `del` 이 아니라 `gc.collect()` 안에서 나온다 — 고리의 카운트는 0 에 닿지 않는다.
- `gc.disable()` 은 자동 순환 수집만 멈추므로, 꺼진 동안 만든 고리는 다시 켜고 수집할 때 치워진다.
- 약한 참조는 카운트에 세지 않으므로 5단계 참조 수는 강한 참조 둘(`obj`, `strong_ref`)만 센 값이다.
- 6단계 `Cache` 는 순환이 없어 `del d1, d2` 순간 해제되고 캐시 항목도 빠진다 — 뒤의 `gc.collect()` 는 안전장치다. (원본에 근거 없음 — 추론)

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
