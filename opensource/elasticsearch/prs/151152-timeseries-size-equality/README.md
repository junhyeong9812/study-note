# PR #151152 - time_series 빌더의 equals/hashCode에 size 포함

## 0. 정향

이 문서는 `time_series` 집계 빌더가 **직렬화·렌더·복제·public API 네 곳에서 상태로 취급하는 `size` 필드를 동등성 판정에서만 빼놓고 있던** 결함의 해설이다.\
결함도 수정도 두 줄이지만, 이 PR은 뒤이은 세 건의 출발점이었다.\
같은 렌즈("직렬화되는 필드가 equals에 있는가")로 훑어서 나온 첫 건이고, 그 렌즈가 이후 세 건을 더 찾아냈다.

> **동등성(equality)** — 두 객체가 "같은 것"인지 판정하는 규칙. 자바에서는 `equals`/`hashCode` 한 쌍이 정한다.\
> 예: `size`가 100인 빌더와 200인 빌더를 `equals`가 true로 보면, 그 둘은 코드 안에서 같은 요청으로 취급된다.

> **집계 빌더(aggregation builder)** — 검색 요청 안의 집계 설정을 담아 코디네이터에서 데이터 노드로 실어 보내는 객체.\
> 예: `{"time_series": {"keyed": true, "size": 200}}` 라는 요청 조각이 `TimeSeriesAggregationBuilder` 인스턴스가 된다.

다 읽으면 이 셋을 설명할 수 있어야 한다.

- "무엇을 근거로 equals가 틀렸다고 말하는가"
- "왜 기존 테스트가 이것을 못 잡았는가"
- "이름이 `...HashCode`인 테스트가 무엇을 검증해야 하는가"

상태: **머지 2026-06-19**(`3ba1d47ecf1`, `main`, `v9.5.0`).\
이슈 #151151을 먼저 열고 그것을 닫는 PR로 올렸다.

같은 폴더: [테스트 해설](tests.md).\
이 PR은 수정이 두 줄이고 무대가 클래스 하나라 별도의 실구조·분석 문서를 두지 않았다 - 공통 배경은 개념 문서에 있다.\
개념 문서: [직렬화 필드와 동등성의 정합 계약](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

## 1. 배경 - size는 어느 모로 보나 상태다

`time_series` 집계는 시계열 차원(dimension) 조합마다 버킷을 만드는 집계이고, 그 빌더가 `TimeSeriesAggregationBuilder`다.\
이 빌더가 들고 있는 상태 필드는 둘뿐이다.

```java
private final boolean keyed;
private int size;
```
(modules/aggregations TimeSeriesAggregationBuilder.java:38-39)

`size`가 "의미 있는 상태"라는 증거는 클래스 안에 네 겹으로 쌓여 있다.

| 면 | 코드 | 좌표 |
|---|---|---|
| wire 직렬화 | `out.writeVInt(size)` / `size = in.readVInt()` | :88, :82 |
| XContent 렌더 | `builder.field(SIZE_FIELD.getPreferredName(), size)` | :104 |
| clone 복제 | `this.size = clone.size` | :76 |
| public API | `setSize(int)` / `getSize()` | :129, :137 |

> **wire 직렬화(wire serialization)** — 객체를 노드 사이로 보내려고 바이트 열로 펼치는 것.\
> 예: `out.writeVInt(size)` 한 줄이 있으면 그 필드는 실제로 다른 노드까지 건너간다.

> **XContent 렌더** — 객체를 JSON 같은 텍스트 형식으로 다시 찍어내는 것(ES의 자체 추상화).\
> 예: 단언 실패 메시지에 `{"time_series":{"keyed":true,"size":200}}`이 찍히는 것이 이 렌더의 결과다.

`size`는 아무 데서나 오는 값도 아니다.\
파서가 `size` 키를 받아 생성자로 넘기고(:50), `doBuild`가 그 값을 그대로 `TimeSeriesAggregationFactory`에 실어 보낸다(:97).\
기본값은 `MultiBucketConsumerService.DEFAULT_MAX_BUCKETS`이고 `setSize`는 0 이하를 거부한다.\
**즉 요청마다 달라질 수 있고, 다르면 데이터 노드가 다르게 동작한다.**

집계 빌더에서 "무엇이 상태인가"의 정답지는 직렬화 목록이다 - 그 근거는 [개념 문서 1절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)에 있다.\
`doWriteTo`가 싣는 것은 `keyed`와 `size` 둘이고, 그러므로 두 빌더가 이 둘 중 하나라도 다르면 서로 다른 요청이다.

## 2. 수정 전 동작 - 정답지 둘 중 하나만 채점했다

수정 전 equals와 hashCode는 `keyed`만 봤다.

```java
// 수정 전
TimeSeriesAggregationBuilder that = (TimeSeriesAggregationBuilder) o;
return keyed == that.keyed;
...
return Objects.hash(super.hashCode(), keyed);
```

`super.equals(o)`가 이름·metadata·하위 집계를 비교하므로(AbstractAggregationBuilder.java:172-174) 그 위에서 이 클래스가 책임지는 것은 자기 필드 둘뿐인데, 그중 하나가 빠져 있었다.

`size=200`짜리 요청 하나가 클래스 안에서 어느 경로로 갈라지는지 세로로 따라가 보면 이렇다.

```text
{"time_series": {"keyed": true, "size": 200}}
        |
        v
  파서 (:50)                     size 키를 읽어 생성자로 넘긴다
        |
        v
  TimeSeriesAggregationBuilder   keyed=true, size=200
        |
        +--> doWriteTo (:88)      writeVInt(200)        -> 바이트에 200이 실린다
        |
        +--> internalXContent     field("size", 200)    -> JSON에 200이 찍힌다
        |      (:104)
        |
        +--> shallowCopy (:76)    this.size = clone.size -> 복제본도 200
        |
        +--> doBuild (:97)        Factory 에 200 전달   -> 데이터 노드가 200개 버킷
        |
        +--> equals (수정 전)      keyed 만 본다          -> 200 은 사라진다
```

네 갈래는 `size`를 그대로 들고 가는데 마지막 한 갈래만 그 값을 버린다.\
결과적으로 `size`가 100인 빌더와 200인 빌더가 - 직렬화하면 바이트가 다르고 데이터 노드에서 다른 개수의 버킷을 만드는 두 요청이 - `equals`로 true였고 해시도 같았다.

이 누락에는 이력이 있다.\
`size` 파라미터는 upstream #93496에서 추가됐고, 그 PR이 생성자·`doWriteTo`·`StreamInput`·`internalXContent`·setter를 전부 갱신하면서 `equals`/`hashCode`만 갱신하지 않았다.\
**필드를 더할 때 따라와야 하는 네 면 중 하나가 누락된 전형적인 형태**다.

## 3. 문제 - 조용하고, 테스트도 조용하다

이 결함은 예외를 만들지 않는다.\
`size`가 다른 두 요청이 "같다"고 판정될 뿐이고, 그 판정을 누가 어떻게 쓰느냐에 따라 증상이 달라진다.

> **조용한 실패(silent failure)** — 프로그램이 에러를 내지 않고 정상처럼 끝나는데 결과만 틀린 것.\
> 예: 예외를 던지면 바로 잡히지만, "두 요청은 같다"는 틀린 true는 아무 로그도 남기지 않는다.

같은 입력 한 쌍을 두 판정자에게 물으면 답이 갈린다.

```text
입력: size=100 인 빌더 A  vs  size=200 인 빌더 B

  직렬화 바이트로 보면              equals 로 보면
  +--------------------------+    +--------------------------+
  | A: [keyed=1, size=100]   |    | A.equals(B)              |
  | B: [keyed=1, size=200]   |    |   keyed == keyed  -> true |
  |                          |    |   (size 는 안 본다)       |
  | -> 바이트가 다르다        |    | -> true                  |
  +--------------------------+    +--------------------------+
        "서로 다른 요청"                  "같은 요청"
```

"이 객체가 무엇인가"의 정의가 한 클래스 안에서 두 갈래로 갈라져 있다 - 그것이 결함의 정확한 형태다.

빌더 equality는 `AggregatorFactories.Builder.equals`를 거쳐 `SearchSourceBuilder`·`SearchRequest`의 동등성으로 올라가므로, 요청을 비교하는 코드는 서로 다른 두 요청을 하나로 본다.

여기서 정직하게 좁혀 둘 것이 하나 있다.\
**샤드 요청 캐시의 키는 equals가 아니다.**\
`ShardSearchRequest.cacheKey`는 요청을 직렬화한 바이트의 SHA-256을 쓰므로(:547-554), `size`가 다르면 직렬화 바이트가 달라 캐시는 원래부터 두 요청을 구분한다.\
그래서 이 결함을 "캐시가 오염된다"로 서술하면 과장이다.\
정확한 서술은 **"이 객체가 무엇인가"의 정의가 코드 안에서 두 갈래로 갈라진 상태**이고, 그 정의를 쓰는 상위 계층이 늘어날 때 비로소 증상이 된다는 것이다.

더 실질적인 문제는 **잠복 조건**이다.\
이 결함은 십 년쯤 묵을 수 있는 종류인데, 집계 빌더의 공통 테스트 베이스가 구조적으로 이것을 못 잡기 때문이다.\
`BaseAggregationTestCase.testEqualsAndHashcode`는 변이 함수를 넘기지 않아서 필드를 하나도 바꿔 보지 않고, `testSerialization`은 판정 기준이 equals라서 equals가 무시하는 필드는 라운드트립으로도 드러나지 않는다.

> **라운드트립(round-trip)** — 객체를 바이트로 썼다가 다시 객체로 읽어 원본과 같은지 보는 검사.\
> 예: 원본과 복원본을 `assertEquals`로 비교하는데, 그 `equals`가 `size`를 안 보면 `size`가 깨져도 통과한다.

> **거짓 음성(false negative)** — 결함이 있는데 테스트가 초록으로 통과하는 것.\
> 예: 판정자 자신이 결함을 품고 있으면, 그 판정자를 쓰는 테스트는 결함을 절대 못 본다.

실측 근거는 [개념 문서 4절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)에 정리했다.\
요컨대 **이 결함을 잡는 테스트는 새로 쓰지 않으면 존재하지 않는다.**

## 4. 수정 해설 - 정답지에 맞춰 두 줄

수정은 누락된 필드를 양쪽에 더하는 것이 전부다.

```java
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    if (super.equals(o) == false) return false;
    TimeSeriesAggregationBuilder that = (TimeSeriesAggregationBuilder) o;
    return keyed == that.keyed && size == that.size;
}

@Override
public int hashCode() {
    return Objects.hash(super.hashCode(), keyed, size);
}
```
(TimeSeriesAggregationBuilder.java:141-153)

같은 입력 한 쌍에 답이 어떻게 달라지는지 나란히 놓으면 이렇다.

```text
      수정 전                              수정 후
+---------------------------+      +---------------------------+
| A(keyed=true, size=100)   |      | A(keyed=true, size=100)   |
| B(keyed=true, size=200)   |      | B(keyed=true, size=200)   |
+---------------------------+      +---------------------------+
| equals: keyed == keyed    |      | equals: keyed == keyed    |
|                           |      |     && size == size       |
| -> true                   |      | -> false                  |
| hash: hash(super, keyed)  |      | hash: hash(super, keyed,  |
|                           |      |            size)          |
| -> 같은 해시               |      | -> 다른 해시               |
+---------------------------+      +---------------------------+
   직렬화 바이트와 어긋난다            직렬화 바이트와 일치한다
```

비교 형태는 필드 타입이 정했다.\
`size`는 primitive `int`라 `==`가 옳고, 바로 옆의 `keyed == that.keyed`와 같은 모양이 된다.\
`Objects.equals`로 박싱해 비교할 이유는 없다 - null이 될 수 없는 값이고, 형제 비교와 스타일도 어긋난다.

> **박싱(boxing)** — `int` 같은 원시 타입을 `Integer` 객체로 감싸는 것.\
> 예: `Objects.equals(size, that.size)`라고 쓰면 두 `int`가 각각 `Integer`로 감싸진 뒤 비교된다.

**hashCode를 같이 고치는 것은 선택이 아니다.**\
equals에 필드를 더하면 "같으면 해시도 같다"는 계약의 강제 방향은 그대로 유지되지만, 반대로 equals에서 뺀 채 hashCode에만 넣으면 계약이 깨진다.\
그래서 두 메서드는 항상 한 쌍으로 움직인다.

> **hashCode 계약** — "두 객체가 equal이면 해시도 반드시 같아야 한다"는 단방향 규칙.\
> 예: 반대 방향("다르면 해시도 달라야 한다")은 요구되지 않는다 - 해시 충돌은 허용된다.

## 5. 리뷰 대응 - 이름이 약속한 것을 검증하라

메인테이너 swallez가 CHANGES_REQUESTED로 한 줄을 남겼다.

> Please add a test for `hashCode`, since this is mentioned in the method name.
> (테스트 파일 인라인 코멘트)

지적은 짧지만 정확했다.\
최초 커밋의 테스트 이름은 `testEqualsAndHashCodeConsiderSize`인데 단언은 `assertNotEquals(small, large)` 하나뿐, 즉 **이름이 약속한 계약의 절반을 검증하지 않고 있었다.**\
커밋 `d0fb50bffcd`로 단언 세 줄을 더했다.\
`size`만 다른 쌍은 해시도 다르고(필드가 hashCode에 참여함을 보인다), 모든 필드가 같은 쌍은 equal이면서 해시도 같다(계약이 실제로 강제하는 방향이다).\
자세한 단언별 의미는 [tests.md](tests.md)에 있다.

같은 날 swallez가 `LGTM`으로 승인했고, 이틀 뒤 머지됐다.\
이 지적은 형제 PR #151154에도 같은 문장으로 달렸고, 그쪽에서도 같은 형태로 보강했다.

## 6. 검증

red를 먼저 확인하고 고쳤다.\
착수 단계에서 프로덕션을 손대지 않은 채 테스트만 추가해 실행했고, 세 건의 형제 테스트와 함께 **3 tests completed, 3 failed**로 결함이 재현됐다.

> **red-green** — 결함을 먼저 실패(red)로 재현한 뒤 고쳐서 통과(green)시키는 순서.\
> 예: 고치고 나서 테스트를 쓰면, 그 테스트가 정말 결함을 잡는 테스트인지 확인할 방법이 없다.

이 PR 몫의 실패 메시지는 `Values should be different. Actual: {"ZfFZkojrzT":{"time_series":{"keyed":true,"size":200}}}`였다.\
렌더된 JSON에 `size:200`이 찍혀 있는데도 equals가 같다고 판정한다는 것이 한 줄로 보인다.

수정 후에는 같은 테스트가 green이고 클래스 전체 회귀가 없었다(`BUILD SUCCESSFUL`).\
리뷰 대응 커밋 뒤에는 `:modules:aggregations:test`와 `spotlessJavaCheck`를 다시 돌려 둘 다 통과를 확인했다.\
상세는 [tests.md](tests.md).

교차 검증은 codex를 한 번 돌렸다.\
세 건을 한 packet으로 묶어 보냈고 이 건에 대한 판정은 `correct & minimal`이었으며, `size`의 직렬화·팩토리 사용·렌더 좌표가 우리 조사와 일치했다.\
형제 검사도 함께 했다 - `TimeSeriesAggregationBuilder`는 서브클래스가 없는 단일 concrete 빌더라 상속으로 인한 누락 케이스가 없고, 필드 둘이 이제 모두 포함되므로 이 빌더의 동등성은 완결이다.

## 7. 상태와 교훈

머지 2026-06-19(`3ba1d47ecf1`, `v9.5.0`).\
리뷰는 swallez 한 명, CHANGES_REQUESTED 한 번 뒤 APPROVED.\
외부 기여자 PR이라 `Check labels`·`Check assignee`는 빨간 채로 남았는데 이는 Elastic triage 팀 전용 항목이라 정상이다.

1. **동등성의 정답지는 직렬화 목록이다.**\
   "이 필드가 상태인가"를 감으로 판단하지 않고 `writeTo`가 싣는 목록을 세어 equals와 차집합을 내면, 판정이 기계적이 되고 재현 가능해진다.\
   이 렌즈 하나로 같은 모듈에서 세 건이 더 나왔다.
2. **필드를 더하는 PR은 네 면을 함께 갱신해야 한다.**\
   wire·clone·XContent·동등성은 코드를 공유하지 않는 독립 경로라, 셋을 갱신하고 하나를 빼면 아무도 모르게 어긋난다.
3. **테스트 이름은 계약을 약속한다.**\
   이름에 `hashCode`가 있는데 equals만 단언하면 리뷰어가 정확히 그 지점을 짚는다.\
   그리고 hashCode 계약이 강제하는 방향은 "같으면 해시도 같다" 쪽이므로, 그 방향을 단언하지 않으면 계약은 검증되지 않은 것이다.
4. **프레임워크가 주는 테스트를 믿기 전에 그 몸체를 읽어라.**\
   `testEqualsAndHashcode`는 이름이 약속하는 것을 하지 않는다(변이 함수가 null이다).\
   이 사실은 주석이 아니라 호출 체인을 따라가야 확인된다.
