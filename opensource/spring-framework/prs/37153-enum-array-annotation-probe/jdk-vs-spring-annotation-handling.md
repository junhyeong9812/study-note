# 개념: JDK의 annotation 동작 방식 vs Spring의 동작 방식 — 그리고 Spring의 해법

> PR #37153의 무대 전체를 층으로 정리한다. "JDK는 인식 못하는데 왜 Spring이
> 통과시키는 게 문제냐"는 질문에 답하려면 두 층의 역할 분담을 알아야 한다.

## 1층: JDK — 일관된 지연(lazy) 계약

JDK의 annotation 처리는 처음부터 끝까지 "미룬다"로 설계돼 있다.

1. **저장**: 바이트코드에 값의 실체가 아니라 참조 정보만 기록한다. enum 값은
   "enum 타입 + 상수명" 문자열, Class 값은 타입 이름.
2. **객체 생성**: `getAnnotation()`은 동적 프록시를 만들어 돌려준다. 이 시점에
   값 해석을 시도하되, **실패해도 죽지 않는다** — 내부 map(memberValues)의 그
   자리에 예외 폭탄(ExceptionProxy)을 심어둘 뿐이다. JVM 기동·클래스 로드·
   getAnnotation 모두 정상 진행.
3. **값 접근**: 속성 메서드를 호출하는 순간에야 폭탄이 터진다 —
   `TypeNotPresentException`(타입 자체 없음), `EnumConstantNotPresentException`
   (상수 없음).

중요한 성질: JDK는 이 계약을 **대칭적으로** 적용한다. 단일 enum이든 enum 배열이든,
읽으면 똑같이 터진다. JDK 입장에서 이것은 버그가 아니라 정의된 동작이다 —
"완벽하지 않은 classpath에서도 안 읽는 값 때문에 죽지는 않는다, 대신 읽는 자가
위험을 진다."

왜 이렇게 설계했나: annotation은 메타데이터다. 클래스 로드 시점에 모든 값을 미리
해석하면 아무도 안 읽을 annotation 하나 때문에 관련 클래스 전부를 로드하고, 참조
하나만 깨져도 로드 자체가 실패한다. 지연은 견고함을 위한 선택이다.

## 2층: Spring — "읽는 자"가 프레임워크 자신이라는 문제

JDK 계약의 "읽는 자가 위험을 진다"가 Spring에서는 문제가 된다. Spring은
컴포넌트 스캔·`MergedAnnotations`·`AnnotatedElementUtils`로 **classpath의 온갖
클래스의 annotation을 대량으로, 사용자 대신, 읽는 쪽**이기 때문이다.

- 내 애플리케이션과 무관한 남의 jar 클래스의 annotation도 스캔 과정에서 읽힌다.
- 폭탄이 터지면 그 예외는 스캔 깊숙한 곳(프레임워크 내부 스택)에서 올라온다 —
  사용자는 자기가 안 읽은 annotation 때문에 기동이 깨지는 경험을 한다.
- 더 나쁘게는, JDK 프록시의 내부 map을 우회 접근하는 경로에서는 예외 대신
  **예외 객체가 값으로** 흘러나올 수 있다(silent corruption).

즉 JDK의 합리적 지연 계약이, "대량으로 대신 읽는" Spring의 사용 패턴과 만나면
시한폭탄 유통망이 된다.

## Spring의 해법: 격리 의미론 + 선별적 probe

Spring은 이 문제를 "로드 불가 annotation은 **없는 것으로 취급한다**"는 의미론으로
풀었다. 구현이 `AttributeMethods`다:

```
AnnotationsScanner.getDeclaredAnnotations (스캔 진입로, element당 캐시)
  └─ annotation마다: AttributeMethods.forAnnotationType(..).canLoad(annotation, source)
       └─ canThrowTypeNotPresentException 플래그가 선 속성만 실호출(probe)
            ├─ 성공 → 통과
            └─ 예외 → false → 스캔 결과에서 제외 + warn 로그
```

설계 결정 세 가지:

1. **선별적 probe**: 모든 속성을 다 호출해 보면 비용이 크다. 그래서 생성자에서
   "늦게 터질 수 있는 타입"(`Class`, `Class[]`, enum, 이제 enum[])만 플래그로
   표시하고, 그 속성만 probe한다. 위험 타입의 목록이 곧 방어망의 커버리지다 —
   **이번 버그는 이 목록에서 enum 배열이 빠져 있던 것**이다.
2. **두 개의 출구**: 같은 probe를 스캔용 `canLoad`(조용한 boolean — 흐름 제어)와
   명시 검증용 `validate`(IllegalStateException — 계약 위반 보고)로 나눠 노출한다.
   소비자의 목적이 다르기 때문이다.
3. **일관된 missing 계약**: 걸러진 annotation은 이후 전 표면에서 "없음"으로
   동작한다 — `isPresent()==false`, `asMap()=={}`, typed 접근은
   `NoSuchElementException`(missing annotation). raw JDK 예외가 아니라 Spring의
   정의된 계약으로 실패가 정리된다.

## 층으로 본 이번 버그와 fix

지금까지의 층을 한 줄씩 놓고 보면 버그가 정확히 어느 층에 있는지가 드러난다.

| 층 | 상태 |
|---|---|
| 환경 (classpath 버전 스큐) | 전제 조건 — 누구의 버그도 아님 |
| JDK (지연 예외, 단일/배열 대칭) | 정의된 동작 — 버그 아님 |
| Spring 방어망 (probe 목록) | **enum 배열만 구멍** — 여기가 버그 |
| fix | 목록에 enum 배열 추가 -> 기존 격리 의미론이 배열까지 확장 |

fix가 1줄로 끝나는 이유가 이 표에 있다: 새 메커니즘을 만든 게 아니라, 이미 있는
방어망의 커버리지 목록을 한 칸 채운 것이다. 반대로 말하면, 이 목록에 아직 빠진
계열이 없는지(예: nested annotation)가 자연스러운 후속 질문이 된다 —
[review.md](review.md)의 F1 참조.

## 관련

각 층을 자세히 다루는 문서는 다음과 같다.

- [enum-annotation-name-resolution.md](enum-annotation-name-resolution.md) — 1층 상세
- [classpath-version-skew.md](classpath-version-skew.md) — 환경 층 상세
- [probe-pattern.md](probe-pattern.md) — 해법의 핵심 장치 상세
- `../../concepts/compile-runtime-layers/compile-runtime-layers.md` — 컴파일/선언/값 3층 구분 일반론
