# java/java-data-processing/02 — XML SAX Parser (SAX 파서) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 두 권만 모이고 마지막 줄에는 2 가 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [SAX] 문서 파싱 시작
  [SAX] <book> 시작 (category=programming)
  [SAX] </book> 스킵: 이펙티브 자바 (36000원 < 40000원)
  [SAX] <book> 시작 (category=programming)
  [SAX] </book> 스킵: Clean Code (33000원 < 40000원)
  [SAX] <book> 시작 (category=database)
  [SAX] </book> 수집: Real MySQL (42000원)
  [SAX] <book> 시작 (category=spring)
  [SAX] </book> 수집: 토비의 스프링 (45000원)
  [SAX] 문서 파싱 완료 (수집: 2건)
2
```

**왜 그런가**
필터는 `</book>` 에서 `currentBook.price >= minPrice` 로 건다.
36000 과 33000 은 40000 보다 작아 스킵되고, 42000 과 45000 만 `books` 에 들어간다.
`endDocument()` 가 `books.size()` 를 찍고, `getBooks().size()` 도 같은 2 다.
근거 — 2-summary 「동작 방식 (4)」의 도서 표와 `</book>` 처리.

### 2. 요소 7 · 속성 3 · 텍스트 10자

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  요소 수: 7
  속성 수: 3
  텍스트 길이: 10자
```

**왜 그런가**
요소 수는 시작 태그 하나마다 1 이다 — `<shelf>` 1 + 책마다 `<book>` · `<title>` · `<price>` 3 × 2 = 7.
속성 수는 각 시작 태그의 `getLength()` 합이다 — 첫 책의 `category` · `lang` 2, 둘째 책의 `category` 1 → 3.
텍스트는 「가나」 2 + 「100」 3 + 「다라」 2 + 「200」 3 = 10 이다.
들여쓰기 · 줄바꿈뿐인 조각은 `trim()` 하면 0 이 된다.
네 값 모두 가운데 공백이 없으므로 조각이 어디서 쪼개져도 합은 같다.
근거 — 2-summary 「동작 방식 (5)」, 「어디서 틀리나 3」.

### 3. `startElement` 한 번 → `characters` 한 번 이상 → `endElement` 한 번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`startElement("author")` 가 한 번 불려 버퍼를 새로 만든다.
`characters()` 가 「조슈아 블로크」를 한 번에, 또는 여러 조각으로 나눠 한 번 이상 준다.
`endElement("author")` 가 한 번 불려 버퍼를 `trim()` 해 `currentBook.author` 에 넣는다.

**왜 그런가**
이벤트는 문서의 차례대로 오고, 글자는 조각으로 올 수 있다.
근거 — 2-summary 「동작 방식 (2)」, 「동작 방식 (3)」.

### 4. 글자가 조각으로 오면 마지막 조각만 남는다

`characters()` 는 한 요소의 글자를 한 번에 주지 않을 수 있다.
바로 대입하면 호출될 때마다 앞의 값을 덮어써, 「이펙티브 자바」가 「브 자바」처럼 잘린다.
그래서 조각을 `StringBuilder` 에 이어 붙이고, 모든 조각이 끝난 것이 확실한 `endElement` 에서 꺼낸다.
근거 — 2-summary 「동작 방식 (3)」, 「어디서 틀리나 1」.

### 5. `</bookstore>` 에서 `NullPointerException` 이 난다

`</book>` 을 처리한 뒤 `currentBook` 은 `null` 이 된다.
그다음 `</bookstore>` 가 오면, 이 검사가 없을 때 `switch` 에는 걸리지 않더라도 책 바깥 종료 태그의 처리에서 `currentBook` 을 건드릴 위험이 있다 — 예컨대 책 바깥에 `<title>` 같은 요소가 있으면 `currentBook.title = …` 에서 예외가 난다.
이 줄은 「지금 책 안이 아니면 아무것도 하지 않는다」를 보장한다.
근거 — 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 6. 아니다 — 파서는 작지만 `books` 목록은 커진다

SAX 파서는 문서를 트리로 쌓지 않으므로 파서 쪽 메모리는 파일 크기를 따라 커지지 않는다.
그러나 `minPrice` 가 0 이면 모든 책이 `books` 에 들어가므로 목록이 책 수만큼 커진다.
「메모리를 거의 안 쓴다」는 파서의 성질이고, 핸들러가 무엇을 모으느냐는 내 코드의 책임이다.
근거 — 2-summary 「어디서 틀리나 6」.

### 7. SAX 로는 안 된다 — DOM 을 고른다

SAX 는 앞에서부터 한 번만 읽고 지나간 요소로 돌아가지 못하며(랜덤 접근 불가), 읽기 전용이다.
뒤의 값을 보고 앞을 고쳐 다시 써야 하는 일은 전체를 트리로 올려 읽기 · 쓰기가 다 되는 DOM 이 맞다.
근거 — 2-summary 「동작 방식 (6)」, 「언제 쓰고 언제 안 쓰나」.

### 8. Push 는 파서가, Pull 은 내 코드가 흐름을 쥔다 — DOM 은 흐름이 아니라 트리다

SAX(Push)는 파서가 이벤트를 핸들러로 밀어 넣으므로 흐름이 파서에 있고, 내 코드는 콜백으로 응답만 한다.
StAX(Pull)는 내 코드가 「다음 이벤트」를 당겨 오므로 흐름을 내가 쥐어 코드가 직관적이다.
둘 다 순차 읽기다.
DOM 은 문서 전체를 메모리의 트리로 만든 뒤 아무 데나 접근하고 수정한다 — 대신 메모리를 많이 쓴다.
근거 — 2-summary 「동작 방식 (2)」, 「동작 방식 (6)」.

### 9. `DefaultHandler` 가 모든 메서드를 빈 몸체로 구현해 두었기 때문이다

`ContentHandler` 를 직접 구현하면 쓰지 않는 메서드까지 모두 적어야 한다.
`DefaultHandler` 는 그것들을 빈 메서드로 이미 구현해 두었으므로, 상속하고 필요한 `startElement` · `characters` 만 오버라이드하면 된다.
파서는 `endElement` 도 부르지만 빈 몸체가 받아 아무 일도 하지 않는다.
근거 — 2-summary 「동작 방식 (5)」의 `DefaultHandler` 풀이.

## 실습 정답

### 실습 1. SAX 로 도서 XML 을 걸러 읽고 통계 내기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 최소 가격 받기 | `BookHandler(int minPrice)` 생성자, `this.minPrice = minPrice` |
| 2. 요소마다 버퍼 새로 | `startElement` 의 `currentText = new StringBuilder()` |
| 3. `<book>` 시작 처리 | `"book".equals(qName)` 분기 — `new Book()`, `attributes.getValue("category")`, `<book> 시작` 로그 |
| 4. `<title>` 의 `lang` | `"title".equals(qName) && currentBook != null` 분기 — `titleLang` |
| 5. 조각 이어 붙이기 | `characters` 의 `currentText.append(ch, start, length)` |
| 6. 태그별 필드 채우기 | `endElement` 의 `if (currentBook == null) return;` 와 `switch (qName)` 의 `title` · `author` · `price` · `year` |
| 7. 필터와 수집/스킵 | `case "book" -> { … }` — `price >= minPrice`, `books.add`, 로그, `currentBook = null` |
| 8. 문서 시작/끝 로그 | `startDocument()` · `endDocument()` |
| 9. 목록 돌려주기 | `getBooks()` |
| 10. 요소 · 속성 세기 | `StatisticsHandler.startElement` — `elementCount++`, `attributes.getLength()` |
| 11. 텍스트 길이 | `StatisticsHandler.characters` — `new String(ch, start, length).trim()` |
| 12. 통계 출력 | `printStats()` |
| 13. 파서 만들기 | `SAXParserFactory.newInstance()`, `factory.newSAXParser()` |
| 14. 도서 파싱과 목록 출력 | `new BookHandler(35000)`, `saxParser.parse(…, bookHandler)`, `for (Book book : …)` |
| 15. 같은 파서로 통계 | 새 `ByteArrayInputStream` 과 `statsHandler` 로 두 번째 `parse`, `printStats()` |
| 16. 비교 세 줄 | `=== SAX vs DOM ===` 아래 `println` 세 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-data-processing/reference/xml-sax.java`

```java
// [데이터 처리 & 유틸] XML SAX Parser (SAX 파서)
// 설명: 이벤트 기반 스트리밍 방식으로 XML을 순차 처리. ContentHandler 콜백, 대용량 XML에 적합
// 팁: SAX는 메모리를 거의 사용하지 않아 수백MB~수GB XML도 처리할 수 있다. 단점은 랜덤 접근이 불가능하고 읽기 전용이라는 점이다. characters()는 한 번에 전체 텍스트를 주지 않을 수 있으므로 StringBuilder로 모아야 한다. StAX(XMLStreamReader)는 Pull 방식으로 SAX보다 코드 작성이 직관적이다.

// === XML SAX Parser: 이벤트 기반 대용량 XML 처리 ===

// SAXParser, SAXParserFactory: 표준 SAX 파서
import javax.xml.parsers.*;
// Attributes, ContentHandler 등 SAX API
import org.xml.sax.*;
// DefaultHandler: ContentHandler 등 모든 핸들러를 빈 메서드로 구현해둔 편의 클래스
import org.xml.sax.helpers.DefaultHandler;
// 바이트 배열 → InputStream
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

// 도서 DTO (SAX 핸들러가 한 책을 만들 때 사용)
class Book {
    String category;
    String title;
    String titleLang;
    String author;
    int price;
    int year;

    @Override
    public String toString() {
        return String.format("Book{category='%s', title='%s'(%s), author='%s', price=%d, year=%d}",
            category, title, titleLang, author, price, year);
    }
}

// SAX ContentHandler: 이벤트 콜백으로 XML 파싱
// DefaultHandler를 상속해 필요한 메서드만 오버라이드
class BookHandler extends DefaultHandler {
    private final List<Book> books = new ArrayList<>();
    // 현재 파싱 중인 도서 (book 시작 시 생성, 종료 시 books에 추가)
    private Book currentBook;
    // 텍스트 누적 버퍼 (characters가 여러 번 호출되어도 모두 모음)
    private StringBuilder currentText;
    private String currentElement;

    // 필터 조건: 가격 기준 필터링 (예시)
    private final int minPrice;

    public BookHandler(int minPrice) {
        this.minPrice = minPrice;
    }

    // 1. 시작 태그를 만나면 호출
    // qName: 정규화된 태그 이름. attributes: 태그 속성들
    @Override
    public void startElement(String uri, String localName, String qName, Attributes attributes) {
        // 새 요소 시작 시 텍스트 버퍼 초기화
        currentText = new StringBuilder();
        currentElement = qName;

        if ("book".equals(qName)) {
            currentBook = new Book();
            // 속성 접근: attributes.getValue("이름")
            currentBook.category = attributes.getValue("category");
            System.out.println("  [SAX] <book> 시작 (category=" + currentBook.category + ")");
        } else if ("title".equals(qName) && currentBook != null) {
            currentBook.titleLang = attributes.getValue("lang");
        }
    }

    // 2. 텍스트 내용을 만나면 호출 (여러 번 호출될 수 있음)
    // 함정: 큰 텍스트는 여러 번에 걸쳐 콜백되므로 한 번의 호출로 전체를 받았다고 가정하면 안 됨
    @Override
    public void characters(char[] ch, int start, int length) {
        if (currentText != null) {
            currentText.append(ch, start, length);
        }
    }

    // 3. 종료 태그를 만나면 호출
    @Override
    public void endElement(String uri, String localName, String qName) {
        if (currentBook == null) return;

        // 누적된 텍스트를 트림
        String text = currentText.toString().trim();

        // switch 표현식 (Java 14+)
        switch (qName) {
            case "title" -> currentBook.title = text;
            case "author" -> currentBook.author = text;
            // 빈 문자열 방어: 숫자 파싱 실패 방지
            case "price" -> currentBook.price = text.isEmpty() ? 0 : Integer.parseInt(text);
            case "year" -> currentBook.year = text.isEmpty() ? 0 : Integer.parseInt(text);
            case "book" -> {
                // 필터링: 최소 가격 이상인 도서만 수집
                if (currentBook.price >= minPrice) {
                    books.add(currentBook);
                    System.out.println("  [SAX] </book> 수집: " + currentBook.title + " (" + currentBook.price + "원)");
                } else {
                    System.out.println("  [SAX] </book> 스킵: " + currentBook.title + " (" + currentBook.price + "원 < " + minPrice + "원)");
                }
                currentBook = null;
            }
        }
    }

    // 4. 파싱 시작/종료 이벤트
    @Override
    public void startDocument() {
        System.out.println("  [SAX] 문서 파싱 시작");
    }

    @Override
    public void endDocument() {
        System.out.println("  [SAX] 문서 파싱 완료 (수집: " + books.size() + "건)");
    }

    public List<Book> getBooks() { return books; }
}

// 통계 수집 핸들러: 같은 XML을 다른 관심사로 처리하는 예시
class StatisticsHandler extends DefaultHandler {
    private int elementCount = 0;
    private int textLength = 0;
    private int attributeCount = 0;

    @Override
    public void startElement(String uri, String localName, String qName, Attributes attributes) {
        elementCount++;
        attributeCount += attributes.getLength();
    }

    @Override
    public void characters(char[] ch, int start, int length) {
        // 공백만 있는 텍스트는 무시 (들여쓰기 등)
        String text = new String(ch, start, length).trim();
        textLength += text.length();
    }

    public void printStats() {
        System.out.println("  요소 수: " + elementCount);
        System.out.println("  속성 수: " + attributeCount);
        System.out.println("  텍스트 길이: " + textLength + "자");
    }
}

public class XmlSaxDemo {
    static final String XML_DATA = """
        <?xml version="1.0" encoding="UTF-8"?>
        <bookstore>
            <book category="programming">
                <title lang="ko">이펙티브 자바</title>
                <author>조슈아 블로크</author>
                <price currency="KRW">36000</price>
                <year>2018</year>
            </book>
            <book category="programming">
                <title lang="en">Clean Code</title>
                <author>로버트 마틴</author>
                <price currency="KRW">33000</price>
                <year>2013</year>
            </book>
            <book category="database">
                <title lang="ko">Real MySQL</title>
                <author>이성욱</author>
                <price currency="KRW">42000</price>
                <year>2021</year>
            </book>
            <book category="spring">
                <title lang="ko">토비의 스프링</title>
                <author>이일민</author>
                <price currency="KRW">45000</price>
                <year>2022</year>
            </book>
        </bookstore>
        """;

    public static void main(String[] args) throws Exception {
        // SAXParserFactory: 보안 권장 설정 — feature로 외부 엔티티 비활성화 (XXE 방어)
        SAXParserFactory factory = SAXParserFactory.newInstance();
        SAXParser saxParser = factory.newSAXParser();

        // 1. 도서 파싱 (35000원 이상만 수집)
        // 같은 파서를 다른 핸들러로 여러 번 사용 가능
        System.out.println("=== SAX 파싱: 35000원 이상 도서 ===");
        BookHandler bookHandler = new BookHandler(35000);
        saxParser.parse(
            new ByteArrayInputStream(XML_DATA.getBytes(StandardCharsets.UTF_8)),
            bookHandler
        );

        System.out.println("\n수집된 도서:");
        for (Book book : bookHandler.getBooks()) {
            System.out.println("  " + book);
        }

        // 2. 통계 수집 (같은 XML, 다른 핸들러)
        System.out.println("\n=== XML 통계 ===");
        StatisticsHandler statsHandler = new StatisticsHandler();
        saxParser.parse(
            new ByteArrayInputStream(XML_DATA.getBytes(StandardCharsets.UTF_8)),
            statsHandler
        );
        statsHandler.printStats();

        // SAX vs DOM 비교
        System.out.println("\n=== SAX vs DOM ===");
        System.out.println("  SAX: 순차 읽기, 메모리 효율적, 읽기 전용, 이벤트 기반");
        System.out.println("  DOM: 전체 로드, 메모리 많이 사용, 읽기/쓰기, 트리 기반");
        System.out.println("  StAX: Pull 방식, SAX보다 사용 쉬움, 읽기/쓰기 가능");

        // 출력:
        // === SAX 파싱: 35000원 이상 도서 ===
        //   [SAX] 문서 파싱 시작
        //   [SAX] <book> 시작 (category=programming)
        //   [SAX] </book> 수집: 이펙티브 자바 (36000원)
        //   [SAX] <book> 시작 (category=programming)
        //   [SAX] </book> 스킵: Clean Code (33000원 < 35000원)
        //   [SAX] <book> 시작 (category=database)
        //   [SAX] </book> 수집: Real MySQL (42000원)
        //   [SAX] <book> 시작 (category=spring)
        //   [SAX] </book> 수집: 토비의 스프링 (45000원)
        //   [SAX] 문서 파싱 완료 (수집: 3건)
        //
        // 수집된 도서:
        //   Book{category='programming', title='이펙티브 자바'(ko), author='조슈아 블로크', price=36000, year=2018}
        //   Book{category='database', title='Real MySQL'(ko), author='이성욱', price=42000, year=2021}
        //   Book{category='spring', title='토비의 스프링'(ko), author='이일민', price=45000, year=2022}
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 결과는 `parse()` 의 반환값이 아니라 핸들러의 필드에 남는다 — 그래서 `getBooks()` 로 꺼낸다.
- 버퍼는 시작 태그에서 비우고, 조각은 `characters` 에서 붙이고, 값은 종료 태그에서 꺼낸다.
- `currentBook` 은 「지금 책 안인가」를 나타내는 상태다 — 만들고, 채우고, 넣고, `null` 로 되돌린다.
- 필터를 `</book>` 에서 걸어 조건에 맞지 않는 책은 메모리에 쌓지 않는다.
- 파서는 다시 쓰지만 입력 스트림은 매번 새로 만든다.
- 정답 코드 주석의 「XXE 방어」는 권고일 뿐 실제 feature 설정은 없다 — 2-summary 「어디서 틀리나 8」.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
