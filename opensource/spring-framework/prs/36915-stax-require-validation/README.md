# PR #36915 — Validate namespace and local name in require

## 0. 정향

이 문서는 `spring-core`의 StAX 유틸리티에 있는 `AbstractXMLStreamReader#require()` 수정 PR을 맥락부터 이해하기 위한 해설이다.\
핵심은 "표준 인터페이스의 세 인자짜리 검증 메서드가 인자 두 개를 통째로 무시하고 있었다"는 것이다.\
다 읽으면 "왜 이게 조용한 통과(silent pass)이고 어떤 호출자가 다치는가"와 "왜 수정에서 이벤트 타입 가드가 먼저 와야 하는가"를 설명할 수 있어야 한다.

> **StAX (Streaming API for XML)** — XML 문서를 앞에서 뒤로 한 번만 훑으며 읽는 JDK 표준 pull 방식 파서 API.\
> 예: `<?pi content?><root ...>` 문서를 START_DOCUMENT → PROCESSING_INSTRUCTION → START_ELEMENT 순으로 하나씩 꺼내 읽는다.

## 1. 배경 — 이 리더는 무엇이고 require()의 계약은 무엇인가

StAX에는 XML을 순차로 읽는 두 가지 API가 있다.\
`XMLStreamReader`는 커서형이고(현재 이벤트 한 개를 가리키며 `next()`로 전진), `XMLEventReader`는 이벤트 객체를 하나씩 꺼내 주는 형태다.\
JDK의 `XMLInputFactory`는 스트림 리더에서 이벤트 리더를 만들어 주지만 그 반대는 제공하지 않는다.\
Spring은 그 빠진 방향을 직접 채운다.

> **XMLStreamReader (커서 기반 파서)** — 리더 객체 하나가 "현재 위치"를 들고 있고, `next()`를 부를 때마다 그 위치가 다음 이벤트로 옮겨 가는 API.\
> 예: `streamReader.getLocalName()`은 "지금 커서가 가리키는 이벤트"의 로컬 이름을 돌려준다 — 커서가 움직이면 같은 호출이 다른 값을 준다.

> **XMLEventReader (이벤트 기반 파서)** — `nextEvent()` 호출마다 이벤트 객체를 새로 만들어 돌려주는 API.\
> 예: `eventReader.nextEvent()`가 돌려준 `XMLEvent`는 커서가 앞으로 나아간 뒤에도 자기 값을 그대로 들고 있다.

`XMLEventStreamReader`가 바로 그 어댑터다.\
클래스 javadoc이 존재 이유를 그대로 적어 두었다.

```java
/**
 * Implementation of the {@link javax.xml.stream.XMLStreamReader} interface that wraps a
 * {@link XMLEventReader}. Useful because the StAX {@link javax.xml.stream.XMLInputFactory}
 * allows one to create an event reader from a stream reader, but not vice-versa.
 * ...
 * @see StaxUtils#createEventStreamReader(javax.xml.stream.XMLEventReader)
 */
class XMLEventStreamReader extends AbstractXMLStreamReader {
```

> **어댑터 (Adapter)** — 한 인터페이스로 만들어진 객체를 다른 인터페이스인 척 감싸서 쓰게 해 주는 클래스.\
> 예: `XMLEventStreamReader`는 이벤트형 `XMLEventReader`를 감싸서 커서형 `XMLStreamReader`처럼 보이게 한다.

클래스 자체는 package-private이지만 공개 진입점이 하나 있다.\
`StaxUtils.createEventStreamReader(XMLEventReader)`가 public 메서드로 이 리더를 `XMLStreamReader` 타입으로 돌려준다.\
따라서 여기서 만들어지는 인스턴스는 프레임워크 내부용이 아니라 외부 코드가 표준 인터페이스로 쓰는 객체다.\
계약 위반이 공개 표면에 드러난다는 뜻이다.

> **package-private** — 자바에서 접근 제어자를 아무것도 붙이지 않았을 때의 가시성. 같은 패키지 안에서만 그 타입 이름을 쓸 수 있다.\
> 예: `class XMLEventStreamReader`는 `org.springframework.util.xml` 밖에서는 타입 이름조차 보이지 않지만, `XMLStreamReader` 타입으로 반환된 인스턴스 자체는 누구나 쓸 수 있다.

`AbstractXMLStreamReader`는 그 어댑터의 상위 클래스로, `XMLStreamReader`의 방대한 메서드 중 "현재 이벤트만 알면 파생시킬 수 있는 것들"을 공통 구현으로 모아 둔다.\
서브클래스는 `getName()`, `getEventType()`, `next()` 같은 원시 접근자만 제공하고, `getLocalName()`, `getNamespaceURI()`, `hasName()`, `isStartElement()` 등은 상위 클래스가 그 위에서 계산한다.\
이 파일은 2012년 모듈 리네이밍(`02a4473c62d`) 시점에 이미 존재했고, `require()`는 그때부터 지금 형태였다.

문제의 `require()` 계약은 JDK의 `javax.xml.stream.XMLStreamReader` javadoc에 명시돼 있다.

```text
 * Test if the current event is of the given type and if the namespace and name match the current
 * namespace and name of the current event.  If the namespaceURI is null it is not checked for equality,
 * if the localName is null it is not checked for equality.
 * @param type the event type
 * @param namespaceURI the uri of the event, may be null
 * @param localName the localName of the event, may be null
 * @throws XMLStreamException if the required values are not matched.
```

읽어야 할 규칙은 세 줄이다.\
첫째, 타입이 다르면 예외다.\
둘째, `namespaceURI`나 `localName`이 **null이 아니면** 현재 이벤트의 값과 같아야 하고, 다르면 예외다.\
셋째, null은 "검사하지 마라"는 뜻이다.\
즉 null은 와일드카드이지 무시 신호가 아니다 — 비-null 인자는 반드시 확인되어야 한다.

> **이벤트 타입 (event type)** — 커서가 지금 어떤 종류의 XML 조각 위에 있는지를 나타내는 `XMLStreamConstants`의 정수 상수.\
> 예: `START_ELEMENT`(=1)는 여는 태그, `END_ELEMENT`는 닫는 태그, `CHARACTERS`는 텍스트, `COMMENT`는 주석 위에 있다는 뜻이다.

> **namespaceURI / localName** — XML 요소 이름을 이루는 두 조각. 네임스페이스 URI는 요소의 진짜 신원이고, 로컬 이름은 접두사를 뗀 이름이다.\
> 예: `<root xmlns='namespace'>`의 namespaceURI는 `"namespace"`, localName은 `"root"`다.

용도는 단순하다.\
`require()`는 파싱 코드가 "여기까지 왔으면 커서는 반드시 이 요소여야 한다"를 코드로 못 박는 어서션이다.\
문서 형식이 기대와 다르면 이상한 값을 읽어 내려가는 대신 그 자리에서 실패하게 만드는 장치다.

> **어서션 (assertion)** — 값을 계산해 돌려주는 대신, 어떤 조건이 참임을 확인하고 아니면 즉시 실패시키는 장치.\
> 예: `require(START_ELEMENT, "namespace", "root")`은 아무 값도 돌려주지 않고, 커서가 그 요소가 아니면 `XMLStreamException`을 던진다.

## 2. 수정 전 동작 방식 — 실코드와 서사

수정 전 구현은 이벤트 타입만 비교하고 끝난다.\
두 인자는 시그니처에만 존재했다.

```java
@Override
public void require(int expectedType, String namespaceURI, String localName) throws XMLStreamException {
	int eventType = getEventType();
	if (eventType != expectedType) {
		throw new XMLStreamException("Expected [" + expectedType + "] but read [" + eventType + "]");
	}
}
```

호출이 실제로 지나가는 경로를 세로로 펴면, 세 인자 중 둘이 어디서도 읽히지 않는 것이 한눈에 보인다.\
커서가 `root`(네임스페이스 `namespace`)의 START_ELEMENT에 있을 때 `require(START_ELEMENT, "wrong-namespace", "wrong")`을 부른 경우다.

```text
호출자                                  reader.require(START_ELEMENT, "wrong-namespace", "wrong")
        |
        v
AbstractXMLStreamReader.require()       세 인자를 받는다
        |
        v
getEventType()                          XMLEventStreamReader 로 내려가 event.getEventType() = 1
        |
        v
eventType != expectedType ?             1 != 1 -> 거짓, 예외 없음
        |
        v
(본문 끝 - return)                      "wrong-namespace" 와 "wrong" 은 한 번도 읽히지 않는다
        |
        v
호출자                                  예외가 없었으므로 "검증했다" 고 믿고 계속 읽는다
```

메서드 본문 어디에도 `namespaceURI`와 `localName`이 등장하지 않는다.\
컴파일러는 불평하지 않는다 — 사용하지 않은 파라미터는 합법이다.\
그래서 이 구현은 "타입만 맞으면 무조건 통과"라는 반쪽 어서션으로 십수 년을 살아남았다.

주목할 점은, 같은 클래스에 이미 필요한 재료가 전부 있었다는 것이다.\
`getLocalName()`은 `getName().getLocalPart()`를 돌려주고, `getNamespaceURI()`는 요소 이벤트인지 확인한 뒤 `getName().getNamespaceURI()`를 돌려준다.

```java
@Override
public String getNamespaceURI() {
	int eventType = getEventType();
	if (eventType == XMLStreamConstants.START_ELEMENT || eventType == XMLStreamConstants.END_ELEMENT) {
		return getName().getNamespaceURI();
	}
	else {
		throw new IllegalStateException("Parser must be on START_ELEMENT or END_ELEMENT state");
	}
}
```

즉 검증에 필요한 접근자는 갖춰져 있었고, `require()`가 그것을 부르지 않았을 뿐이다.

## 3. 무엇이 문제였나 — 검증 누락이 만드는 구체 재현

문제를 한 문장으로 쓰면, **틀린 이름과 틀린 네임스페이스가 조용히 통과한다**.\
어서션이 실패해야 할 자리에서 성공을 반환하므로, 호출자는 자기가 검증했다고 믿는 상태로 잘못된 문서를 계속 읽는다.

> **조용한 통과 (silent pass)** — 실패를 알려야 할 검사가 아무 소리 없이 성공을 돌려주는 실패 모드. 틀린 값도 스택트레이스도 남지 않아 발견이 늦다.\
> 예: `require(START_ELEMENT, null, "wrong")`이 존재하지 않는 이름을 요구했는데도 예외 없이 반환된다.

재현은 짧다.\
테스트에 쓰이는 문서를 그대로 놓고 보자.

```java
private static final String XML =
		"<?pi content?><root xmlns='namespace'><prefix:child xmlns:prefix='namespace2'>content</prefix:child></root>"
		;
```

커서가 `root`(네임스페이스 `namespace`)의 START_ELEMENT에 있을 때, 수정 전 리더에 다음을 호출하면 어떤 것도 예외를 던지지 않는다.

```java
streamReader.require(XMLStreamConstants.START_ELEMENT, null, "wrong");
streamReader.require(XMLStreamConstants.START_ELEMENT, "wrong-namespace", "root");
```

같은 다섯 호출을 수정 전후에 나란히 놓으면 무엇이 달라지는지가 그대로 보인다.\
커서는 두 경우 모두 `{namespace}root`의 START_ELEMENT에 있다.

```text
수정 전 (타입만 비교)                       수정 후 (계약대로 세 축 비교)
+----------------------------------+      +----------------------------------+
| (null, "root")        -> 통과     |      | (null, "root")        -> 통과     |
| ("namespace","root")  -> 통과     |      | ("namespace","root")  -> 통과     |
| ("namespace", null)   -> 통과     |      | ("namespace", null)   -> 통과     |
| (null, "wrong")       -> 통과     |      | (null, "wrong")       -> 예외     |
| ("wrong-namespace",   -> 통과     |      | ("wrong-namespace",   -> 예외     |
|  "root")                         |      |  "root")                         |
+----------------------------------+      +----------------------------------+
  -> 다섯 호출이 전부 같은 결과          -> 맞는 셋은 통과, 틀린 둘만 걸린다
```

앞의 세 호출은 수정 전후 모두 통과하지만 통과하는 이유가 다르다 — 전에는 검사하지 않아서, 후에는 검사했는데 맞아서다.

첫 줄은 존재하지 않는 이름 `wrong`을 요구했는데 통과한다.\
둘째 줄은 네임스페이스가 완전히 다른데도 통과한다.\
표준 구현(JDK 기본 스트림 리더)에 같은 호출을 하면 둘 다 `XMLStreamException`이다.\
다시 말해 이 어댑터는 같은 인터페이스인데 다르게 행동한다 — 어댑터에서 가장 나쁜 종류의 결함이다.

피해 경로는 두 가지다.\
하나는 형식 검증용 호출자다.\
루트 요소가 기대한 스키마의 루트인지 `require()`로 확인하고 파싱을 진행하는 코드는, 엉뚱한 문서를 받아도 검증을 통과시킨 뒤 그 아래에서 훨씬 이해하기 어려운 방식으로 실패한다.\
다른 하나는 구현 교체다.\
`StaxUtils.createEventStreamReader()`가 돌려준 리더로 갈아탄 코드는 어서션이 소리 없이 약해진 것을 알아챌 방법이 없다.

이 결함이 오래 남은 이유도 분명하다.\
저장소 안에 `require()`를 호출하는 코드가 없다.\
이 메서드는 오직 외부 호출자를 위해 존재하는 공개 계약 표면이라, 내부 테스트가 결코 건드리지 않는 사각지대였다.

## 4. 수정 해설 — 무엇을 왜 바꿨나

수정은 계약대로 두 인자를 실제로 검증한다.\
최종 구현은 다음과 같다.

```java
@Override
public void require(int expectedType, @Nullable String namespaceURI, @Nullable String localName)
		throws XMLStreamException {

	int eventType = getEventType();
	if (eventType != expectedType) {
		throw new XMLStreamException("Expected [" + expectedType + "] but read [" + eventType + "]");
	}
	// This reader only exposes a name and namespace for START_ELEMENT and END_ELEMENT,
	// so a non-null namespace or local name can only ever match one of those events.
	if ((namespaceURI != null || localName != null) &&
			eventType != XMLStreamConstants.START_ELEMENT && eventType != XMLStreamConstants.END_ELEMENT) {
		throw new XMLStreamException("Current event is not a START_ELEMENT or END_ELEMENT");
	}
	if (localName != null && !localName.equals(getLocalName())) {
		throw new XMLStreamException("Expected local name [" + localName + "] but read [" + getLocalName() + "]");
	}
	if (namespaceURI != null && !namespaceURI.equals(getNamespaceURI())) {
		throw new XMLStreamException("Expected namespace [" + namespaceURI + "] but read [" + getNamespaceURI() + "]");
	}
}
```

네 블록의 판정 순서를 세로로 펴면, 각 단계가 무엇을 걸러 내고 무엇을 다음으로 넘기는지가 드러난다.

```text
require(expectedType, namespaceURI, localName)   세 인자를 전부 소비한다
        |
        v
[1] eventType != expectedType ?                  다르면 "Expected [n] but read [m]" 으로 탈락
        |  아니면 아래로
        v
[2] (ns != null || local != null)                이름을 노출할 수 없는 이벤트에서
    && 이벤트가 START/END_ELEMENT 가 아님 ?      비-null 이름을 요구하면 여기서 탈락
        |  아니면 아래로
        v
[3] local != null && !local.equals(getLocalName()) ?   "Expected local name [x] but read [y]"
        |  아니면 아래로                                null 이면 비교를 건너뛴다
        v
[4] ns != null && !ns.equals(getNamespaceURI()) ?      "Expected namespace [x] but read [y]"
        |  아니면 아래로                                null 이면 비교를 건너뛴다
        v
정상 반환                                        세 축이 모두 계약을 만족한 경우에만 여기 도달
```

**첫 블록은 그대로다.**\
타입 불일치 검사와 그 메시지는 손대지 않았다.\
기존 동작을 바꾸지 않는다는 신호이자, 이 PR이 순수하게 "빠진 검증을 더한다"임을 분명히 한다.

**둘째 블록이 이 수정의 핵심 판단이다.**\
이벤트 타입 가드를 이름 비교보다 **먼저** 둔다.\
이유는 안전이다.\
`getLocalName()`은 `getName()`을 부르고, `getName()`은 요소 이벤트가 아니면 `IllegalStateException`을 던진다.

```java
@Override
public QName getName() {
	if (this.event.isStartElement()) {
		return this.event.asStartElement().getName();
	}
	else if (this.event.isEndElement()) {
		return this.event.asEndElement().getName();
	}
	else {
		throw new IllegalStateException();
	}
}
```

가드가 없으면 `require(COMMENT, null, "x")` 같은 호출이 `XMLStreamException`이 아니라 `IllegalStateException`으로 터진다.\
이는 계약(`@throws XMLStreamException`) 위반이고, 호출자의 catch 절을 뚫고 나가는 런타임 예외다.\
가드를 앞세워, 이름을 노출할 수 없는 이벤트에서 비-null 이름을 요구하면 "불일치"로 판정하고 올바른 예외 타입으로 보고한다.

> **checked / unchecked 예외** — `XMLStreamException`처럼 시그니처의 `throws`에 적혀 호출자가 반드시 처리해야 하는 것이 checked, `IllegalStateException`처럼 `RuntimeException`을 상속해 그 의무가 없는 것이 unchecked다.\
> 예: 호출자가 `catch (XMLStreamException e)`만 써 둔 코드에 `IllegalStateException`이 날아오면 그 catch를 그냥 통과해 버린다.

같은 호출 `require(COMMENT, null, "x")`을 가드 유무로 나란히 놓으면 차이가 분명하다.

```text
가드가 없다면                             가드가 있으면 (수정안)
+----------------------------+          +----------------------------+
| 타입 비교 -> 통과           |          | 타입 비교 -> 통과           |
| localName 대조 진입         |          | 가드에서 탈락               |
|   getLocalName()           |          |   XMLStreamException       |
|   -> getName()             |          |   "Current event is not a  |
|   -> IllegalStateException |          |    START_ELEMENT or ..."   |
+----------------------------+          +----------------------------+
  -> 계약 밖 unchecked 예외가 샌다         -> 계약이 정한 예외 타입으로 보고
```

**셋째·넷째 블록이 실제 비교다.**\
각각 null이면 건너뛰고(계약의 와일드카드 규칙), 비-null이면 현재 값과 `equals`로 대조한다.\
예외 메시지는 기대값과 실제값을 함께 담아, 실패 지점에서 바로 원인을 읽을 수 있게 한다.\
인자 순서와 달리 `localName`을 먼저 검사하는데, 이름이 다른 쪽이 대개 더 이해하기 쉬운 진단이기 때문이다.

**시그니처에는 `@Nullable`이 붙었다.**\
계약상 두 인자는 null 허용이므로, 이제 그 사실이 타입 수준에 기록된다.\
`org.jspecify.annotations.Nullable`은 이 파일이 이미 `getAttributeValue`에서 쓰고 있어 import 변경이 없다.

한 가지 의도적으로 하지 않은 것이 있다.\
스펙은 ENTITY_REFERENCE에 대해서도 로컬 이름 검증을 허용하지만, 이 어댑터는 엔티티 이름을 노출할 방법이 없다 — `getName()`이 요소 이벤트 밖에서는 예외를 던지기 때문이다.\
그래서 PR은 그 범위를 시도하지 않고, "리더가 실제로 관측할 수 있는 범위 안에서 `require()`를 정직하게 만든다"는 경계를 택했다.\
이 선택은 PR 본문에 `## Note on scope`로 명시돼 있고, 메인테이너가 다른 경계를 원하면 조정하겠다는 여지를 함께 남겼다.

## 5. 검증 — 테스트가 무엇을 고정하나

테스트 하나가 계약의 세 규칙을 한 번에 못 박는다.

```java
@Test  // require(type, namespaceURI, localName) must validate the name and namespace
void requireValidatesNamespaceAndLocalName() throws Exception {
	advanceToStartElement("root");

	streamReader.require(XMLStreamConstants.START_ELEMENT, null, "root");
	streamReader.require(XMLStreamConstants.START_ELEMENT, "namespace", "root");
	streamReader.require(XMLStreamConstants.START_ELEMENT, "namespace", null);

	assertThatExceptionOfType(XMLStreamException.class).isThrownBy(() ->
			streamReader.require(XMLStreamConstants.START_ELEMENT, null, "wrong"));
	assertThatExceptionOfType(XMLStreamException.class).isThrownBy(() ->
			streamReader.require(XMLStreamConstants.START_ELEMENT, "wrong-namespace", "root"));
}
```

앞의 세 호출은 "맞으면 통과한다"를 고정한다.\
이름만 준 경우, 둘 다 준 경우, 네임스페이스만 준 경우 — null 와일드카드가 검사를 건너뛴다는 규칙까지 포함해 정상 경로가 좁아지지 않았음을 보인다.\
뒤의 두 단언이 회귀 방어선이다.\
각각 이름 불일치와 네임스페이스 불일치가 `XMLStreamException`이 되어야 하며, 이 두 줄은 수정 전 코드에서 반드시 실패한다.

> **회귀 방어선 (regression guard)** — 한 번 고친 결함이 나중에 되살아나면 즉시 빨간불이 켜지도록 걸어 두는 테스트.\
> 예: 뒤의 두 `isThrownBy` 단언은 누군가 검증 블록을 지우면 "예외가 던져지지 않았다"로 실패한다.

커서를 원하는 요소로 옮기는 헬퍼는 문서 앞머리의 processing instruction과 START_DOCUMENT를 건너뛰기 위한 것이다.

```java
private void advanceToStartElement(String localName) throws Exception {
	while (streamReader.getEventType() != XMLStreamConstants.START_ELEMENT ||
			!streamReader.getLocalName().equals(localName)) {
		streamReader.next();
	}
}
```

`getEventType()` 검사를 `||`의 왼쪽에 두어 단락 평가를 활용한 점이 중요하다.\
요소 이벤트가 아니면 오른쪽 `getLocalName()`을 아예 부르지 않으므로 `IllegalStateException`을 피한다 — 수정 본문의 가드 순서와 같은 이유다.

> **단락 평가 (short-circuit evaluation)** — `||`의 왼쪽이 참이면 오른쪽을 아예 실행하지 않는 자바의 평가 규칙.\
> 예: 커서가 START_DOCUMENT일 때 왼쪽 `getEventType() != START_ELEMENT`가 참이 되어 오른쪽 `getLocalName()`은 호출되지 않는다.

기존 테스트 `readAll`과 `readCorrect`는 그대로 남아, 이 변경이 일반적인 읽기·변환 경로를 건드리지 않았음을 계속 확인한다.

## 6. 상태와 교훈

PR은 2026-08-15 기준 **OPEN**이며 리뷰·코멘트가 아직 없다.\
대상 파일은 `spring-core/src/main/java/org/springframework/util/xml/AbstractXMLStreamReader.java` 하나이고 테스트가 함께 붙었다.

교훈 하나.\
**사용하지 않은 파라미터는 컴파일러가 잡아 주지 않는 결함 후보다.**\
시그니처가 세 인자를 받는데 본문이 한 인자만 읽는다면, 그것은 대개 "필요 없어서"가 아니라 "구현이 덜 됐기 때문"이다.\
표준 인터페이스를 구현할 때는 javadoc의 각 인자가 본문 어디에서 소비되는지 눈으로 대조해 볼 가치가 있다.

교훈 둘.\
**검증을 추가할 때는 검증 자체가 던지는 예외의 타입까지 설계해야 한다.**\
여기서 `getLocalName()`은 상황에 따라 `IllegalStateException`을 던지는 메서드였고, 그것을 조건 없이 호출했다면 계약이 약속한 `XMLStreamException` 대신 런타임 예외가 새어 나갔을 것이다.\
가드를 앞에 두는 한 줄이 "검증을 고쳤더니 다른 계약을 깼다"를 막는다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
