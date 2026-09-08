# PR #37053 — 무대 구조와 워크플로우: DataBufferUtils 구분자 매처 계층

> PR #37053의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 PR은 이미 머지됐으므로(`7f1966f5f57`), 아래 file:line 중 `TwoByteMatcher.match(byte)`(`DataBufferUtils.java:922-928`)는 **수정 후** 코드다. "수정 전"이라고 표시한 곳은 그 블록이 없던 상태를 뜻한다.

## 1. 무대 — 실구조

이 PR의 무대는 `DataBufferUtils` 안쪽에 숨어 있는 **구분자 매처 계층**과, 그것을 소비하는 **문자열 디코더**다. 매처 계층은 공개 인터페이스 하나(`Matcher`)와 그 뒤의 비공개 구현 네 개(`CompositeMatcher`·`SingleByteMatcher`·`TwoByteMatcher`·`KnuthMorrisPrattMatcher`)로 되어 있고, 구현 선택은 팩토리 메서드가 구분자 길이만 보고 결정한다. 버그는 네 구현 중 하나가 형제들이 모두 갖고 있던 되감기 처리를 갖지 않은 데서 나왔다.

먼저 타입 계층이다. 상속선과 각 구현이 들고 있는 상태를 함께 표시했다.

```
 public interface DataBufferUtils.Matcher                      DataBufferUtils.java:725
   ├─ int match(DataBuffer)   구분자 마지막 바이트의 인덱스, 없으면 -1     :731
   ├─ byte[] delimiter()      직전 match 에서 맞은 구분자                 :736
   └─ void reset()            상태 초기화                                 :741
        △
        │ implements
        ├──────────────────────────────────────────────┐
        │                                              │
 CompositeMatcher                                private interface NestedMatcher
   (여러 구분자를 동시에 추적)  :748                  extends Matcher              :809
   ├─ static final byte[] NO_DELIMITER = new byte[0]     :750    └─ boolean match(byte b)   :815
   ├─ final NestedMatcher[] matchers                     :753          (한 바이트씩 함께 전진)
   ├─ byte[] longestDelimiter = NO_DELIMITER             :755               △
   ├─ initMatchers(byte[][])                             :761               │ implements
   ├─ match(DataBuffer)  위치 루프 + 최장 구분자 선택    :770        ┌──────┴───────────────┐
   ├─ delimiter()  NO_DELIMITER 면 Assert 실패           :791        │                      │
   └─ reset()  자식 전부 reset                           :797   SingleByteMatcher      AbstractNestedMatcher
        │                                                        (상태 없음)  :823      (abstract)      :860
        └─ 보유 ──────────────────────────────────────→          ├─ static final SingleByteMatcher
                                                                 │    NEWLINE_MATCHER   :825
                                                                 ├─ final byte[] delimiter  :827
                                                                 ├─ match(DataBuffer)       :835
                                                                 ├─ match(byte) → delimiter[0]==b  :842
                                                                 └─ reset() 빈 구현         :852
                                                                                    │
                                        AbstractNestedMatcher (상태 있는 매처의 뼈대)  :860
                                          ├─ final byte[] delimiter                   :862
                                          ├─ int matches = 0        ★ 부분 일치 카운터  :864
                                          ├─ protected setMatches(int) / getMatches()  :871 / :875
                                          ├─ match(DataBuffer)  forEachByte 로 위임    :880
                                          ├─ match(byte)  기대 바이트면 ++, 아니면 false :891
                                          ├─ delimiter()                               :900
                                          └─ reset()  matches = 0                      :905
                                               △                        △
                                               │ extends                │ extends
                                    TwoByteMatcher  :915      KnuthMorrisPrattMatcher  :936
                                      ├─ ctor: 길이 2 검증  :917   ├─ final int[] table      :938
                                      └─ match(byte) 오버라이드     ├─ longestSuffixPrefixTable :945
                                          ★ 이 PR 이 추가  :922-928  └─ match(byte) 오버라이드  :962
                                             getMatches()>0 이고                while 로 table 을 타고 되감기
                                             기대와 다르면 setMatches(0)
                                             후 super.match(b)
```

구현 선택은 팩토리 한 곳에서 구분자 **길이만 보고** 이뤄진다. 이 분기가 이 무대의 지형을 결정한다.

```
 matcher(byte[] delimiter)                                     DataBufferUtils.java:690
   └→ createMatcher(delimiter)
 matcher(byte[]... delimiters)                                              :701
   ├─ delimiters.length == 1 ──→ createMatcher(delimiters[0])               :703
   └─ 2개 이상 ──────────────→ new CompositeMatcher(delimiters)             :703

 createMatcher(byte[] delimiter)                                            :706
   switch (delimiter.length)                                                :710
     case 1 → delimiter[0] == 10 ? SingleByteMatcher.NEWLINE_MATCHER        :711
                                 : new SingleByteMatcher(delimiter)
     case 2 → new TwoByteMatcher(delimiter)                                 :712
     default→ new KnuthMorrisPrattMatcher(delimiter)                        :713
```

소비자 쪽 구조는 문자열 디코더 하나로 요약된다. 매처는 디코더 인스턴스가 아니라 **디코드 호출 하나**에 종속된 상태 객체다.

```
 AbstractCharSequenceDecoder<T extends CharSequence>     AbstractCharSequenceDecoder.java:50
   extends AbstractDataBufferDecoder<T>
   ├─ static final Charset DEFAULT_CHARSET = UTF_8                    :53
   ├─ static final List<String> DEFAULT_DELIMITERS = List.of("\r\n","\n")  :56  ★ 구분자 2개
   ├─ final List<String> delimiters                                   :59
   ├─ final boolean stripDelimiter                                    :61
   ├─ ConcurrentMap<Charset, byte[][]> delimitersCache                :65   ← 문자셋별 바이트 캐시
   ├─ decode(Publisher<DataBuffer>, ...)  final                       :97
   │     └ 호출마다 chunks(LimitedDataBufferList) 와 matcher 를 새로 만든다  :102-103
   ├─ getDelimiterBytes(MimeType)                                     :120
   ├─ processDataBuffer(DataBuffer, Matcher, LimitedDataBufferList)   :130  ★ 자르기 로직
   └─ abstract decodeInternal(DataBuffer, Charset)                    :207
        △                                    △
        │ extends                            │ extends
   StringDecoder    StringDecoder.java:44   CharBufferDecoder   CharBufferDecoder.java:44
     textPlainOnly() :66 / allMimeTypes() :83   textPlainOnly() :67 / allMimeTypes() :84
```

`DEFAULT_DELIMITERS`가 `\r\n`과 `\n` 둘이라는 사실이 결정적이다. 구분자가 둘이므로 `matcher(byte[]...)`가 `CompositeMatcher`를 만들고, 그 안에 `\r\n`용 `TwoByteMatcher`와 `\n`용 `SingleByteMatcher`(정확히는 공유 상수 `NEWLINE_MATCHER`)가 나란히 들어간다.

```
 StringDecoder(기본 설정) 의 매처 구성

  DataBufferUtils.matcher(new byte[][]{ {13,10}, {10} })          :701
    └→ CompositeMatcher                                           :748
         matchers[0] = TwoByteMatcher({13,10})     ← createMatcher case 2  :712
         matchers[1] = SingleByteMatcher.NEWLINE_MATCHER  ← case 1 특례     :711
         longestDelimiter : 매 위치마다 NO_DELIMITER 로 초기화 후 갱신       :771
```

## 2. 수정 전 동작 워크플로우

디코딩은 "버퍼 하나 도착 -> 매처로 구분자 위치 찾기 -> 그 자리에서 자르기 -> 구분자 길이만큼 뒤에서 떼기"를 반복한다. 매처는 버퍼 사이에 걸친 구분자를 잡기 위해 상태를 호출 사이에 유지한다. 정상 시나리오와 결함 시나리오를 차례로 본다.

### 시나리오 A — 정상 입력 `"a\r\nb\n"`

바깥 골격부터다. `decode`는 스트림 전체에 대해 매처와 미완성 조각 목록(`chunks`)을 **한 벌만** 만들고, 도착하는 버퍼마다 `processDataBuffer`를 돌린다.

```
 decode(input, elementType, mimeType, hints)         AbstractCharSequenceDecoder.java:97
   ├─ delimiterBytes = getDelimiterBytes(mimeType)                 :100  (문자셋별 캐시 :121)
   ├─ chunks  = new LimitedDataBufferList(maxInMemorySize)         :102  ← 아직 구분자를 못 만난 조각들
   ├─ matcher = DataBufferUtils.matcher(delimiterBytes)            :103  ← 스트림 하나당 하나
   ├─ Flux.from(input).concatMapIterable(buffer -> processDataBuffer(buffer, matcher, chunks))  :106
   ├─ .concatWith(Mono.defer(...))                                 :107-114
   │     스트림이 끝났는데 chunks 가 남아 있으면 구분자 없이 그대로 마지막 항목으로 방출
   ├─ .doFinally(chunks.releaseAndClear())                         :115
   └─ .map(buffer -> decode(buffer, ...)) → decodeInternal 로 문자열화  :117 → :180
```

안쪽 자르기 루프는 다음과 같다. 인덱스 셈을 그림으로 붙여 두면 `split`과 `writePosition` 조정이 무엇을 하는지 분명해진다.

```
 processDataBuffer(buffer="a\r\nb\n", matcher, chunks)   :130
  do {                                                    :136
    endIndex = matcher.match(buffer)                      :137
      ── 첫 회차: "\r\n" 이 인덱스 1,2 에 있으므로 마지막 바이트 인덱스 2 를 반환
    endIndex == -1 ?                                      :138
      ├─ 예 ──→ chunks.add(buffer); release=false; break  :139-141
      └─ 아니오 ──→ 계속
    split = buffer.split(endIndex + 1)                    :143
      split   = "a\r\n"   (앞쪽 3바이트, 구분자 포함)
      buffer  = "b\n"     (뒤쪽 잔여, 같은 메모리 공유)
    delimiterLength = matcher.delimiter().length          :147   ← 2 (\r\n)
    chunks.isEmpty() ?                                    :148
      ├─ 예 ──→ stripDelimiter 이면 split.writePosition(-2)  :149-151
      │           "a\r\n" → "a"        result 에 추가        :152
      └─ 아니오 ──→ chunks 에 붙여 join 한 뒤 같은 방식으로 뒤에서 자름  :154-161
  } while (buffer.readableByteCount() > 0)                :164
      ── 둘째 회차: 남은 "b\n" 에서 "\n" 이 맞아 endIndex=1 → "b" 방출
  return result = ["a", "b"]
```

구분자가 버퍼 경계에 걸린 경우가 매처의 존재 이유다. 첫 버퍼가 `"a\r"`로 끝나면 `match`는 `-1`을 돌려주고 버퍼 전체가 `chunks`로 들어가지만, 매처 내부의 `matches`는 1로 남아 다음 버퍼의 첫 바이트가 `\n`이면 즉시 매치가 완성된다. **바로 이 "호출을 넘어 유지되는 부분 일치 상태"가 결함의 재료다.**

`CompositeMatcher.match`는 위치 하나마다 모든 자식에게 같은 바이트를 먹이고, 맞은 것 중 가장 긴 구분자를 고른다.

```
 CompositeMatcher.match(dataBuffer)                    DataBufferUtils.java:770
   longestDelimiter = NO_DELIMITER                                   :771
   for (pos = readPosition; pos < writePosition; pos++)              :773
     b = dataBuffer.getByte(pos)                                     :774
     for (matcher : matchers)                                        :776
       matcher.match(b) 이고 그 구분자가 지금까지보다 길면 longestDelimiter 갱신  :777-779
     longestDelimiter != NO_DELIMITER ?                              :782
       ├─ 예 ──→ reset() 후 pos 반환                                 :783-784
       └─ 아니오 ──→ 다음 위치
   return -1                                                          :787
```

"가장 긴 것 우선"은 정상 입력에서 필수다. `\r\n` 자리에서는 `\n` 매처도 함께 맞으므로, 더 긴 `\r\n`을 골라야 `\r`이 본문에 남지 않는다. 다만 이 규칙은 **잘못된 매치도 똑같이 우선**한다.

### 시나리오 B — 수정 전, `"a\rXY\nb"`

`TwoByteMatcher`가 `match(byte)`를 오버라이드하지 않던 상태에서는 `AbstractNestedMatcher.match(byte)`(`DataBufferUtils.java:891-897`)가 그대로 쓰였다. 그 구현은 기대한 바이트가 오면 카운터를 올리고, 아니면 `false`만 돌려줄 뿐 **카운터를 되돌리지 않는다**.

```
 입력 바이트   'a'   '\r'   'X'    'Y'    '\n'   'b'
 위치           0     1      2      3      4      5

 TwoByteMatcher(delimiter = {\r, \n}) 의 matches 변화 (수정 전)
   'a'  : b == delimiter[0]('\r') ?  아니오 → false, matches = 0        :892-896
   '\r' : b == delimiter[0] ?        예     → matches = 1, 1 != 2 → false :893-894
   'X'  : b == delimiter[1]('\n') ?  아니오 → false, matches = 1 로 잔류  ★ 결함
   'Y'  : 마찬가지                          → matches = 1 로 잔류
   '\n' : b == delimiter[1] ?        예     → matches = 2 == length → true
            ↳ 실제 입력은 "\r X Y \n" 인데 연속된 "\r\n" 을 본 것처럼 보고한다

 같은 위치에서 SingleByteMatcher(NEWLINE_MATCHER) 도 true (delimiter[0]=='\n')  :842
 CompositeMatcher: 두 후보 중 더 긴 {\r,\n}(길이 2)을 longestDelimiter 로 채택   :777-779
 → match(buffer) 가 pos = 4 를 반환하고, delimiter() 는 길이 2 를 보고한다

 processDataBuffer 에서의 귀결                     AbstractCharSequenceDecoder.java:143-152
   split = buffer.split(4 + 1)  → "a\rXY\n"  (5바이트)
   delimiterLength = 2                              :147   ← 실제 구분자는 "\n" 1바이트인데
   split.writePosition(5 - 2) → "a\rX"              :150
        ↳ '\n' 은 구분자라 지워지는 게 맞지만 'Y' 는 본문인데 함께 잘린다
   결과: "a\rX" (기대 "a\rXY") — 예외도 로그도 없는 조용한 한 글자 손실
```

상태가 버퍼 호출을 넘어 유지되므로 `"a\r"` + `"Xb\n"` 두 버퍼로 나눠 넣어도 결과는 같다. 첫 버퍼에서 `matches = 1`이 남고, 둘째 버퍼의 `X`가 그것을 풀지 못한 채 `\n`에서 거짓 매치가 성립한다.

### 수정 후

`TwoByteMatcher`가 `KnuthMorrisPrattMatcher`와 같은 형태의 되감기를 갖는다(`DataBufferUtils.java:922-928`).

```
   'X'  : getMatches()==1 > 0 이고 b != delimiter()[1] → setMatches(0)   :924-926
          그 뒤 super.match(b): b == delimiter[0] ? 아니오 → false, matches = 0
   '\n' : matches == 0 이므로 delimiter[0]('\r') 과 비교 → 불일치 → false
          ↳ TwoByteMatcher 는 더 이상 맞지 않는다
   같은 위치에서 SingleByteMatcher 만 true → longestDelimiter = {\n} (길이 1)
   → split = "a\rXY\n", delimiterLength = 1 → "a\rXY"  (본문 보존)
```

## 3. 분기 처리 워크플로우

이 무대의 분기는 매처 선택, 위치별 매치 판정, 그리고 자르기 세 층이다. 버그는 둘째 층의 한 구현에 있었다.

### 3-1. 매처 선택 분기

구현 선택은 구분자 개수와 길이만 보는 두 단계 스위치로 끝난다.

```
 matcher(byte[]... delimiters)                          DataBufferUtils.java:701
   ├─ delimiters.length == 0 ──→ Assert 실패 "Delimiters must not be empty"   :702
   ├─ delimiters.length == 1 ──→ createMatcher(delimiters[0])
   └─ 그 외 ──────────────────→ CompositeMatcher (자식들을 같은 인덱스로 함께 전진)

 createMatcher(byte[] delimiter)                                            :706
   ├─ length == 0 ──→ Assert 실패 "Delimiter must not be empty"              :709
   ├─ length == 1
   │    ├─ delimiter[0] == 10('\n') ──→ 공유 상수 NEWLINE_MATCHER            :711, :825
   │    │      (상태가 없어 공유해도 안전하다 — reset 도 빈 구현 :852)
   │    └─ 그 외 ──→ new SingleByteMatcher(delimiter)
   ├─ length == 2 ──→ new TwoByteMatcher(delimiter)          ★ 결함이 살던 갈래  :712
   └─ length >= 3 ──→ new KnuthMorrisPrattMatcher(delimiter)                    :713
```

여기서 실무적으로 중요한 사실 하나. 길이 2 갈래를 실제로 타는 소비자는 사실상 문자 디코더의 `\r\n` 하나다. 멀티파트 파서가 쓰는 구분자는 `--boundary`, `CRLF--boundary`, `CRLFCRLF`로 모두 3바이트 이상이라 KMP 갈래로 간다(4절 참조). 결함이 오래 남은 배경이다.

### 3-2. 바이트 단위 매치 판정 분기 — 네 구현 비교

같은 `boolean match(byte b)` 계약을 네 구현이 서로 다르게 채운다. 되감기 처리의 유무가 한눈에 드러나도록 나란히 놓는다.

```
 SingleByteMatcher.match(byte b)                        :842
   └─ return delimiter[0] == b          ← 상태 자체가 없으므로 되감기 문제가 성립하지 않음

 AbstractNestedMatcher.match(byte b)  (기본 구현)        :891
   ├─ b == delimiter[matches] ?
   │    ├─ 예 ──→ matches++                              :893
   │    │          matches == delimiter.length ?
   │    │            ├─ 예 ──→ return true  (구분자 완성)  :894
   │    │            └─ 아니오 ──→ return false (부분 일치 유지)
   │    └─ 아니오 ──→ return false                        :896
   │                  ★ matches 를 건드리지 않는다 = 되감기는 하위 클래스의 몫
   └─ (이 빈칸이 문서화되지 않은 하위 클래스 의무였다)

 KnuthMorrisPrattMatcher.match(byte b)                  :962
   ├─ while (getMatches() > 0 && b != delimiter()[getMatches()])   :963
   │      setMatches(table[getMatches() - 1])            :964   ← 접미사-접두사 테이블로 되감기
   └─ return super.match(b)                              :966   ← 되감은 뒤 같은 바이트를 재평가

 TwoByteMatcher.match(byte b)   ★ 이 PR 이 추가한 블록    :922-928
   ├─ getMatches() > 0 && b != delimiter()[getMatches()] ?        :924
   │    └─ 예 ──→ setMatches(0)                          :925
   │              (길이 2 에서 부분 일치는 matches==1 뿐이고
   │               그때 KMP 테이블 값은 언제나 table[0]==0 이므로 while 이 if 로 접힌다)
   └─ return super.match(b)                              :927   ← KMP 와 같은 위임 순서

   수정 전: 이 오버라이드 자체가 없었다 → 기본 구현이 그대로 쓰여 되감기 부재
```

`super.match(b)`에 위임하는 **순서**가 계약의 일부다. 카운터를 0으로 되돌린 직후 기본 구현이 같은 바이트를 `delimiter[0]`과 다시 비교하므로, 되감은 그 바이트가 새 구분자의 시작인 경우를 놓치지 않는다.

```
 입력 "a\r\rX\nb" 에서의 되감기 후 재평가 (수정 후)
   '\r'(1) : matches 0 → 1
   '\r'(2) : matches>0 이고 b != '\n' → setMatches(0)
             super.match: b == delimiter[0]('\r') → matches = 1   ← 새 시작으로 다시 인정
   'X'     : matches>0 이고 b != '\n' → setMatches(0)
             super.match: b != '\r' → false, matches = 0
   '\n'    : matches == 0 → delimiter[0] 과 비교 → 불일치 → false
   → TwoByteMatcher 는 맞지 않고 SingleByteMatcher 만 맞는다 (기대대로)
```

### 3-3. 복합 매처의 최장 우선 분기

복합 매처와 단일 매처는 상태 초기화 시점이 다르고, 그 차이가 부분 일치 상태의 수명을 결정한다.

```
 CompositeMatcher.match(dataBuffer)                     :770
   위치 pos 마다
     ├─ 모든 자식에게 같은 바이트 b 를 먹인다                         :776
     ├─ 자식이 true 이고 그 구분자가 현재 longestDelimiter 보다 길면 교체  :777-779
     │     ★ 잘못된 매치라도 길기만 하면 채택된다 (수정 전 결함의 증폭 통로)
     └─ longestDelimiter 가 갱신됐으면                                 :782
          ├─ reset() 로 자식 상태를 모두 0 으로                        :783 → :797
          └─ pos 반환 (구분자 마지막 바이트의 인덱스)                   :784
   끝까지 못 찾으면 -1                                                  :787

 단일 매처 경로 (AbstractNestedMatcher.match(DataBuffer))              :880
   ├─ forEachByte(start, end-start, b -> !this.match(b))               :883
   │     forEachByte 는 처리를 멈춘 위치를 반환하고, 끝까지 처리하면 -1  DataBuffer.java:197-198
   │     즉 match(byte) 가 true 를 낸 첫 위치가 그대로 반환된다
   └─ matchPosition != -1 이면 reset()                                 :884-886
        (찾았으면 다음 탐색을 위해 상태를 비우고, 못 찾았으면 부분 일치를 유지한다 ★)
```

마지막 줄이 이 무대의 핵심 성질이다. **못 찾았을 때 상태를 유지하는 것이 정상 동작**이고, 그래서 되감기를 하위 클래스가 정확히 구현해 주지 않으면 그 상태가 그대로 오염된다.

### 3-4. 자르기 분기

디코더는 매처가 보고한 구분자 길이를 그대로 믿고 본문 뒤에서 그만큼을 떼어낸다.

```
 processDataBuffer(buffer, matcher, chunks)      AbstractCharSequenceDecoder.java:130
   do {
     endIndex = matcher.match(buffer)                                     :137
     ├─ endIndex == -1                                                    :138
     │    └─ chunks.add(buffer); release = false; break                   :139-141
     │       (버퍼 소유권이 chunks 로 넘어가므로 finally 의 release 를 끈다 :168-170)
     └─ endIndex >= 0
          split = buffer.split(endIndex + 1)                              :143
          delimiterLength = matcher.delimiter().length                    :147
          ├─ chunks.isEmpty() ?                                           :148
          │    ├─ 예 ──→ stripDelimiter 이면 writePosition -= delimiterLength  :149-151
          │    │          result.add(split)                               :152
          │    └─ 아니오 ──→ chunks.add(split); joined = join(chunks)      :155-156
          │                  stripDelimiter 이면 joined 에서 뒤로 자름      :157-159
          │                  result.add(joined); chunks.clear()           :160-161
   } while (buffer.readableByteCount() > 0)                               :164

   ★ delimiterLength 를 매처가 보고한 값으로 그대로 믿는다 — 거짓 매치가
     "몇 바이트를 본문에서 떼어낼지" 를 직접 결정하는 구조
```

## 4. 스프링 전역에서의 자리

이 매처는 **바이트 스트림을 논리적 조각으로 쪼개는** 모든 리액티브 경로의 바닥에 있다. grep으로 확인한 실제 소비자는 두 갈래다.

```
[ 갈래 1 — 문자 디코딩 (spring-core → WebFlux) ]
  AbstractCharSequenceDecoder.decode(...)             AbstractCharSequenceDecoder.java:97
    └→ DataBufferUtils.matcher(delimiterBytes)                              :103
         기본 구분자 DEFAULT_DELIMITERS = ["\r\n", "\n"]                    :56
         → CompositeMatcher{ TwoByteMatcher(\r\n), SingleByteMatcher(\n) }  ★ 결함 경로
    ├ StringDecoder        StringDecoder.java:44   (textPlainOnly :66 / allMimeTypes :83)
    └ CharBufferDecoder    CharBufferDecoder.java:44 (textPlainOnly :67 / allMimeTypes :84)

  그 StringDecoder 가 실제로 등록되는 곳
    BaseDefaultCodecs.java:494   typedReaders 에 StringDecoder.textPlainOnly()
                                 → WebFlux 기본 코덱: String 본문 읽기 전부가 여기를 지난다
    BaseDefaultCodecs.java:709   objectReaders 에 StringDecoder.allMimeTypes()
    ServerSentEventHttpMessageReader.java:55   private final StringDecoder lineDecoder
                                 = StringDecoder.textPlainOnly()  → SSE 한 줄 단위 파싱
    KotlinSerializationStringDecoder.java:58   StringDecoder.allMimeTypes(DEFAULT_DELIMITERS, false)
    DefaultRSocketStrategies.java:138          StringDecoder.allMimeTypes()  → RSocket 페이로드
    Jackson2JsonDecoder.java:53 / JacksonJsonDecoder.java:51
                                 CharBufferDecoder.textPlainOnly([",", "\n"], false)
                                 → 구분자가 1바이트 두 개라 SingleByteMatcher 두 개 (이 결함과 무관)

[ 갈래 2 — 멀티파트 파싱 (spring-web) ]
  http/codec/multipart/MultipartParser.java
    :309/:313  PreambleState.firstBoundary = matcher(concat(TWO_HYPHENS, boundary))
    :362       HeadersState.endHeaders     = matcher(concat(CR_LF, CR_LF))       (4바이트)
    :507/:515  BodyState.boundary          = matcher(concat(CR_LF, TWO_HYPHENS, boundary))
  http/converter/multipart/MultipartParser.java
    :258/:262, :305, :449/:457  (같은 구성의 블로킹 변형)
    → 이 구분자들은 모두 길이 3 이상이라 KnuthMorrisPrattMatcher 로 간다.
      KMP 는 되감기를 갖고 있었으므로 이 갈래는 결함의 영향을 받지 않았다.
```

정리하면, `TwoByteMatcher`를 실제로 태우는 상용 경로는 **문자 디코더의 `\r\n` 하나**였다. 그래서 결함의 노출면은 "WebFlux에서 텍스트/String 본문 또는 SSE를 디코딩할 때, 본문에 홀로 있는 `\r`이 나타나는 경우"로 좁혀지고, 동시에 그 경로가 웹 스택의 가장 흔한 길목이라 실제 피해는 작지 않다. 변경 파일은 `spring-core`인데 피해자는 웹 스택이라는 비대칭이 여기서 나온다.

## 5. 관련 개념

### 5-1. 스트리밍 구분자 탐색과 부분 일치 상태

리액티브 스트림에서 데이터는 임의 크기의 `DataBuffer`로 쪼개져 도착한다. 구분자가 버퍼 경계에 걸치는 것은 예외가 아니라 일상이다. 그래서 매처는 "지금까지 구분자의 앞 k바이트를 맞췄다"는 상태를 호출 사이에 들고 있어야 하고, 그 상태를 언제 되감을지가 알고리즘의 본체가 된다.

```
 버퍼 1: "hello\r"        match → -1, 내부 matches = 1 로 유지  ← 여기서 상태를 버리면 구분자를 놓친다
 버퍼 2: "\nworld"        첫 바이트에서 matches = 2 → 매치 성립, pos = 0 반환
```

되감기를 하지 않아도 "구분자가 반드시 연속으로 온다"는 가정 아래서는 대부분 우연히 맞는다. 틀리는 경우는 첫 바이트만 나타나고 뒤가 이어지지 않을 때인데, `\r\n`에서 그것은 정확히 "홀로 있는 `\r`"이다.

### 5-2. Knuth-Morris-Pratt 되감기와 그 특수 케이스

KMP는 부분 일치가 깨졌을 때 처음으로 돌아가는 대신, 이미 읽은 접두사 중 **접미사이기도 한 가장 긴 것**의 길이로 점프한다. 그 표가 `longestSuffixPrefixTable`(`DataBufferUtils.java:945-959`)이다.

```
 delimiter = "aab" 의 표
   i=0 : result[0] = 0
   i=1 : delimiter[1]=='a' == delimiter[0] → result[1] = 1
   i=2 : delimiter[2]=='b' != delimiter[1] → j = result[0] = 0, 'b' != 'a' → result[2] = 0

 match(byte) 의 되감기                                            :962-966
   while (matches > 0 && b != delimiter[matches]) matches = table[matches - 1];
   return super.match(b);
```

길이 2 구분자에서는 부분 일치 상태가 `matches == 1` 하나뿐이고, 그때 참조하는 값은 언제나 `table[0]`이며 `longestSuffixPrefixTable`은 `result[0] = 0`으로 시작한다(`DataBufferUtils.java:947`). 따라서 되감기는 반드시 한 번에 0으로 끝난다. `while`이 `if`로, 테이블 조회가 상수 `0`으로 줄어든 `TwoByteMatcher`의 수정은 축약이 아니라 **이 경우에 접힌 등가 구현**이다.

### 5-3. DataBuffer의 split과 writePosition 조정

`DataBuffer.split(index)`는 버퍼를 둘로 가른다. 앞쪽 `index` 바이트가 새 버퍼로 반환되고, 원본에는 뒤쪽이 남는다. 메모리는 공유하되 영역이 겹치지 않는다(`DataBuffer.java:363-379`). 구분자를 떼어내는 일은 별도 복사 없이 `writePosition`을 뒤로 당기는 것으로 처리한다.

```
 buffer = "a\r\nb\n"        (readPosition 0, writePosition 5)
 endIndex = 2               ← 구분자 "\r\n" 의 마지막 바이트 인덱스
 split = buffer.split(3)
   split  : "a\r\n"  writePosition = 3
   buffer : "b\n"
 stripDelimiter 이면 split.writePosition(3 - delimiterLength)
   delimiterLength = 2 → writePosition = 1 → 읽히는 내용은 "a"
```

여기서 알 수 있듯 잘라내는 양은 오직 `matcher.delimiter().length`가 결정한다. 매처가 실제보다 긴 구분자를 보고하면 그만큼 본문이 잘리고, 아무 검증도 그것을 막지 않는다.

### 5-4. 매처 생명주기 — 어디까지 공유되는가

매처는 `decode` 호출 하나마다 새로 만들어진다(`AbstractCharSequenceDecoder.java:103`). 즉 요청 하나의 본문 스트림에 하나씩 대응하고, 요청 사이에 상태가 새지 않는다. 예외는 `SingleByteMatcher.NEWLINE_MATCHER`인데(`DataBufferUtils.java:825`), 이 인스턴스는 필드가 `final byte[] delimiter` 하나뿐이고 `match(byte)`가 순수 비교라 공유해도 안전하다. 상태가 없다는 것이 공유의 전제조건이라는 점을 이 상수가 보여 준다.

한편 `AbstractNestedMatcher.match(DataBuffer)`가 `this.match(b)`를 람다 안에서 호출하는 것은 **가상 디스패치**다(`DataBufferUtils.java:883`). 그래서 `TwoByteMatcher`가 `match(byte)`를 오버라이드하기만 하면 버퍼 단위 진입 경로와 `CompositeMatcher` 경로 모두에서 자동으로 적용된다. 수정이 8줄로 끝나고 배선 작업이 필요 없었던 이유다.

### 5-5. 참고 — 이미 있는 개념 문서

이 무대와 직접 겹치는 개념 문서는 아직 `../../concepts/`에 없다. 매처 계층과 스트리밍 상태 유지는 이 문서 안에서 자기완결로 다뤘다.
