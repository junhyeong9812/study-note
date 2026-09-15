# 151154 착수 분석

이 문서는 PR 착수 시점의 상세 분석(이름표·형제 검사·범위 밖 포함)이다.\
해설 본문은 [README](README.md)에 있다.

별도 분석 문서를 두는 대신 착수 시점의 판정 근거를 여기 모았다.\
원본은 작업 repo의 `docs/plans/2026-06-13/pr2-matrixstats-missingmap/`와
`docs/plans/2026-06-18/pr-review-responses/`다.

### 8.1 죽은 필드 포렌식 - missing의 참조를 전수로 센다

"이 필드는 죽었다"는 주장은 참조를 하나도 빠뜨리지 않아야 성립한다.\
수정 전 소스에서 `missing`(정확히 이 식별자)의 등장은 넷이었다.

> **전수 조사** — 표본을 뽑지 않고 대상을 하나도 빠짐없이 전부 세는 것.\
> 예: "이 필드는 안 쓰인다"는 주장은 참조 하나만 놓쳐도 뒤집히므로, 몇 개를 확인하는 것으로는
> 성립하지 않는다.

| # | 위치 | 성격 | 판정 |
|---|---|---|---|
| 1 | `private Object missing = null;` (수정 전 :76) | 선언, 초기값 null | 값을 넣는 곳이 아님 |
| 2 | `this.missing = clone.missing;` (수정 전 clone 생성자) | null을 null로 복사 | 값을 만들지 않음 |
| 3 | `if (missing != null) builder.field(MISSING, missing);` (수정 전 :228) | XContent 분기 | 조건이 영원히 거짓 - 죽은 분기 |
| 4 | `Objects.equals(missing, other.missing)` / `Objects.hash(..., missing, ...)` | 동등성 | 항상 `null == null` - 무의미 |

값이 들어올 수 있는 경로는 셋뿐인데 셋 다 막혀 있다.

```text
값이 들어올 수 있는 경로       missing         missingMap
---------------------------------------------------------------------
setter                      없음            missingMap(Map)        :167-173
                              |                  |
                              X                  v
스트림 read                   없음            in.readGenericMap()    :107
  (read 는 넷만 읽는다 :103-108)  |                  |
                              X                  v
파서                          없음            factory.missingMap(map)
  (JSON 의 missing 키를           |             Parser:96-101, :167-169
   missingMap 으로 넣는다)        X                  |
                              |                  v
                              v
                        언제나 null       요청마다 달라지는 실제 상태
```

**setter가 없다**(`missingMap(Map)`만 있다).\
**스트림에서 읽지 않는다**(`read`는 `fields`·`userValueTypeHint`·`format`·`missingMap` 넷만
읽는다 - :103-108).\
**파서가 쓰지 않는다**(JSON의 `missing` 키를 `missingMap`으로 넣는다 -
ArrayValuesSourceParser.java:96-101, :167-169).\
따라서 결론은 "거의 항상 null"이 아니라 **"생성 이후 언제나 null"** 이다.

이 포렌식이 두 가지를 동시에 확정한다.\
4번의 동등성 비교는 언제나 참이므로 그 자리에는 사실상 아무 비교도 없었다.\
그리고 3번의 죽은 분기는 그저 안 쓰이는 코드가 아니라 **`missingMap`이 출력돼야 할 자리를
차지하고 있었다.**

### 8.2 이름표 - 무엇이 상태를 나르는가

| 이름 | 타입·기본값 | 어디에 쓰이나 | 상태인가 |
|---|---|---|---|
| `missingMap` | `Map<String,Object>`, `emptyMap()` (:76) | wire read/write(:107, :115) · setter(:167) · `resolveConfig`(:202) · 파서(Parser:167-169) | 예 |
| `missing` (수정 전) | `Object`, `null` | 선언 · clone · 죽은 XContent 분기 · 버그인 equals | 아니오 |
| `multiValueMode` | `MultiValueMode`, `AVG` (:30) | wire read/write(:60, :65) · clone(:42) · XContent(:89) · `innerBuild`(:84) | 예 |

`missingMap`이 상태를 나른다는 것은 소비처로도 확인된다.\
`resolveConfig`가 `missingMap.get(field)`를 값 소스 설정에 넘기므로(:202), 이 맵이 다르면
데이터 노드가 실제로 다르게 동작한다.

> **상태(state)** — 그 값이 달라지면 객체의 동작이 달라지는 필드.\
> 예: `missingMap`이 다르면 데이터 노드가 빈 필드를 다른 값으로 채우므로 결과가 달라진다 -
> 그래서 상태다.

### 8.3 형제 검사 - 교차 검증이 잡은 multiValueMode

착수 시점의 우리 조사는 부모의 `missingMap`까지였다.\
세 PR의 fix를 한 packet으로 묶어 codex에 독립 검증을 요청하면서 "같은 모듈에 같은 유형의
결함이 더 있는가"를 함께 물었고, 그 답에서 `multiValueMode`가 나왔다.

> **교차 검증(cross-check)** — 같은 대상을 독립된 다른 눈으로 한 번 더 확인하는 것.\
> 예: 우리가 찾은 수정안을 별개 도구에 넘겨 "이게 맞나, 빠진 형제는 없나"를 따로 묻는다.

> `MatrixStatsAggregationBuilder.multiValueMode` is another serialized builder field
> omitted from equality. ... The subclass inherits `ArrayValuesSourceAggregationBuilder`
> equality, so two `matrix_stats` builders differing only by `multiValueMode` still
> compare equal.

교차 확인은 두 단계였다.\
`multiValueMode`가 직렬화·clone·XContent에 모두 있는 것을 실코드로 확인했다.\
그리고 자식 클래스에 `equals`/`hashCode` 오버라이드가 없는 것을 grep으로 확인했다.\
둘 다 일치했으므로 범위를 넓혀 함께 고치기로 합의했고 이슈 #151153의 제목·본문도 두 필드로
갱신했다.\
이 경험에서 나온 절차가 다음 건으로 이어진다 - #151156에서는 "바깥 클래스에도 같은 누락이
있는가"를 **이슈를 열기 전에** 먼저 물었다.

같은 검증이 보고한 두 건은 범위 밖으로 남겼다.\
`InternalAutoDateHistogram.targetBuckets`와 `InternalTimeSeries`의 top-level 동등성 부재인데,
빌더가 아니라 결과(`Internal*`) 클래스라 범주가 다르고 우리가 실코드로 교차 확인하지 않았다.

### 8.4 nullability와 XContent 왕복의 경계

`missing`(null 가능)에서 `missingMap`으로 비교 대상을 바꾸면 "와이어 양쪽에서 null 취급이
갈리지 않는가"를 물어야 한다.

> **nullability(널 허용성)** — 그 자리에 null이 들어올 수 있는지 여부.\
> 예: 기본값이 `emptyMap()`이고 setter가 null을 거부하면, 그 필드는 사실상 null이 안 되는 자리다.

기본값이 `emptyMap()`이고(:76) setter가 null을 거부하며(:168-170) 파서는 실제 맵만 넘기고
(Parser:167-169) 기존 코드가 이미 무방비로 역참조하므로(:202), 정상 인스턴스는 null이 아니다.\
이론적 예외는 하나 - `StreamInput.readGenericMap()`이 API상 nullable이라 비정상 스트림이
null을 보낼 수는 있다.\
정상 writer는 그런 바이트를 만들지 않는다.

XContent 왕복에는 값 타입 경계가 있다.\
파서가 각 값을 `parser.objectText()`로 복원하므로 JSON 스칼라는 제자리로 돌아온다.\
다만 프로그래밍으로 넣은 `Short`·`Byte`·`Float`는 `Integer`/`Double`로 바뀌어 돌아올 수 있고
중첩 구조는 파서가 아예 소비하지 못한다.

이 경계를 결함으로 보지 않은 이유는 셋이다.\
값 타입 제약은 `missingMap`이라는 데이터 모델이 원래 갖고 있던 성질이다.\
우리 테스트가 쓰는 값은 `Integer`라 왕복이 안전하다.\
파서는 이전에도 `missing`을 객체로 받아들이고 있었으므로 파싱 호환성 문제도 아니다.\
**관찰로 기록하고 고치지 않았다.**

### 8.5 교차 검증 대장 - 리뷰 대응 시점 1회

XContent 출력이 바뀌는 변경이라 stakes를 중간으로 보고 codex를 한 번 돌렸다.\
질문 다섯 개에 대한 판정은 다음과 같다.

| # | 대상 | 요지 | 처리 |
|---|---|---|---|
| F1 | `internalXContent` | 스칼라 값은 왕복 OK. 비표준 값 타입·중첩 구조는 타입이 바뀌거나 파싱 불가 | 범위 밖(기존 특성) |
| F2 | 같은 곳 | non-empty `missingMap`이 이제 출력된다 - 정확 출력에 의존하던 소비자가 깨질 수 있다 | 의도된 정정(리뷰어 명시 요청) |
| F3 | `missingMap.isEmpty()` | 비정상 스트림의 null generic map이면 NPE 가능. read에서 정규화 hardening 제안 | 범위 밖(기존 가정) |
| F4 | wire | 전송 포맷 불변이므로 transport BWC 영향 없음 | 확인 |
| F5 | 자식 `equals`의 캐스팅 | `super.equals(obj)`가 true면 `obj.getClass() == this.getClass()`이므로 안전 | 확인 - 중복 가드 제거의 근거 |

> **NPE(NullPointerException)** — null인 참조에 대고 필드나 메서드를 쓰려 할 때 나는 예외.\
> 예: `missingMap`이 null인데 `missingMap.isEmpty()`를 부르면 그 줄에서 바로 터진다.

> **transport BWC** — 노드끼리 주고받는 전송 포맷의 하위 호환.\
> 예: 이번 변경은 wire에 싣는 바이트를 건드리지 않았으므로, 구버전 노드와 섞여 돌아도 영향이
> 없다.

수정이 필요한 finding은 0건이었다.\
F5는 리뷰어의 (a) 지적이 옳다는 독립 확인이기도 하고, 그 원리는 [structure.md](structure.md)
2절에 있다.

### 8.6 범위 밖 - 인접하지만 안 건드린 것

- **`missingMap` 값 타입 검증을 빌더에 두는 것**(8.4의 경계를 원천 차단) - 별개 설계 논의다.
- **`readGenericMap()` null 정규화** - read 경로 변경은 리뷰어가 요청하지 않았고 기존
  가정을 바꾸는 일이라 하지 않았다.
- **`userValueTypeHint`** - 파서가 지원하지 않지만 BWC 때문에 직렬화는 유지되는 필드다
  (:71-74의 주석).\
  같은 클래스에 잔재가 둘 있었던 셈인데, 차이는 이쪽은 여전히 직렬화되므로 상태이고
  `missing`은 아니었다는 점이다.
