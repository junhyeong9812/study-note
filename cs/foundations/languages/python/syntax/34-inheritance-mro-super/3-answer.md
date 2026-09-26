# python/syntax/34-inheritance-mro-super — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★ 단 `dis` 의 **명령 이름·오프셋·줄 번호**는 판이 오르면 바뀐다(11번 답).
> 근거로 쓰는 것은 `co_freevars` 와 「**셀에서 꺼내나 전역에서 찾나**」라는 성질 쪽이다.

## 정답

### 1. `Z K1 K2 K3 D A B C E object` — 탈락 넷, 마지막은 `object` 가 걸린 것

**출력**

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

**왜 그런가**

* ★★★ **merge 의 규칙은 두 줄이다** — 왼쪽 줄부터 맨 앞(head)을 후보로 보고,
  **그 후보가 어느 줄의 꼬리(tail)에도 없으면 뽑는다.** 꼬리는 맨 앞을 뺀 나머지다.
* **탈락은 넷**이다. 첫 셋은 `A`·`A`·`D`·`A` 처럼 **`K3` 의 줄 꼬리**에 걸린 것이고,
  ★★ **마지막 탈락이 `object`** 다 — `후보 object 탈락 — E object 의 꼬리에 있다`.
* ★★★ **그 마지막 줄이 「`object` 가 맨 끝인 것은 특례가 아니다」의 증거다.**
  `object` 는 **모든 줄의 꼬리에 있으므로** 다른 후보가 하나라도 남아 있는 한 못 나간다.
  ★ 언어가 「`object` 를 마지막에 두라」고 따로 정한 규칙은 **없다.** 규칙의 결과일 뿐이다.
* ★ **③의 대조 줄이 이 문항을 근거로 만든다.** 손계산과 `__mro__` 가 **한 글자도 같다.**
  이 줄이 없으면 merge 로그는 「내가 쓴 프로그램의 출력」에 불과하다.
* **④가 성질 넷을 그 줄 위에서 확인한다** — 자식이 앞 · 적은 순서 유지 · `object` 맨 끝 ·
  **각 클래스가 정확히 한 번씩**(`len(real) == len(set(real))`).

★ **막혔다면 십중팔구 「적은 순서」 줄을 빠뜨린 것**이다. 10번 답을 보라.

### 2. `TypeError` — 「일관된 MRO 를 만들 수 없다」, 그리고 `for bases A, B`

**출력**

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

**왜 그런가**

* ★★ **`X` 와 `Y` 는 각각 멀쩡하다.** `X A B object` 와 `Y B A object` 가 먼저 찍혔다.
  **모순은 합칠 때만 생긴다** — 그래서 두 클래스를 따로 읽으면 절대 안 보인다.
* ★★★ **어느 후보도 못 뽑는다** —
  `A` 를 뽑으려면 `Y` 의 줄(`Y B A object`) 꼬리에 `A` 가 있어 막히고,
  `B` 를 뽑으려면 `X` 의 줄(`X A B object`) 꼬리에 `B` 가 있어 막힌다.
  **모든 후보가 꼬리에 걸린 상태**가 곧 선형화 불가다.
* ★★ **메시지가 C3 의 정의를 말한다** —
  `Cannot create a consistent method resolution order (MRO) for bases A, B`.
  ★ **「일관된(consistent)」** 이 낱말이 핵심이다. C3 가 지키려는 것은
  「**어느 부모의 줄에서도 앞뒤가 안 뒤집힌다**」이고, 그것이 불가능하면 **아무 줄이나 세우지 않고 거부한다.**
  ★ 그리고 **다툰 둘이 누구인지**(`for bases A, B`)까지 알려 준다 — `X`·`Y` 가 아니라 **`A`·`B`** 다.
* ★ **문구 안에 개행이 박혀 두 줄로 나온다** — `resolution` 다음에 갈린다.
  출력을 접은 것이 아니라 **메시지 자체에 `\n` 이 있다.**
* ★ **18째 줄에서 터졌다.** 프레임이 하나뿐이고 `<module>` 이다 —
  `class Z(X, Y):` 문을 실행하다 난 것이고 **인스턴스를 만들지도 않았다.**
  ★ **정의 시점에 터진다**는 것이 이 장치의 값이다.

### 3. 넷 다 `1 번` — 그리고 `Right` 는 형제다

**출력**

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

**왜 그런가**

* ★★★ **③의 계수가 넷 다 `1 번`** 이다. `Base` 가 **두 갈래로 이어져 있는데도 한 번**이다 —
  C3 가 `Base` 를 줄의 **한 자리**에만 놓았고, `super()` 가 그 줄을 **한 칸씩** 따라가기 때문이다.
  ★ 「한 번만 돈다」를 산문으로 적지 않고 **계수로 찍은 것**이 이 블록의 값이다.
* ★★ **④가 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 결론을 다시 건다.**
  같은 `Left.go` 안의 같은 `super()` 한 줄인데 다음이 갈린다 —
  `Left()` 에서는 `Base`, `Both()` 에서는 `Right`.
  **무엇이 정하나** — 그 인스턴스의 **타입**의 MRO 다.
* ★ **마지막 줄이 「형제」를 증명한다.** `"Right" in [k.__name__ for k in Left.__bases__]` 가 **`False`** 다.
  `Right` 는 `Left` 의 부모가 **아닌데** `super()` 가 거기로 간다.
  ★ 그래서 `super()` 를 「부모」로 읽으면 이 자리에서 반드시 틀린다.
* **②의 들여쓰기가 사슬의 깊이**다. 네 단계가 한 번씩 내려간다.

### 4. `Base.go` 가 안 찍힌다 — 뒤집으면 둘이 사라지고, 반환값으로는 못 가른다

**출력**

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

**왜 그런가**

* ★★ **①에서 `Base.go` 가 안 찍혔다.** 그런데 **`__mro__` 에는 `Base` 가 버젓이 있다** —
  첫 줄이 `Chain -> Polite -> Rude -> Base -> object` 를 먼저 찍는다.
  ★★★ **줄이 틀린 것이 아니라 줄을 끝까지 안 돈 것**이다.
  창 ①(`__mro__`)만 보면 안 보이고 창 ②(호출 로그)라야 보인다.
* ★★ **②가 더 나쁘다.** 순서만 뒤집으니 **`Polite` 와 `Base` 둘**이 사라졌다.
  **끊긴 자리가 앞으로 옮겨 갔을 뿐**인데 안 도는 클래스가 하나 늘었다.
  ★ 실무의 증상이 이것이다 — 「믹스인을 다른 순서로 적었더니 초기화가 하나 빠졌다」.
* ★★★ **③이 이 문항의 과녁이다.** 두 경우 모두 **`None`** 을 돌려준다.
  **예외도 경고도 없고 반환값으로도 못 가른다.**
  ★ [32번](../32-container-protocol/2-summary.md)의 ABC 가 「만들 때 막는」 장치였다면 여기는 **아무도 안 막는** 자리다.
* ★ 진단은 **계수 로그**다(3번 답). 「몇 번 돌았나」를 찍어야 「안 돈 것」이 드러난다.

★★ **판정 한 줄** — **협력 사슬의 정확성은 언어가 안 봐 준다.**

### 5. `no_super` 만 비어 있고, 갈리는 것은 `LOAD_DEREF` 대 `LOAD_GLOBAL` 한 줄

**출력**

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

**왜 그런가**

* ★★ **②의 결과가 전제를 하나 뒤집는다.**
  `zero_arg` 와 `two_arg` **둘 다** `co_freevars` 에 `('__class__',)` 가 있고,
  **`no_super` 만 비어 있다.**
  ★ 「인자 없는 꼴에만 셀이 생긴다」가 아니다 — **`super` 라는 이름이 메서드 몸통에 있으면** 생긴다.
  문서가 인자 없는 꼴만 설명하므로 오해하기 쉬운 자리다.
* ★ **③과 ④가 갈리는 것은 한 줄뿐이다.**
  `zero_arg` : `LOAD_DEREF 1 (__class__)` — **셀에서 꺼낸다.**
  `two_arg` : `LOAD_GLOBAL 2 (C)` — **전역에서 이름을 찾는다.**
  ★ 그래서 두 인자 꼴은 **`C` 를 나중에 다른 것에 다시 묶으면 따라간다.** 인자 없는 꼴은 안 따라간다.
* ★ **⑤ — `cell_contents is C` 가 참**이다. 셀 안에 **그 클래스 객체 자체**가 들어 있다.
* ★★ **`dis` 의 명령 이름은 흔들리는 칸이다.** `LOAD_SUPER_ATTR` 은 **3.12 에서 새로 생긴 것**이다.
  ★ **외울 것은 명령 이름이 아니라 「셀에서 꺼내나 전역에서 찾나」라는 성질**이다.

### 6. `RuntimeError: super(): no arguments` — 프레임 셋, 마지막이 `inner`

**출력**

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

**왜 그런가**

* ★ **예외 종류가 `TypeError` 가 아니라 `RuntimeError`** 다. 「타입이 틀렸다」가 아니라
  「**지금 이 자리에서는 그 정보를 얻을 수 없다**」는 뜻이기 때문이다.
* ★★ **프레임이 셋**이다 — `<module>`(14줄) → `go`(10줄) → `inner`(9줄).
  **터진 자리가 `inner`** 이고, `inner` 에는 **`self` 도 `__class__` 셀도 없다.**
  컴파일러는 **메서드 몸통에만** 그 셀을 채워 주고 그 안의 중첩 함수에는 안 채운다.
* ★ **실행 중 예외라 캐럿이 없다.** 세 프레임 전부 `File "<stdin>", line N` 꼴이다.
* ★ **고치는 법 둘** — 두 인자 꼴 `super(C, self)` 를 쓰거나,
  바깥에서 `sup = super()` 로 만들어 두고 안에서 그것을 쓴다(**프록시 객체는 넘어간다**).

### 7. `LOUD(quiet(base))` 와 `quiet(LOUD(base))` — 그리고 셋째는 「안 불린 것」이다

**출력**

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

**왜 그런가**

* ★★ **②가 결과를 뒤집어 보인다.** 같은 세 클래스인데 적은 순서만 바꾸자 감싼 순서가 뒤집혔다.
  ★ **왼쪽에 적은 것이 먼저 불리고, 먼저 불린 것이 바깥**이 된다.
  이것이 「믹스인은 왼쪽에 적는다」는 관용구의 근거다.
* ★★★ **③이 이 문항의 과녁이다.** `BaseFirst().label()` 이 그냥 `base` 인 이유는
  **줄에 없어서가 아니다.** 줄은 `BaseFirst -> Base -> Loud -> Quiet -> object` 이고
  `Loud`·`Quiet` 가 **버젓이 있다.**
  ★ **`Base.label` 이 `super()` 를 안 부르므로 거기서 사슬이 끝난 것**이다 — 4번 답과 정확히 같은 구조다.
* ★ **줄에 있는 것과 도는 것은 다르다** — 이 주제에서 두 번 나오는 구분이다(4번·7번).
* **④ — `object` 는 어느 경우에도 맨 끝**이다(1번 답의 근거).

### 8. 세 줄 — `Gamma(Beta)` 도 찍히고, `Plugin` 자신은 안 찍힌다

**출력**

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

**왜 그런가**

* ★ **로그가 세 줄**이다. `Gamma(Beta)` 처럼 **손자**가 만들어질 때도 찍힌다 —
  `Beta` 가 `Plugin` 에게서 물려받은 것이 그대로 걸린다.
* ★★ **`'plugin' in REGISTRY` 가 `False`** 다. **자기 자신이 정의될 때는 안 불린다.**
  ★ 문서가 그렇게 정한다. 안 그러면 **부모를 정의하는 순간부터** 걸려서,
  「등록할 것이 아직 아무것도 없는 클래스」가 목록에 들어간다.
* ★★ **④의 타입 이름이 `classmethod`** 다. **내가 안 붙였다.**
  문서가 *"implicitly a class method"* 라고 적는다 — 그래서 안에서 `cls` 를 쓸 수 있다.
  ★ 붙여도 되지만 **붙일 필요가 없다.**
* **⑤ — 클래스 키워드 인자가 그 함수로 온다.** `class Beta(Plugin, slug="bee")` 의 `slug` 다.
  ★ `Gamma` 는 키워드를 안 줬으므로 기본값 경로를 타 `gamma` 가 됐다.
  ★ **`super().__init_subclass__(**kw)` 를 불러 남은 키워드를 넘기는 것**이 관용구다 —
  안 넘기면 `object.__init_subclass__` 가 모르는 키워드라고 터뜨리거나, 키워드가 조용히 삼켜진다.

### 9. 두 번 돈다 — 그래서 `super()` 를 쓴다

**왜 그런가**

* `Left.go` 와 `Right.go` 가 **각각** `Base.go(self)` 를 부르면 `Base.go` 가 **두 번** 실행된다.
  `Base.__init__` 이 카운터를 올리거나 자원을 잡는 코드였다면 **두 번 잡힌다.**
* ★ `super()` 는 그 자리를 **줄의 다음 한 칸**으로 바꾼다. 줄에 `Base` 가 한 번만 있으므로 **한 번만 돈다**(3번 답).
* ★★ **한 줄로 말하면** — **`super()` 는 「부모를 부르는 문법」이 아니라 「줄을 한 칸 넘기는 문법」이다.**
  그 차이가 다이아몬드에서 횟수로 드러난다.
* ★ 거꾸로, **다이아몬드가 없고 부모를 확실히 하나만 부르고 싶으면** `Base.go(self)` 가 더 정확할 수 있다.
  다만 나중에 누가 다중 상속을 얹으면 **조용히 두 번 돌게** 된다.

### 10. 「부모를 적은 순서」 줄이 하나 더 들어간다

**왜 그런가**

* 공식 하우투의 식은 이렇다 — `L[C] = C + merge(L[B1], ..., L[Bn], [B1, ..., Bn])`.
  ★ **마지막 인자 `[B1, ..., Bn]`** 이 「부모를 적은 순서」다.
* ★★ **그것을 빼먹으면 「왼쪽에 적은 것이 먼저」가 안 지켜진다.**
  부모들의 줄만 합치면 서로 겹치지 않는 부모끼리는 **아무 순서로나 나갈 수 있기** 때문이다.
* ★ 1번의 블록이 그것을 코드로 적었다 —
  `merge([c3(b) for b in bases] + [bases], log)` 의 `+ [bases]` 가 그 줄이다.
* ★ 그리고 그 줄 덕에 `Z` 의 답에서 `K1 K2 K3` 가 **적은 순서 그대로** 나왔다(1번 답의 ④).

### 11. C3 는 보장, 명령 이름은 구현 — 그리고 `co_freevars` 로는 두 꼴을 못 가른다

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| ★★★ 조상 탐색이 **C3** 다 | **언어 보장** | 3.2.10 — *"uses the C3 method resolution order"* |
| ★★★ C3 의 **계산법**(head/tail/merge) | **언어 보장** | 공식 하우투가 알고리즘을 공개한다 |
| 줄을 못 세우면 **클래스를 못 만든다** | **언어 보장** | 하우투 |
| `super()` 가 **type 바로 다음부터** 찾는다 | **언어 보장** | `super()` 문서 |
| 인자 없는 꼴을 **컴파일러가 채운다** | **언어 보장** | `super()` 문서 |
| `__init_subclass__` 가 **암묵적 classmethod** 다 | **언어 보장** | `object.__init_subclass__` |
| `LOAD_SUPER_ATTR` 이라는 **명령 이름** | **CPython 구현** | `dis` — 3.12 에서 생겼다 |
| `LOAD_DEREF` 대 `LOAD_GLOBAL` 로 갈리는 것 | **성질은 보장 · 명령 이름은 구현** | `dis` |
| `super` 라는 **이름만 있어도** 셀이 생기는 것 | **CPython 구현** | 실행 — 문서에 없다 |
| 예외 **문구**와 그 안의 **개행 위치** | **이 판의 관찰** | 실행 |

★★ **마지막 물음의 답**은 「**못 가른다**」이다(5번 답의 ②).
`two_arg` 에도 셀이 생기므로 `co_freevars` 만 봐서는 두 꼴이 같아 보인다.
★ **`dis` 의 한 줄**(`LOAD_DEREF` 대 `LOAD_GLOBAL`)이라야 갈린다 —
그런데 그 창의 **명령 이름은 흔들리므로**, 성질(「셀에서 꺼내나 전역에서 찾나」)로 적어야 한다.

### 12. 29 는 「순서를 쓴다」, 34 는 「순서를 계산한다」

**왜 그런가**

* ★ **경계 한 줄씩** —
  [29번](../29-classes-and-attribute-lookup/2-summary.md)은 **그 순서를 속성 탐색에 어떻게 쓰나**가 정본이다
  (네 층·`super()` 가 부모가 아니라는 것·쉬운 MRO 실패).
  **34번은 그 순서가 어떻게 계산되고 언제 계산이 실패하며, 줄을 실제로 다 도는가**가 정본이다.
* ★★ **자바 11번과의 대비가 이 주제에서 가장 선명하다.**
  자바도 인터페이스 `default` 메서드로 **같은 다이아몬드**가 생긴다.
  그런데 자바는 **줄을 안 세운다** — 같은 시그니처를 둘 상속하면 **컴파일 에러**를 내고
  사람에게 `X.super.m()` 으로 **직접 고르게** 한다.
  ★ 파이썬은 반대로 **C3 로 줄을 세워 자동으로 고르고**, 못 세울 때만 거부한다.
  ★★ **둘의 대가가 다르다** — 자바는 매번 사람이 적어야 하고, 파이썬은
  **줄을 끝까지 도는지 아무도 안 봐 준다**(4번 답). 코틀린도 `super<Base>.m()` 으로 자바 쪽이다.
* ★ **[33번](../33-property-descriptor-slots/2-summary.md)의 `__slots__` 다중 상속 실패는 다른 것**이다.
  그쪽은 `TypeError: multiple bases have instance lay-out conflict` —
  **MRO 는 세울 수 있는데 인스턴스 칸의 배치를 겹칠 수 없는 것**이다.
  이쪽은 `Cannot create a consistent method resolution order` — **줄 자체를 못 세우는 것**이다.
  ★ **둘 다 정의 시점에 터지고 둘 다 `TypeError` 인데 원인이 다르다.** 문구로 갈라야 한다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| C3 손계산과 `__mro__` 대조 | `python3 - <e34_c3.py` | 2(캡처 + 재대조) | 열 개짜리 줄이 **한 글자도 일치** · 탈락 4회 |
| 선형화 불가 트레이스백 전문 | `python3 - <e34_mro_fail.py` | 2 | 프레임 1개 · 문구에 개행 · `(exit 1)` |
| 다이아몬드 호출 계수 | `python3 - <e34_diamond.py` | 2 | 넷 다 **1번** · `Right` 는 형제 |
| 사슬이 끊기는 것 | `python3 - <e34_break.py` | 2 | 반환값이 **둘 다 `None`** — 못 가름 |
| `super()` 두 꼴 `dis` | `python3 - <e34_superdis.py` | 2 | `no_super` 만 셀 없음 · `LOAD_DEREF` 대 `LOAD_GLOBAL` |
| 중첩 함수 `super()` 트레이스백 | `python3 - <e34_nested.py` | 2 | `RuntimeError` · 프레임 3개 |
| 믹스인 순서 | `python3 - <e34_mixin.py` | 2 | 결과 뒤집힘 · `Base` 뒤 믹스인은 안 불림 |
| `__init_subclass__` | `python3 - <e34_initsub.py` | 2 | 3회 호출 · 자기 자신 제외 · 암묵 classmethod |
| 판 확인 | `python3 - <e34_version.py` | 2 | 3.12.3 · cpython · linux |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★ `dis` 의 **명령 이름**(`LOAD_SUPER_ATTR` 등) | **3.12 에서 실제로 바뀌었다** |
| `dis` 의 **오프셋과 줄 번호** | 컴파일러가 정한다. 소스를 고쳐도 바뀐다 |
| `super` 라는 **이름만 있어도** 셀이 생기는 것 | 문서에 없다. 컴파일러의 선택이다 |
| MRO 실패 문구와 그 안의 **개행 위치** | 종류는 명세, 문구는 아니다 |
| `RuntimeError: super(): no arguments` 문구 | 위와 같다 |
| merge 로그의 **탈락 줄 문구** | ★ 내가 쓴 프로그램의 출력이다. 언어의 것이 아니다 |

★ **안 흔들리는 칸** — ★★★ **`__mro__` 의 순서**(C3 는 명세다) · 각 클래스가 **몇 번 돌았나** ·
호출 로그의 **순서** · `co_freevars` 에 `__class__` 가 **있나 없나** ·
예외 **종류** · `File "<stdin>", line N` · `(exit N)`.
★★ **이 주제가 한 번도 안 잰 것** — **속도.** MRO 조회 비용·`super()` 두 꼴의 비용은 여기 없다.
