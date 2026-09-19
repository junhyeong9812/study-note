# Java 13 (2019년 9월)

> 원본: `~/project/java-history/java/java-13.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/메서드 이름·코드블록 2개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> 「한눈에」의 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」, 교차 주 1개는 원문에 없는 보충이다.\
> 원문이 94줄이고 도식이 없어, 새 도식은 그리지 않았다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 텍스트 블록을 미리 선보이고(preview), switch 표현식에 `yield`를 도입해 언어 현대화를 이어간 버전.

이 편을 하나의 비유로 읽으면 **시범 운영 중인 노선을 한 번 더 손보면서, 그 옆에 새 시범 노선을 하나 더 연 일**이다.\
손본 쪽이 switch 표현식(2차)이고, 새로 연 쪽이 텍스트 블록(1차)이다.\
**Java 13의 리듬도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "한 릴리스에 큰 기능을 preview로 넣고, 다음 릴리스에서 개선하며, 그다음에 정식화한다".

본문 흐름에 쓰는 비유는 이 시범 노선 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 한 번 더 손본 시범 노선 | switch 표현식 2차 preview(JEP 354) — 원문 표현으로 `break <값>;`을 "`yield` 문으로 교체했다" |
| 새로 연 시범 노선 | 텍스트 블록 1차 preview(JEP 355) — 원문 표현으로 "처음 등장했다" |
| 시범을 켜는 신청서 | 원문 표현으로 두 기능 모두 `--enable-preview --release 13` 필요 |

초보자가 오해하기 쉬운 자리부터 짚어 두면 이렇다.

- **이 편의 텍스트 블록도 switch 표현식도 정식 기능이 아니다.**\
  원문이 두 절의 상태 줄에 적은 말이 각각 "**미리보기(Preview)**"와 "**미리보기(Preview, 2차)**"이고, 둘 다 `--enable-preview --release 13`이 필요하다.
- **둘은 정식이 되는 시점이 다르다.**\
  원문이 괄호로 적은 그대로다 — 텍스트 블록은 "이후 Java 14에서 2차 preview, Java 15에서 정식화", switch 표현식은 "Java 14에서 정식화"다.
- **`yield`는 `break <값>;`을 대체한 것이지, 화살표 문법을 대체한 것이 아니다.**\
  원문이 적는 그대로다 — "화살표(`->`) 케이스 내부에서 블록을 쓰거나, 전통적 `case ... :` 레이블에서 값을 반환할 때 `yield`를 사용한다".

## 릴리스 정보
- 정식 출시일: 2019년 9월 17일
- 개발 주체: Oracle (OpenJDK)
- LTS 여부: 아니오 (단기 지원)
- 포함 JEP 수: 5개

## 시대적 배경

*(「한눈에」의 시범 노선 비유가 가리키는 자리다.)*

Java 12에서 시작된 preview 기반 언어 진화가 본격적으로 굴러가는 릴리스다. Java 12에서 처음 선보인 switch 표현식이 커뮤니티 피드백을 반영해 2차 preview로 다듬어졌고, 오랫동안 자바 개발자들이 불편해하던 **여러 줄 문자열 리터럴**이 텍스트 블록이라는 형태로 처음 등장했다. "한 릴리스에 큰 기능을 preview로 넣고, 다음 릴리스에서 개선하며, 그다음에 정식화한다"는 리듬이 자리 잡았다.

> **preview(미리보기) 기능** — 아직 정식이 아니어서 켜야만 쓸 수 있고, 다음 릴리스에서 바뀔 수 있는 기능.\
> 예: 원문이 이 편의 리듬을 "preview로 넣고, 다음 릴리스에서 개선하며, 그다음에 정식화한다"로 적고, 이 편에 그 세 자리 중 앞의 둘이 함께 들어 있다(텍스트 블록 1차, switch 표현식 2차).

> **여러 줄 문자열 리터럴(multi-line string literal)** — 줄이 나뉜 문자열을 코드에 그 모양 그대로 적어 넣는 문법.\
> 예: 원문이 이것을 "오랫동안 자바 개발자들이 불편해하던" 것으로 적고, 이 편에서 그 형태로 등장한 것이 텍스트 블록이다.

## 주요 추가 기능

### 텍스트 블록 (JEP 355)
- 상태: **미리보기(Preview)** — `--enable-preview --release 13` 필요. (이후 Java 14에서 2차 preview, Java 15에서 정식화)
- `"""`로 둘러싸는 여러 줄 문자열 리터럴. HTML·JSON·SQL 등 여러 줄 문자열을 escape(`\n`, `\"`)와 연결(`+`) 없이 자연스럽게 작성할 수 있다. 닫는 구분자의 들여쓰기를 기준으로 공통 들여쓰기(incidental whitespace)가 자동 제거된다.

**언제 정식이 되나** — 원문이 첫 불릿 괄호에 적은 그대로다: 이후 Java 14에서 2차 preview, Java 15에서 정식화.

> **escape(이스케이프)** — 문자열 안에 그대로 적을 수 없는 문자를 `\`를 붙여 적는 표기.\
> 예: 원문이 이 절에서 예로 든 둘이 `\n`과 `\"`이고, 아래 "기존 방식" 코드의 줄 끝마다 붙은 `\n`이 그 첫째다.

> **공통 들여쓰기(incidental whitespace)** — 여러 줄에 똑같이 붙어 있어서 내용이 아닌 들여쓰기. 원문에 따르면 자동으로 제거된다.\
> 예: 원문이 그 제거의 기준으로 적은 것이 "닫는 구분자의 들여쓰기"다 — 아래 코드에서 각 블록을 닫는 `"""`가 놓인 자리가 그 기준이다.

```java
// 기존 방식: escape와 연결로 가독성 저하
String html = "<html>\n" +
              "    <body>\n" +
              "        <p>Hello, Java 13</p>\n" +
              "    </body>\n" +
              "</html>\n";

// Java 13 텍스트 블록 (preview)
String html = """
        <html>
            <body>
                <p>Hello, Java 13</p>
            </body>
        </html>
        """;

String json = """
        {
            "name": "Java",
            "version": 13
        }
        """;

String query = """
        SELECT id, name
        FROM users
        WHERE active = true
        """;
```

위 한 블록 안의 코드들은 같은 HTML을 두 방식으로 적은 것으로 시작한다.\
앞쪽에서 줄마다 붙던 `\n`과 줄 사이를 잇던 `+`가 뒤쪽에서는 사라지고, `"""`와 `"""` 사이에 내용이 그 모양 그대로 들어간다.\
원문이 두 코드 첫 줄 주석에 붙인 이름이 각각 "기존 방식: escape와 연결로 가독성 저하"와 "Java 13 텍스트 블록 (preview)"이다.\
원문이 이어서 보여 주는 `json`과 `query`가 절 첫머리에서 든 쓰임(HTML·JSON·SQL) 가운데 뒤의 둘이다.

### switch 표현식 — 2차 미리보기 (JEP 354)
- 상태: **미리보기(Preview, 2차)** — `--enable-preview --release 13` 필요. (Java 14에서 정식화)
- Java 12의 1차 preview에서 값을 돌려줄 때 쓰던 `break <값>;` 문법을 **`yield` 문**으로 교체했다. 화살표(`->`) 케이스 내부에서 블록을 쓰거나, 전통적 `case ... :` 레이블에서 값을 반환할 때 `yield`를 사용한다.

> **`yield`** — switch 표현식의 블록 안에서 "이 블록의 값은 이것이다"를 적는 문장.\
> 예: 아래 첫 코드의 `default` 블록이 `int len = ...`으로 계산한 뒤 `yield len;`으로 값을 내놓는다 — 원문이 그 두 줄에 단 주석이 "블록 안에서 계산 후" / "yield로 값 반환"이다.

```java
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    default -> {
        int len = day.toString().length();   // 블록 안에서 계산 후
        yield len;                            // yield로 값 반환
    }
};

// 전통적 콜론 레이블에서도 yield 사용 가능
int result = switch (code) {
    case 1: yield 100;
    case 2: yield 200;
    default: yield 0;
};
```

위 블록은 원문이 말한 `yield`의 두 자리를 차례로 보여 준다.\
앞쪽 `numLetters`가 "화살표(`->`) 케이스 내부에서 블록을 쓰"는 자리이고, 뒤쪽 `result`가 "전통적 `case ... :` 레이블에서 값을 반환"하는 자리다 — 원문이 뒤쪽 코드 주석에 적은 말이 "전통적 콜론 레이블에서도 yield 사용 가능"이다.

> **재서술자 주:** 이 절의 앞뒤는 이 편 밖에 있다. 같은 시리즈 `java-12.md`가 1차 preview(JEP 325)와 그 시절의 `break <값>;` 문법을 적고, `java-14.md`가 "12·13의 두 차례 preview를 거쳐 정식 기능으로 확정됐다"(JEP 361)고 적는다.

### ZGC: 미사용 메모리 OS 반환 (JEP 351)
- 상태: 실험적(ZGC 자체가 이 시점에 실험적)
- ZGC가 그동안 사용하지 않는 힙 메모리를 OS에 돌려주지 않던 한계를 개선했다. 일정 시간 유휴 상태의 힙 메모리를 OS로 반환해, 컨테이너·클라우드 환경에서 메모리 효율을 높인다(`-XX:ZUncommitDelay`로 지연 시간 조정).

**왜 이것이 나왔나** — 원문이 적은 그대로다. ZGC가 "사용하지 않는 힙 메모리를 OS에 돌려주지 않던 한계"가 고치려던 문제다.

> **유휴(idle) 상태** — 쓰이지 않고 놀고 있는 상태.\
> 예: 원문이 반환 대상으로 적은 것이 "일정 시간 유휴 상태의 힙 메모리"이고, 그 "일정 시간"을 조정하는 옵션이 `-XX:ZUncommitDelay`다.

### 레거시 소켓 API 재구현 (JEP 353)
- 상태: 정식(내부 구현 교체)
- JDK 1.0 시절부터 이어져 유지보수가 어렵던 `java.net.Socket`/`java.net.ServerSocket`의 내부 구현을, 더 단순하고 현대적이며 디버깅하기 쉬운 새 구현(`NioSocketImpl`)으로 교체했다. 이후 Project Loom의 가상 스레드 친화적 I/O를 위한 기반이기도 하다.

**왜 이것이 나왔나** — 원문이 적은 그대로다. `java.net.Socket`/`java.net.ServerSocket`의 내부 구현이 "JDK 1.0 시절부터 이어져 유지보수가 어렵던" 것이었다.

> **내부 구현 교체** — 밖에서 쓰는 이름과 사용법은 그대로 두고, 그 속을 다른 코드로 바꾸는 것.\
> 예: 원문이 상태 줄에 적은 말이 "정식(내부 구현 교체)"이고, 바뀐 쪽의 새 이름이 `NioSocketImpl`이다.

## 그 외 변경 / API 추가
- **JEP 350 — 동적 CDS 아카이브(Dynamic CDS Archives)**: 애플리케이션 실행이 끝나는 시점에 로드된 클래스들을 동적으로 아카이브할 수 있게 해, AppCDS 사용성을 크게 개선(사전 클래스 리스트 작성 불필요).
- **API**: `String`에 텍스트 블록 지원용 메서드 `stripIndent()`, `translateEscapes()`, `formatted(Object...)` 추가(preview 연계). `FileSystems.newFileSystem(Path, Map)` 추가. 유니코드 12.1 지원.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 불릿은 원문 한 문단을 나눠 적은 것이다.)*

- Java 13은 단일한 "킬러 기능"보다 **언어를 점진적으로 다듬어 가는 과정**을 잘 보여주는 릴리스다.
- 텍스트 블록은 자바 개발자들이 수십 년간 바라던 기능으로, preview 단계에서부터 큰 환영을 받았고 Java 15에서 정식화되어 오늘날 SQL/JSON/HTML 작성의 표준이 되었다.
- switch 표현식의 `yield` 도입은 1차 preview의 어색했던 `break <값>` 문법을 깔끔하게 정리해 Java 14 정식화의 길을 닦았다.
- ZGC 메모리 반환과 소켓 API 재구현은 클라우드 시대와 이후 가상 스레드(Project Loom)를 향한 준비 작업이라는 의미가 있다.

## 용어 풀이

- **preview(미리보기) 기능** — 아직 정식이 아니어서 켜야만 쓸 수 있고, 다음 릴리스에서 바뀔 수 있는 기능. 이 편의 두 언어 기능이 모두 그 상태다.
- **`--enable-preview --release 13`** — 이 편의 preview 기능을 켜는 데 원문이 적은 옵션.
- **여러 줄 문자열 리터럴(multi-line string literal)** — 줄이 나뉜 문자열을 코드에 그 모양 그대로 적는 문법. 이 편에서 텍스트 블록이라는 형태로 처음 등장했다.
- **텍스트 블록(text block)** — `"""`로 둘러싸는 여러 줄 문자열 리터럴. 원문이 든 쓰임이 HTML·JSON·SQL이다.
- **escape(이스케이프)** — 그대로 적을 수 없는 문자를 `\`를 붙여 적는 표기. 원문이 든 예가 `\n`과 `\"`다.
- **공통 들여쓰기(incidental whitespace)** — 여러 줄에 똑같이 붙은, 내용이 아닌 들여쓰기. 원문에 따르면 닫는 구분자의 들여쓰기를 기준으로 자동 제거된다.
- **`yield`** — switch 표현식의 블록에서 값을 내놓는 문장. 1차 preview의 `break <값>;`을 대체했다.
- **유휴(idle) 상태** — 쓰이지 않고 놀고 있는 상태. ZGC가 반환하는 대상이 "일정 시간 유휴 상태의 힙 메모리"다.
- **내부 구현 교체** — 밖에서 쓰는 이름과 사용법은 그대로 두고 속을 바꾸는 것. 이 편에서 소켓 API가 `NioSocketImpl`로 바뀌었다.

## 참고 출처
- [JDK 13 — OpenJDK Project](https://openjdk.org/projects/jdk/13/)
- [JEP 355: Text Blocks (Preview)](https://openjdk.org/jeps/355)
- [JEP 354: Switch Expressions (Second Preview)](https://openjdk.org/jeps/354)
- [The arrival of Java 13! — Oracle Blog](https://blogs.oracle.com/java-platform-group/the-arrival-of-java-13)
- [Significant Changes in JDK 13 Release — Oracle Docs](https://docs.oracle.com/en/java/javase/24/migrate/significant-changes-jdk-13.html)
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
