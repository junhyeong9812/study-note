# ts/syntax/29 — `satisfies` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **29 는 11 에서 온다** — [**11번 주제**](../11-literal-types-and-as-const/)의 리터럴 넓히기와 `as const`,
> 그리고 [**21번 주제**](../21-inference-control-const-and-noinfer/)의 `const` 타입 매개변수를 떠올리지 못하면 3·4번이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — `satisfies` 는 **4.9**, `as const` 는 **3.4**, `const` 타입 매개변수는 **5.0** 이다. **7.0 에서 도는지는 던져서 확인했다.**
>
> ★★★ **계산된 타입을 눈으로 보는 법** — 블록에 `const probe: null = …;` 가 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ 이 주제의 **본체 창은 네 가지 비교 격자다** — 1번이 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 객체를 네 가지로 적으면 (예측)

```bash
# ts26b-four.sh
#!/usr/bin/env bash
# 같은 객체 리터럴을 네 가지로 적는다 -- 칸마다 파일 하나씩 따로 던진다
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
decl='type Color = "red" | "green";
type Palette = Record<Color, string | [number, number, number]>;'
good='{ red: [255, 0, 0], green: "#0f0" }'
wrong='{ red: [255, 0, 0], green: 42 }'
missing='{ green: "#0f0" }'
extra='{ red: [255, 0, 0], green: "#0f0", blue: "#00f" }'
write() { # write <모드> <객체> -> 선언 한 줄
  case $1 in
    annot) echo "const x: Palette = $2;" ;;
    as)    echo "const x = $2 as Palette;" ;;
    sat)   echo "const x = $2 satisfies Palette;" ;;
    none)  echo "const x = $2;" ;;
  esac
}
cell() { # cell <모드> <열> -> 칸 하나
  local mode=$1 col=$2 obj=$good tail='' out
  case $col in
    green) tail='const probe: null = x.green;' ;;
    red)   tail='const probe: null = x.red;' ;;
    wrong) obj=$wrong ;;
    missing) obj=$missing ;;
    extra) obj=$extra ;;
    upper) tail='x.green.toUpperCase();' ;;
    assign) tail='x.green = [0, 0, 255];' ;;
  esac
  { echo "$decl"; write "$mode" "$obj"; echo "$tail"; echo 'export {};'; } > "$D/c.ts"
  out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/c.ts" 2>&1)
  case $col in
    green|red) printf '%s\n' "$out" | sed -n "s/.*error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p" | head -1 ;;
    *) codes=$(printf '%s\n' "$out" | grep -o 'error TS[0-9]*' | sed 's/error //' | sort -u | tr '\n' ' ' | sed 's/ $//')
       echo "${codes:-OK}" ;;
  esac
}
declare -A got
for col in green red wrong missing extra upper assign; do
  case $col in
    green) title='[1] x.green 의 타입' ;;
    red) title='[2] x.red 의 타입' ;;
    wrong) title='[3] green 에 42 를 적으면' ;;
    missing) title='[4] red 를 빼면' ;;
    extra) title='[5] blue 를 더하면' ;;
    upper) title='[6] x.green.toUpperCase() 를 부르면' ;;
    assign) title='[7] x.green 에 [0, 0, 255] 를 대입하면' ;;
  esac
  echo "$title"
  for mode in annot as sat none; do
    v=$(cell "$mode" "$col"); got[$mode.$col]=$v
    case $mode in annot) lab=': Palette';; as) lab='as Palette';; sat) lab='satisfies';; none) lab='(plain)';; esac
    printf '  %-11s %s\n' "$lab" "$v"
  done
done
diff=0; total=0
for mode in annot as none; do
  for col in green red wrong missing extra upper assign; do
    total=$((total+1)); if [ "${got[$mode.$col]}" != "${got[sat.$col]}" ]; then diff=$((diff+1)); fi
  done
done
echo
echo "satisfies 행과 갈린 칸 $diff / $total"
```

- [1]·[2] — 네 행이 각각 무엇을 뱉는가? `satisfies` 행과 `(plain)` 행은 **같은가**?
- [3]·[4]·[5] — 네 행 중 **통과하는 것**은 각각 어느 것인가?
- [6] — 어느 행이 막히는가? [7] 은?
- 마지막 줄의 「갈린 칸」은 몇 / 몇인가?

### 2. `as` 로 적은 값을 실제로 쓰면 (예측)

```ts
// ex.29a.ts
// as 로 적은 타입과 실제로 들어 있는 값
interface User {
    id: number;
    name: string;
}
const empty = {} as User;
const half = { id: 1 } as User;

for (const [label, u] of [["empty", empty], ["half", half]] as const) {
    try {
        console.log(label, u.name.toUpperCase());
    } catch (e) {
        console.log(label, (e as Error).constructor.name, (e as Error).message);
    }
}
```

- `tsc --noEmit` 은 **몇 줄의 진단**을 내는가?
- 방출된 `.js` 에서 `as User` 는 어떻게 되는가?
- `node` 로 돌리면 두 줄이 각각 무엇을 찍는가?

### 3. `as const` 와 함께 쓰면 (예측)

```ts
// ex.29b.ts
// satisfies 와 as const -- 붙이는 순서와 문맥 타입
const routes = { home: "/", user: "/u" } as const satisfies Record<string, string>;
const p1: null = null as unknown as typeof routes;
const loose = { home: "/", user: "/u" } satisfies Record<string, string>;
const p2: null = null as unknown as typeof loose;
const picked = { mode: "a" } satisfies Record<string, "a" | "b">;
const p3: null = null as unknown as typeof picked;

const flipped = { home: "/" } satisfies Record<string, string> as const;
const wrong = { home: 1 } as const satisfies Record<string, string>;
console.log(p1, p2, p3, flipped, wrong);
```

- 3·5·7행의 탐침이 각각 무엇을 뱉는가?
- 9·10행 중 어느 쪽이 막히고, 코드는 무엇인가?

### 4. 함수로 받느냐 값에 붙이느냐 (예측)

```ts
// ex.29c.ts
// const 타입 매개변수와 satisfies -- 누가 적나
function define<const T extends Record<string, string>>(t: T): T {
    return t;
}
function plain<T extends Record<string, string>>(t: T): T {
    return t;
}
const byCallee = define({ home: "/", user: "/u" });
const byValue = { home: "/", user: "/u" } as const satisfies Record<string, string>;
const byNeither = plain({ home: "/", user: "/u" });
const p1: null = null as unknown as typeof byCallee;
const p2: null = null as unknown as typeof byValue;
const p3: null = null as unknown as typeof byNeither;

const w1 = define({ home: 1 });
console.log(p1, p2, p3, w1);
```

- 11·12·13행을 나란히 적어라. **같은 줄**이 있는가?
- 15행은 막히는가?

### 5. `satisfies` 와 추론 (왜)

- 1번 [2] 에서 `satisfies` 행의 답은 `(plain)` 행의 답과 **어떤 관계**인가? `satisfies` 는 「검사만 한다」는데 그 관계는 **어디서 생기는가**?

### 6. `as` 가 보는 것 (왜)

- 1번 [3]\~[5] 의 `as` 행 결과를 근거로, `as` 가 보는 **조건**을 한 문장으로 적을 수 있는가?
- 그 조건으로 2번의 결과를 설명할 수 있는가?

### 7. `satisfies` 는 넓히기를 막는가 (경계)

- 「`satisfies` 는 추론을 넓히지 않는다」와 「`satisfies` 는 리터럴을 지킨다」는 **같은 말인가**?
- 리터럴이 **남는 경우**와 **안 남는 경우**를 3번에서 하나씩 댈 수 있는가?

### 8. 붙이는 순서 (경계)

- `as const satisfies T` 와 `satisfies T as const` 중 **되는 쪽**은 어느 것이고, 안 되는 쪽은 **왜** 안 되는가?

### 9. 넷 중 무엇을 고르나 (경계)

- 「나중에 값을 바꿔 넣을 객체」에는 넷 중 무엇이 맞는가? 1번의 **어느 칸**이 근거인가?
- `as` 를 써도 되는 자리는 어떤 자리인가?

### 10. 11·21·06 과 잇기 (연결)

- 4번의 11행과 12행에서 **누가 무엇을 적었는가**? 두 결과는 어떤 관계인가?
- 1번 [5] 의 결과는 [**06번 주제**](../06-excess-property-checks/)의 실측과 같은가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **이 판의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?
- 1번의 「갈린 칸」 수는 **`satisfies` 의 성질인가**, 무엇의 성질인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
