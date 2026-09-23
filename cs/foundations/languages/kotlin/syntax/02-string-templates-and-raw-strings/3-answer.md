# kotlin/syntax/02 — 문자열 템플릿·raw string·멀티라인 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> Java 텍스트 블록 출력은 같은 JDK 의 `javac`/`java` 결과이고, **그 주제의 정본은 [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/)** 다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 이 네 줄에서 `$` 는 언제 보간되는가

**출력** (`dol.kt`)

```text
가격: $100
끝에 달러: 100$
공백 뒤: $ name
한글 식별자
```

**왜 그런가**

```text
  $ 다음 글자              해석
  ----------------------------------------------
  식별자 시작 문자     ──>  보간   ($name, $값)
  {                   ──>  보간   (${expr})
  그 밖 전부           ──>  글자   ($100, $ name, 100$)
```

- 보간 조건 한 문장 — **`$` 바로 뒤에 식별자 시작 문자 또는 `{` 가 올 때만 보간이다.**
- `[A]` `$1` 은 식별자가 아니므로 `$` 가 그대로 글자다. **이스케이프가 필요 없다.**
- `[B]` 문자열 끝의 `$` 도 뒤에 아무것도 없으니 글자다.
- `[C]` `$` 다음이 공백이라 글자다.
- `[D]` **한글도 식별자 시작 문자다** — `값` 이라는 변수가 보간됐다.
- 그래서 "따옴표 안에 `$` 가 있으면 무조건 이스케이프" 라는 습관은 **불필요한 잡음**이다.

### 2. ★ `$` 를 글자로 쓰는 방법 셋 중 raw string 에서 못 쓰는 것은

**출력** (`ex.kt` · `raw.kt` · `md.kt`)

```text
--- 2. $ 를 글자로 ---
이스케이프: $name
관용구  : $name
```

```text
비용: $100
비용: $100  (멀티달러, 2.2+)
```

```text
JSON: {"v": "준형", "raw": "$name"}
$$name 은 글자, 준형 은 보간
```

**왜 그런가**

| | 구문 | 결과 |
|---|---|---|
| `[A]` | `"\$name"` | `$name` — 일반 문자열의 이스케이프 |
| `[B]` | `"""${'$'}name"""` | `$name` — 예전 관용구 |
| `[C]` | `$$"""$name"""` | `$name` — **2.2.0 Stable** |
| `[D]` | `"""\$name"""` | **`\$name`** — 역슬래시가 글자로 남는다 |

```text
  일반 문자열 "…"            raw string """…"""
  +----------------------+   +----------------------------------+
  | \$   OK              |   | \$   불가 (이스케이프가 없다)      |
  | ${'$'}  OK           |   | ${'$'}  OK — 예전 관용구          |
  |                      |   | $$"…" 로 접두 (2.2+)  ★ 새 방법   |
  +----------------------+   +----------------------------------+
```

- `[D]` 가 `[A]` 와 다른 이유 — **raw string 에는 이스케이프라는 개념 자체가 없다.**\
  `\$` 는 "이스케이프된 달러" 가 아니라 **역슬래시 한 글자 + 달러 한 글자**다.
- `[C]` 는 **2.2.0 Stable**. 2.1 이하에서는 `${'$'}` 를 쓴다.
- **멀티달러 규칙** — 접두 `$` 개수 = 보간에 필요한 `$` 개수.\
  `$$$"""$$name 은 글자, $$$name 은 보간"""` 의 출력이 `$$name 은 글자, 준형 은 보간` 이다.\
  즉 **접두보다 적은 `$` 는 전부 글자로 남는다.**
- 쓸 자리 — 셸 스크립트(`$VAR`)·JSON 템플릿(`${placeholder}`)을 통째로 문자열에 넣을 때.

### 3. ★★ 이 함수는 무엇으로 컴파일되는가

**출력 A** (`kotlinc cat.kt -d outcat/` → `javap -c -p outcat/CatKt.class`)

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

**왜 그런가**

- ★ **답이 하나가 아니다. `-jvm-target` 이 가른다.**
- 이유는 클래스 파일 버전으로 확인한다.

```text
$ javap -v -p outcat/CatKt.class | grep -E "major|minor"
  minor version: 0
  major version: 52
```

- `major version: 52` = **Java 8 클래스 파일**. **`kotlinc` 의 기본 `-jvm-target` 은 1.8** 이다 —\
  JRE 21 에서 돌려도 Java 8 바이트코드가 나온다. `StringConcatFactory` 는 Java 9 부터라 쓸 수가 없어 `StringBuilder` 로 떨어진다.
- `-jvm-target 21` 을 주면 `invokedynamic makeConcatWithConstants` 한 줄이다 — javac 9+ 와 같은 형태.
- 되돌릴 수도 있다 — `-jvm-target 21 -Xstring-concat=inline` 은 다시 `StringBuilder` 6호출이 된다(실측).

```text
  -jvm-target 1.8 (기본)       -jvm-target 21          -jvm-target 21 -Xstring-concat=inline
  StringBuilder 6호출          invokedynamic 1개        StringBuilder 6호출
```

- ★ 그래서 **"Kotlin 템플릿은 `StringBuilder` 다" 는 맞는 문장이 아니다.** "`invokedynamic` 이다" 도 마찬가지다.\
  **언어는 결과만 정하고 방법은 빌드 설정이 정한다.** 자기 프로젝트가 어느 쪽인지는 `javap` 로 직접 찍어야 안다.

### 4. ★ 보간 안의 값이 `null` 이면 무슨 일이 일어나는가

**출력** (`ex.kt`)

```text
--- 3. toString 과 null ---
객체: 1000원
null: [null]  길이=null
배열: [I@15db9742
```

**출력** (`javap -c -p outnul8/NulKt.class` — `fun f(s: String?, o: Any?): String = "[$s][$o]"`, 기본 타깃)

```text
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

**왜 그런가**

- **보간 자리에서 NPE 는 안 난다.** `null` 은 `"null"` 이라는 **넉 자**가 된다. `?.` 도 `!!` 도 필요 없다.\
  그래서 **조용히 틀린다** — 예외가 안 나므로 코드 리뷰나 로그에서 눈으로 잡는 수밖에 없다.
- 오버로드가 타입으로 갈린다 — **`String?` 은 `append(String)`, `Any?` 는 `append(Object)`.**\
  대괄호 한 글자는 `append(C)`(`bipush 91` = `[`, `93` = `]`)다. 컴파일러가 **글자 하나까지 골라서** 오버로드를 고른다.
- **배열은 `toString()` 을 오버라이드하지 않아** `[I@15db9742` 가 나온다. `contentToString()` 을 써야 한다.\
  `[I` 는 `int[]` 의 JVM 디스크립터다 — [01번](../01-val-var-and-basic-types/)의 디스크립터 표기와 같은 것.
- ★ **이 함수에는 `checkNotNullParameter` 가 없다.** 두 파라미터가 전부 nullable 이기 때문이다.\
  3번의 `tmpl(name: String, …)` 에는 있었다 — **non-null 파라미터에만 심는다.**\
  그 규칙의 정본은 [03번](../03-null-safe-types/)이다.

### 5. ★★ `trimIndent()` 가 언제 아무 일도 안 하는가

**출력** (`trim.kt` — 각 줄을 `|` 로 감쌌다)

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
--- H. 가운데 빈 줄 ---
[0] |가|
[1] ||
[2] |나|
(줄 수 3)
```

**왜 그런가**

```text
  A. 표준형                          B. 첫 줄이 따옴표에 붙음
  """                                """가
      가        들여쓰기 8              나     ← 들여쓰기 8
      나        들여쓰기 8            """
  """
  최소 공통 = 8 → 8칸 잘림            최소 공통 = 0 → ★ 한 칸도 안 잘린다
```

규칙 셋(전부 실측으로 확인).

1. **첫 줄·마지막 줄이 공백뿐이면 제거**한다 — C(제거 안 함, 4줄)와 A·B(2줄)의 차이.
2. 나머지 줄의 **최소 공통 들여쓰기**만큼 모든 줄에서 뗀다.
3. **공백뿐인 줄은 2의 계산에서 빠진다** — H 에서 가운데 빈 줄이 있는데도 `가`/`나` 가 정상적으로 잘렸다.

- `[B]` 가 `[A]` 와 다른 이유 — **첫 줄 `가` 의 들여쓰기가 0** 이라 최소 공통이 0이 됐다.\
  `나` 앞의 8칸이 그대로 남았다.
- ★ **`[B]` 에서 `trimIndent()` 가 전혀 아무 일도 안 한 것은 아니다.**\
  줄 수가 **2** 라는 것이 증거다 — 마지막의 공백뿐인 줄은 제거됐다(C 와 비교하면 4 → 2).\
  즉 **"아무 일도 안 한다" 가 아니라 "들여쓰기를 한 칸도 못 뗀다"** 가 정확하다.
- `[D]` — 최소에 맞추므로 **상대 들여쓰기는 보존된다**(`나` 앞 2칸).
- `[H]` — 가운데 빈 줄은 계산에서 빠지고, 결과에도 빈 줄로 남는다.

### 6. ★ raw string 에서 이 넷은 어떻게 나오는가

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

**왜 그런가**

```text
  "…" (이스케이프 있음)            """…""" (raw)
  +-----------------------+       +-----------------------------+
  | \n  -> 줄바꿈          |       | \n  -> 역슬래시 + n          |
  | \"  -> 따옴표          |       | "   -> 그대로 (이스케이프 불필요) |
  | $   -> 보간            |       | $   -> 보간 ★ 여기는 같다     |
  | 여러 줄 불가            |       | 여러 줄 가능                  |
  +-----------------------+       +-----------------------------+
```

- ★ **"raw" 가 걸리는 범위는 이스케이프뿐이다. 보간에는 안 걸린다.**\
  그래서 2번의 `${'$'}`·`$$` 가 필요해진다. 이것이 raw string 의 가장 자주 틀리는 자리다.
- `[C]` — 여는 구분자와 같은 `"""` 를 넣는 유일한 방법이 **보간**이다(`${"\"\"\""}`).\
  raw string 에는 **닫는 구분자를 이스케이프할 수단이 없다.**
- Java 텍스트 블록은 같은 문제를 **역슬래시 이스케이프로** 푼다 — 던져서 확인했다.

```text
$ java -cp outtb2 TB2
따옴표 셋: """ 끝
```

- 즉 **Java 는 텍스트 블록 안에서도 이스케이프를 살려 두었고 Kotlin 은 버렸다.** 그 대가가 `${…}` 우회다.\
  텍스트 블록 자체의 정본은 [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/).

### 7. `$name.length` 는 무엇을 보간하는가

**출력** (`ex.kt`)

```text
--- 1. 기본 보간 ---
이름=준형 개수=3 합=6
프로퍼티는 중괄호가 필요하다: 2 / $name.length -> 준형.length
```

**에러** (`kotlinc dol.kt` — `$\{}` 를 시도했을 때)

```text
dol.kt:7:25: error: unsupported escape sequence.
    println("이스케이프 불가? $\{}")
                        ^^
```

**왜 그런가**

- `"$name.length"` 는 **`준형.length`** 다. `$name` 까지만 보간되고 `.length` 는 글자로 남는다.
- 보간의 단위는 **단순 식별자 하나**다. 그 이상(프로퍼티 접근·메서드 호출·연산)은 **반드시 `${}`** 로 감싼다.
- `$` 뒤에 `\` 는 못 온다 — `unsupported escape sequence`.
- 실무에서 가장 자주 틀리는 자리는 **로그와 에러 메시지**다.\
  `"주문 $order.id 실패"` 가 `Order@1a2b3c.id 실패` 로 나가고, `toString()` 이 잘 만들어져 있으면\
  **그럴듯해 보여서 더 늦게 발견된다.**

### 8. 로그에 보간을 쓰면 무엇이 문제인가

**왜 그런가**

- **레벨이 꺼져 있어도 `toString()` 은 이미 불린 뒤다.**\
  `log.debug("무거운 객체: $heavy")` 는 **먼저 문자열을 완성해서** `debug` 에 넘긴다.
- 원인은 로깅 라이브러리가 아니라 **언어**다 — 3번의 바이트코드가 그 증거다.\
  `invokedynamic`(또는 `StringBuilder` 사슬)이 **`debug` 호출보다 먼저** 실행된다.\
  라이브러리는 이미 만들어진 `String` 을 받을 뿐이라 **막을 방법이 없다.**
- 피하는 법 — **람다를 받는 API** 를 쓴다(`log.debug { "무거운 객체: $heavy" }`).\
  람다 안이면 레벨 검사 뒤에야 평가된다. `kotlin-logging` 류가 이 형태다.
- 같은 성질을 갖는 다른 자리 — **`require`/`check` 의 메시지**다.\
  `require(ok) { "비싼 메시지 $x" }` 는 람다라 조건이 참이면 안 만들지만,\
  `require(ok, "비싼 메시지 $x")` 처럼 값으로 넘기면 항상 만든다. 목록의 **51번 주제**가 정본이 된다.

### 9. 이 주제에서 "언어 보장" 과 "구현 세부" 의 경계는 어디인가

| 사실 | 어느 쪽 | 근거 |
|---|---|---|
| `$` 뒤가 식별자·`{` 가 아니면 글자다 | **언어** | 명세 + 실측(`$100`) |
| raw string 은 이스케이프를 해석하지 않는다 | **언어** | 명세 + 실측 |
| raw string 안에서도 보간은 된다 | **언어** | 실측 |
| `null` 이 `"null"` 로 들어간다 | **언어** | 실측 |
| `trimIndent` 의 세 규칙 | **stdlib 계약** | kdoc + 실측 |
| **`StringBuilder` 로 컴파일되는 것** | **구현** | `javap` — `-jvm-target 1.8` |
| **`invokedynamic` 으로 컴파일되는 것** | **구현** | `javap` — `-jvm-target 21` |
| **기본 `-jvm-target` 이 1.8 인 것** | **구현**(이 버전) | `major version: 52` |
| `-Xstring-concat=inline` 이 되돌리는 것 | **구현**(실험 플래그) | `javap` |

- ★ 구현 칸이 유독 넓은 이유 한 문장 — **문자열 잇기는 언어가 결과만 정하고 방법은 정하지 않기 때문이다.**\
  `"이름=준형 개수=3"` 이라는 결과는 보장되고, 그 결과를 만드는 호출은 무엇 하나 보장되지 않는다.
- 그래서 이 주제에서 **성능 이야기를 하려면 반드시 자기 빌드를 `javap` 로 찍어야** 한다.

### 10. 다른 주제와 잇기

**Java 텍스트 블록과의 차이 다섯**

```text
  Java 텍스트 블록 """…"""          Kotlin raw string """…"""
  +-------------------------+      +-------------------------------+
  | 들여쓰기 자동 제거 ★      |      | 자동 제거 없음 — trimIndent() 필요 |
  | \n \t 이스케이프 있음     |      | 이스케이프 없음                 |
  | \  줄 이음 · \s 공백 유지 |      | 대응 문법 없음                  |
  | 보간 없음 (formatted)     |      | 보간 있음 ★                    |
  | 여는 """ 뒤 개행 필수     |      | 필수 아님 (그래서 5번 B 가 생긴다) |
  +-------------------------+      +-------------------------------+
```

**출력** (`TB.java`, JDK 21.0.5 — 자동 제거의 증거)

```text
[가]
[나]
[]
줄 수(개행 기준) = 3
[가  
나]
[한 줄]
```

- 옮길 때 실수하는 자리 — Java 는 자동으로 잘리므로 **`.trimIndent()` 를 빼먹기 쉽고**,\
  붙였는데도 5번의 `[B]` 때문에 **안 잘리는** 두 번째 함정이 이어진다.
- **정본은 [`../../../java/syntax/32-text-blocks/`](../../../java/syntax/32-text-blocks/)** 다.
- `Intrinsics.checkNotNullParameter` 의 정본은 **[03번 주제](../03-null-safe-types/)** 다.
- `trimIndent()` 는 **`const val` 초기값에 못 쓴다** — 런타임 호출이기 때문이다.

```text
extra.kt:1:15: error: const 'val' initializer must be a constant value.
const val C = """
              ^^^
```

- 루프에서 문자열을 잇는 비용은 [`../../../java/syntax/36-stringbuilder-and-concat/`](../../../java/syntax/36-stringbuilder-and-concat/) 가 정본이다.

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `ex.kt` | 기본 보간, `$name.length`, `\$`/`${'$'}`, `toString`/null/배열, raw string 기본 | `kotlinc` → `java` |
| `dol.kt` | `$100`·`100$`·`$ name`·`$값`, `$\` 가 에러인 것 | `kotlinc` (에러) → 그 줄을 빼고 `java` |
| `raw.kt` | raw 안의 `${'$'}`·`$$`·`"""`·이스케이프 없음 | `kotlinc` → `java` |
| `md.kt` | 멀티달러 `$$`·`$$$` (2.2+) | `kotlinc` → `java` |
| `trim.kt` | `trimIndent` 8가지 경우 + `trimMargin` 2가지 (줄 수와 앞 공백을 `\|` 로 가시화) | `kotlinc` → `java` |
| `cat.kt` | 템플릿 컴파일 형태 — **기본 / `-jvm-target 21` / `-Xstring-concat=inline` 세 번** | `javap -c -p` · `javap -v \| grep major` |
| `nul.kt` | `String?`/`Any?` 의 `append` 오버로드, `checkNotNullParameter` 부재 | `javap -c -p` (기본·21 두 번) |
| `extra.kt` | `const val` + `trimIndent` 거부, 람다 보간 | `kotlinc` (에러) → 그 줄을 빼고 `java` |
| `TB.java` | Java 텍스트 블록의 들여쓰기 자동 제거·`\s`·`\` 줄 이음 | `javac` → `java` |
| `TB2.java` | Java 텍스트 블록이 닫는 구분자를 이스케이프할 수 있는 것 | `javac` → `java` |

**구현 의존 항목** — `javap` 의 명령 목록과 상수 풀 번호(`#9`·`#15` …), `StringBuilder` 대 `invokedynamic`,
`major version: 52`, 기본 `-jvm-target` 값, 람다의 합성 클래스 이름(`ExtraKt$$Lambda/0x…@…` — **실행마다 주소가 다르다**) —
전부 **이 컴파일러·이 JVM 타깃의 산출물**이다.\
반면 "`$` 뒤가 식별자일 때만 보간"·"raw 는 이스케이프가 없다"·"raw 에도 보간은 있다"·
"`null` 은 `\"null\"` 넉 자"·`trimIndent` 의 세 규칙은 **언어·stdlib 계약**이라 타깃과 무관하다.

**세 번 찍은 것** — `cat.kt` 는 **기본·`-jvm-target 21`·`-Xstring-concat=inline` 세 조건**에서 각각 `javap` 를 찍었다.
한 조건만 찍었으면 "Kotlin 템플릿은 `StringBuilder` 다" 라는 틀린 결론을 그대로 실었을 것이다.
