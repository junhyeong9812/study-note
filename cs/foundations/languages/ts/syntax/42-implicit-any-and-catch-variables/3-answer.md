# ts/syntax/42 — 암시적 `any` 와 catch 변수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출물·실행은 `tsc` **7.0.2** · `node` **v18.19.1** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ 이 주제의 **본체 창은 「암시적 `any` 격자」(자리 아홉 × 켬/끔 × 두 판)이고, 둘째 기둥은 3창(방출물 + `node`)이다.** `JSON.parse` 의 `any` 는 진단 창이 답하지 않아 **`node` 창으로 바꿔** 물었다(제5의 상태).\
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 켬 — a `TS7006` · b `TS7031` · c `TS7019` · e `TS7005`+`TS7034` · i `TS7053`, 나머지 넷(d·f·g·h)은 OK · 끔 — **f 만 `TS2345`** · 두 판이 갈린 탐침 **`0 / 9`**

**출력**

```bash
# ts42b-grid42.sh
#!/usr/bin/env bash
# 암시적 any 가 생길 만한 자리 아홉 × noImplicitAny 켬/끔 × 판 둘 -- 칸마다 디렉토리와 tsconfig.json 을 따로 만든다
# 설정은 늘 "strict": true 위에 noImplicitAny 하나만 적는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\t'
rows=(
  "ia42a.ts${T}매개변수"
  "ia42b.ts${T}구조 분해 매개변수"
  "ia42c.ts${T}나머지 매개변수"
  "ia42d.ts${T}let v; 뒤 대입"
  "ia42e.ts${T}let v; 을 함수가 읽음"
  "ia42f.ts${T}빈 배열 []"
  "ia42g.ts${T}콜백 매개변수"
  "ia42h.ts${T}JSON.parse 반환"
  "ia42i.ts${T}o[k] 인덱스 접근"
)
codes() { grep -o 'error TS[0-9]*' | sed 's/^error //' | sort -u | tr '\n' ' ' | sed 's/ $//'; }
printf '%-9s %-6s %-16s %-10s %s\n' "탐침" "판" "켬" "끔" "자리"
all=""; i=0; split_flag=0; split_ver=0; total=0
for r in "${rows[@]}"; do
  n=$(awk -F'\t' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r probe where <<< "$r"
  declare -A got=()
  for s in true false; do
    i=$((i+1)); d="$D/c$i"; mkdir -p "$d" && cp "$probe" "$d/" || exit 3
    printf '{ "compilerOptions": { "strict": true, "noImplicitAny": %s, "target": "es2022", "noEmit": true }, "files": ["%s"] }\n' "$s" "$probe" > "$d/tsconfig.json"
    raw7=$(cd "$d" && tsc --pretty false -p tsconfig.json 2>&1); raw5=$(cd "$d" && node "$OLD" --pretty false -p tsconfig.json 2>&1)
    case "$raw7$raw5" in *"error TS5"*) echo "★ 설정 진단(TS5xxx)이 칸에 들었다 -- 격자를 믿지 마라"; exit 4 ;; esac
    got[7,$s]=$(codes <<< "$raw7"); got[5,$s]=$(codes <<< "$raw5")
  done
  for v in 7 5; do
    total=$((total+1))
    [ "${got[$v,true]}" != "${got[$v,false]}" ] && split_flag=$((split_flag+1))
    all="$all|${got[$v,true]:-OK}|${got[$v,false]:-OK}"
  done
  [ "${got[7,true]}${T}${got[7,false]}" != "${got[5,true]}${T}${got[5,false]}" ] && split_ver=$((split_ver+1))
  printf '%-9s %-6s %-16s %-10s %s\n' "$probe" "7.0.2" "${got[7,true]:-OK}" "${got[7,false]:-OK}" "$where"
  printf '%-9s %-6s %-16s %-10s %s\n' "" "5.9.3" "${got[5,true]:-OK}" "${got[5,false]:-OK}" ""
  unset got
done
kinds_seen=$(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)
if [ "$kinds_seen" -lt 2 ]; then echo "★ 모든 칸이 같은 코드다 -- 가짜 격자 의심, 멈춘다"; exit 5; fi
echo
echo "칸에 나온 코드 가짓수 $kinds_seen · 켬과 끔이 갈린 칸 $split_flag / $total · 두 판이 갈린 탐침 $split_ver / ${#rows[@]}"
```

```text
===== bash ts42b-grid42.sh (sh exit=0) =====
탐침    판    켬              끔        자리
ia42a.ts  7.0.2  TS7006           OK         매개변수
          5.9.3  TS7006           OK         
ia42b.ts  7.0.2  TS7031           OK         구조 분해 매개변수
          5.9.3  TS7031           OK         
ia42c.ts  7.0.2  TS7019           OK         나머지 매개변수
          5.9.3  TS7019           OK         
ia42d.ts  7.0.2  OK               OK         let v; 뒤 대입
          5.9.3  OK               OK         
ia42e.ts  7.0.2  TS7005 TS7034    OK         let v; 을 함수가 읽음
          5.9.3  TS7005 TS7034    OK         
ia42f.ts  7.0.2  OK               TS2345     빈 배열 []
          5.9.3  OK               TS2345     
ia42g.ts  7.0.2  OK               OK         콜백 매개변수
          5.9.3  OK               OK         
ia42h.ts  7.0.2  OK               OK         JSON.parse 반환
          5.9.3  OK               OK         
ia42i.ts  7.0.2  TS7053           OK         o[k] 인덱스 접근
          5.9.3  TS7053           OK         

칸에 나온 코드 가짓수 7 · 켬과 끔이 갈린 칸 12 / 18 · 두 판이 갈린 탐침 0 / 9
```

**왜 그런가**

- ★★★ 켬에서 잡힌 다섯은 전부 **타입을 적지도 추론하지도 못한** 자리다 — 매개변수·구조 분해·나머지·함수가 읽는 `let v;`·`string` 키 인덱스.
- ★★★ 켬에서 조용한 넷은 **까닭이 다르다** — `ia42d`·`ia42f` 는 **대입을 보며 타입이 자라서**, `ia42g` 는 **문맥 타입**을 받아서, `ia42h` 는 **선언이 `any` 라고 적혀 있어서**(명시적 `any`).
- ★★ 판은 코드를 안 바꿨다 — 7.0.2 와 5.9.3 이 **규칙은 같고 기본값만** 다르다(39편).
- ★★ 마지막 줄 **켬과 끔이 갈린 칸 `12 / 18`**.

### 2. ★★★ `--noImplicitAny false` 만 **`TS2345`**(`never`) · `strictNullChecks` 까지 끄거나 `--strict false` 면 **`(exit 0)`**

**출력**

```ts
// ia42f.ts
const xs = [];
xs.push(1);
const ys: number[] = xs;
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 ia42f.ts 에 <--noImplicitAny false · --noImplicitAny false --strictNullChecks false · --strict false> (sh exit=0) =====
---- --noImplicitAny false
ia42f.ts(2,9): error TS2345: Argument of type '1' is not assignable to parameter of type 'never'.
(exit 1)
---- --noImplicitAny false --strictNullChecks false
(exit 0)
---- --strict false
(exit 0)
```

**왜 그런가**

- ★★★ 빈 배열이 **대입을 보며 자라는 것**은 `noImplicitAny` 가 켜진 판의 동작이다. 끄고 `strictNullChecks` 를 둔 칸에서는 **`never[]`** 로 굳어 `push(1)` 이 막힌다.
- ★★ 「`noImplicitAny` 를 끄면 진단이 줄기만 한다」가 틀리는 칸이다 — 1번 격자에서 **`ia42f` 만 끔 쪽에 진단이** 있던 까닭.

### 3. ★★★ a **0줄 `(exit 0)`** · b **`TS18046`** · c **0줄** — `node` 는 a 가 **`TypeError`(「port.toFixed is not a function」)**, c 가 **`number 0.0`**

**출력**

```ts
// json42a.ts
const conf = JSON.parse('{"port":"8080"}');
const port: number = conf.port;
console.log(typeof port, port.toFixed(1));
export {};
```

```ts
// json42b.ts
const conf: unknown = JSON.parse('{"port":"8080"}');
const port: number = conf.port;
console.log(typeof port, port.toFixed(1));
export {};
```

```ts
// json42c.ts
const conf: unknown = JSON.parse('{"port":"8080"}');
const port =
    typeof conf === "object" && conf !== null && "port" in conf && typeof conf.port === "number"
        ? conf.port
        : 0;
console.log(typeof port, port.toFixed(1));
export {};
```

```text
===== tsc --pretty false --noEmit -t es2022 <json42a.ts · json42b.ts · json42c.ts 를 하나씩> (sh exit=0) =====
---- json42a.ts
(exit 0)
---- json42b.ts
json42b.ts(2,22): error TS18046: 'conf' is of type 'unknown'.
(exit 1)
---- json42c.ts
(exit 0)
```

```js
// run42.cjs
// 방출된 파일을 차례로 require 한다 -- 던지면 스택 대신 이름과 메시지만 찍는다(스택에는 절대 경로가 박힌다)
for (const f of process.argv.slice(2)) {
    console.log("---- " + f);
    try {
        require("./" + f);
    } catch (e) {
        console.log("threw " + e.name + " -- " + e.message);
    }
}
```

```text
===== tsc --pretty false -t es2022 --module commonjs --outDir e42 json42a.ts json42c.ts ; 이어서 node run42.cjs e42/json42a.js e42/json42c.js (sh exit=0) =====
(tsc exit 0)
---- e42/json42a.js
threw TypeError -- port.toFixed is not a function
---- e42/json42c.js
number 0.0
(node exit 0)
```

**왜 그런가**

- ★★★ `json42a` 의 `conf` 는 **`any`** 다 — `conf.port` 를 `number` 칸에 넣어도 검사가 없다. 실제 값은 문자열이라 `toFixed` 가 없다.
- ★★ `json42b` 는 받는 쪽 `: unknown` 한 단어로 **`TS18046`** — 좁히기 전에 못 쓴다.
- ★★ `json42c` 는 네 조각으로 좁혔다 — `"8080"` 이 문자열이라 **기본값 `0`** 으로 갔다. 같은 입력에서 터지지 않는다.

### 4. ★★★ 두 판 모두 **통과**(`exit 0`) · `as Error` 는 `"m"` 에 **`message undefined`**, `null` 에 **`TypeError`** · `vm realm Error` 의 `instanceof` 는 **`else`**

**출력**

```text
===== tsc --pretty false --noEmit -t es2022 catch42.ts ; 이어서 "$TSC_OLD" 로 --strict 를 붙여 같은 것 (sh exit=0) =====
(7.0.2 exit 0)
(5.9.3 exit 0)
```

```text
===== node e42c/catch42.js ; 이어서 "$NODE20" 로 같은 것을 돌려 cmp (sh exit=0) =====
(node exit 0)
thrown            instanceof   | typeof       | guard        | as Error
new Error("m")    Error m      | else         | message m    | message m
"m"               else         | string m     | else         | message undefined
null              else         | else         | else         | TypeError
{ message: "m" }  else         | else         | message m    | message m
vm realm Error    else         | else         | message m    | message m
node v20.19.6 의 출력: 한 글자도 같다
```

**왜 그런가**

- ★★★ **검사기는 넷 중 무엇이 거짓말하는지 가르지 않는다** — 넷 다 `unknown` 을 받아 통과한다. 갈림은 **`node` 창에서만** 보인다.
- ★★★ `as Error` 는 **확인하지 않는다**(8번) — 문자열에는 `message` 가 없어 **조용히 `undefined`**, `null` 은 읽는 순간 `TypeError`.
- ★★★ `instanceof Error` 는 **이 realm 의 `Error`** 만 본다 — `vm` 컨텍스트가 만든 `Error` 는 `else`. 모양을 보는 `guard` 는 잡는다(대신 `{ message: "m" }` 흉내도 잡는다).
- ★ node 20 도 한 글자도 같았다(블록 끝 줄).

### 5. ★★★ 2행 `catch (e)` 만 켬/끔으로 갈린다(`TS2322` ↔ 침묵) · **3·4행 거절 사유는 늘 침묵(`any`)** · 5행 늘 `TS2322` · 7행 늘 `TS1196` — **세 판이 같다**

**출력**

```bash
# ts42b-reason42.sh
#!/usr/bin/env bash
# reason42.ts 를 useUnknownInCatchVariables 켬/끔 × 판 셋으로 -- 줄마다 난 진단(행:코드)
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
cells() { grep -o '^reason42.ts([0-9]*,[0-9]*): error TS[0-9]*' | sed 's/^reason42.ts(\([0-9]*\),[0-9]*): error /\1:/' | tr '\n' ' ' | sed 's/ $//'; }
printf '%-8s %-6s %s\n' "판" "설정" "행:코드"
all=""
for v in 7.0.2 5.9.3 4.9.5; do
  for u in true false; do
    case $v in 7.0.2) c=(tsc) ;; 5.9.3) c=(node "$OLD") ;; 4.9.5) c=(node "$V49") ;; esac
    raw=$("${c[@]}" --pretty false --noEmit -t es2022 --strict --useUnknownInCatchVariables "$u" reason42.ts 2>&1)
    case "$raw" in *"error TS5"*) echo "★ 설정 진단(TS5xxx)이 들었다 -- 멈춘다"; exit 4 ;; esac
    got=$(cells <<< "$raw"); all="$all|$got"
    printf '%-8s %-6s %s\n' "$v" "$u" "$got"
  done
done
echo
echo "켬/끔 × 판 여섯 줄에서 서로 다른 답 $(tr '|' '\n' <<< "$all" | sed '/^$/d' | sort -u | wc -l)가지"
```

```text
===== bash ts42b-reason42.sh (sh exit=0) =====
판      설정 행:코드
7.0.2    true   2:TS2322 5:TS2322 7:TS1196
7.0.2    false  5:TS2322 7:TS1196
5.9.3    true   2:TS2322 5:TS2322 7:TS1196
5.9.3    false  5:TS2322 7:TS1196
4.9.5    true   2:TS2322 5:TS2322 7:TS1196
4.9.5    false  5:TS2322 7:TS1196

켬/끔 × 판 여섯 줄에서 서로 다른 답 2가지
```

**왜 그런가**

- ★★★ `null` 탐침은 **`unknown` 이면 `TS2322`, `any` 면 침묵**한다 — 침묵이 곧 「`any` 다」라는 답이다.
- ★★★ `useUnknownInCatchVariables` 는 **`catch` 절의 변수만** 바꾼다 — `Promise` 콜백의 매개변수는 **`lib` 선언이 `any`** 로 적어 둔 자리라 플래그가 안 닿는다.
- ★★ 마지막 줄 **서로 다른 답 2가지** — 켬 셋 · 끔 셋이 각각 한 글자도 같다.

### 6. ★★ `ia42d` 는 **대입을 보며 `number` 로 자라** 암시적 `any` 가 안 남는다 · `ia42e` 는 **함수 `read` 가 `v` 를 읽어서** 그 자리의 타입을 정할 수 없다(`TS7034`+`TS7005`)

- ★★ 함수는 **언제 불릴지 모른다** — 제어 흐름이 `v = 1` 뒤라는 것을 함수 몸통 안까지 넘겨주지 못한다. 그래서 **선언 자리**(`TS7034`)와 **읽는 자리**(`TS7005`) 두 줄이 난다.

### 7. ★★★ `JSON.parse` 의 반환은 **선언에 `any` 라고 적힌 명시적 `any`** 다 — `noImplicitAny` 는 「못 정해서 생긴」 `any` 만 본다 · 막는 수는 **받는 쪽 `: unknown`**

```text
===== lib.es5.d.ts 에서 JSON.parse · Promise.prototype.catch 의 선언 줄 -- 7.0.2(PATH 의 tsc 곁 패키지) · 5.9.3("$TSC_OLD" 곁) (sh exit=0) =====
---- 7.0.2
1161:    parse(text: string, reviver?: (this: any, key: string, value: any) => any): any;
1562:    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): Promise<T | TResult>;
---- 5.9.3
1163:    parse(text: string, reviver?: (this: any, key: string, value: any) => any): any;
1564:    catch<TResult = never>(onrejected?: ((reason: any) => TResult | PromiseLike<TResult>) | undefined | null): Promise<T | TResult>;
```

- ★★★ **`parse(…): any;`** — 두 판의 `lib.es5.d.ts` 가 반환을 **`any` 로 적어 둔다.** 같은 블록의 `catch` 는 **`(reason: any)`** 다(5번).
- ★★ 같은 이유로 1번의 `ia42h` 두 칸이 다 OK 였다. `: unknown` 을 붙인 `json42b` 는 바로 `TS18046`(3번).

### 8. ★★★ **`return "message " + e.message;`** — `as Error` 가 한 글자도 안 남는다 · 그래서 `"m"` 을 던지면 문자열의 `message` 를 읽어 **`undefined`**

**출력**

```text
===== tsc --pretty false -t es2022 --module commonjs --outDir e42c catch42.ts ; 방출물에서 viaAs 함수만 sed 로 (sh exit=0) =====
(tsc exit 0)
function viaAs(e) {
    return "message " + e.message;
}
```

- ★★ 단언은 **검사만 끈다** — 실행 시 확인은 없다(30편).

### 9. ★★ `catch (e: Error)` 는 **`TS1196`** · 적을 수 있는 것은 **`unknown`·`any`** 둘 · 거절 사유는 **`(r: unknown) => …` 를 직접 적는다**

- ★★ 5번의 7행이 `TS1196`, 5행(`unknown`)·6행(`any`)은 받아들여졌다. 3·4행의 `r` 은 플래그와 무관하게 `any` 라 **직접 적는 것 말고 길이 없다.**

### 10. ★★ 39편 `pr39h` → **4·5절**(`catch` 변수를 좁히는 꼴 · 들어오는 자리 여섯) · JS 32편 7절 **「다른 realm 의 오류는 `instanceof Error` 가 `false`」**

- ★★ [**39번 주제**](../39-strict-bundle/) 2절은 `catch (e) { e.message }` 가 `TS18046` 이라는 **「켜졌나」** 만 쟀다 — 여기는 그 `unknown` 을 **어떻게 읽나**(4절)와 **어디서는 안 켜지나**(5절 거절 사유).
- ★★ JS 갈래 [**32번**](../../../js/syntax/32-error-handling-and-error/) 7절 — `vm` 의 오류가 `instanceof Error` 에서 `false` 인 것이 **TS 의 좁히기 분기를 그대로 바꾼다**(4번의 `else`).

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"` · `node` · `"$NODE20"` | `7.0.2` · `5.9.3` · `4.9.5` · `v18.19.1` · `v20.19.6` |
| ★★★ 암시적 `any` 격자 | `bash ts42b-grid42.sh` — 36칸, 칸마다 디렉토리 | 켬/끔 갈린 칸 **`12 / 18`** · 두 판 갈린 탐침 **`0 / 9`** |
| ★★ 빈 배열 | `ia42f.ts` × 설정 셋 | `noImplicitAny` 만 끔 → `TS2345` |
| ★★★ `JSON.parse` | 셋 검사 · 둘 방출 · `node run42.cjs` | a 0줄 → `TypeError` · b `TS18046` · c `number 0.0` |
| ★★★ `catch` 좁히기 | 두 판 검사 · 방출 · node 18/20 | 검사 통과 · 5×4 표 · node 20 동일 |
| ★★ 거절 사유 | `bash ts42b-reason42.sh` — 켬/끔 × 세 판 | 서로 다른 답 **2가지** |
| ★ 가짜 격자 자기검사 | 가짜 옵션을 끼운 판 · 위쪽 `tsconfig.json` 판 | 두 스크립트 모두 **`exit 4` 로 멈췄다** |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **`JSON.parse`·거절 사유가 `any`** 인 것(3·5번) — **`lib` 선언**의 성질이다. 선언이 바뀌면 답이 바뀐다.
- ★★ **자라는 타입**(`ia42d`·`ia42f`)과 **빈 배열 `never[]`**(2번) — 추론 규칙이다. 두 판이 같았다.

**안 돌려 본 것**

- ★ **`Error.isError`** — JS 32편이 쟀다. 이 편은 던지지 않았다.
- ★ **검사 시간** · 실제 코드베이스의 진단 분포 — 재지 않았다.
