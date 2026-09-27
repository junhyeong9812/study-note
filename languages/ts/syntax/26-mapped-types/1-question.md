# ts/syntax/26 — 매핑 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> 이 갈래는 **예측형**이다. ★★★ **26 → 28 은 한 사슬이다** — 여기서 만드는 매핑이 [**28번 주제**](../28-utility-types/)의 유틸리티 타입 그 자체다.
> [**22번 주제**](../22-keyof-and-indexed-access-types/)의 `keyof`·`T[K]` 와 [**24번 주제**](../24-conditional-types-and-distribution/)의 조건부를 떠올리지 못하면 답이 안 선다.
> 실행 환경: `tsc` **7.0.2** · `node` **v18.19.1**. 옵션은 **배너에 적힌 것만** 줬고 `-t es2022 --strict` 를 전부 명시했다.
> **버전** — 매핑 타입 **2.1**, `+`/`-` 수정자 **2.8**, 배열·튜플 특례 **3.1**, `as` 리매핑 **4.1**. **7.0 에서 도는지는 던져서 확인했다.**
>
> ★★★ **계산된 타입을 눈으로 보는 법** — 블록에 `const probe: null = null as unknown as X;` 가 자주 나온다.
> **일부러 틀린 주석**을 달아 컴파일러가 `Type 'X' is not assignable to type 'null'` 로 **`X` 를 말하게** 하는 탐침이다.
> ★★ 소스마다 `type Show<T> = …` 한 줄이 끼어 있다 — **탐침의 조수**다. 왜 필요한지가 1번의 과녁이다.
>
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> ★★ 이 주제의 **본체 창은 2창(`null` 탐침 + `Show` 조수)이다** — 2번은 격자 스크립트가 센다.

## 질문

<!-- 형식: 질문 하나 = "?" 하나 = 한 줄.
     유형 태그: (예측) / (왜) / (경계) / (연결) -->

### 1. 같은 타입을 네 가지로 물으면 (예측)

```ts
// ex.26a.ts
// 탐침이 매핑 타입을 어떻게 말하나 -- 별칭 이름 · & {} · 매핑으로 한 번 더 감싸기
interface User {
    id: number;
    readonly name: string;
    email?: string;
}
type Same<T> = { [K in keyof T]: T[K] };
type Show<T> = { [K in keyof T]: T[K] } & {};

const byAlias: null = null as unknown as Partial<User>;
const byIntersect: null = null as unknown as Partial<User> & {};
const byRemap: null = null as unknown as Same<Partial<User>>;
const byShow: null = null as unknown as Show<Partial<User>>;
const inline: null = null as unknown as { [K in keyof User]?: User[K] };
const identity: null = null as unknown as Show<User>;
console.log(byAlias, byIntersect, byRemap, byShow, inline, identity);
```

- 10·11·12·13행은 같은 `Partial<User>` 를 네 가지로 묻는다. **각각 무엇을 뱉는가**?
- 22편에서 쓴 조수(`& {}`)가 여기서도 듣는가?
- 15행을 왜 물어 두었는가?

### 2. 수정자 아홉 벌 (예측)

```bash
# ts26b-modgrid.sh
#!/usr/bin/env bash
# 수정자 격자 -- readonly 3가지 x ? 3가지 = 매핑 아홉 벌, 필드 네 개씩
set -u -o pipefail
D=$(mktemp -d); trap 'rm -rf "$D"' EXIT
src='interface Src { a: number; readonly b: number; c?: number; readonly d?: number; }'
show='type Show<T> = { [K in keyof T]: T[K] } & {};'
mods() { # mods <type text> <field> -> r?(readonly) o?(optional)
  local t=$1 n=$2 ro=. op=.
  case "$t" in *"readonly $n"[?:]*) ro=r;; esac
  case "$t" in *"$n?:"*) op=o;; esac
  printf '%s%s' "$ro" "$op"
}
changed=0; total=0; texts=""
printf '%-10s %-5s | %-3s %-3s %-3s %-3s\n' readonly '?' a b c d
for r in keep + -; do
  for q in keep + -; do
    case $r in keep) rr='';; +) rr='+readonly ';; -) rr='-readonly ';; esac
    case $q in keep) qq='';; +) qq='+?';; -) qq='-?';; esac
    { echo "$src"; echo "$show"; echo "type M = { ${rr}[K in keyof Src]${qq}: Src[K] };"
      echo 'const probe: null = null as unknown as Show<M>;'; echo 'export {};'; } > "$D/p.ts"
    out=$(tsc --pretty false --noEmit -t es2022 --strict "$D/p.ts" 2>&1)
    t=$(printf '%s\n' "$out" | sed -n "s/.*error TS2322: Type '\(.*\)' is not assignable to type 'null'\./\1/p" | head -1)
    row=""
    for n in a b c d; do
      m=$(mods "$t" "$n")
      row="$row $(printf '%-3s' "$m")"
      if [ "$r$q" = keepkeep ]; then eval "orig_$n=$m"; fi
      eval "o=\$orig_$n"
      total=$((total+1)); if [ "$m" != "$o" ]; then changed=$((changed+1)); fi
    done
    printf '%-10s %-5s |%s\n' "$r" "$q" "$row"
    texts="$texts$(printf '%-4s %-4s %s' "$r" "$q" "$t")"$'\n'
  done
done
echo
echo "탐침이 말한 글자 --"
printf '%s' "$texts"
echo
echo "원본(keep keep)과 갈린 칸 $changed / $total"
```

- 표의 `keep` 줄들에서 `b`·`d` 의 `readonly` 는 어떻게 되는가?
- `-` 줄에서 `?` 를 떼면 **`?` 말고 또 무엇이** 사라지는가?
- 마지막 줄의 「갈린 칸」은 몇 / 몇인가?

### 3. `in` 뒤를 바꿔 적으면 (예측)

```ts
// ex.26b.ts
// 동형 매핑 -- 원본의 수정자가 따라오는 자리와 안 따라오는 자리
type Show<T> = { [K in keyof T]: T[K] } & {};
interface Src {
    a: number;
    readonly b: number;
    c?: number;
}
type ByKeyof<T> = { [K in keyof T]: string };
type ByList<T> = { [K in "a" | "b" | "c"]: string };
type ByParam<T, Keys extends keyof T> = { [K in Keys]: string };
type ByAs<T> = { [K in keyof T as K]: string };
type SrcKeys = keyof Src;

const h1: null = null as unknown as Show<ByKeyof<Src>>;
const h2: null = null as unknown as Show<ByList<Src>>;
const h3: null = null as unknown as Show<ByParam<Src, "a" | "b" | "c">>;
const h4: null = null as unknown as Show<ByAs<Src>>;
const h5: null = null as unknown as Show<{ [K in keyof Src]: string }>;
const h6: null = null as unknown as Show<{ [K in SrcKeys]: string }>;
console.log(h1, h2, h3, h4, h5, h6);
```

- 14행부터 19행까지 **원본의 `readonly b`·`c?` 가 따라오는 줄**은 어느 것인가?
- 18행과 19행은 **키 목록이 똑같다.** 결과도 같은가?

### 4. 배열과 튜플에 걸면 (예측)

```ts
// ex.26d.ts
// 매핑 타입을 배열 · 튜플에 걸면
type Boxed<T> = { [K in keyof T]: { v: T[K] } };
type BoxedAs<T> = { [K in keyof T as K]: { v: T[K] } };
type Tup = [1, "가"];

const m1: null = null as unknown as Boxed<string[]>;
const m2: null = null as unknown as Boxed<Tup>;
const m3: null = null as unknown as Boxed<readonly [1, 2]>;
const m4: null = null as unknown as Partial<Tup>;
const m5: null = null as unknown as Boxed<Tup>["length"];
const m6: null = null as unknown as BoxedAs<Tup>["length"];
const m7: null = null as unknown as { [K in keyof Tup]: { v: Tup[K] } }["length"];
console.log(m1, m2, m3, m4, m5, m6, m7);
```

- 6행 `Boxed<string[]>` 는 배열인가 객체인가?
- 10·11·12행은 모두 `["length"]` 를 묻는다. **세 답을 나란히** 적을 수 있는가?

### 5. `as` 절에 무엇을 적느냐에 따라 (예측)

```ts
// ex.26c.ts
// as 로 키를 다시 짓는다 -- 거르기 · 이름 바꾸기 · 값으로 거르기 · 전부 never · 한 이름으로
type Show<T> = { [K in keyof T]: T[K] } & {};
interface User {
    id: number;
    name: string;
    password: string;
    save(): void;
}
type Without<T, X> = { [K in keyof T as Exclude<K, X>]: T[K] };
type Getters<T> = { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] };
type ByValue<T> = { [K in keyof T as T[K] extends Function ? never : K]: T[K] };
type AsNever<T> = { [K in keyof T as never]: T[K] };
type AsSame<T> = { [K in keyof T as "same"]: T[K] };

const r1: null = null as unknown as Show<Without<User, "password">>;
const r2: null = null as unknown as Show<Getters<Pick<User, "id" | "name">>>;
const r3: null = null as unknown as Show<ByValue<User>>;
const r4: null = null as unknown as Show<AsNever<User>>;
const r5: null = null as unknown as Show<AsSame<Pick<User, "id" | "name">>>;
console.log(r1, r2, r3, r4, r5);
```

- 15·17·18행에서 **어느 키가 남는가**?
- 19행은 두 키를 한 이름으로 보낸다. **에러가 나는가**, 난다면 무엇이고 안 난다면 무엇이 남는가?

### 6. `?` 와 `undefined` 의 관계 (왜)

- `?` 가 붙은 속성을 탐침하면 **값 타입 쪽에 무엇이 함께 찍히는가**? 그것은 `?` 를 붙이고 뗄 때 어떻게 움직이는가?
- 그것이 `--strict` 설정과 **어떻게 얽히는가**?

### 7. 방출기가 매핑을 안 푸는 까닭 (왜)

- `.d.ts` 에 `{ [K in keyof User]?: User[K]; }` 가 **적은 그대로** 남는다. 그래서 이 주제에서 5창은 어떤 상태인가?

### 8. 동형이 되는 조건 (경계)

- 원본의 수정자가 따라오려면 `in` 뒤에 **무엇이 적혀 있어야** 하는가?
- `Pick<T, K extends keyof T>` 는 `[P in K]` 인데 왜 동형으로 치는가?

### 9. `as K` 를 붙이면 (경계)

- `[K in keyof T as K]` 는 **수정자**를 지키는가? **배열 특례**는 지키는가?
- 튜플의 칸을 **걸러 내려고** `as` 를 쓰면 무엇을 잃는가?

### 10. 28 의 유틸리티와 잇기 (연결)

- `Partial`·`Readonly`·`Pick`·`Record` 를 **이 문서의 매핑 한 줄씩**으로 적을 수 있는가?
- `Partial<Cat | Dog>` 는 멤버마다 따로 도는데 `Omit<Cat | Dog, "id">` 는 무너진다. **3번의 어느 줄**이 그 차이의 실마리인가?

### 11. 세 층 가르기 (연결)

- 이 주제에서 **언어 보장** · **구현(tsc 7.0.2) 층** · **이 판의 관찰**에 해당하는 항목을 하나씩 댈 수 있는가?
- 1번의 「조수가 바뀐 일」은 어느 층인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
