# python/syntax/34-inheritance-mro-super — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
>
> 이 갈래는 **예측형**이다 — 「무엇을 아는가」가 아니라 「**이 코드의 출력을 예측할 수 있는가**」를 묻는다.
> 코드가 있는 문항은 **돌려 보기 전에** 종이에 출력을 적고 시작한다.
> ★★★ 이 주제의 1번은 **종이와 연필이 필요하다.** `__mro__` 를 외워서 답하는 것이 아니라
> **merge 를 직접 돌려** 열 개짜리 줄을 세워야 한다. 그 줄이 틀리면 나머지가 다 무너진다.
> ★★ 그리고 **「무엇이 안 찍히나」가 답인 문항이 둘**이다(4번·6번).
> 찍힌 것만 맞히고 **안 찍힌 줄을 못 짚으면 틀린 것**으로 친다.
>
> 실행 환경: `python3` **3.12.3** · Linux. 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ **이 주제는 [29번](../29-classes-and-attribute-lookup/1-question.md)을 전부 쓴다** — `super()` 가 「MRO 다음」이라는 것이 거기 정본이다.
> ★ **이 사슬은 [29](../29-classes-and-attribute-lookup/1-question.md) → [33](../33-property-descriptor-slots/1-question.md) → 34** 로 이어진다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 손으로 줄을 세워 본다 (예측)

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

* `Z.__mro__` 를 **종이에 먼저 적어라.** 열 개다.
* ★ merge 로그에서 **탈락 줄이 몇 개**이고, 마지막 탈락은 **무엇이 무엇의 꼬리에 걸린 것**인가?
* ★★ `object` 가 맨 끝인 것은 **특례인가 규칙의 결과인가** — 그 근거가 로그의 어느 줄에 있나?

### 2. 각각은 멀쩡한 두 클래스를 합치면 (예측)

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

* `X.__mro__` 와 `Y.__mro__` 는 각각 어떻게 나오는가?
* ★ `class Z(X, Y)` 에서 무엇이 터지고 **몇째 줄**에서 터지는가?
* ★ 그 메시지가 **C3 의 무엇을 말해 주는가** — 그리고 `for bases` 뒤에 무엇이 오는가?

### 3. 다이아몬드에서 계수기를 심으면 (예측)

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

* ③의 네 수치는 각각 무엇인가?
* ★ ④에서 `Left` 의 다음이 `Left()` 와 `Both()` 에서 각각 무엇인가?
* ★ `Right` 는 `Left` 의 **부모인가 형제인가** — 출력의 어느 줄이 그것을 답하는가?

### 4. ★★ 한 명이 넘겨주기를 그만두면 (예측)

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

* ①에서 **안 찍히는 줄**은 무엇인가?
* ★ ②에서 순서만 뒤집으면 **몇 개가** 안 불리게 되는가?
* ★★ ③이 묻는 것 — 두 경우를 **반환값으로 가를 수 있는가**?

### 5. 두 꼴의 `super()` 를 `dis` 로 보면 (예측)

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

* ②에서 `co_freevars` 가 **셋 중 어느 것만** 비어 있는가?
* ★ ③과 ④가 갈리는 **한 줄**은 무엇인가?
* ★ ⑤의 `cell_contents is C` 는 참인가 거짓인가?

### 6. 인자 없는 `super()` 가 못 쓰이는 자리 (경계)

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

* 무엇이 터지는가 — **예외 종류와 메시지**를 적어라.
* ★ 프레임이 **몇 개**이고 마지막 프레임은 어느 함수인가?

### 7. 믹스인 순서를 바꾸면 (예측)

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

* ②의 두 결과 문자열은 각각 무엇인가?
* ★ ③에서 `BaseFirst().label()` 이 그냥 `base` 인 이유는 무엇인가 — **줄에 없어서인가 안 불려서인가**?

### 8. `__init_subclass__` 가 불리는 시점과 대상 (경계)

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

* ①에서 로그가 **몇 줄** 찍히고, `Gamma(Beta)` 에서도 찍히는가?
* ★ ③에서 `'plugin' in REGISTRY` 는 참인가 거짓인가 — **왜**인가?
* ★ ④의 타입 이름은 무엇이고, 그것을 **내가 붙였는가**?

### 9. `super()` 대신 부모를 직접 적으면 (왜)

* 다이아몬드에서 `Base.go(self)` 를 직접 적으면 `Base` 가 **몇 번** 도는가?
* ★ 그것이 `super()` 를 쓰는 이유를 한 줄로 말하면?

### 10. merge 의 인자 (경계)

* `merge` 의 인자에 **부모들의 줄 말고 무엇이 하나 더** 들어가는가?
* ★ 그것을 빼먹으면 C3 의 어떤 성질이 안 지켜지는가?

### 11. 세 층 가르기 (경계)

* 「MRO 가 C3 다」는 **언어 보장인가 CPython 구현인가**?
* ★ `LOAD_SUPER_ATTR` 이라는 명령 이름은 어느 층인가?
* ★★ `co_freevars` 에 `__class__` 가 있는 것으로 **두 꼴을 가를 수 있는가**?

### 12. 이웃 주제와의 경계 (연결)

* [29번](../29-classes-and-attribute-lookup/2-summary.md)이 정본인 것과 이 주제가 정본인 것을 한 줄씩으로 가르면?
* ★ 자바 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번** 과 견주면, 같은 다이아몬드를 두 언어가 **어떻게 다르게** 처리하는가?
* ★ [33번](../33-property-descriptor-slots/2-summary.md)의 `__slots__` 다중 상속 실패는 이 주제의 MRO 실패와 **같은 것인가 다른 것인가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
