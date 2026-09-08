# 151156 착수 분석

이 문서는 PR 착수 시점의 상세 분석(이름표·형제 검사·범위 밖 포함)이다. 해설 본문은 [README](README.md)에 있다.

### 7.1 이 결함이 잠복한 이유

세 겹이다. 첫째, 상수 관계가 정상 경로에서 어긋남을 가려 준다(3절). 둘째, 이 클래스는
값 객체라 집계 빌더용 프레임워크 테스트의 사정권 밖이다 -
`BaseAggregationTestCase`가 다루는 것은 빌더이고, `RoundingInfo`는 그 빌더의 필드도
아니라 결과 쪽에서 쓰이는 부속이다. 셋째,
`AutoDateHistogramAggregationBuilderTests`는 `ESTestCase`를 직접 상속해 프레임워크
테스트를 아예 받지 않는다(기존 테스트는 간격 검증·단위 목록 검증 둘뿐이었다).

### 7.2 바깥 빌더는 왜 깨끗한가

`AutoDateHistogramAggregationBuilder` 자신이 직렬화하는 것은 둘뿐이다.

```java
numBuckets = in.readVInt();
minimumIntervalExpression = in.readOptionalString();
...
out.writeVInt(numBuckets);
out.writeOptionalString(minimumIntervalExpression);
```
(:125-126, :131-132)

그리고 `hashCode`(:242)와 `equals`(:247)가 둘 다 포함한다. `RoundingInfo[]`는 빌더의
상태가 아니라 `build` 시점에 타임존과 최소 간격으로부터 계산되는 파생물이라 직렬화
대상이 아니다 - **파생물을 직렬화하지 않는다**는 설계가 여기서도 지켜지고 있고,
같은 원칙이 형제 PR [#151796](../151796-variable-width-histogram-shard-size/README.md)의
"resolved 값이 아니라 raw 값을 싣는다"와 이어진다.

### 7.3 범위 밖

- **`InternalAutoDateHistogram.targetBuckets`** - 직렬화되지만 top-level 동등성에서
  누락돼 있다는 교차 검증 보고가 있었다. 결과 클래스라 범주가 다르고 실코드 교차
  확인을 하지 않아 후속 후보로만 남겼다.
- **`RoundingInfo` 생성자의 인자 검증**(duration·약어가 `dateTimeUnit`과 정합한가)
  - 3절이 지적한 느슨함이지만 이 PR의 결함이 아니다.
- **`AutoDateHistogramAggregationBuilderTests`에 프레임워크 테스트 도입** - 이 파일이
  `ESTestCase` 직접 상속이라 라운드트립 커버리지가 없다. 별건이다.
