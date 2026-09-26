# js/syntax/45 — `Proxy`: 「거짓말하는 트랩은 `12 / 24` 에서 던지고 · `Reflect` 로 넘기면 맨 대상과 `0 / 24` 다르고 · 내부 슬롯은 못 빌린다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **node 18.19.1 · Chrome 151 도 네 탐침 전부 한 글자도 같았다**(아래 「실행 검증」의 세 판 대조기) — 예외 문구까지.
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js44b-45a-invariant-grid.js`(1번 · 5번 · 6번 · 7번) · `js44b-45c-falsish.js`(2번 · 6번 · 9번) · `js44b-45d-internal-slots.js`(3번 · 7번) · `js44b-45e-what-a-proxy-looks-like.js`(4번 · 7번 · 8번).

## 정답

### 1. 표 `[1]` — 보통 열 **전부 통과**, 설정 불가+쓰기 불가 열 **`getPrototypeOf` 만 통과**, `preventExtensions` 열은 **`get`·`set`·`defineProperty` 만 통과** — **`12 / 24`** · 표 `[2]` — 던진 칸 **1**(`defineProperty` / 설정 불가) · 맨 대상과 다른 칸 **`0 / 24`** ★★★

**출력**

```text
===== node20 js44b-45a-invariant-grid.js (exit=0) =====
[1] the trap returns what is in the second column
  trap                     what the trap returns             ordinary                         x non-writable+non-configurable  preventExtensions
  get                      'lie'                             ok "lie"                         TypeError                        ok "lie"
  set                      true (writes nothing)             ok "real"                        TypeError                        ok "real"
  has                      false                             ok false                         TypeError                        TypeError
  deleteProperty           true (deletes nothing)            ok true                          TypeError                        TypeError
  defineProperty           true (defines nothing)            ok "real"                        TypeError                        ok "real"
  getOwnPropertyDescriptor undefined                         ok undefined                     TypeError                        TypeError
  ownKeys                  []                                ok []                            TypeError                        TypeError
  getPrototypeOf           a new {}                          ok false                         ok false                         TypeError
  cells that threw: 12 / 24

[2] the trap forwards with Reflect
  trap                     what the trap returns             ordinary                         x non-writable+non-configurable  preventExtensions
  get                      Reflect.get                       ok "real"                        ok "real"                        ok "real"
  set                      Reflect.set                       ok "new"                         ok "real"                        ok "new"
  has                      Reflect.has                       ok true                          ok true                          ok true
  deleteProperty           Reflect.deleteProperty            ok true                          ok false                         ok true
  defineProperty           Reflect.defineProperty            ok "new"                         TypeError                        ok "new"
  getOwnPropertyDescriptor Reflect.getOwnPropertyDescriptor  ok "real w:true c:true"          ok "real w:false c:false"        ok "real w:true c:true"
  ownKeys                  Reflect.ownKeys                   ok ["x"]                         ok ["x"]                         ok ["x"]
  getPrototypeOf           Reflect.getPrototypeOf            ok true                          ok true                          ok true
  cells that threw: 1 / 24
  cells where the bare target gave a different answer: 0 / 24

[3] messages of the exceptions in [1]
  get / x non-writable+non-configurable: 'get' on proxy: property 'x' is a read-only and non-configurable data property on the proxy target but the proxy did not return its actual value (expected 'real' but got 'lie')
  set / x non-writable+non-configurable: 'set' on proxy: trap returned truish for property 'x' which exists in the proxy target as a non-configurable and non-writable data property with a different value
  has / x non-writable+non-configurable: 'has' on proxy: trap returned falsish for property 'x' which exists in the proxy target as non-configurable
  has / preventExtensions: 'has' on proxy: trap returned falsish for property 'x' but the proxy target is not extensible
  deleteProperty / x non-writable+non-configurable: 'deleteProperty' on proxy: trap returned truish for property 'x' which is non-configurable in the proxy target
  deleteProperty / preventExtensions: 'deleteProperty' on proxy: trap returned truish for property 'x' but the proxy target is non-extensible
  defineProperty / x non-writable+non-configurable: 'defineProperty' on proxy: trap returned truish for adding property 'x'  that is incompatible with the existing property in the proxy target
  getOwnPropertyDescriptor / x non-writable+non-configurable: 'getOwnPropertyDescriptor' on proxy: trap returned undefined for property 'x' which is non-configurable in the proxy target
  getOwnPropertyDescriptor / preventExtensions: 'getOwnPropertyDescriptor' on proxy: trap returned undefined for property 'x' which exists in the non-extensible proxy target
  ownKeys / x non-writable+non-configurable: 'ownKeys' on proxy: trap result did not include 'x'
  ownKeys / preventExtensions: 'ownKeys' on proxy: trap result did not include 'x'
  getPrototypeOf / preventExtensions: 'getPrototypeOf' on proxy: proxy target is non-extensible but the trap did not return its actual prototype
```

**왜 그런가**

- ★★★ 내부 메서드는 트랩 결과를 받은 뒤 **대상의 현재 상태와 대조**한다 — 설정 불가 프로퍼티는 값·존재가, 확장 불가 대상은 **키 목록과 프로토타입**이 굳어 있다(5번).
- ★★ 표 `[2]` 의 한 칸은 **맨 대상도 같은 `TypeError`** 다 — `Object.defineProperty` 가 `[[DefineOwnProperty]]` 의 `false` 를 예외로 바꾼다(46번). 비엄격 파일이라 대입·삭제의 `false` 는 조용히 지나갔다.

### 2. `[1]` **`TypeError 「'set' on proxy: trap returned falsish for property 'x'」`** · `[2]` **`no exception · p.x = undefined`** · `[3]` `TypeError …'deleteProperty'…` · `[4]` `no exception · delete gave false` · `[5]` **`false · false`** ★★

**출력**

```text
===== node20 js44b-45c-falsish.js (exit=0) =====
[1] strict  p.x = 1     -> TypeError 「'set' on proxy: trap returned falsish for property 'x'」
[2] sloppy  p.x = 1     -> no exception · p.x = undefined
[3] strict  delete p.x  -> TypeError 「'deleteProperty' on proxy: trap returned falsish for property 'x'」
[4] sloppy  delete p.x  -> no exception · delete gave false
[5] Reflect.set(p, 'x', 1) -> false · Reflect.deleteProperty(p, 'x') -> false
```

**왜 그런가**

- ★★ 트랩의 `false` 는 「안 했다」는 **보고**다. 엄격 모드의 대입·`delete` 가 그 보고를 `TypeError` 로 바꾸고, 비엄격은 버린다(14번과 같은 규칙). `Reflect` 는 그 보고를 **값으로** 돌려준다.

### 3. `Map.get` · `Map.size` · `Set.has` · `Date.getTime` · `#x` — **`TypeError`** · 배열 `push` **`ok 3`** · `this.n` 메서드 **`ok 2`** · `[2]` bind 하면 **`ok "a"` · `ok 1` · `ok 1`** ★★

**출력**

```text
===== node20 js44b-45d-internal-slots.js (exit=0) =====
[1] empty handler
  new Proxy(new Map([[1, 'a']]), {}).get(1)                       TypeError 「Method Map.prototype.get called on incompatible receiver #<Map>」
  new Proxy(new Map([[1, 'a']]), {}).size                         TypeError 「Method get Map.prototype.size called on incompatible receiver #<Map>」
  new Proxy(new Set([1]), {}).has(1)                              TypeError 「Method Set.prototype.has called on incompatible receiver #<Set>」
  new Proxy(new Date(0), {}).getTime()                            TypeError 「this is not a Date object.」
  new Proxy([1, 2], {}).push(3)                                   ok 3
  new Proxy({ n: 1, twice() { return this.n * 2; } }, {}).twice() ok 2
  new Proxy(new C(), {}).getX()   (C has a private #x)            TypeError 「Cannot read private member #x from an object whose class did not declare it」
[2] a get trap that binds functions to the target
  new Proxy(new Map([[1, 'a']]), bound).get(1)                    ok "a"
  new Proxy(new Map([[1, 'a']]), bound).size                      ok 1
  new Proxy(new C(), bound).getX()                                ok 1
```

**왜 그런가**

- ★★ `Map.prototype.get` 은 `this` 에 **`[[MapData]]` 내부 슬롯**이 있는지부터 본다. Proxy 는 그 슬롯이 없는 **다른 객체**다 — 트랩이 가로챌 **프로퍼티 접근**이 아니라서 대상으로 넘어가지 않는다. 프라이빗 `#x` 도 **그 객체 자신**에 붙는 이름이다.
- ★ 배열 `push` 는 `this.length`·인덱스를 **프로퍼티로** 읽고 쓰니 트랩을 거쳐 대상에 닿는다.

### 4. **`=== t` 는 `false`** · `object` · `function` · `function` · **`true`** · `[object Array]` · `[object Map]` · `[1,2]` · **`instanceof` `TypeError`** · `new` 없이 `TypeError` · 취소 전 `1` · 취소 뒤 `get`/`has` **`TypeError`** · **`typeof` `object`/`function`** · **`Array.isArray` `TypeError`** · `revoke()` 두 번째 **`undefined`** ★★

**출력**

```text
===== node20 js44b-45e-what-a-proxy-looks-like.js (exit=0) =====
[1] a live proxy
  new Proxy(t, {}) === t                              ok false
  typeof new Proxy({}, {})                            ok object
  typeof new Proxy(function () {}, {})                ok function
  typeof new Proxy(class {}, {})                      ok function
  Array.isArray(new Proxy([], {}))                    ok true
  toString tag of new Proxy([], {})                   ok [object Array]
  toString tag of new Proxy(new Map(), {})            ok [object Map]
  JSON.stringify(new Proxy([1, 2], {}))               ok [1,2]
  new Proxy({}, {}) instanceof Proxy                  TypeError 「Function has non-object prototype 'undefined' in instanceof check」
  Proxy({}, {})   (without new)                       TypeError 「Constructor Proxy requires 'new'」
[2] Proxy.revocable, then revoke()
  proxy.a before revoke()                             ok 1
  proxy.a                                             TypeError 「Cannot perform 'get' on a proxy that has been revoked」
  'a' in proxy                                        TypeError 「Cannot perform 'has' on a proxy that has been revoked」
  typeof proxy                                        ok object
  typeof (a revoked proxy of a function)              ok function
  Array.isArray(a revoked proxy of [])                TypeError 「Cannot perform 'IsArray' on a proxy that has been revoked」
  revoke() a second time                              ok undefined
```

**왜 그런가**

- ★★ `typeof` 는 `[[Call]]` 이 있나로 가르고, `ProxyCreate` 는 **대상이 호출 가능할 때만** `[[Call]]` 을 단다 — 취소해도 떼지 않는다. `Array.isArray` 는 Proxy 면 **대상을 따라가** 묻는데, 취소 뒤에는 대상이 없어 던진다(문구의 `'IsArray'`).

### 5. **트랩 결과 대 대상의 현재 상태**(`[[GetOwnProperty]]` · `[[IsExtensible]]` · `[[GetPrototypeOf]]`) — 보통 대상은 굳힌 것이 없어 대조할 사실이 없다 · 프로토타입을 굳히는 것은 **확장 불가**이지 프로퍼티 플래그가 아니다 ★★★

- ★★★ 명세 `[[Get]]` 은 「대상 프로퍼티가 **설정 불가 + 쓰기 불가 데이터**면 `SameValue` 가 거짓일 때 `TypeError`」만 검사한다 — 쓰기 가능하거나 설정 가능하면 **검사할 것이 없다.**
- ★★ `[[GetPrototypeOf]]` 의 불변식은 「대상이 **확장 불가**면 대상의 프로토타입과 같아야 한다」 하나다 — 그래서 `x` 의 플래그와 무관하다.

### 6. 1번 `[3]` 의 `trap returned truish …` · `… did not return its actual value` — **Proxy 의 불변식 검사** · 2번 `[1]` 의 `trap returned falsish …` — **엄격 모드의 대입**이 `false` 를 바꾼 것 ★★

- ★★ 앞쪽은 **모드와 무관하게** 던진다(비엄격 파일에서 던졌다). 뒤쪽은 **엄격에서만** 던진다(2번 `[2]`). 문구의 `truish`/`falsish` 가 두 자리를 가른다.

### 7. 구분되는 자리 — **내부 슬롯**(`Map`·`Set`·`Date`) · **프라이빗 이름** · **`=== target` 이 거짓**(별도 객체) · 구분 안 되는 자리 — 프로퍼티 읽기·쓰기·열거 · **`typeof`** · **`Array.isArray`** · `Object.prototype.toString` 의 태그 · `Reflect` 로 넘긴 24칸 ★★

- ★ `=== target` 이 거짓인 것은 4번 첫 줄(`new Proxy(t, {}) === t` → `false`) — `ProxyCreate` 가 `MakeBasicObject` 로 **새 객체**를 만든다.

### 8. 취소는 `[[ProxyTarget]]`·`[[ProxyHandler]]` 를 비울 뿐 **`[[Call]]` 을 떼지 않는다**(그래서 `typeof`) · `Array.isArray` 는 **대상을 찾아가다** 막힌다 · 두 번째 `revoke()` 는 **`undefined`**(이미 비었으면 그냥 돌아간다) ★

### 9. 2번의 **비엄격 `p.x = 1` · `delete p.x`**(트랩의 `false` 가 조용히 버려진다) 와 1번 표 `[2]` 의 **`set`·`deleteProperty` / 설정 불가 칸**(`Reflect` 가 돌려준 `false` 가 비엄격 파일이라 `ok "real"` · `ok false` 로 지나갔다) ★★

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js44b-45a-invariant-grid.js` | ★★★ 24칸 × 2 · 「`12 / 24`」 · 「`0 / 24`」 · 문구 12개 | node20 1벌 · node18 · Chrome 151 대조(같음) |
| `js44b-45c-falsish.js` | ★★ 엄격 / 비엄격 · `Reflect` 의 `false` | 〃 |
| `js44b-45d-internal-slots.js` | ★★ 내부 슬롯 · 프라이빗 이름 · bind 고침 | 〃 |
| `js44b-45e-what-a-proxy-looks-like.js` | ★★ `typeof` · 배열 판별 · 취소 | 〃 |

세 판 대조기(이 묶음의 plain 탐침). 이 주제의 줄 넷(`45a`·`45c`·`45d`·`45e`)은 **전부 `identical · identical`** 이다.

```sh
# js44b-vdiff.sh
#!/usr/bin/env bash
# Every plain probe of 44-46 and js44b-47d (js44b-4NX-*.js, not *.web.js), run on node18, node20 and Chrome 151.
# The other 47 probes need a gc() flag or print counts that move between runs -- js44b-47a-observe.sh compares those.
# A probe that uses a node-only API (process.* or require) is compared between the two node versions only.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
cd "$(dirname "$0")"
s18=0; d18=0; sw=0; dw=0; skip=0
for f in js44b-4[456]?-*.js js44b-47d-*.js; do
  [ -e "$f" ] || continue
  case $f in *.web.js) continue ;; esac
  a="$("$N18" "$f" 2>&1)"; b="$("$N20" "$f" 2>&1)"
  if [ "$a" = "$b" ]; then r18=identical; s18=$((s18 + 1)); else r18=DIFFERS; d18=$((d18 + 1)); fi
  if grep -q 'process\.\|require(' "$f"; then rw="(node only)"; skip=$((skip + 1))
  else
    w="$(./js44b-browser.sh "$f")"
    if [ "$w" = "$b" ]; then rw=identical; sw=$((sw + 1)); else rw=DIFFERS; dw=$((dw + 1)); fi
  fi
  printf '%-40s node18/node20 %-10s node20/Chrome %s\n' "$f" "$r18" "$rw"
done
echo ""
echo "node18 vs node20: identical $s18 · differs $d18   ·   node20 vs Chrome 151: identical $sw · differs $dw · node only $skip"
```

```text
===== ./js44b-vdiff.sh (exit=0) =====
js44b-44d-attributes-grid.js             node18/node20 DIFFERS    node20/Chrome (node only)
js44b-45a-invariant-grid.js              node18/node20 identical  node20/Chrome identical
js44b-45c-falsish.js                     node18/node20 identical  node20/Chrome identical
js44b-45d-internal-slots.js              node18/node20 identical  node20/Chrome identical
js44b-45e-what-a-proxy-looks-like.js     node18/node20 identical  node20/Chrome identical
js44b-46a-reflect-and-traps.js           node18/node20 identical  node20/Chrome identical
js44b-46b-object-vs-reflect.js           node18/node20 identical  node20/Chrome identical
js44b-46c-receiver.js                    node18/node20 identical  node20/Chrome identical
js44b-47d-registry-api.js                node18/node20 DIFFERS    node20/Chrome identical

node18 vs node20: identical 7 · differs 2   ·   node20 vs Chrome 151: identical 8 · differs 0 · node only 1
```

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — 격자의 칸은 **명세**가 정하므로 판이 올라도 같아야 한다. 다시 볼 것은 **문구**다(1번 `[3]`의 12줄 · 3번 · 4번의 `Cannot perform …`).
