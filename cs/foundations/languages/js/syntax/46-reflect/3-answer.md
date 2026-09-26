# js/syntax/46 — `Reflect`: 「함수 13개가 트랩 13개와 `13 / 13` 짝이 맞고 · 옛 창구와 `14 / 19` 행에서 갈리며 · `receiver` 를 버리면 상속한 쪽의 `this` 가 사라진다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 출력은 **node v20.19.6** · x86-64 Linux 에서 실제로 돌려 얻은 것이고, 블록은 **전부 캡처 파일에서 조립**했다.
> ★★★ **node 18.19.1 · Chrome 151 도 세 탐침 전부 한 글자도 같았다**(아래 「실행 검증」의 세 판 대조기).
>
> **이 파일이 인용하는 출력을 낸 소스** — 전문은 [1-question.md](1-question.md) 의 같은 번호 문항에 있다.
> `js44b-46a-reflect-and-traps.js`(1번 · 6번 · 8번) · `js44b-46b-object-vs-reflect.js`(2번 · 4번 · 7번 · 9번) · `js44b-46c-receiver.js`(3번 · 5번 · 6번).

## 정답

### 1. **이름 13 · 함수 13 · `typeof` `object`** · 13개 전부 **같은 이름의 트랩 하나** — `13 / 13` · 짝 없는 트랩 **`none`** · `Object` 에도 있는 것 **6개**, `Reflect` 에만 **7개** ★★★

**출력**

```text
===== node20 js44b-46a-reflect-and-traps.js (exit=0) =====
[1] Object.getOwnPropertyNames(Reflect): 13 names · functions: 13
  defineProperty deleteProperty apply construct get getOwnPropertyDescriptor getPrototypeOf has isExtensible ownKeys preventExtensions set setPrototypeOf
  Reflect[Symbol.toStringTag] = Reflect · typeof Reflect = object

[2] Reflect.<name>(proxy, ...) -- the traps that fired
  Reflect.defineProperty            defineProperty
  Reflect.deleteProperty            deleteProperty
  Reflect.apply                     apply
  Reflect.construct                 construct
  Reflect.get                       get
  Reflect.getOwnPropertyDescriptor  getOwnPropertyDescriptor
  Reflect.getPrototypeOf            getPrototypeOf
  Reflect.has                       has
  Reflect.isExtensible              isExtensible
  Reflect.ownKeys                   ownKeys
  Reflect.preventExtensions         preventExtensions
  Reflect.set                       set
  Reflect.setPrototypeOf            setPrototypeOf
  Reflect functions that fired exactly one trap, of the same name: 13 / 13
  trap names without a Reflect function of that name: none

[3] the same name as an own property of Object?
  on Object too:  defineProperty getOwnPropertyDescriptor getPrototypeOf isExtensible preventExtensions setPrototypeOf
  Reflect only:   deleteProperty apply construct get has ownKeys set
```

**왜 그런가**

- ★★★ `Reflect.<이름>` 은 대상의 **같은 이름의 내부 메서드**를 그대로 부르고, Proxy 의 그 내부 메서드는 **같은 이름의 트랩**을 찾는다 — 두 목록이 한 명세 표에서 나온다.
- ★★ `Reflect` 에만 있는 7개는 원래 **연산자**가 하던 일(`.`·`=`·`in`·`delete`·`()`·`new`)과 `Object.keys` 가 못 하던 일(`ownKeys`)이다.

### 2. 한쪽만 던진 행 **`11 / 19`** · 둘 다 돌려줬는데 값이 다른 행 **`3 / 19`** · 합 **`14 / 19`** ★★★

**출력**

```text
===== node20 js44b-46b-object-vs-reflect.js (exit=0) =====
  request                                           Object / operator                         Reflect
* defineProperty -- change x's value (x fixed)      throws TypeError                          false
* defineProperty -- add y (not extensible)          throws TypeError                          false
* getOwnPropertyDescriptor('str', 'length')         descriptor { value: 3, writable: false }  throws TypeError
* getPrototypeOf(1)                                 Number.prototype                          throws TypeError
* setPrototypeOf -- not extensible, to {}           throws TypeError                          false
~ setPrototypeOf -- not extensible, to the same     "the object"                              true
* preventExtensions(1)                              1                                         throws TypeError
* isExtensible(1)                                   false                                     throws TypeError
~ keys vs ownKeys -- symbol and non-enumerable key  [a]                                       [a, hidden, Symbol(s)]
* keys vs ownKeys -- on 1                           []                                        throws TypeError
* delete o.x vs deleteProperty (x fixed)            throws TypeError                          false
* o.x = 2 vs set (x fixed)                          throws TypeError                          false
  o.x vs get                                        1                                         1
  'x' in o vs has                                   true                                      true
  'x' in 1 vs has(1, 'x')                           throws TypeError                          throws TypeError
  f.apply(null, [1, 2]) vs apply                    3                                         3
~ g.apply(...) -- g has its own apply property      "own apply property"                      3
* f.apply(null) vs apply(f, null) -- no list        NaN                                       throws TypeError
  new C(1) vs construct(C, [1])                     C { v: 1 }                                C { v: 1 }

rows where only one side threw (*): 11 / 19
rows where both returned, different values (~): 3 / 19
rows that differ: 14 / 19
```

**왜 그런가**

- ★★★ 4번의 두 규칙(실패를 `false` 로 · 원시값을 안 감싼다)이 11행을, 반환 모양·조회 범위·조회 경로가 나머지 3행을 가른다.

### 3. `base` · `base` · **`other`** · `true · other.written 1 · base.written undefined` · `true · plain.x 1 · into.x 2 · own x in into true` · `[6]` **`target` 과 `child`** · `[7]` **`set -> getOwnPropertyDescriptor -> defineProperty`** 와 **`set`** ★★

**출력**

```text
===== node20 js44b-46c-receiver.js (exit=0) =====
[1] base.who                              base
[2] Reflect.get(base, 'who')              base
[3] Reflect.get(base, 'who', other)       other
[4] Reflect.set(base, 'who', 1, other)    true · other.written 1 · base.written undefined
[5] Reflect.set(plain, 'x', 2, into)      true · plain.x 1 · into.x 2 · own x in into true
[6] child.who through get(t, k) { return t[k] }                     target
    child.who through get(t, k, r) { return Reflect.get(t, k, r) }  child
[7] p.x = 1 fired: set -> getOwnPropertyDescriptor -> defineProperty
    Reflect.set(p, 'y', 1, {}) fired: set
```

**왜 그런가**

- ★★★ `[[Get]]`/`[[Set]]` 은 `receiver` 를 **getter·setter 의 `this`** 로 넘기고, 데이터 쓰기는 **`receiver` 에** 정의한다(`OrdinarySet`). `t[k]` 로 넘기면 `receiver` 가 **`t` 로 바뀐다.**
- ★★ `[7]` — `receiver` 가 Proxy 자신이면, 대상의 `OrdinarySet` 이 **그 Proxy 의** `[[GetOwnProperty]]`·`[[DefineOwnProperty]]` 를 불러 트랩 둘이 더 불린다. `receiver` 가 `{}` 면 쓰기가 `{}` 에 떨어져 트랩은 `set` 하나다.

### 4. ① **실패를 값으로** — 내부 메서드가 `false` 를 돌려주면 `Reflect` 는 **그대로**, `Object.*`·엄격 연산은 **`TypeError` 로 바꾼다** · ② **원시값** — `Reflect` 는 **대상이 객체가 아니면 첫 줄에서 `TypeError`**, `Object.*` 의 일부는 **`ToObject` 로 감싼다** ★★★

- ★★★ ①은 **호출한 쪽**의 단계(45번의 `falsish` 와 같은 자리), ②는 **인자 검사** 단계다. 11행 = ① 5행 + ② 5행 + `apply` 의 목록 검사 1행.

### 5. 45번 — `Reflect` 로 넘긴 트랩 24칸이 **맨 대상과 `0 / 24`** 달랐다(대조에 걸릴 거짓이 없다) · 3번 `[6]` — **`receiver` 까지 넘겨야** 상속한 쪽의 getter 가 `child` 를 본다 ★★★

- ★★ 이름이 1:1 이고(1번) 인자 순서도 같으니 `(...args) => Reflect[name](...args)` 한 줄이 **13개 트랩 전부**에 맞는다.

### 6. 넘기면 **다른 트랩이 덩달아 불려** 「같은 이름 하나만」을 셀 수 없다 — 3번 `[7]` 에서 `set` 을 넘기자 **`getOwnPropertyDescriptor`·`defineProperty`** 가 더 불렸다 ★★

- ★ 고정 답은 **보통 확장 가능한 대상**의 불변식을 지키게 골랐다(`preventExtensions` 는 `false`, `ownKeys` 는 설정 불가 키 `prototype` 을 포함) — 안 그러면 45번의 `TypeError` 가 대응 표를 가린다.

### 7. `f.apply(null, [1, 2])` 대 `Reflect.apply` — **같다**(`3`) · 자기 `apply` 가 있는 함수 — `g.apply` 는 **그 프로퍼티를 조회**해 `"own apply property"`, `Reflect.apply` 는 조회하지 않아 `3` · 목록 없음 — `f.apply(null)` 은 **인자 0개**(09번의 `apply(t, null)` 과 같은 규칙)로 `NaN`, `Reflect.apply(f, null)` 은 **`TypeError`** ★★

### 8. **없다** — 19행 전부 명세가 정하는 칸이고 세 판이 같았다 · `getOwnPropertyNames(Reflect)` 의 **순서**는 명세가 정하지 않는다(V8 의 정의 순서로 보인다 — 근거로는 개수 13 만 쓴다) ★

### 9. 14번 — **비엄격에서는 실패한 대입·`delete` 가 조용히 버려진다** — 비엄격이면 그 두 행이 「`false` 대 조용함」이 되어 「던지나」를 못 가른다 · 22번 — **`Reflect.ownKeys` 는 심볼 키를 본다**(`Object.keys` 는 안 본다) ★★

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js44b-46a-reflect-and-traps.js` | ★★★ 13개 · 「`13 / 13`」 · `Object` 와 겹치는 6개 | node20 1벌 · node18 · Chrome 151 대조(같음) |
| `js44b-46b-object-vs-reflect.js` | ★★★ 19행 · 「`11 / 19`」 · 「`3 / 19`」 | 〃 |
| `js44b-46c-receiver.js` | ★★ `receiver` 의 `this` · 쓰기 · 트랩에서 넘길 때 | 〃 |

세 판 대조기(이 묶음의 plain 탐침). 이 주제의 줄 셋(`46a`·`46b`·`46c`)은 **전부 `identical · identical`** 이다.

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

**구현 의존 항목 — 판이 오르면 다시 돌릴 것** — 격자 칸은 **명세**가 정한다. 다시 볼 것은 `getOwnPropertyNames(Reflect)` 의 **순서** 정도다.
