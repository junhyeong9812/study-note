# Java 18 (2022년 3월)

> 원본: `~/project/java-history/java/java-18.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·코드블록 5개(java 4 · bash 1)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> ASCII 도식 1개와 「한눈에」의 콘센트 규격 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> UTF-8을 기본 문자셋으로 표준화하고, 의존성 없이 쓸 수 있는 간단한 웹서버와 JavaDoc 코드 스니펫 태그를 도입한 비-LTS 릴리스. 동시에 Loom/Panama/Amber 프로젝트의 프리뷰·인큐베이터 기능들이 다음 단계로 진행되었다.

이 편의 대표 변경을 읽는 비유는 **방마다 콘센트 규격이 다르던 집을 한 규격으로 통일한 날**이다.\
원문이 「주요 추가 기능」에서 통일 이전 상태를 이렇게 적는다 — "기존에는 `file.encoding`이 플랫폼에 따라 달라져(Windows는 흔히 windows-1252/MS949, Linux는 UTF-8), 같은 코드가 환경마다 다르게 동작하는 고질적 버그의 원인이었다."

| 비유 | 실체 |
|---|---|
| 방마다 다르던 콘센트 규격 | 플랫폼마다 달랐던 `file.encoding` — 원문 표현으로 "Windows는 흔히 windows-1252/MS949, Linux는 UTF-8" |
| 통일된 하나의 규격 | UTF-8 — 원문 표현으로 "운영체제·로케일과 무관하게 UTF-8로 고정" |
| 옛 기기를 위해 남겨 둔 어댑터 | `-Dfile.encoding=COMPAT` — 원문 표현으로 "과거 동작이 필요하면 … 되돌릴 수 있다" |

### 이 편에서 미리보기인가 정식인가

이 편에서 흔한 오해는 "18에서 switch 패턴 매칭을 쓸 수 있다"이다. **이 편에서는 2차 프리뷰다.**\
원문이 절 제목·괄호에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(18)에서의 상태 — 원문 절 제목 표기(★는 원문 표기가 아니라 재서술자 추론이거나 다른 편 원문에서 온 것) | 정식이 된 편 |
|---|---|---|
| UTF-8을 기본 문자셋으로 (JEP 400) | **Final/정식** | 18 — 이 편이다 |
| 간단한 웹서버 jwebserver (JEP 408) | **Final/정식** | 18 — 이 편이다 |
| JavaDoc 코드 스니펫 @snippet (JEP 413) | **Final/정식** | 18 — 이 편이다 |
| Pattern Matching for switch (JEP 420) | **Second Preview/2차 프리뷰** | 21 (JEP 441) — 원문이 "정식화는 Java 21(JEP 441)에서 이루어진다"고 직접 적는다 |
| Foreign Function & Memory API (JEP 419) | **Second Incubator/2차 인큐베이터** | 22 (JEP 454) — 출처: 원문 `java-20.md`·`java-22.md`. 이 편 다음 단계는 19의 프리뷰(JEP 424)이고, 원문이 그것을 직접 적는다 |
| Vector API (JEP 417) | **Third Incubator/3차 인큐베이터** | 이 편 뒤로도 인큐베이터가 이어진다 — 출처: 원문 `java-19.md`(4차)·`java-20.md`(5차) |
| 코어 리플렉션 재구현 (JEP 416) · 인터넷 주소 해석 SPI (JEP 418) | ★정식(그 외 변경) — 원문 「그 외 변경」 불릿에 상태 표기가 없다. 재서술자 추론이다 | 18 — 이 편이다 |

> **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문은 이 방식을 "**프리뷰(preview)와 인큐베이터(incubator) 단계를 거쳐 점진적으로 성숙시키는** 개발 방식"이라 적는다.\
> 예: 이 편의 switch 패턴 매칭 코드 첫 줄에 원문이 단 주석이 "--enable-preview 필요"다.

> **비-LTS 릴리스** — 장기 지원 대상이 아닌 6개월 주기 버전. 원문 「릴리스 정보」의 표기가 "아니오 (단기 지원, 6개월 주기 릴리스)"다.\
> 예: 원문은 18을 "Java 17(2021년 9월)이 LTS로 출시된 직후의 첫 번째 비-LTS 릴리스"라 적는다.

## 릴리스 정보
- 정식 출시일: 2022년 3월 22일
- LTS 여부: 아니오 (단기 지원, 6개월 주기 릴리스)
- 포함 JEP 수: 9개

## 시대적 배경
Java 17(2021년 9월)이 LTS로 출시된 직후의 첫 번째 비-LTS 릴리스다.\
6개월 단위 릴리스 케이던스가 안정적으로 자리잡으면서, 거대한 신기능을 한 번에 터뜨리기보다 **프리뷰(preview)와 인큐베이터(incubator) 단계를 거쳐 점진적으로 성숙시키는** 개발 방식이 확립된 시기다.

당시 OpenJDK는 세 개의 큰 프로젝트를 동시에 진행하고 있었다.
- **Project Amber**: 언어 생산성 개선 (패턴 매칭, 레코드 등)
- **Project Panama**: 네이티브 코드/메모리 상호운용 (Foreign Function & Memory API, Vector API)
- **Project Loom**: 경량 동시성 (가상 스레드, 구조적 동시성) — 18에서는 아직 직접적인 기능이 들어오지 않았지만, 다음 릴리스를 향한 준비가 한창이었다.

Java 18은 이 중 Amber와 Panama의 진행, 그리고 플랫폼 기본값 정비(UTF-8)와 개발 편의 기능(웹서버, 스니펫)에 초점을 맞췄다.

> **케이던스(cadence)** — 릴리스가 나오는 일정한 주기. 원문 표현으로 이 시기에 "6개월 단위 릴리스 케이던스가 안정적으로 자리잡"았다.\
> 예: 원문이 이 편을 놓은 자리가 "Java 17(2021년 9월)이 LTS로 출시된 직후"이고, 이 편의 출시일이 2022년 3월 22일이다.

> **Project Amber / Panama / Loom** — OpenJDK가 나눠 굴리던 큰 작업 갈래의 이름. 원문이 각각에 붙인 설명이 위 세 불릿이다.\
> 예: 원문이 이 편의 초점으로 든 것은 그중 Amber와 Panama이고, Loom은 "18에서는 아직 직접적인 기능이 들어오지 않았"다고 적는다.

## 주요 추가 기능

### UTF-8을 기본 문자셋으로 (JEP 400, Final/정식)
- 표준 Java API들이 사용하는 **기본 문자셋(default charset)을 운영체제·로케일과 무관하게 UTF-8로 고정**했다.
- 이제 `Charset.defaultCharset()`이 기본적으로 UTF-8을 반환한다. 콘솔 입출력 등은 여전히 `Console`의 별도 인코딩을 따를 수 있다.
- 과거 동작이 필요하면 `-Dfile.encoding=COMPAT`로 되돌릴 수 있다.

**왜 UTF-8 기본화가 나왔나** — 원문이 같은 절에 적어 둔 그대로다: "기존에는 `file.encoding`이 플랫폼에 따라 달라져(Windows는 흔히 windows-1252/MS949, Linux는 UTF-8), 같은 코드가 환경마다 다르게 동작하는 고질적 버그의 원인이었다."

```text
[18 이전]                                 [18부터 — JEP 400]

  같은 코드                               같은 코드
    Windows : 흔히 windows-1252/MS949     운영체제·로케일과 무관하게
    Linux   : UTF-8                       UTF-8로 고정

  "같은 코드가 환경마다                   Charset.defaultCharset()이
   다르게 동작하는 고질적 버그의 원인"    기본적으로 UTF-8을 반환
```

- 두 칸의 대립축은 원문이 이 절에서 세운 것 그대로다 — 왼쪽이 "기존에는", 오른쪽이 "이제"다.
- 칸 안의 글자는 원문 문장에서 따온 것이다 — "Windows는 흔히 windows-1252/MS949, Linux는 UTF-8" · "운영체제·로케일과 무관하게 … UTF-8로 고정" · "같은 코드가 환경마다 다르게 동작하는 고질적 버그의 원인" · "`Charset.defaultCharset()`이 기본적으로 UTF-8을 반환". 「같은 코드」와 「Windows :」·「Linux :」는 배치를 위해 붙인 이름표다.
- 오른쪽 칸에도 두 가지가 더 붙는다 — 예외 하나는 원문이 바로 적어 둔 "콘솔 입출력 등은 여전히 `Console`의 별도 인코딩을 따를 수 있다"이고, 되돌리기 옵션 하나가 `-Dfile.encoding=COMPAT`다(규칙의 예외가 아니라 "과거 동작이 필요하면 … 되돌릴 수 있다"는 스위치다).

> **문자셋(charset) / 기본 문자셋(default charset)** — 글자를 바이트로 바꾸는 규칙표 / 그 규칙을 따로 지정하지 않았을 때 쓰이는 것.\
> 예: 원문이 아래 코드 주석에서 이 변경의 대상으로 든 것이 "charset을 명시하지 않는 API"다.

```java
// JEP 400의 영향을 받는 것은 default charset에 의존하던 API들이다.
import java.io.*;

// new String(byte[]), FileReader/FileWriter, InputStreamReader, PrintStream 등
// charset을 명시하지 않는 API가 18부터 일관되게 UTF-8을 사용한다.
String text = new String(bytes);          // 18 이전: 플랫폼 charset → 18부터: UTF-8
try (var reader = new FileReader("note.txt")) { /* UTF-8로 읽음 */ }
System.out.println(java.nio.charset.Charset.defaultCharset()); // UTF-8

// 참고: Files.readString/writeString(charset 미지정)은 JEP 400 이전(JDK 11)부터
//       이미 UTF-8 고정이라 이번 변경 대상이 아니다.
```

### 간단한 웹서버 — jwebserver (JEP 408, Final/정식)
- 정적 파일을 서빙하는 **최소 기능 HTTP/1.1 서버**를 JDK에 내장했다. 프로토타이핑, 임시 테스트, 교육 용도가 목적이다.
- 커맨드라인 도구 `jwebserver`와 프로그래밍 API(`com.sun.net.httpserver.SimpleFileServer`)를 모두 제공한다.
- 기본은 현재 디렉토리를 `127.0.0.1:8000`에 읽기 전용으로 서빙한다.

**무엇은 못 하나** — 원문이 같은 절에 적어 둔 그대로다: "**GET과 HEAD 요청만 처리**하며, 그 외 메서드는 405(Method Not Allowed)/501(Not Implemented)로 응답한다. CGI나 동적 콘텐츠는 지원하지 않는다."

> **정적 파일 / 동적 콘텐츠** — 있는 파일을 그대로 내주는 것 / 요청마다 서버가 만들어 내는 것. 원문은 이 서버를 앞쪽으로만 한정하고, 뒤쪽은 "지원하지 않는다"고 적는다.\
> 예: 원문이 이 도구의 용도로 든 것이 "프로토타이핑, 임시 테스트, 교육 용도"다.

```bash
# 현재 디렉토리를 즉시 서빙
$ jwebserver
# 포트/바인드 주소/디렉토리 지정
$ jwebserver -p 9000 -b 0.0.0.0 -d /var/www
```

```java
// 프로그래밍 방식
import com.sun.net.httpserver.SimpleFileServer;
import java.net.InetSocketAddress;
import java.nio.file.Path;

var server = SimpleFileServer.createFileServer(
        new InetSocketAddress(8000),
        Path.of("/var/www"),
        SimpleFileServer.OutputLevel.VERBOSE);
server.start();
```

### JavaDoc 코드 스니펫 — @snippet (JEP 413, Final/정식)
- JavaDoc 표준 Doclet에 **`@snippet` 태그**를 추가하여, API 문서에 들어가는 예제 코드를 더 안전하고 검증 가능하게 작성하도록 했다.
- 인라인 스니펫과 외부 파일 참조 스니펫을 모두 지원하며, 영역 강조·정규식 하이라이팅·링크 마크업이 가능하다.

**왜 @snippet이 나왔나** — 원문이 같은 절에 적어 둔 그대로다: "기존 `<pre>{@code ...}</pre>` 방식의 한계(컴파일·검증 불가, 하이라이팅·링크 부족)를 보완한다."

> **JavaDoc / Doclet** — 소스의 주석에서 API 문서를 뽑아내는 도구 / 그 도구가 문서를 만들어 내는 부분. 원문 표현으로 `@snippet`은 "JavaDoc 표준 Doclet에" 추가된 태그다.\
> 예: 아래 주석의 `{@snippet : … }` 안에 든 두 줄이 그 예제 코드다.

```java
/**
 * 사용 예시:
 * {@snippet :
 *   var list = List.of(1, 2, 3);
 *   list.forEach(System.out::println);
 * }
 */
public void example() { }
```

### Pattern Matching for switch (JEP 420, Second Preview/2차 프리뷰)
- Java 17의 1차 프리뷰(JEP 406)에 이어 **두 번째 프리뷰**다. switch에서 타입 패턴과 가드를 사용할 수 있게 하는 기능을 다듬는 단계다.
- 18에서의 주요 변경: **가드 패턴 표기 정련**(이후 19에서 `when` 키워드로 발전), `null`·전체성(exhaustiveness) 처리 개선, 패턴의 지배 관계(dominance) 검사 강화.
- 정식화는 Java 21(JEP 441)에서 이루어진다.

> **지배 관계(dominance)** — 앞에 쓴 `case`가 뒤의 `case`를 가려 버리는 관계. 원문은 이 편에서 그 "검사 강화"가 있었다고 적기만 한다.\
> 예: 아래 코드에서 `case Integer i && i > 0`이 `case Integer i`보다 앞에 온다 — 원문이 든 세 가지 변경 가운데 이 항목이 그 순서를 따지는 자리다.

```java
// --enable-preview 필요
static String describe(Object obj) {
    return switch (obj) {
        case Integer i && i > 0 -> "양의 정수: " + i;
        case Integer i           -> "0 이하 정수: " + i;
        case String s            -> "문자열: " + s;
        case null                -> "널";
        default                  -> "기타";
    };
}
```

### Foreign Function & Memory API (JEP 419, Second Incubator/2차 인큐베이터)
- 네이티브 라이브러리 함수 호출과 JVM 힙 밖 메모리 접근을 안전하게 다루는 API의 **두 번째 인큐베이터**다(`jdk.incubator.foreign`).
- 기존 JNI를 대체하기 위한 Project Panama의 핵심이다. 18에서는 API 사용성과 안전성을 다듬었다.
- 이후 19에서 `java.lang.foreign` 정식 패키지의 **프리뷰**(JEP 424)로 승격된다.

> **네이티브 라이브러리 / 힙 밖 메모리 / JNI** — JVM 밖의 기계어 라이브러리 / JVM이 관리하는 영역 바깥의 메모리 / 그 둘을 다루던 기존 방식.\
> 예: 원문이 이 API의 자리를 "기존 JNI를 대체하기 위한 Project Panama의 핵심"이라 적는다. 이 편에서는 아직 인큐베이터이고, 패키지 이름도 `jdk.incubator.foreign`이다.

### Vector API (JEP 417, Third Incubator/3차 인큐베이터)
- SIMD 벡터 연산을 하드웨어 벡터 명령으로 안정적으로 컴파일하는 API의 **세 번째 인큐베이터**다(`jdk.incubator.vector`).
- 머신러닝·암호·금융 등 수치 연산 가속이 목적이다. 18에서는 ARM Scalable Vector Extension 등 추가 아키텍처 대응과 성능 개선이 이루어졌다.

> **SIMD** — 하나의 명령으로 여러 값을 한꺼번에 처리하는 CPU 기능(Single Instruction Multiple Data). 원문은 이 API를 그 연산을 "하드웨어 벡터 명령으로 안정적으로 컴파일하는 API"라 적는다.\
> 예: 원문이 쓰임새로 든 분야가 "머신러닝·암호·금융 등 수치 연산 가속"이다.

## 그 외 변경
- **JEP 416: 코어 리플렉션을 Method Handle로 재구현** — `java.lang.reflect.Method`/`Constructor`/`Field`의 내부 구현을 `java.lang.invoke` MethodHandle 기반으로 교체했다. 동작은 동일하되 유지보수성과 일관성이 개선되었다.
- **JEP 418: 인터넷 주소 해석 SPI** — 호스트명·주소 해석에 플랫폼 내장 리졸버 대신 커스텀 리졸버를 끼울 수 있는 서비스 제공자 인터페이스(SPI)를 도입했다. 비동기 DNS, 테스트용 가짜 리졸버 등을 구현할 수 있다.
- `finalize()` 메서드의 deprecation 진행, 작은 라이브러리 API 추가 등 점진적 정리가 이어졌다.

> **SPI(서비스 제공자 인터페이스)** — 정해진 자리에 내가 만든 구현을 끼워 넣을 수 있게 열어 둔 인터페이스. 원문이 JEP 418의 구현 예로 든 것이 "비동기 DNS, 테스트용 가짜 리졸버"다.\
> 예: 원문 표현으로 이 편에서 바꿔 끼울 수 있게 된 것이 "플랫폼 내장 리졸버"다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문의 것이다.)*

Java 18 자체는 "조용한" 릴리스에 가깝지만, 그 안에 담긴 변화는 실무에 의미가 컸다.
- **UTF-8 기본화**(JEP 400)는 수년간 개발자를 괴롭히던 "환경마다 다른 인코딩" 문제를 플랫폼 차원에서 종결지은 결정적 변경이다.
- **jwebserver**는 "정적 파일 잠깐 서빙"에 외부 도구를 깔 필요를 없앴다.
- Panama(FFM, Vector)와 Amber(switch 패턴)의 단계적 진행은 Java 19~21에서 폭발할 가상 스레드·패턴 매칭·네이티브 상호운용의 토대를 다졌다.

## 용어 풀이

- **프리뷰(preview) / 인큐베이터(incubator)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문은 이 방식을 "프리뷰(preview)와 인큐베이터(incubator) 단계를 거쳐 점진적으로 성숙시키는 개발 방식"이라 적는다.
- **비-LTS 릴리스** — 장기 지원 대상이 아닌 6개월 주기 버전. 18의 표기는 "아니오 (단기 지원, 6개월 주기 릴리스)"다.
- **케이던스(cadence)** — 릴리스가 나오는 일정한 주기. 원문 표현으로 이 시기에 "6개월 단위 릴리스 케이던스가 안정적으로 자리잡"았다.
- **Project Amber / Panama / Loom** — OpenJDK가 나눠 굴리던 큰 작업 갈래. 원문 설명으로 각각 언어 생산성 개선 / 네이티브 코드·메모리 상호운용 / 경량 동시성이다.
- **문자셋(charset) / 기본 문자셋(default charset)** — 글자를 바이트로 바꾸는 규칙표 / 따로 지정하지 않았을 때 쓰이는 것. 이 편에서 후자가 UTF-8로 고정됐다.
- **정적 파일 / 동적 콘텐츠** — 있는 파일을 그대로 내주는 것 / 요청마다 서버가 만들어 내는 것. jwebserver는 앞쪽만 다루고, 뒤쪽은 원문 표현으로 "지원하지 않는다".
- **JavaDoc / Doclet** — 소스 주석에서 API 문서를 뽑아내는 도구 / 그 도구가 문서를 만들어 내는 부분. `@snippet`은 "JavaDoc 표준 Doclet에" 추가된 태그다.
- **타입 패턴 / 가드** — `case` 자리에 타입을 적어 맞춰 보는 것 / 그 뒤에 조건을 하나 더 거는 것. 이 편에서 switch 패턴 매칭은 아직 2차 프리뷰다.
- **전체성(exhaustiveness) / 지배 관계(dominance)** — 분기가 모든 경우를 다뤘는지 / 앞의 `case`가 뒤의 `case`를 가려 버리는지. 원문은 이 편에서 둘 다 "개선"·"검사 강화"가 있었다고 적는다.
- **네이티브 라이브러리 / 힙 밖 메모리 / JNI** — JVM 밖의 기계어 라이브러리 / JVM이 관리하는 영역 바깥의 메모리 / 그 둘을 다루던 기존 방식. 원문은 FFM API를 "기존 JNI를 대체하기 위한 Project Panama의 핵심"이라 적는다.
- **SIMD** — 하나의 명령으로 여러 값을 한꺼번에 처리하는 CPU 기능. Vector API가 그 명령으로 컴파일되는 것을 목표로 한다.
- **SPI(서비스 제공자 인터페이스)** — 정해진 자리에 내 구현을 끼워 넣을 수 있게 열어 둔 인터페이스. JEP 418이 주소 해석에 그것을 도입했다.

## 참고 출처
- [JEP 400: UTF-8 by Default](https://openjdk.org/jeps/400)
- [JEP 408: Simple Web Server](https://openjdk.org/jeps/408)
- [JEP 413: Code Snippets in Java API Documentation](https://openjdk.org/jeps/413)
- [JEP 420: Pattern Matching for switch (Second Preview)](https://openjdk.org/jeps/420)
- [JEP 419: Foreign Function & Memory API (Second Incubator)](https://openjdk.org/jeps/419)
- [JEP 417: Vector API (Third Incubator)](https://openjdk.org/jeps/417)
- [JEP 416: Reimplement Core Reflection with Method Handles](https://openjdk.org/jeps/416)
- [JEP 418: Internet-Address Resolution SPI](https://openjdk.org/jeps/418)
- [OpenJDK JDK 18 프로젝트 페이지](https://openjdk.org/projects/jdk/18/)
- [InfoQ: Oracle Releases Java 18](https://www.infoq.com/news/2022/03/java-18-so-far/)
