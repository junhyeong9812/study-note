# PR #36913 — 무대 구조와 수정 전 워크플로우

> PR #36913의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 PR은 OPEN이므로 아래
> `OptionalToObjectConverter.java` 인용은 **수정 전 코드 그대로**다.

## 1. 무대 — 실구조

이 PR의 무대는 `ConversionService`가 "어떤 컨버터를 쓸까"를 고르는 선택 파이프라인이고, 그 파이프라인의 마지막 관문인 `matches()` 한 줄이 대상이다.\
먼저 파이프라인 전체의 소유 관계를 본다.

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ ConversionService (interface)              ConversionService.java:29          │
│   canConvert(Class, Class)                                       :45          │
│   canConvert(TypeDescriptor, TypeDescriptor)                     :65          │
│   convert(Object, Class)                                         :75          │
│   convert(Object, TypeDescriptor, TypeDescriptor)                :106         │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ implements
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ GenericConversionService              GenericConversionService.java:63        │
│───────────────────────────────────────────────────────────────────────────────│
│  NO_OP_CONVERTER  : GenericConverter   (통과용 싱글턴)            :68         │
│  NO_MATCH         : GenericConverter   (캐시 전용 음성 마커)      :74         │
│  converters       : Converters                                    :77         │
│  converterCache   : Map<ConverterCacheKey, GenericConverter>      :79         │
│───────────────────────────────────────────────────────────────────────────────│
│  canConvert(TypeDescriptor, TypeDescriptor)                       :140        │
│  convert(Object, TypeDescriptor, TypeDescriptor)                  :169        │
│  getConverter(source, target)              protected              :224        │
│  getDefaultConverter(source, target)       protected              :253        │
│  handleConverterNotFound(...)              private                :278        │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ has-a
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Converters  (private static class)                                :464        │
│   globalConverters : Set<GenericConverter>       (무조건부 전역)  :466        │
│   converters       : Map<ConvertiblePair, ConvertersForPair>      :468        │
│   add(GenericConverter)                                           :470        │
│   find(sourceType, targetType)                                    :500        │
│   getRegisteredConverter(source, target, pair)                    :516        │
│   getClassHierarchy(Class)                                        :541        │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ 값
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ ConvertersForPair (private static class)                          :612        │
│   converters : Deque<GenericConverter>   (addFirst — 나중 등록 우선) :614/:616│
│   getConverter(sourceType, targetType)                            :620        │
│     1패스: ConditionalGenericConverter 면 matches() 를 물어본다   :622-627    │
│     2패스: ConverterAdapter.matchesFallback (6.2.3 이전 호환)     :629-634    │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ 담고 있는 원소 중 하나
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ OptionalToObjectConverter  (final, package-private)                           │
│                              OptionalToObjectConverter.java:37                │
│   implements ConditionalGenericConverter                                      │
│   conversionService : ConversionService                           :39         │
│   getConvertibleTypes() → { (Optional.class, Object.class) }      :48         │
│   matches(sourceType, targetType)                                 :53  ◄── 대상 │
│   convert(source, sourceType, targetType)                         :58         │
└───────────────────────────────────────────────────────────────────────────────┘
```

> **ConvertiblePair** — "소스 타입 -> 대상 타입" 한 쌍을 담는 등록 키. 레지스트리는 이 키로 컨버터를 모아 둔다.\
> 예: `OptionalToObjectConverter`는 `(Optional.class, Object.class)` 한 쌍만 선언한다.

> **GenericConverter** — 소스·대상을 `TypeDescriptor` 단위로 받아 변환하는 저수준 컨버터 인터페이스. 제네릭까지 보고 판단해야 하는 컨버터가 이것을 쓴다.\
> 예: `Converters`의 `globalConverters`·`converters` 맵이 담고 있는 원소가 전부 이 타입이다.

`ConditionalGenericConverter`는 `GenericConverter`와 `ConditionalConverter`를 합친 빈 인터페이스다(`ConditionalGenericConverter.java:33`).\
실질은 `ConditionalConverter`의 메서드 하나뿐이다.

```java
// ConditionalConverter.java:45-52 (javadoc 요약)
/**
 * Should the conversion from sourceType to targetType currently under
 * consideration be selected?
 */
boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType);
```

즉 `matches()`는 **"이 변환쌍에 내가 선택되어야 하는가"** 를 스스로 답하는 자기 판별 함수이고, 이 답이 `canConvert`의 최종 결과를 그대로 결정한다.

수정 전 `matches()`의 본문은 한 줄이다.

```java
// OptionalToObjectConverter.java:52-55
@Override
public boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType) {
    return ConversionUtils.canConvertElements(sourceType.getElementTypeDescriptor(), targetType, this.conversionService);
}
```

여기 쓰인 두 협력자의 실구조가 결함의 전부다.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ TypeDescriptor#getElementTypeDescriptor()      TypeDescriptor.java:370 │
│   ├─ resolvableType.isArray()  ─▶ 컴포넌트 타입 카드                   │
│   ├─ Stream 대입 가능          ─▶ Stream 의 제네릭 0번                 │
│   └─ 그 외                      ─▶ asCollection().getGeneric(0)        │
│                                     Optional 은 Collection 이 아니므로 │
│                                     → NONE → getRelatedIfResolvable   │
│                                     → null                             │
│   javadoc: "배열 컴포넌트 타입 또는 Collection 원소 타입, 아니면 null" │
│            (:361-368 — Optional 은 아예 대상이 아니다)                 │
└────────────────────────────────────────────────────────────────────────┘
                    │ null 이 이쪽으로 흘러든다
                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ ConversionUtils#canConvertElements(...)        ConversionUtils.java:51 │
│   if (targetElementType == null)      return true;   // "yes"    :54   │
│   if (sourceElementType == null)      return true;   // "maybe"  :58   │◄─ 항상 여기
│   if (conversionService.canConvert(src, tgt)) return true;       :62   │
│   if (ClassUtils.isAssignable(src, tgt))      return true;       :66   │
│   return false;                                                  :71   │
└────────────────────────────────────────────────────────────────────────┘
```

`sourceElementType == null -> true`는 "모르면 막지 않는다"는 관대 규칙이다.\
그 자체는 합리적인데, `getElementTypeDescriptor()`가 Optional에 대해 **언제나** null을 주므로 관대 규칙이 항상 발동해서 `matches()`가 상수 함수가 됐다.

비교 대상으로 형제 컨버터를 나란히 둔다.\
같은 파일 쌍에서 반대 방향을 담당하는 `ObjectToOptionalConverter`는 제네릭을 `ResolvableType`으로 직접 꺼낸다.

```java
// ObjectToOptionalConverter.java:60-68  (반대 방향, 이미 올바른 형태)
@Override
public boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType) {
    if (targetType.getResolvableType().hasGenerics()) {
        return this.conversionService.canConvert(sourceType, new GenericTypeDescriptor(targetType));
    }
    else {
        return true;
    }
}

// :92-98  제네릭 0번으로 카드를 다시 만드는 내부 클래스
private static class GenericTypeDescriptor extends TypeDescriptor {
    public GenericTypeDescriptor(TypeDescriptor typeDescriptor) {
        super(typeDescriptor.getResolvableType().getGeneric(), null, typeDescriptor.getAnnotations());
    }
}
```

`getResolvableType().getGeneric()`가 Optional의 원소 타입을 얻는 올바른 통로이고, 이 PR의 수정은 소스 방향에서 같은 통로를 쓰게 맞추는 일이다.

두 컨버터는 `DefaultConversionService`가 나란히 등록한다.

```java
// DefaultConversionService.java:103-104
converterRegistry.addConverter(new ObjectToOptionalConverter((ConversionService) converterRegistry));
converterRegistry.addConverter(new OptionalToObjectConverter((ConversionService) converterRegistry));
```

## 2. 수정 전 동작 워크플로우

BLUF: `canConvert(Optional<Integer>, LocalDate)` 질의는 캐시 -> 타입 계층 조합 -> `ConvertersForPair` -> `matches()` 순으로 내려가고, 마지막 `matches()`가 무조건 true를 돌려주므로 질의가 true로 끝난다.\
그러나 같은 입력으로 `convert()`를 실행하면 내부 위임에서 컨버터를 못 찾아 예외가 난다.

먼저 **질의(canConvert)** 경로다.

```text
cs.canConvert(TypeDescriptor(Optional<Integer>), TypeDescriptor(LocalDate))
        │
        ▼
GenericConversionService.canConvert(source, target)          GenericConversionService.java:140
        │  return (sourceType == null || getConverter(sourceType, targetType) != null)
        ▼
getConverter(source, target)                                                    :224
        │
        ├─ converterCache.get(key)                                              :226
        │     캐시 히트면 즉시 반환 (NO_MATCH 면 null)                          :227-229
        │     ─ 최초 질의는 미스 ─
        ▼
converters.find(sourceType, targetType)                                         :231
        │       Converters.find                                                 :500
        ├─ sourceCandidates = getClassHierarchy(Optional.class)                  :502
        │       [Optional, Object]           (Optional 은 상속·구현이 없다)
        ├─ targetCandidates = getClassHierarchy(LocalDate.class)                 :503
        │       [LocalDate, Temporal, TemporalAdjuster, ChronoLocalDate,
        │        Comparable, Serializable, Object, …]
        │
        └─ 이중 루프로 (source, target) 쌍을 순서대로 조회                       :504-512
              (Optional, LocalDate)  → 등록 없음
              (Optional, Temporal)   → 등록 없음
              …
              (Optional, Object)     → 등록 있음! ★
        ▼
getRegisteredConverter(source, target, ConvertiblePair(Optional, Object))        :516
        │
        ├─ converters.get(pair) → ConvertersForPair                              :520
        ▼
ConvertersForPair.getConverter(sourceType, targetType)                           :620
        │  1패스: Deque 를 순회하며
        │    converter instanceof ConditionalGenericConverter 이면 matches() 질의 :622-624
        ▼
OptionalToObjectConverter.matches(Optional<Integer>, LocalDate)
        OptionalToObjectConverter.java:53
        │
        ├─ sourceType.getElementTypeDescriptor()          TypeDescriptor.java:370
        │     isArray()? NO / Stream? NO
        │     asCollection().getGeneric(0) → NONE                          :377
        │     → getRelatedIfResolvable(NONE) → null          :477  ★ Optional 은 대상 밖
        │
        ▼
ConversionUtils.canConvertElements(null, LocalDate카드, cs)   ConversionUtils.java:51
        │
        ├─ targetElementType == null ? NO
        ├─ sourceElementType == null ? YES ─▶ return true    ("maybe")    :58-60
        ▼
matches() == true
        ▼
ConvertersForPair 가 OptionalToObjectConverter 반환
        ▼
getConverter 가 캐시에 저장 후 반환                                              :236-239
        ▼
canConvert == true            ← 과대보고
```

이제 같은 카드로 **실행(convert)** 경로를 탄다.\
앞부분은 동일하고, 컨버터를 실제로 호출하는 지점부터 갈린다.

```text
cs.convert(Optional.of(42), TypeDescriptor(Optional<Integer>), TypeDescriptor(LocalDate))
        │
        ▼
GenericConversionService.convert(source, sourceType, targetType)                 :169
        │  (getConverter 는 위와 같은 경로로 OptionalToObjectConverter 를 돌려준다)
        ▼
ConversionUtils.invokeConverter(converter, source, sourceType, targetType)       :181
        │       ConversionUtils.java:37
        ▼
OptionalToObjectConverter.convert(Optional.of(42), …)   OptionalToObjectConverter.java:58
        │
        ├─ source == null ? NO                                                   :59
        ├─ unwrappedSource = optional.orElse(null)  → Integer 42                 :63
        ├─ unwrappedSourceType = TypeDescriptor.forObject(42)  → Integer 카드    :64
        │     ★ 여기서 카드가 "선언"이 아니라 "실제 값"에서 만들어진다
        ▼
this.conversionService.convert(42, Integer카드, LocalDate카드)                   :65
        │       (재귀 — 바깥과 같은 GenericConversionService)
        ▼
getConverter(Integer, LocalDate)
        │  getClassHierarchy(Integer) x getClassHierarchy(LocalDate) 전부 조회
        │  → 등록된 쌍 없음
        │  → getDefaultConverter: Integer.isAssignableTo(LocalDate)? NO → null   :253
        ▼
handleConverterNotFound(42, Integer, LocalDate)                                  :278
        ├─ source == null ? NO
        ├─ sourceType.isAssignableTo(targetType) ? NO
        ▼
throw ConverterNotFoundException(Integer, LocalDate)                             :289
        │
        └─▶ invokeConverter 의 catch(Throwable) 가 감싸                          :46-48
              → ConversionFailedException(Optional<Integer> → LocalDate)
```

여기서 계약 불일치가 눈에 보인다.\
`canConvert`는 **선언 카드**(`Optional<Integer>`)만 보고 답하는데, `convert`는 벗겨낸 **값**(`42`)으로 다시 질의한다.\
두 질문이 같은 근거를 쓰지 않으므로 답이 갈릴 수 있고, 수정 전에는 `matches()`가 선언 카드를 아예 보지 않아서 갈림이 상시화됐다.

수정 후 `matches()`가 선언 카드의 제네릭을 읽으면, 질의는 `Integer -> LocalDate` 컨버터의 부재를 **미리** 알게 되어 false를 돌려주고, `getConverter`는 `NO_MATCH`를 캐시한다.\
그러면 `convert()`도 `OptionalToObjectConverter`를 고르지 않고 바깥에서 `ConverterNotFoundException(Optional<Integer>, LocalDate)`을 던진다.\
수정 전에는 안쪽에서 난 같은 예외를 `ConversionUtils.invokeConverter`가 `ConversionFailedException`으로 감싸 던졌으므로, 던지는 자리만이 아니라 **바깥으로 나오는 예외 타입도 바뀐다**(2026-08-27 실측 정정 — 이전 판본의 "예외 타입은 같다"는 틀렸다. analysis.md §3).

> **NO_MATCH** — "이 타입쌍에는 맞는 컨버터가 없다"를 캐시에 남기기 위한 음성 마커 싱글턴. 다음 질의가 같은 탐색을 반복하지 않게 한다.\
> 예: 수정 후 `(Optional<Integer>, LocalDate)` 판정 false가 `NO_MATCH`로 저장된다.

## 3. 분기 처리 워크플로우

BLUF: 선택 파이프라인에는 네 층의 분기가 있고, 이 PR이 건드리는 것은 가장 안쪽 한 층뿐이다.\
바깥 세 층은 그대로 두고 안쪽 판정만 정확해지면 전체 결과가 맞아떨어지는 구조다.

전체 선택 분기도. `[BUG]`가 결함이 살던 갈래다.

```text
canConvert(source, target)                        GenericConversionService.java:140
   │
   ├─ sourceType == null ? ──▶ YES ─▶ return true   (null 소스는 언제나 가능)
   │
   ▼
getConverter(source, target)                                                    :224
   │
   ├─ [층1] 캐시 조회                                                           :226
   │     ├─ 히트 && != NO_MATCH ─▶ 그 컨버터 반환 (분기 종료)
   │     ├─ 히트 && == NO_MATCH ─▶ null 반환      (분기 종료)
   │     └─ 미스 ─▶ 계속
   │
   ├─ [층2] converters.find(source, target)                                     :231
   │     │      Converters.find                                                 :500
   │     │
   │     ├─ 소스 계층 x 대상 계층 이중 루프                                     :504-512
   │     │     각 (sourceCandidate, targetCandidate) 조합마다
   │     │     getRegisteredConverter 호출                                      :507
   │     │        │
   │     │        ├─ 등록된 ConvertersForPair 있나 ?                            :520
   │     │        │     ├─ YES ─▶ [층3] ConvertersForPair.getConverter          :620
   │     │        │     │            │
   │     │        │     │            ├─ 1패스: Deque 순회                       :622
   │     │        │     │            │    ├─ ConditionalGenericConverter 아님
   │     │        │     │            │    │     ─▶ 무조건 선택
   │     │        │     │            │    └─ 맞으면 [층4] matches() 질의        :624
   │     │        │     │            │          ├─ true  ─▶ 이 컨버터 선택
   │     │        │     │            │          └─ false ─▶ 다음 후보로
   │     │        │     │            │
   │     │        │     │            └─ 2패스: ConverterAdapter.matchesFallback :629-634
   │     │        │     │                 (6.2.3 이전 raw 제네릭 호환 경로)
   │     │        │     │
   │     │        │     └─ NO ──▶ 다음
   │     │        │
   │     │        └─ globalConverters 순회 (getConvertibleTypes()==null 인 것들) :528-532
   │     │              ConditionalConverter.matches() 가 true 면 선택
   │     │
   │     └─ 모든 조합 실패 ─▶ null
   │
   ├─ [층2b] converter == null 이면 getDefaultConverter                         :232-234
   │     sourceType.isAssignableTo(targetType) ? ─▶ YES ─▶ NO_OP_CONVERTER      :254
   │                                              └─ NO  ─▶ null
   │
   └─ 결과 캐시 저장 (null 이면 NO_MATCH)                                       :236-242
```

이 PR이 바꾸는 [층4]의 내부 분기도. 위가 수정 전, 아래가 수정 후다.

```text
[수정 전] OptionalToObjectConverter.matches()      OptionalToObjectConverter.java:53
   │
   ▼
sourceType.getElementTypeDescriptor()              TypeDescriptor.java:370
   │
   ├─ resolvableType.isArray() ?     ──▶ NO   (Optional 은 배열이 아니다)
   ├─ Stream 대입 가능 ?              ──▶ NO
   └─ asCollection().getGeneric(0)    ──▶ Optional 은 Collection 이 아니므로 NONE
         └─▶ getRelatedIfResolvable(NONE) ─▶ null
   │
   ▼
canConvertElements(null, target, cs)               ConversionUtils.java:51
   │
   ├─ targetElementType == null ?  ──▶ NO
   ├─ sourceElementType == null ?  ──▶ YES ─▶ return true          [BUG] 항상 이 갈래
   ├─ (도달 불가) canConvert(src, tgt) ?
   ├─ (도달 불가) isAssignable(src, tgt) ?
   └─ (도달 불가) return false
```

```text
[수정 후] matches()
   │
   ▼
ResolvableType elementType = sourceType.getResolvableType().getGeneric()
   │                                          ResolvableType.java:754
   │
   ▼
elementType.resolve() == null ?                   ResolvableType.java:882
   │
   ├─ YES ─▶ return true       (관대 유지)
   │           ├ raw Optional            : 제네릭 자체가 없음 → NONE.resolve() == null
   │           ├ Optional<?>             : 와일드카드 상한이 Object
   │           │     resolveType()  ResolvableType.java:924-930
   │           │       └ resolveBounds(upperBounds)  :1467
   │           │           bounds[0] == Object.class ─▶ return null   :1468-1470
   │           └ Optional<T> 미해석      : variableResolver 실패 후
   │                 resolveBounds(변수 bounds) ─▶ 역시 Object → null  :940
   │
   └─ NO ──▶ 원소 타입을 카드로 만들어 판별
               new TypeDescriptor(elementType, null, null)  TypeDescriptor.java:128
               │
               ▼
             canConvertElements(원소카드, target, cs)      ConversionUtils.java:51
               │
               ├─ targetElementType == null ? ─▶ NO
               ├─ sourceElementType == null ? ─▶ NO   (이제 여기서 안 빠진다)
               ├─ cs.canConvert(원소, target) ? ─▶ YES ─▶ true
               │      예: Integer → String  (FallbackObjectToStringConverter 존재)
               ├─ isAssignable(원소.getType(), target.getType()) ? ─▶ YES ─▶ true
               │      예: 원소가 Object 로 떨어진 경우 — 무엇이든 담을 수 있음
               └─ 둘 다 아니면 ─▶ return false
                      예: Integer → LocalDate
```

`Optional<? extends Number>`가 어느 갈래로 가는지가 두 분기의 차이를 가장 잘 보여 준다.\
`resolveBounds`가 `bounds[0] == Object.class`일 때만 null을 돌려주므로(`ResolvableType.java:1467-1472`), 상한이 `Number`면 null이 아니고 -> `Number` 카드로 실제 판별이 이루어진다.\
상한이 없는 `Optional<?>`는 상한이 `Object`라 null이 되어 관대 갈래로 간다.\
**결과값이 같은 raw/`Optional<?>`/`Optional<T>` 셋도 도달 경로가 다르다**는 것이 tests.md의 가드 3건이 각각 존재하는 이유다.

`ConversionUtils.canConvertElements`의 네 갈래를 관계로 정리하면 다음과 같다.

```text
                      targetElementType == null
                             │ yes → true ("yes": 대상이 무엇이든 상관없음)
                             │ no
                             ▼
                      sourceElementType == null
                             │ yes → true ("maybe": 모르니 막지 않음)   ← 수정 전 상시 경로
                             │ no
                             ▼
              conversionService.canConvert(src, tgt)
                             │ yes → true ("yes": 등록된 컨버터 있음)
                             │ no
                             ▼
        ClassUtils.isAssignable(src.getType(), tgt.getType())
                             │ yes → true ("maybe": 변환 없이 대입 가능)
                             │ no
                             ▼
                           false ("no")
```

주석의 `yes` / `maybe` / `no` 세 등급이 그대로 코드에 남아 있다는 점이 이 함수의 성격을 말해 준다.\
이 함수는 애초에 **확정적 부정만 신뢰할 수 있는** 근사 판정기이고, 그래서 입력으로 정확한 원소 타입을 주는 일이 호출자의 책임이다.

> **근사 판정기** — 확실히 아닌 경우만 정확히 걸러 내고, 애매하면 일단 통과시키는 판정 함수.\
> 예: `canConvertElements`가 원소 타입을 모를 때 "maybe"로 true를 내는 것.

## 4. 스프링 전역에서의 자리

BLUF: `canConvert`는 프레임워크 곳곳에서 **"변환을 시도할지, 다른 경로로 갈지"를 가르는 분기 조건**으로 쓰인다.\
그래서 잘못된 true는 단순한 오답이 아니라 잘못된 경로 선택을 부른다.

먼저 이 컨버터가 어떻게 레지스트리에 들어가는지다.

```text
new DefaultConversionService()                   DefaultConversionService.java:53
        └─▶ addDefaultConverters(this)                                    :89
              ├─ addScalarConverters(registry)                            :90 → :139
              ├─ addCollectionConverters(registry)                        :91 → :114
              ├─ … ObjectToObjectConverter / IdToEntityConverter /
              │    FallbackObjectToStringConverter …                      :100-102
              ├─ new ObjectToOptionalConverter(cs)                        :103
              └─ new OptionalToObjectConverter(cs)                        :104
                    └─▶ GenericConversionService.addConverter(GenericConverter) :104
                          └─▶ Converters.add                                    :470
                                getConvertibleTypes() = {(Optional, Object)} 이므로
                                converters 맵의 그 키에 addFirst          :479 / :617
```

`addFirst`라는 점이 중요하다.\
나중에 등록된 컨버터가 먼저 질의를 받는다(`GenericConversionService.java:616-618`).\
즉 `(Optional, Object)` 쌍에 사용자 컨버터를 추가로 등록하면 그쪽이 먼저 `matches()`를 받고, 거절해야만 `OptionalToObjectConverter`에게 차례가 온다.

```text
ConvertiblePair(Optional, Object) 키가 들고 있는 Deque — addFirst 로 쌓인다

  head  +-----------------------------+   matches() 를 먼저 받는 자리
        | 사용자 컨버터 (나중 등록)   |
        +-----------------------------+
                    |
                    | false 를 돌려주면
                    v
        +-----------------------------+   그제서야 차례가 온다
        | OptionalToObjectConverter   |
        +-----------------------------+
```

먼저 등록된 쪽이 아니라 나중에 등록된 쪽이 앞에 선다.

> **Deque / addFirst** — 양쪽 끝에서 넣고 뺄 수 있는 큐. `addFirst`는 맨 앞에 끼워 넣는 것이라 나중 것이 먼저 순회된다.\
> 예: `ConvertersForPair.converters`가 `Deque<GenericConverter>`이고 `add`가 `addFirst`를 쓴다.

이제 실제 소비처다.\
grep으로 확인한 `canConvert` 호출처 중 프레임워크 동작을 가르는 자리들이다.

```text
$ grep -rn "\.canConvert(" --include=*.java spring-beans/src/main spring-context/src/main \
        spring-web/src/main spring-webmvc/src/main spring-core/src/main spring-messaging/src/main

spring-beans/…/TypeConverterDelegate.java:126            빈 프로퍼티 바인딩 (1차 시도)
spring-beans/…/TypeConverterDelegate.java:250            빈 프로퍼티 바인딩 (에디터 실패 후 2차)
spring-context/…/AbstractPropertyBindingResult.java:127  폼 필드 표시값 포맷팅
spring-context/…/AbstractPropertyBindingResult.java:170  같은 클래스, String→필드 방향
spring-web/…/ObjectToStringHttpMessageConverter.java:94  HTTP 메시지 읽기 가능 여부
spring-web/…/ObjectToStringHttpMessageConverter.java:99  HTTP 메시지 쓰기 가능 여부
spring-webmvc/…/ServletModelAttributeMethodProcessor.java:139  URI 변수 → 모델 속성
spring-messaging/…/GenericMessageConverter.java:64       메시지 페이로드 변환
spring-core/…/ConvertingPropertyEditorAdapter.java:55    PropertyEditor 어댑터
spring-core/…/ConversionUtils.java:62                    (컨버터 내부 재귀 — 위에서 본 자리)
```

가장 대표적인 소비 형태가 `TypeConverterDelegate`다.\
여기서 `canConvert`는 **에러 처리 경로를 고르는 조건**으로 쓰인다.

```java
// TypeConverterDelegate.java:123-134  (convertIfNecessary 앞부분)
if (editor == null && conversionService != null && newValue != null && typeDescriptor != null) {
    TypeDescriptor sourceTypeDesc = TypeDescriptor.forObject(newValue);
    if (conversionService.canConvert(sourceTypeDesc, typeDescriptor)) {   // ← :126
        try {
            return (T) conversionService.convert(newValue, sourceTypeDesc, typeDescriptor);
        }
        catch (ConversionFailedException ex) {
            // fallback to default conversion logic below
            conversionAttemptEx = ex;
        }
    }
}
```

흐름으로 보면 이렇다.

```text
BeanWrapperImpl / DataBinder 가 프로퍼티 값을 세팅
        │
        ▼
TypeConverterDelegate.convertIfNecessary(name, old, new, requiredType, typeDescriptor)
        TypeConverterDelegate.java:114
        │
        ├─ canConvert(source, target) ?                                    :126
        │     │
        │     ├─ true  ─▶ convert 시도
        │     │             ├─ 성공 ─▶ 반환
        │     │             └─ ConversionFailedException ─▶ 기억해 두고 아래로 폴백
        │     │
        │     └─ false ─▶ 아예 시도하지 않고 PropertyEditor 경로로
        │
        ▼
   PropertyEditor / 기본 변환 로직
        │
        └─ 그래도 실패하면
             ├─ conversionAttemptEx 가 있으면 그 예외를 그대로 던진다      :247
             └─ 없으면 canConvert 재시도 후 IllegalArgumentException 조립  :249-252
```

여기서 잘못된 true의 대가가 드러난다.\
`canConvert`가 true를 주면 `ConversionService.convert`가 먼저 시도되고, 실패하면 그 예외가 `conversionAttemptEx`에 기억되어 **최종 사용자 메시지를 결정한다**.\
즉 "변환기가 없다"는 깔끔한 음성 답을 받아 PropertyEditor 경로로 갔어야 할 입력이, 변환 실패 예외를 안고 다른 메시지로 끝난다.\
`ObjectToStringHttpMessageConverter.canRead/canWrite`(`:94`, `:99`)처럼 `canConvert`가 곧 컴포넌트의 적용 가능성 선언이 되는 자리에서는 영향이 더 직접적이다 — 읽을 수 없는 바디를 읽겠다고 나서게 된다.

다만 영향 범위는 좁다.\
위 호출처들은 대부분 `TypeDescriptor.forObject(값)`으로 소스 카드를 만드는데(`TypeConverterDelegate.java:125`, `TypeDescriptor.java:561`), 실제 값이 `Optional` 인스턴스인 경우 `forObject`는 제네릭을 알 수 없어 raw `Optional` 카드를 만든다.\
그러면 수정 후에도 관대 갈래로 빠져 결과가 같다.\
결함이 실제로 드러나는 것은 **선언에서 온 카드**가 소스로 들어가는 경우 — 필드·메서드 파라미터에서 만든 `TypeDescriptor`처럼 `Optional<X>`의 `X`가 살아 있는 카드다.\
PR 본문이 "Impact is bounded"라고 적은 근거가 이 구조다.

## 5. 관련 개념

이 구조를 이해하는 데 필요한 개념 중 별도 문서가 있는 것은 링크로 대신한다.

- 컴파일 타임 / 선언 메타데이터 런타임 / 값 런타임의 3층 구분 — `canConvert`가 왜 값 없이 동작하는지, 제네릭 정보가 어디에 살아 있는지:
  [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)

별도 문서가 없어 여기서 설명하는 개념은 셋이다.

**타입 계층 조합 탐색과 `(Optional, Object)` 등록의 의미.**\
`Converters.find`는 소스 타입과 대상 타입의 **전체 클래스 계층**을 각각 펼쳐 놓고 모든 조합을 순서대로 조회한다(`GenericConversionService.java:500-514`).\
`OptionalToObjectConverter`가 `(Optional.class, Object.class)` 한 쌍만 선언해도(`OptionalToObjectConverter.java:48-50`) 모든 대상 타입에 대해 후보로 오르는 것은 이 때문이다 — 어떤 대상 타입이든 계층의 마지막에 `Object`가 있다(`:564-565`).\
바꿔 말하면 이 컨버터는 **`Optional`이 소스인 모든 변환 질의의 마지막 관문**이고, `matches()`가 그 관문의 유일한 문지기다.\
문지기가 항상 통과시키면 관문이 없는 것과 같다.

**`matches()`와 `canConvert`의 계약 관계.**\
`ConversionService.canConvert`의 javadoc은 "이 메서드가 true면 `convert`가 변환할 수 **있다**"고 못박는다(`ConversionService.java:33-34`, `:51-52`).\
예외를 하나 명시하는데, 컬렉션·배열·맵의 **원소** 변환 실패는 true를 돌려준 뒤에도 날 수 있다는 것이다(`:35-39`, `:53-57`).\
`Optional`은 그 예외 목록에 없다.\
즉 이 결함은 "javadoc이 허용한 근사"가 아니라 계약 위반이다.

**선언에서 온 카드와 값에서 온 카드.**\
`TypeDescriptor`를 만드는 통로는 두 종류다.\
하나는 필드·메서드 파라미터·`ResolvableType`처럼 **선언**에서 만드는 것(`TypeDescriptor.java:99`, `:111`, `:128`)이고, 다른 하나는 `TypeDescriptor.forObject(값)`처럼 **실제 객체의 런타임 클래스**에서 만드는 것이다.\
전자는 제네릭이 살아 있고 후자는 지워져 있다.\
`OptionalToObjectConverter.convert`가 내부 위임에서 `forObject(unwrappedSource)`를 쓰는 것(`OptionalToObjectConverter.java:64`)과 `matches()`가 선언 카드를 받는 것이 바로 이 두 세계의 만남이고, 두 세계가 서로 다른 답을 내는 것이 이 PR이 정렬하려는 어긋남이다.
