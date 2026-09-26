# ts/syntax/43 — `tsconfig` 의 나머지 선택 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★ **43 은 39 에서 온다** — [**39번 주제**](../39-strict-bundle/)가 7.0 에서 바뀐 **검사** 기본값을 쟀다. 여기는 **출력** 쪽 다이얼(`target`·`module`·`incremental`)이다.
> `lib`·`module`·`isolatedModules`·`skipLibCheck`·`useDefineForClassFields` 의 격자는 형제 편(38·35·36·37·32)이 쟀다 — 9·10번이 그것을 잇는다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 5.9.3 · 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_OLD`·`TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 옛 값 열 행 × 세 판 (예측)

```ts
// z43.ts
export const z = 1;
```

- `tsconfig.json` 이 없는 디렉토리에서 `tsc --pretty false --noEmit <플래그> z43.ts` 를 4.9.5 · 5.9.3 · 7.0.2 에 던진다. 플래그는 `--target es5` · `--target es3` · `--target es2015 --downlevelIteration` · `--module amd` · `--module umd` · `--module system` · `--module none` · `--module commonjs --moduleResolution node10` · `--module system --outFile out.js` · 대조 `--target es2015`. 칸마다 무엇이 나는가?
- README 의 「7.0 에서 `es5`·`downlevelIteration`·AMD/UMD 계열은 불가」는 맞는가?

### 2. 문법 여섯 × `target` 넷 (예측)

```ts
// oc43.ts
export const f = (o?: { a: number }) => o?.a;
```

```ts
// nc43.ts
export const f = (x: number | null) => x ?? 0;
```

```ts
// cf43.ts
export class C {
    x = 1;
}
```

```ts
// as43.ts
export async function f() {
    await 1;
}
```

```ts
// gen43.ts
export function* g() {
    yield 1;
}
```

```ts
// fo43.ts
export function s(xs: number[]) {
    let t = 0;
    for (const x of xs) t += x;
    return t;
}
```

- 여섯을 `-t es2015` · `es2020` · `es2022` · `esnext` 로 방출하면 원래 문법이 방출물에 **남는** 칸과 **내려 쓰인** 칸은 각각 어디인가? 7.0.2 와 5.9.3 이 다른 칸이 있는가?

### 3. `target` 없이 두 판 (예측)

```ts
// ud43.ts
// target 을 적지 않은 채 방출한다 -- 필드 한 줄이 부모 setter 를 부르나
class Parent {
    set x(v: number) {
        console.log("  Parent setter got", v);
    }
    get x() {
        return -1;
    }
}
class Child extends Parent {
    x = 1;
}
const c = new Child();
console.log("  own keys", JSON.stringify(Object.keys(c)), "x", c.x);
```

- `target` 을 주지 않고 7.0.2 와 5.9.3 으로 방출해 `node` 로 돌리면 각각 무엇이 찍히는가? 두 판의 진단은 같은가?

### 4. `incremental` 다섯 단계 (예측)

```bash
# ts42b-inc43.sh
#!/usr/bin/env bash
# incremental 두 설정(declaration 끔/켬) × 판 둘 -- 단계마다 다시 방출한 .js 를 --listEmittedFiles 로 센다
# 파일 셋: a.ts(값 하나) · b.ts(a 를 import) · c.ts(아무도 안 본다) -- 시간은 찍지 않는다
set -u -o pipefail
OLD="${TSC_OLD:?5.9.3 판 tsc 의 경로를 TSC_OLD 로 준다}"
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
steps=("1 처음" "2 안 바꿈" "3 c.ts 값만" "4 a.ts 값만(타입 같음)" "5 a.ts 타입까지")
build() {   # build <판> <declaration>
  local c; if [ "$1" = 7.0.2 ]; then c=(tsc); else c=(node "$OLD"); fi
  (cd "$D/w" && "${c[@]}" --pretty false -p tsconfig.json --declaration "$2" --listEmittedFiles) > "$D/out" 2>&1
  local rc=$?
  emitted=$(grep -o 'dist/[a-z]*\.js$' "$D/out" | sed 's|^dist/||' | tr '\n' ' ' | sed 's/ $//')
  info=$(grep -c '\.tsbuildinfo$' "$D/out")
  if grep -q 'error' "$D/out"; then echo "★ 진단이 나왔다: $(cat "$D/out")"; exit 4; fi
  echo "exit $rc · 다시 방출한 .js [${emitted:-없음}] · .tsbuildinfo 를 썼나 $info"
}
for decl in false true; do
  for v in 7.0.2 5.9.3; do
    rm -rf "$D/w"; mkdir -p "$D/w/src"
    echo '{ "compilerOptions": { "incremental": true, "target": "es2022", "outDir": "dist", "rootDir": "src", "tsBuildInfoFile": "dist/.tsbuildinfo" }, "include": ["src"] }' > "$D/w/tsconfig.json"
    echo 'export const a: number = 1;' > "$D/w/src/a.ts"
    echo 'import { a } from "./a"; export const b = a + 1;' > "$D/w/src/b.ts"
    echo 'export const c = 3;' > "$D/w/src/c.ts"
    echo "---- $v · declaration $decl"
    for s in "${steps[@]}"; do
      case ${s%% *} in
        3) echo 'export const c = 4;' > "$D/w/src/c.ts" ;;
        4) echo 'export const a: number = 2;' > "$D/w/src/a.ts" ;;
        5) echo 'export const a = 2;' > "$D/w/src/a.ts" ;;
      esac
      printf '  %-22s ' "${s#* }"; build "$v" "$decl"
    done
  done
done
```

- 단계마다 다시 방출하는 `.js` 는 무엇인가? `declaration` 을 켠 판과 끈 판이 갈리는 단계는 어디인가?

### 5. `es3` 와 `es5` (경계)

- 7.0.2 에서 `--target es3` 와 `--target es5` 는 다른 진단 코드를 낸다. 각각 무엇이고, 그 차이는 무엇을 말하는가? 5.9.3 의 `es3` 는?

### 6. `module amd` 에 붙는 진단 하나 더 (왜)

- 7.0.2 에서 `--module amd` 만 줬는데 `TS5108` 말고 `TS5095` 가 같이 나는 까닭은 무엇인가?

### 7. 7.0 이 없앤 방출 두 가지 (경계)

- 5.9.3 에서 `fo43.ts` 를 `-t es5` 로, 그리고 `-t es5 --downlevelIteration` 으로 방출하면 `for…of` 가 각각 어떤 모양이 되는가? 7.0.2 에서는 그 둘이 어떻게 되는가?

### 8. 시간을 재지 않은 판별 (왜)

- 4번은 「두 번째 빌드가 무엇을 건너뛰나」를 시간이 아니라 무엇으로 판별했는가? 그 창이 **못 보는** 것은 무엇인가?

### 9. 인용표의 두 칸 (연결)

- `skipLibCheck` 는 37편 6절에서 무엇을 숨겼는가? 「`skipLibCheck` 가 빌드를 빠르게 한다」는 이 묶음 어디서 쟀는가?
- `lib` 를 하나만 적으면 기본 목록이 어떻게 되는가(38편 3절)?

### 10. 3번과 32편 5절 (연결)

- 32편 5절은 `useDefineForClassFields` 를 어떤 판들로 쟀는가? 3번은 그 격자에 어떤 칸 하나를 더한 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
