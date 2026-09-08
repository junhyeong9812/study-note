# PR #151156 - 테스트 해설

> `AutoDateHistogramAggregationBuilderTests`에 추가된 한 건. 문제와 수정은
> [README.md](README.md), 공통 배경은
> [개념 문서](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

배치가 형제 PR과 다르다. 이 결함은 **누락 필드가 둘**이므로 한 테스트 안에서 기준
인스턴스 하나와 변형 둘을 세우고, 각 변형이 한 필드씩만 다르게 만든다. 그래야 어느
필드 때문에 실패했는지가 단언 단위로 갈린다.

| 인스턴스 | duration | 약어 | 나머지 세 필드 |
|---|---|---|---|
| `base` | 1000L | "s" | 동일 |
| `differentDuration` | **2000L** | "s" | 동일 |
| `differentAbbreviation` | 1000L | **"sec"** | 동일 |

## T1. testRoundingInfoEqualsConsidersAllSerializedFields - red

```java
public void testRoundingInfoEqualsConsidersAllSerializedFields() {
    AutoDateHistogramAggregationBuilder.RoundingInfo base = new AutoDateHistogramAggregationBuilder.RoundingInfo(
        Rounding.DateTimeUnit.SECOND_OF_MINUTE, ZoneOffset.UTC, 1000L, "s", 1, 5, 10, 30
    );
    AutoDateHistogramAggregationBuilder.RoundingInfo differentDuration = new AutoDateHistogramAggregationBuilder.RoundingInfo(
        Rounding.DateTimeUnit.SECOND_OF_MINUTE, ZoneOffset.UTC, 2000L, "s", 1, 5, 10, 30
    );
    AutoDateHistogramAggregationBuilder.RoundingInfo differentAbbreviation = new AutoDateHistogramAggregationBuilder.RoundingInfo(
        Rounding.DateTimeUnit.SECOND_OF_MINUTE, ZoneOffset.UTC, 1000L, "sec", 1, 5, 10, 30
    );
    assertNotEquals(base, differentDuration);
    assertNotEquals(base, differentAbbreviation);
}
```
(AutoDateHistogramAggregationBuilderTests.java:65-98. 실제 파일은 인자를 한 줄에
하나씩 펼친 포맷이라 34줄이다 - 위는 읽기 쉽게 접은 것이다.)

- **주장**: 직렬화되는 다섯 필드 중 하나만 달라도 두 `RoundingInfo`는 같지 않다.
- **fix 전 red인 이유**: 수정 전 `equals`가 `rounding`·`innerIntervals`·`dateTimeUnit`
  셋만 비교했고, 세 인스턴스는 그 셋이 모두 같다. `SECOND_OF_MINUTE` + `UTC`로 만든
  `rounding`이 같고 `innerIntervals`가 `{1,5,10,30}`으로 같으며 `dateTimeUnit`도 같은
  단위에서 유도되므로, 비교 대상 전부가 일치해 true가 나온다.

**입력 설계의 근거가 이 테스트의 핵심이다.**

- **생성자를 직접 부른다.** `buildRoundings`가 만드는 여섯 후보는 duration과 약어가
  단위에 따라 고정이므로, 그 경로로는 "셋이 같고 둘이 다른" 쌍을 만들 수 없다
  ([README 3절](README.md)). 결함을 재현하려면 생성자를 직접 불러 임의 조합을 만들어야
  하고, **생성자가 그 조합을 막지 않는다는 사실 자체가 결함이 실재한다는 근거**다.
- **`SECOND_OF_MINUTE`을 고른 이유.** 생성자가 `dateTimeUnit`이 `ALLOWED_INTERVALS`에
  있는지 검증하므로 아무 단위나 쓸 수 없다. 초 단위는 `buildRoundings`의 첫 후보와 같은
  형태라 실제 값과 가장 가깝다.
- **`1000L` -> `2000L`.** 초 단위의 실제 duration이 1000이므로, 2000은 "같은 단위인데
  duration만 다른" 있을 수 없어 보이는 조합이다. 그 조합을 equals가 구분하지 못한다는
  것이 바로 지적이다.
- **`"s"` -> `"sec"`.** 약어는 표시용 문자열이라 값이 무엇이든 의미가 성립한다. 두 변형이
  각각 `long` 비교와 `String` 비교를 대표하도록 나눈 것이기도 하다.
- **`innerIntervals`를 varargs로 넘긴다.** 생성자 시그니처가
  `RoundingInfo(DateTimeUnit, ZoneId, long, String, int...)`라 뒤의 `1, 5, 10, 30`이
  배열이 된다. 세 인스턴스가 같은 값을 나열하므로 배열은 서로 다른 객체지만
  `Objects.deepEquals`로 같게 비교된다 - 즉 **배열 축은 이 테스트에서 변수가 아니다.**

**단언이 둘로 나뉜 이유.** 형제 PR처럼 반복문으로 묶지 않고 두 줄로 나눈 것은, 실패
메시지만으로 어느 필드가 문제인지 알 수 있게 하기 위해서다. 누락 필드가 둘이므로 한
쪽만 고치는 불완전한 수정이 있었다면 이 배치가 그것을 즉시 드러낸다.

**hashCode 단언이 없다.** 형제 PR 둘은 리뷰 지적으로 hashCode 단언을 보강했는데 이
건은 그대로 머지됐다. 리뷰어가 이 파일을 지적하지 않았고 우리도 먼저 보강하지 않았다.
지금 기준으로 보면 이름에 `Equals`만 있어 형제들과 달리 이름과 내용이 어긋나지는 않지만,
`Objects.hash`에 두 필드를 더한 변경을 직접 겨누는 단언이 없다는 점은 남는다 -
**아카이브 시점의 미비로 기록해 둔다.**

## 기존 테스트가 맡은 가드

이 파일에는 원래 두 건이 있었고 둘 다 fix 전후 green이다.

- `testInvalidInterval`(:25-) - `setMinimumIntervalExpression`이 허용 목록 밖 값을
  거부하는지.
- `testRoundingsMatchAllowedIntervals`(:-58) - `buildRoundings`가 만드는 단위 집합이
  `ALLOWED_INTERVALS`의 값 집합과 일치하는지.

두 번째가 이 PR과 간접적으로 맞물린다. `buildRoundings`가 만드는 후보 집합이 고정이라는
사실을 고정하는 테스트이고, 그 고정성이 바로 이 결함을 가려 온 우연이다
([README 3절](README.md)).

이 클래스는 `ESTestCase`를 직접 상속해 프레임워크의 라운드트립·계약 테스트를 받지
않는다. `RoundingInfo`가 빌더의 필드가 아니라 결과 쪽에서 쓰이는 값 객체라 애초에
집계 빌더용 프레임워크의 사정권 밖이기도 하다 - 이 결함이 오래 잠복한 이유의 한
겹이다.

## 실측 요약

- **fix 전**: 형제 셋과 함께 `3 tests completed, 3 failed`. 이 건은
  `testRoundingInfoEqualsConsidersAllSerializedFields`가 실패했고, 원인은 duration
  (1000 vs 2000)과 약어("s" vs "sec") 차이를 equals가 무시한 것이다.
- **fix 후**: green, 클래스 전체 회귀 없음.
- **diff 규모**: 프로덕션 2메서드(hashCode 한 줄 교체, equals에 두 줄 추가) + 테스트
  1건 + import 둘(`Rounding`, `ZoneOffset`) + changelog YAML 1건.
