# kotlin/syntax/02 — 문자열 템플릿·raw string·멀티라인 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Strings](https://kotlinlang.org/docs/strings.html) · [String templates](https://kotlinlang.org/docs/strings.html#string-templates) · [kotlin-stdlib `trimIndent`/`trimMargin`](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.text/trim-indent.html).
> **실행 검증** — 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.
> **버전** — 템플릿·raw string 은 1.0. `trimIndent`/`trimMargin` 은 1.0.\
> **멀티달러 보간(`$$"…"`)은 2.2.0 Stable** — 2.1 이하에서는 `${'$'}` 관용구를 써야 한다.
> **경계** — [`../../언어-특성/README.md`](../../언어-특성/README.md) 는 **「왜 이 언어인가」** 를 답한다.\
> 여기는 **「이 문법이 무엇으로 컴파일되나」** 만 다룬다.\
> **Java 의 텍스트 블록은 [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/) 가 정본**이고, 여기서는 **대비만** 한다(재서술하지 않는다).\
> 문자열 API(`split`·`Regex` 등)는 [목록의 **48번 주제**](../48-string-api-split-trim-pad-regex/)가 맡는다.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**문자열 템플릿은 "따옴표 안에서 코드를 부르는 것" 이 아니라, 컴파일러가 따옴표를 뜯어 이어 붙이는 것이다.**\
**raw string 은 "여러 줄" 이 목적이 아니라 "이스케이프가 없다" 가 목적이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 빈칸이 뚫린 서식 용지 | 문자열 템플릿 `"이름=$name"` |
| 빈칸에 손으로 적어 넣기 | 보간(interpolation) |
| 용지를 복사기로 뽑아 합치는 기계 | `StringBuilder` 또는 `makeConcatWithConstants` |
| 빈칸 표시를 글자로 쓰고 싶을 때 | `\$` · `${'$'}` · `$$"…"` |
| "적힌 그대로" 라고 적힌 용지 | raw string (`"""…"""`) |
| 용지 왼쪽 여백을 잘라 내는 가위 | `trimIndent()` / `trimMargin()` |
| 가위가 가장 짧은 여백에 맞춰 자르는 것 | 최소 공통 들여쓰기 |

```text
  소스                            컴파일러가 만드는 것              결과
  "이름=$name 개수=$n"    ──>     append("이름=")                "이름=준형 개수=3"
                                 append(name)
                                 append(" 개수=")
                                 append(n)
                                 toString()
```

**똑같은 구조로** Kotlin 이 동작한다 — 템플릿은 **런타임 기능이 아니라 컴파일 시점의 분해**다.

실무에서 이게 터지는 자리는 **로그 문자열이다.**\
`log.debug("...$heavyObject...")` 는 로그 레벨과 무관하게 **`toString()` 을 이미 불러 버린 뒤**다.

> **보간(interpolation)** — 문자열 안에 값을 끼워 넣는 것.\
> 예: `"안녕 $name"` 에서 `$name` 자리가 값으로 채워진다.

> **raw string(원시 문자열)** — 이스케이프를 해석하지 않고 적힌 그대로 담는 문자열. `"""` 로 감싼다.\
> 예: `"""C:\temp"""` 는 `\t` 를 탭으로 읽지 않는다.

## 이 주제가 답하려는 질문

1. `$` 는 **언제 보간이 되고 언제 그냥 글자인가** — 그리고 글자로 쓰는 방법이 왜 셋이나 있나.
2. 템플릿은 **무엇으로 컴파일되나** — 그리고 그 답이 하나인가.
3. `trimIndent()` 는 **무엇을 기준으로 자르고, 언제 아무 일도 안 하나.**

## 동작 방식

### (1) `$` 가 보간이 되는 조건 — 생각보다 좁다

**언제 쓰나** — `"$100"` 을 쓰려다 "이스케이프해야 하나" 를 고민할 때.

```kotlin
println("가격: $100")
println("끝에 달러: 100$")
println("공백 뒤: $ name")
val 값 = "한글 식별자"
println("$값")
```

**출력** (`dol.kt`)

```text
가격: $100
끝에 달러: 100$
공백 뒤: $ name
한글 식별자
```

```text
  $ 다음 글자              해석
  ----------------------------------------------
  식별자 시작 문자     ──>  보간   ($name, $값)
  {                   ──>  보간   (${expr})
  그 밖 전부           ──>  글자   ($100, $ name, 100$)
```

- **`$` 뒤에 식별자나 `{` 가 오지 않으면 그냥 글자다.** `"$100"` 에는 아무 조치도 필요 없다.
- 한글도 식별자 시작 문자다 — `$값` 이 보간된다.
- 그래서 "`$` 를 글자로 쓰는 법" 이 필요한 경우는 **뒤에 식별자가 붙을 때뿐**이다.

비용 — 없다. 전부 컴파일 시점 파싱이다.

### (2) `$` 를 글자로 쓰는 세 가지 — 그리고 raw string 에서 하나가 막힌다

**언제 쓰나** — JSON·셸 스크립트·정규식 템플릿을 문자열 안에 넣을 때.

```kotlin
println("이스케이프: \$name")
println("관용구  : ${'$'}name")
```

**출력** (`ex.kt`)

```text
--- 2. $ 를 글자로 ---
이스케이프: $name
관용구  : $name
```

raw string 안에서는 `\$` 가 **안 된다** — 이스케이프 자체가 없기 때문이다.

```kotlin
val a = """비용: ${'$'}100"""
val b = $$"""비용: $100  (멀티달러, 2.2+)"""
```

**출력** (`raw.kt`)

```text
비용: $100
비용: $100  (멀티달러, 2.2+)
```

```text
  일반 문자열 "…"            raw string """…"""
  +----------------------+   +----------------------------------+
  | \$   OK              |   | \$   불가 (이스케이프가 없다)      |
  | ${'$'}  OK           |   | ${'$'}  OK — 예전 관용구          |
  |                      |   | $$"…" 로 접두 (2.2+)  ★ 새 방법   |
  +----------------------+   +----------------------------------+
```

- `${'$'}` 는 **"`$` 라는 `Char` 리터럴을 보간한다"** 는 우회다. 읽기 어렵다는 것이 2.2 가 문법을 새로 판 이유다.
- **멀티달러 보간** — 문자열 앞의 `$` 개수가 **보간에 필요한 `$` 개수**를 정한다.

```kotlin
val b = $$$"""$$name 은 글자, $$$name 은 보간"""
```

```text
$$name 은 글자, 준형 은 보간
```

- `$$$` 접두 → **`$` 셋이 연달아야 보간**이고, `$$` 둘은 글자로 남는다.
- 셸 스크립트(`$VAR`)·JSON 템플릿(`${placeholder}`)을 통째로 넣을 때 쓴다.

비용 — 없다. 접두 개수는 파싱 규칙일 뿐 런타임에 남지 않는다.

### (3) ★★ 템플릿이 무엇으로 컴파일되나 — 답이 하나가 아니다

**언제 쓰나** — "템플릿이 `StringBuilder` 로 바뀐다" 고 들었을 때. **절반만 맞다.**

```kotlin
fun tmpl(name: String, n: Int): String = "이름=$name 개수=$n"
```

**출력 A** (`kotlinc cat.kt -d outcat/` — **플래그 없음**, 그다음 `javap -c -p`)

```text
  public static final java.lang.String tmpl(java.lang.String, int);
    Code:
       0: aload_0
       1: ldc           #9                  // String name
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: new           #17                 // class java/lang/StringBuilder
       9: dup
      10: invokespecial #21                 // Method java/lang/StringBuilder."<init>":()V
      13: ldc           #23                 // String 이름=
      15: invokevirtual #27                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      18: aload_0
      19: invokevirtual #27                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      22: ldc           #29                 // String  개수=
      24: invokevirtual #27                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      27: iload_1
      28: invokevirtual #32                 // Method java/lang/StringBuilder.append:(I)Ljava/lang/StringBuilder;
      31: invokevirtual #36                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      34: areturn
```

**출력 B** (`kotlinc cat.kt -jvm-target 21 -d outcat21/`)

```text
  public static final java.lang.String tmpl(java.lang.String, int);
    Code:
       0: aload_0
       1: ldc           #9                  // String name
       3: invokestatic  #15                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: iload_1
       8: invokedynamic #26,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;I)Ljava/lang/String;
      13: areturn
```

★ **같은 소스가 두 가지로 컴파일된다. 가른 것은 `-jvm-target` 이다.**

플래그를 안 준 쪽의 클래스 파일 버전을 찍으면 이유가 나온다.

```text
$ javap -v -p outcat/CatKt.class | grep -E "major|minor"
  minor version: 0
  major version: 52
```

- `major version: 52` = **Java 8 클래스 파일**이다. `kotlinc` 의 기본 `-jvm-target` 이 **1.8** 이라\
  JRE 21 에서 돌려도 Java 8 바이트코드가 나온다. `StringConcatFactory` 는 Java 9 부터라 쓸 수가 없다.
- `-jvm-target 21` 을 주면 `invokedynamic makeConcatWithConstants` 한 줄로 줄어든다 — **javac 9+ 와 같은 형태.**
- 되돌릴 수도 있다 — `-Xstring-concat=inline` 을 주면 `-jvm-target 21` 에서도 `StringBuilder` 로 나온다(실측).

```text
  -jvm-target 1.8 (기본)        -jvm-target 21              -jvm-target 21 -Xstring-concat=inline
  StringBuilder 6호출           invokedynamic 1개            StringBuilder 6호출
```

- ★ **그래서 "Kotlin 템플릿은 `StringBuilder` 다" 도 "`invokedynamic` 이다" 도 단독으로는 틀린 문장이다.**\
  **빌드 설정이 정한다.** 자기 프로젝트가 어느 쪽인지는 `javap` 로 직접 찍어야 안다 — 이 문서는 빌드 도구 쪽을 확인하지 않았다.

비용 — `invokedynamic` 쪽은 첫 호출에 부트스트랩 비용이 있고 이후는 JIT 가 만든 전용 메서드다.\
`StringBuilder` 쪽은 매 호출 객체 하나. **어느 쪽이든 루프 안에서 문자열을 잇는 것은 여전히 비싸다** —\
같은 대비가 [`../../../java/syntax/36-stringbuilder-and-concat/`](../../../java/syntax/36-stringbuilder-and-concat/) 에 정본으로 있다.

### (4) 템플릿은 `toString()` 을 부른다 — null 도 부른다

**언제 쓰나** — 로그·에러 메시지에 객체를 끼울 때.

```kotlin
class Money(val won: Int) { override fun toString(): String = "${won}원" }
```

**출력** (`ex.kt`)

```text
--- 3. toString 과 null ---
객체: 1000원
null: [null]  길이=null
배열: [I@15db9742
```

```kotlin
fun f(s: String?, o: Any?): String = "[$s][$o]"
```

**출력** (`javap -c -p outnul8/NulKt.class` — 기본 타깃)

```text
Compiled from "nul.kt"
public final class NulKt {
  public static final java.lang.String f(java.lang.String, java.lang.Object);
    Code:
       0: new           #10                 // class java/lang/StringBuilder
       3: dup
       4: invokespecial #14                 // Method java/lang/StringBuilder."<init>":()V
       7: bipush        91
       9: invokevirtual #18                 // Method java/lang/StringBuilder.append:(C)Ljava/lang/StringBuilder;
      12: aload_0
      13: invokevirtual #21                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      16: ldc           #23                 // String ][
      18: invokevirtual #21                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      21: aload_1
      22: invokevirtual #26                 // Method java/lang/StringBuilder.append:(Ljava/lang/Object;)Ljava/lang/StringBuilder;
      25: bipush        93
      27: invokevirtual #18                 // Method java/lang/StringBuilder.append:(C)Ljava/lang/StringBuilder;
      30: invokevirtual #30                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      33: areturn
}
```

- **`String?` 은 `append(String)`, `Any?` 는 `append(Object)`** 로 갈린다. 둘 다 `null` 이면 `"null"` 넉 자를 쓴다.
- 그래서 **템플릿 안에서는 NPE 가 안 난다** — `?.` 도 `!!` 도 필요 없다. 대신 `"null"` 이라는 글자가 조용히 들어간다.
- **배열은 `toString()` 을 오버라이드하지 않아** `[I@15db9742` 가 나온다. `contentToString()` 을 써야 한다.
- ★ **이 함수에는 `checkNotNullParameter` 가 없다** — 두 파라미터가 전부 nullable 이기 때문이다.\
  같은 자리에 non-null 파라미터가 있으면 (3)의 출력처럼 검사가 들어간다([03번](../03-null-safe-types/)이 정본).

비용 — 보간되는 값마다 `toString()` 호출 1회. **레벨이 꺼진 로그에서도 이미 불린 뒤다.**

### (5) raw string — 목적은 "여러 줄" 이 아니라 "이스케이프 없음"

**언제 쓰나** — 경로·정규식·SQL·JSON 을 문자열에 넣을 때.

**출력** (`ex.kt` · `raw.kt`)

```text
--- 4. raw string ---
C:\temp\n 은 그대로다  "따옴표"도 그대로
raw 안에서도 보간은 된다: 준형
```

```text
따옴표 셋을 raw 안에: """
raw 는 이스케이프가 없다: \n \t \\ 그대로
```

```text
  "…" (이스케이프 있음)            """…""" (raw)
  +-----------------------+       +-----------------------------+
  | \n  -> 줄바꿈          |       | \n  -> 역슬래시 + n          |
  | \"  -> 따옴표          |       | "   -> 그대로 (이스케이프 불필요) |
  | $   -> 보간            |       | $   -> 보간 ★ 여기는 같다     |
  | 여러 줄 불가            |       | 여러 줄 가능                  |
  +-----------------------+       +-----------------------------+
```

- ★ **raw string 에도 보간은 살아 있다.** "raw" 는 **이스케이프에만 적용**되지 `$` 에는 적용되지 않는다.\
  그래서 (2)의 `${'$'}`·`$$` 가 필요해진다.
- `"""` 세 개를 raw 안에 넣으려면 **보간으로 우회**한다 — `${"\"\"\""}`.
- **들여쓰기는 자동으로 안 잘린다** — 그게 (6)이다.

비용 — 없다. 컴파일 타임에 상수가 된다(보간이 없으면).

### (6) ★★ `trimIndent()` 가 무엇을 기준으로 자르나 — 그리고 언제 아무 일도 안 하나

**언제 쓰나** — raw string 을 들여쓴 코드 안에서 쓸 때(거의 항상).

**출력** (`trim.kt` — 각 줄을 `|` 로 감싸 공백을 보이게 찍었다)

```text
--- A. 표준형 (첫·마지막 줄이 공백) ---
[0] |가|
[1] |나|
(줄 수 2)
--- B. 첫 줄이 여는 따옴표에 붙음 ---
[0] |가|
[1] |        나|
(줄 수 2)
--- C. trimIndent 없음 ---
[0] ||
[1] |        가|
[2] |        나|
[3] |    |
(줄 수 4)
--- D. 들여쓰기가 다를 때 ---
[0] |가|
[1] |  나|
(줄 수 2)
--- E. 마지막 줄이 내용 ---
[0] |가|
[1] |나|
(줄 수 2)
--- F. trimMargin ---
[0] |가|
[1] |  나|
(줄 수 2)
--- G. trimMargin("#") ---
[0] |가|
[1] |나|
(줄 수 2)
--- H. 가운데 빈 줄 ---
[0] |가|
[1] ||
[2] |나|
(줄 수 3)
```

각 줄이 나온 소스는 이렇다.

```kotlin
val b = """가
    나
""".trimIndent()          // B — 첫 줄이 여는 따옴표에 붙었다
```

★ **B 가 이 절의 급소다.**

```text
  A. 표준형                          B. 첫 줄이 따옴표에 붙음
  """                                """가
      가        들여쓰기 8              나     ← 들여쓰기 8
      나        들여쓰기 8            """
  """
  최소 공통 = 8 → 8칸 잘림            최소 공통 = 0 → ★ 한 칸도 안 잘린다
                                      (빈 첫/끝 줄 제거만 일어난다)
```

규칙 셋.

1. **첫 줄과 마지막 줄이 공백뿐이면 제거**한다(A·B·C 비교 — C 는 4줄, A·B 는 2줄).
2. 나머지 줄의 **최소 공통 들여쓰기**를 찾아 그만큼 모든 줄에서 뗀다.
3. **공백뿐인 줄은 2의 계산에서 빠진다**(H — 가운데 빈 줄이 있어도 `가`/`나` 가 정상적으로 잘렸다).

- ★ **그래서 "아무 일도 안 한다" 는 정확히는 「들여쓰기를 한 칸도 못 뗀다」** 이다 —\
  줄 하나라도 들여쓰기가 0이면 최소 공통이 0이 된다. **B 가 그 경우다.**\
  빈 첫/끝 줄 제거는 **그래도 일어난다**(B 의 줄 수가 2인 것이 증거).
- D — 들여쓰기가 고르지 않으면 **최소에 맞춘다.** 상대 들여쓰기는 보존된다(`나` 앞에 2칸이 남았다).
- E — 마지막 줄이 내용이면 **그 줄도 계산에 들어간다.** 정상 동작한다.
- `trimMargin()` 은 다르다 — **`|` 를 찾아 그 앞까지 버린다**(F). 기본 접두는 `|` 이고 인자로 바꿀 수 있다(G).\
  들여쓰기를 **의도적으로 남기고 싶을 때** 쓴다(F 에서 `나` 앞 2칸이 남았다 — `|  나` 였기 때문).

비용 — **런타임 함수 호출**이다. 상수 폴딩이 아니다. 뜨거운 경로에서는 상수로 빼 둔다.

### (7) Java 의 텍스트 블록과 무엇이 다른가 — 대비만

**언제 쓰나** — Java 코드를 Kotlin 으로 옮길 때.

**출력** (`TB.java`, JDK 21.0.5)

```text
[가]
[나]
[]
줄 수(개행 기준) = 3
[가  
나]
[한 줄]
```

```text
  Java 텍스트 블록 """…"""          Kotlin raw string """…"""
  +-------------------------+      +-------------------------------+
  | 들여쓰기 자동 제거 ★      |      | 자동 제거 없음 — trimIndent() 필요 |
  | \n \t 이스케이프 있음     |      | 이스케이프 없음                 |
  | \  줄 이음 · \s 공백 유지 |      | 대응 문법 없음                  |
  | 보간 없음 (formatted)     |      | 보간 있음 ★                    |
  | 여는 """ 뒤 개행 필수     |      | 필수 아님 (그래서 (6)의 B 가 생긴다) |
  +-------------------------+      +-------------------------------+
```

- **정본은 [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/)** 다. 여기서 재서술하지 않는다.
- 옮길 때 실수하는 자리 하나 — **Java 는 자동으로 잘리므로 `.trimIndent()` 를 빼먹기 쉽다.**\
  그리고 (6)의 B 때문에 **붙였는데도 안 잘리는** 두 번째 함정이 이어진다.

## 문법 — 형태와 규칙

```kotlin
// 보간
"$name"                 // 식별자
"${name.length}"        // 식 — 프로퍼티 접근에도 중괄호가 필요하다
"${if (n > 0) "양" else "음"}"

// $ 를 글자로
"\$name"                // 일반 문자열
"""${'$'}name"""        // raw string — 예전 관용구
$$"""$name"""           // raw string — 2.2+ 멀티달러
$$$"""$$name"""         // $ 셋이어야 보간

// raw string
"""
    여러 줄
    이스케이프 없음
""".trimIndent()

"""
    |여백을 남기고 싶을 때
    |  들여쓰기 보존
""".trimMargin()
```

규칙 불릿.

- **`$name.length` 는 `name` 만 보간하고 `.length` 는 글자로 남는다** — 실측: `$name.length -> 준형.length`.\
  프로퍼티·메서드는 **반드시 `${}`** 로 감싼다.
- raw string 에 **`\$` 는 못 쓴다.** 이스케이프 자체가 없다.
- `$` 뒤에 `\` 를 붙이면 에러다 — `unsupported escape sequence`(실측).
- `trimIndent()`/`trimMargin()` 은 **stdlib 확장 함수**이지 문법이 아니다. 호출을 안 하면 아무 일도 안 일어난다.

## 어디서 틀리나

| 틀리는 형태 | 무슨 일이 일어나나 | 고치는 법 |
|---|---|---|
| `"$obj.name"` | `obj` 만 보간되고 `.name` 은 글자 | `"${obj.name}"` |
| raw string 안에 `\$` | 이스케이프가 없어 그대로 두 글자 | `${'$'}` 또는 `$$"…"` |
| `"""` 를 들여쓴 코드에 쓰고 `trimIndent()` 안 붙임 | 앞 공백이 전부 들어간다 | `.trimIndent()` |
| `"""가` 처럼 첫 줄을 따옴표에 붙임 | ★ `trimIndent()` 를 붙여도 **안 잘린다** | 여는 `"""` 다음에 개행을 넣는다 |
| `log.debug("… $heavy …")` | 레벨과 무관하게 `toString()` 이 이미 불렸다 | 람다를 받는 로깅 API 를 쓴다 |
| `"$nullable"` | NPE 가 아니라 `"null"` 넉 자가 들어간다 | 의도인지 확인하고, 아니면 `?: "(없음)"` |
| `"$intArray"` | `[I@15db9742` | `contentToString()` |
| "템플릿은 `StringBuilder` 다" 라고 외움 | `-jvm-target` 에 따라 다르다 | `javap` 로 자기 빌드를 찍어 본다 |
| 뜨거운 루프에서 `trimIndent()` | 호출마다 문자열을 다시 만든다 | 상수로 빼 둔다 |

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `$` 뒤가 식별자·`{` 가 아니면 글자다 | **언어** | 명세 + 실측(`$100`) |
| raw string 은 이스케이프를 해석하지 않는다 | **언어** | 명세 + 실측 |
| raw string 안에서도 보간은 된다 | **언어** | 실측 |
| 보간되는 값에 `toString()` 이 불린다 | **언어** | 명세 |
| `null` 이 `"null"` 로 들어간다 | **언어** | 실측 (`[null]`) |
| `trimIndent` 의 세 규칙 | **stdlib 계약** | kdoc + 실측 |
| **템플릿이 `StringBuilder` 로 컴파일되는 것** | **구현** | `javap` — `-jvm-target 1.8` 에서만 |
| **템플릿이 `invokedynamic` 으로 컴파일되는 것** | **구현** | `javap` — `-jvm-target 21` 에서 |
| **`-Xstring-concat=inline` 이 되돌리는 것** | **구현**(실험 플래그) | `javap` |
| `kotlinc` 의 기본 `-jvm-target` 이 1.8 인 것 | **구현**(이 버전) | `major version: 52` |

★ **이 주제에서 "구현" 칸이 특히 넓은 이유는 하나다 — 문자열 잇기는 언어가 결과만 정하고 방법은 안 정한다.**\
결과(`"이름=준형 개수=3"`)는 보장되고, 그 결과를 만드는 호출은 보장되지 않는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 짧은 메시지·로그 | 일반 문자열 + 보간 | 가장 읽기 쉽다 |
| 경로·정규식 | raw string | 역슬래시 지옥이 사라진다 |
| SQL·JSON·HTML 덩어리 | raw string + `trimIndent()` | 소스 들여쓰기와 결과 들여쓰기를 분리 |
| 결과 들여쓰기를 의도적으로 남길 때 | `trimMargin()` | `\|` 위치가 곧 왼쪽 끝 |
| 셸·JSON **템플릿**(`$VAR` 를 남겨야 함) | `$$"…"` (2.2+) | `${'$'}` 범벅을 피한다 |
| 2.1 이하 프로젝트 | `${'$'}` | 멀티달러가 없다 |
| 뜨거운 루프 안 | 보간 대신 `StringBuilder` 직접 | 어느 컴파일 형태든 루프 안에서는 비싸다 |
| 로깅 | 람다 받는 API | 보간은 **레벨 검사 전에** 평가된다 |

판단 규칙 두 줄.

- **`\` 가 하나라도 보이면 raw string 을 생각한다.**
- **`"""` 를 썼으면 `.trimIndent()` 가 붙었는지, 그리고 여는 따옴표 다음이 개행인지 둘 다 본다.**

## 핵심 문장

- `$` 는 **뒤에 식별자나 `{` 가 올 때만** 보간이다. `"$100"` 은 아무 조치도 필요 없다.
- raw string 의 "raw" 는 **이스케이프에만 걸린다** — 보간은 살아 있고, 그래서 `${'$'}`·`$$` 가 생겼다.
- **템플릿이 무엇으로 컴파일되는지는 `-jvm-target` 이 정한다** — 기본 1.8 이면 `StringBuilder`, 21 이면 `invokedynamic`.
- `trimIndent()` 는 **최소 공통 들여쓰기**를 뗀다. 줄 하나라도 들여쓰기가 0이면 **한 칸도 못 뗀다.**
- 보간은 **`toString()` 을 이미 부른 뒤**다. 로그 레벨은 그다음에 검사된다.
- 템플릿 안의 `null` 은 예외가 아니라 **`"null"` 넉 자**다.

## 관련 자료

- [`../README.md`](../README.md) — Kotlin 문법·API 주제 목록(이 주제는 02번)
- [01번 주제](../01-val-var-and-basic-types/) — 보간되는 값들의 타입. `Int` 와 `Int?` 가 `append` 오버로드를 가른다
- [03번 주제](../03-null-safe-types/) — (3)·(4)에 보이는 `Intrinsics.checkNotNullParameter` 가 **거기 정본**이다
- [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/) — **Java 텍스트 블록의 정본.** 여기는 대비만 했다
- [`../../../java/syntax/36-stringbuilder-and-concat/`](../../../java/syntax/36-stringbuilder-and-concat/) — **`invokedynamic` 문자열 잇기의 정본.** 비용 논의는 거기
- [`../../../java/syntax/35-string/`](../../../java/syntax/35-string/) — `String` 자체의 불변성·상수 풀
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 「왜 이 언어인가」. 문법이 아니라 선택 논증
- [목록의 **48번 주제**](../48-string-api-split-trim-pad-regex/)(문자열 API — `split`/`trim*`/`Regex`) — `trimIndent` 밖의 문자열 함수들
- [목록의 **37번 주제**](../37-lambdas-with-receiver-and-type-safe-builders/)(리시버 지정 람다와 DSL) — raw string + 빌더로 SQL/HTML 을 짜는 다음 단계

## 용어 풀이

- **문자열 템플릿(string template)** — 문자열 안에 `$` 로 값을 끼워 넣는 문법.
- **보간(interpolation)** — 그 끼워 넣기 자체. 컴파일 시점에 분해되어 이어 붙이기로 바뀐다.
- **raw string** — `"""` 로 감싼 문자열. 이스케이프를 해석하지 않고 여러 줄을 담는다.
- **멀티달러 보간(multi-dollar interpolation)** — 문자열 앞에 `$` 를 여러 개 붙여 보간에 필요한 `$` 개수를 올리는 문법. **2.2.0 Stable.**
- **`trimIndent()`** — 최소 공통 들여쓰기를 떼고 빈 첫/끝 줄을 없애는 stdlib 확장 함수.
- **`trimMargin()`** — 줄마다 접두(기본 `|`)를 찾아 그 앞을 버리는 확장 함수.
- **최소 공통 들여쓰기** — 공백뿐인 줄을 뺀 모든 줄의 앞 공백 중 가장 짧은 것.
- **`StringConcatFactory` / `makeConcatWithConstants`** — Java 9 부터 문자열 잇기를 런타임에 조립하는 JDK 기능. `invokedynamic` 으로 불린다.
- **`invokedynamic`** — 호출 대상을 첫 실행 때 결정하는 JVM 명령.
- **`-jvm-target`** — kotlinc 가 만들 클래스 파일의 JVM 버전. **이 문서에서는 이것이 결과를 가른다.**
- **`Intrinsics.checkNotNullParameter`** — 컴파일러가 non-null 파라미터에 심는 런타임 검사. [03번](../03-null-safe-types/)이 정본.

---

## 더 들어가면

- `-Xstring-concat` 에는 세 값이 있다 — `indy-with-constants`(9+ 기본)·`indy`·`inline`.\
  **`inline` 은 `-jvm-target 21` 에서도 `StringBuilder` 를 만든다**(실측). 옛 JVM 에서의 회귀나 벤치마크 비교에 쓴다.
- raw string 안에 여는 구분자와 같은 `"""` 를 넣는 유일한 방법이 **보간**이라는 것은,\
  Kotlin 이 **닫는 구분자를 이스케이프할 수단을 아예 안 두기로** 했다는 뜻이다.\
  Java 텍스트 블록은 역슬래시로 이스케이프할 수 있다 — 던져서 확인했다.

```text
$ java -cp outtb2 TB2
따옴표 셋: """ 끝
```

- `trimIndent()` 가 **런타임 호출**이라는 사실은 상수 표현식으로 쓸 수 없다는 뜻이기도 하다.

```text
extra.kt:1:15: error: const 'val' initializer must be a constant value.
const val C = """
              ^^^
```

  (`const` 의 정본은 [목록의 **16번 주제**](../16-properties-backing-field-lateinit-const/)가 된다.)
- 보간 안에 **람다 자체**를 넣으면 합성 클래스의 기본 `toString` 이 찍힌다. 부르고 싶으면 `${f()}` 로 적는다.

```text
람다: ExtraKt$$Lambda/0x0000740304000dd8@511d50c0
부르면: 1
```
