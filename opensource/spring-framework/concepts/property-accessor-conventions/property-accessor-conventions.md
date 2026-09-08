# 개념: 자바 프로퍼티 접근자 관례 — JavaBeans, record, 그리고 이름이 계약인 이유

> PR #36911(이름 해석)·#37139(setter 판별)의 무대가 되는 개념 묶음. PR별 상세는
> `../../prs/36911-property-name-resolution/README.md`·`../../prs/37139-property-setter-prefix/README.md`, 구조·워크플로우는 각 폴더의
> structure.md 참조.

## 프로퍼티 = 필드·읽기·쓰기 메서드의 "묶음"이라는 약속

자바에서 프로퍼티는 언어 기능이 아니라 **관례**다. JavaBeans 명세가 정한 묶음 —
backing field + 읽기 메서드(`getName()`/`isActive()`) + 쓰기 메서드
(`setName(...)`) — 을 프레임워크들이 리플렉션으로 재구성한다. JDK 표준 표현이
`java.beans.PropertyDescriptor`이고, `java.beans`가 없는 환경(Android 등)을 위해
Spring 변환 시스템은 경량 표현 `Property`(spring-core `core/convert`)를 따로
가진다.

관례의 핵심은 **이름 유도 규칙**이다:

| 메서드 형태 | 논리 이름 | 근거 관례 |
|---|---|---|
| `getName()` | name | JavaBeans — get 접두사 제거 + 첫 글자 소문자화 |
| `isActive()` | active | JavaBeans — boolean용 is 접두사 |
| `setName(v)` | name | JavaBeans — set 접두사 제거 |
| `name()` | name | **record 컴포넌트 접근자** — 접두사 없음 (Java 16+) |

record의 등장이 이 표를 흔들었다: "읽기 메서드는 반드시 get/is로 시작한다"는
전제가 깨지고, **무접두사 이름 자체가 합법 접근자**가 됐다. 그 순간 "이름 어딘가에
get이 있으면 접두사"라는 느슨한 판별(`indexOf`)은 `budget()`->"", `issue()`->"sue"
같은 오판을 낳는다 — #36911이 고친 결함의 뿌리이고, setter 쪽의 같은 패턴
(`offsetX`->"x", `upset`->"")이 #37139다. 교훈으로 일반화하면: **관례 검증은 "포함"이
아니라 "시작"으로** — 접두사 관례에 `indexOf`를 쓰면 관례 밖 이름이 들어오는 순간
거짓 양성이 된다.

## 이름은 장식이 아니라 결합 키다

`Property` 카드가 이름을 정확히 유도해야 하는 진짜 이유는 표시용이 아니다 —
**이름으로 backing field를 찾아 애노테이션을 수집**하기 때문이다(`getField()`).
이름이 틀리면:

1. 필드 조회 실패 — 예외 없이 null
2. 필드에 붙은 애노테이션이 **조용히 탈락** (record는 컴포넌트 애노테이션이
   backing field로 전파되는 경우가 많아 실동작 차이로 나타남)

즉 이름 유도의 오류는 "이상한 이름"이 아니라 **무음 애노테이션 소실**로 발현되는
silent failure다. 이름이 두 표현(메서드 <-> 필드)을 잇는 결합 키인 구조에서는, 키
유도 규칙의 정확성이 곧 데이터 정합성이다.

## 소비자 — 이 카드는 어디서 쓰이나

- `TypeDescriptor`: Property 카드로 변환 맥락(타입 + getter/setter/field 애노테이션
  합집합)을 구성 — 타입 변환 시 `@NumberFormat` 같은 애노테이션이 먹히는 경로.
- SpEL `ReflectivePropertyAccessor`: 표현식 평가 중 접근자를 찾아 카드로 포장.

## 관련

- `../../prs/36911-property-name-resolution/README.md` — 읽기 메서드 이름 유도 결함과 isPlainAccessor 해법
- `../../prs/37139-property-setter-prefix/README.md` — 쓰기 메서드(setter) 판별 강화
- `annotation-all-or-nothing-contract.md` — "무음 소실보다 명시적 실패"라는 같은
  설계 원칙의 annotation 격리 버전
