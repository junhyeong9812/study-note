# PR #151154 - 무대의 실구조

> `matrix_stats` 빌더가 놓인 계층과, 그 계층을 타고 흐르는 세 경로(동등성 위임·wire·
> XContent 왕복). 문제와 수정은 [README.md](README.md), 착수 분석은
> README 8절 부록, 테스트는 [tests.md](tests.md).
>
> 기준: upstream `main`(2026-09-08). 이 시점의 파일에는 이미 수정이 반영돼 있으므로
> 아래 file:line은 "수정 후" 좌표다.

## 1. 계층 - 왜 두 층인가

`matrix_stats`는 필드 하나가 아니라 **필드 목록**을 받는 집계다. 그래서 보통의
`ValuesSourceAggregationBuilder` 계열이 아니라 별도의 배열 값 소스 계열에 속한다.

```
+---------------------------------------------------------------------------+
| AbstractAggregationBuilder                server search/aggregations/      |
|   상태: name, metadata, factoriesBuilder                                    |
|   writeTo: name, factoriesBuilder, metadata + doWriteTo(하위 위임)   :56-61  |
|   equals: name, metadata, factoriesBuilder                        :166-175 |
+---------------------------------------------------------------------------+
                                  ^
                                  | extends
+---------------------------------------------------------------------------+
| ArrayValuesSourceAggregationBuilder   modules/aggregations metric/         |
|   상태: fields, userValueTypeHint, format, missingMap              :70-76   |
|   read:    fields, userValueTypeHint, format, missingMap          :103-108 |
|   doWriteTo: 위 넷 + innerWriteTo(하위 위임)                        :111-117 |
|   internalXContent: fields, missing(=missingMap), format,                  |
|                     valueType + doXContentBody(하위 위임)           :220-238 |
|   equals/hashCode: 위 넷                                           :242-257 |
+---------------------------------------------------------------------------+
                                  ^
                                  | extends (LeafOnly - 하위 집계 불가)  :37-68
+---------------------------------------------------------------------------+
| MatrixStatsAggregationBuilder                                             |
|   상태: multiValueMode (기본 AVG)                                    :30     |
|   StreamInput ctor: multiValueMode 읽기                              :58-61 |
|   innerWriteTo:     multiValueMode 쓰기                              :63-66 |
|   clone ctor:       multiValueMode 복사                              :36-43 |
|   doXContentBody:   mode 렌더                                        :87-91 |
|   equals/hashCode:  super + multiValueMode                           :93-104|
|                     ^^^ 이 PR이 추가한 자리                                  |
+---------------------------------------------------------------------------+
```

그림에서 읽어야 할 것은 **각 층이 자기 필드만 책임지고 나머지는 위임한다**는 규칙이
직렬화·XContent·동등성 셋에 똑같이 적용된다는 점이다. `doWriteTo`가 자기 넷을 쓰고
`innerWriteTo`로 내려가듯, `equals`도 `super.equals`로 올라간 뒤 자기 필드를 본다.
그러므로 **한 층이 자기 몫을 안 하면 그 층의 필드만 정확히 빠진다.** 수정 전
`MatrixStatsAggregationBuilder`가 `equals`를 오버라이드하지 않았다는 것은 이 규칙의
한 칸이 비어 있었다는 뜻이다.

## 2. 동등성 위임 체인 - getClass가 어디에서 평가되나

자식 `equals`에는 null 검사도 `getClass` 검사도 없는데 캐스팅이 안전하다. 그 이유가
이 절의 전부다.

```
matrixStatsA.equals(obj)
  |
  +- if (this == obj) return true;                       MatrixStats:95
  |
  +- if (super.equals(obj) == false) return false;       MatrixStats:96
  |     |
  |     +- ArrayValuesSource.equals(obj)                 ArrayValuesSource:248
  |          if (this == obj) return true;                              :249
  |          if (obj == null || getClass() != obj.getClass()) return false;  :250
  |          |                  ^^^^^^^^^^
  |          |                  this 는 MatrixStats 인스턴스이므로
  |          |                  getClass() == MatrixStatsAggregationBuilder.class
  |          |
  |          +- if (super.equals(obj) == false) return false;           :251
  |          |     +- AbstractAggregationBuilder.equals - name/metadata/factories
  |          +- fields, format, missingMap, userValueTypeHint 비교        :253-256
  |
  +- MatrixStatsAggregationBuilder other = (MatrixStatsAggregationBuilder) obj;  :97
  |     ^^^ super 가 true 였다면 obj != null 이고 obj.getClass() == this.getClass()
  |         이므로 이 캐스팅은 항상 성공한다
  |
  +- return multiValueMode == other.multiValueMode;      MatrixStats:98
```

핵심은 `getClass()`가 **정적 타입이 아니라 런타임 `this`의 클래스**를 반환한다는
자바의 규칙이다. 부모 메서드 안에서 실행돼도 `this`가 자식 인스턴스면
`getClass()`는 자식 클래스를 돌려준다. 그래서 자식이 같은 검사를 한 번 더 하는 것은
순수 중복이고, 리뷰어의 (a) 지적이 옳았다.

hashCode도 같은 모양으로 합성된다.

```
MatrixStats.hashCode()  = Objects.hash(super.hashCode(), multiValueMode)      :103
ArrayValuesSource.hashCode() = Objects.hash(super.hashCode(), fields, format,
                                            missingMap, userValueTypeHint)     :244
Abstract.hashCode()     = Objects.hash(name, metadata, factoriesBuilder)
```

**equals에 참여하는 필드 집합과 hashCode에 참여하는 필드 집합이 층마다 일치**해야
계약이 유지된다. 이 PR이 두 메서드를 항상 짝으로 고친 이유다.

## 3. missing 값의 세 경로 - 수정 전후

"필드별 missing 대체값"이라는 한 가지 데이터가 wire·XContent·동등성 셋으로 각각
복제된다. 수정 전에는 그 셋이 서로 다른 필드를 보고 있었다.

```
                     [수정 전]                          [수정 후]

파서 (JSON "missing": {f: v})
   Parser:96-101 START_OBJECT 를 Map 으로 수집
   Parser:167-169 factory.missingMap(map)
        |                                          |
        v                                          v
   missingMap  <- 값이 들어오는 유일한 통로       missingMap
        |                                          |
   +----+----+----------------+              +-----+-----+----------------+
   |         |                |              |           |                |
  wire    XContent          equals          wire      XContent          equals
   |         |                |              |           |                |
 write     if (missing        Objects       write     if (missingMap    Objects
 Generic     != null)          .equals      Generic     .isEmpty()       .equals
 Map(:115)   ^^^^^^^          (missing,     Map(:115)   == false)        (missingMap,
             항상 거짓         other.        (:107 read)  field(MISSING,   other.
             = 출력 없음       missing)                   missingMap)      missingMap)
                              = 항상 참                   (:226-228)       (:255)
```

수정 전 그림에서 `missing`(유령)은 어느 통로로도 값을 받지 못하는데 XContent와
동등성 둘이 그것을 보고 있었다. 그 결과가 **출력 누락 하나와 무의미한 비교 하나**다.
수정 후에는 세 경로가 모두 `missingMap` 하나를 본다.

## 4. XContent 왕복 - 쓴 것을 파서가 되읽는가

XContent 출력을 바꿨으므로 반대편(파서)과 형태가 맞는지 확인해야 한다.

```
[쓰기]  internalXContent                        ArrayValuesSource:220-238
          if (missingMap.isEmpty() == false)                      :226
              builder.field("missing", missingMap)                :227
          => JSON  "missing": { "fieldA": vA, "fieldB": vB }

[읽기]  ArrayValuesSourceParser.parse                    Parser:62-171
          token == START_OBJECT 이고 필드명이 "missing" 이면          :96-97
              missingMap = new HashMap<>()                          :98
              END_OBJECT 까지 parseMissingAndAdd 반복                 :99-101
                  각 항목: fieldName -> parser.objectText()
          마지막에 factory.missingMap(missingMap)                     :167-169
```

형태(중첩 객체)가 양쪽에서 일치하므로 왕복이 성립한다. 값 타입에는 경계가 있는데
(`objectText()`가 JSON 스칼라만 원형 복원한다) 그것은 이 데이터 모델의 선재 제약이고
이번 변경이 들여온 것이 아니다 - README 8.4절.

빈 맵일 때 키를 생략하는 `isEmpty()` 가드도 왕복을 위한 것이다. 빈 객체를 출력하면
파서가 빈 맵을 만들어 넣게 되는데, 애초에 아무것도 설정하지 않은 빌더의 기본값도
빈 맵이므로 의미는 같다 - 다만 출력이 커지고 "설정하지 않음"과 "빈 맵으로 설정함"의
구분이 흐려진다. 이전 `!= null` 가드가 갖던 "없으면 안 쓴다"는 의미를 그대로 옮긴 것이다.

## 5. 이 무대의 자리 - matrix_stats는 왜 별도 계열인가

`ArrayValuesSourceAggregationBuilder`는 `modules/aggregations` 안에만 있고, 서브클래스도
`MatrixStatsAggregationBuilder` 하나다. 서버 코어의 `ValuesSourceAggregationBuilder`와
이름이 비슷하지만 다른 계열이고, 차이는 "값 소스가 하나인가 여럿인가"다.

```
ValuesSourceAggregationBuilder (server)        ArrayValuesSourceAggregationBuilder (module)
  field 하나 + missing 하나(스칼라)              fields 목록 + missingMap(필드별)
  대부분의 집계                                   matrix_stats 하나
```

이 대비가 결함의 배경이기도 하다. 배열 계열이 서버 계열의 형태를 물려받으며 스칼라
`missing` 필드를 함께 들여왔는데, 실제로 쓰는 것은 맵 쪽이고 스칼라 쪽은 이름만 남았다.
클래스 주석이 `userValueTypeHint`에 대해 "파서는 지원하지 않지만 BWC 때문에 남긴다"고
적어 둔 것(:71-74)을 보면, 이 클래스에는 그런 잔재가 하나 더 있었던 셈이다. 차이는
`userValueTypeHint`는 여전히 직렬화되므로 상태이고 `missing`은 아니었다는 점이다.
