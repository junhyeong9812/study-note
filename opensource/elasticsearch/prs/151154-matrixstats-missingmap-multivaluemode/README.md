# PR #151154 - matrix_stats 빌더의 equals/hashCode (missingMap·multiValueMode)

## 0. 정향

이 문서는 `matrix_stats` 집계 빌더의 동등성이 **두 층에서 동시에 어긋나 있던** 결함의 해설이다.\
부모 클래스는 이름이 비슷한 죽은 필드를 대신 비교하고 있었고, 자식 클래스는 자기 필드를
가지고도 `equals`를 오버라이드하지 않아 부모 것을 물려받고 있었다.\
여기에 리뷰가 세 번째 결함을 하나 더 끌어냈다 - 죽은 필드가 막고 있던 XContent 출력 누락이다.

> **동등성(equality)** — 두 객체를 "같은 것"으로 볼지 정하는 규칙. 자바에서는 `equals`와
> `hashCode` 한 쌍이 그 규칙이다.\
> 예: 필드별 missing 대체값만 다른 두 빌더에서 `equals`가 true를 돌려주면, 서로 다른 두 요청이
> 코드상 하나로 취급된다.

> **XContent** — Elasticsearch가 요청·응답을 JSON 등으로 쓰고 읽는 직렬화 계층.\
> 예: 빌더의 `internalXContent`가 `"missing": {"fieldA": 0}` 같은 JSON 조각을 만들어 낸다.

네 PR 중 가장 이야기가 많은 건이다.\
다 읽으면 다음 셋을 설명할 수 있어야 한다.

- "이름이 비슷한 두 필드 중 어느 쪽이 진짜 상태인가를 어떻게 판정하는가"
- "상속 계층에서 동등성 누락이 어떻게 숨는가"
- "죽은 코드가 어떻게 두 번째 결함을 감추는가"

상태: **머지 2026-06-19**(`6e5be615e88`, `main`, `v9.5.0`). 이슈 #151153을 닫는다.

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md).\
착수 분석은 별도 문서 [analysis.md](analysis.md)로 두었다 - 죽은 필드 포렌식·nullability
판정·교차 검증 대장이 그 내용이다.\
개념 문서: [직렬화 필드와 동등성의 정합 계약](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md).

## 1. 배경 - 두 층으로 나뉜 빌더

`matrix_stats`는 여러 필드의 상관·공분산 같은 행렬 통계를 내는 집계라 **필드를 여러 개** 받는다.\
그래서 값 소스 하나를 받는 보통의 집계와 계층이 다르다.

> **집계 빌더(aggregation builder)** — 사용자가 보낸 집계 요청을 담아 데이터 노드까지
> 실어 나르는 객체.\
> 예: `matrix_stats` 요청의 필드 목록과 옵션이 `MatrixStatsAggregationBuilder` 한 개에 담긴다.

```text
MatrixStatsAggregationBuilder                 자기 필드: multiValueMode
  extends ArrayValuesSourceAggregationBuilder.LeafOnly
    extends ArrayValuesSourceAggregationBuilder   자기 필드: fields, userValueTypeHint, format, missingMap
      extends AbstractAggregationBuilder          자기 필드: name, metadata, factoriesBuilder
```

부모 `ArrayValuesSourceAggregationBuilder`가 "여러 필드"를 다루는 공통 상태를 갖는다.\
자식 `MatrixStatsAggregationBuilder`가 행렬 통계 고유의 `multiValueMode`(한 문서에 값이
여럿일 때 어느 값을 쓸지 - AVG·MIN·MAX 등)를 갖는다.

> **MultiValueMode** — 한 문서의 한 필드에 값이 여러 개 있을 때 그중 무엇을 대표값으로 쓸지
> 정하는 열거형.\
> 예: `MIN`이면 가장 작은 값을, `MAX`면 가장 큰 값을, 기본값 `AVG`면 평균을 쓴다.

**동등성도 이 계층을 따라 위임된다**: 자식 `equals`가 `super.equals(obj)`를 먼저 부르고,
true일 때만 자기 필드를 비교한다.\
그 위임 구조는 [structure.md](structure.md)에 그렸다.

> **위임(delegation)** — 자기가 직접 처리하지 않고 다른 쪽에 넘겨 처리하게 하는 것.\
> 예: 자식 `equals`는 이름·메타데이터 비교를 직접 하지 않고 `super.equals`에 넘긴다.

부모의 상태 필드 넷 중 하나가 이 결함의 주인공이다.

```java
private List<String> fields = Collections.emptyList();
private ValueType userValueTypeHint = null;
private String format = null;
private Map<String, Object> missingMap = Collections.emptyMap();
```
(modules/aggregations ArrayValuesSourceAggregationBuilder.java:70-76)

`missingMap`은 "필드별 missing 대체값"을 담는 맵이다.\
필드가 여럿이므로 missing 값도 필드마다 달라야 해서 스칼라가 아니라 맵인 것이다.

> **missingMap** — 필드 이름을 키로, 그 필드에 값이 없을 때 대신 쓸 값을 값으로 갖는 맵.\
> 예: `{"priceA": 0, "priceB": 1}`이면 `priceA`가 비었을 때 0을, `priceB`가 비었을 때 1을 쓴다.

그리고 이것이 직렬화되는 실제 상태다 - `out.writeGenericMap(missingMap)`(:115)와
`missingMap = in.readGenericMap()`(:107), 파서의 `factory.missingMap(missingMap)`
(ArrayValuesSourceParser.java:167-169), setter `missingMap(Map)`(:167-173)이 전부 이 필드를
가리킨다.

> **wire 직렬화(wire serialization)** — 객체를 노드 사이로 보내려고 바이트 열로 바꾸는 것.\
> 예: 조정 노드가 만든 빌더를 `writeTo`로 바이트에 실어 데이터 노드로 보내고, 저쪽에서
> 같은 순서로 읽어 빌더를 복원한다.

## 2. 수정 전 동작 - 유령을 비교하고 있었다

수정 전 부모 클래스에는 필드가 하나 더 있었다.

```java
// 수정 전
private Object missing = null;
```

그리고 `equals`/`hashCode`가 비교하던 것이 `missingMap`이 아니라 이 `missing`이었다.

```java
// 수정 전
return Objects.hash(super.hashCode(), fields, format, missing, userValueTypeHint);
...
&& Objects.equals(missing, other.missing)
```

값이 어디서 들어와 어디로 갈라지는지를 한 장으로 보면 이렇다.

```text
JSON 요청   "missing": { "fieldA": 0 }
        |
        v
ArrayValuesSourceParser.parse         Parser:96-101  START_OBJECT 를 Map 으로 수집
        |
        v
factory.missingMap(map)               Parser:167-169
        |
        v
missingMap = {fieldA=0}    <- 값이 들어오는 유일한 통로
        |
        +--> doWriteTo         out.writeGenericMap(missingMap)   :115
        |                      -> 값이 그대로 실린다
        |
        +--> internalXContent  if (missing != null)              :228
        |                      -> missing 은 언제나 null 이라 거짓
        |                      -> 출력 없음
        |
        +--> equals            Objects.equals(missing, other.missing)
                               -> null == null 이라 언제나 참

missing = null             <- setter 없음 · 스트림 읽기 없음 · 파서 없음
```

세 소비처 중 wire 하나만 진짜 상태를 보고, XContent와 equals 둘은 유령을 본다.\
갈림이 생기는 자리는 `missingMap`에서 내려가는 세 갈래의 두 번째·세 번째 칸이다.

이 `missing` 필드의 실체를 전수로 확인하면 **생성 이후 언제나 null**이다.\
setter가 없고(`missingMap(Map)`만 있다), 스트림에서 읽지도 쓰지도 않으며, 파서는 JSON의
`missing` 키를 `missingMap`으로 넣는다.\
남은 참조는 clone 생성자의 복사 한 줄과 `internalXContent`의 `if (missing != null)` 분기뿐이었는데,
값이 항상 null이므로 그 분기는 **한 번도 실행되지 않는 죽은 코드**였다.\
참조를 전수로 센 근거는 8.1절에 있다.

> **죽은 코드(dead code)** — 문법상 멀쩡히 있지만 실행되는 경로가 없어 절대 돌지 않는 코드.\
> 예: 조건이 `if (missing != null)`인데 `missing`에 값을 넣는 곳이 하나도 없으면, 그 블록 안은
> 영원히 실행되지 않는다.

자식 쪽에는 다른 종류의 누락이 있었다.\
`MatrixStatsAggregationBuilder`는 `multiValueMode`를 선언(:30)하고 clone에서 복사(:42)하고
스트림에 쓰고 읽고(:60, :65) XContent로 렌더(:89)하는데, **`equals`/`hashCode`를 오버라이드하지
않았다.**\
그래서 부모의 구현을 그대로 물려받았고, 부모는 `multiValueMode`의 존재를 모른다.

정리하면 수정 전 상태는 세 겹이었다.

| 결함 | 위치 | 결과 |
|---|---|---|
| 죽은 `missing`을 비교 | 부모 `equals`/`hashCode` | 항상 `null == null` - 비교가 무의미 |
| `missingMap`이 비교에서 누락 | 부모 `equals`/`hashCode` | missingMap만 다른 두 빌더가 같다고 판정 |
| `multiValueMode`가 비교에서 누락 | 자식이 오버라이드 없음 | mode만 다른 두 빌더가 같다고 판정 |

## 3. 문제 - 상속과 이름 유사성이 함께 숨긴다

같은 입력에 판정이 어떻게 갈리는지를 수정 전후로 나란히 놓으면 이렇다.

```text
[수정 전] equals 가 missing 을 본다          [수정 후] equals 가 missingMap 을 본다

빌더 A  missingMap = {field=1}               빌더 A  missingMap = {field=1}
빌더 B  missingMap = {field=2}               빌더 B  missingMap = {field=2}
        missing = null (둘 다)                       (missing 필드 자체가 없다)
+-------------------------------+            +-------------------------------+
| Objects.equals(null, null)    |            | Objects.equals({field=1},     |
|            -> true            |            |                {field=2})     |
| A.equals(B) -> true           |            |            -> false           |
+-------------------------------+            | A.equals(B) -> false          |
                                             +-------------------------------+
  -> 다른 두 요청이 같다고 판정된다               -> 두 요청이 구분된다
```

이 결함이 오래 잠복한 이유는 두 겹이다.

**첫째, 이름이 비슷한 필드가 알리바이를 만든다.**\
`equals`를 읽는 사람 눈에는 `Objects.equals(missing, other.missing)`이 멀쩡해 보인다.\
"missing 값을 비교하는구나"로 읽히기 때문이다.\
이 줄이 틀렸다는 것은 `missing`의 참조를 전수로 세어 봐야 드러난다 - 그리고 그 결과가
"선언·clone·죽은 XContent 분기·이 equals" 넷뿐이다.

**둘째, 상속이 누락을 시야 밖으로 옮긴다.**\
`MatrixStatsAggregationBuilder`만 열어 보면 `equals`가 아예 없으므로 "비교할 것이 없나 보다"로
넘어가기 쉽다.\
자식 파일과 부모 파일과 자식의 직렬화 목록을 **동시에** 놓아야 `multiValueMode`가 어디에도 안
들어간다는 것이 보인다.\
실제로 이 건은 우리 초기 조사에서 놓쳤고, codex 교차 검증이 형제 누락으로 잡아냈다(8.3절).

증상 자체는 형제 PR과 같다 - 예외는 나지 않고, 서로 다른 요청이 같다고 판정될 뿐이다.

> **조용한 실패(silent failure)** — 에러를 내지 않고 정상처럼 끝나는데 결과만 틀린 것.\
> 예: `size`가 다른 두 요청을 "같다"고 판정해도 예외가 나지 않으므로, 잘못됐다는 신호가
> 어디에도 남지 않는다.

그 판정을 실제로 누가 쓰는지, 그리고 "캐시 키가 오염된다"가 왜 과장인지는
[개념 문서 5절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)에
정리했다.

## 4. 수정 해설 - 두 층을 각각

**부모: 비교 대상을 진짜 상태로 바꾼다.**

```java
@Override
public int hashCode() {
    return Objects.hash(super.hashCode(), fields, format, missingMap, userValueTypeHint);
}
...
    return Objects.equals(fields, other.fields)
        && Objects.equals(format, other.format)
        && Objects.equals(missingMap, other.missingMap)
        && Objects.equals(userValueTypeHint, other.userValueTypeHint);
```
(ArrayValuesSourceAggregationBuilder.java:242-257)

`Map`이므로 `Objects.equals`가 옳고, 형제 비교와 형태·순서가 그대로 유지된다.\
null 안전성은 따로 확인했다 - `missingMap`은 기본값이 `Collections.emptyMap()`(:76)이고
setter가 null을 거부하며(:168-170) 코드 곳곳이 무방비로 역참조한다(:202).\
즉 non-null이 이 클래스의 사실상 계약이고, 그렇더라도 `Objects.equals`는 어느 쪽이든 안전하다.

> **역참조(dereference)** — 참조가 가리키는 객체의 내용을 실제로 꺼내 쓰는 것.\
> 예: `missingMap.get(field)`처럼 null 검사 없이 바로 메서드를 부르면, null일 경우 그 자리에서
> NPE가 난다.

**자식: 부모에 위임하고 자기 필드를 더한다.**

```java
@Override
public boolean equals(Object obj) {
    if (this == obj) return true;
    if (super.equals(obj) == false) return false;
    MatrixStatsAggregationBuilder other = (MatrixStatsAggregationBuilder) obj;
    return multiValueMode == other.multiValueMode;
}

@Override
public int hashCode() {
    return Objects.hash(super.hashCode(), multiValueMode);
}
```
(MatrixStatsAggregationBuilder.java:93-104)

`multiValueMode`는 enum이라 `==`가 옳다(null-safe하고 동일성이 곧 동등성이다).

> **enum(열거형)** — 값이 미리 정해진 상수 몇 개로 고정된 타입. 상수마다 인스턴스가 하나뿐이다.\
> 예: `MultiValueMode.MIN`은 프로그램 전체에서 같은 객체 하나이므로, `==` 비교가 곧 값 비교다.

캐스팅 앞에 null·`getClass` 가드가 없는데도 안전한 이유는 [structure.md](structure.md)의
위임 체인 절에 있다 - 요지는 부모 `equals`가 이미 그 검사를 하고, 그 안의 `getClass()`가
**런타임 `this`**(=자식 인스턴스)에서 평가된다는 것이다.

죽은 `missing` 필드를 이 PR에서 제거할지는 처음에 보류했다.\
결함(=동등성)과 수정을 1:1로 유지하는 편이 리뷰 마찰이 적다는 판단이었다.\
그 판단은 리뷰에서 뒤집힌다.

## 5. 리뷰 대응 - 세 지적, 그중 하나가 네 번째 결함을 열었다

메인테이너 swallez가 CHANGES_REQUESTED와 함께 인라인 세 건을 남겼다.

> **CHANGES_REQUESTED** — GitHub 리뷰 상태 중 하나로, "이대로는 머지 못 하니 고쳐 달라"는 판정.\
> 예: 승인(APPROVED)과 달리 이 상태에서는 지적을 반영하고 다시 리뷰를 받아야 머지로 넘어간다.

**(a) 중복 가드 제거.**\
"This can be removed, this is already checked in the parent class."\
자식 `equals`의 `if (obj == null || getClass() != obj.getClass()) return false;`가 부모
검사와 중복이라는 지적이다.\
부모 `equals`가 그 검사를 수행하고(:250) 자식은 그 직후 `super.equals(obj)`를 호출하므로 순수
중복이 맞다.\
한 줄 제거했다.\
`if (this == obj)`는 지적 대상이 아니었고 유효한 단축이라 남겼다 - **리뷰어가 짚은 위치만
고친다**는 범위 규율이다.

**(b) 죽은 필드 제거 + XContent 교체.**\
"The `missing` field is actually useless and can be removed. Use `missingMap` to replace it in
`internalXContent`."\
여기서 네 번째 결함이 드러났다.\
죽은 분기 때문에 **`missingMap`이 XContent 출력에 한 번도 실리지 않고 있었다.**\
즉 빌더는 상태를 들고 있고 wire로도 보내는데 XContent에만 안 나오는 비대칭이 잠복해 있었던 것이다.\
필드와 clone 복사를 지우고 출력을 바꿨다.

```java
if (missingMap.isEmpty() == false) {
    builder.field(CommonFields.MISSING.getPreferredName(), missingMap);
}
```
(ArrayValuesSourceAggregationBuilder.java:226-228)

같은 상태를 들고 있을 때 출력이 어떻게 달라지는지를 나란히 놓으면 이렇다.

```text
[수정 전] internalXContent                   [수정 후] internalXContent

missingMap = { fieldA: vA }                  missingMap = { fieldA: vA }
        |                                            |
        v                                            v
if (missing != null)            :228         if (missingMap.isEmpty() == false)  :226
  missing 은 언제나 null                        비어 있지 않다
  -> 조건이 영원히 거짓                          -> 조건 참
  -> 분기가 한 번도 실행되지 않음                 -> builder.field("missing", missingMap)  :227
+------------------------------+             +------------------------------+
| 출력 JSON 에 missing 이 없다   |             | "missing": { "fieldA": vA }  |
+------------------------------+             +------------------------------+
  -> wire 로는 보내면서                          -> wire · XContent · equals 가
     XContent 에만 안 나오는 비대칭                  같은 필드 하나를 본다
```

`isEmpty()` 가드는 이전 `!= null` 가드와 같은 의미("없으면 안 쓴다")를 보존한다.\
`builder.field(name, Map)`은 JSON 중첩 객체로 렌더되고, 파서는 `missing`을 `START_OBJECT`로
기대하므로(ArrayValuesSourceParser.java:96-101) 왕복이 성립한다.\
이 왕복의 경계 조건(값 타입이 바뀔 수 있는 경우)은 8.4절에 있다.

**(c) 테스트의 hashCode 단언.**\
"This doesn't test `hashCode` which is mentioned in the method name. Same for the second test
method."\
형제 PR #151152와 같은 지적이고 같은 형태로 보강했다.\
다만 이 클래스는 `ESTestCase`를 직접 상속해 프레임워크의 일반 계약 테스트를 물려받지 않으므로,
계약의 강제 방향(equal이면 해시도 같다)까지 직접 단언할 값어치가 더 크다.\
그 판단 근거를 답글에 적고 "최소로 줄이길 원하면 그렇게 하겠다"고 덧붙였다.\
리뷰어는 그대로 승인했다.

세 건 모두 커밋 `62bcb7ec779` 하나로 반영했다.\
XContent 출력 변경은 동작 변경이므로 codex 교차 검증을 한 번 돌려 왕복 정합·BWC·NPE·캐스팅
안전을 확인했고, 수정이 필요한 finding은 0건이었다(8.5절의 대장).\
같은 날 swallez가 `LGTM`으로 승인했다.

> **BWC(backward compatibility, 하위 호환)** — 새 버전이 옛 버전과 계속 맞물려 돌아가는 성질.\
> 예: 구버전 노드가 보낸 바이트를 신버전 노드가 그대로 읽을 수 있어야 롤링 업그레이드가 된다.

## 6. 검증

red를 먼저 확인했다.\
`missingMap` 쪽은 프로덕션 수정 전 red를 확인했다
(`Values should be different. Actual: {"matrix":{"matrix_stats":{"fields":[],"mode":"AVG"}}}` -
렌더된 JSON에는 missingMap이 아예 안 나오는데도 내부 필드가 다르다는 것이 그대로 보인다).\
`multiValueMode` 쪽은 부모 수정만 적용한 상태에서 red를 확인한 뒤 자식 오버라이드를 넣어
green으로 만들었다.\
**한 PR 안에서 두 번의 red -> green을 밟았다.**

> **red -> green** — 결함을 재현해 실패(red)를 먼저 보고, 고친 뒤 통과(green)를 확인하는 순서.\
> 예: 프로덕션을 안 고친 채 테스트만 돌려 실패를 봐야, 그 테스트가 진짜 결함을 겨누는지 알 수 있다.

수정 후 `:modules:aggregations:test --tests "...metric.*"`와 `spotlessJavaCheck` 모두
`BUILD SUCCESSFUL`.\
상세와 단언별 의미는 [tests.md](tests.md).

## 7. 상태와 교훈

머지 2026-06-19(`6e5be615e88`, `v9.5.0`). 리뷰 한 라운드(인라인 3건) 뒤 APPROVED.

1. **이름이 비슷한 두 필드가 있으면 참조를 전수로 센다.**\
   `missing`과 `missingMap`처럼 한 글자 차이인 필드에서는 코드를 읽는 눈이 알리바이를 만들어 준다.\
   "이 필드에 값이 들어오는 경로가 실제로 있는가"를 setter·파서·스트림·생성자로 나눠 세면
   유령이 드러난다.
2. **상속 계층에서는 자식·부모·직렬화 목록을 동시에 놓아야 한다.**\
   자식 파일만 보면 `equals`가 없는 것이 정상으로 보인다.\
   이 건은 우리 조사가 놓치고 교차 검증이 잡았다.
3. **죽은 코드는 두 번째 결함을 감춘다.**\
   항상 null인 필드를 조건으로 쓴 분기는 실행되지 않을 뿐 아니라, 그 자리에 있어야 할 진짜
   출력을 대신 막고 있었다.\
   죽은 분기를 발견하면 "이 분기가 원래 무엇을 하려던 자리인가"를 물어야 한다.
4. **리뷰 지적은 범위를 넓힐 근거가 될 수 있다.**\
   우리는 스코프 규율 때문에 죽은 필드를 남겼는데, 리뷰어가 제거를 요청하면서 잠복 결함 하나가
   함께 해소됐다.\
   최소 스코프는 기본값이지 목표가 아니다.
