# ts/syntax/32 — 클래스의 타입 측면 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Classes](https://www.typescriptlang.org/docs/handbook/2/classes.html)(`private` 의 「soft private」·괄호 접근 · `implements` 는 검사일 뿐 · 매개변수 프로퍼티 · `abstract`) ·
> [TSConfig — `useDefineForClassFields`](https://www.typescriptlang.org/tsconfig/useDefineForClassFields.html) ·
> [TypeScript 3.7 릴리스 노트 — `useDefineForClassFields` 와 `declare` 프로퍼티](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html) ·
> [TypeScript 5.8 릴리스 노트 — `--erasableSyntaxOnly`](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html).
> 위는 **규칙 확인용 링크**이고(열어서 문장을 확인했다), 본문의 진단·방출물·출력은 **전부 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> ★ TSConfig 페이지 본문에는 **기본값 문장이 없었다** — 기본값은 5절에서 **던져서** 얻었다.
> **실행 검증** — 본판은 아래다. ★ 5절의 판 비교에는 이 머신의 **다른 프로젝트에 깔린 `tsc` 4.9.5** 를 **읽기만** 해서 썼다(환경변수 **`TSC_49`**).

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 3창(방출된 `.js` + `node`)이다.**
> 클래스의 TS 수식어(`private`·`protected`·`readonly`·`implements`·`abstract`·매개변수 프로퍼티)가 **방출물에서 무엇이 되나**를 격자와 방출물로 보인다(1·2절).
> ★★★ **직접 선행은 JS 갈래 [`../../../js/syntax/16-class-syntax/`](../../../js/syntax/16-class-syntax/)다** — `#private` 가 **리플렉션·브랜드 태그·`Proxy` 트랩 어디에도 안 보이고**, `#x in obj` 로 브랜드를 묻고,
> `Proxy` 로 감싸면 `#x` 읽기가 `TypeError` 라는 것은 **그쪽 1절 `[3]`(바깥 창 일곱 가지)과 5절이 정본**이다. 「**필드 = 정의, 생성자 대입 = 대입**」도 그쪽 4절이다. **다시 재지 않고 인용한다.**
> 여기서 새로 재는 것은 **TS 수식어 쪽**이다 — 그리고 두 방출물을 **나란히** 놓는다.
> ★ 클래스가 **값이자 타입**이라는 것(`typeof Class` 는 생성자)은 [**23번 주제**](../23-typeof-type-operator/) 3절이 정본이다.
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> **버전** — `#private` 는 **ES2022**(JS 쪽), `useDefineForClassFields` 는 **TS 3.7**(릴리스 노트), `--erasableSyntaxOnly` 는 **5.8**. ★ **7.0.2 에서 도는지는 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | ★★★ 1절 서른여섯 칸 · 5절 스물다섯 칸과 마지막 줄의 **수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 방출된 `.js` 와 `node` 출력 | 방출기의 고정 형식 · 예외는 **이름(과 메시지)만** 찍었다 |
| **★ 판에 매인다** | 5절 마지막 행 — 4.9.5 는 `TS2729` 를 **안 낸다** | 판 격자 자체가 결론이다 |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 — 이 주제의 질문은 **`.js` 에 무엇이 남나**다 | — |
| **흔들린다** | 절대 경로 | 격자는 작업 디렉토리 아래 임시 폴더에서 돌렸고, 파싱 단계 `SyntaxError` 는 **이름만** 뽑아 경로를 안 실었다 |
| **안 잰 것** | `#private` 의 속도 · 메모리 · WeakMap 하향 방출의 비용 | **재지 않았다** |

## 한눈에 — 쉽게 말하면

**TS `private` 는 「관계자 외 출입금지」 팻말이고, JS `#` 는 잠긴 금고다. 팻말은 컴파일러라는 경비원이 있을 때만 통하고, 방출물에는 팻말 자체가 없다.**

| 비유 | 실체 |
|---|---|
| **팻말** — 경비원이 있을 때만 막는다 | `private x` — 컴파일러가 `TS2341` 로 막는다 · 방출물에서 **평범한 필드** |
| 팻말 옆 **개구멍** — 경비원도 눈감아 준다 | `o["x"]` — `private` 인데 **컴파일도 통과**한다(핸드북의 「soft private」) |
| ★★★ **금고** — 경비원이 없어도 잠겨 있다 | `#x` — 방출물에 **`#x` 가 남고** `Object.keys`·`JSON.stringify` 에 **안 보인다** |
| **「수정 금지」 스티커** | `readonly x` — 컴파일러만 `TS2540` · 방출물에서 평범한 필드 |
| **자격증 검사** — 검사관만 보고 떠난다 | `implements Shape` — 검사만 하고 **방출물에 흔적이 없다** · 타입도 안 준다 |
| **「견본 — 판매 금지」 도장** | `abstract` — `new` 를 컴파일러만 막는다 · 방출물은 **평범한 클래스** |

- ★★★ 한 줄로 — 「**TS 의 클래스 수식어는 전부 방출물에서 사라진다. 런타임에 남는 비밀은 JS 의 `#` 하나다.**」

```text
  같은 클래스, 두 세계

  컴파일 세계(ex.32a.ts)            실행 세계(방출된 .js, -t es2022)
  class Account {                   class Account {
      private owner = "kim";  ──>       owner = "kim";          ← private 가 사라졌다
      #balance = 100;         ──>       #balance = 100;         ← # 는 JS 문법이라 남는다
  }                                 }
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **★★★ TS `private` 와 JS `#` 는 런타임에 무엇이 다른가** — 필드 여섯 가지 × 바깥에서 여섯 가지를 **격자로** 센다(1절). 두 방출물을 나란히(2절).
2. **`implements`·매개변수 프로퍼티·`abstract` 는 방출물에서 무엇이 되나** — 사라지는 것과 **대입문이 되는 것**(3·4절).
3. **필드 선언은 설정에 따라 무엇이 되나** — `useDefineForClassFields` 판 격자(5절).

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **3창 — 방출된 `.js` + `node`** | 수식어가 **런타임에 남긴 것** | 실행 결과 | **본체**(1\~5절) |
| ★★★ **`private` 대 `#` 격자** | 필드 여섯 × (방출 · 실행 다섯) | 칸마다 파일 하나 | 1절 |
| ★★★ **판 격자** | `ex.32d.ts` × 설정 다섯 | 판마다 방출 + `node` | 5절 |
| ★ **설정 대조** | `--strict` 를 끄면 | 글자 단위 대조 | 6절 |
| ★ **제5의 상태 — 창을 바꿔 물었다** | `#x` 의 **런타임 브랜드 검사**(`Proxy` · 칸 없는 객체) | JS 16편의 실측 | 1절 — `#x` 바깥 접근은 여기서 **파싱 단계**에 막혀 그 창까지 못 간다 |
| ★ **부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — | — |

비용 — 격자 서른여섯 칸(방출 서른여섯 번 · 검사 서른 번 · `node` 서른 번) + 파일 넷의 컴파일·방출·실행 + 판 격자 다섯 판.

```text
  이 주제의 축 — 「누가 막나」 × 「방출물에 남나」

                         컴파일러가 막나      방출물               런타임이 막나
  private x              TS2341 (점 접근만)   x = 1;               아니다
  protected x            TS2445 (점 접근만)   x = 1;               아니다
  readonly x             TS2540 (쓰기)        x = 1;               아니다
  #x                     TS18013              #x = 1;              ★ 그렇다
  implements I           (몸통 대조)          사라짐               —
  abstract class / m()   TS2511 (new)         평범한 class         아니다
  constructor(public x)  —                    x; + this.x = x;     —  ← 대입문이 생긴다
```

### (1) ★★★ `private` 대 `#` 격자 — 필드 여섯 가지 × 바깥에서 여섯 가지

**언제 쓰나** — 「`private` 로 충분한가, `#` 가 필요한가」를 고를 때. 이 주제의 결론이 이 격자에 있다.

```bash
# ts30b-privgrid.sh
#!/usr/bin/env bash
# 필드 하나(값 1)를 여섯 가지로 선언하고, 클래스 바깥에서 여섯 가지를 묻는다 -- 칸마다 파일 하나씩
# 컴파일 칸은 진단 코드 · 실행 칸은 node 출력(앞에 진단 코드) · 실행 칸이 막혔는지를 센다
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'   # 구분자는 탭(규칙 32)
kinds=(
  "public${T}x = 1;${T}x${T}-t es2022"
  "private${T}private x = 1;${T}x${T}-t es2022"
  "protected${T}protected x = 1;${T}x${T}-t es2022"
  "readonly${T}readonly x = 1;${T}x${T}-t es2022"
  "#x${T}#x = 1;${T}#x${T}-t es2022"
  "#x@es2021${T}#x = 1;${T}#x${T}-t es2021"
)
codes() { tsc --pretty false --noEmit --strict $2 "$1" 2>&1 | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
cell() { # cell <열> <필드선언> <이름> <타깃> -> 칸 하나
  local col=$1 field=$2 key=$3 tgt=$4 f="$D/c.ts" probe c out
  case $col in
    emit)
      { echo "class Box {"; echo "    $field"; echo "}"; } > "$f"
      rm -rf "$D/o"; tsc --pretty false --strict $tgt --outDir "$D/o" "$f" > /dev/null 2>&1
      sed -n '/^class Box/,/^}/p' "$D/o/c.js" | sed '1d;$d' | sed 's/^ *//' | tr '\n' ' ' | sed 's/ $//'
      return ;;
    keys)  probe='JSON.stringify(Object.keys(o))' ;;
    json)  probe='JSON.stringify(o)' ;;
    dot)   probe="o.$key" ;;
    brack) probe="o[\"$key\"]" ;;
    write) probe="(o.$key = 9, JSON.stringify(Object.entries(o)))" ;;
  esac
  { echo "class Box {"; echo "    $field"; echo "}"; echo "const o = new Box();"
    echo "try {"; echo "    console.log($probe);"; echo "} catch (e) {"
    echo "    console.log((e as Error).constructor.name);"; echo "}"; } > "$f"
  c=$(codes "$f" "$tgt")
  rm -rf "$D/o"; tsc --pretty false --strict $tgt --outDir "$D/o" "$f" > /dev/null 2>&1
  node "$D/o/c.js" > "$D/run.txt" 2>&1
  out=$(grep -m1 -o '^[A-Z][A-Za-z]*Error' "$D/run.txt" || head -1 "$D/run.txt")   # 파싱 단계 에러는 try 로 못 잡는다 -- 이름만 뽑는다
  if [ -n "$c" ]; then echo "($c) $out"; else echo "$out"; fi
}
cols=(emit keys json dot brack write)
blocked=0; total=0
for k in "${kinds[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$k")
  if [ "$n" -ne 4 ]; then echo "칸 수 $n ≠ 4: $k"; exit 3; fi
  IFS="$T" read -r name field key tgt <<< "$k"
  echo "[$name] $field  ($tgt)"
  for col in "${cols[@]}"; do
    v=$(cell "$col" "$field" "$key" "$tgt")
    printf '    %-5s %s\n' "$col" "$v"
    if [ "$col" != emit ]; then
      total=$((total+1))
      case $col in
        keys|json) case $v in *'"x"'*|*'"#x"'*) ;; *) blocked=$((blocked+1)) ;; esac ;;
        dot|brack|write) case $v in *Error*|*undefined*) blocked=$((blocked+1)) ;; esac ;;
      esac
    fi
  done
done
echo
echo "런타임에 값이 안 보이거나 막힌 칸 $blocked / $total"
```

```text
===== bash ts30b-privgrid.sh (sh exit=0) =====
[public] x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   1
    brack 1
    write [["x",9]]
[private] private x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   (TS2341) 1
    brack 1
    write (TS2341) [["x",9]]
[protected] protected x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   (TS2445) 1
    brack 1
    write (TS2445) [["x",9]]
[readonly] readonly x = 1;  (-t es2022)
    emit  x = 1;
    keys  ["x"]
    json  {"x":1}
    dot   1
    brack 1
    write (TS2540) [["x",9]]
[#x] #x = 1;  (-t es2022)
    emit  #x = 1;
    keys  []
    json  {}
    dot   (TS18013) SyntaxError
    brack (TS7053) undefined
    write (TS18013) SyntaxError
[#x@es2021] #x = 1;  (-t es2021)
    emit  constructor() { _Box_x.set(this, 1); }
    keys  []
    json  {}
    dot   (TS18013) SyntaxError
    brack (TS7053) undefined
    write (TS18013) SyntaxError

런타임에 값이 안 보이거나 막힌 칸 10 / 30
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`emit` 열** — `public`·`private`·`protected`·`readonly` 넷이 전부 **`x = 1;`** 이다. **수식어가 한 글자도 안 남았다.**
  `#x` 는 **`#x = 1;`** 으로 남고, `-t es2021` 이면 **`constructor() { _Box_x.set(this, 1); }`** — **WeakMap 에 담는 코드**로 바뀐다.
- ★★★ **`keys`·`json` 열** — TS 수식어 네 행은 **`["x"]`·`{"x":1}`**. `#x` 두 행만 **`[]`·`{}`**.
- ★★ **`dot` 열** — `private` 는 **`(TS2341) 1`**, `protected` 는 **`(TS2445) 1`**. **진단은 났는데 방출물은 `1` 을 읽었다.**
  `#x` 는 **`(TS18013) SyntaxError`** — 방출물이 **파싱조차 안 된다.**
- ★★★ **`brack` 열** — **`[private]` 가 `1`, 진단 없음.** `o["x"]` 는 `private` 인데 **컴파일러도 통과시킨다.** `protected` 도 같다.
  `#x` 는 `o["#x"]` 가 **다른 문자열 키**라 `(TS7053) undefined`.
- ★★ **`write` 열** — `readonly` 는 **`(TS2540) [["x",9]]`** — 컴파일러는 막았지만 방출물은 **9 를 썼다.**
- ★★★ 마지막 줄 **런타임에 값이 안 보이거나 막힌 칸 10 / 30** — 열 칸 **전부가 `#x` 두 행**이다. **TS 수식어 네 행은 0 / 20.**

```text
  여섯 × 다섯(실행 칸) — 런타임이 막은 칸만 ★

              keys     json      dot                 brack             write
  public      ["x"]    {"x":1}   1                   1                 [["x",9]]
  private     ["x"]    {"x":1}   (TS2341) 1          1   ← 진단도 없다  (TS2341) [["x",9]]
  protected   ["x"]    {"x":1}   (TS2445) 1          1                 (TS2445) [["x",9]]
  readonly    ["x"]    {"x":1}   1                   1                 (TS2540) [["x",9]]
  #x          ★[]      ★{}       ★(TS18013) SyntaxError  ★(TS7053) undefined  ★(TS18013) SyntaxError
  #x@es2021   ★[]      ★{}       ★(TS18013) SyntaxError  ★(TS7053) undefined  ★(TS18013) SyntaxError
```

- ★★★ **`#x` 의 `SyntaxError` 는 「런타임 강제」가 아니라 「문법 강제」다.** 클래스 **바깥에서 `o.#x` 라고 쓰는 것 자체**가 JS 에서 파싱 에러다 — 파일 전체가 안 돈다.
  **런타임 강제**(칸 없는 객체·`Proxy` 에서 `#x` 를 읽으면 `TypeError`)는 **클래스 안의 코드**가 남의 객체를 읽을 때 나온다 — **JS 16편 5절이 정본**이다(창을 바꿔 물었다).
- ★★ `-t es2021` 로 내려도 `#x` 는 **비밀을 지킨다**(`[]`·`{}`). 문법 대신 **WeakMap** 이 금고 노릇을 한다(2절).

비용 — `#x` 는 **같은 클래스 안에서만** 보인다. 테스트·직렬화·디버깅에서 `private` 처럼 **옆문으로 읽을 방법이 없다.**

### (2) ★★★ 두 방출물 나란히 — `private` 는 사라지고 `#` 는 남는다

**언제 쓰나** — 「이 객체를 `JSON.stringify` 하면 비밀이 새나」를 판단할 때.

```ts
// ex.32a.ts
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    private owner = "kim";
    #balance = 100;
    peek(): number {
        return this.#balance;
    }
}
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32a.ts (tsc exit=0) =====
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32a ex.32a.ts (tsc exit=0) =====
===== 방출된 e32a/ex.32a.js =====
"use strict";
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    owner = "kim";
    #balance = 100;
    peek() {
        return this.#balance;
    }
}
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== node e32a/ex.32a.js (node exit=0) =====
[1] keys  [ 'owner' ]
[2] json  {"owner":"kim"}
[3] owner kim
[4] peek  100
[5] spread { owner: 'kim' }
```

```text
===== tsc --pretty false -t es2021 --strict --outDir e32a21 ex.32a.ts (tsc exit=0) =====
===== 방출된 e32a21/ex.32a.js =====
"use strict";
var __classPrivateFieldGet = (this && this.__classPrivateFieldGet) || function (receiver, state, kind, f) {
    if (kind === "a" && !f) throw new TypeError("Private accessor was defined without a getter");
    if (typeof state === "function" ? receiver !== state || !f : !state.has(receiver)) throw new TypeError("Cannot read private member from an object whose class did not declare it");
    return kind === "m" ? f : kind === "a" ? f.call(receiver) : f ? f.value : state.get(receiver);
};
var _Account_balance;
// TS private 와 JS # 을 한 클래스에 -- 방출물과 바깥에서 본 모습
class Account {
    constructor() {
        this.owner = "kim";
        _Account_balance.set(this, 100);
    }
    peek() {
        return __classPrivateFieldGet(this, _Account_balance, "f");
    }
}
_Account_balance = new WeakMap();
const acc = new Account();
console.log("[1] keys ", Object.keys(acc));
console.log("[2] json ", JSON.stringify(acc));
console.log("[3] owner", acc["owner"]);
console.log("[4] peek ", acc.peek());
console.log("[5] spread", { ...acc });
```

```text
===== node e32a21/ex.32a.js (node exit=0) =====
[1] keys  [ 'owner' ]
[2] json  {"owner":"kim"}
[3] owner kim
[4] peek  100
[5] spread { owner: 'kim' }
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단 **0줄** — 13행 `acc["owner"]` 가 **`private` 인데 통과**했다(1절 `brack` 열과 같은 답).
- ★★★ **`-t es2022` 방출물** — `private owner = "kim";` 이 **`owner = "kim";`**, `#balance = 100;` 은 **그대로**. `peek()` 안의 `this.#balance` 도 그대로.
- ★★★ **`-t es2021` 방출물** — `#balance` 가 **`_Account_balance = new WeakMap()`** 과 **`__classPrivateFieldGet`** 도우미로 바뀌었다.
  도우미가 `!state.has(receiver)` 면 **`TypeError("Cannot read private member from an object whose class did not declare it")`** 를 던진다 — **JS 16편에서 본 그 문구를 흉내 낸다.**
  `owner` 는 **생성자 안 `this.owner = "kim";`** 으로 바뀌었다 — 5절의 `useDefineForClassFields` 기본값이 `es2021` 에서 꺼진 것이다.
- ★★★ **`node` 다섯 줄이 두 판에서 한 글자도 같다** — `[1] keys [ 'owner' ]` · `[2] json {"owner":"kim"}` · `[3] owner kim` · `[4] peek 100` · `[5] spread { owner: 'kim' }`.
  **`owner` 는 어디에나 새고, `balance` 는 어디에도 안 샌다.**

```text
  같은 두 필드, 세 방출물

                   ex.32a.ts          -t es2022            -t es2021
  private owner    private owner="kim" owner = "kim";       this.owner = "kim";          ← 평범한 프로퍼티
  #balance         #balance = 100      #balance = 100;      _Account_balance.set(this, 100)   ← WeakMap
  바깥에서 보이나                       owner 만             owner 만
```

비용 — `private` 로 표시한 필드도 **로그·직렬화·스프레드에 그대로 나간다**(`[2]`·`[5]`). 비밀번호·토큰을 `private` 로 「숨겼다」고 믿으면 안 된다.

### (3) ★★ 매개변수 프로퍼티와 `implements` — 대입문이 생기고, 검사는 사라진다

**언제 쓰나** — 생성자 인자를 필드로 바로 받을 때, 인터페이스를 「구현한다」고 적을 때.

```ts
// ex.32b.ts
// 매개변수 프로퍼티와 implements -- 방출물에 무엇이 남나
interface Shape {
    area(): number;
    scale(factor: number): void;
}
class Rect implements Shape {
    constructor(public w: number, private h: number, readonly tag = "rect") {}
    area(): number {
        return this.w * this.h;
    }
    scale(factor) {
        this.w *= factor;
    }
}
const r = new Rect(2, 3);
r.scale(2);
console.log(r.area(), Object.keys(r), r instanceof Rect);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32b.ts (tsc exit=1) =====
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32b ex.32b.ts (tsc exit=2) =====
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
===== 방출된 e32b/ex.32b.js =====
"use strict";
class Rect {
    w;
    h;
    tag;
    constructor(w, h, tag = "rect") {
        this.w = w;
        this.h = h;
        this.tag = tag;
    }
    area() {
        return this.w * this.h;
    }
    scale(factor) {
        this.w *= factor;
    }
}
const r = new Rect(2, 3);
r.scale(2);
console.log(r.area(), Object.keys(r), r instanceof Rect);
```

```text
===== node e32b/ex.32b.js (node exit=0) =====
12 [ 'w', 'h', 'tag' ] true
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **11행 `scale(factor)` 가 `TS7006`**(「Parameter 'factor' implicitly has an 'any' type.」). `Shape` 가 `scale(factor: number)` 를 **적어 뒀는데도** 매개변수 타입을 **안 받았다.**
  핸드북 — 「`implements` 절은 클래스가 그 인터페이스로 **취급될 수 있는지 검사할 뿐**, 클래스나 메서드의 타입을 **전혀** 바꾸지 않는다.」
- ★★★ 방출물 — **`class Rect {`** — `implements Shape` 가 **흔적도 없다.** `interface Shape` 도 통째로 없다.
- ★★★ **매개변수 프로퍼티** `constructor(public w: number, private h: number, readonly tag = "rect")` 가
  **필드 선언 세 줄(`w; h; tag;`)** + **생성자 대입 세 줄(`this.w = w;` …)** 로 바뀌었다. **TS 가 코드를 만들어 넣은** 몇 안 되는 자리다.
  ★ 수식어(`public`·`private`·`readonly`)는 셋 다 **사라졌다.**
- ★ `node` — `12 [ 'w', 'h', 'tag' ] true`. `private h` 도 `Object.keys` 에 **있다.**

```text
===== tsc --pretty false --noEmit -t es2022 --strict --erasableSyntaxOnly ex.32b.ts (tsc exit=1) =====
ex.32b.ts(7,17): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(7,35): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(7,54): error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.
ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

- ★★★ `--erasableSyntaxOnly` 를 주면 **7행의 세 매개변수 프로퍼티**가 각각 **`TS1294`**(열 17·35·54). **지우기만 해서는 JS 가 안 되는** 문법이기 때문이다 — 대입문을 **만들어야** 하니까.
  ★ [**31번 주제**](../31-enum-pitfalls/)의 enum 과 **같은 이유로 같은 코드**다.

```text
  매개변수 프로퍼티 — 한 줄이 여섯 줄이 된다

  constructor(public w: number, private h: number, readonly tag = "rect") {}
         │
         ▼  (방출, -t es2022)
  w;                        ← 필드 선언
  h;
  tag;
  constructor(w, h, tag = "rect") {
      this.w = w;           ← 대입문 — TS 가 만들어 넣었다
      this.h = h;
      this.tag = tag;
  }
```

```text
  implements 가 하는 일과 안 하는 일

  interface Shape { scale(factor: number): void }
  class Rect implements Shape { scale(factor) { … } }
                                      │
       하는 일 ─ Rect 의 모양이 Shape 에 맞나 검사한다          (안 맞으면 에러)
    안 하는 일 ─ factor 에 number 를 넣어 주지 않는다            → TS7006
    안 하는 일 ─ 방출물에 남지 않는다                            → class Rect {
```

비용 — 매개변수 프로퍼티는 **`--erasableSyntaxOnly` 와 못 산다**(타입만 지우는 실행기를 쓰면 막힌다). `implements` 는 **타입을 안 주므로** 메서드 매개변수에 타입을 **다시 적어야** 한다.

### (4) ★★ `abstract` — 컴파일러만 아는 「판매 금지」

**언제 쓰나** — 「이 클래스는 직접 만들지 마라」를 표시할 때.

```ts
// ex.32c.ts
// abstract 클래스와 abstract 메서드 -- 방출물과 node
abstract class Animal {
    abstract sound(): string;
    greet(): string {
        return "I say " + this.sound();
    }
}
class Dog extends Animal {
    sound(): string {
        return "woof";
    }
}
console.log("[1]", new Dog().greet());
const Ctor = Animal as unknown as new () => Animal;
try {
    console.log("[2]", new Ctor().greet());
} catch (e) {
    console.log("[2]", (e as Error).constructor.name, (e as Error).message);
}
const direct = new Animal();
console.log("[3]", typeof direct, typeof direct.greet);
```

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.32c.ts (tsc exit=1) =====
ex.32c.ts(20,16): error TS2511: Cannot create an instance of an abstract class.
```

```text
===== tsc --pretty false -t es2022 --strict --outDir e32c ex.32c.ts (tsc exit=2) =====
ex.32c.ts(20,16): error TS2511: Cannot create an instance of an abstract class.
===== 방출된 e32c/ex.32c.js =====
"use strict";
// abstract 클래스와 abstract 메서드 -- 방출물과 node
class Animal {
    greet() {
        return "I say " + this.sound();
    }
}
class Dog extends Animal {
    sound() {
        return "woof";
    }
}
console.log("[1]", new Dog().greet());
const Ctor = Animal;
try {
    console.log("[2]", new Ctor().greet());
}
catch (e) {
    console.log("[2]", e.constructor.name, e.message);
}
const direct = new Animal();
console.log("[3]", typeof direct, typeof direct.greet);
```

```text
===== node e32c/ex.32c.js (node exit=0) =====
[1] I say woof
[2] TypeError this.sound is not a function
[3] object function
```

그림 해설 — 한 단계에 한 문장.

- ★★ 진단은 **20행 `new Animal()` 하나** — **`TS2511`**(「Cannot create an instance of an abstract class.」).
  ★ 14행 `new Ctor()` 는 `as unknown as new () => Animal` 로 **30편의 이중 단언**을 거쳐 **진단이 없다.**
- ★★★ 방출물 — `abstract class Animal` 이 **`class Animal`**, `abstract sound(): string;` 은 **한 줄도 없다.** 방출물의 `Animal` 은 **`greet()` 만 가진 평범한 클래스**다.
- ★★★ `node` — `[1] I say woof` · **`[2] TypeError this.sound is not a function`** · **`[3] object function`**.
  진단이 난 20행도 **방출되어 실행됐고**, `new Animal()` 은 **멀쩡한 객체**를 만들었다(`[3]`). 터진 것은 **없는 메서드를 부를 때**(`[2]`)다.

```text
  abstract 의 한살이

  abstract class Animal { abstract sound(); greet() {…} }
         │ 방출
  class Animal { greet() {…} }          ← abstract 도, sound 선언도 없다
         │ node
  new Animal()          → 객체가 생긴다        [3]
  new Animal().greet()  → this.sound(…)  → TypeError   [2]
```

비용 — `abstract` 는 **TS 코드 안에서만** 지켜진다. JS 소비자나 이중 단언은 **그냥 `new` 한다.**

### (5) ★★★ `useDefineForClassFields` 판 격자 — 필드 선언이 「정의」인가 「대입」인가

**언제 쓰나** — `target` 을 올리거나 내릴 때, 부모에 **접근자**가 있는 클래스를 상속할 때, 필드 초기자가 **매개변수 프로퍼티를 읽을 때**.

```ts
// ex.32d.ts
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v: number) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}

class Base {
    name = "base";
}
class Redeclared extends Base {
    name!: string;
}

class Point {
    doubled = this.n * 2;
    constructor(public n: number) {}
}

const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

```bash
# ts30b-definegrid.sh
#!/usr/bin/env bash
# ex.32d.ts 를 설정 다섯 판으로 방출하고 node 로 돌린다 -- 진단이 있어도 tsc 는 방출한다(noEmitOnError 기본값 false)
set -u -o pipefail
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'   # 구분자는 탭(규칙 32)
rows=(
  "7.0.2${T}-t es2022"
  "7.0.2${T}-t es2021"
  "7.0.2${T}-t es2022 --useDefineForClassFields false"
  "7.0.2${T}-t es2021 --useDefineForClassFields true"
  "4.9.5${T}-t es2022"
)
declare -A got
first=""
for row in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$row")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $row"; exit 3; fi
  IFS="$T" read -r ver opts <<< "$row"
  if [ "$ver" = 4.9.5 ]; then cmd=(node "$V49"); else cmd=(tsc); fi
  rm -rf "$D/o"
  diag=$("${cmd[@]}" --pretty false --strict $opts --outDir "$D/o" ex.32d.ts 2>&1 | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
  run=$(node "$D/o/ex.32d.js" 2>&1)
  key="$ver $opts"; [ -z "$first" ] && first=$key
  got[$key.diag]=${diag:-OK}
  for i in 1 2 3; do got[$key.$i]=$(grep "^\[$i\]" <<< "$run"); done
  got[$key.setter]=$(grep -c 'Parent setter' <<< "$run" || true)
  echo "[$key]"
  printf '    진단   %s\n' "${diag:-OK}"
  printf '    setter 호출 %s번\n' "${got[$key.setter]}"
  for i in 1 2 3; do printf '    %s\n' "${got[$key.$i]}"; done
done
diff=0; total=0
for row in "${rows[@]:1}"; do
  IFS="$T" read -r ver opts <<< "$row"; key="$ver $opts"
  for col in diag setter 1 2 3; do
    total=$((total+1)); if [ "${got[$key.$col]}" != "${got[$first.$col]}" ]; then diff=$((diff+1)); fi
  done
done
echo
echo "첫 행($first)과 갈린 칸 $diff / $total"
```

```text
===== bash ts30b-definegrid.sh (sh exit=0) =====
[7.0.2 -t es2022]
    진단   TS2610 TS2612 TS2729
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  NaN
[7.0.2 -t es2021]
    진단   TS2610
    setter 호출 1번
    [1] Child      own keys [] x -1
    [2] Redeclared name     base
    [3] Point      doubled  42
[7.0.2 -t es2022 --useDefineForClassFields false]
    진단   TS2610
    setter 호출 1번
    [1] Child      own keys [] x -1
    [2] Redeclared name     base
    [3] Point      doubled  42
[7.0.2 -t es2021 --useDefineForClassFields true]
    진단   TS2610 TS2612
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  42
[4.9.5 -t es2022]
    진단   TS2610 TS2612
    setter 호출 0번
    [1] Child      own keys ["x"] x 1
    [2] Redeclared name     undefined
    [3] Point      doubled  NaN

첫 행(7.0.2 -t es2022)과 갈린 칸 13 / 20
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **`7.0.2 -t es2022`** — 부모 setter **0번**, `[1] own keys ["x"] x 1` · **`[2] undefined`** · **`[3] NaN`**. 진단 `TS2610 TS2612 TS2729`.
- ★★★ **`7.0.2 -t es2021`** — setter **1번**, `[1] own keys [] x -1` · **`[2] base`** · **`[3] 42`**. 진단 `TS2610` 만.
- ★★ **`-t es2022 --useDefineForClassFields false`** 가 **`-t es2021` 과 다섯 칸이 한 글자도 같다.** 달라진 것은 **타깃이 아니라 이 플래그**다 — 기본값이 **타깃에 달려 있다**는 증거다.
- ★★★ **`-t es2021 --useDefineForClassFields true`** — `[1]`·`[2]` 는 첫 판(`es2022`)과 같은데 **`[3]` 은 `42`** 다. **여기서 갈린다.**
- ★★ **`4.9.5 -t es2022`** — 실행 세 줄은 **7.0.2 첫 판과 같고**(`NaN` 까지) 진단만 **`TS2610 TS2612`** — **`TS2729` 가 없다.**
- ★★ 마지막 줄 **첫 행과 갈린 칸 13 / 20**.

```text
===== tsc --pretty false -t es2022 --strict --outDir e32d ex.32d.ts (tsc exit=2) =====
ex.32d.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
ex.32d.ts(18,5): error TS2612: Property 'name' will overwrite the base property in 'Base'. If this is intentional, add an initializer. Otherwise, add a 'declare' modifier or remove the redundant declaration.
ex.32d.ts(22,20): error TS2729: Property 'n' is used before its initialization.
===== 방출된 e32d/ex.32d.js =====
"use strict";
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}
class Base {
    name = "base";
}
class Redeclared extends Base {
    name;
}
class Point {
    n;
    doubled = this.n * 2;
    constructor(n) {
        this.n = n;
    }
}
const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

```text
===== tsc --pretty false -t es2021 --strict --useDefineForClassFields true --outDir e32d21 ex.32d.ts (tsc exit=2) =====
ex.32d.ts(11,5): error TS2610: 'x' is defined as an accessor in class 'Parent', but is overridden here in 'Child' as an instance property.
ex.32d.ts(18,5): error TS2612: Property 'name' will overwrite the base property in 'Base'. If this is intentional, add an initializer. Otherwise, add a 'declare' modifier or remove the redundant declaration.
===== 방출된 e32d21/ex.32d.js =====
"use strict";
// 필드 선언이 방출물에서 무엇이 되나 -- 세 가지 클래스
class Parent {
    set x(v) {
        console.log("    (Parent setter got " + v + ")");
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    constructor() {
        super(...arguments);
        Object.defineProperty(this, "x", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: 1
        });
    }
}
class Base {
    constructor() {
        Object.defineProperty(this, "name", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: "base"
        });
    }
}
class Redeclared extends Base {
    constructor() {
        super(...arguments);
        Object.defineProperty(this, "name", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
    }
}
class Point {
    constructor(n) {
        Object.defineProperty(this, "n", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: n
        });
        Object.defineProperty(this, "doubled", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: this.n * 2
        });
    }
}
const c = new Child();
console.log("[1] Child      own keys", JSON.stringify(Object.keys(c)), "x", c.x);
console.log("[2] Redeclared name    ", new Redeclared().name);
console.log("[3] Point      doubled ", new Point(21).doubled);
```

- ★★★ **`[3]` 이 갈린 이유는 방출물에 있다.** `es2022` 판은 **네이티브 필드** `n; doubled = this.n * 2;` 를 쓰고 생성자에서 `this.n = n` — **필드 초기자가 생성자 몸통보다 먼저** 돌아 `this.n` 이 `undefined`, 그래서 `NaN`.
  `es2021 + true` 판은 **둘 다 생성자 안의 `Object.defineProperty`** 로 옮기되 **`n` 을 먼저** 정의한다 — 순서가 살아서 `42`.
  ★ 그러니 `NaN` 은 `useDefineForClassFields` 가 아니라 **「네이티브 필드로 방출했나」** 에 달렸다.
- ★★★ **`[1]` — JS 16편 4절과 같은 갈림길이다.** 필드 `x = 1` 이 **정의**(`defineProperty` 또는 네이티브 필드)로 방출되면 부모 setter 를 **안 부르고** own 키가 생긴다((가)).
  **대입**(`this.x = 1`)으로 방출되면 setter 가 **가져간다**((나)). TS 는 **같은 소스를 설정에 따라 두 길 중 하나로** 보낸다.
- ★★ **`[2]` — `name!: string` 재선언**이 정의로 방출되면 **`undefined` 로 덮는다**(부모가 넣은 `"base"` 를 지운다). `TS2612` 가 그것을 경고한다 — 「`declare` 를 붙이거나 지워라」.

```text
  같은 한 줄 「x = 1」 — 설정에 따라 두 길(JS 16편 4절의 (가)·(나))

  useDefineForClassFields true        class Child { x = 1; }                 (가) 정의
  (es2022 이상 기본)                   또는 Object.defineProperty(this, "x")   → setter 0번 · own ["x"]

  useDefineForClassFields false       constructor() { super(…); this.x = 1; } (나) 대입
  (es2021 이하 기본)                                                         → setter 1번 · own []
```

비용 — **타깃을 올리는 것만으로** 부모 setter 가 안 불리게 되고, 재선언 필드가 `undefined` 가 되고, 초기자가 `NaN` 이 될 수 있다. `TS2610`·`TS2612`·`TS2729` 가 그 세 자리를 **경고**한다.

### (6) ★ 설정 대조

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.32a.ts    exit 0 = exit 0 · 출력 한 글자도 같다
ex.32b.ts    exit 1 = exit 0 · ★ 출력이 다르다
ex.32c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.32d.ts    exit 1 = exit 1 · 출력 한 글자도 같다
```

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.32b.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.32b.ts) (sh exit=1) =====
1d0
< ex.32b.ts(11,11): error TS7006: Parameter 'factor' implicitly has an 'any' type.
```

- ★★ `ex.32b.ts` 만 갈렸다 — `--strict false` 에서 **`TS7006` 이 사라진다**(`noImplicitAny` 가 꺼진다). `implements` 가 타입을 안 준다는 사실은 **`strict` 가 켜져 있어야 드러난다.**
- ★ 나머지 셋은 두 판이 **한 글자도 같다** — `abstract`·`private`·필드 방출 경고는 `strict` 에 안 달렸다.

비용 — 없다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  private x = 1;                     컴파일러만 막는다 · 방출물 x = 1;           (1·2절)
  protected x = 1; / readonly x = 1; 같다                                        (1절)
  #x = 1;                            JS 문법 · 방출물에 남는다(es2021 → WeakMap)  (1·2절)
  class C implements I { … }         검사만 · 방출물에 없다 · 타입을 안 준다      (3절)
  constructor(public x: T) {}        필드 선언 + 생성자 대입으로 방출              (3절)
  abstract class A { abstract m(); } new 를 컴파일러만 막는다 · 방출물 평범한 class (4절)
  name!: T  /  declare name: T       재선언 — 정의로 방출되면 덮는다 / 방출 안 됨  (5절 · 3.7 릴리스 노트)
```

**금지 사례** — 이 주제에서 던져 받은 것이다.

| 쓴 꼴 | 진단 | 어느 절 |
|---|---|---|
| 바깥에서 `o.x` — `private` | `TS2341` | 1절 |
| 바깥에서 `o.x` — `protected` | `TS2445` | 1절 |
| `readonly` 에 대입 | `TS2540` | 1절 |
| 바깥에서 `o.#x` | `TS18013` | 1절 |
| `implements` 한 메서드의 매개변수에 타입 없음 | `TS7006` | 3절 |
| `--erasableSyntaxOnly` 에서 매개변수 프로퍼티 | `TS1294` | 3절 |
| `abstract` 클래스를 `new` | `TS2511` | 4절 |
| 부모 접근자를 자식 필드로 덮음 | `TS2610` | 5절 |
| 부모 필드를 초기자 없이 재선언(정의 방출일 때) | `TS2612` | 5절 |
| 필드 초기자가 초기화 전의 매개변수 프로퍼티를 읽음 | `TS2729` — **7.0.2** (4.9.5 는 안 냄) | 5절 |

**규칙 불릿**

- ★★★ **`private`·`protected`·`readonly` 는 방출물에서 사라진다** — 런타임에 막힌 칸 **0 / 20**(1절).
- ★★★ **`#x` 는 방출물에 남는다** — `keys`·`json` 에 안 보이고 바깥 접근은 **파싱 에러**(1절).
- ★★ **`o["x"]` 는 `private` 를 컴파일러에서도 넘는다**(1절 `brack` · 핸드북의 「soft private」).
- ★★★ **`implements` 는 검사만 하고 타입을 안 준다**(3절 `TS7006`).
- ★★ **매개변수 프로퍼티는 TS 가 대입문을 만들어 넣는 문법이다** — 그래서 `--erasableSyntaxOnly` 가 막는다(3절).
- ★★★ **`useDefineForClassFields` 기본값은 타깃에 달렸다** — es2022 에서 켜지고 es2021 에서 꺼진다(5절).

## 어디서 틀리나

- ★★★ 「**`private` 필드는 바깥에서 안 보인다**」 — `Object.keys`·`JSON.stringify`·스프레드에 **다 보인다**(1·2절).
- ★★★ 「**`private` 는 컴파일러가 확실히 막는다**」 — **`o["x"]` 는 진단 없이 통과**한다(1절 `brack`).
- ★★ 「**`readonly` 필드는 못 바꾼다**」 — 방출물은 **9 를 썼다**(1절 `write`). 런타임 동결은 `Object.freeze` 의 몫이다([**07번 주제**](../07-object-type-details/)).
- ★★★ 「**`implements` 하면 메서드 매개변수 타입이 따라온다**」 — **안 따라온다.** `TS7006`(3절).
- ★★ 「**`abstract` 클래스는 인스턴스를 못 만든다**」 — **TS 코드에서만.** 방출물은 `new` 가 되고 **없는 메서드를 부를 때** 터진다(4절).
- ★★★ 「**`target` 만 올렸는데 동작은 같겠지**」 — 부모 setter · 재선언 필드 · 초기자 순서가 **셋 다** 바뀔 수 있다(5절 **13 / 20**).
- ★★ 「**`#x` 의 `SyntaxError` 가 런타임 보호다**」 — 그것은 **문법**이다. 런타임 보호(`TypeError`)는 **클래스 안 코드가 남의 객체를 읽을 때**다 — JS 16편 5절.
- ★ 「**`name!: string` 은 부모 값을 그대로 쓴다는 뜻**」 — 정의로 방출되면 **`undefined` 로 덮는다**(5절 `[2]`). 그 뜻이면 `declare name: string` 이다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(핸드북)** | `private` 는 「soft private」 — **괄호 접근은 타입 검사 중에도 허용** · `#` 는 컴파일 뒤에도 비밀 | 핸드북 · 1절 |
| **언어 보장(핸드북)** | `implements` 는 **검사일 뿐** 클래스·메서드의 타입을 바꾸지 않는다 | 핸드북 · 3절 |
| **언어 보장(핸드북)** | `abstract` 클래스는 **직접 인스턴스화할 수 없다**(타입 검사 규칙) | 핸드북 · 4절 `TS2511` |
| **언어 보장(ECMAScript)** | 클래스 바깥의 `o.#x` 는 **문법 에러** · 필드는 **정의**(`DefineField`) | JS 16편 · 1절 |
| **언어 보장(3.7 · 5.8)** | `useDefineForClassFields` 는 정의 방출로 바꾸는 플래그 · `--erasableSyntaxOnly` 는 매개변수 프로퍼티를 막는다 | 릴리스 노트 · 3·5절 |
| **★ 이 판(7.0.2)의 관찰** | `useDefineForClassFields` 기본값이 **es2022 에서 켜지고 es2021 에서 꺼진다** | 5절 — TSConfig 페이지 본문에 **문장이 없어** 던져서 얻었다 |
| **★ 이 판의 관찰** | `es2021 + true` 판이 매개변수 프로퍼티를 **먼저** 정의해 `42` | 5절 — 방출기의 순서 선택이다 |
| **★ 판 격자** | 4.9.5 는 `TS2729` 를 안 낸다 | 5절 |
| **★ 이 판의 관찰** | 하향 방출 도우미의 `TypeError` 문구 | 2절 `-t es2021` 방출물 |
| **★ 부적용 — 5창(`.d.ts`)** | 선언 방출은 안 물었다 | — |
| **안 잰 것** | `#private`·WeakMap 방출의 속도·메모리 | **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| **`#x`** — 런타임에도 **숨겨야** 할 것(토큰·내부 상태) · 직렬화에 **새면 안 되는** 것 | 테스트·디버거에서 **읽어야** 할 것 — 옆문이 없다 |
| **`private`** — 팀 안의 **설계 의도** 표시 · 직렬화돼도 괜찮은 것 | ★★★ **비밀** — `JSON.stringify` 에 나간다(2절) |
| **`implements`** — 「이 클래스가 계약을 지키나」를 **검사**받고 싶을 때 | 메서드 타입을 **물려받으려고** — 안 준다(3절) |
| **매개변수 프로퍼티** — 생성자 인자 → 필드 보일러플레이트 줄이기 | `--erasableSyntaxOnly` 를 쓸 때 — `TS1294`(3절) |
| **`abstract`** — 하위 클래스가 **채워야 할 자리** 표시 | JS 소비자에게 **런타임 보호**가 필요할 때 — 생성자에서 `new.target` 을 확인하는 쪽이다(**여기서는 안 던졌다**) |
| **`declare name: T`** — 부모가 채운 필드의 **타입만** 좁힐 때 | `name!: T` — 정의 방출에서 **덮는다**(5절) |

```text
  private 냐 # 냐 — 1·2절에서 거꾸로 세운 선택

  JSON·로그·스프레드로 새면 안 되는가?
    예 ──> #x                     (keys [] · json {} — 1절)
    아니오
  테스트·디버거에서 옆문으로 읽어야 하는가?
    예 ──> private x              (o["x"] 가 통과 — 1절 brack)
    아니오 ──> 둘 다 된다 — 팀의 관례를 따른다
```

## 핵심 문장

1. **TS 의 클래스 수식어는 방출물에서 전부 사라진다** — `private` 필드는 `keys`·`json`·스프레드에 그대로 보인다.
2. **런타임에 남는 비밀은 JS 의 `#` 하나다** — 격자의 막힌 칸 **10 / 30** 이 전부 `#x` 행이다.
3. **`implements` 는 검사만 하고, 매개변수 프로퍼티는 대입문을 만든다** — 하나는 사라지고 하나는 코드가 생긴다.
4. **필드 선언이 「정의」인가 「대입」인가는 `useDefineForClassFields` 가 정하고, 그 기본값은 타깃이 정한다.**

## 관련 자료

- JS 갈래 [`../../../js/syntax/16-class-syntax/`](../../../js/syntax/16-class-syntax/) — ★★★ **README 의 선행(JS 16).** `#private` 의 경계는 그쪽 1절 `[3]`(바깥 창 일곱 가지)과 5절(브랜드 태그·`Proxy` 트랩·`#x in obj`), 「필드 = 정의, 생성자 대입 = 대입」은 그쪽 4절이 정본이다. **여기는 TS 수식어가 방출물에서 무엇이 되나부터.**
- [**05번 주제** — 구조적 타이핑](../05-structural-typing/) — ★ README 의 선행. `implements` 없이도 **모양이 맞으면** 할당된다 — `implements` 는 그 위에 **검사**만 얹는다.
- [**23번 주제** — `typeof` 타입 연산자](../23-typeof-type-operator/) — 클래스가 **값이자 타입**이라는 것(`typeof Class` 는 생성자)은 그쪽 3절.
- [**07번 주제** — 객체 타입 세부](../07-object-type-details/) — `readonly` 가 런타임을 막지 않는다는 실측의 정본.
- [**30번 주제** — 타입 단언과 non-null `!`](../30-type-assertions-and-non-null/) — 4절의 `as unknown as` 우회, 5절의 `name!` 은 그쪽의 「선언 쪽 `!`」이다.
- [**31번 주제** — 열거형의 함정](../31-enum-pitfalls/) — `--erasableSyntaxOnly` 가 enum 과 매개변수 프로퍼티를 **같은 `TS1294`** 로 막는다.
- 목록의 **47번 주제**(데코레이터) — 클래스 필드 방출과 데코레이터가 만나는 자리는 그쪽.
- Kotlin 갈래 [`../../../kotlin/syntax/18-visibility-modifiers/`](../../../kotlin/syntax/18-visibility-modifiers/) — `private` 가 **바이트코드 수준에서** 지켜지는 언어와의 비교 축.

## 용어 풀이

> **soft private** — 컴파일러만 막고 방출물에서는 평범한 프로퍼티가 되는 비공개. TS `private`·`protected`.\
> 예: 1절 `[private]` — `o["x"]` 가 진단 없이 `1`.

> **hard private** — 방출물·런타임에서도 비공개인 것. JS `#x`.\
> 예: 1절 `[#x]` — `Object.keys` 가 `[]`.

> **매개변수 프로퍼티(parameter property)** — 생성자 매개변수에 `public`·`private`·`readonly` 를 붙여 **필드 선언 + 대입**을 한 번에 적는 TS 문법.\
> 예: 3절 — `public w` 가 방출물에서 `w;` + `this.w = w;`.

> **`implements`** — 클래스가 인터페이스 모양을 **만족하는지 검사**하는 절. 타입을 주지 않고 방출물에 없다.\
> 예: 3절 — `scale(factor)` 가 `TS7006`.

> **`abstract`** — 직접 `new` 할 수 없는 클래스·구현이 없는 멤버를 표시. 방출물에서 사라진다.\
> 예: 4절 — `new Animal()` 은 `TS2511` 인데 방출물은 실행된다.

> **`useDefineForClassFields`** — 클래스 필드를 **`[[Define]]`(정의)** 으로 방출할지 **`[[Set]]`(대입)** 으로 방출할지 고르는 플래그.\
> 예: 5절 — `true` 면 부모 setter 0번, `false` 면 1번.

> **`TS2729`** — 「Property 'n' is used before its initialization.」 필드 초기자가 아직 초기화 안 된 것을 읽을 때.\
> 예: 5절 `Point` — 7.0.2 만 낸다.

## 더 들어가면

- **`#x` 의 WeakMap 하향 방출** — 2절 `-t es2021` 방출물의 `__classPrivateFieldGet` 가 **브랜드 검사**(`state.has(receiver)`)를 흉내 낸다. 칸 없는 객체에 쓰면 `TypeError` 가 날 것으로 **읽히지만 던지지 않았다.**
- **`declare` 필드** — 3.7 릴리스 노트는 `declare resident: Dog;` 가 **출력 코드를 만들지 않는다**고 적는다. 5절 `[2]` 의 `name!` 을 `declare name` 으로 바꾸면 `"base"` 가 남을 것 — **던지지 않았다.**
- **`protected` 와 구조적 타이핑** — `private`·`protected` 멤버가 있는 클래스는 **모양이 같아도** 다른 클래스와 호환되지 않는다(명목적으로 군다). 05편의 브랜드 타입과 같은 효과다 — **여기서는 안 던졌다.**
- **`accessor` 키워드·데코레이터** — 목록의 **47번 주제**.
