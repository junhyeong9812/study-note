# java/java-data-processing/02 — XML SAX Parser (SAX 파서) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 최소 가격을 40000 으로 바꾸면 (예측)

```java
// 질문용 발췌 — XML 은 정리의 네 권(가격 36000, 33000, 42000, 45000 차례) 그대로
BookHandler h = new BookHandler(40000);
saxParser.parse(new ByteArrayInputStream(XML_DATA.getBytes(StandardCharsets.UTF_8)), h);
System.out.println(h.getBooks().size());
```

- 어느 책이 「수집」, 어느 책이 「스킵」 로그를 남기고, 마지막 줄에는 몇이 찍히나?

### 2. 작은 XML 을 통계 핸들러로 읽으면 (예측)

```java
// 질문용 발췌 — StatisticsHandler 로 이 XML 을 parse 한다
String xml = """
    <shelf>
      <book category="a"><title lang="ko">가나</title><price>100</price></book>
      <book category="b"><title>다라</title><price>200</price></book>
    </shelf>
    """;
```

- `printStats()` 가 알리는 요소 수 · 속성 수 · 텍스트 길이는 각각 얼마인가?

### 3. 태그 하나를 읽을 때 불리는 메서드의 차례 (예측)

- `<author>조슈아 블로크</author>` 한 줄을 읽는 동안 `BookHandler` 의 어느 메서드가 어떤 차례로, 몇 번씩 불리나?

### 4. `characters()` 에서 값을 바로 대입하지 않고 `StringBuilder` 에 모으는 까닭 (왜)

- 왜 `characters()` 에서 `title = new String(ch, start, length)` 로 바로 넣으면 위험한가?

### 5. `endElement` 가 `currentBook == null` 검사로 시작하는 까닭 (왜)

- 이 한 줄이 없으면 어느 종료 태그에서 무슨 일이 생기나?

### 6. 「메모리를 거의 안 쓴다」가 어디까지 맞나 (경계)

- 수 GB 짜리 도서 XML 에 `new BookHandler(0)` 을 쓰면 메모리 사용이 파일 크기와 상관없이 작게 유지되나?

### 7. SAX 로 할 수 없는 일 (경계)

- 마지막 `<book>` 의 가격을 보고 첫 `<book>` 을 고쳐 파일에 다시 써야 한다면 SAX 로 되나, 무엇을 골라야 하나?

### 8. SAX · StAX · DOM 의 차이 (연결)

- Push 와 Pull 은 「흐름을 누가 쥐나」에서 어떻게 다르고, DOM 은 이 둘과 무엇이 근본적으로 다른가?

### 9. `ContentHandler` 를 직접 구현하지 않고 `DefaultHandler` 를 상속하는 까닭 (연결)

- `StatisticsHandler` 가 `endElement` 를 쓰지 않고도 핸들러로 동작할 수 있는 것은 무엇 덕분인가?

## 실습

### 실습 1. SAX 로 도서 XML 을 걸러 읽고 통계 내기

**만들 것** — 네 권의 도서 XML 을 SAX 로 읽어 최소 가격 이상인 책만 모으는 핸들러와, 같은 XML 의 요소 · 속성 · 텍스트 길이를 세는 핸들러를 만들고, 파서 하나로 두 번 읽는다.

**요구 조건**

1단계 — 도서 핸들러 `BookHandler` (`DefaultHandler` 상속)
1. 생성자로 최소 가격 `minPrice` 를 받아 둔다.
2. `startElement` 는 요소가 시작될 때마다 텍스트 버퍼(`StringBuilder`)를 새로 만든다.
3. `<book>` 이 시작되면 새 `Book` 을 `currentBook` 에 두고 `category` 속성을 넣은 뒤 `  [SAX] <book> 시작 (category=…)` 로그를 찍는다.
4. 책 안에서 `<title>` 이 시작되면 `lang` 속성을 `titleLang` 에 넣는다.
5. `characters` 는 버퍼가 있을 때 받은 조각을 버퍼 뒤에 이어 붙인다.
6. `endElement` 는 `currentBook` 이 없으면 곧바로 돌아가고, 있으면 버퍼를 `trim()` 한 글자를 태그 이름에 따라 `title` · `author` · `price` · `year` 에 넣는다 — 가격과 연도는 정수로 바꾸되 빈 문자열이면 0.
7. `</book>` 에서 가격이 `minPrice` 이상이면 목록에 넣고 `  [SAX] </book> 수집: 제목 (가격원)` 을, 아니면 `  [SAX] </book> 스킵: 제목 (가격원 < 최소가격원)` 을 찍은 뒤 `currentBook` 을 비운다.
8. `startDocument` 는 `  [SAX] 문서 파싱 시작` 을, `endDocument` 는 `  [SAX] 문서 파싱 완료 (수집: N건)` 을 찍는다.
9. `getBooks()` 로 모은 목록을 돌려준다.

2단계 — 통계 핸들러 `StatisticsHandler`
10. 시작 태그마다 요소 수를 1 늘리고 그 태그의 속성 개수를 더한다.
11. `characters` 로 받은 조각을 `trim()` 한 길이를 텍스트 길이에 더한다.
12. `printStats()` 는 요소 수 · 속성 수 · 텍스트 길이를 한 줄씩 찍는다.

3단계 — `main`
13. 팩토리에서 파서 하나를 만든다.
14. 「35000원 이상 도서」 제목을 찍고, `BookHandler(35000)` 로 XML 을 읽은 뒤 모은 책을 한 줄씩 찍는다.
15. 「XML 통계」 제목을 찍고, 같은 파서와 새 입력 스트림으로 `StatisticsHandler` 를 돌려 통계를 찍는다.
16. 끝으로 SAX · DOM · StAX 비교 세 줄을 찍는다.

**시작 코드**

```java
import javax.xml.parsers.*;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

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

class BookHandler extends DefaultHandler {
    private final List<Book> books = new ArrayList<>();
    private Book currentBook;
    private StringBuilder currentText;
    private final int minPrice;

    public BookHandler(int minPrice) {
        // TODO: 최소 가격 저장
    }

    @Override
    public void startElement(String uri, String localName, String qName, Attributes attributes) {
        // TODO: 버퍼 새로 만들기
        // TODO: <book> 이면 Book 생성 + category 속성 + 로그
        // TODO: 책 안의 <title> 이면 lang 속성
    }

    @Override
    public void characters(char[] ch, int start, int length) {
        // TODO: 버퍼가 있으면 조각 이어 붙이기
    }

    @Override
    public void endElement(String uri, String localName, String qName) {
        // TODO: 책 바깥이면 돌아가기
        // TODO: 버퍼를 trim 해서 태그 이름별로 필드에 넣기 (price · year 는 빈 문자열이면 0)
        // TODO: </book> 이면 가격 필터 → 수집/스킵 로그 → currentBook 비우기
    }

    @Override
    public void startDocument() {
        // TODO: 시작 로그
    }

    @Override
    public void endDocument() {
        // TODO: 완료 로그 (수집 건수)
    }

    public List<Book> getBooks() { return books; }
}

class StatisticsHandler extends DefaultHandler {
    private int elementCount = 0;
    private int textLength = 0;
    private int attributeCount = 0;

    // TODO: startElement — 요소 수 +1, 속성 수 더하기

    // TODO: characters — trim 한 길이 더하기

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
        // TODO: 팩토리 → 파서

        System.out.println("=== SAX 파싱: 35000원 이상 도서 ===");
        // TODO: BookHandler(35000) 으로 parse

        System.out.println("\n수집된 도서:");
        // TODO: 모은 책을 "  " + book 으로 찍기

        System.out.println("\n=== XML 통계 ===");
        // TODO: 새 입력 스트림 + StatisticsHandler 로 parse, printStats()

        System.out.println("\n=== SAX vs DOM ===");
        System.out.println("  SAX: 순차 읽기, 메모리 효율적, 읽기 전용, 이벤트 기반");
        System.out.println("  DOM: 전체 로드, 메모리 많이 사용, 읽기/쓰기, 트리 기반");
        System.out.println("  StAX: Pull 방식, SAX보다 사용 쉬움, 읽기/쓰기 가능");
    }
}
```

**확인 방법** — 파일을 `XmlSaxDemo.java` 로 저장하고 `javac XmlSaxDemo.java && java XmlSaxDemo` 로 돌린다.
`Clean Code` 만 「스킵」 되고 세 권이 「수집된 도서」에 나오는지, 통계 세 줄이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
