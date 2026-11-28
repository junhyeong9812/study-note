# java/java-data-processing/03 — XML JAXB Binding (JAXB 바인딩) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 속성 · 요소 · 텍스트가 모두 채워진 한 줄이 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  Book{category='programming', title='이펙티브 자바', author='조슈아 블로크', price=36000 KRW, year=2018}
```

**왜 그런가**
- `category` 는 `@XmlAttribute` 라서 `<book category="programming">` 의 속성값을 받는다.
- `title` · `author` · `year` 는 `@XmlElement` 라서 같은 이름의 자식 요소 텍스트를 받고, `year` 는 `int` 로 바뀐다.
- `price` 는 `BookPrice` 객체가 되어 `currency` 에 속성 `KRW`, `value` 에 `@XmlValue` 로 텍스트 `36000` 이 들어간다.
- `BookPrice.toString()` 이 `value + " " + currency` 라서 `price=36000 KRW` 꼴이 된다.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (4)」.

### 2. `category` 는 속성, 나머지는 들여쓴 자식 요소, 가격은 속성 + 텍스트

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
<bookstore>
    <book category="java">
        <title>모던 자바 인 액션</title>
        <author>라울 외</author>
        <price currency="KRW">38000</price>
        <year>2019</year>
    </book>
</bookstore>
```

앞에 XML 선언 줄이 붙는다.

**왜 그런가**
- 루트 태그 이름은 `@XmlRootElement(name = "bookstore")` 에서, `<book>` 이라는 이름은 리스트 필드의 `@XmlElement(name = "book")` 에서 온다.
- `@XmlAttribute` 인 `category` · `currency` 는 여는 태그 안에, `@XmlValue` 인 `value` 는 `<price>` 태그 사이에 쓰인다.
- `JAXB_FORMATTED_OUTPUT` 이 `true` 라서 줄바꿈과 들여쓰기가 들어간다.
- 자식 요소의 차례(`title` → `author` → `price` → `year`)와 들여쓰기 폭은 구현의 기본 동작에 기댄 예상이다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「동작 방식 (6)」 · 「구현 세부사항 대 언어 보장」.

### 3. 3권이 찍히고 `<book>` 요소도 3개다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
도서 추가 후: 3권
```

`writer` 의 XML 에는 `<book>` 요소가 3개 — 이펙티브 자바, Real MySQL, 토비의 스프링 차례로 — 들어간다.

**왜 그런가**
- 언마샬링으로 `<book>` 2개가 `JaxbBook` 2개가 되어 `books` 리스트에 들어간다.
- 언마샬링 결과는 평범한 자바 객체라서 `addBook` 으로 리스트에 하나를 더할 수 있다.
- 마샬링은 리스트의 원소 수만큼 `<book>` 요소를 쓰므로 3개가 된다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (5)」.

### 4. JAXB 는 리플렉션으로 빈 객체를 먼저 만들기 때문이다

JAXB 는 XML 을 읽을 때 생성자 인자에 무엇을 넣을지 모른다.
그래서 리플렉션으로 인자 없는 생성자를 불러 빈 객체를 만든 뒤, XML 에 나온 값을 필드에 하나씩 채운다.
인자 있는 생성자만 두면 Java 는 기본 생성자를 만들어 주지 않으므로 JAXB 가 객체를 만들 수 없다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 5. 기본값 `PUBLIC_MEMBER` 는 public getter/setter 도 매핑해 같은 값이 두 번 잡힐 수 있다

기본 접근 방식 `PUBLIC_MEMBER` 는 public getter/setter 쌍도 매핑 대상으로 본다.
필드에 `@XmlElement` 를 붙이고 같은 값의 public getter 도 두면 같은 값이 두 경로로 매핑되는 문제가 생길 수 있다.
`FIELD` 로 두면 필드만 보므로 겹침이 없고, `JaxbBook` 처럼 setter 가 없거나 getter 가 없어도 매핑된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 6. 둘 수 없다 — `@XmlValue` 는 한 클래스에 1개만이다

태그 사이 텍스트는 한 요소에 한 덩어리뿐이라 `@XmlValue` 는 한 클래스에 1개만 가능하다.
그래서 `<price currency="KRW">36000</price>` 는 속성 쪽 `@XmlAttribute currency` 하나와 텍스트 쪽 `@XmlValue value` 하나로 나눠 받는다.
속성은 따로 여러 개 둘 수 있지만 텍스트 자리는 하나다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 7. 의존성이 없으면 패키지를 못 찾고, 구현이 없으면 실제 변환을 할 주체가 없다

JAXB 는 Java 11 부터 JDK 에서 제거되었으므로 의존성 없이는 `jakarta.xml.bind` 패키지를 찾지 못한다.
API(`jakarta.xml.bind-api`)만 넣으면 인터페이스는 있어 코드는 맞춰지지만, 실제로 변환하는 런타임 구현(`jaxb-runtime`)이 없어 실행 단계에서 막힌다.
원본 주석이 API 를 `implementation`, 구현을 `runtimeOnly` 로 둔 것이 이 구분이다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 1」.

### 8. 컨텍스트는 비싼 공장이고, 일꾼은 거기서 꺼내 쓰는 것이다

`JAXBContext` 는 `Bookstore` 에서 `JaxbBook` · `BookPrice` 까지 따라간 매핑 정보를 보관하며, 생성 비용이 크다.
그래서 한 번 만들고, 읽을 때는 `createUnmarshaller()`, 쓸 때는 `createMarshaller()` 로 일꾼을 꺼낸다.
두 일꾼은 같은 매핑 정보를 쓰므로 읽고 고친 객체를 같은 모양의 XML 로 되돌릴 수 있다.
`Marshaller` 는 들여쓰기 · 인코딩 설정을 지닌 채 같은 루트 타입의 다른 객체(`newStore`)도 마샬링할 수 있어 다시 쓴다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 9. 둘 다 같은 어노테이션 클래스이고, `xjc` 는 스키마에서 그것을 자동으로 만든다

예제는 XML 구조를 보고 어노테이션을 손으로 붙인 클래스다.
`xjc` 는 XML 스키마를 읽어 같은 종류의 JAXB 어노테이션 클래스를 생성해 준다.
요소가 몇 개 안 되면 손으로 써도 되지만, 스키마가 크고 복잡하면 이름 · 중첩을 틀리기 쉬우므로 `xjc` 로 생성하는 쪽이 낫다.
근거: 2-summary 「어디서 틀리나 6」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 서점 XML 을 읽고 고쳐 다시 XML 로 쓰기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 루트 요소 `bookstore` | `Bookstore` 위의 `@XmlRootElement(name = "bookstore")` |
| 2. 필드 직접 매핑 | 세 클래스의 `@XmlAccessorType(XmlAccessType.FIELD)` |
| 3. 원소마다 `<book>` | `books` 필드의 `@XmlElement(name = "book")` |
| 4. `category` 속성, 나머지 자식 요소 | `JaxbBook` 의 `@XmlAttribute category`, `@XmlElement title` · `author` · `price` · `year` |
| 5. `currency` 속성, `value` 텍스트 | `BookPrice` 의 `@XmlAttribute currency`, `@XmlValue value` |
| 6. 기본 생성자 | `public Bookstore() {}` · `public JaxbBook() {}` · `public BookPrice() {}` |
| 7. 컨텍스트 한 번 | `JAXBContext.newInstance(Bookstore.class)` |
| 8. `XML_DATA` 읽기 | `context.createUnmarshaller()` · `unmarshaller.unmarshal(new StringReader(XML_DATA))` |
| 9. 도서 수 · 각 책 찍기 | `bookstore.getBooks().size()` · `for (JaxbBook book : …)` 의 `"  " + book` |
| 10. 한 권 추가 · 권수 | `bookstore.addBook(new JaxbBook("spring", …))` · `"도서 추가 후: " + … + "권"` |
| 11. 들여쓰기 · UTF-8 마샬링 | `context.createMarshaller()` · `JAXB_FORMATTED_OUTPUT` · `JAXB_ENCODING` · `marshal(bookstore, writer)` |
| 12. 새 서점에 두 권 | `new Bookstore()` · `newStore.addBook(...)` 두 번 |
| 13. 같은 `Marshaller` 재사용 | `marshaller.marshal(newStore, newWriter)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-data-processing/reference/xml-jaxb.java`

```java
// [데이터 처리 & 유틸] XML JAXB Binding (JAXB 바인딩)
// 설명: Java 객체와 XML 간 자동 변환. @XmlRootElement 어노테이션, 마샬링/언마샬링
// 팁: JAXB는 Java 11부터 JDK에서 제거되었으므로 별도 의존성(jakarta.xml.bind-api + jaxb-runtime)이 필요하다. 기본 생성자가 반드시 있어야 하며, @XmlAccessorType(FIELD)을 사용하면 getter 없이도 필드를 매핑할 수 있다. 복잡한 XML 스키마는 xjc 도구로 Java 클래스를 자동 생성할 수 있다.

// === JAXB: XML <-> Java 객체 자동 변환 ===
// 참고: Java 11+에서는 jakarta.xml.bind 의존성 필요
// implementation 'jakarta.xml.bind:jakarta.xml.bind-api:4.0.0'
// runtimeOnly 'org.glassfish.jaxb:jaxb-runtime:4.0.3'

// JAXBContext, Marshaller, Unmarshaller: JAXB 핵심 API
import jakarta.xml.bind.*;
// 어노테이션: @XmlRootElement, @XmlElement, @XmlAttribute, @XmlValue 등
import jakarta.xml.bind.annotation.*;
// 문자열 ↔ Reader/Writer 어댑터
import java.io.StringReader;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.List;

// === JAXB 어노테이션으로 매핑 정의 ===

// @XmlRootElement: 이 클래스가 XML의 루트 요소가 됨 (name 속성으로 태그명 지정)
@XmlRootElement(name = "bookstore")
// @XmlAccessorType(FIELD): getter/setter 대신 필드를 직접 매핑 (간결)
// 함정: 기본값은 PUBLIC_MEMBER이므로 같은 필드+getter가 두 번 매핑되는 문제가 있을 수 있음
@XmlAccessorType(XmlAccessType.FIELD)
class Bookstore {
    // @XmlElement(name="book"): List의 각 요소가 <book> 태그로 직렬화
    @XmlElement(name = "book")
    private List<JaxbBook> books = new ArrayList<>();

    public Bookstore() {} // JAXB는 기본 생성자 필요 (리플렉션으로 인스턴스 생성)

    public List<JaxbBook> getBooks() { return books; }
    public void setBooks(List<JaxbBook> books) { this.books = books; }
    public void addBook(JaxbBook book) { this.books.add(book); }
}

@XmlAccessorType(XmlAccessType.FIELD)
class JaxbBook {
    // @XmlAttribute: 필드를 XML 속성(태그 안의 key="value")으로 매핑
    @XmlAttribute // XML 속성으로 매핑
    private String category;

    // @XmlElement: 필드를 자식 요소(<title>...</title>)로 매핑
    @XmlElement
    private String title;

    @XmlElement
    private String author;

    // 객체 타입: 중첩 요소 <price>...</price>로 직렬화
    @XmlElement
    private BookPrice price;

    @XmlElement
    private int year;

    public JaxbBook() {}

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

// 가격: 속성(currency) + 텍스트 값(가격)을 함께 갖는 케이스
// XML: <price currency="KRW">36000</price>
@XmlAccessorType(XmlAccessType.FIELD)
class BookPrice {
    @XmlAttribute
    private String currency;

    // @XmlValue: 태그 사이의 텍스트 값. 한 클래스에 1개만 가능
    @XmlValue // 태그의 텍스트 내용
    private int value;

    public BookPrice() {}

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
        // JAXBContext: 매핑 정보를 보관. 생성 비용이 크므로 한 번 만들고 재사용 권장
        JAXBContext context = JAXBContext.newInstance(Bookstore.class);

        // === 1. 언마샬링 (XML -> Java 객체) ===
        // unmarshal: XML 입력을 객체로 변환
        System.out.println("=== 언마샬링 (XML -> 객체) ===");
        Unmarshaller unmarshaller = context.createUnmarshaller();
        Bookstore bookstore = (Bookstore) unmarshaller.unmarshal(new StringReader(XML_DATA));

        System.out.println("도서 수: " + bookstore.getBooks().size());
        for (JaxbBook book : bookstore.getBooks()) {
            System.out.println("  " + book);
        }

        // === 2. 객체 수정 ===
        // 일반 자바 객체로 다루므로 자유롭게 수정 가능
        System.out.println("\n=== 객체 수정 ===");
        bookstore.addBook(new JaxbBook(
            "spring", "토비의 스프링", "이일민", 45000, "KRW", 2022
        ));
        System.out.println("도서 추가 후: " + bookstore.getBooks().size() + "권");

        // === 3. 마샬링 (Java 객체 -> XML) ===
        System.out.println("\n=== 마샬링 (객체 -> XML) ===");
        Marshaller marshaller = context.createMarshaller();
        // JAXB_FORMATTED_OUTPUT: 들여쓰기 적용
        marshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true);  // 들여쓰기
        // 인코딩 명시 (한글 안전)
        marshaller.setProperty(Marshaller.JAXB_ENCODING, "UTF-8");

        // marshal(객체, Writer): 객체를 XML 문자열로 직렬화
        StringWriter writer = new StringWriter();
        marshaller.marshal(bookstore, writer);
        System.out.println(writer.toString());

        // === 4. 새 객체에서 XML 생성 ===
        // 실제로는 객체로 데이터를 만들고 XML로 직렬화하는 게 더 자연스러움
        System.out.println("=== 새 객체 -> XML ===");
        Bookstore newStore = new Bookstore();
        newStore.addBook(new JaxbBook("java", "모던 자바 인 액션", "라울 외", 38000, "KRW", 2019));
        newStore.addBook(new JaxbBook("kotlin", "코틀린 인 액션", "드미트리", 35000, "KRW", 2017));

        StringWriter newWriter = new StringWriter();
        marshaller.marshal(newStore, newWriter);
        System.out.println(newWriter.toString());

        // 출력:
        // === 언마샬링 (XML -> 객체) ===
        // 도서 수: 2
        //   Book{category='programming', title='이펙티브 자바', author='조슈아 블로크', price=36000 KRW, year=2018}
        //   Book{category='database', title='Real MySQL', author='이성욱', price=42000 KRW, year=2021}
        //
        // === 객체 수정 ===
        // 도서 추가 후: 3권
        //
        // === 마샬링 (객체 -> XML) ===
        // <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        // <bookstore>
        //     <book category="programming">
        //         <title>이펙티브 자바</title>
        //         ...
        //     </book>
        //     ...
        // </bookstore>
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- XML 의 세 자리(요소 · 속성 · 텍스트)에 `@XmlElement` · `@XmlAttribute` · `@XmlValue` 를 하나씩 맞추는 것이 매핑의 전부다.
- 리스트 필드 하나에 `@XmlElement(name = "book")` 을 붙여 되풀이되는 `<book>` 을 받는다.
- 세 클래스 모두 기본 생성자 + `FIELD` 접근이라 getter/setter 유무와 상관없이 매핑된다.
- `JAXBContext` 는 한 번만 만들고, 읽기 · 쓰기 일꾼을 거기서 꺼내며 `Marshaller` 는 재사용한다.
- `unmarshal` 은 `Object` 를 돌려주므로 `(Bookstore)` 로 형변환한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
