# PR #36913 분석 — OptionalToObjectConverter.matches()의 canConvert 과대보고

> 기준: 머지 커밋 `af466ccf63b` (2026-08-20, 마일스톤 7.1.0-M2, 라벨 type: bug / in: core).
> 인용한 `OptionalToObjectConverter.java` 좌표는 머지 **후** 코드이며, 수정 전 코드는 diff의
> `-` 쪽을 병기한다.
> 근거: 실파일 정독 + `af466ccf63b` diff + `docs/plans/2026-08-14/pr36913-optional-wildcard-tests/`
> + 이 문서 작성 중 실행한 실측(아래 3절 각주).
> 같은 폴더의 README(서사)·structure(선택 파이프라인 구조)·tests(테스트별)·gates(이해 게이트)와
> 중복을 피해, 이 문서는 **이름표 사전·단계 추적 표(실측값)·계약 대조·기각된 대안**을 맡는다.

## 0. 결론

`OptionalToObjectConverter#matches()`는 원소 타입을 `TypeDescriptor#getElementTypeDescriptor()`로 꺼냈는데, 그 메서드는 javadoc상 **배열·Stream·Collection 전용**이라 `Optional`에 대해서는 언제나 `null`을 돌려준다.\
`ConversionUtils#canConvertElements`가 null 원소 타입을 "maybe"로 보아 무조건 true를 내므로, 이 `matches()`는 판별기가 아니라 **상수 함수**였고 `canConvert(Optional<Integer>, LocalDate)`가 true를 보고한 뒤 `convert`는 실패했다.\
수정은 원소 타입을 `sourceType.getResolvableType().getGeneric()`로 직접 꺼내 대상과 대조하되, 해석되지 않으면(raw·와일드카드·미해석 타입변수) 관대하게 true를 유지하는 것이다.\
PR은 머지됐다(7.1.0-M2).

> **상수 함수** — 입력이 무엇이든 늘 같은 값을 돌려주는 함수. 판별을 맡긴 자리에 상수 함수가 앉으면 판별이 사라진 것과 같다.\
> 예: 수정 전 `matches()`는 어떤 타입쌍을 줘도 true였다.

## 1. 무대

결함은 패키지 프라이빗 컨버터 하나의 자기 판별 메서드에 있었지만, 그 컨버터가 `Optional`을 소스로 하는 모든 변환 질의의 마지막 관문이라 영향은 좁지 않다.\
아래 항목은 모듈에서 호출 맥락까지 그 자리를 짚어 간다.

> **package-private** — 접근 제어자를 붙이지 않아 같은 패키지 안에서만 보이는 가시성. 바깥에서는 이름으로 부를 수 없다.\
> 예: `OptionalToObjectConverter`는 package-private이라 `ConversionService` 진입점을 통해서만 닿는다.

- 모듈: `spring-core`, 패키지 `org.springframework.core.convert.support`.
- 파일: `spring-core/src/main/java/org/springframework/core/convert/support/OptionalToObjectConverter.java`
  (`final class`, **package-private**, :38). `@since 7.0`, 저자 Sam Brannen.
- 결함 지점: `matches(TypeDescriptor, TypeDescriptor)` (:53-63).
- 공개 진입 API: 컨버터 자체는 package-private이라 직접 부를 수 없다. 진입은
  `ConversionService#canConvert(TypeDescriptor, TypeDescriptor)`
  (`ConversionService.java:65`)와 `convert(Object, TypeDescriptor, TypeDescriptor)`이며,
  구현은 `GenericConversionService` (:140 / :169)다.
- 등록: `DefaultConversionService.addDefaultConverters` (:104)가 `new OptionalToObjectConverter(cs)`를 등록한다.\
  선언 타입쌍은 `{(Optional.class, Object.class)}` 하나뿐인데(:49-51), `Converters.find`(:500)가 대상 타입의 **전체 클래스 계층**을 펼쳐 조합 탐색하고 모든 계층의 끝에 `Object`가 있으므로, 결과적으로 이 컨버터는 **`Optional`이 소스인 모든 변환 질의의 마지막 관문**이 된다.\
  `matches()`가 그 관문의 유일한 문지기다.
- 누가 어떤 상황에서 부르나: `canConvert`는 프레임워크 곳곳에서 "변환을 시도할지, 다른 경로로 갈지"를 가르는 분기 조건이다 — `TypeConverterDelegate.java:126`(빈 프로퍼티 바인딩 1차 시도), `ObjectToStringHttpMessageConverter.java:94/:99`(HTTP 메시지 read/write 가능 여부), `GenericMessageConverter.java:64`, `ServletModelAttributeMethodProcessor.java:139` 등.\
  즉 잘못된 true는 단순 오답이 아니라 잘못된 경로 선택을 부른다.

## 2. 전체 메서드 그래프

아래 그래프는 같은 타입쌍에 대한 두 경로, 곧 `canConvert` 질의와 `convert` 실행이 어디까지 같은 코드를 쓰다가 어디서 갈라지는지를 나란히 그린 것이다.\
오른쪽 숫자는 각 파일의 줄 번호다.

```text
[질의 경로]
cs.canConvert(TypeDescriptor(Optional<Integer>), TypeDescriptor(LocalDate))
   |
   v
GenericConversionService.canConvert(source, target)      GenericConversionService.java:140
   |  return (sourceType == null || getConverter(sourceType, targetType) != null)   :142
   v
getConverter(source, target)                                                  :224
   +-- converterCache 조회 (미스면 계속, NO_MATCH면 null)                     :79, :226-229
   +-- converters.find(sourceType, targetType)                                :231 -> :500
   |     +-- getClassHierarchy(Optional) x getClassHierarchy(LocalDate) 이중 루프  :504-512
   |     +-- (Optional, Object) 조합에서 등록 발견                             :507 -> :516
   |     v
   |   ConvertersForPair.getConverter(source, target)                         :620
   |     +-- Deque 순회: ConditionalGenericConverter면 matches() 질의          :621-627
   |           v
   |     OptionalToObjectConverter.matches(source, target)   OptionalToObjectConverter.java:54
   |           |
   |           |  [수정 전]
   |           +-- sourceType.getElementTypeDescriptor()      TypeDescriptor.java:370
   |           |     +-- isArray()? NO / Stream? NO
   |           |     +-- asCollection().getGeneric(0) -> NONE                  :378
   |           |     +-- getRelatedIfResolvable(NONE) -> null                  :477-481
   |           |
   |           |  [수정 후]
   |           +-- sourceType.getResolvableType().getGeneric()  TypeDescriptor.java:161, ResolvableType.java:754
   |           +-- elementType.resolve() == null ? -> return true              :56-60
   |           |     (raw / 와일드카드 / 미해석 타입변수)
   |           +-- new TypeDescriptor(elementType, null, null)  TypeDescriptor.java:128
   |           v
   |     ConversionUtils.canConvertElements(sourceElementType, targetType, cs)  ConversionUtils.java:51
   |           +-- targetElementType == null -> true   ("yes")                 :54-57
   |           +-- sourceElementType == null -> true   ("maybe")               :58-61   <-- 수정 전 상시 경로
   |           +-- cs.canConvert(src, tgt) -> true     ("yes")                 :62-65
   |           +-- ClassUtils.isAssignable(src, tgt) -> true ("maybe")         :66-69
   |           +-- return false                        ("no")                  :71
   |
   +-- 결과를 converterCache에 저장(null이면 NO_MATCH)                          :236-241

[실행 경로 — 질의와 같은 getConverter를 쓰고, 컨버터를 실제로 호출하는 지점부터 갈린다]
cs.convert(Optional.of(42), Optional<Integer>카드, LocalDate카드)              :169
   +-- converter = getConverter(...)                                           :179
   +-- converter != null ?
   |     +-- YES -> ConversionUtils.invokeConverter(...)                       :181 -> :37
   |     |      v
   |     |   OptionalToObjectConverter.convert(...)      OptionalToObjectConverter.java:66
   |     |      +-- source == null -> null                                     :67-69
   |     |      +-- unwrappedSource = optional.orElse(null)  -> Integer 42     :71
   |     |      +-- unwrappedSourceType = TypeDescriptor.forObject(42)         :72   <-- 값에서 만든 카드
   |     |      +-- cs.convert(42, Integer카드, LocalDate카드)  (재귀)          :73
   |     |             -> 컨버터 없음 -> handleConverterNotFound               :278
   |     |             -> throw ConverterNotFoundException                     :289
   |     |      +-- invokeConverter의 catch(Throwable)가 감싼다                 :46-48
   |     |             -> ConversionFailedException
   |     +-- NO  -> handleConverterNotFound(...)                               :184 -> :289
   |                  -> ConverterNotFoundException(Optional<Integer>, LocalDate)
```

데이터 흐름의 어긋남이 그래프에 그대로 보인다.\
**질의는 선언 카드**(`Optional<Integer>`)를 보고 답하는데 **실행은 벗겨낸 값**(`42`)으로 다시 질의한다.\
두 질문이 같은 근거를 쓰지 않으면 답이 갈릴 수 있고, 수정 전에는 `matches()`가 선언 카드를 아예 읽지 않아 갈림이 상시화됐다.

## 2.5 핵심 이름표 사전

이 흐름에서 헷갈리는 것은 `TypeDescriptor`가 두 출신으로 존재한다는 점이다 — **선언에서 온 카드**(필드·파라미터·`ResolvableType`, 제네릭이 살아 있다)와 **값에서 온 카드**(`forObject`, 제네릭이 지워져 있다).\
아래 각 항목은 어느 쪽인지를 밝힌다.

> **타입 소거(type erasure)** — 자바 제네릭은 컴파일 후 실행 객체에 인자가 남지 않는다. 값에서 만든 카드에 제네릭이 없는 것은 이 때문이다.\
> 예: `Optional.of(42)` 인스턴스만 보고는 그것이 `Optional<Integer>` 선언이었는지 알 수 없다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `matches(TypeDescriptor, TypeDescriptor)` :54 | "이 변환쌍에 내가 선택되어야 하는가" 자기 판별 | (소스 카드, 대상 카드) -> boolean | `ConvertersForPair.getConverter` :624 | 결함이 살던 메서드. 이 답이 `canConvert` 최종 결과를 그대로 결정한다 |
| `sourceType` (파라미터) | 소스 **선언** 카드 | — | 질의·실행 양쪽에서 전달 | `Optional<X>`의 X가 여기 살아 있는데 수정 전에는 읽지 않았다 |
| `targetType` (파라미터) | 대상 선언 카드 | — | 동일 | 판별의 상대편. `LocalDate`처럼 변환기 없는 타입이 결함을 드러낸다 |
| `getElementTypeDescriptor()` `TypeDescriptor.java:370` | 배열 컴포넌트 / Stream 원소 / Collection 원소 타입 | — -> TypeDescriptor 또는 null | 수정 전 `matches` :55 | **결함의 실체** — javadoc(:361-369)이 Optional을 대상으로 명시하지 않으며, 실측상 `Optional<Integer>`에도 null을 준다 |
| `getRelatedIfResolvable(ResolvableType)` :477 | 해석 안 되면 null, 되면 카드 생성 | ResolvableType -> TypeDescriptor 또는 null | `getElementTypeDescriptor` :378 | `asCollection()`이 NONE을 주므로 항상 null로 귀결 |
| `getResolvableType()` :161 | 카드가 감싼 `ResolvableType` 원본 | — -> ResolvableType | 수정 후 `matches` :55 | 제네릭에 접근하는 **올바른 통로** |
| `getGeneric(int...)` `ResolvableType.java:754` | 제네릭 인자 하나를 꺼낸다 | 인덱스(생략 시 0) -> ResolvableType | 수정 후 `matches` :55 | `Optional<Integer>` -> `Integer` |
| `elementType` (지역, :55) | 꺼낸 원소 타입 | — | 수정이 도입 | 수정의 중심 변수 |
| `resolve()` `ResolvableType.java:882` | 실제 Class로 해석, 못 하면 null | — -> Class 또는 null | :56의 가드 | "원소 타입을 아는가"의 판정 |
| `resolveType()` :919 | 한 단계 해석 (ParameterizedType/Wildcard/TypeVariable 분기) | — -> ResolvableType | `resolveClass` :912 | 와일드카드·타입변수가 여기서 상한으로 접힌다 |
| `resolveBounds(Type[])` :1467-1472 | 상한 배열에서 의미 있는 상한 고르기 | Type[] -> Type 또는 null | `resolveType` :925/:940 | **관대/엄격의 갈림.** `bounds[0] == Object.class`면 null -> "정보 없음" |
| `sourceElementType` (지역, :61) | 원소 타입을 카드로 다시 포장한 것 | ResolvableType -> TypeDescriptor | 수정 후 `matches` :61 | `new TypeDescriptor(rt, null, null)` (:128) — 선언 카드 계열 |
| `canConvertElements(...)` `ConversionUtils.java:51` | yes / maybe / no 3등급 근사 판정기 | (소스원소, 대상, cs) -> boolean | `matches` :62 | 결함이 아니다. **확정적 부정만 신뢰 가능**한 근사기이고, 정확한 원소 타입을 주는 것이 호출자 책임 |
| `conversionService` :40 | 재귀 질의용 서비스 참조 | — | `matches` :62, `convert` :73 | 등록 시 `DefaultConversionService` 자신이 주입됨(:104) |
| `getConvertibleTypes()` :49 | 선언 타입쌍 `{(Optional, Object)}` | — -> Set | `Converters.add` :470 | 이 컨버터가 모든 대상 타입의 후보가 되는 이유 |
| `convert(...)` :66 | Optional을 벗겨 위임 | (값, 소스카드, 대상카드) -> Object | `invokeConverter` :41 | `forObject(unwrapped)` (:72)로 **값 카드**를 만들어 재질의 — 질의와 근거가 다른 지점 |
| `TypeDescriptor.forObject(Object)` :561 | 런타임 클래스에서 카드 생성 | 값 -> TypeDescriptor | `convert` :72, `TypeConverterDelegate:125` | 제네릭이 지워져 있다. 실사용 소비처 대부분이 이 카드를 소스로 쓰므로 **결함의 실노출이 제한적**이었다 |
| `converterCache` / `NO_MATCH` :79 / :74 | 판정 결과 캐시와 음성 마커 | — | `getConverter` :226/:238 | 수정 후 false 판정이 `NO_MATCH`로 캐시되어 실행 경로도 함께 정합해진다 |
| `handleConverterNotFound` :278 | 컨버터 부재 시 최종 처리 | — | `convert` :184 | 수정 후 예외가 **여기서** 나온다(:289) |
| `invokeConverter` :37 | 컨버터 호출 + 예외 래핑 | — | `convert` :181 | `catch (Throwable)` (:46)이 `ConverterNotFoundException`을 `ConversionFailedException`으로 감싼다 |
| `ObjectToOptionalConverter.matches` (:61-68) + `GenericTypeDescriptor` (:93-98) | 반대 방향의 **이미 올바른** 구현 | — | 대상이 Optional일 때 | 수정의 참조 모델. 커밋 메시지의 "mirroring ObjectToOptionalConverter" |

## 3. 결함 경로 단계 추적

아래 값은 추정이 아니라 현재 main(수정 후) 바이너리로 **실행해 얻은 것**이다.\
수정 전 경로는 raw `Optional`을 소스로 쓰면 그대로 재현된다 — raw는 수정 후에도 관대 갈래로 빠져 `matches()`가 true를 돌려주므로, 그때의 실행 결과가 곧 수정 전 `Optional<Integer>`의 결과와 같은 경로다.

| 단계 | 정상: `Optional<Integer>` -> `String` | 결함: `Optional<Integer>` -> `LocalDate` | 관대 유지: `Optional<?>` -> `LocalDate` |
|---|---|---|---|
| 소스 카드 출신 | 선언(`forClassWithGenerics`) | 선언 | 선언(필드 `Optional<?>`) |
| 수정 전 `getElementTypeDescriptor()` | **null** (실측) | **null** (실측) | **null** |
| 수정 전 `canConvertElements` 진입 갈래 | `sourceElementType == null` -> "maybe" | 동일 | 동일 |
| 수정 전 `matches()` | true | **true (과대보고)** | true |
| 수정 전 `canConvert` | true (우연히 정답) | **true (오답)** | true (정답) |
| 수정 전 `convert(Optional.of(42), ...)` | `"42"` | 컨버터 선택 -> 내부 위임 실패 -> **`ConversionFailedException`** (cause `ConverterNotFoundException`, 실측) | 동일하게 `ConversionFailedException` |
| 수정 후 `getGeneric().resolve()` | `Integer` (실측) | `Integer` (실측) | **null** (상한 `Object` -> `resolveBounds` null, 실측) |
| 수정 후 :56 가드 | 통과 안 함(해석됨) | 통과 안 함 | **true 조기 반환** |
| 수정 후 `canConvertElements` 진입 갈래 | `cs.canConvert(Integer, String)` -> true ("yes") | 셋 다 실패 -> **false** ("no") | (미도달) |
| 수정 후 `matches()` | true | **false** | true |
| 수정 후 `canConvert` | true (실측) | **false** (실측) | true (실측) |
| 수정 후 `convert(Optional.of(42), ...)` | `"42"` (실측) | 컨버터 미선택 -> **`ConverterNotFoundException`** (실측) | `ConversionFailedException` (경로 불변) |

세 번째 열을 추가로 두는 이유는 `Optional<? extends Number>`가 어느 갈래로 가는지를 대조하기 위해서다.\
실측상 `Optional<? extends Number>`의 `getGeneric().resolve()`는 **`Number`**이므로 가드를 통과하지 않고 실제 판별로 간다 — `-> String`은 true, `-> LocalDate`는 false.\
반면 `Optional<?>`는 상한이 `Object`라 `resolveBounds`가 null을 돌려주고(:1468-1470) 관대 갈래로 빠진다.\
**같은 와일드카드인데 갈림이 생기는 근거는 상한이 `Object`냐 아니냐 하나뿐이다.**

여기서 기존 tests.md·structure.md의 서술 하나를 실측으로 정정해 둔다.\
두 문서는 결함 케이스의 `convert()` 예외 타입이 수정 전후 같아서 예외 단언이 판별력을 갖지 못한다고 적었으나, 실제로는 **수정 전 `ConversionFailedException` / 수정 후 `ConverterNotFoundException`**으로 서로 다르다 (두 클래스는 형제이며 상속 관계가 아니다 — 각각 `ConversionException`을 직접 상속: `ConversionFailedException.java:31`, `ConverterNotFoundException.java:30`).\
따라서 테스트의 `assertThatExceptionOfType(ConverterNotFoundException.class)` 단언도 수정 전에는 red다.

## 4. 계약

이 무대에는 명시된 계약이 여덟 개 얽혀 있고, 그중 결함이 실제로 어긴 것은 셋뿐이다.\
다음 표는 계약별로 출처와 위반 여부를 대조한다.

| 계약 | 출처 | 결함이 어겼는가 |
|---|---|---|
| `canConvert`가 true면 `convert`가 변환할 수 **있다** | `ConversionService.java:33-34`, :51-52 ("If this method returns true, it means convert(...) is capable of converting") | **예 — 이 PR의 본체.** 계약 위반이다 |
| 예외 조항: **collection·array·map** 타입 간 변환은 원소 변환 실패가 true 뒤에도 날 수 있다 | 같은 javadoc의 "Special note on collections, arrays, and maps types" (:35-39, :53-57) | 아니오 — **`Optional`은 그 예외 목록에 없다.** 그래서 이 결함은 "javadoc이 허용한 근사"가 아니다 |
| `matches()`는 "이 변환쌍에 내가 선택되어야 하는가"에 답한다 | `ConditionalConverter.java:45-52` | 예 — 항상 true를 답해 판별 기능을 잃었다 |
| `getElementTypeDescriptor()`는 배열 컴포넌트 또는 Collection 원소를 주고, 아니면 null | `TypeDescriptor.java:361-369` javadoc | 아니오 — **javadoc대로 동작했다.** 결함은 호출자가 Optional에 이 메서드를 쓴 데 있다 |
| `canConvertElements`는 yes/maybe/no 3등급 근사기이고 null 원소는 "maybe"로 통과시킨다 | `ConversionUtils.java:54-71`의 주석 | 아니오 — 전제. **확정적 부정만 신뢰 가능**하므로 정확한 원소 타입을 주는 것이 호출자 책임이다 |
| 원소 타입을 모르면 막지 않는다(관대) | 수정이 명시한 새 계약 (:56-60의 주석) | — 새로 문서화된 계약. 관대 가드 3건이 이것을 고정한다 |
| 형제 컨버터는 대상 Optional의 제네릭을 `getResolvableType().getGeneric()`로 읽는다 | `ObjectToOptionalConverter.java:62-63`, :93-98 | 예 — 소스 방향만 다른 통로를 쓰고 있었다. 수정은 두 방향을 같은 통로로 맞춘다 |
| 기존 테스트가 고정하던 것 | `DefaultConversionServiceTests$OptionalConversionTests`의 기존 12건은 전부 **변환이 성공하는** 방향(convertObjectToOptional 등) | 부정 방향 가드가 없어 과대보고가 오래 숨었다 |

## 5. 수정안

수정은 채택된 한 벌과 검토 끝에 기각된 대안들로 나뉜다.\
앞의 5.1은 실제로 머지된 코드와 그 배치 판단이고, 뒤의 5.2는 같은 결함을 다른 자리에서 고치려던 안들과 기각 사유다.

### 5.1 채택된 수정 (머지 커밋 `af466ccf63b`)

`OptionalToObjectConverter.java:53-63`:

```java
	@Override
	public boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType) {
		ResolvableType elementType = sourceType.getResolvableType().getGeneric();
		if (elementType.resolve() == null) {
			// Unknown Optional element type (raw Optional, wildcard, or unresolved
			// type variable): remain permissive.
			return true;
		}
		TypeDescriptor sourceElementType = new TypeDescriptor(elementType, null, null);
		return ConversionUtils.canConvertElements(sourceElementType, targetType, this.conversionService);
	}
```

수정 전은 한 줄이었다: `return ConversionUtils.canConvertElements(sourceType.getElementTypeDescriptor(), targetType, this.conversionService);`

**왜 이 위치인가.**\
결함은 세 곳 중 어디서도 고칠 수 있었다 — (1) `getElementTypeDescriptor()`가 Optional을 다루게 하거나, (2) `canConvertElements`가 null을 엄격하게 처리하게 하거나, (3) 호출자인 `matches()`가 올바른 원소 타입을 넘기게 하거나.\
채택된 것은 (3)이며, 이유는 blast radius다.\
(1)과 (2)는 컬렉션·배열·Stream 컨버터 전체가 공유하는 공용 코드라 한 컨버터의 버그를 고치려고 공용 계약을 흔들게 된다.\
(3)은 **한 컨버터 안에 갇힌 변경**이고, 마침 반대 방향 형제(`ObjectToOptionalConverter`)가 이미 같은 통로를 쓰고 있어 대칭도 회복된다.

> **blast radius** — 한 변경이 영향을 미치는 범위. 같은 결함이라도 어디서 고치느냐에 따라 흔들리는 코드의 폭이 달라진다.\
> 예: `canConvertElements`를 고치면 컬렉션·배열·Stream 컨버터 전체가 영향권에 들어간다.

**가드(`resolve() == null -> true`)는 동작 중립이다.**\
리뷰에서 확인된 사실이며, 가드가 없어도 미상 원소는 `Object`로 떨어지고 `canConvertElements`의 assignable 폴백(:66-69, `Object`는 무엇이든 담을 수 있다 -> "maybe")이 어차피 true를 낸다.\
가드의 가치는 동작 변경이 아니라 **의도의 문서화와 불필요한 `TypeDescriptor` 생성 회피**다.

### 5.2 검토됐다가 기각된 대안

같은 결함을 고칠 자리는 여럿이었고, 다섯 대안이 각각 다른 이유로 빠졌다.\
아래는 대안과 기각 사유를 하나씩 정리한 것이다.

- **`TypeDescriptor#getElementTypeDescriptor()`가 `Optional`도 다루게 확장.** 가장 "근본적"으로 보이는 수정이다.\
  기각 이유는 계약 표면이다.\
  이 메서드의 javadoc(:361-369)이 배열·Collection을 명시하고 있고, 반환값을 쓰는 컬렉션 계열 컨버터·`TypeDescriptor.elementTypeDescriptor(Object)` 등이 "이 카드가 배열/컬렉션이다"라는 전제를 깔고 있다.\
  `Optional`을 원소 컨테이너로 승격시키면 그 전제가 조용히 바뀐다 — 한 컨버터의 버그를 고치는 대가로는 너무 크다.
- **`canConvertElements`가 null 원소를 false로 처리(엄격화).** 기각 이유는 과잉 필터링이다.\
  이 함수는 컬렉션·맵 컨버터가 공유하며, 원소 제네릭이 지워진 raw 컬렉션에서도 정당한 변환을 허용해야 한다.\
  "모르면 막지 않는다"는 3등급 설계 자체가 의도된 것이고, 주석의 yes/maybe/no 표기가 그 의도를 남기고 있다.
- **`matches()`에서 미상 원소를 false로 처리(컨버터 단위 엄격화).** 즉 가드를 뒤집는 안.\
  기각 이유는 실측 소비 형태다.\
  `TypeConverterDelegate.java:125` 등 대부분의 소비처는 `TypeDescriptor.forObject(값)`로 소스 카드를 만드는데, 실제 값이 `Optional` 인스턴스면 제네릭이 지워져 raw 카드가 된다.\
  미상을 false로 막으면 **지금 정상 동작하는 실사용 경로가 대량으로 끊긴다.**\
  관대 3형제 테스트(raw / `Optional<?>` / `Optional<T>`)가 이 기각을 실행으로 고정한다.
- **`ObjectToOptionalConverter`처럼 `hasGenerics()`로 분기.** 형제 구현은 `targetType.getResolvableType().hasGenerics()`로 판정한다(:62).\
  이 안을 그대로 쓰지 않은 이유는 `hasGenerics()`가 "제네릭 선언이 있는가"만 보아 `Optional<?>`·`Optional<T>`에서 true를 주기 때문이다 — 그러면 상한이 `Object`인 미상 원소를 `Object` 카드로 판별하게 되어 가드의 의도(관대)가 코드에 드러나지 않는다.\
  `resolve() == null`은 "실제로 아는가"를 직접 묻는다.
- **형제의 `GenericTypeDescriptor` 내부 클래스(:93-98)를 소스 방향에도 재사용.** 그쪽은 `typeDescriptor.getAnnotations()`를 원소 카드에 물려주는데, 소스 방향에서는 대상 판별에 애노테이션이 관여하지 않으므로 `new TypeDescriptor(elementType, null, null)` 한 줄이면 충분하다.\
  (이 항목은 문서화된 기각 기록이 아니라 두 구현의 차이에서 유도한 서술이다.)

## 6. 범위 밖과 인접 영향

이 수정이 건드리지 않은 인접 영역을 정리하면, 실노출이 제한적이었던 구조적 이유와 바뀌는 예외 타입 하나가 드러난다.\
아래 항목은 같은 패턴의 다른 위치, 하위호환, 캐시, 범위 밖 순이다.

- **같은 패턴의 다른 위치 — 반대 방향 컨버터.** `ObjectToOptionalConverter.matches`(:61-68)는 이미 `getResolvableType().getGeneric()`을 쓰고 있어 같은 결함이 없다.\
  이 PR은 두 방향의 비대칭을 없앤 셈이다.
- **같은 패턴의 다른 위치 — 컬렉션 계열.** `getElementTypeDescriptor()`를 쓰는 배열·Collection·Stream 컨버터들은 **정당한 사용자**다.\
  그쪽은 `canConvert`의 javadoc 예외 조항(:35-39)이 명시적으로 커버하므로, 원소 변환 실패가 true 뒤에 나도 계약 위반이 아니다.\
  Optional만 그 조항 밖에 있었다는 것이 이 PR의 논거였다.
- **하위호환 — 바뀌는 집합.** "원소 타입이 해석되는 `Optional<X>` 선언 카드를 소스로 하고, `X -> 대상` 변환기가 없는" 질의뿐이다.\
  그 질의는 이제 `canConvert`가 false를 돌려주고, `convert`는 `ConversionFailedException` 대신 `ConverterNotFoundException`을 던진다.\
  **예외 타입이 바뀐다는 점은 명시할 가치가 있다** — 두 예외는 형제라 `catch`가 좁게 잡혀 있으면 영향을 받는다.\
  다만 어느 쪽이든 변환은 원래 실패했으므로 성공 경로의 회귀는 없다.
- **하위호환 — 실노출이 제한적인 구조적 이유.** 실사용 소비처 대부분이 `TypeDescriptor.forObject(값)`로 소스 카드를 만들고, `Optional` 인스턴스에서 만든 카드는 제네릭이 지워진 raw다.\
  그런 카드는 수정 후에도 관대 갈래로 빠져 결과가 같다.\
  결함이 실제로 드러나는 것은 필드·메서드 파라미터 같은 **선언에서 온 카드**가 소스인 경우다.\
  PR 본문의 "Impact is bounded"가 이 구조를 가리킨다.
- **캐시와의 상호작용.** 수정 후 false 판정은 `converterCache`에 `NO_MATCH`(:74)로 저장되므로(:236-241), 같은 타입쌍의 후속 질의·실행이 일관되게 컨버터 미선택 경로를 탄다.\
  질의와 실행이 같은 `getConverter`를 공유한다는 점이 이 수정으로 "질의 = 실행" 일관성을 얻는 메커니즘이다.
- **다루지 않은 것.** `convert()`가 `forObject(unwrappedSource)`(:72)로 값 카드를 만들어 재질의하는 구조 자체는 그대로다 — 즉 `Optional<Number>` 선언에 실제로 `Integer`가 담긴 경우처럼 선언과 값이 갈리는 상황의 근사는 남아 있다.\
  `Converters.find`의 계층 조합 탐색, `ConvertersForPair`의 2패스 폴백(:628-635), `addFirst` 등록 순서(:616-618)도 범위 밖이다.
