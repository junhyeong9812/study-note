# Java 변천사 — 쉽게 다시 쓴 판

> 원본: `~/project/java-history/java/README.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·코드네임·LTS 표시·한 줄 요약·문서 링크·「전체 타임라인」과 「릴리스 모델의 변천」 두 표·「용어 메모」는 원문 그대로다.\
> ASCII 도식 3개는 원문의 mermaid 도식 3개(버전 타임라인 · 언어 기능 계보 · 릴리스 모델)를 글자로 옮긴 것이고, **새로 그린 도식은 없다.**\
> 「한눈에」의 묶음 표와 「급하면 이렇게 골라 읽어도 된다」 길찾기, LTS 교차 대조 세 줄은 원문 README에 없는 보충이다.\
> **원문 README에는 「읽는 법」·「큰 줄기」 같은 절이 없다.** 그 자리를 대신하는 길찾기는 보충이고, 길찾기가 가리키는 근거는 아래 「전체 타임라인」 표의 한 줄 요약(원문)에서 가져왔다 — 단 java-24 괄호 하나만 그 표가 아니라 `java-24.md` 본문에서 가져왔다.\
> 목차의 「시기」 열은 따로 만들지 않았다 — 원문 「전체 타임라인」 표의 **「출시」 열**이 27편 모두 같은 `YYYY-MM` 형식이라 그대로 쓰면 된다.\
> H1만 다른 주제 README(`history/spring/README.md`·`history/python/README.md` 등)와 형식을 맞춰 바꿨다 — 원문 H1은 「Java 변천사 — JDK 1.0부터 Java 26까지」다. 나머지 절 제목은 원문 그대로다.

> 자바 언어와 플랫폼의 역사를 버전별로 정리한 "책". 각 장(章)은 한 버전이며, 어떤 기능이 언제 추가되었는지, 그 배경과 의의를 다룬다.

## 한눈에 — 28편이 놓인 자리

이 폴더는 **27편 + 이 README = 28편**이다.\
아래 표는 원문 「시대 구분으로 읽기」가 이미 나눠 둔 다섯 절에 27편을 그대로 얹은 것이다 — 절 제목과 연도 범위는 원문의 것이고, 나눈 기준도 원문의 것이다.

| 원문 「시대 구분으로 읽기」의 절 | 그 절이 묶는 편 | 편수 |
|---|---|---|
| 1부. 태동기 (1996\~2002) — JDK 1.0 \~ 1.4 | `jdk-1.0` · `jdk-1.1` · `jdk-1.2` · `jdk-1.3` · `jdk-1.4` | 5 |
| 2부. 현대 자바의 기반 (2004\~2011) — Java 5, 6, 7 | `java-5` · `java-6` · `java-7` | 3 |
| 3부. 함수형 혁명과 모듈화 (2014\~2017) — Java 8, 9 | `java-8` · `java-9` | 2 |
| 4부. 빠른 진화 (2018\~2021) — Java 10 \~ 17 | `java-10` · `java-11` · `java-12` · `java-13` · `java-14` · `java-15` · `java-16` · `java-17` | 8 |
| 5부. Loom과 패턴 매칭의 완성 (2022\~2026) — Java 18 \~ 26 | `java-18` · `java-19` · `java-20` · `java-21` · `java-22` · `java-23` · `java-24` · `java-25` · `java-26` | 9 |
| (색인) | `README.md` — 위 27편의 목차 | 1 |
| **합계** | | **28** |

시기는 이 표가 아니라 아래 「전체 타임라인」 표의 **「출시」 열**에서 읽으면 된다. 27편 모두 같은 형식으로 적혀 있다.

## 급하면 이렇게 골라 읽어도 된다

*(이 절은 원문 README에 없는 보충이다. 괄호 안의 말은 아래 「전체 타임라인」 표의 한 줄 요약에서 옮긴 것이다 — java-24 괄호 하나만 예외로, 그 편 본문에서 가져왔다.)*

- **지금 실무에서 쓰는 버전만 보고 싶다** → LTS 다섯 편: [java-8.md](java-8.md)("람다·Stream·Optional·java.time — 함수형 혁명") → [java-11.md](java-11.md)("표준 HTTP 클라이언트, 단일 파일 실행, 첫 6개월모델 LTS") → [java-17.md](java-17.md)("sealed 클래스 정식, switch 패턴 매칭(preview)") → [java-21.md](java-21.md)("가상 스레드 정식, record 패턴 정식, switch 패턴 매칭 정식") → [java-25.md](java-25.md)("Scoped Values·Module Import·Compact Source Files·Flexible Constructors 정식")
- **지금 쓰는 문법이 어디서 왔는지 보고 싶다** → [java-5.md](java-5.md)("제네릭·어노테이션·enum·for-each·오토박싱 — 언어 대변혁") → [java-8.md](java-8.md) → [java-14.md](java-14.md)("switch 표현식 정식, record(preview), 유용한 NPE 메시지") → [java-16.md](java-16.md)("record 정식, instanceof 패턴 매칭 정식") → [java-21.md](java-21.md)
- **동시성이 왜 지금 모양인지 보고 싶다** → [java-19.md](java-19.md)("**가상 스레드(preview)**, record 패턴(preview), 구조적 동시성") → [java-21.md](java-21.md) → [java-24.md](java-24.md)(이 편의 JEP 491이 가상 스레드의 고정(pinning) 문제를 푼다 — `java-24.md` 본문에서 가져옴)
- **릴리스 제도 자체가 궁금하다** → [java-9.md](java-9.md)("모듈 시스템(Jigsaw), jshell, 6개월 릴리스 모델 전환") → [java-11.md](java-11.md) → [java-23.md](java-23.md)("마크다운 Javadoc, 세대별 ZGC 기본화, String Templates 철회") → 그리고 이 문서의 「릴리스 모델의 변천」

---

## 이 책의 구성

각 버전은 독립된 마크다운 문서로 작성되어 있다. 문서마다 **릴리스 정보 → 시대적 배경 → 주요 추가 기능(코드 예시 포함) → 그 외 변경 → 영향과 의의 → 참고 출처** 구조를 따른다.

---

## 전체 타임라인

| 버전 | 출시 | 코드네임 | LTS | 한 줄 요약 | 문서 |
|------|------|----------|:---:|------------|------|
| JDK 1.0 | 1996-01 | — | | 자바 최초 정식 릴리스, JVM/바이트코드 모델 확립, AWT·애플릿 | [jdk-1.0.md](jdk-1.0.md) |
| JDK 1.1 | 1997-02 | — | | 내부 클래스, JavaBeans, JDBC, RMI, 리플렉션, 위임 이벤트 모델 | [jdk-1.1.md](jdk-1.1.md) |
| J2SE 1.2 | 1998-12 | Playground | | "Java 2" 브랜딩, Swing, Collections Framework, JIT, 플랫폼 분화 | [jdk-1.2.md](jdk-1.2.md) |
| J2SE 1.3 | 2000-05 | Kestrel | | HotSpot JVM 기본 탑재, JNDI, JPDA | [jdk-1.3.md](jdk-1.3.md) |
| J2SE 1.4 | 2002-02 | Merlin | | assert, NIO, 정규식, logging, XML(JAXP), 예외 체이닝 | [jdk-1.4.md](jdk-1.4.md) |
| J2SE 5.0 | 2004-09 | Tiger | | 제네릭·어노테이션·enum·for-each·오토박싱 — 언어 대변혁 | [java-5.md](java-5.md) |
| Java SE 6 | 2006-12 | Mustang | | 성능 중심, 스크립팅 API, 컴파일러 API, 웹서비스 스택 내장 | [java-6.md](java-6.md) |
| Java SE 7 | 2011-07 | Dolphin | | Project Coin(try-with-resources, diamond, multi-catch), NIO.2 | [java-7.md](java-7.md) |
| Java SE 8 | 2014-03 | — | | **람다·Stream·Optional·java.time — 함수형 혁명** | [java-8.md](java-8.md) |
| Java SE 9 | 2017-09 | — | | 모듈 시스템(Jigsaw), jshell, 6개월 릴리스 모델 전환 | [java-9.md](java-9.md) |
| Java SE 10 | 2018-03 | — | | `var` 지역변수 타입 추론 | [java-10.md](java-10.md) |
| Java SE 11 | 2018-09 | — | ✅ | 표준 HTTP 클라이언트, 단일 파일 실행, 첫 6개월모델 LTS | [java-11.md](java-11.md) |
| Java SE 12 | 2019-03 | — | | switch 표현식(preview), Shenandoah GC | [java-12.md](java-12.md) |
| Java SE 13 | 2019-09 | — | | 텍스트 블록(preview), switch 표현식 `yield` | [java-13.md](java-13.md) |
| Java SE 14 | 2020-03 | — | | switch 표현식 정식, record(preview), 유용한 NPE 메시지 | [java-14.md](java-14.md) |
| Java SE 15 | 2020-09 | — | | 텍스트 블록 정식, sealed 클래스(preview), Nashorn 제거 | [java-15.md](java-15.md) |
| Java SE 16 | 2021-03 | — | | record 정식, instanceof 패턴 매칭 정식 | [java-16.md](java-16.md) |
| Java SE 17 | 2021-09 | — | ✅ | sealed 클래스 정식, switch 패턴 매칭(preview) | [java-17.md](java-17.md) |
| Java SE 18 | 2022-03 | — | | UTF-8 기본 charset, jwebserver | [java-18.md](java-18.md) |
| Java SE 19 | 2022-09 | — | | **가상 스레드(preview)**, record 패턴(preview), 구조적 동시성 | [java-19.md](java-19.md) |
| Java SE 20 | 2023-03 | — | | 가상 스레드·record 패턴·switch 패턴 매칭 추가 preview | [java-20.md](java-20.md) |
| Java SE 21 | 2023-09 | — | ✅ | **가상 스레드 정식, record 패턴 정식, switch 패턴 매칭 정식** | [java-21.md](java-21.md) |
| Java SE 22 | 2024-03 | — | | FFM API 정식, 미명명 변수/패턴 정식, Stream Gatherers(preview) | [java-22.md](java-22.md) |
| Java SE 23 | 2024-09 | — | | 마크다운 Javadoc, 세대별 ZGC 기본화, String Templates 철회 | [java-23.md](java-23.md) |
| Java SE 24 | 2025-03 | — | | 역대 최다(24 JEP), Class-File API·Stream Gatherers 정식, 양자내성 암호 | [java-24.md](java-24.md) |
| Java SE 25 | 2025-09 | — | ✅ | Scoped Values·Module Import·Compact Source Files·Flexible Constructors 정식 | [java-25.md](java-25.md) |
| Java SE 26 | 2026-03 | — | | HTTP/3 클라이언트, AOT 객체 캐싱(Any GC), final 무결성 준비, Applet API 제거 | [java-26.md](java-26.md) |

*(이 줄은 원문 표에 없는 보충이다.)* 원본이 Java 26 에서 멈춘 뒤의 변화는 [99-그-뒤.md](99-그-뒤.md) 에 따로 적었다 — 재서술이 아니라 **출처를 달아 새로 쓴 편**이다(Java 27 출시·프리뷰 차수 진행·JDK 28 대상 JEP, 2026-09-20 기준).

> LTS(Long-Term Support): Java 8, 11, 17, 21, 25. 6개월 케이던스 시대에는 9월 릴리스 중 Oracle이 지정한 버전(11, 17, 21, 25...)이 LTS이며, "짝수성"으로 정해지는 것이 아니다(11·17·21·25는 홀수). 초기엔 3년 간격이었다가 2023년부터 2년 주기로 단축되었다.

위 표의 `✅`는 다섯 중 넷(11·17·21·25)에만 붙어 있고 Java 8 행은 비어 있는데, 두 자리가 어긋난 것이 아니라 기준이 다르다.\
각 편이 그 기준을 직접 적는다 — `java-8.md`는 "현대적 LTS 모델(Java 11부터 시작) 이전 버전이지만, Oracle이 상용·확장 지원을 장기간 제공하여 사실상 가장 오래 살아남은 "장기 지원" 버전으로 취급됨"이라 적고, `java-11.md`는 자기를 "6개월 케이던스 도입 이후 첫 LTS"라 적는다.\
나머지 셋도 각 편과 이 표가 서로 맞는다 — `java-17.md`는 "직전 LTS는 Java 11(2018), 다음 LTS는 Java 21(2023)", `java-21.md`는 "Java 17(2021), Java 25(2025)와 함께 장기 지원 라인", `java-25.md`는 "직전 LTS는 Java 21(2023.09)"이다.

### 버전 타임라인 (다이어그램)

아래는 주요 분기점이 된 버전을 연도·핵심 키워드와 함께 정리한 타임라인이다.

```text
Java 주요 버전 타임라인

1996 : JDK 1.0 - JVM/바이트코드, AWT, 애플릿
1998 : J2SE 1.2 - Swing, Collections, JIT
2004 : Java 5 - 제네릭, 어노테이션, enum
2014 : Java 8 - 람다, Stream, java.time
2017 : Java 9 - 모듈 시스템 Jigsaw, jshell
2018 : Java 11 LTS - 표준 HTTP 클라이언트
2021 : Java 17 LTS - sealed 클래스 정식
2023 : Java 21 LTS - 가상 스레드 정식
2025 : Java 25 LTS - Scoped Values 정식
2026 : Java 26 - HTTP/3 클라이언트, AOT 객체 캐싱(Any GC)
```

- 이 그림은 원문의 mermaid `timeline` 도식을 글자로 옮긴 것이다 — 맨 윗줄은 원문의 `title`이고, 열 줄의 연도와 글자는 원문의 것 그대로다.
- **줄 사이의 간격은 연수에 비례하지 않는다.** 원문의 `timeline`도 마찬가지로 항목을 차례로 늘어놓을 뿐이다 — 1998과 2004 사이(6년)도, 2025와 2026 사이(1년)도 한 줄 간격이다.
- 27편 가운데 열 편만 뽑혀 있다. 나머지는 위 「전체 타임라인」 표에서 본다.

### 언어 기능 계보: preview에서 정식까지

주요 언어 기능이 preview 단계를 거쳐 어느 버전에서 정식화됐는지 보여준다.

```text
텍스트 블록        13: preview  -->  14: 2차 preview     -->  15: 정식
record             14: preview  -->  15: 2차 preview     -->  16: 정식
switch 패턴 매칭   17: preview  -->  18~20: 추가 preview  -->  21: 정식
가상 스레드        19: preview  -->  20: 2차 preview     -->  21: 정식
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 네 줄이 원문의 네 묶음이고, 각 줄의 화살표 둘씩 **화살표 여덟**으로 원문의 화살표 수와 같다. 왼쪽 이름과 칸 안의 글자도 원문의 것 그대로다.
- 네 줄은 서로 잇지 않았다 — 원문도 네 묶음 사이에 아무 화살표를 긋지 않는다.

위 네 기능 모두 "preview에서 여러 버전을 거쳐 정식화"되는 6개월 케이던스 시대의 전형적 도입 경로를 따른다.

---

## 시대 구분으로 읽기

### 1부. 태동기 (1996\~2002) — JDK 1.0 \~ 1.4
자바의 기본 골격이 잡힌 시기. JVM/바이트코드, AWT/Swing GUI, Collections, NIO 등 플랫폼의 토대가 마련됐다. 언어 문법은 거의 고정적이었다.

### 2부. 현대 자바의 기반 (2004\~2011) — Java 5, 6, 7
**Java 5의 제네릭·어노테이션**이 언어를 바꿨고, 이는 Spring·Hibernate·JUnit 등 어노테이션 기반 생태계의 토대가 됐다. Java 7은 Oracle 인수 후 첫 릴리스로 Project Coin과 NIO.2를 도입했다.

### 3부. 함수형 혁명과 모듈화 (2014\~2017) — Java 8, 9
**Java 8의 람다·Stream**은 자바 작성 방식을 근본적으로 바꿨다. Java 9는 모듈 시스템을 도입한 구(舊) 비정기 모델의 마지막 릴리스였고, 6개월 정기 케이던스로의 전환이 이때 발표되었다(실제 첫 6개월 주기 릴리스는 Java 10, 2018-03).

### 4부. 빠른 진화 (2018\~2021) — Java 10 \~ 17
6개월마다 릴리스되며 `var`, switch 표현식, 텍스트 블록, record, sealed class, 패턴 매칭이 preview → 정식 경로를 밟았다. Java 11·17이 LTS.

### 5부. Loom과 패턴 매칭의 완성 (2022\~2026) — Java 18 \~ 26
**가상 스레드(Project Loom)**, record 패턴, switch 패턴 매칭이 정식화(Java 21)되고, FFM API(Project Panama), Scoped Values, 모듈 임포트 등이 자리잡았다. Java 21·25가 LTS. 비-LTS인 Java 26은 HTTP/3 클라이언트와 모든 GC에 적용되는 AOT 객체 캐싱을 정식화하고, 구조적 동시성·원시 타입 패턴은 다음 LTS(Java 29)를 향해 프리뷰를 이어간다.

---

## 릴리스 모델의 변천

| 시기 | 모델 | 특징 |
|------|------|------|
| 1996\~2017 (JDK 1.0 \~ Java 9) | 비정기 (수년 간격) | 기능이 모일 때마다 릴리스. Java 6→7 사이 약 5년 공백 |
| 2017\~ (Java 10 이후) | **6개월 정기 케이던스** | 매년 3월/9월 릴리스. 기능은 preview → 정식으로 점진 도입 |
| 2018\~ | **LTS 도입** | 처음엔 3년 주기(11, 17), 2023부터 2년 주기(21, 25)로 단축 |

이 표의 둘째 행 「2017\~」과 아래 그림의 「2018\~」는 기준이 다르다 — 원문이 위 「3부」에서 그 둘을 갈라 적는다: "6개월 정기 케이던스로의 전환이 이때 발표되었다(실제 첫 6개월 주기 릴리스는 Java 10, 2018-03)."

릴리스 모델은 크게 세 단계로 변해 왔다.

```text
비정기 (1996~2017)     -->  6개월 케이던스 (2018~)      -->  LTS 2년 주기 (2023~)
기능이 모이면 릴리스        매년 3월/9월 정기 릴리스         21, 25... 2년 간격 LTS
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 칸 셋과 화살표 둘로 원문과 같고, 각 칸의 두 줄은 원문이 한 칸 안에서 줄을 바꿔 적은 글자 그대로다.

비정기 대형 릴리스에서 6개월 정기 릴리스로, 다시 LTS 주기가 3년에서 2년으로 짧아지는 흐름이다.

- **개발 주체:** JDK 1.0\~1.4 = Sun Microsystems / Java 5\~6 = Sun (JCP 주도) / Java 7\~ = Oracle (2010년 Sun 인수)
- **변경 절차:** 초기에는 비공식 절차 → J2SE 1.4(JSR 59)·5.0(JSR 176)부터 JCP의 JSR로 플랫폼 명세가 정식화 → Java 9 전후부터는 개별 기능을 **JEP**(JDK Enhancement Proposal)로 추적(단, 플랫폼 자체는 지금도 Java SE 버전마다 JSR로 명세된다)

---

## 용어 메모

- **JSR** (Java Specification Request): JCP의 표준 명세 단위. 예) 제네릭=JSR 14, 람다=JSR 335.
- **JEP** (JDK Enhancement Proposal): OpenJDK의 기능 제안 단위. 예) `var`=JEP 286, 가상 스레드=JEP 444.
- **preview / incubator / experimental:** 정식 채택 전 단계. preview는 언어/API 기능, incubator는 모듈 단위 API, experimental은 주로 JVM/GC 기능을 시험 배포한다.
