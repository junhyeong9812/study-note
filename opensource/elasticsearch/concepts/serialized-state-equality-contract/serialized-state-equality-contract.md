# 직렬화 필드와 동등성의 정합 계약 - 집계 빌더의 상태 네 면

## 0. 정향

이 문서는 Elasticsearch 집계 빌더(`AggregationBuilder`)에서 반복해 나온 한 종류의 결함,
즉 **한 필드가 어떤 복제 경로에는 실리고 어떤 경로에는 안 실리는 비대칭**을 설명한다.
아카이브의 PR 네 건이 전부 이 결함의 변종이고, 그래서 각 PR 문서가 공유하는 배경을
여기 한 번만 적는다. 다 읽으면 "무엇을 정답지로 삼아 equals를 채점하는가", "왜 이
결함이 예외를 만들지 않는가", "왜 어떤 변종은 두 줄로 고쳐지고 어떤 변종은 전송
프로토콜 버전을 새로 발급해야 하는가"를 설명할 수 있어야 한다.

기준 코드는 upstream `main`(2026-09-08 시점)이고, 인용한 file:line은 네 PR이 모두
반영된 뒤의 좌표다.

## 1. 계약 - "의미 있는 상태"의 정답지는 writeTo다

자바의 `equals`/`hashCode` 계약은 두 문장으로 요약된다. `a.equals(b)`면
`a.hashCode() == b.hashCode()`여야 하고(역은 요구되지 않는다), "논리적으로 같다"의
기준은 그 객체의 **의미 있는 상태 전체**여야 한다. 문제는 두 번째 문장이 클래스마다
해석이 갈린다는 점이다. 어떤 필드가 "의미 있는 상태"인지는 자바가 정해 주지 않는다.

집계 빌더에는 그 해석이 코드에 이미 적혀 있다. 빌더는 좌표 노드에서 데이터 노드로
`StreamOutput`에 실려 건너가고 데이터 노드가 `StreamInput` 생성자로 복원한다. 즉
**`writeTo`/`StreamInput` 생성자가 싣는 필드 목록이 "이 객체가 무엇인가"의 정의**이고,
그 목록이 equals의 정답지다. 이 문장을 뒤집으면 결함의 판별식이 나온다.

> 직렬화되는 필드가 서로 다르면 두 빌더는 서로 다른 요청이다. 따라서 equals로 같으면 안 된다.

이 판별식은 기계적으로 적용된다. 클래스를 열어 `writeTo`가 쓰는 필드를 세고,
`equals`가 비교하는 필드를 세서 차집합을 보면 된다. 아카이브의 PR 세 건(#151152,
#151154, #151156)이 정확히 이 방법으로 발견됐다.

## 2. 상태의 네 면 - 같은 필드를 네 번 복제한다

집계 빌더의 한 필드는 서로 **독립된** 네 경로로 복제된다. 네 경로는 코드를 공유하지
않으므로, 한 곳을 고쳐도 나머지 세 곳은 여전히 빠져 있을 수 있다.

| 면 | 담당 메서드 | 언제 쓰이나 |
|---|---|---|
| wire | `doWriteTo`/`innerWriteTo` + `StreamInput` 생성자 | 좌표 노드 -> 데이터 노드 hop |
| clone | `shallowCopy`가 부르는 clone 생성자 | 좌표 노드 안의 rewrite |
| XContent | `internalXContent`/`doXContentBody` + 파서 | 요청 재렌더·`toString`·round-trip |
| 동등성 | `equals`/`hashCode` | 요청·결과 비교 |

새 필드를 추가하는 기능 PR은 보통 파서·setter·wire·XContent까지는 갱신하고 동등성만
빠뜨린다. `time_series`의 `size`가 그랬다 - upstream #93496이 필드를 넣으면서
`equals`/`hashCode`를 갱신하지 않았다. 반대 방향도 있다. `variable_width_histogram`의
`shard_size`는 동등성에는 들어 있는데 wire·clone·XContent 셋에서 빠져 있었다.

## 3. 두 방향 - 정방향 결함과 역방향 결함

같은 "비대칭"이지만 방향에 따라 증상도 수정 비용도 다르다.

| | 정방향 (직렬화 O, equals X) | 역방향 (equals O, 직렬화 X) |
|---|---|---|
| 아카이브 사례 | #151152 · #151154 · #151156 | #151796 |
| 증상 | 다른 요청이 같다고 판정된다 | 파라미터가 데이터 노드에 도달하지 못해 무동작한다 |
| 사용자 가시성 | 없음(조용함) | 있음(설정이 무시된다) |
| 수정 범위 | equals·hashCode 두 줄 | wire 포맷 변경 -> TransportVersion 신규 발급 |
| 잡는 테스트 | 누락 필드만 다른 not-equal 단언 | 직렬화 round-trip |

역방향이 더 위험하다. 좌표 노드는 두 요청을 "다르다"고 보는데 데이터 노드는 둘 다
기본값으로 실행하므로, **판단하는 쪽과 실행하는 쪽의 인식이 어긋난다**. 그리고 고치려면
전송 바이트가 늘어나므로 롤링 업그레이드 중 구버전 노드와의 호환을 따로 설계해야 한다.

## 4. 왜 기존 테스트가 못 잡았나

집계 빌더의 공통 테스트 베이스 `BaseAggregationTestCase`는 이름만 보면 이 결함을
잡아 줄 것 같다. 실제로는 두 테스트 모두 정방향 결함에 무력하다.

`testEqualsAndHashcode`는 변이 함수를 넘기지 않는다.

```java
public void testEqualsAndHashcode() throws IOException {
    // TODO we only change name and boost, we should extend by any sub-test supplying a "mutate" method that randomly changes one
    // aspect of the object under test
    checkEqualsAndHashCode(createTestAggregatorBuilder(), this::copyAggregation);
}
```
(test/framework BaseAggregationTestCase.java:181-185)

인자가 둘뿐인 `checkEqualsAndHashCode`는 세 인자 버전에 `null`을 넘기고
(EqualsHashCodeTestUtils.java:51-53), 변이 함수가 null이면 변이 블록 자체를 건너뛴다
(:93-103). 즉 이 테스트가 확인하는 것은 자기 자신과 같다·null과 다르다·복사본과
같다뿐이고, **필드 하나를 바꿔도 다른가는 한 번도 묻지 않는다.** 코드의 TODO 주석은
"name과 boost만 바꾼다"고 적혀 있지만 현재 구현은 아무것도 변이시키지 않는다.

`testSerialization`은 라운드트립을 하지만 판정 기준이 equals다.

```java
AggregationBuilder deserialized = in.readNamedWriteable(AggregationBuilder.class);
assertEquals(testAgg, deserialized);
assertEquals(testAgg.hashCode(), deserialized.hashCode());
```
(BaseAggregationTestCase.java:163-165)

정방향 결함에서는 원본과 복원본이 그 필드까지 실제로 같으므로 통과하고, 설령 equals가
그 필드를 무시해도 통과한다 - **채점자와 피채점자가 같은 오류를 공유하는 거짓 음성**이다.
반대로 역방향 결함에서는 이 단언이 곧바로 깨진다. 복원본의 필드가 기본값으로 돌아왔는데
equals는 그 필드를 보기 때문이다. #151796에서 신규 테스트 45건 중 31건이 실패한 이유가
이것이다.

정리하면 이렇다. **정방향 결함은 "누락 필드만 다른 not-equal 단언"을 새로 써야 잡히고,
역방향 결함은 직렬화 round-trip 테스트만 있으면 잡힌다.** 후자가 아예 없던 빌더가
#151796의 무대였다.

## 5. 증상의 크기 - 소비자를 실제로 세어 본다

"equals가 틀리면 캐시 키가 틀린다"는 설명은 직관적이지만, 이 코드베이스에서는 절반만
맞다. 샤드 요청 캐시의 키는 equals가 아니라 **직렬화한 바이트의 SHA-256 다이제스트**다.

```java
public BytesReference cacheKey(CheckedBiConsumer<ShardSearchRequest, StreamOutput, IOException> differentiator) throws IOException {
    BytesStreamOutput out = scratch.get();
    try {
        this.innerWriteTo(out, true);
        ...
        return new BytesArray(MessageDigests.digest(out.bytes(), MessageDigests.sha256()));
```
(server ShardSearchRequest.java:547-554)

그래서 정방향 결함이 있어도 요청 캐시가 두 요청을 섞지는 않는다 - 직렬화 바이트가
다르기 때문이다. 이 관계를 뒤집으면 오히려 **역방향 결함이 캐시에 위험하다**. 직렬화
바이트가 같으면(파라미터가 안 실리므로) 서로 다른 두 요청이 같은 캐시 키를 갖는다.

정방향 결함의 실제 소비자는 그보다 좁다. 첫째, 요청 동등성이다. 빌더 equality는
`AggregatorFactories.Builder.equals`(server AggregatorFactories.java:618-625)를 거쳐
`SearchSourceBuilder.equals`(:2176)와 `SearchRequest.equals`(:927)로 올라간다. 둘째,
결과 동등성이다. `RoundingInfo`는 `InternalAutoDateHistogram.BucketInfo`가
`Objects.deepEquals`로 비교하므로(InternalAutoDateHistogram.java:161) reduce 경로의
결과 비교에 직접 참여한다. 셋째, 테스트 프레임워크의 라운드트립 단언 자체다.

그러니 정방향 결함의 정직한 서술은 이렇다. **당장 사용자 데이터를 망가뜨리는 결함은
아니지만, "이 객체가 무엇인가"의 정의가 코드 안에서 두 갈래로 갈라진 상태**이고, 그
정의를 믿고 쓰는 상위 계층이 언제 늘어날지는 아무도 보장하지 않는다. 업스트림
메인테이너가 세 건을 모두 `>bug`로 라벨링하고 엿새 만에 머지한 것도 그 판단으로 읽힌다.

## 6. 고치는 법 - 방향에 따라 비용이 갈린다

정방향은 누락 필드를 equals와 hashCode 양쪽에 더하면 끝난다. 비교 형태는 필드 타입이
정한다. primitive는 `==`(`size == that.size`, `roughEstimateDurationMillis == other.roughEstimateDurationMillis`),
enum도 `==`(`multiValueMode == other.multiValueMode`), 참조 타입은 `Objects.equals`,
배열은 `Objects.deepEquals` + `Arrays.hashCode`. **equals에 넣은 필드는 반드시
hashCode에도 넣는다** - 그러지 않으면 계약이 실제로 강제하는 방향(같으면 해시도 같다)이
깨진다.

역방향은 wire를 건드려야 하므로 절차가 하나 더 붙는다. 새 필드를 무조건 쓰면 구버전
노드가 모르는 바이트를 만나 스트림이 깨지므로, `TransportVersion.fromName(...)`으로
기능 이름을 선언하고 `getTransportVersion().supports(...)` 게이트 안에서만 읽고 쓴다.
읽기와 쓰기가 **같은 게이트·같은 순서**여야 한다는 것이 이 패턴의 핵심 불변식이다.
자세한 것은 [#151796 실구조](../../prs/151796-variable-width-histogram-shard-size/structure.md) 3-4절.

## 7. 네 PR 대조

같은 렌즈로 찾은 네 건을 한 표에 세우면 변종의 지도가 된다.

| PR | 클래스 | 어긋난 필드 | 방향 | 원인 유형 |
|---|---|---|---|---|
| #151152 | `TimeSeriesAggregationBuilder` | `size` | 정방향 | 기능 PR이 동등성만 안 따라갔다 |
| #151154 | `ArrayValuesSourceAggregationBuilder` | `missingMap` | 정방향 | 이름이 비슷한 죽은 필드를 대신 비교했다 |
| #151154 | `MatrixStatsAggregationBuilder` | `multiValueMode` | 정방향 | 서브클래스가 equals를 오버라이드하지 않았다 |
| #151156 | `AutoDateHistogramAggregationBuilder.RoundingInfo` | `roughEstimateDurationMillis`·`unitAbbreviation` | 정방향 | 다섯 중 셋만 비교했다 |
| #151796 | `VariableWidthHistogramAggregationBuilder` | `shardSize`·`initialBuffer` | 역방향 | 전파 경로 세 곳을 다 빠뜨렸다 |

원인 유형이 넷으로 갈린다는 점이 이 표의 요점이다. **"필드를 안 넣었다"만이 원인이
아니다.** 이름이 비슷한 죽은 필드를 대신 비교하거나(#151154 missingMap), 상속으로
받은 부모 equals가 자식 필드를 모르거나(#151154 multiValueMode) 하는 경우는 클래스
하나만 봐서는 안 보이고, 부모·자식과 실제 직렬화 목록을 같이 놓아야 보인다. 그래서
수정할 때마다 **형제 검사**(같은 계층의 다른 필드·다른 서브클래스에도 같은 누락이
있는가)를 한 번씩 돌리는 것이 이 시리즈에서 굳어진 절차다. #151154의 `multiValueMode`가
그 검사에서 나왔고, #151156은 검사를 먼저 돌리고 이슈를 열었다.

## 8. 남은 후보

같은 렌즈로 쓸어 본 결과는 작업 repo의
`docs/plans/2026-06-20/agg-serialization-equals-research/task.md`에 남아 있다. 실코드로
확인한 것과 서브에이전트 보고만 있는 것이 섞여 있으므로, 착수 전 실코드 재확인이
필요하다는 단서를 붙여 옮긴다.

- 실코드 확인됨: `IpPrefixAggregationBuilder`(`appendPrefixLength`·`keyed`),
  `RangeQueryBuilder`(`relation`), `MultiTermsAggregationBuilder`(`showTermDocCountError`).
- grep 수준 확인: `TopMetricsAggregationBuilder`·`TTestAggregationBuilder`·
  `GeoLineAggregationBuilder` - equals/hashCode 자체가 없어 자기 필드 전부가 무시된다.
- 미교차확인: `InternalAutoDateHistogram.targetBuckets`, `InternalTimeSeries`의
  top-level equals 부재. 둘 다 빌더가 아니라 결과(`Internal*`) 클래스라 범주가 다르다.
