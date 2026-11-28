# java/java-data-processing/05 — CSV OpenCSV (CSV 처리) — 정리 (힌트)

> 출처 — study-site 항목 `java/csv-opencsv`(항목 데이터 `data/java/data-processing.json`) · 정답 코드 study-practice `java/java-data-processing/reference/csv-opencsv.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**OpenCSV 는 「엑셀 표를 한 줄씩 읽어 주는 낭독자」와 「표를 대신 받아 적는 서기」를 함께 둔 도구다.**
낭독자는 표의 한 줄을 칸별로 끊어 읽어 준다.
더 똑똑한 낭독자는 머리줄의 칸 이름을 보고 각 칸의 값을 서류 양식의 알맞은 칸에 옮겨 적어 준다.
서기는 거꾸로 서류 양식을 받아 표의 한 줄로 받아 적는다.
OpenCSV 도 똑같은 구조다.
`CSVReader` 가 낭독자이고, `CsvToBean` 이 양식에 옮겨 주는 낭독자이며, `CSVWriter` · `StatefulBeanToCsv` 가 서기다.

| 비유 | 실체 |
|---|---|
| 표의 한 줄 | CSV 의 한 행(쉼표로 나뉜 한 줄) |
| 칸별로 끊어 읽은 값 | `String[]` 배열 |
| 머리줄의 칸 이름 | CSV 헤더(첫 줄) |
| 서류 양식 | Bean 클래스(`Employee`) |
| 양식의 칸에 붙은 이름표 | `@CsvBindByName(column = "이름")` |
| 받아 적는 서기 | `CSVWriter` · `StatefulBeanToCsv` |

```text
  CSV 텍스트                     Java 쪽
 ┌──────────────────┐  읽기   ┌──────────────────────────┐
 │ 이름,부서,...     │ ──────▶ │ String[]  (CSVReader)    │
 │ 홍길동,개발팀,... │         │ Employee  (CsvToBean)    │
 └──────────────────┘ ◀────── └──────────────────────────┘
                        쓰기    CSVWriter / StatefulBeanToCsv
```

> **CSV** — 값을 쉼표로 나누고 행을 줄바꿈으로 나눈 텍스트 표 형식이다.\
> 예: `홍길동,개발팀,시니어,7500,2018` 이 한 행이다.

> **OpenCSV** — Java 에서 CSV 를 읽고 쓰는 외부 라이브러리다.\
> 예: 의존성 `implementation 'com.opencsv:opencsv:5.9'` 로 들여온다.

## 이 주제가 답하려는 질문

1. CSV 한 줄을 Java 에서 어떤 꼴로 받아 다루나?
2. 행을 배열이 아니라 객체로 바로 받으려면 무엇을 준비해야 하나?
3. 객체 목록을 CSV 텍스트로 되돌려 쓰는 방법은 몇 가지이고 무엇이 다른가?
4. 데이터가 아주 클 때 어떤 방식을 골라야 하나?

## 동작 방식

### (1) `CSVReader` — 한 줄을 `String[]` 로

**언제 쓰나** — 열 구조가 단순하거나, 파일이 커서 한 줄씩만 다루고 싶을 때 쓴다.
가장 저수준 API 다.

```text
new CSVReader(new StringReader(CSV_DATA))
        │
        ▼  readNext() 1번째   → ["이름","부서","직급","연봉","입사년도"]   ← 헤더도 그냥 한 줄
        ▼  readNext() 2번째   → ["홍길동","개발팀","시니어","7500","2018"]
        ▼  ...
        ▼  readNext() 6번째   → ["최지은","개발팀","주니어","5000","2023"]
        ▼  readNext() 7번째   → null  → while 종료
```

- `CSVReader` 는 다른 `Reader` 를 감싼다.
  예제는 문자열을 `StringReader` 로 감쌌지만, 실제로는 파일 `Reader` 를 감싼다.
- `readNext()` 를 부를 때마다 한 행이 `String[]` 로 돌아온다.
- 첫 줄이 헤더라는 것을 `CSVReader` 는 모른다.
  헤더를 건너뛰려면 루프 전에 `readNext()` 를 한 번 직접 부른다.
- 더 읽을 줄이 없으면 `null` 이 돌아오고, `while ((line = reader.readNext()) != null)` 이 끝난다.
- 값은 모두 문자열이다.
  `"7500"` 도 숫자가 아니라 문자열이며, 열은 `line[0]`, `line[3]` 처럼 인덱스로 고른다.
- `readNext()` 는 검증 실패 때 체크 예외 `CsvValidationException` 을 던질 수 있어서 이 예외를 import 한다.
- `try (...)` 로 열면 블록이 끝날 때 `close()` 가 저절로 불린다.

> **try-with-resources** — `try (자원)` 꼴로 연 자원을 블록이 끝날 때 자동으로 닫는 Java 문법이다.\
> 예: `try (CSVReader reader = ...) { ... }`.

### (2) `CsvToBean` — 한 행을 객체 하나로

**언제 쓰나** — 행을 의미 있는 객체로 다루고, 열 이름으로 값을 짝짓고 싶을 때 쓴다.

```text
헤더   : 이름 | 부서 | 직급 | 연봉 | 입사년도
          │     │      │      │       │      (@CsvBindByName column 으로 짝짓기)
Employee: name department position salary joinYear
                                     │       │
                              "7500" → 7500 (int 로 자동 변환)

CsvToBeanBuilder(reader).withType(Employee.class)
                        .withIgnoreLeadingWhiteSpace(true)
                        .build()  ──▶ csvToBean.parse() ──▶ List<Employee> (5개)
```

- 필드마다 `@CsvBindByName(column = "이름")` 을 달아 「헤더 `이름` 열 → 이 필드」로 짝짓는다.
- `column` 을 생략하면 필드 이름과 같은 헤더를 찾는다.
- 열 위치로 짝지으려면 `@CsvBindByPosition` 을 써서 열 인덱스로 매핑한다.
- `int` 필드는 문자열을 숫자로 자동 변환한다.
  변환이 실패하면 예외(원본 주석은 `CsvException`)가 난다.
- OpenCSV 가 리플렉션으로 객체를 만들기 때문에 **인자 없는 기본 생성자가 반드시 있어야 한다**.
- 원본 주석에 따르면 값은 setter 를 불러 채운다.
- `withIgnoreLeadingWhiteSpace(true)` 는 셀 앞쪽 공백을 지운다.
- `parse()` 는 **전체 데이터를 한 번에 `List` 로 메모리에 올린다**.
  큰 파일에서는 이것이 함정이다(「어디서 틀리나」 2).

> **Bean** — 기본 생성자와 getter · setter 를 갖춘, 값을 담는 단순한 Java 클래스다.\
> 예: `Employee` 가 이 문서의 Bean 이다.

> **리플렉션** — 실행 중에 클래스 · 필드 · 생성자를 이름으로 찾아 다루는 Java 기능이다.\
> 예: OpenCSV 가 `Employee.class` 를 받아 기본 생성자로 객체를 만드는 것.

### (3) 객체 목록을 스트림으로 집계하기

**언제 쓰나** — CSV 를 객체 목록으로 받은 뒤 그룹별 통계를 낼 때 쓴다.

```text
employees (5명)
   │ groupingBy(Employee::getDepartment, averagingInt(Employee::getSalary))
   ▼
Map: 개발팀 → (7500+9000+5000)/3
     기획팀 → 4500/1
     디자인팀 → 6000/1
   │ forEach((dept, avg) -> printf("  %s: %.0f만원%n", dept, avg))
   ▼
부서 한 줄씩 찍힌다 (소수점 아래 0자리로 반올림)
```

- `groupingBy` 가 부서 이름을 키로 묶고, `averagingInt` 가 묶음마다 연봉의 평균(`double`)을 낸다.
- `%.0f` 는 소수점 아래를 반올림해 0자리로 보인다.
- `groupingBy` 가 돌려주는 `Map` 의 종류 · 순서는 Java API 가 약속하지 않는다.
  그래서 부서 줄의 **차례는 보장되지 않는다**.

### (4) `CSVWriter` — `String[]` 를 한 줄로

**언제 쓰나** — 무엇을 어떤 차례로 쓸지 직접 정하고 싶을 때 쓴다.

```text
new CSVWriter(stringWriter)
   writeNext({"이름","부서","직급","연봉","입사년도"})   ← 헤더도 직접
   writeNext({"한소희","마케팅팀","시니어","7000","2019"})
   writeNext({"오세진","개발팀","주니어","4800","2024"})
   close()  (try 블록 끝)
        ▼
stringWriter 안에 CSV 3줄이 쌓인다
```

- 읽기의 거울이다: `String[]` 하나가 한 줄이 된다.
- **헤더는 저절로 들어가지 않는다** — 첫 `writeNext` 로 직접 쓴다.
- 숫자는 `String.valueOf(...)` 로 문자열로 바꿔 넣는다.
- 큰따옴표 · 쉼표가 들어간 필드는 자동으로 이스케이프된다.

> **이스케이프** — 구분자 · 따옴표처럼 특별한 뜻이 있는 글자를 값으로 쓸 수 있게 감싸거나 바꾸는 일이다.\
> 예: 값 안에 쉼표가 있으면 그 필드 전체를 따옴표로 감싼다.

### (5) `StatefulBeanToCsv` — 객체를 바로 한 줄로

**언제 쓰나** — 어노테이션이 달린 Bean 목록을 그대로 CSV 로 쓰고 싶을 때 쓴다.

```text
StatefulBeanToCsvBuilder<Employee>(beanWriter).withSeparator(',').build()
   write(List.of(윤아름, 서준혁))
        ▼
헤더 한 줄 (어노테이션 column 에서 뽑음 — 원본 주석의 주장)
+ 객체마다 한 줄
```

- (2) 의 거울이다: 객체를 읽을 때 쓴 `@CsvBindByName` 정보를 쓸 때도 쓴다.
- 원본 주석에 따르면 헤더를 어노테이션의 `column` 에서 뽑아 직접 써 준다.
  그래서 `CSVWriter` 처럼 헤더를 손으로 쓰지 않는다.
- `withSeparator(',')` 는 구분자를 정한다.
  기본값이 쉼표지만 명시적으로 적었다.
- `write(List)` 는 컬렉션을 한 번에 쓴다.
- 이름에 「Stateful」이 붙은 까닭은 헤더를 이미 썼는지 같은 상태를 기억하기 때문이다(원본에 근거 없음 — 추론).

## 문법 — 형태와 규칙

```java
class Item {
    @CsvBindByName(column = "품명") private String name;   // 헤더 이름으로
    @CsvBindByPosition(position = 1) private int qty;      // (예시용) 열 인덱스로
    public Item() {}                                       // 기본 생성자 필수
    // getter / setter ...
}

try (CSVReader r = new CSVReader(new FileReader("items.csv"))) {
    List<Item> items = new CsvToBeanBuilder<Item>(r)
        .withType(Item.class)
        .build()
        .parse();
}
```

- 한 클래스 안에서는 매핑 방식을 하나로 고른다 — 위 예는 두 어노테이션의 꼴만 보이려고 섞었다(확인 필요).
- `CSVReader.readNext()` → `String[]` 또는 `null`.
- `CSVWriter.writeNext(String[])` → 한 줄을 쓴다.
- `new CsvToBeanBuilder<T>(reader).withType(T.class).build().parse()` → `List<T>`.
- `new StatefulBeanToCsvBuilder<T>(writer).withSeparator(',').build().write(list)` → 헤더 + 행들.
- `List.of(...)` 는 불변 리스트를 만든다(Java 9+).
- 예제의 `"""` 로 감싼 문자열은 텍스트 블록이다.
  닫는 `"""` 의 들여쓰기 기준만큼 각 줄 앞 공백이 빠진다.

> **텍스트 블록** — `"""` 로 여러 줄 문자열을 그대로 적는 Java 문법이다.\
> 예: 예제의 `CSV_DATA`.

## 어디서 틀리나

### 1. 헤더를 데이터로 처리한다

`CSVReader` 는 헤더를 알아서 건너뛰지 않는다.
루프 전에 `readNext()` 를 한 번 부르지 않으면 첫 바퀴에 `이름, 부서, …` 가 데이터처럼 찍힌다.

### 2. 큰 파일을 `parse()` 로 통째로 읽는다

`parse()` 는 모든 행을 `List` 로 한 번에 올린다.
대용량 CSV 는 `CsvToBean` 대신 `CSVReader` 로 한 줄씩 처리하는 편이 메모리에 낫다.
원본 주석은 `CsvToBean` 의 `iterator()` 로 한 줄씩 처리하는 길도 든다.

### 3. 기본 생성자를 빠뜨린다

인자 있는 생성자만 두면 Java 는 기본 생성자를 만들어 주지 않는다.
OpenCSV 가 객체를 만들 수 없어 매핑이 실패한다.

### 4. `CSVWriter` 에 헤더를 안 쓴다

`CSVWriter` 는 헤더를 자동으로 넣지 않는다.
첫 `writeNext` 로 헤더를 직접 써야 한다.

### 5. `@CsvBindByName` 과 `@CsvBindByPosition` 을 헷갈린다

`@CsvBindByName` 은 헤더 이름으로, `@CsvBindByPosition` 은 열 인덱스로 짝짓는다.
열 차례가 바뀌는 파일에는 이름 방식이, 헤더가 없는 파일에는 위치 방식이 맞는다.

### 6. 숫자 열에 숫자가 아닌 값이 있다

`int` 필드에 `"칠천"` 같은 값이 오면 변환이 실패해 예외가 난다.
원본 주석은 이 예외를 `CsvException` 이라 부른다.

### 7. 부서별 평균의 차례를 믿는다

`groupingBy` 결과 `Map` 의 순서는 약속되지 않는다.
CSV 에 나온 차례대로 찍히리라 기대하면 안 된다.

### 8. 원본 주석 중 의심스러운 것

- **원본의 주장**: 「OpenCSV Bean 매핑은 setter 기반 (필드 직접 접근이 아닌 setter 호출)」.
  **왜 의심스러운가**: setter 가 없을 때 필드에 직접 넣는 경로가 있을 수 있다(확인 필요).
- **원본의 주장**: `StatefulBeanToCsv` 의 헤더는 「어노테이션의 column 속성에서 추출」.
  **왜 의심스러운가**: 헤더 열의 차례와 글자 꼴(대소문자)이 `column` 에 적은 그대로라고는 말하지 않는다 — 필드 선언 차례와 다를 수 있다(확인 필요).

### 9. 따옴표 · 쉼표를 손으로 이스케이프한다

`CSVWriter` 는 큰따옴표 · 쉼표가 든 필드를 자동으로 이스케이프한다.
손으로 따옴표를 덧붙이면 이중으로 감싸진다(원본에 근거 없음 — 추론).

### 10. 대안을 모른다

OpenCSV 말고 Apache Commons CSV 도 대안이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `readNext()` 가 끝에서 `null` 을 돌려준다 | OpenCSV 라이브러리 API |
| Bean 에 기본 생성자가 필요하다 | OpenCSV 의 객체 생성 방식(리플렉션) |
| 값을 setter 로 채운다 | OpenCSV 구현 — 원본 주석의 주장(확인 필요) |
| `StatefulBeanToCsv` 가 헤더를 쓴다 · 그 차례 | OpenCSV 구현 · 매핑 전략에 따름(확인 필요) |
| 큰따옴표 · 쉼표 자동 이스케이프 | OpenCSV 라이브러리 |
| `groupingBy` 결과 `Map` 의 순서가 약속되지 않는다 | Java 표준 API 명세(약속하지 않음을 약속) |
| `List.of` 가 불변 리스트다 | Java 표준 API(Java 9+) |
| 텍스트 블록의 들여쓰기 제거 | Java 언어 명세 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 아주 큰 파일을 한 번 훑기 | `CSVReader` 한 줄씩 · `CsvToBean` 의 `iterator()` | `parse()` 로 전부 올리기 |
| 행을 객체로 다루며 집계 | `CsvToBean` + 스트림 | 인덱스 `line[3]` 에 기대는 코드 |
| 열 차례가 바뀌기도 하는 파일 | `@CsvBindByName` | `@CsvBindByPosition` |
| 헤더 없는 파일 | `@CsvBindByPosition` · `CSVReader` | `@CsvBindByName` |
| 쓸 열 · 차례를 내가 정함 | `CSVWriter` | `StatefulBeanToCsv` |
| Bean 목록을 그대로 내보냄 | `StatefulBeanToCsv` | 필드마다 `String.valueOf` 를 손으로 |

## 핵심 문장

1. **`CSVReader` 는 한 줄을 `String[]` 로 준다** — 헤더도 그냥 한 줄이고, 끝에서는 `null` 이다.
2. **`CsvToBean` 은 어노테이션으로 열과 필드를 짝지어 행을 객체로 바꾼다** — 기본 생성자가 필수다.
3. **`parse()` 는 전부를 메모리에 올린다** — 큰 파일은 한 줄씩 처리한다.
4. **쓰기도 두 길이다** — `CSVWriter` 는 헤더까지 손으로, `StatefulBeanToCsv` 는 어노테이션에서 헤더를 뽑는다.
5. **특수 문자는 라이브러리가 이스케이프한다** — 손으로 따옴표를 덧대지 않는다.

## 관련 자료

- [excel-poi](../06-excel-poi/2-summary.md)
- `batch-processing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `yaml-snakeyaml` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/java/data-processing.json` 의 `csv-opencsv`

## 용어 풀이

- **CSV** — 쉼표로 값을, 줄바꿈으로 행을 나눈 텍스트 표 형식.
- **OpenCSV** — Java 용 CSV 읽기 · 쓰기 외부 라이브러리.
- **헤더** — CSV 의 첫 줄로, 열의 이름을 적은 행.
- **`CSVReader`** — 한 행을 `String[]` 로 돌려주는 OpenCSV 의 저수준 읽기 클래스.
- **`CSVWriter`** — `String[]` 를 한 행으로 쓰는 저수준 쓰기 클래스.
- **`CsvToBean`** — CSV 행을 Bean 객체로 바꿔 주는 클래스.
- **`StatefulBeanToCsv`** — Bean 객체를 CSV 행으로 쓰는 클래스.
- **Bean** — 기본 생성자와 getter · setter 를 갖춘 값 담는 클래스.
- **Bean 매핑** — CSV 열과 Bean 필드를 짝지어 서로 바꾸는 일.
- **`@CsvBindByName`** — 헤더 이름으로 열과 필드를 짝짓는 어노테이션.
- **`@CsvBindByPosition`** — 열 인덱스로 열과 필드를 짝짓는 어노테이션.
- **리플렉션** — 실행 중에 클래스 구성 요소를 찾아 다루는 Java 기능.
- **이스케이프** — 특별한 뜻이 있는 글자를 값으로 쓸 수 있게 감싸는 일.
- **try-with-resources** — 연 자원을 블록 끝에서 자동으로 닫는 문법.
- **텍스트 블록** — `"""` 로 적는 여러 줄 문자열.
- **`groupingBy` · `averagingInt`** — 스트림 원소를 키로 묶는 수집기 · 묶음의 `int` 평균을 내는 수집기.

## 더 들어가면

- `CSVWriter` 는 기본 설정에서 모든 필드를 큰따옴표로 감싸 쓴다고 알려져 있다(확인 필요).
  감싸지 않으려면 `writeNext(배열, false)` 꼴을 쓴다(확인 필요).
- `CsvToBean` 은 `Iterable` 이라 `for (Employee e : csvToBean)` 처럼 한 행씩 돌 수 있다(확인 필요).
- `@CsvBindByName(required = true)` 로 빈 값을 오류로 다룰 수 있다(확인 필요).
- `CsvToBeanBuilder` 에 `withThrowExceptions(false)` 를 주면 오류 행을 모아 두고 계속 읽는다(확인 필요).
- `StatefulBeanToCsv` 가 이름 매핑으로 헤더를 쓸 때 헤더를 대문자로 바꾸고 이름순으로 늘어놓는다는 보고가 있다(확인 필요).
  열 차례를 정하려면 매핑 전략을 직접 지정한다(확인 필요).
- CSV 형식의 흔한 기준 문서로 RFC 4180 이 꼽힌다(확인 필요).
