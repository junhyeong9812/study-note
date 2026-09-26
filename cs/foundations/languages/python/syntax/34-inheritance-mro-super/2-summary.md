# python/syntax/34-inheritance-mro-super — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [3.2.10. Custom classes](https://docs.python.org/3.12/reference/datamodel.html#custom-classes) — 조상 탐색이 **C3** 라는 것
> - [`super()`](https://docs.python.org/3.12/library/functions.html#super) — *"The search starts from the class right after the type."* · 인자 없는 꼴의 조건
> - [`type.mro`](https://docs.python.org/3.12/library/stdtypes.html#class.mro) · [`__mro__`](https://docs.python.org/3.12/library/stdtypes.html#class.__mro__) — 순서를 담은 튜플
> - [`object.__init_subclass__`](https://docs.python.org/3.12/reference/datamodel.html#object.__init_subclass__) — **암묵적으로 classmethod** 라는 것
> - [3.3.3.6. Creating the class object](https://docs.python.org/3.12/reference/datamodel.html#creating-the-class-object) — `__set_name__`·`__init_subclass__`·`__class__` 셀이 만들어지는 자리
> - [The Python 2.3 Method Resolution Order](https://docs.python.org/3/howto/mro.html) — **C3 의 정의와 merge 알고리즘**이 여기 적혀 있다
>
> **실행 검증** — 이 문서에 실린 출력은 전부 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.\
> ★ 던지는 형태를 하나로 고정했다 — `python3 - <파일` 로 던져 트레이스백이 `File "<stdin>", line N` 이 된다.\
> ★★ **캐럿은 예외 종류에 달렸다** — 실행 중 예외는 소스 줄도 `^` 캐럿도 안 나오고, `SyntaxError` 라야 둘 다 나온다.
> 이 문서의 트레이스백은 **둘 다 실행 중 예외**라 캐럿이 없다. 하나는 프레임 하나, 하나는 셋이다.\
> ★★★ **두 트레이스백 모두 표준 라이브러리를 안 지난다** — 그래서 절대 경로가 한 곳도 안 박힌다.
> 지났더라면 싣지 않고 타입·메시지만 찍었을 것이다.\
> **버전** — C3 는 **2.3** 부터, 인자 없는 `super()` 는 **3.0** 부터, `__init_subclass__` 는 **3.6**(PEP 487)부터다.
> 이 노트 범위(3.10\~3.13)에서 규칙은 안 바뀌었고, **바이트코드만 3.12 에서 `LOAD_SUPER_ATTR` 로 바뀌었다.**\
> **구현 대 언어 보장 한 줄** — ★★★ **C3 선형화는 언어 보장**이다.
> 문서가 규칙의 이름을 적고 계산법을 하우투로 공개한다. **구현 쪽에 남는 것은 바이트코드 이름과 예외 문구뿐**이다.\
> ★ **흔들리는 칸 / 안 흔들리는 칸** — 재대조에서 「고칠 것」과 「설계상 안 맞는 것」을 기계적으로 가르려고 미리 선언한다.
>
> | 흔들린다 | 안 흔들린다(근거로 써도 되는 칸) |
> |---|---|
> | `dis` 의 **명령 이름과 오프셋** — 판마다 바뀐다(3.12 에서 실제로 바뀌었다) | ★★★ **`__mro__` 의 순서** — C3 는 명세다 |
> | `id()` 와 `0x…` 주소 — **이 주제는 한 번도 안 찍었다** | 예외 **종류** · `File "<stdin>", line N` · `(exit N)` |
> | 판이 오르면 예외 **문구**(MRO 실패 문구의 개행 위치 포함) | **호출 로그의 순서** · 각 클래스가 **몇 번 돌았나** |
> | `dis` 출력의 **줄 번호**(소스에서 몇째 줄인지) | `co_freevars` 에 `__class__` 가 **있나 없나** |
>
> ★ **이 주제의 블록에는 주소도 시간도 절대경로도 한 곳도 안 찍힌다.** 같은 판에서 다시 돌리면 **한 글자도 안 변한다**(재대조 전부 동일).\
> ★★ **`__mro__` 는 순서가 보장된다** — 튜플이고, 그 순서가 곧 C3 의 답이다.
> 이 문서가 순서를 그대로 싣는 근거가 그것이다.\
> **선행** — [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md)(★★★ **`super()` 가 「MRO 다음」이라는 것의 정본**) ·
> [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md)(클래스 칸에 무엇을 앉히나) ·
> [24-decorators](../24-decorators/2-summary.md)(데코레이터가 클래스에도 걸린다).\
> **이 사슬** — [29](../29-classes-and-attribute-lookup/2-summary.md) → [33](../33-property-descriptor-slots/2-summary.md) → 34 → [35번](../35-abc-and-protocol/2-summary.md) .
> **29 가 「칸을 훑는다」였고 33 이 「칸에 무엇을 앉히나」였다면, 34 는 「칸을 훑는 순서가 어떻게 계산되나」다.**

## 한눈에 — 쉽게 말하면

**MRO 는 「조상들을 한 줄로 세운 것」이고, C3 는 그 줄을 세우는 규칙이다.**

줄서기에 비유하면 이렇다.

* 각 클래스는 **자기 줄**(자기 MRO)을 이미 가지고 있다.
* 자식은 **부모들의 줄 + 부모를 적은 순서**를 받아 **한 줄로 합친다.** 이 합치기가 `merge` 다.
* 합칠 때 규칙은 둘뿐이다 — **앞에서부터 후보를 보되, 다른 줄의 「꼬리」에 있는 후보는 아직 못 나간다.**
* 모든 후보가 꼬리에 걸리면 **줄을 못 세운다.** 그때가 `TypeError` 다.

```text
   class Z(K1, K2, K3) 의 줄을 세운다

   받는 줄들                              규칙
   K1 의 줄  : K1 A B C object
   K2 의 줄  : K2 D B E object            ① 왼쪽 줄부터 맨 앞(head)을 후보로 본다
   K3 의 줄  : K3 D A object              ② 그 후보가 어느 줄의 "꼬리" 에도 없으면 뽑는다
   적은 순서 : K1 K2 K3                   ③ 꼬리에 있으면 다음 줄의 head 로 넘어간다

   -> Z K1 K2 K3 D A B C E object

   ★ "꼬리에 있으면 못 나간다" 한 줄이 C3 의 전부다
   ★ 그 덕에 자식이 부모보다 앞이고, 적은 순서가 지켜지고, 공통 조상이 뒤로 간다
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 세워 놓은 한 줄 | MRO | `Cls.__mro__` |
| 줄을 세우는 규칙 | C3 선형화 | `merge` 를 손으로 돌려 `__mro__` 와 견준다 |
| 다른 줄의 꼬리에 걸린 후보 | 아직 못 뽑는 클래스 | merge 로그의 「탈락」 줄 |
| ★ **모든 후보가 걸린 상태** | 선형화 불가 | 정의 시점에 `TypeError` |
| 내 다음 사람 | `super()` | **부모가 아니라 MRO 상 내 다음** |
| 줄을 끝까지 도는 것 | 협력적 다중 상속 | 모두가 `super()` 를 불러야 한다 |
| ★ **한 사람이 넘겨주기를 그만두면** | `super()` 를 안 부른 클래스 | 그 뒤가 통째로 안 돈다. **예외도 경고도 없다** |
| 줄의 맨 끝 | `object` | `Cls.__mro__[-1] is object` |
| 컴파일러가 몰래 쥐여 주는 쪽지 | `__class__` 셀 | `co_freevars` 에 `__class__` 가 있다 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 굳어 있다.\
「**믹스인 순서를 바꿨더니 결과가 뒤집혔다**」와
「**분명히 `super().__init__()` 을 불렀는데 부모 초기화가 안 됐다**」가 그것이다.\
앞엣것은 **줄의 앞뒤**이고, 뒤엣것은 **누군가 넘겨주기를 그만둔 것**이다.

> **MRO(method resolution order)** — 조상을 훑을 순서를 한 줄로 편 것. `Cls.__mro__` 가 그 튜플이다.\
> 예: `D(B, C)`·`B(A)`·`C(A)` 면 `D B C A object`.

> **C3 선형화(C3 linearization)** — MRO 를 만드는 규칙. **못 만드는 순서가 있다.**\
> 예: 두 부모가 같은 조상 둘을 **반대 순서로** 들고 있으면 줄이 안 선다.

> **협력적 다중 상속(cooperative multiple inheritance)** — 모든 참여자가 `super()` 를 불러 줄 전체를 도는 방식.\
> 예: 한 군데만 빼먹어도 그 뒤가 통째로 안 돈다.

### ★★ 이 주제가 쓰는 창 / 부적용인 창

**본체는 「`__mro__` 덤프 + 손계산 대조」 창이다.** 순서를 찍어만 놓으면 외우는 것이 되므로,
**merge 를 직접 돌려 그 결과가 `__mro__` 와 한 글자도 같은지**를 출력으로 보인다.

| 창 | 무엇을 말해 주나 | 못 보는 것 |
|---|---|---|
| ① ★★★ **`__mro__` 덤프 + 손계산 대조** | 줄이 **왜 그 순서인가** | 실제로 무엇이 불리는지 |
| ② ★ **호출 로그와 횟수 계수** | 누가 **몇 번** 돌았나 — 끊긴 자리 | 왜 거기서 끊겼는지 |
| ③ 예외 종류와 문구 | 줄을 **못 세운 자리** | 세웠는데 뜻이 틀린 것 |
| ④ ★ **`dis` 와 `co_freevars`** | 컴파일러가 **무엇을 채웠나** | 실행 시각의 선택 |
| ★ **부적용인 창** — `timeit` 류 속도 측정 | — | **이 문서는 속도를 한 번도 안 쟀다.** MRO 조회 비용은 여기 없다 |

★★ **②가 없으면 ①이 근거가 못 된다.** 순서를 찍는 것과 그 순서대로 실제로 도는 것은 다른 주장이다 —
**`Rude` 처럼 넘겨주기를 그만둔 클래스가 있으면 줄은 그대로인데 뒤가 안 돈다**(동작 4).

★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**
「인자 없는 `super()` 는 무엇으로 되어 있나」를 **문서 문장**으로만 물을 수도 있었지만,
**`dis` 와 `co_freevars` 라는 창**으로 바꿔 물었다(동작 5). 컴파일러가 실제로 채운 것을 눈으로 본다.
★ 바꾼 창이 무엇을 못 보는지도 적는다 — **`dis` 의 명령 이름은 판마다 바뀐다.**
3.12 가 `LOAD_SUPER_ATTR` 로 바꾼 자리가 그것이라, **근거로 쓰는 것은 `co_freevars` 쪽**이다.

먼저 판을 박아 둔다. 이 문서의 모든 출력은 아래 판에서 나왔다.

```python
# e34_version.py
import sys

print("version_info   =", sys.version_info)
print("implementation =", sys.implementation.name)
print("platform       =", sys.platform)
print("object.__mro__ =", [k.__name__ for k in object.__mro__])
```
```text
===== python3 - <e34_version.py =====
version_info   = sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
implementation = cpython
platform       = linux
object.__mro__ = ['object']
(exit 0)
```

★ `object.__mro__` 가 자기 자신 하나뿐이다 — **줄의 끝이 어디인지**가 첫 줄에 이미 있다.

## 이 주제가 답하려는 질문

1. ★★★ **C3 는 어떻게 계산되나** — `__mro__` 를 보고 외우는 것이 아니라 **손으로 세울 수 있나.**
2. ★★ **언제 계산이 실패하나** — 그리고 그 실패 메시지가 C3 의 정의에 대해 무엇을 말하나.
3. **`super()` 는 무엇을 보고 다음을 고르나** — 그리고 **누가 하나라도 빠지면** 무슨 일이 나나.

★ 첫째·둘째가 이 주제의 인출 목표다.
**「꼬리에 있으면 못 나간다」 한 줄로 merge 를 돌릴 수 있는 것**이 아는 것과 들은 것의 경계다.

## 동작 방식

> 이 절이 본문이다. 그림이 먼저 오고 문장이 그 그림을 읽어 준다.

### 1. ★★★ C3 를 손으로 돌려 `__mro__` 와 맞춘다

**언제 쓰나** — 이 주제의 심장. 「왜 저 순서지」가 막힐 때 **외운 규칙 대신 돌릴 수 있는 절차**를 갖는 것.

공식 하우투가 규칙을 적는다 — *"take the head of the first list ...
if this head is not in the tail of any of the other lists, then add it ... otherwise look at the head of the next list."*
꼬리(tail)는 **맨 앞을 뺀 나머지**다.

```text
   손으로 돌리는 절차

   L[C] = C + merge( L[부모1], L[부모2], ..., [부모들을 적은 순서] )

   merge 한 걸음
     ① 남은 줄들을 왼쪽부터 본다. 그 줄의 맨 앞이 후보다
     ② 그 후보가 "어느 줄의 꼬리에도" 없으면 -> 뽑는다. 모든 줄의 맨 앞에서 지운다
     ③ 있으면 -> 다음 줄의 맨 앞을 후보로 삼는다
     ④ 모든 후보가 꼬리에 걸리면 -> 선형화 불가

   ★ merge 의 인자에 "부모를 적은 순서" 가 한 줄 더 들어가는 것을 빠뜨리기 쉽다
     그 줄이 "왼쪽에 적은 것이 먼저" 를 보장한다
```

돌려 볼 계층은 공식 하우투와 같은 모양이다. `A`\~`E` 는 전부 `object` 직속이고,
`K1(A, B, C)`·`K2(D, B, E)`·`K3(D, A)` 위에 `Z(K1, K2, K3)` 를 얹는다.

```python
# e34_c3.py
class A: pass
class B: pass
class C: pass
class D: pass
class E: pass
class K1(A, B, C): pass
class K2(D, B, E): pass
class K3(D, A): pass
class Z(K1, K2, K3): pass


def names(seq):
    return " ".join(k.__name__ for k in seq)


def merge(lists, log):
    """C3 의 merge — 규칙은 두 줄이다.
       ① 남은 리스트들의 맨 앞(head)을 왼쪽부터 본다
       ② 그 head 가 어느 리스트의 「꼬리」에도 없으면 뽑는다. 있으면 다음 후보로 넘어간다"""
    out = []
    lists = [list(x) for x in lists]
    step = 0
    while True:
        lists = [x for x in lists if x]
        if not lists:
            return out
        for cand_list in lists:
            head = cand_list[0]
            in_tail = [x for x in lists if head in x[1:]]
            if in_tail:
                log.append("   후보 %-3s 탈락 — %s 의 꼬리에 있다"
                           % (head.__name__, names(in_tail[0])))
                continue
            step += 1
            log.append("   %d) %-3s 채택 — 어느 꼬리에도 없다" % (step, head.__name__))
            out.append(head)
            for x in lists:
                if x and x[0] is head:
                    del x[0]
            break
        else:
            log.append("   ★ 남은 후보가 전부 꼬리에 걸린다 — 선형화 불가")
            return None


def c3(cls):
    if cls is object:
        return [object]
    log = []
    bases = list(cls.__bases__)
    seq = merge([c3(b) for b in bases] + [bases], log)
    return [cls] + seq


print("① 손으로 계산한다 — Z(K1, K2, K3)")
print("   Z 의 직접 부모        :", names(Z.__bases__))
print("   K1(A,B,C) K2(D,B,E) K3(D,A) 이고 A~E 는 전부 object 직속이다")
print("② merge 가 고른 순서를 한 걸음씩 찍는다")
log = []
bases = list(Z.__bases__)
picked = merge([c3(b) for b in bases] + [bases], log)
for line in log:
    print(line)
print("③ 손계산 결과와 CPython 의 __mro__ 를 견준다")
hand = [Z] + picked
real = list(Z.__mro__)
print("   손계산  :", names(hand))
print("   __mro__ :", names(real))
print("   한 글자도 같은가 :", hand == real)
print("④ C3 의 세 성질을 그 줄에서 확인한다")
idx = {k.__name__: i for i, k in enumerate(real)}
print("   자식이 부모보다 앞인가 (Z<K1<A) :", idx["Z"] < idx["K1"] < idx["A"])
print("   적은 순서가 지켜지나 (K1<K2<K3) :", idx["K1"] < idx["K2"] < idx["K3"])
print("   object 가 맨 끝인가             :", real[-1] is object)
print("   각 클래스가 정확히 한 번씩인가  :", len(real) == len(set(real)))
print("⑤ mro() 는 튜플이 아니라 리스트로 같은 것을 준다")
print("   Z.mro() == list(Z.__mro__) :", Z.mro() == list(Z.__mro__))
```
```text
===== python3 - <e34_c3.py =====
① 손으로 계산한다 — Z(K1, K2, K3)
   Z 의 직접 부모        : K1 K2 K3
   K1(A,B,C) K2(D,B,E) K3(D,A) 이고 A~E 는 전부 object 직속이다
② merge 가 고른 순서를 한 걸음씩 찍는다
   1) K1  채택 — 어느 꼬리에도 없다
   후보 A   탈락 — K3 D A object 의 꼬리에 있다
   2) K2  채택 — 어느 꼬리에도 없다
   후보 A   탈락 — K3 D A object 의 꼬리에 있다
   후보 D   탈락 — K3 D A object 의 꼬리에 있다
   3) K3  채택 — 어느 꼬리에도 없다
   후보 A   탈락 — D A object 의 꼬리에 있다
   4) D   채택 — 어느 꼬리에도 없다
   5) A   채택 — 어느 꼬리에도 없다
   6) B   채택 — 어느 꼬리에도 없다
   7) C   채택 — 어느 꼬리에도 없다
   후보 object 탈락 — E object 의 꼬리에 있다
   8) E   채택 — 어느 꼬리에도 없다
   9) object 채택 — 어느 꼬리에도 없다
③ 손계산 결과와 CPython 의 __mro__ 를 견준다
   손계산  : Z K1 K2 K3 D A B C E object
   __mro__ : Z K1 K2 K3 D A B C E object
   한 글자도 같은가 : True
④ C3 의 세 성질을 그 줄에서 확인한다
   자식이 부모보다 앞인가 (Z<K1<A) : True
   적은 순서가 지켜지나 (K1<K2<K3) : True
   object 가 맨 끝인가             : True
   각 클래스가 정확히 한 번씩인가  : True
⑤ mro() 는 튜플이 아니라 리스트로 같은 것을 준다
   Z.mro() == list(Z.__mro__) : True
(exit 0)
```

그림 해설 — 다섯 덩어리가 「손계산」에서 「보장」까지 간다.

* ★★★ **②가 이 절의 본체다.** 아홉 번의 채택과 네 번의 탈락이 **한 줄씩 이유를 달고** 찍혔다.
  ★ 첫 탈락 줄이 규칙을 그대로 말한다 — `후보 A 탈락 — K3 D A object 의 꼬리에 있다`.
  `A` 가 `K3` 의 줄에서 **맨 앞이 아니므로** 아직 못 나간다.
* ★★ **가장 얄궂은 탈락은 마지막 것**이다 — `후보 object 탈락 — E object 의 꼬리에 있다`.
  `object` 는 **모든 줄의 꼬리에 있으므로** 다른 후보가 하나라도 남아 있는 한 못 나간다.
  ★ **`object` 가 항상 맨 끝인 것이 특례가 아니라 이 규칙의 결과**라는 것이 여기서 드러난다.
* ★ **③이 대조다.** 손계산이 `Z K1 K2 K3 D A B C E object` 이고 `__mro__` 도 같다 — **한 글자도 같다.**
  ★ 이 줄이 있어야 ②가 「내가 만든 이야기」가 아니라 **언어가 실제로 하는 일**이 된다.
* **④가 C3 의 성질 넷을 그 줄 위에서 확인한다** — 자식이 부모보다 앞 · 적은 순서 유지 ·
  `object` 맨 끝 · **각 클래스가 정확히 한 번씩**.
  ★ 마지막 것이 다이아몬드를 다루는 핵심이다(동작 3).
* **⑤ — `mro()` 는 메서드, `__mro__` 는 튜플**이고 같은 것을 준다.

★★ 그래서 이 절의 한 줄은 이렇다 — **MRO 는 외우는 표가 아니라 두 줄짜리 규칙으로 돌리는 계산이다.**

**비용** — C3 는 **클래스를 만들 때 한 번** 계산해 튜플로 박아 둔다. 조회할 때마다 다시 풀지 않는다.
★ **그 비용이 얼마인지는 이 문서가 안 쟀다** — 속도 창을 열지 않았다.

### 2. ★★ 줄을 못 세우는 상속 — 그 에러가 C3 의 정의를 말한다

**언제 쓰나** — 「이 상속이 왜 안 되지」가 날 때. 그리고 **C3 가 무엇을 지키려 하는지** 알고 싶을 때.

[29번](../29-classes-and-attribute-lookup/2-summary.md)이 **가장 쉬운 실패**(부모를 자식보다 먼저 적는 것)를 실측했다.
여기서는 **더 흔하고 더 안 보이는 실패**를 던진다 — **두 부모가 같은 조상 둘을 반대 순서로 들고 있는 것.**

```text
   class X(A, B)  ->  X 의 줄 : X A B object     A 가 B 보다 앞이다
   class Y(B, A)  ->  Y 의 줄 : Y B A object     B 가 A 보다 앞이다

   class Z(X, Y) 를 만들려면 두 줄을 합쳐야 한다

     A 를 뽑으려면?  ->  Y 의 줄(Y B A object)의 꼬리에 A 가 있다. 못 뽑는다
     B 를 뽑으려면?  ->  X 의 줄(X A B object)의 꼬리에 B 가 있다. 못 뽑는다

   ★ 모든 후보가 꼬리에 걸렸다 -> 줄을 못 세운다 -> 정의 시점에 TypeError

   ★ X 도 Y 도 각각은 멀쩡하다. 합칠 때만 모순이 된다
```

```python
# e34_mro_fail.py
class A: pass
class B: pass


class X(A, B):     # A 다음 B 라고 적었다
    pass


class Y(B, A):     # 여기서는 B 다음 A 라고 적었다
    pass


print("X 의 MRO :", [k.__name__ for k in X.__mro__])
print("Y 의 MRO :", [k.__name__ for k in Y.__mro__])
print("둘을 한꺼번에 물려받는다 — A 와 B 의 앞뒤가 모순이다")


class Z(X, Y):
    pass
```
```text
===== python3 - <e34_mro_fail.py =====
X 의 MRO : ['X', 'A', 'B', 'object']
Y 의 MRO : ['Y', 'B', 'A', 'object']
둘을 한꺼번에 물려받는다 — A 와 B 의 앞뒤가 모순이다
Traceback (most recent call last):
  File "<stdin>", line 18, in <module>
TypeError: Cannot create a consistent method resolution
order (MRO) for bases A, B
(exit 1)
```

그림 해설.

* ★★ **`X` 와 `Y` 는 각각 멀쩡하다.** 둘의 `__mro__` 가 먼저 찍혔다.
  **모순은 두 줄을 합칠 때만 생긴다** — 그래서 코드를 따로 읽으면 안 보인다.
* ★★★ **에러 문구가 C3 의 정의를 그대로 말한다** —
  `Cannot create a consistent method resolution order (MRO) for bases A, B`.
  ★ **「일관된(consistent)」** 이 낱말이 핵심이다. C3 가 지키려는 것은 「**어느 부모의 줄에서도 앞뒤가 안 뒤집힌다**」이고,
  그것이 불가능하면 **아무 줄이나 세우지 않고 거부한다.**
  ★ 그리고 **어느 둘이 다퉜는지**(`for bases A, B`)까지 알려 준다.
* ★ **문구 안에 개행이 박혀 두 줄로 나온다** — `resolution` 다음에 줄이 갈린다.
  출력을 접은 것이 아니라 **메시지 자체에 `\n` 이 들어 있다.** 그대로 실었다([29번](../29-classes-and-attribute-lookup/2-summary.md)도 같은 관찰).
* ★ **실행 중 예외라 소스 줄도 캐럿도 없다.** 프레임이 **하나뿐**이고 그것이 `<module>` 이다 —
  `class Z(X, Y):` 문을 실행하다 난 것이다. **인스턴스를 만들지도 않았다.**
* ★ 그래서 **정의 시점에 터진다**는 것이 이 장치의 값이다.
  [32번](../32-container-protocol/2-summary.md)이 실측한 ABC 의 「만들 때 막는다」보다 **한 단계 더 앞**이다.

**비용** — 공짜로 앞당겨 터진다. 대가는 **고치기 어렵다는 것** —
두 부모가 남의 코드면 순서를 바꿀 방법이 없어 **구조를 바꿔야** 한다.

### 3. ★★ 다이아몬드 — 각 클래스가 정확히 한 번씩 돈다

**언제 쓰나** — 「부모 초기화가 두 번 도는 것 같다」가 날 때. 그리고 `super()` 가 **왜** 필요한지 볼 때.

```text
   다이아몬드                     Both() 를 부르면

        Base                      Both.go  -> 내 다음(Left)
        /  \                      Left.go  -> 내 다음(Right)   <- ★ 부모가 아니라 형제다
     Left   Right                 Right.go -> 내 다음(Base)
        \  /                      Base.go  -> 끝
        Both
                                  ★ Base 가 한 번만 돈다

   만약 super() 대신 Base.go(self) 를 직접 적었다면
        Left.go  -> Base.go
        Right.go -> Base.go        <- Base 가 두 번 돈다
```

```python
# e34_diamond.py
COUNT = {}


class Base:
    def go(self, depth):
        COUNT["Base"] = COUNT.get("Base", 0) + 1
        print("   " + "  " * depth + "Base.go   — super() 를 안 부른다 (여기가 끝)")


class Left(Base):
    def go(self, depth):
        COUNT["Left"] = COUNT.get("Left", 0) + 1
        print("   " + "  " * depth + "Left.go   -> 내 다음에게 넘긴다")
        super().go(depth + 1)


class Right(Base):
    def go(self, depth):
        COUNT["Right"] = COUNT.get("Right", 0) + 1
        print("   " + "  " * depth + "Right.go  -> 내 다음에게 넘긴다")
        super().go(depth + 1)


class Both(Left, Right):
    def go(self, depth=0):
        COUNT["Both"] = COUNT.get("Both", 0) + 1
        print("   " + "  " * depth + "Both.go   -> 내 다음에게 넘긴다")
        super().go(depth + 1)


print("① MRO 한 줄")
print("   ", " -> ".join(k.__name__ for k in Both.__mro__))
print("② Both().go() 가 지나간 길")
Both().go()
print("③ 몇 번씩 돌았나 — 다이아몬드인데 Base 가 한 번이다")
for nm in ("Both", "Left", "Right", "Base"):
    print("   %-6s : %d 번" % (nm, COUNT.get(nm, 0)))
print("④ 같은 Left.go 안의 같은 super() 가 어디로 가나")
print("   Left() 에서 Left 의 다음  :", Left.__mro__[Left.__mro__.index(Left) + 1].__name__)
print("   Both() 에서 Left 의 다음  :", Both.__mro__[Both.__mro__.index(Left) + 1].__name__)
print("   ★ Right 는 Left 의 부모가 아니라 형제다 :",
      "Right" in [k.__name__ for k in Left.__bases__])
```
```text
===== python3 - <e34_diamond.py =====
① MRO 한 줄
    Both -> Left -> Right -> Base -> object
② Both().go() 가 지나간 길
   Both.go   -> 내 다음에게 넘긴다
     Left.go   -> 내 다음에게 넘긴다
       Right.go  -> 내 다음에게 넘긴다
         Base.go   — super() 를 안 부른다 (여기가 끝)
③ 몇 번씩 돌았나 — 다이아몬드인데 Base 가 한 번이다
   Both   : 1 번
   Left   : 1 번
   Right  : 1 번
   Base   : 1 번
④ 같은 Left.go 안의 같은 super() 가 어디로 가나
   Left() 에서 Left 의 다음  : Base
   Both() 에서 Left 의 다음  : Right
   ★ Right 는 Left 의 부모가 아니라 형제다 : False
(exit 0)
```

그림 해설 — 네 덩어리가 「한 번씩」을 수치로 못 박는다.

* ★ **②의 들여쓰기가 사슬의 깊이**다. 네 단계가 한 번씩 내려간다.
* ★★★ **③이 이 절의 과녁이다.** 계수기가 **넷 다 `1 번`** 이라고 답한다.
  ★ **`Base` 가 두 갈래로 이어져 있는데도 한 번**이다 — C3 가 `Base` 를 줄의 **한 자리**에만 놓았기 때문이다.
  ★ 「한 번만 돈다」를 산문으로 적지 않고 **계수로 찍은 것**이 이 블록의 값이다.
* ★★ **④가 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 결론을 다시 건다.**
  같은 `Left.go` 안의 같은 `super()` 한 줄인데,
  `Left()` 에서는 다음이 `Base` 이고 `Both()` 에서는 `Right` 다.
  ★ 그리고 **`Right` 는 `Left` 의 부모가 아니다**(`Left.__bases__` 에 없다 — 출력이 `False`).
  **형제로 간다.**
* ★ 그래서 `super()` 의 정확한 뜻은 「**그 인스턴스의 타입의 MRO 에서 내 다음**」이다.
  문서가 그렇게 적는다 — *"The search starts from the class right after the type."*

**비용** — 다이아몬드를 안전하게 도는 값으로 **모두가 같은 서명을 지켜야** 한다.
`super().go(depth + 1)` 처럼 인자가 있으면 **줄 전체가 그 인자를 받아야** 한다.

### 4. ★★★ 사슬이 끊기는 것 — 예외도 경고도 없다

**언제 쓰나** — 「분명히 `super()` 를 불렀는데 부모가 안 돈다」가 날 때. **이 주제에서 가장 조용한 자리다.**

```text
   Chain(Polite, Rude) 의 줄 : Chain Polite Rude Base object

   Chain.go  -> super()  -> Polite.go
   Polite.go -> super()  -> Rude.go
   Rude.go   -> ★ super() 를 안 부른다
                              Base.go 가 "영영 안 불린다"

   ★ 줄은 멀쩡히 서 있다. Base 는 줄에 있는데 아무도 안 부른 것이다
   ★ 순서만 뒤집으면 끊긴 자리가 앞으로 옮겨 가 Polite 까지 같이 사라진다
```

```python
# e34_break.py
class Base:
    def go(self):
        print("      Base.go     — 끝")


class Polite(Base):
    def go(self):
        print("      Polite.go   -> super()")
        super().go()


class Rude(Base):
    def go(self):
        print("      Rude.go     — ★ super() 를 안 부른다")


class Chain(Polite, Rude):
    def go(self):
        print("      Chain.go    -> super()")
        super().go()


class Chain2(Rude, Polite):
    def go(self):
        print("      Chain2.go   -> super()")
        super().go()


print("① Chain(Polite, Rude) — MRO")
print("   ", " -> ".join(k.__name__ for k in Chain.__mro__))
print("   Chain().go() 가 지나간 길")
Chain().go()
print("   ★ Base.go 가 안 찍혔다. Rude 가 사슬을 끊었다")
print("② 순서만 뒤집으면 — Chain2(Rude, Polite)")
print("   ", " -> ".join(k.__name__ for k in Chain2.__mro__))
print("   Chain2().go() 가 지나간 길")
Chain2().go()
print("   ★ Polite 도 Base 도 아예 안 불렸다. 끊긴 자리가 앞으로 옮겨 갔을 뿐이다")
print("③ 예외도 경고도 없다 — 돌아온 값으로도 못 가른다")
print("   Chain().go()  가 돌려준 것 :", Chain().go())
print("   Chain2().go() 가 돌려준 것 :", Chain2().go())
```
```text
===== python3 - <e34_break.py =====
① Chain(Polite, Rude) — MRO
    Chain -> Polite -> Rude -> Base -> object
   Chain().go() 가 지나간 길
      Chain.go    -> super()
      Polite.go   -> super()
      Rude.go     — ★ super() 를 안 부른다
   ★ Base.go 가 안 찍혔다. Rude 가 사슬을 끊었다
② 순서만 뒤집으면 — Chain2(Rude, Polite)
    Chain2 -> Rude -> Polite -> Base -> object
   Chain2().go() 가 지나간 길
      Chain2.go   -> super()
      Rude.go     — ★ super() 를 안 부른다
   ★ Polite 도 Base 도 아예 안 불렸다. 끊긴 자리가 앞으로 옮겨 갔을 뿐이다
③ 예외도 경고도 없다 — 돌아온 값으로도 못 가른다
      Chain.go    -> super()
      Polite.go   -> super()
      Rude.go     — ★ super() 를 안 부른다
   Chain().go()  가 돌려준 것 : None
      Chain2.go   -> super()
      Rude.go     — ★ super() 를 안 부른다
   Chain2().go() 가 돌려준 것 : None
(exit 0)
```

그림 해설 — 세 덩어리가 「조용하다」를 세 가지 방법으로 보인다.

* ★★ **①에서 `Base.go` 가 안 찍혔다.** `Rude` 가 넘겨주기를 그만뒀기 때문이다.
  ★ **`__mro__` 에는 `Base` 가 버젓이 있다** — 첫 줄이 그것을 먼저 찍는다.
  **줄이 틀린 것이 아니라 줄을 끝까지 안 돈 것**이다. 창 ①만 보면 안 보이고 창 ②라야 보인다.
* ★★ **②가 더 나쁘다.** 순서만 뒤집으니 `Polite` 까지 통째로 사라졌다.
  **끊긴 자리가 앞으로 옮겨 갔을 뿐**인데 안 도는 클래스가 하나 더 늘었다.
  ★ 실무의 증상이 이것이다 — 「믹스인을 다른 순서로 적었더니 초기화가 하나 빠졌다」.
* ★★★ **③이 이 절의 과녁이다.** 두 경우 모두 **돌려준 값이 `None`** 이다.
  **예외도 경고도 없고 반환값으로도 못 가른다.**
  ★ [32번](../32-container-protocol/2-summary.md)의 ABC 가 「만들 때 막는」 장치였다면,
  여기는 **아무도 안 막는** 자리다.

★★ 그래서 판정 한 줄 — **협력 사슬의 정확성은 언어가 안 봐 준다. 모든 참여자가 `super()` 를 부르는지는 사람이 지켜야 한다.**
★ 진단은 **계수 로그**다(동작 3의 ③). 「몇 번 돌았나」를 찍어야 「안 돈 것」이 드러난다.

**비용** — 조용하므로 **테스트가 통과한 채로 틀린다.**
`Base.__init__` 이 필드를 채우는 코드였다면 **그 필드가 없는 객체**가 살아 돌아다닌다.

### 5. ★ 인자 없는 `super()` — 컴파일러가 `__class__` 셀을 채운다

**언제 쓰나** — 「`super()` 가 인자 없이 어떻게 자기 클래스를 아나」가 궁금할 때.
그리고 **중첩 함수 안에서 `super()` 가 터질 때.**

문서가 조건을 적는다 — 인자 없는 꼴은
*"the compiler fills in the necessary details to correctly retrieve the class being defined,
as well as accessing the current instance for ordinary methods."*

```text
   def zero_arg(self):          def two_arg(self):
       return super().go()          return super(C, self).go()

   컴파일러가 하는 일                 내가 하는 일

   __class__ 라는 자유변수 셀을 만들고   C 라는 "이름" 을 전역에서 찾는다
   거기에 C 를 넣어 둔다                 -> C 를 나중에 다른 것에 다시 묶으면 따라간다
   -> LOAD_DEREF __class__

   ★ 그래서 인자 없는 꼴은 "정의된 그 클래스" 를 확실히 잡는다
   ★ 대신 셀이 없는 자리(중첩 함수)에서는 못 쓴다
```

```python
# e34_superdis.py
import dis


class P:
    def go(self):
        return "P.go"


class C(P):
    def zero_arg(self):
        return super().go()

    def two_arg(self):
        return super(C, self).go()

    def no_super(self):
        return "super 를 안 쓴다"


print("① 두 꼴이 같은 답을 준다")
c = C()
print("   zero_arg ->", c.zero_arg())
print("   two_arg  ->", c.two_arg())
print("② 컴파일러가 채워 주는 것 — __class__ 셀")
for nm in ("zero_arg", "two_arg", "no_super"):
    fn = getattr(C, nm)
    print("   %-9s co_freevars : %s" % (nm, fn.__code__.co_freevars))
print("   ★ super 라는 이름이 몸통에 있으면 __class__ 셀이 생긴다")
print("③ dis 로 본 zero_arg")
dis.dis(C.zero_arg)
print("④ dis 로 본 two_arg")
dis.dis(C.two_arg)
print("⑤ 셀에 실제로 무엇이 들어 있나")
cell = C.zero_arg.__closure__[0]
print("   C.zero_arg.__closure__[0].cell_contents is C :", cell.cell_contents is C)
```
```text
===== python3 - <e34_superdis.py =====
① 두 꼴이 같은 답을 준다
   zero_arg -> P.go
   two_arg  -> P.go
② 컴파일러가 채워 주는 것 — __class__ 셀
   zero_arg  co_freevars : ('__class__',)
   two_arg   co_freevars : ('__class__',)
   no_super  co_freevars : ()
   ★ super 라는 이름이 몸통에 있으면 __class__ 셀이 생긴다
③ dis 로 본 zero_arg
              0 COPY_FREE_VARS           1

 10           2 RESUME                   0

 11           4 LOAD_GLOBAL              0 (super)
             14 LOAD_DEREF               1 (__class__)
             16 LOAD_FAST                0 (self)
             18 LOAD_SUPER_ATTR          5 (NULL|self + go)
             22 CALL                     0
             30 RETURN_VALUE
④ dis 로 본 two_arg
              0 COPY_FREE_VARS           1

 13           2 RESUME                   0

 14           4 LOAD_GLOBAL              0 (super)
             14 LOAD_GLOBAL              2 (C)
             24 LOAD_FAST                0 (self)
             26 LOAD_SUPER_ATTR         11 (NULL|self + go)
             30 CALL                     0
             38 RETURN_VALUE
⑤ 셀에 실제로 무엇이 들어 있나
   C.zero_arg.__closure__[0].cell_contents is C : True
(exit 0)
```

그림 해설 — 다섯 덩어리가 「컴파일러가 채운 것」을 눈으로 보인다.

* **①에서 두 꼴이 같은 답을 준다.** 겉보기로는 못 가른다.
* ★★ **②가 근거다.** `zero_arg` 와 `two_arg` 는 `co_freevars` 에 `('__class__',)` 가 있고
  **`no_super` 만 비어 있다.**
  ★ **전제가 하나 뒤집힌다** — 「인자 없는 꼴에만 셀이 생긴다」가 아니다.
  **`super` 라는 이름이 메서드 몸통에 있으면** 두 인자 꼴에도 셀이 생긴다.
  문서가 인자 없는 꼴만 말하므로 오해하기 쉬운 자리다.
* ★ **③과 ④가 갈리는 자리는 한 줄뿐이다.**
  `zero_arg` 는 `LOAD_DEREF 1 (__class__)` 로 **셀에서 꺼내고**,
  `two_arg` 는 `LOAD_GLOBAL 2 (C)` 로 **전역에서 이름을 찾는다.**
  ★ 그래서 두 인자 꼴은 **`C` 를 다른 것에 다시 묶으면 따라간다** — 인자 없는 꼴은 안 따라간다.
* ★★ **`dis` 의 명령 이름은 흔들리는 칸이다.** `LOAD_SUPER_ATTR` 은 **3.12 에서 새로 생긴 것**이고
  그 전 판은 `LOAD_METHOD` 를 썼다. **근거로 쓰는 것은 `co_freevars` 쪽**이다.
* ★ **⑤가 셀의 내용을 확인한다** — `cell_contents is C` 가 참이다. **추측이 아니라 그 객체 자체다.**

인자 없는 꼴이 **못 쓰이는 자리**가 있다. 중첩 함수 안이다.

```python
# e34_nested.py
class P:
    def go(self):
        return "P.go"


class C(P):
    def go(self):
        def inner():
            return super().go()        # ★ 중첩 함수 안이다
        return inner()


print("C().go() 를 부른다")
print(C().go())
```
```text
===== python3 - <e34_nested.py =====
C().go() 를 부른다
Traceback (most recent call last):
  File "<stdin>", line 14, in <module>
  File "<stdin>", line 10, in go
  File "<stdin>", line 9, in inner
RuntimeError: super(): no arguments
(exit 1)
```

* ★ **`RuntimeError: super(): no arguments`** 다. `TypeError` 가 아니라 **`RuntimeError`** 인 것이 특징이다.
* ★★ **프레임이 셋**이다 — `<module>` → `go` → `inner`.
  터진 자리가 `inner` 이고, **`inner` 에는 `self` 도 `__class__` 셀도 없다.**
  컴파일러는 **메서드 몸통에만** 그 셀을 채워 주고 그 안의 중첩 함수에는 안 채운다.
* ★ **실행 중 예외라 캐럿이 없다.** 세 프레임 전부 `File "<stdin>", line N` 꼴이다.
* ★ **고치는 법 둘** — 두 인자 꼴 `super(C, self)` 를 쓰거나,
  바깥에서 `sup = super()` 로 만들어 두고 안에서 그것을 쓴다.

**비용** — 인자 없는 꼴이 **짧고 안전한 기본값**이다. 두 인자 꼴은 중첩 함수·동적 호출에만 쓴다.
★ **두 꼴의 속도 차이는 안 쟀다.**

### 6. ★★ 믹스인 순서 — 왼쪽이 바깥이다

**언제 쓰나** — 믹스인을 적는 순서를 정할 때. 「왜 이 데코레이션이 저 데코레이션 안에 들어가지」가 막힐 때.

```text
   class LoudFirst(Loud, Quiet, Base)      class QuietFirst(Quiet, Loud, Base)

   줄 : LoudFirst Loud Quiet Base object   줄 : QuietFirst Quiet Loud Base object

   label() 이 도는 길                       label() 이 도는 길
     Loud  가 바깥                            Quiet 가 바깥
       Quiet 가 안                              Loud  가 안
         Base 가 알맹이                           Base 가 알맹이

   -> LOUD(quiet(base))                    -> quiet(LOUD(base))

   ★ 왼쪽에 적은 것이 "먼저 불리고" 그래서 "바깥" 이 된다
```

```python
# e34_mixin.py
class Base:
    def label(self):
        return "base"


class Loud:
    def label(self):
        return "LOUD(" + super().label() + ")"


class Quiet:
    def label(self):
        return "quiet(" + super().label() + ")"


class LoudFirst(Loud, Quiet, Base):
    pass


class QuietFirst(Quiet, Loud, Base):
    pass


print("① 같은 세 클래스, 적은 순서만 다르다")
for cls in (LoudFirst, QuietFirst):
    print("   %-10s MRO : %s" % (cls.__name__, " -> ".join(k.__name__ for k in cls.__mro__)))
print("② 결과가 뒤집힌다 — 왼쪽에 적은 것이 바깥이다")
print("   LoudFirst().label()  ->", LoudFirst().label())
print("   QuietFirst().label() ->", QuietFirst().label())
print("③ 믹스인을 Base 뒤에 적으면 아예 안 불린다")


class BaseFirst(Base, Loud, Quiet):
    pass


print("   BaseFirst MRO :", " -> ".join(k.__name__ for k in BaseFirst.__mro__))
print("   BaseFirst().label() ->", BaseFirst().label())
print("   ★ Base.label 이 super() 를 안 부르므로 거기서 끝난다")
print("④ object 는 어느 경우에도 맨 끝이다")
for cls in (LoudFirst, QuietFirst, BaseFirst):
    print("   %-10s 마지막 : %s" % (cls.__name__, cls.__mro__[-1].__name__))
```
```text
===== python3 - <e34_mixin.py =====
① 같은 세 클래스, 적은 순서만 다르다
   LoudFirst  MRO : LoudFirst -> Loud -> Quiet -> Base -> object
   QuietFirst MRO : QuietFirst -> Quiet -> Loud -> Base -> object
② 결과가 뒤집힌다 — 왼쪽에 적은 것이 바깥이다
   LoudFirst().label()  -> LOUD(quiet(base))
   QuietFirst().label() -> quiet(LOUD(base))
③ 믹스인을 Base 뒤에 적으면 아예 안 불린다
   BaseFirst MRO : BaseFirst -> Base -> Loud -> Quiet -> object
   BaseFirst().label() -> base
   ★ Base.label 이 super() 를 안 부르므로 거기서 끝난다
④ object 는 어느 경우에도 맨 끝이다
   LoudFirst  마지막 : object
   QuietFirst 마지막 : object
   BaseFirst  마지막 : object
(exit 0)
```

그림 해설.

* ★★ **②가 결과를 뒤집어 보인다.** 같은 세 클래스인데 `LOUD(quiet(base))` 와 `quiet(LOUD(base))` 다.
  ★ **왼쪽이 먼저 불리고, 먼저 불린 것이 바깥이 된다.**
  이것이 「믹스인은 왼쪽에 적는다」는 관용구의 근거다.
* ★★★ **③이 가장 흔한 사고다.** 믹스인을 `Base` **뒤**에 적으면 `BaseFirst().label()` 이 그냥 `base` 다.
  ★ 줄에는 `Loud`·`Quiet` 가 **있는데도** 안 불렸다 —
  `Base.label` 이 `super()` 를 안 부르므로 **거기서 사슬이 끝난다**(동작 4와 같은 구조).
  ★ **줄에 있는 것과 도는 것은 다르다** — 창 ①과 창 ②를 둘 다 봐야 하는 이유다.
* **④ — `object` 는 어느 경우에도 맨 끝**이다. 동작 1의 merge 로그가 그 이유를 보였다.

**비용** — 순서 하나로 동작이 바뀌므로 **읽는 사람이 줄을 머릿속에 세워야 한다.**
★ 그래서 믹스인을 쓰는 코드는 **`__mro__` 를 주석이나 테스트로 못 박아 두는 것**이 관행이다.

### 7. ★ `__init_subclass__` — 자식이 만들어질 때 부모가 끼어든다

**언제 쓰나** — 플러그인 등록·하위 클래스 검증을 할 때. 메타클래스를 안 쓰고 같은 일을 하는 길이다.

```text
   class Alpha(Plugin):          class 문이 클래스 객체를 다 만든 "직후"

       ...                       ① 부모(정확히는 MRO 상 Plugin 의 super) 의
                                    __init_subclass__ 가 불린다
   ^ 이 줄이 끝나는 순간         ② cls 자리에 "방금 만들어진 자식" 이 온다
                                 ③ class Beta(Plugin, slug="bee") 의 키워드가
                                    그 함수의 인자로 온다

   ★ 자기 자신에게는 안 불린다 (Plugin 자신이 만들어질 때는 조용하다)
   ★ 손으로 안 붙였는데 classmethod 가 된다
```

```python
# e34_initsub.py
REGISTRY = []


class Plugin:
    def __init_subclass__(cls, /, slug=None, **kw):
        super().__init_subclass__(**kw)
        cls.slug = slug or cls.__name__.lower()
        REGISTRY.append(cls.slug)
        print("      __init_subclass__ : %s 가 만들어졌다 (slug=%s)" % (cls.__name__, cls.slug))


print("① class 문이 끝나는 순간 부모의 __init_subclass__ 가 불린다")


class Alpha(Plugin):
    pass


class Beta(Plugin, slug="bee"):
    pass


class Gamma(Beta):
    pass


print("② 등록된 것")
print("   REGISTRY :", REGISTRY)
print("③ 자기 자신에게는 안 불린다 — Plugin 은 목록에 없다")
print("   'plugin' in REGISTRY :", "plugin" in REGISTRY)
print("④ 암묵적으로 classmethod 가 된다 — 손으로 안 붙였는데")
print("   type(Plugin.__dict__['__init_subclass__']).__name__ :",
      type(Plugin.__dict__["__init_subclass__"]).__name__)
print("⑤ 클래스 키워드 인자는 여기로 온다")
print("   Beta.slug  :", Beta.slug)
print("   Gamma.slug :", Gamma.slug)
```
```text
===== python3 - <e34_initsub.py =====
① class 문이 끝나는 순간 부모의 __init_subclass__ 가 불린다
      __init_subclass__ : Alpha 가 만들어졌다 (slug=alpha)
      __init_subclass__ : Beta 가 만들어졌다 (slug=bee)
      __init_subclass__ : Gamma 가 만들어졌다 (slug=gamma)
② 등록된 것
   REGISTRY : ['alpha', 'bee', 'gamma']
③ 자기 자신에게는 안 불린다 — Plugin 은 목록에 없다
   'plugin' in REGISTRY : False
④ 암묵적으로 classmethod 가 된다 — 손으로 안 붙였는데
   type(Plugin.__dict__['__init_subclass__']).__name__ : classmethod
⑤ 클래스 키워드 인자는 여기로 온다
   Beta.slug  : bee
   Gamma.slug : gamma
(exit 0)
```

그림 해설.

* ★ **①에서 세 번 불렸다.** `Gamma(Beta)` 처럼 **손자**가 만들어질 때도 불린다 —
  `Beta` 가 물려받은 것이 그대로 걸린다.
* ★ **③ — 자기 자신에게는 안 불린다.** `Plugin` 은 목록에 없다.
  문서가 그렇게 정한다. 안 그러면 부모를 정의하는 순간부터 걸려 버린다.
* ★★ **④가 이 장치의 특징이다.** `type(Plugin.__dict__['__init_subclass__']).__name__` 이 **`classmethod`** 다.
  `@classmethod` 를 **손으로 안 붙였는데** 그렇게 된다 — 문서가 *"implicitly a class method"* 라고 적는다.
  ★ 그래서 안에서 `cls` 를 쓸 수 있다.
* **⑤ — 클래스 키워드 인자가 그 함수로 온다.** `class Beta(Plugin, slug="bee")` 의 `slug` 가 그것이다.
  ★ **`super().__init_subclass__(**kw)` 를 불러 남은 키워드를 넘기는 것**이 관용구다 —
  안 넘기면 `object.__init_subclass__` 가 **모르는 키워드라고 터뜨린다.**

★ 이 갈고리는 **`__set_name__` 과 한 자리에서 불린다**([33번](../33-property-descriptor-slots/2-summary.md) 동작 3).
문서가 둘을 같은 절(Creating the class object)에 두었고, **`__set_name__` 이 먼저, `__init_subclass__` 가 나중**이다.

**비용** — 메타클래스보다 훨씬 싸다. 메타클래스는 **충돌**이 나지만 이 갈고리는 그냥 메서드라 MRO 로 합쳐진다.

## 문법 — 형태와 규칙

**형태 — 무엇을 적으면 줄이 어떻게 서나**

```text
class C(Base1, Base2):          # 줄 = C + merge(Base1의 줄, Base2의 줄, [Base1, Base2])
                                #   왼쪽에 적은 것이 먼저 = 바깥

    def __init_subclass__(cls, /, **kw):   # 자식이 만들어질 때. 암묵적으로 classmethod
        super().__init_subclass__(**kw)    #   남은 키워드를 반드시 넘긴다

    def go(self):
        super().go()            # "부모" 가 아니라 "이 인스턴스의 MRO 에서 C 다음"
                                #   -> 컴파일러가 __class__ 셀을 채워 준다

    def go2(self):
        super(C, self).go()     # 두 인자 꼴. C 를 전역에서 이름으로 찾는다

    def bad(self):
        def inner():
            super().go()        # ★ RuntimeError — 중첩 함수에는 셀이 없다
        inner()
```

```text
진단 — 줄과 실행을 각각 다른 창으로 본다

C.__mro__                  줄 그 자체 (튜플, 순서가 보장된다)
C.mro()                    같은 것을 리스트로
C.__bases__                글자 그대로 적은 부모. ★ super() 가 가는 곳과 다를 수 있다
C.__mro__.index(X)         X 가 줄의 몇째인가
C.__mro__[-1] is object    맨 끝 확인
호출마다 계수기를 올린다      ★ 몇 번 돌았나 — "안 돈 것" 은 이 창으로만 보인다
fn.__code__.co_freevars    컴파일러가 __class__ 셀을 채웠나
dis.dis(fn)                LOAD_DEREF 인가 LOAD_GLOBAL 인가 (★ 명령 이름은 판마다 바뀐다)
```

규칙 열둘.

1. ★★★ **MRO 는 C3 로 계산되고, 규칙은 「꼬리에 있으면 못 나간다」 한 줄**이다.
2. ★ **merge 의 인자에 「부모를 적은 순서」가 한 줄 더 들어간다.** 그 줄이 왼쪽 우선을 보장한다.
3. ★ **`object` 가 맨 끝인 것은 특례가 아니라 규칙의 결과**다 — 모든 줄의 꼬리에 있다.
4. ★★ **줄을 못 세우면 정의 시점에 `TypeError`** 다. 인스턴스를 안 만들어도 터진다.
5. ★ **두 부모가 같은 조상 둘을 반대 순서로 들면 못 세운다.** 각각은 멀쩡한데 합칠 때 모순이다.
6. ★ **`super()`** 는 「**그 인스턴스의 타입의 MRO 에서 내 다음**」이다. 형제로 갈 수 있다([29번](../29-classes-and-attribute-lookup/2-summary.md) 정본).
7. ★★ **다이아몬드에서 각 클래스가 정확히 한 번씩** 돈다 — 계수로 확인한다.
8. ★★★ **한 명이라도 `super()` 를 안 부르면 그 뒤가 통째로 안 돈다.** 예외도 경고도 반환값 차이도 없다.
9. ★ **왼쪽에 적은 믹스인이 먼저 불리고 바깥이 된다.** `Base` 뒤에 적으면 아예 안 불린다.
10. ★ **인자 없는 `super()` 는 `__class__` 셀을 쓴다.** 중첩 함수에는 그 셀이 없어 `RuntimeError` 다.
11. ★ **`super` 라는 이름이 몸통에 있으면 두 인자 꼴에도 셀이 생긴다** — 셀 유무로 두 꼴을 못 가른다.
12. ★ **`__init_subclass__` 는 암묵적으로 classmethod** 이고 **자기 자신에게는 안 불린다**(3.6+).

**금지 사례 — 문법은 맞는데 조용히 어긋나는 것들**

```text
class X(A, B): pass
class Y(B, A): pass
class Z(X, Y): pass          # ① 정의 시점에 TypeError — 합칠 수 없는 두 줄

class Rude(Base):
    def go(self):
        pass                 # ② super() 를 안 불렀다 — 그 뒤가 통째로 안 돈다. 조용하다

class BaseFirst(Base, Mixin): # ③ 믹스인을 Base 뒤에 적었다 — Mixin 이 아예 안 불린다
    pass

class C(P):
    def go(self):
        def inner():
            return super().go()   # ④ RuntimeError 「super(): no arguments」
        return inner()

class Plugin:
    def __init_subclass__(cls, slug=None):
        cls.slug = slug           # ⑤ super().__init_subclass__() 를 안 불렀다
                                  #    남은 키워드가 있으면 조용히 삼켜진다

class Left(Base):
    def go(self):
        Base.go(self)             # ⑥ super() 대신 직접 적었다
                                  #    다이아몬드에서 Base 가 두 번 돈다
```

★ ②·③·⑤·⑥이 **아무 말이 없다.** ①과 ④만 터진다.

## 어디서 틀리나

### (1) ★★ `super()` 를 「부모」로 읽는다

**MRO 상 다음**이다. 다중 상속에서 **형제**로 갈 수 있다.\
★ 정본은 [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 5이고, 여기서는 **계수로 「한 번씩」까지** 확인했다(동작 3).

### (2) ★★★ MRO 를 표로 외운다

**두 줄짜리 규칙으로 돌리는 계산**이다. 외우면 `K1 K2 K3 D A B C E` 같은 줄에서 막힌다.\
★ 규칙은 **「그 후보가 어느 줄의 꼬리에도 없으면 뽑는다」** 하나다.

### (3) ★ merge 에 「적은 순서」 줄을 빠뜨린다

부모들의 줄만 합치면 **왼쪽 우선이 안 지켜진다.**\
★ `merge(L[B1], L[B2], [B1, B2])` 의 **마지막 인자**가 그것이다.

### (4) ★ `object` 가 맨 끝인 것을 특례로 외운다

**규칙의 결과**다. `object` 는 모든 줄의 꼬리에 있으므로 다른 후보가 남아 있는 한 못 나간다(동작 1의 merge 로그).

### (5) ★★ 상속 순서를 스타일로 안다

**합칠 수 없는 순서가 있다.** 각각은 멀쩡한 두 클래스를 합치는 것만으로 `TypeError` 가 난다(동작 2).\
★ 그리고 그것은 **정의 시점**이다.

### (6) ★★★ 협력 사슬에서 한 군데 `super()` 를 빼먹는다

**그 뒤가 통째로 안 돈다.** 예외도 경고도 없고 **반환값도 `None` 으로 같다**(동작 4의 ③).\
★ `__mro__` 를 찍어도 안 보인다 — **줄에는 있는데 아무도 안 부른 것**이다. 계수 로그라야 보인다.

### (7) ★★ 믹스인을 `Base` 뒤에 적는다

**아예 안 불린다.** `Base.label` 이 `super()` 를 안 부르므로 거기서 끝난다(동작 6의 ③).\
★ 관용구는 **믹스인을 왼쪽에, 실제 베이스를 오른쪽에** 적는 것이다.

### (8) ★ 믹스인 순서가 결과를 안 바꾼다고 믿는다

**바꾼다.** `LOUD(quiet(base))` 와 `quiet(LOUD(base))` 로 뒤집힌다 — **왼쪽이 바깥**이다.

### (9) ★ 중첩 함수 안에서 `super()` 를 쓴다

**`RuntimeError: super(): no arguments`** 다. `TypeError` 가 아니다.\
★ 컴파일러는 **메서드 몸통에만** `__class__` 셀을 채운다.

### (10) ★ `co_freevars` 로 두 꼴을 가르려 한다

**못 가른다.** `super` 라는 **이름만 있어도** 두 인자 꼴에 셀이 생긴다(동작 5의 ②).\
★ 갈리는 것은 `dis` 의 `LOAD_DEREF` 대 `LOAD_GLOBAL` 한 줄이다.

### (11) ★ `super()` 대신 `Base.go(self)` 를 직접 적는다

다이아몬드에서 **공통 조상이 두 번 돈다.** 한 번씩 도는 것이 `super()` 를 쓰는 이유다.

### (12) ★ `__init_subclass__` 에서 `super()` 를 안 부른다

남은 키워드가 **조용히 삼켜진다.** 관용구는 `super().__init_subclass__(**kw)` 다.\
★ 그리고 **자기 자신에게는 안 불린다** — 부모 자신을 등록하려면 따로 적어야 한다.

### (13) ★ `dis` 의 명령 이름을 성질로 적는다

**판마다 바뀐다.** `LOAD_SUPER_ATTR` 은 **3.12 에서 생긴 것**이다.\
★ 외울 것은 명령 이름이 아니라 「**셀에서 꺼내나 전역에서 찾나**」라는 성질이다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★★★ **이 주제는 「언어 보장」이 이 배치에서 가장 두껍다** —
C3 는 규칙의 **이름**뿐 아니라 **계산법까지** 공식 하우투가 공개한다.
구현 쪽에 남는 것은 **바이트코드와 예외 문구**뿐이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **언어 보장** | 레퍼런스·하우투가 정한 것 | 문서 문장 인용 + 손계산 대조 |
| **CPython 구현** | 이 구현이 그렇게 하는 것 | `dis` · 예외 문구 |
| **이 판(3.12.3)의 관찰** | 이 판에서 그랬을 뿐 | 명령 이름 · 문구의 개행 위치 |

### 언어 보장

| 사실 | 근거 |
|---|---|
| ★★★ 조상 탐색 순서가 **C3** 이고 다이아몬드에서 옳게 동작한다 | 3.2.10 — *"uses the C3 method resolution order"* |
| ★★★ C3 의 **계산법**(head/tail/merge) | The Python 2.3 Method Resolution Order 하우투 |
| 줄을 못 세우면 **클래스를 만들 때** 실패한다 | 하우투 — 선형화가 없으면 클래스를 만들 수 없다 |
| `super()` 는 **type 바로 다음 클래스부터** 찾는다 | `super()` — *"The search starts from the class right after the type."* |
| 인자 없는 꼴은 **컴파일러가 채운다** | `super()` — *"the compiler fills in the necessary details"* |
| 인자 없는 꼴은 **메서드 정의 안에서만** 쓸 수 있다 | `super()` 문서 |
| `__mro__` 는 `getattr()` 과 `super()` 가 **함께 쓰는** 순서다 | `super()` 문서 |
| `__init_subclass__` 는 **암묵적으로 classmethod** 다 | `object.__init_subclass__` — *"implicitly a class method"* |
| `__init_subclass__` 는 **자기 자신이 정의될 때는 안 불린다** | 같은 문서 |
| 클래스 키워드 인자가 `__init_subclass__` 로 간다 | PEP 487 |

### CPython 구현 세부사항

| 사실 | 어떻게 확인했나 |
|---|---|
| `LOAD_SUPER_ATTR` 이라는 명령 | `dis` — **3.12 에서 새로 생긴 것** |
| `LOAD_DEREF __class__` 대 `LOAD_GLOBAL C` 로 갈리는 것 | `dis` — 성질은 보장, **명령 이름은 구현** |
| `super` 라는 **이름만 있어도** 셀이 생기는 것 | 실행 — `co_freevars` |
| MRO 실패 문구에 **개행이 박혀 두 줄로** 나오는 것 | 실행 — [29번](../29-classes-and-attribute-lookup/2-summary.md)도 같은 관찰 |
| `RuntimeError: super(): no arguments` 라는 **문구와 예외 종류** | 실행 |
| `type.__mro__` 가 `getset_descriptor` 인 것 | 실행 — [33번](../33-property-descriptor-slots/2-summary.md)의 「더 들어가면」 |

### 이 판(3.12.3)의 관찰

| 관찰 | 어디가 흔들리나 |
|---|---|
| `dis` 의 **명령 이름과 오프셋** | 판마다 바뀐다. 3.12 가 실제로 바꿨다 |
| `dis` 의 **줄 번호** | 소스에서 몇째 줄인지라 블록을 고치면 바뀐다 |
| 예외 **문구** 셋 전부 | 종류는 명세, 문구는 아니다 |
| MRO 실패 문구의 **줄바꿈 위치** | 메시지 안의 개행이다 |
| `merge` 로그의 **탈락 줄 문구** | ★ 이것은 **내가 쓴 프로그램의 출력**이지 언어의 것이 아니다 |

### 그래서 이렇게 적으면 틀린다

* ✗ 「MRO 는 CPython 이 정하는 순서다」\
  ○ ★★★ **C3 라는 것과 그 계산법까지 언어 문서가 공개한다.** 구현인 것은 **바이트코드와 문구**다.
* ✗ 「`super()` 는 부모를 부른다」\
  ○ **MRO 상 다음**이다. 형제일 수 있다.
* ✗ 「다이아몬드에서는 공통 조상이 두 번 돈다」\
  ○ `super()` 를 쓰면 **한 번**이다. 두 번 도는 것은 `Base.go(self)` 를 직접 적었을 때다.
* ✗ 「`super()` 를 빼먹으면 어디선가 터지겠지」\
  ○ **안 터진다.** 반환값도 같다. 계수 로그라야 보인다.
* ✗ 「`__mro__` 를 찍어 보면 무엇이 도는지 알 수 있다」\
  ○ **줄에 있는 것과 도는 것은 다르다.** 창 둘을 다 봐야 한다.
* ✗ 「상속 순서는 스타일이다」\
  ○ **합칠 수 없는 순서가 있고**, 순서가 **결과를 뒤집는다.**
* ✗ 「`object` 가 맨 끝인 것은 언어가 특별히 정한 것이다」\
  ○ **C3 의 결과**다. 모든 줄의 꼬리에 있어 마지막까지 못 나간다.
* ✗ 「중첩 함수의 `super()` 는 `TypeError` 다」\
  ○ **`RuntimeError`** 다.
* ✗ 「`co_freevars` 에 `__class__` 가 있으면 인자 없는 꼴이다」\
  ○ **`super` 라는 이름만 있어도** 생긴다.
* ✗ 「`__init_subclass__` 에 `@classmethod` 를 붙여야 한다」\
  ○ **암묵적으로 된다.** 붙여도 되지만 필요 없다.

**판정 기준 한 줄**: **「줄이 어떻게 서나」를 물으면 C3 를 손으로 돌리고,
「실제로 무엇이 도나」를 물으면 계수 로그를 본다. 둘은 같은 질문이 아니다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 판정 |
|---|---|
| 단일 상속으로 충분하다 | **그렇게 한다.** MRO 를 생각할 일이 없다 |
| 기능을 여러 클래스에 얹는다 | **믹스인** — ★ 왼쪽에 적는다. 믹스인마다 `super()` 를 부른다 |
| 다이아몬드가 생긴다 | ★ **모든 참여자가 `super()` 를 부르고 서명을 맞춘다.** 아니면 단일 상속으로 바꾼다 |
| 부모 메서드를 확실히 하나만 부르고 싶다 | `Base.go(self)` — ★ 다이아몬드에서는 **두 번 돌 각오**를 한다 |
| 하위 클래스를 등록·검증한다 | **`__init_subclass__`** — 메타클래스보다 훨씬 싸다 |
| 클래스 생성 자체를 바꿔야 한다 | 메타클래스 — ★ **충돌이 난다.** 되도록 피한다 |
| 다중 상속 코드를 읽는다 | ★ **`__mro__` 를 먼저 찍는다.** 그 다음 계수 로그를 심는다 |
| 중첩 함수·람다 안에서 부모를 부른다 | **두 인자 꼴** `super(C, self)` 또는 바깥에서 만든 프록시 |
| 협력 사슬이 도는지 확인하고 싶다 | ★ **계수기를 심는다.** 「안 돈 것」은 이 창으로만 보인다 |
| 추상 계약을 강제하고 싶다 | [35번](../35-abc-and-protocol/2-summary.md) — ABC 가 **인스턴스를 만들 때** 막는다 |

## 핵심 문장

* ★★★ **MRO 는 외우는 표가 아니라 두 줄짜리 규칙으로 돌리는 계산이다** —
  「후보가 어느 줄의 꼬리에도 없으면 뽑는다」. 손으로 돌린 결과가 `__mro__` 와 **한 글자도 같았다.**
* ★★ **`object` 가 맨 끝인 것은 특례가 아니라 그 규칙의 결과**다. 모든 줄의 꼬리에 있어 마지막까지 못 나간다.
* ★★★ **줄을 못 세우면 정의 시점에 `TypeError` 이고, 그 문구가 C3 의 정의를 말한다** —
  `Cannot create a consistent method resolution order`.
  ★ **각각은 멀쩡한 두 클래스**를 합치는 것만으로 난다.
* ★★ **`super()`** 는 「**그 인스턴스의 타입의 MRO 에서 내 다음**」이다. **형제로 간다.**
  그 덕에 다이아몬드에서 **각 클래스가 정확히 한 번씩** 돈다(계수로 확인).
* ★★★ **한 명이라도 `super()` 를 안 부르면 그 뒤가 통째로 안 돈다 — 예외도 경고도 반환값 차이도 없다.**
  `__mro__` 에는 버젓이 있으므로 **줄을 찍어도 안 보인다.** 계수 로그라야 보인다.
* ★★ **믹스인은 왼쪽에 적은 것이 먼저 불리고 바깥이 된다.** `Base` 뒤에 적으면 **아예 안 불린다.**
* ★ **인자 없는 `super()` 는 컴파일러가 채운 `__class__` 셀을 쓴다.**
  ★ 다만 **`super` 라는 이름만 있어도 셀이 생기므로** 셀 유무로 두 꼴을 못 가른다 — 갈리는 것은 `LOAD_DEREF` 대 `LOAD_GLOBAL` 이다.
* ★ **중첩 함수 안에서는 `RuntimeError: super(): no arguments`** 다. 셀이 메서드 몸통에만 있기 때문이다.
* ★ **`__init_subclass__` 는 암묵적으로 classmethod** 이고 **자기 자신에게는 안 불린다**(3.6+).

## 관련 자료

* 목록: [python/syntax 주제 목록](../README.md) — 이 주제는 **34번**
* 선행·정본: [29-classes-and-attribute-lookup](../29-classes-and-attribute-lookup/2-summary.md) — ★★★ **`super()` 가 「MRO 다음」이라는 것의 정본.**\
  **경계**: 「속성을 어느 칸에서 찾나」와 「`super()` 가 부모가 아니다」는 그쪽까지,
  여기는 「**그 순서가 어떻게 계산되고 언제 계산이 실패하나**」부터다.
  쉬운 실패(`class Bad(A, B)`)도 그쪽 실측이라 여기서는 **더 안 보이는 실패**를 던졌다.
* 선행: [33-property-descriptor-slots](../33-property-descriptor-slots/2-summary.md) — 클래스 칸에 무엇을 앉히나.\
  **경계**: 칸 하나의 이야기는 그쪽, **여러 칸을 훑는 순서**는 여기.
  ★ `__slots__` 의 **다중 상속 레이아웃 충돌**은 그쪽이 정본이다 — MRO 와 다른 이유로 막히는 자리다.
* 선행: [24-decorators](../24-decorators/2-summary.md) — 데코레이터가 이름에 결과를 다시 묶는 것.
* 이어지는 곳: [35-abc-and-protocol](../35-abc-and-protocol/2-summary.md) — 「추상 베이스 클래스와 `Protocol`」 — ★ ABC 가 **줄 위에 계약을 얹는** 장치다.
  `collections.abc` 의 믹스인이 이 주제의 MRO 로 합쳐진다.
* 이어지는 곳: [36-dataclasses](../36-dataclasses/2-summary.md) — 「`dataclasses`」 — ★ 상속한 `dataclass` 의 필드가 **MRO 를 거꾸로 훑어** 모인다.
  「부모 필드가 앞」이라는 규칙이 이 주제 위에 선다.
* 이어지는 곳: 목록의 **37번 주제** 「`enum`」 — `Enum` 이 **메타클래스**로 만들어진 대표 사례다.
* 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **09번** 「상속과 오버라이딩」 —
  ★ **자바는 클래스 단일 상속이라 MRO 가 필요 없다.** 필드는 **가리기**(hiding)이지 오버라이딩이 아니다.
* 다른 갈래: 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번** 「인터페이스 `default` 메서드」 —
  ★ **가장 가까운 대비**다. 자바도 `default` 메서드로 다이아몬드가 생기는데,
  **C3 로 줄을 세우는 대신 컴파일 에러를 내고 사람에게 `X.super.m()` 을 적게 한다.**
  파이썬은 **줄을 세워 자동으로 고르고**, 못 세울 때만 거부한다.
* 다른 갈래: Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **20번** 「인터페이스 기본 구현과 `super`」 —
  코틀린도 `super<Base>.m()` 으로 **사람이 고르게** 한다.
* 원리: [`cs/foundations/oop-basics/`](../../../../oop-basics/) — 상속·다형성 일반론.
  여기는 그 일반론을 **파이썬의 줄 세우기 규칙으로** 좁혀 받는다.
* 공식 문서: [Custom classes](https://docs.python.org/3.12/reference/datamodel.html#custom-classes) ·
  [`super()`](https://docs.python.org/3.12/library/functions.html#super) ·
  [`__init_subclass__`](https://docs.python.org/3.12/reference/datamodel.html#object.__init_subclass__) ·
  [The Python 2.3 Method Resolution Order](https://docs.python.org/3/howto/mro.html)

## 용어 풀이

* **MRO(method resolution order)**: 조상을 훑을 순서를 한 줄로 편 것.\
  예: `Cls.__mro__` 가 그 튜플이고 **순서가 보장된다.**
* **C3 선형화(C3 linearization)**: MRO 를 만드는 규칙. 못 만드는 순서가 있다.\
  예: 규칙은 「후보가 어느 줄의 꼬리에도 없으면 뽑는다」 한 줄이다.
* **head / tail**: 한 줄의 **맨 앞**과 **맨 앞을 뺀 나머지**.\
  예: `K1 A B C object` 의 head 는 `K1`, tail 은 `A B C object` 다.
* **merge**: 여러 줄을 한 줄로 합치는 절차. C3 의 본체다.\
  예: 인자에 **「부모를 적은 순서」 줄이 하나 더** 들어간다.
* **선형화 불가(inconsistent MRO)**: 모든 후보가 꼬리에 걸려 줄을 못 세우는 상태.\
  예: 정의 시점에 `TypeError` 가 난다.
* **`super()`**: MRO 상 내 다음에게 넘기는 프록시.\
  예: 부모가 아니라 **형제**일 수 있다.
* **협력적 다중 상속(cooperative multiple inheritance)**: 모두가 `super()` 를 불러 줄 전체를 도는 방식.\
  예: 한 군데만 빼먹어도 그 뒤가 통째로 안 돈다. **조용하다.**
* **믹스인(mixin)**: 기능만 얹으려고 만든 작은 클래스.\
  예: **왼쪽에 적는다.** 오른쪽에 적으면 안 불릴 수 있다.
* **`__class__` 셀**: 인자 없는 `super()` 를 위해 컴파일러가 만들어 주는 자유변수.\
  예: `co_freevars` 에 `'__class__'` 로 보인다. **중첩 함수에는 없다.**
* **`__init_subclass__`**: 하위 클래스가 만들어질 때 불리는 갈고리(3.6+).\
  예: **암묵적으로 classmethod** 이고 자기 자신에게는 안 불린다.
* **클래스 키워드 인자**: `class C(Base, slug="x")` 의 `slug`.\
  예: `__init_subclass__` 의 인자로 온다.

## 더 들어가면

* ★ **`type.__mro__` 자체가 `getset_descriptor` 다** — [33번](../33-property-descriptor-slots/2-summary.md)의 「더 들어가면」에서 던져 확인했다.
  ★ 즉 **줄을 읽는 창조차 이 배치가 다룬 디스크립터 규칙 위에 서 있다.**
* ★ **메타클래스가 `mro()` 를 재정의할 수 있다** — C3 대신 다른 순서를 쓸 수 있다는 뜻이다.
  ★ 그런 코드를 읽을 일은 드물지만, 「**C3 는 기본값이지 유일한 선택이 아니다**」는 것이 `mro()` 가 메서드인 이유다.
  이 배치에서는 재정의를 던지지 않았다 — **인출 대상 밖**이다.
* ★ **`super()` 는 속성 조회에도 걸린다.** 메서드만이 아니라 `super().x` 도 MRO 다음부터 찾는다.
  ★ 이 문서는 메서드만 던졌다.
* ★ **`__mro_entries__`(PEP 560)** 는 제네릭 별칭(`list[int]` 같은 것)을 베이스에 쓸 수 있게 해 주는 장치이고,
  **MRO 계산 앞단**에 끼어든다. 목록의 **41번 주제** 가 그 자리다.
* ★ **`__init_subclass__` 와 `__set_name__` 은 같은 자리에서 불린다** —
  문서의 「Creating the class object」 절이 둘을 나란히 두었고 **`__set_name__` 이 먼저**다.
  [33번](../33-property-descriptor-slots/2-summary.md) 동작 3이 `__set_name__` 쪽 실측이다.
* ★ **`abc.ABCMeta` 가 메타클래스의 대표 사례**이고, 그것이 만든 클래스의 `type()` 이 `ABCMeta` 로 나온다 —
  [35번](../35-abc-and-protocol/2-summary.md) 이 실제로 찍는다.
