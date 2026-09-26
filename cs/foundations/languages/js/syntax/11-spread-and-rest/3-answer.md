# js/syntax/11 — 스프레드와 나머지: 「같은 점 셋이 자리마다 다른 일을 한다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **두 판이 갈린 블록은 양쪽을 다 실었다** — 8번 답에 있다.
> ★★ **표준 출력과 표준 오류를 한 블록에도 안 섞었다** — 이 주제의 블록은 전부 표준 출력이다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.

```text
// js08b-11a-three-places.js
// js08b-11b-traps.js
// js08b-11c-shallow.js
// js08b-11h-browser.js
// js08b-11x-forms.js
// js08b-vdiff.sh
// js08b-versions.sh
```

> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **트랩 호출 순서와 이름** |
> | 예외 **문구** — **이 주제에서 실제로 두 판이 갈렸다** | ★★★ **예외의 종류** · 결과 객체의 키 목록 |
> | 브라우저 UA 문자열의 뒷자리 | ★★ **동일성 판정** · 디스크립터의 모양 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 값을 세 자리에 넣으면 — **객체 자리만 다른 문을 쓴다** ★★★

**출력**

```text
===== node20 js08b-11a-three-places.js (exit=0) =====
[1] spread -- three places, three different rules
  [...arr]                                 -> [1,2]
  [0, ...arr, 3]                           -> [0,1,2,3]
  [...'ab']                                -> ["a","b"]
  [...new Set([1, 1, 2])]                  -> [1,2]
  [...new Map([['k', 1]])]                 -> [["k",1]]
  [...obj]                                 -> TypeError: objSrc is not iterable
  { ...obj }                               -> {"a":1,"b":2}
  { ...arr }                               -> {"0":1,"1":2}
  { ...'ab' }                              -> {"0":"a","1":"b"}
  { ...new Set([1, 2]) }                   -> {}
  { ...7 }                                 -> {}
  { ...null }                              -> {}
  { ...undefined }                         -> {}
  [...null]                                -> TypeError: null is not iterable
  f(...arr)                                -> [1,2]
  f(...'ab')                               -> ["a","b"]
  f(...obj)                                -> TypeError: Spread syntax requires ...iterable[Symbol.iterator] to be a function

[2] later wins -- object spread is just property copying in order
  { ...obj, a: 9 }                         -> {"a":9,"b":2}
  { a: 9, ...obj }                         -> {"a":1,"b":2}
  { ...{ a: 1 }, ...{ a: 2 } }             -> {"a":2}
  { ...obj, ...{ b: undefined } }          -> {"a":1,"b":"<undefined>"}
  array spread does not merge              -> [1,2,2,3]

[3] rest -- three places, always the last one
  function (a, ...r) with (1, 2, 3)        -> [1,[2,3]]
  const [a, ...r] = [1, 2, 3]              -> [1,[2,3]]
  const { a, ...r } = { a: 1, b: 2 }       -> [1,{"b":2}]
  rest of an array pattern is an Array     -> true
  rest of an object pattern is an Object   -> [object Object]
  rest param is an Array                   -> true

[4] which form each place accepts -- SyntaxError or not
  form                                    sloppy  strict
  [...a, b]  spread not last              ok      ok
  [a, ...b] = arr  rest not last          ERR     ERR
  function f(...r, b)                     ERR     ERR
  function f(...r = [])                   ERR     ERR
  const [...r = []] = []                  ERR     ERR
  const { ...r, a } = {}                  ERR     ERR
  const { a, ...r } = {}                  ok      ok
  const [...r,] = []  trailing comma      ERR     ERR
  [...a,]  spread then comma              ok      ok
  f(...a,)  call trailing comma           ok      ok
  const { ...{ a } } = {}                 ERR     ERR
  const [...[a, b]] = [1, 2]              ok      ok
  settings-dependent cells                0 of 12

[5] the messages behind the ERR cells
  [a, ...b] = arr  rest not last          SyntaxError: Rest element must be last element
  function f(...r, b)                     SyntaxError: Rest parameter must be last formal parameter
  function f(...r = [])                   SyntaxError: Rest parameter may not have a default initializer
  const [...r = []] = []                  SyntaxError: Invalid destructuring assignment target
  const { ...r, a } = {}                  SyntaxError: Rest element must be last element
  const [...r,] = []  trailing comma      SyntaxError: Rest element must be last element
  const { ...{ a } } = {}                 SyntaxError: `...` must be followed by an identifier in declaration contexts
```

**왜 그런가**

- ★★★ **터지는 줄은 셋**이다 — `[...obj]` · `[...null]` · `f(...obj)`. 전부 **배열·호출 자리**다.
  **조용히 빈 결과를 내는 줄은 넷**이다 — `{ ...new Set(...) }` · `{ ...7 }` · `{ ...null }` · `{ ...undefined }`.
  전부 **객체 자리**이고 결과가 `{}` 다.
- ★★★ **가른 것은 「자리」다.** 객체 자리는 **프로퍼티를 복사**하므로 복사할 것이 없으면 빈 객체를 만들고,
  배열·호출 자리는 **이터레이터를 요구**하므로 없으면 거부한다.
  ★ 그래서 **`{ ...null }` 은 `{}`, `[...null]` 은 `TypeError`** 다. 같은 점 셋인데 결과가 정반대다.
- ★★★ **`{ ...new Set([1, 2]) }` 은 `{}`** 다. `Set` 은 원소를 **자기 프로퍼티로 갖고 있지 않다** —
  원소는 내부 슬롯에 있고 프로퍼티로는 아무것도 안 보인다.
  ★★ **「이터러블이니까 될 것」이 틀리는 이유는 객체 자리가 이터러블을 안 보기 때문**이다.
  ★★★ **이것이 [09번](../09-call-apply-bind/2-summary.md)의 `apply(t, new Set(...))` 과 같은 모양의 사고**다 —
  **자리마다 보는 것이 다른데 한 가지로 외웠을 때** 나는 실패이고, 둘 다 **에러가 안 난다.**
- ★★ **규칙 한 줄 — 나중에 적은 것이 이긴다.** `{ ...obj, a: 9 }` 의 `a` 는 `9` 이고 `{ a: 9, ...obj }` 의 `a` 는 `1` 이다.
  ★ **`undefined` 도 값이라 덮어쓴다** — 「없는 것」이 아니다.
- ★★ **모으는 자리 셋의 타입** — 매개변수의 나머지와 배열 패턴의 나머지는 **`Array`**,
  객체 패턴의 나머지는 **`[object Object]`**(평범한 객체)다.
- ★★★ **`[...a, b]` 와 `[a, ...b, c] = arr` 이 갈리는 이유는 대괄호가 같아도 역할이 다르기 때문**이다.
  앞엣것은 **값을 만드는 배열 리터럴**이라 스프레드가 어디에 와도 되고,
  뒤엣것은 **받는 패턴**이라 나머지가 마지막이어야 한다(`Rest element must be last element`).
  ★ 같은 이유로 `[...a,]` 는 되고 `const [...r,] = arr` 은 안 된다.
- ★★★ **`[4]` 의 설정에 달린 칸은 0 / 12** 다. **엄격·비엄격이 한 칸도 안 갈린다.**
  ★ [08번](../08-function-forms-and-parameters/2-summary.md)은 1/9·7/12·7/20,
  [09번](../09-call-apply-bind/2-summary.md)은 15/24, [10번](../10-destructuring-assignment/2-summary.md)은 2/12 였다.
  ★★ **점 셋의 규칙은 모드와 완전히 무관하다** — 고정 행으로 세어 두면 **0도 결론**이 된다.

### 2. 로그를 심으면 무엇이 보이나 — **세 자리가 다른 연산을 부른다** ★★★

**출력**

```text
===== node20 js08b-11b-traps.js (exit=0) =====
[1] object spread -- ownKeys, then a descriptor and a get per key
  { ...traced(2 keys) }         ["ownKeys","getOwnPropertyDescriptor a","get a","getOwnPropertyDescriptor b","get b"]
  { ...traced(0 keys) }         ["ownKeys"]
  Object.assign({}, traced)     ["ownKeys","getOwnPropertyDescriptor a","get a"]
  const { ...r } = traced       ["ownKeys","getOwnPropertyDescriptor a","get a"]
  const { a, ...r } = traced    ["get a","ownKeys","getOwnPropertyDescriptor b","get b"]

[2] array spread -- the iterator protocol, and nothing else
  [...tracedIterable(2)]        ["read Symbol.iterator","next 0","next 1","next 2"]
  [0, ...it(1), 9]              ["read Symbol.iterator","next 0","next 1"]
  f(...it(2))                   ["read Symbol.iterator","next 0","next 1","next 2"]
  { ...it(2) }  object place    ["read Symbol.iterator"]
  new Set([...it(1)])           ["read Symbol.iterator","next 0","next 1"]

[3] a getter is called once and its value is stored -- the getter itself is not copied
  source read twice             [2,3]
  copy read twice               [1,1]
  descriptor in the source      ["get","set","enumerable","configurable"]
  descriptor in the copy        {"value":1,"writable":true,"enumerable":true,"configurable":true}
  getter calls so far           3

[4] a setter in the target is skipped by spread but not by assign
  { ...sink, k: 1 } -> k is         1
  setter calls after spread         0
  setter calls after Object.assign  1
  spread target descriptor          ["value","writable","enumerable","configurable"]
```

**왜 그런가**

- ★★★ **객체 자리는 `ownKeys` 한 번 + 키마다 `getOwnPropertyDescriptor` 한 번, `get` 한 번**을 부른다.
  두 키면 다섯 번이다. 빈 객체면 **`ownKeys` 한 번**뿐이다.
  ★ **디스크립터를 먼저 보는 이유는 「열거 가능한가」를 가리기 위해서**다 —
  그래서 비열거 프로퍼티는 `get` 까지 가지 않고 걸러진다(10번의 객체 나머지와 같은 규칙).
  ★ `Object.assign` 과 `const { ...r } = ` 도 같은 트랩 순서를 쓴다 — **한 연산의 세 얼굴**이다.
  ★ `const { a, ...rest }` 만 순서가 다르다 — **`a` 를 먼저 `get` 한 뒤** 나머지를 훑는다.
- ★★★ **`{ ...it(2) }` 의 로그가 `["read Symbol.iterator"]` 한 줄뿐인 것이 증명이다.**
  객체 자리는 **`Symbol.iterator` 를 「프로퍼티로 읽었을 뿐」 부르지 않았다.**
  ★★ 값으로는 그냥 객체 하나가 나올 뿐이라 **이유가 안 보인다.** 로그라야 보인다 —
  그래서 이 주제의 본체 창이 **로그 심기**다.
- ★★ **호출 자리의 로그는 배열 자리와 한 글자도 같다**(`read Symbol.iterator, next 0, next 1, next 2`).
  **두 자리는 같은 규칙**이다. 다른 것은 객체 자리 하나뿐이다.
- ★★★ **`[3]` — 원본은 읽을 때마다 늘어나고(`[2,3]`) 복사본은 늘 같다(`[1,1]`).**
  디스크립터가 **`["get","set","enumerable","configurable"]`** 에서
  **`{"value":1,"writable":true,"enumerable":true,"configurable":true}`** 로 바뀌었다.
  ★★ **getter 가 한 번 불려 그 값이 굳은 것**이다. **getter 자체는 복사되지 않는다.**
- ★★★ **`[4]` — 스프레드는 setter 를 0회, `Object.assign` 은 1회 부른다.**
  ★★ **스프레드는 프로퍼티를 「정의」하고 `Object.assign` 은 「대입」한다.**
  대상에 setter 가 있으면 대입은 그것을 타고, 정의는 그것을 덮어쓴다 —
  출력에서 `{ ...sink, k: 1 }` 의 `k` 가 **`1`**(getter 의 `"from getter"` 가 아니다)이고
  디스크립터가 `["value","writable",...]` 인 것이 그 증거다.

### 3. 얕은 복사가 무엇을 만드나 — **한 겹만 새것이다** ★★

**출력**

```text
===== node20 js08b-11c-shallow.js (exit=0) =====
[1] one level deep is copied, the rest is shared
  original after editing the copy         {"n":1,"inner":{"deep":99},"list":[1,2,3]}
  copy                                    {"n":99,"inner":{"deep":99},"list":[1,2,3]}
  copy.inner === original.inner           true
  copy.list === original.list             true
  array spread, same story                [{"deep":99}]
  arrCopy[0] === arrOrig[0]               true

[2] what a spread copy loses
  instance own keys                       ["x","own"]
  copy own keys                           ["x","own"]
  p instanceof Point                      true
  pc instanceof Point                     false
  p.double (prototype getter)             6
  pc.double                               undefined
  typeof pc.kind                          undefined
  non-enumerable 'hidden' copied?         false
  symbol key copied?                      true
  prototype of the copy                   true

[3] arrays -- spread reads the iterator, so holes and extra keys change shape
  sparse array                            [1,null,3]
  1 in sparse (hole present?)             false
  [...sparse]                             [1,null,3]
  1 in [...sparse]                        true
  [...sparse].length                      3
  extra key survived?                     false
  Array.from(sparse)                      [1,null,3]
  sparse.slice() keeps the hole           false
  { ...sparse } (object place)            {"0":1,"2":3,"tag":"extra"}

[4] merging -- what each form does with the same two objects
  { ...base, ...patch }                   {"a":1,"inner":{"deep":2},"b":2}
  Object.assign({}, base, patch)          {"a":1,"inner":{"deep":2},"b":2}
  nested object is replaced, not merged   {"deep":2}
  [...listBase, ...listPatch]             [1,2,3]
  [listBase, listPatch] (no spread)       [[1,2],[3]]
  [...listBase].concat is the same        [1,2,3]
```

**왜 그런가**

- ★★★ **클래스 인스턴스를 스프레드하면 넷을 잃는다** —
  ① **프로토타입**(`pc instanceof Point` 가 `false`) ② **메서드**(`typeof pc.kind` 가 `undefined`)
  ③ **프로토타입의 getter**(`pc.double` 이 `undefined`) ④ **비열거 프로퍼티**(`hidden` 이 없다).
  ★★ **자기 것이고 열거 가능한 데이터 프로퍼티만 남는다** — 출력의 키 목록이 원본과 같은 `["x","own"]` 이라
  **얼핏 「다 복사됐다」로 보인다.** 잃은 것은 키 목록에 안 나타난다.
- ★★ **심볼 키는 온다**(`true`). 복사본의 프로토타입은 **`Object.prototype`** 이다 — **평범한 객체**가 된다.
  ★ 그래서 도메인 객체를 스프레드하면 **조용히 자료 덩어리로 강등**된다.
- ★★★ **`1 in sparse` 는 `false` 인데 `1 in [...sparse]` 는 `true`** 다.
  **구멍이 진짜 `undefined` 슬롯으로 메워진 것**이다 — 이터레이터가 그 자리에서 `undefined` 를 내주기 때문이다.
  ★ **`slice()` 는 구멍을 유지한다**(`false`). 같은 「복사」인데 결과가 다르다.
  ★ **배열의 여분 프로퍼티(`tag`)는 안 온다** — 이터레이터는 원소만 낸다.
- ★★ **같은 희소 배열을 객체 자리에 넣으면 정반대**다 — `{ ...sparse }` 가 `{"0":1,"2":3,"tag":"extra"}` 다.
  **구멍은 키째 빠지고 `tag` 는 온다.**
  ★★ **한 값에 두 자리를 대면 서로 다른 답이 나온다** — 10번 `[4]` 와 같은 모양의 증거다.
- ★★ **중첩 객체는 병합되지 않고 갈아치워진다.** `{ ...base, ...patch }.inner` 가 `{"deep":2}` 다.
  `Object.assign` 도 같다 — **깊은 병합은 둘 다 안 해 준다.**

### 4. 세 자리는 무엇을 보고 고르나 ★★★

**출력** — 1번 `[1]` 과 2번 `[2]` 가 답의 근거다.

**왜 그런가**

- ★★ **한 낱말로** — 배열 자리와 호출 자리는 **이터러블**, 객체 자리는 **프로퍼티**다.
- ★★★ **유사 배열을 펴려면 `apply` 나 `Array.from`** 을 쓴다.
  스프레드는 **`Symbol.iterator` 만 보므로** `{ 0: 'a', length: 1 }` 을 못 편다 — `TypeError` 다.
- ★★ **서로 못 덮는 자리** — **`apply` 는 `Set` 을 못 편다**(조용히 0개),
  **스프레드는 유사 배열을 못 편다**(`TypeError`). 09번에서 확인한 대비가 그대로다.
- ★ **`Array.from` 은 두 문을 다 연다** — 이터러블이면 그쪽으로, 아니면 `length` 로 읽는다.
  그래서 **스프레드가 못 하는 일을 한다.** 정본은 [목록의 **26번 주제**](../26-array-search-flatten-and-create/)다.

### 5. 스프레드와 `Object.assign` 은 무엇이 다른가 ★★

**출력** — 2번 `[4]` 의 네 줄이 답이다.

**왜 그런가**

- ★★ **대상에 setter 가 있을 때 갈린다.** 스프레드는 setter 를 **0회**, `Object.assign` 은 **1회** 부른다.
- ★★ **스프레드는 프로퍼티를 「정의」한다** — 대상에 무엇이 있든 **새 데이터 프로퍼티로 덮어쓴다.**
  **`Object.assign` 은 「대입」한다** — 대상에 setter 가 있으면 **그것을 타고**, 없으면 값을 넣는다.
  ★ 그래서 대상이 평범한 객체면 결과가 같아 보이고, **접근자가 섞이면 갈린다.**
  ★ 읽는 쪽도 다르다 — 둘 다 **원본의 getter 는 부른다.** 갈리는 것은 **대상 쪽**이다.
- ★ **정본은 [목록의 27번 주제](../27-object-static-methods/)다**. 여기서는 갈리는 한 자리만 본다.

### 6. 나머지는 왜 마지막이어야 하나 ★★

**출력** — 1번 `[4]`·`[5]` 의 열두 줄이 답이다.

**왜 그런가**

- ★★ **세 자리 모두 `SyntaxError`** 이고 문구가 두 가지다 —
  매개변수는 `Rest parameter must be last formal parameter`,
  패턴(배열·객체)은 `Rest element must be last element` 다.
- ★★★ **펴는 쪽이 자리가 자유로운 이유는 「값을 만드는 중」이기 때문**이다.
  `[0, ...a, 9]` 는 원소를 순서대로 쌓는 일이라 중간에 와도 된다.
  **모으는 쪽은 「남은 것 전부」라는 뜻**이라 **뒤에 무엇이 오면 「남은 것」이 정의되지 않는다.**
  ★ 즉 **문법 제약이 아니라 뜻의 제약**이다.
- ★ **기본값을 달면 `Rest parameter may not have a default initializer`**(매개변수) 또는
  `Invalid destructuring assignment target`(패턴)이고, **꼬리 쉼표를 붙이면 `Rest element must be last element`** 다.
  ★ 「남은 것 전부」에는 **없을 때 쓸 기본값이 필요 없다** — 없으면 빈 배열·빈 객체다.

### 7. 어디서 조용히 틀리나 ★★★

**출력** — 1번 `[1]`, 3번 `[1]`·`[2]`·`[3]` 이 각각 근거다.

**왜 그런가**

- ★★★ **에러 없이 틀리는 자리 넷** —
  ① **`{ ...이터러블 }` 이 `{}` 가 되는 것** — `Set`·`Map`·제너레이터.
  ② **`{ ...null }` 이 `{}` 가 되는 것** — 「대상이 비었다」가 안 드러난다.
  ③ **얕은 복사라 중첩이 공유되는 것** — 원본이 바뀌어도 아무 신호가 없다.
  ④ **클래스 인스턴스를 스프레드해 프로토타입과 메서드를 잃는 것** — 키 목록은 그대로라 눈에 안 띈다.
  ★ 다섯째로 **희소 배열의 구멍이 메워지는 것**도 같은 집안이다.
- ★★★ **①이 [09번](../09-call-apply-bind/2-summary.md)의 `apply(t, new Set(...))` 과 같은 모양**이다.
  둘 다 **「이터러블이니까 될 것」이라는 기대**가 **자리를 잘못 고른 것**이고, 둘 다 **조용히 0개**가 된다.
- ★★ **비싼 getter 가 있는 객체에 `{ ...obj }` 를 쓰면 전부 불린다.**
  2번 `[1]` 의 트랩 로그가 그것을 보인다 — 필요한 키만 적으면 그 키만 부른다.

### 8. 보장인가 엔진 사정인가 ★★★

**출력**

```text
===== ./js08b-vdiff.sh 11 (exit=0) =====
  DIFFERENT js08b-11a-three-places.js
      18c18
      <   f(...obj)                                -> TypeError: Found non-callable @@iterator
      ---
      >   f(...obj)                                -> TypeError: Spread syntax requires ...iterable[Symbol.iterator] to be a function
  same      js08b-11b-traps.js
  same      js08b-11c-shallow.js
  ----
  identical on node18 and node20: 2   different: 1
```

갈린 블록은 v18 쪽도 싣는다.

```text
===== node18 js08b-11a-three-places.js (exit=0) =====
[1] spread -- three places, three different rules
  [...arr]                                 -> [1,2]
  [0, ...arr, 3]                           -> [0,1,2,3]
  [...'ab']                                -> ["a","b"]
  [...new Set([1, 1, 2])]                  -> [1,2]
  [...new Map([['k', 1]])]                 -> [["k",1]]
  [...obj]                                 -> TypeError: objSrc is not iterable
  { ...obj }                               -> {"a":1,"b":2}
  { ...arr }                               -> {"0":1,"1":2}
  { ...'ab' }                              -> {"0":"a","1":"b"}
  { ...new Set([1, 2]) }                   -> {}
  { ...7 }                                 -> {}
  { ...null }                              -> {}
  { ...undefined }                         -> {}
  [...null]                                -> TypeError: null is not iterable
  f(...arr)                                -> [1,2]
  f(...'ab')                               -> ["a","b"]
  f(...obj)                                -> TypeError: Found non-callable @@iterator

[2] later wins -- object spread is just property copying in order
  { ...obj, a: 9 }                         -> {"a":9,"b":2}
  { a: 9, ...obj }                         -> {"a":1,"b":2}
  { ...{ a: 1 }, ...{ a: 2 } }             -> {"a":2}
  { ...obj, ...{ b: undefined } }          -> {"a":1,"b":"<undefined>"}
  array spread does not merge              -> [1,2,2,3]

[3] rest -- three places, always the last one
  function (a, ...r) with (1, 2, 3)        -> [1,[2,3]]
  const [a, ...r] = [1, 2, 3]              -> [1,[2,3]]
  const { a, ...r } = { a: 1, b: 2 }       -> [1,{"b":2}]
  rest of an array pattern is an Array     -> true
  rest of an object pattern is an Object   -> [object Object]
  rest param is an Array                   -> true

[4] which form each place accepts -- SyntaxError or not
  form                                    sloppy  strict
  [...a, b]  spread not last              ok      ok
  [a, ...b] = arr  rest not last          ERR     ERR
  function f(...r, b)                     ERR     ERR
  function f(...r = [])                   ERR     ERR
  const [...r = []] = []                  ERR     ERR
  const { ...r, a } = {}                  ERR     ERR
  const { a, ...r } = {}                  ok      ok
  const [...r,] = []  trailing comma      ERR     ERR
  [...a,]  spread then comma              ok      ok
  f(...a,)  call trailing comma           ok      ok
  const { ...{ a } } = {}                 ERR     ERR
  const [...[a, b]] = [1, 2]              ok      ok
  settings-dependent cells                0 of 12

[5] the messages behind the ERR cells
  [a, ...b] = arr  rest not last          SyntaxError: Rest element must be last element
  function f(...r, b)                     SyntaxError: Rest parameter must be last formal parameter
  function f(...r = [])                   SyntaxError: Rest parameter may not have a default initializer
  const [...r = []] = []                  SyntaxError: Invalid destructuring assignment target
  const { ...r, a } = {}                  SyntaxError: Rest element must be last element
  const [...r,] = []  trailing comma      SyntaxError: Rest element must be last element
  const { ...{ a } } = {}                 SyntaxError: `...` must be followed by an identifier in declaration contexts
```

브라우저에 같은 줄을 던진 결과는 이렇다.

```text
===== google-chrome --headless --dump-dom page11.html | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' (exit=0) =====
  engine                              Chrome/151.0.0.0
  { ...null }                         {}
  [...null]                           TypeError: null is not iterable
  { ...7 }                            {}
  { ...'ab' }                         {"0":"a","1":"b"}
  { ...new Set([1, 2]) }              {}
  [...new Set([1, 1, 2])]             [1,2]
  [...{ length: 1 }]                  TypeError: {(intermediate value)} is not iterable
  object spread trap order            ownKeys,gopd a,get a
  getter becomes a value              {"value":1,"writable":true,"enumerable":true,"configurable":true}
  spread copy loses the prototype     false,undefined
  hole becomes a slot                 false then true
  f(...r, b) compiles?                SyntaxError: Rest parameter must be last formal parameter
```

**왜 그런가**

- ★★ **두 판이 갈린 자리는 하나**다 — `f(...obj)` 의 예외 **문구**다.
  v18 은 `Found non-callable @@iterator`, v20 은 `Spread syntax requires ...iterable[Symbol.iterator] to be a function` 이다.
- ★★★ **그 차이는 V8 의 사정이다.** 근거 둘 —
  ① **종류가 둘 다 `TypeError`** 이고 **무엇이 실패하는지가 안 바뀌었다** ·
  ② 명세는 「이터러블이 아니면 `TypeError` 를 던진다」까지만 정하고 **문구를 정하지 않는다.**
  ★ v20 쪽 문구가 **무엇을 기대했는지를 말해 주도록 고쳐진 것**이다 — 진단 품질 개선이지 규칙 변경이 아니다.
  ★★ **[08번](../08-function-forms-and-parameters/2-summary.md)에서도 같은 일이 있었다** —
  네 주제 중 **둘에서 한 건씩, 둘 다 예외 문구**였다. **문구를 근거로 쓰면 판이 오를 때 문서가 조용히 틀린다.**
- ★★ **호스트가 정하는 칸은 0개**다. 브라우저의 열세 줄이 Node 와 전부 같다.
  ★ **문구까지 같은 것은 Chrome 151 이 v20 과 같은 계열의 V8 이기 때문**이다 —
  **같은 줄이 Node 18 에서는 달랐다**는 것이 그 증거다. 「브라우저와 같다」를 명세 보장으로 읽으면 안 된다.
- ★ **부적용인 창은 셋**이다 — ⑥ `toFixed(20)` · ⑦ `\uXXXX` 펼치기 · **성능 측정**.
  ★★ 성능은 「안 쟀다」가 아니라 「**이 문서가 안 재기로 한 것**」이다.
  스프레드가 객체를 하나 더 만든다는 것은 관찰했지만 **얼마나 드는지는 재지 않았고**,
  그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.

### 9. 경계 — 어디까지가 이 주제인가 ★★

**출력** — 없다. 이 문항은 지도 문항이다.

**왜 그런가**

| 주제 | 정본 |
|---|---|
| 나머지 매개변수 대 `arguments` | [08 — 함수 정의 형태와 매개변수](../08-function-forms-and-parameters/2-summary.md) |
| `apply` 와 유사 배열 · 인자 개수 상한 | [09 — `call`·`apply`·`bind`](../09-call-apply-bind/2-summary.md) |
| 구조 분해 패턴의 규칙 | [10 — 구조 분해 할당](../10-destructuring-assignment/2-summary.md) |
| 이터러블 프로토콜 계약 | [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) |
| `Object.assign` API | [목록의 **27번 주제**](../27-object-static-methods/) |
| 깊은 복사 수단 비교 | [목록의 **48번 주제**](../48-deep-copy-methods-compared/) |
| 프로퍼티 열거 순서 | [목록의 **13번 주제**](../13-object-literals-and-properties/) |
| `Array.from` 의 두 문 | [목록의 **26번 주제**](../26-array-search-flatten-and-create/) |

- ★★★ **10번에서 이어받는 것** — 「두 패턴이 서로 다른 문을 쓴다」는 결론을 그대로 받아,
  **펴는 쪽에서도 같은 갈림이 있다**는 것을 트랩 로그로 증명한다.
- ★★ **Go 의 `xs...` 와 닮은 것** — **가변 인자를 한 번에 펴 넘긴다**는 점이다.
  **다른 것 셋** — Go 는 **타입이 맞아야 하고**(`[]T` 를 `...T` 자리에만),
  **객체 자리가 아예 없으며**(맵을 펴는 문법이 없다), **펴는 것이 마지막 인자에만** 온다.
  정본은 [Go 갈래의 12번](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/)이다.
- ★ **이 주제가 끝까지 책임지는 것 셋** —
  ① **세 자리가 두 규칙으로 갈린다는 것**과 그것을 **트랩 로그로 증명하는 법**
  ② **객체 자리가 아무것도 거부하지 않는다는 것**과 그 조용한 실패
  ③ **얕은 복사가 잃는 것 넷**과 희소 배열에서 갈리는 자리.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js08b-11a-three-places.js` | ★★★ **세 자리 격자** · 터지는 셋과 조용히 비는 넷 · **문법 12형태 × 두 모드 0 / 12** | node20 1벌 + node18 1벌(**갈렸다**) |
| `js08b-11b-traps.js` | ★★★ **트랩 호출 순서** · `{ ...it }` 이 이터레이터를 안 부르는 것 · getter/setter | node20 1벌 + node18 대조 1벌 |
| `js08b-11c-shallow.js` | **얕은 복사** · 인스턴스가 잃는 넷 · **희소 배열의 구멍** · 병합 | node20 1벌 + node18 대조 1벌 |
| `js08b-11h-browser.js` | ★★★ **호스트가 정하는 칸 0개** | Chrome 151 1벌 |
| `js08b-11x-forms.js` | 형태 — `node --check` **진단 0줄**(빈 출력도 블록으로) | node20 1벌 |
| `js08b-vdiff.sh` | 세 스크립트 중 **둘이 두 판에서 한 글자도 같다**는 것 | 1벌 |
| `js08b-versions.sh` | 이 문서의 모든 출력이 **어느 판에서 나왔나** | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · x86-64 Linux)에서만** 그렇다.

- ★★★ **`f(...obj)` 의 예외 문구** — **두 판에서 실제로 갈렸다.**
  `Found non-callable @@iterator`(v18) 대 `Spread syntax requires ...iterable[Symbol.iterator] to be a function`(v20).
  **종류는 둘 다 `TypeError`** 다.
- ★★ **나머지 예외 문구 전부** — `Rest element must be last element` ·
  `` `...` must be followed by an identifier in declaration contexts `` ·
  `{(intermediate value)} is not iterable`. **문구에 소스 텍스트가 박히는 것**도 10번과 같다.
- ★ **브라우저와 Node 20 의 문구가 같은 것** — **같은 계열의 V8 이기 때문**이다. 명세가 정한 것이 아니다.

**세 자리가 두 규칙으로 갈리는 것 · 객체 자리가 아무 값도 거부하지 않는 것 · 트랩 호출 순서(`ownKeys` → 디스크립터 → `get`) · 객체 자리가 자기 것이고 열거 가능한 것만 가져오고 심볼 키를 포함하는 것 · getter 가 값으로 굳는 것 · 스프레드가 대상의 setter 를 안 부르는 것 · 나중에 적은 것이 이기는 것 · 얕은 복사라는 것 · 복사본의 프로토타입이 `Object.prototype` 인 것 · 이터레이터가 구멍을 `undefined` 로 메우는 것 · 모으는 자리가 마지막이어야 하는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 다른 엔진(SpiderMonkey·JavaScriptCore)에서의 **문구** ·
  제너레이터를 편 경우(`[...gen]`) · `Proxy` 의 `getPrototypeOf`·`has` 트랩이 불리는지(로그에 안 나왔지만 **없다는 증명은 아니다**) ·
  `structuredClone` 과의 비교(48번의 몫) · TypedArray·`ArrayBuffer` 스프레드 ·
  Node 18 보다 낮은 판.
- ★ **못 잰 것** — **스프레드와 `concat`·`Object.assign`·`slice` 의 비용 차이.**
  객체가 하나 더 만들어진다는 것은 관찰했지만 **얼마나 드는지는 재지 않았다.**
  그래서 이 문서에는 「느리다」·「빠르다」가 한 줄도 없다.
- ★ **부적용인 창** — ⑥ `toFixed(20)` · ⑦ `\uXXXX` 펼치기.
  「안 쟀다」가 아니라 「**이 주제에는 그 칸이 없다**」이다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **`f(...obj)` 의 예외 문구** — **이미 한 번 바뀌었다.** 다음 판에서 또 바뀔 수 있다.
- ★★ **나머지 예외 문구** — 1번 블록의 `[5]` 에 일곱 줄이 들어 있다.
- ★ **브라우저 쪽 0개** — 호스트나 엔진 계열이 바뀌면 그 줄이 바뀐다.
- **세 자리의 규칙과 트랩 순서는 다시 돌릴 필요가 없다** — ES2015(객체 자리는 ES2018) 이후 바뀐 적이 없다.
