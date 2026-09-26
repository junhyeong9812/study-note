# ts/syntax/47 — 데코레이터 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **47 은 32 에서 온다** — [**32번 주제**](../32-class-type-aspects/) 5절이 필드 선언의 「정의 대 대입」을 쟀다.
> 「표준 데코레이터」는 **TS 5.0 이 구현한 판**(`experimentalDecorators` 없음)을 뜻한다 — JS 표준이라는 뜻이 아니다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1** · **v20.19.6** · Chrome **151**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`). 방출물은 `run47.cjs` 로 돈다(예외는 이름·메시지만 찍는다).
>
> 격자의 칸마다 앞에 붙는 파일:

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

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 자리 일곱 × 두 판 × 판 셋 (예측)

- 아래 격자에서 칸마다 `show` 가 받는 인자 수와 둘째 인자는 무엇인가? 진단과 방출 도우미는? 4.9.5 의 「표준」 줄은 무엇이 나는가?

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

### 2. 레거시 모양 둘을 두 판에 (예측)

- 아래를 `experimentalDecorators` 없이 / 있이 방출해 `node run47.cjs` 로 돌리면 각각 무엇이 찍히고 진단은 무엇인가?

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

### 3. 평가와 적용 (예측)

- 아래를 두 판으로 방출해 돌리면 `evaluate`·`apply` 줄은 어떤 순서로 나오는가?

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

### 4. 메타데이터 두 길 (예측)

- 첫 파일을 레거시 + `--emitDecoratorMetadata` 로, 둘째·셋째를 표준 판(`--lib es2022,esnext.decorators,dom`)으로 방출해 node 18 · 20 에서 돌리면 각각 무엇이 찍히는가?

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

### 5. 엔진 셋과 `-t esnext` (예측)

- 아래 `.js` 를 node 18 · 20 의 `--check` 로, 같은 문법을 Chrome 151 에서 간접 `eval` 로 던지면? 그리고 `.ts` 를 `-t esnext` 로 방출한 것을 `node --check` 하면?

```js
// nat47.js
function d(value, context) {
    return value;
}
@d
class A {}
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

### 6. 필드 초기화 세 설정 (예측)

- 아래를 `-t es2022` · `-t es2022 --useDefineForClassFields false` · `-t es2021` 로 방출해 돌리면 줄 순서와 `n` 은 설정마다 같은가?

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

### 7. 표준 판의 매개변수 자리 (왜)

- 표준 판으로 `m(@p x: number)` 를 방출하면 방출물과 `node` 출력에서 그 데코레이터는 어떻게 되나? 진단 창만 보고 멈추면 왜 부족한가?

### 8. 시그니처 검사가 보는 것 (왜)

- 2번의 두 데코레이터에 대해 TS 가 시그니처에서 검사하는 것은 무엇이고, 그것이 두 함수를 어떻게 가르나?

### 9. `reflect-metadata` 없이 (경계)

- 4번 첫 파일의 방출물에서 `__metadata` 도우미는 `Reflect.metadata` 가 없을 때 무엇을 하나? 그러면 라이브러리 없는 실패는 어디서 드러나나?

### 10. 세 층 (경계)

- 「데코레이터는 stage 3 이라 어느 ES 판에도 없다」를 이 문서는 무엇으로 뒷받침하고 무엇으로는 뒷받침하지 못하나?

### 11. 다른 갈래와 잇기 (연결)

- Python 의 `@` 와 Java·Kotlin 의 애너테이션 사이에서 TS 데코레이터는 어디에 서나? 레거시의 `emitDecoratorMetadata` 는 어느 쪽에 가까운가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
