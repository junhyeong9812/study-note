# JDK 1.2 / J2SE 1.2 — "Java 2" (코드네임 Playground, 1998년 12월)

> 원본: `~/project/java-history/java/jdk-1.2.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/패키지 이름·코드블록 3개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> ASCII 도식 1개와 「한눈에」의 가구 비유·대응표, 용어 블록의 「예:」, 「용어 풀이」, 다른 편을 가리키는 교차 주 2개, 재서술자 주 1개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 자바 역사상 가장 큰 분수령 중 하나. Swing과 Collections Framework가 등장하고, "Java 2" 브랜딩과 함께 J2SE/J2EE/J2ME로 플랫폼이 분화한 버전이다.

이 편의 Swing을 하나의 비유로 읽으면 **묵는 집의 가구를 빌려 쓰던 것을, 내 가구를 직접 들고 다니는 것으로 바꾼 일**이다.\
남의 가구를 빌려 쓰면 집집마다 의자 모양과 높이가 달라진다.\
내 가구를 들고 다니면 어느 집에 묵든 같은 의자에 앉게 되고, 마음에 들지 않으면 같은 가구의 겉천을 통째로 바꿀 수도 있다.

**Swing도 똑같은 구조다** — 원문 자신이 이렇게 적는다: "AWT의 네이티브 피어 의존을 벗어나, 모든 플랫폼에서 동일하게 동작하고 Look & Feel을 교체할 수 있다".

본문 흐름에 쓰는 비유는 이 가구 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 묵는 집의 가구를 빌려 쓰는 것 | 원문 표현으로 "AWT의 네이티브 피어 의존" |
| 집집마다 의자 모양이 달라지는 것 | 원문이 1.2 이전 상태로 적은 "GUI(AWT)는 여전히 무겁고 플랫폼 의존적이었으며" |
| 내 가구를 직접 들고 다니는 것 | 원문 표현으로 "순수 자바로 그려지는 경량(lightweight) GUI 툴킷" |
| 같은 가구의 겉천을 통째로 바꾸는 것 | 원문 표현으로 "Look & Feel을 교체할 수 있다" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **"Java 2"는 버전 번호 2가 아니다.**\
  원문이 「릴리스 정보」에 직접 적는다 — "버전 번호는 1.2지만 "Java 2"로 마케팅됨".
- **세 에디션이 이 버전에서 한꺼번에 출범한 것이 아니다.**\
  원문이 「시대적 배경」에 직접 적는다 — "다만 세 에디션이 한 시점에 동시에 출범한 것은 아니고, Standard Edition이 먼저 자리잡은 뒤 Micro/Enterprise 에디션이 이듬해에 별도로 출범했다".
- **이 시점의 컬렉션 코드는 지금 모습과 다르다.**\
  원문이 컬렉션 코드 주석에 직접 적어 둔 그대로다 — "1.2 당시 문법은 raw type + 명시적 캐스트 + Iterator".

## 릴리스 정보
- 정식 출시일: 1998년 12월 (릴리스 표상의 1.2.0 빌드 날짜는 1998-12-04, Sun의 공식 발표·일반 가용성 기준으로는 1998-12-08로 출처에 따라 갈린다)
- 개발 주체: Sun Microsystems
- 공식 명칭: J2SE 1.2 (Java 2 Platform, Standard Edition) — 버전 번호는 1.2지만 "Java 2"로 마케팅됨
- 코드네임: Playground (일부 출처에서만 쓰이는 비공식 명칭. Sun의 공식 코드네임 관행은 1.3 Kestrel부터 본격화됨)

*(교차 주: 넷째 불릿이 말하는 "1.3 Kestrel부터"는 뒤의 편과 맞물린다 — `jdk-1.3` 편이 자기 코드네임을 "Kestrel (황조롱이)"로 적고, 「영향과 의의」에서 "이 무렵부터 자바 릴리스에 코드네임이 본격적으로 붙기 시작했다"고 적는다.)*

## 시대적 배경

JDK 1.1까지 자바는 빠르게 성장했지만, GUI(AWT)는 여전히 무겁고 플랫폼 의존적이었으며, 자료구조 API는 `Vector`/`Hashtable` 수준으로 일관성이 떨어졌다.\
동시에 자바의 적용 범위가 데스크톱·서버·임베디드로 넓어지면서 하나의 JDK로 모든 영역을 감당하기 어려워졌다.

*(원문이 「시대적 배경」에서 부족·한계로 적은 자리는 위 두 줄이다 — 이는 1.2가 치른 대가가 아니라 1.2가 나온 동기다.)*

Sun은 이 버전을 "Java 2"로 새롭게 브랜딩하며, 플랫폼을 용도별로 나누는 방향을 잡았다. 다만 세 에디션이 한 시점에 동시에 출범한 것은 아니고, Standard Edition이 먼저 자리잡은 뒤 Micro/Enterprise 에디션이 이듬해에 별도로 출범했다:
- **J2SE** (Standard Edition) — 데스크톱/일반 애플리케이션 (Java 2 SE, 1998-12)
- **J2ME** (Micro Edition) — 모바일/임베디드 (별도 출범 1999-06)
- **J2EE** (Enterprise Edition) — 서버/엔터프라이즈 (별도 출범 1999-12)

세 불릿의 괄호 안 날짜가 위 문장의 "이듬해에 별도로 출범했다"와 맞는다 — SE가 1998년, 나머지 둘이 1999년이다.

> **에디션(edition)** — 같은 플랫폼을 쓰임새별로 갈라 따로 묶어 낸 판.\
> 예: 원문이 이 자리에서 든 셋이 J2SE(데스크톱/일반 애플리케이션)·J2ME(모바일/임베디드)·J2EE(서버/엔터프라이즈)다.

## 주요 추가 기능

### Swing

- 순수 자바로 그려지는 경량(lightweight) GUI 툴킷. AWT의 네이티브 피어 의존을 벗어나, 모든 플랫폼에서 동일하게 동작하고 Look & Feel을 교체할 수 있다.
- 컴포넌트 이름 앞에 `J`가 붙는다(`JButton`, `JFrame`, `JTable` 등). 이후 10여 년간 자바 데스크톱 GUI의 표준이 되었다.

위 첫 불릿 한 문장의 앞뒤를 두 칸에 나눠 놓으면 이렇다.

```text
왼쪽 칸 = Swing이 "벗어나"라고 원문이 적은 대상   오른쪽 칸 = Swing에 대해 적은 것
+----------------------------------+      +----------------------------------+
|  "AWT의 네이티브 피어 의존"      |      |  "순수 자바로 그려지는            |
|                                  |      |   경량(lightweight) GUI 툴킷"     |
|                                  |      |  "모든 플랫폼에서 동일하게        |
|                                  |      |   동작하고 Look & Feel을          |
|                                  |      |   교체할 수 있다"                 |
+----------------------------------+      +----------------------------------+
```

두 칸 모두 위 첫 불릿 한 문장에서 뽑은 것이다 — 왼쪽이 그 문장에서 "벗어나"의 대상으로 적힌 것, 오른쪽이 벗어난 뒤의 상태로 적힌 것이다.\
원문은 이 두 칸을 항목별로 하나씩 짝지어 적지는 않는다.

> **경량(lightweight) 컴포넌트** — 운영체제의 화면 부품을 빌리지 않고 자바가 직접 그려 내는 화면 요소.\
> 예: 원문이 이 자리에서 Swing을 부르는 말이 "순수 자바로 그려지는 경량(lightweight) GUI 툴킷"이다.

> **Look & Feel** — 화면의 생김새와 조작감을 통째로 정해 둔 한 벌. 원문은 이것을 "교체할 수 있다"고 적는다.\
> 예: 원문은 Swing이 "모든 플랫폼에서 동일하게 동작"한다고 적으면서, 그 Look & Feel은 "교체할 수 있다"고 적는다.

```java
import javax.swing.*;

public class Demo {
    public static void main(String[] args) {
        JFrame f = new JFrame("Swing 예제");
        // 1.2~1.4에서는 JFrame.add()를 직접 호출하면 런타임 오류가 난다.
        // 컨텐트 페인에 추가해야 한다(JFrame.add 위임은 J2SE 5.0부터).
        f.getContentPane().add(new JButton("클릭"));
        f.setSize(200, 100);
        f.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        f.setVisible(true);
    }
}
```

위 코드가 주석으로 이 시점의 제약을 알려 준다 — `f.getContentPane().add(…)`로 적은 것이 주석의 "컨텐트 페인에 추가해야 한다"이고, 그러지 않아도 되는 시점을 주석은 "J2SE 5.0부터"로 적는다.

### 컬렉션 프레임워크(Collections Framework)

- `List`, `Set`, `Map` 인터페이스와 `ArrayList`, `HashMap`, `TreeMap`, `LinkedList` 등 구현체, 그리고 `Collections`/`Arrays` 유틸리티, `Iterator`를 통합 제공.
- 기존의 산발적인 `Vector`/`Hashtable`을 일관된 체계로 대체하여, 자바 프로그래밍의 데이터 처리 방식을 표준화했다.

둘째 불릿의 `Vector`/`Hashtable`은 `jdk-1.0` 편이 "초기 자료구조(아직 Collections Framework 이전)"로 든 바로 그것들이다.

> **컬렉션 프레임워크** — 여러 값을 담는 자료구조를 공통 인터페이스로 묶어 둔 체계.\
> 예: 원문이 이 자리에서 든 인터페이스가 `List`, `Set`, `Map`이고, 구현체가 `ArrayList`, `HashMap`, `TreeMap`, `LinkedList`다.

```java
import java.util.*;

// 제네릭·diamond·for-each·오토박싱은 모두 J2SE 5.0부터다.
// 1.2 당시 문법은 raw type + 명시적 캐스트 + Iterator.
List list = new ArrayList();
list.add("a");
list.add("b");
Collections.sort(list);

Map map = new HashMap();
map.put("one", new Integer(1));   // 오토박싱이 없으므로 명시적 래핑
Iterator it = map.entrySet().iterator();
while (it.hasNext()) {
    Map.Entry e = (Map.Entry) it.next();
    System.out.println(e.getKey() + "=" + e.getValue());
}
```

위 코드가 둘째 주석의 세 가지를 그대로 보여 준다 — `new ArrayList()`에 타입 인자가 없는 것이 raw type, `(Map.Entry) it.next()`가 명시적 캐스트, `while (it.hasNext())`가 `Iterator`다.\
`new Integer(1)`에 붙은 주석 "오토박싱이 없으므로 명시적 래핑"도 같은 제약을 가리킨다.

> **재서술자 주:** 위 첫 주석이 든 넷 중 `diamond`는 J2SE 5.0이 아니라 Java SE 7의 기능으로 보인다. 같은 시리즈의 `java-7` 편이 「다이아몬드 연산자 (Diamond Operator, `<>`)」를 그 편의 절로 두고 있고, 원문 repo의 `README`(`~/project/java-history/java/README.md`) 표도 diamond를 Java SE 7 행에 적는다. 나머지 셋(제네릭·for-each·오토박싱)은 `java-5` 편의 서술과 맞는다. 원문 코드블록은 고치지 않고 그대로 두었다.

### JIT 컴파일러 기본 탑재

- Sun JVM에 JIT(Just-In-Time) 컴파일러가 기본 포함되어, 바이트코드를 실행 시점에 네이티브 코드로 변환함으로써 성능이 크게 향상되었다.

> **JIT(Just-In-Time) 컴파일러** — 원문 표현 그대로 "바이트코드를 실행 시점에 네이티브 코드로 변환"하는 컴파일러.\
> 예: `jdk-1.1` 편이 "Windows 환경에서의" 지원으로 적었던 것이, 이 편에서 "기본 포함"이 된다.

### strictfp 키워드

- 부동소수점 연산이 플랫폼과 무관하게 IEEE 754 규약대로 동일한 결과를 내도록 강제하는 키워드. 플랫폼 독립성을 수치 연산 영역까지 확장했다.

```java
public strictfp class Calc {
    double compute(double a, double b) { return a * b; }
}
```

*(교차 주: 이 키워드의 뒷이야기는 `java-17` 편이 적는다 — 그 편은 "항상 엄격한 부동소수점 (JEP 306)"에서 "`strictfp` 의미를 기본으로 되돌려, 모든 플랫폼에서 동일한 부동소수점 결과를 보장"한다고 적는다.)*

> **IEEE 754** — 부동소수점 수를 어떻게 저장하고 계산할지 정해 둔 표준.\
> 예: 원문은 `strictfp`를 "플랫폼과 무관하게 IEEE 754 규약대로 동일한 결과를 내도록 강제하는 키워드"로 적는다.

## 그 외 변경 / API 추가
- Java Plug-in: 브라우저에서 Sun JRE로 애플릿을 실행하게 해주는 플러그인.
- Java IDL: CORBA와의 연동을 위한 IDL 지원.
- 정책 기반 보안 모델(Policy/Permission) 강화 — 세분화된 권한 제어.
- 접근성(Accessibility) API, 드래그 앤 드롭(DnD) 등 추가. (`Collator`는 이미 JDK 1.1부터 제공되던 API다)

넷째 불릿의 괄호는 원문이 스스로 달아 둔 단서다 — `Collator`는 "이미 JDK 1.1부터 제공되던 API"라서 이 편의 추가가 아니다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 불릿은 원문 한 문단을 문장 단위로 끊은 것이다.)*

- J2SE 1.2는 "Java 2"라는 이름이 보여주듯 사실상 자바의 2세대를 연 버전이다.
- Swing은 데스크톱 자바의 표준이 되었고, 컬렉션 프레임워크는 오늘날까지 모든 자바 코드의 기본 도구로 쓰인다.
- 플랫폼의 SE/EE/ME 분화는 자바가 임베디드부터 대형 서버까지 전 영역을 아우르는 생태계로 확장되는 출발점이었다.
- "Java 2" 브랜딩은 이후 J2SE 5.0(2004)까지 약 6년간 유지되었다.

## 용어 풀이

- **에디션(edition)** — 같은 플랫폼을 쓰임새별로 갈라 따로 묶어 낸 판. 원문이 든 셋이 J2SE·J2ME·J2EE이고, 셋이 동시에 출범한 것은 아니라고 원문이 못 박는다.
- **경량(lightweight) 컴포넌트** — 운영체제의 화면 부품을 빌리지 않고 자바가 직접 그려 내는 화면 요소. 원문이 Swing을 부르는 말이 "순수 자바로 그려지는 경량(lightweight) GUI 툴킷"이다.
- **네이티브 피어(native peer) 의존** — 화면 요소를 운영체제의 것에 기대어 만드는 것. 원문은 Swing이 이 의존을 "벗어나"면서 "모든 플랫폼에서 동일하게 동작"하게 됐다고 적는다.
- **Look & Feel** — 화면의 생김새와 조작감을 통째로 정해 둔 한 벌. 원문은 이것을 "교체할 수 있다"고 적는다.
- **컨텐트 페인(content pane)** — `JFrame`에 컴포넌트를 담을 때 거쳐야 하는 안쪽 영역. 원문 코드 주석은 1.2~1.4에서 `JFrame.add()`를 직접 부르면 런타임 오류가 나며, 위임은 J2SE 5.0부터라고 적는다.
- **컬렉션 프레임워크(Collections Framework)** — 여러 값을 담는 자료구조를 공통 인터페이스로 묶어 둔 체계. 원문이 든 인터페이스가 `List`·`Set`·`Map`이다.
- **raw type** — 타입 인자를 붙이지 않은 제네릭 타입. 원문 코드 주석은 1.2 당시 문법을 "raw type + 명시적 캐스트 + Iterator"로 적는다.
- **`Iterator`** — 컬렉션의 요소를 하나씩 꺼내 순회하게 해 주는 객체. 원문 코드의 `while (it.hasNext())`가 그 쓰임이다.
- **JIT(Just-In-Time) 컴파일러** — 원문 표현 그대로 "바이트코드를 실행 시점에 네이티브 코드로 변환"하는 컴파일러. 이 편에서 Sun JVM에 기본 포함됐다.
- **`strictfp`** — 원문 표현 그대로 "부동소수점 연산이 플랫폼과 무관하게 IEEE 754 규약대로 동일한 결과를 내도록 강제하는 키워드".
- **IEEE 754** — 부동소수점 수를 어떻게 저장하고 계산할지 정해 둔 표준. 원문이 `strictfp`의 기준으로 든 규약이다.

## 참고 출처
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [Java 1.2 - javaalmanac.io](https://javaalmanac.io/jdk/1.2/)
- [JDK release dates - Java Glossary (mindprod)](https://www.mindprod.com/jgloss/jdkreleasedates.html)
