# Java 6 (Java SE 6, Mustang, 2006년 12월)

> 원본: `~/project/java-history/java/java-6.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JSR 번호·클래스/패키지 이름·코드블록 5개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개와 「한눈에」의 연식 변경 비유·대응표, 용어 블록의 「예:」, 「용어 풀이」, 다른 편을 가리키는 교차 주 4개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 언어 문법 변화는 거의 없지만 JVM 성능을 대폭 끌어올리고 스크립팅·컴파일러 API, 웹서비스 스택을 플랫폼에 내장한 "성능과 통합"의 릴리스.

이 편을 하나의 비유로 읽으면 **차체 디자인은 그대로 둔 채 엔진을 손보고, 따로 사서 달던 옵션을 기본 장착으로 바꾼 연식 변경 모델**이다.\
밖에서 보면 작년 차와 구분이 잘 안 되지만, 몰아 보면 다르고 옵션을 따로 살 일이 없어진다.

**Java SE 6도 똑같은 구조다** — 원문 자신이 「시대적 배경」에서 이렇게 적는다: "Sun은 Java SE 6에서 의도적으로 언어 변경을 최소화하고 **JVM 성능, 진단 도구, 라이브러리 통합**에 집중했다".

본문 흐름에 쓰는 비유는 이 연식 변경 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 차체 디자인은 그대로 두는 것 | 원문 표현으로 "의도적으로 언어 변경을 최소화하고" |
| 엔진을 손보는 것 | 원문 표현으로 "**JVM 성능, 진단 도구, 라이브러리 통합**에 집중했다" |
| 따로 사서 달던 옵션을 기본 장착으로 | 원문 표현으로 "그동안 별도 다운로드로 쓰던 JAXB·JAX-WS 같은 웹서비스 스택을 JDK 본체에 포함했다" |
| 몰아 보면 다른 것 | 원문 표현으로 "Java 6은 "체감 성능" 향상으로 특히 유명하다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **"성능 향상"에 원문이 붙인 수치는 없다.**\
  원문이 적는 것은 "JVM 성능 대폭 개선 (서버/클라이언트 HotSpot 최적화, 동기화·가비지 컬렉션 튜닝)"과 ""체감 성능" 향상으로 특히 유명하다"까지이며, 몇 배·몇 퍼센트 같은 값은 이 편 어디에도 나오지 않는다.
- **이 버전의 이름은 더 이상 "J2SE"가 아니다.**\
  원문이 「릴리스 정보」에 직접 적는다 — "이 버전부터 "J2SE"에서 "Java SE"로 브랜드 변경".
- **Java 6이 오래 쓰인 것은 좋아서만은 아니다.**\
  원문이 「영향과 의의」에서 이유를 함께 적는다 — "실제로 Java 7 출시가 Sun의 경영난과 Oracle 인수로 지연되면서".

## 릴리스 정보
- 정식 출시일: 2006년 12월 11일
- 개발 주체: Sun Microsystems (JCP 표준화)
- 공식 명칭: Java SE 6 (내부 버전 1.6) — 이 버전부터 "J2SE"에서 "Java SE"로 브랜드 변경
- 코드네임: Mustang
- 플랫폼 스펙: JSR 270 (Java SE 6 Release Contents)
- LTS 여부: 해당 시대엔 LTS 개념 없음

## 시대적 배경

J2SE 5.0이 언어 문법을 한꺼번에 갈아엎은 직후라, Sun은 Java SE 6에서 의도적으로 언어 변경을 최소화하고 **JVM 성능, 진단 도구, 라이브러리 통합**에 집중했다.\
또한 SOAP/WSDL 기반 웹서비스가 엔터프라이즈 표준으로 자리 잡던 시기라, 그동안 별도 다운로드로 쓰던 JAXB·JAX-WS 같은 웹서비스 스택을 JDK 본체에 포함했다.

위 둘째 줄의 앞뒤를 두 칸에 나눠 놓으면 이렇다.

```text
왼쪽 칸 = 원문이 "그동안"이라 적은 쪽     오른쪽 칸 = 이 편이 한 일
+---------------------------------+      +---------------------------------+
|  JAXB · JAX-WS 같은              |      |  같은 스택이                     |
|  웹서비스 스택을                 |      |                                  |
|  "별도 다운로드로" 쓰던 상태      |      |  "JDK 본체에 포함"된 상태         |
+---------------------------------+      +---------------------------------+
```

두 칸은 같은 것(JAXB·JAX-WS 같은 웹서비스 스택)이 놓인 자리가 달라진 것이고, 두 칸의 따옴표 문구는 모두 위 둘째 줄 한 문장에서 뽑았다.

Mustang은 개발 과정을 오픈으로 공개해 정기 빌드를 배포한 첫 릴리스이기도 하며, 직후인 2006~2007년 Sun이 Java를 GPL로 오픈소스화(OpenJDK)하는 흐름과 맞물린다.

> **웹서비스 스택** — 프로그램끼리 네트워크로 기능을 주고받게 해 주는 규격과 그 구현을 묶어 부르는 말.\
> 예: 원문이 이 자리에서 든 규격이 SOAP/WSDL이고, 스택으로 든 것이 JAXB·JAX-WS다.

## 주요 추가 기능

### 스크립팅 API (Scripting for the Java Platform, JSR 223)

JVM 위에서 스크립트 언어를 실행하는 표준 프레임워크다. Mozilla Rhino 기반 JavaScript 엔진이 기본 탑재되어, 별도 라이브러리 없이 Java에서 스크립트를 평가할 수 있게 되었다.

```java
import javax.script.*;

ScriptEngineManager manager = new ScriptEngineManager();
ScriptEngine engine = manager.getEngineByName("JavaScript");
Object result = engine.eval("var x = 10; x * 2;");
System.out.println(result); // 20.0 (Rhino는 JS 숫자를 Double로 반환)

// Java 변수를 스크립트로 바인딩
engine.put("name", "Mustang");
engine.eval("print('Hello ' + name)");
```

위 코드가 두 가지를 차례로 보여 준다 — `engine.eval("var x = 10; x * 2;")`가 본문이 말한 "Java에서 스크립트를 평가"이고, `engine.put("name", "Mustang")`이 코드 주석이 말한 "Java 변수를 스크립트로 바인딩"이다.\
첫 결과에 붙은 주석 "20.0 (Rhino는 JS 숫자를 Double로 반환)"은 왜 `20`이 아니라 `20.0`인지를 원문이 직접 적어 둔 것이다.

*(교차 주: 여기 기본 탑재된 Rhino가 뒤에서 어떻게 되는지는 다른 편이 적는다 — `java-8` 편은 Nashorn을 "기존 Rhino 엔진을 대체하는 고성능 JavaScript 런타임"으로 적고, `java-15` 편은 "Nashorn JavaScript 엔진 제거 (JEP 372)" 아래에서 "Nashorn 엔진·API·도구가 완전히 제거됐다"고 적는다.)*

> **스크립트 엔진(script engine)** — 스크립트 언어로 쓰인 글을 받아 실행해 주는 부품.\
> 예: 위 코드의 `manager.getEngineByName("JavaScript")`로 꺼내 온 `engine`이 그것이다.

### 컴파일러 API (Java Compiler API, JSR 199)

런타임에 Java 소스를 프로그래밍 방식으로 컴파일할 수 있다. 이전에는 임시 `.java` 파일을 만들고 `javac`를 외부 프로세스로 호출하거나 내부 API를 해킹해야 했다.

*(원문이 이 절에서 불편으로 적은 문장은 위 둘째 줄의 "이전에는 임시 `.java` 파일을 만들고 `javac`를 외부 프로세스로 호출하거나 내부 API를 해킹해야 했다"이며, 이는 이 API가 치른 대가가 아니라 이 API가 나온 동기다.)*

```java
import javax.tools.*;

JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
int result = compiler.run(null, null, null, "Hello.java");
System.out.println(result == 0 ? "컴파일 성공" : "실패");
```
이 API는 동적 코드 생성, JSP 컨테이너, 어노테이션 처리 도구의 기반이 되었다.

위 코드에서 `ToolProvider.getSystemJavaCompiler()`로 얻은 컴파일러를 `compiler.run(...)`으로 부르는 것이, 본문이 말한 "`javac`를 외부 프로세스로 호출"하지 않는 쪽이다.

### 플러그인 가능한 어노테이션 처리 (Pluggable Annotation Processing, JSR 269)

컴파일 시점에 어노테이션을 처리하는 표준 API(`javax.annotation.processing`, `javax.lang.model`)가 도입되었다. 별도 도구였던 `apt`를 대체하며, 이후 Lombok·Dagger·MapStruct 같은 코드 생성 도구의 토대가 된다.

> **어노테이션 처리(annotation processing)** — 코드에 붙은 어노테이션을 읽어 무언가를 하는 일. 원문은 그 시점을 "컴파일 시점"으로 적는다.\
> 예: 원문이 이 위에 세워진 도구로 든 것이 Lombok·Dagger·MapStruct다.

*(교차 주: 이 절이 읽어 처리하는 어노테이션은 앞 편이 도입한 것이다 — `java-5` 편의 「어노테이션 / 메타데이터 (Annotations, JSR 175)」가 "언어 구성요소에 메타데이터를 부착할 수 있게 되었다"고 적는 그 메타데이터다.)*

### JDBC 4.0 (JSR 221)

데이터베이스 접근이 한결 간결해졌다. 드라이버 자동 로딩(`Class.forName` 불필요), `SQLException` 계층 개선(`SQLException`이 `Iterable`을 구현, 원인별 서브클래스 추가), `SQLXML`·`RowId`·`NClob` 등 새 SQL 타입 지원이 추가되었다.

도입 전 (JDBC 3.0):
```java
Class.forName("com.mysql.jdbc.Driver"); // 수동 드라이버 로딩 필요
Connection conn = DriverManager.getConnection(url, user, pw);
```

도입 후 (JDBC 4.0):
```java
// 드라이버가 클래스패스에 있으면 자동 로딩됨
Connection conn = DriverManager.getConnection(url, user, pw);
```

두 블록에서 달라진 것은 한 줄뿐이다 — 위의 `Class.forName("com.mysql.jdbc.Driver")`가 아래에서는 아예 없고, 그 자리를 아래 코드 주석 "드라이버가 클래스패스에 있으면 자동 로딩됨"이 설명한다.

*(교차 주: 여기서 다듬어지는 JDBC는 `jdk-1.1` 편이 "데이터베이스 접속을 위한 표준 API"로 도입한 그것이다 — 두 편의 코드 모두 `DriverManager.getConnection(...)`으로 시작한다.)*

> **드라이버 자동 로딩** — 어느 드라이버를 쓸지 코드에 직접 적지 않아도, 놓여 있는 것을 찾아 쓰게 되는 것.\
> 예: 원문은 그 조건을 코드 주석에서 "드라이버가 클래스패스에 있으면"으로 적는다.

### JAXB 2.0 (JSR 222) 및 웹서비스 스택

XML 바인딩(JAXB 2.0)과 SOAP 웹서비스(JAX-WS 2.0, JSR 224)가 JDK에 내장되어 어노테이션만으로 웹서비스를 만들 수 있게 되었다.

```java
import javax.jws.WebService;

@WebService
public class Calculator {
    public int add(int a, int b) { return a + b; }
}
```
함께 StAX(Streaming API for XML, JSR 173)도 표준 라이브러리에 편입되었다.

위 코드에서 본문이 말한 "어노테이션만으로"에 해당하는 것은 `@WebService` 한 줄이다 — 나머지는 평범한 클래스와 메서드다.

*(교차 주: 여기서 JDK에 내장된 이 스택이 뒤에서 어떻게 되는지는 `java-11` 편이 적는다 — 그 편의 "JEP 320 — Java EE 및 CORBA 모듈 제거"가 "`java.xml.ws`(JAX-WS), `java.xml.bind`(JAXB), `java.activation`, `java.corba` 등 제거"를 든다.)*

> **XML 바인딩(binding)** — XML 문서와 자바 객체를 서로 옮겨 담을 수 있게 짝지어 두는 것.\
> 예: 원문이 이 자리에서 그 수단으로 든 것이 JAXB 2.0이다.

### GUI / 데스크톱 개선
- Swing의 `GroupLayout` 레이아웃 매니저 (NetBeans Matisse 디자이너 지원)
- `SwingWorker` 표준 편입 (백그라운드 작업과 EDT 분리)
- 테이블 정렬·필터링, 향상된 드래그앤드롭
- `java.awt.Desktop` API (기본 브라우저/메일/파일 연결 실행)
- 시스템 트레이 지원 (`SystemTray`, `TrayIcon`)

원문은 이 절에서 다섯 가지를 이름과 괄호 설명으로만 들 뿐, 각각이 어떻게 동작하는지는 적지 않는다.

## 그 외 변경 / API 추가
- JVM 성능 대폭 개선 (서버/클라이언트 HotSpot 최적화, 동기화·가비지 컬렉션 튜닝) — Java 6은 "체감 성능" 향상으로 특히 유명하다
- `java.lang.management` 기반 모니터링·진단 강화, JConsole 개선
- Common Annotations (JSR 250) 편입 (`@PostConstruct`, `@Resource` 등)
- `Console` 클래스 (`System.console()`)로 비밀번호 입력 등 콘솔 처리 개선
- 다양한 `NavigableMap`/`NavigableSet` 등 컬렉션 보강

첫 불릿의 HotSpot은 `jdk-1.3` 편이 "기본 JVM이 되었다"고 적은 그 가상 머신이다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문 한 문단을 문장 단위로 끊은 것이다.)*

- Java SE 6은 "조용하지만 강력한" 릴리스로 평가된다.
- 새 문법으로 개발자를 흥분시키진 않았지만, 눈에 띄는 성능 향상과 웹서비스·스크립팅·컴파일러 API의 플랫폼 통합으로 엔터프라이즈 현장에서 매우 오래 사랑받았다.
- 실제로 Java 7 출시가 Sun의 경영난과 Oracle 인수로 지연되면서, Java 6은 여러 해 동안 사실상의 산업 표준 JDK로 장기 군림했다.

## 용어 풀이

- **웹서비스 스택** — 프로그램끼리 네트워크로 기능을 주고받게 해 주는 규격과 그 구현을 묶어 부르는 말. 원문이 든 규격이 SOAP/WSDL이고, 원문이 "웹서비스 스택"이라 부른 것이 JAXB·JAX-WS다.
- **스크립트 엔진(script engine)** — 스크립트 언어로 쓰인 글을 받아 실행해 주는 부품. 이 편에 기본 탑재된 것이 "Mozilla Rhino 기반 JavaScript 엔진"이다.
- **스크립팅 API** — 원문 표현 그대로 "JVM 위에서 스크립트 언어를 실행하는 표준 프레임워크".
- **바인딩(스크립트 쪽)** — 자바 쪽 값을 스크립트가 쓸 수 있게 이름으로 걸어 두는 것. 원문 코드 주석은 이를 "Java 변수를 스크립트로 바인딩"이라 적고, 그 호출이 `engine.put("name", "Mustang")`이다.
- **컴파일러 API** — 원문 표현 그대로 "런타임에 Java 소스를 프로그래밍 방식으로 컴파일"하게 해 주는 API. 원문이 든 기반 쓰임이 동적 코드 생성·JSP 컨테이너·어노테이션 처리 도구다.
- **어노테이션 처리(annotation processing)** — 코드에 붙은 어노테이션을 읽어 무언가를 하는 일. 원문은 그 시점을 "컴파일 시점"으로 적고, 이 위에 세워진 도구로 Lombok·Dagger·MapStruct를 든다.
- **드라이버 자동 로딩** — 어느 드라이버를 쓸지 코드에 직접 적지 않아도 되는 것. 원문은 그 조건을 "드라이버가 클래스패스에 있으면"으로 적고, 필요 없어진 호출로 `Class.forName`을 든다.
- **XML 바인딩(binding)** — XML 문서와 자바 객체를 서로 옮겨 담을 수 있게 짝지어 두는 것. 원문이 그 수단으로 든 것이 JAXB 2.0이다.
- **"체감 성능"** — 원문이 Java 6의 성능 향상에 붙인 표현. 원문은 이 편에서 그 향상폭을 수치로 적지 않는다.

## 참고 출처
- [Java version history — Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [Java Platform, Standard Edition 6 — Oracle](https://www.oracle.com/java/technologies/se6-jsp.html)
- [JSR 270: Java SE 6 Release Contents — JCP](https://jcp.org/en/jsr/detail?id=270)
- [Java SE 6 (December 11, 2006) — Liquisearch](https://www.liquisearch.com/java_version_history/java_se_6_december_11_2006)
