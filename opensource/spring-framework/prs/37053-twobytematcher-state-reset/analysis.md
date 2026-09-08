# PR #37053 분석 — TwoByteMatcher의 부분 일치 상태가 풀리지 않는 결함

> 기준: 머지 커밋 `7f1966f5f57`(upstream merge `4b5c92703c6`, 2026-08-05 Brian Clozel).
> 이하 `DataBufferUtils.java:NNN`·`AbstractCharSequenceDecoder.java:NNN`은 이 커밋 기준이며,
> `TwoByteMatcher.match(byte)`(`:921-927`)만 **수정 후**에 존재하는 블록이다. "수정 전"은 그 블록이 없던 상태를 뜻한다.
>
> 이 문서는 결함의 인과 사슬만 다룬다. 서사 해설은 README.md, 무대 지도는 structure.md, 테스트별 해설은 tests.md,
> 이해 게이트 문답은 gates.md가 소유한다.

## 0. 결론

**결함**: `DataBufferUtils.TwoByteMatcher`가 `AbstractNestedMatcher.match(byte)`를 그대로 물려받았는데,
그 기본 구현은 **불일치 시 부분 일치 카운터를 되돌리지 않는다**(되감기를 하위 클래스에 위임하는 설계).
형제 구현인 `KnuthMorrisPrattMatcher`는 접미사-접두사 테이블로, `SingleByteMatcher`는 무상태로 각자 답을 갖고 있었지만
`TwoByteMatcher`만 그 자리가 비어 있었다. 그래서 구분자 첫 바이트를 한 번 맞추면 `matches`가 1에 얼어붙어,
사이에 몇 바이트가 끼든 나중에 나타난 둘째 바이트가 거짓으로 매치를 완성한다.

**증상**: 기본 구분자 `\r\n`과 `\n`을 쓰는 `StringDecoder`에서, 줄 안에 홀로 있는 `\r`이 있으면
`CompositeMatcher`의 최장 우선 규칙이 거짓 `\r\n`(길이 2)을 진짜 `\n`(길이 1)보다 선호하고,
`AbstractCharSequenceDecoder`가 보고된 길이만큼 뒤에서 잘라내므로 **본문 한 글자가 예외도 로그도 없이 사라진다**.
`"a\rXY\nb"`가 `["a\rXY", "b"]`가 아니라 `["a\rX", "b"]`로 디코딩된다.

**수정**: `TwoByteMatcher`가 `match(byte)`를 오버라이드해, 부분 일치 상태에서 기대하지 않은 바이트가 오면
`setMatches(0)`으로 되감은 뒤 `super.match(b)`에 위임한다(`DataBufferUtils.java:921-927`, 본문 8줄).

**상태**: MERGED. 2026-08-05 Brian Clozel이 리뷰 코멘트 없이 병합. 라벨 `type: bug`, `in: core`.

## 1. 무대

결함이 사는 자리, 그것이 의존하는 기본 구현, 증폭과 손실이 확정되는 지점이 서로 다른 파일에 흩어져 있다.

| 축 | 값 |
|---|---|
| 모듈 | `spring-core` (실제 피해자는 웹 스택) |
| 파일 | `spring-core/src/main/java/org/springframework/core/io/buffer/DataBufferUtils.java` |
| 결함 지점 | `DataBufferUtils.TwoByteMatcher` (`:914-928`) — 정확히는 `match(byte)` 오버라이드의 **부재** |
| 결함이 의존하는 기본 구현 | `AbstractNestedMatcher#match(byte)` `:889-896` |
| 증폭 지점 | `CompositeMatcher#match(DataBuffer)`의 최장 우선 `:775-779` |
| 손실 확정 지점 | `AbstractCharSequenceDecoder#processDataBuffer` `:130-172`, 특히 `:147-151` |
| 공개 진입 API | `DataBufferUtils.matcher(byte[])` `:689` / `DataBufferUtils.matcher(byte[]...)` `:700` / 인터페이스 `DataBufferUtils.Matcher` `:724` |

`Matcher`는 여러 개로 쪼개져 도착하는 `DataBuffer` 스트림에서 구분자 위치를 찾아 주는 **상태를 가진** 도구다.
상태를 갖는 이유는 스트리밍에서 구분자가 버퍼 경계에 걸쳐 쪼개져 도착하기 때문이다(`\r`이 앞 버퍼 끝, `\n`이 다음 버퍼 앞).
그 "호출을 넘어 유지되는 부분 일치 상태"가 이 매처의 존재 이유이자 이번 결함의 재료다.

누가 부르나. 소비자는 두 갈래다. (1) `spring-core`의 `AbstractCharSequenceDecoder`와 그 파생인
`StringDecoder`·`CharBufferDecoder` — WebFlux에서 텍스트나 `String` 본문을 디코딩하면 반드시 지나간다
(`BaseDefaultCodecs`가 기본 코덱으로 등록, SSE 한 줄 파싱, RSocket 페이로드 포함).
(2) `spring-web`의 멀티파트 파서 두 종류. 다만 (2)의 구분자는 `--boundary`, `CRLF--boundary`, `CRLFCRLF`로
모두 3바이트 이상이라 `KnuthMorrisPrattMatcher` 갈래로 가므로 **이 결함의 영향을 받지 않았다**.
즉 `TwoByteMatcher`를 실제로 태우는 상용 경로는 문자 디코더의 `\r\n` 하나였고, 그 하나가 웹 스택에서
가장 흔한 길목이라는 비대칭이 이 PR의 성격을 규정한다.

## 2. 전체 메서드 그래프

팩토리에서 소비, 매칭까지를 한 장에 펼치면 결함이 심어지는 자리와 손실이 확정되는 자리가 갈라져 보인다.

```
  [ 팩토리 — 구분자 "길이만" 보고 구현을 고른다 ]

  DataBufferUtils.matcher(byte[]... delimiters)                DataBufferUtils.java:700
      |-- delimiters.length == 0  -> Assert 실패                            :701
      |-- delimiters.length == 1  -> createMatcher(delimiters[0])           :702
      +-- 2개 이상               -> new CompositeMatcher(delimiters)       :702, :756
                                        initMatchers: 각 구분자마다 createMatcher  :760-766
  createMatcher(byte[] delimiter)                                          :705
      switch (delimiter.length)                                            :709
        case 1 -> delimiter[0]==10 ? SingleByteMatcher.NEWLINE_MATCHER : new SingleByteMatcher(...)  :710
        case 2 -> new TwoByteMatcher(delimiter)            [!] 결함이 살던 갈래  :711
        default-> new KnuthMorrisPrattMatcher(delimiter)                   :712


  [ 소비 — 디코드 호출 하나당 매처 하나 ]

  AbstractCharSequenceDecoder.decode(input, elementType, mimeType, hints)  AbstractCharSequenceDecoder.java:97
      delimiterBytes = getDelimiterBytes(mimeType)                          :100
          DEFAULT_DELIMITERS = List.of("\r\n", "\n")                        :56   <- 구분자 2개
      chunks  = new LimitedDataBufferList(maxInMemorySize)                  :102
      matcher = DataBufferUtils.matcher(delimiterBytes)                     :103
          => CompositeMatcher{ TwoByteMatcher({13,10}), SingleByteMatcher.NEWLINE_MATCHER }
      Flux.from(input).concatMapIterable(buffer -> processDataBuffer(buffer, matcher, chunks))  :106
                                  |
                                  v
  processDataBuffer(buffer, matcher, chunks)                                :130
      do {
          endIndex = matcher.match(buffer)                                  :137
          if (endIndex == -1) { chunks.add(buffer); release = false; break; }  :138-142
          split = buffer.split(endIndex + 1)                                :143
          delimiterLength = matcher.delimiter().length                      :147
          if (chunks.isEmpty()) {
              if (stripDelimiter) split.writePosition(split.writePosition() - delimiterLength)  :149-151
              result.add(split)                                             :152
          } else { chunks.add(split); joined = join(chunks); ... }          :154-162
      } while (buffer.readableByteCount() > 0)                              :164
                                  |
      [!] delimiterLength 를 매처가 보고한 값으로 그대로 믿는다 =
          거짓 매치가 "본문에서 몇 바이트를 떼어낼지"를 직접 결정한다


  [ 매칭 — 위치 하나마다 모든 자식을 함께 전진 ]

  CompositeMatcher.match(DataBuffer)                          DataBufferUtils.java:768
      longestDelimiter = NO_DELIMITER                                       :770
      for (pos = readPosition .. writePosition-1)                           :772
          b = dataBuffer.getByte(pos)                                       :773
          for (matcher : matchers)                                          :775
              if (matcher.match(b) && matcher.delimiter().length > longestDelimiter.length)  :776
                  longestDelimiter = matcher.delimiter()                    :777
          if (longestDelimiter != NO_DELIMITER) { reset(); return pos; }     :781-784
      return -1                                                             :786

  AbstractNestedMatcher.match(DataBuffer)   (단일 매처 경로)                 :878
      matchPosition = dataBuffer.forEachByte(start, end-start, b -> !this.match(b))  :882
          ^ 가상 디스패치 -> TwoByteMatcher 오버라이드가 자동 적용
      if (matchPosition != -1) reset()                                      :883-885
      return matchPosition                                                  :886
          [!] 못 찾았으면 reset 하지 않는다 = 부분 일치 상태를 다음 버퍼로 넘긴다 (정상 동작)

  AbstractNestedMatcher.match(byte b)       (되감기 없는 기본 구현)          :889
      if (b == delimiter[matches]) { matches++; return matches == length; }  :891-894
      return false                                        [!] matches 를 건드리지 않는다  :895

  KnuthMorrisPrattMatcher.match(byte b)                                     :960
      while (getMatches() > 0 && b != delimiter()[getMatches()])            :962
          setMatches(this.table[getMatches() - 1])                          :963
      return super.match(b)                                                 :965

  TwoByteMatcher.match(byte b)              [!] 이 PR 이 추가한 블록          :921
      if (getMatches() > 0 && b != delimiter()[getMatches()])               :923
          setMatches(0)                                                     :924
      return super.match(b)                                                 :926
      (수정 전: 이 오버라이드 자체가 없어 :889 기본 구현이 그대로 쓰였다)
```

## 2.5 핵심 이름표 사전

이 무대에서 헷갈리는 것은 "match"라는 이름이 두 가지 계약을 동시에 가리킨다는 점이다.
`match(DataBuffer)`는 **버퍼 안에서 구분자 마지막 바이트의 인덱스 또는 -1**을 돌려주고,
`match(byte)`는 **이 한 바이트로 구분자가 완성되었는가**를 돌려준다. 아래 항목은 그 구분을 명시한다.

### 2.5.1 팩토리와 공개 계약

바깥에서 보이는 이름은 팩토리 셋과 인터페이스 메서드 넷이 전부다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `matcher(byte[])` `:689` | 구분자 하나짜리 매처 생성 | `byte[]` -> `Matcher` | 테스트, 단일 구분자 소비자 | 매처 층 테스트가 이 경로를 써서 `CompositeMatcher` 없이 `TwoByteMatcher`를 단독 관찰한다 |
| `matcher(byte[]...)` `:700` | 구분자 여럿이면 `CompositeMatcher`, 하나면 위와 동일 | `byte[][]` -> `Matcher` | `AbstractCharSequenceDecoder.decode` `:103` | 구분자가 둘이라 증상 층에서만 최장 우선 증폭이 재현된다 |
| `createMatcher(byte[])` `:705` | **길이만 보고** 구현을 고르는 분기 | `byte[]` -> `NestedMatcher` | `matcher(...)`, `CompositeMatcher.initMatchers` | 길이 2 갈래를 타는 상용 경로가 문자 디코더의 `\r\n` 하나뿐이라 결함이 오래 숨었다 |
| `Matcher.match(DataBuffer)` `:730` | 첫 매치 구분자의 **마지막 바이트 인덱스**, 없으면 -1 | `DataBuffer` -> `int` | `processDataBuffer` `:137` | 결함 시 진짜 `\n` 위치를 반환하되 `delimiter()`가 길이 2를 보고한다 |
| `Matcher.delimiter()` `:735` | **직전** `match(DataBuffer)`에서 맞은 구분자 | 없음 -> `byte[]` | `processDataBuffer` `:147` | 이 배열의 `length`가 잘라낼 바이트 수를 직접 결정한다 |
| `Matcher.reset()` `:740` | 상태 초기화 | 없음 -> void | 매치 성립 시 내부에서 자동 호출 | 결함은 reset 시점이 아니라 **미스매치 시 되감기 부재**다 |
| `NestedMatcher.match(byte)` `:814` | 한 바이트씩 함께 전진하기 위한 내부 계약 | `byte` -> `boolean`(구분자 완성 여부) | `CompositeMatcher.match` `:776`, `AbstractNestedMatcher.match(DataBuffer)`의 람다 `:882` | 결함이 사는 계약 |

### 2.5.2 매처 구현들

구현 쪽 이름표는 네 매처가 상태를 어떻게 다루는지, 그리고 그중 어느 자리가 비어 있었는지를 드러낸다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `CompositeMatcher.matchers` `:752` | 자식 매처 배열(구분자마다 하나) | - | `match`/`reset`이 순회 | `\r\n`용 `TwoByteMatcher`와 `\n`용 `SingleByteMatcher`가 나란히 들어간다 |
| `CompositeMatcher.longestDelimiter` `:754` | 현재 위치에서 맞은 것 중 **가장 긴** 구분자 | - | `match`가 위치마다 갱신 `:777` | 거짓 매치라도 길기만 하면 채택된다. 증폭 통로 |
| `NO_DELIMITER` `:749` | 길이 0 센티널(`byte[0]`) | - | 초기화·판정 `:770,:781` | "이번 위치에서 아무것도 안 맞았다"의 표현 |
| `SingleByteMatcher.NEWLINE_MATCHER` `:824` | `{10}` 전용 공유 상수 | - | `createMatcher` `:710` | 상태가 없어 공유해도 안전. `reset()`도 빈 구현 `:851` |
| `SingleByteMatcher.match(byte)` `:841` | `delimiter[0] == b` 순수 비교 | `byte` -> `boolean` | `CompositeMatcher.match` | 무상태라 되감기 문제가 성립하지 않는다 |
| `AbstractNestedMatcher.delimiter` `:861` | 찾을 구분자 바이트열(final) | - | `match(byte)`의 비교 대상 | - |
| `AbstractNestedMatcher.matches` `:863` | **부분 일치 카운터**. "구분자의 몇 바이트까지 연속으로 맞췄나" | - | `match(byte)`가 증가 `:892`, `reset()`이 0 복귀 `:904` | **결함의 중심 상태**. 수정 전에는 미스매치 시 1에 얼어붙었다 |
| `getMatches()` / `setMatches(int)` `:874` / `:870` | protected 접근자. 파일 내 유일 사용처가 하위 클래스의 미스매치 폴백 | - | `KnuthMorrisPrattMatcher.match` `:962-963`, 수정 후 `TwoByteMatcher.match` `:923-924` | 접근자의 존재 자체가 "폴백은 하위 클래스 몫"이라는 설계 신호였다 |
| `AbstractNestedMatcher.match(DataBuffer)` `:878` | `forEachByte`로 바이트 단위 `match`에 위임, 찾았을 때만 `reset` | `DataBuffer` -> `int` | 단일 매처 경로 | 못 찾았을 때 상태를 유지하는 것이 **정상 동작**이라 되감기 부재가 그대로 오염으로 남는다 |
| `AbstractNestedMatcher.match(byte)` `:889` | 기대 바이트면 카운터 증가, 아니면 `false`만 반환 | `byte` -> `boolean` | 위 람다, `CompositeMatcher` | **미스매치 경로에 되감기가 없다.** 버그가 아니라 의도된 위임 계약 |
| `TwoByteMatcher(byte[])` `:916` | 길이 2 검증만 하는 생성자 | - | `createMatcher` `:711` | 수정 전에는 클래스 전체가 이 생성자뿐이었다 |
| `TwoByteMatcher.match(byte)` `:921` | 부분 일치 중 기대와 다른 바이트가 오면 0으로 되감고 `super`에 위임 | `byte` -> `boolean` | 상동 | **이 PR이 추가한 8줄** |
| `KnuthMorrisPrattMatcher.table` `:937` | 접미사-접두사 길이표 | - | `match(byte)`의 되감기 목적지 | 길이 2에서는 `table[0]`만 참조되고 그 값은 항상 0 `:946` |
| `longestSuffixPrefixTable(byte[])` `:944` | 위 표를 만드는 정적 헬퍼. `result[0] = 0`으로 시작 | `byte[]` -> `int[]` | 생성자 `:941` | `if` + `setMatches(0)`이 KMP `while`의 **등가 접힘**임을 보증하는 근거 |
| `KnuthMorrisPrattMatcher.match(byte)` `:960` | 표를 타고 되감은 뒤 `super.match(b)` | `byte` -> `boolean` | 길이 3+ 구분자 | 수정이 그대로 본뜬 형제 구현 |

### 2.5.3 소비 측 (`AbstractCharSequenceDecoder.java`)

소비 측 이름표는 매처의 보고가 실제 문자열 손실로 바뀌는 자리를 짚는다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `DEFAULT_DELIMITERS` `:56` | `List.of("\r\n", "\n")` | - | 생성자 기본값, `StringDecoder.allMimeTypes()` 등 | 구분자가 둘이라 `CompositeMatcher` 경로가 켜지고 최장 우선이 개입한다 |
| `stripDelimiter` `:61` | 방출 전에 구분자를 떼어낼지 | - | `processDataBuffer` `:149,:157` | false면 자르지 않으므로 이 결함의 글자 손실도 일어나지 않는다(경계 조건) |
| `delimitersCache` `:65` | 문자셋별 구분자 바이트 캐시 | `Charset` -> `byte[][]` | `getDelimiterBytes` `:121` | 결함과 무관 |
| `decode(...)` `:97` | 스트림 하나당 `chunks`와 `matcher`를 **한 벌만** 만든다 | `Publisher<DataBuffer>` -> `Flux<T>` | WebFlux 코덱 | 매처가 요청 하나의 본문 스트림에 종속. 요청 사이 상태 누수는 없다 |
| `chunks` (지역) `:102` | 아직 구분자를 못 만난 조각들(`LimitedDataBufferList`) | - | `processDataBuffer` | 비어 있지 않으면 join 후 자르는 두 번째 분기 `:154-162` |
| `processDataBuffer(...)` `:130` | 버퍼 하나에서 구분자를 반복해서 찾아 자른다 | (buffer, matcher, chunks) -> `Collection<DataBuffer>` | `concatMapIterable` `:106` | 손실이 실제로 발생하는 메서드 |
| `endIndex` (지역) `:137` | `matcher.match(buffer)` 결과. 구분자 마지막 바이트 인덱스 | - | `split` 위치 계산 `:143` | 결함 시 진짜 `\n`의 위치가 들어온다(여기까지는 맞다) |
| `split` (지역) `:143` | `buffer.split(endIndex + 1)`. 앞쪽 조각(구분자 포함) | - | 방출 대상 | `"a\rXY\n"` 5바이트 |
| `delimiterLength` (지역) `:147` | `matcher.delimiter().length` | - | `writePosition` 조정 `:150,:158` | **결함이 여기서 값으로 전달된다.** 1이어야 할 값이 2로 온다 |
| `release` (지역) `:133` | 버퍼 소유권이 `chunks`로 넘어갔는지 | - | `finally` `:167-171` | 결함과 무관하지만 오독하기 쉬운 자리 |

## 3. 결함 경로 단계 추적

구분자는 `\r\n` = `{13, 10}`이고 `matches`는 0에서 시작한다. `TwoByteMatcher` 하나의 카운터를 따라간다.

### 3.1 정상 케이스 `"a\r\nb"` (수정 전후 동일)

연속된 구분자에서는 카운터가 한 번도 되감길 일이 없으므로 수정 전후 흐름이 같다.

| 위치 | 바이트 | 진입 시 `matches` | 판정 | 종료 시 `matches` | `match(byte)` 반환 |
|---|---|---|---|---|---|
| 0 | `a` | 0 | `a != delimiter[0]`(13) | 0 | false |
| 1 | `\r` | 0 | `13 == delimiter[0]` | 1 | false (1 != 2) |
| 2 | `\n` | 1 | `10 == delimiter[1]` | 2 | **true** |

`match(DataBuffer)`가 인덱스 2를 반환하고 `delimiter()`는 길이 2를 보고한다. `split`은 `"a\r\n"` 3바이트,
`writePosition(3 - 2)`로 `"a"`가 남는다. 옳다. 같은 위치에서 `SingleByteMatcher`도 맞지만 최장 우선이
길이 2를 고르므로 `\r`이 본문에 남지 않는다 — 최장 우선은 정상 입력에서 **필수** 규칙이다.

### 3.2 결함 케이스 `"a\rXY\nb"` (수정 전)

여기서는 카운터가 위치 2에서 1로 얼어붙고, 그 잔류가 위치 4에서 거짓 매치를 완성한다.

| 위치 | 바이트 | 진입 시 `matches` | 기본 구현 `:889`의 판정 | 종료 시 `matches` | 반환 |
|---|---|---|---|---|---|
| 0 | `a` | 0 | `a != 13` | 0 | false |
| 1 | `\r` | 0 | `13 == delimiter[0]` | 1 | false |
| 2 | `X` | 1 | `X != delimiter[1]`(10) -> `return false`, **카운터 미조정** | **1 (잔류)** [!] | false |
| 3 | `Y` | 1 | 동일 | **1 (잔류)** | false |
| 4 | `\n` | 1 | `10 == delimiter[1]` | 2 | **true (거짓 매치)** |

같은 위치 4에서 `SingleByteMatcher`(`{10}`)도 true지만, `CompositeMatcher`가 더 긴 `{13,10}`을 채택한다(`:776-777`).
그 뒤가 손실이다.

| 하류 단계 | 값 | 비고 |
|---|---|---|
| `CompositeMatcher.match` 반환 `:783` | `4` | 위치 자체는 진짜 `\n`이라 맞다 |
| `matcher.delimiter().length` `:147` | **2** | 실제 구분자는 `\n` 1바이트인데 2로 보고 |
| `buffer.split(4 + 1)` `:143` | `split = "a\rXY\n"` (5바이트) | - |
| `split.writePosition(5 - 2)` `:150` | `"a\rX"` | `\n`은 구분자라 지워지는 게 맞지만 `Y`는 본문인데 함께 잘린다 |
| 최종 방출 | `["a\rX", "b"]` | 기대는 `["a\rXY", "b"]`. 예외도 로그도 없다 |

**버퍼 경계를 넘어도 같다.** `matches`는 `match(DataBuffer)`가 못 찾았을 때 초기화되지 않으므로(`:883-885`),
`"a\r"`과 `"Xb\n"` 두 버퍼로 나눠 보내면 첫 버퍼에서 `matches = 1`이 남고 둘째 버퍼의 `X`가 그것을 풀지 못한 채
`\n`에서 거짓 매치가 성립한다. 결과는 `"a\rXb"`가 아니라 `"a\rX"`.

### 3.3 수정 후 같은 입력

되감기가 들어오면 같은 입력에서 카운터가 위치 2부터 0으로 풀려 거짓 매치가 성립하지 않는다.

| 위치 | 바이트 | 진입 `matches` | `:923` 조건 | 되감기 후 `super.match(b)` `:889` | 종료 `matches` | 반환 |
|---|---|---|---|---|---|---|
| 1 | `\r` | 0 | `getMatches() > 0` 거짓 -> 건너뜀 | `13 == delimiter[0]` -> 1 | 1 | false |
| 2 | `X` | 1 | 참(`X != 10`) -> `setMatches(0)` | `X != delimiter[0]`(13) | 0 | false |
| 3 | `Y` | 0 | 거짓 | `Y != 13` | 0 | false |
| 4 | `\n` | 0 | 거짓 | `10 != delimiter[0]`(13) | 0 | **false** |

`TwoByteMatcher`는 더 이상 맞지 않고 `SingleByteMatcher`만 맞으므로 `longestDelimiter = {10}`,
`delimiterLength = 1` -> `"a\rXY"`가 보존된다.

**되감은 바이트를 버리지 않는다.** `super.match(b)`에 위임하는 **순서**가 계약의 일부다. 카운터를 0으로 되돌린
직후 기본 구현이 같은 바이트를 `delimiter[0]`과 다시 비교하므로, 되감은 그 바이트가 새 구분자의 시작인 경우를
놓치지 않는다. `"a\r\rX\nb"`가 그 경우다.

| 위치 | 바이트 | 진입 `matches` | `:923` 조건 | `super.match(b)` | 종료 `matches` |
|---|---|---|---|---|---|
| 1 | `\r` | 0 | 거짓 | `13 == delimiter[0]` | 1 |
| 2 | `\r` | 1 | 참(`13 != 10`) -> `setMatches(0)` | `13 == delimiter[0]` -> **재시작** | 1 |
| 3 | `X` | 1 | 참 -> `setMatches(0)` | `X != 13` | 0 |
| 4 | `\n` | 0 | 거짓 | `10 != 13` | 0 |

즉 두 번째 `\r`이 새 부분 일치로 인정되므로, 그 다음에 `\n`이 **바로** 왔다면 정상적으로 매치된다.
여기서는 `X`가 끼어 있으므로 최종 결과는 `-1`이 맞다.

## 4. 계약과 위반

이 무대의 계약 일곱 가지 중 결함이 어기는 것은 둘뿐이고, 나머지는 전제이거나 수정이 지켜야 할 제약이다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| 매처는 **연속된** 구분자 시퀀스 위치만 매치한다 | `Matcher.match(DataBuffer)` javadoc "Find the first matching delimiter" `:727-729` | 위반. 비연속 두 바이트가 매치되어 데이터가 유실된다 |
| 부분 일치 상태는 `DataBuffer` 경계를 넘어 유지된다 | `AbstractNestedMatcher.match(DataBuffer)`가 못 찾았을 때 `reset`하지 않음 `:883-885` | 위반 아님. **의도된 동작**이며, 그래서 되감기 누락이 그대로 오염으로 남는다 |
| 미스매치 시 어디로 되감을지는 **하위 클래스가 정한다** | `AbstractNestedMatcher.match(byte)`의 미스매치 경로가 `matches`를 건드리지 않음 `:895`; protected `getMatches`/`setMatches`의 유일 사용처가 하위 클래스 오버라이드 | 위반. 이 위임을 `TwoByteMatcher`만 이행하지 않았다 |
| 진짜(연속) 구분자는 폴백에 영향받지 않는다 | 수정의 둘째 조건 `b != delimiter()[getMatches()]`가 거짓이면 되감기를 건너뜀 `:923` | 수정이 유지. 거짓 양성만 제거하고 참 양성은 건드리지 않는다 |
| `match(byte)` 진입 시 `matches`는 0 이상 `length-1` 이하 | `length` 도달 즉시 true 반환 후 외곽 `match(DataBuffer)`가 `reset` `:883-885`; `CompositeMatcher`도 채택 시 `reset` `:782` | 유지. 그래서 `delimiter()[getMatches()]` 인덱싱이 항상 in-bounds다 |
| `delimiter()`가 보고한 길이만큼 본문 뒤에서 잘라낸다 | `AbstractCharSequenceDecoder.processDataBuffer` `:147-151` | 결함이 아니라 전제. 이 전제 때문에 거짓 매치가 곧바로 글자 손실이 된다 |
| `CompositeMatcher`는 맞은 것 중 가장 긴 구분자를 고른다 | `:776-779` | 결함이 아니라 전제이자 증폭 통로. 정상 입력에서는 필수 규칙이다 |

**함정 하나.** 기본 구현이 미스매치 시 리셋하지 않는 것은 버그처럼 보이지만 의도된 위임 계약이다.
기본 구현을 "고쳐서" 리셋하게 만들면 `KnuthMorrisPrattMatcher`의 백트랙 전제가 깨져 회귀한다.
수정은 폴백을 빠뜨린 하위 클래스에 국한해야 한다.

## 5. 수정안

### 5.1 채택한 수정 — 빠져 있던 되감기를 형제 구현과 같은 형태로 채운다

수정 전 이 클래스는 생성자 하나뿐이었고, 수정은 형제 구현과 같은 모양의 `match(byte)` 오버라이드를 더한다.

```java
// before (DataBufferUtils.java:914-919, 클래스 전체가 생성자뿐이었다)
private static class TwoByteMatcher extends AbstractNestedMatcher {

	protected TwoByteMatcher(byte[] delimiter) {
		super(delimiter);
		Assert.isTrue(delimiter.length == 2, "Expected a 2-byte delimiter");
	}
}

// after (DataBufferUtils.java:914-928)
private static class TwoByteMatcher extends AbstractNestedMatcher {

	protected TwoByteMatcher(byte[] delimiter) {
		super(delimiter);
		Assert.isTrue(delimiter.length == 2, "Expected a 2-byte delimiter");
	}

	@Override
	public boolean match(byte b) {
		if (getMatches() > 0 && b != delimiter()[getMatches()]) {
			setMatches(0);
		}
		return super.match(b);
	}
}
```

**왜 그 위치인가.** 세 가지가 이 좌표를 강제한다.

1. **계약의 소유자가 여기다.** 되감기는 `AbstractNestedMatcher`가 하위 클래스에 위임한 책임이고,
   형제 둘은 각자 이행했다. 누락된 클래스에 그 이행을 채우는 것이 가장 좁은 수정이다.
2. **가상 디스패치가 배선을 대신한다.** `AbstractNestedMatcher.match(DataBuffer)`가 람다 안에서
   `this.match(b)`를 부르므로(`:882`), 오버라이드만 하면 단일 매처 경로와 `CompositeMatcher` 경로
   양쪽에 자동으로 적용된다. 별도 연결 작업이 필요 없어 본문 8줄로 끝난다.
3. **KMP의 등가 접힘이다.** 길이 2 구분자에서 부분 일치 상태는 `matches == 1` 하나뿐이고,
   그때 KMP가 참조하는 값은 언제나 `table[0]`이며 `longestSuffixPrefixTable`은 `result[0] = 0`으로 시작한다(`:946`).
   따라서 되감기는 반드시 한 번에 0으로 끝난다. `while`이 `if`로, 테이블 조회가 상수 0으로 줄어든 것은
   축약이 아니라 **이 경우에 접힌 등가 구현**이고, 그 등가성이 코드에서 읽힌다.

### 5.2 검토하고 기각한 대안

같은 증상을 없애는 다른 네 접근을 검토했고, 각각 다음 이유로 밀렸다.

| 대안 | 기각 이유 |
|---|---|
| `AbstractNestedMatcher.match(byte)`의 미스매치 경로에서 `matches = 0`으로 리셋 | `KnuthMorrisPrattMatcher`가 그 자리를 **자기 테이블로 되감는 전제**로 오버라이드하고 있다. base가 먼저 0으로 밀면 KMP의 부분 재사용이 깨져 길이 3+ 구분자에서 회귀한다. 클래스 javadoc이 아니라 protected 접근자의 사용처가 그 설계를 말해 준다 |
| 길이 2에도 `KnuthMorrisPrattMatcher`를 쓰도록 `createMatcher`의 `case 2`를 삭제 | 동작은 맞아지지만 `TwoByteMatcher`의 존재 이유(길이 2는 KMP 테이블에서 얻을 이득이 없다)를 부정한다. 클래스 javadoc이 그 판단을 명시하고 있고, 그 판단 자체는 옳았다 |
| `CompositeMatcher`에서 채택 직전에 "정말 연속인가"를 재검증 | 거짓 매치를 만드는 쪽이 아니라 소비하는 쪽에 검증을 붙이는 것이라 원인이 남는다. 단일 매처 경로(`matcher(byte[])` 하나짜리)에는 `CompositeMatcher`가 없으므로 그 경로가 안 고쳐진다 |
| `processDataBuffer`에서 `delimiterLength`를 신뢰하지 않고 실제 바이트를 확인 | 소비 측 전부에 방어 코드를 흩뿌리게 된다. `delimiter()`가 보고한 길이를 믿는 것은 `Matcher` 인터페이스의 계약이고, 계약을 어긴 쪽을 고치는 것이 맞다 |

### 5.3 테스트 배치

테스트는 두 층으로 나뉘고, 갈리는 기준은 `CompositeMatcher`의 개입 여부다.
`matcher(delims)`에 2바이트 구분자 **하나만** 넘기면 `createMatcher`가 `TwoByteMatcher`를 직접 만들어
최장 우선 규칙이 끼어들지 않은 상태로 상태 기계만 관찰할 수 있다.

| 테스트 | 파일 | 층 | fix 전 | 고정하는 것 |
|---|---|---|---|---|
| `matcherDoesNotMatchAcrossNonContiguousDelimiterBytes` | `DataBufferUtilsTests` | 매처 | red | 되감기의 존재 (`"a\rXY\nb"` -> `-1`) |
| `matcherMatchesContiguousTwoByteDelimiter` | 〃 | 매처 | green | 참 양성 보존 (`"a\r\nb"` -> `2`) |
| `matcherDoesNotMatchAfterRepeatedFirstDelimiterByte` | 〃 | 매처 | red | 되감기 직후 재시도 경로의 무오염 (`"a\r\rX\nb"` -> `-1`) |
| `decodePreservesCharacterBeforeLoneNewlineAfterCarriageReturn` | `StringDecoderTests` | 증상 | red | 한 버퍼 안에서 글자 보존 |
| `decodePreservesCharacterAcrossBuffersAfterCarriageReturn` | 〃 | 증상 | red | 호출 경계를 넘는 상태 유지 하에서도 글자 보존 |

가드가 하나뿐인 것은 수정이 좁기 때문이다. 바꾼 것은 거짓 양성을 만드는 상태 잔류 하나이고,
그 상태 잔류에 의존하는 정상 동작은 존재하지 않는다. 매처 층 세 건은
`@ParameterizedDataBufferAllocatingTest`로 여섯 가지 버퍼 팩터리에 대해 반복 실행된다. 상세는 tests.md 소유.

## 6. 범위 밖과 인접 영향

### 6.1 같은 패턴의 다른 위치 — 형제들은 이미 채워져 있었다

네 구현의 미스매치 폴백을 나란히 놓으면 빈칸이 하나뿐임이 바로 보인다.

| 구현 | 미스매치 폴백 | 상태 |
|---|---|---|
| `SingleByteMatcher` `:822` | 불필요 | 무상태(`delimiter[0] == b`). 되감기 문제가 성립하지 않고 `reset()`도 빈 구현 `:851` |
| `TwoByteMatcher` `:914` | **누락 -> 이 PR이 채움** | 길이 2 |
| `KnuthMorrisPrattMatcher` `:935` | 있음 `:960-966` | 접미사-접두사 테이블로 되감기 |
| `CompositeMatcher` `:747` | 해당 없음 | 자식에게 위임하고 자신은 최장 선택만 한다 |

이 표가 결함을 찾은 방법 자체다. 형제 구현들을 나란히 놓고 "이 클래스만 없는 것은 무엇인가"를 물으면
컴파일러도 테스트도 잡지 못하는 종류의 누락이 눈에 보인다.

### 6.2 하위 호환

거짓 양성만 제거하고 참 양성은 그대로 두는 수정이므로, 관측 가능한 변화는 **잘못 잘리던 입력이 안 잘리는 것**뿐이다.
`getMatches() > 0 && b != delimiter()[getMatches()]` 조건이 참이 되는 경우가 곧 "수정 전에 상태가 오염되던 경우"와
정확히 같고, 그 상태 오염에 의존하던 정상 동작은 없다. 공개 API 시그니처·예외 타입·반환 계약은 모두 그대로다.

영향을 받는 소비자는 `TwoByteMatcher` 갈래를 타는 경로 하나 — `\r\n` 구분자를 쓰는 문자 디코딩 —
이며, 멀티파트 파서(구분자 3바이트 이상 -> KMP)와 Jackson 계열의 `CharBufferDecoder.textPlainOnly([",", "\n"], false)`
(1바이트 구분자 둘 -> `SingleByteMatcher` 둘)는 애초에 이 갈래에 오지 않는다.

### 6.3 결함의 나이와 노출면

결함은 2020년 Rossen Stoyanchev의 리팩토링(`fb4363e4e04`, gh-25915)까지 거슬러 올라간다.
그 커밋이 성능을 위해 구분자 길이별로 구현을 분기하면서 길이 2 전용 빠른 경로를 신설했는데,
KMP 테이블이 수행하던 **되감기라는 기능**이 테이블과 함께 버려졌다. 성능을 위한 특수 케이스는 일반 케이스와
동작이 같아야 한다는 것이 이 결함의 일반화된 교훈이고, 이번 수정처럼 "일반 구현을 이 경우에 맞게 접은 형태"로
쓰면 그 등가성이 코드에서 검증 가능해진다.

노출면은 "WebFlux에서 텍스트나 `String` 본문 또는 SSE를 디코딩할 때, 본문에 홀로 있는 `\r`이 나타나는 경우"다.
드문 입력이 아니다 — 사용자가 붙여 넣은 텍스트, 옛 macOS 계열 개행, 텍스트로 읽히는 준-바이너리 페이로드,
CSV/로그 필드 안의 CR이 모두 해당한다. 변경 파일은 `spring-core`인데 피해자는 웹 스택이라는 비대칭이 여기서 나온다.
