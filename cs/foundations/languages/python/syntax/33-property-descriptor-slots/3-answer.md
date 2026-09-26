# python/syntax/33-property-descriptor-slots — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> [1-question.md](1-question.md)의 번호와 **1:1**로 대응한다. 질문 12개 = 답 12개.
>
> 이 파일의 모든 출력은 `python3` **3.12.3**(Linux, x86_64)에서 실제로 돌려 나온 것이다. 지어낸 출력은 없다.
> 던지는 형태는 `python3 - <파일` 로 고정했다.
> ★ 이 파일의 블록에는 **주소도 시간도 절대경로도 안 찍힌다** — 같은 판에서 다시 돌리면 **한 글자도 안 변한다.**
> ★★★ 단 하나 예외가 **`getsizeof` 의 바이트 수**다. 그 값은 **판·빌드·플랫폼이 바꾼다** —
> 이 문서가 근거로 쓰는 것은 **「어느 쪽이 작나」** 한 줄뿐이다(10번 답).

## 정답

### 1. 로그가 안 찍히는 줄은 `s.raw` 하나 — 그리고 `getattr_static` 은 셋 다 조용하다

**출력**

```python
# e33_three.py
import inspect


class Logged:                       # ② 손으로 만든 디스크립터
    def __set_name__(self, owner, name):
        self.public = name          # ★ 이름을 자동으로 받는다
        self.private = "_" + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        print("      [디스크립터] __get__ 이 답한다 :", self.public)
        return getattr(obj, self.private)

    def __set__(self, obj, value):
        print("      [디스크립터] __set__ 이 가로챈다 :", self.public, "<-", repr(value))
        setattr(obj, self.private, value)


class Sensor:
    __slots__ = ("raw", "_tag")     # ③ __slots__ — member_descriptor 두 개가 생긴다

    tag = Logged()

    @property                       # ① property
    def celsius(self):
        print("      [property] fget 이 답한다")
        return self.raw / 10

    @celsius.setter
    def celsius(self, v):
        print("      [property] fset 이 받는다")
        self.raw = round(v * 10)

    def __init__(self, raw, tag):
        self.raw = raw              # member_descriptor 가 받는다 — 조용하다
        self.tag = tag


print("① 세 장치가 한 클래스 칸에 나란히 있다")
s = Sensor(235, "실외")
for nm in ("celsius", "tag", "raw", "_tag"):
    print("   %-8s -> %s" % (nm, type(Sensor.__dict__[nm]).__name__))

print("② 누가 답하나 — 읽기")
print("   s.celsius ->", s.celsius)
print("   s.tag     ->", s.tag)
print("   s.raw     ->", s.raw, "  <- member_descriptor 는 로그를 안 남긴다")

print("③ 누가 답하나 — 쓰기")
s.celsius = 21.0
s.tag = "실내"
print("   다시 읽으면 :", end=" ")
print(s.raw, "|", getattr(s, "_tag"))

print("④ 셋 다 데이터 디스크립터인가 — 29번의 판별식을 그대로 건다")
for nm in ("celsius", "tag", "raw"):
    t = type(Sensor.__dict__[nm])
    print("   %-8s __get__:%-5s __set__:%-5s __delete__:%s"
          % (nm, hasattr(t, "__get__"), hasattr(t, "__set__"), hasattr(t, "__delete__")))

print("⑤ ★ getattr_static 은 디스크립터를 「부르지 않고」 거기 앉은 것을 본다")
for nm in ("celsius", "tag", "raw"):
    got = inspect.getattr_static(s, nm)
    print("   getattr_static(s, %-9s) -> %s" % (repr(nm), type(got).__name__))
print("   ★ 위 세 줄에 [property]·[디스크립터] 로그가 한 줄도 없다")

print("⑥ 인스턴스 칸은 아예 없다")
print("   hasattr(s, '__dict__') :", hasattr(s, "__dict__"))
try:
    vars(s)
except TypeError as ex:
    print("   vars(s) -> TypeError:", ex)
```
```text
===== python3 - <e33_three.py =====
① 세 장치가 한 클래스 칸에 나란히 있다
      [디스크립터] __set__ 이 가로챈다 : tag <- '실외'
   celsius  -> property
   tag      -> Logged
   raw      -> member_descriptor
   _tag     -> member_descriptor
② 누가 답하나 — 읽기
      [property] fget 이 답한다
   s.celsius -> 23.5
      [디스크립터] __get__ 이 답한다 : tag
   s.tag     -> 실외
   s.raw     -> 235   <- member_descriptor 는 로그를 안 남긴다
③ 누가 답하나 — 쓰기
      [property] fset 이 받는다
      [디스크립터] __set__ 이 가로챈다 : tag <- '실내'
   다시 읽으면 : 210 | 실내
④ 셋 다 데이터 디스크립터인가 — 29번의 판별식을 그대로 건다
   celsius  __get__:True  __set__:True  __delete__:True
   tag      __get__:True  __set__:True  __delete__:False
   raw      __get__:True  __set__:True  __delete__:True
⑤ ★ getattr_static 은 디스크립터를 「부르지 않고」 거기 앉은 것을 본다
   getattr_static(s, 'celsius') -> property
   getattr_static(s, 'tag'    ) -> Logged
   getattr_static(s, 'raw'    ) -> member_descriptor
   ★ 위 세 줄에 [property]·[디스크립터] 로그가 한 줄도 없다
⑥ 인스턴스 칸은 아예 없다
   hasattr(s, '__dict__') : False
   vars(s) -> TypeError: vars() argument must have __dict__ attribute
(exit 0)
```

**왜 그런가**

* ★ **`s.raw` 만 조용하다.** `member_descriptor` 는 **C 로 된 칸**이라 `print` 를 심을 자리가 없다.
  ★★ **「조용한 것」과 「안 지나간 것」은 다르다** — `raw` 도 분명히 디스크립터를 지나갔다.
  로그가 없다는 이유로 「그냥 인스턴스 칸에서 나왔겠지」로 읽으면 틀린다(`__slots__` 라 인스턴스 칸이 아예 없다).
* **④의 표가 셋을 한 규칙으로 묶는다** — 셋 다 `__get__`·`__set__` 이 참이라 **전부 데이터 디스크립터**다.
  ★ `tag`(내가 만든 `Logged`)만 `__delete__` 가 거짓인데, **판별식은 `__set__` 또는 `__delete__` 이므로** 자격에 차이가 없다.
* ★★ **⑤에서 로그가 한 줄도 안 찍힌다.** `inspect.getattr_static` 이 **디스크립터 프로토콜을 안 태우기** 때문이다.
  문서가 그렇게 적는다 — *"without triggering dynamic lookup via the descriptor protocol"*.
  이 세 줄이 「무엇이 거기 있나」와 「무엇이 답하나」를 가르는 증거다.
* ★ **⑥에서 `vars(s)` 가 `TypeError`** 다. 진단창 하나가 통째로 막히는 것은 [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 8의 ④와 같다.

★★★ **이 문항의 한 줄** — **세 장치는 다른 기능이 아니라 클래스 칸에 데이터 디스크립터를 앉히는 세 가지 방법이다.**

### 2. `is` 가 거짓이고, `fget` 은 같은 함수다

**출력**

```python
# e33_property.py
class Temp:
    def __init__(self, c):
        self._c = c

    @property
    def celsius(self):
        return self._c

    only_getter = celsius          # ★ setter 를 붙이기 전의 그 객체를 따로 붙잡아 둔다

    @celsius.setter
    def celsius(self, v):
        if v < -273.15:
            raise ValueError("절대영도 아래는 못 넣는다: %r" % v)
        self._c = v

    @celsius.deleter
    def celsius(self):
        print("      fdel 이 불렸다")
        self._c = None


print("① property 의 세 칸 — fget·fset·fdel")
for nm in ("only_getter", "celsius"):
    p = Temp.__dict__[nm]
    print("   %-11s fget:%-8s fset:%-8s fdel:%s"
          % (nm,
             p.fget.__name__ if p.fget else None,
             p.fset.__name__ if p.fset else None,
             p.fdel.__name__ if p.fdel else None))

print("② ★ @celsius.setter 는 그 자리를 고치는 게 아니라 새 property 를 만든다")
print("   only_getter is celsius :", Temp.__dict__["only_getter"] is Temp.__dict__["celsius"])
print("   둘 다 property 인가     :",
      type(Temp.__dict__["only_getter"]).__name__, type(Temp.__dict__["celsius"]).__name__)
print("   두 fget 이 같은 함수인가 :",
      Temp.__dict__["only_getter"].fget is Temp.__dict__["celsius"].fget)
print("   only_getter 에 fset 이 있나 :", Temp.__dict__["only_getter"].fset is not None)

print("③ 그래서 only_getter 쪽으로 대입하면 막힌다")
t = Temp(20.0)
print("   t.only_getter ->", t.only_getter)
try:
    t.only_getter = 30.0
except AttributeError as ex:
    print("   t.only_getter = 30.0 -> AttributeError:", ex)

print("④ celsius 쪽은 대입이 되고 검증도 돈다")
t.celsius = 30.0
print("   t.celsius ->", t.celsius)
try:
    t.celsius = -300.0
except ValueError as ex:
    print("   t.celsius = -300.0 -> ValueError:", ex)

print("⑤ del 은 fdel 로 간다")
del t.celsius
print("   t.celsius ->", t.celsius)

print("⑥ ★ property 는 클래스 칸에 놓여야 먹는다 — 인스턴스에 붙이면 그냥 객체다")


class Plain:
    pass


p = Plain()
p.x = property(lambda self: "인스턴스에 붙인 것")
print("   type(p.x)        :", type(p.x).__name__)
print("   p.x 가 문자열인가 :", isinstance(p.x, str))
print("   p.x.fget 을 손으로 부르면 :", p.x.fget(p))
Plain.y = property(lambda self: "클래스 칸에 놓으니 불린다")
print("   클래스 칸에 놓은 뒤 p.y  :", p.y)
print("   type(p.y)        :", type(p.y).__name__)
```
```text
===== python3 - <e33_property.py =====
① property 의 세 칸 — fget·fset·fdel
   only_getter fget:celsius  fset:None     fdel:None
   celsius     fget:celsius  fset:celsius  fdel:celsius
② ★ @celsius.setter 는 그 자리를 고치는 게 아니라 새 property 를 만든다
   only_getter is celsius : False
   둘 다 property 인가     : property property
   두 fget 이 같은 함수인가 : True
   only_getter 에 fset 이 있나 : False
③ 그래서 only_getter 쪽으로 대입하면 막힌다
   t.only_getter -> 20.0
   t.only_getter = 30.0 -> AttributeError: property 'only_getter' of 'Temp' object has no setter
④ celsius 쪽은 대입이 되고 검증도 돈다
   t.celsius -> 30.0
   t.celsius = -300.0 -> ValueError: 절대영도 아래는 못 넣는다: -300.0
⑤ del 은 fdel 로 간다
      fdel 이 불렸다
   t.celsius -> None
⑥ ★ property 는 클래스 칸에 놓여야 먹는다 — 인스턴스에 붙이면 그냥 객체다
   type(p.x)        : property
   p.x 가 문자열인가 : False
   p.x.fget 을 손으로 부르면 : 인스턴스에 붙인 것
   클래스 칸에 놓은 뒤 p.y  : 클래스 칸에 놓으니 불린다
   type(p.y)        : str
(exit 0)
```

**왜 그런가**

* ★★ **`only_getter is celsius` 가 `False`** 다. `@celsius.setter` 는 **그 자리를 고치는 게 아니라
  새 `property` 를 만들어 돌려준다.** 문서가 그렇게 적는다 — *"Returns a new property object"*.
  그 결과가 [24번](../24-decorators/2-summary.md)의 규칙대로 **이름 `celsius` 에 다시 묶인다.**
* ★ **두 `fget` 은 같은 함수다**(`is` 가 참). **함수는 물려주고 껍데기만 새로 짠 것**이다.
  그래서 `only_getter` 와 `celsius` 를 읽으면 같은 값이 나오는데 **쓰기만 갈린다**(③).
* **③의 문구가 어느 칸이 비었는지 말해 준다** — `property 'only_getter' of 'Temp' object has no setter`.
* ★★ **⑥이 둘째 과녁이다.** `type(p.x)` 가 **`property`** 이고 `type(p.y)` 가 **`str`** 이다.
  같은 물건인데 **인스턴스에 붙이면 그냥 객체**이고 **클래스 칸에 놓으면 안내원**이 된다.
  ★ 이유는 [29번](../29-classes-and-attribute-lookup/2-summary.md)의 네 층 그대로다 — 디스크립터 판정은 **MRO 를 훑어 찾은 것**에만 걸린다.
  ★ `p.x.fget(p)` 로 손으로 부르니 값이 나오는 것이 그 증거다 — **함수는 멀쩡하고 걸리는 자리가 없었을 뿐이다.**

### 3. 인스턴스 칸은 그대로인데 답이 뒤집힌다

**출력**

```python
# e33_flip.py
class Answers:
    def __get__(self, obj, objtype=None):
        return "디스크립터가 답한다"


class Holder:
    x = Answers()


h = Holder()
h.__dict__["x"] = "인스턴스 칸의 값"

print("① 지금은 비데이터 디스크립터다 — 29번의 결론대로 인스턴스 칸이 이긴다")
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   vars(h)['x']              ->", vars(h)["x"])
print("   h.x                       ->", h.x)

print("② ★ 역방향 실험 — 클래스에 __set__ 을 나중에 붙여 데이터 디스크립터로 바꾼다")
Answers.__set__ = lambda self, obj, value: obj.__dict__.__setitem__("x", value)
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   vars(h)['x']              ->", vars(h)["x"], "  <- 인스턴스 칸은 한 글자도 안 건드렸다")
print("   h.x                       ->", h.x, "  <- 우선순위가 뒤집혔다")

print("③ 떼면 그대로 돌아온다")
del Answers.__set__
print("   Answers 에 __set__ 이 있나 :", hasattr(Answers, "__set__"))
print("   h.x                       ->", h.x)

print("④ ★ __delete__ 만 붙여도 데이터 디스크립터가 된다")
Answers.__delete__ = lambda self, obj: None
print("   __set__:%s __delete__:%s" % (hasattr(Answers, "__set__"), hasattr(Answers, "__delete__")))
print("   h.x                       ->", h.x)
print("   그런데 대입은 못 한다 :", end=" ")
try:
    h.x = "새 값"
except AttributeError as ex:
    print("AttributeError:", ex)

print("⑤ 바뀐 것은 인스턴스가 아니라 「디스크립터의 타입」이다")
print("   type(Holder.__dict__['x']).__name__ :", type(Holder.__dict__["x"]).__name__)
print("   vars(h) :", vars(h))
```
```text
===== python3 - <e33_flip.py =====
① 지금은 비데이터 디스크립터다 — 29번의 결론대로 인스턴스 칸이 이긴다
   Answers 에 __set__ 이 있나 : False
   vars(h)['x']              -> 인스턴스 칸의 값
   h.x                       -> 인스턴스 칸의 값
② ★ 역방향 실험 — 클래스에 __set__ 을 나중에 붙여 데이터 디스크립터로 바꾼다
   Answers 에 __set__ 이 있나 : True
   vars(h)['x']              -> 인스턴스 칸의 값   <- 인스턴스 칸은 한 글자도 안 건드렸다
   h.x                       -> 디스크립터가 답한다   <- 우선순위가 뒤집혔다
③ 떼면 그대로 돌아온다
   Answers 에 __set__ 이 있나 : False
   h.x                       -> 인스턴스 칸의 값
④ ★ __delete__ 만 붙여도 데이터 디스크립터가 된다
   __set__:False __delete__:True
   h.x                       -> 디스크립터가 답한다
   그런데 대입은 못 한다 : AttributeError: __set__
⑤ 바뀐 것은 인스턴스가 아니라 「디스크립터의 타입」이다
   type(Holder.__dict__['x']).__name__ : Answers
   vars(h) : {'x': '인스턴스 칸의 값'}
(exit 0)
```

**왜 그런가**

* ★★★ **②에서 `vars(h)['x']` 는 한 글자도 안 변했는데 `h.x` 의 답이 바뀌었다.**
  [29번](../29-classes-and-attribute-lookup/2-summary.md)이 **두 클래스를 만들어** 잰 것을, 여기서는 **한 클래스를 두고 왕복**시켰다.
  결론은 같지만 **무엇이 원인인지가 더 좁혀진다** — 값도 아니고 클래스 칸의 물건도 아니고 **그 물건의 타입**이다.
* **③ — 떼면 그대로 돌아온다.** 되돌릴 수 있다는 것이 「타입의 성질」임을 한 번 더 못 박는다.
* ★★ **④가 판별식의 나머지 절반이다.** `__delete__` 만 붙여도 **데이터 디스크립터**가 되어 읽기는 이기는데,
  **대입은 `AttributeError: __set__`** 이다.
  ★ 즉 「데이터 디스크립터인데 쓸 수 없는」 어중간한 상태가 성립한다.
  문서의 판별식이 `__set__` **또는** `__delete__` 인 이유가 이 자리다.
* **⑤ — `type(Holder.__dict__['x']).__name__` 이 내내 `Answers` 다.** 클래스 칸의 물건도 안 바뀌었다.

★ **판정 한 줄** — **판별은 객체가 아니라 그 객체의 타입에서 한다.**

### 4. `__set_name__` 은 `class` 문이 끝나기 전에 두 번, 나중에 붙이면 0번

**출력**

```python
# e33_descriptor.py
class Traced:
    def __set_name__(self, owner, name):
        print("      __set_name__ : owner =", owner.__name__, "| name =", name)
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            print("      __get__   : 클래스에서 꺼냈다 (obj 가 None)")
            return self
        print("      __get__   : 인스턴스에서 꺼냈다")
        return obj.__dict__.get(self.name, "(아직 없음)")

    def __set__(self, obj, value):
        print("      __set__   :", repr(value))
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        print("      __delete__ 가 불렸다")
        obj.__dict__.pop(self.name, None)


print("① class 문이 끝나기 전에 __set_name__ 이 먼저 불린다")


class Box:
    a = Traced()
    b = Traced()


print("② 그 덕에 이름을 손으로 안 넘겨도 된다")
print("   Box.__dict__['a'].name :", Box.__dict__["a"].name)
print("   Box.__dict__['b'].name :", Box.__dict__["b"].name)

bx = Box()
print("③ 읽기·쓰기·지우기가 각각 다른 갈고리로 간다")
print("   bx.a ->", bx.a)
bx.a = 7
print("   vars(bx) :", vars(bx))
print("   bx.a ->", bx.a)
del bx.a
print("   vars(bx) :", vars(bx))

print("④ 클래스에서 꺼내면 obj 자리에 None 이 들어온다")
print("   type(Box.a).__name__ :", type(Box.a).__name__)

print("⑤ ★ 디스크립터 하나가 인스턴스 여럿을 상대한다 — 상태를 자기 안에 두면 새어 나간다")
p, q = Box(), Box()
p.b = "p 의 값"
q.b = "q 의 값"
print("   p.b ->", p.b)
print("   q.b ->", q.b)
print("   vars(p) :", vars(p))
print("   vars(q) :", vars(q))
print("   ★ 값은 인스턴스 칸에 넣었기 때문에 안 섞인다. 디스크립터 자신에게 넣으면 섞인다")

print("⑥ ★ __set_name__ 은 class 문이 만들 때만 불린다 — 나중에 붙이면 안 불린다")
late = Traced()
Box.c = late
print("   Box.c 를 붙인 뒤 late 에 name 이 있나 :", hasattr(late, "name"))
try:
    Box().c
except AttributeError as ex:
    print("   그래서 Box().c 를 읽으면 -> AttributeError:", ex)
```
```text
===== python3 - <e33_descriptor.py =====
① class 문이 끝나기 전에 __set_name__ 이 먼저 불린다
      __set_name__ : owner = Box | name = a
      __set_name__ : owner = Box | name = b
② 그 덕에 이름을 손으로 안 넘겨도 된다
   Box.__dict__['a'].name : a
   Box.__dict__['b'].name : b
③ 읽기·쓰기·지우기가 각각 다른 갈고리로 간다
      __get__   : 인스턴스에서 꺼냈다
   bx.a -> (아직 없음)
      __set__   : 7
   vars(bx) : {'a': 7}
      __get__   : 인스턴스에서 꺼냈다
   bx.a -> 7
      __delete__ 가 불렸다
   vars(bx) : {}
④ 클래스에서 꺼내면 obj 자리에 None 이 들어온다
      __get__   : 클래스에서 꺼냈다 (obj 가 None)
   type(Box.a).__name__ : Traced
⑤ ★ 디스크립터 하나가 인스턴스 여럿을 상대한다 — 상태를 자기 안에 두면 새어 나간다
      __set__   : 'p 의 값'
      __set__   : 'q 의 값'
      __get__   : 인스턴스에서 꺼냈다
   p.b -> p 의 값
      __get__   : 인스턴스에서 꺼냈다
   q.b -> q 의 값
   vars(p) : {'b': 'p 의 값'}
   vars(q) : {'b': 'q 의 값'}
   ★ 값은 인스턴스 칸에 넣었기 때문에 안 섞인다. 디스크립터 자신에게 넣으면 섞인다
⑥ ★ __set_name__ 은 class 문이 만들 때만 불린다 — 나중에 붙이면 안 불린다
   Box.c 를 붙인 뒤 late 에 name 이 있나 : False
      __get__   : 인스턴스에서 꺼냈다
   그래서 Box().c 를 읽으면 -> AttributeError: 'Traced' object has no attribute 'name'
(exit 0)
```

**왜 그런가**

* ★ **①에서 로그가 두 줄**이고 그것이 `② 그 덕에…` 줄보다 **먼저** 찍혔다 —
  `class Box:` 문이 **끝나기 전**에 불린 것이다. 문서가 그렇게 정한다(PEP 487, 3.6+).
  ★ 이것이 [29번](../29-classes-and-attribute-lookup/2-summary.md)이 「이 주제에서는 안 돌려 봤다」고 남겨 둔 자리이고, 여기서 돌렸다.
* **②가 그 덕을 보인다** — `Box.__dict__['a'].name` 이 `a` 다. **이름을 손으로 안 넘겨도 된다.**
* ★ **④에서 `obj` 자리에 `None` 이 온다.** 그래서 `Box.a` 가 디스크립터 **자기 자신**을 돌려줬다.
  관용구 `if obj is None: return self` 가 여기서 나온다 — 안 쓰면 `Cls.x` 가 터진다.
* ★★ **⑤가 실무의 함정이다.** 디스크립터는 클래스 칸에 **하나뿐**인데 인스턴스는 여럿이다.
  값을 `obj.__dict__` 에 넣었으므로 `p.b` 와 `q.b` 가 안 섞였다.
  ★ 자기 안에 넣었다면 **모든 인스턴스가 한 값을 나눠 쓴다**(9번 답).
* ★ **⑥ — 나중에 붙이면 `__set_name__` 이 안 불린다.** 그래서 `late` 에 `name` 이 없고,
  읽는 순간 **디스크립터 안에서** `AttributeError: 'Traced' object has no attribute 'name'` 이 난다.
  ★ **터지는 자리가 원인에서 멀다** — 붙인 줄이 아니라 읽은 줄에서 터진다.

### 5. 둘은 정의 시점에 터지고, `'__dict__'` 를 넣으면 사물함이 되살아난다

**출력**

```python
# e33_slots_edge.py
print("① __slots__ 에 적은 이름을 클래스 변수로도 쓰면")
try:
    class Conflict:
        __slots__ = ("x",)
        x = 1
except ValueError as ex:
    print("   ValueError:", ex)

print("② 둘 다 비지 않은 __slots__ 를 다중 상속하면")


class L1:
    __slots__ = ("a",)


class R1:
    __slots__ = ("b",)


try:
    class Both1(L1, R1):
        __slots__ = ()
except TypeError as ex:
    print("   TypeError:", ex)

print("③ 한쪽이 비어 있으면 된다")


class R2:
    __slots__ = ()


class Both2(L1, R2):
    __slots__ = ("c",)


o = Both2()
o.a, o.c = 1, 3
print("   Both2 인스턴스에 __dict__ 가 있나 :", hasattr(o, "__dict__"))
print("   o.a, o.c ->", o.a, o.c)

print("④ ★ __slots__ 에 '__dict__' 를 넣으면 사물함이 되살아난다")


class Hybrid:
    __slots__ = ("fixed", "__dict__")


h = Hybrid()
h.fixed = 1
h.anything = 2
print("   vars(h) :", vars(h), "  <- fixed 는 여기 없다")
print("   h.fixed ->", h.fixed, "| h.anything ->", h.anything)
print("   클래스 칸의 fixed 의 정체 :", type(Hybrid.__dict__["fixed"]).__name__)

print("⑤ 문자열 하나를 주면 글자 단위가 아니라 이름 하나다")


class OneName:
    __slots__ = "only"


n = OneName()
n.only = 5
print("   OneName.__slots__  :", repr(OneName.__slots__))
print("   클래스 칸의 이름들 :", sorted(k for k in OneName.__dict__ if not k.startswith("__")))

print("⑥ 선언한 이름이라도 넣기 전에 읽으면 없다")


class Lazy:
    __slots__ = ("v",)


z = Lazy()
try:
    z.v
except AttributeError as ex:
    print("   AttributeError:", ex)
z.v = 1
del z.v
try:
    z.v
except AttributeError as ex:
    print("   넣었다 지운 뒤에도 -> AttributeError:", ex)
```
```text
===== python3 - <e33_slots_edge.py =====
① __slots__ 에 적은 이름을 클래스 변수로도 쓰면
   ValueError: 'x' in __slots__ conflicts with class variable
② 둘 다 비지 않은 __slots__ 를 다중 상속하면
   TypeError: multiple bases have instance lay-out conflict
③ 한쪽이 비어 있으면 된다
   Both2 인스턴스에 __dict__ 가 있나 : False
   o.a, o.c -> 1 3
④ ★ __slots__ 에 '__dict__' 를 넣으면 사물함이 되살아난다
   vars(h) : {'anything': 2}   <- fixed 는 여기 없다
   h.fixed -> 1 | h.anything -> 2
   클래스 칸의 fixed 의 정체 : member_descriptor
⑤ 문자열 하나를 주면 글자 단위가 아니라 이름 하나다
   OneName.__slots__  : 'only'
   클래스 칸의 이름들 : ['only']
⑥ 선언한 이름이라도 넣기 전에 읽으면 없다
   AttributeError: 'Lazy' object has no attribute 'v'
   넣었다 지운 뒤에도 -> AttributeError: 'Lazy' object has no attribute 'v'
(exit 0)
```

**왜 그런가**

* ★ **①과 ② 둘 다 「클래스를 정의할 때」 터진다.** 인스턴스를 만들지도 않았다.
  ①은 `ValueError: 'x' in __slots__ conflicts with class variable` —
  `__slots__` 가 클래스 칸에 `x` 라는 `member_descriptor` 를 놓으려는데 **`x = 1` 이 이미 그 자리를 차지**했다.
  ②는 `TypeError: multiple bases have instance lay-out conflict` —
  두 부모가 **각자 인스턴스 칸의 자리를 정해 놓아** 겹칠 방법이 없다.
* **③ 한쪽이 비면 된다.** `__slots__ = ()` 는 자리를 안 잡으므로 충돌이 없다 — **믹스인의 관용구**가 여기서 나온다.
* ★★ **④가 가장 얄궂다.** `vars(h)` 에 **`anything` 만 있고 `fixed` 는 없다.**
  `fixed` 는 `member_descriptor` 가 든 고정 칸에 있고 `anything` 은 되살아난 `__dict__` 에 있다 —
  **한 객체가 두 저장소를 동시에 쓴다.** 아끼려던 것을 도로 내놓는 셈이라 대개는 안 쓴다.
* **⑤ 칸은 하나다.** 문자열이 이터러블이라 `o`·`n`·`l`·`y` 로 쪼개질 것 같은데 **안 그렇다** —
  언어가 문자열을 특별히 가려 받는다. 클래스 칸의 이름이 `['only']` 하나다.
* ★ **⑥ 선언한 이름이라도 넣기 전에는 `AttributeError`** 이고 **넣었다 지운 뒤에도 같다.**
  `__slots__` 의 칸은 「비어 있을 수 있는 칸」이지 「기본값이 있는 칸」이 아니다.

①의 트레이스백 전문은 이렇다.

```python
# e33_slots_conflict_tb.py
print("__slots__ 에 적은 이름을 클래스 몸통에서 또 대입한다")


class Conflict:
    __slots__ = ("x",)
    x = 1
```
```text
===== python3 - <e33_slots_conflict_tb.py =====
__slots__ 에 적은 이름을 클래스 몸통에서 또 대입한다
Traceback (most recent call last):
  File "<stdin>", line 4, in <module>
ValueError: 'x' in __slots__ conflicts with class variable
(exit 1)
```

* ★ **실행 중 예외라 소스 줄도 캐럿도 없다.** 프레임이 **하나뿐**이고 그것이 `<module>` 이다 —
  어느 메서드 안이 아니라 **`class` 문을 실행하다** 난 것이다.

### 6. 세 답이 전부 다르다 — 칸에 있는 것 · 답한 것 · 앉은 것

**출력**

```python
# e33_static_window.py
import inspect


class Normal:
    shared = "클래스 칸의 값"

    def __init__(self):
        self.own = "인스턴스 칸의 값"

    @property
    def computed(self):
        return "property 가 계산한 값"

    def method(self):
        return "메서드"


n = Normal()
n.__dict__["computed"] = "인스턴스 칸에 몰래 넣은 값"

print("① 보통 클래스에서 두 창을 견준다")
rows = ("shared", "own", "computed", "method")
for nm in rows:
    live = getattr(n, nm)
    stat = inspect.getattr_static(n, nm)
    print("   %-9s getattr -> %-28s getattr_static 의 타입 -> %s"
          % (nm, live if not callable(live) else "(메서드 객체)", type(stat).__name__))

print("② ★ computed 한 줄이 이 창의 값어치다")
print("   vars(n)['computed']          :", vars(n)["computed"])
print("   n.computed                   :", n.computed)
print("   getattr_static 이 본 것의 타입 :", type(inspect.getattr_static(n, "computed")).__name__)
print("   ★ 세 답이 전부 다르다 — 「칸에 있는 것」·「답한 것」·「거기 앉은 것」이 셋 다 다르다")

print("③ 갈고리가 있는 객체에서는 차이가 더 벌어진다")


class Ghost:
    def __getattr__(self, name):
        return "<%s 를 즉석에서 만들었다>" % name


g = Ghost()
print("   g.zzz                :", g.zzz)
print("   hasattr(g, 'zzz')    :", hasattr(g, "zzz"))
try:
    inspect.getattr_static(g, "zzz")
except AttributeError as ex:
    print("   getattr_static(g,'zzz') -> AttributeError:", ex)
print("   ★ 29번이 「제5의 상태」라 부른 자리를 이 창은 없다고 답한다")
```
```text
===== python3 - <e33_static_window.py =====
① 보통 클래스에서 두 창을 견준다
   shared    getattr -> 클래스 칸의 값                     getattr_static 의 타입 -> str
   own       getattr -> 인스턴스 칸의 값                    getattr_static 의 타입 -> str
   computed  getattr -> property 가 계산한 값             getattr_static 의 타입 -> property
   method    getattr -> (메서드 객체)                     getattr_static 의 타입 -> function
② ★ computed 한 줄이 이 창의 값어치다
   vars(n)['computed']          : 인스턴스 칸에 몰래 넣은 값
   n.computed                   : property 가 계산한 값
   getattr_static 이 본 것의 타입 : property
   ★ 세 답이 전부 다르다 — 「칸에 있는 것」·「답한 것」·「거기 앉은 것」이 셋 다 다르다
③ 갈고리가 있는 객체에서는 차이가 더 벌어진다
   g.zzz                : <zzz 를 즉석에서 만들었다>
   hasattr(g, 'zzz')    : True
   getattr_static(g,'zzz') -> AttributeError: zzz
   ★ 29번이 「제5의 상태」라 부른 자리를 이 창은 없다고 답한다
(exit 0)
```

**왜 그런가**

* ★★★ **②의 세 줄이 이 창의 값어치다.**
  `vars(n)['computed']` 는 **인스턴스 칸에 몰래 넣은 값**,
  `n.computed` 는 **`property` 가 계산한 값**,
  `getattr_static` 은 **`property` 객체 그 자체**다.
  ★ 앞의 둘이 갈리는 것은 [29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 7의 결론(데이터 디스크립터가 인스턴스 칸을 이긴다)이고,
  **세 번째가 이 주제가 더한 것**이다.
* ★★ **③에서 답이 갈리는 이유**는 두 함수가 **다른 길을 가기** 때문이다.
  `hasattr` 는 **실제로 접근해 보고**(그래서 `__getattr__` 이 걸려 `True`),
  `getattr_static` 은 **칸만 들여다본다**(그래서 `AttributeError`).
  ★ [29번](../29-classes-and-attribute-lookup/2-summary.md)이 「**제5의 상태**」라 부른 자리 —
  세 창이 전부 「없음」인데 값이 나오는 그 자리를 **이 창은 「없다」로 정확히 답한다.**
* ★ 그래서 이 창의 쓸모는 하나다 — **「읽었는데 코드가 돌았다」를 피하는 것.**
  `property` 안에 DB 조회가 있으면 평범한 `getattr` 한 줄이 조회를 돌린다.
  ★ 대신 **이 창은 값을 모른다** — 계산값이 필요하면 결국 안내원을 불러야 한다.

### 7. 디스크립터 판정이 「MRO 를 훑어 찾은 것」에만 걸리기 때문이다

**왜 그런가**

* 문서가 우선순위를 한 문장으로 적는다 — *"data descriptors take precedence over instance dictionaries,
  instance dictionaries take precedence over non-data descriptors,
  and non-data descriptors take precedence over class variables."*
  ★ **이 문장의 주어는 전부 클래스 쪽에서 찾은 것**이다. 인스턴스 칸의 물건은 **값으로만** 쓰인다.
* 그래서 `p.x = property(...)` 는 **그냥 값을 넣은 것**이고, `p.x` 를 읽으면 그 값이 그대로 나온다 —
  **`property` 객체 자체**다(2번 답의 ⑥).
* ★ **`p.x.fget(p)` 로 손으로 부르니 값이 나오는 것**이 결정적이다.
  함수도 멀쩡하고 `property` 도 멀쩡하다 — **걸리는 자리가 없었을 뿐**이다.
  「객체가 망가졌나」와 「프로토콜이 안 걸렸나」를 가르는 한 줄이다.
* ★ 같은 규칙의 다른 얼굴이 [32번](../32-container-protocol/2-summary.md)의 「특수 메서드는 타입에서 찾는다」이고,
  [29번](../29-classes-and-attribute-lookup/2-summary.md) 「어디서 틀리나 (11)」이 그 대비를 적어 둔 자리다.

### 8. `__set__` **또는** `__delete__` — 두 가지를 대야 답이 완성된다

**왜 그런가**

* 문서의 판별식은 **둘 중 하나**다. `__set__` 만 외우면 절반이다.
* ★ **하나만 있으면 어중간한 상태가 된다**(3번 답의 ④) —
  `__delete__` 만 있으면 **읽기는 인스턴스 칸을 이기는데 대입은 `AttributeError: __set__`** 이다.
  ★ 즉 「데이터 디스크립터」는 **「인스턴스 칸을 이긴다」는 자격**이지 「쓸 수 있다」는 뜻이 아니다.
* ★★ **판별은 타입에서 한다.** 3번의 실험이 그것을 직접 보였다 —
  `Answers.__set__ = ...` 로 **클래스에 붙이자** 뒤집혔고, 인스턴스는 한 글자도 안 건드렸다.
  ★ 실무에서는 몽키 패치가 이 자리를 건드릴 수 있다는 뜻이다.

### 9. 디스크립터는 클래스 칸에 하나뿐이라 인스턴스끼리 새어 나간다

**왜 그런가**

* 클래스 칸의 `Logged()` 는 **객체 하나**다. 인스턴스가 천 개여도 그 하나가 천 번 불린다.
  `self.value = v` 로 두면 **마지막에 쓴 값이 앞의 것을 덮는다.**
* ★★ **[29번](../29-classes-and-attribute-lookup/2-summary.md) 동작 3의 「클래스 변수 공유」와 같은 집안**이다 —
  클래스 몸통의 `items = []` 가 하나뿐인 것과 **정확히 같은 구조**다.
* ★★ 그리고 [20번](../20-mutable-default-args/2-summary.md)의 **가변 기본 인자와도 같은 집안**이다.
  셋 다 「**한 번만 만들어진 물건을 여럿이 나눠 쓴다**」이고, 처방도 셋 다 같다 —
  **만드는 시점·두는 자리를 인스턴스 쪽으로 옮긴다.**
* 이 주제의 처방은 `obj.__dict__[self.name] = value` 이고,
  그 `self.name` 을 채워 주는 것이 **`__set_name__`**(4번 답)이다. 두 장치가 짝이다.

### 10. 창이 얕아서다 — 근거는 「어느 쪽이 작나」 하나뿐이고, 속도는 한 번도 안 쟀다

**출력**

```python
# e33_slots_size.py
import sys


class WithDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class WithSlots:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


a = WithDict(1, 2)
b = WithSlots(1, 2)

print("① getsizeof 는 얕다 — 인스턴스 껍데기만 잰다")
print("   getsizeof(WithDict 인스턴스)  :", sys.getsizeof(a))
print("   getsizeof(WithSlots 인스턴스) :", sys.getsizeof(b))
print("   ★ 두 값이 같다 — 여기까지만 보면 아낀 것이 없어 보인다")

print("② dict 판은 옆에 __dict__ 가 따로 달려 있다")
print("   getsizeof(a.__dict__)         :", sys.getsizeof(a.__dict__))
print("   slots 판에 __dict__ 가 있나    :", hasattr(b, "__dict__"))

print("③ 그래서 합쳐 세야 한다")
tot_d = sys.getsizeof(a) + sys.getsizeof(a.__dict__)
tot_s = sys.getsizeof(b)
print("   dict 판 합계  :", tot_d)
print("   slots 판 합계 :", tot_s)
print("   어느 쪽이 작나 :", "slots" if tot_s < tot_d else "dict")
print("   정수 몫       :", tot_d // tot_s)

print("④ 칸이 늘면 어떻게 되나 — 여덟 칸짜리로 다시")
names = tuple("abcdefgh")
Big = type("Big", (), {})
BigSlots = type("BigSlots", (), {"__slots__": names})
big = Big()
bigs = BigSlots()
for i, nm in enumerate(names):
    setattr(big, nm, i)
    setattr(bigs, nm, i)
print("   dict 판 합계  :", sys.getsizeof(big) + sys.getsizeof(big.__dict__))
print("   slots 판 합계 :", sys.getsizeof(bigs))

print("⑤ 잰 것과 안 잰 것")
print("   잰 것   : 위 수치 — 이 판·이 머신의 바이트 수")
print("   안 잰 것 : 속도. 이 문서는 __slots__ 가 빠른지 느린지 한 번도 안 쟀다")
```
```text
===== python3 - <e33_slots_size.py =====
① getsizeof 는 얕다 — 인스턴스 껍데기만 잰다
   getsizeof(WithDict 인스턴스)  : 48
   getsizeof(WithSlots 인스턴스) : 48
   ★ 두 값이 같다 — 여기까지만 보면 아낀 것이 없어 보인다
② dict 판은 옆에 __dict__ 가 따로 달려 있다
   getsizeof(a.__dict__)         : 296
   slots 판에 __dict__ 가 있나    : False
③ 그래서 합쳐 세야 한다
   dict 판 합계  : 344
   slots 판 합계 : 48
   어느 쪽이 작나 : slots
   정수 몫       : 7
④ 칸이 늘면 어떻게 되나 — 여덟 칸짜리로 다시
   dict 판 합계  : 344
   slots 판 합계 : 96
⑤ 잰 것과 안 잰 것
   잰 것   : 위 수치 — 이 판·이 머신의 바이트 수
   안 잰 것 : 속도. 이 문서는 __slots__ 가 빠른지 느린지 한 번도 안 쟀다
(exit 0)
```

**왜 그런가**

* ★★ **①이 함정이다.** 두 인스턴스의 `getsizeof` 가 **같게** 나온다.
  `getsizeof` 는 **얕아서** 그 객체 자신의 바이트 수만 재고 **가리키는 곳은 안 따라간다.**
  ★ 여기서 멈추면 **「아낀 것이 없다」는 정반대 결론**이 나온다.
* **②가 이유다.** `dict` 판은 `__dict__` 가 **옆에 따로 달려 있고** `slots` 판에는 그것이 없다.
* ★★★ **③이 답이다. 그런데 근거로 쓰는 것은 「어느 쪽이 작나」 한 줄뿐이다.**
  바이트 수도 정수 몫도 **판·빌드·플랫폼이 바꾼다.** 머리말의 「흔들리는 칸」 표가 그것을 미리 선언한 자리다.
* ★ **④에서 칸을 여덟으로 늘려도 대소 관계가 유지된다.**
  ★ 다만 `dict` 판 합계가 두 경우에 **같은 수**로 나왔는데, 이것은 `dict` 용량이 계단식이라 그런 것이고
  **성질이 아니라 이 판의 관찰**이다.
* ★★★ **⑤가 이 문서의 규칙을 스스로 선언한다 — 속도는 한 번도 안 쟀다.**
  그래서 이 주제 어디에도 「`__slots__` 가 빠르다」는 문장이 없다.
  ★ 「부적용인 창」에 적어 둔 그대로다 — **잴 창을 열지 않기로 한 것**이지 재 보고 같았던 것이 아니다.

**그래서 이렇게 적으면 틀린다**

* ✗ 「`__slots__` 는 메모리를 7배 아낀다」 → ○ **이 판에서 이 두 클래스의 합계**가 그랬을 뿐이다.
* ✗ 「`getsizeof` 로 견주면 차이가 보인다」 → ○ **같게 나온다.** `__dict__` 를 따로 세야 한다.
* ✗ 「`__slots__` 는 빠르다」 → ○ **안 쟀다.**

### 11. 우선순위는 보장, 절감은 구현, 이름은 구현이고 성질은 보장

**왜 그런가**

| 사실 | 층 | 근거 |
|---|---|---|
| 데이터 디스크립터 > 인스턴스 칸 > 비데이터 > 클래스 변수 | **언어 보장** | 3.3.2.3 Invoking Descriptors 의 한 문장 |
| `property` 가 세 칸을 갖고 빈 칸이면 `AttributeError` | **언어 보장** | `property` 문서 |
| `__slots__` 가 `__dict__` 를 없앤다 | **언어 보장** | 3.3.2.4 |
| 클래스 변수와 충돌하면 `ValueError` | **언어 보장** | 3.3.2.4 — *"raise ValueError"* |
| ★★★ **얼마나 아끼는가** | **CPython 구현** | 문서에 수치가 **없다.** `getsizeof` 로 잰 것이다 |
| `getsizeof` 가 얕은 것 | **CPython 구현** | 실행 |
| `member_descriptor` 라는 **이름** | **CPython 구현** | 내부 타입 이름 |
| 그것이 **데이터 디스크립터라는 성질** | **언어 보장** | 3.3.2.4 가 정한 동작에서 따라온다 |
| 예외 **문구** 전부 | **이 판의 관찰** | 종류는 명세, 문구는 아니다 |

★★ **이름과 성질이 다른 층이라는 것**이 이 문항의 과녁이다.
`member_descriptor` 가 `slot_descriptor` 로 바뀌어도 **인스턴스 칸을 이긴다는 사실은 안 바뀐다.**

### 12. 29 는 「어느 칸에서 나오나」, 33 은 「그 칸에 무엇을 앉히나」

**왜 그런가**

* ★ **경계 한 줄씩** —
  [29번](../29-classes-and-attribute-lookup/2-summary.md)은 **탐색의 순서와 우선순위**가 정본이다(네 층·`__getattr__`·`__slots__` 의 기본 동작·상속에서 풀리는 것).
  **33번은 그 칸에 앉히는 세 가지 방법**이 정본이다(`property` 의 세 칸·디스크립터 네 갈고리·`__slots__` 의 경계·`getattr_static`).
* ★★ **`cached_property` 가 두 번째에 안 계산되는 이유**는 네 층으로 바로 읽힌다 —
  그것이 **비데이터 디스크립터**라서, 첫 접근 때 인스턴스 칸에 값을 넣고 나면
  **그 다음부터는 인스턴스 칸이 이긴다.** 「더 들어가면」의 ①이 그 실측이고 로그가 한 번만 찍혔다.
  ★ 그래서 **`__slots__` 인 클래스에는 못 쓴다** — 넣을 칸이 없어 `TypeError` 다(같은 블록의 ②).
* ★ **`@dataclass(slots=True)`**(3.10+)는 이 주제의 `__slots__` 선언을 **대신 써 준다.**
  ★ 다만 그 옵션은 **새 클래스를 만들어 돌려주므로** 성질이 하나 더 붙는다 — 정본은 [36번](../36-dataclasses/2-summary.md) 다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 세 장치를 한 클래스에 얹은 호출 로그 | `python3 - <e33_three.py` | 2(캡처 + 재대조) | 셋 다 데이터 디스크립터 · `member_descriptor` 만 조용함 |
| `property` 의 세 칸과 새 객체 | `python3 - <e33_property.py` | 2 | `is` 가 거짓 · `fget` 은 같은 함수 |
| 데이터/비데이터 우선순위 왕복 | `python3 - <e33_flip.py` | 2 | `__set__` 붙였다 떼자 답이 왕복 · `__delete__` 만도 데이터 |
| 디스크립터 네 갈고리 + `__set_name__` | `python3 - <e33_descriptor.py` | 2 | `class` 문 끝나기 전 2회 호출 · 나중에 붙이면 0회 |
| `__slots__` 경계 여섯 | `python3 - <e33_slots_edge.py` | 2 | `ValueError`·`TypeError` 는 **정의 시점** |
| `__slots__` 충돌 트레이스백 전문 | `python3 - <e33_slots_conflict_tb.py` | 2 | 프레임 1개 · `(exit 1)` |
| `getsizeof` 로 크기 비교 | `python3 - <e33_slots_size.py` | 2 | 두 판 모두 `slots` 쪽이 작음. **수치는 근거로 안 씀** |
| `getattr_static` 의 세 답 | `python3 - <e33_static_window.py` | 2 | 로그 0줄 · `__getattr__` 자리에 `AttributeError` |
| `cached_property`·내장 디스크립터·`__weakref__` | `python3 - <e33_more.py` | 2 | `member_descriptor` 와 `getset_descriptor` 가 **갈림** |
| 판 확인 | `python3 - <e33_version.py` | 2 | 3.12.3 · cpython · linux |

**구현 의존 항목** — 판이 오르면 다시 돌려야 하는 것.

| 항목 | 왜 |
|---|---|
| ★★★ `getsizeof` 의 **바이트 수 전부** | 문서에 수치가 없다. **대소 관계만** 근거다 |
| 칸을 늘려도 `dict` 판 합계가 안 변한 것 | `dict` 용량이 계단식이라 그렇다. 성질이 아니다 |
| `member_descriptor`·`getset_descriptor` 라는 **이름** | 내부 타입 이름. **성질**은 안 흔들린다 |
| `multiple bases have instance lay-out conflict` 문구 | 종류는 명세, 문구는 아니다 |
| `No '__dict__' attribute on … to cache …` 문구 | `functools` 구현의 문구다 |
| `__slots__ = "only"` 가 이름 하나가 되는 것 | 문서는 「문자열도 받는다」까지만 적는다 |

★ **안 흔들리는 칸** — 어느 갈고리가 **불렸나 안 불렸나**, 호출 **순서**,
`fget`/`fset`/`fdel` 이 **찼나 비었나**, `vars()` 의 **내용**, 예외 **종류**,
`File "<stdin>", line N`, `(exit N)`, 그리고 **크기의 대소 관계**.
★★ **이 주제가 한 번도 안 잰 것** — **속도.** 그래서 이 문서에는 성능 주장이 한 줄도 없다.
