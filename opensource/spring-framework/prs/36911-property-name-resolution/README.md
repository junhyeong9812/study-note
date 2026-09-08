# PR #36911 — Fix property name resolution for record-style accessors

## 0. 정향

이 문서는 `spring-core`의 `Property#resolveName()` 버그 수정 PR을 처음부터 이해하기
위한 해설이다. 바뀐 코드만이 아니라, `Property`라는 객체가 무엇이고 이름 해석이 왜
필요한지부터 시작한다. 다 읽으면 "record 컴포넌트 이름에 is가 들어가면 애노테이션이
사라지던 버그"를 남에게 설명할 수 있어야 한다. 관련 개념 문서:
`../../concepts/compile-runtime-layers/compile-runtime-layers.md` (선언 메타데이터 층),
`../../concepts/property-metadata-deep-dive/property-metadata-deep-dive.md` (Property 심화),
`../../concepts/property-accessor-conventions/property-accessor-conventions.md` (접근자 관례 일반론).

## 1. 배경 — Property는 무엇을 하는 물건인가

`Property`는 "클래스의 논리적 속성 하나"를 설명하는 메타데이터 카드다. 자바에서
프로퍼티는 필드, 읽기 메서드, 쓰기 메서드의 묶음이라는 개념이고, JDK의
`java.beans.PropertyDescriptor`가 그 표준 표현이다. 그런데 `java.beans` 패키지가
없는 환경(Android 등)이 있어서, Spring의 타입 변환 시스템은 자체 경량 표현인
`Property`를 만들었다.

카드가 들고 있는 것은 값이 아니라 구조 정보다: 어느 클래스(`objectType`), 어떻게
읽고 쓰나(`readMethod`/`writeMethod`), 논리 이름(`name`), 그리고 getter, setter,
backing field에서 모은 애노테이션. 소비자는 두 부류다. `TypeDescriptor`가 이 카드로
변환 맥락(타입과 애노테이션)을 만들고, SpEL의 `ReflectivePropertyAccessor`가 표현식
평가 중에 접근자 메서드를 찾아 이 카드로 포장한다.

이름이 중요한 이유는 `getField()`에 있다. 애노테이션을 모을 때 카드는 **이름으로**
backing field를 찾는다. 이름이 틀리면 필드를 못 찾고, 필드에 붙은 애노테이션이
에러 없이 조용히 빠진다. record는 컴포넌트 애노테이션이 backing field로 전파되는
경우가 많아 이 무음 탈락이 실제 동작 차이로 나타난다.

## 2. 수정 전 동작 방식 — indexOf 기반 이름 유도

이름 없이 카드가 만들어지면 `resolveName()`이 읽기 메서드 이름에서 논리 이름을
유도한다. 수정 전 코드는 접두사를 `indexOf`로 찾았다:

```java
int index = this.readMethod.getName().indexOf("get");
if (index != -1) {
    index += 3;
}
else {
    index = this.readMethod.getName().indexOf("is");
    if (index != -1) {
        index += 2;
    }
    else {
        // Record-style plain accessor method, for example, name()
        index = 0;
    }
}
return StringUtils.uncapitalize(this.readMethod.getName().substring(index));
```

JavaBeans 시절에는 이 코드가 안전했다. 읽기 메서드는 반드시 `get`/`is`로
시작했으므로 `indexOf`는 항상 0을 돌려줬고, 사실상 `startsWith`처럼 동작했다.
record 지원(gh-26029)이 `index = 0` 폴백을 추가하면서 무접두사 접근자가 들어오기
시작했는데, `indexOf`가 이름 **어디서든** 접두사를 찾는다는 성질이 그대로 남았다.

## 3. 무엇이 문제였나 — 이름 중간의 get과 is

접두사 글자를 우연히 품은 record 접근자가 잘못 잘렸다. 몇 가지 예를 값으로
따라가면 문제가 선명해진다. 다음 표는 접근자별 결과 비교다.

| 접근자 | indexOf 매칭 위치 | 결과 | 기대 |
|---|---|---|---|
| `budget()` | "get"이 3번 | `substring(6)` = 빈 문자열 | budget |
| `issue()` | "is"가 0번 | `substring(2)` = "sue" | issue |
| `isTarget()` | "get"이 5번 | `substring(8)` = 빈 문자열 | target |

`is`는 흔한 두 글자 조합이라 `issue`, `island`, `history`, `decision` 같은 평범한
이름이 전부 걸렸다. 빈/틀린 이름은 `getField()` 실패로 이어지고, 컴포넌트
애노테이션이 조용히 사라진다. SpEL이 이름 없이 카드를 만드는 경로가 실제 노출
지점이었다.

## 4. 수정 해설 — 두 단계의 진화

수정은 두 번에 걸쳐 다듬어졌다. 1차 커밋은 `indexOf`를 `startsWith`로 바꾸고,
record 컴포넌트 접근자를 `isRecord()`와 `RecordComponent`로 판별해 접두사를 벗기지
않게 했다. 리뷰에서 sbrannen이 방향을 넓혔다: Spring의 "record 스타일 접근자"
지원은 `java.lang.Record` 전용이 아니라 Kotlin data class와 커스텀 자바 데이터
클래스까지라서, record API 없이 판별하라는 요청이었다.

최종 판별식 `isPlainAccessor()`는 클래스의 정체 대신 메서드의 모양을 본다:

```java
private static boolean isPlainAccessor(Method method) {
    if (Modifier.isStatic(method.getModifiers()) ||
            method.getParameterCount() > 0 || method.getReturnType() == void.class) {
        return false;
    }
    try {
        // Accessor method referring to instance field of same name?
        Field field = method.getDeclaringClass().getDeclaredField(method.getName());
        return !Modifier.isStatic(field.getModifiers());
    }
    catch (Exception ex) {
        return false;
    }
}
```

세 가지 신호다: 비static 무인자 비void 메서드이고, 선언 클래스에 **같은 이름의
인스턴스 필드**가 있으면 plain accessor다. record의 backing field는 컴포넌트와 같은
이름이므로 자동으로 통과하고, 같은 모양의 어떤 데이터 클래스도 통과한다. 이 신호는
`CachedIntrospectionResults#isPlainAccessor`의 핵심 신호를 미러한 것이다.

호출 위치도 다듬어졌다. plain 체크는 접두사가 있는 이름에서만 결과를 바꾸므로
(무접두사 이름은 어차피 폴백에서 이름 전체를 쓴다), `get`/`is` 분기 안으로 옮겨
불필요한 리플렉션을 제거했다:

```java
if (methodName.startsWith("get")) {
    index = (isPlainAccessor(this.readMethod) ? 0 : 3);
}
else if (methodName.startsWith("is")) {
    index = (isPlainAccessor(this.readMethod) ? 0 : 2);
}
else {
    index = 0;
}
```

의도된 동작 변경이 하나 있다. `boolean isUrgent` 필드 + `isUrgent()` getter처럼
**같은 이름 필드로 뒷받침되는** 접두사형 getter는 이제 `urgent`가 아니라 필드명
`isUrgent`로 해석된다. record 컴포넌트 `isUrgent`와 구조적으로 동일해 구분이
불가능하고, 필드명이 곧 저자의 의도라는 판단이다. `java.beans`와 갈리는 지점이라
PR 본문 "Note on impact"에 공개했고, 최종 판단은 메인테이너에게 있다.

setter 분기도 1차 커밋에서 함께 조였었지만, 이건 별개의 동작 변경이라 리뷰 요청에
따라 원복하고 전용 PR #37139로 분리했다(그 해설은 `../37139/README.md`).

## 5. 검증 — 테스트 18건이 각각 고정하는 것

`PropertyTests`는 크게 네 무리다. JavaBeans 보존(`getName`, `isEnabled`,
`setName`, 그리고 회귀 가드 `isTarget` — 옛 코드에서 빈 문자열이 되는 모양),
record 시나리오(`budget`/`issue`/`name` 컴포넌트, record 위의 일반 getter, 문자
그대로 `get`/`is`/`getWidget`인 컴포넌트), 손으로 쓴 데이터 클래스 시나리오(같은
4형태 + 필드 우선 정책을 고정하는 `isUrgent`), static 엣지(동명 static 필드,
static 메서드 — 둘 다 plain 아님).

이중 `isTarget`은 "핵심 수정(indexOf->startsWith)이 되돌려지면 실패하는" 유일한
가드라는 점에서, `isUrgent`는 합의된 정책을 문서화한다는 점에서 각각 무게가 있다.

## 6. 상태와 교훈

2026-08-14 기준 리뷰 반영을 마치고 재리뷰 대기 중이다. sbrannen은 이 PR을 계기로
SpEL 쪽 이름 전달 문제를 #37123으로 직접 가져가 구현했다 — SpEL이 명시 이름을
넘기면 `resolveName()` 경로 자체를 타지 않게 된다.

교훈 둘. 첫째, `indexOf`로 접두사를 찾는 코드는 "입력이 항상 접두사로 시작한다"는
암묵 전제를 갖는다 — 입력 집합이 넓어지는 순간(여기서는 record 지원) 전제가 깨지고
버그가 된다. 둘째, 무음 실패(애노테이션 탈락)는 예외가 없어 오래 숨는다. 이름 유도
같은 조용한 변환일수록 결과를 소비하는 쪽(`getField`)까지 따라가 봐야 실피해가
보인다.

---

연관 ko-docs (모듈 지도): `spring-core/02-타입-변환-conversion.md`
