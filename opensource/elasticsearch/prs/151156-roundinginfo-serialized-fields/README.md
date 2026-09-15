# PR #151156 - AutoDateHistogram RoundingInfo의 equals/hashCode에 직렬화 필드 전부 포함

## 0. 정향

이 문서는 `auto_date_histogram` 집계가 쓰는 값 객체 `RoundingInfo`가 **다섯 필드를 직렬화하면서 셋만 비교하고 있던** 결함의 해설이다.\
형제 PR 셋 중 가장 단순한 건이고, 그래서 다른 것을 배울 자리다.\
앞선 #151154에서 얻은 **형제 검사** 절차를 이슈를 열기 전에 적용한 첫 사례이고, "실무에서 재현되지 않는 결함을 그래도 고칠 값어치가 있는가"를 판단한 사례이기도 하다.

> **값 객체(value object)** — 고유한 정체성 없이 담고 있는 값들로만 자신을 정의하는 객체.\
> 예: 같은 단위·같은 duration·같은 약어를 가진 두 `RoundingInfo`는 서로 다른 인스턴스여도 "같은 것"으로 취급돼야 한다.

> **형제 검사(sibling check)** — 결함 하나를 찾았을 때 같은 클래스·같은 계층의 이웃에도 같은 누락이 있는지 훑는 절차.\
> 예: `RoundingInfo`를 고치기 전에 그것을 품은 바깥 빌더에도 같은 누락이 있는지 먼저 확인했다.

다 읽으면 "다섯 중 셋"이 왜 결함인지, 그리고 왜 이 결함이 현재 코드베이스에서는 사실상 발화하지 않는지를 함께 설명할 수 있어야 한다.

상태: **머지 2026-06-19**(`5130e384dd8`, `main`, `v9.5.0`).\
이슈 #151155를 닫는다.\
리뷰 라운드 없이 `LGTM. Thanks for the fix!`로 한 번에 승인됐다.

같은 폴더: [테스트 해설](tests.md).\
무대가 값 객체 하나라 실구조 문서는 두지 않았고, 착수 분석은 별도 문서 [analysis.md](analysis.md)에 있다.\
개념 문서: [직렬화 필드와 동등성의 정합 계약](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

## 1. 배경 - RoundingInfo는 무엇을 담는 값 객체인가

`auto_date_histogram`은 사용자가 간격을 지정하지 않고 **원하는 버킷 개수**를 주면 데이터 범위를 보고 적당한 시간 단위를 스스로 고르는 집계다.\
그 "고를 수 있는 단위 후보"를 하나씩 표현한 것이 `RoundingInfo`다.

```java
public static class RoundingInfo implements Writeable {
    final Rounding rounding;
    final int[] innerIntervals;
    final long roughEstimateDurationMillis;
    final String unitAbbreviation;
    final String dateTimeUnit;
```
(modules/aggregations AutoDateHistogramAggregationBuilder.java:260-265)

후보는 여섯 개가 고정으로 만들어진다 - 초·분·시·일·월·년.

```java
roundings[0] = new RoundingInfo(Rounding.DateTimeUnit.SECOND_OF_MINUTE, timeZone, 1000L, "s", 1, 5, 10, 30);
roundings[1] = new RoundingInfo(Rounding.DateTimeUnit.MINUTE_OF_HOUR, timeZone, 60 * 1000L, "m", 1, 5, 10, 30);
...
```
(:80-101, `buildRoundings`)

`roughEstimateDurationMillis`는 그 단위의 대략적 길이(초면 1000)이다.\
`unitAbbreviation`은 사람이 읽는 약어("s")이고, `innerIntervals`는 그 단위 안에서 쓸 수 있는 배수(1·5·10·30초)다.\
집계가 버킷 수를 맞추려고 단위를 한 칸씩 키울 때 이 값들을 쓴다.

이 클래스는 `Writeable`이므로 노드 사이를 건너간다.\
다섯 필드가 모두 실린다.

> **Writeable** — ES에서 "이 객체는 노드 사이로 보낼 수 있다"를 선언하는 인터페이스. `writeTo`로 쓰고 `StreamInput` 생성자로 읽는다.\
> 예: `RoundingInfo`가 `Writeable`이라는 것은, 이 객체가 코디네이터에서 데이터 노드로 실제로 건너간다는 뜻이다.

```java
@Override
public void writeTo(StreamOutput out) throws IOException {
    rounding.writeTo(out);
    out.writeVLong(roughEstimateDurationMillis);
    out.writeIntArray(innerIntervals);
    out.writeString(unitAbbreviation);
    out.writeString(dateTimeUnit);
}
```
(:293-300, `StreamInput` 생성자는 같은 다섯을 같은 순서로 읽는다 - :285-291)

## 2. 수정 전 동작 - 다섯을 싣고 셋을 비교했다

수정 전 동등성은 세 필드만 봤다.

```java
// 수정 전
public int hashCode() {
    return Objects.hash(rounding, Arrays.hashCode(innerIntervals), dateTimeUnit);
}
...
    return Objects.equals(rounding, other.rounding)
        && Objects.deepEquals(innerIntervals, other.innerIntervals)
        && Objects.equals(dateTimeUnit, other.dateTimeUnit);
```

`RoundingInfo` 인스턴스 하나가 어느 갈래로 나뉘어 처리되는지 세로로 따라가면 이렇다.

```text
  RoundingInfo(SECOND_OF_MINUTE, UTC, 1000L, "s", 1,5,10,30)
        |
        +--> writeTo (:293)
        |       rounding                    -> 실린다
        |       roughEstimateDurationMillis -> 실린다 (1000)
        |       innerIntervals              -> 실린다 ({1,5,10,30})
        |       unitAbbreviation            -> 실린다 ("s")
        |       dateTimeUnit                -> 실린다
        |
        +--> equals (수정 전)
                rounding                    -> 본다
                roughEstimateDurationMillis -> 안 본다
                innerIntervals              -> 본다
                unitAbbreviation            -> 안 본다
                dateTimeUnit                -> 본다
```

직렬화 목록과 비교 목록을 나란히 놓으면 차집합이 바로 나온다.

| 필드 | writeTo | equals·hashCode (수정 전) |
|---|---|---|
| `rounding` | 예 | 예 |
| `roughEstimateDurationMillis` | 예 | **아니오** |
| `innerIntervals` | 예 | 예 |
| `unitAbbreviation` | 예 | **아니오** |
| `dateTimeUnit` | 예 | 예 |

이 표가 이 PR의 전부다.\
판정에 해석이 끼어들 자리가 없다 - 직렬화 목록이 동등성의 정답지이고([개념 문서 1절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)), 그 정답지의 다섯 중 둘이 채점에서 빠져 있었다.

## 3. 문제 - 계약 위반이지만, 현재 코드에서는 발화하지 않는다

정직하게 말하면 이 결함은 **지금의 upstream 코드에서 실제로 두 인스턴스가 갈리는 상황을 만들기 어렵다.**\
이유는 `buildRoundings`가 여섯 후보를 상수로 만들기 때문이다.\
`SECOND_OF_MINUTE`이면 duration은 언제나 `1000L`이고 약어는 언제나 `"s"`다.\
즉 정상 경로에서는 **비교에 포함된 `dateTimeUnit`이 빠진 두 필드의 값을 사실상 결정한다.**\
그래서 "셋이 같은데 둘이 다른" 인스턴스 쌍이 정상 생성으로는 나오지 않는다.

정상 경로와 생성자 직접 호출을 나란히 놓으면 결함이 어디서만 보이는지가 드러난다.

```text
  정상 경로 (buildRoundings)            생성자 직접 호출
+-----------------------------+      +-----------------------------+
| SECOND_OF_MINUTE            |      | SECOND_OF_MINUTE            |
|   -> duration 은 항상 1000   |      |   -> duration 2000 도 가능   |
|   -> 약어는 항상 "s"         |      |   -> 약어 "sec" 도 가능       |
+-----------------------------+      +-----------------------------+
| 셋이 같으면 다섯도 같다       |      | 셋은 같은데 둘이 다른 쌍       |
| -> 어긋남이 안 보인다         |      | -> equals 가 true 라 red     |
+-----------------------------+      +-----------------------------+
   상수 관계라는 우연이 가려 준다         우연을 걷어내면 어긋남이 보인다
```

그래도 고칠 값어치가 있다고 본 근거가 셋이다.

**첫째, 생성자가 그 결정 관계를 강제하지 않는다.**\
`RoundingInfo`의 public 생성자는 duration과 약어를 인자로 받고 검증하지 않는다(:267-283에서 검증하는 것은 `dateTimeUnit`이 허용 목록에 있는가뿐이다).\
테스트나 외부 코드가 임의 조합을 만들 수 있고, 실제로 이 PR의 테스트가 그렇게 만든다.

**둘째, 역직렬화 경로는 상수를 거치지 않는다.**\
`StreamInput` 생성자는 스트림에 실려 온 값을 그대로 받는다(:285-291).\
상대 노드의 버전이 달라 상수가 달라진다면 - 예컨대 어느 버전이 `unitAbbreviation`을 바꾼다면 - 두 값이 실제로 갈린다.\
`writeTo`가 이 필드들을 굳이 싣는 이유도 "받는 쪽이 스스로 계산하지 않고 보낸 값을 쓴다"는 설계이기 때문이다.

> **역직렬화(deserialization)** — 바이트 열을 다시 객체로 되살리는 것.\
> 예: `StreamInput` 생성자는 `readVLong()`이 준 값을 그대로 `roughEstimateDurationMillis`에 넣는다 - `SECOND_OF_MINUTE`이니 1000일 것이라고 계산하지 않는다.

**셋째, 이 값 객체의 동등성은 결과 비교에 직접 참여한다.**\
`RoundingInfo`는 빌더의 `equals`에는 들어가지 않지만(빌더가 직렬화하는 것은 `numBuckets`와 `minimumIntervalExpression` 둘뿐이다 - :125-126, :131-132), 결과 쪽에서 `InternalAutoDateHistogram.BucketInfo`가 `RoundingInfo[]`를 `Objects.deepEquals`로 비교한다(InternalAutoDateHistogram.java:161).\
즉 **이 결함이 고쳐지면 reduce 결과의 동등성 판정도 함께 정확해진다** - 교차 검증이 보너스로 짚은 지점이다.

> **deep-equality** — 배열이나 중첩 구조를 원소 하나하나까지 내려가 비교하는 것.\
> 예: `Objects.deepEquals(RoundingInfo[], RoundingInfo[])`는 배열 주소가 아니라 원소들의 `equals`를 차례로 부른다 - 그래서 원소의 equals가 틀리면 배열 비교도 같이 틀린다.

> **reduce** — 여러 샤드가 낸 부분 결과를 코디네이터가 하나로 합치는 단계.\
> 예: 샤드별 `InternalAutoDateHistogram`을 합칠 때 `BucketInfo`가 서로 같은지 비교한다.

요컨대 이것은 "지금 터지는 버그"가 아니라 **직렬화가 정의한 상태와 동등성이 정의한 상태가 어긋나 있는 상태**이고, 상수 관계라는 우연이 그 어긋남을 가려 주고 있었다.\
우연에 기댄 정합은 그 우연이 깨지는 순간 조용히 틀린다.

> **조용한 실패(silent failure)** — 프로그램이 에러를 내지 않고 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 두 `RoundingInfo`가 "같다"고 잘못 판정돼도 예외는 나지 않는다 - 판정 결과만 틀린 채 위로 올라간다.

## 4. 수정 해설 - 다섯을 다 본다

```java
@Override
public int hashCode() {
    return Objects.hash(rounding, Arrays.hashCode(innerIntervals), dateTimeUnit, roughEstimateDurationMillis, unitAbbreviation);
}

@Override
public boolean equals(Object obj) {
    ...
    RoundingInfo other = (RoundingInfo) obj;
    return Objects.equals(rounding, other.rounding)
        && Objects.deepEquals(innerIntervals, other.innerIntervals)
        && Objects.equals(dateTimeUnit, other.dateTimeUnit)
        && roughEstimateDurationMillis == other.roughEstimateDurationMillis
        && Objects.equals(unitAbbreviation, other.unitAbbreviation);
}
```
(AutoDateHistogramAggregationBuilder.java:318-337)

같은 입력 한 쌍에 답이 어떻게 달라지는지 나란히 놓으면 이렇다.

```text
      수정 전                              수정 후
+-----------------------------+    +-----------------------------+
| base (1000L, "s")           |    | base (1000L, "s")           |
| differentDuration (2000L)   |    | differentDuration (2000L)   |
+-----------------------------+    +-----------------------------+
| 비교 필드 3 개               |    | 비교 필드 5 개               |
|   rounding        같다       |    |   rounding        같다       |
|   innerIntervals  같다       |    |   innerIntervals  같다       |
|   dateTimeUnit    같다       |    |   dateTimeUnit    같다       |
|                             |    |   duration   1000 vs 2000   |
|                             |    |   약어       "s" vs "s"      |
| -> true                     |    | -> false                    |
+-----------------------------+    +-----------------------------+
   직렬화 다섯과 어긋난다              직렬화 다섯과 일치한다
```

비교 형태는 타입이 정했다.\
`roughEstimateDurationMillis`는 primitive `long`이라 `==`이고, `unitAbbreviation`은 `String`이라 `Objects.equals`다.\
후자는 정상 생성 경로에서는 항상 non-null이지만(`buildRoundings`가 리터럴을 넘긴다) 생성자가 non-null을 강제하지 않으므로 방어적 비교가 옳다.

> **방어적 비교(null-safe comparison)** — 한쪽이 null이어도 예외 없이 결론을 내는 비교.\
> 예: `a.equals(b)`는 a가 null이면 터지지만, `Objects.equals(a, b)`는 둘 다 null일 때 true를 낸다.

기존 두 줄의 형태를 바꾸지 않고 뒤에 두 줄을 더한 것도 의도적이다.\
`innerIntervals`가 `int[]`라 `Objects.deepEquals`(equals)와 `Arrays.hashCode`(hashCode)로 비대칭적으로 다뤄지는데, 이것은 배열의 올바른 취급이므로 손대지 않았다.

## 5. 검증

이 건은 **이슈를 열기 전에** 교차 검증을 한 번 돌렸다.\
앞선 #151154에서 우리 조사가 형제 누락(`multiValueMode`)을 놓친 경험이 있어서, 같은 실수를 반복하지 않으려고 절차를 앞당긴 것이다.\
물은 것은 넷이었다.

| 질문 | codex 판정 | 우리 교차 확인 |
|---|---|---|
| RoundingInfo 수정이 정확·완전한가 | correct and complete - 다섯 중 누락된 둘을 더하면 완전 | `writeTo`(:294)·ctor(:285) 실코드 일치 |
| **바깥 클래스에도 같은 누락이 있는가** | 없음 - 빌더는 `numBuckets`·`minimumIntervalExpression`만 직렬화하고 둘 다 이미 비교한다 | 직렬화(:125-126, :131-132)·동등성(:242-252) 실코드 일치 |
| `long ==`·`String Objects.equals`에 함정이 있는가 | 없음. 약어는 `buildRoundings`에서 항상 non-null 리터럴이나 생성자가 강제하지 않으므로 `Objects.equals`가 옳다 | - |
| BWC·reduce 영향 | wire 불변. 보너스로 `BucketInfo`의 `RoundingInfo[]` deep-equality가 정확해진다 | InternalAutoDateHistogram.java:161 확인 |

> **BWC(backward compatibility)** — 구버전 노드와 신버전 노드가 섞여 있어도 통신이 깨지지 않는 성질.\
> 예: 이 PR은 `writeTo`의 필드 순서·개수를 하나도 건드리지 않았으므로 바이트 형식이 그대로다 - "wire 불변"이 그 뜻이다.

계획대로 진행했고 변경은 없었다.\
형제 검사가 "없음"으로 나온 것이 이 PR을 작게 유지한 근거다.

테스트는 red를 먼저 확인했다.\
프로덕션을 손대지 않은 상태에서 형제 셋과 함께 돌려 `3 tests completed, 3 failed`였다.\
이 건은 `testRoundingInfoEqualsConsidersAllSerializedFields`가 duration(1000 vs 2000)과 약어("s" vs "sec") 차이를 equals가 무시해 실패했다.\
수정 후 green, 클래스 전체 회귀 없음.\
상세는 [tests.md](tests.md).

## 6. 상태와 교훈

머지 2026-06-19(`5130e384dd8`, `v9.5.0`).\
swallez가 `LGTM. Thanks for the fix!`로 바로 승인했고 코드 변경 요청은 없었다.\
승인 코멘트에 감사 답글만 남겼다.

1. **직렬화 목록과 비교 목록을 표로 세우면 판정이 끝난다.**\
   이 PR은 그 표 한 장이 문제 제기·수정·테스트를 모두 결정했다.\
   해석이 개입할 여지가 없다는 것이 이 렌즈의 강점이다.
2. **형제 검사를 이슈 전에 돌리면 PR이 작아진다.**\
   #151154에서는 검사가 늦어 범위가 중간에 넓어졌고, 이 건에서는 먼저 돌려 "바깥 클래스는 깨끗하다"를 확인한 뒤 작게 올렸다.\
   리뷰 한 번에 승인된 데에는 그 영향도 있었을 것이다.
3. **"지금 재현되지 않는다"와 "고칠 필요가 없다"는 다르다.**\
   이 결함은 상수 관계라는 우연이 가리고 있었다.\
   그 우연은 생성자가 강제하지 않고, 역직렬화 경로는 아예 거치지도 않는다.\
   우연에 기댄 정합은 우연이 깨질 때 조용히 틀린다.
4. **값 객체의 동등성은 생각보다 멀리까지 쓰인다.**\
   빌더에 안 들어간다고 영향이 없는 것이 아니다 - 결과 클래스의 배열 deep-equality가 이 메서드를 그대로 쓴다.
