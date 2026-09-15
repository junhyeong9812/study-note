# PR #37157 — 무대의 실구조와 워크플로우

> PR #37157의 무대가 되는 실구조·워크플로우.\
> 문제·수정은 [README.md](README.md), 테스트는 [tests.md](tests.md) 참조.
>
> 기준: 로컬 HEAD `526c706d1c3`.\
> 이 시점의 `AttributeMethods.java`는 **수정 전** 상태이므로, base 코드의 file:line은 그대로 쓰고 이 PR이 추가하는 요소는 diff 기준으로 표기한다.
>
> 무대의 **기본 구조**(플래그 계산식, `canLoad`/`validate`의 뼈대, `AnnotationsScanner` 소비 사슬)는 [`../37153/structure.md`](../37153-enum-array-annotation-probe/structure.md)가 담당한다.\
> 이 문서는 그 위에 재귀가 얹힌 뒤의 구조와, 재귀가 실제로 걸어 다니는 **nested 값 트리**의 워크플로우만 다룬다.\
> probe 개념은 [probe-pattern.md](../37153-enum-array-annotation-probe/probe-pattern.md) 참조.

## 1. 무대 — 재귀 확장 후의 실구조

이 PR이 만드는 구조적 변화는 셋이다.\
생성자의 지역 변수 하나, 그리고 `canLoad`/`validate` 각각에 붙는 private 헬퍼 하나씩.\
클래스의 필드 구성은 그대로다.

> **헬퍼(helper) 메서드** — 본체 메서드가 길어지지 않도록 한 조각을 떼어 낸 보조 메서드.\
> 예: `canLoadNestedAnnotations`는 "값이 annotation이면 안쪽으로 내려간다"만 담당한다.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ final class AttributeMethods                              AttributeMethods.java:41 │
│                                                                               │
│  [필드 — 변화 없음]                                                            │
│   attributeMethods :59 · canThrowTypeNotPresentException :61                   │
│   hasDefaultValueMethod :63 · hasNestedAnnotation :65                          │
│                                                                               │
│  [생성자 :68]  ─ 변화: 표현식을 지역 변수로 승격해 두 결정이 공유              │
│     boolean nestedAnnotation =                                                 │
│         (type.isAnnotation() || (type.isArray() && type.componentType()        │
│                                              .isAnnotation()));   ← base :80   │
│     ├─ if (!foundNestedAnnotation && nestedAnnotation) ...        ← base :80-82│
│     └─ canThrowTypeNotPresentException[i] =                                    │
│            (type == Class.class || type == Class[].class ||                    │
│             type.isEnum() || nestedAnnotation);                   ← base :84   │
│                                                                               │
│  [canLoad :102]  ─ 변화: invoke 반환값을 캡처해 재귀 헬퍼로 넘김               │
│      Object value = invokeAnnotationMethod(get(i), annotation);   ← base :107  │
│      if (!canLoadNestedAnnotations(value, source)) return false;               │
│                                                                               │
│  [validate :136] ─ 변화: 동일                                                  │
│      Object value = invokeAnnotationMethod(get(i), annotation);   ← base :141  │
│      validateNestedAnnotations(value);                                         │
│                                                                               │
│  [신설] private boolean canLoadNestedAnnotations(@Nullable Object, AnnotatedElement)│
│  [신설] private void    validateNestedAnnotations(@Nullable Object)            │
└──────────────────────────────────────────────────────────────────────────────┘
```

여기서 중요한 것은 재귀가 **인스턴스 사이를 건너뛰는 방식**이다.\
`AttributeMethods`는 annotation 타입당 하나이므로, 안쪽 annotation을 검사하려면 그 타입의 `AttributeMethods`를 새로 얻어야 한다.\
그 통로가 이미 있던 정적 캐시다.

```text
  AttributeMethods(@Outer)                     AttributeMethods(@Inner)
        │                                             ^
        │ canLoadNestedAnnotations(value, source)     │
        │   value instanceof Annotation nested        │
        └──── forAnnotationType(nested.annotationType()) ──┘   base :256
                    └ cache.computeIfAbsent(...)             base :260
                          (ConcurrentReferenceHashMap :47 — 재귀가 타입 그래프를
                           따라가도 타입당 인스턴스는 하나로 유지된다)
```

재귀가 걸어 다니는 대상은 타입 선언이 아니라 **값 트리**다.\
그래서 무대에 새로 등장하는 개념이 "annotation 인스턴스가 이루는 트리"다.

> **값 트리(value tree)** — annotation 인스턴스들이 속성 호출로 이어져 만드는 트리. 노드는 프록시, 간선은 속성 호출 1회.\
> 예: `@DeepNestedValue -> @NestedValue -> @EnumValueInner -> enum 상수`가 깊이 3짜리 값 트리다.

```text
                    @DeepNestedValue 프록시          ← 스캔이 발견한 바깥 annotation
                          │  value()
                          v
                    @NestedValue 프록시              ← 속성 값이 또 하나의 annotation
                          │  value()
                          v
                    @EnumValueInner 프록시
                          │  value()
                          v
                    ExampleEnum 상수 해석            ← 실제 폭탄 위치
                          └ 상수가 없으면 EnumConstantNotPresentException

  각 노드는 JDK 동적 프록시이고, 간선은 "속성 메서드 1회 호출"이다.
  간선을 밟는 실제 호출은 AnnotationUtils.invokeAnnotationMethod  AnnotationUtils.java:1082
  (프록시면 InvocationHandler 직접 호출 :1086-1090, 아니면 리플렉션 폴백 :1095)
```

배열 속성이면 한 노드에서 여러 자식으로 갈라진다(`EnumValueInner[] value()`).\
즉 값 트리는 일반적으로 **가지가 여럿인 유한 트리**이고, 재귀는 그 위의 DFS다.

> **DFS(깊이 우선 탐색)** — 트리를 훑을 때 형제로 옆으로 가기 전에 자식으로 끝까지 내려가는 순서.\
> 예: `@Deep`의 첫 속성을 만나면 그 안쪽 끝(enum 상수)까지 먼저 내려갔다가 돌아온다.

## 2. 수정 전 동작 워크플로우

수정 전 동작을 이해하는 핵심은 "probe가 무엇을 관측하느냐"다.\
probe는 속성을 **한 겹만** 호출하고 반환값을 버리는데, nested annotation 속성은 그 한 겹이 **성공한다**.

검사가 값 트리의 어디까지 닿는지를 먼저 그림 하나로 못박는다.

```text
값 트리                       수정 전 검사가 닿는 범위
  @Outer        <---- 여기까지만 본다 (속성 목록을 읽고 플래그 판정)
    |
    | value()   <---- 플래그 false 라 이 간선을 밟지도 않는다
    v
  @Inner        <---- 검사 대상 밖
    |
    | color()
    v
  enum 상수      <---- 폭탄. 아무도 여기까지 오지 않는다

  -> 검사 깊이 0, 폭탄 깊이 2. 둘이 만나지 않는다.
```

```text
스캔 진입: AnnotationsScanner.getDeclaredAnnotations(source, ...)   AnnotationsScanner.java:432
   └ :446  AttributeMethods.forAnnotationType(@Outer).canLoad(outer, source)
        │
        ├ [수정 전 ①] 플래그 게이트 :105
        │     @Outer 의 속성 타입은 @Inner (annotation)
        │     → :84 계산식에 annotation 계열이 없으므로 플래그 = false
        │     → 실호출 자체를 건너뜀 ⇒ 관측 기회 0
        │
        └ [수정 전 ② — 만약 플래그만 추가했다면] :107
              frame 1: invoke(outer.value())  ─→ @Inner 프록시 반환   OK 성공
                       (반환값은 버려진다 — base :107 은 결과를 받지 않는다)
              frame 2: inner.value()          ─→ 아무도 호출하지 않음  X
              ⇒ 여전히 예외 없음 ⇒ canLoad == true
   │
   v
canLoad == true → annotations[i] 그대로 유지 :450 → 스캔 통과(isPresent == true)
   → asMap() 이 오염된 nested 프록시를 값으로 실어 나름 (silent corruption)
   → synthesize().value().value() 호출 시 raw EnumConstantNotPresentException 누출
```

`@Outer` 대신 오염이 **직접 속성**에 있었다면(예: `ExampleEnum value()`) frame 1에서 바로 터져 걸러졌을 것이다.\
같은 오염인데 한 겹 안으로 들어가는 순간 방어망이 사라지는 비대칭이 이 PR의 표적이다.

**수정 후 — 값 트리 DFS.**\
재귀가 붙으면 워크플로우는 트리 순회가 된다.\
`@DeepNestedValue` 시나리오를 끝까지 따라가면 이렇다.

```text
canLoad(@DeepNestedValue 인스턴스, source)                            [깊이 0]
 │ i=0: 플래그 true (속성 타입이 @NestedValue — nestedAnnotation 가지)
 │ value = invoke(deep.value())  → @NestedValue 프록시 (성공)
 │
 └─ canLoadNestedAnnotations(value, source)
      value instanceof Annotation → forAnnotationType(@NestedValue).canLoad(nested, source)   [깊이 1]
        │ i=0: 플래그 true (속성 타입이 @EnumValueInner)
        │ value = invoke(nested.value()) → @EnumValueInner 프록시 (성공)
        │
        └─ canLoadNestedAnnotations(...)
             → forAnnotationType(@EnumValueInner).canLoad(inner, source)                 [깊이 2]
               │ i=0: 플래그 true (속성 타입이 enum — base :84 가 원래 다루던 가지)
               │ value = invoke(inner.value())
               │        X EnumConstantNotPresentException
               └ catch (Throwable) base :113
                    ├ failureLogger.log("Failed to introspect meta-annotation @EnumValueInner",
                    │                    source, ex)                      base :116
                    │      - 로그가 지목하는 것은 바깥이 아니라 실제 깨진 annotation 이다
                    └ return false                                        base :119
        ⇒ 깊이 1 의 canLoadNestedAnnotations 가 false 를 보고 return false
 ⇒ 깊이 0 이 false 반환
   → AnnotationsScanner :447 annotations[i] = null
   → 바깥 @DeepNestedValue 가 통째로 스캔에서 사라진다 (의도된 blast radius — README §4)
```

`validate` 쪽은 같은 트리를 같은 순서로 걷되, 실패 보고가 예외다.\
그리고 **안쪽에서 만들어진 예외가 재래핑 없이 그대로 올라온다**는 것이 구조적 특징이다.

> **재래핑(re-wrapping)** — 올라오던 예외를 중간 단계에서 새 예외로 다시 감싸는 것.\
> 예: 각 프레임이 자기 이름으로 감싸면 최상위 메시지는 가장 바깥 annotation을 가리키게 되어 원인이 흐려진다.

```text
validate(@DeepNestedValue)                               [깊이 0]
 └ invoke 성공 → validateNestedAnnotations(value)
      └ validate(@NestedValue)                                [깊이 1]
           └ invoke 성공 → validateNestedAnnotations(value)
                └ validate(@EnumValueInner)              [깊이 2]
                     └ invoke X EnumConstantNotPresentException
                          catch (Throwable) base :146
                            throw new IllegalStateException(
                                "Could not obtain annotation attribute value for value"
                                + " declared on @...EnumValueInner", ex)   base :147-149
                     ^
           [깊이 1] 의 try 가 이 ISE 를 받는다
              catch (IllegalStateException ex) { throw ex; }   base :143-145  ← 그대로 통과
      ^
 [깊이 0] 도 동일하게 통과
 ⇒ 호출자는 "가장 안쪽 @EnumValueInner 에서 실패했다"는 메시지와
   EnumConstantNotPresentException cause 를 그대로 받는다
```

`catch (IllegalStateException ex) { throw ex; }`는 원래 "다른 종류의 실패는 삼키되 ISE는 통과시킨다"는 목적으로 있던 가지인데, 재귀가 붙자 **진단 품질을 보존하는 장치**로 재활용된다.\
이 가지가 없었다면 깊이마다 한 겹씩 더 감싸여 원인 annotation이 메시지에서 흐려졌을 것이다.

## 3. 분기 처리 워크플로우

재귀가 추가하는 분기는 값의 런타임 형태를 보는 `instanceof` 삼분기다.

> **instanceof 패턴 매칭** — "이 값이 그 타입이면, 그 타입 변수로 바로 받아라"를 한 줄로 쓰는 자바 문법.\
> 예: `value instanceof Annotation nested`는 검사와 형변환과 변수 선언을 동시에 한다.

```text
[분기 1] canLoadNestedAnnotations(value, source)
│
├─ value instanceof Annotation nested
│     → return forAnnotationType(nested.annotationType()).canLoad(nested, source)
│         (한 단계 더 내려간다)
├─ value instanceof Annotation[] nestedArray
│     ├ 원소 순회 — 하나라도 canLoad == false 면 즉시 return false (단축 평가)
│     └ 빈 배열이면 루프가 0회 → 아래 return true 로 떨어짐
└─ 그 외 (Class · Class[] · enum · enum[] · String 등)
      → return true   - 이 값들의 폭탄은 이미 frame 1 의 invoke 에서 터졌다

[분기 2] validateNestedAnnotations(value)   ── 같은 삼분기, 보고 방식만 다름
│
├─ value instanceof Annotation nested       → forAnnotationType(...).validate(nested)
├─ else if value instanceof Annotation[]    → 원소마다 validate (첫 실패에서 예외로 탈출)
└─ 그 외                                     → 아무것도 하지 않음
```

두 헬퍼의 분기 형태가 미세하게 다르다는 점은 실코드 그대로다.\
`canLoadNestedAnnotations`는 `if` 둘을 나란히 쓰고(첫 가지가 `return`으로 끝나므로 결과는 `else if`와 같다), `validateNestedAnnotations`는 `if / else if`를 쓴다.\
값 하나가 `Annotation`이면서 동시에 `Annotation[]`일 수는 없으므로 동작 차이는 없다.

플래그 계산식 쪽 분기도 이 PR에서 다시 그려진다.\
주의할 점은 이 PR의 diff가 **#37153이 아니라 base 위에서** 만들어졌다는 것이다.

```text
[분기 3] canThrowTypeNotPresentException[i]  — 세 판본

base (현재 HEAD :84)
   type == Class.class || type == Class[].class || type.isEnum()
       └ enum[] X · annotation X · annotation[] X

PR #37153 적용 시
   ... || type.isEnum() || (type.isArray() && type.componentType().isEnum())
       └ enum[] OK · annotation X · annotation[] X

PR #37157 적용 시 (이 PR)
   ... || type.isEnum() || nestedAnnotation
       └ enum[] X · annotation OK · annotation[] OK
       - 두 PR 이 같은 줄을 서로 다르게 넓힌다 — 먼저 머지되는 쪽 기준으로
         나머지 한쪽이 rebase 되어야 하며, 최종 형태는 네 가지가 모두 선 식이 된다.
```

마지막 분기 묶음은 종료 조건이다.\
이 재귀에는 visited 집합이 없다.

> **visited 집합** — 이미 방문한 노드를 기억해 두어 같은 곳을 다시 밟지 않게 하는 재귀 가드.\
> 예: 순환이 있는 그래프를 재귀로 돌면 visited가 없을 때 무한히 맴돈다.

```text
[분기 4] 재귀는 어디서 멈추나
│
├─ 값이 annotation 이 아니다      → 즉시 true/무동작 (분기 1·2 의 마지막 가지)
├─ 속성 중 플래그 선 것이 없다     → 루프가 invoke 를 한 번도 안 함 → true
├─ 배열이 비었다                  → 자식 없음 → true
└─ 그 외에는 한 단계 내려간다
      - 값 트리가 유한하다는 보장이 종료의 근거다 —
        JLS §9.6.1 이 annotation 멤버 타입의 순환을 컴파일 에러로 금지한다.
        상세: ../concepts/jls-annotation-rules.md

  - 대조: 같은 패키지에 visited 집합을 쓰는 재귀가 이미 있다.
    AnnotationTypeMapping.computeSynthesizableFlag  AnnotationTypeMapping.java:261
      └ :279 hasNestedAnnotation() 이면 nested 타입으로 재귀하되
        :288-291 "Java 가 아닌 JVM 언어의 재귀적 annotation 정의"를 대비해
        visitedAnnotationTypes.add(...) 로 가드한다.
      이 재귀가 걷는 축은 '타입 그래프'이고, #37157 의 재귀가 걷는 축은 '값 트리'다.
      축이 다르므로 같은 가드가 그대로 필요한 것은 아니다(개념 문서 참조).
```

## 4. 스프링 전역에서의 자리

소비 사슬은 #37153과 동일하다 — `AnnotationsScanner:446`(조용한 출구)과 `AnnotationUtils.validateAnnotation:775`(시끄러운 출구) 둘뿐이고, 그 위로 `MergedAnnotations` 계열 전체와 `@Configuration` 파싱이 얹힌다.\
전체 그림은 [`../37153/structure.md`](../37153-enum-array-annotation-probe/structure.md) §4에 있으므로 여기서는 **이 PR이 그 사슬에서 무엇을 바꾸는지**만 짚는다.

```text
[조용한 출구] MergedAnnotations 계열 → AnnotationsScanner.java:446
   변화 전: nested 멤버가 오염되어도 canLoad == true
              → 바깥 annotation 이 스캔에 남음
              → 컴포넌트 스캔·조건 평가·@Qualifier 매칭이 오염된 값을 손에 쥔다
   변화 후: 재귀 probe 가 false 를 반환
              → :447 annotations[i] = null → 바깥 annotation 전체가 사라짐
              → warn 로그(:116)는 바깥이 아니라 실제로 깨진 안쪽 타입을 지목
   - 숨김 단위가 'annotation 1개'인 이유는 타입 계약상 부분 숨김이 표현 불가능하기 때문
     — ../concepts/annotation-all-or-nothing-contract.md

[메타-annotation 축] AnnotationTypeMappings.java:93 → 같은 게이트
   메타-annotation 위에 얹힌 nested 멤버의 오염도 같은 재귀로 걸러진다.

[시끄러운 출구] ConfigurationClassParser.java:688-692 → AnnotationUtils.java:775 → validate
   변화 전: nested 오염은 validate 를 통과 → 리플렉션 경로가 그대로 채택됨
   변화 후: 안쪽에서 만든 IllegalStateException 이 재래핑 없이 올라옴
              → catch (Throwable) 에 걸려 ASM 기반 파싱으로 폴백
   - 즉 이 PR 은 "리플렉션으로는 못 읽는 클래스"의 판정 범위를 nested 까지 넓힌다.
```

성능 측면에서 전역에 미치는 영향의 형태도 구조에서 읽힌다.\
추가 비용은 **nested 속성이 있는 annotation 타입에만**, 그리고 **캐시 미스 때만** 발생한다.

```text
비용이 붙는 자리
  ├ 플래그 계산: 타입당 1회 (AttributeMethods.cache :47 가 반복을 막음)
  ├ 재귀 probe : element 단위 캐시 미스마다 (declaredAnnotationCache  AnnotationsScanner.java:55)
  └ 재귀 깊이  : 값 트리의 깊이 — 실무 annotation 은 보통 1~2단
  - 실측치(속성당 +50~70ns)와 그 해석은 README §5.
```

## 5. 관련 개념

이 구조를 읽는 데 필요한 개념은 이미 문서화되어 있으므로 링크로 연결한다.

- [JLS와 annotation 멤버 타입 규칙](../../concepts/jls-annotation-rules/jls-annotation-rules.md) — 위 [분기 4]의 종료 근거, 그리고 "값 트리 vs 메타-annotation 그래프"의 축 구분.
- [annotation 격리는 왜 all-or-nothing인가](../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md) — §4의 숨김 단위가 annotation 1개인 이유.
- [probe(사전 시험 호출)](../37153-enum-array-annotation-probe/probe-pattern.md) — 두 출구(`canLoad`/`validate`)의 설계 의도.
- [Mockito stubbing 메커니즘](../../concepts/mockito-stubbing-mechanics/mockito-stubbing-mechanics.md) — 이 무대를 테스트로 재현할 때 중첩 프록시 stubbing이 왜 까다로운지([tests.md](tests.md)의 전제).

한 가지, 이 문서의 구조에서만 선명해지는 성질을 덧붙인다.\
**폭탄의 깊이가 fix의 모양을 결정한다.**\
`Class`·`enum` 같은 스칼라 값은 폭탄이 첫 겹에 있어서 "플래그를 세워 한 번 호출해 보는" 것으로 충분하고(#37153이 한 줄로 끝난 이유), nested annotation은 폭탄이 둘째 겹 이상에 있어서 반환값을 받아 내려가는 순회가 필요하다.\
같은 방어망의 같은 종류 구멍이라도, 값의 **형태**가 아니라 실패의 **위치**를 봐야 고치는 모양이 정해진다.
