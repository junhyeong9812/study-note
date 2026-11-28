# python/python-interview/13 — Python 메모리 관리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 리스트를 이름 · 다른 리스트로 가리킬 때의 refcount (예측)

```python
# 질문용 발췌
a = [1, 2, 3]
print(f"  생성 직후:     refcount = {sys.getrefcount(a)}")
b = a
print(f"  b = a 후:      refcount = {sys.getrefcount(a)}")
c = [a, a, a]
print(f"  리스트에 3번:  refcount = {sys.getrefcount(a)}")
del b
print(f"  del b 후:      refcount = {sys.getrefcount(a)}")
del c
print(f"  del c 후:      refcount = {sys.getrefcount(a)}")
```

- 다섯 줄에 찍히는 숫자는 각각 무엇인가?
- `del c` 한 번에 숫자가 왜 3 이나 내려가나?

### 2. `sys.getrefcount` 가 늘 하나 크게 보이는 까닭 (왜)

- 이름 하나만 가리키는 리스트인데 왜 1 이 아니라 2 가 나오나?
- 원본 코드 곳곳의 `- 1` 은 무엇을 보정하나?

### 3. 서로를 가리키는 두 `Node` 의 이름을 지운 뒤 (예측)

```python
# 질문용 발췌
class Node:
    def __init__(self, name):
        self.name = name
        self.ref = None
    def __del__(self):
        print(f"  [GC] Node({self.name}) 해제됨")

a = Node("A")
b = Node("B")
a.ref = b
b.ref = a
print(f"  A -> B -> A 순환 생성")
print(f"  A refcount: {sys.getrefcount(a) - 1}")
print(f"  B refcount: {sys.getrefcount(b) - 1}")
del a, b
print("  del a, b 후에도 순환 참조로 메모리 남아있음")
print("\n  gc.collect() 호출:")
collected = gc.collect()
print(f"  수집된 객체: {collected}개")
```

- 두 refcount 줄에는 무엇이 찍히나?
- `[GC] … 해제됨` 줄들은 어느 줄과 어느 줄 사이에 찍히나?
- `collected` 에는 몇이 담기나?

### 4. 강한 참조와 약한 참조를 차례로 지울 때 (예측)

```python
# 질문용 발췌
obj = Cache("data")          # __del__ 이 "  Cache(data) 해제" 를 출력한다
strong_ref = obj
weak_ref = weakref.ref(obj)
print(f"  strong ref: {strong_ref}")
print(f"  weak ref(): {weak_ref()}")
print(f"  refcount:   {sys.getrefcount(obj) - 1}")
del obj
print(f"  del obj 후:")
print(f"  strong ref: {strong_ref}")
print(f"  weak ref(): {weak_ref()}")
del strong_ref
print(f"  del strong_ref 후:")
print(f"  weak ref(): {weak_ref()}")
```

- `refcount` 줄의 숫자는 무엇인가?
- `del obj` 뒤의 `weak_ref()` 는 무엇을 돌려주나?
- `Cache(data) 해제` 줄은 어느 줄 바로 앞에 찍히고, 마지막 `weak_ref()` 는 무엇인가?

### 5. `gc.disable()` 이 멈추는 범위 (경계)

- 자동 수집을 끈 동안 순환이 없는 객체의 마지막 참조를 지우면 그 객체는 언제 해제되나?
- 끈 동안 만든 순환 참조는 언제 치워지나?

### 6. 리소스 해제를 `__del__` 보다 `with` 에 맡기는 까닭 (왜)

- 파일 · 연결을 `__del__` 에서 닫으면 무엇이 불확실해지나?

### 7. `WeakValueDictionary` 캐시에서 항목이 사라지는 때 (경계)

- `get_data` 가 돌려준 값을 바깥에서 아무도 들고 있지 않게 되면 캐시 항목은 어떻게 되나?
- 그 성질 때문에 이 캐시가 치르는 대가는 무엇인가?

### 8. 부모↔자식 트리와 약한 참조 (연결)

- 부모가 자식을, 자식이 부모를 가리켜야 하는 트리에서 어느 쪽을 약한 참조로 두나?
- 그렇게 하면 `gc` 없이 참조 카운팅만으로 트리가 치워질 수 있는 까닭은?

### 9. 「3세대」 · `(700, 10, 10)` 같은 숫자의 지위 (경계)

- 세대 수와 임계값은 언어가 정한 값인가?
- `getrefcount` 의 숫자, `gc.collect()` 의 반환값, `__del__` 이 불리는 시점은 각각 누가 정하나?

## 실습

### 실습 1. 참조 카운팅 · 순환 참조 · gc · weakref 를 한 파일로 추적하기

**만들 것** — 참조 카운트의 변화, 즉시 해제, 순환 참조와 수동 수집, `gc` 상태 조회 · 끄고 켜기, 약한 참조, 약한 값 캐시를 차례로 보여 주는 스크립트 한 개.

**요구 조건**

1. 1단계 — 리스트 `a` 를 만들고 `b = a`, `c = [a, a, a]`, `del b`, `del c` 를 차례로 하면서 생성 직후를 포함한 다섯 시점마다 `sys.getrefcount(a)` 를 출력한다.
2. 2단계 — `Tracked` 클래스에 해제 직전 `해제: <이름>` 을 출력하는 `__del__` 을 넣고, 객체 하나를 만든 뒤 `del` 로 지워 「해제 완료」 출력보다 해제 줄이 먼저 나오게 한다.
3. 3단계 — `Node` 둘(A, B)이 `ref` 속성으로 서로를 가리키게 하고, 두 객체의 참조 수를 `getrefcount` 인자분을 뺀 값으로 출력한다.
4. 3단계 — 두 객체의 `id` 를 저장한 뒤 이름 `a`, `b` 를 지우고, `gc.collect()` 로 수동 수집해 그 반환값을 「수집된 객체」로 출력한다.
5. 4단계 — `gc` 가 켜져 있는지, 세대별 임계값, 세대별 카운트를 출력한다.
6. 4단계 — 자동 수집을 끄고 꺼진 상태를 출력한 뒤, `Node` X ⇄ Y 순환을 만들고 두 이름을 지운다.
7. 4단계 — 자동 수집을 다시 켜고 수동 수집해 수집 개수를 출력한다.
8. 5단계 — `Cache` 객체에 강한 참조 `strong_ref` 와 약한 참조 `weak_ref` 를 하나씩 만들고, 두 참조로 본 객체와 참조 수(인자분 제외)를 출력한다.
9. 5단계 — `del obj` 뒤에 두 참조로 본 객체를, `del strong_ref` 뒤에 약한 참조로 본 결과(`None`)를 출력한다.
10. 6단계 — `WeakValueDictionary` 캐시와 `get_data(key)` 를 만든다: 키가 있으면 「캐시 히트」 출력 후 그 값을, 없으면 「캐시 미스」 출력 후 `Cache(key)` 를 만들어 캐시에 넣고 돌려준다.
11. 6단계 — 같은 키로 두 번 불러 캐시 크기를 출력하고, 받은 두 이름을 지우고 `gc.collect()` 를 부른 뒤 캐시 크기를 다시 출력한다.
12. 7단계 — 「핵심 정리」 다섯 줄을 출력한다(시작 코드에 채워져 있다).

**시작 코드**

```python
"""Python 메모리 관리: 참조 카운팅, 순환 참조, gc"""
import sys
import gc
import weakref

# === 1. 참조 카운팅 ===
print("=== 1. 참조 카운팅 (sys.getrefcount) ===")

a = [1, 2, 3]
print(f"  생성 직후:     refcount = {...}")  # TODO: a 의 참조 카운트

# TODO: b 가 a 와 같은 리스트를 가리키게 한다
print(f"  b = a 후:      refcount = {...}")  # TODO

# TODO: a 를 세 번 담은 리스트 c 를 만든다
print(f"  리스트에 3번:  refcount = {...}")  # TODO

# TODO: 이름 b 를 지운다
print(f"  del b 후:      refcount = {...}")  # TODO

# TODO: 이름 c 를 지운다
print(f"  del c 후:      refcount = {...}")  # TODO

# === 2. 참조 카운트 0 -> 즉시 해제 ===
print("\n=== 2. 참조 카운트 0 -> 즉시 해제 ===")

class Tracked:
    def __init__(self, name):
        self.name = name
        print(f"  생성: {name}")

    # TODO: 해제 직전에 "  해제: <name>" 을 출력하는 메서드

print("객체 생성:")
t = Tracked("obj1")
print("del t:")
# TODO: 마지막 강한 참조를 지운다
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

a = Node("A")
b = Node("B")
# TODO: A -> B, B -> A 로 서로 가리키게 한다

print(f"  A -> B -> A 순환 생성")
print(f"  A refcount: {...}")  # TODO: getrefcount 인자분을 뺀 값
print(f"  B refcount: {...}")  # TODO

aid = id(a)
bid = id(b)
# TODO: 이름 a, b 를 지운다
print("  del a, b 후에도 순환 참조로 메모리 남아있음")

print("\n  gc.collect() 호출:")
collected = ...  # TODO: 순환 쓰레기를 수동 수집하고 개수를 받는다
print(f"  수집된 객체: {collected}개")

# === 4. gc 모듈 활용 ===
print("\n=== 4. gc 모듈 ===")

print(f"  gc 활성화: {...}")         # TODO
print(f"  gc 세대별 임계값: {...}")   # TODO
print(f"  gc 세대별 카운트: {...}")   # TODO

# TODO: 자동 수집을 끈다
print(f"\n  gc 비활성화: {...}")      # TODO

x = Node("X")
y = Node("Y")
# TODO: x, y 가 서로 가리키게 하고 두 이름을 지운다
print("  순환 참조 생성 (gc 꺼짐)")

# TODO: 자동 수집을 다시 켠다
collected = ...  # TODO: 수동 수집
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
strong_ref = ...  # TODO: 강한 참조
weak_ref = ...    # TODO: 약한 참조

print(f"  strong ref: {strong_ref}")
print(f"  weak ref(): {...}")  # TODO: 약한 참조로 객체 꺼내기
print(f"  refcount:   {...}")  # TODO: 인자분을 뺀 참조 수

# TODO: obj 를 지운다
print(f"  del obj 후:")
print(f"  strong ref: {strong_ref}")
print(f"  weak ref(): {...}")  # TODO

# TODO: strong_ref 를 지운다
print(f"  del strong_ref 후:")
print(f"  weak ref(): {...}")  # TODO

# === 6. WeakValueDictionary: 캐시에 활용 ===
print("\n=== 6. WeakValueDictionary ===")

cache = ...  # TODO: 값을 약하게 쥐는 dict

def get_data(key):
    # TODO: 있으면 "  캐시 히트: <key>" 출력 후 캐시 값을 돌려준다
    # TODO: 없으면 "  캐시 미스: <key>" 출력, Cache(key) 를 만들어 캐시에 넣고 돌려준다
    ...

d1 = get_data("user:1")
d2 = get_data("user:1")
print(f"  캐시 크기: {...}")  # TODO

# TODO: d1, d2 를 지우고 gc.collect() 를 부른다
print(f"  강한 참조 제거 후 캐시 크기: {...}")  # TODO

print("\n=== 핵심 정리 ===")
print("1. CPython 기본: 참조 카운팅 (즉시 해제)")
print("2. 순환 참조: 참조 카운팅으로 해제 불가 -> gc가 처리")
print("3. gc: 3세대 가비지 컬렉터, 주기적으로 순환 참조 수집")
print("4. weakref: 참조 카운트에 영향 없는 참조 (캐시에 유용)")
print("5. __del__은 GC 타이밍에 따라 호출 -> 리소스 해제는 with문 사용")
```

**확인 방법** — `python memory-management.py` 로 돌려, 1단계 숫자가 다섯 번 오르내리다 처음 값으로 돌아오는지, 「해제: obj1」 이 「해제 완료」 앞에 오는지, `[GC]` 줄이 `gc.collect()` 뒤에야 나오는지, 약한 참조가 마지막에 `None` 이 되는지, 캐시 크기가 1 에서 0 이 되는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
