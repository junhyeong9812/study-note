# ts/syntax/47 — 데코레이터 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 진단·방출·실행은 `tsc` **7.0.2** · node **18 · 20** · Chrome **151** 에서 실제로 얻었다. 판 비교는 **5.9.3 · 4.9.5** 를 환경변수(`TSC_OLD`·`TSC_49`)로 받아 **읽기만** 했다. 라이브러리는 설치하지 않았다.\
> 블록은 전부 **캡처 스크립트가 파일로 받은 것**이고 손으로 옮겨 적지 않았다 — 배너의 `(… exit=N)` 도 스크립트가 찍은 값이다.\
> ★★★ **세 층을 섞지 마라 — TS 구현 / TC39 제안 / 엔진.** 이 파일의 「표준」은 **TS 5.0 이 구현한 판**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 표준은 **인자 둘**(`value, context` — `kind` 가 자리를 말한다) · 레거시는 **셋**(클래스만 하나) — 갈린 칸 **`21 / 21`**, `node` 로그까지 **`14 / 21`** · 4.9.5 의 「표준」 줄은 **`TS1219` + 레거시 방출**

**출력**

```ts
// show47.ts
// 격자의 칸마다 앞에 붙는 데코레이터 -- 받은 인자를 그대로 적는다(두 판 어느 쪽 시그니처로도 불릴 수 있게 느슨하게)
function show(label: string) {
    return function (...args: any[]): any {
        const [a, b, c] = args;
        const second = typeof b === "object" && b !== null ? "kind=" + b.kind + " name=" + String(b.name) : "key=" + String(b);
        console.log(label, "args=" + args.length, "first=" + typeof a, second, "third=" + typeof c);
    };
}
```

```bash
# ts46b-grid47.sh
#!/usr/bin/env bash
# 데코레이터 두 판 격자 -- 자리 일곱 × (표준 · experimentalDecorators) × 판 셋
# 칸마다 파일 한 장 = show47.ts + 클래스 한 줄 + `new A();` · 칸마다 디렉토리를 따로 · -t es2022 로 방출해 node 로 돈다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"; V49="${TSC_49:?4.9.5 판을 TSC_49 로 준다}"
EXTRA=${EXTRA:-}   # 자기검사용
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
T=$'\x1f'   # 구분자는 US(0x1f) -- 규칙 32
rows=(
  "class${T}@show(\"class\") class A {}"
  "method${T}class A { @show(\"method\") m() {} }"
  "static${T}class A { @show(\"static\") static s() {} }"
  "field${T}class A { @show(\"field\") x = 1; }"
  "getter${T}class A { @show(\"getter\") get g() { return 1; } }"
  "accessor${T}class A { @show(\"accessor\") accessor y = 2; }"
  "param${T}class A { m(@show(\"param\") p: number) {} }"
)
run() { case $1 in 7.0.2) tsc "${@:2}" ;; 5.9.3) node "$OLD" "${@:2}" ;; 4.9.5) node "$V49" "${@:2}" ;; esac; }
helper() { grep -o '__esDecorate\|__decorate\|__param' "$1" | sort -u | tr '\n' ' ' | sed 's/ $//'; }
split_mode=0; split_log=0; split_ver=0; nm=0; nv=0; kinds=""
for r in "${rows[@]}"; do
  n=$(awk -F'\x1f' '{print NF}' <<< "$r"); if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $r"; exit 3; fi
  IFS="$T" read -r id cls <<< "$r"
  echo "[$id] $cls"
  declare -A got=()
  for mode in std legacy; do
    for v in 7.0.2 5.9.3 4.9.5; do
      d="$D/$id-$mode-$v"; mkdir -p "$d" || exit 3
      { cat show47.ts; echo "$cls"; echo "new A();"; } > "$d/c.ts" || exit 3
      if [ $mode = legacy ]; then fl=(--experimentalDecorators); else fl=(); fi
      raw=$(cd "$d" && run $v --pretty false -t es2022 "${fl[@]}" $EXTRA --outDir o c.ts 2>&1); rc=$?
      if grep -qE '^error TS' <<< "$raw"; then echo "★ 파일에 안 붙은 진단(설정 진단)이 칸에 들었다 -- 격자를 믿지 마라: $(grep -oE '^error TS[0-9]+' <<< "$raw" | sed 's/^error //' | sort -u | tr '\n' ' ')"; exit 4; fi
      codes=$(grep -o 'error TS[0-9]*' <<< "$raw" | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
      if [ -f "$d/o/c.js" ]; then h=$(helper "$d/o/c.js"); log=$(cd "$d" && node "$OLDPWD/run47.cjs" o/c.js 2>&1 | tr '\n' ';' | sed 's/;$//'); else h="(방출 없음)"; log="-"; fi
      got[$mode,$v]="${codes:-OK} | ${h:-(도우미 없음)} | ${log:-(로그 없음)}"; got[log,$mode,$v]="${log:-(로그 없음)}"
      kinds="$kinds${T}${h:-none}"
      printf '    %-6s %-6s tsc exit=%s  %s\n' "$mode" "$v" "$rc" "${got[$mode,$v]}"
    done
  done
  for v in 7.0.2 5.9.3 4.9.5; do nm=$((nm+1)); [ "${got[std,$v]}" != "${got[legacy,$v]}" ] && split_mode=$((split_mode+1)); [ "${got[log,std,$v]}" != "${got[log,legacy,$v]}" ] && split_log=$((split_log+1)); done
  for mode in std legacy; do nv=$((nv+1)); if [ "${got[$mode,7.0.2]}" != "${got[$mode,5.9.3]}" ] || [ "${got[$mode,7.0.2]}" != "${got[$mode,4.9.5]}" ]; then split_ver=$((split_ver+1)); fi; done
  unset got
done
k=$(tr "$T" '\n' <<< "$kinds" | sed '/^$/d' | sort -u | tr '\n' ' ' | sed 's/ $//')
case "$k" in *__esDecorate*__decorate*|*__decorate*__esDecorate*) ;; *) echo "★ 방출 도우미가 한 종류뿐이다($k) -- 모드 플래그가 안 먹은 격자, 멈춘다"; exit 5 ;; esac
echo
echo "표준과 레거시가 갈린 칸 $split_mode / $nm · 그중 node 로그까지 갈린 칸 $split_log / $nm · 한 판(모드)에서 세 판이 갈린 줄 $split_ver / $nv · 칸에 나온 방출 도우미 <$k>"
```

```text
===== bash ts46b-grid47.sh (sh exit=0) =====
[class] @show("class") class A {}
    std    7.0.2  tsc exit=0  OK | __esDecorate | class args=2 first=function kind=class name=A third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | class args=2 first=function kind=class name=A third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 7.0.2  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 5.9.3  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
    legacy 4.9.5  tsc exit=0  OK | __decorate | class args=1 first=function key=undefined third=undefined
[method] class A { @show("method") m() {} }
    std    7.0.2  tsc exit=0  OK | __esDecorate | method args=2 first=function kind=method name=m third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | method args=2 first=function kind=method name=m third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | method args=3 first=object key=m third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | method args=3 first=object key=m third=object
[static] class A { @show("static") static s() {} }
    std    7.0.2  tsc exit=0  OK | __esDecorate | static args=2 first=function kind=method name=s third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | static args=2 first=function kind=method name=s third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | static args=3 first=function key=s third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | static args=3 first=function key=s third=object
[field] class A { @show("field") x = 1; }
    std    7.0.2  tsc exit=0  OK | __esDecorate | field args=2 first=undefined kind=field name=x third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | field args=2 first=undefined kind=field name=x third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | field args=3 first=object key=x third=undefined
    legacy 7.0.2  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
    legacy 5.9.3  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
    legacy 4.9.5  tsc exit=0  OK | __decorate | field args=3 first=object key=x third=undefined
[getter] class A { @show("getter") get g() { return 1; } }
    std    7.0.2  tsc exit=0  OK | __esDecorate | getter args=2 first=function kind=getter name=g third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | getter args=2 first=function kind=getter name=g third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | getter args=3 first=object key=g third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | getter args=3 first=object key=g third=object
[accessor] class A { @show("accessor") accessor y = 2; }
    std    7.0.2  tsc exit=0  OK | __esDecorate | accessor args=2 first=object kind=accessor name=y third=undefined
    std    5.9.3  tsc exit=0  OK | __esDecorate | accessor args=2 first=object kind=accessor name=y third=undefined
    std    4.9.5  tsc exit=2  TS1219 | __decorate | accessor args=3 first=object key=y third=object
    legacy 7.0.2  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
    legacy 5.9.3  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
    legacy 4.9.5  tsc exit=0  OK | __decorate | accessor args=3 first=object key=y third=object
[param] class A { m(@show("param") p: number) {} }
    std    7.0.2  tsc exit=2  TS1206 | (도우미 없음) | (로그 없음)
    std    5.9.3  tsc exit=2  TS1206 | (도우미 없음) | (로그 없음)
    std    4.9.5  tsc exit=2  TS1219 | __decorate __param | param args=3 first=object key=m third=number
    legacy 7.0.2  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number
    legacy 5.9.3  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number
    legacy 4.9.5  tsc exit=0  OK | __decorate __param | param args=3 first=object key=m third=number

표준과 레거시가 갈린 칸 21 / 21 · 그중 node 로그까지 갈린 칸 14 / 21 · 한 판(모드)에서 세 판이 갈린 줄 7 / 14 · 칸에 나온 방출 도우미 <__decorate __decorate __param __esDecorate none>
```

**왜 그런가**

- ★★★ 4.9.5 에는 표준 판이 **없다** — 플래그를 빼도 `__decorate` 로 방출하고 「실험 기능」 진단 `TS1219` 만 더한다. 그래서 로그가 안 갈린 일곱 칸이 전부 4.9.5 다.
- ★★★ **매개변수** — 표준 판은 `TS1206` · 도우미 없음 · 로그 없음. 레거시는 `(prototype, "m", 0)`.
- ★★ 한 모드 안에서 세 판이 갈린 줄 `7 / 14` — 전부 표준 줄의 4.9.5 다.

### 2. ★★★ 표준 — `logKey got key: [object Object]` + `wrap` 에 **`TS1241`** 과 `TypeError` · 레거시 — `logKey got key: m` · `wrapped call: n` · `n() returned 1`

**출력**

```ts
// sig47.ts
// 레거시 모양 (target, key, descriptor) 으로 쓴 데코레이터 둘 -- 하나는 느슨하게, 하나는 타입을 다 적어서
function logKey(target: any, key?: any): void {
    console.log("logKey got key:", String(key));
}
function wrap(target: any, key: string, d: PropertyDescriptor): void {
    const orig = d.value;
    d.value = function (this: unknown, ...a: unknown[]) {
        console.log("wrapped call:", key);
        return orig.apply(this, a);
    };
}
class A {
    @logKey m() {}
}
class B {
    @wrap n() {
        return 1;
    }
}
console.log("n() returned", new B().n());
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 sig47.ts ; node run47.cjs e47/sig47.js ; 이어서 "$TSC_OLD" 방출물의 node 출력을 cmp (sh exit=0) =====
---- (표준)
sig47.ts(16,5): error TS1241: Unable to resolve signature of method decorator when called as an expression.
  The runtime will invoke the decorator with 2 arguments, but the decorator expects 3.
(tsc exit 2)
logKey got key: [object Object]
threw TypeError: Cannot read properties of undefined (reading 'value')
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
---- --experimentalDecorators
(tsc exit 0)
logKey got key: m
wrapped call: n
n() returned 1
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
```

**왜 그런가**

- ★★★ 표준 판은 `(value, context)` 두 인자로 부른다 — `key` 자리에 **`context` 객체**가 오고, `descriptor` 자리는 `undefined` 라 `d.value` 에서 `TypeError`.
- ★★ `TS1241` 이 붙어도 **방출은 된다**(tsc exit 2) — `run47.cjs` 가 그 방출물을 돌려 `TypeError` 를 받았다.

### 3. ★★★ 표준 — **식을 전부 먼저 평가**(c1 c2 m1 m2 f1 s1) → 적용 **s1 · m2 m1 · f1 · c2 c1** · 레거시 — **멤버마다 평가·적용**(m1 m2 → m2 m1 · f1 · s1) → 클래스 **c1 c2 → c2 c1**

**출력**

```ts
// ord47.ts
// 데코레이터 식이 언제 평가되고 언제 적용되나 -- 클래스 둘 · 메서드 둘 · 필드 · static
function tag(n: string) {
    console.log("evaluate", n);
    return function (...args: any[]): any {
        console.log("apply", n);
    };
}
@tag("c1") @tag("c2")
class A {
    @tag("m1") @tag("m2") m() {}
    @tag("f1") x = 1;
    @tag("s1") static s() {}
}
console.log("-- new A()");
new A();
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 ord47.ts ; node run47.cjs e47/ord47.js ; 이어서 "$TSC_OLD" 방출물의 node 출력을 cmp (sh exit=0) =====
---- (표준)
(tsc exit 0)
evaluate c1
evaluate c2
evaluate m1
evaluate m2
evaluate f1
evaluate s1
apply s1
apply m2
apply m1
apply f1
apply c2
apply c1
-- new A()
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
---- --experimentalDecorators
(tsc exit 0)
evaluate m1
evaluate m2
apply m2
apply m1
evaluate f1
apply f1
evaluate s1
apply s1
evaluate c1
evaluate c2
apply c2
apply c1
-- new A()
(node exit 0)
5.9.3 방출물의 node 출력: 한 글자도 같다
```

**왜 그런가**

- ★★★ 한 자리 안의 `@a @b` 는 두 판 모두 **평가 위→아래 · 적용 아래→위**다.
- ★★ 자리 사이는 판마다 다르다 — 표준은 `static` → 인스턴스 → 클래스, 레거시는 소스 순서(인스턴스 → `static`) 뒤 클래스.
- ★ 전부 `-- new A()` 앞에서 끝났다 — **클래스 정의 때** 돈다. 5.9.3 방출물도 한 글자 같다.

### 4. ★★★ 레거시 — 클래스 정의는 조용히 지나가고 **`Reflect.getMetadata is not a function`** · 표준(폴리필 없음) — `context.metadata` 가 **`undefined`** 라 **`TypeError`** · 폴리필 있음 — `{ greet: 'marked' }` · node 18 과 20 이 같다

**출력**

```ts
// meta47a.ts
// 레거시 + emitDecoratorMetadata -- 방출물이 무엇을 부르나, 그리고 읽으려 하면
function mark(...args: any[]): any {}
class Svc {
    @mark greet(name: string, n: number): boolean {
        return true;
    }
}
console.log("typeof Reflect.metadata:", typeof (Reflect as any).metadata);
console.log((Reflect as any).getMetadata("design:paramtypes", Svc.prototype, "greet"));
```

```text
===== tsc --pretty false -t es2022 --experimentalDecorators --emitDecoratorMetadata --outDir e47 meta47a.ts ; 방출물의 metadata 줄 ; node run47.cjs (sh exit=0) =====
(tsc exit 0)
===== 방출물에서 metadata 가 든 줄 =====
8:var __metadata = (this && this.__metadata) || function (k, v) {
9:    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
20:    __metadata("design:type", Function),
21:    __metadata("design:paramtypes", [String, Number]),
22:    __metadata("design:returntype", Boolean)
24:console.log("typeof Reflect.metadata:", typeof Reflect.metadata);
===== node =====
typeof Reflect.metadata: undefined
threw TypeError: Reflect.getMetadata is not a function
(node exit 0)
```

```ts
// meta47b.ts
// 표준 데코레이터의 context.metadata -- 폴리필 없이
function mark(_value: unknown, context: ClassMethodDecoratorContext) {
    console.log("typeof context.metadata:", typeof context.metadata);
    (context.metadata as any)[context.name] = "marked";
}
class Svc {
    @mark greet() {}
}
console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
console.log((Svc as any)[Symbol.metadata]);
```

```ts
// meta47c.ts
// 표준 데코레이터의 context.metadata -- 첫 줄에 Symbol.metadata 폴리필
(Symbol as any).metadata ??= Symbol("Symbol.metadata");
function mark(_value: unknown, context: ClassMethodDecoratorContext) {
    console.log("typeof context.metadata:", typeof context.metadata);
    (context.metadata as any)[context.name] = "marked";
}
class Svc {
    @mark greet() {}
}
console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
console.log((Svc as any)[Symbol.metadata]);
```

```text
===== tsc --pretty false -t es2022 --lib es2022,esnext.decorators,dom --outDir e47 <meta47b.ts · meta47c.ts 를 하나씩> ; node 18 · node 20 으로 node run47.cjs (sh exit=0) =====
(tsc meta47b exit 0)
(tsc meta47c exit 0)
===== meta47b 방출물에서 Symbol.metadata 가 든 줄 =====
46:            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
49:            if (_metadata) Object.defineProperty(this, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
57:console.log("typeof Symbol.metadata:", typeof Symbol.metadata);
58:console.log(Svc[Symbol.metadata]);
---- node v18.19.1 meta47b
typeof context.metadata: undefined
threw TypeError: Cannot set properties of undefined (setting 'greet')
(node exit 0)
---- node v18.19.1 meta47c
typeof context.metadata: object
typeof Symbol.metadata: symbol
[Object: null prototype] { greet: 'marked' }
(node exit 0)
---- node v20.19.6 meta47b
typeof context.metadata: undefined
threw TypeError: Cannot set properties of undefined (setting 'greet')
(node exit 0)
---- node v20.19.6 meta47c
typeof context.metadata: object
typeof Symbol.metadata: symbol
[Object: null prototype] { greet: 'marked' }
(node exit 0)
```

**왜 그런가**

- ★★★ 레거시는 **컴파일러가 타입을 값으로** 적는다(`[String, Number]` · `Boolean`) — 그러나 `Reflect.metadata` 가 있을 때만 부른다.
- ★★★ 표준 방출물은 `Symbol.metadata` 가 **있을 때만** 메타데이터 객체를 만든다 — node 18 · 20 에 그 심볼이 없다.

### 5. ★★★ 셋 다 **`SyntaxError: Invalid or unexpected token`** · `-t esnext` 방출물은 **`@d` 를 그대로 남겨** `node --check` 가 같은 `SyntaxError`(7.0.2 · 5.9.3)

**출력**

```js
// nat47.js
function d(value, context) {
    return value;
}
@d
class A {}
```

```bash
# ts46b-native47.sh
#!/usr/bin/env bash
# 엔진이 @ 문법을 파싱하나 -- node 18 · node 20 의 --check (스택 줄은 빼고 첫 두 줄만 -- 전부 받은 뒤 거른다, 규칙 19-A)
set -u -o pipefail
N20="${NODE20:?node 20 의 경로를 NODE20 으로 준다}"
for n in node "$N20"; do
  out=$("$n" --check nat47.js 2>&1); rc=$?
  echo "---- node $("$n" --version) --check nat47.js (exit $rc)"
  sed -n '1,/Error/p' <<< "$out" | sed "s|^$PWD/||" | sed -n '1p;/Error/p'
done
```

```text
===== bash ts46b-native47.sh (sh exit=0) =====
---- node v18.19.1 --check nat47.js (exit 1)
nat47.js:4
SyntaxError: Invalid or unexpected token
---- node v20.19.6 --check nat47.js (exit 1)
nat47.js:4
SyntaxError: Invalid or unexpected token
```

```html
<!-- c47.html -->
<!doctype html>
<meta charset="utf-8">
<pre id="o"></pre>
<script>
  // 엔진이 @ 문법을 파싱하나 -- 문자열을 간접 eval 로 던져 예외 이름·메시지를 적는다
  const cases = [
    ["class decorator", "function d(v, c) { return v; }\n@d\nclass A {}"],
    ["method decorator", "function d(v, c) { return v; }\nclass B { @d m() {} }"],
    ["no decorator", "class C {}"],
    ["typeof Symbol.metadata", "typeof Symbol.metadata"],
  ];
  const out = [];
  for (const [label, src] of cases) {
    try {
      out.push(label + " — ok " + String((0, eval)(src)));
    } catch (e) {
      out.push(label + " — " + e.name + ": " + e.message);
    }
  }
  document.getElementById("o").textContent = out.join("\n");
</script>
```

```text
===== google-chrome --headless=new --disable-gpu --no-sandbox --dump-dom file://…/c47.html 의 <pre> 안 (sh exit=0) =====
class decorator — SyntaxError: Invalid or unexpected token
method decorator — SyntaxError: Invalid or unexpected token
no decorator — ok undefined
typeof Symbol.metadata — ok undefined
```

```ts
// nat47.ts
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value: unknown, context: ClassDecoratorContext) {
    console.log("decorated", String(context.name));
}
@d
class A {}
```

```text
===== tsc · "$TSC_OLD" --pretty false <-t es2022 · -t esnext> --outDir e47 nat47.ts ; esnext 방출물 ; node --check (sh exit=0) =====
---- 7.0.2 -t es2022 (tsc exit 0) 방출물 56줄 · __esDecorate 2곳
node --check exit 0: (진단 없음)
---- 7.0.2 -t esnext (tsc exit 0) 방출물 8줄 · __esDecorate 0곳
"use strict";
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value, context) {
    console.log("decorated", String(context.name));
}
@d
class A {
}
node --check exit 1: SyntaxError: Invalid or unexpected token
---- 5.9.3 -t es2022 (tsc exit 0) 방출물 55줄 · __esDecorate 2곳
node --check exit 0: (진단 없음)
---- 5.9.3 -t esnext (tsc exit 0) 방출물 7줄 · __esDecorate 0곳
// 표준 클래스 데코레이터 하나 -- target 에 따라 방출이 어떻게 달라지나
function d(value, context) {
    console.log("decorated", String(context.name));
}
@d
class A {
}
node --check exit 1: SyntaxError: Invalid or unexpected token
```

**왜 그런가**

- ★★★ 엔진 셋이 `@` 를 **토큰으로도** 모른다 — 데코레이터 없는 클래스는 통과한다.
- ★★ TS 는 `esnext` 를 「최신 제안까지 아는 엔진」으로 가정해 풀어 쓰지 않는다. `es2022` 면 `__esDecorate` 로 풀어 **55\~56줄**이 되고 `--check` 를 통과한다.

### 6. ★★ **세 설정 모두 같다** — 인스턴스마다 `field initializer got 4` → `addInitializer ran for n` → `constructor body sees 40` · `n = 40`

**출력**

```ts
// init47.ts
// 표준 필드 데코레이터 -- 초기값을 바꾸는 함수를 돌려주고 addInitializer 를 건다
function times10(_value: undefined, context: ClassFieldDecoratorContext<P, number>) {
    context.addInitializer(function () {
        console.log("addInitializer ran for", String(context.name));
    });
    return function (this: P, initial: number) {
        console.log("field initializer got", initial);
        return initial * 10;
    };
}
class P {
    @times10 n = 4;
    constructor() {
        console.log("constructor body sees", this.n);
    }
}
console.log("-- first");
new P();
console.log("-- second");
console.log("n =", new P().n);
```

```text
===== tsc --pretty false <-t es2022 · -t es2022 --useDefineForClassFields false · -t es2021> --outDir e47 init47.ts ; node run47.cjs (sh exit=0) =====
---- -t es2022
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
---- -t es2022 --useDefineForClassFields false
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
---- -t es2021
(tsc exit 0)
-- first
field initializer got 4
addInitializer ran for n
constructor body sees 40
-- second
field initializer got 4
addInitializer ran for n
constructor body sees 40
n = 40
(node exit 0)
```

**왜 그런가**

- ★★ 필드 데코레이터가 돌려준 함수가 **초기값 변환기**다 — 인스턴스를 만들 때마다 돈다.
- ★ 이 탐침은 필드가 정의냐 대입이냐([32번 주제](../32-class-type-aspects/) 5절)를 **드러내지 않는다** — 부모 접근자와 겹치는 자리는 재지 않았다.

### 7. ★★★ 방출물에서 **사라진다** — `__param` 0줄 · `node` 는 아무것도 안 찍는다 · 진단 창은 `TS1206` 을 말하지만 **방출을 막지 않으므로**, 방출물(`__param` 줄 수)과 `node` 로그로 **창을 바꿔** 확인했다

```ts
// param47.ts
// 매개변수 자리의 데코레이터 하나
function p(...args: any[]): any {
    console.log("param decorator args", args.length, String(args[1]), args[2]);
}
class A {
    m(@p x: number) {}
}
new A();
```

```text
===== tsc --pretty false -t es2022 [--experimentalDecorators] --outDir e47 param47.ts ; __param 줄 수 ; node run47.cjs (sh exit=0) =====
---- (표준)
param47.ts(6,7): error TS1206: Decorators are not valid here.
(tsc exit 2)
방출물의 __param 줄: 0
(node exit 0)
---- --experimentalDecorators
(tsc exit 0)
방출물의 __param 줄: 1
param decorator args 3 m 0
(node exit 0)
```

- ★★ `noEmitOnError` 가 없으면 **데코레이터가 빠진 코드가 배포된다** — [02번 주제](../02-type-checking-vs-emit/).

### 8. ★★★ 「**그 인자 수·타입으로 불릴 수 있나**」 만 본다 — `logKey(target: any, key?: any)` 는 두 인자로도 불릴 수 있어 통과, `wrap(…, key: string, d: PropertyDescriptor)` 는 셋째가 필수라 `TS1241`

- ★★ 통과한 쪽이 더 위험하다 — **진단 0 에 틀린 값**(`[object Object]`)이다. 두 판 모두에서 쓰려는 「범용」 데코레이터를 `any` 로 쓰면 이렇게 된다.

### 9. ★★ `if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);` — 없으면 **아무것도 안 한다** · 실패는 **읽는 쪽**(`Reflect.getMetadata(…)`)으로 밀린다

- ★ 그래서 `reflect-metadata` 를 들여와야 하는 것은 **메타데이터를 읽는 라이브러리**다. 정의하는 쪽은 조용하다.

### 10. ★★ 뒷받침하는 것 — **엔진 셋(node 18 · 20 · Chrome 151)이 `@` 를 파싱하지 못한다**(5번) · 뒷받침하지 못하는 것 — **「stage 3」이라는 단계 자체**(TC39 문서 — 출처 확인 못 함)와 **다른 엔진·다음 판**

- ★★ 「이 엔진들이 모른다」는 「어느 ES 판에도 없다」와 **맞아떨어지지만 같은 말이 아니다.** 제안 단계는 제안 문서가, 엔진 지원은 실행이 말한다.

### 11. ★★ **둘 사이** — Python 처럼 **함수가 정의 때 불려 값을 바꿔 치우지만**, Python 과 달리 **엔진이 문법을 모르고 TS 가 풀어 써야** 돈다 · `emitDecoratorMetadata` 는 **애너테이션 쪽** — 코드를 안 바꾸고 타입 정보를 남겨 **읽는 쪽이 뜻을 준다**

- Python 갈래 [**24번**](../../../python/syntax/24-decorators/) · Java 갈래 [**16번**](../../../java/syntax/16-annotations/) · Kotlin 갈래 [**35번**](../../../kotlin/syntax/35-annotations-and-use-site-targets/).

## 실행 검증

| 무엇 | 어떻게 | 결과 |
|---|---|---|
| 판 | `tsc --version` · `"$TSC_OLD"`·`"$TSC_49"` · `node` · `"$NODE20"` · `google-chrome --version` | `7.0.2` · `5.9.3` · `4.9.5` · `v18.19.1` · `v20.19.6` · `151.0.7922.173` |
| ★★★ 두 판 격자 | `bash ts46b-grid47.sh` — 7 × 2 × 3 | 갈린 칸 **`21 / 21`** · 로그까지 **`14 / 21`** · 세 판이 갈린 줄 **`7 / 14`** |
| ★ 자기검사 | `EXTRA=--bogusOpt` · `EXTRA=--experimentalDecorators` | **`exit 4`** · **`exit 5`** |
| ★★★ 시그니처 · 순서 | `sig47.ts` · `ord47.ts` × 두 판 | 5.9.3 방출물과 `node` 출력 동일 |
| ★★ 메타데이터 | `meta47a/b/c.ts` × node 18 · 20 | 두 node 같음 |
| ★★★ 엔진 | `node --check` 둘 · Chrome 151 | 셋 다 `SyntaxError` |

**구현 의존 항목 — 판이 오르면 다시 돌릴 것**

- ★★★ **엔진의 `@` 파싱 · `Symbol.metadata`**(4·5번) — 엔진이 제안을 구현하면 여기가 먼저 바뀐다.
- ★★ **`-t esnext` 방출이 `@` 를 남기는 것**(5번) — TS 의 가정이다.
- ★ **4.9.5 의 `TS1219`**(1번) — 4.x 판의 성질이다.

**안 돌려 본 것**

- ★★ **TC39 의 현재 단계** — 출처를 확인하지 못했다(외부 네트워크 금지).
- ★ 부모 접근자와 겹치는 필드 데코레이터 · `-t es2015` 이하의 방출 · `private` 멤버 데코레이터.
