# ts/syntax/26 — 매핑 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Handbook — Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html) ·
> [TypeScript 2.8 릴리스 노트 — Improved control over mapped type modifiers](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-8.html) ·
> [TypeScript 4.1 릴리스 노트 — Key Remapping in Mapped Types](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-1.html).
> 위는 **규칙 확인용 링크**이고, 본문의 진단·출력은 **전부 이 판에서 직접 던져 받은 것**이다. 핸드북 예제를 옮기지 않았다.
> **실행 검증** — 아래 판에서 실제로 돌려 얻었다.

```text
===== tsc --version · node --version · python3 --version (sh exit=0) =====
Version 7.0.2
v18.19.1
Python 3.12.3
```

> ★★★ **본체 창 선언 — 이 주제의 본체는 2창(`null` 탐침)이다. 단 조수가 바뀌었다.**
> 매핑 타입이 무엇을 만들었는지는 **탐침이 아니면 안 보인다.** 그런데 [**22번 주제**](../22-keyof-and-indexed-access-types/)가 찾은
> 조수 `& {}` 가 **여기서는 안 듣는다**(1절). 그래서 조수를 **매핑 한 겹 + `& {}`** 로 바꿨다 — 이 문서의 `Show<T>` 가 그것이다.
> ★★ 수정자는 한 번에 아홉 벌을 봐야 규칙이 보여서, **격자 스크립트**(2절)가 두 번째 기둥이다.
> ★★★ **26 → 28 은 한 사슬이다.** 여기서 만드는 `{ [K in keyof T]?: T[K] }` 가 [**28번 주제**](../28-utility-types/)의 `Partial` 그 자체이고,
> 28 의 급소(`Omit` 이 유니온에서 무너지는 것)는 이 문서 3절의 「**동형이냐 아니냐**」에서 이유가 나온다.
> ★ 소스 펜스 첫 줄 `// 파일명` 은 대조용 배너다 — 실파일에는 없다. **진단의 행 번호는 그 줄을 뺀 기준**이다.
> ★★ 표 안의 `\|` 는 이스케이프이고 **뜻은 `|` 다.**
> **버전** — 매핑 타입은 **TS 2.1**, `+`/`-` 수정자는 **TS 2.8**, 튜플·배열에 걸린 매핑이 배열로 남는 것은 **TS 3.1**,
> `as` 키 리매핑은 **TS 4.1** 이다. ★ **7.0.2 에서 도는지는 외우지 않고 던져서 확인했다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## ★★★ 이 주제가 쓰는 탐침 — 그리고 조수를 바꾼 이유

**계산된 타입은 눈에 안 보인다.** 그래서 이 갈래는 **일부러 틀린 주석을 달아 컴파일러가 답을 뱉게** 한다.

```text
  const probe: null = null as unknown as X;
                                         └─ 이 자리의 타입이 X 라면

  TS2322  「Type 'X' is not assignable to type 'null'.」
                       ↑ 여기서 X 를 읽는다
```

- ★★ 이 문서의 `TS2322 … is not assignable to type 'null'` 은 **에러가 아니라 출력**이다. 세지 말고 읽어라.
- ★★★ **그런데 매핑 타입 앞에서 탐침은 메아리만 돌려준다.** `Partial<User>` 를 물으면 `Partial<User>` 라고 답한다.
  22편에서 `keyof User` 를 펼치게 한 `& {}` 를 붙여도 **여전히 `Partial<User>`** 다(1절 11행).

> ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.**\
> 22편의 조수가 안 들어서 **조수를 바꿔** 물었다. `type Show<T> = { [K in keyof T]: T[K] } & {};` —
> 매핑 한 겹으로 **새 익명 객체를 만들게** 하고, 그 위에 `& {}` 를 얹는다.\
> ★ **바꾼 조수가 못 보는 것** — `Show` 는 **그 자체가 매핑 타입**이다. 그러니 조수가 결과를 **바꿀 위험**이 있다.
> 그래서 1절 15행에서 **`Show<User>` 가 `User` 와 같은 글자인지** 먼저 확인했다(수정자까지 같다).
> 다만 배열·튜플에서는 조수도 **배열로 남는다**(4절의 성질) — 그 자리에서는 조수 없이 `["length"]` 로 물었다.

## 이 문서에서 흔들리는 칸과 안 흔들리는 칸

| | 무엇 | 왜 |
|---|---|---|
| **안 흔들린다** | 에러 코드(`TS####`)·`(행,열)`·종료 코드 | 같은 입력·같은 옵션이면 같은 글자다 |
| **안 흔들린다** | 탐침이 뱉는 **타입 글자** | **계산된 것**이다. 공백까지 재현된다 |
| **안 흔들린다** | 2절 격자의 **`r`/`o` 배치**와 마지막 줄의 **갈린 칸 수** | 스크립트가 세어 찍는다 |
| **안 흔들린다** | 유니온 원소의 **표시 순서** | 7절 — 5회 md5 **가짓수 1**. **관찰이지 보장이 아니다** |
| **★ 설정에 달렸다** | ★★★ **`--strict` 를 끄면 `\| undefined` 가 표시에서 사라진다** — 네 파일 중 **셋이 갈렸다** | 7절에 대조와 `diff` 를 실었다 |
| **★ 구현 층** | ★★★ 탐침이 **별칭 이름으로 답하느냐 펼쳐 답하느냐** | 1절 — 「표시」의 문제다 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 **계산하지 않는다** | 0절의 근거 블록 |
| **★ 부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** — 매핑 타입은 **전부 타입 층**이다 | 이 문서에 `.js` 블록이 **하나도 없다** |
| **흔들린다** | 절대 경로 | 작업 디렉토리에서 **상대 경로로만** 던졌다 |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** 그래서 이 문서에 **빠르다·느리다는 말이 한 줄도 없다** |

★★ `--strict` 결과가 [**25번 주제**](../25-infer-and-recursive-conditional-types/)와 **다르다** — 거기서는 다섯 중 하나도 안 갈렸다.
**갈린 까닭은 매핑 타입이 아니라 `?` 가 붙은 속성의 표시**다(7절).

## 한눈에 — 쉽게 말하면

**매핑 타입은 「원본 서류의 항목 이름을 한 줄씩 읽어 가며, 같은 이름으로 새 서류를 한 장 더 쓰는 일」이다.**

| 비유 | 실체 |
|---|---|
| 원본 서류의 **항목 이름을 한 줄씩** 읽는다 | `[K in keyof T]` |
| 항목마다 **적을 내용**을 정한다 | `: T[K]` · `: string` · `: () => T[K]` |
| 새 서류에 **「수정 금지」 도장**을 찍거나 지운다 | `+readonly` / `-readonly` |
| 새 서류에 **「생략 가능」 표시**를 달거나 뗀다 | `+?` / `-?` |
| ★★★ **원본을 보고 베끼면** 원본의 도장·표시가 **저절로 따라온다** | 동형 매핑 — `keyof T` 를 **글자 그대로** 적은 경우(3절) |
| ★★ **항목 이름만 불러 주고 쓰게 하면** 도장이 안 따라온다 | `[K in "a" \| "b"]` — 동형이 아니다 |
| ★ 옮겨 적을 때 **이름을 바꾸거나 빼 버린다** | `as` 리매핑 — `never` 면 **그 줄이 사라진다**(5절) |
| ★★ **번호 매긴 목록**을 넘기면 **목록 그대로** 돌려준다 | 배열·튜플의 특례(4절) — 단 `as` 를 쓰면 깨진다 |

- ★★★ 한 줄로 — 「**매핑 타입은 키 목록을 돌며 속성을 하나씩 다시 쓰는 틀이고, `keyof T` 를 글자 그대로 쓰면 원본의 수정자가 따라온다.**」

```text
  매핑 타입은 원본을 한 줄씩 옮겨 적는다

   원본 User                         { [K in keyof User]?: User[K] }
   ────────────────────             ────────────────────────────────
   id: number            ──K="id"──▶  id?: number
   readonly name: string ──K="name"─▶ readonly name?: string   ← ★ readonly 가 따라왔다
   email?: string        ──K="email"▶ email?: string

        keyof User = "id" | "name" | "email"  이 한 줄씩 K 로 들어간다
```

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 둔다.

1. **수정자 `+`/`-` 를 조합하면 무엇이 되나** — `readonly` 세 가지 × `?` 세 가지 = **아홉 벌을 격자로** 던진다(2절).
2. **★★★ 원본의 수정자는 언제 따라오고 언제 안 따라오나** — `in` 뒤를 **다섯 가지로** 바꿔 적어 본다(3절).
3. **`as` 로 키를 다시 지으면 무엇이 사라지나** — 거르기·이름 바꾸기·전부 `never`·충돌을 던진다(5절). 그리고 **배열에 걸면 왜 깨지나**(4절).

★★ 2번이 이 주제의 급소다. **28 의 `Omit` 이 왜 유니온에서 무너지는지**가 거기서 나온다.

```text
  사슬 — 이 주제가 어디에 서 있나

  22  keyof T · T[K]            키를 꺼내는 법
   │
  24  T extends U ? X : Y        조건부와 분배      ─┐
   │                                                 │ as 절의 Exclude
  26  { [K in keyof T]: … }     ★ 여기 — 키를 돌며 다시 쓴다
   │                                                 │
  27  `get${Capitalize<K>}`     as 절에서 이름 짓기 ─┘
   │
  28  Partial · Pick · Omit …   ★ 26 의 한 줄짜리 완성품 — Omit 은 3절에서 무너진다
```

## 동작 방식

### (0) 이 주제가 쓰는 창

| 창 | 무엇을 보여 주나 | 성질 | 이 주제에서 |
|---|---|---|---|
| ★★★ **2창 — `null` 탐침 + `Show` 조수** | 컴파일러가 **계산한** 객체 모양 | 계산된 것 | **본체**(1·3·4·5절) |
| ★★ **격자 — 스크립트가 세는 칸** | 수정자 아홉 벌 × 필드 넷 | 참/거짓 | 2절 |
| ★★ **2창 + `Show`** | 메아리를 글자로 바꾼 것 | **제5의 상태** | 1절 |
| **1창 — 멤버십 대입** | 값이 그 타입에 드느냐 | 에러가 나느냐 | 이 주제에서는 **안 썼다** |
| ★ **부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** | 방출기가 **적은 그대로** 남긴다 | 아래 블록이 근거 |
| ★ **부적용 — 3창(방출 `.js`)** | ★★ **잴 것이 없다** | 매핑 타입은 **전부 타입 층**이다 | `.js` 블록이 **하나도 없다** |

**5창이 왜 부적용인가** — 방출기는 **계산하지 않는다.** 적은 것을 적은 그대로 남긴다.
이 블록은 26·27·28 **세 주제가 같이 쓰는 근거**다.

```ts
// ex.26f.ts
// 방출기는 매핑 · 템플릿 리터럴 · 유틸리티를 계산하나
interface User {
    id: number;
    name: string;
}
export type Opt = { [K in keyof User]?: User[K] };
export type Up = Uppercase<"ab">;
export type Pair = `${"a" | "b"}-${"x" | "y"}`;
export type NoId = Omit<User, "id">;
export declare const opt: Partial<User>;
```

```text
===== tsc --pretty false -t es2022 --strict --declaration --emitDeclarationOnly --outDir d26f ex.26f.ts (tsc exit=0) =====
===== 방출된 d26f/ex.26f.d.ts =====
interface User {
    id: number;
    name: string;
}
export type Opt = {
    [K in keyof User]?: User[K];
};
export type Up = Uppercase<"ab">;
export type Pair = `${"a" | "b"}-${"x" | "y"}`;
export type NoId = Omit<User, "id">;
export declare const opt: Partial<User>;
export {};
```

- ★★★ `export type Opt = { [K in keyof User]?: User[K]; };` 가 **풀리지 않은 채** 나왔다. `id?`·`name?` 으로 펼쳐 적지 않는다.
- ★★ `Uppercase<"ab">`·`` `${"a" | "b"}-${"x" | "y"}` ``·`Omit<User, "id">`·`Partial<User>` 도 **적은 그대로**다.
- ★ 그러므로 `.d.ts` 로 답을 읽을 수 없다 — 「재 봤더니 같았다」가 아니라 **잴 것이 없다.**

비용 — 컴파일 다섯 번 + 격자 아홉 번 + `--strict` 대조 여덟 번 + `diff` 두 번 + 순서 확인 다섯 번.

### (1) ★★★ 탐침이 매핑 타입을 어떻게 말하나 — 22편의 조수가 안 듣는다

**언제 쓰나** — 매핑 타입이 **무엇을 만들었는지** 눈으로 보고 싶을 때. 이 주제의 모든 절이 여기서 출발한다.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26a.ts (tsc exit=1) =====
ex.26a.ts(10,7): error TS2322: Type 'Partial<User>' is not assignable to type 'null'.
ex.26a.ts(11,7): error TS2322: Type 'Partial<User>' is not assignable to type 'null'.
ex.26a.ts(12,7): error TS2322: Type 'Same<Partial<User>>' is not assignable to type 'null'.
ex.26a.ts(13,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
ex.26a.ts(14,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
ex.26a.ts(15,7): error TS2322: Type '{ id: number; readonly name: string; email?: string | undefined; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 10행 — `Partial<User>` 를 물으니 **`Partial<User>`** 라고 답한다. 답이 아니라 **메아리**다.
- ★★★ **11행이 이 절의 급소다.** 22편에서 `keyof User` 를 펼치게 한 **`& {}` 를 붙여도 `Partial<User>`** 다.
  빈 객체와의 교차는 **그냥 지워지고** 별칭 이름이 살아남는다. 22편의 조수가 **여기서는 안 듣는다.**
- ★★ 12행 — 매핑 한 겹(`Same<…>`)으로 감싸도 **`Same<Partial<User>>`** 다. 별칭이 **한 겹 늘었을 뿐**이다.
- ★★★ 13행 — **둘을 합친 `Show<…>`** 에서야 `{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }` 로 **펼쳐진다.**
- ★ 14행 — 별칭 없이 **소스에 직접 적은** 매핑은 처음부터 펼쳐진다. 이름이 없으니 되돌려 줄 이름도 없다.
- ★★★ 15행 — **`Show<User>` 가 원본 `User` 와 같은 글자**다(`readonly name`·`email?` 까지). 조수가 **결과를 바꾸지 않는다**는 확인이다.

```text
  탐침의 조수 — 22편과 26편이 다르다

  keyof User            + & {}   →  "id" | "name" | ...   22편: 펼쳐진다
  Partial<User>         + & {}   →  Partial<User>          ★ 26편: 그대로다
  Same<Partial<User>>            →  Same<Partial<User>>    별칭이 한 겹 늘 뿐
  Show<Partial<User>>            →  { id?: ...; ... }      ★ 매핑 + & {} 둘 다 있어야 펼쳐진다

  Show<T> = { [K in keyof T]: T[K] } & {}
            └── 새 익명 객체를 만든다 ─┘   └ 이름을 못 붙이게 한다
```

- ★★★ 이것은 **명세가 정한 규칙이 아니라 tsc 7.0.2 의 「표시」 방식**이다. **구현 층**에 적어라.
- ★ 이 문서의 나머지 탐침은 **전부 `Show<…>` 로 감쌌다.** 소스마다 첫 줄 근처에 그 정의가 있는 이유다.

비용 — 조수가 **스스로 매핑 타입**이라, 배열·튜플에서는 조수 자신이 배열로 남는다(4절). 그 자리에서는 조수를 빼고 물었다.

### (2) ★★ 수정자 격자 — `readonly`·`?` 를 더하고 빼고 그대로 두면

**언제 쓰나** — 「`-readonly` 와 `-?` 를 섞으면 정확히 무엇이 남나」를 **한 번에** 보고 싶을 때.

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

```text
===== bash ts26b-modgrid.sh (sh exit=0) =====
readonly   ?     | a   b   c   d  
keep       keep  | ..  r.  .o  ro 
keep       +     | .o  ro  .o  ro 
keep       -     | ..  r.  ..  r. 
+          keep  | r.  r.  ro  ro 
+          +     | ro  ro  ro  ro 
+          -     | r.  r.  r.  r. 
-          keep  | ..  ..  .o  .o 
-          +     | .o  .o  .o  .o 
-          -     | ..  ..  ..  .. 

탐침이 말한 글자 --
keep keep { a: number; readonly b: number; c?: number | undefined; readonly d?: number | undefined; }
keep +    { a?: number | undefined; readonly b?: number | undefined; c?: number | undefined; readonly d?: number | undefined; }
keep -    { a: number; readonly b: number; c: number; readonly d: number; }
+    keep { readonly a: number; readonly b: number; readonly c?: number | undefined; readonly d?: number | undefined; }
+    +    { readonly a?: number | undefined; readonly b?: number | undefined; readonly c?: number | undefined; readonly d?: number | undefined; }
+    -    { readonly a: number; readonly b: number; readonly c: number; readonly d: number; }
-    keep { a: number; b: number; c?: number | undefined; d?: number | undefined; }
-    +    { a?: number | undefined; b?: number | undefined; c?: number | undefined; d?: number | undefined; }
-    -    { a: number; b: number; c: number; d: number; }

원본(keep keep)과 갈린 칸 20 / 36
```

그림 해설 — 한 단계에 한 문장.

- 표의 읽는 법 — `r` 는 `readonly`, `o` 는 `?`(선택), `.` 은 **없음**이다. 원본은 첫 줄 `keep keep` 이다(`a` 아무것도 없음 · `b` `readonly` · `c` `?` · `d` 둘 다).
- ★★★ **`keep` 줄은 원본을 그대로 둔다.** `readonly` 칸이 `keep` 인 세 줄에서 `b`·`d` 의 `r` 가 **안 바뀐다.** `?` 칸도 같다.
  ★ 이것이 **동형 매핑의 수정자 보존**이다 — 격자의 `[K in keyof Src]` 가 **`keyof` 를 글자 그대로** 적었기 때문이다(3절).
- ★★ `+` 는 **전부에 붙이고**, `-` 는 **전부에서 뗀다.** 원본에 있었든 없었든 상관없다.
- ★★ `+readonly` 와 그냥 `readonly` 는 **같은 것**이다 — 소스의 `+` 는 생략해도 된다(형태 절).
- ★★★ 마지막 줄 — **원본과 갈린 칸 20 / 36**. 스크립트가 센 것이다. 네 필드 × 아홉 벌 중 **16 칸은 `keep` 이 지킨 칸**이다.
- ★★ 아래쪽 「탐침이 말한 글자」 목록을 보라. **`-?` 가 붙은 줄에서는 `| undefined` 까지 사라진다**(`keep -` 줄의 `c: number`).
  `?` 가 붙을 때 `undefined` 가 **같이 붙고**, 뗄 때 **같이 떨어진다.**

```text
  수정자 두 축 — 줄마다 한 축씩 읽는다

             readonly 축                ? 축
  keep       원본 것을 그대로           원본 것을 그대로       ← 동형이라 따라온다
  +          전부에 붙인다              전부에 붙인다 (+ | undefined)
  -          전부에서 뗀다              전부에서 뗀다 (- | undefined)

  두 축은 서로 모른다 — 아홉 벌이 전부 두 축의 곱이다
```

비용 — `-?` 는 **`undefined` 까지 지운다.** 「있을 수도 없을 수도」가 아니라 「**반드시 있고, `undefined` 도 아니다**」가 된다.

### (3) ★★★ 동형 매핑 — 원본의 수정자가 따라오는 자리와 안 따라오는 자리

**언제 쓰나** — 「내가 만든 매핑이 원본의 `readonly`·`?` 를 **이어받나**」가 궁금할 때. ★ 28 의 `Omit` 이 이 절에 걸려 있다.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26b.ts (tsc exit=1) =====
ex.26b.ts(14,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(15,7): error TS2322: Type '{ a: string; b: string; c: string; }' is not assignable to type 'null'.
ex.26b.ts(16,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(17,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(18,7): error TS2322: Type '{ a: string; readonly b: string; c?: string | undefined; }' is not assignable to type 'null'.
ex.26b.ts(19,7): error TS2322: Type '{ a: string; b: string; c: string; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 14행 — `[K in keyof T]` 는 **`readonly b`·`c?` 가 따라왔다.** 값을 전부 `string` 으로 바꿨는데도 **수정자는 원본 것**이다.
- ★★★ 15행 — `[K in "a" | "b" | "c"]` 는 **키 이름은 똑같은데 수정자가 하나도 안 따라왔다.** 원본을 **안 보고** 이름만 받았기 때문이다.
- ★★ 16행 — `Keys extends keyof T` 인 타입 매개변수로 받으면 **따라온다.** 제약이 「이 키들은 `T` 의 키다」를 말해 주기 때문이다.
  ★ 이것이 **`Pick` 의 꼴**이다(`type Pick<T, K extends keyof T> = { [P in K]: T[P] }`, [**28번 주제**](../28-utility-types/)).
- ★ 17행 — `as K` 로 **자기 이름 그대로** 다시 지어도 수정자는 **따라온다.**
- ★★ 18행 — 제네릭이 아니어도 **`keyof Src` 를 글자 그대로** 적으면 따라온다.
- ★★★ **19행이 이 절의 과녁이다.** `type SrcKeys = keyof Src` 로 **별칭을 한 번 거치면** 수정자가 **사라진다.**
  같은 키 목록인데 **`keyof` 가 소스에 적혀 있지 않으면** 컴파일러는 원본이 무엇인지 모른다.

```text
  원본의 수정자가 따라오나 — in 뒤에 무엇을 적었나

  [K in keyof T]                    따라온다    14행
  [K in Keys]  (Keys extends keyof T) 따라온다  16행   ★ Pick 의 꼴
  [K in keyof T as K]               따라온다    17행
  [K in keyof Src]   (제네릭 아님)   따라온다    18행
  ──────────────────────────────────────────────────
  [K in "a" | "b" | "c"]            안 따라온다 15행
  [K in SrcKeys]  (별칭을 거침)      안 따라온다 19행   ★ 키는 같은데

  갈리는 축 — 키 목록이 무엇이냐가 아니라 "keyof 무엇" 이라고 적혀 있느냐
```

> **동형 매핑(homomorphic mapped type)** — `in` 뒤가 `keyof T`(또는 `keyof T` 로 제약된 타입 매개변수)인 매핑.\
> 예: `{ [K in keyof T]: string }` — 원본 `T` 의 `readonly`·`?` 를 **그대로 이어받는다.**

★★ 이 성질이 [**28번 주제**](../28-utility-types/)에서 두 번 나온다 — `Partial<Cat | Dog>` 는 **멀쩡하고**, `Omit<Cat | Dog, "id">` 는 **무너진다.**
`Partial` 은 `[P in keyof T]` 라 **유니온의 멤버마다 따로** 돌고, `Omit` 은 그 안에서 `keyof (Cat | Dog)` 를 **먼저 계산해 버린다.**
★ 유니온의 `keyof` 가 **교집합**이라는 사실은 [**22번 주제**](../22-keyof-and-indexed-access-types/) 1절이 이미 실측했다 — 여기서는 **인용한다.**


```text
  같은 키, 다른 결과 — 18행과 19행

  원본 Src { a; readonly b; c? }

  { [K in keyof Src]: string }     →  { a; readonly b; c? }     keyof 가 보인다 → 원본을 본뜬다
  type SrcKeys = keyof Src
  { [K in SrcKeys]: string }       →  { a; b; c }               "a"|"b"|"c" 만 보인다 → 원본을 모른다
```
비용 — **별칭 하나로 수정자가 조용히 빠진다**(19행). 진단이 없으므로 **결과 모양을 탐침으로 확인하는 수밖에** 없다.

### (4) ★★ 배열·튜플에 걸면 — 배열로 남는 특례, 그리고 `as` 가 깨는 것

**언제 쓰나** — 「튜플의 각 칸을 감싸고 싶다」처럼 **배열에 매핑을 걸 때.** 유명한 특례라 던져서 확인한다.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26d.ts (tsc exit=1) =====
ex.26d.ts(6,7): error TS2322: Type '{ v: string; }[]' is not assignable to type 'null'.
ex.26d.ts(7,7): error TS2322: Type '[{ v: 1; }, { v: "가"; }]' is not assignable to type 'null'.
ex.26d.ts(8,7): error TS2322: Type 'readonly [{ v: 1; }, { v: 2; }]' is not assignable to type 'null'.
ex.26d.ts(9,7): error TS2322: Type '[(1 | undefined)?, ("가" | undefined)?]' is not assignable to type 'null'.
ex.26d.ts(10,7): error TS2322: Type '2' is not assignable to type 'null'.
ex.26d.ts(11,7): error TS2322: Type '{ v: 2; }' is not assignable to type 'null'.
ex.26d.ts(12,7): error TS2322: Type '{ v: 2; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★ 6행 — `Boxed<string[]>` 가 **`{ v: string; }[]`** 다. 배열의 **메서드 이름 하나하나를 감싼 객체가 아니라** 여전히 **배열**이다.
- ★★ 7행 — 튜플도 **튜플로** 남는다(`[{ v: 1; }, { v: "가"; }]`). 칸마다 감쌌다.
- ★ 8행 — `readonly` 튜플은 **`readonly` 튜플로** 남는다. 3절의 동형 보존과 같은 이야기다.
- ★★ 9행 — 표준 `Partial` 을 튜플에 걸면 **선택 칸 튜플** `[(1 | undefined)?, ("가" | undefined)?]` 이 된다.
- ★★★ **10·11·12행을 나란히 읽어라.** 셋 다 `["length"]` 를 물었다.
  10행 `Boxed<Tup>["length"]` 는 **`2`** — 튜플이니 길이도 그대로다.
  11행 `BoxedAs<Tup>["length"]` 는 **`{ v: 2; }`** — `length` 까지 **감싸졌다.** `as` 를 붙인 순간 **배열이 아니라 평범한 객체**로 돌았다.
  12행 — 제네릭을 거치지 않고 **튜플에 직접 적은** 매핑도 **`{ v: 2; }`** 다.
- ★★★ 즉 특례의 조건은 둘이다 — **제네릭 동형 매핑**이어야 하고, **`as` 가 없어야** 한다.

```text
  배열로 남나, 객체로 펼쳐지나

  Boxed<Tup>                   제네릭 · 동형 · as 없음   →  [ {v:1}, {v:"가"} ]    length = 2
  BoxedAs<Tup>                 as K 를 붙였다            →  { 0:…, 1:…, length:{v:2}, map:…, … }
  { [K in keyof Tup]: … }      제네릭을 안 거쳤다         →  같은 꼴 — length 도 감싸진다

  ★ 탐침을 Show 로 감싸지 않은 이유 — Show 도 매핑이라 배열에서는 배열로 남는다.
    그래서 이 절은 ["length"] 한 칸으로 물었다 (제5의 상태)
```

비용 — `as` 로 튜플의 키를 거르려다 **튜플 자체를 잃는다.** 배열 메서드까지 전부 감싼 객체가 되어 **`map` 도 못 쓴다.**

### (5) ★★ `as` 로 키를 다시 짓는다 — `never` 면 그 줄이 사라진다

**언제 쓰나** — 키를 **빼거나**(비밀번호), **이름을 바꾸거나**(`getId`), **값 모양으로 거를** 때.

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

```text
===== tsc --pretty false --noEmit -t es2022 --strict ex.26c.ts (tsc exit=1) =====
ex.26c.ts(15,7): error TS2322: Type '{ id: number; name: string; save: () => void; }' is not assignable to type 'null'.
ex.26c.ts(16,7): error TS2322: Type '{ getId: () => number; getName: () => string; }' is not assignable to type 'null'.
ex.26c.ts(17,7): error TS2322: Type '{ id: number; name: string; password: string; }' is not assignable to type 'null'.
ex.26c.ts(18,7): error TS2322: Type '{}' is not assignable to type 'null'.
ex.26c.ts(19,7): error TS2322: Type '{ same: string | number; }' is not assignable to type 'null'.
```

그림 해설 — 한 단계에 한 문장.

- ★★★ 15행 — `as Exclude<K, "password">` 가 `password` 를 **빼 버렸다.** `Exclude` 가 그 키를 **`never` 로 만들고**, 키가 `never` 면 **그 줄이 사라진다.**
  ★ `Exclude` 가 분배 조건부라는 것은 [**24번 주제**](../24-conditional-types-and-distribution/) 5절이 직접 다시 만들어 확인했다 — 인용한다.
- ★★ 16행 — `` as `get${Capitalize<string & K>}` `` 가 이름을 **`getId`·`getName`** 으로 바꿨다. 값도 `() => T[K]` 로 바꿨다.
  ★ 템플릿 리터럴과 `Capitalize` 의 정본은 [**27번 주제**](../27-template-literal-types/)다. **여기는 「키 이름을 새로 짓는 자리에 쓸 수 있다」까지**다.
- ★★ 17행 — **값의 모양으로** 거를 수도 있다. `T[K] extends Function ? never : K` 가 `save` 를 뺐다.
- ★★ 18행 — 전부 `never` 로 보내면 **`{}`** 이다. 줄이 하나도 안 남는다.
- ★★★ 19행 — 두 키를 **같은 이름 `"same"`** 으로 보내면 **한 줄로 합쳐지고 값은 유니온**(`string | number`)이 된다. **진단이 없다.**

```text
  as 절이 키 하나에 하는 일

  K = "id"        as Exclude<K,"password">   →  "id"        그대로 남는다
  K = "password"  as Exclude<K,"password">   →  never       ★ 그 줄이 사라진다
  K = "id"        as `get${Capitalize<K>}`    →  "getId"     이름이 바뀐다
  K = "id" · "name"  as "same"                →  "same"      ★ 한 줄로 합쳐진다 — 값은 유니온
```

비용 — 이름이 **부딪혀도 조용하다**(19행). 두 속성이 한 속성으로 뭉개졌다는 신호가 **값 타입이 유니온이 됐다는 것**밖에 없다.

### (6) ★ `as` 를 붙여도 수정자는 지킨다 — 하지만 배열은 못 지킨다

3절 17행과 4절 11행을 **한 줄로** 모은다. 둘 다 `as K` 로 **자기 이름 그대로** 다시 지었다.

```text
                        수정자(readonly · ?)     배열·튜플 모양
  [K in keyof T]        따라온다                 배열로 남는다
  [K in keyof T as K]   따라온다 (3절 17행)      ★ 객체로 펼쳐진다 (4절 11행)
```

- ★★ 그러므로 「`as` 를 붙이면 동형이 깨진다」는 **반만 맞다.** 수정자 쪽은 **안 깨지고**, 배열 특례 쪽만 **깨진다.**
- ★ 이 차이는 **두 번 던져서 얻은 것**이지 규칙 문장을 읽고 적은 것이 아니다. 판이 바뀌면 **다시 던져라.**

비용 — 없다. 이 절은 **앞의 두 결과를 한 표로 모은다.**

### (7) ★ 설정 대조와 표시 순서 — 근거로 쓸 칸을 먼저 못 박는다

**언제 쓰나** — 본문의 글자를 근거로 쓰기 전에, **무엇이 흔들리지 않는지** 선언할 때.

```text
===== 같은 파일을 --strict 와 --strict false 로 각각 던져 글자 단위로 대조한다 (sh exit=0) =====
ex.26a.ts    exit 1 = exit 1 · ★ 출력이 다르다
ex.26b.ts    exit 1 = exit 1 · ★ 출력이 다르다
ex.26c.ts    exit 1 = exit 1 · 출력 한 글자도 같다
ex.26d.ts    exit 1 = exit 1 · ★ 출력이 다르다
```

```text
===== diff <(tsc --pretty false --noEmit -t es2022 --strict ex.26a.ts) <(tsc --pretty false --noEmit -t es2022 --strict false ex.26a.ts) (sh exit=1) =====
4,6c4,6
< ex.26a.ts(13,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
< ex.26a.ts(14,7): error TS2322: Type '{ id?: number | undefined; readonly name?: string | undefined; email?: string | undefined; }' is not assignable to type 'null'.
< ex.26a.ts(15,7): error TS2322: Type '{ id: number; readonly name: string; email?: string | undefined; }' is not assignable to type 'null'.
---
> ex.26a.ts(13,7): error TS2322: Type '{ id?: number; readonly name?: string; email?: string; }' is not assignable to type 'null'.
> ex.26a.ts(14,7): error TS2322: Type '{ id?: number; readonly name?: string; email?: string; }' is not assignable to type 'null'.
> ex.26a.ts(15,7): error TS2322: Type '{ id: number; readonly name: string; email?: string; }' is not assignable to type 'null'.
```

```text
===== 같은 명령을 5회 돌려 md5 가짓수를 센다 (가짓수 1 = 순서가 안 흔들렸다) (sh exit=0) =====
ex.26c.ts    5회 md5 가짓수 1
ex.27a.ts    5회 md5 가짓수 1
ex.28a.ts    5회 md5 가짓수 1
ex.28b.ts    5회 md5 가짓수 1
```

그림 해설 — 한 단계에 한 문장.

- ★★★ **네 파일 중 셋이 갈렸다**(26a·26b·26d). [**25번 주제**](../25-infer-and-recursive-conditional-types/)가 다섯 중 하나도 안 갈린 것과 다르다.
- ★★ `diff` 가 무엇이 갈렸는지 말한다 — **`| undefined` 가 사라졌다.** `id?: number | undefined` 가 `id?: number` 로 찍힌다.
  **`--strict` 에 딸린 `strictNullChecks` 가 꺼지면 `undefined` 를 따로 적지 않는** 것이다.
- ★★ **그런데 `?` 와 `readonly` 는 그대로다.** 매핑이 만든 **모양**은 설정을 안 타고, **표시에 붙는 `undefined`** 만 탄다.
- ★ 26c 는 **안 갈렸다** — 그 파일에는 `?` 속성이 없다. 그래서 갈린 원인이 매핑이 아니라 **`?` 의 표시**라고 읽는다.
- ★★ 같은 명령을 5회 돌려 md5 **가짓수가 1** 이다(26c 줄). 유니온 원소의 **표시 순서가 안 흔들렸다.** ★ **관찰이지 보장이 아니다.**

```text
  --strict 가 바꾸는 것과 안 바꾸는 것 — 26a 13행

  --strict           { id?: number | undefined; readonly name?: string | undefined; … }
  --strict false     { id?: number;             readonly name?: string;             … }
                             └─ 여기만 빠진다 ─┘
  ?  · readonly · 키 목록        그대로          ← 매핑이 만든 모양
  | undefined                    빠진다          ← strictNullChecks 가 붙이는 표시
```

비용 — 없다. 이 절은 **뒤의 모든 인용이 딛고 설 바닥**을 깐다.

## 문법 — 형태와 규칙

```text
형태 — 이 주제에서 던진 것
  { [K in keyof T]: T[K] }                    동형 매핑 — 원본 그대로       (1·3절)
  { [K in keyof T]?: T[K] }                   전부 선택으로 = Partial        (1절)
  { +readonly [K in keyof T]+?: T[K] }        + 는 붙인다 (생략 가능)        (2절)
  { -readonly [K in keyof T]-?: T[K] }        - 는 뗀다 — ? 와 함께 undefined 도  (2절)
  { [K in Keys]: X }   (Keys extends keyof T) 동형으로 친다 — Pick 의 꼴     (3절)
  { [K in "a" | "b"]: X }                     동형이 아니다                  (3절)
  { [K in keyof T as Exclude<K, "x">]: T[K] } as 로 거르기 — never 면 사라진다 (5절)   ★ 4.1
  { [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K] }   이름 바꾸기 (5절)
```

**금지 사례** — 이 주제에는 **막히는 자리가 거의 없다.** 이 주제의 실패는 에러가 아니라 **조용한 모양 변화**다.

| 쓴 꼴 | 진단 | 무엇이 일어나나 |
|---|---|---|
| `[K in SrcKeys]` (별칭) | **없음** | 수정자가 **조용히 빠진다**(3절 19행) |
| `[K in keyof T as K]` 를 튜플에 | **없음** | 튜플이 **객체로 펼쳐진다**(4절 11행) |
| 두 키를 같은 이름으로 `as` | **없음** | **한 줄로 합쳐지고 값이 유니온**(5절 19행) |

**규칙 불릿**

- ★★★ **매핑 타입은 키 목록을 돌며 속성을 한 줄씩 다시 쓴다** — `[K in 키목록]: 값`.
- ★★★ **`keyof T` 를 글자 그대로 적으면 원본의 `readonly`·`?` 가 따라온다**(동형). 별칭을 거치면 **안 따라온다**(3절).
- ★★ **`+` 는 전부에 붙이고 `-` 는 전부에서 뗀다** — 원본에 있었는지와 무관하다(2절).
- ★★ **`-?` 는 `| undefined` 까지 지운다**(2절 격자의 글자 목록).
- ★★ **`as` 절의 결과가 `never` 면 그 키는 사라진다** — 거르기의 기제다(5절).
- ★★ **이름이 부딪히면 한 줄로 합쳐지고 값은 유니온이 된다** — 진단이 없다(5절 19행).
- ★★★ **제네릭 동형 매핑을 배열·튜플에 걸면 배열·튜플로 남는다** — 단 **`as` 를 붙이면 객체로 펼쳐진다**(4절).
- ★ **탐침에는 `Show<T>` 조수가 필요하다** — `& {}` 만으로는 매핑 타입의 별칭이 안 벗겨진다(1절). **구현 층**이다.

## 어디서 틀리나

- ★★★ 「**22편처럼 `& {}` 만 붙이면 펼쳐지겠지**」 — **안 펼쳐진다**(1절 11행). 매핑 한 겹을 더 씌워야 한다.
- ★★★ 「**키 목록이 같으면 결과도 같겠지**」 — **`keyof` 가 글자로 적혀 있느냐**에 따라 수정자가 갈린다(3절 18·19행).
- ★★★ 「**`as K` 는 자기 이름 그대로니 아무것도 안 바꾸겠지**」 — 수정자는 지키지만 **튜플은 객체로 펼쳐진다**(4절 11행).
- ★★ 「**`-?` 는 `?` 만 떼겠지**」 — **`undefined` 도 같이** 뗀다(2절).
- ★★ 「**`readonly` 를 붙이면 속까지 못 바꾸겠지**」 — 매핑은 **한 층만** 돈다. 깊이는 [**28번 주제**](../28-utility-types/)가 던진다.
- ★★ 「**이름이 겹치면 에러가 나겠지**」 — **안 난다.** 값이 유니온으로 합쳐질 뿐이다(5절 19행).
- ★ 「**`--strict` 와 무관하겠지**」 — **`| undefined` 표시가 갈린다**(7절). 모양은 같다.
- ★ 「**매핑 타입은 느리겠지**」 — **이 문서는 시간을 재지 않았다.** 근거 없이 말하지 마라.

## 구현 세부사항 대 언어 보장

| 층 | 무엇 | 근거 |
|---|---|---|
| **언어 보장(2.1)** | `[K in 키목록]` 이 키마다 속성을 하나씩 만든다 | 1절 |
| **언어 보장(2.8)** | `+`/`-` 가 `readonly`·`?` 를 붙이고 뗀다 | 2절 격자 |
| **언어 보장(2.1·3.1)** | 동형 매핑이 원본 수정자를 이어받고, 배열·튜플에 걸리면 배열·튜플로 남는다 | 3·4절 — **릴리스 노트가 규칙으로 적은 것** |
| **언어 보장(4.1)** | `as` 절이 키를 다시 짓고, `never` 면 그 키가 사라진다 | 5절 15·18행 |
| **★ 이 판(7.0.2)의 관찰** | ★★★ **별칭을 거친 `keyof` 는 동형으로 안 친다** | 3절 19행 — **던져서** 얻었다 |
| **★ 이 판의 관찰** | ★★ `as K` 는 수정자는 지키고 **배열 특례는 깬다** | 3절 17행 · 4절 11행 |
| **★ 이 판의 관찰** | 이름이 부딪히면 **값이 유니온**으로 합쳐진다 | 5절 19행 |
| **★★★ 구현(tsc 7.0.2) 층** | ★★★ 탐침이 **별칭 이름으로 답하는 것**, `& {}` 가 안 듣는 것 | 1절 — **표시의 문제다** |
| **★ 설정에 달렸다** | `--strict` 를 끄면 **`\| undefined` 표시**가 사라진다 | 7절 |
| **이 판의 관찰** | 유니온 원소의 **표시 순서** | 7절 — 5회 md5 가짓수 1 |
| **★ 부적용 — 5창(`.d.ts`)** | ★★ **잴 것이 없다** — 방출기가 계산하지 않는다 | 0절 |
| **★ 부적용 — 3창(`.js`)** | ★★ **잴 것이 없다** — 전부 타입 층이다 | `.js` 블록이 **하나도 없다** |
| **안 잰 것** | ★★★ 검사 **시간**·메모리 | **재지 않았다.** 목록의 **45번 주제**로 넘긴다 |

## 언제 쓰고 언제 안 쓰나

| 매핑 타입을 직접 쓴다 | 안 쓴다 |
|---|---|
| 키마다 **값을 바꾸고 싶을** 때(`() => T[K]`·`{ v: T[K] }`) | 수정자만 바꿀 때 — **`Partial`·`Readonly` 가 이미 있다**([**28번 주제**](../28-utility-types/)) |
| **키 이름을 새로 짓거나 거를** 때(`as`) | 키 몇 개만 빼면 될 때 — `Omit` 이 있다. 단 **유니온이면 28 을 먼저 읽어라** |
| 원본 수정자를 **이어받고 싶을** 때 — `keyof T` 를 **글자 그대로** 적어라 | 키 목록을 **별칭으로 빼 두고** 쓰는 자리 — 수정자가 빠진다(3절 19행) |
| 튜플의 칸마다 감쌀 때 — **`as` 없이** 써라 | 튜플에 `as` 를 걸어야 할 때 — 튜플을 잃는다(4절 11행) |

## 핵심 문장

1. **매핑 타입은 키 목록을 돌며 속성을 한 줄씩 다시 쓰는 틀이다.**
2. **`keyof T` 를 글자 그대로 적으면 원본의 `readonly`·`?` 가 따라온다** — 별칭 하나로 조용히 빠진다.
3. **`+` 는 전부에 붙이고 `-` 는 전부에서 뗀다** — `-?` 는 `undefined` 까지 지운다.
4. **`as` 가 `never` 를 내면 그 키는 사라진다** — 거르기의 기제다.
5. **제네릭 동형 매핑은 배열을 배열로 남긴다** — `as` 를 붙이면 그 특례가 깨진다.
6. **탐침에는 `Show` 조수가 필요하다** — 22편의 `& {}` 는 여기서 안 듣는다.

## 관련 자료

- [**22번 주제** — `keyof` 와 인덱스 접근 타입](../22-keyof-and-indexed-access-types/) — ★★★ `[K in keyof T]` 의 `keyof`·`T[K]` 가 전부 그쪽 문법이다. **유니온의 `keyof` 가 교집합**이라는 실측도 그쪽.
- [**24번 주제** — 조건부 타입과 분배](../24-conditional-types-and-distribution/) — **README 의 선행.** 5절의 `Exclude` 와 `T[K] extends Function ? never : K` 가 그쪽 문법이다.
- [**25번 주제** — `infer` 와 재귀 조건부 타입](../25-infer-and-recursive-conditional-types/) — 7절의 `--strict` 대조가 **그쪽과 다른 결과**다.
- [**21번 주제** — 추론 제어](../21-inference-control-const-and-noinfer/) — `readonly` 가 **추론에서** 붙는 자리(`<const T>`)는 그쪽. 여기는 **매핑이 붙이는 자리**.
- [**27번 주제**](../27-template-literal-types/)(템플릿 리터럴 타입) — 5절 16행의 `` `get${Capitalize<…>}` `` 은 그쪽이 정본. **여기는 `as` 자리에 쓸 수 있다까지.**
- [**28번 주제**](../28-utility-types/)(유틸리티 타입) — ★★★ **사슬의 다음.** `Partial`·`Required`·`Readonly`·`Pick`·`Record` 가 **전부 이 문서의 매핑 한 줄**이다. `Omit` 의 붕괴도 3절에서 이유가 나온다.
- 목록의 **45번 주제**(타입 수준 성능) — ★★★ **검사 시간은 그쪽이다.** 이 문서는 **재지 않았다.**
- `` Kotlin 갈래 목록([`kotlin/syntax/README.md`](../../../kotlin/syntax/README.md))의 **22번**([`data class` — 무엇이 생성되고 무엇이 안 되나](../../../kotlin/syntax/22-data-class-generated-members/)) `` — Kotlin 에는 **타입에서 타입을 찍어 내는 틀이 없다.** 그쪽은 `copy` 처럼 **컴파일러가 멤버를 생성**하는 쪽이고, 여기는 **타입이 타입을 계산**하는 쪽이다.

## 용어 풀이

> **매핑 타입(mapped type)** — `{ [K in 키목록]: 값 }` 꼴로 **키마다 속성을 하나씩 만드는** 타입.\
> 예: `{ [K in "a" | "b"]: number }` 은 `{ a: number; b: number; }` 이다.

> **수정자(modifier)** — 속성에 붙는 `readonly`(바꿀 수 없음)와 `?`(없어도 됨).\
> 예: `readonly name?: string` 은 두 수정자가 다 붙은 속성이다.

> **`+`/`-` 수정자** — 매핑이 수정자를 **붙이거나(`+`) 떼는(`-`)** 표시(TS 2.8).\
> 예: `{ -readonly [K in keyof T]-?: T[K] }` 는 `readonly` 와 `?` 를 **둘 다 뗀다.**

> **동형 매핑(homomorphic mapped type)** — `in` 뒤에 `keyof T` 가 **글자 그대로** 있는 매핑. 원본 수정자를 이어받는다.\
> 예: `[K in keyof T]` 는 동형이고, `type Ks = keyof T` 를 거친 `[K in Ks]` 는 **아니다**(3절 19행).

> **키 리매핑(`as` 절)** — 매핑하면서 **키 이름을 새로 짓는** 문법(TS 4.1). 결과가 `never` 면 그 키가 사라진다.\
> 예: `[K in keyof T as Exclude<K, "password">]` 는 `password` 를 뺀다.

> **`Show<T>` 조수** — 탐침이 **별칭 이름으로 답할 때** 매핑 한 겹과 `& {}` 로 **펼쳐 찍게** 하는 수. 흔히 Prettify·Simplify 라고 부르는 모양이다.\
> 예: `Partial<User>` 는 메아리이고 `Show<Partial<User>>` 는 `{ id?: …; … }` 이다. **tsc 의 표시 방식에 기댄 수다.**

> **메아리** — 탐침이 계산한 결과 대신 **물어본 이름을 그대로** 돌려주는 것.\
> 예: 1절 10행의 `Partial<User>`.

> **`strictNullChecks`** — `--strict` 에 딸린 설정. 꺼지면 `null`·`undefined` 를 **따로 적지 않는다.**\
> 예: 7절 — `id?: number | undefined` 가 `id?: number` 로 찍힌다.

## 더 들어가면

- **왜 별칭을 거치면 동형이 아닌가** — 컴파일러가 「이 매핑은 `T` 를 본떴다」를 알려면 **`in` 뒤에서 `T` 를 봐야** 한다.
  `SrcKeys` 는 이미 **계산이 끝난 키 유니온**이라 거기서 `Src` 를 거꾸로 찾을 길이 없다.
  ★ 다만 **이것을 명세 문장으로 확인하지는 않았다** — 3절 18·19행의 출력에서 **읽은 것**이다.
- **`Show` 조수를 어디까지 믿을 수 있나** — 1절 15행이 `Show<User>` 가 `User` 와 **같은 글자**임을 확인했다.
  하지만 조수는 **동형 매핑**이라 3·4절의 성질을 **그대로 가진다** — 배열은 배열로 남고, 유니온은 멤버마다 돈다.
  [**28번 주제**](../28-utility-types/)에서 유니온을 탐침할 때 **조수가 유니온을 보존한다**는 것을 다시 쓴다.
- **깊은 `Readonly`** — 매핑은 **한 층만** 돈다. 속까지 막으려면 **재귀 매핑**(`{ readonly [K in keyof T]: DeepRO<T[K]> }`)을 쓴다.
  재귀의 한계는 [**25번 주제**](../25-infer-and-recursive-conditional-types/) 6절의 이야기와 같은 집안이다. **이 문서에서는 안 던졌다.**
- **`as` 로 튜플 칸만 거르고 싶다면** — 4절이 보였듯 `as` 를 쓰면 튜플을 잃는다.
  튜플을 거를 때는 매핑 대신 **재귀 조건부로 튜플을 다시 쌓는** 쪽이 흔하다. **안 던졌다.**
