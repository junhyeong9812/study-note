# PR #36914 — 무대 구조와 수정 전 워크플로우

> PR #36914의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 PR은 OPEN이므로 아래
> `AbstractXMLStreamReader.java` 인용은 **수정 전 코드 그대로**다.

## 1. 무대 — 실구조

이 PR의 무대는 StAX 어댑터 계층이다. `XMLEventReader`(객체형 API)를
`XMLStreamReader`(커서형 API)처럼 보이게 감싸는 어댑터가 있고, 그 어댑터의 추상 상위
클래스가 "최소 접근자만으로 계산되는 파생 메서드"를 채워 넣는다. 결함은 그 파생 메서드
하나에 있었다.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ javax.xml.stream.XMLStreamReader  (JDK 인터페이스)                           │
│   getEventType() / next() / getText() / getName() / getLocation() …          │
│   getTextCharacters()                                    ← 전체 반환         │
│   getTextCharacters(int sourceStart, char[] target,      ← 조각 복사         │
│                     int targetStart, int length)            (계약: 실제      │
│                                                              복사량 반환)    │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ implements
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ AbstractXMLStreamReader  (abstract, package-private)                         │
│                          AbstractXMLStreamReader.java:32                     │
│──────────────────────────────────────────────────────────────────────────────│
│  필드 없음 — 상태를 전혀 갖지 않는다                                         │
│──────────────────────────────────────────────────────────────────────────────│
│  파생 구현 (서브클래스의 최소 접근자만으로 계산)                             │
│    getElementText()             next()+getText() 루프              :35       │
│    getAttributeLocalName(int)   getAttributeName(i).getLocalPart() :66       │
│    getNamespaceURI()            getName().getNamespaceURI()        :81       │
│    hasText() / hasName()        getEventType() 판정          :97 / :116      │
│    isStartElement() / isEndElement() / isCharacters()   :127 / :132 / :137   │
│    nextTag()                    next() 루프                        :142      │
│    getLocalName()               getName().getLocalPart()           :181      │
│    getTextCharacters()          getText().toCharArray()            :186      │
│    getTextCharacters(int,char[],int,int)                           :191 ◄─ 대상│
│    getTextLength()              getText().length()                 :199      │
│──────────────────────────────────────────────────────────────────────────────│
│  서브클래스가 채워야 하는 것: getEventType(), getText(), getName(),          │
│                              getLocation(), next(), getAttribute*() …        │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ extends  (저장소 내 유일한 서브클래스)
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ XMLEventStreamReader  (package-private)     XMLEventStreamReader.java:45     │
│──────────────────────────────────────────────────────────────────────────────│
│  event       : XMLEvent          (현재 커서가 가리키는 이벤트)     :47       │
│  eventReader : XMLEventReader    (감싸고 있는 객체형 리더)         :49       │
│──────────────────────────────────────────────────────────────────────────────│
│  생성자: event = eventReader.nextEvent()   ← 첫 이벤트로 미리 전진 :52-55    │
│  getEventType()  → event.getEventType()                            :77       │
│  getText()       → isCharacters ? asCharacters().getData()                   │
│                    : COMMENT ? ((Comment) event).getText()                   │
│                    : throw IllegalStateException                   :152      │
│  getTextStart()  → 항상 0                                          :147      │
│  next()          → event = eventReader.nextEvent()                 :275      │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ 공개 진입점이 생성한다
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ StaxUtils  (public 유틸리티)                       StaxUtils.java            │
│   createEventStreamReader(XMLEventReader) → new XMLEventStreamReader :303    │
│   createStaxSource(XMLStreamReader) / (XMLEventReader)          :88 / :97    │
│   createXMLReader(XMLStreamReader) → StaxStreamXMLReader                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

`AbstractXMLStreamReader`가 **상태를 하나도 갖지 않는다**는 점이 이 구조의 성격을 정한다.
파생 메서드는 매 호출마다 서브클래스의 접근자를 다시 부르고, 그 결과로 계산한다. 캐시가
없으므로 `getTextCharacters()`는 부를 때마다 새 배열을 만든다.

```java
// AbstractXMLStreamReader.java:185-196  (수정 전 원본 그대로)
@Override
public char[] getTextCharacters() {
    return getText().toCharArray();
}

@Override
public int getTextCharacters(int sourceStart, char[] target, int targetStart, int length) {
    char[] source = getTextCharacters();
    length = Math.min(length, source.length);
    System.arraycopy(source, sourceStart, target, targetStart, length);
    return length;
}
```

세 줄 안에 계약이 세 개 들어 있다. `sourceStart`는 **원본 안의 시작 인덱스**,
`targetStart`는 대상 버퍼의 시작 인덱스, 반환값은 **실제 복사한 문자 수**다. 가운데
`Math.min` 한 줄이 이 셋 중 첫 번째와 세 번째를 동시에 어긴다.

같은 파일 안에 대조군이 있다. `getTextLength()`는 텍스트 길이를 그대로 돌려주고
(`:199-201`), `XMLEventStreamReader.getTextStart()`는 항상 0을 돌려준다(`:146-149`).
즉 이 어댑터는 "텍스트는 언제나 인덱스 0에서 시작하고 전체가 한 덩어리"라는 세계관 위에
서 있고, 그 세계관이 `getTextCharacters(int, …)`의 상한 계산에도 그대로 스며들었다.

## 2. 수정 전 동작 워크플로우

BLUF: 텍스트 노드를 조각내어 읽는 정상 사용 패턴에서, 두 번째 호출부터
`System.arraycopy`가 원본 배열 끝을 넘겨 읽으려 하고 `ArrayIndexOutOfBoundsException`이
난다.

시나리오는 `XMLEventReader`를 커서형으로 바꿔 쓰는 외부 호출자다. 텍스트 노드가
`"content"`(7자)이고, 호출자는 StAX javadoc이 예제로 실어 둔 조각 읽기 루프를 돈다.

```
XMLInputFactory.createXMLEventReader(new StringReader(XML))
        │
        ▼
StaxUtils.createEventStreamReader(eventReader)              StaxUtils.java:303
        └─▶ new XMLEventStreamReader(eventReader)      XMLEventStreamReader.java:52
              event = eventReader.nextEvent()                            :54
        │
        ▼
(호출자) 커서를 CHARACTERS 이벤트까지 전진
        while (reader.getEventType() != CHARACTERS) reader.next();
              getEventType → event.getEventType()                        :77
              next()       → event = eventReader.nextEvent()             :275
        │
        ▼
(호출자) javadoc 권장 루프
        char[] buf = new char[4];
        for (int sourceStart = 0; ; sourceStart += 4) {
            int n = reader.getTextCharacters(sourceStart, buf, 0, 4);
            if (n < 4) break;
        }

  ── 1회전: sourceStart = 0 ─────────────────────────────────────────────────
        │
        ▼
AbstractXMLStreamReader.getTextCharacters(0, buf, 0, 4)                  :191
        │
        ├─ char[] source = getTextCharacters()                           :192
        │     └─▶ getText().toCharArray()                                :186
        │           └─▶ XMLEventStreamReader.getText()                   :152
        │                 event.asCharacters().getData() = "content"
        │           → source = ['c','o','n','t','e','n','t']  (길이 7)
        │
        ├─ length = Math.min(4, source.length)                           :193
        │           = Math.min(4, 7) = 4
        │
        ├─ System.arraycopy(source, 0, buf, 0, 4)                        :194
        │     인덱스 0~3 복사 → "cont"           (정상)
        │
        └─ return 4                                                      :195
        │
        ▼
   호출자: n(4) == length(4) 이므로 계속 → sourceStart = 4

  ── 2회전: sourceStart = 4 ─────────────────────────────────────────────────
        │
        ▼
AbstractXMLStreamReader.getTextCharacters(4, buf, 0, 4)                  :191
        │
        ├─ char[] source = getTextCharacters()   ← 다시 "content" 전체를 새 배열로
        │
        ├─ length = Math.min(4, source.length)                           :193
        │           = Math.min(4, 7) = 4         ★ sourceStart 를 보지 않는다
        │              (남은 문자는 인덱스 4~6 의 3자뿐)
        │
        ├─ System.arraycopy(source, 4, buf, 0, 4)                        :194
        │     인덱스 4,5,6,7 을 읽으려 함 → 인덱스 7 은 없다
        │
        ▼
throw ArrayIndexOutOfBoundsException
      "arraycopy: last source index 8 out of bounds for char[7]"
```

값 세 개만 비교하면 어긋남이 한눈에 보인다.

```
텍스트 "content" (길이 7), 요청 length = 4

           │ sourceStart = 0 │ sourceStart = 4
───────────┼─────────────────┼──────────────────
남은 문자  │        7        │        3
수정 전 상한│ min(4, 7) = 4   │ min(4, 7) = 4      ← 남은 수(3)를 초과
수정 후 상한│ min(4, 7-0) = 4 │ min(4, 7-4) = 3    ← 정확
arraycopy  │  index 0..3 OK  │  index 4..7 → AIOOBE
```

`sourceStart == 0`일 때 두 계산식이 같은 값을 낸다는 것이 결함이 오래 숨은 이유다.
javadoc도 "Usually, one requests text starting at a sourceStart of 0"이라고 적어 두었고,
저장소 안에서 이 오버로드를 부르는 코드는 하나도 없다(4절 참조).

## 3. 분기 처리 워크플로우

BLUF: 이 메서드에는 명시적 `if`가 하나도 없다. 분기는 전부 `Math.min`과
`System.arraycopy`의 내부 경계 검사에 숨어 있고, 그래서 잘못된 상한이 예외라는 형태로만
드러난다.

```
getTextCharacters(sourceStart, target, targetStart, length)   AbstractXMLStreamReader.java:191
   │
   ▼
source = getTextCharacters()                                                  :192
   │  └─ getText() 가 던지는 분기 (서브클래스)      XMLEventStreamReader.java:152
   │       ├─ event.isCharacters() ? ─▶ asCharacters().getData()
   │       ├─ eventType == COMMENT ? ─▶ ((Comment) event).getText()
   │       └─ 그 외             ─▶ throw IllegalStateException
   │            (즉 CHARACTERS/COMMENT 가 아닌 커서 위치에서는 여기서 이미 실패)
   │
   ▼
length = Math.min(length, source.length)                                      :193
   │
   ├─ length <= source.length ?  ─▶ length 유지
   │      예: length=4, source.length=7 → 4
   │
   └─ length >  source.length ?  ─▶ source.length 로 축소
          예: length=10, source.length=7 → 7
   │
   │   ★ 어느 갈래든 sourceStart 가 계산에 들어가지 않는다  [BUG]
   ▼
System.arraycopy(source, sourceStart, target, targetStart, length)            :194
   │
   ├─ sourceStart + length <= source.length ?
   │      └─ YES ─▶ 정상 복사
   │              (수정 전에는 sourceStart == 0 이거나
   │               남은 길이가 요청 길이 이상일 때만 성립)
   │
   ├─ sourceStart + length >  source.length ?
   │      └─ YES ─▶ ArrayIndexOutOfBoundsException              [BUG 발현]
   │
   ├─ targetStart + length > target.length ?
   │      └─ YES ─▶ ArrayIndexOutOfBoundsException  (호출자 잘못 — 이 PR과 무관)
   │
   └─ length < 0 ?
          └─ YES ─▶ IndexOutOfBoundsException
   │
   ▼
return length                                                                 :195
   │
   └─ 호출자의 종료 판정: 반환값 < 요청 length 이면 "텍스트 끝"
        ★ 수정 전에는 상한이 축소되지 않으므로 이 신호가 나올 수 없다
```

수정 후 상한 계산이 어떻게 갈리는지 경계별로 정리하면 다음과 같다.
`length = Math.min(length, source.length - sourceStart)` 한 줄이 만드는 결과다.

```
source.length = 7 인 경우

sourceStart │ 남은 = 7 - sourceStart │ 수정 후 상한(요청 10) │ 결과
────────────┼────────────────────────┼───────────────────────┼──────────────────────
     0      │           7            │  min(10, 7) = 7       │ 전체 복사, 7 반환
     4      │           3            │  min(10, 3) = 3       │ "ent" 복사, 3 반환
     7      │           0            │  min(10, 0) = 0       │ 복사 없음, 0 반환
            │                        │                       │ (javadoc 이 허용하는
            │                        │                       │  유효 입력 — "less than
            │                        │                       │  or equal to")
     8      │          -1            │  min(10,-1) = -1      │ arraycopy 가
            │                        │                       │ IndexOutOfBounds
            │                        │                       │ (javadoc 범위 밖 입력이므로
            │                        │                       │  예외가 정답)
```

즉 수정은 **유효 입력에서 예외를 없애되 무효 입력을 조용히 삼키지 않는다.** 상한을
`Math.max(0, …)`로 한 번 더 조였다면 `sourceStart = 8`도 0을 반환하며 통과했을 텐데, 그것은
계약 위반 입력을 감추는 셈이 되므로 하지 않았다.

## 4. 스프링 전역에서의 자리

BLUF: 이 어댑터는 **OXM(Object/XML 매핑)의 `StAXSource` 언마셜링 경로**에서 불린다. 다만
문제의 오버로드를 부르는 코드는 저장소 안에 없고, 계약을 소비하는 것은 외부 라이브러리
(XStream)와 외부 호출자다.

먼저 어댑터가 만들어지는 실제 사슬이다.

```
$ grep -rn "createEventStreamReader" --include=*.java . | grep -v /test/

spring-oxm/…/oxm/xstream/XStreamMarshaller.java:786
spring-core/…/util/xml/StaxUtils.java:303        (선언 자체)
spring-core/…/util/xml/XMLEventStreamReader.java:43   (javadoc @see)
```

```
(사용자 코드) marshaller.unmarshal(new StAXSource(eventReader))
        │
        ▼
AbstractMarshaller.unmarshal(Source source)          AbstractMarshaller.java:389
        │
        ├─ source instanceof DOMSource ?      ─▶ unmarshalDomSource
        ├─ StaxUtils.isStaxSource(source) ?   ─▶ YES                       :393
        │        │
        │        ▼
        │   unmarshalStaxSource(staxSource)                               :443
        │        │
        │        ├─ StaxUtils.getXMLStreamReader(source) != null ?
        │        │      └─ YES ─▶ unmarshalXmlStreamReader(streamReader)
        │        │
        │        └─ NO ─▶ StaxUtils.getXMLEventReader(source)
        │                   └─▶ unmarshalXmlEventReader(eventReader)      :451
        │                         (추상 — 구현체가 채운다)                :604
        │                            │
        │                            ▼
        │                   XStreamMarshaller.unmarshalXmlEventReader     XStreamMarshaller.java:784
        │                            │
        │                            ├─ StaxUtils.createEventStreamReader(eventReader)  :786
        │                            │     └─▶ new XMLEventStreamReader(...)  ★ 이 PR의 무대
        │                            │
        │                            └─▶ unmarshalXmlStreamReader(streamReader)         :787
        │                                  └─▶ new StaxReader(new QNameMap(), streamReader, nameCoder)
        │                                        ← XStream 라이브러리가 커서형 API 를 소비
        │
        ├─ source instanceof SAXSource ?      ─▶ unmarshalSaxSource
        └─ source instanceof StreamSource ?   ─▶ unmarshalStreamSource
```

이제 문제의 오버로드를 실제로 부르는 곳을 확인한다.

```
$ grep -rn "getTextCharacters" --include=*.java . | grep -v /test/

spring-core/…/util/xml/StaxStreamXMLReader.java:214   ← 인자 없는 쪽
spring-core/…/util/xml/StaxStreamXMLReader.java:224   ← 인자 없는 쪽
spring-core/…/util/xml/AbstractXMLStreamReader.java:186   (인자 없는 구현)
spring-core/…/util/xml/AbstractXMLStreamReader.java:191   (문제의 오버로드 구현)
spring-core/…/util/xml/AbstractXMLStreamReader.java:192   (그 안에서 위를 호출)
```

`StaxStreamXMLReader`는 StAX 커서형 리더를 SAX로 다시 넘기는 어댑터인데, 텍스트를 넘길 때
**전체 배열 + `getTextStart()` + `getTextLength()`** 조합을 쓴다.

```java
// StaxStreamXMLReader.java:213-217 (handleCharacters 안쪽)
if (getContentHandler() != null) {
    getContentHandler().characters(this.reader.getTextCharacters(),
            this.reader.getTextStart(), this.reader.getTextLength());
}
```

즉 in-tree 소비자는 조각 읽기를 쓰지 않는다. 그렇다면 이 결함이 왜 실피해인가 — 답은
**공개 API 표면**에 있다.

```
StaxUtils.createEventStreamReader(XMLEventReader)     StaxUtils.java:303
   │  public static, 반환 타입 = javax.xml.stream.XMLStreamReader
   │
   ▼
호출자가 손에 쥐는 것은 "JDK 인터페이스 XMLStreamReader"다.
   │
   ├─ 호출자는 인터페이스 javadoc 이 보장한 계약대로 쓸 권리가 있다
   │     - sourceStart 는 0 이상 텍스트 길이 이하
   │     - 반환값이 length 보다 작으면 텍스트 끝
   │     - javadoc 이 조각 읽기 루프를 예제 코드로 싣고 있다
   │
   └─ 그 계약대로 쓰면 두 번째 반복에서 AIOOBE
         ★ 계약이 권장한 사용 패턴이 곧 크래시 재현 절차
```

여기에 더해 XStream 같은 외부 라이브러리가 이 어댑터를 커서형 리더로 소비한다
(`XStreamMarshaller.java:787` -> `StaxReader`). 라이브러리 구현이 텍스트를 조각으로 읽는
전략을 쓰면 스프링 코드 한 줄 바꾸지 않고도 이 경로에 도달한다. 즉 in-tree 호출처가 없다는
사실은 "안전하다"가 아니라 "저장소 안 테스트로는 드러나지 않는다"를 뜻한다.

마지막으로 이 상위 클래스를 상속하는 구체 클래스가 몇 개인지도 확인해 둔다.

```
$ grep -rn "extends AbstractXMLStreamReader" --include=*.java .

spring-core/…/util/xml/XMLEventStreamReader.java:45
```

하나뿐이다. 따라서 이 수정의 blast radius는 `StaxUtils.createEventStreamReader`가
돌려주는 객체 하나로 닫혀 있다.

## 5. 관련 개념

이 구조를 이해하는 데 필요한 개념 셋을 여기서 설명한다(해당 개념의 별도 문서는 아직 없다).

**StAX의 두 API — 커서형과 객체형.** StAX는 XML을 스트리밍으로 읽는 두 가지 API를 준다.
`XMLStreamReader`는 **커서형**이다: 하나의 커서가 문서를 훑고, 현재 이벤트의 값은
`getEventType()`·`getText()`·`getName()` 같은 접근자로 뽑아 쓴다. 객체를 만들지 않으므로
빠르지만, 커서가 이동하면 이전 값은 사라진다. `XMLEventReader`는 **객체형**이다: 이벤트마다
`XMLEvent` 객체를 하나씩 돌려주므로 보관·재사용이 가능한 대신 할당 비용이 있다. JDK의
`XMLInputFactory`는 스트림 리더에서 이벤트 리더를 만들어 주지만 그 반대는 만들어 주지
않는데, `XMLEventStreamReader`가 그 빈자리를 메운다 — 클래스 javadoc이 그 동기를 그대로
적어 두었다(`XMLEventStreamReader.java:37-39`).

**`sourceStart`가 무엇의 인덱스인가.** `getTextCharacters(int sourceStart, char[] target,
int targetStart, int length)`에는 인덱스가 둘 들어간다. `sourceStart`는 **원본 텍스트**
안의 시작 위치이고, `targetStart`는 **대상 버퍼** 안의 시작 위치다. 둘을 혼동하면 이 PR의
결함과 정확히 같은 모양이 나온다 — 상한은 "0부터 세는 전체 길이"로 계산하면서 복사는
offset부터 시작하게 된다. 파라미터 이름이 `source`/`target` 접두사로 갈라져 있다는 사실
자체가 두 세계를 구분하라는 신호인데, 상한 계산 한 줄이 그 구분을 놓쳤다.

**"최대 length"와 "실제 복사량"의 계약.** 이 메서드에서 `length`는 요청 상한이고 반환값은
실제 복사량이다. 둘이 다를 수 있다는 것이 API 설계의 전부다. 호출자는 그 차이를 종료
신호로 삼아 `sourceStart += 복사량`으로 전진하는 루프를 돈다. 그래서 "요청보다 적게
복사하고 그 수를 반환한다"는 동작은 예외적 처리가 아니라 **정상 종료 경로**다. 수정 전
코드는 그 경로를 만들어 낼 수 없었다 — 상한이 `sourceStart`와 무관하므로 마지막 조각에서
축소가 일어나지 않고, 대신 예외가 났다. 인덱스와 길이를 함께 받는 API를 구현할 때
"이 상한이 어느 지점을 기준으로 한 값인가"를 한 번 확인해야 하는 이유다.
