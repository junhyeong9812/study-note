# PR #151152 - 테스트 해설

> `TimeSeriesAggregationBuilderTests`에 추가된 한 건과, 이 파일이 상속하는 프레임워크
> 테스트가 왜 가드 역할을 못 하는지.\
> 문제와 수정은 [README.md](README.md), 공통 배경은
> [개념 문서](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

배치를 먼저 본다.\
이 결함은 **equals가 필드 하나를 안 본다**는 것이므로, 테스트는 그 필드만 다른 쌍과 그 필드까지 같은 쌍을 나란히 세워야 한다.\
앞쪽이 결함을 red로 만들고, 뒤쪽이 hashCode 계약의 강제 방향을 지킨다.

> **가드 테스트(regression guard)** — 결함을 잡으려고가 아니라, 나중에 다시 깨지지 않게 현재 동작을 못 박아 두는 테스트.\
> 예: 수정 전후 모두 green인 테스트는 결함을 못 잡지만, 미래의 회귀는 막아 준다.

| 무대 | size만 다른 쌍 | 모든 필드가 같은 쌍 |
|---|---|---|
| equals | `assertNotEquals(small, large)` - red | `assertEquals(small, smallCopy)` - 전후 green |
| hashCode | `assertNotEquals(hash, hash)` - red | `assertEquals(hash, hash)` - 전후 green |

네 칸을 그림으로 두면 어느 칸이 결함을 겨누는지가 한눈에 보인다.

```text
                 size 만 다른 쌍          모든 필드가 같은 쌍
               (small 100 / large 200)   (small 100 / smallCopy 100)
            +--------------------------+--------------------------+
   equals   | assertNotEquals          | assertEquals             |
            |   -> fix 전 RED          |   -> 전후 GREEN          |
            +--------------------------+--------------------------+
  hashCode  | assertNotEquals          | assertEquals             |
            |   -> fix 전 RED          |   -> 전후 GREEN          |
            +--------------------------+--------------------------+
              왼쪽 = 결함을 드러낸다        오른쪽 = 과잉 수정을 막는다
```

## T1. testEqualsAndHashCodeConsiderSize - red

추가한 한 건이 네 단언으로 위 표의 네 칸을 채운다.

```java
public void testEqualsAndHashCodeConsiderSize() {
    String name = randomAlphaOfLength(10);
    boolean keyed = randomBoolean();
    TimeSeriesAggregationBuilder small = new TimeSeriesAggregationBuilder(name, keyed, 100);
    TimeSeriesAggregationBuilder large = new TimeSeriesAggregationBuilder(name, keyed, 200);
    assertNotEquals(small, large);
    assertNotEquals(small.hashCode(), large.hashCode());

    // Builders that agree on every field, including size, are equal and hash consistently.
    TimeSeriesAggregationBuilder smallCopy = new TimeSeriesAggregationBuilder(name, keyed, 100);
    assertEquals(small, smallCopy);
    assertEquals(small.hashCode(), smallCopy.hashCode());
}
```
(TimeSeriesAggregationBuilderTests.java:27-39)

- **주장**: `size`만 다른 두 빌더는 같지 않고 해시도 다르며, 모든 필드가 같은 두 빌더는 같고 해시도 같다.
- **fix 전 red인 이유**: 수정 전 `equals`가 `return keyed == that.keyed;`이므로 `name`·`keyed`가 같고 `size`만 다른 두 빌더에서 true가 나온다.\
  실측 실패 메시지는 `Values should be different. Actual: {"ZfFZkojrzT":{"time_series":{"keyed":true,"size":200}}}`다.\
  단언 실패 메시지가 렌더한 JSON에 `size:200`이 찍혀 있는데도 equals는 같다고 한다는 대비가 그대로 드러난다.

**입력 설계가 세 부분으로 나뉜다.** 각각 이유가 다르다.

- `name`과 `keyed`를 **랜덤으로 뽑아 두 빌더가 공유**한다.\
  이렇게 하면 두 빌더가 `size` 말고는 어느 것도 다르지 않다는 것이 구조적으로 보장된다.\
  상수로 고정하지 않고 랜덤을 쓴 것은 이 파일이 속한 ES 테스트 관례(`randomAlphaOfLength`, `randomBoolean`)이고, 특정 이름에 우연히 기대는 테스트가 되지 않게 한다.
- `size`만 **상수 100과 200으로 고정**한다.\
  랜덤 두 값을 뽑으면 우연히 같아져 테스트가 flaky해진다.\
  값이 무엇이든 상관없는 자리이므로 고정이 옳다.
- `smallCopy`는 `small`과 **같은 인자로 다시 만든** 별개 인스턴스다.\
  `small` 자신을 다시 비교하면 `this == o` 단축 경로에 걸려 아무것도 검증하지 못한다.

> **flaky 테스트** — 코드가 그대로인데도 돌릴 때마다 통과·실패가 갈리는 테스트.\
> 예: 랜덤 두 값을 뽑아 "다르다"를 단언하면, 두 값이 우연히 같아지는 날 실패한다.

> **단축 경로(short circuit)** — 본 비교에 들어가기 전에 즉시 결론을 내는 첫 줄.\
> 예: `if (this == o) return true;`는 같은 인스턴스면 필드를 하나도 안 보고 true를 낸다.

**네 단언의 역할이 각각 다르다.**

- `assertNotEquals(small, large)` - 결함을 직접 겨눈다.\
  red를 만드는 단언이 이것이다.
- `assertNotEquals(small.hashCode(), large.hashCode())` - `size`가 hashCode에도 참여함을 본다.\
  엄밀히 말해 hashCode 계약은 "다르면 해시도 달라야 한다"를 요구하지 않으므로 이것은 계약 검증이 아니라 **필드 참여의 관측**이다.\
  flaky 걱정은 없다 - `Objects.hash(super.hashCode(), keyed, size)`에서 `Integer.hashCode(100)`과 `Integer.hashCode(200)`이 결정론적으로 다르고 나머지 인자가 같으므로 결과도 항상 다르다.
- `assertEquals(small, smallCopy)` - 수정이 "이미 같던 것"을 갈라놓지 않았음을 고정한다.\
  필드를 하나 더 보게 만드는 변경이므로 과잉 엄격해질 위험이 있고, 이 단언이 그 방향의 가드다.
- `assertEquals(small.hashCode(), smallCopy.hashCode())` - **hashCode 계약이 실제로 강제하는 유일한 방향**(equal이면 해시도 같다)을 검증한다.\
  앞의 세 단언이 다 통과해도 이 방향이 깨지면 계약 위반이다.

뒤의 세 단언은 처음부터 있던 것이 아니다.\
최초 커밋에는 `assertNotEquals(small, large)` 하나뿐이었고, 리뷰어 swallez가 "메서드 이름에 hashCode가 있는데 hashCode 테스트가 없다"고 지적해 커밋 `d0fb50bffcd`에서 보강했다.\
**이름이 약속한 계약을 실제로 검증하는가**가 이 PR에서 배운 테스트 렌즈다.

## T2. 상속받은 프레임워크 테스트 - 가드는 되지만 결함은 못 잡는다

이 클래스는 `AggregationBuilderTestCase`를 거쳐 `BaseAggregationTestCase`를 상속하므로, `createTestAggregatorBuilder` 하나만 구현하면 직렬화·XContent·shallowCopy 라운드트립 테스트를 공짜로 받는다.

```java
protected TimeSeriesAggregationBuilder createTestAggregatorBuilder() {
    // Size set large enough tests not intending to hit the size limit shouldn't see it.
    return new TimeSeriesAggregationBuilder(randomAlphaOfLength(10), randomBoolean(), randomIntBetween(1000, 100_000));
}
```
(TimeSeriesAggregationBuilderTests.java:16-20)

이 테스트들은 **fix 전후 모두 green**이고, 그래서 회귀 가드로만 기능한다.\
왜 결함을 못 잡는지가 이 PR의 핵심 학습이다.

`testSerialization`이 왜 통과하는지는 경로를 세로로 따라가면 보인다.

```text
  testAgg (keyed=true, size=57000)
        |
        v
  writeTo -> 바이트                  size=57000 이 실린다
        |
        v
  readFrom -> deserialized          size=57000 로 복원된다
        |
        v
  assertEquals(testAgg, deserialized)
        |
        v
  equals (수정 전) : keyed 만 비교    -> true -> GREEN
        ^
        |
    판정자 자신이 결함을 품고 있다
```

- `testEqualsAndHashcode`는 **아무 필드도 변이시키지 않는다.**\
  인자 둘짜리 `checkEqualsAndHashCode`가 세 인자 버전에 변이 함수로 `null`을 넘기고(EqualsHashCodeTestUtils.java:51-53), null이면 변이 블록을 통째로 건너뛴다(:93-103).\
  코드의 TODO 주석은 "name과 boost만 바꾼다"고 적혀 있지만 현재 구현은 그것도 하지 않는다.\
  그러니 이름과 달리 이 테스트는 필드 누락을 원리적으로 잡을 수 없다.
- `testSerialization`은 라운드트립 후 `assertEquals(testAgg, deserialized)`로 판정한다(BaseAggregationTestCase.java:163-165).\
  복원본은 `size`까지 실제로 같으므로 통과하고, **판정자가 결함이 있는 equals 자신**이라 `size`를 무시해도 통과한다.\
  거짓 음성이다.
- `testShallowCopy`·`testPlainDeepCopyEquivalentToStreamCopy`도 같은 이유로 통과한다.

> **변이 함수(mutation function)** — 원본에서 필드 하나를 바꾼 사본을 만들어 주는 함수.\
> 예: `size`만 바꾼 사본을 만들어 "원본과 같지 않다"를 단언해야 필드 누락이 드러난다 - 이 함수가 null이면 그 단언 자체가 실행되지 않는다.

여기서 방향이 갈린다.\
같은 프레임워크 테스트가 **역방향 결함**(equals에는 있는데 직렬화가 안 되는 경우)에서는 즉시 실패한다.\
형제 PR [#151796](../151796-variable-width-histogram-shard-size/tests.md)에서 45건 중 31건이 그렇게 깨졌다.

```text
  이번 결함 (equals 에만 없음)        역방향 결함 (직렬화에만 없음)
+-----------------------------+   +-----------------------------+
| 원본   size=57000           |   | 원본   shard_size=50        |
| 바이트 size=57000 (실린다)   |   | 바이트 (안 실린다)           |
| 복원본 size=57000           |   | 복원본 shard_size=기본값     |
+-----------------------------+   +-----------------------------+
| equals: size 를 안 본다      |   | equals: shard_size 를 본다   |
| -> true -> GREEN            |   | -> false -> RED             |
+-----------------------------+   +-----------------------------+
   라운드트립 테스트가 못 잡는다        라운드트립 테스트가 바로 잡는다
```

결함의 방향이 어느 테스트가 유효한지를 정한다.

## 실측 요약

- **fix 전**: 세 형제 PR의 red 테스트를 한 번에 돌려 `3 tests completed, 3 failed`.\
  이 PR 몫은 `TimeSeriesAggregationBuilderTests.testEqualsAndHashCodeConsiderSize`이고 실패 메시지는 `Values should be different. Actual: {...time_series:{keyed:true,size:200}}`였다.\
  (이때 프로덕션 코드는 손대지 않은 상태였다 - red가 진짜 결함을 가리키는지 먼저 확인했다.)
- **fix 후**: 같은 테스트 green, 클래스 전체 회귀 없음(`BUILD SUCCESSFUL`, 약 34초).
- **리뷰 대응 후**: `:modules:aggregations:test` + `:modules:aggregations:spotlessJavaCheck` 둘 다 `BUILD SUCCESSFUL`.
- **diff 규모**: 프로덕션 2줄(`equals`·`hashCode` 각 한 줄) + 테스트 1건 + changelog YAML 1건.

> 빌드 종료 코드 해석 주의: 최초 red 실행에서 gradle 출력을 `| tail`로 파이프해 종료
> 코드가 가려졌다(tail의 0이 잡혔다).\
> 실제 결과는 출력의 `BUILD FAILED`/`3 failed`다.\
> 이후 실행부터는 파이프를 걷어냈다.

> **exit 마스킹** — 파이프 뒤 명령의 종료 코드가 앞 명령의 실패를 덮어 가리는 것.\
> 예: `gradle test | tail`은 gradle이 실패해도 `tail`이 성공하므로 전체 종료 코드가 0이 된다.
