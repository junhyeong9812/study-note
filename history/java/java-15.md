# Java 15 (2020년 9월)

> 원본: `~/project/java-history/java/java-15.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/API 이름·코드블록 2개(java 2)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> 「한눈에」의 양면 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다. 새 도식은 없다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 텍스트 블록을 정식화하고, 봉인 클래스(sealed)를 처음 선보이며, ZGC·Shenandoah를 정식 GC로 승격하고 Nashorn을 제거한 정리·확장의 릴리스.

이 편을 읽는 비유는 **들이는 문과 내보내는 문이 같은 날 함께 열린 창고**다.\
원문이 「시대적 배경」에서 그 양면을 이렇게 적는다 — "각 버전은 "새 기능 preview 도입 → 다듬기 → 정식화"와 "낡은 기능 정리"를 병행했다. Java 15는 그 양면을 모두 보여준다."

| 비유 | 실체 |
|---|---|
| 들이는 문 | 텍스트 블록 정식화 — 원문 표현으로 "텍스트 블록을 정식 기능으로 끌어올리는 동시에" |
| 내보내는 문 | Nashorn JavaScript 엔진 제거 — 원문 표현으로 "더 이상 쓸모가 적어진 Nashorn JavaScript 엔진을 제거했다" |
| 안쪽에서 등급이 올라간 물건 | ZGC·Shenandoah와 14의 preview 기능들 — 원문 표현으로 "한 단계씩 더 성숙시켰다" |

### 이 편에서 미리보기인가 정식인가

이 편에서 흔한 오해가 "15부터 sealed를 그냥 쓴다"이다. **sealed는 이 편에서 preview다.**\
원문이 기능마다 절 제목·불릿에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(15)에서의 상태 — 원문 절 제목·불릿 표기(★는 원문 표기가 아니라 다른 편 원문에서 온 것) | 정식이 된 편 |
|---|---|---|
| sealed 클래스 (JEP 360) | **preview** ★(1차) — 차수 「1차」는 이 편 원문에 없다. 원문 `java-16.md`의 "15의 1차 preview"·원문 `java-17.md`의 "15(1차)·16(2차)"에서 왔다 | 17 (JEP 409) — 출처: 원문 `java-17.md` |
| record (JEP 384) | **2차 preview** | 16 (JEP 395) — 출처: 원문 `java-16.md` |
| instanceof 패턴 매칭 (JEP 375) | **2차 preview** | 16 (JEP 394) — 출처: 원문 `java-16.md` |
| Foreign-Memory Access API (JEP 383) | **2차 incubator** | 이 편에서는 아직 incubator다 — 16에서 3차(JEP 393)로 이어진다(출처: 원문 `java-16.md`) |

나머지는 절 제목대로 이 편(15)에서 정식이 된다 — 절 제목 표기가 「정식」인 텍스트 블록(JEP 378)·Hidden Class(JEP 371)·EdDSA(JEP 339)와, 「정식화」인 ZGC(JEP 377)·Shenandoah(JEP 379) 다섯이다. 텍스트 블록은 13 1차 preview, 14 2차 preview를 거쳤다.

## 릴리스 정보
- 정식 출시일: 2020년 9월 15일
- LTS 여부: 아니오 (단기 지원 릴리스)

## 시대적 배경

Java 11(LTS, 2018) 이후 6개월 주기 릴리스가 안정적으로 반복되며, 각 버전은 "새 기능 preview 도입 → 다듬기 → 정식화"와 "낡은 기능 정리"를 병행했다.\
Java 15는 그 양면을 모두 보여준다.\
텍스트 블록을 정식 기능으로 끌어올리는 동시에, 더 이상 쓸모가 적어진 Nashorn JavaScript 엔진을 제거했다.\
또한 experimental 상태였던 GC(ZGC·Shenandoah)와 14에서 preview였던 언어 기능들을 한 단계씩 더 성숙시켰다.

**왜 저지연 GC에 힘을 쏟았나** — 이 시기 Java 진영은 마이크로서비스·클라우드 환경에서의 저지연 GC 수요에 대응하느라, 실험 단계였던 ZGC와 Shenandoah를 production-ready로 끌어올리는 데 공을 들였다.

> **GC(Garbage Collection) / 저지연 GC** — 더 이상 쓰이지 않는 객체를 정리해 메모리를 돌려주는 일 / 그 정리 때문에 프로그램이 멈추는 시간을 짧게 유지하는 것을 목표로 삼은 GC.\
> 예: 원문이 이 편의 ZGC를 "대용량 힙에서도 정지 시간을 밀리초 단위로 유지한다"고 적는다.

## 주요 추가 기능

### 텍스트 블록 (JEP 378, 정식)

*(「한눈에」의 비유 표에서 "들이는 문"에 해당하는 자리다.)*

13(1차 preview)·14(2차 preview)를 거쳐 정식 기능으로 확정됐다.\
여러 줄 문자열을 `"""`로 감싸 JSON·HTML·SQL 같은 내장 텍스트를 escape 지옥 없이 작성할 수 있다.

> **escape(이스케이프)** — 따옴표나 줄바꿈처럼 그냥은 적을 수 없는 글자를 `\"`·`\n` 같은 표기로 대신 적는 것. 원문은 그것이 쌓인 상태를 "escape 지옥"이라 부른다.\
> 예: 아래 코드에는 `\n`도 `\"`도 없다 — 큰따옴표가 그대로 `"name"`·`"Java"`로 적혀 있다.

```java
String json = """
        {
            "name": "Java",
            "version": 15
        }
        """;
```

### sealed 클래스 (JEP 360, preview)

클래스/인터페이스를 **상속·구현할 수 있는 대상을 명시적으로 제한**하는 기능.\
`permits` 절로 허용 목록을 지정해, 타입 계층을 설계자가 통제할 수 있다.\
이 버전에서 처음 preview로 등장했다.

상속을 **통째로** 막는 장치가 아니다 — **허용 목록 밖만** 막는다(원문이 코드 마지막 줄 주석에 적은 그대로다: "위 셋 외에는 Shape를 구현할 수 없다"). 원문의 두 문장이 말하는 것은 허용 목록을 지정해 **대상을 제한**한다는 것이고, 그 목록에 적힌 셋은 실제로 `Shape`를 구현한다.

> **sealed / `permits`** — 그 타입을 상속·구현할 수 있는 대상을 제한하겠다는 표시 / 그 허용 목록을 적는 절.\
> 예: 아래 코드에서 `permits Circle, Rectangle, Triangle`이 허용 목록이고, 원문이 코드 마지막 줄 주석에 적어 둔 것이 "위 셋 외에는 Shape를 구현할 수 없다"이다.

```java
public sealed interface Shape
        permits Circle, Rectangle, Triangle { }

public final class Circle implements Shape { }
public final class Rectangle implements Shape { }
public final class Triangle implements Shape { }
// 위 셋 외에는 Shape를 구현할 수 없다
```

### Hidden Class (JEP 371, 정식)

프레임워크가 런타임에 생성해 쓰는 클래스를, 다른 클래스에서 직접 참조할 수 없는 **숨겨진 클래스**로 정의하는 표준 API.\
프록시·람다·동적 언어 구현체 등에 유용하며, 기존의 비표준 `Unsafe.defineAnonymousClass`를 대체한다.

> **Hidden Class(숨겨진 클래스)** — 원문 표현으로 "다른 클래스에서 직접 참조할 수 없는" 클래스를 만들어 쓰는 표준 API. 원문이 쓸모로 든 곳이 프록시·람다·동적 언어 구현체다.\
> 예: 원문이 이것이 대체한다고 든 것이 "기존의 비표준 `Unsafe.defineAnonymousClass`"다.

### ZGC 정식화 (JEP 377)

저지연 확장형 가비지 컬렉터 ZGC가 experimental 딱지를 떼고 production 기능이 됐다.\
대용량 힙에서도 정지 시간을 밀리초 단위로 유지한다.

### Shenandoah 정식화 (JEP 379)

또 다른 저지연 GC인 Shenandoah도 experimental에서 production 기능으로 승격됐다.

### EdDSA (JEP 339, 정식)

Edwards-Curve Digital Signature Algorithm(Ed25519/Ed448) 서명 알고리즘을 표준 지원.\
성능과 보안성이 좋아 널리 쓰이는 현대 서명 방식을 플랫폼에 내장했다.

> **서명 알고리즘** — 이 데이터가 그 사람이 보낸 것이 맞고 도중에 바뀌지 않았음을 확인할 수 있게 해 주는 수학적 절차. 원문이 이 편에서 표준 지원했다고 든 것이 Ed25519/Ed448이다.\
> 예: 원문이 EdDSA를 설명한 말이 "성능과 보안성이 좋아 널리 쓰이는 현대 서명 방식"이다.

## 그 외 변경

- **Nashorn JavaScript 엔진 제거 (JEP 372)**: 11에서 deprecated됐던 Nashorn 엔진·API·도구가 완전히 제거됐다.
- **instanceof 패턴 매칭 2차 preview (JEP 375)**: 14의 1차 preview에 이어 변경 없이 한 번 더 preview.
- **record 2차 preview (JEP 384)**: record가 sealed 타입, 지역(local) record 등과 함께 다듬어진 2차 preview.
- **Foreign-Memory Access API 2차 incubator (JEP 383)**.
- **JEP 373**: 레거시 DatagramSocket API를 현대적으로 재구현.
- **JEP 374**: 편향 잠금(biased locking) 비활성화 및 지원 중단.
- **제거/지원 중단**: Solaris/SPARC 포트 제거(JEP 381), RMI Activation 지원 중단(JEP 385).

> **deprecated(지원 중단 예고) / 제거** — 앞으로 없앨 것이라고 표시만 해 둔 상태 / 실제로 빼 버린 상태. 원문이 이 편에서 든 것 가운데 Nashorn과 RMI Activation 두 경우는 표시와 제거가 서로 다른 편에서 일어난다.\
> 예: 원문이 Nashorn을 "11에서 deprecated됐던 … 완전히 제거됐다"로 적는다. 이 편의 RMI Activation은 반대로 지원 중단 쪽이고, 제거는 17(JEP 407)이다(출처: 원문 `java-17.md`).

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다.)*

Java 15는 14에서 뿌린 씨앗을 키운 "징검다리" 릴리스다.\
텍스트 블록을 정식화해 일상 코드의 가독성을 끌어올렸고, sealed 클래스를 도입해 record·패턴 매칭과 함께 대수적 데이터 타입(ADT) 스타일과 향후의 switch 패턴 매칭을 위한 기반을 놓았다.\
ZGC·Shenandoah 정식화는 Java가 클라우드·대용량 서비스의 저지연 요구에 진지하게 대응하고 있음을 보여주는 신호였다.\
동시에 Nashorn 제거처럼 군더더기를 걷어내며 플랫폼을 가볍게 유지했다.

> **대수적 데이터 타입(ADT)** — 원문이 sealed·record·패턴 매칭이 함께 만들어 낸다고 든 "스타일"의 이름. 원문은 이 편에서 이 이름만 들고 뜻을 풀지 않는다.\
> 예: 원문이 같은 문장에서 이 스타일과 나란히 든 또 하나의 기반이 "향후의 switch 패턴 매칭"이고, 그 switch 패턴 매칭은 17에서야 preview로 등장한다(출처: 원문 `java-17.md`).

## 용어 풀이

본문에 용어 블록이 있는 말은 그 블록이 정본이다(한정어가 줄어드는 것을 막으려 여기서 다시 풀지 않는다). 어느 절에 있는지만 적는다.

- **preview(미리보기)** — 정식 기능이 아직 아닌 상태로 먼저 실어 보내는 단계. 원문은 이 흐름을 "새 기능 preview 도입 → 다듬기 → 정식화"라 적고, 이 편의 sealed 클래스를 두고 "이 버전에서 처음 preview로 등장했다"고 적는다. **incubator(인큐베이터)** 는 원문이 API 쪽 미완성 단계에 쓰는 표기로, 이 편에서는 Foreign-Memory Access API가 2차 incubator다. **experimental / production-ready** 는 아직 실험 단계인 상태 / 운영에 써도 되는 상태로, 원문은 ZGC·Shenandoah가 이 편에서 앞에서 뒤로 옮겨 갔다고 적는다(시리즈 공통 용어라 이 편에는 본문 블록을 두지 않았다).
- **GC(Garbage Collection) / 저지연 GC / escape(이스케이프)** — 「시대적 배경」과 「텍스트 블록 (JEP 378, 정식)」 절의 용어 블록. **텍스트 블록** 은 여러 줄 문자열을 `"""`로 감싸 적는 문법으로, 13·14의 preview를 거쳐 이 편에서 정식이 됐다(이 편에는 본문 블록이 없다).
- **sealed / `permits` / Hidden Class(숨겨진 클래스) / 서명 알고리즘 / deprecated(지원 중단 예고)·제거 / 대수적 데이터 타입(ADT)** — 각각 그 기능의 절과 「그 외 변경」·「영향과 의의」의 용어 블록.

## 참고 출처
- [OpenJDK: JDK 15](https://openjdk.org/projects/jdk/15/)
- [JEP 378: Text Blocks](https://openjdk.org/jeps/378)
- [JEP 360: Sealed Classes (Preview)](https://openjdk.org/jeps/360)
- [JEP 371: Hidden Classes](https://openjdk.org/jeps/371)
- [JEP 377: ZGC: A Scalable Low-Latency Garbage Collector](https://openjdk.org/jeps/377)
- [JEP 372: Remove the Nashorn JavaScript Engine](https://openjdk.org/jeps/372)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
