# PR #37153 — Include enum array attributes in TypeNotPresentException probing

## 0. 정향

이 문서는 `spring-core` annotation 처리의 `AttributeMethods` 수정 PR을 처음부터
이해하기 위한 해설이다. "annotation이 참조하는 enum 상수가 런타임에 없을 수 있다"는
전제가 낯설다면 [enum 상수의 이름 저장과 지연 해석](enum-annotation-name-resolution.md)과
[classpath 버전 스큐](classpath-version-skew.md)를 먼저 읽는 것이 좋다. 다 읽으면
"왜 단일 enum 속성과 enum 배열 속성이 같은 오염에 다르게 반응했는가"와 "1줄 fix가
어떤 경로로 그 비대칭을 없애는가"를 설명할 수 있어야 한다.

같은 폴더의 심화 문서: [probe 패턴](probe-pattern.md) ·
[테스트 해설](tests.md) · [리뷰 과정](review.md)

## 1. 배경 — AttributeMethods는 왜 존재하나

Spring의 annotation 처리(`MergedAnnotations`, `AnnotatedElementUtils` 등)는
클래스에 붙은 annotation을 대량으로 훑는다. 그런데 JDK의 annotation 값 해석은
지연(lazy)이다: `Class` 속성이 가리키는 타입이 classpath에 없거나, enum 속성이
가리키는 상수가 로드된 enum에 없으면, annotation 객체 생성 시점이 아니라 **속성을
읽는 순간에** `TypeNotPresentException`/`EnumConstantNotPresentException`이 터진다.

`AttributeMethods`는 이 시한폭탄에 대한 방어 장치다. annotation 타입별로 속성
메서드를 정리하면서, "늦게 터질 수 있는 타입"(`Class`, `Class[]`, enum)의 속성에
`canThrowTypeNotPresentException` 플래그를 세운다. 스캔 경로
(`AnnotationsScanner.getDeclaredAnnotations`)는 `canLoad()`로 플래그 선 속성을
**미리 한 번 실호출(probe)** 해 보고, 예외가 나면 그 annotation을 스캔 결과에서
통째로 제외한다(warn 로그). 원조 동기는 javadoc에 남아 있는 Google App Engine의
지연 `Class` 실패였다.

## 2. 수정 전 동작 — enum만 배열이 빠진 비대칭

플래그 계산식은 이랬다:

```java
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class || type.isEnum());
```

`Class`는 스칼라·배열을 모두 다루는데 enum은 `type.isEnum()`(스칼라)뿐이다.
공교롭게도 바로 윗줄의 nested annotation 검사는
`type.isAnnotation() || (type.isArray() && type.componentType().isAnnotation())`로
배열까지 다루고 있어, 같은 생성자 안에서도 enum만 배열이 빠진 비대칭이었다.

결과: enum **배열** 속성은 probe 대상이 아니므로, 오염된 annotation(런타임 enum에
없는 상수를 참조)이 `canLoad()`를 — 검사 없이 — 통과한다.

## 3. 무엇이 문제였나 — 세 갈래 누출 (실측)

v1 enum(BLUE 있음)으로 컴파일한 annotation을 v2 enum(BLUE 제거)으로 실행하는
재현에서, 단일 enum 속성과 enum 배열 속성이 이렇게 갈렸다:

| | 단일 enum 속성 | enum 배열 속성 (수정 전) |
|---|---|---|
| `isPresent()` | false + warn 로그 (필터링, 설계 의도) | **true** — 오염된 annotation이 정상 행세 |
| `asMap()` | 빈 맵 (missing) | **`{value=EnumConstantNotPresentException 객체}`** — 예외 객체가 값으로 들어간 맵 |
| `getEnumArray`/`synthesize().value()` | `NoSuchElementException` (missing 계약) | **raw `EnumConstantNotPresentException`** 누출 |

특히 `asMap()` 행이 가장 나쁘다. 예외가 나는 것이 아니라 **오염된 값이 조용히
하류로 흘러가는** silent corruption이라, `AnnotationAttributes` 기반 소비자
(빈 이름 결정, `@Qualifier` 매칭 등)는 엉뚱한 곳에서 `ClassCastException`으로
죽는다. JDK 자체는 단일/배열을 똑같이 취급하므로(둘 다 읽는 순간 예외), 이
비대칭은 Spring이 만든 것이었다.

## 4. 수정 해설 — 1줄, 그리고 왜 그 1줄이면 충분한가

수정은 판정식에 배열 가지 하나를 더하는 것이 전부다.

```java
this.canThrowTypeNotPresentException[i] = (type == Class.class || type == Class[].class ||
		type.isEnum() || (type.isArray() && type.componentType().isEnum()));
```

바로 윗줄 nested annotation 관용구를 그대로 재사용했다. 이 플래그의 소비처는
`canLoad()`/`validate()`(같은 클래스)와 `AnnotationsScanner`(canLoad 호출) 셋뿐이고,
셋 모두 "플래그가 서 있으면 probe한다"는 게이트로만 쓰므로, 변경 효과는 "probe
대상 확대" 하나로 국한된다. annotation 멤버는 다차원 배열이 문법상 불가능하므로
`componentType()` 1단계 검사로 완결이다.

수정 후 enum 배열도 단일 enum과 동일하게: 스캔 단계에서 probe -> 예외 관측 ->
warn 로그 + 필터링 -> `isPresent()==false`, `asMap()=={}`, typed 접근은
missing-annotation 계약(`NoSuchElementException`)으로 정리된다.

비용: probe 플래그 계산은 annotation 타입당 1회. 실호출 비용은 기존 `Class[]`
probe와 같은 종류이며 enum 배열 속성에만 추가된다(스캐너의
`declaredAnnotationCache`가 반복 빈도를 제한하지만, 비용을 없애는 것은 아니다 —
캐시 미스마다 발생).

## 5. 검증

검증은 단위 테스트, 패키지 전체 스위트, 실물 재현 세 층으로 쌓았다.

- test-first: 테스트 5건을 먼저 넣어 3건 red(플래그·canLoad 실패·validate 실패)
  확인 -> fix 1줄로 21/21 green. 상세는 [tests.md](tests.md).
- annotation 패키지 전체 스위트 733 tests, 0 failures.
- 실물 스모크: v1/v2 enum 2단 컴파일 데모로 수정 전 3갈래 누출과 수정 후 필터링을
  모두 실측(§3 표).

## 6. 교훈

이 한 줄짜리 수정이 남긴 것은 결함을 찾는 법, 정상 판정의 기준, 그리고 fix의 성격 셋이다.

1. **대칭 결함은 같은 식 안에서 찾아라.** "단일 X는 다루는데 X[]가 빠졌다"는
   패턴은 바로 윗줄(nested annotation)이 정답 관용구를 이미 들고 있었다. 리뷰에서도
   같은 질문이 나왔다: 이 식에 아직 빠진 계열은 없나? (nested annotation 자체의
   probe 누락 가능성 — 후속 조사로 분리, [review.md](review.md) 참조.)
2. **"에러 없이 돈다" ≠ 정상.** 수정 전 `asMap()`은 예외 없이 오염된 맵을
   돌려줬다. 예외보다 silent corruption이 더 나쁘다.
3. **필터링의 의미론.** Spring은 로드 불가 annotation을 "없는 것"으로 취급하기로
   설계했다. fix는 새 동작을 만든 게 아니라 기존 의미론을 배열까지 확장한 것이다.
