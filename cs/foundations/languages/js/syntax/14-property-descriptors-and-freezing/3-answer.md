# js/syntax/14 — 프로퍼티 디스크립터와 동결: 「막힌 것은 값이 아니라 플래그에 적혀 있다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제에는 두 판이 갈린 블록이 하나 있다**(`js12b-14c-freeze.js` 의 `fa.toSorted()` 한 줄).
> **그 블록은 양쪽을 나란히 싣는다** — 3번 정답에 node20 판과 node18 판이 둘 다 있다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
> ★★★ **격자 두 개는 통째로 `"use strict"` 아래에서 돌렸다** — 비엄격이면 막힌 칸이 `OK` 로 보여 격자가 안 읽힌다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js12b-14a-dump.js
// js12b-14b-configurable.js
// js12b-14c-freeze.js
// js12b-14s-strict.js
// js12b-hb-browser.js
// js12b-versions.sh
// js12b-vdiff.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **세 플래그의 `true`/`false`** |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **집계 줄** — `blocked 11 / 27` · `mode-dependent cells 9 / 13` |
> | V8 이 객체를 적는 방식(`#<Object>`·`[object Array]`) | ★★★ **예외의 종류**(`TypeError`) · 세 술어의 판정 |
> | ★ **`fa.toSorted()` 한 줄** — **판에 달렸다** | ★★ **전역 오염 목록** · 대조기의 `identical / differs` 집계 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 어디서 온 프로퍼티인가 — **리터럴은 `true,true,true`, `defineProperty` 는 `false,false,false`** ★★★

**출력**

```text
===== node20 js12b-14a-dump.js (exit=0) =====
[1] where did the property come from?
source                                kind      value                 writable enumerable configurable
literal  { a: 1 }                     data      1                     w=true   e=true   c=true
assignment  o.a = 1                   data      1                     w=true   e=true   c=true
defineProperty { value: 1 }           data      1                     w=false  e=false  c=false
defineProperty {} (no value)          data      undefined             w=false  e=false  c=false
literal getter  { get g() {} }        accessor  get=fn set=undefined  w=-      e=true   c=true
defineProperty { get }                accessor  get=fn set=undefined  w=-      e=false  c=false
Object.create 2nd arg                 data      1                     w=false  e=false  c=false
class prototype method                data      [fn]                  w=true   e=false  c=true
array element  [7]                    data      7                     w=true   e=true   c=true
array length   [7]                    data      1                     w=true   e=false  c=false
function .prototype                   data      {}                    w=true   e=false  c=false
function .name                        data      "f"                   w=false  e=false  c=true
function .length                      data      2                     w=false  e=false  c=true
Object.prototype.toString             data      [fn]                  w=true   e=false  c=true
globalThis.NaN                        data      NaN                   w=false  e=false  c=false

[2] the same property after each sealing call
state                                 kind      value                 writable enumerable configurable
plain                      .a         data      1                     w=true   e=true   c=true
preventExtensions          .a         data      1                     w=true   e=true   c=true
seal                       .a         data      1                     w=true   e=true   c=false
freeze                     .a         data      1                     w=false  e=true   c=false
plain                      .g         accessor  get=fn set=undefined  w=-      e=true   c=true
seal                       .g         accessor  get=fn set=undefined  w=-      e=true   c=false
freeze                     .g         accessor  get=fn set=undefined  w=-      e=true   c=false

[3] defineProperty defaults are the opposite of the literal's
literal        {"value":1,"writable":true,"enumerable":true,"configurable":true}
defineProperty {"value":1,"writable":false,"enumerable":false,"configurable":false}
all three flags flipped? true
is the defineProperty one visible to Object.keys / JSON? [] {}

[4] defineProperty on an EXISTING property only changes what you pass
after { enumerable: false } -> {"value":1,"writable":true,"enumerable":false,"configurable":true}
```

**왜 그런가**

- ★★★ **첫 세 줄 중 둘이 같다.** 리터럴 `{ a: 1 }` 과 대입 `o.a = 1` 은 **둘 다 `w=true e=true c=true`** 이고,
  `defineProperty { value: 1 }` 만 **`w=false e=false c=false`** 다.
  ★ **대입이 리터럴과 다를 것이라는 짐작이 여기서 끊긴다** — 평범한 대입은 리터럴과 한 글자도 같은 허가증을 만든다.
- ★★★ `[3]` 의 `all three flags flipped?` 는 **`true`** 다(스크립트가 세 칸을 직접 비교해 찍는다).
  그 아래 줄은 **`[] {}`** — `Object.keys` 가 빈 배열이고 `JSON.stringify` 가 빈 객체다.
  **넣었는데 안 보인다.** `enumerable` 기본값이 `false` 이기 때문이다.
- ★★ **클래스 프로토타입 메서드는 `w=true e=false c=true`** 다.
  `e=false` 이므로 **`Object.keys(C.prototype)` 는 빈 배열**이고 `for...in` 에도 안 뜬다.
- ★★ **배열의 `length` 는 `w=true e=false c=false`**, **함수의 `.name` 은 `w=false e=false c=true`** 로 **정반대**다.
  **대입으로 바꿀 수 있는 쪽은 `length`** 다(`arr.length = 0` 이 먹는다).
  `.name` 은 대입으로는 못 바꾸지만 **`c=true` 라 `defineProperty` 로는 바꿀 수 있다.**
  ★★★ 그래서 **「읽기 전용」과 「고정」은 다른 말**이다.
- ★★ `[2]` — **`preventExtensions` 는 한 칸도 안 내린다**(`ttt` 그대로) ·
  **`seal` 은 `configurable` 만** · **`freeze` 는 `configurable` 과 `writable` 둘 다** 내린다.
  ★★★ **`enumerable` 은 셋 다 안 건드린다** — 동결한 뒤에도 `e=true` 다.
- ★★ `.g` 세 줄이 `w=-` 인 것은 **접근자 디스크립터에 `writable` 칸 자체가 없기 때문**이다.
  덤프 스크립트가 `("get" in d)` 로 종류를 가르는 것이 **두 디스크립터의 키 집합이 다르다**는 증거다.
  `freeze` 뒤에 바뀐 것은 **`c=true` → `c=false` 하나뿐**이다 — 내릴 `writable` 이 없어서다.
- ★ `[4]` — **`writable` 과 `configurable` 은 `true` 로 남는다.**
  `{"value":1,"writable":true,"enumerable":false,"configurable":true}` 가 그 줄이다.
  **이미 있는 프로퍼티에는 준 칸만 바꾸고 나머지는 그대로 둔다** — 새로 만들 때와 규칙이 다르다.

### 2. 설정 불가가 된 뒤에는 무엇이 통하나 — **27칸 중 11칸만 막힌다** ★★★

**출력**

```text
===== node20 js12b-14b-configurable.js (exit=0) =====
[1] grid -- strict mode throughout
start             operation                               result
w=true  c=false   defineProperty value: 2                 OK  now value=2 w=true e=true c=false
w=true  c=false   defineProperty value: 1 (same)          OK  now value=1 w=true e=true c=false
w=true  c=false   defineProperty writable: true           OK  now value=1 w=true e=true c=false
w=true  c=false   defineProperty writable: false          OK  now value=1 w=false e=true c=false
w=true  c=false   defineProperty enumerable: false        TypeError Cannot redefine property: p
w=true  c=false   defineProperty configurable: true       TypeError Cannot redefine property: p
w=true  c=false   defineProperty get() {} (to accessor)   TypeError Cannot redefine property: p
w=true  c=false   assignment  o.p = 2                     OK  now value=2 w=true e=true c=false
w=true  c=false   delete o.p                              TypeError Cannot delete property 'p' of #<Object>

w=false c=false   defineProperty value: 2                 TypeError Cannot redefine property: p
w=false c=false   defineProperty value: 1 (same)          OK  now value=1 w=false e=true c=false
w=false c=false   defineProperty writable: true           TypeError Cannot redefine property: p
w=false c=false   defineProperty writable: false          OK  now value=1 w=false e=true c=false
w=false c=false   defineProperty enumerable: false        TypeError Cannot redefine property: p
w=false c=false   defineProperty configurable: true       TypeError Cannot redefine property: p
w=false c=false   defineProperty get() {} (to accessor)   TypeError Cannot redefine property: p
w=false c=false   assignment  o.p = 2                     TypeError Cannot assign to read only property 'p' of object '#<Object>'
w=false c=false   delete o.p                              TypeError Cannot delete property 'p' of #<Object>

w=true  c=true    defineProperty value: 2                 OK  now value=2 w=true e=true c=true
w=true  c=true    defineProperty value: 1 (same)          OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty writable: true           OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty writable: false          OK  now value=1 w=false e=true c=true
w=true  c=true    defineProperty enumerable: false        OK  now value=1 w=true e=false c=true
w=true  c=true    defineProperty configurable: true       OK  now value=1 w=true e=true c=true
w=true  c=true    defineProperty get() {} (to accessor)   OK  now accessor e=true c=true
w=true  c=true    assignment  o.p = 2                     OK  now value=2 w=true e=true c=true
w=true  c=true    delete o.p                              OK  now (deleted)

blocked cells 11 / 27

[2] the one-way door -- writable true->false is allowed even when configurable is false
true -> false   {"value":1,"writable":false,"enumerable":false,"configurable":false}
false -> true   TypeError Cannot redefine property: p
```

**왜 그런가**

- ★★★ 집계 줄은 **`blocked cells 11 / 27`** 이다. **16칸이 통과한다** — 「설정 불가면 아무것도 못 한다」가 절반도 안 맞는다.
- ★★★ **`w=true c=false` 에서 `defineProperty value: 2` 는 통과한다.**
  「설정 불가」로 읽으면 아무 재정의도 안 될 것 같은데, 그 자리에서 **값을 바꿀 권한은 `writable` 이 이미 주고 있다.**
  ★ **`configurable` 이 지키는 문은 허가증 자체**(플래그 변경·데이터↔접근자 변환·삭제)이지 값이 아니다.
- ★★★ `[2]` — **`true -> false` 는 통과하고 `false -> true` 는 `TypeError Cannot redefine property: p`** 다.
  ★ **일방통행 문**이다. 방향이 **권한을 줄이는 쪽**이라서 허용된다 — 줄이는 것은 나중에 관찰을 뒤집지 않는다.
- ★★ **`value: 1 (same)` 이 통과하는 것은 그것이 아무것도 안 바꾸기 때문**이다.
  ★★★ **그래서 「`TypeError` 가 안 났다」를 「바꿀 수 있다」로 읽으면 안 된다.** 같은 행의 `value: 2` 는 막힌다.
- ★★ **`assignment o.p = 2` 는 `writable` 만, `delete o.p` 는 `configurable` 만 본다** —
  `w=true c=false` 행에서 앞엣것은 통과하고 뒤엣것은 막히는 것이 그 증거다.
- ★ `[2]` 의 `"enumerable":false` 는 **만들 때 그 칸을 안 줘서 기본값이 박힌 것**이다 — 1번의 결론이 되풀이된다.

### 3. 세 봉인 함수를 나란히 돌리면 — **계단이고, 얕고, 접근자는 빠져나간다** ★★★

**출력** (node20)

```text
===== node20 js12b-14c-freeze.js (exit=0) =====
[1] grid -- strict mode throughout
operation                 plain               preventExtensions   seal                freeze              
add    o.nu = 1           OK                  TypeError           TypeError           TypeError           
write  o.a = 2            OK                  OK                  OK                  TypeError           
delete o.a                OK                  OK                  TypeError           TypeError           
reconfig defineProperty   OK                  OK                  TypeError           TypeError           
mutate o.deep.n = 2       OK                  OK                  OK                  OK                  
setPrototypeOf(o, null)   OK                  TypeError           TypeError           TypeError           

[2] the three predicates
object                            isExtensible   isSealed   isFrozen
{}                                true           false      false
Object.preventExtensions({})      false          true       true
Object.seal({})                   false          true       true
Object.freeze({})                 false          true       true
{ a: 1 }                          true           false      false
Object.preventExtensions({a:1})   false          false      false
Object.seal({a:1})                false          true       false
Object.freeze({a:1})              false          true       true
preventExt + w:false,c:false prop false          true       true
Object.freeze([])                 false          true       true
Object.freeze([1])                false          true       true
5  (primitive)                    false          true       true
'str'  (primitive)                false          true       true

[3] freeze is shallow -- the nested object is untouched
after mutating through the frozen object -> {"a":1,"deep":{"n":99},"arr":[1,2,3]}
isFrozen(outer)      true
isFrozen(outer.deep) false

[4] a getter survives freeze -- the VALUE it returns can still change
isFrozen true   descriptor {"get":"[fn]","enumerable":true,"configurable":false}
g.next reads: 1 2 3

[5] a frozen array
fa[0] = 9       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.push(4)      TypeError Cannot add property 3, object is not extensible
fa.length = 0   TypeError Cannot assign to read only property 'length' of object '[object Array]'
fa.sort()       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
```

**출력** (node18 — 이 배치에서 두 판이 갈린 유일한 블록이다)

```text
===== node18 js12b-14c-freeze.js (exit=0) =====
[1] grid -- strict mode throughout
operation                 plain               preventExtensions   seal                freeze              
add    o.nu = 1           OK                  TypeError           TypeError           TypeError           
write  o.a = 2            OK                  OK                  OK                  TypeError           
delete o.a                OK                  OK                  TypeError           TypeError           
reconfig defineProperty   OK                  OK                  TypeError           TypeError           
mutate o.deep.n = 2       OK                  OK                  OK                  OK                  
setPrototypeOf(o, null)   OK                  TypeError           TypeError           TypeError           

[2] the three predicates
object                            isExtensible   isSealed   isFrozen
{}                                true           false      false
Object.preventExtensions({})      false          true       true
Object.seal({})                   false          true       true
Object.freeze({})                 false          true       true
{ a: 1 }                          true           false      false
Object.preventExtensions({a:1})   false          false      false
Object.seal({a:1})                false          true       false
Object.freeze({a:1})              false          true       true
preventExt + w:false,c:false prop false          true       true
Object.freeze([])                 false          true       true
Object.freeze([1])                false          true       true
5  (primitive)                    false          true       true
'str'  (primitive)                false          true       true

[3] freeze is shallow -- the nested object is untouched
after mutating through the frozen object -> {"a":1,"deep":{"n":99},"arr":[1,2,3]}
isFrozen(outer)      true
isFrozen(outer.deep) false

[4] a getter survives freeze -- the VALUE it returns can still change
isFrozen true   descriptor {"get":"[fn]","enumerable":true,"configurable":false}
g.next reads: 1 2 3

[5] a frozen array
fa[0] = 9       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.push(4)      TypeError Cannot add property 3, object is not extensible
fa.length = 0   TypeError Cannot assign to read only property 'length' of object '[object Array]'
fa.sort()       TypeError Cannot assign to read only property '0' of object '[object Array]'
fa.toSorted()   OK  [1,2,3]
```

**왜 그런가**

- ★★★ **네 칸이 전부 `OK` 인 행은 `mutate o.deep.n = 2`** 다. **셋 중 무엇으로도 안쪽은 못 막는다** — 얕음의 첫 증거다.
- ★★ **`setPrototypeOf` 는 `preventExtensions` 부터 막힌다.** 프로토타입 교체는
  **확장 가능성에 걸려 있지 개별 프로퍼티의 플래그에 걸려 있지 않기** 때문이다(경로 쪽 정본은 15번).
- ★★★ **`{}` 의 `isFrozen` 은 `false` 이고 `Object.preventExtensions({})` 의 `isFrozen` 은 `true`** 다.
  차이를 만드는 조건은 **확장 가능성 하나뿐**이다 — `{}` 는 아직 새 프로퍼티를 받을 수 있다.
  ★★★ **이것이 이 문서를 쓰면서 뒤집힌 전제다.** 브리핑에는 「`isFrozen` 이 빈 객체에서 `true`」로 적혀 있었는데
  **실측은 「확장 가능한 빈 객체는 `false`, 비확장 빈 객체는 `true`」** 였다.
  10번 정답의 브라우저 줄(`14  isFrozen {} / prevExt {}` → `[false,true]`)이 **두 번째 엔진 자리에서 같은 답**을 준다.
- ★★★ **`freeze` 를 안 불렀는데 `isFrozen` 이 `true` 인 줄은 `preventExt + w:false,c:false prop`** 이다.
  **세 술어는 호출 이력이 아니라 지금 상태를 본다** — 비확장이고 모든 own 프로퍼티가 `c=false`·`w=false` 면 얼어 있는 것이다.
  ★ 빈 객체가 `true` 인 것도 같은 이유다. **검사할 프로퍼티가 없으면 「모든 …」 조건이 자동으로 참**이 된다.
- ★★ **원시값은 안 터진다.** `5` 와 `'str'` 둘 다 **`isExtensible false` · `isSealed true` · `isFrozen true`** 다 —
  own 프로퍼티를 못 붙이니 조건이 자동으로 참이 된다.
- ★★★ `[3]` — **`isFrozen(outer)` 는 `true`, `isFrozen(outer.deep)` 는 `false`** 다.
  `outer.arr` 는 **`[1,2,3]` 으로 늘어났다** — `push` 가 엄격 모드인데도 통과했다. **저쪽은 안 얼었기 때문**이다.
- ★★★ `[4]` — **`g.next reads: 1 2 3`** 이다. `isFrozen` 은 `true` 인데 읽을 때마다 값이 다르다.
  1번의 `[2]` 가 이유를 이미 보였다 — **`freeze` 가 내리는 것은 `writable` 인데 접근자에는 그 칸이 없다.**
  ★ 얼어붙은 것은 **`get` 함수를 가리키는 자리**이지 그 함수가 세는 `counter` 가 아니다.
  ★ 그 줄의 JSON 에 `set` 칸이 없는 것은 **`undefined` 라 `JSON.stringify` 가 지운 것**이다 —
  1번 덤프의 `get=fn set=undefined` 가 칸이 있다는 것을 따로 보인다.
- ★★ `[5]` — **막히는 것은 네 줄**이다. `fa[0] = 9` 와 `fa.sort()` 가 **같은 문구**로 막히는 것은
  **`sort` 가 제자리 정렬**이라 결국 `'0'` 에 쓰려 하기 때문이다.
  `fa.push(4)` 는 길이를 늘리려는 것이라 `Cannot add property 3, object is not extensible` 이고,
  `fa.length = 0` 은 **`length` 도 읽기 전용이 됐다**고 답한다.
- ★★★ **다섯째 줄이 두 판에서 갈린 줄**이다 — 9번 정답에서 따로 본다.

### 4. 두 모드에서 같은 열세 줄을 돌리면 — **13칸 중 9칸이 모드에 달렸다** ★★★

**출력**

```text
===== node20 js12b-14s-strict.js (exit=0) =====
[1] strict-first grid
frozen.a = 2                SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1
frozen.nu = 1 (add)         SPLIT strict: TypeError Cannot add property nu, object is not extensible
                                  sloppy: OK keys=["a"]
delete frozen.a             SPLIT strict: TypeError Cannot delete property 'a' of #<Object>
                                  sloppy: OK false keys=["a"]
sealed.a = 2                SAME  strict: OK a=2
                                  sloppy: OK a=2
delete sealed.a             SPLIT strict: TypeError Cannot delete property 'a' of #<Object>
                                  sloppy: OK false keys=["a"]
preventExt.nu = 1           SPLIT strict: TypeError Cannot add property nu, object is not extensible
                                  sloppy: OK keys=["a"]
non-writable.a = 2          SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1
getter-only.a = 2           SPLIT strict: TypeError Cannot set property a of #<Object> which has only a getter
                                  sloppy: OK a=1
proto has non-writable a    SPLIT strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: OK a=1 own=false
frozen array push           SAME  strict: TypeError Cannot add property 1, object is not extensible
                                  sloppy: TypeError Cannot add property 1, object is not extensible
defineProperty on frozen    SAME  strict: TypeError Cannot redefine property: a
                                  sloppy: TypeError Cannot redefine property: a
assign to undeclared G      SPLIT strict: ReferenceError <G> is not defined
                                  sloppy: OK 1
frozen globalThis-ish prop  SAME  strict: TypeError Cannot assign to read only property 'a' of object '#<Object>'
                                  sloppy: TypeError Cannot assign to read only property 'a' of object '#<Object>'

mode-dependent cells 9 / 13

[2] leftovers on globalThis
globals starting with js12b14 -> ["js12b14SloppyG11"]
any js12b14StrictG* leaked?    -> false
```

**왜 그런가**

- ★★★ 집계 줄은 **`mode-dependent cells 9 / 13`** 이다. 이 배치 네 주제 중 **가장 크게 갈린다**
  (12번은 11칸 중 6칸, 13번은 잴 칸 자체가 없었다).
- ★★★ **갈린 아홉 칸의 비엄격 쪽 답이 전부 같은 모양**이다 —
  **「`OK` 인데 값이 안 바뀌어 있다」.** `frozen.a = 2` 의 비엄격 답이 **`OK a=1`** 인 것이 그 전형이다.
  **던지지도 않고 쓰지도 않는다.** ★ 예외도 경고도 반환값도 없으므로 **「에러가 없다」로는 절대 못 가른다.**
- ★★★ **`SAME` 네 칸 중 `sealed.a = 2` 만 다른 이유로 `SAME`** 이다.
  그 칸은 **양쪽 다 `OK a=2`** — **애초에 아무것도 안 막혔다.** `seal` 이 `writable` 을 안 건드리기 때문이고,
  1번의 `[2]` 에서 `seal .a` 가 `w=true` 인 것이 그 증거다. **두 블록이 서로를 설명한다.**
  나머지 셋(`frozen array push`·`defineProperty on frozen`·`Object.assign` 쪽)은 **양쪽 다 `TypeError`** —
  ★★ **그 문들은 모드와 무관하게 던진다.** 「비엄격이면 조용하다」는 **대입(`=`)과 `delete` 에만** 해당한다.
- ★★ **`delete frozen.a` 의 비엄격 반환값은 `false`** 다(`OK false keys=["a"]`).
  ★ 12번의 결론 그대로다 — **`delete` 의 반환값은 「지웠나」가 아니라 「거부되지 않았나」** 이고, 여기서는 거부됐다.
- ★★ **`own=false` 는 own 프로퍼티가 아예 안 생겼다는 뜻**이다.
  프로토타입에 `w=false` 인 데이터 프로퍼티가 있으면 **자식에 새 own 프로퍼티를 만드는 것조차 막힌다.**
  ★ 쓰기가 체인을 어떻게 보는지는 15번이 정본이고, 여기서는 **막는 것이 디스크립터라는 사실**까지다.
- ★★★ `[2]` — **전역에 남은 이름은 하나**, `js12b14SloppyG11` 이다.
  열두 번째 탐침(`assign to undeclared G`)의 **비엄격** 판이 만든 것이고,
  **`any js12b14StrictG* leaked? -> false`** 가 엄격 쪽은 하나도 안 샜음을 따로 찍는다.
- ★ **엄격을 먼저 돌린 이유** — 비엄격 탐침이 만든 암시적 전역을 뒤이어 도는 엄격 탐침이 읽으면
  **두 모드가 「같다」는 거짓 결과**가 나오고, **값도 정상이고 예외도 없어 모든 검사기를 통과하기** 때문이다.
  ★★ 이 배치 직전에 실제로 그 사고가 났다. 처방은 둘 — **닫힌 쪽을 먼저 돌린다** · **탐침마다 전역 이름을 다르게 준다.**

### 5. 세 플래그는 각각 무엇을 지키는가 ★★★

- ★★★ 한 줄씩 — **`writable` 은 대입**(`o.a = 2`)을, **`configurable` 은 삭제와 재정의**(플래그 변경·데이터↔접근자 변환 포함)를,
  **`enumerable` 은 보이기**(`Object.keys`·`for...in`·`JSON.stringify`·`{ ...o }`·`Object.assign` 이 전부 이 칸을 본다)를 정한다.
  ★★ **셋은 서로 상관없다.** 2번 격자를 세로로 읽으면 세 문이 각각 다른 플래그에 달려 있는 것이 보인다.
- ★★★ **함수의 `.name` 이 「읽기 전용」**(`w=false c=true`)이고 **배열의 `length` 가 「반쯤 고정」**(`w=true c=false`)이다.
  앞엣것은 **대입으로는 못 바꾸는데 `defineProperty` 로는 바꾼다**, 뒤엣것은 **대입으로는 바꾸는데 지우거나 허가증은 못 고친다.**
  ★ 두 낱말을 갈라 써야 이 두 줄을 설명할 수 있다.
- ★★ **접근자에는 `value` 와 `writable` 이 없다.** 그래서 **`freeze` 가 접근자를 못 잠근다** —
  `freeze` 가 하는 일이 `writable` 을 내리는 것인데 내릴 칸이 없다. 3번의 `[4]` 가 그 결과다.
- ★ **안 바뀐다.** `getOwnPropertyDescriptor` 가 돌려주는 것은 **사본**이다.
  고친 것을 반영하려면 **`defineProperty` 로 다시 넣어야** 한다.

### 6. `isFrozen` 은 언제 `true` 라고 답하는가 — **상태를 묻지 호출을 묻지 않는다** ★★★

- ★★★ 포함 관계로 — **`isExtensible`** 은 「새 프로퍼티를 더할 수 있나」,
  **`isSealed`** 는 **비확장 ∧ 모든 own 프로퍼티가 `configurable: false`**,
  **`isFrozen`** 은 **`isSealed` 의 조건 ∧ 모든 own 데이터 프로퍼티가 `writable: false`** 다.
  ★ **뒤의 둘의 차이는 `writable` 한 칸**이다. 3번의 `{ a: 1 }` 네 줄이 그 계단을 그대로 보인다 —
  `seal({a:1})` 은 `isSealed` 만 `true` 이고 `isFrozen` 은 `false` 다.
- ★★★ **빈 객체에서는 「모든 own 프로퍼티가 …」라는 조건이 검사할 대상이 없어 자동으로 참**이 된다.
  그래서 **비확장이기만 하면 `isSealed` 도 `isFrozen` 도 `true`** 다.
  ★★ 거꾸로 **아직 확장 가능한 `{}` 는 둘 다 `false`** 다 — `isFrozen({})` 이 `false` 인 이유가 이것 하나뿐이다.
- ★★ **아니다.** `preventExtensions` 만 부른 객체가 `isFrozen: true` 인 줄이 실측에 있다.
  **술어는 호출 이력이 아니라 지금 상태를 본다.**
- ★ **반대 방향도 어긋난다.** `freeze` 를 부른 객체의 **안쪽**에 물으면 `isFrozen(outer.deep)` 가 **`false`** 다.
  ★★★ **두 방향이 모두 어긋나므로 `isFrozen` 을 「깊은 동결을 했나」의 검사로 쓸 수 없다.**

### 7. 동결은 정확히 어디서 멈추는가 ★★★

- ★★★ 깨지는 자리 셋.
  1. **중첩 객체·배열** — `outer.deep.n = 99` 와 `outer.arr.push(3)` 이 엄격 모드에서도 통과했다.
  2. **접근자 프로퍼티** — `g.next` 가 `1 2 3` 으로 계속 바뀐다.
  3. **비엄격에서 시도한 쓰기** — 안 터지므로 **막혔다는 사실 자체가 안 보인다.**
- ★★★ **`freeze` 가 하는 일**은 「비확장으로 만들고, 모든 own 프로퍼티의 `configurable` 을 내리고,
  데이터 프로퍼티의 `writable` 을 내리는 것」이다.
  ★ **그 한 줄에 접근자가 빠져나가는 이유가 들어 있다** — 접근자에는 내릴 `writable` 이 없다.
  1번의 `[2]` 에서 `freeze .g` 가 `seal .g` 와 **한 칸도 안 다른 것**이 그 확인이다.
- ★★ **`seal` 이 보장하는 것은 「키 집합이 안 바뀐다」** 이고(추가도 삭제도 막힌다),
  **보장하지 않는 것은 「값이 안 바뀐다」** 이다 — `writable` 을 안 건드리므로 대입이 그대로 먹는다.
- ★ **프로토타입 교체**(`Object.setPrototypeOf`)가 같이 막힌다. 3번 격자의 마지막 행이 그것이다.

### 8. 왜 엄격 모드라야 보이는가 ★★★

- ★★★ **아무것도 안 남긴다.** 예외도 경고도 없고, 대입식의 반환값은 원래 **쓰려던 값**이라 실패를 못 알린다.
  ★★ 이것이 이 주제의 가장 비싼 사고다 — **테스트가 통과하고 로그가 깨끗한데 값이 안 바뀐다.**
- ★★★ **④ 예외의 `constructor.name` + `message` 창이 비엄격에서는 원리상 안 열린다.**
  그래서 같은 질문을 **「쓴 뒤에 값을 다시 읽는」 창**으로 바꿔 물었다 —
  4번 격자의 탐침이 전부 `return 'a=' + o.a` 로 끝나고, 비엄격 답이 **`OK a=1`** 인 것이 그 답이다.
  ★ **바꾼 창이 못 보는 것** — **원래 값과 쓰려던 값이 같으면 그 창도 아무것도 못 가른다.**
  그때는 세 번째 창(`isFrozen`·디스크립터 찍기)이 필요하다.
- ★★ **모드와 무관하게 던지는 셋은 `Object.defineProperty` · `Array.prototype.push` · `Object.assign`** 이고,
  공통점은 **전부 메서드 호출**이라는 것이다 — 조용히 실패하는 것은 **대입 연산자와 `delete` 연산자**뿐이다.
- ★ 발견하는 법 셋 — **엄격 모드나 모듈(`.mjs`)로 돌려 본다** · **쓴 뒤에 다시 읽는다** · **디스크립터와 `isFrozen` 을 찍어 본다.**

### 9. 두 판이 갈린 한 줄 — **19블록 중 1개, 그리고 그것이 이 주제의 것이다** ★★

**출력**

```text
===== ./js12b-vdiff.sh (exit=0) =====
js12b-12a-shortcircuit.js    identical
js12b-12b-grid.js            identical
js12b-12c-assign.js          identical
js12b-12s-strict.js          identical
js12b-12x-forms.js           identical
js12b-12y-caret.js           identical
js12b-13a-order.js           identical
js12b-13b-intkeys.js         identical
js12b-13c-computed.js        identical
js12b-13d-views.js           identical
js12b-14a-dump.js            identical
js12b-14b-configurable.js    identical
js12b-14c-freeze.js          DIFFERS
    40c40
    < fa.toSorted()   OK  [1,2,3]
    ---
    > fa.toSorted()   OK  [1,2,3]  returned [1,2,3]
js12b-14s-strict.js          identical
js12b-15a-chain.js           identical
js12b-15b-proxy.js           identical
js12b-15c-shadow.js          identical
js12b-15d-misc.js            identical
js12b-15e-pycontrast.js      identical

identical 18  ·  differs 1  ·  total 19
```

**왜 그런가**

- ★★★ **갈린 것은 하나**다(`identical 18 · differs 1 · total 19`). 그 하나가 **`js12b-14c-freeze.js` 의 `[5]` 마지막 줄 `fa.toSorted()`** 로,
  node18 은 `OK  [1,2,3]`, node20 은 `OK  [1,2,3]  returned [1,2,3]` 이다.
- ★★★ **node18 의 `OK` 는 「`toSorted` 가 통과했다」는 뜻이 아니다.**
  소스가 **`fa.toSorted && fa.toSorted()`** 이므로 v18 에서는 `fa.toSorted` 가 `undefined` 라
  **`&&` 가 거기서 단축 평가했다.** 돌려받은 값이 `undefined` 라 `returned …` 꼬리가 안 붙은 것이다.
  ★ **12번에서 본 단축 평가가 여기서 되돌아온다** — 「값이 같아 보이는데 부른 것이 다르다」의 또 한 사례다.
- ★★ **갈린 것은 동결의 규칙이 아니라 `Array.prototype.toSorted` 의 존재 여부**다(ES2024, v18 에 없다).
  **동결 쪽은 두 판이 한 글자도 안 갈렸다** — 목록의 `js12b-14a-dump.js`·`js12b-14b-configurable.js`·`js12b-14s-strict.js` 가 전부 `identical` 이다.
- ★ **근거의 종류가 두 판에서 다르다.**
  **node20 줄**은 「**동결된 배열에서도 비변형 메서드는 통과한다**」의 근거이고,
  **node18 줄**은 「**그 메서드가 이 판에 없다**」의 근거일 뿐이다. 뒤엣것 위에 동결의 결론을 세우면 안 된다.

### 10. 보장인가 엔진 사정인가 판인가 ★★★

**출력**

```text
===== google-chrome --headless --dump-dom js12b-page.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g' (exit=0) =====
  engine                                Chrome/151.0.0.0
  12  0 ?? 'D' / 0 || 'D'               [0,"D"]
  12  ||= does not write                []
  12  = x || y writes                   ["set"]
  12  a?.b[f()] skips f                 calls 0
  12  a ?? b || c compiles?             SyntaxError: Unexpected token '||'
  12  new a?.b() compiles?              SyntaxError: Invalid optional chain from new expression
  13  enumeration order                 ["1","2","b","a","01","Symbol(s)"]
  13  '4294967295' is an index?         ["a","4294967295","z"]
  13  computed key calls toString       ["K"] ["toString"]
  13  __proto__ literal vs computed     true,false
  14  literal vs defineProperty desc    {"value":1,"writable":true,"enumerable":true,"configurable":true} | {"value":1,"writable":false,"enumerable":false,"configurable":false}
  14  isFrozen {} / prevExt {}          [false,true]
  14  freeze is shallow                 {"d":{"n":2}}
  14  strict write to frozen            TypeError: Cannot assign to read only property 'a' of object '#<Object>'
  15  chain of new TypeError            TypeError -> Error -> Object -> null
  15  String(Object.create(null))       TypeError: Cannot convert object to primitive value
  15  write does not walk               o/p/own:true
  15  non-writable proto blocks         TypeError: Cannot assign to read only property 'v' of object '#<Object>'
  15  Symbol.hasInstance overrides      true
```

**왜 그런가**

- ★★★ **셋 다 명세다.** 디스크립터 기본값도 2번 격자의 허용/거부 27칸도 세 술어의 정의도 전부 ECMA-262 가 정한다 —
  다른 엔진에서 다르면 **그 엔진이 틀린 것**이다.
- ★★★ **명세의 몫은 「종류」이고 「문구」는 엔진의 사정**이다.
  `#<Object>` 도 `[object Array]` 도 **V8 이 객체를 메시지에 적는 방식**이다.
  ★★ 앞엣것이 브랜드 태그처럼 보이지만 **우리가 ③ 창을 연 것이 아니라 엔진이 적어 넣은 것**이라 근거로 쓰지 않는다.
- ★★ **호스트가 정하는 칸은 0개**다. 브라우저의 `14` 로 시작하는 네 줄이 Node 쪽과 전부 같다 —
  디스크립터 두 벌도, **`isFrozen {} / prevExt {}` 가 `[false,true]` 인 것도**, 얕음도, 엄격 쓰기의 `TypeError` 도.
  ★ 문구까지 같은 것은 **둘 다 V8 이기 때문**이지 명세가 정한 것이 아니다.
- ★★★ **「예전엔 구현 나름이라던 것이 명세로 못 박힌」 자리는 디스크립터 자체이고, 그 판은 ES5** 다.
  `Object.defineProperty` 와 `Object.getOwnPropertyDescriptor` 가 그때 들어오면서
  **프로퍼티의 속성을 사용자 코드가 처음으로 관찰하고 조작할 수 있게** 됐다.
  ★ **ES2015 가 `Reflect` 와 프록시 불변식으로 그 계약을 확장했다** — 디스크립터가
  **엔진과 사용자 코드가 프로퍼티에 대해 주고받는 공용 언어**가 된 것이 그 판이다.
  ★★ 판별은 **[ECMA-262 아카이브](https://262.ecma-international.org/)** 로만 접지했고 **조항 번호는 인용하지 않는다.**
  13번의 「열거 순서가 못 박힌 자리」와 같은 집안이고 **이쪽이 먼저**다.
- ★ **부적용인 창은 둘** — **③ 브랜드 태그**(디스크립터는 값의 종류를 묻지 않는다)와
  **진단의 `(행,열)`**(이 주제에는 `SyntaxError` 가 한 줄도 없어 캐럿이 나올 자리가 없다).
  **「안 쟀다」와 다르다** — 「재 봤더니 같았다」가 아니라 **「잴 것이 없다」** 이다.
  ★ 반면 **성능은 「안 쟀다」** 쪽이다 — 잴 수야 있는데 이 문서가 안 쟀다.

### 11. 경계 — 어디까지가 이 주제인가 ★★

- **어느 문법이 어떤 디스크립터를 만드나** → [13번](../13-object-literals-and-properties/2-summary.md) ·
  **조회·쓰기가 체인을 타는 경로** → [15번](../15-prototype-chain/2-summary.md) ·
  **엄격 모드 규칙 전부** → 목록의 **35번 주제** ·
  **프록시 불변식과 트랩** → 목록의 **45번 주제**·**46번 주제** ·
  **깊은 동결·깊은 복사** → 목록의 **48번 주제**.
- ★★★ **13번은 「리터럴의 각 형태가 어떤 허가증을 만드나」까지** 갔다. 이 주제는 **그 허가증이 무엇을 막는지**부터다.
  ★★ **12번과의 경계는 정반대 방향**이다 — 12번은 **「막혔을 때 무엇이 보이나」** 까지이고
  여기는 **「왜 막히나」** 부터다. 12번에서 `||=` 가 동결된 객체에서 조용했던 그 자리의 이유가 4번 격자에 있다.
- ★★ **이름이 같고 하는 일이 다르다.** 파이썬의 **데이터 디스크립터는 조회 우선순위를 바꿔 「인스턴스 칸을 이긴다」** —
  값이 인스턴스에 **보이는데도** 클래스 칸에서 답이 나온다.
  **JS 의 프로퍼티 디스크립터는 플래그 셋일 뿐 조회 순서를 한 칸도 바꾸지 않는다** — 조회 경로 대비의 본론은 15번이 맡는다.
- ★ 이 주제가 끝까지 책임지는 것 셋 —
  ① **세 플래그가 각각 무엇을 막는지**(리터럴과 `defineProperty` 의 기본값 대비 포함)
  ② **`configurable: false` 뒤에 남는 것과 닫히는 것의 정확한 목록**
  ③ **세 봉인 함수의 계단과 그 계단이 멈추는 자리**(얕음·접근자·세 술어).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js12b-14a-dump.js` | ★★★ **리터럴 `ttt` 대 `defineProperty` `fff`** · 15줄 출처 대비표 · 세 봉인 함수가 내리는 칸 · 기존 프로퍼티에는 준 칸만 바뀌는 것 | node20 1벌 + node18 대조 1벌 |
| `js12b-14b-configurable.js` | ★★★ **`blocked cells 11 / 27`** · `writable` 일방통행 · `w=true c=false` 에서 값 변경이 통과하는 것 | node20 1벌 + node18 대조 1벌 |
| `js12b-14c-freeze.js` | ★★★ **6연산 × 4상태 격자** · 세 술어 13줄 · **얕음** · 접근자가 안 잠기는 것 · 동결 배열 | node20 1벌 + **node18 1벌(갈린 블록이라 양쪽을 다 싣는다)** |
| `js12b-14s-strict.js` | ★★★ **`mode-dependent cells 9 / 13`** · 조용한 실패의 모양 · 모드와 무관하게 던지는 셋 · 전역 오염 실측(1개) | node20 1벌 + node18 대조 1벌 |
| `js12b-hb-browser.js` · `js12b-page.html` | ★★★ **호스트가 정하는 칸 0개** · `isFrozen {} / prevExt {}` 가 `[false,true]` 인 것의 재확인 | Chrome 151 1벌 |
| `js12b-vdiff.sh` | **19블록 중 갈린 것 1개** — 그 하나가 이 주제의 것 | 1벌 |
| `js12b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** · 두 판의 디스크립터 기본값이 같다는 것 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **예외 문구 전부** — `Cannot redefine property: p` · `Cannot delete property 'p' of #<Object>` ·
  `Cannot assign to read only property 'a' of object '#<Object>'` ·
  `Cannot add property nu, object is not extensible` ·
  `Cannot set property a of #<Object> which has only a getter` ·
  `Cannot assign to read only property '0' of object '[object Array]'`.
  **종류(`TypeError`·`ReferenceError`)만 명세가 정한다.**
- ★★ **V8 이 객체를 적는 방식**(`#<Object>`·`[object Array]`)도 문구의 일부다.
- ★ **두 판과 Chrome 151 의 문구가 같은 것** — **같은 계열의 V8 이기 때문**이다.

**판(ES 버전)에 달린 항목 — 엔진 사정과 갈라 적는다**

- ★★★ **`Array.prototype.toSorted` 의 존재 여부**(ES2024). 이것만이 두 판을 가른 줄이다. 정본은 목록의 **25번 주제**.

**세 플래그의 의미 · 리터럴과 `defineProperty` 의 기본값 · 27칸 격자의 허용과 거부 · `writable` 의 일방통행 · 세 봉인 함수의 계단 · 셋 다 얕다는 것 · 접근자가 `freeze` 로 안 잠기는 것 · 세 술어의 정의(비확장 빈 객체가 `true` 인 것 포함) · 엄격에서 실패한 쓰기가 `TypeError` 인 것 · `defineProperty` · `push` · `Object.assign` 이 모드와 무관하게 던지는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 **문구** ·
  **`Proxy` 의 불변식 위반**(45번이 정본) · **`Reflect.defineProperty` 가 `false` 를 돌려주는 자리** ·
  **심볼 키 프로퍼티의 디스크립터** · **호스트 객체(DOM)의 디스크립터** · **깊은 동결 재귀와 순환 참조** ·
  **`getOwnPropertyDescriptors` + `Object.create` 로 접근자를 보존하는 복사**(27번·48번의 자리).
- ★ **안 돌려 본 것(판)** — **ES5 판 엔진에서 원시값에 `isFrozen` 을 던지면 어떻게 되나.**
  이 머신에 그 판의 엔진이 없어 **직접 못 던져 봤다.** 이 문서가 근거로 쓰는 것은 **지금 판의 출력**(`true`)뿐이다.
- ★ **안 쟀다** — **동결·`defineProperty`·디스크립터 조회의 비용.** 「동결하면 느려진다」는 흔한 말도 **한 줄도 안 적었다.**
- ★ **부적용인 창** — **③ 브랜드 태그**(가를 칸이 없다)와 **진단의 `(행,열)`**(`SyntaxError` 가 한 줄도 없다). **「재 봤더니 같았다」가 아니라 「잴 것이 없다」** 이다.
- ★★ **창을 바꿔 물은 자리** — 「비엄격에서 막혔나」를 **④ 예외 창 대신 「쓴 뒤 다시 읽기」 창**으로 물었다. 그 창은 **원래 값과 쓰려던 값이 같으면 아무것도 못 가른다.**

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **예외 문구 전부** — 11번 주제에서 **실제로 한 번 바뀐 전례**가 있다.
- ★★★ **`fa.toSorted()` 줄** — **지금도 두 판이 갈려 있는 유일한 줄**이다. 판이 오르면 node18 쪽이 사라진다.
- ★★ **브라우저 대조** — 호스트가 정하는 칸이 0개라는 판정은 **이 판의 관찰**이다.
- **세 플래그·격자·세 술어의 규칙 자체는 다시 돌릴 필요가 없다** — ES5 이후 바뀐 적이 없다.
