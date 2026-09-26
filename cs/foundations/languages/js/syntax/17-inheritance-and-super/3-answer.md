# js/syntax/17 — 상속과 `super`: 「`super` 는 정의된 자리를 기억하고, `this` 는 부른 자리를 따른다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스는 한 줄도 없다. 모든 블록은 표준 출력뿐이다.
> ★★★ **이 주제의 블록은 두 판에서 전부 identical** 이다(11번의 대조기 출력).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js16b-17a-two-chains.js     -> 1번
// js16b-17b-super-call.js     -> 2번
// js16b-17c-homeobject.js     -> 3번
// js16b-17e-ctor-virtual.js   -> 4번
// js16b-17d-builtins.js       -> 5번
// js16b-17f-super-edges.js    -> 6번
// js16b-vdiff.sh              -> 11번
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 두 사슬 — **인스턴스 쪽은 `B.prototype → A.prototype`, 생성자 쪽은 `B → A`** ★★

**출력**

```text
===== node20 js16b-17a-two-chains.js (exit=0) =====
[1] the instance side
  new B() -> B.prototype -> A.prototype -> Object.prototype -> null
[2] the constructor side
  B -> A -> Function.prototype -> Object.prototype -> null
  Plain -> Function.prototype -> Object.prototype -> null   <- a class without extends

[3] a static method defined on A, called through B
  B.create()                 -> A.create called on B
  Object.hasOwn(B, 'create') -> false
  b.hello()                  -> A.hello   own? false

[4] the same two links, written by hand for old-style functions
  only the instance link:      Object.getPrototypeOf(OldB) === OldA ? false
  after setPrototypeOf(OldB, OldA):                    === OldA ? true

[5] extends null
  chain of N.prototype       N.prototype -> null
  Object.getPrototypeOf(N) === Function.prototype ? true
  new N()  -> TypeError Super constructor null of N is not a constructor
  new N2() with `return Object.create(N2.prototype)` -> instanceof N2 true, has toString? false
```

**왜 그런가**

- ★★★ **`B` 의 윗집이 `A` 자신이다** — 명세가 `ClassDefinitionEvaluation` 에서 *"Let ctorParent be superclass."* 로 생성자의 윗집을 정한다.
  그래서 `B.create()` 는 **빌려 본 정적 메서드**(`hasOwn` 이 `false`)이고, 그 안의 `this` 는 수신자 `B` 라 `A.create called on B` 다.
- ★ `Plain` 은 `extends` 가 없어 곧장 `Function.prototype` 이다.
- ★★ **`[4]` 는 `false` 다음 `true`** — 옛 방식은 인스턴스 쪽 링크만 걸면 생성자 쪽은 **안 이어진다.** 두 번째 `setPrototypeOf` 가 필요하다.
- ★★★ **`[5]`** — `N.prototype -> null` · `N` 의 윗집은 `Function.prototype`(명세 *"Let protoParent be null. Let ctorParent be %Function.prototype%."*) ·
  `new N()` 은 `TypeError Super constructor null of N is not a constructor`. 파생이라 암묵 생성자가 생성자 쪽 윗집(`Function.prototype`)을 부르려 하는데 그것이 생성자가 아니다.
  ★ **문구의 `null` 과 사슬의 `Function.prototype` 이 다르다** — 문구는 V8 의 것이다.
  `N2` 는 객체를 직접 반환해 `instanceof N2 true`, **`has toString? false`** — `Object.prototype` 이 사슬에 없다.

### 2. `super()` 규칙 — **전에 쓰면·안 부르면 `ReferenceError`, 두 번이면 다른 `ReferenceError`, 원시 반환은 `TypeError`** ★★★

**출력**

```text
===== node20 js16b-17b-super-call.js (exit=0) =====
[1] this before super()
this.early = 1; super(1)                            -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor
an arrow reads this before super()                  -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor

[2] never calling super()
constructor() {}                                    -> ReferenceError Must call super constructor in derived class before accessing 'this' or returning from derived constructor
constructor() { return { replaced: true } }         -> {"replaced":true}
  ...is it an instance of the class?                -> false
constructor() { return 7 }                          -> TypeError Derived constructors may only return object or undefined
super(1); return 7                                  -> TypeError Derived constructors may only return object or undefined
base class: this.a = 1; return 7                    -> {"a":1}

[3] calling super() twice
super(1); super(2)                                  -> ReferenceError Super constructor may only be called once

[4] the implicit constructor forwards every argument
new Implicit(42).v                                  -> 42
Implicit.length                                     -> 0

[5] new.target -- which class did `new` name?
new Shape()                                         -> TypeError Shape is abstract
new Circle().kind                                   -> Circle
Legacy()                                            -> called without new
new Legacy()  (returns an object, not the string)   -> object
```

**왜 그런가**

- ★★★ **같은 문구가 세 줄**이다 — `this.early = 1; super(1)` · 화살표로 읽기 · `constructor() {}`.
  문구 `Must call super constructor in derived class before accessing 'this' or returning from derived constructor` 의 **앞 절이 앞 두 줄, 뒷 절이 셋째 줄**이다.
  ★ 화살표는 둘러싼 생성자의 `this` 를 쓰므로(07번) **우회가 안 된다.**
- ★★ **두 번은 다른 문구다** — `Super constructor may only be called once`. 종류는 같은 `ReferenceError` 다.
- ★★★ **원시 반환은 `super()` 뒤여도 `TypeError`**(`Derived constructors may only return object or undefined`) — **같은 결과**다.
  ★ **기반 클래스는 원시 반환을 무시해** `{"a":1}` 이다. 객체 반환은 `super()` 없이도 되지만 **`instanceof` 가 `false`** 다.
- ★ `[4]` — `42` 와 `0`. 암묵 생성자는 명세 NOTE 대로 `constructor(...args) { super(...args); }` 처럼 굴지만 **선언된 매개변수가 없어 `length` 가 0** 이다.
- ★★ `[5]` — `TypeError Shape is abstract`(우리가 던진 문구) · `Circle` · `called without new` · `object`.
  **`new.target` 은 부모 생성자 안에서도 `new` 에 적힌 자식**이다. `new Legacy()` 는 기반 생성자가 원시 반환(문자열)을 무시해 객체다.

### 3. 떼어 붙인 메서드 — **`this` 는 부른 자리, `super` 는 정의된 자리의 윗집** ★★★

**출력**

```text
===== node20 js16b-17c-homeobject.js (exit=0) =====
[1] detach Dog's method and attach it to an object whose parent is Robot
  dog.describe()                 this=dog  super.who()=Animal.who
  toaster.describe()             this=toaster  super.who()=Animal.who
  Dog.prototype.describe.call({name:'plain'})  this=plain  super.who()=Animal.who
  toaster.who()  (its own chain) Robot.who

[2] the same with object literals
  o1.m()   this=o1  super.who()=P1.who
  o2.m()   this=o2  super.who()=P1.who
  Object.setPrototypeOf(o2, null) and call again  this=o2  super.who()=P1.who

[3] change the prototype of the object the method was written in
  after setPrototypeOf(o1, P2):  o2.m()  this=o2  super.who()=P2.who

[4] trap log -- whom does super.who() ask, and with which receiver?
  home.m()   ["get(who) receiver=home"]
  guest.m()  ["get(who) receiver=guest"]

[5] super.x = v -- where does the value land?
  own x on kid?  true   kid.x written via super   parent.x parent's x

[6] super in three function forms
  return { m() { return super.toString; } }               -> compiles
  return { m: function () { return super.toString; } }    -> SyntaxError 'super' keyword unexpected here
  return { m: () => super.toString }                      -> SyntaxError 'super' keyword unexpected here
```

**왜 그런가**

- ★★★ **`[1]` — `super.who()` 는 네 줄 모두 `Animal.who`** 인데 `this` 는 `dog`·`toaster`·`plain` 으로 바뀐다. `toaster` 자신의 사슬은 `Robot.who` 다.
  **07번의 `assigned to another object -> "hi lee"` 와 정확히 반대편**이다 — `this` 는 따라가고 `super` 는 남는다.
- ★★ **`[2]`** — 세 줄 모두 `P1.who`. **`o2` 의 윗집을 끊어도** 같다 — `super` 는 `o2` 를 안 본다.
- ★★★ **`[3]` — `P2.who`**. 고정된 것은 HomeObject(`o1`)이고, 그 **윗집은 부를 때 읽는다.**
- ★★★ **`[4]`** — `["get(who) receiver=home"]` 과 `["get(who) receiver=guest"]`. **질문 상대(`tapped`)와 질문 수(1)는 같고 receiver 만 다르다.**
  `guest` 는 `tapped` 와 사슬 관계가 **전혀 없는데도** 그 트랩이 불렸다 — 출발 칸을 정한 것이 `guest` 가 아니라 **`m` 의 도장**이라는 증거다.
- ★★ **`[5]`** — `own x on kid?  true`, `parent.x` 는 `parent's x` 그대로. `super.x = v` 는 **수신자 `this`** 에 쓴다.
- ★★ **`[6]`** — 첫 줄만 `compiles`. `function` 식과 둘러싼 메서드 없는 화살표는 `SyntaxError 'super' keyword unexpected here` 다.
  명세는 메서드 정의에서만 `MakeMethod(closure, obj)` 로 도장을 찍는다.

### 4. 부모 생성자 속 가상 호출 — **자식 메서드가 불리지만 자식 필드는 아직 없고, 넣은 값은 덮인다** ★★★

**출력**

```text
===== node20 js16b-17e-ctor-virtual.js (exit=0) =====
[1] the log
   1. Widget constructor calls this.describe()
   2.   -> Button.describe sees label=undefined (own? false)
   3. Widget constructor calls this.init()
   4.   Button.init set count=99, note='set by init'
   5. Button constructor after super(): label=OK count=0 note=undefined

[2] the same, with a #private field
   1. Widget constructor calls this.describe()
   2.   -> PrivButton.describe  #label in this=false  TypeError Cannot read private member #label from an object whose class did not declare it
   3. Widget constructor calls this.init()
  after construction: pb.describe()  PrivButton.describe  #label in this=true  value=OK
```

**왜 그런가**

- ★★★ **2번 줄 `label=undefined (own? false)`** — 디스패치는 이미 자식(`Button.describe`)인데 **자식 필드는 칸조차 없다.**
  16번이 찍은 순서대로 **자식 필드 초기자는 `super()` 가 돌아온 뒤** 돈다.
- ★★★ **5번 줄 `count=0 note=undefined`** — 4번에서 `init()` 이 넣은 `99` 와 `'set by init'` 을 **필드 초기자가 덮었다.**
  초기자 없는 `note;` 도 `undefined` 로 덮는다 — 공개 필드는 `DefineField` 가 **정의**(`CreateDataPropertyOrThrow`)로 놓기 때문이다.
- ★★★ **`[2]` — `#label in this=false`**, 읽으면 `TypeError Cannot read private member #label from an object whose class did not declare it`.
  ★ **값 창이 닫혀 브랜드 검사로 바꿔 물은 자리**다. 문구는 「선언 안 했다」고 말하지만 **선언은 했고 아직 설치 전**이다 — 문구를 근거로 쓰지 않는다.
  생성이 끝나면 `#label in this=true  value=OK`.
- ★ `[2]` 에 `init` 로그 줄이 없는 것은 `PrivButton` 이 `init` 을 덮어쓰지 않아 `Widget.init`(빈 함수)이 불렸기 때문이다.

### 5. 내장 상속 — **`class` 는 진짜 내장 객체를, 옛 방식은 `instanceof` 만 속이는 가짜를 만든다** ★★★

**출력**

```text
===== node20 js16b-17d-builtins.js (exit=0) =====
[1] extends Array
s.length after push(1,2) and s[5] = 9               6
after s.length = 1 -> JSON                          [1]
tag / Array.isArray / instanceof Stack              [object Array] / true / true
s.top()                                             1

[2] what do map / filter / slice / spread build?
Stack.from([1,2,3]) constructor                     Stack
t.map(x => x * 2) constructor                       Stack
t.filter(x => x > 1) constructor                    Stack
t.slice(1) constructor                              Stack
[...t] constructor                                  Array
Stack[Symbol.species] === Stack                     true
species -> Array : u.map(...) constructor           Array
                   u itself                         PlainResults

[3] the old way -- Array.call(this)
o.length after push(1,2) and o[5] = 9               2
tag / Array.isArray / instanceof Array              [object Object] / false / true

[4] extends Error
e1.name / e1.constructor.name                       Error / ValidationError
String(e1)                                          Error: bad input
e1.stack first line                                 Error: bad input
tag / instanceof Error / instanceof ValidationError [object Error] / true / true
with this.name set: String(e2)                      NamedError: bad input
                    e2.stack first line             NamedError: bad input
                    e2.cause === e1                 true
own keys of e2                                      ["stack","message","cause","name"]
name on the prototype: stack first line             ProtoNamed: x
old way: e3.message / tag                           "" / [object Object]
old way: has own stack?                             false

[5] extends Map
tag / size / get('k')                               [object Map] / 1 / 1
```

**왜 그런가**

- ★★★ **`[1]`** — `6` · `[1]` · `[object Array] / true / true`. `Array` 생성자가 `super()` 로 **진짜 배열을** 만들었다.
- ★★ **`[2]`** — `from`·`map`·`filter`·`slice` 넷이 `Stack`, **`[...t]` 만 `Array`** 다. `Stack[Symbol.species] === Stack` 이 `true` 이고,
  species 를 `Array` 로 돌리면 `u.map(...)` 이 `Array`, `u` 자신은 `PlainResults` 다.
- ★★★ **`[3]`** — `length` `2` · `[object Object] / false / true`. **`instanceof Array` 만 `true`** 다 — 사슬에 `Array.prototype` 이 있을 뿐 배열이 아니다.
  ★ 브랜드가 이 판정의 창이다.
- ★★★ **`[4]`** — `e1.name` 은 **`Error`**(`constructor.name` 만 `ValidationError`) · `String(e1)` 은 `Error: bad input` ·
  `this.name` 을 단 `e2` 는 `NamedError: bad input` · own 키 `["stack","message","cause","name"]` · 옛 방식 `e3.message` 는 **`""`** 에 브랜드 `[object Object]`.
  ★★ **`stack` 은 ECMA-262 에 없다** — own 키의 `stack` 과 `stack first line` 줄들은 **엔진 칸**이다.
- ★ `[5]` — `[object Map] / 1 / 1`.

### 6. 메서드 안의 화살표 · 정적 `super` — **화살표는 둘러싼 메서드의 도장을, 정적 메서드는 클래스를 도장으로 쓴다** ★★

**출력**

```text
===== node20 js16b-17f-super-edges.js (exit=0) =====
[1] an arrow inside a method
  d.who()       Dog.who
  d.viaArrow()  Animal.who
  detached, called on {}  Animal.who

[2] super inside a static method
  Dog.kind()    Dog.kind -> Animal.kind on Dog
  Object.getPrototypeOf(Dog) === Animal ? true
```

**왜 그런가**

- ★★ **`d.viaArrow()` 는 `Animal.who`**, 떼어서 `{}` 에 대고 불러도 **같은 `Animal.who`** 다. 화살표는 스스로 도장이 없지만
  명세 문장대로 *"the necessary state to implement super is accessible via the envRecord that is captured by the function object of the ArrowFunction."* — 둘러싼 메서드의 것을 쓴다.
- ★★ **`Dog.kind()` 는 `Dog.kind -> Animal.kind on Dog`** — 정적 메서드의 도장은 `Dog` 이고 그 윗집이 `Animal`(둘째 줄 `true`)이다.
  `Animal.kind` 안의 `this.name` 은 **`Dog`** — `super` 는 출발 칸만 바꾸고 수신자는 `this` 로 넘긴다(3번 `[4]` 와 같은 규칙).

### 7. 파생 클래스에서는 부모가 객체를 만든다 — **세 현상의 공통 원인이다** ★★★

- ★★★ **`super()` 전의 `ReferenceError`** — 객체가 **아직 만들어지지 않았으니** 가리킬 `this` 가 없다.
  명세의 기본 생성자가 파생이면 *"Let result be ? Construct(func, args, NewTarget)."* 로 부모에게 만들게 한다.
- ★★★ **`extends Array` 가 진짜 배열인 것** — 만든 쪽이 **`Array` 생성자**다. 배열의 이그조틱 동작은 만들 때 정해진다.
- ★★★ **옛 `Array.call(this)` 의 실패** — `new OldStack()` 이 **먼저 평범한 객체를 만든 뒤** `Array` 를 함수로 부른다. 이미 만들어진 객체는 배열로 바뀌지 않는다
  (`length` `2`, 브랜드 `[object Object]`).
- ★★ **윗집이 자식의 `prototype` 인 것은 `new.target` 덕**이다 — 부모는 `NewTarget`(= 자식 클래스)을 받아 그 `prototype` 을 윗집으로 쓴다.
  기반 쪽 단계가 *"OrdinaryCreateFromConstructor(NewTarget, ...)"* 인 것이 그 흔적이고, 그래서 4번에서 부모 생성자 안의 디스패치가 이미 자식이었다.
- ★ **원시 반환** — 기반 생성자는 **자기가 만든 `this`** 가 있어 원시 반환을 무시하고 그것을 돌려주면 된다.
  파생 생성자가 원시값을 반환하면 **돌려줄 객체가 무엇인지** 정할 수 없다 — 그래서 `TypeError` 다(`super()` 뒤여도).
  ★ 이 마지막 문장은 **해석**이다. 사실로 확인한 것은 두 출력(`{"a":1}` 과 `TypeError`)이다.

### 8. HomeObject 고정 · 윗집 동적 — **정할 때 집, 부를 때 윗집** ★★★

- ★★★ **정의할 때** — 메서드가 적힌 객체(HomeObject). `MakeMethod(closure, obj)` 가 찍는다. **이후 바뀌지 않는다**(3번 `[1]`·`[2]`).
  **부를 때** — ① 그 HomeObject 의 **현재 윗집**(3번 `[3]` 의 `P2.who`) ② 수신자 **`this`**(3번 `[4]` 의 `receiver=guest`).
- ★★ **`receiver` 가 15번의 「탐색은 체인을 타고, 값은 수신자에 떨어진다」를 다시 보인다.** `super` 는 **탐색의 출발 칸**만 바꾼 조회이고,
  부모 쪽이 getter/setter 였다면 그 안의 `this` 도 수신자다(15번의 「체인 위 setter 의 `this` 는 수신자」).
- ★ **그렇다** — `super.x = v` 가 `kid` 에 own 을 만든 것(3번 `[5]`)은 **쓰기가 수신자에 내려앉는다**의 `super` 판이다.

### 9. C# 12번과 정반대 — **C# 은 파생 초기자가 먼저, JS 는 `super()` 뒤** ★★★

| | C# (12번 4번 문항 `cs12b-virtual.cs`) | JS (4번 문항) | C++ (C# 12번의 대조) |
|---|---|---|---|
| 불리는 메서드 | 자식 것 | 자식 것 | **부모 것** |
| 자식 필드 초기자 값 | ★ **보인다**(`FromInitializer=「필드 초기자가 넣은 값」`) | ★★★ **안 보인다**(`label=undefined (own? false)`) | 안 본다 |
| 자식 생성자 본문 값 | 안 보인다(`FromBody=「null」`) | 안 보인다 | 안 본다 |

- ★★★ **C# 은 파생 필드 초기자가 기반 생성자보다 먼저** 돌고(12번 1번 문항), **JS 는 `super()` 가 돌아온 뒤** 돈다(16번의 순서 로그).
- ★★ **JS 에만 있는 두 번째 사고** — 부모 생성자가 부른 자식 메서드가 넣은 값(`count=99`)을 **필드 초기자가 덮는다**(`count=0`).
  근거 연산은 **`DefineField`** — 공개 필드를 `CreateDataPropertyOrThrow` 로 정의한다. ★ C# 쪽에서 같은 칸은 **묻지 않았다.**

### 10. 파이썬 34번의 `super()` — **파이썬은 `type(self)` 의 MRO, JS 는 HomeObject 의 윗집** ★★

- ★★ 파이썬은 **`type(self)` 의 MRO 에서 「내 다음」** — 문서 인용 *"The search starts from the class right after the type."*
  JS 는 **HomeObject 의 윗집**에서 찾기 시작한다.
- ★★★ **목적지가 인스턴스 따라 바뀌는 쪽은 파이썬**이다. 34번에서 같은 `Left.go` 의 `super()` 가 `Left() 에서 Left 의 다음  : Base`, `Both() 에서 Left 의 다음  : Right` 였다.
  JS 는 3번 `[1]` 에서 `toaster` 가 불러도 `Animal.who` 였다 — **안 바뀐다.**
- ★ **JS 는 단일 상속**이라 조상을 한 줄로 세울 일이 없다. `__mro__` 에 해당하는 물건이 없으니 **잴 것이 없다.**

### 11. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js16b-vdiff.sh (exit=0) =====
js16b-16a-where.js               identical
js16b-16b-rules.js               identical
js16b-16c-order.js               identical
js16b-16d-define-vs-set.js       identical
js16b-16e-private.js             identical
js16b-16f-private-windows.js     identical
js16b-16g-forin.js               identical
js16b-17a-two-chains.js          identical
js16b-17b-super-call.js          identical
js16b-17c-homeobject.js          identical
js16b-17d-builtins.js            identical
js16b-17e-ctor-virtual.js        identical
js16b-17f-super-edges.js         identical
js16b-18a-grid.js                identical
js16b-18b-array.js               identical
js16b-18c-hasown.js              identical
js16b-18d-mutate.js              identical
js16b-18f-refimpl.js             identical
js16b-19a-protocol-log.js        identical
js16b-19b-make-your-own.js       identical
js16b-19c-errors.js              DIFFERS
    4c4
    < id(...plain)                                -> TypeError Found non-callable @@iterator
    ---
    > id(...plain)                                -> TypeError Spread syntax requires ...iterable[Symbol.iterator] to be a function
js16b-19d-strings-maps.js        identical
js16b-19f-close-and-helpers.js   identical

identical 22  ·  differs 1  ·  total 23
```

**왜 그런가**

- ★★★ **이 주제의 블록은 전부 `identical`** 이다. 갈린 한 블록은 19번 주제의 스프레드 문구다.
- ★★★ **명세가 정하는 것 셋(대표)** — ① `extends` 가 두 사슬을 잇는 것 ② `super` 가 HomeObject 의 윗집에서 찾고 수신자로 `this` 를 넘기는 것 ③ 파생 생성자의 `super()` 규칙과 **예외의 종류**.
  **V8 의 문구 셋** — `Must call super constructor in derived class before accessing 'this' or returning from derived constructor` ·
  `Derived constructors may only return object or undefined` · `'super' keyword unexpected here`.
- ★★ **`e.stack` 은 ECMA-262 에 없다** — 엔진/호스트 칸. own 키 중 **`stack` 만** 명세 밖이다.
- ★★ **문구가 원인을 틀리게 말하는 두 곳** — `Super constructor null of N`(사슬은 `Function.prototype`) · `#label` 의 「class did not declare it」(선언했고 설치 전).
- ★ **창을 바꿔 물은 자리** — 부모 생성자 안의 `#label`(값 창이 `TypeError` 로 닫혀 `#label in this` 로 물었다).
  **부적용** — 진단의 `(행,열)`(묻는 것이 「컴파일되나」라 가를 열이 없다) · 파이썬 MRO 창(단일 상속).

### 12. 경계 — 어디까지가 이 주제인가 ★★

- **필드 초기화 순서** → 16번 · **조회와 수신자 규칙** → 15번 · **`this` 판정** → 07번 · **잘 알려진 심볼 전체** → [목록의 **22번 주제**](../22-symbol-and-well-known-symbols/) ·
  **`Error` 의 `cause` 쓰임** → [목록의 **32번 주제**](../32-error-handling-and-error/) · **`instanceof` 대 `Array.isArray`** → [목록의 **34번 주제**](../34-type-checking-idioms/) · **트랩의 `receiver`** → [목록의 **45번 주제**](../45-proxy/)·**46번 주제**.
- ★★ 16번의 로그는 **「언제 도나」의 순서**만 찍었다. 이 주제의 로그는 **그 순서 한가운데서 자식 메서드가 불리면 무엇을 보나**를 찍는다 — 같은 순서가 **사고로 나타나는 자리**다.
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **`extends` 가 잇는 두 사슬**(정적 멤버 · `extends null`)
  ② **`super` 의 출발 칸이 HomeObject 의 윗집이라는 것**(`this` 와 갈리는 것)
  ③ **파생 클래스에서는 부모가 객체를 만든다는 것**과 그 결과(`super()` 규칙 · 생성자 속 가상 호출 · 내장 상속).

## 실행 검증

| 소스 | 무엇을 고정하나 | 어디서 |
|---|---|---|
| `js16b-17a-two-chains.js` | 두 사슬 · 정적 메서드 상속 · 옛 방식 두 링크 · `extends null` | node20 1벌 + node18 대조(identical) |
| `js16b-17b-super-call.js` | `super()` 규칙(전 · 안 · 두 번 · 반환) · 암묵 생성자 · `new.target` | node20 1벌 + node18 대조(identical) |
| `js16b-17c-homeobject.js` | ★★★ **떼어 붙인 메서드의 `this`/`super`** · 윗집 동적 조회 · **트랩 로그의 receiver** · `super.x = v` · `SyntaxError` 자리 | node20 1벌 + node18 대조(identical) |
| `js16b-17e-ctor-virtual.js` | ★★★ **부모 생성자 속 가상 호출의 생성 로그** · 필드 초기자의 덮어쓰기 · `#private` 미설치 | node20 1벌 + node18 대조(identical) |
| `js16b-17d-builtins.js` | `extends Array`/`Error`/`Map` 대 옛 방식 · `Symbol.species` · 브랜드 | node20 1벌 + node18 대조(identical) |
| `js16b-17f-super-edges.js` | 메서드 안 화살표의 `super` · 정적 메서드의 `super` | node20 1벌 + node18 대조(identical) |
| `js16b-vdiff.sh` · `js16b-versions.sh` | 두 판 대조 · 판 정보 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — 1·2·3·4번의 문구. **종류만 명세가 정한다.**
- ★★★ **`e.stack` 의 존재와 첫 줄 · own 키의 `stack`** — ECMA-262 에 없다.
- ★ **이름 붙인 로그 문장**(`A.create called on B` 등)은 우리 스크립트가 지은 것이다.

**두 사슬 · `super()` 규칙과 예외의 종류 · HomeObject 와 수신자 · 필드가 `super()` 뒤 정의로 설치되는 것 · 내장 상속의 브랜드와 `Symbol.species` · `Error.prototype.name` 은 구현 의존이 아니다.**

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — 브라우저 · 다른 엔진의 문구 · **`setPrototypeOf(B, X)` 뒤 `new B()` 의 `super()` 목적지** ·
  클래스를 만드는 함수 꼴의 믹스인 · `super()` 두 번째 호출에서 부모 생성자가 도는지 · `Promise`/`RegExp` 의 `Symbol.species` · C# 쪽 「부모 생성자 중 넣은 값」 칸.
- ★ **못 잰 것** — **없다.**
- ★★★ **안 쟀다** — **성능 전부.**
- ★★ **부적용** — 진단의 `(행,열)` · 파이썬 MRO 창.
- ★★ **창을 바꿔 물은 자리** — 부모 생성자 안의 `#label`(값 창 대신 `#label in this`).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 특히 원인을 틀리게 말하는 두 문구는 고쳐질 가능성이 있다.
- ★★ **`e.stack` 첫 줄과 own 키 목록** — 엔진이 언제든 바꿀 수 있다.
- **사슬·`super`·필드 설치 순서 자체는 다시 돌릴 필요가 없다** — 명세 의미다.
