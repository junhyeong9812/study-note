# 151796 착수 분석

이 문서는 PR 착수 시점의 상세 분석(이름표·형제 검사·범위 밖 포함)이다. 해설 본문은 [README](README.md)에 있다.

### 7.1 설계 선택 - 무엇을 어떤 형태로 싣는가

wire 인코딩은 네 안을 비교해서 골랐다.

| 접근 | 장점 | 단점 | 판정 |
|---|---|---|---|
| `writeInt`/`readInt` | `-1` 센티넬을 그대로 보존, 단순 | 고정 4바이트 | **채택** - equals가 원시 필드를 비교하므로 센티넬 보존이 필수 |
| `writeVInt`/`readVInt` | 설정값 범위에서 바이트가 작다 | 음수에 부적합(5바이트, 비관용적) | 기각 |
| `writeOptionalVInt`(-1을 null로) | wire가 작다 | -1과 null을 오가는 변환 코드가 붙고 이득이 미미 | 기각 |
| resolved 값(`getShardSize()`)을 직렬화 | wire가 단순 | 미설정이 명시값으로 바뀌어 원시 상태가 변질 -> 라운드트립 equals가 깨진다 | 기각 |

마지막 행이 원칙이다. **직렬화의 단위는 파생값이 아니라 원시 필드여야 한다.** 형제 PR
[#151156](../151156-roundinginfo-serialized-fields/README.md)에서 `RoundingInfo[]`가
파생물이라 직렬화 대상이 아니었던 것과 같은 원칙의 다른 얼굴이다.

XContent도 두 안을 비교했다. 항상 출력하면 단순하지만 `-1`이 재파싱에서 setter 검증에
걸리므로, `!= -1`일 때만 출력하는 쪽을 택했다.

### 7.2 리스크 판정

stakes는 **중간**으로 봤다. 근거는 셋이다. 집계 의미가 변한다(두 파라미터가 이제 실제로
적용된다), wire 포맷이 바뀐다(전송 버전으로 흡수), 그리고 TransportVersion 워크플로우가
우리에게 낯설다. 반대로 blast radius는 집계 하나로 한정되고 되돌리기 쉬우므로 높음까지
올리지는 않았다.

가장 신경 쓴 실패 모드는 **구버전 노드로 직렬화하는 경로**다. 게이트가 false면 두
필드를 보내지 않고, 수신 측은 `-1`을 유지해 getter가 기본값을 계산한다. 즉 구버전
경로는 **수정 전과 똑같은(잘못된) 동작으로 안전하게 degrade**하고 새 예외를 만들지
않는다. 전 노드가 업그레이드되면 정상화된다. 이 경로를 테스트로 고정한 것이 교차 검증이
요구한 `testSerializationBeforeShardSizeSupport`다.

가정적 회귀 두 가지도 테스트가 막는다. 게이트가 비대칭이거나 순서가 어긋나면
`testSerialization`이 스트림 오독으로 깨지고, XContent에 `-1`을 내보내면
`testFromXContent`가 재파싱에서 깨진다.

### 7.3 범위 밖

- **`VariableWidthHistogramAggregator` 알고리즘**(merge phase) - 이 PR은 파라미터
  전달만 고친다.
- **`innerBuild`의 교차 검증**(`initialBuffer >= numBuckets` 등 - :174-204) - 기존 로직
  그대로다. `BaseAggregationTestCase`가 `build()`를 부르지 않으므로 테스트의 랜덤 값은
  setter 제약만 만족하면 된다.
- **연구 백로그의 다른 후보 열두 건** - 같은 스윕에서 나온 후보들이고, 목록은
  [개념 문서 8절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)에
  있다. 이 건만 별도로 뽑은 이유는 **유일하게 기능 버그이고 유일하게 BWC가 필요해서**다.
