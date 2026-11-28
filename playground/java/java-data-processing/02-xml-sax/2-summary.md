# java/java-data-processing/02 — XML SAX Parser (SAX 파서) — 정리 (힌트)

> 출처 — study-site 항목 `java/xml-sax`(항목 데이터 `data/java/data-processing.json`) · 정답 코드 study-practice `java/java-data-processing/reference/xml-sax.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**SAX 는 「원고를 처음부터 끝까지 소리 내어 읽어 주는 낭독자」다.**
낭독자는 원고를 한 번에 넘겨주지 않는다.
「지금 제목이 시작된다」, 「글자는 이렇다」, 「제목이 끝났다」 하고 읽는 차례대로 외칠 뿐이다.
받아 적는 사람은 들은 것 가운데 필요한 것만 공책에 적는다.
지나간 대목을 다시 읽어 달라고 할 수는 없다.
SAX 파서와 핸들러도 똑같은 구조다.
파서가 XML 을 앞에서부터 읽으며 이벤트를 알리고, 핸들러가 그 이벤트를 받아 필요한 값만 모은다.

| 비유 | 실체 |
|---|---|
| 낭독자 | `SAXParser` |
| 「제목 시작!」 하는 외침 | `startElement()` 호출 |
| 「글자는 이렇다」 | `characters()` 호출 |
| 「제목 끝!」 | `endElement()` 호출 |
| 받아 적는 사람 | `DefaultHandler` 를 상속한 핸들러 (`BookHandler`) |
| 공책 | 핸들러의 필드 (`currentBook`, `books`) |
| 원고 전체를 복사해 책상에 펼치기 | DOM 방식 |

```text
XML 파일 ──(앞에서부터 한 번만 읽음)──▶ SAXParser
                                          │ 이벤트를 차례로 알림
                                          ▼
                          startElement · characters · endElement …
                                          │
                                          ▼
                                핸들러(BookHandler)
                                필요한 값만 골라 List<Book> 에 모음
```

## 이 주제가 답하려는 질문

1. 문서 전체를 메모리에 올리지 않고 XML 을 어떻게 읽나?
2. 파서가 알려 주는 이벤트는 어떤 것이 있고, 어떤 차례로 오나?
3. 이벤트가 따로따로 오는데, 「한 책」 같은 묶음은 어떻게 다시 조립하나?
4. SAX 는 DOM · StAX 와 무엇이 다르고, 언제 SAX 를 고르나?

## 동작 방식

### (1) 파서와 핸들러를 나눈다

**언제 쓰나** — SAX 로 XML 을 읽을 때마다 쓰는 기본 틀이다.
읽는 일(파서)과 무엇을 할지(핸들러)를 나눠 둔다.

```text
SAXParserFactory.newInstance()          파서를 만드는 공장을 얻는다
        │
        ▼
factory.newSAXParser()                  파서 하나를 만든다
        │
        ▼
saxParser.parse(입력 스트림, 핸들러)      XML 을 끝까지 읽으며
        │                               핸들러의 메서드를 차례로 부른다
        ▼
핸들러의 필드에 결과가 남는다              bookHandler.getBooks()
```

- 공장(`SAXParserFactory`)에서 파서(`SAXParser`)를 얻는다.
- `parse()` 에 입력(`InputStream`)과 핸들러를 함께 넘긴다.
- 파서는 값을 돌려주지 않는다 — 결과는 핸들러가 스스로 모은다.
- 그래서 `parse()` 가 끝난 뒤 핸들러에게 `getBooks()` 처럼 결과를 물어본다.

예제에서는 문자열 XML 을 `XML_DATA.getBytes(StandardCharsets.UTF_8)` 로 바이트로 바꾸고 `ByteArrayInputStream` 에 담아 넘긴다.

> **핸들러** — 파서가 알리는 이벤트를 받아 처리하는 객체.\
> 예: `BookHandler` 는 `<book>` 이 끝날 때마다 책 하나를 목록에 넣는다.

### (2) 이벤트는 문서의 차례대로 온다

**언제 쓰나** — 핸들러의 어느 메서드에 무슨 일을 넣을지 정할 때 이 차례를 떠올린다.

```text
<bookstore>
  <book category="programming">          ─▶ startElement("book", 속성: category)
    <title lang="ko">이펙티브 자바</title> ─▶ startElement("title", 속성: lang)
                                            characters("이펙티브 자바")  ← 한 번 이상
                                            endElement("title")
    …
  </book>                                ─▶ endElement("book")
</bookstore>

문서 처음 ─▶ startDocument()          문서 끝 ─▶ endDocument()
```

- 파서는 읽기 시작할 때 `startDocument()` 를 한 번 부른다.
- 시작 태그를 만날 때마다 `startElement(uri, localName, qName, attributes)` 를 부른다.
- 태그 사이 글자를 만나면 `characters(ch, start, length)` 를 부른다.
- 종료 태그를 만나면 `endElement(uri, localName, qName)` 을 부른다.
- 다 읽으면 `endDocument()` 를 한 번 부른다.

`qName` 은 태그 이름(예제에서는 `"book"`, `"title"` 같은 글자 그대로)이고, `attributes` 로 그 태그의 속성을 읽는다.
속성 하나는 `attributes.getValue("category")` 처럼 이름으로 꺼내고, 속성 개수는 `attributes.getLength()` 로 센다.
속성은 시작 태그에만 있으므로 `startElement` 에서만 읽을 수 있다.

> **콜백** — 내가 부르는 것이 아니라 상대(여기서는 파서)가 때가 되면 불러 주는 메서드.\
> 예: `endElement()` 는 내 코드가 부르지 않는다 — 파서가 `</book>` 을 만나면 부른다.

이 방식을 **Push 방식**이라 한다 — 파서가 이벤트를 핸들러 쪽으로 밀어 넣는다.

### (3) `characters()` 는 조각으로 올 수 있다

**언제 쓰나** — 태그 안의 글자(제목 · 가격 등)를 꺼낼 때 늘 이 함정을 막아야 한다.

```text
<title>이펙티브 자바</title>

startElement("title")   → currentText = new StringBuilder()     (버퍼 비우기)
characters("이펙티")     → currentText.append(…)  → "이펙티"
characters("브 자바")    → currentText.append(…)  → "이펙티브 자바"
endElement("title")     → currentText.toString().trim() 를 title 에 넣는다
```

- 시작 태그에서 버퍼(`StringBuilder`)를 새로 만든다.
- `characters()` 가 몇 번 불리든 받은 조각을 버퍼 뒤에 붙인다.
- 종료 태그에서 버퍼를 문자열로 바꾸고 `trim()` 으로 앞뒤 공백을 걷어 쓴다.
- 원본 팁 그대로 — `characters()` 는 한 번에 전체 텍스트를 주지 않을 수 있으므로 `StringBuilder` 로 모아야 한다.
- 위 그림의 쪼개진 지점은 예시일 뿐이다 — 어디서 쪼개질지, 쪼개질지 말지는 정해져 있지 않다.

태그 사이의 줄바꿈 · 들여쓰기 공백도 `characters()` 로 온다.
예제의 `BookHandler` 는 이 공백도 버퍼에 붙이지만, 다음 시작 태그에서 버퍼를 다시 비우고 종료 태그에서 `trim()` 을 하므로 결과가 흐려지지 않는다.
`characters()` 안의 `if (currentText != null)` 은 첫 시작 태그 전에 버퍼가 아직 없을 때를 막는다.

### (4) 묶음은 핸들러가 상태를 들고 다시 조립한다

**언제 쓰나** — 「책 하나」처럼 여러 태그에 흩어진 값을 객체 하나로 모을 때 쓴다.

예제가 읽는 XML 은 네 권의 책이다(`<bookstore>` 안에 `<book>` 넷).

| 차례 | category | title (lang) | author | price | year |
|---|---|---|---|---|---|
| 1 | programming | 이펙티브 자바 (ko) | 조슈아 블로크 | 36000 | 2018 |
| 2 | programming | Clean Code (en) | 로버트 마틴 | 33000 | 2013 |
| 3 | database | Real MySQL (ko) | 이성욱 | 42000 | 2021 |
| 4 | spring | 토비의 스프링 (ko) | 이일민 | 45000 | 2022 |

각 `<book>` 은 `category` 속성을, `<title>` 은 `lang` 속성을, `<price>` 는 `currency="KRW"` 속성을 가진다.

```text
<book category=…>   startElement   → currentBook = new Book(), category 저장, "<book> 시작" 로그
<title lang=…>      startElement   → currentBook.titleLang 저장
</title>            endElement     → currentBook.title = 버퍼
</author>           endElement     → currentBook.author = 버퍼
</price>            endElement     → currentBook.price = 숫자로 바꾼 버퍼 (빈 문자열이면 0)
</year>             endElement     → currentBook.year  = 숫자로 바꾼 버퍼 (빈 문자열이면 0)
</book>             endElement     → price >= minPrice 이면 books 에 넣고 "수집" 로그
                                     아니면 "스킵" 로그
                                     그리고 currentBook = null
```

- `<book>` 이 시작되면 빈 `Book` 을 만들어 `currentBook` 에 둔다.
- 자식 태그가 끝날 때마다 `switch (qName)` 으로 어느 필드에 넣을지 고른다.
- `</book>` 에서 가격 필터(`minPrice`)를 통과한 책만 `books` 목록에 넣는다.
- 그다음 `currentBook` 을 `null` 로 되돌려 「지금은 책 안이 아니다」를 표시한다.
- `endElement` 첫 줄 `if (currentBook == null) return;` 은 책 바깥의 종료 태그(`</bookstore>`)를 걸러 낸다.
- `endDocument()` 에서 모은 건수를 로그로 남긴다.

필터를 파싱하는 도중에 거는 것이 핵심이다.
조건에 맞지 않는 책은 목록에 들어가지 않으므로 메모리에 쌓이지 않는다.
`minPrice` 를 35000 으로 주면 33000 원인 `Clean Code` 하나만 스킵되고 세 권이 남는다.

### (5) 같은 파서, 다른 핸들러

**언제 쓰나** — 같은 XML 에서 서로 다른 것(목록 · 통계)을 뽑고 싶을 때, 관심사마다 핸들러를 따로 만든다.

```text
saxParser.parse(입력1, bookHandler)    → 책 목록
saxParser.parse(입력2, statsHandler)   → 요소 수 · 속성 수 · 텍스트 길이

StatisticsHandler
  startElement → elementCount++ , attributeCount += attributes.getLength()
  characters   → textLength += (받은 조각을 trim 한 길이)
```

- 파서 하나를 두 번 쓴다 — 핸들러만 바꿔 끼운다.
- 다만 입력 스트림은 한 번 읽으면 끝나므로 매번 새 `ByteArrayInputStream` 을 만든다.
- `StatisticsHandler` 는 시작 태그 하나마다 요소 수를 1 늘린다 — 루트 `<bookstore>` 도 센다.
- 속성 수는 각 시작 태그의 `attributes.getLength()` 를 더한 값이다.
- 텍스트 길이는 조각마다 `trim()` 한 길이를 더한다 — 들여쓰기 공백뿐인 조각은 0 이 된다.
- `DefaultHandler` 를 상속했으므로 `endElement` 같은 나머지 메서드는 쓰지 않아도 된다.

> **DefaultHandler** — `ContentHandler` 등 SAX 핸들러 인터페이스의 메서드를 모두 빈 몸체로 구현해 둔 편의 클래스.\
> 예: `StatisticsHandler` 는 `startElement` 와 `characters` 만 오버라이드한다.

### (6) SAX · DOM · StAX 견주기

**언제 쓰나** — XML 을 읽는 방법을 고를 때.

```text
SAX   파서 ─이벤트 밀어 줌─▶ 핸들러      (Push)  순차 읽기 · 읽기 전용 · 메모리 적음
StAX  코드 ─다음 것 달라─▶ 리더          (Pull)  순차 읽기 · 코드가 직관적
DOM   파일 전체 ─▶ 메모리의 트리          (트리)  아무 데나 접근 · 수정 가능 · 메모리 많이
```

- SAX 는 순차 읽기 · 메모리 효율적 · 읽기 전용 · 이벤트 기반이다.
- DOM 은 문서 전체를 트리로 메모리에 올린다 — 메모리를 많이 쓰지만 읽기와 쓰기가 다 된다.
- StAX(`XMLStreamReader`)는 Pull 방식이다 — 내 코드가 「다음 이벤트」를 직접 당겨 오므로 SAX 보다 코드 작성이 직관적이다.
- 원본 팁 그대로 — SAX 는 메모리를 거의 쓰지 않아 수백 MB~수 GB XML 도 처리할 수 있다.
- 대신 랜덤 접근이 안 되고 읽기 전용이다 — 지나간 요소로 돌아갈 수 없고, 문서를 고쳐 쓸 수 없다.

## 문법 — 형태와 규칙

```java
import javax.xml.parsers.*;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;

class NameHandler extends DefaultHandler {
    private StringBuilder buf;
    @Override
    public void startElement(String uri, String localName, String qName, Attributes atts) {
        buf = new StringBuilder();                 // 요소마다 버퍼 새로
    }
    @Override
    public void characters(char[] ch, int start, int length) {
        if (buf != null) buf.append(ch, start, length);   // 조각을 이어 붙임
    }
    @Override
    public void endElement(String uri, String localName, String qName) {
        if ("name".equals(qName)) System.out.println(buf.toString().trim());
    }
}
// SAXParserFactory.newInstance().newSAXParser().parse(inputStream, new NameHandler());
```

- 핸들러는 `DefaultHandler` 를 상속하고 필요한 메서드만 `@Override` 한다.
- 메서드 시그니처는 정해져 있다 — `startElement(String uri, String localName, String qName, Attributes attributes)` · `characters(char[] ch, int start, int length)` · `endElement(String uri, String localName, String qName)` · `startDocument()` · `endDocument()`.
- `characters` 의 글자는 `ch` 배열 전체가 아니라 `ch[start]` 부터 `length` 개뿐이다 — `append(ch, start, length)` 나 `new String(ch, start, length)` 로 그 범위만 쓴다.
- 태그 이름 비교는 `"book".equals(qName)` 처럼 상수 쪽에서 `equals` 를 부른다.
- 속성은 `attributes.getValue("이름")` 으로, 개수는 `attributes.getLength()` 로 읽는다.
- 숫자 필드는 `Integer.parseInt(text)` 로 바꾸되, 빈 문자열이면 0 으로 둔다(예제의 방어).
- 예제의 `case "title" -> …` 는 화살표 꼴 `switch` 다 — 원본 주석은 Java 14+ 라 적는다.
- 예제의 `XML_DATA` 는 `"""` 로 감싼 여러 줄 문자열(텍스트 블록)이다.

## 어디서 틀리나

### 1. `characters()` 한 번에 전체 글자가 온다고 믿기

`characters()` 에서 `title = new String(ch, start, length)` 처럼 바로 대입하면, 글자가 쪼개져 올 때 마지막 조각만 남는다.
원본 팁 — 한 번에 전체 텍스트를 주지 않을 수 있으므로 `StringBuilder` 로 모으고, 종료 태그에서 꺼내 쓴다.

### 2. 버퍼를 비우지 않기

`startElement` 에서 버퍼를 새로 만들지 않으면 앞 요소의 글자와 공백이 다음 요소에 섞인다.
예제는 시작 태그마다 `currentText = new StringBuilder()` 로 비운다.

### 3. 공백 조각을 잊기

들여쓰기 · 줄바꿈도 `characters()` 로 온다.
`trim()` 없이 쓰면 값 앞뒤에 공백이 붙는다.
`StatisticsHandler` 처럼 조각마다 `trim()` 하면 공백뿐인 조각은 0 이 되지만, 글자 중간의 공백이 조각 경계에 걸리면 그 공백까지 깎여 길이가 줄 수 있다(원본에 근거 없음 — 추론).

### 4. 책 바깥의 이벤트를 막지 않기

`</bookstore>` 같은 바깥 종료 태그에서 `currentBook` 을 건드리면 `NullPointerException` 이 난다.
예제는 `endElement` 첫 줄에서 `currentBook == null` 이면 곧바로 돌아간다.

### 5. 숫자 파싱

빈 `<price></price>` 를 `Integer.parseInt("")` 로 바꾸면 예외가 난다.
예제는 빈 문자열이면 0 으로 둔다.
숫자가 아닌 글자(예: `"36,000"`)는 이 방어로 막히지 않고 여전히 `NumberFormatException` 이 난다(원본에 근거 없음 — 추론).

### 6. 「메모리를 거의 안 쓴다」를 핸들러에까지 넓히기

원본 팁은 SAX 가 메모리를 거의 쓰지 않아 수백 MB~수 GB 도 처리한다고 한다.
이것은 파서가 문서를 트리로 쌓지 않는다는 뜻이다.
핸들러가 결과를 목록에 모으면 그 목록은 조건에 맞는 건수만큼 커진다 — `BookHandler` 의 `books` 가 그렇다.
그래서 필터를 파싱 중에 거는 것이 중요하다.

### 7. 지나간 요소로 돌아가려 하기

SAX 는 앞에서부터 한 번만 읽는다.
「뒤에 나오는 요소를 보고 앞 요소를 처리」해야 하면 앞 값을 필드에 따로 들고 있어야 한다.
문서를 고쳐 써야 하면 SAX 가 아니라 DOM 을 쓴다.

### 8. 원본 주석과 코드가 어긋나는 곳

- **원본의 주장** — `main` 의 주석이 「SAXParserFactory: 보안 권장 설정 — feature로 외부 엔티티 비활성화 (XXE 방어)」라고 적는다.
  **왜 의심스러운가** — 코드에는 `factory.newSAXParser()` 만 있고 feature 를 거는 호출이 없다. 주석은 「이렇게 해야 한다」는 권고일 뿐, 이 코드가 막아 주지는 않는다.
- **원본의 주장** — 주석이 `switch (qName)` 을 「switch 표현식」이라 부른다.
  **왜 의심스러운가** — 결과 값을 쓰지 않으므로 화살표 꼴을 쓴 `switch` 문에 가깝다(원본에 근거 없음 — 추론).
- 필드 `currentElement` 는 값을 넣기만 하고 어디서도 읽지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `characters()` 가 글자를 여러 조각으로 나눠 줄 수 있다 | SAX API 가 허용한다 — 실제로 어디서 쪼갤지는 파서 구현이 정한다 |
| 이벤트가 문서의 차례대로 온다 | SAX API |
| `DefaultHandler` 의 메서드는 빈 몸체다 | SAX API (`org.xml.sax.helpers`) |
| `SAXParserFactory.newInstance()` 가 어떤 파서를 주나 | 실행 환경(JDK · 설정)에 따른다 (확인 필요) |
| 태그 사이 공백이 `characters()` 로 오나, 다른 이벤트로 오나 | DTD · 검증 설정과 파서 구현에 따른다 (확인 필요) |
| 수백 MB~수 GB 도 처리할 수 있다 | 원본 팁의 서술 — 실제 한계는 핸들러가 모으는 양과 환경에 따른다 |
| 화살표 꼴 `switch` 와 텍스트 블록 | Java 언어 (버전 요건은 「더 들어가면」) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 수백 MB 넘는 XML 에서 조건에 맞는 것만 뽑기 | SAX (또는 StAX) | DOM — 전체를 메모리에 올린다 |
| 한 번 훑으며 개수 · 합계 같은 통계 내기 | SAX — 핸들러 하나로 끝 | DOM |
| 앞뒤를 오가며 여러 번 찾아보기 | DOM | SAX — 랜덤 접근이 안 된다 |
| XML 을 고쳐서 다시 쓰기 | DOM (또는 StAX 의 쓰기 쪽) | SAX — 읽기 전용 |
| 순차로 읽되 흐름을 내 코드로 조절하고 싶다 | StAX (`XMLStreamReader`) | SAX — 콜백이라 흐름이 파서에 있다 |

## 핵심 문장

1. **SAX 는 XML 을 앞에서부터 한 번 읽으며 이벤트를 핸들러에 밀어 넣는다** — 문서 트리를 만들지 않는다.
2. **결과는 핸들러가 상태(필드)를 들고 스스로 조립한다** — 시작 태그에서 만들고, 종료 태그에서 채우고 넣는다.
3. **`characters()` 는 조각으로 올 수 있으므로 버퍼에 모으고 종료 태그에서 꺼낸다.**
4. **메모리가 적은 대신 랜덤 접근과 쓰기를 포기한다** — 그것이 필요하면 DOM, 흐름을 직접 쥐고 싶으면 StAX.
5. **관심사마다 핸들러를 나누면 같은 파서로 같은 XML 을 여러 용도로 읽는다.**

## 관련 자료

- `xml-dom` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [xml-jaxb](../03-xml-jaxb/2-summary.md)
- `batch-processing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/data-processing.json` 의 `xml-sax`

## 용어 풀이

- **SAX** — Simple API for XML. 이벤트 기반으로 XML 을 순차 처리하는 API.
- **이벤트 기반** — 무언가를 만났을 때 알림(이벤트)을 받아 처리하는 방식.
- **스트리밍** — 데이터를 다 받아 두지 않고 흘러오는 대로 처리하는 방식.
- **콜백** — 상대가 때가 되면 불러 주는 메서드.
- **핸들러** — 파서의 이벤트를 받아 처리하는 객체.
- **ContentHandler** — 시작 태그 · 글자 · 종료 태그 같은 내용 이벤트를 받는 SAX 인터페이스.
- **DefaultHandler** — SAX 핸들러 인터페이스들을 빈 메서드로 구현해 둔 편의 클래스.
- **qName** — 정규화된 태그 이름. 예제에서는 `"book"` 같은 태그 이름 그대로.
- **Attributes** — 시작 태그의 속성 묶음. `getValue(이름)` · `getLength()` 로 읽는다.
- **DOM** — 문서 전체를 트리로 메모리에 올려 다루는 방식.
- **StAX** — 내 코드가 다음 이벤트를 당겨 오는 Pull 방식 XML API. `XMLStreamReader` 로 읽는다.
- **Push / Pull** — 파서가 이벤트를 밀어 주나(Push), 코드가 당겨 오나(Pull).
- **DTO** — 값을 담아 나르기만 하는 객체. 예제의 `Book`.
- **랜덤 접근** — 원하는 위치로 곧바로 가서 읽는 것.
- **XXE** — XML 외부 엔티티를 이용한 공격.

## 더 들어가면

- `localName` 과 `uri` 는 네임스페이스 처리를 켰을 때 채워진다. 기본 팩토리는 네임스페이스 처리가 꺼져 있어 `localName` 이 빈 문자열일 수 있고, 그래서 예제는 `qName` 을 쓴다 (확인 필요).
- XXE 를 막으려면 팩토리에 `setFeature(…)` 로 외부 엔티티 · DOCTYPE 을 끄는 설정을 건다. feature 이름은 파서마다 다를 수 있다 (확인 필요).
- `SAXParser` 는 여러 스레드가 함께 쓰기에 안전하지 않다고 알려져 있다 — 스레드마다 따로 만든다 (확인 필요).
- 텍스트 블록(`"""`)은 Java 15 에서 정식 기능이 되었다 (확인 필요). 이 예제를 컴파일하려면 그 이상이 필요하다.
- DTD 로 검증할 때는 요소 사이 공백이 `characters()` 대신 `ignorableWhitespace()` 로 올 수 있다 (확인 필요).
- StAX 는 쓰기용 `XMLStreamWriter` 도 갖고 있어 「읽기/쓰기 가능」이라 소개된다 (확인 필요).
- 깊이 중첩된 XML 에서는 현재 경로를 스택(`Deque<String>`)으로 들고 다니는 패턴을 흔히 쓴다 (확인 필요).
