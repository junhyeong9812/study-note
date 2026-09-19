# JDK 1.4 / J2SE 1.4 (코드네임 Merlin, 2002년 2월)

> 원본: `~/project/java-history/java/jdk-1.4.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR 번호·클래스/패키지 이름·코드블록 6개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개와 「한눈에」의 공구함 비유·대응표, 용어 블록의 「예:」, 「용어 풀이」, 다른 편을 가리키는 교차 주 1개, 재서술자 주 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 언어와 라이브러리 양면에서 풍성한 기능을 더한 버전. `assert` 키워드가 추가되었고, NIO·정규식·로깅·XML 파서·예외 체이닝 등 오늘날 자바 개발자가 매일 쓰는 API가 표준에 대거 편입되었다.

이 편을 하나의 비유로 읽으면 **일이 생길 때마다 옆집에서 빌려 오던 공구를, 기본 공구함 안에 아예 넣어 둔 일**이다.\
빌려 쓰는 동안에도 일은 됐지만, 공구함에 들어오면 빌리러 갈 필요가 없어진다.

**1.4도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "고성능 I/O, 표준 로깅, XML 처리, 정규식 같은 기능을 그동안 서드파티 라이브러리(예: Apache Log4j, Jakarta ORO, JDOM)에 의존해 왔다. 1.4는 이런 사실상 표준(de facto standard)들을 플랫폼 자체에 흡수하여, 외부 의존 없이도 견고한 애플리케이션을 만들 수 있게 했다".

본문 흐름에 쓰는 비유는 이 공구함 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 옆집에서 그때그때 빌려 오는 공구 | 원문 표현으로 "서드파티 라이브러리(예: Apache Log4j, Jakarta ORO, JDOM)" |
| 기본 공구함에 처음부터 들어 있는 것 | 원문 표현으로 "사실상 표준(de facto standard)들을 플랫폼 자체에 흡수하여" |
| 빌리러 가지 않아도 되는 상태 | 원문 표현으로 "외부 의존 없이도 견고한 애플리케이션을 만들 수 있게 했다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **`assert`가 자바에 추가된 첫 키워드는 아니다.**\
  원문이 그 자리에서 직접 못 박는다 — "언어에 추가된 첫 키워드는 아니다 — `strictfp`가 이미 J2SE 1.2에서 추가된 바 있다".
- **`assert`는 그냥 켜져 있지 않다.**\
  원문 표현으로 "기본적으로 비활성화되어 있으며 `-ea` 옵션으로 켠다(운영 성능에 영향 없음)".
- **Java Web Start가 이 버전에서 만들어진 것은 아니다.**\
  원문이 그 자리에서 직접 적는다 — "1.4에서 처음 만들어진 것이 아니라 1.4에서 플랫폼에 포함된 것".

## 릴리스 정보
- 정식 출시일: 2002년 2월 6일
- 개발 주체: Sun Microsystems
- 공식 명칭: J2SE 1.4 (Java 2 Platform, Standard Edition v1.4)
- 코드네임: Merlin (멀린, 쇠황조롱이)
- 참고: JCP(Java Community Process)를 거쳐 개발된 최초의 자바 플랫폼 릴리스(JSR 59).

> **재서술자 주:** 위 다섯째 불릿의 "JCP"는 원문 파일에서 라틴 문자 `C`·`P`가 아니라 겉모습이 같은 키릴 문자로 적혀 있다(`JСР`). 원문 자신이 같은 괄호에서 "Java Community Process"로 풀어 적고 있으므로 `JCP`의 표기 오류로 보이며, 이 문서에서는 라틴 문자로 적었다.

> **JCP(Java Community Process)** — 자바 플랫폼에 무엇을 넣을지 커뮤니티가 모여 표준으로 정하는 절차. 그렇게 정해진 각 건에 JSR 번호가 붙는다.\
> 예: 원문은 이 편을 "JCP를 거쳐 개발된 최초의 자바 플랫폼 릴리스(JSR 59)"라 적는다.

## 시대적 배경

J2SE 1.3이 성능·안정성을 다졌다면, 1.4는 다시 기능 확장으로 방향을 잡았다.\
당시 자바 애플리케이션은 점점 대형화·서버화되었고, 고성능 I/O, 표준 로깅, XML 처리, 정규식 같은 기능을 그동안 서드파티 라이브러리(예: Apache Log4j, Jakarta ORO, JDOM)에 의존해 왔다.\
1.4는 이런 사실상 표준(de facto standard)들을 플랫폼 자체에 흡수하여, 외부 의존 없이도 견고한 애플리케이션을 만들 수 있게 했다.

빌려 쓰던 쪽과 이 편이 들여온 쪽을 위아래 두 칸에 놓으면 이렇다.

```text
위 칸 = 원문이 "의존해 왔다"며 괄호로 든 서드파티 라이브러리
+--------------------------------------------------------------+
|  Apache Log4j    ·    Jakarta ORO    ·    JDOM               |
+--------------------------------------------------------------+

아래 칸 = 원문이 그 라이브러리에 "의존해 왔다"고 적은 기능
+--------------------------------------------------------------+
|  고성능 I/O  ·  표준 로깅  ·  XML 처리  ·  정규식            |
+--------------------------------------------------------------+
```

두 칸 모두 원문 「시대적 배경」의 한 문장에서 뽑았다 — 아래 칸의 넷이 그 문장이 든 기능이고, 위 칸의 셋이 그 문장의 괄호 안 예다. 1.4가 한 일을 원문은 "이런 사실상 표준(de facto standard)들을 플랫폼 자체에 흡수하여"로 적는다.\
원문은 위 칸과 아래 칸을 하나씩 짝지어 적지 않는다 — 어느 라이브러리가 어느 기능을 맡았다는 서술은 원문에 없다.

> **사실상 표준(de facto standard)** — 누가 표준으로 정해서가 아니라, 다들 그것을 쓰다 보니 표준처럼 된 것.\
> 예: 원문이 이 이름으로 부른 것이 위 칸의 서드파티 라이브러리들이다.

## 주요 추가 기능

### assert 키워드

- 1.4에서 새로 추가된 키워드(언어에 추가된 첫 키워드는 아니다 — `strictfp`가 이미 J2SE 1.2에서 추가된 바 있다). 프로그램의 가정(invariant)을 코드로 명시하고, 실행 시 검증할 수 있다.
- 기본적으로 비활성화되어 있으며 `-ea` 옵션으로 켠다(운영 성능에 영향 없음).

> **가정(invariant)** — "여기까지 왔다면 이것만큼은 참이어야 한다"고 코드가 전제하는 조건.\
> 예: 아래 코드가 든 가정이 `x >= 0`이고, 원문은 이를 "프로그램의 가정(invariant)을 코드로 명시하고, 실행 시 검증할 수 있다"고 적는다.

```java
public int sqrt(int x) {
    assert x >= 0 : "음수는 허용되지 않음: " + x;
    return (int) Math.sqrt(x);
}
// 실행: java -ea Main  (assertion 활성화)
```

위 코드의 마지막 주석이 둘째 불릿의 `-ea`를 실제 실행 명령으로 보여 준다.

### NIO (New I/O) — java.nio

- 채널(Channel), 버퍼(Buffer), 셀렉터(Selector) 기반의 고성능·논블로킹 I/O. 대규모 동시 연결을 효율적으로 처리할 수 있게 되어 서버 프로그래밍에 큰 영향을 주었다.

> **논블로킹(non-blocking)** — 결과가 준비될 때까지 그 자리에 붙들려 기다리지 않고, 일단 돌아와 다른 일을 할 수 있는 방식.\
> 예: 원문이 NIO의 효과로 든 것이 "대규모 동시 연결을 효율적으로 처리할 수 있게 되어"다.

```java
import java.nio.*;
import java.nio.channels.*;
import java.io.RandomAccessFile;

FileChannel ch = new RandomAccessFile("data.txt", "r").getChannel();
ByteBuffer buf = ByteBuffer.allocate(1024);
ch.read(buf);
buf.flip();
while (buf.hasRemaining()) {
    System.out.print((char) buf.get());
}
ch.close();
```

위 코드에는 원문이 든 셋 중 둘이 실제로 나온다 — `FileChannel`이 채널(Channel)이고, `ByteBuffer`가 버퍼(Buffer)다.\
셋째인 셀렉터(Selector)는 이 코드에 나오지 않으며, 원문도 이 절에서 셋의 이름만 들 뿐 각각이 무엇을 하는지는 적지 않는다.

*(교차 주: 이 NIO 뒤에 오는 것을 `java-7` 편이 적는다 — 그 편의 소제목은 「NIO.2 — 새 파일 시스템 API (JSR 203)」이고, 그 편은 NIO.2가 대체한 대상을 `java.nio`가 아니라 "노후한 `java.io.File` API"라고 적는다.)*

### 정규 표현식 — java.util.regex

- Perl 스타일 정규식을 표준 라이브러리로 제공. `Pattern`과 `Matcher`로 문자열 매칭·치환·추출을 수행한다.

> **정규 표현식(regular expression)** — 찾고 싶은 문자열의 모양을 기호로 적어 두는 표기법.\
> 예: 아래 코드의 `"(\\d{4})-(\\d{2})-(\\d{2})"`가 그 표기이고, 원문이 든 쓰임이 "문자열 매칭·치환·추출"이다.

```java
import java.util.regex.*;

Pattern p = Pattern.compile("(\\d{4})-(\\d{2})-(\\d{2})");
Matcher m = p.matcher("오늘은 2002-02-06 입니다");
if (m.find()) {
    System.out.println("연도: " + m.group(1)); // 2002
}
```

위 코드가 찾아 내는 `2002-02-06`은 「릴리스 정보」의 출시일과 같은 날짜다.

### 로깅 API — java.util.logging

- 표준 로깅 프레임워크. 로거(Logger), 핸들러(Handler), 레벨(Level) 개념으로 애플리케이션 로그를 체계적으로 남길 수 있다.

```java
import java.util.logging.*;

Logger log = Logger.getLogger("app");
log.info("애플리케이션 시작");
log.warning("설정 파일이 비어 있음");
```

위 코드의 `info`와 `warning`이 원문이 든 셋 중 레벨(Level)에 해당하는 자리다.

### 예외 체이닝(Exception Chaining)

- 한 예외가 다른 예외로 인해 발생했음을 "원인(cause)"으로 연결해 보존하는 기능. `Throwable`에 `getCause()`와 cause 생성자가 추가되어, 저수준 예외를 감싸 던지면서도 원래 스택 트레이스를 잃지 않는다.

> **원인(cause)** — 지금 던지는 예외가 어떤 예외 때문에 생겼는지를 가리켜 두는 자리.\
> 예: 아래 코드에서 `new RuntimeException("설정 로딩 실패", e)`의 둘째 인자 `e`가 그 자리이고, 원문 주석도 "e를 cause로 연결"이라 적는다.

```java
try {
    loadConfig();
} catch (IOException e) {
    throw new RuntimeException("설정 로딩 실패", e); // e를 cause로 연결
}
```

### XML 처리 — JAXP

- JAXP(Java API for XML Processing)가 코어에 포함되어, DOM·SAX 파서와 XSLT 변환을 표준으로 사용할 수 있게 되었다.

```java
import javax.xml.parsers.*;
import org.w3c.dom.Document;

DocumentBuilder db = DocumentBuilderFactory.newInstance().newDocumentBuilder();
Document doc = db.parse("config.xml");
System.out.println(doc.getDocumentElement().getNodeName());
```

위 코드의 `org.w3c.dom.Document`와 `db.parse(...)`가 원문이 든 셋 중 DOM 파서에 해당하는 자리다. SAX와 XSLT는 이 코드에 나오지 않는다.

### IPv6 지원

- `java.net`에 IPv6 주소 지원이 추가되어, 차세대 인터넷 프로토콜 환경에서도 동작하게 되었다.

### Java Web Start

- 웹 링크 클릭만으로 데스크톱 자바 애플리케이션을 다운로드·실행·자동 업데이트하는 배포 기술(JNLP 기반)이다.
- 엄밀히는 Web Start 1.0이 2001년 3월에 별도 제품으로 먼저 출시되었고, J2SE 1.4부터 JRE에 기본 번들로 통합되었다. (1.4에서 처음 만들어진 것이 아니라 1.4에서 플랫폼에 포함된 것)

둘째 불릿의 두 날짜가 서로 맞는다 — 별도 제품 출시가 2001년 3월이고, 「릴리스 정보」의 이 편 출시일이 2002년 2월 6일이다.

## 그 외 변경 / API 추가
- Image I/O API: 다양한 이미지 포맷의 읽기/쓰기 표준화.
- Preferences API(`java.util.prefs`): 사용자/시스템 환경설정 저장.
- JAAS, JSSE, JCE 등 보안·암호화 확장이 코어에 통합.
- `LinkedHashMap`, `LinkedHashSet`, `IdentityHashMap`, `RandomAccess` 마커 인터페이스, `Collections.rotate`/`swap` 등 컬렉션 보강. (`Integer.bitCount` 같은 정수 비트연산 유틸은 1.4가 아니라 J2SE 5.0부터다)

넷째 불릿의 괄호는 원문이 스스로 달아 둔 단서다 — `Integer.bitCount` 같은 정수 비트연산 유틸은 "1.4가 아니라 J2SE 5.0부터"라서 이 편의 보강이 아니다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 불릿은 원문 한 문단을 문장 단위로 끊은 것이다.)*

- J2SE 1.4는 "외부 라이브러리에 기대던 핵심 기능들을 표준으로 끌어들인" 버전이다.
- NIO는 고성능 서버·네트워킹 프레임워크의 토대가 되었고, 정규식·로깅·XML·예외 체이닝은 지금도 거의 모든 자바 프로젝트에서 사용된다.
- 또한 JCP를 통해 개발된 최초의 릴리스로서, 이후 자바 발전이 커뮤니티 표준 프로세스로 운영되는 관행을 정착시켰다.
- 이 버전을 끝으로 다음 릴리스(2004)에서는 "Java 2"의 1.x 번호 체계를 버리고 J2SE 5.0으로 도약하며, 제네릭·오토박싱·애너테이션 등 대규모 언어 개편이 이어진다.

넷째 불릿이 예고하는 셋은 다음 편에서 실제로 절이 된다 — `java-5` 편에 「제네릭 (Generics, JSR 14)」·「오토박싱 / 언박싱 (Autoboxing/Unboxing, JSR 201)」·「어노테이션 / 메타데이터 (Annotations, JSR 175)」가 있다.

## 용어 풀이

- **JCP(Java Community Process)** — 자바 플랫폼에 무엇을 넣을지 커뮤니티가 모여 표준으로 정하는 절차. 원문은 이 편을 "JCP를 거쳐 개발된 최초의 자바 플랫폼 릴리스(JSR 59)"라 적는다.
- **JSR** — 그 절차에서 다루는 건마다 붙는 번호. 이 편에 나온 것이 JSR 59다.
- **사실상 표준(de facto standard)** — 누가 표준으로 정해서가 아니라, 다들 그것을 쓰다 보니 표준처럼 된 것. 원문이 서드파티 라이브러리들을 부른 이름이다.
- **`assert` / `-ea`** — 프로그램의 가정을 코드로 적어 두고 실행 시 검증하는 키워드 / 그 검증을 켜는 실행 옵션. 원문은 기본적으로 비활성화이며 운영 성능에 영향이 없다고 적는다.
- **가정(invariant)** — "여기까지 왔다면 이것만큼은 참이어야 한다"고 코드가 전제하는 조건. 원문 코드가 든 예가 `x >= 0`이다.
- **논블로킹(non-blocking)** — 결과가 준비될 때까지 그 자리에 붙들려 기다리지 않고, 일단 돌아와 다른 일을 할 수 있는 방식. 원문이 NIO의 효과로 든 것이 "대규모 동시 연결을 효율적으로 처리"다.
- **채널(Channel)·버퍼(Buffer)·셀렉터(Selector)** — 원문이 NIO의 기반으로 이름만 든 셋. 코드에 나오는 것은 `FileChannel`과 `ByteBuffer` 둘이다.
- **정규 표현식(regular expression)** — 찾고 싶은 문자열의 모양을 기호로 적어 두는 표기법. 원문이 든 쓰임이 "문자열 매칭·치환·추출"이고, 다루는 짝이 `Pattern`과 `Matcher`다.
- **로거(Logger)·핸들러(Handler)·레벨(Level)** — 원문이 표준 로깅의 개념으로 든 셋. 코드의 `info`·`warning`이 레벨에 해당한다.
- **예외 체이닝 / 원인(cause)** — 한 예외가 다른 예외로 인해 발생했음을 연결해 보존하는 기능 / 그 연결 자리. 원문은 이로써 "저수준 예외를 감싸 던지면서도 원래 스택 트레이스를 잃지 않는다"고 적는다.
- **JAXP** — 원문 표현 그대로 "Java API for XML Processing". 코어에 포함되어 DOM·SAX 파서와 XSLT 변환을 표준으로 쓸 수 있게 됐다.
- **JNLP** — Java Web Start가 기반으로 삼는 것으로 원문이 괄호에 든 이름.

## 참고 출처
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [Java 1.4 - javaalmanac.io](https://javaalmanac.io/jdk/1.4/)
- [JDK release dates - Java Glossary (mindprod)](https://www.mindprod.com/jgloss/jdkreleasedates.html)
