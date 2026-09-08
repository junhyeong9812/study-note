# PR #36915 — 무대의 실구조와 워크플로우

> PR #36915의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이 커밋에는 PR #36915가 아직 반영되지 않았으므로,
> 아래 file:line 인용은 전부 **수정 전 코드**를 그대로 가리킨다.

## 1. 무대 — 실구조

이 PR의 무대는 클래스 세 개와 인터페이스 두 개가 만드는 얇은 어댑터 층이다. 결론부터
말하면, **`XMLEventStreamReader`가 JDK의 이벤트형 리더를 커서형 리더로 둔갑시키고,
`AbstractXMLStreamReader`가 그 둔갑에 필요한 파생 메서드를 전부 대신 계산한다.**
`require()`는 그 파생 메서드 층에 속한다.

먼저 소유·상속 관계다.

```
javax.xml.stream.XMLStreamReader              (JDK 표준 인터페이스, 커서형)
        ▲ implements
        │
┌───────┴──────────────────────────────────────────────────────────┐
│ AbstractXMLStreamReader                    (package-private,     │
│   AbstractXMLStreamReader.java:32)          abstract)            │
│                                                                  │
│  필드 없음 — 상태를 전혀 갖지 않는다                              │
│                                                                  │
│  [파생 구현 — 서브클래스의 원시 접근자 위에서 계산]               │
│    getLocalName()      :180  → getName().getLocalPart()          │
│    getNamespaceURI()   :81   → 요소 이벤트 확인 후 getName()      │
│    getPrefix()         :104  → 요소 이벤트 확인 후 getName()      │
│    hasName()           :115  → 이벤트 타입이 요소인가             │
│    hasText()           :96   → 이벤트 타입이 텍스트류인가         │
│    isStartElement()    :126 / isEndElement() :131                │
│    getElementText()    :35   → next() 루프로 텍스트 수집          │
│    nextTag()           :141  → 공백·주석·PI를 건너뛰며 next()     │
│    require(...)        :155  ◀── 이 PR의 대상                     │
│    getAttributeValue(ns, local) :163                             │
│    getTextCharacters() :186 / getTextLength() :198               │
└──────────────────────────────────────────────────────────────────┘
        ▲ extends
        │
┌───────┴──────────────────────────────────────────────────────────┐
│ XMLEventStreamReader        (XMLEventStreamReader.java:45)       │
│                                                                  │
│  필드                                                             │
│    XMLEvent       event        :47   ← 현재 커서가 가리키는 이벤트 │
│    XMLEventReader eventReader  :49   ← 감싼 이벤트 소스           │
│                                                                  │
│  [원시 접근자 — 상위 클래스가 이 위에서 파생 계산]                │
│    getEventType()  :76  → event.getEventType()                   │
│    getName()       :58  → start/end면 QName, 아니면 ISE           │
│    next()          :274 → event = eventReader.nextEvent()        │
│    getText()       :152 / getLocation() :72 / close() :280        │
│    getAttributeCount() :166 / getAttributeName(i) :180 …          │
└──────────────────────────────────────────────────────────────────┘
        ▲ 생성
        │
  StaxUtils.createEventStreamReader(XMLEventReader)   StaxUtils.java:303
        └─ public static — 이 어댑터의 유일한 공개 진입점
```

여기서 두 가지가 이 PR을 설명한다.

첫째, **`AbstractXMLStreamReader`는 상태가 없다.** 필드가 하나도 없고, 모든 메서드가
서브클래스의 `getEventType()`·`getName()`을 다시 불러 계산한다. 그래서 `require()`가
이름과 네임스페이스를 검증하려면 새 자료를 끌어올 필요가 없다 — 같은 클래스의
`getLocalName()`(:180)과 `getNamespaceURI()`(:81)를 부르면 끝이다. 재료는 이미 손 안에
있었고, 수정 전 `require()`는 그것을 쓰지 않았을 뿐이다.

둘째, **이름을 노출할 수 있는 이벤트는 두 종류뿐이다.** `getName()`은 시작·끝 요소가
아니면 `IllegalStateException`을 던진다.

```
XMLEventStreamReader.getName()            (XMLEventStreamReader.java:58-69)
   ├─ event.isStartElement() → asStartElement().getName()   QName
   ├─ event.isEndElement()   → asEndElement().getName()     QName
   └─ 그 외                   → throw new IllegalStateException()   ← 가드 없는 호출은 여기로
```

`getLocalName()`도 `getNamespaceURI()`도 결국 이 메서드를 지나간다. 즉 "이름을 비교하는
코드"는 어느 것이든 이벤트 타입 가드를 먼저 통과해야 안전하다. 이것이 3절 분기도에서
핵심이 되는 구조적 제약이다.

세 번째 등장인물은 검증 대상이 아니라 데이터 소스다.

```
javax.xml.stream.XMLEventReader   (JDK, 이벤트형)
        │  nextEvent() 호출마다 XMLEvent 객체 하나
        ▼
   XMLEvent  ── START_DOCUMENT / PROCESSING_INSTRUCTION / START_ELEMENT
                / CHARACTERS / END_ELEMENT / END_DOCUMENT …
        │
        └─ StartElement.getName() → QName{namespaceURI, localPart, prefix}
```

`QName`은 네임스페이스 URI와 로컬 이름을 함께 담는 JDK 타입이다. `require()`의 두
파라미터는 정확히 이 `QName`의 두 구성 요소와 대응한다.

## 2. 수정 전 동작 워크플로우

무대에 오르는 시나리오를 둘로 나눈다. 하나는 어댑터가 만들어져 문서를 훑는 정상
흐름이고, 다른 하나는 그 도중 호출자가 `require()`로 위치를 확인하는 흐름이다.
**전자는 수정 전후가 같고, 후자만 이 PR이 바꾼다.**

### 2.1 어댑터 생성과 문서 순회

`XMLEventReader`를 커서형으로 바꿔 쓰는 전체 경로다. 실제 호출자는 4절에서 다룬다.

```
호출자
  │
  │ StaxUtils.createEventStreamReader(eventReader)          StaxUtils.java:303
  ▼
new XMLEventStreamReader(eventReader)                       XMLEventStreamReader.java:52
  │  생성자가 곧바로 eventReader.nextEvent() 1회
  │  → this.event = 첫 이벤트(START_DOCUMENT)
  │  즉 "생성 직후 커서는 이미 첫 이벤트 위에 있다"
  ▼
XMLStreamReader 타입으로 반환 (구현 클래스는 package-private이라 외부에서 안 보인다)
  │
  │ 호출자 루프
  ▼
while (reader.hasNext()) {                    AbstractXMLStreamReader.java:176
    int type = reader.next();                 XMLEventStreamReader.java:274
    //  ├ this.event = eventReader.nextEvent()
    //  └ return this.event.getEventType()
    …  reader.getLocalName() / getText() / getAttributeValue(...) 로 내용 소비
}
```

테스트 픽스처 문서로 커서 위치를 구체화하면 이렇다.

```
XML: <?pi content?><root xmlns='namespace'>
                     <prefix:child xmlns:prefix='namespace2'>content</prefix:child></root>

생성자 직후    event = START_DOCUMENT           getName() → IllegalStateException
next()  ①     event = PROCESSING_INSTRUCTION   getName() → IllegalStateException
next()  ②     event = START_ELEMENT root       getName() → {namespace}root      ★
next()  ③     event = START_ELEMENT child      getName() → {namespace2}child
next()  ④     event = CHARACTERS "content"     getName() → IllegalStateException
next()  ⑤     event = END_ELEMENT child        getName() → {namespace2}child
next()  ⑥     event = END_ELEMENT root         getName() → {namespace}root
next()  ⑦     event = END_DOCUMENT             hasNext() → false
```

위 표에서 별표를 붙인 `START_ELEMENT root` 줄이 tests.md의
`advanceToStartElement("root")`가 멈추는 자리이고, 아래 2.2의 출발점이다.

### 2.2 수정 전 `require()` 호출

호출자가 "커서가 지금 `{namespace}root`의 시작 태그여야 한다"를 못 박으려고
`require()`를 부르는 흐름이다. 수정 전 본문(`AbstractXMLStreamReader.java:155-161`)은
파라미터 세 개 중 하나만 읽는다.

```
호출자: reader.require(START_ELEMENT, "wrong-namespace", "wrong")
  │
  ▼
AbstractXMLStreamReader.require(expectedType, namespaceURI, localName)   :155
  │
  ├─ int eventType = getEventType();                                     :157
  │      └→ XMLEventStreamReader.getEventType()  :76  →  event.getEventType()
  │                                                      = START_ELEMENT (1)
  │
  ├─ if (eventType != expectedType) → throw XMLStreamException            :158
  │      · 1 == 1 이므로 통과
  │
  └─ (본문 끝)                                                            :161
         namespaceURI 와 localName 은 한 번도 읽히지 않는다.
         메서드가 정상 반환 → 호출자는 "검증했다"고 믿는다.
```

수정 전 본문을 데이터 흐름으로 그리면 두 인자가 그대로 버려지는 것이 한눈에 보인다.

```
   expectedType ─────────────┐
                             ▼
   getEventType() ────────► [ != 비교 ] ──► 불일치면 XMLStreamException
                                          └─ 일치하면 return

   namespaceURI  ──► (소비처 없음)
   localName     ──► (소비처 없음)
```

컴파일러는 사용되지 않은 파라미터를 오류로 보지 않는다. 그래서 이 반쪽 구현이
구조적으로 조용히 유지되었다. 대비를 위해 같은 클래스의 다른 메서드는 두 인자를
모두 소비한다는 점을 붙여 둘 만하다. `getAttributeValue(namespaceURI, localName)`
(:163-173)은 `localName`을 `equals`로 대조하고 `namespaceURI`가 null이면 건너뛰는,
바로 그 "null = 와일드카드" 규칙을 이미 구현하고 있다.

## 3. 분기 처리 워크플로우

`require()`의 분기 구조를 수정 전후로 나란히 놓으면 이 PR이 정확히 무엇을 채우는지가
드러난다. **수정 전 분기도에는 잎이 두 개뿐이고, 그중 하나가 잘못된 통과를 흡수한다.**

### 3.1 수정 전 (버그가 살던 분기)

수정 전 분기도는 질문 하나에 잎 둘로 끝난다.

```
require(expectedType, namespaceURI, localName)
        │
        ▼
  getEventType() == expectedType ?
        │
   ┌────┴──────────────────────────────┐
   │ 아니오                            │ 예
   ▼                                   ▼
XMLStreamException                 return (정상 종료)      ◀◀ 버그가 살던 분기
"Expected [n] but read [m]"          │
                                     ├─ localName 이 "wrong" 이어도 여기로
                                     ├─ namespaceURI 가 "wrong-ns" 여도 여기로
                                     └─ 둘 다 null 이어도 여기로 (이것만 정상)
```

버그의 성격은 "틀린 분기로 간다"가 아니라 **"분기 자체가 없다"**이다. 검증 실패를
표현할 잎이 존재하지 않으므로, 세 가지 서로 다른 상황이 모두 같은 잎(정상 반환)으로
수렴한다. 호출자 입장에서는 성공과 미검증이 구분되지 않는다.

### 3.2 수정 후 (PR이 만드는 분기)

PR은 잎을 셋 더 만든다. 순서가 중요하다 — **이름을 읽기 전에 이름을 읽어도 되는
이벤트인지부터 판정한다.**

```
require(expectedType, namespaceURI, localName)
        │
        ▼
 ① getEventType() == expectedType ?
        │
   ┌────┴────┐
   │ 아니오  │ 예
   ▼         ▼
 XMLStream   ② (namespaceURI != null || localName != null)
 Exception       && 이벤트가 START_ELEMENT/END_ELEMENT 가 아님 ?
                     │
                ┌────┴────┐
                │ 예      │ 아니오
                ▼         ▼
        XMLStreamException  ③ localName != null
        "Current event is      && !localName.equals(getLocalName()) ?
         not a START_ELEMENT       │
         or END_ELEMENT"      ┌────┴────┐
              ▲               │ 예      │ 아니오
              │               ▼         ▼
    이 잎이 없으면    XMLStreamException  ④ namespaceURI != null
    getLocalName() →  "Expected local        && !namespaceURI.equals(getNamespaceURI()) ?
    getName() 이         name [x] but            │
    IllegalState         read [y]"          ┌────┴────┐
    Exception 을                            │ 예      │ 아니오
    던져 계약을                             ▼         ▼
    깨뜨린다                     XMLStreamException   return (정상)
                                 "Expected namespace
                                  [x] but read [y]"
```

두 번째 분기, 곧 이벤트 타입 가드가 이 수정의 설계 판단이다. 근거는 1절에서 본 구조적
제약이다.

```
③·④ 가 부르는 것         실제로 도달하는 곳                이벤트가 요소가 아니면
────────────────────    ──────────────────────────    ──────────────────────
getLocalName()      →   getName().getLocalPart()      IllegalStateException
  :180                    XMLEventStreamReader:58        (계약 밖 런타임 예외)
getNamespaceURI()   →   요소 확인 후 getName()          IllegalStateException
  :81                     AbstractXMLStreamReader:87     ("Parser must be on
                                                          START_ELEMENT or
                                                          END_ELEMENT state")
```

즉 이 가드가 없으면 `require(COMMENT, null, "x")` 같은 호출이 메서드 시그니처가 약속한
`XMLStreamException`(checked) 대신 `IllegalStateException`(unchecked)으로 빠져나간다.
가드를 앞세워, 이름을 노출할 수 없는 이벤트에서의 비-null 요구를 "불일치"로 판정하고
계약이 정한 예외 타입으로 보고한다.

한편 null 인자의 처리는 로컬명 비교와 네임스페이스 비교 각각의 첫 조건이 담당한다.
null이면 비교를 건너뛴다 —
JDK javadoc이 정한 와일드카드 규칙이다. 그래서 `require(START_ELEMENT, null, null)`은
수정 후에도 타입만 보고 통과하며, 이 부분은 수정 전과 동작이 같다.

## 4. 스프링 전역에서의 자리

이 어댑터는 프레임워크 안에서 **딱 한 곳**에서만 만들어진다. 저장소 전체를 grep한
결과, `StaxUtils.createEventStreamReader`의 실제 호출처는 하나다.

```
AbstractMarshaller.unmarshal(Source)                 AbstractMarshaller.java:389
   │  Source 타입 판별
   ├─ DOMSource            → unmarshalDomSource(...)
   ├─ StaxUtils.isStaxSource(source)  :393
   │     └→ unmarshalStaxSource(source)              :443
   │           ├─ StaxUtils.getXMLStreamReader(staxSource)  != null
   │           │     └→ unmarshalXmlStreamReader(streamReader)   (어댑터 불필요)
   │           └─ StaxUtils.getXMLEventReader(staxSource)   != null
   │                 └→ unmarshalXmlEventReader(eventReader)     :451
   │                       │  (abstract, :604)
   │                       ▼
   │                    XStreamMarshaller.unmarshalXmlEventReader(...)
   │                                        XStreamMarshaller.java:784
   │                       │
   │                       │ StaxUtils.createEventStreamReader(eventReader)   :786
   │                       ▼
   │                    ★ new XMLEventStreamReader(eventReader)
   │                       │
   │                       │ unmarshalXmlStreamReader(streamReader)           :787
   │                       ▼
   │                    new StaxReader(new QNameMap(), streamReader, nameCoder)
   │                       └→ XStream 라이브러리가 이 커서형 리더로 문서를 읽는다
   ├─ SAXSource            → unmarshalSaxSource(...)
   └─ StreamSource         → unmarshalStreamSource(...)
```

여기서 두 가지를 확인해 둘 필요가 있다.

**첫째, 프레임워크 내부에는 `require()` 호출자가 없다.** 저장소 전체에서 `.require(`를
grep하면 이 메서드를 부르는 코드가 나오지 않는다. 위 경로에서 실제로 리더를 소비하는
쪽은 XStream 라이브러리의 `StaxReader`이고, 그것이 `require()`를 쓰는지는 Spring이
통제하지 않는다. 즉 `require()`는 **내부 소비자가 없는 공개 계약 표면**이다. 결함이
오래 살아남은 구조적 이유가 여기 있다 — 내부 테스트가 결코 밟지 않는 코드였다.

**둘째, 공개 표면인 것은 분명하다.** 진입점 `StaxUtils.createEventStreamReader`는
`public static`이고(`StaxUtils.java:303`) 반환 타입이 JDK 표준 `XMLStreamReader`다.
구현 클래스 `XMLEventStreamReader`가 package-private이어도, 반환된 객체를 받은 외부
코드는 표준 인터페이스의 모든 메서드를 계약대로 쓸 권리가 있다. `require()`도 그중
하나다.

참고로 같은 `spring-core`의 StAX 유틸리티 층은 `spring-oxm`·`spring-web`의 여러
지점에서 쓰인다(`AbstractMarshaller`, `Jaxb2Marshaller`, `XmlEventDecoder`,
`Jaxb2XmlDecoder`, `JacksonXmlDecoder`, `Jaxb2CollectionHttpMessageConverter` 등).
다만 그것들이 쓰는 것은 `StaxUtils`의 다른 팩터리(`createXMLReader`,
`createStaxSource`, `getXMLStreamReader` 등)이고, 이번 무대인 이벤트->스트림 어댑터로
들어오는 경로는 위의 XStream 하나뿐이다.

## 5. 관련 개념

이 구조를 이해하는 데 필요한 개념 넷을 여기서 설명한다(해당 개념의 별도 문서는 아직 없다).

### 5.1 StAX의 두 API — 커서형과 이벤트형

StAX는 XML을 앞에서 뒤로 한 번만 훑는 pull 방식 파서이고, 같은 일을 하는 API가 두 벌
있다.

```
커서형  XMLStreamReader          이벤트형  XMLEventReader
─────────────────────────      ────────────────────────────
리더 객체 하나가 "현재 위치"    nextEvent() 호출마다 XMLEvent
를 들고 있고, next() 로 전진     객체를 새로 만들어 돌려준다

값은 리더에게 묻는다             값은 이벤트 객체에게 묻는다
  reader.getLocalName()           event.asStartElement()
  reader.getText()                     .getName().getLocalPart()

객체 할당이 없어 빠르다          이벤트를 보관·재생할 수 있다
현재 위치를 벗어나면 정보 소실   지나간 이벤트도 그대로 남는다
```

JDK의 `XMLInputFactory`는 `createXMLEventReader(XMLStreamReader)`, 즉 **커서형에서
이벤트형으로 가는 방향만** 제공한다. Spring이 그 반대 방향을 직접 구현한 것이
`XMLEventStreamReader`이고, 클래스 javadoc(`XMLEventStreamReader.java:37-43`)이 그
사실을 존재 이유로 적어 두었다.

방향이 왜 한쪽만 표준에 있는지는 정보량으로 설명된다. 이벤트형은 커서형보다 정보가
많다(이벤트 객체가 자기 값을 다 들고 있다). 많은 쪽에서 적은 쪽을 만드는 것은
자연스럽지만, 반대는 "현재 이벤트 하나만 붙들고 커서인 척"해야 한다. 이 어댑터가
필드로 `XMLEvent event` 하나만 들고 있는 것(`:47`)이 정확히 그 "인 척"의 구현이다.

### 5.2 QName — 네임스페이스와 로컬 이름

XML의 요소 이름은 문자열 하나가 아니라 두 조각이다.

```
<prefix:child xmlns:prefix='namespace2'>

  prefix     → 접두사. 문서 안에서만 의미 있는 별명
  namespace2 → 네임스페이스 URI. 진짜 신원
  child      → 로컬 이름

QName = { namespaceURI: "namespace2", localPart: "child", prefix: "prefix" }
```

접두사는 문서마다 자유롭게 바뀔 수 있으므로 비교 대상이 되지 못한다. 그래서
`require()`가 받는 두 인자는 접두사가 아니라 **네임스페이스 URI와 로컬 이름**이고,
`AbstractXMLStreamReader`도 그 둘을 각각 `getNamespaceURI()`(:81)와
`getLocalName()`(:180)으로 노출한다. 두 값을 함께 대조해야 비로소 "이 요소가 맞다"고
말할 수 있다.

기본 네임스페이스(`xmlns='namespace'`)를 선언하면 접두사 없는 요소도 그 URI를 갖는다.
tests.md의 픽스처가 `root`에 기본 네임스페이스를 붙여 둔 이유가 이것이다 — 네임스페이스가
없는 문서였다면 `getNamespaceURI()`가 빈 문자열을 돌려주어 네임스페이스 검증을 시험할
수 없다.

### 5.3 어댑터 + 템플릿 메서드 — 파생 메서드를 상위로 올리는 이유

`XMLStreamReader`는 메서드가 수십 개인 넓은 인터페이스다. 그중 상당수는 "현재 이벤트
타입과 현재 이름만 알면 계산할 수 있는" 파생값이다. Spring은 그 파생 계산을 추상
상위 클래스에 모으고, 서브클래스에는 진짜 원시 접근자만 남겼다.

```
서브클래스가 제공해야 하는 것 (원시)      상위 클래스가 계산해 주는 것 (파생)
────────────────────────────────      ──────────────────────────────────
getEventType()                    →   isStartElement() / isEndElement()
                                       isCharacters() / isWhiteSpace()
                                       hasName() / hasText() / hasNext()
getName()                         →   getLocalName() / getNamespaceURI()
                                       getPrefix()
next()                            →   nextTag() / getElementText()
getText()                         →   getTextCharacters() / getTextLength()
getAttributeName(i)               →   getAttributeLocalName(i)
getAttributeValue(i)                   getAttributeNamespace(i)
                                       getAttributePrefix(i)
                                       getAttributeValue(ns, localName)
```

이 배치의 장점은 새 어댑터를 붙일 때 구현할 메서드가 확 줄어든다는 것이다. 대가는
**파생 메서드의 결함이 모든 서브클래스에 동시에 상속된다**는 점이다. `require()`가
바로 그 자리에 있다. 현재 서브클래스는 `XMLEventStreamReader` 하나뿐이지만
(grep 확인), 구조상 이 층에 붙는 결함은 어댑터 개수만큼 곱해진다.

### 5.4 조용한 통과 — 어서션이 사라지는 실패 모드

`require()`가 하는 일은 계산이 아니라 어서션이다. 어서션의 실패 모드는 일반 로직과
다르다.

```
일반 메서드가 고장나면        어서션이 고장나면
──────────────────────      ──────────────────────────────
틀린 값이 흘러나온다          아무 값도 흘러나오지 않는다
호출자가 곧 이상을 느낀다     호출자는 "확인했다"고 믿는다
스택트레이스가 남는다         아무 흔적도 남지 않는다
```

이 차이 때문에 어서션의 무력화는 발견이 늦다. 게다가 어서션이 지켜 주던 조건이
깨진 채로 진행되므로, 실제 실패는 훨씬 뒤 엉뚱한 자리에서 훨씬 이해하기 어려운
형태로 나타난다. 3.1의 분기도에서 "정상 반환" 잎이 세 가지 상황을 한꺼번에 흡수하는
그림이 이 실패 모드의 구조적 원인이다.

관련해서 `../../concepts/`에는 이 주제를 다루는 문서가 아직 없다. 인접 개념으로
계약과 구현의 어긋남을 다루는 [`../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md`]
(../../concepts/annotation-all-or-nothing-contract/annotation-all-or-nothing-contract.md)가 있으나, 대상 도메인이 달라
직접 연결되지는 않는다.
