# java/java-data-processing/03 — XML JAXB Binding (JAXB 바인딩) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 언마샬링한 첫 책을 `toString()` 으로 찍으면 (예측)

```java
// 질문용 발췌
// XML_DATA 의 첫 <book>:
//   <book category="programming">
//       <title>이펙티브 자바</title> <author>조슈아 블로크</author>
//       <price currency="KRW">36000</price> <year>2018</year>
//   </book>
Bookstore bookstore = (Bookstore) unmarshaller.unmarshal(new StringReader(XML_DATA));
System.out.println("  " + bookstore.getBooks().get(0));
// JaxbBook.toString(): "Book{category='%s', title='%s', author='%s', price=%s, year=%d}"
// BookPrice.toString(): value + " " + currency
```

- 찍히는 한 줄은 어떤 모양인가?

### 2. 새 책 한 권을 마샬링하면 (예측)

```java
// 질문용 발췌
Bookstore newStore = new Bookstore();
newStore.addBook(new JaxbBook("java", "모던 자바 인 액션", "라울 외", 38000, "KRW", 2019));
marshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true);
marshaller.marshal(newStore, newWriter);
```

- `newWriter` 에 담기는 `<book>` 요소는 속성 · 자식 요소가 어떤 모양으로 놓이나?

### 3. 두 권을 읽고 한 권을 더한 뒤 마샬링하면 (예측)

```java
// 질문용 발췌
Bookstore bookstore = (Bookstore) unmarshaller.unmarshal(new StringReader(XML_DATA)); // <book> 2개
bookstore.addBook(new JaxbBook("spring", "토비의 스프링", "이일민", 45000, "KRW", 2022));
System.out.println("도서 추가 후: " + bookstore.getBooks().size() + "권");
marshaller.marshal(bookstore, writer);
```

- 찍히는 권수는 얼마이고, `writer` 의 XML 에는 `<book>` 요소가 몇 개 들어가나?

### 4. 매핑 클래스마다 기본 생성자를 두는 까닭 (왜)

- 인자 있는 생성자가 이미 있는데도 JAXB 는 왜 `public JaxbBook() {}` 를 따로 요구하나?

### 5. `@XmlAccessorType(XmlAccessType.FIELD)` 를 붙이는 까닭 (왜)

- 이 설정 없이 기본 접근 방식에 맡기면 필드 어노테이션과 public getter 가 함께 있을 때 무엇이 문제가 되나?

### 6. `<price currency="KRW">36000</price>` 를 받는 클래스의 한계 (경계)

- `BookPrice` 에 태그 사이 텍스트를 받을 `@XmlValue` 필드를 하나 더 둘 수 있나?

### 7. Java 11 이후 JDK 만으로 이 예제를 쓰려면 (경계)

- 의존성을 하나도 넣지 않거나, API 만 넣고 런타임 구현을 빼면 어디서 막히나?

### 8. `JAXBContext` 와 `Marshaller` · `Unmarshaller` 의 관계 (연결)

- 예제는 왜 `JAXBContext` 를 한 번만 만들고 거기서 `Unmarshaller` 와 `Marshaller` 를 꺼내며, 같은 `Marshaller` 를 두 객체에 다시 쓰나?

### 9. 손으로 쓴 매핑 클래스와 `xjc` (연결)

- 예제처럼 어노테이션을 직접 붙인 클래스와 `xjc` 가 만든 클래스는 어떤 관계이고, 언제 `xjc` 쪽으로 가나?

## 실습

### 실습 1. 서점 XML 을 읽고 고쳐 다시 XML 로 쓰기

**만들 것** — 서점 XML 문자열을 `Bookstore` 객체로 읽어 들이고, 책을 한 권 더한 뒤 다시 XML 로 쓰고, 새 서점 객체를 만들어 XML 로 쓰는 프로그램.

**준비물** — Java 11 이후라면 `jakarta.xml.bind:jakarta.xml.bind-api`(컴파일)와 `org.glassfish.jaxb:jaxb-runtime`(실행) 의존성이 필요하다.

**요구 조건**

1단계 — 매핑 정의

1. `Bookstore` 는 문서의 루트 요소이고 태그 이름은 `bookstore` 다.
2. 세 클래스 모두 getter 없이 필드를 직접 매핑하도록 접근 방식을 정한다.
3. `Bookstore` 의 `List<JaxbBook> books` 는 원소 하나가 `<book>` 요소 하나가 되게 한다.
4. `JaxbBook` 의 `category` 는 `<book>` 의 속성, `title` · `author` · `price` · `year` 는 자식 요소가 된다.
5. `BookPrice` 의 `currency` 는 속성, `value` 는 `<price>` 태그 사이 텍스트가 된다.
6. 세 클래스 모두 JAXB 가 객체를 만들 수 있게 기본 생성자를 둔다.

2단계 — 언마샬링

7. `Bookstore.class` 로 `JAXBContext` 를 한 번 만든다.
8. 그 컨텍스트의 `Unmarshaller` 로 `XML_DATA` 를 읽어 `Bookstore` 를 얻는다.
9. `=== 언마샬링 (XML -> 객체) ===` 머리 줄 뒤에 도서 수와 각 책(앞에 공백 두 칸)을 찍는다.

3단계 — 수정과 마샬링

10. `=== 객체 수정 ===` 머리 줄 뒤에 `토비의 스프링` 책(`spring`, `이일민`, 45000, `KRW`, 2022)을 더하고 `도서 추가 후: N권` 을 찍는다.
11. `=== 마샬링 (객체 -> XML) ===` 머리 줄 뒤에 같은 컨텍스트의 `Marshaller` 로 들여쓰기 · UTF-8 인코딩을 켜고 `bookstore` 를 문자열로 만들어 찍는다.

4단계 — 새 객체에서 XML 만들기

12. `=== 새 객체 -> XML ===` 머리 줄 뒤에 빈 `Bookstore` 를 만들고 `모던 자바 인 액션`(`java`, `라울 외`, 38000, `KRW`, 2019)과 `코틀린 인 액션`(`kotlin`, `드미트리`, 35000, `KRW`, 2017)을 더한다.
13. 3단계의 `Marshaller` 를 그대로 다시 써서 XML 문자열로 찍는다.

**시작 코드**

```java
import jakarta.xml.bind.*;
import jakarta.xml.bind.annotation.*;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.List;

// TODO: 루트 요소(태그 이름 bookstore) + 필드 직접 매핑
class Bookstore {
    // TODO: 원소마다 <book> 요소
    private List<JaxbBook> books = new ArrayList<>();

    // TODO: 기본 생성자

    public List<JaxbBook> getBooks() { return books; }
    public void setBooks(List<JaxbBook> books) { this.books = books; }
    public void addBook(JaxbBook book) { this.books.add(book); }
}

// TODO: 필드 직접 매핑
class JaxbBook {
    // TODO: 속성
    private String category;
    // TODO: 자식 요소 (아래 넷 모두)
    private String title;
    private String author;
    private BookPrice price;
    private int year;

    // TODO: 기본 생성자

    public JaxbBook(String category, String title, String author, int priceValue, String currency, int year) {
        this.category = category;
        this.title = title;
        this.author = author;
        this.price = new BookPrice(priceValue, currency);
        this.year = year;
    }

    public String getCategory() { return category; }
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
    public BookPrice getPrice() { return price; }
    public int getYear() { return year; }

    @Override
    public String toString() {
        return String.format("Book{category='%s', title='%s', author='%s', price=%s, year=%d}",
            category, title, author, price, year);
    }
}

// TODO: 필드 직접 매핑
class BookPrice {
    // TODO: 속성
    private String currency;
    // TODO: 태그 사이 텍스트
    private int value;

    // TODO: 기본 생성자

    public BookPrice(int value, String currency) {
        this.value = value;
        this.currency = currency;
    }

    @Override
    public String toString() {
        return value + " " + currency;
    }
}

public class XmlJaxbDemo {
    static final String XML_DATA = """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <bookstore>
            <book category="programming">
                <title>이펙티브 자바</title>
                <author>조슈아 블로크</author>
                <price currency="KRW">36000</price>
                <year>2018</year>
            </book>
            <book category="database">
                <title>Real MySQL</title>
                <author>이성욱</author>
                <price currency="KRW">42000</price>
                <year>2021</year>
            </book>
        </bookstore>
        """;

    public static void main(String[] args) throws Exception {
        // TODO: JAXBContext 한 번 만들기

        System.out.println("=== 언마샬링 (XML -> 객체) ===");
        // TODO: Unmarshaller 로 XML_DATA 읽기, 도서 수와 각 책 찍기

        System.out.println("\n=== 객체 수정 ===");
        // TODO: 토비의 스프링 추가, 권수 찍기

        System.out.println("\n=== 마샬링 (객체 -> XML) ===");
        // TODO: Marshaller 만들고 들여쓰기 · UTF-8 설정, bookstore 를 문자열로 찍기

        System.out.println("=== 새 객체 -> XML ===");
        // TODO: 새 Bookstore 에 두 권 넣고 같은 Marshaller 로 찍기
    }
}
```

**확인 방법** — 의존성을 넣고 `XmlJaxbDemo` 를 실행해, 도서 수가 2에서 3으로 바뀌는지, 마샬링한 XML 에 `<book category="…">` 와 `<price currency="KRW">…</price>` 꼴이 들여쓰기되어 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
