# js/syntax/18 — `for...in` 과 열거: 「체인을 걷는 열거는 `for...in` 하나뿐이다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다.** 표준 출력뿐이고 스택트레이스가 없다.
> ★★ **이 주제의 블록은 두 판에서 identical 이다** — 그래서 양쪽을 나란히 실은 자리가 없다.
> ★ **이 주제의 탐침은 전부 비엄격 스크립트다.** 엄격에서 따로 돌리지 않았다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다
> (`js16b-18a-grid.js` → 1번 · `js16b-18b-array.js` → 2번 · `js16b-18d-mutate.js` → 3번 · `js16b-18c-hasown.js` → 4번 · `js16b-18f-refimpl.js` → 5번).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 예외 **문구**(V8) | ★★★ 격자의 `o`/`.` · **예외의 종류** |
> | ★★ `Proxy` 가 낀 체인의 **트랩 순서** | ★★★ Proxy 없는 체인의 **`for-in` 순서**(ES2020) |
> | ★★ 순회 중 변경의 **비보장 행** | ★★ 처리 전 삭제 무시 · 자기 자신에 추가한 키 미방문 |
>
> ★ **이 주제의 블록에는 주소도 시간도 난수도 안 찍힌다.** 같은 판에서 다시 돌리면 한 글자도 안 변한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여섯 종 × 아홉 문법 — **체인에 닿는 열은 `for-in` 과 `in` 둘, 목록은 `for-in` 하나** ★★★

**출력**

```text
===== node20 js16b-18a-grid.js (exit=0) =====
[1] who sees what   (o = sees it, . = does not)
                          for-in   keys     entries  JSON     {...}    assign   gOPN     ownKeys  in
own enumerable            o        o        o        o        o        o        o        o        o
own non-enumerable        .        .        .        .        .        .        o        o        o
own symbol                .        .        .        .        o        o        .        o        o
inherited enumerable      o        .        .        .        .        .        .        .        o
inherited non-enumerable  .        .        .        .        .        .        .        .        o
inherited symbol          .        .        .        .        .        .        .        .        o
seen                      2/6      1/6      1/6      1/6      2/6      2/6      2/6      3/6      6/6
columns that reach the chain: ["for-in","in"]

[2] for-in order across two links
  Object.keys(parent)  ["1","2","b","a"]
  Object.keys(child)   ["3","9","z","y"]
  for-in child         ["3","9","z","y","1","2","b","a"]

[3] own NON-enumerable key, parent enumerable key, same name
  for-in c3            ["other"]
  'shared' in c3       true   c3.shared  own, hidden

[4] trap log -- what for-in asks each link of the chain
  for-in keys ["c","p"]
  trap log    ["C.ownKeys","C.getPrototypeOf","P.ownKeys","P.getPrototypeOf","C.gopd(c)","C.gopd(p)","C.getPrototypeOf","P.gopd(p)"]
  Object.keys trap log ["C.ownKeys","C.gopd(c)"]
```

**왜 그런가**

- ★★★ **`seen` 줄** — `for-in 2/6` · `keys 1/6` · `entries 1/6` · `JSON 1/6` · `{...} 2/6` · `assign 2/6` · `gOPN 2/6` · `ownKeys 3/6` · `in 6/6`.
- ★★★ **`columns that reach the chain: ["for-in","in"]`** — 두 개다. `in` 은 **이름 하나를 묻는 연산자**라 목록이 아니다.
  그래서 **체인을 걷는 목록은 `for-in` 하나**다. 나머지 일곱 열은 **상속 세 줄이 전부 `.`** 이다.
- ★★ **`{...}`·`assign` 과 `for-in` 은 둘 다 `2/6` 인데 겹치는 칸은 own 열거 한 칸뿐**이다 —
  앞쪽은 **own 심볼**을, `for-in` 은 **상속 열거**를 둘째 칸으로 가진다. 개수가 같다는 것은 아무것도 말하지 않는다.
- ★★ **상속 심볼은 열거 가능하다**(`proto` 를 리터럴로 만들었다). 그래도 `for-in` 에 안 나온다 —
  "Returned property keys do not include keys that are Symbols."
- ★★★ **`[2]` `for-in child` 는 `["3","9","z","y","1","2","b","a"]`** — 자식의 `Object.keys` 뒤에 부모의 `Object.keys` 를 **그대로 이어 붙인 것**이다.
  **부모의 `"1"`·`"2"` 가 자식의 `"z"`·`"y"` 뒤**에 온다 — 세 덩어리 순서는 **칸마다** 걸린다(8번).
- ★★★ **`[3]` `for-in c3` 은 `["other"]`** 다. 부모의 열거 가능한 `shared` 가 **own 비열거 `shared` 에 가려졌다**(6번).
  그러면서 `'shared' in c3` 는 `true`, `c3.shared` 는 `own, hidden` — **조회에서는 보인다.**
- ★★ **`[4]` `for-in` 로그에 `get` 은 0줄**이다. `for...in` 은 **키만 내놓고 값을 안 읽는다.**
  `Object.keys` 로그는 `["C.ownKeys","C.gopd(c)"]` — **`getPrototypeOf` 가 없다.** 첫 칸에서 멈춘다는 격자의 결론이 발자국으로 다시 선다.

### 2. 배열의 `for...in` — **문자열 인덱스 · 구멍 건너뜀 · 붙인 것과 프로토타입 확장이 섞인다** ★★★

**출력**

```text
===== node20 js16b-18b-array.js (exit=0) =====
[1] what are the keys?
  i="0"  typeof string  i + 1 = "01"
  i="1"  typeof string  i + 1 = "11"
  i="3"  typeof string  i + 1 = "31"
  for-of values  ["a","b","<undefined>","d"]   <- the hole at 2 is visited by for-of, skipped by for-in

[2] an extra property and a prototype extension
  for-in arr          ["0","1","3","extra","polluted"]
  for-in []           ["polluted"]
  for-of arr          ["a","b","<undefined>","d"]
  Object.keys(arr)    ["0","1","3","extra"]
  for-in + hasOwn     ["0","1","3","extra"]

[3] the same extension, defined non-enumerable
  for-in arr          ["0","1","3","extra"]
  typeof arr.quiet    function

[4] built-in methods and length
  'map' in arr        true   enumerable? false
  'length' in arr     true   enumerable? false
```

**왜 그런가**

- ★★★ **`typeof string`, `i + 1` 이 `"01"`·`"11"`·`"31"`** 이다. 배열 인덱스도 **문자열 프로퍼티 키**라 `+` 가 이어 붙이기가 된다(13편).
  **구멍(2번 자리)은 0줄** — `i="0"`·`"1"`·`"3"` 세 줄뿐이다. 구멍은 **프로퍼티가 없는 칸**이라 열거할 것이 없다.
- ★★ **`for-of` 는 2번 자리에 `<undefined>`** 를 낸다. 인덱스 범위를 돌며 값을 읽기 때문이다(규칙은 19편).
- ★★★ **`for-in arr` = `["0","1","3","extra","polluted"]`**, **`for-in []` = `["polluted"]`**.
  `Array.prototype` 에 **대입으로** 붙인 것은 열거 가능이라 **모든 배열의 `for-in`** 에 나온다. 빈 배열도 예외가 아니다.
- ★★ **`Object.keys(arr)` 와 `for-in + hasOwn` 은 같다** — `["0","1","3","extra"]`. 가드는 **체인에서 온 `polluted` 만** 거른다.
  ★ **`extra` 는 못 거른다** — 진짜 own 이기 때문이다. 「인덱스만」이 목표라면 가드로는 안 된다(10번).
- ★★ **`[3]` 비열거로 정의하면 `for-in arr` 에서 `quiet` 가 사라진다** — 그런데 `typeof arr.quiet` 는 `function`. 조회는 되고 열거는 안 된다.
- ★ **`[4]` `map`·`length` 는 둘 다 `in` 으로 `true`, `enumerable? false`.** 내장이 전부 비열거라 평소에는 함정이 안 보인다.

### 3. 순회 도중 지우거나 더하면 — **처리 전 삭제는 무시가 보장, 자기 자신에 추가는 미방문이 묶임, 나머지는 관찰** ★★★

**출력**

```text
===== node20 js16b-18d-mutate.js (exit=0) =====
[1] deleting during for-in
delete a not-yet-visited key (c) at a       visited ["a","b"]                 keys after ["a","b"]
delete the current key at each step         visited ["a","b","c"]             keys after []
delete a parent key (p) before it comes     visited ["a"]                     keys after ["a"]

[2] adding during for-in
add a new own key (z) at a                  visited ["a","b"]                 keys after ["a","b","z"]
add a new integer key (0) at a              visited ["a","b"]                 keys after ["0","a","b"]
add a parent key (q) at a                   visited ["a","b"]                 keys after ["a","b"]
delete then re-add b at a                   visited ["a","b","c"]             keys after ["a","c","b"]

[3] the same delete, with Object.keys(...).forEach
Object.keys(snap).forEach, delete c at a    ["a=1","b=2","c=undefined"]
```

**왜 그런가**

- ★★★ 행마다 칸을 가른다 — 「명세 알고리즘」 열은 5번의 `[2]` 에서 온다.

| 행 | 이 판 `visited` | 칸 | 근거 |
|---|---|---|---|
| 처리 전 `c` 삭제 | `["a","b"]` | ★★★ **명세 보장** | "A property that is deleted before it is processed by the iterator's next method is ignored." |
| 매번 지금 키 삭제 | `["a","b","c"]` | ★★ **집합 보장 · 순서 관찰** | 지운 것은 전부 이미 처리된 키. 첫 삭제로 순서 제약은 풀린다 |
| 윗칸 `p` 삭제 | `["a"]` | ★ **보장으로 읽힌다(해석)** | 아래 둘째 불릿 |
| 자기에게 `z` 추가 | `["a","b"]` | ★★★ **명세가 묶는다** | 「obj 자신에 추가」는 `CreateForInIterator` 제약을 **안 푼다** — 떠 둔 키 목록대로 |
| 자기에게 `0` 추가 | `["a","b"]` | ★★★ **명세가 묶는다** | 같은 이유. **정렬상 맨 앞 키인데도** 안 나온다 |
| 윗칸에 `q` 추가 | `["a","b"]` | ★★★ **관찰** | 「체인 위 객체에 추가」가 제약을 푼다 → "not guaranteed to be processed" |
| `b` 지우고 다시 넣기 | `["a","b","c"]` | ★★ **관찰** | 삭제가 제약을 푼다. 다시 넣은 `b` 는 새로 더한 것 |

- ★★ **윗칸 `p` 행** — 삭제 문장은 "Properties of the target object may be deleted during enumeration." 로 시작해 **대상 객체**를 말한다.
  그런데 윗칸의 키는 "must be obtained by invoking EnumerateObjectProperties passing the prototype object as the argument" — 윗칸은
  **그 안쪽 열거의 대상 객체**다. 그래서 같은 문장이 걸린다고 **읽었다.** 문장이 직접 적은 것은 아니므로 「해석」으로 표시했다.
- ★★ **`keys after`** — 정수 키 `0` 을 더한 행은 `["0","a","b"]` 로 **맨 앞에 섰는데도** 방문되지 않았다.
  지웠다 다시 넣은 행은 `["a","c","b"]` 인데 **방문 순서는 `a,b,c`** — 시작 때 뜬 순서대로 간 것으로 읽힌다(관찰).
- ★★ 「추가는 명세가 안 묶는다」는 **윗칸 추가·재추가 두 행에만 맞다.** 자기 자신에 더한 두 행은 둘째 겹이 묶는다.
- ★★★ **`[3]` `Object.keys(snap).forEach` 는 지운 `c` 도 방문한다 — 값은 `undefined`**(`"c=undefined"`).
  이미 만든 배열(스냅숏)을 돌기 때문이다. `for-in` 이 처리 전 삭제를 **건너뛰는 것과 정반대**다.

### 4. `hasOwnProperty` 세 객체 — **밖에서 묻는 두 방법만 셋 다 `true`** · `for-in null` 은 조용하다 ★★★

**출력**

```text
===== node20 js16b-18c-hasown.js (exit=0) =====
[1] three unusual objects, three ways to ask own-ness
Object.create(null)  o.hasOwnProperty('k')                        -> TypeError o.hasOwnProperty is not a function
Object.create(null)  Object.hasOwn(o, 'k')                        -> true
Object.create(null)  Object.prototype.hasOwnProperty.call         -> true
own hasOwnProperty() {return false}  o.hasOwnProperty('k')        -> false
own hasOwnProperty() {return false}  Object.hasOwn(o, 'k')        -> true
own hasOwnProperty() {return false}  Object.prototype.hasOwnProperty.call-> true
own hasOwnProperty: 42  o.hasOwnProperty('k')                     -> TypeError o.hasOwnProperty is not a function
own hasOwnProperty: 42  Object.hasOwn(o, 'k')                     -> true
own hasOwnProperty: 42  Object.prototype.hasOwnProperty.call      -> true

[2] for-in over Object.create(null)
for-in bare2                                                      -> ["x","y"]

[3] a symbol key and for-in
for-in withSym                                                    -> ["visible"]
Object.getOwnPropertySymbols(withSym).length                      -> 1

[4] for-in over primitives, null and undefined
for-in 'ab'                                                       -> ["0","1"]
for-in 42                                                         -> []
for-in true                                                       -> []
for-in null                                                       -> []
for-in undefined                                                  -> []
Object.keys(null)  (for contrast)                                 -> TypeError Cannot convert undefined or null to object
```

**왜 그런가**

- ★★★ **`[1]` 아홉 줄 중 예외 둘** — `Object.create(null)` 과 `hasOwnProperty: 42` 의 `o.hasOwnProperty('k')` 가 **`TypeError`** 다.
  하나는 **빌려 올 윗집이 없어서**, 하나는 **own `42` 가 윗집의 메서드를 가려서**(15편의 조회 규칙) 호출할 것이 함수가 아니다.
- ★★ **자기 `hasOwnProperty()` 를 가진 객체는 `false`** 를 답한다 — **거짓말**이다. `k` 는 own 이다.
  `o.method()` 꼴은 **객체에게 묻는 것**이라 객체가 답을 바꿀 수 있다.
- ★★★ **`Object.hasOwn` 과 `Object.prototype.hasOwnProperty.call` 은 세 객체 모두 `true`** — 둘 다 **객체 밖에서** 묻는다.
- ★★ **`[2]` `Object.create(null)` 에 `for-in` 은 된다**(`["x","y"]`). `for...in` 은 문이라 메서드를 안 빌린다.
- ★★★ **`[4]` 던지는 줄은 하나** — `Object.keys(null)` 의 `TypeError`. **`for-in null`·`for-in undefined` 는 `[]`** 다.
  명세의 `ForIn/OfHeadEvaluation` 이 enumerate 일 때 값이 `undefined`·`null` 이면 **break 완료**를 돌려주기 때문이다 — 몸통이 0회 돈다.
- ★ **`for-in 'ab'` = `["0","1"]`**(문자열 래퍼의 인덱스), **`for-in 42` = `[]`**(래퍼에 열거 가능한 own 이 없다).

### 5. 명세 알고리즘 대 V8 — **키는 같고 발자국은 다르며, 둘 다 적법하다** ★★

**출력**

```text
===== node20 js16b-18f-refimpl.js (exit=0) =====
[1] the same two-link Proxy chain, walked two ways
spec algorithm keys  ["c","p"]
spec algorithm log   ["C.ownKeys","C.gopd(c)","C.getPrototypeOf","P.ownKeys","P.gopd(p)","P.getPrototypeOf"]  (6 entries)
V8 for-in keys       ["c","p"]
V8 for-in log        ["C.ownKeys","C.getPrototypeOf","P.ownKeys","P.getPrototypeOf","C.gopd(c)","C.gopd(p)","C.getPrototypeOf","P.gopd(p)"]  (8 entries)
same keys? true   same log? false

[2] the 18d mutation rows, walked by the hand-ported spec algorithm and by V8's for-in
delete a not-yet-visited key (c) at a     spec ["a","b"]         V8 ["a","b"]         same
delete the current key at each step       spec ["a","b","c"]     V8 ["a","b","c"]     same
delete a parent key (p) before it comes   spec ["a"]             V8 ["a"]             same
add a new own key (z) at a                spec ["a","b"]         V8 ["a","b"]         same
add a new integer key (0) at a            spec ["a","b"]         V8 ["a","b"]         same
add a parent key (q) at a                 spec ["a","b","q"]     V8 ["a","b"]         DIFFERENT
delete then re-add b at a                 spec ["a","b","c"]     V8 ["a","b","c"]     same
```

**왜 그런가**

- ★★ **`[1]` 키는 둘 다 `["c","p"]`**, 로그는 **6줄 대 8줄**이다.
- ★★★ **명세 알고리즘은 칸마다 끝내고 올라간다** — `C.ownKeys → C.gopd(c) → C.getPrototypeOf → P.ownKeys → P.gopd(p) → P.getPrototypeOf`.
  **V8 은 먼저 체인 끝까지 키를 모은다** — `C.ownKeys → C.getPrototypeOf → P.ownKeys → P.getPrototypeOf` — 그다음 키마다 `gopd` 로 확인한다.
  ★ V8 의 `C.gopd(p)` 는 윗칸 키를 내기 전 **아래 칸을 다시 본 것**으로 읽힌다(로그에서 나온 추론이다).
- ★★★ **둘 다 적법하다** — 순서 제약은 "if neither obj nor any object in its prototype chain is a Proxy exotic object …" 일 때만 걸린다.
  **이 체인의 두 칸이 전부 `Proxy`** 라 `CreateForInIterator` 처럼 굴 의무가 없다. 명세가 요구하는 것은 **`[[OwnPropertyKeys]]` 와 `[[GetOwnProperty]]` 를 부른다**는 것까지다.
- ★★★ **`[2]` `DIFFERENT` 는 한 행 — 윗칸에 `q` 를 더한 행**이다. 명세 알고리즘은 `q` 를 방문했고 V8 은 안 했다.
  3번에서 그 행은 **「관찰」 칸**이었다 — **제약이 풀린 행에서만 갈렸다.** 제약이 살아 있는 두 행(자기 자신에 추가)은 `same` 이다.
- ★ 이 생성기는 **이 문서가 명세 단계를 직접 JS 로 적은 것**이다. 정본은 명세 문장이고, 생성기는 그 읽기가 맞는지 **대 보는 도구**다.

### 6. own 비열거가 부모를 가리는 이유 — **처리 판정에 `[[Enumerable]]` 을 안 본다** ★★★

- ★★★ `EnumerateObjectProperties` 의 두 문장이다 —
  "a property of a prototype is not processed if it has the same name as a property that has already been processed by the iterator's next method." ·
  "The values of [[Enumerable]] attributes are not considered when determining if a property of a prototype object has already been processed."
  판정에서 빠지는 것은 **`[[Enumerable]]`** 이다.
- ★★ 「**처리했다**」는 「이름을 봤다」, 「**내놓았다**」는 「반복값으로 돌려줬다」다. own 비열거 키는 **처리는 됐고 내놓지는 않았다.**
  명세 알고리즘에서도 `desc` 가 있으면 먼저 **방문 목록에 넣고**, 그다음에 `enumerable` 일 때만 돌려준다(5번 생성기의 순서가 그렇다).
- ★★ **조회는 own 이 이긴다**(15편) — `c3.shared` 는 own 값 `own, hidden` 이다. **열거가 가리는 것과 조회가 가리는 것이 같은 이름**이라
  「안 보이는데 읽힌다」가 된다. 두 규칙 모두 **아래 칸이 윗칸을 가린다**는 점에서는 한 방향이다.

### 7. 「순회 중 추가」의 비보장 — **엔진들이 원래 같던 자리만 못 박았다** ★★★

- ★★★ **첫 겹**(모든 객체) — 처리 전 삭제는 무시 · 추가한 것은 "not guaranteed to be processed" · 한 이름은 "at most once".
  **둘째 겹**(Proxy·TypedArray·모듈 네임스페이스·구현 제공 이국 객체가 체인에 없을 때) — 반복자는 `CreateForInIterator` 처럼 굴어야 한다.
- ★★★ **제약을 푸는 사건 넷** — `[[Prototype]]` 변경 · obj 나 체인 위 객체에서 **삭제** · **체인 위 객체에** 추가 · `[[Enumerable]]` 변경.
  ★★★ **빠진 것은** 「**obj 자신에 추가**」다. 그래서 3번의 `z`·`0` 두 행은 제약이 살아 있는 채로 **떠 둔 키 목록대로** 끝난다 — 미방문이 묶인다.
- ★★ 노트가 이유를 적었다 — "The list of exotic objects for which implementations are not required to match CreateForInIterator was chosen because implementations historically differed in behaviour for those cases, and agreed in all others."
  ES2020 은 **엔진들이 이미 합의하던 자리만** 못 박았다.
- ★ 순회 중 구조를 바꿔야 하면 **`Object.keys(o)` 로 스냅숏을 먼저** 뜨고, 몸통에서 `Object.hasOwn(o, k)` 로 아직 있나를 확인한다(3번 `[3]`).

### 8. 세 덩어리는 칸마다 — **체인 전체를 다시 정렬하지 않는다** ★★

- ★★★ **칸마다** 걸린다. 1번 `[2]` 에서 **부모의 정수 키 `"1"` 이 자식의 문자 키 `"y"` 뒤**에 왔다.
  체인 전체에 걸렸다면 `"1"`·`"2"`·`"3"`·`"9"` 가 맨 앞에 모였을 것이다. `CreateForInIterator` 도 칸마다 own 키를 **그 칸의** `[[OwnPropertyKeys]]` 순서로 뜬다.
- ★★ **`Object.keys` 순서는 ES2015**(`[[OwnPropertyKeys]]` 의 세 덩어리), **`for...in` 순서는 ES2020**(for-in order 제안) — 둘 다 13편이 인용했다.
  ★ 13편의 정수 키 23후보 가운데 **`"01"`·`"4294967295"` 는 배열 인덱스가 아니라 문자열 키**다 — 칸 안의 첫 덩어리 판정도 13편 것을 그대로 쓴다.
- ★ **조건** — 체인에 **Proxy 등 이국 객체가 없고**, 순회 중 제약을 푸는 사건이 **안 일어났을 때**다.

### 9. 클래스 메서드는 비열거 — **`class` 로 옮기면 `for...in` 이 조용히 바뀐다** ★★

- ★★★ [16편](../16-class-syntax/2-summary.md)의 `js16b-16a-where.js` `[4]` —
  **비열거**: 클래스의 메서드 · 게터 · 정적 메서드(`enumerable false`).
  **열거 가능**: 필드 · 정적 필드 · 객체 리터럴의 메서드와 게터 · **`Old.prototype.method = function`**(`enumerable true`).
  그리고 `Object.keys(C.prototype)` 이 `[]`, `Object.keys(Old.prototype)` 이 `["method"]`.
- ★★ 생성자 함수 버전의 인스턴스는 `for...in` 에 **상속된 `method` 가 나오고**, `class` 버전은 **안 나온다.**
  ★ 이것은 **추론**이다 — 16편의 플래그(실측)와 이 주제의 격자 「`for-in` 은 상속 열거를 적는다」(실측)를 합친 것이고,
  두 인스턴스에 `for-in` 을 직접 던진 줄은 이 배치에 없다.
- ★ 프로토타입에 붙여야 하면 **`Object.defineProperty(..., { enumerable: false })`** 로 정의한다 — 2번 `[3]` 이 그 실측이다.

### 10. 배열에는 `for...of` — **`for...in` 은 프로퍼티를, `for...of` 는 인덱스 범위의 값을 돈다** ★★

- ★★★ **`for...in` = 열거 가능한 문자열 키**(own + 체인), **`for...of` = 배열 반복자가 내는 값**(0 부터 `length - 1` 까지).
- ★★ **구멍** — `for-in` 은 **건너뛰고**(프로퍼티가 없다), `for-of` 는 **`<undefined>`** 로 방문한다. 구멍은 「값이 `undefined` 인 칸」과 **다르다** — 프로퍼티 자체가 없다.
- ★★ **`hasOwn` 가드로는 안 고쳐진다** — `polluted` 는 걸러지지만 **`extra` 가 남고**, 인덱스는 **여전히 문자열**이다.
- ★ `for...of` 의 규칙은 [19편](../19-iterable-protocol-and-for-of/2-summary.md)이 정본이다.

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

- **두 판이 갈린 블록은 이 주제에 0개**다. 대조기가 `DIFFERS` 로 찍은 한 줄은 **19편**의 스프레드 문구다.
- ★★★ **명세 보장** — `for-in` 이 상속 열거를 적고 심볼을 안 적는 것 · own 비열거가 부모를 가리는 것 · 처리 전 삭제를 무시하는 것 ·
  `for-in null` 이 break 완료인 것 · Proxy 없는 체인의 순서(ES2020).
  **V8 관찰** — Proxy 체인의 **트랩 순서**(키 먼저 모으기) · 윗칸 추가 `q` 미방문 · 재추가 `b` 를 원래 자리에서 방문 · 예외 **문구**.
  ★★ **트랩의 종류(`ownKeys`·`gopd`)는 명세가 요구하고, 순서는 V8 이다.**
- ★★ **부적용** — ③ 브랜드 태그(열거의 답은 키 목록이라 `JSON.stringify` 로 다 찍힌다 · 평소 창이 닫힌 자리가 없다) ·
  진단의 `(행,열)`(`SyntaxError` 가 없다). **안 돌렸다** — 두 번 컴파일(엄격/비엄격) · 브라우저.
  ★ 「부적용」은 **잴 것이 없다**는 뜻이고, 「안 돌렸다」는 **잴 것이 있는데 이번에 안 쟀다**는 뜻이다.
- ★★★ 「`for...in` 은 느리다」 — **안 쟀다.** 이 문서에 속도 주장이 한 줄도 없다.

### 12. 경계 — 어디까지가 이 주제인가 ★★

- **own 키 순서 세 덩어리** → 13편 · **`enumerable` 플래그 바꾸기**(`defineProperty`·`freeze` — `freeze` 는 `enumerable` 을 안 건드린다) → 14편 ·
  **조회가 체인을 타는 규칙** → 15편 · **`for...of`** → 19편 · **`Object.keys`/`assign` 의 쓰임** → [목록의 **27번 주제**](../27-object-static-methods/) ·
  **`Proxy` 트랩 계약** → [목록의 **45번 주제**](../45-proxy/).
- ★★★ 15편은 **조회가 체인을 탄다**까지 책임졌다. 이 주제가 더한 것은 **「체인 순회」 — 체인을 걷는 열거**다.
- ★ 이 주제가 끝까지 책임지는 것 셋 — ① **체인에 닿는 목록은 `for-in` 하나**라는 격자 ·
  ② **가리기가 `enumerable` 을 안 본다**는 규칙 · ③ **순회 중 변경의 보장/관찰 가르기**.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js16b-18a-grid.js` | ★★★ **6종 × 9열 격자** · 체인에 닿는 열 · `for-in` 순서(own 뒤 부모) · 가리기 · 트랩 로그(V8) | node20 1벌 + node18 대조 |
| `js16b-18b-array.js` | ★★★ 배열 `for-in` 의 문자열 인덱스 · 구멍 · `extra`/`polluted` 섞임 · `hasOwn` 가드 · 비열거 정의 | node20 1벌 + node18 대조 |
| `js16b-18c-hasown.js` | ★★ `hasOwnProperty` 세 객체 · `Object.create(null)` 의 `for-in` · 심볼 · 원시값/`null` 의 `for-in` 대 `Object.keys(null)` | node20 1벌 + node18 대조 |
| `js16b-18d-mutate.js` | ★★★ 순회 중 삭제 3행 · 추가 4행 · `Object.keys` 스냅숏 | node20 1벌 + node18 대조 |
| `js16b-18f-refimpl.js` | ★★ **명세 알고리즘을 옮긴 생성기** 대 V8 — 트랩 로그 · 변경 7행(`q` 행만 `DIFFERENT`) | node20 1벌 + node18 대조(같은 출력 — 손 `diff`) |
| `js16b-vdiff.sh` · `js16b-versions.sh` | 두 판 대조 · 판 정보 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · x86-64 Linux)에서만** 그렇다.

- ★★★ **`Proxy` 체인의 트랩 순서**(8줄) — 명세가 묶지 않는다.
- ★★★ **순회 중 윗칸 추가 `q` 미방문** · **재추가 `b` 방문** — 명세 비보장 행.
- ★★ **예외 문구** — `o.hasOwnProperty is not a function` · `Cannot convert undefined or null to object`. 종류(`TypeError`)만 명세다.

**`for-in` 이 열거 가능한 문자열 키를 own 과 체인에서 내놓는 것 · 심볼을 안 내놓는 것 · own 비열거가 부모를 가리는 것 · Proxy 없는 체인의 순서 · 처리 전 삭제 무시 · 자기 자신에 추가한 키 미방문 · `for-in null` 의 0회 · 나머지 여덟 뷰가 own 에서 멈추는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — ★★ **엄격 모드**(탐침이 전부 비엄격) · **브라우저** · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  **TypedArray·모듈 네임스페이스 객체의 `for-in`**(순서 제약 예외 목록에 있다) · 순회 중 **`[[Prototype]]` 교체**와 **`enumerable` 변경** ·
  **16편 클래스 인스턴스에 직접 던진 `for-in`**(9번은 추론이다).
- ★ **못 잰 것** — 없다.
- ★★★ **안 쟀다** — **성능 전부.** 「`for...in` 은 느리다」·「`Object.keys` 가 빠르다」를 한 줄도 쓰지 않았다.
- ★★ **부적용인 창** — ③ 브랜드 태그 · 진단의 `(행,열)`. **잴 것이 없다.**

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **`js16b-18d-mutate.js` 와 `js16b-18f-refimpl.js` 의 비보장 행** — V8 이 바꿔도 명세 위반이 아니므로 **예고 없이 바뀔 수 있다.**
- ★★ **`js16b-18a-grid.js` 의 `[4]` 트랩 로그** — 같은 이유.
- ★ **예외 문구.**
- **격자의 `o`/`.` 와 Proxy 없는 체인의 순서는 다시 돌릴 필요가 없다** — 명세가 묶었다(순서는 ES2020 부터).
