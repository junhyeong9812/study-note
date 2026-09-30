# Java 14 (2020년 3월)

> 원본: `~/project/java-history/java/java-14.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션 이름·코드블록 5개(java 4 · text 1)·「릴리스 정보」와 「그 외 변경」의 목록은 원문 그대로다.\
> 「한눈에」의 씨앗 비유와 대응표, 「이 편에서 미리보기인가 정식인가」 표, 용어 블록의 「예:」, 「용어 풀이」, 「재서술자 주」 1개는 원문에 없는 보충이다. 새 도식은 없다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> switch 표현식을 정식 기능으로 확정하고, record·패턴 매칭·텍스트 블록 같은 현대 Java 문법의 씨앗을 preview로 대거 심은 릴리스.

이 편을 읽는 비유는 원문이 스스로 쓴 낱말 **씨앗** 하나다.\
한 밭에 **올해 거둔 것**과 **올해 심은 씨앗**과 **작년에 심어 올해 한 번 더 손본 것**이 함께 있는 상태다.\
원문이 「시대적 배경」에서 이 셋을 나란히 적는다 — "switch 표현식은 12·13에서 두 차례 preview를 거쳐 이번에 정식화됐고, record·instanceof 패턴 매칭은 처음 preview로 등장했으며, 텍스트 블록은 두 번째 preview에 들어갔다."

| 비유 | 실체 |
|---|---|
| 올해 거둔 것 | switch 표현식 — 원문 표현으로 "12·13에서 두 차례 preview를 거쳐 이번에 정식화됐고" |
| 올해 심은 씨앗 | record·instanceof 패턴 매칭 — 원문 표현으로 "처음 preview로 등장했으며" |
| 작년에 심어 올해 한 번 더 손본 것 | 텍스트 블록 — 원문 표현으로 "두 번째 preview에 들어갔다" |

### 이 편에서 미리보기인가 정식인가

초보자가 이 편에서 흔히 하는 오해가 "Java 14를 쓰면 이 목록이 전부 그냥 쓰인다"이다.\
원문은 기능마다 절 제목·불릿에 상태를 적어 두었다. 그 상태를 한자리에 모으면 이렇다.

| 기능 | 이 편(14)에서의 상태 — 원문 절 제목·불릿 표기 | 정식이 된 편 |
|---|---|---|
| record (JEP 359) | **preview** | 16 (JEP 395) — 출처: 원문 `java-16.md` |
| instanceof 패턴 매칭 (JEP 305) | **preview** | 16 (JEP 394) — 출처: 원문 `java-16.md` |
| 텍스트 블록 (JEP 368) | **2차 preview** | 15 (JEP 378) — 출처: 원문 `java-15.md` |
| jpackage (JEP 343) | **incubator** | 16 (JEP 392) — 출처: 원문 `java-16.md` |
| Foreign-Memory Access API (JEP 370) | **incubator** | 이 편 뒤로도 incubator가 이어진다 — 15에서 2차(JEP 383), 16에서 3차(JEP 393). 출처: 원문 `java-15.md`·`java-16.md` |

나머지 셋(switch 표현식 JEP 361 · 유용한 NullPointerException JEP 358 · JFR 이벤트 스트리밍 JEP 349)은 절 제목대로 **정식**이고, 정식이 된 편도 14다 — 다만 NPE 상세 메시지는 기본 비활성화다(아래 참고).

> **preview(미리보기) / incubator(인큐베이터)** — 정식 기능이 아직 아닌 상태로 먼저 실어 보내는 단계 / 원문이 preview와 나란히 쓰는 또 하나의 미완성 단계 표기(이 편에서는 도구·API 쪽인 jpackage, Foreign-Memory Access API에 붙어 있다). 원문은 preview 제도를 "새 문법을 **preview 기능**으로 먼저 내보내 커뮤니티 피드백을 받고, 다듬어 정식화하는 점진적 전략"이라 적는다.\
> 예: 원문 절 제목이 `record (JEP 359, preview)`·`instanceof 패턴 매칭 (JEP 305, preview)`이고, 「그 외 변경」의 불릿이 "패키징 도구 jpackage (JEP 343, incubator)"다.

## 릴리스 정보
- 정식 출시일: 2020년 3월 17일
- LTS 여부: 아니오 (단기 지원 릴리스, 다음 버전 출시까지만 지원)

## 시대적 배경

Java는 9 버전부터 6개월 주기 릴리스 모델로 전환했고, Java 14는 그 흐름 속의 한 단계였다.\
짧은 주기 덕분에 새 문법을 **preview 기능**으로 먼저 내보내 커뮤니티 피드백을 받고, 다듬어 정식화하는 점진적 전략이 자리를 잡던 시기다.

Java 14는 이 전략의 대표 사례다.\
switch 표현식은 12·13에서 두 차례 preview를 거쳐 이번에 정식화됐고, record·instanceof 패턴 매칭은 처음 preview로 등장했으며, 텍스트 블록은 두 번째 preview에 들어갔다.\
"한 번에 큰 변화"가 아니라 "여러 번에 걸친 안전한 진화"라는 모던 Java의 개발 문화가 뚜렷이 드러난다.

> **재서술자 주:** 위 첫 문장의 "9 버전부터"는 같은 시리즈 9편·10편과 어긋난다. 원문 `java-9.md`는 "Java 9는 옛 모델의 마지막 메이저 릴리스가 되었고, 6개월 뒤 Java 10(2018년 3월)이 새 모델의 첫 릴리스로 나왔다"고 적고, 원문 `java-10.md`는 10을 "6개월 릴리스 케이던스의 첫 결과물"이라 적는다. 새 모델로 **전환이 발표된** 것이 9 시점(2017년 9월)이고 **그 모델로 나온 첫 릴리스**는 10이라는 뜻으로 읽는 것이 맞아 보인다.

## 주요 추가 기능

### switch 표현식 (JEP 361, 정식)

*(「한눈에」의 비유 표에서 "올해 거둔 것"에 해당하는 자리다.)*

12·13의 두 차례 preview를 거쳐 정식 기능으로 확정됐다.\
switch를 **문장(statement)** 뿐 아니라 **값을 반환하는 표현식(expression)** 으로 쓸 수 있다.\
화살표(`->`) 문법으로 fall-through와 break 누락 버그를 제거하고, `yield`로 블록에서 값을 반환한다.

> **문장(statement) / 표현식(expression)** — 시키기만 하고 값을 남기지 않는 코드 / 값을 하나 내놓아 그 자리에 대입할 수 있는 코드.\
> 예: 아래 코드의 `switch (day) { … }` 전체가 `int numLetters =`의 오른쪽에 놓였다 — 원문 표현으로 "값을 반환하는 표현식"으로 쓰인 것이다.

> **fall-through** — 한 `case`를 처리하고 멈추지 않고 다음 `case`로 흘러내리는 동작. 원문은 이것과 "break 누락 버그"를 화살표 문법이 제거한 것으로 적는다.\
> 예: 아래 코드에는 `break`가 한 번도 나오지 않는다 — 각 `case`가 `->` 뒤에 값을 바로 적는다.

> **`yield`** — 화살표 뒤에 블록 `{ }`을 쓸 때, 그 블록에서 값을 내보내는 키워드.\
> 예: 아래 `default` 블록의 마지막 줄 `yield len;`에 원문이 단 주석이 "블록에서 값 반환"이다.

```java
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    case THURSDAY, SATURDAY     -> 8;
    case WEDNESDAY              -> 9;
    default -> {
        int len = day.toString().length();
        yield len; // 블록에서 값 반환
    }
};
```

### record (JEP 359, preview)

불변 데이터를 담는 클래스를 한 줄로 선언하는 새 타입.\
생성자, 접근자, `equals`/`hashCode`/`toString`이 자동 생성된다.\
보일러플레이트 제거가 목표이며, 이 버전에서 처음 preview로 등장했다.

> **record** — 원문 표현으로 "불변 데이터를 담는 클래스를 한 줄로 선언하는 새 타입". 원문이 이 자리에서 자동 생성된다고 든 것은 생성자·접근자와 `equals`/`hashCode`/`toString`이다.\
> 예: 아래 `record Point(int x, int y) { }` 한 줄이 그 선언이고, 원문이 주석으로 "자동 생성된 접근자"라 가리킨 것이 `p.x()`다.

> **보일러플레이트(boilerplate)** — 뜻은 거의 없는데 형식상 매번 똑같이 써야 하는 코드. 원문은 record의 목표를 "보일러플레이트 제거"라고 적는다.\
> 예: 원문이 record가 대신 만들어 준다고 든 생성자·접근자·`equals`/`hashCode`/`toString`이 그동안 손으로 적던 자리다.

```java
record Point(int x, int y) { }

var p = new Point(3, 4);
System.out.println(p.x());      // 3 (자동 생성된 접근자)
System.out.println(p);          // Point[x=3, y=4]
```

### instanceof 패턴 매칭 (JEP 305, preview)

`instanceof` 검사와 형 변환을 한 번에 처리한다.\
검사에 성공하면 바인딩 변수에 캐스팅된 값이 자동으로 들어가, 별도 캐스팅 코드가 사라진다.

검사 자체가 없어지는 것이 아니다 — 원문의 두 문장이 말하는 것은 검사와 형 변환이 **한 번에** 처리된다는 것이고, 값이 들어가는 조건도 "검사에 성공하면"이다.

> **바인딩 변수** — 패턴이 맞았을 때 그 값이 자동으로 담기는 변수. 원문은 여기에 "캐스팅된 값이 자동으로 들어"간다고 적는다.\
> 예: 아래 `obj instanceof String s`의 `s`가 그것이고, 원문이 단 주석이 "s는 이미 String으로 캐스팅됨"이다.

```java
if (obj instanceof String s) {
    // s는 이미 String으로 캐스팅됨
    System.out.println(s.length());
}
```

### 유용한 NullPointerException (JEP 358, 정식)

NPE 발생 시 **정확히 어떤 변수/표현식이 null이었는지**를 메시지에 담아 알려준다. 디버깅 시간을 크게 줄여준다.

**기본으로 켜지는 것은 언제부터인가** — 원문이 같은 절에 적어 둔 그대로다: "다만 14에서는 이 상세 메시지가 **기본 비활성화**라 `-XX:+ShowCodeDetailsInExceptionMessages` 옵션을 켜야 하며, 기본 활성화는 JDK 15부터다."

> **NullPointerException(NPE)** — 값이 없는(`null`) 것을 대상으로 무언가를 하려 할 때 나는 오류. 이 변경은 그 오류의 **메시지**를 바꾼 것이다.\
> 예: 아래 메시지가 `null`이었던 대상을 `"<local1>.name"`이라고 집어 준다.

```text
Cannot invoke "String.toLowerCase()" because "<local1>.name" is null
```

### 텍스트 블록 (JEP 368, 2차 preview)

여러 줄 문자열을 `"""`로 감싸 가독성 있게 작성한다.\
13에서 1차 preview로 나왔고, 14에서 `\`(줄 이음), `\s`(공백 유지) 이스케이프가 추가된 2차 preview가 됐다.

> **텍스트 블록** — 원문 표현으로 "여러 줄 문자열을 `"""`로 감싸 가독성 있게 작성"하는 문법. 14 시점에는 아직 2차 preview이고, 정식이 되는 것은 15(JEP 378)다(출처: 원문 `java-15.md`).\
> 예: 아래 코드에서 여는 `"""`와 닫는 `"""` 사이의 다섯 줄이 그대로 문자열이 된다.

```java
String html = """
        <html>
            <body>
                <p>Hello</p>
            </body>
        </html>
        """;
```

### JFR 이벤트 스트리밍 (JEP 349, 정식)

JDK Flight Recorder의 데이터를 파일로 덤프하지 않고 **실시간 스트림**으로 소비할 수 있게 했다.\
모니터링·관측(observability) 도구가 애플리케이션 성능 데이터를 즉시 받아볼 수 있다.

> **JDK Flight Recorder(JFR)** — JVM이 자기 동작 데이터를 기록해 두는 장치. 이 변경 전에는 원문 표현으로 그 데이터를 "파일로 덤프"해서 봐야 했다.\
> 예: 원문이 이 변경의 수혜자로 든 것이 "모니터링·관측(observability) 도구"다.

## 그 외 변경

- **패키징 도구 jpackage (JEP 343, incubator)**: 플랫폼별 네이티브 설치 패키지(msi, dmg, deb 등)를 만드는 도구가 incubator로 도입.
- **Foreign-Memory Access API (JEP 370, incubator)**: 힙 밖 네이티브 메모리에 안전하게 접근하는 API가 incubator로 시작.
- **JEP 345**: G1 GC의 NUMA 인식 메모리 할당.
- **JEP 352**: 비휘발성(NVM) 매핑 ByteBuffer 지원.
- **JEP 364**: ZGC를 macOS로 포팅 (JEP 365는 Windows로 포팅).
- **제거/지원 중단**: CMS 가비지 컬렉터 제거(JEP 363), Pack200 도구·API 제거(JEP 367), Solaris/SPARC 포트 지원 중단(JEP 362), ParallelScavenge+SerialOld GC 조합 지원 중단(JEP 366).

> **힙 밖(off-heap) 메모리** — JVM이 관리하는 영역 바깥의 메모리. 원문은 Foreign-Memory Access API를 "힙 밖 네이티브 메모리에 안전하게 접근하는 API"라 적는다.\
> 예: 이 API는 이 편에서 incubator로 시작해, 원문 `java-16.md`가 3차 incubator(JEP 393)로, `java-17.md`가 링커와 합친 FFM API(JEP 412)로 이어 적는다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다.)*

Java 14는 "모던 Java 문법"의 토대를 놓은 분기점이다.\
이후 LTS인 Java 17을 화려하게 만든 record·패턴 매칭·텍스트 블록·sealed 같은 기능들의 출발선이 대부분 이 버전(혹은 직전)에 있다.\
switch 표현식 정식화로 함수형 스타일이 표준 문법에 편입됐고, 유용한 NPE 메시지는 일상적인 개발 경험을 즉시 개선했다.\
preview 제도를 적극 활용해 큰 언어 변화를 안전하게 굴려가는 모던 Java 개발 모델을 가장 잘 보여준 릴리스이기도 하다.

## 용어 풀이

본문에 용어 블록이 있는 말은 그 블록이 정본이다(한정어가 줄어드는 것을 막으려 여기서 다시 풀지 않는다). 어느 절에 있는지만 적는다.

- **preview(미리보기) / incubator(인큐베이터)** — 「이 편에서 미리보기인가 정식인가」의 용어 블록.
- **JEP 번호 / LTS·단기 지원 릴리스** — OpenJDK가 제안 하나에 매기는 고유 번호(JDK Enhancement Proposal)로, 같은 기능이 단계를 올릴 때마다 새 번호를 받는다 / 장기간 지원을 받는 버전과, 원문 표현으로 "다음 버전 출시까지만 지원"되는 버전의 구분 — 14는 후자다. (시리즈 공통 용어라 이 편에는 본문 블록을 두지 않았다.)
- **문장(statement) / 표현식(expression) / fall-through / `yield`** — 「switch 표현식 (JEP 361, 정식)」 절의 용어 블록.
- **record / 보일러플레이트(boilerplate) / 바인딩 변수** — 「record (JEP 359, preview)」·「instanceof 패턴 매칭 (JEP 305, preview)」 절의 용어 블록.
- **NullPointerException(NPE) / 텍스트 블록 / JDK Flight Recorder(JFR) / 힙 밖(off-heap) 메모리** — 각각 그 기능의 절과 「그 외 변경」의 용어 블록.

## 참고 출처
- [OpenJDK: JDK 14](https://openjdk.org/projects/jdk/14/)
- [JEP 361: Switch Expressions](https://openjdk.org/jeps/361)
- [JEP 359: Records (Preview)](https://openjdk.org/jeps/359)
- [JEP 305: Pattern Matching for instanceof (Preview)](https://openjdk.org/jeps/305)
- [JEP 358: Helpful NullPointerExceptions](https://openjdk.org/jeps/358)
- [JEP 368: Text Blocks (Second Preview)](https://openjdk.org/jeps/368)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
