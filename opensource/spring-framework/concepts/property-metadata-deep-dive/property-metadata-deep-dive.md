# Property 개념 해설 — "프로퍼티 메타데이터"란 무엇인가

> 대상: `org.springframework.core.convert.Property` (spring-core)
> 목적: 이 객체가 **무엇이고, 언제 태어나고, 누가 왜 쓰는지**를 개념부터 잡는다.
> 출생지: `docs/plans/2026-08-14/pr36911-plain-accessor-review/`(작업 문서)에서
> 2026-08-20 concepts로 이전. 관련: [property-accessor-conventions.md](../property-accessor-conventions/property-accessor-conventions.md)(관례 일반론),
> `../../prs/36911-property-name-resolution/README.md`·`../../prs/37139-property-setter-prefix/README.md`(버그·수정 서사).

---

## 1. "프로퍼티"라는 추상부터

자바 클래스는 상태를 **필드**에 저장하고, 외부에는 **메서드**로 노출한다.
그런데 프레임워크 입장에서는 "필드 name + getName() + setName()"을 각각 따로
보는 게 아니라, **"name이라는 속성 하나"** 로 묶어서 다루고 싶다. 이 묶음의
논리적 단위가 **프로퍼티**다.

```
        ┌─────────────── 프로퍼티 "name" (논리적 개념) ───────────────┐
        │                                                              │
클래스:  private String name;   getName()          setName(String)     │
        └─ 필드(저장)           └─ 읽기 메서드      └─ 쓰기 메서드 ────┘
```

이 묶음에는 두 가지 핵심 성질이 있다.

- 프로퍼티는 **개념**이지 코드 요소가 아니다. 클래스 파일 어디에도 "프로퍼티"라는
  선언은 없다 — 프레임워크가 규약(naming convention)으로 **추론**해낸다.
- 세 요소가 다 있을 필요 없다. getter만(읽기 전용), setter만(쓰기 전용),
  필드 없이 계산된 값만 돌려주는 getter도 전부 프로퍼티다.

## 2. "메타데이터"란 무엇인가

메타데이터는 값이 아니라 **값의 구조에 대한 설명**이다. 둘을 나란히 놓으면 차이가 분명해진다.

- **데이터**: `person.getName()`이 돌려주는 `"김준형"` — 실제 값.
- **메타데이터**: "Person 클래스에는 name이라는 String 프로퍼티가 있고, getName으로
  읽고 setName으로 쓰며, 필드에 @NotBlank가 붙어 있다" — **값이 아니라 구조에 대한
  설명**.

`Property` 객체가 들고 있는 것은 전부 후자다. **값은 한 번도 안 들어온다.**

```java
public final class Property {
    private final Class<?> objectType;          // 어느 클래스의 프로퍼티인가
    private final @Nullable Method readMethod;  // 어떻게 읽는가 (없을 수 있음)
    private final @Nullable Method writeMethod; // 어떻게 쓰는가 (없을 수 있음)
    private final String name;                  // 논리적 이름
    private final MethodParameter methodParameter; // 타입 정보의 출처
    private Annotation @Nullable [] annotations;   // getter+setter+필드의 애노테이션 합
}
```

비유하면 **도서관의 도서 카드**다. 카드에는 책 내용(값)이 없다 — 제목, 위치,
분류(구조 정보)만 있다. 카드가 있어야 책을 찾아 읽고(read) 꽂을(write) 수 있다.

## 3. 왜 이 클래스가 따로 있나

JDK에 이미 같은 역할의 `java.beans.PropertyDescriptor`가 있다. 그런데
`java.beans` 패키지는 Android·Java ME 같은 환경에 없다. Spring의 **타입 변환
시스템**(spring-core의 convert)은 어디서든 돌아야 해서, 의존 없는 경량 대체물을
직접 만든 것이 `Property`다. (클래스 javadoc이 정확히 이렇게 말한다.)

즉 위치를 그리면:

```
java.beans.PropertyDescriptor  ← JDK 표준 (무거운 introspection 세계)
        ↕ 같은 개념의 경량 버전
o.s.core.convert.Property      ← Spring 변환 시스템 전용 (이식성)
```

## 4. 누가, 언제 만드나 — 수명주기

**Property는 스스로 아무것도 스캔하지 않는다.** 클래스를 뒤져 메서드를 찾아내는
주체는 항상 **호출자**다. 호출자가 이미 찾아낸 Method 객체를 건네주면, Property는
그것을 **포장(wrap)** 할 뿐이다.

실제 생성 지점은 프레임워크 전체에 딱 4곳이다:

```java
// SpEL — 표현식 "obj.budget"을 평가하다가 budget() 메서드를 찾아낸 뒤:
Property property = new Property(type, method, null);        // 읽기, 이름 없음
Property property = new Property(type, null, method);        // 쓰기, 이름 없음

// spring-beans — 이미 PropertyDescriptor가 있어 이름을 알 때:
Property property = new Property(getBeanClass(), getReadMethod(), getWriteMethod(), getName());
```

흐름 전체를 그리면 (SpEL에서 `#{order.budget}`을 읽는 경우):

```
1. SpEL: "budget이라는 프로퍼티를 읽고 싶다"
2. SpEL이 Order 클래스에서 후보 메서드 탐색: getBudget()? isBudget()? budget()?
   → budget() 발견                                   [탐색은 SpEL의 일]
3. new Property(Order.class, budgetMethod, null)      [포장 — 여기가 Property 탄생]
   └ 이름이 null이므로 resolveName()이 "budget"을 유도   [이번 두 PR의 무대]
4. new TypeDescriptor(property)                       [변환 맥락에 탑재]
5. 변환기가 TypeDescriptor를 통해 타입·애노테이션을 조회
   └ 애노테이션 수집 시 getField()가 이름 "budget"으로 backing field를 찾아 합산
```

## 5. 무엇에 쓰이나 — 소비자 관점

이 카드를 받아 가는 쪽은 셋이고, 각자 가져가는 것이 다르다.

| 소비자 | 무엇을 가져가나 | 왜 |
|---|---|---|
| `TypeDescriptor` | 타입 + 애노테이션 + 제네릭 맥락 | "String->Money 변환할 때 @NumberFormat 고려" 같은 판단 |
| `getAnnotations()` | getter+setter+**backing field**의 애노테이션 합집합 | 애노테이션을 어디에 붙였든(필드/getter/setter) 동일하게 동작하게 |
| `getName()` | 논리 이름 | 캐시 키, 비교, 필드 탐색의 입력 |

여기서 **이름이 왜 중요한지**가 나온다: `getField()`는 유도된 **이름으로** 필드를
찾는다. 이름이 틀리면 필드를 못 찾고, 필드에 붙인 애노테이션이 **조용히**
빠진다(에러 없음 — 그래서 원 버그가 오래 숨어 있었다).

## 6. resolveName() — 이름 유도 규칙 (두 PR 반영 최종본)

이름 없이 생성됐을 때만 호출된다. **문자열 규약 처리이지, 값·필드 접근이 아니다.**

읽기 메서드가 있으면 다음 규칙으로 이름을 유도한다.

| 메서드 이름 | 규칙 | 결과 |
|---|---|---|
| `getName()` (동명 필드 없음) | "get" 시작 -> 3글자 벗김 | `name` |
| `isEnabled()` (동명 필드 없음) | "is" 시작 -> 2글자 벗김 | `enabled` |
| `issue()` (필드 `issue` 있음) | **plain accessor** — 벗기지 않음 | `issue` |
| `budget()` (프리픽스 없음) | 규약 밖 -> 그대로 | `budget` |
| `isUrgent()` (필드 `isUrgent` 있음) | plain accessor 우선 | `isUrgent` |

표에서 plain accessor 판별은 유일하게 필드를 **확인**하는 지점이다. 조건은 비static +
무인자 + 비void + **선언 클래스에 같은 이름의 인스턴스 필드 존재**이며, record·Kotlin
data class·커스텀 데이터 클래스가 모두 이 모양이다.

쓰기 메서드만 있으면 다음과 같이 갈린다(setter PR 반영).

| 메서드 이름 | 결과 |
|---|---|
| `setName(String)` | `name` |
| `updateName(String)` | `IllegalArgumentException` (전부터) |
| `offsetX(String)`, `upset(String)` | `IllegalArgumentException` (이번 강화 — 전에는 `x`, `""`) |

## 7. 흔한 오해 정리 (이번 세션에서 실제로 나온 것들)

아래 여섯 가지는 이번 세션에서 실제로 나온 오해와 그에 대한 정정이다.

| 오해 | 실제 |
|---|---|
| "Property가 메서드를 스캔/생성해 객체에 주입한다" | 탐색은 호출자(SpEL 등)의 일. Property는 이미 찾은 Method를 포장하는 카드일 뿐, 아무것도 만들거나 주입하지 않는다 |
| "불변 객체인지 판별한다" | final·불변성은 안 본다. 보는 건 "같은 이름의 인스턴스 필드가 있는가"뿐 |
| "파라미터 이름과 비교한다" | 파라미터는 **개수만**(0개) 본다. 이름 대조 상대는 **declared field** |
| "isPlainAccessor가 false면 프로퍼티가 아니다" | false = 거부가 아니라 **JavaBeans 규약으로 폴백**해서 이름을 계속 유도 |
| "set을 벗긴 이름으로 실제 필드와 비교한다" | setter 분기는 순수 문자열 처리. 필드 비교 없음. 유도된 이름과 일치하는 필드가 없어도 프로퍼티는 유효 |
| "프로퍼티 = 필드" | 프로퍼티는 논리적 속성. 필드는 그중 한 요소(없어도 됨) |

## 8. 한 문장 요약

`Property`는 "이 클래스의 이 속성은 이렇게 읽고 이렇게 쓰며 이런 타입·애노테이션을
갖는다"를 담은 **프로퍼티 1개짜리 메타데이터 카드**이고, 호출자가 찾아준 접근자
메서드를 포장해 태어나며, 이름이 없을 때만 메서드 이름의 문자열 규약(+plain
accessor 필드 확인)으로 논리 이름을 유도한다 — 이번 두 PR은 그 이름 유도 규칙을
고친 것이다.
