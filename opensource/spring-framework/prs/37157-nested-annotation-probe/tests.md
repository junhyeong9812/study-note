# PR #37157 — 테스트 해설 (테스트 하나하나)

> `AttributeMethodsTests`에 추가된 12건. 형식·개념은 ../37153/tests.md,
> ../37153/guard-tests.md 참조. mock 구조가 #37153과 다른 핵심: **mock이 2겹**이다
> (outer mock의 `value()`가 inner mock을 반환, inner mock의 `value()`가 예외) —
> 1겹으로 만들면 기존 직접-속성 probe 테스트가 될 뿐, 이 PR의 새 동작인 재귀 층을
> 검증하지 못한다.

먼저 전체 배치. red 6건이 결함 재현이고, 가드 6건이 보존 동작의 명세다.

| | 오염(willThrow via inner) | 정상/빈(willReturn) |
|---|---|---|
| 플래그 | 1·2: annotation/annotation[] -> true (red 2) | — |
| canLoad 단일 | 3: false (red) | 4: true (양성 가드) |
| validate 단일 | 5: ISE+메시지·cause (red) | 6: 무예외 (양성 가드) |
| canLoad 배열 | 7: false (red) | 8: 정상 배열 true / 9: **빈 배열** true (가드 2) |
| validate 배열 | 10: ISE+메시지·cause (red) | — |
| depth-2 | 11: canLoad false (red) / 12: validate ISE (red) | — |

## 1·2. 플래그 테스트 — red

첫 두 건은 mock도 예외도 없이 플래그 한 칸만 보는 가장 좁은 재현이다.

```java
@Test
void canThrowTypeNotPresentExceptionWhenHasAnnotationAttributeReturnsTrue() {
	AttributeMethods methods = AttributeMethods.forAnnotationType(NestedValue.class);
	assertThat(methods.canThrowTypeNotPresentException(0)).isTrue();
}
```

annotation(과 annotation[]) 속성이 probe 대상으로 표시되는가. fix 전 false -> red.
가장 좁은 재현(mock·예외 불요).

## 3·4. canLoad 단일 nested — red + 양성 가드

다음 두 건은 2겹 mock으로 재귀 층 자체를 겨눈다.

```java
@Test
void isValidWhenNestedAnnotationHasEnumConstantNotPresentExceptionReturnsFalse() {
	EnumValueInner inner = mockBrokenEnumValueInner();
	NestedValue annotation = mockAnnotation(NestedValue.class);
	given(annotation.value()).willReturn(inner);
	AttributeMethods attributes = AttributeMethods.forAnnotationType(annotation.annotationType());
	assertThat(attributes.canLoad(annotation, getClass())).isFalse();
}
```

- **2겹 mock의 의미**: outer는 정상적으로 inner를 반환(프레임 1 invoke 성공을
  재현)하고, inner의 `value()`만 던진다(프레임 2의 폭탄). 재귀가 없으면 예외를
  관측할 코드가 없어 true 오판 -> red. 정상 inner를 주는 4번은 "재귀가 무고한
  nested를 걸러버리지 않는다"의 양성 가드.
- **inner를 변수로 선행 생성하는 이유**: `willReturn(mockBrokenEnumValueInner())`
  처럼 인자 안에서 mock을 만들며 stubbing하면 Mockito의 진행 중 stubbing 슬롯이
  겹쳐 `UnfinishedStubbingException` — 실제로 밟았던 함정이다. 상세:
  [mockito-stubbing-mechanics](../../concepts/mockito-stubbing-mechanics/mockito-stubbing-mechanics.md).

## 5·6. validate 단일 nested — red + 양성 가드

같은 오염을 시끄러운 출구에 걸되, 어서션이 예외 타입에서 멈추지 않는다.

```java
assertThatIllegalStateException().isThrownBy(() -> attributes.validate(annotation))
		.withMessageContaining("EnumValueInner")
		.withCauseInstanceOf(EnumConstantNotPresentException.class);
```

- ISE가 던져진다는 것만이 아니라 **메시지가 가장 안쪽 annotation(EnumValueInner)을
  지목하고 원인 예외가 cause로 보존된다**는 계약까지 고정한다(리뷰 F3 반영).
  이 어서션이 없으면, 미래에 각 프레임이 ISE를 자기 컨텍스트로 재래핑하는
  수정(진단이 바깥 이름으로 바뀌는 회귀)이 타입 검사만으로는 통과해버린다.

## 7~9. canLoad 배열 — red + 가드 2 (리뷰 F2 반영)

배열 쪽은 오염·정상·빈 배열 세 입력을 각각 맡는 세 건으로 갈라진다.

```java
@Test
void isValidWhenNestedAnnotationArrayIsEmptyReturnsTrue() {
	NestedArrayValue annotation = mockAnnotation(NestedArrayValue.class);
	given(annotation.value()).willReturn(new EnumValueInner[0]);
	...
	assertThat(attributes.canLoad(annotation, getClass())).isTrue();
}
```

- 7(오염 원소 1개 -> false)이 red, 8(정상 원소 -> true)이 양성 가드.
- **9(빈 배열 -> true)가 따로 있는 이유**: 검사할 원소가 없으면 "깨진 게 발견되지
  않음" = 통과(공허한 참)가 정답이다. 현재 구현은 "발견하면 실패" 구조라 루프
  0회면 자연히 true인데, 미래에 "증명될 때만 true"(누적 boolean) 구조로 재구성되면
  **루프 0회 경로만 false로 뒤집혀** 빈 배열 annotation이 조용히 스캔에서 사라진다
  — 다른 테스트는 전부 green인 채로. 그 경로 하나를 고정하는 가드다.

## 10. validate 배열 — red (F2 반영)

7번의 validate 판이며 5번과 같은 메시지·cause 어서션을 포함한다.

## 11·12. depth-2 — red 2

마지막 두 건은 재귀가 한 단이 아니라 연쇄로 도는 경로를 세운다.

```java
EnumValueInner inner = mockBrokenEnumValueInner();
NestedValue nested = mockAnnotation(NestedValue.class);
given(nested.value()).willReturn(inner);
DeepNestedValue annotation = mockAnnotation(DeepNestedValue.class);
given(annotation.value()).willReturn(nested);
```

3겹 구조(Deep->Nested->EnumValueInner)로 재귀가 **2단 연쇄**되는 경로를 canLoad
(boolean 전파)와 validate(ISE 그대로 통과 2회) 양쪽에서 고정한다. validate 쪽도
메시지가 여전히 최심부(EnumValueInner)를 지목해야 한다 — "매 프레임 그대로
재던지기"가 연쇄에서도 유지된다는 증명(F3 반영).

## fixture와 헬퍼

열두 건이 공유하는 재료는 포장 깊이가 다른 annotation 넷과 enum 하나다.

```java
@interface EnumValueInner { ExampleEnum value(); }   // 폭탄을 담는 최심부(단일 enum이라 기존 플래그로 probe됨)
@interface NestedValue { EnumValueInner value(); }    // 1겹 포장
@interface NestedArrayValue { EnumValueInner[] value(); }
@interface DeepNestedValue { NestedValue value(); }   // 2겹 포장
enum ExampleEnum { ONE }
```

`mockBrokenEnumValueInner()`(value()가 ECNPE를 던지는 mock)와
`mockHealthyEnumValueInner()`(ONE 반환)가 stubbing 완결 상태의 inner를 만들어
반환한다 — 헬퍼를 다른 stubbing의 인자 자리에서 호출하지 않는 것이 규칙.

## 실측 요약

실행 결과는 정정을 한 번 거친 뒤 red/green 예측과 정확히 일치했다.

- fix 전: 23 중 6 failed(1·2·3·5·7·11) — 1차 시도는 Mockito 중첩 stubbing 버그로
  8 failed(가드까지 오염)였고, 정정 후 예측과 정확히 일치.
- fix 후: 27/27 green(리뷰 반영분 포함) + annotation 패키지 스위트 통과.
- 성능: before/after 벤치로 기존 probe 무회귀·nested 속성당 +50~70ns 실측
  (상세는 README §5).
