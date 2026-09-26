# js/syntax/23 — `Map`·`Set` 과 약한 컬렉션: 「키는 `-0` 을 `+0` 으로 접은 뒤 같은 값으로 찾고, 약한 쪽은 수명을 들여다볼 창을 아예 안 준다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173**(6번·7번) · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 하나도 없다).
>
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다** — 스택트레이스에는 절대 경로가 박혀 재현이 안 된다.
> ★★★ **이 주제는 두 판이 갈린 블록을 하나 갖고 있다**(`js20b-23d-weak-keys.js`) — 12번 답에 v18 판을 싣는다.
> ★★★ **8번 블록의 `ticks:` 줄은 흔들리는 칸으로 선언돼 있다** — 명세가 시점을 묶지 않는다. 다시 돌려 달라져도 「고칠 것」이 아니다.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다(2번의 소스만 여기 싣는다).
> `js20b-23a-key-equality-grid.js`(1번) · `js20b-23b-stored-key.js`(2번) · `js20b-23c-map-vs-object.js`(3번) · `js20b-23d-weak-keys.js`(4번 · 12번) ·
> `js20b-23e-reclaim-gc.js`(5번) · `js20b-23g-set-methods.web.js`(6번) · `js20b-23h-upsert.web.js`(7번) · `js20b-23f-timing-gc.js`(8번) · `js20b-vdiff.sh`(12번).

## 정답

### 1. 여덟 × 여덟 — **`Map` 키와 한 칸도 안 갈리는 것은 `Set` 과 `includes`, 갈린 칸은 `9 / 56`** ★★★

**출력**

```text
===== node20 js20b-23a-key-equality-grid.js (exit=0) =====
[1] the grid  (y = treated as the same, n = treated as different)
                              Map key    Set        ===        ==         Object.is  object key includes   indexOf
NaN, NaN                      y          y          n          n          y          y          y          n
0, -0                         y          y          y          y          n          y          y          y
'1', 1                        n          n          n          y          n          y          n          n
1, 1.0                        y          y          y          y          y          y          y          y
true, 1                       n          n          n          y          n          n          n          n
null, undefined               n          n          n          y          n          n          n          n
{a:1}, {a:1}  (two objects)   n          n          n          n          n          y          n          n
o, o  (one object)            y          y          y          y          y          y          y          y

[2] per column, cells whose answer differs from the Map-key column:
  Set         0 / 8
  ===         1 / 8
  ==          4 / 8
  Object.is   1 / 8
  object key  2 / 8
  includes    0 / 8
  indexOf     1 / 8
cells whose answer differs from the Map-key column: 9 / 56
```

**왜 그런가**

- ★★★ **`Map` 키 · `Set` · `includes` 가 SameValueZero 한 가족**이다 — 두 열 다 `0 / 8`.
- ★★★ **`NaN, NaN` 행** — `===` · `==` · `indexOf` 만 n. `===` 가족(IsStrictlyEqual)은 `NaN` 을 자기와도 다르다고 본다.
  ★ **`indexOf` 와 `includes` 가 여기서 갈린다** — 같은 「찾기」인데 규칙이 다르다.
- ★★★ **`0, -0` 행** — `Object.is` **하나만** n. SameValue 는 부호를 가르고, SameValueZero 는 이 한 행에서만 SameValue 와 다르다.
- ★★ **`==` 가 `4 / 8` 로 가장 많이 갈린다** — `NaN` 에서는 다르다 하고, `'1', 1` · `true, 1` · `null, undefined` 에서는 **강제 변환으로 같다** 한다.
- ★★ **객체 키가 `2 / 8`** — `'1', 1` 과 **모양이 같은 두 객체**에서 y. 비교가 아니라 **`ToPropertyKey` 로 글자가 된 뒤** 글자가 같아서다(`"1"`, `"[object Object]"`).
  ★ `NaN` 행과 `0, -0` 행에서 객체 키가 y 인 것도 같은 이유다(`"NaN"`, `"0"`) — **답은 `Map` 과 같지만 이유가 다르다.**
- 비교 규칙 자체는 명세 보장이다. 예외도 흔들리는 칸도 없다.

### 2. `-0` 은 **`+0` 으로 접혀 들어간다** — `CanonicalizeKeyedCollectionKey` 뒤에 SameValue ★★★

**소스**

```js
// js20b-23b-stored-key.js
// Map / Set 에 -0 과 여러 NaN 을 넣으면 무엇이 저장되나 -- 저장된 키를 다시 꺼내 본다.
const row = (label, v) => console.log("  " + label.padEnd(52) + v);
console.log("[1] -0 as a key");
const m = new Map([[-0, "minus zero"]]);
const k = [...m.keys()][0];
row("new Map([[-0, ...]]) -> Object.is(key, -0)", Object.is(k, -0));
row("                     -> Object.is(key, +0)", Object.is(k, 0));
row("m.get(0) / m.get(-0)", m.get(0) + " / " + m.get(-0));
row("new Set([-0]) -> Object.is(first, -0)", Object.is([...new Set([-0])][0], -0));
const nans = [NaN, 0 / 0, Number("x"), Math.sqrt(-1)];
console.log("");
console.log("[2] four NaN values made four ways");
row("new Set([NaN, 0/0, Number('x'), sqrt(-1)]).size", new Set(nans).size);
const mn = new Map();
for (const n of nans) mn.set(n, (mn.get(n) ?? 0) + 1);
row("count per key after 4 sets", JSON.stringify([...mn].map(([k2, v]) => [String(k2), v])));
```

**출력**

```text
===== node20 js20b-23b-stored-key.js (exit=0) =====
[1] -0 as a key
  new Map([[-0, ...]]) -> Object.is(key, -0)          false
                       -> Object.is(key, +0)          true
  m.get(0) / m.get(-0)                                minus zero / minus zero
  new Set([-0]) -> Object.is(first, -0)               false

[2] four NaN values made four ways
  new Set([NaN, 0/0, Number('x'), sqrt(-1)]).size     1
  count per key after 4 sets                          [["NaN",4]]
```

**왜 그런가**

- ★★★ **꺼낸 키가 `+0` 이다**(`Object.is(key, -0)` false · `Object.is(key, +0)` true). `Set` 도 같다.
- ★★★ 최신 초안의 `Map.prototype.set` 은 **먼저 `CanonicalizeKeyedCollectionKey`**— 키가 `-0` 이면 `+0` 을 돌려준다 — **로 접고, 그다음 SameValue 로** 칸을 찾는다.
  `get`·`has` 도 먼저 접는다 — 그래서 `m.get(0)` 과 `m.get(-0)` 이 둘 다 찾힌다.
  ★ 관찰되는 **비교 결과**는 SameValueZero 와 같다. 다르게 드러나는 것은 **저장된 키**뿐이다 — 「SameValueZero 로 비교한다」로만 외우면 이 줄을 놓친다.
- ★★ **왜 접나** — 한 칸에 `+0` 과 `-0` 두 표현이 섞여 있으면 **꺼낸 키가 먼저 넣은 쪽에 따라 달라진다.** 입구에서 하나로 정해 두면 그 흔들림이 없다.
- ★ **`NaN` 을 네 가지로 만들어도 한 칸**이다(`size 1`, 한 키에 `4` 가 쌓였다) — SameValue 는 모든 `NaN` 을 같다고 본다.

### 3. `Map` 대 객체 — **객체는 키를 글자로 바꾸고, 물려받은 이름이 있고, `"__proto__"` 대입이 프로토타입을 바꾸고, JSON 에서 `Map` 은 `{}`** ★★★

**출력**

```text
===== node20 js20b-23c-map-vs-object.js (exit=0) =====
[1] two different objects as keys
  object: Object.keys(om)                                   ["[object Object]"]
  object: om[u1]                                            second
  Map:    mm.size / mm.get(u1) / mm.get(u2)                 2 / first / second
  Map:    mm.get({ id: 1 })                                 undefined

[2] the size of each
  object: o3.size                                           undefined
  object: Object.keys(o3).length                            3
  Map:    m3.size                                           3

[3] names that come from Object.prototype
  object: 'toString' in {}  /  typeof {}['toString']        true  /  function
  Map:    new Map().has('toString')                         false
  object: 'constructor' in {}  /  typeof {}['constructor']  true  /  function
  Map:    new Map().has('constructor')                      false
  object: 'hasOwnProperty' in {}  /  typeof {}['hasOwnProperty']true  /  function
  Map:    new Map().has('hasOwnProperty')                   false
  object: tally of a, constructor, a                        {"a":2,"constructor":"function Object() { [native code] }1"}
  Map:    tally of a, constructor, a                        [["a",2],["constructor",1]]

[4] the string key "__proto__"
  object: after po['__proto__'] = 'plain string'            keys []  typeof po.__proto__ object
  object: after po2['__proto__'] = { injected: true }       keys []  po2.injected true
  Map:    after set('__proto__', { injected: true })        size 1  keys ["__proto__"]  pm.injected undefined
  JSON.parse('{"__proto__": ...}')                          keys ["__proto__"]  parsed.injected undefined

[5] JSON
  JSON.stringify(map)                                       {}
  JSON.stringify([...map])                                  [["a",1],["b",2]]
  JSON.stringify(Object.fromEntries(map))                   {"a":1,"b":2}
  new Map(JSON.parse(JSON.stringify([...map]))).get('b')    2
  JSON.stringify(new Set([1, 2]))                           {}
  JSON.stringify({ m: map })                                {"m":{}}

[6] a Set: add again, delete then add
  add('x') again -> order                                   ["x","y","z"]
  delete('x'), add('x') -> order                            ["y","z","x"]
  st.add('w') returns the set itself?                       true
```

**왜 그런가**

- ★★★ **`[1]`** — `u1`·`u2` 가 **둘 다 `"[object Object]"`** 가 되어 한 칸이다. `om[u1]` 이 **`second`**(나중 값). `Map` 은 두 칸이고, 새로 만든 `{ id: 1 }` 로는 **못 찾는다.**
- ★★ **`[2]`** — 객체에는 `size` 가 없다. `Object.keys(o3).length` 는 **배열을 만들어** 센다.
- ★★★ **`[3]`** — `{}` 에도 `toString`·`constructor`·`hasOwnProperty` 가 **체인에서** 보인다([15번](../15-prototype-chain/2-summary.md)).
  `tally[w] || 0` 이 `constructor` 에서 **함수**를 읽고, 거기에 `+ 1` 이 **문자열 이어 붙이기**가 되어 `"function Object() { [native code] }1"` 이 들어간다.
  `Map` 에는 물려받은 키가 없다 — `has` 가 전부 false, 셈이 `1` 이다.
- ★★★ **`[4]`** — `po["__proto__"] = …` 는 **`Object.prototype` 의 `__proto__` 접근자(setter)** 를 부른다.
  문자열은 조용히 무시(자기 키 `[]`, `typeof po.__proto__` 는 여전히 `object`), 객체는 **프로토타입이 된다**(`po2.injected` true — **자기 키는 여전히 `[]`**).
  `Map` 은 그냥 키 한 칸. `JSON.parse` 는 **자기 키**로 만든다 — 리터럴의 다섯 형태는 [13번](../13-object-literals-and-properties/2-summary.md)이 정본이다.
- ★★★ **`[5]`** — `JSON.stringify` 는 **열거 가능한 자기 프로퍼티**를 읽는다. `Map`·`Set` 의 내용은 프로퍼티가 아니라 **내부 슬롯**(`[[MapData]]`)에 있어서 `{}` 다. 에러가 없다.
  `[...map]` 과 `new Map(...)` 으로 왕복하면 값이 산다(`get('b')` 가 `2`).
- ★ **`[6]`** — 다시 `add` 는 자리 그대로, **지웠다 넣으면 맨 뒤.** `add` 는 `Set` 자신을 돌려준다.

### 4. 약한 쪽 — **원시값과 `Symbol.for` 심볼은 `TypeError`, 등록 안 된 심볼은 된다(node 20), `WeakMap` 에는 넷뿐** ★★★

**출력**

```text
===== node20 js20b-23d-weak-keys.js (exit=0) =====
[1] candidate keys for WeakMap.prototype.set
  new WeakMap().set({}, 1)                          ok true
  new WeakMap().set([], 1)                          ok true
  new WeakMap().set(function () {}, 1)              ok true
  new WeakMap().set(1, 1)                           TypeError 「Invalid value used as weak map key」
  new WeakMap().set('str', 1)                       TypeError 「Invalid value used as weak map key」
  new WeakMap().set(null, 1)                        TypeError 「Invalid value used as weak map key」
  new WeakMap().set(undefined, 1)                   TypeError 「Invalid value used as weak map key」
  new WeakMap().set(1n, 1)                          TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol('local'), 1)             ok true
  new WeakMap().set(Symbol.for('registered'), 1)    TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol.iterator, 1)             ok true

[2] the same primitive in the other weak holders
  new WeakSet().add(1)                              TypeError 「Invalid value used in weak set」
  new WeakRef(1)                                    TypeError 「WeakRef: invalid target」
  new WeakRef(Symbol('local')).deref()              ok symbol
  new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: invalid target」
  new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: invalid target」
  registry.register(t, t)  (held value = target)    TypeError 「FinalizationRegistry.prototype.register: target and holdings must not be same」
  new WeakMap([[1, 'x']])                           TypeError 「Invalid value used as weak map key」
  new WeakMap().get(1)                              ok undefined
  new WeakMap().has(1)                              ok false

[3] what each prototype has
  Map.prototype                                     size keys values entries forEach clear get set has delete
  WeakMap.prototype                                 ---- ---- ------ ------- ------- ----- get set has delete
  Symbol.iterator in Map.prototype                  true
  Symbol.iterator in WeakMap.prototype              false
  [...new WeakMap()]                                TypeError 「WeakMap is not a function or its return value is not iterable」
  for (const x of new WeakSet()) {}                 TypeError 「WeakSet is not a function or its return value is not iterable」
  JSON.stringify(new WeakMap([[t, 1]]))             {}
```

**왜 그런가**

- ★★★ **`[1]`** — 네 자리가 같은 검사 **`CanBeHeldWeakly`** 를 쓴다: 객체면 true, **심볼이고 `KeyForSymbol` 이 `undefined`**(등록 안 됨)면 true, 나머지 false.
  그래서 **심볼 셋이 같은 답이 아니다** — `Symbol('local')` · `Symbol.iterator` 는 되고 `Symbol.for('registered')` 는 `TypeError`.
  ★ 등록된 심볼은 **같은 문자열로 언제든 다시 얻을 수 있어서** 수거된다는 말이 성립하지 않는다.
- ★★ **`[2]`** — `get(1)` · `has(1)` 은 **던지지 않는다**(`undefined` · `false`). 넣을 때만 검사한다.
  `WeakRef(Symbol('local'))` 은 **된다**(`symbol`). `register(t, t)` 는 `target and holdings must not be same`.
- ★★★ **`[3]`** — `WeakMap.prototype` 에는 `get set has delete` 넷, 나머지 여섯 자리는 `----`. `Symbol.iterator` 도 없어서 **펴면 `TypeError`**, JSON 은 `{}`.
- ★★★ **이 소스는 node 18 과 node 20 에서 출력이 다르다** — 12번.

### 5. 수명 — **붙잡힌 것은 0/20, 안 붙잡힌 것은 20/20(이 판), 같은 잡 안의 `deref()` 는 전부 20/20** ★★★

**출력**

```text
===== node20 --expose-gc js20b-23e-reclaim-gc.js (exit=0) =====
condition                                     callback  deref() after  deref() in the job
                                              ran       a later gc     right after gc()
dropped (no reference left)                   20/20     object 0/20    object 20/20
kept in a local that stays alive              0/20      object 20/20   object 20/20
key of a Map                                  0/20      object 20/20   object 20/20
key of a WeakMap                              20/20     object 0/20    object 20/20
WeakMap key whose value points back at it     20/20     object 0/20    object 20/20
unregistered before gc                        0/20      object 0/20    object 20/20
```

**왜 그런가**

- ★★★ **「key of a Map」 — 콜백 `0/20`, `deref()` 객체 `20/20`.** `Map` 은 키를 강하게 쥔다. 다른 곳에서 전부 잊혀도 산다.
- ★★★ **「key of a WeakMap」 — `20/20` 수거.** `WeakMap` 은 키를 살리지 않는다.
  ★★★ **값이 키를 되가리켜도 `20/20`** — 값은 키에 **매달려** 있을 뿐 키를 못 살린다(에피머론).
- ★★ **「unregistered before gc」** — 콜백 `0/20` 인데 `deref()` 도 `0/20`. **수거는 됐고 콜백만 취소**됐다. 두 창을 같이 봐야 「안 수거」와 갈린다.
- ★★★ **맨 오른쪽 열 `20/20` × 6** — 같은 동기 실행 안에서는 `WeakRef` 를 만들 때(그리고 `deref()` 할 때) 대상이 **`[[KeptAlive]]`** 에 들어가고,
  `ClearKeptObjects` 는 "when a synchronous sequence of ECMAScript executions completes" 에 돈다. 그래서 탐침은 **`await tick()` 으로 잡을 넘긴 뒤** `gc()` 를 다시 부른다.
- ★★★ **명세가 보장하는 칸** — 「붙잡힌 것은 안 죽는다」(`keep` · `Map` 키 행의 0/20 · 20/20) · 맨 오른쪽 열(KeptAlive).
  **이 판의 관찰인 칸** — `20/20` 으로 **수거된** 행들. 명세 —
  "This specification does not make any guarantees that any object or symbol will be garbage collected."
  이 판의 V8 이 `gc()` 한 번에 거뒀을 뿐이다.

### 6. 집합 연산 — **결과는 새 `Set`, 순서는 this 먼저(또는 작은 쪽), 인자는 set-like, 크기에 따라 `has` 와 `keys` 를 갈아 쓴다** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-23g-set-methods.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] a = {1,2,3,4}, b = {5,3,1} -- results in iteration order
  a.union(b)                                              [1,2,3,4,5]
  b.union(a)                                              [5,3,1,2,4]
  a.intersection(b)                                       [3,1]
  b.intersection(a)                                       [3,1]
  a.difference(b)                                         [2,4]
  a.symmetricDifference(b)                                [2,4,5]
  a.isSubsetOf(b) / isSupersetOf(b) / isDisjointFrom(b)   false / false / false
  new Set([1,3]).isSubsetOf(a)                            true
  a after all of the above                                [1,2,3,4]
  a.union(b) === a                                        false

[2] what can be the argument
  a.union([5, 6])                                         TypeError 「The .size property is NaN」
  a.union(new Map([[9, 'x']]))                            [1,2,3,4,9]
  a.union({ size: 1, has: () => true })                   TypeError 「string "keys" is not a function」
  a.union({ has() {}, keys() {} })  (no size)             TypeError 「The .size property is NaN」
  a.union({ size: -1, has() {}, keys() {} })              RangeError 「'-1' is an invalid size」
  a.union('abc')                                          TypeError 「Set.prototype.union argument must be an object」
  new Set([NaN, 0]).intersection(new Set([NaN, -0]))      [NaN,0]

[3] a set-like argument with logging -- which of size / has / keys each method calls
  {1,2,3}.union(size 2)  -> [1,2,3,9]
      size keys() next next next
  {1,2,3}.union(size 5)  -> [1,2,3,9,8,7,6]
      size keys() next next next next next next
  {1,2,3}.intersection(size 2)  -> [2]
      size keys() next next next
  {1,2,3}.intersection(size 5)  -> [2]
      size has(1) has(2) has(3)
  {1,2,3}.difference(size 2)  -> [1,3]
      size keys() next next next
  {1,2,3}.difference(size 5)  -> [1,3]
      size has(1) has(2) has(3)
  {1,2,3}.symmetricDifference(size 2)  -> [1,3,9]
      size keys() next next next
  {1,2,3}.symmetricDifference(size 5)  -> [1,3,9,8,7,6]
      size keys() next next next next next next
  {1,2,3}.isSubsetOf(size 2)  -> false
      size
  {1,2,3}.isSubsetOf(size 5)  -> false
      size has(1)
  {1,2,3}.isSupersetOf(size 2)  -> false
      size keys() next next
  {1,2,3}.isSupersetOf(size 5)  -> false
      size
  {1,2,3}.isDisjointFrom(size 2)  -> false
      size keys() next
  {1,2,3}.isDisjointFrom(size 5)  -> false
      size has(1) has(2)
```

**왜 그런가**

- ★★★ **`[1]` `a.intersection(b)` 는 `[3,1]` — b 의 순서다.** a(4개)가 b(3개)보다 커서 **b 의 `keys()` 를 돌며 a 에 있나** 물었다. `b.intersection(a)` 는 b 가 작아 b 를 돌았고 역시 `[3,1]`.
  `union` 은 **this 의 순서 뒤에 인자의 새 원소** — `a.union(b)` `[1,2,3,4,5]` 대 `b.union(a)` `[5,3,1,2,4]`.
- ★★★ **`[2]`** — `GetSetRecord` 가 `size`(숫자로 바꿔 `NaN` 이면 `TypeError`, 음수면 `RangeError`) → `has`(함수여야) → `keys`(함수여야) 순으로 검사한다.
  **배열은 `size` 가 없어 `TypeError 「The .size property is NaN」`**, `Map` 은 셋 다 있어 **통과**(키가 원소로 쓰인다), `keys` 없는 객체는 `string "keys" is not a function`, 원시값은 `argument must be an object`.
  ★ `NaN` · `-0` 은 교집합에서도 SameValueZero 대로 — `[NaN,0]`.
- ★★★ **`[3]`** — `intersection`·`difference` 는 **인자가 작으면 `keys()` 를, 크면 `has()` 를** 쓴다. `union`·`symmetricDifference` 는 언제나 `keys()`.
  판정 메서드는 **크기만으로 답이 나오면 `size` 하나만** 읽는다 — `isSubsetOf(size 2)` 는 **`size` 한 낱말**, `isSupersetOf(size 5)` 도 `size` 한 낱말.
- ★ 결과 순서와 로그 순서는 명세 알고리즘이 정한다. 문구만 V8 의 것이다.

### 7. Upsert — **콜백은 키가 없을 때 한 번, 접힌 키로 · 반환값이 이긴다 · 함수 아닌 콜백의 문구는 원인을 안 가리킨다** ★★

**출력**

```text
===== google-chrome --headless --dump-dom 'js20b-page.html?js20b-23h-upsert.web.js' | sed -n '/===OUT===/,/===END===/p' | sed '1d;$d' | sed 's/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&amp;/\&/g' (exit=0) =====
[1] getOrInsert(key, value)
  m.getOrInsert('a', 99)                                    1
  m.getOrInsert('b', 2)                                     2
  m entries                                                 [["a",1],["b",2]]
  argument expression evaluated for an existing key?        times 1

[2] getOrInsertComputed(key, callback) with a logging callback
  c.getOrInsertComputed('a', cb)                            old   log []
  c.getOrInsertComputed('b', cb)                            made-b   log ["callback(b)"]
  c.getOrInsertComputed('b', cb)  (again)                   made-b   log []
  c.getOrInsertComputed(-0, cb) -> key passed to cb         zero   log ["+0"]
  c entries                                                 [["a","old"],["b","made-b"],["0","zero"]]

[3] the callback writes the same key before returning
  return value                                              returned
  w.get('k') afterwards                                     returned
  w.size                                                    1

[4] the callback throws
  t.getOrInsertComputed('k', () => { throw ... })           Error 「from callback」
  t.has('k') afterwards                                     false
  t.getOrInsertComputed('k', 'not a function')              TypeError 「Map.prototype.getOrInsertComputed is not a function」
  new Map([['k', 1]]).getOrInsertComputed('k', 42)          TypeError 「Map.prototype.getOrInsertComputed is not a function」

[5] the WeakMap versions
  wm.getOrInsert(key, 1) then (key, 2)                      1 then 1
  wm.getOrInsert(1, 'x')                                    TypeError 「Invalid value used as weak map key」
  wm.getOrInsertComputed(1, cb)  -> cb log                  TypeError 「Invalid value used as weak map key」
    cb log after that attempt                               []
  typeof Set.prototype.getOrInsert                          undefined

[6] the older idiom next to it -- a Map subclass that logs its own has / get / set
  if (!has) set; get(...).push  -> calls                    ["has","set","get"]
  getOrInsert(...).push          -> calls                   []
```

**왜 그런가**

- ★★★ **`[2]`** — 로그가 `[]` → `["callback(b)"]` → `[]`. **없을 때만, 한 번.** `-0` 으로 부르면 콜백이 `+0` 을 받는다 — 명세가 **콜백을 부르기 전에** 키를 접는다.
- ★★ **`[1]` `times 1`** — `getOrInsert("a", mk())` 의 `mk()` 는 **메서드가 불리기 전에** 인자로 평가된다. 키가 있어도 한 번 돈다. 비싸면 `getOrInsertComputed`.
- ★★ **`[3]`** — 콜백이 `set("k", "set inside")` 를 해도 **콜백 반환값 `returned` 가 남는다**(`size 1`). 명세가 콜백 뒤 **다시 찾아 그 칸을 덮는다** — "The Map may have been modified during execution of callback."
- ★★★ **`[4]`** — 콜백이 던지면 **아무것도 안 들어간다**. 그리고 함수 아닌 콜백에는 **`TypeError 「Map.prototype.getOrInsertComputed is not a function」`** —
  ★★★ **메서드는 있다.** 함수가 아닌 것은 **콜백**이다. V8 의 문구가 **원인을 가리키지 않는다**(규칙 27). 키가 **있어도** 던지는 것은 명세 순서(콜백 검사가 첫 단계)다.
- ★ **`[5]`** — `WeakMap` 판은 원시값 키에 **콜백을 부르기 전에** 던진다(`cb log []`). `Set` 에는 없다.
- ★★ **`[6]`** — 옛 관용구는 `has` · `set` · `get` 세 번, `getOrInsert` 는 서브클래스가 덮은 메서드를 **하나도 안 부른다**. 빠르다는 뜻이 아니다 — **안 쟀다.**

### 8. 두 블록으로 가른 이유 — **「불렸나」는 판마다 세어 대조하고, 「언제」는 명세가 묶지 않아 흔들리는 칸으로 둔다** ★★★

**출력**

```text
===== node20 --expose-gc js20b-23f-timing-gc.js (exit=0) =====
[1] gc() called -- macrotask index at which the callback ran, per round (-1 = not within 20)
  ticks: 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  rounds where it had run before gc() returned: 0/20
[2] gc() not called -- the same, per round
  ticks: -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1 -1
```

**왜 그런가**

- ★★★ **명세의 목표 절 첫 문장** — "This specification does not make any guarantees that any object or symbol will be garbage collected. Objects or symbols which are not live may be released after long periods of time, or never at all."
  정리 잡도 호스트가 "at some future time, if possible" 에 돌린다.
- ★★ **`ticks:` 줄 셋이 흔들리는 칸**이다. 이 판에서는 `[1]` 이 전부 `0`(첫 매크로태스크), `gc()` 가 **돌아오기 전에는 0/20** 이었다 — 콜백은 동기로 안 돈다.
  ★ 5번 블록에 이 시점을 섞으면 **한 줄만 흔들려도 블록 전체가 「불일치」** 가 된다. 갈라 두면 재대조가 파일 단위로 판정된다(규칙 11).
- ★★★ **`[2]` 가 전부 `-1` 이어도 「안 불린다」가 아니다** — **「20틱 안에는 안 왔다」** 다. 이 판이 그 짧은 시간에 GC 를 안 했을 뿐이다. 명세는 "or never at all" 까지 허용한다.

### 9. 파이썬과 JS — **파이썬은 「값이 같으면 타입을 넘어 한 칸」, JS `Map` 은 「타입이 다르면 다른 칸, `NaN` 은 일부러 한 칸」** ★★★

파이썬 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md))의 **12번** 출력을 인용한다(이 배치에서 다시 돌리지 않았다).

| 짝 | 파이썬 `dict` | JS `Map` |
|---|---|---|
| `1` · `1.0` · `True` | **한 칸**(`{1: '불리언'}`) | `1`·`1.0` 한 칸, **`true` 는 다른 칸**(1번의 `true, 1` 행 n) |
| `nan` 둘 | **두 칸**(같은 객체일 때만 찾힌다) | **한 칸**(2번 — `NaN` 네 개가 `size 1`) |
| `0.0` · `-0.0` | 한 칸 | 한 칸, 저장된 키는 `+0` |

- ★★★ 파이썬은 `hash` + `==` 가 **타입을 가로질러** 같게 만들고, `nan` 은 `==` 가 거짓이라 **정체로만** 찾힌다.
  JS `Map` 은 **강제 변환을 안 하고**, SameValue 가 `NaN` 을 **같다고 정의**한다. 방향이 반대다.
- ★ `set` 원소도 두 언어에서 각자 `dict` 키·`Map` 키와 같은 규칙이다 — 파이썬은 같은 목록 **13번**, JS 는 1번의 `Set` 열(`0 / 8`).

### 10. `WeakMap` 에 창이 없는 이유 — **키를 쥔 사람만 물을 수 있어야 「언제 비워졌나」가 안 샌다** ★★★

- ★★★ 명세 — "an ECMAScript implementation must not provide any means to observe a key of a WeakMap that does not require the observer to present the observed key."
- ★★ 그 앞 문장이 이유다 — 구현은 키가 쓸모없어진 때와 항목이 치워지는 때 사이에 **임의의 지연**을 둘 수 있고, "If this latency was observable to ECMAScript program, it would be a source of indeterminacy that could impact program execution."
  `size` 하나만 있어도 **GC 시점이 값으로 새어 나온다.**
- ★ 그래서 이 문서는 **`FinalizationRegistry` 콜백과 `WeakRef.deref()`** 로 바꿔 물었다(5번 — 제5의 상태). ★ **바꾼 창이 못 보는 것** — `WeakMap` **안의 항목 자체**. 대상이 수거됐다는 것까지만 보인다.

### 11. 고르는 기준 — **레코드는 객체, 키가 데이터인 사전은 `Map`. 해시의 원리는 `05-hashmap` 이 정본** ★★

- ★★ 여섯 기준(3번의 출력) — 키 타입(객체는 글자로 바꾼다) · 순서(객체는 정수 키가 앞 — [13번](../13-object-literals-and-properties/2-summary.md)) · 크기(`size` 없음) ·
  물려받은 이름(`constructor` 가 이미 있다) · `"__proto__"`(대입이 프로토타입을 바꾼다) · JSON(`Map` 은 `{}`).
- ★★ 「`Map` 이 더 빠르다」는 **「안 쟀다」** 칸이다. 이 문서에 속도 주장이 한 줄도 없다.
- ★ [`cs/data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/2-summary.md) 은 **버킷·충돌·재해싱·`LinkedHashMap` 이 삽입 순서를 기억하는 구현**까지.
  이 주제는 **JS 명세가 약속한 관찰 가능한 의미**(무엇이 같은 키인가 · 어떤 순서로 나오나 · 무엇을 약하게 쥐나)부터다.
  명세도 자료구조는 묻지 않고 "on average, provide access times that are sublinear" 만 요구한다.

### 12. 두 판이 갈린 블록 — **`js20b-23d-weak-keys.js` 하나. 심볼 키(ES2023 판 경계)와 `WeakRef` 문구** ★★

**출력** — 같은 소스의 node 18 판.

```text
===== node18 js20b-23d-weak-keys.js (exit=0) =====
[1] candidate keys for WeakMap.prototype.set
  new WeakMap().set({}, 1)                          ok true
  new WeakMap().set([], 1)                          ok true
  new WeakMap().set(function () {}, 1)              ok true
  new WeakMap().set(1, 1)                           TypeError 「Invalid value used as weak map key」
  new WeakMap().set('str', 1)                       TypeError 「Invalid value used as weak map key」
  new WeakMap().set(null, 1)                        TypeError 「Invalid value used as weak map key」
  new WeakMap().set(undefined, 1)                   TypeError 「Invalid value used as weak map key」
  new WeakMap().set(1n, 1)                          TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol('local'), 1)             TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol.for('registered'), 1)    TypeError 「Invalid value used as weak map key」
  new WeakMap().set(Symbol.iterator, 1)             TypeError 「Invalid value used as weak map key」

[2] the same primitive in the other weak holders
  new WeakSet().add(1)                              TypeError 「Invalid value used in weak set」
  new WeakRef(1)                                    TypeError 「WeakRef: target must be an object」
  new WeakRef(Symbol('local')).deref()              TypeError 「WeakRef: target must be an object」
  new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: target must be an object」
  new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: target must be an object」
  registry.register(t, t)  (held value = target)    TypeError 「FinalizationRegistry.prototype.register: target and holdings must not be same」
  new WeakMap([[1, 'x']])                           TypeError 「Invalid value used as weak map key」
  new WeakMap().get(1)                              ok undefined
  new WeakMap().has(1)                              ok false

[3] what each prototype has
  Map.prototype                                     size keys values entries forEach clear get set has delete
  WeakMap.prototype                                 ---- ---- ------ ------- ------- ----- get set has delete
  Symbol.iterator in Map.prototype                  true
  Symbol.iterator in WeakMap.prototype              false
  [...new WeakMap()]                                TypeError 「WeakMap is not a function or its return value is not iterable」
  for (const x of new WeakSet()) {}                 TypeError 「WeakSet is not a function or its return value is not iterable」
  JSON.stringify(new WeakMap([[t, 1]]))             {}
```

**두 판 대조기**

```sh
# js20b-vdiff.sh
#!/usr/bin/env bash
# 두 node 판이 갈린 탐침이 몇 개인가 -- 스크립트가 직접 센다(브라우저 탐침 *.web.js 는 대상이 아니다).
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
same=0; diffn=0
for f in js20b-2[0-3]?-*.js; do
  case $f in *.web.js) continue ;; esac
  flags=""; case $f in *-gc.js) flags="--expose-gc" ;; esac
  a="$("$N18" $flags "$f" 2>&1)"
  b="$("$N20" $flags "$f" 2>&1)"
  if [ "$a" = "$b" ]; then
    printf '%-36s identical\n' "$f"; same=$((same + 1))
  else
    printf '%-36s DIFFERS\n' "$f"; diffn=$((diffn + 1))
    diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | sed 's/^/    /'
  fi
done
echo ""
echo "identical $same  ·  differs $diffn  ·  total $((same + diffn))"
```
```text
===== ./js20b-vdiff.sh (exit=0) =====
js20b-20a-start-and-end.js           identical
js20b-20b-two-way.js                 identical
js20b-20c-return-finally.js          identical
js20b-20d-throw.js                   identical
js20b-20e-delegate.js                identical
js20b-20f-errors.js                  DIFFERS
    9c9
    <   function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier」
    ---
    >   function* g() { [1].forEach(x => { yield x; }); }   SyntaxError 「Unexpected identifier 'x'」
js20b-20g-grid.js                    identical
js20b-20h-lazy-seq.js                identical
js20b-21x-node-absent.js             identical
js20b-22a-basics.js                  identical
js20b-22b-key-grid.js                identical
js20b-22c-toprimitive-hints.js       identical
js20b-22d-hasinstance.js             identical
js20b-22e-tostringtag.js             identical
js20b-22f-species.js                 DIFFERS
    9,12c9,12
    <   toSorted          -               TypeError 「a.toSorted is not a function」
    <   toReversed        -               TypeError 「a.toReversed is not a function」
    <   with              -               TypeError 「a.with is not a function」
    <   toSpliced         -               TypeError 「a.toSpliced is not a function」
    ---
    >   toSorted          -               Array
    >   toReversed        -               Array
    >   with              -               Array
    >   toSpliced         -               Array
js20b-22g-other-hooks.js             DIFFERS
    29c29
    <   keys                                              ["copyWithin","entries","fill","find","findIndex","flat","flatMap","includes","keys","values","at","findLast","findLastIndex"]
    ---
    >   keys                                              ["at","copyWithin","entries","fill","find","findIndex","findLast","findLastIndex","flat","flatMap","includes","keys","values","toReversed","toSorted","toSpliced"]
js20b-22h-registry.js                DIFFERS
    20,21c20,21
    <   new WeakMap().set(Symbol('k'), 1)                   TypeError 「Invalid value used as weak map key」
    <   new WeakRef(Symbol('k'))                            TypeError 「WeakRef: target must be an object」
    ---
    >   new WeakMap().set(Symbol('k'), 1)                   ok
    >   new WeakRef(Symbol('k'))                            ok
    23,25c23,25
    <   new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: target must be an object」
    <   new WeakMap().set(Symbol.iterator, 1)               TypeError 「Invalid value used as weak map key」
    <   new WeakRef(Symbol.iterator)                        TypeError 「WeakRef: target must be an object」
    ---
    >   new WeakRef(Symbol.for('k'))                        TypeError 「WeakRef: invalid target」
    >   new WeakMap().set(Symbol.iterator, 1)               ok
    >   new WeakRef(Symbol.iterator)                        ok
    27c27
    < symbol kinds accepted as a WeakMap key 0 / 3
    ---
    > symbol kinds accepted as a WeakMap key 2 / 3
js20b-22i-wellknown.js               DIFFERS
    3c3
    < a `using` declaration: SyntaxError 「Unexpected identifier」
    ---
    > a `using` declaration: SyntaxError 「Unexpected identifier 'r'」
js20b-23a-key-equality-grid.js       identical
js20b-23b-stored-key.js              identical
js20b-23c-map-vs-object.js           identical
js20b-23d-weak-keys.js               DIFFERS
    10c10
    <   new WeakMap().set(Symbol('local'), 1)             TypeError 「Invalid value used as weak map key」
    ---
    >   new WeakMap().set(Symbol('local'), 1)             ok true
    12c12
    <   new WeakMap().set(Symbol.iterator, 1)             TypeError 「Invalid value used as weak map key」
    ---
    >   new WeakMap().set(Symbol.iterator, 1)             ok true
    16,19c16,19
    <   new WeakRef(1)                                    TypeError 「WeakRef: target must be an object」
    <   new WeakRef(Symbol('local')).deref()              TypeError 「WeakRef: target must be an object」
    <   new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: target must be an object」
    <   new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: target must be an object」
    ---
    >   new WeakRef(1)                                    TypeError 「WeakRef: invalid target」
    >   new WeakRef(Symbol('local')).deref()              ok symbol
    >   new WeakRef(Symbol.for('registered'))             TypeError 「WeakRef: invalid target」
    >   new FinalizationRegistry(f).register(1, 'h')      TypeError 「FinalizationRegistry.prototype.register: invalid target」
js20b-23e-reclaim-gc.js              identical
js20b-23f-timing-gc.js               identical

identical 18  ·  differs 6  ·  total 24
```

집계 줄 —

`identical 18  ·  differs 6  ·  total 24`

**왜 그런가**

- ★★★ **판 경계** — `Symbol('local')` · `Symbol.iterator` 를 `WeakMap` 키로, `Symbol('local')` 을 `WeakRef` 대상으로 쓰는 줄. v18 은 `TypeError`, v20 은 된다. **Symbols as WeakMap keys(ES2023)** 가 들어오기 전과 후다.
- ★★ **문구** — `new WeakRef(1)` · `register(1, 'h')` 의 문구가 `target must be an object`(v18) 대 `invalid target`(v20). 종류는 둘 다 `TypeError` 다.
- ★ 근거로 쓰는 것 — **되나/안 되나(판 경계)와 예외 종류.** 근거로 안 쓰는 것 — 문구.
- ★ 대조기의 다른 `DIFFERS` 줄은 **다른 주제의 탐침**이다(같은 배치가 한 대조기를 공유한다).

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js20b-23a-key-equality-grid.js` | ★★★ 값의 짝 8 × 비교 자리 8 격자 · 「갈린 칸 9 / 56」 | node20 1벌 + node18 대조 1벌 |
| `js20b-23b-stored-key.js` | ★★★ `-0` 이 `+0` 으로 저장되는 것 · `NaN` 네 가지가 한 칸 | node20 1벌 + node18 대조 1벌 |
| `js20b-23c-map-vs-object.js` | ★★★ 객체 키 뭉개짐 · 크기 · 물려받은 이름 · `"__proto__"` · JSON · `Set` 재삽입 | node20 1벌 + node18 대조 1벌 |
| `js20b-23d-weak-keys.js` | ★★★ 약한 키 후보 11개 · 약한 자리 넷 · `WeakMap` 에 없는 것 | node20 1벌 + **node18 판도 싣는다**(갈린 블록) |
| `js20b-23e-reclaim-gc.js` | ★★★ 수명 조건 6 × 20판 — 콜백 · `deref()` · KeptAlive | node20 `--expose-gc` 1벌(판 안에서 20판) + node18 대조 1벌 |
| `js20b-23f-timing-gc.js` | ★★ 콜백 시점 — **흔들리는 칸** | node20 `--expose-gc` 1벌 + node18 대조 1벌 |
| `js20b-23g-set-methods.web.js` | ★★ 집합 연산 결과 순서 · 인자 검사 · 인자 로그 | **Chrome 151 만** |
| `js20b-23h-upsert.web.js` | ★★ Upsert 콜백 시점 · 덮어쓰기 · 문구 | **Chrome 151 만** |
| `js20b-vdiff.sh` · `js20b-versions.sh` | 두 판이 갈린 탐침 수 · 이 문서의 출력이 **어느 판에서 나왔나** + 판별 기능 표 | 1벌씩 |

브라우저 탐침(6번·7번)을 돌린 페이지 — 탐침 파일 이름을 주소의 `?` 뒤에 붙여 연다. `console.log` 를 가로채 줄을 모은 뒤 `<pre>` 에 쓰고, `--dump-dom` 이 그것을 내보낸다.

```html
<!-- js20b-page.html -->
<!doctype html>
<meta charset="utf-8">
<title>js20b</title>
<pre id="o"></pre>
<script>
// 탐침 스크립트 하나를 이 페이지에서 돌린다 -- 파일 이름은 주소의 ? 뒤에 온다.
// console.log 를 가로채 줄을 모으고, 마지막 스크립트가 그 줄을 <pre> 에 쓴다(--dump-dom 이 그것을 내보낸다).
const __lines = [];
console.log = (...a) => { __lines.push(a.join(" ")); };
window.addEventListener("error", (e) => { __lines.push("uncaught " + e.message); });
document.write('<script src="' + location.search.slice(1) + '"><\/script>');
</script>
<script>
document.getElementById("o").textContent = "==" + "=OUT===\n" + __lines.join("\n") + "\n===END" + "===";
</script>
```

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **`gc()` 한 번에 안 붙잡힌 대상이 수거된 것(20/20)** · 콜백이 첫 매크로태스크에 돈 것 · `gc()` 없이 20틱 안에 안 돈 것 — 명세는 "may" 뿐이다. `gc()` 자체가 V8 플래그다.
- ★★ **예외 문구 전부** — `Invalid value used as weak map key` · `Invalid value used in weak set` · `WeakRef: invalid target`(v20) / `WeakRef: target must be an object`(v18) ·
  `FinalizationRegistry.prototype.register: invalid target` · `target and holdings must not be same` · `WeakMap is not a function or its return value is not iterable` ·
  `The .size property is NaN` · `'-1' is an invalid size` · `string "keys" is not a function` · `Set.prototype.union argument must be an object` ·
  ★ `Map.prototype.getOrInsertComputed is not a function`(**원인과 다른 문구**). **종류만 명세가 정한다.**

**격자의 비교 규칙 · `-0` 접기 · 삽입 순서 · `CanBeHeldWeakly` · `WeakMap` 에 창이 없는 것 · 강하게 붙잡힌 것이 안 죽는 것 · KeptAlive · `GetSetRecord` 검사 순서 · `intersection` 의 크기 가지 · Upsert 의 콜백 시점과 덮어쓰기는 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것 / 부적용인 창**

- **안 돌려 본 것** — **브라우저의 GC**(`FinalizationRegistry` 는 node 에서만) · **파이썬 쪽 재실행**(12번 문서 인용) · 다른 엔진(SpiderMonkey·JavaScriptCore)의 문구.
- ★ **못 잰 것** — **집합 연산·Upsert 의 node 판 동작.** 두 node 판에 메서드가 없다(판별 블록) — Chrome 151 로 창을 바꿨다.
- ★★★ **안 쟀다** — **성능 전부.** 「`Map` 이 객체보다 빠르다」·「`WeakMap` 이 메모리를 아낀다」를 **한 줄도 쓰지 않았다.**
- ★★ **부적용인 창** — **③ 브랜드 태그**(집합 연산 인자조차 프로퍼티 셋으로 판정된다) · **진단의 `(행,열)`**(`SyntaxError` 가 없다). **「잴 것이 없다」는 뜻**이다.
- ★★★ **창을 바꿔 물은 자리** — `WeakMap` 안의 수명. 들여다볼 창이 없어 **`FinalizationRegistry` 와 `WeakRef`** 로 물었다(5번 · 10번).

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **node 22 이후의 판** — 집합 연산(ES2025)·Upsert(ES2026)가 들어온 판에서는 **6번·7번을 node 로도** 돌린다. 판별 블록의 `no` 가 `yes` 로 바뀌는지 먼저 본다.
- ★★ **`gc()` 관찰 전부**(5번·8번) — GC 전략이 바뀌면 `20/20` 이 움직일 수 있다. 움직여도 명세 위반이 아니다.
- ★★ **예외 문구 전부** — 이 주제 안에서 이미 바뀌었다(12번).
