# PR #37153 분석 — AttributeMethods의 enum 배열 probe 누락

> 기준: PR 브랜치 `refs/pr/37153`, base = upstream main `a16509447075`.\
> 아래 file:line은 별도 표기가 없으면 **PR 적용 후** 파일의 좌표이고, "base:NN"은 수정 전 좌표다.\
> 상태: OPEN (2026-08-19 제출, 라벨 `status: waiting-for-triage`, `in: core`).
>
> 이 문서는 결함 한 건을 진입 API에서 결함 지점까지 **호출·데이터 흐름으로** 추적하고, 그 흐름에 등장하는 이름 하나하나의 역할을 사전으로 정리한다.\
> 무대의 일반 구조와 워크플로우는 [structure.md](structure.md), 문제·수정의 서술은 [README.md](README.md), 테스트는 [tests.md](tests.md), 리뷰 판단은 [review.md](review.md)가 담당하므로 여기서는 반복하지 않고 링크한다.

## 0. 결론

**결함**: `AttributeMethods` 생성자가 "값을 읽는 순간 터질 수 있는 속성"을 표시하는 플래그를 계산할 때 `Class`는 스칼라와 배열을 모두 세면서 enum은 스칼라(`type.isEnum()`)만 세어, **enum 배열 속성이 probe 대상에서 빠지고** 오염된 annotation이 스캔 필터를 무검사로 통과한다.

**수정**: 같은 생성자 바로 윗줄의 nested annotation 판별 관용구를 그대로 재사용해 `(type.isArray() && type.componentType().isEnum())` 한 가지를 계산식에 더한다(본문 1줄, 줄바꿈 포함 2줄).

**상태**: PR #37153 OPEN, 리뷰 대기.

> **probe 대상** — "읽는 순간 터질 수 있다"고 표시돼, 쓰기 전에 한 번 시험 호출해 보는 속성.\
> 예: `Class value()`는 표시돼 있어 미리 불러 보지만, 수정 전 `ExampleEnum[] value()`는 표시가 없어 그냥 지나쳤다.

> **스캔 필터(scan filter)** — 읽을 수 없는 annotation을 스캔 결과에서 빼 버리는 걸러내기 단계.\
> 예: `canLoad`가 false를 돌려주면 스캐너가 그 자리를 `null`로 비운다.

## 1. 무대 — 모듈, 클래스, 공개 진입 API

결함이 사는 파일과 그 파일을 감싸는 테스트의 좌표부터 고정한다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.annotation`.
- 결함 클래스: `AttributeMethods` (package-private final, 파일
  `spring-core/src/main/java/org/springframework/core/annotation/AttributeMethods.java`).
- 테스트: `spring-core/src/test/java/org/springframework/core/annotation/AttributeMethodsTests.java`.

`AttributeMethods`는 공개 API가 아니다.\
사용자가 손에 쥐는 표면은 `MergedAnnotations.from(...)`, `AnnotatedElementUtils.*`, `AnnotationUtils.*` 셋이고, 이 클래스는 그 아래에서 annotation 타입당 하나씩 만들어져 캐시되는 내부 자료구조다.\
그래서 "누가 어떤 상황에서 부르나"는 두 갈래로 좁다.

> **공개 API(public API)** — 라이브러리 사용자가 직접 부르도록 약속된 표면. 바꾸면 호환성이 깨진다.\
> 예: `MergedAnnotations.from(...)`은 공개 API이고, 그 안의 `AttributeMethods`는 package-private 내부 부품이다.

| 부르는 쪽 | 호출 지점 | 어떤 상황 | 실패를 어떻게 받나 |
|---|---|---|---|
| `AnnotationsScanner.getDeclaredAnnotations` | `AnnotationsScanner.java:446` | element(클래스, 메서드, 필드)에 선언된 annotation을 처음 읽을 때. `MergedAnnotations` 계열 전부가 결국 여기를 지난다 | `canLoad`가 boolean `false` -> 그 자리를 `null`로 비우고 warn 로그 |
| `AnnotationUtils.validateAnnotation` | `AnnotationUtils.java:775` | `ConfigurationClassParser`가 `@Configuration` 클래스를 리플렉션으로 읽어도 되는지 판단할 때 | `validate`가 `IllegalStateException` -> ASM 파싱으로 폴백 |

즉 결함이 사는 자리는 특정 기능이 아니라 **annotation을 읽는 모든 상위 기능이 공유하는 최하단 게이트**다.\
게이트가 "통과"로 오판하면 컴포넌트 스캔, 조건 평가, `@Qualifier` 매칭이 전부 같은 오염된 값을 손에 쥔다.

## 2. 전체 메서드 그래프 — 진입점부터 결함 지점까지

이 무대의 특징은 축이 둘이라는 것이다.\
플래그가 **만들어지는** 축(annotation 타입당 1회)과 플래그가 **쓰이는** 축(annotation 인스턴스마다)이 따로 돌다가 배열 인덱스 하나에서 만난다.

```text
[축 1 - 소비: annotation 인스턴스를 만날 때마다]

 사용자 코드
   MergedAnnotations.from(element, ...)
     └─ TypeMappedAnnotations.java:241-242  AnnotationsScanner.scan(criteria, element, ...)
          └─ AnnotationsScanner.java:79/:86  scan -> process
               └─ AnnotationsScanner.java:432  getDeclaredAnnotations(source, defensive)
                    ├─ :434  declaredAnnotationCache.get(source)      (히트면 아래를 건너뜀)
                    └─ :439  source.getDeclaredAnnotations()          JDK 프록시 배열
                         └─ :442  각 annotation 마다
                              :445  isIgnorable(type)  또는
                              :446  AttributeMethods.forAnnotationType(type)
                                        .canLoad(annotation, source)
                                          │
                                          v
                              AttributeMethods.java:103  canLoad(annotation, source)
                                :105  for i in 0..size()-1
                                :106    if (canThrowTypeNotPresentException(i))   <== 결함이 결정되는 게이트
                                :108      AnnotationUtils.invokeAnnotationMethod(get(i), annotation)
                                              └─ AnnotationUtils.java:1082
                                                   :1086-1090 프록시면 InvocationHandler.invoke
                                                   :1095      아니면 ReflectionUtils.invokeMethod
                                :114    catch (Throwable) -> :117 warn 로그 -> :120 return false
                              -> false 면 AnnotationsScanner.java:447  annotations[i] = null

[축 2 - 생산: annotation 타입당 1회, 캐시]

 AttributeMethods.forAnnotationType(type)                 AttributeMethods.java:256
   └─ :260  cache.computeIfAbsent(type, AttributeMethods::compute)
        └─ compute(type)                                  :264
             :265  type.getDeclaredMethods()
             :268  isAttributeMethod 아닌 것 제거          (:282)
             :277  이름순 정렬
             └─ new AttributeMethods(type, methods)       :68
                  :74-86  속성마다 1회 루프
                    :76   Class<?> type = method.getReturnType();
                    :80   foundNestedAnnotation 판정 (스칼라 + 배열을 이미 본다)
                    :83   ReflectionUtils.makeAccessible(method)
                    :84-85  canThrowTypeNotPresentException[i] = ...   <== 결함이 만들어지는 줄

[두 축이 만나는 유일한 지점]

   boolean[] canThrowTypeNotPresentException   (필드 :61)
        생산: 생성자 :84-85 가 인덱스별로 채운다
        소비: canThrowTypeNotPresentException(int) :192 를 통해 canLoad :106 / validate :140 이 읽는다
```

데이터의 관점에서 보면 결함은 "잘못된 값이 흐른" 것이 아니라 **흘러야 할 호출이 아예 일어나지 않은** 것이다.\
플래그가 false면 `invokeAnnotationMethod`가 호출되지 않고, 호출되지 않으면 예외가 관측되지 않으며, 관측되지 않으면 `canLoad`는 성공으로 결론 낸다.

> **누락 결함(missing-call defect)** — 계산을 틀리게 한 것이 아니라 해야 할 호출을 아예 하지 않아서 생기는 결함.\
> 예: probe를 건너뛰면 예외가 없으므로 로그도, 실패 카운터도, 스택트레이스도 남지 않는다.

## 2.5 핵심 이름표 사전

흐름에 등장하는 이름을 네 묶음으로 나눠 정리한다.\
각 항목은 역할, 입력과 출력, 누가 언제 부르는지, 그리고 이 결함과 어떻게 얽히는지를 담는다.

**(a) 플래그를 만드는 쪽.**\
다음은 생성자가 판정식을 계산할 때 관여하는 이름들이다.

| 이름 | 역할 / 입출력 | 누가 언제 | 결함과의 관계 |
|---|---|---|---|
| `AttributeMethods(annotationType, attributeMethods)` :68 | 속성 목록을 받아 성질 플래그 3종을 한 루프에서 계산하는 private 생성자. 입력 = annotation 타입 + 정렬된 `Method[]`, 출력 = 불변 인스턴스 | `compute(type)` :279 가 캐시 미스 때 1회 | 결함이 사는 유일한 메서드 |
| `attributeMethods` (필드 :59) | 이름 오름차순으로 정렬된 속성 메서드 배열. 인덱스가 곧 속성의 신원 | 생성자에서 대입, `get(int)` :181 이 노출 | 플래그 배열과 **인덱스를 공유**한다 - 그래서 플래그 계산이 틀리면 그 속성만 정확히 빠진다 |
| `type` (지역 :76) | `method.getReturnType()` 결과. 속성의 선언 반환 타입 | 루프 회차마다 | 판정의 유일한 입력. `ExampleEnum[]`일 때 `type.isEnum()`이 **false**라는 것이 결함의 씨앗 - 배열 클래스는 enum이 아니다 |
| `type.isEnum()` | 이 클래스 자체가 enum 타입인가 | :84 | 스칼라만 잡는다. `ExampleEnum[].class.isEnum()`은 false |
| `type.isArray()` / `type.componentType()` | 배열인가, 그 원소 타입은 무엇인가 | :80(nested annotation 판정)에서 이미 쓰이고 있었다 | 수정이 :85에서 **재사용**하는 도구. 새 도구를 들여오지 않은 것이 이 fix의 성격 |
| `canThrowTypeNotPresentException` (필드 :61, `boolean[]`) | 인덱스별 "이 속성은 읽는 순간 터질 수 있다" 표시 | 생성자가 채우고 `canLoad`/`validate`가 읽는다 | **결함의 산출물**. enum 배열 인덱스에 false가 들어간다 |
| `foundNestedAnnotation` (지역 :73) / `hasNestedAnnotation` (필드 :65) | 이 annotation에 nested annotation 속성이 하나라도 있는가 | :80-82에서 세우고 :88에서 필드로 고정 | 이번 fix의 대상은 아니지만 **정답 관용구를 들고 있던 이웃**. :80이 스칼라와 배열을 모두 보는데 :84는 그렇지 않다는 비대칭이 결함을 눈에 띄게 만든 단서 |
| `foundDefaultValueMethod` (지역 :72) / `hasDefaultValueMethod` (필드 :63) | 기본값을 가진 속성이 있는가 | :77-79 | 무관. 같은 루프에 있을 뿐 |
| `cache` (static :47) | annotation 타입 -> `AttributeMethods` 캐시(`ConcurrentReferenceHashMap`) | `forAnnotationType` :260 | 플래그 계산이 타입당 1회로 제한되는 근거. 잘못된 플래그도 이 캐시에 그대로 눌러앉는다 |
| `NONE` (static :45) | 속성이 0개인 경우의 공유 인스턴스 | :257(타입 null), :274(속성 0개) | 결함 경로에 들어오지 않는 조기 탈출구 |
| `methodComparator` (static :49) | 속성 메서드 이름 오름차순 비교자 | `compute` :277 | 인덱스 안정성의 근거 - 플래그 배열과 메서드 배열의 대응이 실행 간에 흔들리지 않는다 |

**(b) 플래그를 쓰는 쪽.**\
다음은 probe의 두 출구와 그 안에서 쓰이는 이름들이다.

| 이름 | 역할 / 입출력 | 누가 언제 | 결함과의 관계 |
|---|---|---|---|
| `canLoad(annotation, source)` :103 | 조용한 출구. 플래그 선 속성을 실호출해 보고 결과값을 버린다. 출력 = boolean | `AnnotationsScanner.java:446` | 결함 시 probe를 건너뛰고 true(오판)를 반환 |
| `validate(annotation)` :137 | 시끄러운 출구. 같은 probe를 돌리되 실패를 `IllegalStateException`으로 보고. 출력 = void | `AnnotationUtils.java:775` | 결함 시 아무것도 던지지 않는다 |
| `canThrowTypeNotPresentException(int index)` :192 | 플래그 배열 접근자. 입력 = 인덱스, 출력 = boolean | `canLoad` :106, `validate` :140, 테스트 | 결함을 가장 좁게 관측할 수 있는 지점 - mock도 예외도 없이 false가 보인다 |
| `size()` :229 | 속성 개수 | 두 루프의 상한 | - |
| `get(int index)` :181 | 인덱스의 속성 메서드 | probe 직전 :108/:142 | - |
| `AnnotationUtils.invokeAnnotationMethod(method, annotation)` `AnnotationUtils.java:1082` | 속성을 실제로 호출하는 헬퍼. 프록시면 `InvocationHandler.invoke`(:1086-1090), 실패하면 리플렉션 폴백(:1095). 출력 = 속성 값(@Nullable) | probe 안에서만 | **결함 시 한 번도 불리지 않는다**. `canLoad`는 반환값을 받지 않고 버린다(#37157이 바로 이 점을 바꾼다) |
| `catch (IllegalStateException ex)` :110 / :144 | 리플렉션 호출 자체의 평범한 실패. `canLoad`는 삼키고 `validate`는 재던진다 | probe 실패 시 | 결함과 무관하지만, 두 출구의 성격 차이를 보여 주는 가지 |
| `catch (Throwable ex)` :114 / :147 | `TypeNotPresentException`, `EnumConstantNotPresentException` 등 "타입을 못 읽음" 계열 | probe 실패 시 | 결함이 고쳐지면 enum 배열의 예외가 **여기로** 떨어진다 |
| `failureLogger` (static :43, `IntrospectionFailureLogger.WARN`) | 조용한 출구의 흔적 남기기. `log(message, source, ex)` | :117 | 필터링이 완전한 침묵은 아님을 보증 |
| `source` (파라미터) | 이 annotation이 선언된 element. 로그 문구에만 쓰인다 | `canLoad` 전체 | 진단용. `validate`에는 이 파라미터가 없다 |

**(c) 바깥 소비자.**\
다음은 오판된 플래그가 사용자 표면까지 새어 나가는 길목들이다.

| 이름 | 역할 | 누가 언제 | 결함과의 관계 |
|---|---|---|---|
| `AnnotationsScanner.getDeclaredAnnotations(source, defensive)` :432 | element의 선언 annotation을 읽고 필터링해 돌려주는 단일 관문 | 모든 스캔 경로 | 결함의 1차 피해자. `canLoad`가 true면 오염된 annotation을 그대로 통과시킨다 |
| `declaredAnnotationCache` (static `AnnotationsScanner.java:55`) | element -> 필터링된 배열 캐시 | :434 조회, :456 저장 | probe **반복** 빈도를 제한할 뿐 probe 자체를 없애지 않는다. 그래서 "캐시가 있으니 비용은 element당 1회"라는 서술은 과일반화(리뷰 감사에서 정정) |
| `annotations[i] = null` :447 / `allIgnored` :441 / `NO_ANNOTATIONS` :50 | 필터링의 실제 표현 - 자리를 비우고, 전부 비면 공유 빈 배열로 교체 | :442 루프 | "로드 불가 annotation은 없는 것으로 취급"이라는 의미론의 구현 |
| `MergedAnnotations.isPresent(X)` | 사용자 표면. "이 element에 X가 있나" | 사용자 코드 | 결함 시 오염된 annotation에 대해 **true** - 정상 설계는 false |
| `MergedAnnotation.asMap()` | 속성 이름 -> 값 맵 | `AnnotatedElementUtils.getMergedAnnotationAttributes` 계열 | 결함 시 `{value=EnumConstantNotPresentException 객체}`. 예외를 던지지 않고 **예외 객체를 값으로 실어 나른다**. 실측으로 발견됐고 PR 본문 Problem 절의 두 번째 항목이 됐다 |
| `synthesize().value()`, `getEnumArray(...)` | typed 접근 | 사용자 코드 | 결함 시 raw `EnumConstantNotPresentException` 누출. 고친 뒤에는 missing-annotation 계약(`NoSuchElementException`) |

**(d) 테스트 fixture.**\
다음은 이 결함을 테스트에서 재현하고 경계를 고정하는 재료들이다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `EnumArrayValue` (`ExampleEnum[] value()`) | 결함을 재현하는 최소 annotation | 신규. 기존 fixture에 enum 계열이 없어 추가 |
| `StringArrayValue` (`String[] value()`) | 새 조건이 임의 배열로 과확장되지 않음을 고정하는 음성 가드용 | 리뷰 open question에서 채택 |
| `ExampleEnum { ONE }` | 정상 값 공급원 | 양성 가드에서 `new ExampleEnum[] {ExampleEnum.ONE}` |
| `mockAnnotation(Class)` (기존 헬퍼) | `annotationType()`이 스텁된 Mockito mock annotation 생성 | `willThrow(new EnumConstantNotPresentException(...))`로 버전 스큐를 한 줄로 압축 |

사전을 한 줄로 압축하면 이렇다.\
**`type`이라는 지역 변수 하나에 대한 판정식이 `canThrowTypeNotPresentException[i]`를 정하고, 그 배열 한 칸이 `invokeAnnotationMethod` 호출 여부를 정하며, 그 호출 여부가 `isPresent`/`asMap`까지의 모든 것을 정한다.**

## 3. 결함 경로 단계 추적

같은 오염(구버전 enum 상수 `BLUE`를 참조하는 annotation, 런타임 enum에는 그 상수가 없음)을 두 형태의 속성에 각각 걸고 단계별로 따라간다.\
정상 케이스는 단일 enum 속성(`ExampleEnum value()`), 결함 케이스는 enum 배열 속성(`ExampleEnum[] value()`)이며, 그 외 조건은 동일하다.

| 단계 | 코드 위치 | 정상 케이스 (단일 enum) | 결함 케이스 (enum 배열, 수정 전) |
|---|---|---|---|
| 1. 타입 확보 | 생성자 :76 | `type = ExampleEnum.class` | `type = ExampleEnum[].class` |
| 2. 플래그 판정 | base :84 | `type.isEnum()` = true -> 플래그 **true** | `type == Class.class` false, `type == Class[].class` false, `type.isEnum()` **false** -> 플래그 **false** |
| 3. 캐시 고정 | :260 | 이 타입의 플래그가 캐시에 눌러앉음 | 동일 (틀린 값이 눌러앉음) |
| 4. probe 게이트 | `canLoad` :106 | 통과 -> 실호출 준비 | **차단** -> 이 인덱스는 건너뜀 |
| 5. 실호출 | :108 | `invokeAnnotationMethod` 실행 | 실행되지 않음 (호출 0회) |
| 6. 예외 관측 | :114 | `EnumConstantNotPresentException` 포착 | 관측 대상 없음 |
| 7. 보고 | :117, :120 | warn 로그 + `return false` | 루프가 끝나 :124 `return true` |
| 8. 스캐너 처리 | `AnnotationsScanner.java:447` | `annotations[i] = null` (제외) | 배열에 그대로 남음 |
| 9. 사용자 표면 | `isPresent(X)` | **false** (설계된 격리) | **true** (오염된 annotation이 정상 행세) |
| 10. 값 읽기 | `asMap()` | `{}` (missing) | `{value=EnumConstantNotPresentException 객체}` |
| 11. typed 접근 | `synthesize().value()` | `NoSuchElementException` (missing 계약) | raw `EnumConstantNotPresentException` |

단계 5가 이 결함의 성격을 규정한다.\
흔한 버그는 "잘못된 값을 계산"하지만, 여기서는 **계산 자체가 일어나지 않는다**.\
그래서 로그도, 예외도, 실패 카운터도 남지 않는다.\
9~11의 결과 가운데 가장 나쁜 것은 예외를 던지는 11이 아니라 조용히 오염된 맵을 돌려주는 10이다 - 소비자(`AnnotationBeanNameGenerator`, `QualifierAnnotationAutowireCandidateResolver` 등)는 enum을 기대한 자리에서 예외 객체를 받아 엉뚱한 곳에서 `ClassCastException`으로 죽는다.

같은 enum 배열 속성이 fix 전후에 어떤 최종 상태로 끝나는지를 나란히 놓으면 이렇다.

```text
입력은 동일: ExampleEnum[] value() 속성, 런타임에 없는 상수를 가리킨다

  수정 전 (플래그 false)                    수정 후 (플래그 true)
  +--------------------------------+        +--------------------------------+
  | 2. 플래그    : false           |        | 2. 플래그    : true            |
  | 4. probe 게이트: 차단          |        | 4. probe 게이트: 통과          |
  | 5. 실호출    : 0 회            |        | 5. 실호출    : 1 회            |
  | 6. 예외 관측 : 없음            |        | 6. 예외 관측 : 포착            |
  | 7. 보고      : return true    |        | 7. 보고      : warn + false   |
  | 8. 스캐너    : 배열에 그대로   |        | 8. 스캐너    : 자리를 null 로  |
  | 9. isPresent : true            |        | 9. isPresent : false           |
  |10. asMap     : {value=예외}    |        |10. asMap     : {}              |
  |11. typed     : 예외 누출       |        |11. typed     : NoSuchElement   |
  +--------------------------------+        +--------------------------------+
    -> 오염된 값이 하류로 흘러간다             -> 단일 enum 과 같은 결말로 모인다
```

바뀐 칸은 2번 하나뿐이고, 4번 이후는 전부 그 한 칸의 결과다.

`validate` 쪽은 4~7만 다르다.\
정상 케이스는 :147-150에서 `IllegalStateException`으로 감싸 던지고, 결함 케이스는 게이트에서 걸려 **아무 일도 일어나지 않은 채 정상 종료**한다.\
그 결과 `ConfigurationClassParser`는 리플렉션으로 읽을 수 없는 클래스를 읽을 수 있다고 판단해 ASM 폴백을 하지 않는다.

## 4. 계약

이 무대에서 코드가 고정하고 있던 약속은 넷이다.

> **계약(contract)** — 코드가 호출자에게 지키기로 한 약속. javadoc·시그니처·테스트로 표현된다.\
> 예: `canLoad`의 javadoc "모든 값이 존재하면 true"가 이 PR이 어겼다고 지목한 약속이다.

- **`canLoad`의 javadoc** (`AttributeMethods.java:100`): `@return {@code true} if all values are present`.\
  "모든 값이 존재한다"는 단언인데, 결함 상태에서는 존재하지 않는 값이 있는데도 true를 반환한다.\
  이것이 이 PR이 어기는 것으로 지목한 1차 계약이다.
- **`validate`의 javadoc** (:134): `@throws IllegalStateException if a declared {@code Class} attribute could not be read`.\
  문구는 `Class`를 예로 들 뿐 타입을 열거하지 않는 일반 서술이고, 단일 enum이 이미 이 경로를 타고 있었다.\
  (리뷰에서 javadoc 갱신 필요성을 물었고, 열거식이 아니므로 무변경이 맞다고 정리됐다.)
- **`canThrowTypeNotPresentException(int)`의 javadoc** (:186-191): "인덱스의 속성이 접근 시 `TypeNotPresentException`을 던질 수 있는지".\
  여기서도 타입 목록을 약속하지 않는다 - 약속은 "던질 수 있으면 true"라는 **의미**이고, enum 배열은 던질 수 있으므로 false는 그 의미에 어긋난다.
- **기존 테스트가 고정한 것**: `AttributeMethodsTests`의 Class 계열 쌍(`canThrowTypeNotPresentExceptionWhenHasClassAttributeReturnsTrue` / `...ClassArrayAttribute...`)이 이미 **스칼라와 배열을 대칭으로** 요구하고 있었다.\
  enum에는 그 쌍이 없었다는 것이 결함이 오래 살아남은 이유이자, 이번 PR이 같은 모양의 쌍을 채워 넣는 근거다.

그리고 계약이 아닌 것 하나를 분명히 해 둔다.\
JDK가 오염된 annotation에 대해 프록시를 정상 생성하고 값을 읽는 순간에야 던지는 것은 **정의된 동작**이지 결함이 아니다.\
Spring이 그 위에 얹은 "로드 불가 annotation은 없는 것으로 취급한다"는 격리 의미론이 이 PR이 지키려는 계약이며, fix는 새 의미론을 만드는 것이 아니라 기존 의미론을 배열까지 확장한다.

> **격리 의미론(isolation semantics)** — 읽을 수 없는 대상을 에러로 터뜨리는 대신 "처음부터 없었던 것"으로 취급하는 규칙.\
> 예: 오염된 `@Foo`는 `isPresent()`가 false가 되고, 스캔 결과 배열에서 그 자리가 비워진다.

## 5. 수정안

**before** (base `a16509447075`의 `AttributeMethods.java:84`)

```java
			ReflectionUtils.makeAccessible(method);
			this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class || type.isEnum());
```

**after** (`refs/pr/37153`의 `AttributeMethods.java:83-85`)

```java
			ReflectionUtils.makeAccessible(method);
			this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class ||
					type.isEnum() || (type.isArray() && type.componentType().isEnum()));
```

**왜 이 위치인가.**\
결함의 인과 사슬(§2.5 마지막 문장)에서 상류 끝이 이 줄이다.\
하류의 `canLoad`, `validate`, `AnnotationsScanner`, `asMap`은 모두 "플래그가 서 있으면 probe한다"는 게이트를 전제로 이미 올바르게 동작하고 있으므로, 게이트의 판정만 고치면 나머지는 자동으로 정합해진다.\
소비처가 셋뿐(:106, :140, 그리고 테스트)이라는 점이 변경 효과를 "probe 대상 확대" 하나로 국한시킨다는 보증이기도 하다.

**표현을 새로 만들지 않은 이유.**\
바로 네 줄 위 :80이 nested annotation을 `type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation())`로 판정하고 있다.\
같은 파일, 같은 루프, 같은 질문("스칼라와 배열을 함께 본다")에 대해 이미 채택된 관용구를 그대로 따르는 것이 리뷰 비용을 가장 낮춘다.\
또 annotation 멤버는 문법상 다차원 배열이 불가능하므로 `componentType()` 1단계 검사로 완결이다.

> **관용구(idiom)** — 같은 코드베이스에서 같은 문제에 반복해 쓰이는 정해진 표현 방식.\
> 예: "스칼라와 배열을 함께 본다"를 `X || (isArray() && componentType().X)`로 쓰는 것.

**검토된 대안과 기각 이유.**

- `type == ExampleEnum[].class` 식의 **열거**: 불가능하다.\
  `Class[].class`는 단일 타입이라 상수로 적을 수 있지만 enum 배열은 enum 타입마다 다른 클래스이므로 열거할 대상이 무한하다.
- `type.isArray()`만으로 **모든 배열을 probe**: 조건은 짧아지지만 `String[]`, `int[]` 등 절대 던질 수 없는 속성까지 리플렉션 실호출을 추가한다.\
  기각했고, 그 기각이 무너지지 않도록 음성 가드 테스트(`canThrowTypeNotPresentExceptionWhenHasNonEnumArrayAttributeReturnsFalse`)를 리뷰 반영으로 넣었다.
- **플래그를 건드리지 않고 `canLoad`에서 반환값을 검사**: 값이 배열인지 보고 원소를 훑는 방식.\
  이 결함에는 과잉이다 - enum 배열의 폭탄은 첫 겹 호출에서 이미 터지므로 호출만 일어나면 충분하다.\
  (반환값을 받아야만 잡히는 결함은 nested annotation이고, 그것이 #37157이다.)
- **`AnnotationsScanner` 쪽에서 방어**: 게이트가 아니라 게이트 사용자를 고치는 것이라 같은 결함이 `validate` 경로에는 남는다.\
  두 출구가 같은 플래그를 공유한다는 구조상 상류 수정이 맞다.

## 6. 범위 밖과 인접 영향

이 PR이 남긴 인접 과제와 감수한 비용, 그리고 원리적 한계를 정리한다.

- **같은 식의 나머지 계열**: :84의 판정식은 이 PR 이후에도 `type.isAnnotation()` 계열을 다루지 않는다.\
  리뷰에서 나온 이 지적(F1)이 스모크로 재현되어 별도 PR **#37157**이 됐다.\
  두 PR은 같은 줄을 서로 다르게 넓히므로 먼저 머지되는 쪽 기준으로 나머지가 rebase되어야 하며, 최종 형태는 `Class`, `Class[]`, enum, enum 배열, annotation, annotation 배열이 모두 선 식이다.
- **하위호환**: 정상 annotation의 동작은 변하지 않는다(양성 가드 2건이 이를 직접 고정).\
  변하는 것은 **오염된 enum 배열 annotation**의 동작뿐인데, 그것이 이 PR의 목적이자 동시에 동작 변화이기도 하다 - 지금까지 스캔을 통과하던 annotation이 이제 `isPresent=false`가 된다.\
  리뷰 판단에 따라 PR 본문 Fix 절에 이 점을 명시했다.
- **비용**: 플래그 계산은 타입당 1회이고, 추가되는 것은 enum 배열 속성에 대한 리플렉션 실호출이다(종류상 이미 통과 중인 `Class[]` probe와 같다).\
  `declaredAnnotationCache`가 반복 빈도를 제한하지만 캐시 미스마다 재발생하므로 "element당 1회"까지 단정하지는 않는다(리뷰 감사에서 정정된 표현).\
  enum 배열 속성은 실무에서 드물지 않아(`@RequestMapping`의 `RequestMethod[]` 등) 비용 질문 자체는 정당했다.\
  정량 측정은 이 PR에서 하지 않았고, 뒤이은 #37157의 마이크로벤치가 기존 probe 무회귀(enum 25 -> 25 ns/op)를 실측했다.
- **원리적 한계**: probe는 "annotation 객체를 얻은 뒤"에 도는 장치이므로, annotation **타입 자체**가 classpath에 없어 `getDeclaredAnnotations()` 파싱 단계에서 `NoClassDefFoundError`가 나는 경우는 이 방어망 밖이다.\
  이 한계는 #37157 본문에 명시적으로 서술됐다.

> **마이크로벤치(microbenchmark)** — 아주 작은 코드 조각 하나의 실행 시간만 반복 측정하는 성능 실험.\
> 예: probe 한 번에 25 ns가 걸린다는 식으로 나노초 단위 수치를 뽑는다.
