# JDK 1.3 / J2SE 1.3 (코드네임 Kestrel, 2000년 5월)

> 원본: `~/project/java-history/java/jdk-1.3.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·클래스/패키지 이름·코드블록 2개·「릴리스 정보」와 「그 외 변경 / API 추가」의 목록은 원문 그대로다.\
> 「한눈에」의 창고 비유·대응표, 용어 블록의 「예:」, 「용어 풀이」, 다른 편을 가리키는 교차 주 2개는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 성능과 안정성에 집중한 버전. HotSpot JVM을 기본 탑재하여 자바의 고질적 약점이던 실행 속도를 크게 개선하고, JNDI·JPDA·Java Sound 등 플랫폼 인프라를 보강했다.

이 편의 HotSpot을 하나의 비유로 읽으면 **창고의 모든 품목을 똑같이 다루는 대신, 어느 품목이 자주 나가는지 지켜보다가 그것에만 전용 라인을 까는 일**이다(무엇이 자주 나갈지는 미리 알 수 없으니 돌려 보고 그때 정한다).

**HotSpot도 똑같은 구조다** — 원문 자신이 이렇게 적는다: "자주 실행되는 "핫스팟" 코드를 런타임에 분석하여 집중적으로 네이티브 컴파일·최적화함으로써, 단순 JIT보다 뛰어난 성능을 냈다".

본문 흐름에 쓰는 비유는 이 창고 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 자주 나가는 품목 | 원문 표현으로 "자주 실행되는 "핫스팟" 코드" |
| 돌려 보면서 세어 보고 그때 정하는 것 | 원문 표현으로 "런타임에 분석하여", 원문이 붙인 이름으로 "적응형 최적화(adaptive optimization)" |
| 그 품목에만 전용 라인을 까는 것 | 원문 표현으로 "집중적으로 네이티브 컴파일·최적화" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **이 버전은 "새 문법"의 버전이 아니다.**\
  원문이 「시대적 배경」에서 성격을 직접 적는다 — "그 기능들을 "실제 운영 환경에서 빠르고 안정적으로" 돌아가게 만드는 데 초점을 맞춘 점진적·성숙화 버전이다".
- **JNDI가 이 버전에서 처음 만들어진 것은 아니다.**\
  원문은 "이전에는 별도 확장으로 제공되던 JNDI가 코어 플랫폼에 통합되었다"고 적는다 — 새로 생긴 것이 아니라 들어온 것이다.

## 릴리스 정보
- 정식 출시일: 2000년 5월 8일
- 개발 주체: Sun Microsystems
- 공식 명칭: J2SE 1.3 (Java 2 Platform, Standard Edition v1.3)
- 코드네임: Kestrel (황조롱이)

## 시대적 배경

J2SE 1.2가 기능을 대폭 확장했다면, 1.3은 그 기능들을 "실제 운영 환경에서 빠르고 안정적으로" 돌아가게 만드는 데 초점을 맞춘 점진적·성숙화 버전이다.\
당시 자바는 여전히 "느리다"는 비판을 받았는데, Sun이 인수한 기술을 바탕으로 한 HotSpot JVM의 기본 탑재가 이 인식을 바꾸는 전환점이 되었다.\
같은 시기 J2EE 기반 서버 애플리케이션이 본격 확산되면서, JNDI 같은 엔터프라이즈 연계 API의 표준 포함도 중요했다.

*(원문이 「시대적 배경」에서 약점으로 적은 자리는 위 둘째 줄의 "당시 자바는 여전히 "느리다"는 비판을 받았는데"다 — 이는 1.3이 치른 대가가 아니라 1.3이 나온 동기다.)*

## 주요 추가 기능

### HotSpot JVM 기본 탑재

- 적응형 최적화(adaptive optimization)를 수행하는 HotSpot 가상 머신이 기본 JVM이 되었다.
- 자주 실행되는 "핫스팟" 코드를 런타임에 분석하여 집중적으로 네이티브 컴파일·최적화함으로써, 단순 JIT보다 뛰어난 성능을 냈다. 이로써 자바의 "느리다"는 평판이 본격적으로 개선되기 시작했다.

> **적응형 최적화(adaptive optimization)** — 미리 정해 두지 않고, 돌아가는 동안 관찰한 결과에 맞춰 최적화 대상을 고르는 방식.\
> 예: 원문이 그 관찰 대상으로 든 것이 "자주 실행되는 "핫스팟" 코드"다.

### JNDI (Java Naming and Directory Interface)

- 이전에는 별도 확장으로 제공되던 JNDI가 코어 플랫폼에 통합되었다.
- LDAP, DNS, RMI 레지스트리 등 다양한 네이밍·디렉터리 서비스를 통일된 API로 조회·바인딩할 수 있게 했다. J2EE에서 데이터소스·EJB 룩업의 핵심 메커니즘이 되었다.

> **네이밍·디렉터리 서비스** — "이 이름으로 등록된 것이 무엇인가"를 물어보면 답해 주는 서비스.\
> 예: 원문이 이 자리에서 든 것이 LDAP, DNS, RMI 레지스트리다.

> **룩업(lookup)** — 이름을 주고 그 이름에 묶인 것을 받아 오는 일.\
> 예: 아래 코드의 `ctx.lookup("java:comp/env/jdbc/MyDB")`가 그것이고, 원문이 든 쓰임이 "J2EE에서 데이터소스·EJB 룩업"이다.

```java
import javax.naming.*;

Context ctx = new InitialContext();
Object obj = ctx.lookup("java:comp/env/jdbc/MyDB");
```

### JPDA (Java Platform Debugger Architecture)

- 표준 디버깅 인프라. 1.3에서는 JVMDI(JVM Debug Interface), JDWP(디버그 와이어 프로토콜), JDI(디버그 인터페이스)로 구성되어, IDE와 도구들이 일관된 방식으로 자바 프로그램을 원격 디버깅할 수 있게 했다. (저수준 JVMDI는 이후 J2SE 5.0에서 JVMTI로 대체된다)

*(교차 주: 괄호 안의 "J2SE 5.0에서 JVMTI로 대체된다"는 뒤의 편과 맞물린다 — `java-5` 편이 「그 외 변경 / API 추가」에 "JVM Tool Interface(JVMTI), JPDA 개선"을 적는다.)*

### Java Sound API

- 오디오(샘플 기반 사운드, MIDI) 재생·녹음·합성을 위한 표준 API가 코어에 포함되었다.

### 동적 프록시(Dynamic Proxy)

- `java.lang.reflect.Proxy`를 통해 런타임에 인터페이스 구현 객체를 동적으로 생성하는 기능. AOP, 원격 호출 스텁, 프레임워크의 인터셉터 등에 폭넓게 활용되었다.

> **동적 프록시(dynamic proxy)** — 인터페이스만 주면 그 인터페이스를 구현한 객체를 실행 중에 만들어 주는 기능.\
> 예: 아래 코드에서 `MyService.class` 하나만 넘겨 받은 객체가 만들어지고, 그 객체의 호출은 `InvocationHandler`의 `invoke`로 들어온다.

```java
// 제네릭(Class<?>)·람다는 1.3에 없다 — raw Class[] + InvocationHandler 익명 클래스
MyService proxy = (MyService) Proxy.newProxyInstance(
    MyService.class.getClassLoader(),
    new Class[]{ MyService.class },
    new InvocationHandler() {
        public Object invoke(Object p, Method method, Object[] args) throws Throwable {
            System.out.println("호출: " + method.getName());
            return null;
        }
    });
```

위 코드 주석이 이 시점의 문법 한계를 그대로 알려 준다 — `new Class[]{ … }`가 주석이 말하는 raw `Class[]`이고, `new InvocationHandler() { … }`가 주석이 말하는 익명 클래스다.

## 그 외 변경 / API 추가
- RMI를 CORBA(IIOP) 위에서 동작시키는 RMI-IIOP 지원 — J2EE 상호운용성 강화.
- JavaSound, Java Naming 통합 외에 `Timer`/`TimerTask` 등 유틸리티 추가.
- 디버깅·프로파일링·성능 관련 개선이 전반적으로 이루어짐.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 세 불릿은 원문 한 문단을 문장 단위로 끊은 것이다.)*

- J2SE 1.3은 화려한 신기능보다 내실(성능·안정성·운영 인프라)을 다진 버전으로 평가된다.
- 특히 HotSpot의 기본 탑재는 자바를 서버 사이드 주류 언어로 끌어올리는 결정적 계기가 되었고, JNDI·JPDA는 이후 엔터프라이즈 자바와 개발 도구 생태계의 표준 토대가 되었다.
- 이 무렵부터 자바 릴리스에 코드네임이 본격적으로 붙기 시작했다(1.3 Kestrel, 1.4 Merlin은 맹금류(새) 이름이지만, 이후 5.0 Tiger·6 Mustang·7 Dolphin처럼 새에 국한되지는 않았다).

*(교차 주: 셋째 불릿이 든 코드네임은 뒤의 편들과 맞는다 — `jdk-1.4` 편이 "Merlin (멀린, 쇠황조롱이)", `java-5` 편이 "Tiger", `java-6` 편이 "Mustang"을 자기 「릴리스 정보」에 적는다.)*

## 용어 풀이

- **적응형 최적화(adaptive optimization)** — 미리 정해 두지 않고, 돌아가는 동안 관찰한 결과에 맞춰 최적화 대상을 고르는 방식. 원문이 HotSpot이 수행하는 것으로 든 이름이다.
- **핫스팟(hot spot)** — 프로그램에서 유난히 자주 실행되는 부분. 원문은 이런 코드를 "런타임에 분석하여 집중적으로 네이티브 컴파일·최적화"한다고 적는다.
- **HotSpot JVM** — 적응형 최적화를 수행하는 가상 머신. 이 편에서 기본 JVM이 되었고, 원문은 그 성능을 "단순 JIT보다 뛰어난 성능을 냈다"로 견준다.
- **네이밍·디렉터리 서비스** — "이 이름으로 등록된 것이 무엇인가"를 물어보면 답해 주는 서비스. 원문이 든 것이 LDAP, DNS, RMI 레지스트리다.
- **룩업(lookup)** — 이름을 주고 그 이름에 묶인 것을 받아 오는 일. 원문이 든 쓰임이 "J2EE에서 데이터소스·EJB 룩업"이다.
- **JNDI** — 다양한 네이밍·디렉터리 서비스를 "통일된 API로 조회·바인딩"하게 해 주는 인터페이스. 이 편에서 코어 플랫폼에 통합됐다.
- **JPDA** — 원문 표현 그대로 "표준 디버깅 인프라". 1.3에서의 구성은 JVMDI(JVM Debug Interface)·JDWP(디버그 와이어 프로토콜)·JDI(디버그 인터페이스) 셋이다.
- **동적 프록시(dynamic proxy)** — 인터페이스만 주면 그 인터페이스를 구현한 객체를 실행 중에 만들어 주는 기능. 원문이 든 통로가 `java.lang.reflect.Proxy`다.
- **`InvocationHandler`** — 동적 프록시로 들어온 호출이 모이는 자리. 원문 코드에서는 `invoke`가 호출된 메서드 이름을 찍는다.

## 참고 출처
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
- [Java 1.3 - javaalmanac.io](https://javaalmanac.io/jdk/1.3/)
- [JDK release dates - Java Glossary (mindprod)](https://www.mindprod.com/jgloss/jdkreleasedates.html)
