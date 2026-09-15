# PR #36914 분석 — AbstractXMLStreamReader.getTextCharacters의 sourceStart 무시

> 기준: PR base `0c60266986` = 현재 `upstream/main` `7daf1013aa8` (두 커밋 사이에 `AbstractXMLStreamReader.java`·`XMLEventStreamReader.java` 변경 없음 — `git diff`로 확인).
> PR head: `refs/pr/36914`. 상태 OPEN, 라벨 `status: waiting-for-triage` 하나, 코멘트 1건.
> 이 문서는 README(서사)·structure.md(무대 지도)·tests.md(테스트 해설)와 중복을 피하고, 호출 그래프·이름표 사전·단계 추적·수정안 판단에 집중한다.

## 0. 결론

`AbstractXMLStreamReader.getTextCharacters(int sourceStart, char[] target, int targetStart, int length)`는 복사 상한을 `Math.min(length, source.length)`로 계산해 **복사 시작점 `sourceStart`를 계산에서 빠뜨렸고**, 그 결과 StAX javadoc이 예제로 싣고 있는 조각 읽기 루프의 두 번째 반복에서 `System.arraycopy`가 원본 배열 끝을 넘겨 읽으며 `ArrayIndexOutOfBoundsException`을 던졌다.\
수정은 상한을 `Math.min(length, source.length - sourceStart)`로 바꿔 **상한 계산과 복사 시작점이 같은 전제를 쓰게 하는** 한 줄이다.\
PR은 2026-06-13 제출 후 리뷰 대기 상태다.

> **StAX 조각 읽기 (chunked read)** — 텍스트 전체를 한 번에 받지 않고, 고정 버퍼에 `sourceStart`를 전진시키며 여러 번 나눠 받는 사용 패턴.\
> 예: `for (int s = 0; ; s += 4) { n = reader.getTextCharacters(s, buf, 0, 4); if (n < 4) break; }`

> **오프셋 (offset, 여기서는 `sourceStart`)** — 원본 텍스트 안에서 복사를 시작할 인덱스.\
> 예: `"content"`(7자)에서 `sourceStart = 4`는 인덱스 4부터, 즉 `"ent"`부터 읽겠다는 뜻이다.

## 1. 무대

결함은 `spring-core`의 StAX 어댑터 추상 상위 클래스 한 메서드에 있고, 그 클래스는 package-private이지만 public 팩터리를 통해 JDK 표준 인터페이스 타입으로 노출된다.\
다음 표는 그 좌표를 항목별로 정리한 것이다.

> **package-private** — 접근 제어자를 붙이지 않았을 때의 가시성. 같은 패키지 밖에서는 클래스 이름조차 쓸 수 없다.\
> 예: `AbstractXMLStreamReader`·`XMLEventStreamReader`가 그렇고, 그래서 외부는 `StaxUtils` 팩터리를 통해서만 이 객체를 손에 쥔다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 패키지 | `org.springframework.util.xml` |
| 결함 파일 | `spring-core/src/main/java/org/springframework/util/xml/AbstractXMLStreamReader.java` |
| 결함 메서드 | `getTextCharacters(int, char[], int, int)` (`:190-196`) |
| 유일한 서브클래스 | `XMLEventStreamReader` (`XMLEventStreamReader.java:45`) |
| 공개 진입 API | `StaxUtils.createEventStreamReader(XMLEventReader)` (`StaxUtils.java:303`, `public static`, 반환 타입 `javax.xml.stream.XMLStreamReader`) |
| 테스트 | `spring-core/src/test/java/org/springframework/util/xml/XMLEventStreamReaderTests.java` |

`AbstractXMLStreamReader`와 `XMLEventStreamReader`는 둘 다 package-private이다.\
그런데 결함이 공개 표면에 노출되는 이유는 `StaxUtils.createEventStreamReader`가 public이고 **반환 타입이 JDK 표준 인터페이스**라는 데 있다.\
호출자는 구현 클래스 이름을 볼 수 없는 대신 `XMLStreamReader` javadoc이 약속한 모든 계약을 쓸 권리를 갖는다.

누가 언제 부르는가는 두 층으로 갈린다.\
**어댑터를 만드는 쪽**은 저장소 안에 하나뿐이다 — `XStreamMarshaller.unmarshalXmlEventReader`가 `StAXSource` 언마셜링 경로에서 `createEventStreamReader`를 호출한 뒤 XStream의 `StaxReader`에 넘긴다.\
**문제의 4인자 오버로드를 부르는 쪽**은 저장소 안에 하나도 없다.\
`git grep getTextCharacters` 기준으로 프로덕션 호출처는 `StaxStreamXMLReader.java:214`(문자 이벤트)와 `:224`(주석 이벤트) 두 곳뿐이고, 둘 다 인자 없는 `getTextCharacters()`에 `getTextStart()`·`getTextLength()`를 조합해 쓴다.\
즉 이 결함은 **외부 호출자 전용 사각지대**다.

## 2. 전체 메서드 그래프

아래 그래프는 세 갈래다.\
어댑터가 만들어지는 경로, 호출자가 조각 읽기 루프를 돌 때 결함에 닿는 경로, 그리고 저장소 안의 실제 소비자가 그 경로를 비켜 가는 대조군이다.\
오른쪽 숫자는 각 파일의 줄 번호다.

```text
[생성 경로]
 (사용자) marshaller.unmarshal(new StAXSource(eventReader))
    -> AbstractMarshaller.unmarshal(Source)                     AbstractMarshaller.java:389
       -> unmarshalStaxSource(...)                              AbstractMarshaller.java:443
          -> unmarshalXmlEventReader(eventReader)               AbstractMarshaller.java:451 (abstract)
             -> XStreamMarshaller.unmarshalXmlEventReader       XStreamMarshaller.java:784
                -> StaxUtils.createEventStreamReader(...)       StaxUtils.java:303
                   -> new XMLEventStreamReader(eventReader)     XMLEventStreamReader.java:52
                        this.event = eventReader.nextEvent()    XMLEventStreamReader.java:54
                -> unmarshalXmlStreamReader(streamReader)       XStreamMarshaller.java:787
                   -> new StaxReader(..., streamReader, ...)    (XStream 라이브러리가 커서형으로 소비)

[결함 경로 — 호출자가 조각 읽기 루프를 돌 때]
 (호출자) for (int s = 0; ; s += len) { n = reader.getTextCharacters(s, buf, 0, len); if (n < len) break; }
    |
    v
 AbstractXMLStreamReader.getTextCharacters(sourceStart, target, targetStart, length)   :190-196
    |
    +-- (1) char[] source = getTextCharacters();                                       :192
    |        -> AbstractXMLStreamReader.getTextCharacters()                            :185-188
    |             -> return getText().toCharArray();                                   :187
    |                  -> XMLEventStreamReader.getText()                               :151-162
    |                       event.isCharacters() ? asCharacters().getData()            :153-154
    |                       : eventType == COMMENT ? ((Comment) event).getText()       :156-157
    |                       : throw IllegalStateException                              :160
    |        데이터: source = "content".toCharArray() (길이 7). 호출마다 새 배열.
    |
    +-- (2) length = Math.min(length, source.length);                                  :193  [BUG]
    |        데이터: sourceStart 가 이 식에 등장하지 않는다.
    |
    +-- (3) System.arraycopy(source, sourceStart, target, targetStart, length);        :194
    |        JDK 내부 경계 검사: sourceStart + length > source.length 이면 AIOOBE
    |
    +-- (4) return length;                                                             :195
             호출자 종료 판정: 반환값 < 요청 length 이면 "텍스트 끝"

[대조군 — 저장소 내 실제 소비자는 이 경로를 안 탄다]
 StaxStreamXMLReader.handleCharacters()                          StaxStreamXMLReader.java:209
    -> contentHandler.characters(reader.getTextCharacters(),     :214  (인자 없는 오버로드)
                                 reader.getTextStart(),          :215  -> XMLEventStreamReader:147 = 항상 0
                                 reader.getTextLength())         :215  -> AbstractXMLStreamReader:199
```

그래프에서 읽어야 할 것은 두 가지다.\
첫째, 결함 지점 (2)는 (1)이 만든 `source`의 길이만 보고 (3)이 쓸 `sourceStart`를 보지 않는다 — **한 메서드 안에서 두 줄이 서로 다른 전제를 쓴다**.\
둘째, in-tree 소비자(`StaxStreamXMLReader`)는 `getTextStart()`가 항상 0을 돌려주는 세계관 위에서 전체 배열을 한 번에 넘기므로 이 경로를 절대 밟지 않는다.\
그래서 저장소 테스트로는 결함이 드러나지 않았다.

두 전제가 어긋나는 지점을 원본 배열 칸으로 옮겨 놓으면 이렇다.

```text
source = "content" (길이 7), sourceStart = 4, 요청 length = 4

 index   0   1   2   3   4   5   6  | 7
       +---+---+---+---+---+---+---+ - - -+
       | c | o | n | t | e | n | t | |  X  |   <- 없는 칸
       +---+---+---+---+---+---+---+ - - -+
                       ^-- 복사는 여기서 시작 (:194 는 sourceStart 를 쓴다)
       ^-------- 상한은 여기서부터 센다 (:193 은 source.length 만 본다)

       :193  min(4, 7)     = 4   -> 인덱스 4..7 요청 -> AIOOBE
       :193  min(4, 7 - 4) = 3   -> 인덱스 4..6 요청 -> "ent", 3 반환
```

## 2.5 핵심 이름표 사전

이 흐름에서 헷갈리는 것은 "인덱스"가 두 세계에 각각 있고(원본 / 대상), "길이"가 요청량과 실제량 두 의미로 쓰인다는 점이다.\
아래 표는 각 이름표가 어느 세계의 값인지를 명시한다.\
예시 값은 텍스트 노드 `"content"`(7자), 버퍼 4자, 두 번째 반복(`sourceStart = 4`) 기준이다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `getTextCharacters(int,char[],int,int)` (`:190-196`) | StAX 조각 읽기 API의 구현 | (sourceStart, target, targetStart, length) -> 실제 복사한 문자 수 | 외부 호출자만. 저장소 내 호출처 0 | 결함 본체. 네 줄 중 `:193` 한 줄이 틀렸다 |
| `sourceStart` (파라미터) | **원본 텍스트** 안의 복사 시작 인덱스 | 호출자가 넘김. 유효 범위 = 0 이상, 텍스트 길이 이하 | 조각 읽기 루프가 매 반복 `+= length`로 전진시킴 | `:194`의 arraycopy는 이 값을 쓰는데 `:193`의 상한 계산은 안 쓴다. 이 비대칭이 결함 자체 |
| `target` / `targetStart` (파라미터) | **대상 버퍼**와 그 안의 쓰기 시작 인덱스 | 호출자가 넘김 | 위와 같음 | 무관. 다만 `source`/`target` 접두사가 두 세계를 나누라는 신호였고 `:193`이 그 구분을 놓쳤다 |
| `length` (파라미터, 재대입됨) | 진입 시 = 요청 상한, `:193` 이후 = 실제 복사량 | 4 -> (수정 전) 4, (수정 후) 3 | `:193`에서 덮어써지고 `:194`가 소비, `:195`가 반환 | 같은 변수가 두 의미를 갖는다. `:193`이 상한을 줄이지 못하면 "실제 복사량"이라는 두 번째 의미가 거짓이 된다 |
| `source` (지역변수, `:192`) | 현재 이벤트 텍스트 전체의 char 배열 사본 | `getTextCharacters()` -> `['c','o','n','t','e','n','t']` | 매 호출마다 새로 만들어짐(캐시 없음) | `source.length`(=7)가 `:193`의 유일한 기준이 되면서 "남은 길이"(=3)를 대신했다 |
| `source.length - sourceStart` (수정이 도입) | "이 위치에서 아직 읽을 수 있는 문자 수" | 7 - 4 -> 3 | `:193`(수정 후) | 수정의 전부. 상한을 복사 시작점과 같은 전제로 옮긴다 |
| `getTextCharacters()` (`:185-188`) | 텍스트 전체를 char 배열로 | () -> `getText().toCharArray()` | 4인자 오버로드가 매 호출 1회, `StaxStreamXMLReader:214`·`:224`가 각각 1회 | 조각 읽기 루프가 조각 수만큼 전체 텍스트를 재복사하게 만든다(성능 주제 — 이 PR 범위 밖) |
| `getText()` (`XMLEventStreamReader.java:151-162`) | 현재 이벤트의 텍스트 | () -> CHARACTERS면 `asCharacters().getData()`, COMMENT면 `Comment.getText()`, 그 외 `IllegalStateException` | `getTextCharacters()`가 부름 | 커서가 텍스트 이벤트가 아니면 결함 지점에 닿기 전에 여기서 먼저 실패한다 |
| `getTextStart()` (`XMLEventStreamReader.java:146-149`) | 텍스트가 시작하는 인덱스 | () -> **항상 0** | `StaxStreamXMLReader:215`·`:225` | 이 어댑터의 세계관("텍스트는 0에서 시작하는 한 덩어리")을 드러낸다. 같은 가정이 `:193`에 새어 들어간 것 |
| `getTextLength()` (`:198-201`) | 텍스트 전체 길이 | () -> `getText().length()` | `StaxStreamXMLReader:215`·`:225` | in-tree 소비자가 조각 읽기 대신 이 조합을 쓰는 이유. 결함이 오래 숨은 구조적 원인 |
| `System.arraycopy` (`:194`) | JDK의 배열 구간 복사 | (src, srcPos, dst, dstPos, len) | `:194`가 1회 | 경계 위반을 **예외로만** 알린다. 명시적 `if`가 없어 결함이 조용한 오답이 아니라 크래시로 나타난다 |
| `XMLEventStreamReader.event` (`:47`) | 현재 커서가 가리키는 `XMLEvent` | 생성자(`:54`)와 `next()`(`:276`)가 갱신 | `getEventType()`·`getText()`·`getName()`이 읽음 | 결함 자체와 무관하지만 "텍스트 이벤트에 커서를 두는" 전제를 만든다 |
| `next()` (`XMLEventStreamReader.java:274-278`) | 커서 전진 | () -> 새 이벤트 타입 | 호출자·테스트 헬퍼 | 테스트가 CHARACTERS 이벤트에 도달하는 수단 |
| `StaxUtils.createEventStreamReader` (`StaxUtils.java:303`) | 이벤트형 -> 커서형 어댑터 팩터리 | `XMLEventReader` -> `XMLStreamReader` | `XStreamMarshaller:786`, 그리고 외부 코드 | 결함이 **공개 계약 표면**에 노출되는 유일한 통로 |
| `advanceToCharacters()` (테스트 헬퍼) | 커서를 CHARACTERS 이벤트까지 전진 | () -> void | 회귀 테스트가 1회 | `next()` 횟수를 상수로 박지 않고 이벤트 타입으로 조건을 걸어, 파서 구현 차이에 덜 민감하게 만든다 |

표에서 결함이 한 행으로 보인다.\
`length`(요청 상한)를 줄일 때 기준으로 삼아야 할 것은 `source.length - sourceStart`(남은 길이)인데 코드는 `source.length`(전체 길이)를 썼다.\
두 값은 `sourceStart == 0`일 때만 같다.

## 3. 결함 경로 단계 추적

호출자가 StAX javadoc의 예제 루프(`for (int sourceStart = 0; ; sourceStart += length)`)를 4자 버퍼로 도는 상황이다.\
텍스트 노드는 `"content"`(7자).\
정상 케이스(첫 반복)와 결함 케이스(둘째 반복)를 같은 단계로 나란히 놓는다.

| 단계 | 코드 | 첫 반복 (sourceStart = 0, 정상) | 둘째 반복 (sourceStart = 4, 결함) |
|---|---|---|---|
| (1) 원본 확보 | `:192` `source = getTextCharacters()` | `['c','o','n','t','e','n','t']`, `source.length = 7` | 동일 (전체를 다시 복사) |
| (2) 남은 문자 수 (코드에 없는 개념) | — | `7 - 0 = 7` | `7 - 4 = 3` |
| (3) 상한 계산 | `:193` `length = Math.min(length, source.length)` | `min(4, 7) = 4` — (2)와 같아 우연히 정확 | `min(4, 7) = 4` — (2)의 3을 **초과** |
| (4) 복사 | `:194` `arraycopy(source, sourceStart, target, targetStart, length)` | 인덱스 0..3 -> `"cont"` | 인덱스 4..7 요청 -> 인덱스 7 없음 |
| (5) 결과 | `:195` `return length` | `4` 반환 | `ArrayIndexOutOfBoundsException: arraycopy: last source index 8 out of bounds for char[7]` |
| (6) 호출자 판정 | `if (n < length) break;` | `4 == 4` -> `sourceStart += 4`로 계속 | 도달 못 함 |

수정 후 (3)은 `min(4, 7 - 4) = 3`이 되고, (4)는 인덱스 4..6에서 `"ent"`를 복사하며, (5)가 3을 반환하고, (6)이 `3 < 4`로 루프를 정상 종료한다.

결함 발동 조건은 두 개가 **동시에** 성립할 때다: (a) `sourceStart > 0`, (b) 남은 문자 수 < 요청 `length`.\
어느 하나라도 빠지면 수정 전 코드도 정상 동작한다.\
(a)만 있고 (b)가 없으면 상한이 요청량 그대로 유지되면서 arraycopy도 범위 안이고, (b)만 있고 (a)가 없으면 두 계산식이 같은 값을 낸다.\
이 교집합이 좁은 것이 결함이 오래 살아남은 이유이자, 테스트 입력(`sourceStart=4`, `length=10`, 텍스트 7자)이 두 조건을 동시에 만족시키는 최소 구성인 이유다.

경계 세 개도 정리해 둔다.\
`sourceStart == 7`(정확히 다 읽고 한 번 더 호출)이면 수정 후 상한이 `min(10, 0) = 0`이 되어 아무것도 복사하지 않고 0을 반환한다 — javadoc이 `sourceStart`를 "less than or equal to the number of characters"로 허용하므로 유효 입력이고 0이 정답이다.\
`sourceStart == 8`이면 상한이 `-1`이 되어 `arraycopy`가 `IndexOutOfBoundsException`을 던진다 — javadoc 범위 밖 입력이므로 예외가 정답이다.\
`sourceStart == 0`이면 수정 전후 식이 항등이다.

## 4. 계약과 위반

`javax.xml.stream.XMLStreamReader#getTextCharacters(int, char[], int, int)`의 javadoc(JDK 21 `src.zip`)이 고정하는 것은 네 가지다.

- **(C1)** "Text starting a `sourceStart` is copied into `target` starting at `targetStart`" — `sourceStart`는 원본 인덱스이고, 복사는 그 지점부터다.
- **(C2)** "Up to `length` characters are copied" — `length`는 상한이지 요구량이 아니다.
- **(C3)** "The number of characters actually copied is returned" — 반환값은 실제 복사량이다.
- **(C4)** "The `sourceStart` argument must be greater or equal to 0 and less than or equal to the number of characters associated with the event" + "If the number of characters actually copied is less than the `length`, then there is no more text. Otherwise, subsequent calls need to be made until all text has been retrieved" — 유효 입력 범위와 종료 신호 규약. javadoc은 이 규약을 `sourceStart += length` 루프 예제로 못 박아 두었다.

수정 전 코드는 (C1)을 상한 계산에서만 어긴다(복사 자체는 `sourceStart`를 쓴다).\
그 결과 (C4)의 유효 입력에서 예외가 나고, 마지막 조각에서 상한 축소가 일어나지 않으므로 (C3)이 약속한 "요청량보다 작은 반환값"이라는 종료 신호를 **만들어 낼 수 없다** — (C4)의 루프는 원리적으로 종료할 수 없고 그 전에 예외로 끝난다.

저장소 안의 기존 테스트가 고정하던 것은 이 계약이 아니다.\
`XMLEventStreamReaderTests`의 `readAll`·`readCorrect`는 문서 전체를 훑어 변환 결과를 비교하는 통합형이고, 조각 읽기 오버로드를 부르지 않는다.\
즉 이 계약 표면에는 **수정 전 기준으로 테스트가 0건**이었다.

## 5. 수정안

프로덕션 diff는 한 줄이다(`spring-core/src/main/java/org/springframework/util/xml/AbstractXMLStreamReader.java:193`).

```java
// before (base 0c60266986:190-196)
	@Override
	public int getTextCharacters(int sourceStart, char[] target, int targetStart, int length) {
		char[] source = getTextCharacters();
		length = Math.min(length, source.length);
		System.arraycopy(source, sourceStart, target, targetStart, length);
		return length;
	}

// after (refs/pr/36914:190-196)
	@Override
	public int getTextCharacters(int sourceStart, char[] target, int targetStart, int length) {
		char[] source = getTextCharacters();
		length = Math.min(length, source.length - sourceStart);
		System.arraycopy(source, sourceStart, target, targetStart, length);
		return length;
	}
```

**왜 그 위치인가.**\
잘못된 값이 처음 만들어지는 지점이 `:193`이다.\
`:194`의 `arraycopy`는 자기가 받은 인자대로 정확히 동작했고, `:195`의 반환도 자기가 받은 값을 그대로 돌려줬다.\
상한을 만드는 한 줄만 고치면 (C2)(C3)(C4)가 동시에 회복된다 — `:194`는 범위 안에 들어오고, `:195`는 축소된 값을 돌려주며, 그것이 곧 종료 신호가 된다.\
하류 두 줄은 손댈 필요가 없다.

**검토한 대안과 기각 이유**는 셋이다.

첫째, `length = Math.max(0, Math.min(length, source.length - sourceStart))`로 음수까지 막는 안. 기각했다.\
`sourceStart > source.length`는 (C4)가 명시적으로 배제한 무효 입력이고, 0을 돌려주면 호출자에게는 "텍스트 끝"으로 보여 계약 위반이 조용히 삼켜진다.\
수정의 목표는 **유효 입력에서 예외를 없애되 무효 입력을 감추지 않는 것**이었다.

> **무음 실패 (silent failure)** — 잘못된 입력이나 처리가 예외·로그 없이 정상처럼 통과해 버리는 상태.\
> 예: 범위를 벗어난 `sourceStart = 8`에 0을 돌려주면 호출자 눈에는 "텍스트 끝"으로 보여 위반이 감춰진다.

둘째, `sourceStart`를 명시적으로 검증해 `IndexOutOfBoundsException`을 직접 던지는 안. 기각했다.\
`arraycopy`가 이미 같은 계열의 예외를 정확한 메시지("last source index N out of bounds for char[M]")와 함께 던지므로 중복이고, diff가 커져 리뷰 대상이 흐려진다.

셋째, `getTextCharacters()`의 결과를 캐싱해 조각 읽기의 반복 재복사를 없애는 안. 기각했다 — 정확성 결함이 아니라 성능 주제이고, `AbstractXMLStreamReader`가 **필드를 하나도 갖지 않는다**는 설계(모든 파생 메서드가 서브클래스 접근자를 매번 다시 부른다)를 깨야 하므로 별건이다.\
버그 수정 PR에 섞으면 "이 클래스가 상태를 가져도 되는가"라는 별도 판단을 리뷰어에게 떠넘기게 된다.

테스트는 `XMLEventStreamReaderTests`에 회귀 1건과 헬퍼 1개를 더한다.\
입력 `sourceStart=4`, `length=10`, 텍스트 7자는 3절에서 본 발동 조건 (a)(b)를 동시에 만족하는 최소 구성이고, 단언 두 개(반환값 3 + 내용 `"ent"`)가 서로를 검증한다 — 반환값 단언만 있으면 "아무것도 복사하지 않고 3을 반환"하는 구현이, 내용 단언만 있으면 반환값이 (C3)과 어긋나는 구현이 통과한다.\
기대값 `"ent"`는 "예외만 막고 오프셋은 여전히 0부터 복사"하는 오수정(`"con"`이 나옴)도 함께 배제한다.

## 6. 범위 밖과 인접 영향

**blast radius.**\
`git grep "extends AbstractXMLStreamReader"` 결과 서브클래스는 `XMLEventStreamReader` 하나이고, `git grep "implements XMLStreamReader"`로도 다른 구현은 나오지 않는다.\
따라서 이 수정이 영향을 주는 객체는 `StaxUtils.createEventStreamReader`가 돌려주는 인스턴스로 닫혀 있다.

> **blast radius (영향 반경)** — 어떤 변경이 잘못됐을 때 피해가 번질 수 있는 범위.\
> 예: 여기서는 서브클래스가 하나뿐이라 범위가 그 팩터리가 돌려주는 객체 하나로 닫힌다.

**하위호환.**\
`sourceStart == 0`인 모든 호출에서 `source.length - 0 == source.length`이므로 수정 전후 식이 항등이다.\
관측 가능한 차이가 생기는 경우는 `sourceStart > 0`인 호출뿐이고, 그중에서도 남은 길이가 요청 길이보다 작은 경우뿐이다.\
그 경우 수정 전 동작은 **예외**였으므로, 예외에 의존하던 코드가 아닌 한 회귀는 원리적으로 없다.\
in-tree 소비자(`StaxStreamXMLReader:214`·`:224`)는 이 오버로드를 아예 부르지 않는다.

**같은 파일의 인접 결함 — PR #36915.**\
같은 클래스의 `require(int, String, String)`(`:155-161`)이 비-null `namespaceURI`·`localName`을 검증하지 않는 별건이 있고, 별도 PR로 제출되어 있다.\
두 결함은 같은 파일·같은 계약 계열(JSR-173 구현 정합)이지만 메서드가 다르고 성격도 다르다(이쪽은 즉시 크래시, 저쪽은 조용한 통과).\
버그헌트 당시 문서(`docs/plans/2026-06-13/spring-core-bug-hunt/B3-...`, `B8-...`)는 묶음 PR을 후보로 남겼으나 최종적으로 분리 제출을 택했다 — 리뷰 단위를 작게 유지하기 위해서다.

**같은 패턴의 다른 위치.**\
"인덱스와 길이를 함께 받고 상한을 계산하는" 메서드는 이 클래스에 더 없다.\
`getTextLength()`(`:198-201`)와 `XMLEventStreamReader.getTextStart()`(`:146-149`)는 인덱스를 받지 않는다.\
다만 이 둘이 표현하는 "텍스트는 0에서 시작하는 한 덩어리"라는 가정은 어댑터 전반에 깔려 있으며, 결함의 상한 계산에 새어 든 것이 바로 그 가정이다.\
향후 이 어댑터에 인덱스 기반 API를 더할 때 같은 함정이 재현될 수 있다.

**성능(미수정으로 남긴 것).**\
조각 읽기 루프는 조각 수에 비례해 `getText().toCharArray()`를 반복하므로 전체 텍스트를 조각 수만큼 재복사한다.\
이번 PR은 손대지 않았다.\
실제 영향 규모는 미확인이며, 캐싱을 도입하려면 5절 셋째 대안에서 적은 대로 무상태 설계를 바꿔야 한다.
