# Java 16 (2021년 3월)

> 원본: `~/project/java-history/java/java-16.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·코드블록 3개(java 3)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> 「한눈에」의 이삿짐 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다. 새 도식은 없다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> record와 instanceof 패턴 매칭을 동시에 정식화하고, JDK 내부를 기본적으로 강하게 캡슐화하며, Vector·외부 메모리 API를 incubator로 밀어붙인 "정식화 러시" 릴리스.

이 편을 읽는 비유는 **이사 전날**이다.\
원문이 「시대적 배경」에서 그 성격을 이렇게 적는다 — "Java 16은 다음 LTS(Java 17)를 6개월 앞둔 버전이다. … LTS에서 안정적으로 제공할 채비를 갖추는 성격이 강하다."

| 비유 | 실체 |
|---|---|
| 이사 날 | 다음 LTS인 Java 17 — 원문 표현으로 "다음 LTS(Java 17)를 6개월 앞둔 버전" |
| 정식 포장으로 묶어 둔 짐 | record·instanceof 패턴 매칭 — 원문 표현으로 "이 버전에서 동시에 정식 기능이 된 것이 그 증거다" |
| 아직 상자에 못 넣은 짐 | sealed 2차 preview·Vector·외부 메모리/링커 API — 원문이 각각 preview·incubator로 적은 것들 |

### 이 편에서 미리보기인가 정식인가

이 편에서 흔한 오해는 방향이 둘이다 — **record와 instanceof 패턴 매칭은 여기서 정식이 되고, sealed는 아직 preview다.**\
원문이 절 제목·본문에 적어 둔 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(16)에서의 상태 — 원문 절 제목·본문 표기(★는 원문 표기가 아니라 재서술자 추론이거나 다른 편 원문에서 온 것) | 정식이 된 편 |
|---|---|---|
| record (JEP 395) | **정식화** | 16 — 이 편이다 (14 1차, 15 2차 preview를 거쳤다) |
| instanceof 패턴 매칭 (JEP 394) | **정식화** | 16 — 이 편이다 (14·15의 preview를 거쳤다) |
| sealed 클래스 (JEP 397) | **2차 preview** | 17 — 원문이 같은 절에 "17에서 정식화된다"고 직접 적는다 |
| Vector API (JEP 338) | **incubator** ★(1차) — 차수 「1차」는 이 편 원문에 없다. 원문 `java-17.md`의 "16의 1차 incubator(JEP 338)"에서 왔다 | 이 편에서는 아직 incubator다 — 17에서 2차(JEP 414)로 이어진다(출처: 원문 `java-17.md`) |
| Foreign-Memory Access API (JEP 393) | **3차 incubator** | 이 편에서는 아직 incubator다 — 원문이 "후일 17의 통합 FFM API(JEP 412)로 합쳐진다"고 적고, 그 FFM API의 정식화는 22(JEP 454)다(출처: 원문 `java-17.md`) |
| Foreign Linker API (JEP 389) | **incubator** | 위와 같이 17의 JEP 412로 합쳐지고, 정식화는 22(JEP 454)다(출처: 원문 `java-17.md`) |
| jpackage (JEP 392) | **정식화** | 16 — 이 편이다 (14에서 incubator였다) |

> **preview(미리보기) / incubator(인큐베이터)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 원문은 이 편에서 언어 문법 쪽에 preview를, API 쪽에 incubator를 붙여 쓴다.\
> 예: 이 편의 sealed 클래스가 "2차 preview"이고, Vector API가 "incubator"다.

> **LTS** — 장기 지원(Long-Term Support) 버전. 원문은 16을 "LTS인 17 직전 버전"이라 적고, 16 자체는 LTS가 아니라고 적는다.\
> 예: 원문 「릴리스 정보」의 표기가 "아니오 (단기 지원 릴리스, LTS인 17 직전 버전)"이다.

## 릴리스 정보
- 정식 출시일: 2021년 3월 16일
- LTS 여부: 아니오 (단기 지원 릴리스, LTS인 17 직전 버전)

## 시대적 배경

Java 16은 다음 LTS(Java 17)를 6개월 앞둔 버전이다.\
그동안 여러 차례 preview를 거치며 다듬어 온 핵심 언어 기능들을 정식화해, LTS에서 안정적으로 제공할 채비를 갖추는 성격이 강하다.\
record와 instanceof 패턴 매칭이 이 버전에서 동시에 정식 기능이 된 것이 그 증거다.

또한 모듈 시스템(Java 9) 이후 오래 끌어온 과제인 **JDK 내부 API 캡슐화**를 이 버전에서 기본 정책으로 전환했다.\
빌드 인프라를 Mercurial에서 Git/GitHub로 옮긴 것도 이 시기다.

> **캡슐화(encapsulation)** — 안쪽에서만 쓰라고 만든 것을 바깥에서 건드리지 못하게 막아 두는 것. 원문이 이 편의 전환 대상으로 든 것이 "JDK 내부 API"다.\
> 예: 원문이 「그 외 변경」에서 적은 구체적 내용이 "JDK 내부 API에 대한 리플렉션 접근을 **기본적으로 차단**"하는 것이다.

## 주요 추가 기능

### record 정식화 (JEP 395)

*(「한눈에」의 비유 표에서 "정식 포장으로 묶어 둔 짐"에 해당하는 자리다.)*

14·15의 두 차례 preview를 거쳐 정식 기능으로 확정됐다.\
불변 데이터 운반 객체를 간결하게 선언하며, 생성자·접근자·`equals`/`hashCode`/`toString`이 자동 생성된다.

> **record** — 원문 표현으로 "불변 데이터 운반 객체를 간결하게 선언"하는 타입. 원문이 이 자리에서 자동 생성된다고 든 것은 생성자·접근자와 `equals`/`hashCode`/`toString`이다.\
> 예: 아래 `record Range(int lo, int hi)`가 그 선언이고, 자동 생성된 접근자를 쓰는 곳이 `r.lo()`·`r.hi()`다.

> **컴팩트 생성자(compact constructor)** — record 이름만 적고 괄호 없이 여는 생성자 자리. 원문이 그 쓸모로 적은 것이 "검증 로직 추가 가능"이다.\
> 예: 아래 코드의 `Range { … }` 블록이 그것이고, 그 안에서 `lo > hi`이면 예외를 던진다.

```java
record Range(int lo, int hi) {
    // 컴팩트 생성자로 검증 로직 추가 가능
    Range {
        if (lo > hi) throw new IllegalArgumentException("lo > hi");
    }
}

var r = new Range(1, 10);
System.out.println(r.lo() + ".." + r.hi()); // 1..10
```

### instanceof 패턴 매칭 정식화 (JEP 394)

14·15의 preview를 거쳐 정식 기능이 됐다.\
`instanceof` 검사와 캐스팅, 바인딩 변수 선언을 한 번에 처리한다.

검사가 사라지는 것이 아니다 — 원문이 든 것은 검사와 캐스팅과 변수 선언 **셋을 한 번에** 처리한다는 것이다.

> **바인딩 변수** — 패턴이 맞았을 때 그 값이 담기는 변수. 원문은 이 편에서 그 선언까지 `instanceof` 한 줄에 함께 들어간다고 적는다.\
> 예: 아래 `obj instanceof String s`의 `s`가 그것이고, 원문이 주석에 적어 둔 대로 "패턴 변수를 조건식에서 바로 활용 가능"해 뒤이어 `s.length() > 5`를 쓴다.

```java
// 패턴 변수를 조건식에서 바로 활용 가능
if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase());
}
```

### sealed 클래스 2차 preview (JEP 397)

15의 1차 preview에 이어 다듬어진 2차 preview.\
봉인된 타입과 record를 결합하는 미래(switch 패턴 매칭)를 준비하는 단계로, 17에서 정식화된다.

### Vector API (JEP 338, incubator)

SIMD(Single Instruction Multiple Data) 하드웨어 명령으로 벡터 연산을 표현하는 API가 incubator로 처음 등장.\
CPU의 벡터 유닛을 활용해 수치 계산 성능을 끌어올린다.

> **SIMD / 벡터 연산** — 하나의 명령으로 여러 개의 값을 한꺼번에 처리하는 CPU 기능(Single Instruction Multiple Data)과, 그것을 쓰는 연산. 원문은 이 API를 그 명령으로 "벡터 연산을 표현하는 API"라 적는다.\
> 예: 아래 코드의 `va.mul(vb)`에 원문이 단 주석이 "벡터 곱"이다.

```java
// incubator 모듈: jdk.incubator.vector
var va = FloatVector.fromArray(SPECIES, a, 0);
var vb = FloatVector.fromArray(SPECIES, b, 0);
var vc = va.mul(vb);          // 벡터 곱
vc.intoArray(c, 0);
```

### 외부 메모리/링커 API (JEP 393, 389, incubator)

힙 밖 네이티브 메모리에 안전하게 접근하는 **Foreign-Memory Access API**가 3차 incubator(JEP 393)로, 네이티브 함수를 호출하는 **Foreign Linker API**가 incubator(JEP 389)로 제공됐다.\
후일 17의 통합 FFM API(JEP 412)로 합쳐진다.

> **네이티브(native) 코드 / 힙 밖 메모리** — JVM 밖에서 도는 기계어 코드(C 라이브러리 같은 것) / JVM이 관리하는 영역 바깥의 메모리.\
> 예: 원문이 이 절에서 둘을 나눠 든 그대로다 — 메모리 쪽이 Foreign-Memory Access API(JEP 393), 함수 호출 쪽이 Foreign Linker API(JEP 389)다.

### jpackage 정식화 (JEP 392)

14에서 incubator로 나온 패키징 도구가 정식 기능이 됐다.\
Java 애플리케이션을 msi·dmg·deb 등 플랫폼별 네이티브 설치 패키지로 묶는다.

## 그 외 변경

- **JDK 내부의 강한 캡슐화 (JEP 396)**: `sun.misc.Unsafe` 등 일부 예외를 빼고, JDK 내부 API에 대한 리플렉션 접근을 **기본적으로 차단**(strong encapsulation)하도록 정책을 전환. `--illegal-access` 기본값이 `permit`에서 `deny`로 바뀌어, 내부 API에 의존하던 레거시 코드의 마이그레이션을 압박했다.
- **JEP 380**: Unix 도메인 소켓 채널 지원.
- **JEP 387**: Elastic Metaspace — 미사용 메타스페이스 메모리를 OS에 더 신속히 반환.
- **JEP 376**: ZGC의 스레드 스택 처리를 동시(concurrent) 단계로 이동해 정지 시간 단축.
- **JEP 390**: 값 기반 클래스(value-based class)에 대한 경고 도입.
- **JEP 347**: C++14 언어 기능을 JDK 소스에 허용.
- **JEP 357**: 소스 코드 관리 시스템을 Mercurial에서 Git으로 이전.
- **이식성**: Alpine Linux 포트(JEP 386), Windows/AArch64 포트(JEP 388).

원문이 비용으로 적은 문장은 위 첫 불릿의 "내부 API에 의존하던 레거시 코드의 마이그레이션을 압박했다"와, 「영향과 의의」의 "단기적으로 호환성 통증을 유발했지만"이다.

> **리플렉션(reflection)** — 실행 중에 클래스·필드·메서드를 이름으로 뒤져 건드리는 기능. 이 편이 기본적으로 차단한 것은 그 접근 가운데 "JDK 내부 API"를 향한 것이다.\
> 예: 원문이 그 전환을 옵션 기본값의 변화로 적는다 — "`--illegal-access` 기본값이 `permit`에서 `deny`로 바뀌어".

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다.)*

Java 16은 LTS 직전의 "마지막 다듬기" 릴리스로서 의미가 크다.\
record와 instanceof 패턴 매칭이라는 두 핵심 문법이 동시에 정식화되면서, 곧 나올 17의 sealed 정식화·switch 패턴 매칭과 맞물려 Java의 데이터 중심·패턴 중심 프로그래밍이 완성형에 다가섰다.\
JDK 내부의 강한 캡슐화 기본화는 단기적으로 호환성 통증을 유발했지만, 모듈 시스템이 약속한 캡슐화를 현실로 만든 중요한 전환이었다.\
incubator 단계의 Vector·외부 메모리 API는 Java의 고성능·네이티브 상호운용 로드맵을 예고했다.

## 용어 풀이

- **preview(미리보기) / incubator(인큐베이터)** — 정식이 아닌 채로 먼저 실어 보내는 단계 표기. 이 편에서는 언어 문법 쪽(sealed)에 preview가, API 쪽(Vector·외부 메모리/링커)에 incubator가 붙어 있다.
- **LTS** — 장기 지원 버전. 16은 원문 표기로 "아니오 (단기 지원 릴리스, LTS인 17 직전 버전)"다.
- **캡슐화(encapsulation)** — 안쪽에서만 쓰라고 만든 것을 바깥에서 건드리지 못하게 막아 두는 것. 이 편의 전환 대상은 "JDK 내부 API"다.
- **리플렉션(reflection)** — 실행 중에 클래스·필드·메서드를 이름으로 뒤져 건드리는 기능. 이 편은 그중 JDK 내부 API를 향한 접근을 기본 차단했다.
- **record** — 원문 표현으로 "불변 데이터 운반 객체를 간결하게 선언"하는 타입. 자동 생성되는 것은 생성자·접근자와 `equals`/`hashCode`/`toString`이다. 이 편에서 정식이 됐다.
- **컴팩트 생성자(compact constructor)** — record 이름만 적고 괄호 없이 여는 생성자 자리. 원문이 든 쓸모가 "검증 로직 추가 가능"이다.
- **바인딩 변수 / 패턴 변수** — 패턴이 맞았을 때 값이 담기는 변수. 원문 주석 표현으로 "패턴 변수를 조건식에서 바로 활용 가능"하다.
- **sealed** — 상속·구현 대상을 제한하는 표시. 이 편에서는 2차 preview이고, 원문이 "17에서 정식화된다"고 적는다.
- **SIMD / 벡터 연산** — 하나의 명령으로 여러 값을 한꺼번에 처리하는 CPU 기능과 그것을 쓰는 연산. 원문 주석 표현으로 `va.mul(vb)`가 "벡터 곱"이다.
- **네이티브(native) 코드 / 힙 밖 메모리** — JVM 밖에서 도는 기계어 코드 / JVM이 관리하는 영역 바깥의 메모리. 이 편에서 각각 Foreign Linker API와 Foreign-Memory Access API가 다룬다.
- **jpackage** — 원문 표현으로 Java 애플리케이션을 "msi·dmg·deb 등 플랫폼별 네이티브 설치 패키지로 묶는" 도구. 14의 incubator를 거쳐 이 편에서 정식이 됐다.

## 참고 출처
- [OpenJDK: JDK 16](https://openjdk.org/projects/jdk/16/)
- [JEP 395: Records](https://openjdk.org/jeps/395)
- [JEP 394: Pattern Matching for instanceof](https://openjdk.org/jeps/394)
- [JEP 397: Sealed Classes (Second Preview)](https://openjdk.org/jeps/397)
- [JEP 338: Vector API (Incubator)](https://openjdk.org/jeps/338)
- [JEP 396: Strongly Encapsulate JDK Internals by Default](https://openjdk.org/jeps/396)
- [JEP 392: Packaging Tool](https://openjdk.org/jeps/392)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
