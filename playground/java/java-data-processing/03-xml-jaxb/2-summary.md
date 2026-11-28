# java/java-data-processing/03 — XML JAXB Binding (JAXB 바인딩) — 정리 (힌트)

> 출처 — study-site 항목 `java/xml-jaxb`(항목 데이터 `data/java/data-processing.json`) · 정답 코드 study-practice `java/java-data-processing/reference/xml-jaxb.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**JAXB 는 「양식에 맞춰 서류를 옮겨 적는 사무원」이다.**
사무원은 「이 칸은 제목, 이 칸은 저자」라는 대응표를 받는다.
종이 서류(XML)가 들어오면 대응표대로 장부(Java 객체)에 옮겨 적는다.
장부를 고친 뒤 다시 종이 서류로 뽑을 때도 같은 대응표를 쓴다.
JAXB 도 똑같은 구조다.
대응표는 클래스와 필드에 붙인 어노테이션이다.
XML → 객체 방향을 **언마샬링**, 객체 → XML 방향을 **마샬링**이라 부른다.

> **JAXB** — Java 객체와 XML 사이를 어노테이션 기반으로 자동 변환하는 Java 의 XML 바인딩 API.\
> 예: `@XmlRootElement` 를 붙인 `Bookstore` 를 `<bookstore>…</bookstore>` 로 바꾼다.

> **바인딩** — 한쪽 구조의 각 부분을 다른 쪽 구조의 각 부분과 짝지어 묶는 것.\
> 예: `<title>` 요소 ↔ `title` 필드.

| 비유 | 실체 |
|---|---|
| 종이 서류 | XML 문서 |
| 장부 | Java 객체(`Bookstore`, `JaxbBook`) |
| 대응표 | `@XmlRootElement` · `@XmlElement` · `@XmlAttribute` · `@XmlValue` |
| 사무원을 고용한 사무소 | `JAXBContext` |
| 서류 → 장부로 옮기는 사무원 | `Unmarshaller` |
| 장부 → 서류로 옮기는 사무원 | `Marshaller` |

```text
          언마샬링 (Unmarshaller.unmarshal)
  XML 문서  ─────────────────────────────▶  Java 객체
  <bookstore>                               Bookstore
    <book category="..">                      books: [JaxbBook, ...]
  ◀─────────────────────────────────────
          마샬링 (Marshaller.marshal)
```

## 이 주제가 답하려는 질문

1. XML 요소 · 속성 · 텍스트를 Java 필드에 어떻게 짝지어 알려 주나?
2. XML 문자열을 객체로, 객체를 XML 문자열로 바꾸는 코드는 어떤 차례로 쓰나?
3. 매핑 클래스는 어떤 조건을 지켜야 하고, 어디서 자주 깨지나?
4. 최신 Java 에서 JAXB 를 쓰려면 무엇을 따로 챙겨야 하나?

## 동작 방식

### (1) 어노테이션 — XML 의 세 가지 자리에 필드를 짝짓기

**언제 쓰나** — XML 구조를 클래스로 옮겨 적을 때, 필드 하나하나가 XML 의 어느 자리에 해당하는지 알려 준다.

XML 에서 값이 놓이는 자리는 세 가지다.
요소(`<title>…</title>`), 속성(`category="programming"`), 태그 사이 텍스트(`<price …>36000</price>` 의 `36000`)다.

```text
<book category="programming">          ← @XmlAttribute  category
    <title>이펙티브 자바</title>          ← @XmlElement    title
    <price currency="KRW">36000</price>  ← @XmlElement    price (BookPrice 객체)
</book>                                        └ BookPrice 안:
                                                 @XmlAttribute currency = "KRW"
                                                 @XmlValue     value    = 36000
```

- `@XmlRootElement(name = "bookstore")` 는 그 클래스를 문서의 맨 바깥 요소로 정하고 태그 이름을 `bookstore` 로 준다.
- `@XmlElement` 는 필드를 자식 요소로 짝짓는다.
- `@XmlAttribute` 는 필드를 태그 안의 `key="value"` 속성으로 짝짓는다.
- `@XmlValue` 는 필드를 태그 사이의 텍스트로 짝짓는다.
- 필드 타입이 객체(`BookPrice`)면 그 객체가 다시 중첩 요소가 되고, 그 클래스의 어노테이션대로 안쪽이 채워진다.

> **요소(element)** — 여는 태그와 닫는 태그로 둘러싼 XML 의 한 덩어리.\
> 예: `<year>2018</year>`.

> **속성(attribute)** — 여는 태그 안에 적는 이름=값 쌍.\
> 예: `<price currency="KRW">` 의 `currency="KRW"`.

> **어노테이션** — 클래스 · 필드 · 메서드에 붙여 도구가 읽을 정보를 남기는 `@이름` 꼴의 표시.\
> 예: `@XmlAttribute`.

### (2) 리스트 — 같은 이름의 요소가 되풀이될 때

**언제 쓰나** — `<book>` 처럼 같은 요소가 여러 번 나오는 구조를 받을 때 쓴다.

```text
@XmlElement(name = "book")             <bookstore>
private List<JaxbBook> books;   ◀──▶      <book …>…</book>    ← books[0]
                                          <book …>…</book>    ← books[1]
                                       </bookstore>
```

- `List` 필드에 `@XmlElement(name = "book")` 을 붙이면 리스트의 원소 하나가 `<book>` 요소 하나가 된다.
- 언마샬링 때는 `<book>` 요소가 나올 때마다 `JaxbBook` 하나가 만들어져 리스트에 들어간다.
- 마샬링 때는 리스트의 원소 수만큼 `<book>` 요소가 쓰인다.
- 필드 이름이 `books` 여도 태그 이름은 `name` 으로 준 `book` 이 된다.

### (3) 접근 방식 — `@XmlAccessorType(XmlAccessType.FIELD)`

**언제 쓰나** — getter · setter 없이 필드만으로 매핑하고 싶을 때 클래스에 붙인다.

```text
기본값 PUBLIC_MEMBER                       FIELD
 ├ public getter/setter 쌍  → 매핑          ├ 필드 → 매핑
 └ (어노테이션 붙인) 필드     → 매핑          └ getter 는 보지 않음
 ⇒ 같은 값이 두 경로로 잡힐 수 있다           ⇒ 필드 하나 = 자리 하나
```

- JAXB 가 무엇을 매핑 대상으로 볼지는 접근 방식이 정한다.
- 기본값은 `PUBLIC_MEMBER` 라서 public getter/setter 도 매핑 대상으로 본다.
- 그래서 필드에 어노테이션을 붙이고 같은 이름의 public getter 도 두면, 같은 값이 두 번 매핑되는 문제가 생길 수 있다.
- `FIELD` 를 쓰면 필드를 직접 읽고 쓰므로 getter 가 없어도 된다(`JaxbBook` 은 setter 가 없다).

> **접근 방식(access type)** — JAXB 가 필드를 볼지 getter/setter 를 볼지 정하는 설정.\
> 예: `@XmlAccessorType(XmlAccessType.FIELD)`.

### (4) 언마샬링 — XML 문자열에서 객체로

**언제 쓰나** — 파일 · 문자열 · 네트워크로 받은 XML 을 자바 코드에서 다루고 싶을 때 쓴다.

```text
JAXBContext.newInstance(Bookstore.class)
        │  매핑 정보 준비 (Bookstore → JaxbBook → BookPrice 까지 따라감)
        ▼
context.createUnmarshaller()
        │
        ▼
unmarshaller.unmarshal(new StringReader(XML_DATA))
        │  기본 생성자로 빈 객체 생성 → 대응표대로 필드 채움
        ▼
(Bookstore) 로 형변환 → books 에 JaxbBook 2개
```

- `JAXBContext` 는 매핑 정보를 보관한다.
- 루트 클래스 하나만 넘겨도 필드 타입을 따라 `JaxbBook` · `BookPrice` 까지 매핑 정보가 만들어진다.
- `unmarshal` 은 `Object` 를 돌려주므로 루트 타입으로 형변환한다.
- JAXB 는 리플렉션으로 인스턴스를 만들기 때문에 매핑 클래스마다 기본 생성자가 있어야 한다.
- 빈 객체를 먼저 만든 뒤 XML 에 나온 값을 필드에 채우는 차례다.
- 그래서 XML 에 없는 요소에 해당하는 필드는 기본 생성자가 남긴 값 그대로 남는다고 보는 것이 자연스럽다(원본에 근거 없음 — 추론).
- 문자열을 넘길 때는 `StringReader` 로 감싸 `Reader` 로 만든다.
- 텍스트 `"36000"` 은 `int` 필드에 들어가며 숫자로 바뀐다.

> **언마샬링** — XML 같은 외부 표현을 읽어 메모리의 객체로 되살리는 것.\
> 예: `unmarshaller.unmarshal(reader)`.

> **리플렉션** — 실행 중에 클래스 · 생성자 · 필드를 이름으로 찾아 다루는 Java 기능.\
> 예: 기본 생성자를 찾아 `new` 없이 객체를 만든다.

### (5) 언마샬링한 객체는 그냥 자바 객체다

**언제 쓰나** — 읽은 데이터를 고치거나 더한 뒤 다시 XML 로 내보낼 때다.

```text
bookstore.books = [이펙티브 자바, Real MySQL]
        │  bookstore.addBook(new JaxbBook("spring", ...))
        ▼
bookstore.books = [이펙티브 자바, Real MySQL, 토비의 스프링]
```

- 언마샬링의 결과는 평범한 객체라서 메서드로 자유롭게 고칠 수 있다.
- XML 과 묶여 있는 특별한 객체가 아니므로, 고친 내용은 다시 마샬링해야 XML 에 나타난다.

### (6) 마샬링 — 객체에서 XML 문자열로

**언제 쓰나** — 객체로 만든 데이터를 XML 로 저장하거나 보낼 때 쓴다.

```text
context.createMarshaller()
        │  setProperty(JAXB_FORMATTED_OUTPUT, true)   → 들여쓰기
        │  setProperty(JAXB_ENCODING, "UTF-8")        → 인코딩
        ▼
marshaller.marshal(bookstore, new StringWriter())
        │  @XmlRootElement 이름으로 바깥 태그 → 필드마다 요소·속성·텍스트
        ▼
writer.toString()  →  "<?xml …?>\n<bookstore>\n    <book category=…>…"
```

- `Marshaller` 도 같은 `JAXBContext` 에서 만든다.
- `JAXB_FORMATTED_OUTPUT` 을 `true` 로 두면 줄바꿈과 들여쓰기가 들어간다.
- `JAXB_ENCODING` 으로 인코딩을 `"UTF-8"` 로 밝혀 한글을 안전하게 다룬다.
- `marshal(객체, Writer)` 가 객체를 XML 로 써 넣고, `StringWriter` 의 `toString()` 으로 문자열을 얻는다.
- 같은 `Marshaller` 로 다른 루트 객체(`newStore`)를 또 마샬링할 수 있다.
- 처음부터 객체로 데이터를 만들고 XML 로 내보내는 쪽이 오히려 더 자연스러운 쓰임이다.

> **마샬링** — 메모리의 객체를 XML 같은 외부 표현으로 써 내는 것.\
> 예: `marshaller.marshal(bookstore, writer)`.

## 문법 — 형태와 규칙

```java
@XmlRootElement(name = "note")
@XmlAccessorType(XmlAccessType.FIELD)
class Note {
    @XmlAttribute private String lang;      // <note lang="ko">
    @XmlElement   private String body;      //   <body>안녕</body>
    public Note() {}                        // 기본 생성자
}

JAXBContext ctx = JAXBContext.newInstance(Note.class);
Note n = (Note) ctx.createUnmarshaller()
                   .unmarshal(new StringReader("<note lang=\"ko\"><body>안녕</body></note>"));
StringWriter w = new StringWriter();
ctx.createMarshaller().marshal(n, w);
```

| 어노테이션 · API | 자리 | 하는 일 |
|---|---|---|
| `@XmlRootElement(name = "…")` | 클래스 | 문서의 루트 요소로 정하고 태그 이름을 준다 |
| `@XmlAccessorType(XmlAccessType.FIELD)` | 클래스 | 필드를 직접 매핑한다 (기본값은 `PUBLIC_MEMBER`) |
| `@XmlElement` / `@XmlElement(name = "…")` | 필드 | 자식 요소로 매핑, `name` 으로 태그 이름 지정 |
| `@XmlAttribute` | 필드 | 태그 안의 속성으로 매핑 |
| `@XmlValue` | 필드 | 태그 사이 텍스트로 매핑, 한 클래스에 1개만 |
| `JAXBContext.newInstance(루트.class)` | 코드 | 매핑 정보 준비, 한 번 만들어 재사용 권장 |
| `createUnmarshaller().unmarshal(Reader)` | 코드 | XML → 객체, `Object` 반환이라 형변환 |
| `createMarshaller().marshal(객체, Writer)` | 코드 | 객체 → XML |
| `Marshaller.JAXB_FORMATTED_OUTPUT` | 속성 | `true` 면 들여쓰기 |
| `Marshaller.JAXB_ENCODING` | 속성 | 출력 인코딩 지정 |

- 매핑 클래스마다 인자 없는 기본 생성자를 둔다.
- 루트 클래스에만 `@XmlRootElement` 를 붙인다(예제에서 `JaxbBook` · `BookPrice` 에는 없다).
- 패키지는 `jakarta.xml.bind.*`(API)와 `jakarta.xml.bind.annotation.*`(어노테이션) 두 곳에서 가져온다.
- Java 11 이후에는 의존성 두 개가 따로 필요하다 — API(`jakarta.xml.bind:jakarta.xml.bind-api`)와 구현(`org.glassfish.jaxb:jaxb-runtime`).
- 원본 주석은 Gradle 로 `implementation '…bind-api:4.0.0'` 과 `runtimeOnly '…jaxb-runtime:4.0.3'` 를 예로 든다.

> **의존성** — 프로젝트가 빌드 · 실행에 필요로 하는 바깥 라이브러리.\
> 예: `jaxb-runtime`.

## 어디서 틀리나

### 1. Java 11 이후 JDK 에 JAXB 가 없다

JAXB 는 Java 11 부터 JDK 에서 제거되었다.
그래서 의존성 없이 import 하면 패키지를 찾지 못한다.
API(`jakarta.xml.bind-api`)만 넣고 구현(`jaxb-runtime`)을 빼도 안 된다.
API 는 인터페이스뿐이고, 실제로 변환하는 일은 런타임 구현이 한다.
원본 주석이 구현을 `runtimeOnly` 로 둔 까닭도 여기 있다 — 컴파일에는 API 만, 실행에는 구현이 있어야 한다.

### 2. 기본 생성자를 빠뜨린다

JAXB 는 리플렉션으로 빈 객체를 먼저 만든다.
인자 있는 생성자(`JaxbBook(String, String, …)`)만 두면 기본 생성자가 사라지므로 JAXB 가 객체를 만들 수 없다.
예제의 세 클래스가 모두 `public X() {}` 를 따로 둔 까닭이다.

### 3. 접근 방식을 정하지 않아 같은 값이 두 번 잡힌다

기본 접근 방식 `PUBLIC_MEMBER` 는 public getter/setter 도 매핑 대상으로 본다.
필드에 `@XmlElement` 를 붙이고 public getter 도 두면 같은 값이 두 번 매핑되는 문제가 생길 수 있다.
`@XmlAccessorType(XmlAccessType.FIELD)` 를 쓰면 필드만 보므로 getter 가 없어도 되고 겹침도 없다.

### 4. `@XmlValue` 를 둘 붙인다

태그 사이 텍스트는 한 덩어리뿐이라 `@XmlValue` 는 한 클래스에 1개만 가능하다.
속성과 텍스트를 함께 가진 요소(`<price currency="KRW">36000</price>`)는 `@XmlAttribute` 필드 + `@XmlValue` 필드 하나로 짝짓는다.

### 5. `JAXBContext` 를 매번 새로 만든다

`JAXBContext` 는 생성 비용이 크다.
변환할 때마다 `newInstance` 를 부르지 말고 한 번 만들어 재사용한다.
`Marshaller` · `Unmarshaller` 는 이 컨텍스트에서 필요할 때 꺼내 쓴다.

### 6. 스키마가 복잡한데 손으로 클래스를 다 쓴다

복잡한 XML 스키마는 `xjc` 도구로 Java 클래스를 자동 생성할 수 있다.
요소가 수십 개인 스키마를 손으로 옮기면 이름 · 중첩을 틀리기 쉽다.

> **XML 스키마** — XML 문서에 어떤 요소 · 속성이 어떤 차례 · 타입으로 올 수 있는지 정한 규칙 문서.\
> 예: `book` 안에 `title` · `author` 가 온다는 정의.

> **xjc** — XML 스키마를 읽어 JAXB 어노테이션이 붙은 Java 클래스를 만들어 주는 도구.\
> 예: 스키마 하나에서 `Bookstore` · `JaxbBook` 같은 클래스를 생성한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| JAXB 는 Java 11 부터 JDK 에 없다 | JDK 배포 구성 (원본 팁) |
| 실제 변환은 `jaxb-runtime` 이 한다 | 선택한 구현 라이브러리 — API 는 인터페이스만 정한다 |
| 의존성 버전 `4.0.0` · `4.0.3` | 원본 주석의 예일 뿐, 빌드 설정이 정한다 |
| `JAXBContext` 생성 비용이 크다 | 구현의 성능 특성 (원본 주석, 수치는 없다) |
| 매핑 클래스에 기본 생성자가 필요하다 | JAXB 명세의 기본 규칙 (원본 팁) — 예외 경로가 있는지는 (확인 필요) |
| 마샬링한 자식 요소가 필드 선언 순서로 나온다 | 명시하지 않으면 구현에 기댄다 — 순서를 고정하는 방법은 (확인 필요) (원본에 근거 없음 — 추론) |
| 머리말이 `standalone="yes"` 를 단다 · 들여쓰기 폭 | 구현의 기본 동작 (원본 주석의 예) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 구조가 정해진 XML 을 객체로 다루고 싶다 | JAXB 어노테이션 + `Unmarshaller` | 문자열 잘라 붙이기 |
| 객체로 만든 데이터를 XML 로 내보낸다 | `Marshaller` + `JAXB_FORMATTED_OUTPUT` | 손으로 태그 문자열 이어 붙이기 |
| 스키마가 크고 복잡하다 | `xjc` 로 클래스 생성 | 수십 개 클래스를 손으로 작성 |
| 변환을 여러 번 한다 | `JAXBContext` 하나를 재사용 | 변환마다 `newInstance` |
| getter 없이 필드만 둔 클래스 | `@XmlAccessorType(FIELD)` | 기본 `PUBLIC_MEMBER` 에 기대기 |
| Java 11 이후 프로젝트 | `jakarta.xml.bind-api` + `jaxb-runtime` 의존성 | JDK 에 들어 있다고 가정 |

## 핵심 문장

1. **JAXB 는 어노테이션을 대응표 삼아 XML 과 객체를 오간다** — 객체로 가면 언마샬링, XML 로 가면 마샬링이다.
2. **XML 의 세 자리에 어노테이션 셋이 맞는다** — 요소는 `@XmlElement`, 속성은 `@XmlAttribute`, 텍스트는 `@XmlValue`(클래스당 1개).
3. **`JAXBContext` 가 공장이고 `Marshaller` · `Unmarshaller` 가 일꾼이다** — 컨텍스트는 비싸니 한 번 만들어 재사용한다.
4. **매핑 클래스는 기본 생성자를 갖고, `FIELD` 접근이면 getter 가 없어도 된다.**
5. **Java 11 이후에는 API 와 구현 의존성을 따로 넣어야 한다.**

## 관련 자료

- `xml-dom` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [xml-sax](../02-xml-sax/2-summary.md)
- `yaml-snakeyaml` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/data-processing.json` 의 `xml-jaxb`

## 용어 풀이

- **JAXB** — Java 객체와 XML 을 어노테이션으로 자동 변환하는 API.
- **바인딩** — 두 구조의 부분끼리 짝지어 묶는 것.
- **마샬링** — 객체를 XML 같은 외부 표현으로 써 내는 것.
- **언마샬링** — 외부 표현을 읽어 객체로 되살리는 것.
- **요소** — 여는 태그와 닫는 태그로 둘러싼 XML 의 한 덩어리.
- **속성** — 여는 태그 안의 이름=값 쌍.
- **어노테이션** — 도구가 읽을 정보를 남기는 `@이름` 꼴 표시.
- **접근 방식** — JAXB 가 필드를 볼지 getter/setter 를 볼지 정하는 설정.
- **`JAXBContext`** — 매핑 정보를 보관하고 `Marshaller` · `Unmarshaller` 를 만드는 객체.
- **리플렉션** — 실행 중에 클래스의 생성자 · 필드를 이름으로 다루는 기능.
- **기본 생성자** — 인자가 없는 생성자.
- **의존성** — 빌드 · 실행에 필요한 바깥 라이브러리.
- **XML 스키마** — XML 문서의 허용 구조를 정한 규칙 문서.
- **xjc** — 스키마에서 JAXB 클래스를 생성하는 도구.

## 더 들어가면

- 예전 패키지 이름은 `javax.xml.bind` 였고, Jakarta EE 로 옮겨 가며 `jakarta.xml.bind` 로 바뀌었다 — 두 이름을 한 프로젝트에 섞으면 어노테이션이 인식되지 않을 수 있다 (확인 필요).
- 자식 요소의 순서를 고정하려면 클래스에 `@XmlType(propOrder = {...})` 를 붙이는 방법이 있다 (확인 필요).
- `@XmlElementWrapper` 로 리스트를 `<books><book/>…</books>` 처럼 감싸는 바깥 요소를 둘 수 있다 (확인 필요).
- `@XmlTransient` 를 붙인 필드는 매핑에서 빠진다 (확인 필요).
- 예제의 텍스트 블록은 닫는 `"""` 가 내용과 같은 들여쓰기라 앞 공백이 걷혀 `<?xml` 이 문자열 맨 앞에 온다 — XML 선언 앞에 공백이 있으면 파서가 거부할 수 있다 (확인 필요).
- `Marshaller.JAXB_FRAGMENT` 를 `true` 로 두면 XML 선언 줄을 빼고 쓸 수 있다 (확인 필요).
