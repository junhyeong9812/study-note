# ts/syntax/30 — 타입 단언과 non-null `!` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **30 은 29 의 짝이다** — [**29번 주제**](../29-satisfies/)가 `as` 의 절반(빠진 키·더한 키 통과 · 겹칠 수 없는 값만 `TS2352` · `{} as User` 가 진단 0줄에 런타임 `TypeError`)을 이미 쟀다.
> 여기서는 **`as unknown as` · `!` · 단언 함수 · 타입 가드를 한 격자에 놓고**, 「방출물에 무엇이 남나」로 가른다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — `!`(non-null 단언)은 **2.0**, 확정 할당 단언 `let x!: T` 는 **2.7**, 단언 함수 `asserts` 는 **3.7** 이다. **7.0 에서 도는지는 던져서 확인했다.**
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 격자가 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. undefined 가 올 수 있는 값을 아홉 가지로 쓰면 (예측)

```bash
# ts30b-bypass.sh
#!/usr/bin/env bash
# 같은 값(undefined 가 올 수 있는 got)을 User 로 쓰는 일곱 가지 꼴 -- 칸마다 파일 하나씩
# 칸마다 세 가지를 묻는다: 컴파일 진단 · 방출된 줄이 소스 줄과 같나 · node 실행 결과
set -u -o pipefail
D=$(mktemp -d "$PWD/.grid.XXXXXX"); trap 'rm -rf "$D"' EXIT
prelude='interface User {
    name: string;
}
function find(id: number): User | undefined {
    return id === 1 ? { name: "kim" } : undefined;
}
function isUser(v: unknown): v is User {
    return typeof v === "object" && v !== null && "name" in v && typeof v.name === "string";
}
function assertUser(v: unknown): asserts v is User {
    if (!isUser(v)) throw new Error("assertUser failed");
}
const got = find(2);
const num = 42;'
T=$'\t'   # 구분자는 탭 -- 행 안에 ; 가 나오므로 ; 는 못 쓴다(규칙 32)
rows=(
  "plain${T}"'const out = got.name.toUpperCase();'
  "as${T}"'const out = (got as User).name.toUpperCase();'
  "angle${T}"'const out = (<User>got).name.toUpperCase();'
  "bang${T}"'const out = got!.name.toUpperCase();'
  "unk${T}"'const out = (got as unknown as User).name.toUpperCase();'
  "asserts${T}"'assertUser(got); const out = got.name.toUpperCase();'
  "guard${T}"'const out = isUser(got) ? got.name.toUpperCase() : "(else branch)";'
  "num-as${T}"'const out = (num as User).name.toUpperCase();'
  "num-unk${T}"'const out = (num as unknown as User).name.toUpperCase();'
)
changed=0; total=0; threw=0
for row in "${rows[@]}"; do
  IFS="$T" read -r label use <<< "$row"
  n=$(awk -F'\t' '{print NF}' <<< "$row")
  if [ "$n" -ne 2 ]; then echo "칸 수 $n ≠ 2: $row"; exit 3; fi
  { echo "$prelude"; echo "try {"; echo "    $use"; echo '    console.log("ok", out);'
    echo "} catch (e) {"; echo '    console.log((e as Error).constructor.name, (e as Error).message);'; echo "}"; } > "$D/c.ts"
  diag=$(tsc --pretty false --noEmit -t es2022 --strict "$D/c.ts" 2>&1 | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
  rm -rf "$D/o"; tsc --pretty false -t es2022 --strict --outDir "$D/o" "$D/c.ts" > /dev/null 2>&1
  emitted=$(sed -n '/^try {/,/console.log("ok"/p' "$D/o/c.js" | sed '1d;$d' | sed 's/^ *//' | tr '\n' ' ' | sed 's/ $//')
  if [ "$emitted" = "$use" ]; then same='같다'; else same='★ 바뀌었다'; changed=$((changed+1)); fi
  run=$(node "$D/o/c.js" 2>&1)
  case $run in ok\ *) ;; *) threw=$((threw+1)) ;; esac
  total=$((total+1))
  printf '[%s] %s\n' "$label" "$use"
  printf '    진단   %s\n' "${diag:-OK}"
  printf '    방출   %s   (%s)\n' "$emitted" "$same"
  printf '    node   %s\n' "$run"
done
echo
echo "방출된 줄이 소스 줄과 달라진 칸 $changed / $total"
echo "node 에서 예외로 끝난 칸 $threw / $total"
```

- 아홉 행 각각의 **진단** 칸은 무엇인가? `OK` 가 아닌 행은 어느 것인가?
- **방출** 칸에서 소스 줄과 **같게 남는** 행은 어느 것인가?
- **node** 칸에서 예외로 끝나지 **않는** 행은 어느 것이고, `[asserts]` 행의 예외는 `[bang]` 행의 예외와 **종류가 같은가**?
- 마지막 두 줄의 수는 각각 몇 / 몇인가?

### 2. `!` 를 붙인 값을 다른 곳으로 넘기면 (예측)

```ts
// ex.30a.ts
// ! 를 붙인 값이 곧바로 쓰이지 않고 다른 곳으로 흘러가면
interface User {
    name: string;
}
const table = new Map<number, User>([[1, { name: "kim" }]]);

const u = table.get(2)!;
const list: User[] = [u];
console.log("[1] list.length", list.length);
console.log("[2] typeof list[0]", typeof list[0]);
const copy = { ...list[0] };
console.log("[3] copy", JSON.stringify(copy));
try {
    console.log("[4]", list[0].name.length);
} catch (e) {
    console.log("[4]", (e as Error).constructor.name, (e as Error).message);
}
```

- `tsc --noEmit` 은 몇 줄의 진단을 내는가?
- 소스 7행(`const u = …`)은 방출된 `.js` 에서 어떻게 되는가?
- `node` 로 돌리면 `[1]`\~`[4]` 가 각각 무엇을 찍는가? **처음으로 예외가 나는 줄**은 어디인가?

### 3. 선언 쪽의 `!` (예측)

```ts
// ex.30b.ts
// 선언 쪽의 ! -- 확정 할당 단언
let plain: number;
let banged!: number;
console.log(plain + 1, banged + 1);

class NoInit {
    count: number;
}
class BangInit {
    count!: number;
}
console.log(new NoInit().count, new BangInit().count);
```

- 진단이 나는 줄은 어디이고, 코드는 무엇인가? `!` 를 붙인 두 선언은?
- 진단이 있어도 방출은 되는가? 그 방출물에서 `banged!` 와 `count!` 는 어떻게 되는가?
- `node` 의 두 줄은 무엇인가?

### 4. 단언을 쓴 세 자리 — 입력이 바뀌면 (예측)

```ts
// ex.30c.ts
// 단언을 쓴 세 자리 -- 같은 코드가 입력만 바뀌면
interface Config {
    host: string;
    port: number;
}
interface Repo {
    load(id: number): string;
    save(v: string): void;
}
function readConfig(text: string): Config {
    return JSON.parse(text) as Config;
}
function portOf(ports: Map<string, number>, key: string): number {
    return ports.get(key)!;
}
const fakeRepo = { load: (id: number) => "row" + id } as unknown as Repo;

const tries: [string, () => unknown][] = [
    ["readConfig full   ", () => readConfig('{"host":"a","port":1}').host.length],
    ["readConfig partial", () => readConfig('{"port":1}').host.length],
    ["portOf present    ", () => portOf(new Map([["web", 80]]), "web") + 1],
    ["portOf missing    ", () => portOf(new Map([["web", 80]]), "db") + 1],
    ["fakeRepo.load     ", () => fakeRepo.load(7)],
    ["fakeRepo.save     ", () => fakeRepo.save("x")],
];
for (const [label, f] of tries) {
    try {
        console.log(label, "->", f());
    } catch (e) {
        console.log(label, "->", (e as Error).constructor.name, (e as Error).message);
    }
}
```

- 컴파일러는 이 파일에 무엇이라고 하는가?
- 여섯 줄 중 **예외 없이 틀린 값**을 내는 줄은 어느 것인가?

### 5. `as unknown as` 가 넘는 것 (왜)

- 1번의 `[num-as]` 와 `[num-unk]` 의 진단 칸을 견주면 — 두 번 단언하면 **무엇이** 통과되는가? `unknown` 을 가운데 끼우는 것이 왜 통하는가?

### 6. `!` 와 Kotlin `!!` (왜)

- Kotlin 의 `!!` 는 null 이면 그 자리에서 NPE 를 던진다. TS 의 `!` 는 2번에서 **어디서** 터졌는가? 두 기호가 다른 이유를 **방출물**로 설명할 수 있는가?

### 7. 단언 함수의 방출 (왜)

- 1번에서 `[asserts]` 행의 방출 칸을 `as`·`!` 행과 견주고, 그 결과를 설명할 수 있는가? 단언 함수의 **몸통이 틀렸다면** 이 격자는 무엇을 보장하는가?

### 8. 같은 `!`, 두 자리 (경계)

- 3번의 `let banged!: number` 와 1번의 `got!` 는 **같은 연산자인가**? 각각 컴파일러의 어느 검사를 끄는가?

### 9. 언제 써도 되나 (경계)

- 4번의 여섯 줄을 근거로, `as`·`!`·`as unknown as` 를 **써도 되는 자리**와 **안 되는 자리**를 한 줄씩 가를 수 있는가?

### 10. 29·14·13 과 잇기 (연결)

- 29편 2절의 `{} as User` 와 1번의 `[as]` 행은 **같은 모양의 실패**인가?
- `[asserts]`·`[guard]` 행이 믿는 함수의 몸통을 컴파일러가 검사하는가? 어느 편이 그것을 쟀는가?

### 11. 세 층 가르기 (연결)

- 「`as`·`!` 는 방출물에서 사라진다」는 **언어 보장**인가, **이 판의 관찰**인가? 1번 마지막 줄의 수는 무엇의 성질인가?
- `--strict` 를 끄면 3번의 진단은 어떻게 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
