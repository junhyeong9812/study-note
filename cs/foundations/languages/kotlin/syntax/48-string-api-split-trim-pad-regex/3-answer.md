# kotlin/syntax/48 — 문자열 API — `split`/`trim*`/`pad*`/`Regex` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다. 따옴표 안의 `<U+XXXX>` 는 **보이지 않는 글자를 격자가 바꿔 찍은 것**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **Java `split(d)` 와 2 / 5 행이 갈린다**(`"a,b,,"` 4 대 2 · `","` 2 대 **0**) · **Java `split(d, -1)` 과는 0 / 5**

**출력**

```text
===== javac -d o48j JSplit.java =====
(exit 0)
===== kotlinc -cp o48j grid48.kt -d o48g =====
(exit 0)
```

```text
===== java -cp o48g:o48j:kotlin-stdlib.jar Grid48Kt =====
input	delim	kt split(d)	java split(d)	kt split(Regex(d))	kt split(d, limit=2)	java split(d, -1)
"a,b,,"	","	4 ["a", "b", "", ""]	2 ["a", "b"]	4 ["a", "b", "", ""]	2 ["a", "b,,"]	4 ["a", "b", "", ""]
",a"	","	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]	2 ["", "a"]
""	","	1 [""]	1 [""]	1 [""]	1 [""]	1 [""]
","	","	2 ["", ""]	0 []	2 ["", ""]	2 ["", ""]	2 ["", ""]
"a<U+0020><U+0020>b"	"<U+0020>"	3 ["a", "", "b"]	3 ["a", "", "b"]	3 ["a", "", "b"]	2 ["a", "<U+0020>b"]	3 ["a", "", "b"]
rows where kt split(d) and java split(d, -1) differ: 0 / 5
rows where kt split(d) and java split(d) differ: 2 / 5
(exit 0)
```

**왜 그런가**

- ★★★ Java `split(regex)` 는 `limit` 0 으로 부른 것과 같고, 그 꼴은 **끝의 빈 조각을 지운다** — `","` 는 조각 둘이 **전부 빈 끝 조각**이라 `0 []` 이다. Kotlin 은 **지우지 않는다** — Java 의 `-1` 과 같다.
- ★★ 앞 빈 조각(`",a"`)과 빈 입력(`""` → `[""]`)은 두 언어가 같다.
- ★ `split(Regex(d))` 도 Kotlin 규칙(남긴다)이다 · `limit = 2` 는 나머지를 **마지막 조각에 통째로** 둔다.

### 2. ★★★ Java `trim` 과 **4 / 7**(U+3000 · U+00A0 · U+2003 은 Kotlin 만, U+0001 은 Java 만 깎는다) · Java `strip` 과 **1 / 7**(U+00A0)

**출력**

```text
===== kotlinc -cp o48j trim48.kt -d o48t =====
(exit 0)
===== java -cp o48t:o48j:kotlin-stdlib.jar Trim48Kt =====
pad	kt isWhitespace	java isWhitespace	kt trim()	java trim()	java strip()
U+0020	true	true	U+0061	U+0061	U+0061
U+0009	true	true	U+0061	U+0061	U+0061
U+3000	true	true	U+0061	U+3000 U+0061 U+3000	U+0061
U+00A0	true	false	U+0061	U+00A0 U+0061 U+00A0	U+00A0 U+0061 U+00A0
U+2003	true	true	U+0061	U+2003 U+0061 U+2003	U+0061
U+0001	false	false	U+0001 U+0061 U+0001	U+0061	U+0001 U+0061 U+0001
U+200B	false	false	U+200B U+0061 U+200B	U+200B U+0061 U+200B	U+200B U+0061 U+200B
rows where kt trim() and java strip() differ: 1 / 7
rows where kt trim() and java trim() differ: 4 / 7
(exit 0)
```

**왜 그런가**

- ★★★ Java `trim` 은 **`<= U+0020`** 이 공백이다 — 제어문자 U+0001 이 들어가고 ASCII 밖은 전부 빠진다.
- ★★★ Kotlin `trim` 은 JVM 에서 **`Character.isWhitespace || Character.isSpaceChar`** — 전각·em 공백(둘 다 `isWhitespace`)에 **U+00A0(`isSpaceChar` 만 참)** 까지 깎는다. `strip` 은 `isWhitespace` 만이라 U+00A0 을 남긴다.
- ★ U+200B 는 어느 판정에서도 공백이 아니다 — 셋 다 남긴다.

### 3. ★★ Java `split(".")` 은 **`0 []`** · `split("\\.")` 은 `[a, b]` · Kotlin `split(".")` 은 **`[a, b]`** · `split(Regex("."))` 는 **`4 [, , , ]`** · `split(Regex("\\."))` 는 `[a, b]`

**출력**

```text
===== javac -d o48d Dot48.java =====
(exit 0)
===== java -cp o48d Dot48 =====
java split(".")    0 []
java split("\\.")  2 [a, b]
(exit 0)
```

```text
===== kotlinc dot48.kt -d o48k =====
(exit 0)
===== java -cp o48k:kotlin-stdlib.jar Dot48Kt =====
kt split(".")         2 [a, b]
kt split(Regex("."))  4 [, , , ]
kt split(Regex("\\.")) 2 [a, b]
(exit 0)
```

**왜 그런가**

- ★★★ Java 의 인자는 **정규식** — `.` 은 아무 글자라 세 글자가 모두 구분자, 남은 네 빈 조각은 **끝 조각 규칙**으로 전부 지워진다.
- ★★★ Kotlin `split(String)` 의 인자는 **글자** — 점 하나로 자른다. 정규식을 원하면 `Regex` 를 **타입으로** 준다 — 그때도 끝 조각을 남겨 빈 문자열 넷이다.

### 4. ★★ `matches` **false** · `containsMatchIn` **true** · `find` **`12 2..3`** · `findAll` **`[12, 345]`** · `matchEntire` **null** · `7`\~`9`·`11` 은 **`host:kim`** · ★★★ **`10` 은 `host:lee`** · `12` 는 `a-b-c  -----`

**출력**

```text
===== kotlinc regex48.kt -d o48r =====
(exit 0)
===== java -cp o48r:kotlin-stdlib.jar Regex48Kt =====
1 matches(s)          false
2 containsMatchIn(s)  true
3 find(s)             12 2..3
4 findAll(s)          [12, 345]
5 matchEntire(s)      null
6 matches("345")      true
7 host:kim
8 host:kim
9 host:kim
10 host:lee
11 host:kim
12 a-b-c  -----
(exit 0)
```

**왜 그런가**

- ★★★ `matches` 는 **전체** 일치, `containsMatchIn`·`find` 는 **부분** 일치 — `"ab12cd345"` 전체는 숫자가 아니다.
- ★★★ `"$2:$1"` 의 `$` 뒤는 **숫자**라 Kotlin 템플릿이 아니다 — 글자 `$2:$1` 이 그대로 `replace` 에 간다(`7` = `8`).
- ★★★ `10` 의 `${user}` 는 **Kotlin 템플릿**이다 — 바깥의 `val user = "lee"` 로 먼저 바뀌어 치환 문자열이 `${host}:lee` 가 됐다. 에러도 경고도 없다.
- ★ `12` — `String.replace(String, String)` 은 **글자**, `replace(Regex, String)` 은 **정규식**(다섯 글자 전부 `-`).

### 5. ★ `[007]` · **`[12345]`**(안 자른다) · `[ab...]` · `[  ab]` · `[007]` · `IllegalArgumentException: Desired length -1 is less than zero.`

**출력**

```text
===== kotlinc pad48.kt -d o48p =====
(exit 0)
===== java -cp o48p:kotlin-stdlib.jar Pad48Kt =====
1 [007]
2 [12345]
3 [ab...]
4 [  ab]
5 [007]
6 IllegalArgumentException: Desired length -1 is less than zero.
(exit 0)
```

**왜 그런가**

- ★★ `padStart` 는 **최소 길이**다 — `length <= this.length` 면 원본을 돌려준다(2-summary (1)의 stdlib 발췌).
- ★ 기본 채움 글자는 공백(`4`) · 음수 길이는 `IllegalArgumentException`.

### 6. ★★ `cut` 에 **`StringsKt.split$default`** · `pad` 에 **`StringsKt.padStart(String, int, char)`** · `clean` 에 **`StringsKt.trim(CharSequence)`** · `Call48` 은 **`007 [a, b, , ] 4`**

**출력**

```text
===== kotlinc call48.kt -d o48c =====
(exit 0)
===== java -cp o48c:kotlin-stdlib.jar Call48Kt =====
[a, b, , ] [007] [x]
(exit 0)
===== javap -c -p o48c/Call48Kt.class | grep -E 'public static final|StringsKt' =====
  public static final java.util.List<java.lang.String> cut(java.lang.String);
      26: invokestatic  #28                 // Method kotlin/text/StringsKt.split$default:(Ljava/lang/CharSequence;[Ljava/lang/String;ZIILjava/lang/Object;)Ljava/util/List;
  public static final java.lang.String pad(java.lang.String);
      10: invokestatic  #35                 // Method kotlin/text/StringsKt.padStart:(Ljava/lang/String;IC)Ljava/lang/String;
  public static final java.lang.String clean(java.lang.String);
      10: invokestatic  #40                 // Method kotlin/text/StringsKt.trim:(Ljava/lang/CharSequence;)Ljava/lang/CharSequence;
  public static final void main();
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.text.StringsKt =====
public final class kotlin.text.StringsKt extends kotlin.text.StringsKt___StringsKt {
}
(exit 0)
===== javap -cp kotlin-stdlib.jar kotlin.text.StringsKt__StringsKt | grep -E '^public|^final|^class| (split|padStart|trim)\(java.lang.(CharSequence|String), (java.lang.String|int)' =====
class kotlin.text.StringsKt__StringsKt extends kotlin.text.StringsKt__StringsJVMKt {
  public static final java.lang.CharSequence padStart(java.lang.CharSequence, int, char);
  public static final java.lang.String padStart(java.lang.String, int, char);
  public static final java.util.List<java.lang.String> split(java.lang.CharSequence, java.lang.String[], boolean, int);
(exit 0)
===== javac -cp kotlin-stdlib.jar -d o48c Call48.java =====
(exit 0)
===== java -cp o48c:kotlin-stdlib.jar Call48 =====
007 [a, b, , ] 4
(exit 0)
```

**왜 그런가**

- ★★★ 확장 함수는 **수신자를 첫 인자로 받는 정적 메서드**다 — `String` 클래스는 그대로이고, `kotlin.text.StringsKt` 파사드에 함수가 있다.
- ★★ 기본값이 있는 인자(`ignoreCase`·`limit`)는 **`$default` 다리**가 채운다 — Java 에는 그 문법이 없어 `StringsKt.split(s, new String[] {","}, false, 0)` 처럼 **다 준다.** 결과가 4개인 것은 **Kotlin 규칙**이 Java 에서 불러도 그대로라서다.
- ★ `String.trim()` 은 `@InlineOnly` 라 클래스 파일에 없고 `trim(CharSequence)` 로 풀렸다.

### 7. **둘 다 계약이다** — Kotlin KDoc 「`the resulting list will end with an empty string`」 · Java javadoc 「`Trailing empty strings are therefore not included in the resulting array.`」

**왜 그런가**

- ★★★ 2-summary (1)의 발췌 — `Strings.kt` 의 `split` KDoc 과 JDK `String.java` 의 `split(String regex)` javadoc. 두 약속이 **반대**다.
- ★★ 그래서 어느 쪽도 「고쳐지지」 않는다 — Java 코드를 옮길 때 **부르는 쪽이** 맞춘다(`split(regex, -1)` ↔ Kotlin `split`).

### 8. **U+00A0** — Kotlin 은 `isSpaceChar` 를 더해 깎고, `strip` 은 `isWhitespace` 만이라 남긴다 · **`Character.isWhitespace(this) || Character.isSpaceChar(this)` 한 줄이 JVM 구현**이다

**왜 그런가**

- ★★ 2-summary (3) — Kotlin `trim` 의 선언은 `trim(Char::isWhitespace)`(계약), `isWhitespace` 의 **JVM `actual`** 이 두 JDK 판정의 합집합이다.
- ★ U+00A0 은 「줄바꿈 없는 공백」이라 JDK `isWhitespace` 가 일부러 뺀다 — 2번 격자의 `java isWhitespace` 열이 `false` 다.

### 9. `$` 뒤가 **숫자**면 템플릿이 아니고, **`{`** 면 템플릿이다 — 빠뜨리면 **같은 이름의 변수가 조용히 끼어든다**

**왜 그런가**

- ★★★ [02번 주제](../02-string-templates-and-raw-strings/) (1) — 「`$` 뒤에 식별자나 `{` 가 오지 않으면 그냥 글자다.」 `$1` 은 글자, `${host}` 는 식.
- ★★ 4번의 `10` — `"\${host}:${user}"` 에서 `user` 는 바깥 변수 `"lee"` 로 바뀌었다. 그룹 이름을 쓸 때는 **`\${…}`** 를 둘 다, 또는 람다 `replace` 로 템플릿 해석 자체를 피한다.

### 10. **Java → Kotlin 이면 열 수가 늘어난다**(끝 빈 칸이 살아난다) · **Kotlin → Java 면 줄어든다**(끝 빈 칸이 사라진다)

**왜 그런가**

- ★★ [Java 35번](../../../java/syntax/35-string/)은 `"a,b,,c,,".split(",")` 이 4개라 「마지막 열이 비면 검증을 통과해 버린다」고 적었다 — Kotlin 으로 옮기면 같은 줄에서 **끝 빈 칸이 살아나** 열 수가 늘고, 반대로 **검증이 실패**하기 시작한다(규칙은 1번 격자의 `"a,b,,"` 행 — 이 문서는 `"a,b,,c,,"` 자체를 **던지지 않았다**).
- ★ 옮긴 뒤 한 번 돌려 보는 것으로는 안 잡힌다 — **끝이 빈 줄**이 들어올 때만 갈린다.

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간을 찍지 않았다 | `split` 격자 · `trim` 격자 · 갈린 행 수 · 실행 출력 |
| | stdlib·JDK 소스 발췌(줄 번호째) · `javap` 의 명령·상수 풀 번호 |
| | 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 71개 · 동일 71 · 흔들린 칸 0 · ★고칠 것 0**(46\~49 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `JSplit.java` · `grid48.kt` | ★★★ Java 대비 `split` 격자 — 입력 5 × 꼴 5 | `javac` → `kotlinc -cp` → `java` (칸 수 검사·갈린 행 수는 프로그램이 센다) |
| `trim48.kt` | ★★ `trim`·`strip` 코드포인트 격자 — 글자 7 | `kotlinc -cp` → `java` |
| `Dot48.java` · `dot48.kt` | ★★ `split(".")` 한 쌍 | `javac` → `java` · `kotlinc` → `java` |
| `regex48.kt` | ★★ 전체/부분 일치 · `$` 그룹 참조 | `kotlinc` → `java` |
| `pad48.kt` | `padStart`·`padEnd` 경계 | `kotlinc` → `java` |
| `call48.kt` · `Call48.java` | ★★ `StringsKt` 정적 메서드 · Java 에서 부르기 | `kotlinc` → `javap -c -p`(전부 받은 뒤 `grep`) → `javac -cp` → `java` |
| `Strings.kt` · `CharJVM.kt` · `Regex.kt`(stdlib 소스 jar) · `String.java`(JDK `src.zip`) | `split`·`trim`·`padStart`·`isWhitespace`·`matches`·`replace` 계약 | `unzip` → `sed -n` |
| `form48.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — JVM `isWhitespace` 의 합집합 · `StringsKt` 파사드 구조 · `split$default` · 예외 문장 — 이 stdlib·컴파일러 판의 산출물이다.\
반면 **끝 빈 조각(양쪽 모두)** · **Java `trim` 의 `<= U+0020`** · **`matches` = 전체** · **`$` 뒤가 숫자면 글자** 는 **계약(KDoc·javadoc·언어 규칙)** 이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`"$1"` 은 템플릿과 부딪히지 않았다** — `$` 뒤가 숫자라 글자다. 부딪히는 것은 이름 있는 그룹 `${name}` 이고, 그쪽은 **같은 이름 변수가 있으면 조용히** 틀린다.
2. ★★ **U+3000 은 Java `strip()` 도 깎았다** — 「전각 공백은 Java 가 못 깎는다」는 `trim` 에만 맞다. `strip` 과 Kotlin 이 갈리는 글자는 **U+00A0** 이었다.
3. ★ **Java 에서 `",".split(",")` 이 `0 []`** — 「최소 한 개는 나온다」가 아니다. 조각이 전부 빈 끝 조각이면 배열이 빈다.
