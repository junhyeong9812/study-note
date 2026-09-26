# js/syntax/16 — `class` 문법: 「메서드는 프로토타입에, 필드는 인스턴스에 정의된다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다). 브라우저는 **안 돌렸다.**
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제의 블록은 두 판에서 전부 identical 이다.** 그래서 양쪽을 나란히 실은 자리가 없다.
> ★★ **엄격 고정 블록은 `js16b-16d-define-vs-set.js` 하나**이고, 나머지는 **파일은 비엄격 · 클래스 몸통만 엄격**이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항(1\~6)과 [2-summary.md](2-summary.md) 동작 (6)에 있다.
> `js16b-16a-where.js` · `js16b-16b-rules.js` · `js16b-16c-order.js` · `js16b-16d-define-vs-set.js` · `js16b-16e-private.js` ·
> `js16b-16f-private-windows.js` · `js16b-16g-forin.js` · `js16b-versions.sh` · `js16b-vdiff.sh`
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **격자의 칸** · **own 키 목록과 그 순서** |
> | Node 스택트레이스의 절대 경로 — 한 줄도 싣지 않았다 | ★★★ **순서 로그의 번호** · setter 호출 횟수 · 트랩 로그 줄 수 |
> | `structuredClone` 의 동작(호스트 API) | ★★ **예외의 종류** · `true`/`false` |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 27칸 중 **6칸** — 메서드·getter 는 프로토타입, 필드는 인스턴스, `static` 셋은 생성자, `#private` 세 행은 전부 `.` ★★★

**출력**

```text
===== node20 js16b-16a-where.js (exit=0) =====
[1] where does each member land?   (W=writable E=enumerable C=configurable)
member         prototype         instance          constructor       
method         data     W-C      .                 .                 
acc            accessor  -C      .                 .                 
field          .                 data     WEC      .                 
staticMethod   .                 .                 data     W-C      
staticField    .                 .                 data     WEC      
fromBlock      .                 .                 data     WEC      
#secret        .                 .                 .                 
#privMethod    .                 .                 .                 
#staticSecret  .                 .                 .                 
cells with a property: 6 / 27

[2] the whole own-key list of each place (Reflect.ownKeys sees strings AND symbols)
prototype    ["constructor","method","acc"]
instance     ["field"]
constructor  ["length","name","prototype","staticMethod","reveal","staticField","fromBlock"]

[3] #private -- what does each reflection API report?
Reflect.ownKeys(inst)                 ["field"]
Object.getOwnPropertySymbols(inst)    []
JSON.stringify(inst)                  {"field":"f"}
Object.entries(inst)                  [["field","f"]]
{ ...inst }                           {"field":"f"}
structuredClone(inst)                 {"field":"f"}
'#secret' in inst                     false
C.reveal(inst)  (inside the class)    s,pm,ss

[4] enumerable flag -- class members vs object-literal and old-style members
class C { method() {} }               enumerable false
class C { get acc() {} }              enumerable false
class C { static staticMethod() {} }  enumerable false
class C { field = ... }               enumerable true
class C { static staticField = ... }  enumerable true
{ method() {} }  (literal)            enumerable true
{ get acc() {} }  (literal)           enumerable true
Old.prototype.method = function       enumerable true
Object.keys(C.prototype)              []
Object.keys(Old.prototype)            ["method"]
```

**왜 그런가**

```text
                     prototype      instance      constructor
   method            data W-C        .             .
   acc               accessor -C     .             .
   field             .               data WEC      .
   staticMethod      .               .             data W-C
   staticField       .               .             data WEC
   fromBlock         .               .             data WEC
   #secret           .               .             .
   #privMethod       .               .             .
   #staticSecret     .               .             .
                                                    -> cells with a property: 6 / 27
```

- ★★★ **행마다 채워진 칸이 많아야 하나** — 한 멤버는 한 자리에만 떨어진다. 인스턴스에는 `field` **하나만** 있다.
- ★★★ **`#private` 세 행이 `.` 인 것은 「없다」가 아니다** — `getOwnPropertyDescriptor` 가 **문자열 키 `"#secret"`** 을 찾았을 뿐이다.
  `[3]` 마지막 줄 `C.reveal(inst)` 가 `s,pm,ss` 를 돌려준다 — **값은 있다.** 프로퍼티가 아닌 별도의 칸(`[[PrivateElements]]`)에 있을 뿐이다.
- ★★ **플래그** — 메서드·정적 메서드는 `W-C`(비열거), getter 는 `accessor -C`, 필드·정적 필드는 `WEC`.
  ★ `fromBlock` 이 `WEC` 인 것은 `static {}` 안의 `C.fromBlock = …` 가 **평범한 대입**이기 때문이다.
- ★★★ **`[2]` 생성자의 키 순서가 소스와 다르다** — `staticMethod`·`reveal`(메서드) 다음에 `staticField`·`fromBlock`(필드·블록)이다.
  소스에서 `reveal` 은 **맨 끝**에 있었다. ★ 메서드는 클래스 평가 중에 먼저 붙고, 정적 필드·`static {}` 는 명세 `ClassDefinitionEvaluation` 의
  "For each element elementRecord of staticElements, do" 루프에서 **그 뒤에** 선언 순서로 돈다. 키 순서가 삽입 순서라는 것은 13번이다.
- ★★ **`[3]` 여덟 창 중 일곱이 `field` 하나만 본다** — `Reflect.ownKeys`·심볼·JSON·`entries`·스프레드·`structuredClone`, 그리고 `'#secret' in inst` 는 `false`.
- ★★★ **`[4]` 클래스 메서드만 비열거다** — 클래스의 `method`·`acc`·`staticMethod` 가 `false`, 리터럴의 두 줄과 옛 방식이 `true`, 필드 둘은 `true`.
  그래서 `Object.keys(C.prototype)` 는 `[]`, `Object.keys(Old.prototype)` 는 `["method"]` 다.

### 2. 클래스는 **`new` 로만 부르는 엄격한 함수**다 — 다섯 군데에서 평범한 함수와 다르다 ★★★

**출력**

```text
===== node20 js16b-16b-rules.js (exit=0) =====
[1] typeof, and calling without new
typeof class {}                             -> function
typeof K                                    -> function
F()   (plain function, no new)              -> called as a plain function
K()   (class, no new)                       -> TypeError Class constructor K cannot be invoked without 'new'
K.call({})                                  -> TypeError Class constructor K cannot be invoked without 'new'
new K() instanceof K                        -> true

[2] using the name before the declaration line
use before `class Late {}` in the block     -> ReferenceError Cannot access 'Late' before initialization
use before `function Early() {}`            -> function

[3] implicit globals and detached this -- inside a class body vs a plain function
class method: leakedFromClass = 1           -> ReferenceError leakedFromClass is not defined
plain function: leakedFromFunction = 1      -> assigned
'leakedFromClass' in globalThis             -> false
'leakedFromFunction' in globalThis          -> true
globals leaked by the 2 probes: ["leakedFromFunction"]  (1 / 2)
detached class method: this is              -> undefined
detached plain function: this is            -> globalThis

[4] reassigning the class name from inside
Named = 1  (inside a method)                -> TypeError Assignment to constant variable.
class expression's own name, from inside    -> function
typeof Inner  (from outside)                -> undefined

[5] has .prototype? can it be new-ed? (see topic 08)
class K                         has .prototype true   new ok
function F                      has .prototype true   new ok
K.prototype.m  (class method)   has .prototype false  TypeError
K.s  (static method)            has .prototype false  TypeError
() => {}                        has .prototype false  TypeError
K.prototype writable?  false   F.prototype writable?  true
```

**왜 그런가**

- ★★★ `[1]` **`typeof` 는 `function` 인데 `K()` 와 `K.call({})` 가 둘 다 `TypeError`** 다. `new K() instanceof K` 는 `true`.
- ★★ `[2]` **클래스는 TDZ** — `ReferenceError`(`Cannot access 'Late' before initialization`). 함수 선언은 `function`. 정본은 05번이다.
- ★★★ `[3]` **몸통의 `leakedFromClass = 1` 은 `ReferenceError`, 바깥 비엄격 함수는 `assigned`.** `globalThis` 에 남은 이름은 **`["leakedFromFunction"]` 하나**(`1 / 2`)다.
  ★ 명세 문장 — "All parts of a ClassDeclaration or a ClassExpression are strict mode code."
  ★ 떼어 낸 클래스 메서드의 `this` 는 **`undefined`**, 떼어 낸 비엄격 함수는 **`globalThis`** 다 — 엄격 모드의 기본 바인딩(07번).
- ★★ `[4]` **안쪽 이름은 `const`** — `Named = 1` 이 `TypeError`(`Assignment to constant variable.`). 클래스 식의 이름은 안에서 `function`, 밖에서 `undefined`.
- ★★★ `[5]` **클래스와 `function F` 는 `prototype` 도 있고 `new` 도 된다.** 클래스 메서드·정적 메서드·화살표는 **셋 다 `prototype` 이 없고 `new` 가 `TypeError`**.
  ★ **`K.prototype` 은 `writable false`, `F.prototype` 은 `true`** 다.

### 3. 필드가 **생성자 본문보다 먼저** · 파생 필드는 **`super()` 가 돌아오는 순간** · `static` 은 **정의 때 한 번** ★★★

**출력**

```text
===== node20 js16b-16c-order.js (exit=0) =====
[1] one class -- field initializers vs the constructor body
  1. field a initializer
  2. field b initializer  (sees this.a = 1)
  3. constructor body starts  (this.a is 1, this.b is 2)

[2] base and derived -- where do the derived fields go?
  1. Derived constructor body -- before super()
  2. Base field initializer
  3. Base constructor body
  4. Derived field initializer
  5. Derived constructor body -- after super()  (derivedField is D)

[3] static parts -- when do they run?
  1. before the class
  2. static field first
  3. static {} block  (this === S: true, S.first set: yes)
  4. static field second  (this.name is S)
  5. after the class
  6. instance field initializer  (only at new S())
  7. after new S()
```

**왜 그런가**

- ★★★ `[1]` **`a` → `b` → 생성자 본문**이다. 본문이 시작할 때 `this.a` 는 `1`, `this.b` 는 `2` — `b` 가 소스에서 생성자 **아래**에 있어도 먼저 돈다.
  ★ 필드는 **필드끼리의 선언 순서**로 돌고, 뒤 필드는 앞 필드를 본다(`sees this.a = 1`).
- ★★★ `[2]` **다섯 걸음** — 파생 본문 `super()` 앞 → 기반 필드 → 기반 본문 → **파생 필드** → 파생 본문 `super()` 뒤. 마지막 줄의 `derivedField` 는 **`D`** 다.
  ★ 명세 이름 `InitializeInstanceElements` — `#private` 메서드를 먼저 붙이고 필드를 선언 순서로 `DefineField` 한다. `super()` 자체는 17번이다.
- ★★★ `[3]` **`static first` → `static {}` → `static second` 가 `before the class` 와 `after the class` 사이**에 있다.
  블록 안에서 **`this === S` 가 `true`, `S.first` 는 이미 `yes`**, `static second` 의 `this.name` 은 **`S`** 다.
  ★ 인스턴스 필드는 **`new S()` 때**(6번)만 돈다.

### 4. 필드는 **setter 호출 0 · own `x`**, 대입은 **호출 1 · own `_x`** — 비쓰기 위에서는 필드만 통과한다 ★★★

**출력**

```text
===== node20 js16b-16d-define-vs-set.js (exit=0) =====
[1] a setter named x on the parent's prototype
x = 1       own keys ["x"]     own x {"value":1,"writable":true,"enumerable":true,"configurable":true}       o.x 1
            setter calls []
this.x = 1  own keys ["_x"]    own x none                                                                    o.x getter:1
            setter calls ["Parent setter got 1"]

[2] a NON-writable x on the parent's prototype (strict)
x = 1       ok, own x = 1
this.x = 1  TypeError Cannot assign to read only property 'x' of object '#<AssignOverRO>'

[3] the same two operations outside classes (topic 11)
defineProperty  setter calls 0   own x? true
plain  o.x = 2  setter calls 1   own x? false
```

**왜 그런가**

- ★★★ `[1]` **필드 `x = 1`** — own 키 `["x"]`, own `x` 는 `{"value":1,"writable":true,"enumerable":true,"configurable":true}`, `o.x` 는 **`1`**, setter 호출 **`[]`**.
  **대입 `this.x = 1`** — own 키 `["_x"]`, own `x` **없음**, `o.x` 는 **`getter:1`**, setter 호출 **`["Parent setter got 1"]`**.
- ★★★ **필드는 정의다** — `DefineField` 의 "Perform ? CreateDataPropertyOrThrow(receiver, fieldName, initValue)." 가 체인을 안 본다.
  **대입은 15번의 쓰기 경로**다 — 체인을 올라가 setter 를 찾고, setter 안 `this` 가 **수신자**라 `_x` 가 인스턴스에 생긴다(15번이 이미 증명했다).
- ★★ **own `x` 가 생긴 쪽에서는 `o.x` 가 부모 getter 를 거치지 않는다** — own 이 체인 위의 접근자를 가린다(15번 「읽기에서 own 이 무조건 이긴다」).
- ★★★ `[2]` **부모 프로토타입의 비쓰기 `x`** — 필드는 `ok, own x = 1`, 대입은 `TypeError`(`Cannot assign to read only property 'x' of object '#<AssignOverRO>'`).
  ★ 15번 `[3]` 의 「대입은 막히고 `defineProperty` 는 통과」와 같은 갈림길이다.
- ★★ `[3]` **클래스 밖** — `defineProperty` 는 호출 `0`·own `true`, `o.x = 2` 는 호출 `1`·own `false`.

### 5. `#x in` 은 **브랜드 검사** — `Object.create` 로 만든 가짜는 `instanceof` 만 속이고, 칸이 없으면 **`TypeError`** ★★★

**출력**

```text
===== node20 js16b-16e-private.js (exit=0) =====
[1] #x in obj -- the brand check (ES2022)
Account.isAccount(a1)                                   -> true
Account.isAccount(new Lookalike())                      -> false
Account.isAccount({})                                   -> false
Account.isAccount(Object.create(Account.prototype))     -> false
Object.create(Account.prototype) instanceof Account     -> true
Account.isAccount(7)                                    -> TypeError Cannot use 'in' operator to search for '#balance' in 7

[2] reading #balance off something that lacks it
Account.peek(a1)                                        -> 10
a1.sameAs(a2)  (another instance, same class)           -> true
Account.peek(new Lookalike())                           -> TypeError Cannot read private member #balance from an object whose class did not declare it
Account.peek(Object.create(Account.prototype))          -> TypeError Cannot read private member #balance from an object whose class did not declare it
Account.peek(new Proxy(a1, {}))                         -> TypeError Cannot read private member #balance from an object whose class did not declare it

[3] #x written outside any class body
new Function('o', 'return o.#balance')                  -> SyntaxError Private field '#balance' must be declared in an enclosing class
new Function('class Q { m() { return this.#nope } }')   -> SyntaxError Private field '#nope' must be declared in an enclosing class
```

**왜 그런가**

- ★★★ `[1]` **`Object.create(Account.prototype)` 은 브랜드 `false` · `instanceof` `true`** — 같은 객체에 두 질문이 **반대로** 답한다.
  `instanceof` 는 체인만 보고(15번), 브랜드는 **생성자가 그 객체 위에서 돌아 칸을 붙였나**를 본다.
  ★ `Lookalike`·`{}` 는 `false`, 원시값 `7` 은 **`TypeError`**(`Cannot use 'in' operator to search for '#balance' in 7`).
- ★★★ `[2]` **같은 클래스의 다른 인스턴스는 읽힌다**(`sameAs` 가 `true`). 칸이 없는 셋 — `Lookalike`·`Object.create`·**`new Proxy(a1, {})`** — 은 전부 **`TypeError`** 다.
  ★ 명세 `PrivateGet` — "If entry is empty, throw a TypeError exception." · `PrivateElementFind` 는 **그 객체 자신의** `[[PrivateElements]]` 를 본다. 프록시는 대상과 **다른 객체**다.
- ★★ `[3]` **두 줄 다 `SyntaxError`** — 클래스 밖 `o.#balance`, 그리고 클래스 안이어도 **선언 안 한** `#nope`. 실행 전에 던져지므로 `new Function` 으로 받았다.

### 6. 브랜드 태그 같음 · 트랩 로그 **0줄** · 동결 뒤에도 `#x` 는 바뀜 · 다른 평가의 `#x` 는 **다른 이름** ★★★

**출력**

```text
===== node20 js16b-16f-private-windows.js (exit=0) =====
[1] window 3 -- the brand tag, with and without #x
toString.call(new WithPriv())                 -> [object Object]
toString.call(new NoPriv())                   -> [object Object]
getOwnPropertyNames(new WithPriv())           -> ["field"]

[2] window 1 -- a Proxy that logs every trap
p.field                                       -> f
  trap log ["get(field)"]
WithPriv.has(p)                               -> false
  trap log []
WithPriv.bump(p)                              -> TypeError Cannot read private member #x from an object whose class did not declare it
  trap log []

[3] #x after Object.freeze
Object.isFrozen(w)                            -> true
WithPriv.bump(w)  (after freeze)              -> 2
w.field = 'g'  (after freeze, sloppy file)    -> f

[4] two classes that both spell #x
WithPriv.has(new Other())  (same spelling #x) -> false
K1.has(new K1())                              -> true
K1.has(new K2())  (same source, 2nd eval)     -> false
```

**왜 그런가**

- ★★★ `[1]` **둘 다 `[object Object]`** — ③ 브랜드 태그는 `#x` 를 못 본다. `getOwnPropertyNames` 도 `["field"]` 뿐이다.
- ★★★ `[2]` **공개 `p.field` 는 트랩 로그 `["get(field)"]` 한 줄, `#x` 두 호출은 로그 `[]`** — `has(p)` 는 `false`, `bump(p)` 는 `TypeError`.
  ★ **트랩을 한 번도 안 불렀다** — ① 창은 `#x` 를 원리상 못 본다. 핸들러로 고칠 길도 없다.
- ★★ `[3]` **얼린 뒤에도 `bump(w)` 가 `2`** 다. 공개 `w.field = 'g'` 는 **조용히 무시**되어 `f` 그대로다(파일이 비엄격이라 예외가 아니다).
  ★ 동결은 **프로퍼티**의 플래그를 바꾸고(14번), `#x` 는 프로퍼티가 아니다.
- ★★ `[4]` **`WithPriv.has(new Other())` 는 `false`** — 철자가 같아도 몸통이 다르면 다른 이름이다.
  **`K1.has(new K1())` 는 `true`, `K1.has(new K2())` 는 `false`** — 같은 소스라도 **평가가 두 번이면 이름이 둘**이다.

### 7. `typeof` 는 **호출 방식을 말해 주지 않는다** — 호출 자격과 생성 자격은 따로다 ★★

- ★★ **`typeof` 는 「호출할 수 있는 객체인가」만 말한다.** 클래스는 `function` 인데 `K()` 가 `TypeError` 다 — **`new` 로만 부를 수 있다.**
- ★★★ **08번의 반례 둘** — 제너레이터(`prototype` 있음 · `new` 안 됨), bound 함수(`prototype` 없음 · `new` 됨).
  ★ 클래스 메서드·정적 메서드는 **`prototype` 없음 · `new` 안 됨** 칸이다 — 리터럴의 메서드 단축과 같다(2번 `[5]`).
- ★★ **클래스의 `.prototype` 은 쓰기 불가 데이터 프로퍼티다** — `K.prototype writable?  false` 한 줄이 근거다(`F.prototype` 은 `true`).
  ★ **15번처럼 갈아끼우는 대입 자체는 이 문서가 안 던졌다.** 쓰기 불가 칸에 대입하면 모드에 따라 무엇이 되나는 14번 격자의 몫이다.
- ★ **떼어 낸 메서드의 `this` 가 `undefined`** 다 — 몸통이 엄격이라 기본 바인딩이 `globalThis` 로 안 떨어진다. 처방(`bind`·필드 화살표)은 07번에 있다.

### 8. **필드 순서로는 C++ 쪽**이다 — 파생 필드가 기반이 다 끝난 뒤에 채워진다 ★★★

| 단계 | C++ (C# 12번 정답 2번) | C# (C# 12번 정답 1번) | JS (3번 `[2]`) |
|---|---|---|---|
| 1 | 기반 멤버 초기자 | ★ **파생 필드 초기자** | 파생 생성자 본문 — `super()` 앞 |
| 2 | 기반 생성자 본문 | 기반 필드 초기자 | 기반 필드 초기자 |
| 3 | ★ **파생 멤버 초기자** | 기반 생성자 본문 | 기반 생성자 본문 |
| 4 | 파생 생성자 본문 | 파생 생성자 본문 | ★ **파생 필드 초기자** |
| 5 | — | — | 파생 생성자 본문 — `super()` 뒤 |

- ★★★ **파생 초기자의 자리** — C++ 3번째, C# **1번째**, JS 4번째(기반 두 단계 **뒤**). **JS 는 C++ 쪽이다.** 근거는 3번 `[2]` 의 2·3번 줄(기반) 다음 4번 줄(파생 필드).
- ★★ **JS 에만 있는 단계는 1번** — 파생 생성자 본문이 `super()` **앞에서** 먼저 돈다. 그 자리에서 `this` 를 쓰면 무엇이 나오나는 **이 문서가 안 던졌다**(17번).
- ★ **C++ 의 기반/파생 순서는 C# 갈래 12번 정답 2번**(`cs12b-cpp-order.cpp`)이 쟀다. **C++ 13번은 상속을 다루지 않았고** 한 클래스 안의 **선언 순서**를 쟀다 —
  JS 3번 `[1]` 의 `a` → `b` 가 그 모양이다.
- ★ **물리는 자리** — 순서 표에서 따라 나오는 것은 「기반 생성자 본문(3번)이 도는 동안 파생 필드(4번)는 아직 안 채워졌다」까지다.
  그때 기반이 파생의 메서드를 부르면 무엇이 보이나는 **17번**이 잰다 — 여기서는 안 던졌다.

### 9. 값이 **돌아오기** 때문이다 — 「잴 것이 없다」면 결론이 「없음」이어야 한다 ★★★

- ★★★ **부적용(잴 것이 없다)** = 창을 열 대상 자체가 없다(예: 이 주제의 `(행,열)` — 값으로 못 가르는 문법 성질이 없다).
  **제5의 상태(창을 바꿔 물었다)** = 대상은 있는데 평소 창이 전부 닫혀 **다른 창으로 물어 답을 얻었다.**
  ★★★ 가르는 관찰 한 줄 — **`C.reveal(inst)` 가 `s,pm,ss` 를 돌려준다.** 대상이 있다.
- ★★★ **네 창의 결과** —
  ② 격자 `#private` 세 행 전부 `.`, own 키·심볼·JSON·`entries`·스프레드·`structuredClone` 전부 `field` 하나 ·
  ③ 브랜드 태그 `[object Object]`(있으나 없으나 같다) ·
  ① 모든 트랩을 심은 `Proxy` 에서 트랩 로그 **0줄** ·
  ④ **클래스 밖**에서는 묻는 문장 자체가 `SyntaxError`, **클래스 안**에서는 칸이 없을 때만 `TypeError` 로 답한다.
- ★★★ **바꾼 창이 못 보는 것 셋** — ① 이름을 미리 알아야 한다(목록을 못 뽑는다) · ② 그 클래스 소스가 `static` 메서드를 미리 심어 협조해야 한다 ·
  ③ 같은 철자라도 **다른 몸통·다른 평가**의 `#x` 는 못 묻는다(6번 `[4]`).
- ★★ **`'#secret' in inst` 는 문자열 `"#secret"` 이라는 프로퍼티 키**를 물었다. 진짜 브랜드 검사는 **따옴표 없는** `#secret in inst` 이고 클래스 몸통 안에서만 쓸 수 있다.

### 10. `ClassElementEvaluation` 이 **`false`** 를 넘긴다 — 옛 방식은 `for...in` 에 메서드가 끼고 클래스는 안 낀다 ★★

- ★★★ **`ClassElementEvaluation`** — "MethodDefinitionEvaluation of MethodDefinition with arguments obj and false." 그 `false` 가 열거 가능 여부다.
  ★ **필드는 `DefineField` → `CreateDataPropertyOrThrow`** 라 평범한 데이터 프로퍼티(`WEC`)가 된다 — 메서드 경로를 안 탄다.
- ★★ **돌렸다** — 요약 동작 (6)의 블록이다. 인스턴스의 `for...in` 이 옛 방식 `["field","method"]`, 클래스 `["field"]`. **`Object.keys` 는 둘 다 `["field"]`**.

```text
===== node20 js16b-16g-forin.js (exit=0) =====
for...in new Modern()        ["field"]
for...in new Old()           ["field","method"]
Object.keys(new Modern())    ["field"]
Object.keys(new Old())       ["field"]
'method' in new Modern()     true
```

- ★★ **`'method' in new Modern()` 은 `true`** — `in` 은 열거 여부를 안 본다. **비열거는 「없다」가 아니라 「목록에 안 올린다」라는 뜻**이다.
- ★ `for...in` 의 규칙(체인 순회·중복 이름·순서)은 **18번**이 정본이다.

### 11. 보장인가 엔진 사정인가 ★★★

- ★★★ **명세** — 멤버가 붙는 세 자리와 클래스 메서드의 비열거 · 필드 = `CreateDataPropertyOrThrow` · `#x` 를 못 찾으면 `TypeError`(`PrivateGet`) ·
  몸통 전체가 엄격 · 예외의 **종류** 전부.
  **V8 문구** — `Class constructor K cannot be invoked without 'new'` · `Cannot read private member #balance from an object whose class did not declare it` ·
  `Private field '#balance' must be declared in an enclosing class` · `Cannot use 'in' operator to search for '#balance' in 7`.
- ★★ **`structuredClone` 은 호스트 API**(HTML 표준, Node 가 전역으로 준다)다. ECMA-262 에 없으므로 「언어가 `#private` 를 복제하지 않는다」로 적으면 **보장의 주체를 틀린다** — 이 판 Node 의 관찰이다.
- ★★ **부적용** — 진단의 `(행,열)`(18-C). `SyntaxError` 는 있지만 묻는 것이 「되나 안 되나」라 종류와 문구로 끝난다.
  **안 돌린 것** — 브라우저. **안 잰 것** — 성능·메모리 전부.
- ★★ **한 파일 안에서 클래스 몸통(엄격)과 바깥 함수(비엄격)를 나란히** 돌렸다(2번 `[3]`). 지킨 규칙 둘 — **엄격을 먼저** · **탐침마다 전역 이름을 다르게**(규칙 22).
  끝에 `globalThis` 로 세어 스크립트가 `1 / 2` 를 직접 찍었다.

### 12. 경계 — 어디까지가 이 주제인가 ★★

- **체인 조회·쓰기 경로** → [15번](../15-prototype-chain/2-summary.md) · **`extends`·`super`·`new.target`** → [17번](../17-inheritance-and-super/2-summary.md) ·
  **열거 규칙** → [18번](../18-for-in-and-enumeration/2-summary.md) · **`Proxy` 트랩 계약** → 목록의 **45번 주제** ·
  **클래스 TDZ** → [05번](../05-var-let-const-and-tdz/2-summary.md) · **떼어 낸 메서드의 `this`** → [07번](../07-this-binding-four-rules/2-summary.md) ·
  **「정의 대 대입」을 처음 잰 곳** → [11번](../11-spread-and-rest/2-summary.md).
- ★★★ **15번에서 받아 쓴 것 넷** — ① 읽기는 체인을 타고 쓰기는 수신자에 내려앉는다 ② 쓰기 트랩 로그 `["C.set","B.set","A.set","C.gopd"]` ③ 체인 위 setter 의 `this` 는 수신자(그래서 `_x` 가 인스턴스에) ④ `prototype` 과 `[[Prototype]]` 은 다른 칸이다.
- ★★ **같은 갈림길의 자리 — 대상 쪽에 setter 가 있을 때.** 11번은 스프레드(정의) 대 `Object.assign`(대입)이 setter 호출 `0` 대 `1`, 여기는 필드(정의) 대 생성자 대입이 `0` 대 `1` 이다.
- ★ **끝까지 책임지는 것 셋** — ① **멤버 일곱 종류가 어느 자리에 붙나**(27칸 격자) ② **필드는 정의이고 생성자 대입은 대입이다** ③ **`#private` 는 프로퍼티가 아니고 클래스 안쪽의 브랜드 검사로만 보인다.**

## 실행 검증

| 소스 | 무엇을 고정하나 | 어디서 |
|---|---|---|
| `js16b-16a-where.js` | ★★★ **27칸 격자**(`6 / 27`) · 세 자리의 own 키 전체 · `#private` 에 눈먼 바깥 창 일곱 · 클래스 메서드 비열거 | node20 1벌 + node18 대조 |
| `js16b-16b-rules.js` | `new` 없는 호출 · TDZ · 몸통 엄격(누수 `1 / 2`) · 떼어 낸 `this` · 안쪽 `const` · `prototype` × `new` 5형태 · `.prototype` 쓰기 불가 | node20 1벌 + node18 대조 |
| `js16b-16c-order.js` | ★★★ 필드 → 본문 · 기반/파생 다섯 걸음 · `static` 정의 시점 | node20 1벌 + node18 대조 |
| `js16b-16d-define-vs-set.js` | ★★★ 정의 대 대입(setter 호출 `0`/`1`) · 비쓰기 위 필드 통과·대입 `TypeError` | node20 1벌 + node18 대조 (**엄격 고정**) |
| `js16b-16e-private.js` | ★★★ 브랜드 검사 · `instanceof` 와의 불일치 · 칸 없음 `TypeError` · 프록시 · 클래스 밖 `SyntaxError` | node20 1벌 + node18 대조 |
| `js16b-16f-private-windows.js` | ★★★ 브랜드 태그 · 트랩 로그 0줄 · 동결 무력 · 평가마다 다른 `#x` | node20 1벌 + node18 대조 |
| `js16b-16g-forin.js` | 클래스 대 옛 방식의 `for...in` · `Object.keys` · `in` | node20 1벌 + node18 대조 |
| `js16b-versions.sh` · `js16b-vdiff.sh` | 이 문서의 출력이 어느 판에서 나왔나 · 두 판에서 갈린 블록 | 1벌씩 |

```sh
# js16b-vdiff.sh
#!/usr/bin/env bash
# 두 판이 갈린 블록이 몇 개인가 -- 스크립트가 직접 센다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js16b-1[6-9]?-*.js; do
  a="$("$N18" "$f" 2>&1)"
  b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-32s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-32s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```

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

★ 이 주제의 블록은 위 대조에서 **전부 `identical`** 이다. 끝줄 —
`identical 22  ·  differs 1  ·  total 23`

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — 11번에 모아 둔 넷과 `Cannot access 'Late' before initialization` · `leakedFromClass is not defined` · `Assignment to constant variable.` ·
  `Cannot assign to read only property 'x' of object '#<AssignOverRO>'`. **종류만 명세가 정한다.**
- ★★ **`structuredClone` 이 `#private` 를 안 옮긴 것** — 호스트 API 의 이 판 관찰이다.
- ★ **두 판이 한 글자도 안 갈린 것** — 둘 다 V8 이기 때문이지 보장이 아니다.

**멤버가 붙는 세 자리 · 클래스 메서드 비열거 · 필드가 정의인 것 · 필드 초기자 순서 · `static` 이 정의 때 도는 것 · 몸통 엄격 · 클래스 TDZ · `new` 없는 호출의 `TypeError` · `#x` 를 못 찾으면 `TypeError` · 클래스 밖 `#x` 의 `SyntaxError` 는 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용 / 창을 바꿔 물은 자리**

- **안 돌려 본 것** — 브라우저 · 다른 엔진의 문구 · 트랜스파일러가 필드를 무엇으로 바꾸나 · 클래스 `.prototype` 에 **실제로 대입**해 보기(쓰기 불가 플래그만 봤다) ·
  파생 생성자에서 `super()` **앞의 `this`**(17번) · 기반 생성자가 파생 메서드를 부를 때의 파생 필드(17번) · 모듈 중복 로드에서의 `#x in` · 파이썬 대비.
- ★ **못 잰 것** — **없다.** 도구가 없어 못 잰 칸은 없었다.
- ★★★ **안 쟀다** — **성능·메모리 전부.** 「`#private` 는 느리다」·「필드는 메모리를 더 먹는다」를 한 줄도 쓰지 않았다.
- ★★ **부적용** — 진단의 `(행,열)`(18-C). **잴 것이 없다.**
- ★★★ **창을 바꿔 물은 자리** — `#private` 의 존재. ①②③④ 가 전부 닫혀 **클래스 안쪽의 `#x in o`·`C.reveal`** 로 물었다(9번).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 11번 주제에서 실제로 한 번 바뀐 전례가 있고, 이 배치의 19번 블록도 두 판에서 문구가 갈렸다.
- ★★ **`structuredClone` 의 동작** — 호스트가 언제든 바꿀 수 있다.
- **격자·순서·정의 대 대입은 다시 돌릴 필요가 없다** — ES2022 이후 명세가 고정한 것이다. ★ 다시 찍어야 할 것은 **새 클래스 문법**(예: 데코레이터)이 이 격자에 칸을 더하는가다.
