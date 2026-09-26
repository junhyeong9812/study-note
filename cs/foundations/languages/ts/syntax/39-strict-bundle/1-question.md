# ts/syntax/39 — `strict` 묶음 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **39 는 02 에서 온다** — [**02번 주제**](../02-type-checking-vs-emit/)가 7.0 의 기본값 변화를 머리말에 적었다.
> 여기서는 `strict` 한 줄이 **무엇을 켜고, 판마다 그 기본값이 어떻게 다른지**를 탐침으로 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 설정 실험은 **칸마다 디렉토리와 `tsconfig.json` 을 따로** 만들어 `-p` 로 던졌다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. `--showConfig` 세 판 (예측)

```bash
# ts38b-show39.sh
#!/usr/bin/env bash
# "strict": true 한 줄짜리 tsconfig.json 을 판 셋의 --showConfig 에 준다 -- 펼쳐 적은 키를 본다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
V49="${TSC_49:?4.9.5 판 tsc 의 경로를 TSC_49 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
echo 'export const a = 1;' > "$D/a39.ts"
keys() { node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{console.log(Object.keys(JSON.parse(s).compilerOptions).join(" "))})'; }
for s in true false; do
  printf '{ "compilerOptions": { "strict": %s }, "files": ["a39.ts"] }\n' "$s" > "$D/tsconfig.json"
  echo "---- \"strict\": $s"
  for v in 7 5 4; do
    case $v in 7) vn=7.0.2; c=(tsc) ;; 5) vn=5.9.3; c=(node "$OLD") ;; 4) vn=4.9.5; c=(node "$V49") ;; esac
    out=$(cd "$D" && "${c[@]}" --showConfig -p tsconfig.json); rc=$?
    echo "$vn (exit $rc) -- $(keys <<< "$out")"
  done
done
```

- 세 판은 `"strict": true` 를 각각 어떤 키들로 돌려주는가? `"strict": false` 는?

### 2. 탐침 아홉과 「키 없음」 (예측)

```ts
// pr39a.ts
function f(x) { return x; }
export {};
```

```ts
// pr39b.ts
function g() { return this.x; }
export {};
```

```ts
// pr39c.ts
let s: string = null;
export {};
```

```ts
// pr39d.ts
let h: (x: string | number) => void = (x: string) => {};
export {};
```

```ts
// pr39e.ts
function k(a: number) {}
k.call(undefined, "x");
export {};
```

```ts
// pr39f.ts
class C { p: number; }
export {};
```

```ts
// pr39g.ts
const r = [1].values().next();
if (r.done) { const v: number = r.value; }
export {};
```

```ts
// pr39h.ts
try {} catch (e) { e.message; }
export {};
```

```ts
// pr39i.ts
var package = 1;
```

- 탐침마다 **하위 플래그 하나**에만 걸리게 썼다. 각각 어느 플래그이고, `"strict": true` 에서 어느 코드를 내는가?
- 칸마다 `{ "compilerOptions": { "target": "es2022", "noEmit": true }, "files": [탐침] }` — **`strict` 키가 없는** 설정으로 던지면 7.0.2 · 5.9.3 · 4.9.5 는 각각 몇 탐침에서 진단을 내는가?

### 3. `"strict": false` 와 「`true` + 하위 하나만 `false`」 (예측)

- 2번의 탐침 아홉을 `"strict": false` 로, 그리고 `"strict": true` + **그 탐침의 하위 플래그 하나만 `false`** 로 7.0.2 에 던지면 칸마다 무엇이 나는가? 4.9.5 에서 달라지는 칸은?

### 4. 설정 없이 두 판 (예측)

- `tsconfig.json` 이 위쪽 어디에도 없는 디렉토리에서 `tsc --pretty false --noEmit pr39c.ts pr39i.ts` 를 7.0.2 와 5.9.3 으로 던지면 각각 무엇이 나고 종료 코드는 몇인가?

### 5. `pr39i.ts` 를 방출하면 (예측)

- `--strict false` 로 `pr39i.ts` 를 7.0.2 와 5.9.3 에서 방출하면 진단과 방출물 첫 줄은 각각 무엇인가? 7.0.2 에 `--alwaysStrict false` 를 주면?

### 6. 옛 코드 한 장에 하나씩 켜기 (예측)

```ts
// legacy39.ts
// strict 없이 자란 코드를 흉내 낸 한 장
function sum(xs) {
    let t = 0;
    for (const x of xs) t += x;
    return t;
}
function format(prefix, value) {
    return prefix + ": " + value;
}
function describe() {
    return this.name + " (" + this.age + ")";
}
let current: string = null;
let pending: number = undefined;
const handlers: { [k: string]: (e: string | number) => void } = {};
handlers.click = (e: string) => console.log(e.length);
function pad(n: number, width: number) {
    return String(n).padStart(width, "0");
}
pad.call(undefined, "7", 3);
pad.apply(undefined, [7]);
class Account {
    id: number;
    owner: string;
    balance = 0;
}
const it = new Set([1, 2]).values();
const step = it.next();
if (step.done) {
    const last: number = step.value;
}
try {
    JSON.parse("{");
} catch (err) {
    console.log(err.message);
}
export { sum, format, describe, current, pending, Account };
```

- `"strict": false` 를 바닥으로 두고 하위 플래그를 **하나씩만** 켜서 새 진단을 센다. 어느 플래그가 **혼자서는** 제대로 안 켜지거나 진단을 못 내는가? 하나씩 켠 수의 합과 `"strict": true` 로 한 번에 켠 수는 같은가?

### 7. 도움말의 기본값 문구 (왜)

- 「`strict` 가 무엇을 켜나」는 `tsc --help --all` 의 기본값 문구로도 물을 수 있다. 그 문구를 결론의 근거로 쓰지 않고 2번 같은 탐침으로 다시 확인하는 까닭은 무엇인가? 4.9.5 의 `useUnknownInCatchVariables` 로 답하라.

### 8. 레퍼런스의 Enables 목록 (경계)

- TSConfig 레퍼런스는 `strict` 가 켜는 것으로 **아홉**을 적는다. 7.0.2 에서 `strict` 로 **끄고 켤 수 있는** 것도 아홉인가? 3·5번으로 답하라.

### 9. 켜는 순서의 축 (왜)

- 6번 결과로 기존 코드베이스에 하위 플래그를 켜는 순서를 짠다면 무엇을 축으로 두는가? 「진단이 적은 것부터」만으로 정하면 어디서 막히는가?

### 10. 02·35 와 잇기 (연결)

- 4번의 결과는 02편 머리말의 어느 문장을 설정 없는 칸에서 다시 확인한 것인가?
- 5번의 `TS5108` 은 02편 7절의 어느 코드와 같은 집안인가?
- 2번이 칸마다 디렉토리를 따로 만든 까닭은 35편 6절의 어느 진단 때문인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
