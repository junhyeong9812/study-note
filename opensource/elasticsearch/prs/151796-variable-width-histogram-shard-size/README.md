# PR #151796 - variable_width_histogram의 shard_size·initial_buffer 직렬화

## 0. 정향

이 문서는 `variable_width_histogram` 집계의 튜닝 파라미터 두 개가 **사용자가 설정해도
데이터 노드에 도달하지 못해 사실상 무동작이던** 결함의 해설이다.\
앞선 세 건과 결함의 방향이 반대다 - 저쪽은 직렬화되는 필드가 동등성에서 빠진 경우였고,
이쪽은 **동등성에는 있는데 직렬화가 안 되는** 경우다.\
방향이 뒤집히면 증상도 수정 비용도 달라진다.\
사용자 눈에 보이는 오동작이 생기고, 고치려면 전송 포맷을 바꿔야 하므로 롤링 업그레이드
호환을 설계해야 한다.\
다 읽으면 "왜 이 방향이 더 위험한가", "왜 -1을 `writeVInt`로 보내면 안 되는가",
"구버전 노드로 보낼 때 무엇이 안전한 degrade인가"를 설명할 수 있어야 한다.

> **동등성(equality)** — 두 객체를 "같은 것"으로 볼지 판정하는 규칙. 자바에서는
> `equals`/`hashCode`가 정한다.\
> 예: `shard_size`가 200인 요청과 400인 요청을 `equals`가 같다고 하면, 요청을 비교하는
> 코드는 서로 다른 둘을 하나로 본다.

> **직렬화(serialization)** — 객체를 바이트로 펴서 다른 곳에 보내고, 받은 쪽이 다시
> 객체로 되살리는 것.\
> 예: 좌표 노드가 만든 집계 빌더를 바이트로 바꿔 데이터 노드로 보내면, 데이터 노드가
> 그 바이트로 같은 빌더를 다시 만든다.

상태: **리뷰 대기**(2026-06-20 제출, `>bug`·`Team:Analytics`·`v9.6.0` 라벨).\
이슈 #151795를 닫는 PR이다.\
브랜치 신선도에 대한 관찰은 6절에 있다.

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md).\
착수 분석은 별도 문서 [analysis.md](analysis.md)로 두었다 - 대안 비교표와 리스크 판정이
그 내용이다.\
개념 문서: [직렬화 필드와 동등성의 정합 계약](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

## 1. 배경 - 두 파라미터는 제대로 구현돼 있었다

`variable_width_histogram`은 고정 폭이 아니라 데이터 분포에 맞춰 폭이 다른 버킷을
만드는 집계다.\
정확도와 비용을 조절하는 파라미터 둘을 받는다.

> **가변 폭 히스토그램(variable width histogram)** — 구간 폭을 미리 고정하지 않고 데이터가
> 몰린 모양에 맞춰 버킷 경계를 정하는 집계.\
> 예: 값이 0 근처에 촘촘하고 멀리 드문드문 있으면, 앞쪽은 좁은 버킷 여럿으로 뒤쪽은
> 넓은 버킷으로 나뉜다.

- `shard_size` - 각 샤드가 유지할 버킷 수.\
  크면 정확하고 비싸다.
- `initial_buffer` - 샤드에서 초기에 버퍼링할 문서 수.\
  메모리와 직결된다.

> **샤드(shard)** — 인덱스를 쪼개 여러 노드에 나눠 둔 조각. 검색과 집계는 샤드마다 따로
> 돌고 그 결과를 합친다.\
> 예: `shard_size`는 전체가 아니라 **샤드 하나가** 유지할 버킷 수를 정하는 값이다.

두 파라미터는 겉보기에 완전히 구현돼 있다.\
파서가 받고(:59-60), setter가 값을 검증하고(`shard_size`는 1 이하를, `initial_buffer`는
0 이하를 거부한다 - :110-125), 데이터 노드의 `innerBuild`가 실제로 소비해 팩토리에
넘긴다(:172-173, :208-219).

미설정 상태는 `-1` 센티넬로 표현하고, getter가 그때 기본값을 계산한다.

> **센티넬 값(sentinel value)** — "값이 없음"을 나타내려고 정상 범위 밖의 값 하나를
> 골라 쓰는 표현법.\
> 예: `shard_size`는 2 이상만 유효하므로 `-1`을 "사용자가 설정하지 않았다"는 뜻으로 쓴다.

```java
public int getShardSize() {
    if (shardSize == -1) {
        return numBuckets * 50;
    }
    return shardSize;
}

public int getInitialBuffer() {
    if (initialBuffer == -1) {
        return Math.min(10 * getShardSize(), 50000);
    }
    return initialBuffer;
}
```
(server VariableWidthHistogramAggregationBuilder.java:127-139)

즉 **필드가 담는 것은 "사용자가 준 값 또는 미설정"이라는 원시 상태**이고, "실제로 쓸
값"은 저장하지 않고 매번 계산한다.\
이 구분이 뒤에서 수정 방식을 결정한다.

## 2. 수정 전 동작 - 세 전파 경로가 전부 numBuckets만 날랐다

문제는 이 두 필드가 빌더 밖으로 나가는 세 경로 어디에도 실리지 않았다는 것이다.

| 경로 | 수정 전 | 결과 |
|---|---|---|
| wire (`innerWriteTo` / `StreamInput` 생성자) | `numBuckets`만 | 좌표 노드 -> 데이터 노드 hop에서 두 필드가 `-1`로 리셋 |
| clone (`shallowCopy`의 생성자) | `numBuckets`만 | 좌표 노드 안의 rewrite만으로도 유실 |
| XContent (`doXContentBody`) | `numBuckets`만 | XContent 왕복 시 유실 |

> **wire** — 노드와 노드 사이로 실제 바이트가 오가는 전송 경로.\
> 예: 좌표 노드가 `innerWriteTo`로 쓴 바이트를 데이터 노드가 `StreamInput` 생성자로 읽는다.

> **XContent** — 엘라스틱서치가 JSON 같은 구조화 문서를 읽고 쓰는 공용 표현. 요청을
> 다시 JSON으로 렌더하거나 그 JSON을 다시 파싱하는 데 쓴다.\
> 예: `doXContentBody`가 빌더를 JSON으로 찍고, `PARSER`가 그 JSON을 다시 빌더로 만든다.

> **좌표 노드(coordinating node)와 데이터 노드(data node)** — 요청을 받아 흩뿌리고 결과를
> 모으는 노드가 좌표 노드, 자기 샤드에서 실제로 집계를 돌리는 노드가 데이터 노드다.\
> 예: 사용자가 준 `shard_size`는 좌표 노드에서 파싱되고, 그것을 쓰는 `innerBuild`는
> 데이터 노드에서 돈다.

사용자가 넣은 값이 어디서 사라지는지를 한 줄기로 따라가면 이렇다.

```text
요청 JSON
  "variable_width_histogram": { "buckets": 10,
                                "shard_size": 200,
                                "initial_buffer": 5000 }
        |
        v  PARSER.declareInt   :59-60
+---------------------------------------------+
| 빌더 (좌표 노드)                             |
|   numBuckets    = 10                        |
|   shardSize     = 200    <- 사용자 값        |
|   initialBuffer = 5000   <- 사용자 값        |
+---------------------------------------------+
        |
        v  innerWriteTo - numBuckets 만 싣는다
   [ wire 바이트: numBuckets=10 ]
        |
        v  StreamInput 생성자
+---------------------------------------------+
| 빌더 (데이터 노드)                            |
|   numBuckets    = 10                        |
|   shardSize     = -1     <- 리셋됨           |
|   initialBuffer = -1     <- 리셋됨           |
+---------------------------------------------+
        |
        v  innerBuild   :172-173
   getShardSize()     -> -1 이므로 numBuckets * 50
   getInitialBuffer() -> -1 이므로 min(10 * getShardSize(), 50000)
        |
        v
   VariableWidthHistogramAggregatorFactory 가 기본값으로 실행   :208-219
```

세 경로는 서로 독립이므로 하나만 고쳐서는 안 된다 - 그 독립성은
[structure.md](structure.md)에 그렸다.

그런데 **`equals`/`hashCode`에는 두 필드가 들어 있었다.**

```java
@Override
public int hashCode() {
    return Objects.hash(super.hashCode(), numBuckets, shardSize, initialBuffer);
}
```
(:234-237)

이 조합이 이 결함의 성격을 정한다.\
좌표 노드는 `shard_size`가 다른 두 요청을 "다르다"고 판정하는데, 데이터 노드는 둘 다
기본값으로 실행한다.\
**판단하는 쪽과 실행하는 쪽의 인식이 어긋난 상태**다.

```text
좌표 노드가 보는 것 (equals)            데이터 노드가 하는 것 (innerBuild)
+-----------------------------+        +-----------------------------+
| 요청 A: shard_size = 200    |        | A: shardSize = -1           |
| 요청 B: shard_size = 400    |        | B: shardSize = -1           |
| equals -> "서로 다른 요청"  |        | 둘 다 numBuckets * 50 로 실행 |
+-----------------------------+        +-----------------------------+
  -> 다르다고 판정한 두 요청이 실제로는 똑같이 실행된다
```

## 3. 문제 - 사용자가 설정한 값이 조용히 무시된다

증상은 앞선 세 건과 달리 사용자에게 보인다.\
문서에 있는 파라미터를 요청에 넣어도 집계 결과가 달라지지 않는다.\
왜 그런지는 `getShardSize`의 폴백을 보면 한 줄로 드러난다 - 역직렬화 후 `shardSize`가
`-1`로 돌아오므로 getter가 `numBuckets * 50`을 반환하고, 사용자 값은 증발한다.

```text
수정 전 (wire 에 두 필드가 없다)          수정 후 (버전 게이트 안에 실린다)
+--------------------------------+      +--------------------------------+
| 요청: shard_size = 200         |      | 요청: shard_size = 200         |
| wire: numBuckets 만            |      | wire: numBuckets + shardSize   |
| 데이터 노드: shardSize = -1    |      | 데이터 노드: shardSize = 200   |
| getShardSize() = numBuckets*50 |      | getShardSize() = 200           |
+--------------------------------+      +--------------------------------+
  -> 사용자 값이 조용히 증발한다            -> 파라미터가 실제로 동작한다
```

**왜 이 방향이 더 까다로운가.**\
흔한 직렬화-동등성 결함은 정방향이라 equals 두 줄을 고치면 끝난다.\
이 건은 wire에 필드를 **추가**해야 하므로 전송 바이트가 늘어나고, 그러면 구버전 노드가
모르는 바이트를 만나 스트림이 깨진다.\
즉 롤링 업그레이드 호환(BWC)이 수정의 일부가 된다.

> **롤링 업그레이드 호환(BWC, backward compatibility)** — 클러스터를 한 노드씩 올리는
> 동안 신버전 노드와 구버전 노드가 섞여 돌아도 통신이 깨지지 않아야 한다는 제약.\
> 예: 신버전이 필드 둘을 더 보내는데 구버전이 그 바이트를 모르면, 받는 쪽이 엉뚱한
> 자리에서 값을 읽어 스트림이 깨진다.

**왜 아무도 못 잡았나.**\
이 빌더에는 직렬화·XContent 테스트가 **아예 없었다.**\
집계 빌더의 프레임워크 베이스 `BaseAggregationTestCase`는 `createTestAggregatorBuilder`
하나만 구현하면 라운드트립 테스트 네 개를 자동으로 주는데, 이 빌더는 그 하위 테스트
클래스 자체가 없었다.\
역방향 결함은 그 라운드트립 테스트만 있으면 즉시 잡히므로
([개념 문서 4절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)),
**테스트의 부재가 곧 근본 원인**이었다.

> **라운드트립(round-trip)** — 객체를 바이트나 JSON으로 바꿨다가 다시 객체로 되돌린 뒤,
> 원본과 같은지 보는 검사.\
> 예: 빌더를 스트림에 쓰고 다시 읽어 `assertEquals(원본, 복원본)`을 하면 전송 중에 잃은
> 필드가 드러난다.

## 4. 수정 해설 - 네 자리를 채우고 버전 게이트를 세운다

빌더 한 파일에 다섯 편집(TransportVersion 선언 + 네 경로)과, gradle이 생성하는 리소스
두 개다.

**(a) 전송 버전 이름 선언.**

```java
private static final TransportVersion VARIABLE_WIDTH_HISTOGRAM_SHARD_SIZE = TransportVersion.fromName(
    "variable_width_histogram_shard_size"
);
```
(:48-50)

> **TransportVersion(전송 버전)** — 노드 간 전송 포맷의 능력에 붙인 버전 이름. 상대가
> 이 버전을 지원하는지 물어보고 새 필드를 보낼지 말지 정한다.\
> 예: `supports(VARIABLE_WIDTH_HISTOGRAM_SHARD_SIZE)`가 false면 상대는 두 필드를 모르는
> 구버전이므로 보내지 않는다.

코드에는 **이름만** 적는다.\
정수 id는 `./gradlew generateTransportVersion`이
`transport/definitions/referable/<이름>.csv`에 생성한다.\
이 파일들은 수기 편집 금지다.

**(b)(c) wire - 같은 게이트, 같은 순서.**

```java
protected void innerWriteTo(StreamOutput out) throws IOException {
    out.writeVInt(numBuckets);
    if (out.getTransportVersion().supports(VARIABLE_WIDTH_HISTOGRAM_SHARD_SIZE)) {
        out.writeInt(shardSize);
        out.writeInt(initialBuffer);
    }
}
```
(:151-158, 읽는 쪽은 :77-84에서 같은 게이트로 `readInt` 둘)

`numBuckets`는 게이트 **밖**에 그대로 둔다 - 기존 wire 포맷을 바꾸지 않기 위해서다.\
새 필드는 뒤에 붙이고 게이트로 감싼다.\
읽기와 쓰기가 같은 게이트·같은 순서여야 한다는 것이 이 패턴의 유일한 불변식이고,
어긋나면 수신 측이 정수를 다음 필드로 오독해 스트림이 깨진다.

**`writeVInt`가 아니라 `writeInt`인 이유가 이 PR의 작은 핵심이다.**\
미설정 값이 `-1`인데 `writeVInt`는 음수에 부적합하다(가변 길이 인코딩이 음수를 5바이트로
부풀리고 관용적이지도 않다).\
그리고 센티넬을 그대로 보존하는 것이 필수다 - `equals`가 원시 필드를 비교하므로 `-1`이
`-1`로 돌아오지 않으면 라운드트립 동등성이 깨진다.

> **가변 길이 인코딩(variable-length encoding)** — 작은 수는 적은 바이트로, 큰 수는 많은
> 바이트로 싣는 정수 표현. `writeVInt`가 그것이다.\
> 예: 작은 양수에는 이득이지만 `-1`은 비트 패턴이 커서 오히려 5바이트로 부푼다.

**(d) clone.**

```java
this.shardSize = clone.shardSize;
this.initialBuffer = clone.initialBuffer;
```
(:93-94)

BWC와 무관한 순수 누락이다.\
wire를 고쳐도 이 줄이 없으면 rewrite 경로에서 여전히 유실된다.

> **rewrite** — 좌표 노드가 요청을 실행하기 전에 같은 뜻의 더 싼 형태로 바꿔 쓰는 단계.
> 이 과정에서 빌더가 `shallowCopy`로 복제된다.\
> 예: 노드 밖으로 나가지 않아도, 복제 생성자가 필드를 안 옮기면 그 자리에서 값이 사라진다.

**(e) XContent - 설정된 값만.**

```java
if (shardSize != -1) {
    builder.field(SHARD_SIZE_FIELD.getPreferredName(), shardSize);
}
if (initialBuffer != -1) {
    builder.field(INITIAL_BUFFER_FIELD.getPreferredName(), initialBuffer);
}
```
(:225-230)

`-1`을 출력하면 안 된다.\
그 JSON을 다시 파싱하면 setter 검증(`shard_size > 1`)이 `IllegalArgumentException`을
던지기 때문이다.\
`numBuckets`는 기본값 10도 유효한 입력이라 항상 출력하지만, 이 둘은 센티넬이므로 조건부다.

## 5. 검증

**테스트를 먼저 썼다.**\
구현 diff를 열지 않은 상태에서 명세(요구사항 정의)만 보고 `BaseAggregationTestCase`
하위 테스트를 설계했고, 수정 전 실행에서 **45개 중 31개 실패**로 결함이 재현됐다.\
실패한 것은 `testSerialization`·`testFromXContent`·`testShallowCopy`와 그 multi
변종들이고 `testToString`만 통과했다 - **세 전파 경로가 각각 하나씩 실패를 낸 것**이라
예측과 정확히 일치했다.

수정 후 `./gradlew :server:spotlessJavaCheck :server:test --tests '*VariableWidthHistogramTests'
--tests '*VariableWidthHistogramAggregatorTests' -Dtests.iters=10`이 `BUILD SUCCESSFUL`.\
기존 Aggregator 테스트를 함께 돌려 알고리즘 쪽 회귀가 없음을 확인했다.

교차 검증(codex 1회, stakes 중간)에서 블로킹 0건, 비블로킹 1건을 받았다.\
지적은 "신규 테스트가 게이트 true 분기만 커버하고 **구버전으로 보내는 else 분기**는 한
번도 타지 않는다"였고, 이것이 우리 반증 질문("오래된 노드 경로는?")의 사각과 정확히
겹쳐 채택했다.\
`testSerializationBeforeShardSizeSupport`를 추가해 게이트 직전 버전으로 직렬화하면 두
필드가 드롭되고 수신 측이 기본값으로 폴백하는 것을 명시 검증한다 - 상세는
[tests.md](tests.md).\
나머지 하나는 지적이 아니라 확인이었다(게이트 read/write 대칭, 리소스 존재,
`getMinimalSupportedVersion()` 유지가 적절함).

## 6. 상태 - 리뷰 대기, 그리고 브랜치 신선도

2026-09-08 현재 **OPEN**이고 리뷰는 아직 없다.\
triage는 지났다 - `>bug`, `:Analytics/Aggregations`, `Team:Analytics`,
`external-contributor`, `v9.6.0` 라벨이 붙었고 봇이
`Pinging @elastic/es-analytical-engine (Team:Analytics)`를 남겼다.\
PR의 마지막 갱신은 2026-07-08이다.

> **triage** — 들어온 이슈·PR을 담당 팀과 우선순위로 분류하는 단계.\
> 예: `Team:Analytics` 라벨이 붙고 팀 멘션이 달렸다는 것은 분류가 끝나 리뷰 대기열에
> 올라갔다는 뜻이다.

제출 직후 전송 버전 충돌을 한 번 겪었다.\
브랜치를 딴 뒤 main에 다른 전송 버전이 머지되면 `upper_bounds/<minor>.csv`의 "최신 버전"
한 줄이 항상 충돌한다.\
이 파일을 손으로 고치는 것은 BWC상 위험하므로 `git merge upstream/main` 후
`./gradlew resolveTransportVersionConflict`로 우리 버전 id를 재생성했고(9421000 ->
9426000), 코드는 id가 아니라 **이름**을 참조하므로 코드 변경은 0이었다.

같은 문제가 다시 쌓여 있을 가능성이 높다는 것이 현재 관찰이다.\
PR의 diff는 `upper_bounds/9.5.csv`를 `variable_width_histogram_shard_size,9426000`으로
바꾸는데, upstream main에는 이미 `9.6.csv`가 생겼고 `9.5.csv`의 값도
`initial_9.5.4,9458008`로 넘어갔다.\
라벨이 `v9.6.0`인 것도 그 사이 개발 라인이 이동했다는 뜻이다.\
**머지 전에 다시 한 번 main을 병합하고 `resolveTransportVersionConflict`를 돌려야 할
것으로 보인다** - 이것은 실코드 관찰에서 나온 추정이고, 리뷰어가 요청하기 전에 먼저
손대는 것이 좋은지는 판단이 필요하다.
