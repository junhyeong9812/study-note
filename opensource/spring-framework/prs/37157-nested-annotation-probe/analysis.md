# PR #37157 분석 — nested annotation 안의 지연 실패를 probe가 보지 못한다

> 기준: PR 브랜치 `refs/pr/37157`, base = upstream main `a16509447075`(#37153 커밋을 포함하지 않는
> 독립 브랜치). file:line은 별도 표기가 없으면 **PR 적용 후** 좌표이고, "base:NN"은 수정 전 좌표다.
> 상태: OPEN (2026-08-19 제출, 라벨 `status: waiting-for-triage`, `in: core`).
>
> 무대의 재귀 구조와 값 트리 워크플로우는 [structure.md](structure.md), 서술은
> [README.md](README.md), 테스트 12건은 [tests.md](tests.md)가 담당한다. 이 문서는 그 위에
> **진입 API에서 결함 지점까지의 호출 그래프, 이름표 사전, 프레임 단위 단계 추적, 계약과
> 대안 판단**을 얹는다. 앞선 PR의 기본 무대는 [`../37153/analysis.md`](../37153-enum-array-annotation-probe/analysis.md).

## 0. 결론

**결함**: probe는 속성을 한 겹만 실호출하고 반환값을 버리는데, nested annotation 속성은 그 한 겹이
**성공한다**(JDK가 안쪽 프록시를 정상 반환). 폭탄은 반환된 프록시 안에 있으므로, 오염이 nested
annotation 안에 있으면 같은 오염이 직접 속성에 있을 때와 달리 스캔 필터를 통과한다.

**수정**: 플래그 계산식에 annotation 계열을 추가하는 것만으로는 잡히지 않으므로, `canLoad`와
`validate`가 invoke **반환값을 받아** 그것이 `Annotation`/`Annotation[]`이면 그 타입의
`AttributeMethods`로 재귀하도록 private 헬퍼 둘(`canLoadNestedAnnotations`,
`validateNestedAnnotations`)을 추가한다.

**상태**: PR #37157 OPEN, 리뷰 대기. #37153의 리뷰 finding에서 파생했으나 base가 main인 독립 PR이다.

## 1. 무대 — 모듈, 클래스, 공개 진입 API

무대와 소비자는 #37153과 완전히 동일하다. `spring-core`의 package-private
`org.springframework.core.annotation.AttributeMethods`이고, 부르는 곳은 `AnnotationsScanner.java:446`
(조용한 출구)과 `AnnotationUtils.java:775`(시끄러운 출구) 둘뿐이며, 그 위로 `MergedAnnotations`
계열 전체와 `@Configuration` 파싱이 얹힌다. 달라지는 것은 **결함이 사는 층**이다.

- #37153: 결함이 생성자의 판정식 한 줄(플래그가 서지 않음).
- #37157: 플래그를 세워도 남는 결함 - `canLoad`/`validate` 루프가 **invoke 반환값을 버린다**
  (base :108, :142가 결과를 대입하지 않는다).

그래서 이 PR은 판정식 한 줄과 두 메서드의 본문, 그리고 신설 헬퍼 둘을 함께 건드린다.

닿는 상황은 annotation 속성이 또 다른 annotation인 구성 전부다. 실제 예로
`@ComponentScan`의 `Filter[] includeFilters()`(`ComponentScan.java:165`)가 있고, 안쪽
`@Filter`가 참조하는 `Class`나 enum이 classpath 부분 업그레이드로 사라져 있으면 바깥
`@ComponentScan`이 오염된 채 스캔을 통과한다.

## 2. 전체 메서드 그래프 — 진입점부터 결함 지점까지

수정 후의 호출 그래프다. 화살표 옆의 프레임 번호는 §3의 단계 추적에서 그대로 쓴다.

```
 사용자 코드
   MergedAnnotations.from(element, ...)
     └─ AnnotationsScanner.java:432   getDeclaredAnnotations(source, defensive)
          └─ :446  AttributeMethods.forAnnotationType(@Outer).canLoad(outer, source)
                                                                    |
[프레임 1]  AttributeMethods.java:104  canLoad(annotation=@Outer 인스턴스, source)
              :107  플래그 게이트. 플래그는 생성자 :80(nestedAnnotation 지역 변수)과
                    :85-86(Class || Class[] || isEnum || nestedAnnotation)이 정한다
              :109  Object value = AnnotationUtils.invokeAnnotationMethod(get(i), annotation)
                        └─ AnnotationUtils.java:1082 (프록시면 :1086-1090 InvocationHandler,
                           아니면 :1095 리플렉션)
                        결과: @Inner 프록시 반환 - 예외 없음 (결함의 핵심 사실)
              :110  if (!canLoadNestedAnnotations(value, source)) return false;
                        |
                        v
            AttributeMethods.java:131  canLoadNestedAnnotations(value, source)
              :132-133  Annotation 이면 forAnnotationType(nested.annotationType()).canLoad(...)
              :135-140  Annotation[] 이면 원소마다, 하나라도 false 면 즉시 false
              :142      그 외(Class, enum, String ...) -> true
                        |
                        v
[프레임 2]  AttributeMethods.java:104  canLoad(annotation=@Inner 인스턴스, source)   [재귀]
              :107  플래그 true (안쪽 속성 타입이 enum)
              :109  invoke -> EnumConstantNotPresentException
              :118  catch (Throwable)
              :120-123  failureLogger.log("Failed to introspect meta-annotation @" +
                            annotation.annotationType().getSimpleName(), source, ex)
                        - 이 프레임의 annotation 이 @Inner 이므로 로그가 @Inner 를 지목
              :124  return false
                        |
                        v
            프레임 1 은 예외가 아니라 boolean false 를 받는다 -> :111 return false
              -> AnnotationsScanner.java:447  annotations[i] = null (바깥 @Outer 가 통째로 사라짐)

[시끄러운 출구 - 같은 트리, 다른 보고]
   AnnotationUtils.java:775 -> validate(@Outer) :155
     :160-161  value = invoke(...) -> @Inner 프록시, validateNestedAnnotations(value)  :175
                 └─ validate(@Inner) :166-170  catch (Throwable) -> new IllegalStateException(
                        "... value declared on @...EnumValueInner", ex)
     :163-164  catch (IllegalStateException ex) { throw ex; }   <== 재래핑 없이 그대로 통과
```

그래프에서 이 PR의 성격이 드러난다. **추가된 것은 판정이 아니라 통로다.** base에서
`invokeAnnotationMethod`의 반환값은 어디에도 대입되지 않고 버려졌는데(base :108, :142), 그 값을
지역 변수 `value`로 받아 헬퍼에 넘기는 순간 같은 검사 기계장치가 한 겹 아래에서 다시 돌아간다.

## 2.5 핵심 이름표 사전

이 PR에서 새로 등장하거나 역할이 바뀌는 이름을 중심으로 정리한다. base에서 그대로인 이름
(`cache`, `NONE`, `failureLogger`, `attributeMethods`, `size()`, `get(int)` 등)의 사전은
[`../37153/analysis.md`](../37153-enum-array-annotation-probe/analysis.md) §2.5에 있으므로 여기서는 반복하지 않는다.

**(a) 생성자 쪽.** 다음은 판정식 주변에서 이 PR이 바꾼 이름들이다.

| 이름 | 역할 / 입출력 | 누가 언제 | 이 결함과의 관계 |
|---|---|---|---|
| `nestedAnnotation` (신설 지역 변수 :80) | "이 속성의 타입이 annotation이거나 annotation 배열인가". 입력 = `type`, 출력 = boolean | 생성자 루프 회차마다 1회 | base에서는 같은 표현식이 :80의 `if` 조건 안에만 있었다. 이 PR이 지역 변수로 승격해 `foundNestedAnnotation`(:81)과 `canThrowTypeNotPresentException`(:86) **두 결정이 공유**하게 만들었다(리뷰 F4 반영) - 두 판정이 미래에 갈라질 수 없게 하는 구조적 잠금 |
| `foundNestedAnnotation` (지역 :73) / `hasNestedAnnotation` (필드 :65) | annotation 속성이 하나라도 있는가 | :81-83, :89 | 값은 base와 동일. 소비처(`AnnotationTypeMapping.java:279`, `AnnotationUtils.java:917`)도 무변경 - 명세서의 보존 동작 |
| `canThrowTypeNotPresentException[i]` (필드 :61) | 인덱스별 probe 대상 표시 | :85-86 생산, :107/:158 소비 | base에서 annotation 계열이 빠져 있었다. 다만 **이것만 고쳐서는 결함이 잡히지 않는다**는 것이 이 PR의 출발점 |
| `type.isAnnotation()` / `type.componentType().isAnnotation()` | 스칼라, 배열 각각의 annotation 여부 | :80 | 판정의 도구. `Class[].class`처럼 상수로 적을 수 없어 리플렉션 질의가 필요하다 |

**(b) canLoad 축.** 다음은 조용한 출구에 재귀가 붙으면서 등장한 이름들이다.

| 이름 | 역할 / 입출력 | 누가 언제 | 이 결함과의 관계 |
|---|---|---|---|
| `value` (신설 지역 :109) | invoke의 반환값. 타입은 `@Nullable Object` | probe 성공 시마다 | **결함 수정의 물리적 핵심**. base :108은 이 값을 받지 않았고, 받지 않으면 안쪽으로 내려갈 방법이 없다 |
| `canLoadNestedAnnotations(value, source)` :131 | 값이 annotation(배열)이면 그 인스턴스에 대해 `canLoad`를 재귀 호출. 출력 = boolean(하나라도 실패하면 false) | `canLoad` :110에서만 | 신설. `private`이므로 외부 계약 표면이 늘지 않는다 |
| `nested` (패턴 변수 :132, :136) / `nestedArray` (:135) | 안쪽 annotation 인스턴스와 그 배열 | 재귀 진입 직전 | `nested.annotationType()`이 재귀할 타입을 정한다(mock에서 이 메서드가 스텁되어야 하는 이유). 배열 길이가 0이면 루프 0회 -> :142 `return true`(공허한 참)이며, 그 경로만 고정하는 가드 테스트가 따로 있다 |
| `forAnnotationType(nested.annotationType())` :133, :137 | 재귀가 **인스턴스 사이를 건너뛰는 통로**. 입력 = annotation 타입, 출력 = 그 타입의 `AttributeMethods` | 재귀 1단마다 | 정적 `cache`(:47)를 지나므로 값 트리를 깊이 내려가도 타입당 인스턴스는 하나로 유지된다 |
| `source` (파라미터) | 바깥 element. 재귀에도 **그대로 전달**된다 | 프레임마다 | 재귀 깊이와 무관하게 최초 element를 가리켜 "어느 element를 스캔하다 실패했나"를 로그에 보존한다 |
| `catch (Throwable ex)` :118 + `failureLogger.log` :120-123 | 실제로 예외를 관측한 프레임에서만 실행 | 폭탄이 있는 프레임 | 로그가 **가장 안쪽 annotation**을 지목하는 이유. 바깥 프레임은 예외가 아니라 boolean false를 받으므로 로그를 남기지 않는다. `return false`가 :111(재귀 결과 전파)과 :124(자기 관측 결과)로 나뉘는 것도 같은 이유 |

**(c) validate 축.** 다음은 시끄러운 출구 쪽의 동형 재귀에 쓰이는 이름들이다.

| 이름 | 역할 / 입출력 | 누가 언제 | 이 결함과의 관계 |
|---|---|---|---|
| `validateNestedAnnotations(value)` :175 | 동형 재귀의 validate 판. 출력 = void, 실패는 예외로 | `validate` :161에서만 | 신설. `canLoadNestedAnnotations`와 분기 형태가 미세하게 다르다(`if/else if` vs 조기 `return` 2연발) - 반환 규약이 달라 생긴 차이이며 동작 차이는 없다 |
| `catch (IllegalStateException ex) { throw ex; }` :163-164 | 안쪽이 만든 ISE를 **재래핑 없이** 통과시키는 가지 | 재귀 프레임마다 | base에도 있던 가지인데, 재귀가 붙으면서 **진단 품질 보존 장치**로 재활용된다. 없었다면 깊이마다 한 겹씩 감싸여 최상위 메시지가 바깥 annotation을 가리켰을 것이다 |
| `new IllegalStateException("Could not obtain annotation attribute value for " + get(i).getName() + " declared on @" + ClassUtils.getCanonicalName(annotation.annotationType()), ex)` :167-169 | 실패 보고. 메시지가 **그 프레임의** 속성 이름과 annotation 타입으로 조립된다 | 폭탄이 있는 프레임에서 1회 | 메시지가 최심부를 지목한다는 계약의 구현. 테스트가 `withMessageContaining("EnumValueInner")`로 못박았다 |

**(d) 종료 보장.** 다음은 재귀가 끝난다는 근거와, 그 근거를 헷갈리게 하는 대조군이다.

| 이름 | 역할 | 이 결함과의 관계 |
|---|---|---|
| 값 트리(annotation 인스턴스가 속성 호출로 이루는 트리) | 재귀가 실제로 걷는 대상 | JLS §9.6.1이 annotation 멤버 타입의 순환을 컴파일 에러로 금지하므로 항상 유한 - visited 집합이 없어도 종료한다 |
| 메타-annotation 그래프 | annotation 위에 붙은 annotation의 그래프 | **순환 가능**하다(`@Retention`과 `@Documented`가 서로를 참조). 이 재귀가 걷는 축이 아니다 - 헷갈리기 쉬운 대칭 |
| `AnnotationTypeMapping.computeSynthesizableFlag` (`AnnotationTypeMapping.java:262`) + `visitedAnnotationTypes` (:264, :290) | 같은 패키지의 다른 재귀. 타입 그래프를 걷기 때문에 visited 가드를 쓴다 | 대조군. "같은 패키지에 가드를 쓰는 재귀가 있는데 왜 여기는 없나"에 대한 답이 축의 차이다 |

**(e) 테스트 fixture와 헬퍼.** 다음은 `AttributeMethodsTests.java`가 이 결함을 재현하려고 세운 재료들이다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `EnumValueInner { ExampleEnum value(); }` :335-339 | 폭탄을 담는 최심부. 속성이 단일 enum이라 **base의 플래그로도 이미 probe 대상**이다 | 재귀가 도달하기만 하면 잡힌다는 것을 보이기 위한 설계 - 새 검사를 만든 게 아니라 도달 경로를 만든 PR임을 드러낸다 |
| `NestedValue { EnumValueInner value(); }` :342-346 | 1겹 포장 | depth-1 케이스 |
| `NestedArrayValue { EnumValueInner[] value(); }` :349-353 | 배열 포장 | 배열 분기와 빈 배열 경로 |
| `DeepNestedValue { NestedValue value(); }` :356-360 | 2겹 포장 | 재귀가 연쇄되는 경로(depth-2) |
| `mockBrokenEnumValueInner()` :255-259 | `value()`가 `EnumConstantNotPresentException`을 던지는 inner mock을 **완결된 상태로** 반환 | 2겹 mock의 안쪽. 다른 stubbing의 인자 자리에서 부르면 `UnfinishedStubbingException` |
| `mockHealthyEnumValueInner()` :261-265 | 정상 값(`ExampleEnum.ONE`)을 반환하는 inner mock | 양성 가드 - 재귀가 무고한 nested를 걸러버리지 않음을 고정 |
| `mockAnnotation(Class)` :276-280 | `annotationType()`이 스텁된 mock 생성 | 재귀가 `nested.annotationType()`으로 다음 타입을 정하므로 **이 스텁이 없으면 재귀 자체가 성립하지 않는다** |

## 3. 결함 경로 단계 추적

같은 오염(안쪽 annotation이 런타임에 없는 enum 상수를 참조)을 두 위치에 놓고 비교한다. 정상
케이스는 오염이 **직접 속성**에 있는 경우(`EnumValueInner`를 바로 스캔), 결함 케이스는 오염이
**한 겹 안**에 있는 경우(`NestedValue`를 스캔)다.

| 단계 | 코드 위치 | 정상 케이스 (직접 속성 오염) | 결함 케이스 (nested 오염, 수정 전) |
|---|---|---|---|
| 1. 플래그 판정 | 생성자 base :84 | `type = ExampleEnum` -> `isEnum()` true -> 플래그 true | `type = EnumValueInner` -> annotation 계열이 식에 없음 -> 플래그 **false** |
| 2. probe 게이트 | `canLoad` base :106 | 통과 | 차단 (호출 0회) |
| 3. 실호출 | base :108 | `invoke` -> `EnumConstantNotPresentException` | 일어나지 않음 |
| 3'. (플래그만 추가했다면) | base :108 | - | `invoke` -> **@EnumValueInner 프록시 반환, 예외 없음**. 반환값은 대입되지 않고 버려짐 |
| 4. 예외 관측 | base :113 | 포착 | 관측할 것이 없음 |
| 5. 보고 | base :116, :119 | warn 로그(@EnumValueInner) + `return false` | 루프 종료 -> `return true` |
| 6. 스캐너 | `AnnotationsScanner.java:447` | `annotations[i] = null` | 배열에 그대로 남음 |
| 7. 사용자 표면 | `isPresent(X)` | false | **true** |
| 8. 값 읽기 | `asMap()` | `{}` | `{value=@Inner(color=BLUE /* Warning: constant not present! */)}` - 폭탄을 품은 프록시가 값으로 실린다 |
| 9. typed 접근 | `synthesize().value().value()` | missing 계약 | raw `EnumConstantNotPresentException` 누출 |

단계 3'가 이 PR의 존재 이유다. #37153식 1줄 확장을 그대로 적용해 플래그를 세워도 결과는 5단계에서
`return true`로 같다 - **invoke가 성공하기 때문**이다. 스모크에서 실제로 확인된 사실이며, 이것이
"같은 모양의 구멍이라도 fix의 모양은 다르다"의 근거다.

수정 후에는 3'가 다음처럼 이어진다.

| 프레임 | 위치 | 동작 | 상태 |
|---|---|---|---|
| 1 | :109 | `value = invoke(nestedValue.value())` -> @EnumValueInner 프록시 | 예외 없음 |
| 1 | :110 | `canLoadNestedAnnotations(value, source)` 호출 | - |
| - | :132-133 | `value instanceof Annotation` -> `forAnnotationType(EnumValueInner).canLoad(...)` | 재귀 진입 |
| 2 | :107 | 안쪽 속성 타입이 enum -> 플래그 true | - |
| 2 | :109 | `invoke(inner.value())` -> `EnumConstantNotPresentException` | 폭탄 |
| 2 | :118-123 | `catch (Throwable)` -> warn 로그. `annotation` 파라미터가 @EnumValueInner이므로 **로그가 최심부를 지목** | - |
| 2 | :124 | `return false` | - |
| 1 | :110-111 | 예외가 아니라 boolean false를 받음 -> `return false` (로그 없음) | - |
| 스캐너 | :447 | 바깥 `@NestedValue`가 통째로 제거 | `isPresent=false`, `asMap()={}` |

`validate` 쪽은 같은 트리를 같은 순서로 걷되 프레임 2가 ISE를 만들고(:167-169), 프레임 1이
:163-164에서 그것을 **그대로 재던진다**. 그래서 최상위 메시지가 여전히 `@EnumValueInner`를
가리킨다. depth-2(`DeepNestedValue` -> `NestedValue` -> `EnumValueInner`)에서도 통과 프레임이 둘로
늘 뿐 결과는 같다.

## 4. 계약

이 무대가 고정하고 있던 약속은 다섯이며, 그중 결함이 어긴 것은 첫째 하나다.

- **`canLoad`의 javadoc** (:101): `@return {@code true} if all values are present`. "모든 값"에
  nested annotation 안의 값이 포함되는지가 이 PR이 답하는 질문이다. 이 PR은 포함된다고 읽는다 -
  안쪽 값이 없으면 바깥 annotation을 온전히 읽을 수 없기 때문이다. 결함 상태는 안쪽에 없는 값이
  있는데도 true를 반환한다.
- **all-or-nothing 격리 의미론**: 필터링 단위는 annotation 1개다. nested 멤버 하나가 깨졌다고
  그 속성만 숨기는 것은 annotation 타입 계약상 표현이 불가능하다(던지면 원점 회귀, null은 계약
  위반, 기본값 대입은 조작). 따라서 **의도된 blast radius는 바깥 annotation 전체**이며, 이것은
  결함이 아니라 채택된 설계다.
- **진단 메시지 계약**: 실패 보고는 실제로 깨진 가장 안쪽 annotation을 지목한다. base의
  `catch (IllegalStateException ex) { throw ex; }`(:163-164)가 이 계약을 이미 가능하게 하고
  있었고, 테스트가 `withMessageContaining("EnumValueInner")`와 `withCauseInstanceOf(...)`로
  못박았다(리뷰 F3 반영). 이 어서션이 없으면 각 프레임이 자기 컨텍스트로 재래핑하는 미래 수정이
  타입 검사만으로 통과해 버린다.
- **빈 배열의 귀결**: `@NestedArrayValue({})`는 합법이고 검사할 원소가 없으므로 통과가 정답이다
  (공허한 참). 현재 구현은 "깨진 것을 발견하면 false" 구조라 루프 0회면 자연히 :142의
  `return true`로 떨어진다.
- **보존 동작**: 기존 probe 대상(`Class`, `Class[]`, enum)의 판정과 비용, `hasNestedAnnotation`의
  값과 소비처, 정상 nested annotation의 통과. 명세서가 금지영역으로 고정했고 가드 6건이 지킨다.

## 5. 수정안

**before** (base `a16509447075`, `AttributeMethods.java:80`, `:84`, `:108`, `:142`)

```java
			if (!foundNestedAnnotation && (type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation()))) {
				foundNestedAnnotation = true;
			}
			ReflectionUtils.makeAccessible(method);
			this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class || type.isEnum());
```

```java
				try {
					AnnotationUtils.invokeAnnotationMethod(get(i), annotation);
				}
```

**after** (`refs/pr/37157`, `:80-86`, `:108-113`, `:131-143`)

```java
			boolean nestedAnnotation = (type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation()));
			if (!foundNestedAnnotation && nestedAnnotation) {
				foundNestedAnnotation = true;
			}
			ReflectionUtils.makeAccessible(method);
			this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class ||
					type.isEnum() || nestedAnnotation);
```

```java
				try {
					Object value = AnnotationUtils.invokeAnnotationMethod(get(i), annotation);
					if (!canLoadNestedAnnotations(value, source)) {
						return false;
					}
				}
```

```java
	private boolean canLoadNestedAnnotations(@Nullable Object value, AnnotatedElement source) {
		if (value instanceof Annotation nested) {
			return forAnnotationType(nested.annotationType()).canLoad(nested, source);
		}
		if (value instanceof Annotation[] nestedArray) {
			for (Annotation nested : nestedArray) {
				if (!forAnnotationType(nested.annotationType()).canLoad(nested, source)) {
					return false;
				}
			}
		}
		return true;
	}
```

`validate` 쪽도 동형이다(:160-161이 반환값을 받아 :175의 `validateNestedAnnotations`에 넘긴다).

**왜 이 위치인가.** 결함은 "판정이 틀렸다"가 아니라 "검사가 한 겹에서 멈춘다"이므로, 고쳐야 할
곳은 판정식이 아니라 **검사의 도달 범위**다. 그리고 도달 범위를 넓히는 가장 작은 수단이 이미
있던 진입점(`forAnnotationType`)을 재사용해 같은 검사를 안쪽 인스턴스에 다시 거는 것이다.
헬퍼를 `private`으로 둔 덕에 클래스의 계약 표면(package-private 메서드 목록)은 변하지 않는다.

**검토된 대안과 기각 이유.**

- **플래그 확장만 (#37153식 1줄)**: 스모크로 재현 실패를 확인했다. invoke가 성공하므로 아무것도
  잡히지 않는다(§3 단계 3'). 이 PR이 존재하는 이유 자체다.
- **`visited` 집합 추가**: `AnnotationTypeMapping`이 쓰는 가드를 그대로 들여오는 안. 기각했다 -
  이 재귀가 걷는 것은 값 트리이고 JLS §9.6.1이 멤버 타입 순환을 컴파일 에러로 금지하므로 순환이
  문법적으로 불가능하다. 리뷰에서 "javac가 아닌 수제 구현체가 순환 annotation을 만들면?"이라는
  질문이 나왔고, `canLoad`/`validate`는 package-private이며 프레임워크 호출처(`AnnotationsScanner`)는
  JDK 파싱 프록시만 공급하므로 그런 구현체가 닿는 경로가 없다는 것으로 해소했다. 불요 복잡도로
  판단해 미도입.
- **재귀 대신 명시적 스택**: 깊이가 실무에서 1~2단이고 문법적으로 유한하므로 이득이 없다.
- **속성 단위 부분 숨김**: annotation 타입 계약상 표현 불가능(§4).
- **재귀 전 사전 게이트로 비용 최적화**(안쪽에 flagged 속성이 있는 타입만 내려가기): 마이크로벤치
  결과 추가 비용의 지배 항이 **바깥 invoke 자체**(속성당 +50~70 ns)이고 내부 재귀 단락으로 아낄 수
  있는 몫은 약 12 ns였다. 복잡도 대비 실익이 약해 미채택했고, 이 수치가 PR 본문 성능 서술의 근거가
  됐다.

## 6. 범위 밖과 인접 영향

이 PR이 닿지 못하는 한계와, 형제 PR과의 관계, 그리고 감수한 비용을 정리한다.

- **Case A - nested annotation 타입 자체가 없는 경우**: 이 PR로 해결 불가다. 안쪽 annotation의
  **타입**이 classpath에 없으면 `source.getDeclaredAnnotations()`(`AnnotationsScanner.java:439`)의
  파싱 단계에서 이미 `NoClassDefFoundError`가 나고, 그것은 probe가 시작되기 전이다. 게다가 `Error`를
  프레임워크가 삼켜야 하는가 자체가 논쟁적이다. 수정 후 스모크에서 Case A가 **불변**임을 확인했고,
  PR 본문에 한계로 명시했다.
- **#37153과의 관계**: 두 PR이 같은 줄(플래그 계산식)을 서로 다르게 넓힌다. #37157은 enum 배열 항을
  **포함하지 않으며**(내용 분리), 먼저 머지되는 쪽 기준으로 나머지가 rebase되어야 한다. 최종
  형태는 `Class`, `Class[]`, enum, enum 배열, annotation, annotation 배열이 모두 선 식이다.
  PR 본문에 "complementary to #37153"으로 관계를 명시했다.
- **동작 변화와 하위호환**: 정상 annotation은 무변화(가드 6건이 고정). 변하는 것은 nested 오염
  annotation이 스캔에서 사라진다는 점이며, blast radius가 바깥 annotation 전체라는 사실을 PR
  본문에 서술했다. 시끄러운 출구 쪽에서는 `ConfigurationClassParser`가 ASM 폴백으로 넘어가는
  범위가 nested까지 넓어진다.
- **비용**: 실측(before/after jar 마이크로벤치, warmup 20만 + 5라운드 x 50만, best-of-5) 결과
  기존 probe는 무회귀(Plain 7 -> 7, Enum 25 -> 25 ns/op), nested 속성은 +50~70 ns/op
  (NestedPlain 8 -> 58, NestedEnum 7 -> 70, NestedArr[1] 7 -> 77), 비캐시 element 스캔은
  523 -> 826 ns/op다. 주 스캔 경로는 `declaredAnnotationCache`가 element당 1회로 제한한다.
- **남은 계열 없음**: 이 PR 이후 판정식은 `Class`, enum, annotation의 스칼라와 배열로 닫힌다.
  annotation 멤버로 허용되는 나머지 타입(원시형, `String`)은 지연 실패가 없다.
