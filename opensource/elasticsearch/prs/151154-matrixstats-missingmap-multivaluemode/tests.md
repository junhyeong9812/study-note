# PR #151154 - 테스트 해설

> 신규 파일 `MatrixStatsAggregationBuilderTests`의 두 건. 문제와 수정은
> [README.md](README.md), 계층 구조는 [structure.md](structure.md), 공통 배경은
> [개념 문서](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

배치를 먼저 본다. 이 PR은 **두 층에 각각 결함이 있으므로 테스트도 층마다 하나씩**이다.
부모 층의 `missingMap`과 자식 층의 `multiValueMode`를 각각 겨누고, 두 테스트 모두
concrete 클래스인 `MatrixStatsAggregationBuilder`로 검증한다 - 부모가 abstract이라
직접 인스턴스를 만들 수 없기 때문이다.

| 겨누는 층 | 테스트 | red가 된 시점 |
|---|---|---|
| 부모 `ArrayValuesSourceAggregationBuilder` | `testEqualsAndHashCodeConsiderMissingMap` | 프로덕션 수정 전 |
| 자식 `MatrixStatsAggregationBuilder` | `testEqualsAndHashCodeConsiderMultiValueMode` | 부모만 고친 상태에서 |

두 번째 행이 이 PR의 특징이다. **한 PR 안에서 red -> green을 두 번 밟았다.** 부모
수정을 넣은 뒤에도 두 번째 테스트가 여전히 red였고, 그것이 "부모만 고쳐서는
`matrix_stats`의 동등성이 완결되지 않는다"는 증거였다.

## T1. testEqualsAndHashCodeConsiderMissingMap - red

```java
public void testEqualsAndHashCodeConsiderMissingMap() {
    MatrixStatsAggregationBuilder a = new MatrixStatsAggregationBuilder("matrix").missingMap(Map.of("field", 1));
    MatrixStatsAggregationBuilder b = new MatrixStatsAggregationBuilder("matrix").missingMap(Map.of("field", 2));
    assertNotEquals(a, b);
    assertNotEquals(a.hashCode(), b.hashCode());

    // Builders that agree on missingMap are equal and, per the hashCode contract, must hash consistently.
    MatrixStatsAggregationBuilder aCopy = new MatrixStatsAggregationBuilder("matrix").missingMap(Map.of("field", 1));
    assertEquals(a, aCopy);
    assertEquals(a.hashCode(), aCopy.hashCode());
}
```
(MatrixStatsAggregationBuilderTests.java:23-33)

- **주장**: 같은 키에 다른 값을 넣은 두 `missingMap`은 서로 다른 요청이므로 같지 않다.
- **fix 전 red인 이유**: 수정 전 부모 `equals`가 `missingMap`이 아니라 항상 null인
  `missing`을 비교했으므로, 두 빌더의 나머지가 같으면 결과가 true였다.
- **실측 실패 메시지**:
  `Values should be different. Actual: {"matrix":{"matrix_stats":{"fields":[],"mode":"AVG"}}}`.
  이 메시지가 결함의 성격을 한 줄로 보여 준다. **렌더된 JSON에 `missing`이 아예 없다** -
  당시 `internalXContent`가 죽은 `missing` 필드를 조건으로 삼고 있었기 때문이다. 즉
  실패 메시지만으로는 두 빌더가 어디가 다른지 알 수조차 없었고, 그 자체가 리뷰에서
  드러날 XContent 출력 누락의 예고였다.

**입력 설계의 근거.** 값을 `Map.of("field", 1)`과 `Map.of("field", 2)`로 잡은 것은
"키는 같고 값만 다른" 최소 차이를 만들기 위해서다. 키를 다르게 하면 맵 크기나 키 집합
같은 다른 축이 함께 달라져 무엇이 판정을 갈랐는지 흐려진다. 값 타입으로 `Integer`를
쓴 것도 의도적이다 - XContent 왕복에서 타입이 보존되는 값이라(README 8.4절) 이후 이
테스트가 왕복 관련 변경에 휘말리지 않는다.

**네 단언의 역할**은 형제 PR [#151152](../151152-timeseries-size-equality/tests.md)의
T1과 같다. 앞의 둘이 결함을 겨누고 필드 참여를 관측하며, 뒤의 둘이 "이미 같던 것"을
갈라놓지 않았음과 hashCode 계약의 강제 방향을 지킨다. 뒤의 세 줄은 리뷰 대응(커밋
`62bcb7ec779`)에서 추가됐다.

## T2. testEqualsAndHashCodeConsiderMultiValueMode - 두 번째 red

```java
public void testEqualsAndHashCodeConsiderMultiValueMode() {
    MatrixStatsAggregationBuilder a = new MatrixStatsAggregationBuilder("matrix").multiValueMode(MultiValueMode.MIN);
    MatrixStatsAggregationBuilder b = new MatrixStatsAggregationBuilder("matrix").multiValueMode(MultiValueMode.MAX);
    assertNotEquals(a, b);
    assertNotEquals(a.hashCode(), b.hashCode());

    // Builders that agree on multiValueMode are equal and, per the hashCode contract, must hash consistently.
    MatrixStatsAggregationBuilder aCopy = new MatrixStatsAggregationBuilder("matrix").multiValueMode(MultiValueMode.MIN);
    assertEquals(a, aCopy);
    assertEquals(a.hashCode(), aCopy.hashCode());
}
```
(MatrixStatsAggregationBuilderTests.java:41-51)

- **주장**: `multiValueMode`만 다른 두 빌더는 같지 않다.
- **red인 이유**: 자식이 `equals`를 오버라이드하지 않아 부모 구현을 물려받았고, 부모는
  이 필드를 모른다. 그래서 **부모의 `missingMap` 수정을 적용한 뒤에도** 이 테스트는
  여전히 실패했다(실측 메시지의 `mode:MAX`). 자식에 오버라이드를 추가하고서야 green이
  됐다.
- 기본값이 `AVG`이므로 `MIN`과 `MAX`를 골랐다. 한쪽을 기본값으로 두면 "setter가 실제로
  값을 바꿨는가"라는 다른 실패 원인이 섞일 수 있다.

이 테스트가 [structure.md](structure.md) 1절의 위임 규칙을 그대로 검증한다. 각 층이
자기 필드를 책임진다는 규칙이 지켜지면 통과하고, 한 칸이 비면 정확히 그 층의 필드에서
실패한다.

## 왜 이 파일은 ESTestCase를 직접 상속하나

이 파일은 형제 PR의 테스트와 달리 `BaseAggregationTestCase` 계열이 아니라 `ESTestCase`를
직접 상속한다.

```java
public class MatrixStatsAggregationBuilderTests extends ESTestCase {
```
(MatrixStatsAggregationBuilderTests.java:16)

결과가 둘이다. 첫째, 프레임워크가 주는 직렬화·XContent·shallowCopy 라운드트립 테스트를
받지 못한다. 둘째, 일반 equals/hashCode 계약 테스트도 상속하지 않는다. 두 번째가
리뷰 대응에서 판단 근거가 됐다 - 형제 PR은 프레임워크 테스트가 계약의 정방향을 일부나마
건드리지만 이 클래스는 그마저 없으므로, `assertEquals(a.hashCode(), aCopy.hashCode())`를
직접 두는 값어치가 더 크다. 그 근거를 리뷰 답글에 적고 "최소로 줄이길 원하면 그렇게
하겠다"고 덧붙였으며, 리뷰어는 그대로 승인했다.

거꾸로 말하면 이 빌더에는 여전히 직렬화 라운드트립 테스트가 없다. 이번 결함은 정방향
(직렬화 O, equals X)이라 라운드트립 테스트로는 어차피 잡히지 않았겠지만
([개념 문서 4절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)),
역방향 결함이 생긴다면 이 파일은 그것을 잡지 못한다. **범위 밖으로 남긴 관찰**이다.

## 실측 요약

- **fix 전(부모)**: 세 형제 PR의 red를 한 번에 돌려 `3 tests completed, 3 failed`.
  이 PR 몫의 실패 메시지는 `Values should be different. Actual:
  {"matrix":{"matrix_stats":{"fields":[],"mode":"AVG"}}}`.
- **부모 수정 후**: T1 green, **T2는 여전히 red**(`mode:MAX`). 자식 오버라이드 추가 후
  둘 다 green.
- **리뷰 대응 후**: `:modules:aggregations:test --tests "...metric.*"`와
  `:modules:aggregations:spotlessJavaCheck` 모두 `BUILD SUCCESSFUL`.
- **최종 diff**: 프로덕션 2파일(부모의 필드 제거·XContent 교체·동등성 교체, 자식의
  오버라이드 추가) + 테스트 신규 1파일 + changelog YAML 1건.
