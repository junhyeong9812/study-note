# PR #36913 — 이해 게이트 기록

> 출처: 세션 07fec95c (2026-08-14~17), 작업 폴더 `docs/plans/2026-08-14/pr36913-optional-wildcard-tests/`.
> 답변은 원문 그대로(오타 포함), 판정·정답은 대화에 기록된 것만 옮긴다.
> lazy 모드 규칙: 게이트마다 최대 2회 시도, 2회차도 fail이면 워커가 틀린 부분을 지적하고 통과 처리한다.

## 게이트 목록

이 작업에서는 게이트가 두 번 열렸고 둘 다 2회차 fail로 통과 처리됐다. 다음 표는 게이트별
대상과 시도 횟수, 최종 판정이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|------|------|------|-----------|
| G1 | diff A — 와일드카드 테스트 2건 추가 | 2 | 2회차 fail, 규칙에 따라 통과 처리 |
| G2 | diff B — 리뷰 반영 수정 (테스트 14건에서 17건) | 2 | 2회차 fail, 규칙에 따라 통과 처리 |

계획 게이트는 없다. 이 작업은 sbrannen 리뷰 요청(와일드카드 케이스 테스트 추가) 대응이라 인터뷰와 spec 합의 직후 바로 diff A 적용으로 들어갔고, log에도 계획 게이트 행이 없다. 대신 착수 직후 `ResolvableType.resolveBounds`의 실동작을 소스로 확인하는 가정 실증을 먼저 했다.

## G1 — diff A: 와일드카드 테스트 2건 추가

Claude가 먼저 설명한 내용:

- `Optional<?>` -> `LocalDate`: true 기대. 원소 타입을 알 수 없으니(비한정 와일드카드의 상한 Object는 `resolveBounds`가 null 처리) 관대 유지.
- `Optional<? extends Number>` -> `String`: true / -> `LocalDate`: false 기대. 상한 `Number`가 원소 타입으로 resolve되어 "Number를 LocalDate로 바꿀 수 있나"로 판별. `convert()`도 `ConverterNotFoundException`으로 일관성 확인.
- 와일드카드 타입은 코드로 직접 만들 수 없어 테스트 픽스처 필드(`private Optional<?> wildcardOptional;`)를 선언하고 `getDeclaredField`로 `TypeDescriptor`를 얻는다.

**질문** (원문)

> 같은 와일드카드인데 왜 `Optional<?>`는 관대(true)이고 `Optional<? extends Number>`는 false가 될 수 있을까요? — 두 경우에 `resolveBounds`(상한 배열을 받아 타입을 돌려주는 함수)가 각각 무엇을 반환하는지로 설명해 주세요.

**시도 1 — 답변**

> Number는 숫자 객체에 한정되도록 결국 비교 범위를 좁힌거고, 그렇기 떄문에 LocalDate는 결국 String타입에 인터페이스가 걸려있는 추상 객체이기에 Number는 false인게 맞다는거지 이걸 말하고 싶은거구나.

**판정 1** — fail (1/2). 부족점:

- `Optional<?>` 쪽이 빠졌다. 비한정 와일드카드의 상한이 무엇이고 `resolveBounds`가 그때 무엇을 반환하는지, 그 반환값 때문에 `matches()`가 왜 관대(true)로 가는지를 짚어야 두 경우의 대비가 성립한다.
- `LocalDate`가 false인 이유 설명이 틀렸다. LocalDate는 String과 인터페이스 관계도 아니고 추상 객체라서도 아니다. Number를 기준으로 무엇을 판정하는지 다시 확인해야 한다.

**시도 2 — 답변**

> 우선 1. ?는 상한이 Object라서 그런거고, 결국 자바는 모든 Object를 상속하기에 true인거 아니야? 하지만 Number로 잡으면 LocalDate가 들어오면 순수 숫자로 이뤄진 int,float,Double과 같은 객체인지 확인하기 때문 아니야? 결국 들어오는 객체가 Number라는 객체를상속하는지 확인하기 때문인거 아니야?

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리**

인정된 부분: `Optional<?>`의 상한이 `Object`라는 것은 정확하다. 갈림의 출발점을 제대로 짚었다.

1. `Optional<?>`가 true인 메커니즘은 "모든 객체가 Object를 상속하니 통과"가 아니다. `resolveBounds`는 상한이 `Object.class`이면 그것을 "유의미한 정보가 없다"로 취급해 null을 반환한다.

```java
if (bounds.length == 0 || bounds[0] == Object.class) {
    return null;
}
```

원소 타입이 null, 즉 미상이므로 `matches()`는 판별할 근거가 없다고 보고 판별을 포기하고 관대하게 true를 돌려준다. 상속 관계를 확인해서 통과시키는 게 아니라 아예 확인하지 않고 통과시키는 것이다. 그래서 대상이 `LocalDate`처럼 실제로는 변환 불가능한 타입이어도 `Optional<?>`는 true가 된다.

2. `Optional<? extends Number>`가 false가 되는 메커니즘은 "들어오는 객체가 Number를 상속하는지" 확인하는 게 아니다. 상한이 `Object`가 아니므로 `resolveBounds`가 `Number`를 반환하고, 이 `Number`가 실제 판별 기준(원소 타입)이 된다. 그 다음 판정은 상속 검사가 아니라 `Number`에서 대상 타입으로 가는 변환기가 ConversionService에 등록돼 있는지(`canConvert`)다.

- 대상이 `String`: `Number -> String` 변환기가 있으므로 true
- 대상이 `LocalDate`: `Number -> LocalDate` 변환기가 등록돼 있지 않으므로 false

`LocalDate`가 추상 객체라서도, `String`과 인터페이스 관계라서도 아니다. 순전히 그 변환 경로가 등록돼 있느냐의 문제다. 정리하면 갈림의 근거는 상한이 Object냐 아니냐다.

**게이트 종료 후 후속 되묻기** (같은 주제라 함께 남긴다)

> 아 결국 ?인 경우 resolveBounds는 상한이 Object라는게 들어오는 객체가 별도 객체를 상속받은 객체가 아닌 경우 Object인거잖아? (...) 결국 들어오는 객체의 타입을 ConversionService에 등록되어있는 지 확인하고 (...)

Claude의 답: 결론은 정확하지만 "들어오는 객체"가 아니라 "선언된 타입"이다. 이 판별은 전부 정적(선언 수준) 타입 분석이라 실제 객체는 아직 등장하지 않는다. `canConvert(TypeDescriptor, TypeDescriptor)`는 타입 설명서 두 장만 비교한다.

이어서 사용자가 "내가 바라보는 관점은 런타임 관점이고 실제 컴파일 테스트 관점에서는 저게 아니라는거야?"라고 묻자 Claude가 3층으로 정리했다.

1. 컴파일 타임 — javac가 `Optional<? extends Number>` 변수에 `Optional<String>`을 못 넣게 막는 검사. 컴파일되면서 객체 수준에서는 타입이 소거된다.
2. 런타임의 선언 메타데이터 읽기 — 이 코드가 노는 층. 타입 소거는 객체에만 적용되고, 선언(필드·메서드 시그니처)의 제네릭 정보는 클래스 파일에 남아 리플렉션으로 읽힌다. `f.getGenericType()`이 그것이고 `ResolvableType` / `TypeDescriptor`가 읽는 게 바로 이 정보다.
3. 런타임의 실제 값 처리 — `convert(Optional.of(42), ...)`를 실행하는 순간에야 객체가 등장한다. 소거 때문에 `Optional.of(42)` 객체는 자기가 `Optional<Integer>`였는지 모르므로 2층의 선언 정보(TypeDescriptor)를 옆에 같이 넘겨준다. `TypeDescriptor`라는 클래스가 존재하는 근본 이유가 이것이다.

이 대화가 계기가 되어 `docs/study/concepts/compile-runtime-layers.md` 문서화 요청이 나왔다.

## G2 — diff B: 리뷰 반영 수정 (테스트 14건에서 17건)

적용 내용: 픽스처 개명, raw Optional 독립 테스트, `Optional<T>`(타입 변수) 테스트, bounded 테스트에 `convert(...) == "42"` 결과값 단언 추가, 헬퍼 위치 정리.

**질문** (원문)

> Opus 리뷰 F2는 bounded 테스트의 `canConvert(->String).isTrue()` 단언이 "판별력 0"이라고 했고, 그래서 `convert(Optional.of(42), …, String) == "42"` 단언을 추가했습니다. **`isTrue()` 단언만으로는 왜 부족했을까요?** — 힌트: 상한 `Number` 해석이 틀려서 원소 타입이 `Object`로 잡혀도 이 단언이 통과해버리는 이유가 무엇일까요?

**시도 1 — 답변** (문서화 요청 메시지 끝에 함께 제출됐다)

> 우선 그리고 질문에 대한 답을 하면 convert를 통해 옵셔널 42을 Nuber객체로 잡고 이를 바탕으로 String으로 제대로 바뀌였을때 문자열 "42"인지 정확히 검사하도록 테스트를 설계한거 아니야?

**판정 1** — fail (1/2). 부족점:

- 답변은 새로 추가한 단언이 무엇을 하는지만 설명했고, 질문인 "기존 `isTrue()` 단언이 왜 부족했나"에는 답하지 않았다.
- 상한 Number 해석이 틀려서 원소 타입이 Object로 잡혔다고 가정했을 때 `canConvert(->String)`가 어떤 값을 반환할지, `DefaultConversionService`에 어떤 변환기가 등록돼 있는지를 근거로 짚어야 한다.

**시도 2 — 답변**

> 그런데 이게 Number라는 해석이 틀릴 수가 있어? Object로 즉 해석이 안되면 그거 자체가 Object로 판정하는 문제가 있고 Object -> String으로 변환하면 ""으로 나오겠지?

**판정 2** — fail (2/2), 규칙에 따라 통과 처리.

**정답 정리**

인정된 부분: "지금 코드에서 Number 해석이 틀릴 수 있느냐"는 반문 자체는 좋은 질문이다. 다만 회귀 테스트가 겨냥하는 것은 현재 코드가 아니라 미래의 변경이다. 누군가 `resolveBounds`의 Object 처리나 `matches()`의 원소 타입 해석을 리팩토링하다 상한 해석을 망가뜨리면 원소가 `Number`가 아니라 `Object`로 잡히는 상태가 될 수 있다. 테스트의 값어치는 그 상황을 잡아내느냐로 매겨진다.

바로잡을 부분: "Object -> String 변환이 빈 문자열을 낸다"는 틀렸다. `DefaultConversionService`에는 `ObjectToStringConverter` 계열의 fallback 변환기가 등록돼 있다.

- `canConvert(Object, String)` -> true (변환기가 존재하므로)
- 실제로 변환하면 `toString()` 기반이라 `42`는 `"42"`가 된다. `""`이 아니다.

여기서 결론이 나온다. 상한 해석이 깨져 원소가 `Object`로 잘못 잡혀도 `Object -> String` 변환기가 있으니 `canConvert`는 여전히 true이고, `canConvert(boundedWildcardOptionalType, String).isTrue()` 단언은 상한 해석이 맞든 틀리든 똑같이 통과한다. 즉 이 단언은 "Number 상한이 실제로 판별에 쓰였다"를 전혀 증명하지 못한다. 판별력 0이다.

보강은 두 갈래로 들어간다.

1. `convert(Optional.of(42), boundedType, String) == "42"` — 통과 여부만이 아니라 변환 파이프라인이 원소를 실제로 꺼내 String으로 바꾸는 것까지 확인하는 end-to-end 단언. 긍정 방향에 행위적 내용을 부여한다.
2. 판별력의 핵심은 여전히 `-> LocalDate`가 false인 쪽이다. `Number -> LocalDate` 변환기는 등록돼 있지 않으므로, 상한 해석이 깨져 원소가 `Object`로 잡히면 이 단언이 무너진다. 상한 해석이 살아 있어야만 통과하는 단언이라 진짜 회귀 가드 역할을 한다.

일반화하면, 통과가 쉬운 fallback 경로가 존재하는 방향의 긍정 단언은 회귀 가드가 되기 어렵고, 부정 단언(false여야 하는 쪽)이 판별력을 담당하는 경우가 많다.

## 반복된 오해 패턴

두 게이트의 오답은 뿌리가 하나다. 판별의 입력이 객체가 아니라 선언이라는 점을 놓친
것이며, 그 착오가 아래 네 가지 모양으로 나타났다.

1. **선언 타입과 런타임 객체를 혼동.** G1의 두 시도 모두 "들어오는 객체가 Number를 상속하는지"로 읽었다. `canConvert(TypeDescriptor, TypeDescriptor)`는 선언 메타데이터 두 장을 비교할 뿐 객체는 등장하지 않는다. 이 혼동이 컴파일/런타임 3층 정리와 별도 개념 문서 요청으로 이어졌다.
2. **"확인해서 통과"와 "확인하지 않고 통과"를 구분 못함.** `Optional<?>`의 true는 상속 검사 결과가 아니라 판별 포기다. null 반환이 곧 "모른다"라는 신호라는 점을 코드에서 확인해야 한다.
3. **변환 가능성을 타입의 성질로 설명.** LocalDate가 false인 이유를 "추상 객체", "String과 인터페이스 관계"로 설명했다. 실제 근거는 ConversionService에 그 변환기가 등록돼 있느냐 하나뿐이다.
4. **질문의 대상을 바꿔서 답함.** G2 1회차는 새 단언이 무엇을 하는지를 설명했고, 질문이었던 "기존 단언이 왜 부족한가"에는 답하지 않았다. 가상의 고장 상황을 세워 단언이 그때도 통과하는지 따져보는 사고가 필요했다.

## 교훈

이 기록에서 남길 것은 테스트의 값어치를 재는 기준, 한 줄 가드가 정책을 정한다는 사실,
그리고 두 fail의 공통 뿌리 셋이다.

- 테스트의 값어치는 "지금 코드에서 통과하나"가 아니라 "코드가 고장 났을 때 무너지나"로 매긴다. 긍정 단언에 fallback 경로가 있으면 그 단언은 고장을 못 잡는다.
- `resolveBounds`가 null을 반환하는 조건(`bounds[0] == Object.class`)처럼, 한 줄의 가드가 전체 판별 정책(관대냐 엄격이냐)을 결정하는 경우가 있다. 소스를 직접 확인하는 가정 실증이 이 작업에서 첫 단계였고, 그 덕에 코드 수정 없이 테스트만으로 리뷰 요청을 충족할 수 있었다.
- 이 작업의 게이트 2건이 모두 2회차 fail이었는데, 두 fail의 공통 뿌리는 같다. 대상 코드가 무엇을 입력으로 받는지(객체냐 선언 정보냐)를 확정하지 않은 채 결론부터 세운 것이다.
