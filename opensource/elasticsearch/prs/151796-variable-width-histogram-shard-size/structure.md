# PR #151796 - 무대의 실구조와 워크플로우

> 집계 파라미터가 좌표 노드에서 데이터 노드까지 가는 길, 그 길이 셋으로 갈라진다는
> 사실, 그리고 그 위에 세운 버전 게이트. 문제와 수정은 [README.md](README.md), 테스트는
> [tests.md](tests.md).
>
> 기준: 브랜치 `fix/variable-width-histogram-shard-size-serialization`(머지 커밋
> `9f94b453016` = upstream main 병합 후). **이 시점의 빌더에는 이미 수정이 반영돼
> 있으므로** 아래 file:line은 "수정 후" 좌표이고, 수정 전 동작은 diff의 `-`쪽으로
> 재구성한 것이다.

## 1. 무대 - 요청 하나가 지나는 길

집계 요청은 좌표 노드에서 만들어져 각 데이터 노드로 흩어지고, 각 노드가 자기 샤드에서
집계를 돌린 뒤 결과가 좌표 노드로 모여 reduce된다. 이 PR의 결함은 그중 **첫 hop**에서
필드가 사라지는 것이었다.

```
+---------------------------------------------------------------------------+
| 요청 (REST/JSON)                                                           |
|   "variable_width_histogram": { "field": ..., "buckets": 10,               |
|                                 "shard_size": 200, "initial_buffer": 5000 }|
+---------------------------------------------------------------------------+
                                   |
                                   v  ObjectParser
+---------------------------------------------------------------------------+
| VariableWidthHistogramAggregationBuilder (좌표 노드)                        |
|   PARSER.declareInt(...setNumBuckets, "buckets")                    :58    |
|   PARSER.declareInt(...setShardSize, "shard_size")                  :59    |
|   PARSER.declareInt(...setInitialBuffer, "initial_buffer")          :60    |
|                                                                           |
|   상태 (원시 필드 - -1 = 미설정)                                             |
|     numBuckets = 10 / shardSize = -1 / initialBuffer = -1           :63-65 |
|   setter 검증: shard_size > 1, initial_buffer > 0                   :110-125|
|   getter 폴백: -1 이면 numBuckets 에서 계산                           :127-139|
+---------------------------------------------------------------------------+
        |                     |                        |
        | wire                | clone                  | XContent
        v                     v                        v
+----------------+  +-------------------+  +---------------------------+
| innerWriteTo   |  | shallowCopy ->    |  | doXContentBody            |
|          :151  |  | clone 생성자 :86  |  |                     :222  |
+----------------+  +-------------------+  +---------------------------+
        |
        v  (StreamInput 생성자 :77)
+---------------------------------------------------------------------------+
| 데이터 노드                                                                 |
|   innerBuild                                                       :160    |
|     int initialBuffer = getInitialBuffer();                         :172   |
|     int shardSize = getShardSize();                                 :173   |
|     교차 검증 (initialBuffer >= numBuckets, 3/4*shardSize >= numBuckets)     |
|                                                                    :174-204|
|     new VariableWidthHistogramAggregatorFactory(..., shardSize,            |
|                                        initialBuffer, ...)         :208-219|
+---------------------------------------------------------------------------+
```

그림에서 읽어야 할 것은 하나다. **파라미터를 실제로 쓰는 코드는 데이터 노드 쪽에 있고,
사용자가 값을 넣는 곳은 좌표 노드 쪽에 있다.** 그 사이를 잇는 유일한 통로가 wire이고,
수정 전에는 그 통로에 `numBuckets`만 실려 있었다. `innerBuild`가 아무리 `getShardSize()`를
불러도 그때 `shardSize`는 이미 `-1`이라 기본값이 나온다.

## 2. 세 경로는 독립이다

같은 두 필드를 복제하는 경로가 셋인데 코드를 공유하지 않는다. 그래서 하나만 고치면
나머지 둘로 여전히 샌다.

```
                     shardSize / initialBuffer (원시 필드, -1 = 미설정)
                                     |
        +----------------------------+----------------------------+
        |                            |                            |
   [wire]                       [clone]                      [XContent]
   노드 간 전송                  좌표 노드 안 rewrite            요청 재렌더·재파싱
        |                            |                            |
  innerWriteTo :151            clone 생성자 :86-95            doXContentBody :222
  StreamInput ctor :77                                             + PARSER
        |                            |                            |
  버전 게이트 필요                게이트 무관                    센티넬 출력 금지
  (구버전 노드 존재)              (같은 JVM 안)                  (재파싱이 -1 거부)
        |                            |                            |
  testSerialization           testShallowCopy               testFromXContent
```

세 경로의 성격이 다르다는 점이 수정 방식을 갈랐다. **wire만 BWC 문제를 갖는다** -
상대가 구버전일 수 있기 때문이다. clone은 같은 JVM 안의 복사라 조건 없이 두 줄을
더하면 끝난다. XContent는 버전 문제가 없는 대신 **재파싱 가능성**이라는 제약이 있어
`-1`을 내보내면 안 된다.

프레임워크 테스트가 정확히 이 셋을 하나씩 맡는다는 점도 그림에 함께 적었다. 수정 전
45개 중 31개가 실패한 것은 세 경로가 각각 자기 몫의 실패를 냈기 때문이다.

## 3. 버전 게이트 - 롤링 업그레이드 중의 분기

새 필드를 wire에 얹으면 그 바이트를 모르는 구버전 노드가 스트림을 오독한다. 그래서
전송 버전으로 상대의 능력을 물어보고 분기한다.

```
                    좌표 노드가 데이터 노드로 빌더를 직렬화
                                    |
                    out.getTransportVersion().supports(
                        VARIABLE_WIDTH_HISTOGRAM_SHARD_SIZE)         :154
                                    |
            +-----------------------+------------------------+
          true (신버전 수신자)                            false (구버전 수신자)
            |                                                |
  writeVInt(numBuckets)                            writeVInt(numBuckets)
  writeInt(shardSize)                              (두 필드는 쓰지 않음)
  writeInt(initialBuffer)          :153-157                  |
            |                                                |
            v                                                v
  수신: 같은 게이트로 readInt 둘    :80-83        수신: 구버전이라 읽지 않음
            |                                                |
  shardSize = 123 (사용자 값)                      shardSize = -1 (기본값 유지)
            |                                                |
            v                                                v
  getShardSize() = 123                             getShardSize() = numBuckets * 50
  => 파라미터가 동작한다                             => 수정 전과 같은 (잘못된) 동작
                                                     예외 없음, 전 노드 업그레이드 후 정상화
```

이 분기의 불변식은 둘이다. **읽기와 쓰기가 같은 게이트를 쓸 것**, 그리고 **게이트 안의
필드 순서가 같을 것**. 하나라도 어긋나면 수신 측이 정수를 다음 필드의 값으로 읽어
스트림이 깨진다. `numBuckets`를 게이트 밖에 그대로 둔 것도 같은 이유다 - 기존 포맷의
앞부분은 건드리지 않고 뒤에만 붙인다.

`getMinimalSupportedVersion()`은 손대지 않았다. 구버전이 이 필드가 빠진 빌더를 받아도
문제가 없으므로 최소 지원 버전을 올릴 이유가 없다.

## 4. 전송 버전은 이름으로 참조한다

`TransportVersion`을 처음 쓰면 헷갈리는 것이 "정수 id를 어디에 적는가"다. 답은 **코드에는
안 적는다**이다.

```
[코드]  TransportVersion.fromName("variable_width_histogram_shard_size")   :48-50
             |  이름(String 리터럴)만 참조. 정규식 [_0-9a-zA-Z]+
             v
[생성]  ./gradlew generateTransportVersion
             |
             +- server/src/main/resources/transport/definitions/referable/
             |     variable_width_histogram_shard_size.csv   <- 9426000 (이름 -> id)
             |
             +- server/src/main/resources/transport/upper_bounds/9.5.csv
                   <- variable_width_histogram_shard_size,9426000 (그 minor의 최신)

[금지]  위 두 파일을 손으로 편집하지 않는다.
[충돌]  브랜치를 딴 뒤 main 에 다른 TV 가 머지되면 upper_bounds 의 한 줄이 항상 충돌
        -> git merge upstream/main 후 ./gradlew resolveTransportVersionConflict
        -> 우리 id 를 새로 발급하고 충돌 파일을 스테이징. 코드는 이름을 참조하므로 변경 0
```

이 "이름 참조" 설계가 실제로 값을 했다. 제출 직후 다른 전송 버전이 main에 먼저 머지돼
id가 9421000에서 9426000으로 재발급됐는데, 빌더 코드도 테스트 코드도 한 줄도 바뀌지
않았다. 테스트가 버전 상수를 직접 적지 않고
`TransportVersionUtils.getPreviousVersion(TransportVersion.fromName(...))`으로 얻는
것도 같은 이유다 - [tests.md](tests.md)의 T2.

예방책은 하나다. **Writeable이나 전송 버전을 건드리는 PR은 최신 main에서 브랜치를 딴다.**

## 5. 원시 값과 파생 값 - 무엇을 저장하고 무엇을 계산하나

이 빌더의 상태 설계가 수정 방식을 결정했으므로 따로 정리한다.

```
저장한다 (source of truth)          계산한다 (파생, 저장 안 함)
  shardSize    = -1 또는 사용자 값     getShardSize()    = -1 이면 numBuckets * 50
  initialBuffer= -1 또는 사용자 값     getInitialBuffer()= -1 이면 min(10*getShardSize(), 50000)
  numBuckets   = 10 또는 사용자 값
        |
        +-- equals/hashCode 가 보는 것          :234-246
        +-- wire 가 실어야 하는 것               :153-157
        +-- XContent 가 내보내야 하는 것 (-1 제외) :225-230
```

세 면이 모두 **원시 필드**를 다룬다는 것이 이 설계의 규칙이다. 파생 값을 직렬화하면
"미설정"이 "명시값 350"으로 바뀌어 라운드트립 동등성이 깨지고, XContent에 `-1`을
내보내면 재파싱이 setter 검증에 걸린다. 즉 **어느 면에서든 파생 값을 흘리면 상태의
의미가 변질된다.**

같은 원칙이 형제 PR에서도 보인다. `auto_date_histogram`의 빌더가 `RoundingInfo[]`를
직렬화하지 않는 이유도 그것이 타임존과 최소 간격에서 계산되는 파생물이기 때문이다 -
[#151156 README 7.2절](../151156-roundinginfo-serialized-fields/README.md).

## 6. 이 결함의 자리 - 형제 셋과의 대비

같은 렌즈로 찾은 네 건 중 이 건만 방향이 반대다.

```
[정방향]  직렬화 O, equals X          #151152 · #151154 · #151156
            wire  --[size]-->            equals: size 를 안 봄
            증상: 다른 요청이 같다고 판정된다 (조용함)
            수정: equals/hashCode 두 줄
            잡는 테스트: 누락 필드만 다른 not-equal 단언 (새로 써야 함)

[역방향]  equals O, 직렬화 X          #151796  <- 이 PR
            wire  --[  ]-->              equals: shardSize 를 봄
            증상: 파라미터가 무동작한다 (사용자에게 보임)
            수정: wire 포맷 변경 -> TransportVersion 신규 발급
            잡는 테스트: 직렬화 라운드트립 (프레임워크가 이미 제공)
```

역방향이 더 위험한 이유는 좌표 노드와 데이터 노드의 인식이 갈리기 때문이다. 좌표
노드는 두 요청을 다르다고 보는데 데이터 노드는 같게 실행한다. 캐시 쪽으로 보면 더
분명하다 - 샤드 요청 캐시의 키는 직렬화 바이트의 다이제스트이므로
([개념 문서 5절](../../concepts/serialized-state-equality-contract/serialized-state-equality-contract.md)),
파라미터가 wire에 안 실리면 **서로 다른 두 요청이 같은 캐시 키를 갖는다.**
