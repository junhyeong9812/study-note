# ts/syntax/32 — 클래스의 타입 측면 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **32 는 「`.js` 방출물로 증명하는」 주제다** — 클래스에 붙은 TS 수식어가 **방출물에서 무엇이 되나**가 전부다.
> ★★★ 직접 선행은 JS 갈래 [`../../../js/syntax/16-class-syntax/`](../../../js/syntax/16-class-syntax/)다 — `#private` 의 경계(리플렉션·브랜드 검사·`Proxy`)와 「필드 = 정의, 생성자 대입 = 대입」을 거기서 쟀다.
> [**05번 주제**](../05-structural-typing/)의 구조적 타이핑도 떠올려라.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 판 비교(6번)에는 이 머신의 다른 프로젝트에 깔린 **`tsc` 4.9.5** 를 **읽기만** 해서 썼다(환경변수 `TSC_49`).
>
> ★ 소스 펜스 첫 줄 `// 파일명`·`# 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 이 주제의 **본체 창은 3창(방출된 `.js` + `node`)이다** — 1번 격자와 2번 두 방출물이 그 자리다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 필드 하나를 여섯 가지로 선언하고 바깥에서 물으면 (예측)

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

- `emit` 열 — `private x = 1;` 과 `readonly x = 1;` 은 방출물에서 무엇이 되는가? `[#x@es2021]` 은?
- `keys`·`json` 열 — `[private]` 행은 무엇을 찍는가?
- `brack` 열 — `[private]` 행의 `o["x"]` 는 **컴파일되는가**?
- `dot` 열 — `[#x]` 행은 진단과 실행이 각각 무엇인가?
- 마지막 줄의 수는 몇 / 몇이고, 그 칸들은 **어느 행들**에 있는가?

### 2. 한 클래스에 `private` 와 `#` (예측)

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

- 진단은 몇 줄인가? `-t es2022` 방출물에서 `private owner` 와 `#balance` 는 각각 어떻게 되는가?
- `-t es2021` 로 방출하면 `#balance` 는 무엇으로 바뀌는가? `node` 의 다섯 줄은 두 판이 같은가?

### 3. 매개변수 프로퍼티와 `implements` (예측)

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

- 진단이 나는 줄과 코드는 무엇인가? `implements Shape` 가 있는데도 나는 이유를 짐작할 수 있는가?
- 방출물의 `constructor` 몸통은 몇 줄인가? `implements` 는 방출물 어디에 남는가?
- `--erasableSyntaxOnly` 를 주면 무엇이 더 나는가?

### 4. `abstract` 클래스 (예측)

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

- 진단은 어느 줄에서 나는가? 방출물에서 `abstract` 는 어떻게 되는가?
- `node` 의 `[2]`·`[3]` 은 무엇을 찍는가?

### 5. 필드 선언을 설정 다섯 판으로 (예측)

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

- `-t es2022` 판에서 `[1]`\~`[3]` 은 무엇인가? `-t es2021` 판은?
- 부모의 setter 가 불리는 판은 어느 것인가?
- `-t es2021 --useDefineForClassFields true` 판의 `[3]` 은 첫 판과 같은가?
- 마지막 줄의 수는 몇 / 몇인가?

### 6. `private` 는 무엇을 지키나 (왜)

- 1번에서 `[private]` 행과 `[public]` 행의 실행 칸을 견주고, 그 결과를 방출물로 설명할 수 있는가? `private` 가 막는 것은 무엇인가?

### 7. `#x` 바깥 읽기가 막히는 방식 (왜)

- 1번 `[#x]` 의 `dot` 칸은 「런타임 강제」인가, 무엇인가? JS 16편의 `TypeError`(「Cannot read private member」)와는 **어떤 경우에** 갈리는가?

### 8. `implements` 는 타입을 주는가 (경계)

- 3번의 진단을 근거로, `implements` 가 하는 일과 **안 하는 일**을 한 줄씩 가를 수 있는가?

### 9. `abstract` 의 경계 (경계)

- 4번의 진단 칸과 `node` 칸을 근거로, `abstract` 가 막는 것은 **어느 세계**에서인가? `as unknown as` 로 넘기면 무엇이 터지는가?

### 10. JS 16 과 잇기 (연결)

- 5번의 `-t es2022` 판 `[1]` 은 JS 16편 4절의 **(가)·(나) 중 어느 쪽**과 같은 결과인가? `-t es2021` 판은?
- 3번 방출물의 `w; h; tag;` 세 줄은 JS 의 **무엇**인가?

### 11. 세 층과 판 경계 (연결)

- `useDefineForClassFields` 의 기본값은 무엇에 달려 있나? 5번의 어느 두 행이 근거인가?
- 5번 마지막 행(4.9.5)과 첫 행이 갈리는 칸은 **어느 층**의 차이인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
