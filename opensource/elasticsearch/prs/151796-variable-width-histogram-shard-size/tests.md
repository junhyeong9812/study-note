# PR #151796 - 테스트 해설

> 신규 파일 `VariableWidthHistogramTests` 하나. 프레임워크가 공짜로 주는 네 테스트와
> 우리가 직접 쓴 한 건으로 나뉜다. 문제와 수정은 [README.md](README.md), 전파 경로는
> [structure.md](structure.md), 공통 배경은
> [개념 문서](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

배치를 먼저 본다. 이 결함은 **역방향**(동등성에는 있고 직렬화에 없는 경우)이라 형제 PR
셋과 정반대의 테스트가 유효하다. 저쪽은 "누락 필드만 다른 not-equal" 단언을 새로 써야
했지만, 이쪽은 **프레임워크의 라운드트립 테스트만 있으면 저절로 깨진다.** 그래서 이
PR의 테스트 설계는 "무엇을 새로 단언할까"가 아니라 **"프레임워크 테스트가 두 필드를
실제로 흔들게 만들려면 무엇을 랜덤화해야 하나"** 였다.

| 무대 | 담당 | 방향 |
|---|---|---|
| wire·XContent·clone 라운드트립 | 프레임워크 4테스트 (상속) | red -> green |
| 구버전으로 보낼 때의 드롭 분기 | `testSerializationBeforeShardSizeSupport` (직접 작성) | 게이트 else 분기 고정 |

## T1. createTestAggregatorBuilder - 프레임워크에 red를 만들어 주는 입력

이 파일이 하는 일의 대부분은 단언이 아니라 **입력 생성**이다.

```java
@Override
protected VariableWidthHistogramAggregationBuilder createTestAggregatorBuilder() {
    VariableWidthHistogramAggregationBuilder factory = new VariableWidthHistogramAggregationBuilder(randomAlphaOfLengthBetween(3, 10));
    factory.field(INT_FIELD_NAME);
    if (randomBoolean()) {
        factory.setNumBuckets(randomIntBetween(1, 1000));
    }
    if (randomBoolean()) {
        // shard_size must be greater than 1
        factory.setShardSize(randomIntBetween(2, 10000));
    }
    if (randomBoolean()) {
        // initial_buffer must be greater than 0
        factory.setInitialBuffer(randomIntBetween(1, 50000));
    }
    return factory;
}
```
(VariableWidthHistogramTests.java:22-38)

`BaseAggregationTestCase`는 이 메서드 하나만 구현하면 네 테스트를 자동으로 준다.

- `testSerialization` - 스트림 왕복 후 `assertEquals(원본, 복원본)`과 해시 일치, 그리고
  왕복 후 XContent 문자열이 같은지(BaseAggregationTestCase.java:157-172).
- `testFromXContent` - XContent 출력을 다시 파싱해 원본과 비교.
- `testShallowCopy` - `shallowCopy` 후 `assertEquals(원본, 복제본)`(:187-192).
- `testPlainDeepCopyEquivalentToStreamCopy` - deep copy와 stream copy의 동등성(:194-201).

**세 `randomBoolean()` 가드가 설계의 전부다.** 두 필드를 항상 설정하면 "미설정(-1)"
상태가 한 번도 테스트되지 않고, 항상 설정하지 않으면 결함이 재현되지 않는다. 절반씩
섞이므로 반복 실행에서 설정·미설정 조합이 모두 나오고, **센티넬 `-1`의 왕복 보존까지
같은 테스트가 검증**한다. 값 범위는 setter 제약을 그대로 따랐다(`shard_size`는 2 이상,
`initial_buffer`는 1 이상).

`build()`가 호출되지 않는다는 점도 알고 쓴 것이다. `BaseAggregationTestCase`는 빌더만
다루고 `innerBuild`를 부르지 않으므로, `innerBuild`의 교차 검증
(`initialBuffer >= numBuckets`, `3/4 * shard_size >= buckets`)을 만족시킬 필요가 없다.
그 제약까지 맞추려 했다면 랜덤 범위가 훨씬 좁아졌을 것이다.

**red 실측이 예측과 정확히 맞았다.** 수정 전 실행에서 **45개 중 31개 실패**했고, 통과한
것은 `testToString` 계열뿐이었다. 실패 목록이 `testSerialization`·`testFromXContent`·
`testShallowCopy`와 그 multi 변종들이라 **세 전파 경로가 각각 자기 몫의 실패를 냈다** -
"한 경로만 고치면 나머지가 남는다"는 진단이 테스트 결과로 그대로 확인된 셈이다.

왜 이 라운드트립이 깨지는지는 한 줄이다. 복원본의 `shardSize`가 `-1`로 돌아오는데
`equals`는 그 필드를 비교하므로(README 2절), `assertEquals(원본, 복원본)`이 실패한다.
**형제 PR 셋에서는 같은 단언이 거짓 음성이었지만**
([개념 문서 4절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)),
방향이 뒤집히면 같은 단언이 결함을 정면으로 잡는다.

## T2. testSerializationBeforeShardSizeSupport - 구버전 드롭 분기

프레임워크 테스트는 현재 버전끼리의 왕복만 본다. 즉 새로 세운 버전 게이트의 `true`
분기만 타고 **`else` 분기(구버전으로 보내 두 필드를 생략하는 경로)는 한 번도 실행되지
않는다.** 교차 검증이 이 사각을 지적했고, 채택해 추가한 것이 이 테스트다.

```java
public void testSerializationBeforeShardSizeSupport() throws IOException {
    TransportVersion before = TransportVersionUtils.getPreviousVersion(
        TransportVersion.fromName("variable_width_histogram_shard_size")
    );
    VariableWidthHistogramAggregationBuilder original = new VariableWidthHistogramAggregationBuilder("test");
    original.field(INT_FIELD_NAME);
    original.setNumBuckets(7);
    original.setShardSize(123);
    original.setInitialBuffer(456);

    VariableWidthHistogramAggregationBuilder deserialized = (VariableWidthHistogramAggregationBuilder) copyNamedWriteable(
        original,
        namedWriteableRegistry(),
        AggregationBuilder.class,
        before
    );

    // buckets survives, but shard_size/initial_buffer are dropped and resolve to the defaults derived from buckets
    assertEquals(7 * 50, deserialized.getShardSize());
    assertEquals(Math.min(10 * (7 * 50), 50000), deserialized.getInitialBuffer());
}
```
(VariableWidthHistogramTests.java:45-65)

- **주장**: 게이트를 모르는 구버전 노드로 직렬화하면 두 필드가 생략되고, 수신 측은
  `-1` 폴백으로 기본값을 계산한다. 예외는 나지 않는다.
- **핵심 장치는 `getPreviousVersion(fromName(...))`이다.** 이름으로 우리 게이트 버전을
  얻고 그 **직전** 버전을 뽑으면, `supports(...)`가 반드시 false가 되어 `else` 분기가
  강제된다. 버전 상수를 손으로 적지 않는 것이 중요하다 - id는 gradle이 생성하고 충돌 시
  재생성되므로(README 6절), 코드가 id를 알면 그때마다 테스트가 깨진다.
- **`copyNamedWriteable(..., before)`** 는 지정한 전송 버전으로 직렬화·역직렬화하는 테스트
  헬퍼다. 실제 클러스터를 띄우지 않고 버전 협상 결과만 흉내 낸다.

**단언이 getter를 보는 이유.** 원시 필드는 package-private이 아니라 private이므로 직접
읽을 수 없고, 애초에 확인하고 싶은 것이 "드롭된 뒤 기본값으로 폴백하는가"다. 그래서
`getShardSize()`가 `numBuckets * 50`을 반환하는지 본다. `numBuckets`를 7로 잡은 것도
계산이 눈으로 검산되게 하려는 것이다 - `7 * 50 = 350`, `min(10 * 350, 50000) = 3500`.

**이 두 단언이 세 가지를 한꺼번에 고정한다.** 두 필드가 실제로 드롭됐다는 것(설정한
123·456이 아니다), 수신 측이 예외 없이 폴백한다는 것, 그리고 **`numBuckets`는 게이트
밖이라 보존된다**는 것이다. 마지막이 중요하다 - 기본값 계산이 `numBuckets`에서 나오므로,
`350`이라는 값 자체가 "7이 살아남았다"의 증거다. 기존 wire 포맷을 건드리지 않았음을
이 한 줄이 확인한다.

주석에 "buckets survives, but shard_size/initial_buffer are dropped"라고 적어 둔 것은
숫자만 보고는 의도가 안 읽히기 때문이다.

## 실측 요약

- **fix 전**: 신규 테스트 **45개 중 31개 실패**. `testSerialization`·`testFromXContent`·
  `testShallowCopy`와 multi 변종이 실패하고 `testToString`만 통과 - 세 전파 경로가
  각각 실패를 냈다. (테스트를 구현 diff 없이 명세만 보고 먼저 작성한 상태에서 실행했다.)
- **fix 후**: `./gradlew :server:spotlessJavaCheck :server:test --tests '*VariableWidthHistogramTests'
  --tests '*VariableWidthHistogramAggregatorTests' -Dtests.iters=10` -> `BUILD SUCCESSFUL`.
  `-Dtests.iters=10`으로 랜덤 조합을 열 번 돌려 설정·미설정 경우가 모두 지나가게 했다.
- **교차 검증 후**: `testSerializationBeforeShardSizeSupport` 추가 후 재실행
  `BUILD SUCCESSFUL`.
- **diff 규모**: 프로덕션 1파일(5편집) + 테스트 신규 1파일 + gradle 생성 리소스 2개 +
  changelog YAML 1건.

## 남는 것

이 빌더는 이제 라운드트립 테스트를 갖게 됐고, 그것이 이 PR의 **재발 방지 장치**다.
앞으로 누가 이 빌더에 필드를 더하면서 `innerWriteTo`를 빠뜨리면 `testSerialization`이
즉시 실패한다. 반대로 **정방향 결함**(직렬화는 되는데 동등성에서 빠지는 경우)은 이
테스트가 여전히 못 잡는다 - 그쪽은 형제 PR 셋처럼 누락 필드만 다른 not-equal 단언을
따로 써야 한다.
