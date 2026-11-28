# java/java-data-processing/05 — CSV OpenCSV (CSV 처리) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 다섯 번 돌고, 첫 줄은 홍길동의 줄이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  홍길동 (개발팀, 시니어) - 연봉: 7500만원
```

`while` 몸통은 5번 돈다.

**왜 그런가**
루프 전 `readNext()` 가 헤더 줄을 가져가 버린다.
남은 데이터 5줄이 한 바퀴에 한 줄씩 `String[]` 로 오고, 여섯 번째 호출에서 `null` 이 와서 끝난다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 헤더가 데이터처럼 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  이름 (부서, 직급) - 연봉: 연봉만원
```

**왜 그런가**
`CSVReader` 는 첫 줄이 헤더인 줄 모른다.
첫 `readNext()` 가 헤더 줄을 `["이름","부서","직급","연봉","입사년도"]` 로 돌려주고, 그대로 형식 문자열에 들어간다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 3. 개발팀은 7167만원이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  개발팀: 7167만원
```

**왜 그런가**
`averagingInt` 가 (7500 + 9000 + 5000) / 3 = 21500 / 3 = 7166.66… 을 `double` 로 낸다.
`%.0f` 가 소수점 아래를 반올림해 7167 이 된다.
이 줄이 몇 번째로 찍히는지는 정해지지 않는다(퀴즈 7).
근거: 2-summary 「동작 방식 (3)」.

### 4. OpenCSV 가 리플렉션으로 빈 객체부터 만들기 때문이다

OpenCSV 는 `Employee.class` 를 받아 리플렉션으로 인자 없는 생성자를 불러 객체를 만들고, 그 뒤에 열 값을 채운다.
인자 있는 생성자를 하나라도 적으면 Java 는 기본 생성자를 만들어 주지 않으므로 직접 적어야 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 5. `StatefulBeanToCsv` 는 어노테이션에서 헤더를 뽑아 스스로 쓰기 때문이다

`CSVWriter` 는 `String[]` 를 한 줄로 옮길 뿐이라 헤더가 무엇인지 모른다 — 자동으로 넣지 않는다.
`StatefulBeanToCsv` 는 Bean 의 `@CsvBindByName` 정보를 알고 있어 그 `column` 에서 헤더를 만들어 먼저 쓴다(원본 주석의 주장 — 헤더의 차례와 글자 꼴은 확인 필요).
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「어디서 틀리나 8」.

### 6. 모든 행을 한꺼번에 메모리에 올리는 데서 문제가 된다

`parse()` 는 전체 행을 `List` 로 한 번에 만든다.
행이 많으면 그만큼 객체가 메모리에 쌓여 감당하지 못할 수 있다.
대신 `CSVReader` 로 한 줄씩 읽어 처리하거나, `CsvToBean` 의 `iterator()` 로 한 행씩 받는다.
근거: 2-summary 「동작 방식 (2)」 · 「어어디서 틀리나 2」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 믿으면 안 된다

`groupingBy` 가 돌려주는 `Map` 의 종류와 순서를 Java API 는 약속하지 않는다.
그래서 개발팀 · 기획팀 · 디자인팀 줄이 어떤 차례로 찍힐지 코드만으로 정할 수 없다.
근거: 2-summary 「동작 방식 (3)」 · 「구현 세부사항 대 언어 보장」.

### 8. 인덱스 접근은 `@CsvBindByPosition` 과 같은 생각이고, `@CsvBindByName` 이 열 차례 변화에 대한 약점을 덜어 준다

`line[3]` 은 「네 번째 열이 연봉」이라는 위치 약속에 기댄다 — 열 인덱스로 짝짓는 `@CsvBindByPosition` 과 같다.
파일의 열 차례가 바뀌면 위치 방식은 엉뚱한 값을 읽는다.
`@CsvBindByName` 은 헤더 이름으로 짝지어 차례가 바뀌어도 맞는 필드를 찾는다.
거꾸로 헤더가 없는 파일에는 위치 방식만 쓸 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「어디서 틀리나 5」.

## 실습 정답

### 실습 1. 직원 CSV 를 읽고, 객체로 바꾸고, 다시 쓰기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 다섯 필드를 헤더 이름으로 짝짓기 | `@CsvBindByName(column = "이름")` … `@CsvBindByName(column = "입사년도")` |
| 2. 인자 없는 생성자 | `public Employee() {}` |
| 3. `CSVReader` 를 try-with-resources 로 | `try (CSVReader reader = new CSVReader(new StringReader(CSV_DATA)))` |
| 4. 헤더를 읽어 찍기 | `String[] header = reader.readNext();` · `Arrays.toString(header)` |
| 5. `null` 까지 읽으며 찍기 | `while ((line = reader.readNext()) != null)` · `line[0]` … `line[3]` |
| 6. `CsvToBean` 만들기(타입 · 앞 공백 무시) | `new CsvToBeanBuilder<Employee>(reader).withType(Employee.class).withIgnoreLeadingWhiteSpace(true).build()` |
| 7. `parse()` 후 객체마다 찍기 | `csvToBean.parse()` · `employees.forEach(...)` |
| 8. 부서별 평균 연봉 | `Collectors.groupingBy(Employee::getDepartment, Collectors.averagingInt(Employee::getSalary))` · `%.0f` |
| 9. `CSVWriter` 로 헤더 직접 쓰기 | `writer.writeNext(new String[]{"이름", "부서", "직급", "연봉", "입사년도"})` |
| 10. 두 직원을 `String[]` 로 쓰고 찍기 | `for (Employee emp : newEmployees) writer.writeNext(...)` · `String.valueOf(...)` · `stringWriter.toString()` |
| 11. `StatefulBeanToCsv` 로 목록 한 번에 쓰기 | `new StatefulBeanToCsvBuilder<Employee>(beanWriter).withSeparator(',').build()` · `beanToCsv.write(List.of(...))` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-data-processing/reference/csv-opencsv.java`

```java
// [데이터 처리 & 유틸] CSV OpenCSV (CSV 처리)
// 설명: OpenCSV로 CSV 읽기/쓰기. CSVReader/Writer, Bean 매핑으로 객체 변환
// 팁: OpenCSV의 @CsvBindByName은 헤더 이름으로, @CsvBindByPosition은 열 인덱스로 매핑한다. 큰따옴표가 포함된 필드는 자동으로 이스케이프된다. 대용량 CSV는 CsvToBean 대신 CSVReader로 한 줄씩 처리하는 것이 메모리 효율적이다. Apache Commons CSV도 대안이다.

// === OpenCSV: CSV 읽기/쓰기 & Bean 매핑 ===
// 의존성: implementation 'com.opencsv:opencsv:5.9'

// CSVReader / CSVWriter 등 저수준 API
import com.opencsv.*;
// Bean 매핑용 빌더 / 어노테이션 (@CsvBindByName 등)
import com.opencsv.bean.*;
// CSV 검증 실패 시 던져지는 체크 예외
import com.opencsv.exceptions.CsvValidationException;
// Reader / Writer / StringReader / StringWriter
import java.io.*;
// List / Arrays 등 컬렉션 유틸
import java.util.*;

// Bean 매핑용 클래스 (CSV 한 행 = Employee 객체 1개로 변환)
class Employee {
    // CSV 헤더 "이름" 열을 이 필드로 매핑 (헤더명 기준 매핑)
    @CsvBindByName(column = "이름")
    private String name;

    // 주의: column 속성을 생략하면 필드명과 일치하는 헤더를 찾음
    @CsvBindByName(column = "부서")
    private String department;

    @CsvBindByName(column = "직급")
    private String position;

    // 숫자 타입은 OpenCSV가 자동으로 변환 (변환 실패 시 CsvException)
    @CsvBindByName(column = "연봉")
    private int salary;

    @CsvBindByName(column = "입사년도")
    private int joinYear;

    // OpenCSV가 리플렉션으로 인스턴스 생성 → 기본 생성자 필수
    public Employee() {}

    // 직접 생성용 편의 생성자
    public Employee(String name, String department, String position, int salary, int joinYear) {
        this.name = name;
        this.department = department;
        this.position = position;
        this.salary = salary;
        this.joinYear = joinYear;
    }

    // Getters & Setters
    // OpenCSV Bean 매핑은 setter 기반 (필드 직접 접근이 아닌 setter 호출)
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getDepartment() { return department; }
    public void setDepartment(String department) { this.department = department; }
    public String getPosition() { return position; }
    public void setPosition(String position) { this.position = position; }
    public int getSalary() { return salary; }
    public void setSalary(int salary) { this.salary = salary; }
    public int getJoinYear() { return joinYear; }
    public void setJoinYear(int joinYear) { this.joinYear = joinYear; }

    // 디버깅/로깅용 표현
    @Override
    public String toString() {
        return String.format("Employee{name='%s', dept='%s', pos='%s', salary=%d, year=%d}",
            name, department, position, salary, joinYear);
    }
}

public class CsvOpenCsvDemo {
    // 테스트용 CSV 데이터 (헤더 + 5행). 실제로는 파일에서 읽음
    static final String CSV_DATA = """
        이름,부서,직급,연봉,입사년도
        홍길동,개발팀,시니어,7500,2018
        김영희,기획팀,주니어,4500,2022
        이철수,개발팀,리드,9000,2015
        박민수,디자인팀,미드,6000,2020
        최지은,개발팀,주니어,5000,2023
        """;

    public static void main(String[] args) throws Exception {
        // === 1. 기본 CSVReader로 읽기 ===
        // 가장 저수준 API: 한 줄을 String[] 배열로 반환
        System.out.println("=== CSVReader 기본 읽기 ===");
        // try-with-resources: 자동으로 close() 호출
        try (CSVReader reader = new CSVReader(new StringReader(CSV_DATA))) {
            // 첫 줄을 헤더로 읽음 (자동 헤더 인식이 아님 - 직접 호출)
            String[] header = reader.readNext(); // 헤더
            System.out.println("헤더: " + Arrays.toString(header));

            // 더 이상 읽을 줄이 없으면 readNext()는 null 반환
            String[] line;
            while ((line = reader.readNext()) != null) {
                // 인덱스로 접근: 0=이름, 1=부서, 2=직급, 3=연봉
                System.out.printf("  %s (%s, %s) - 연봉: %s만원%n",
                    line[0], line[1], line[2], line[3]);
            }
        }

        // === 2. CsvToBean: CSV -> Java 객체 ===
        // 어노테이션 기반 매핑으로 한 행을 객체로 자동 변환
        System.out.println("\n=== CsvToBean: CSV -> 객체 ===");
        try (CSVReader reader = new CSVReader(new StringReader(CSV_DATA))) {
            // CsvToBeanBuilder: 매핑 설정을 선언적으로 구성
            CsvToBean<Employee> csvToBean = new CsvToBeanBuilder<Employee>(reader)
                .withType(Employee.class)
                // 셀 앞쪽 공백 자동 제거 (CSV 데이터 정제)
                .withIgnoreLeadingWhiteSpace(true)
                .build();

            // parse(): 전체 데이터를 List<Employee>로 한 번에 반환 (메모리 모두 로드)
            // 함정: 대용량 CSV는 iterator() 사용해 한 줄씩 처리해야 함
            List<Employee> employees = csvToBean.parse();
            employees.forEach(emp -> System.out.println("  " + emp));

            // 부서별 평균 연봉: Stream API의 groupingBy + averagingInt 활용
            System.out.println("\n부서별 평균 연봉:");
            employees.stream()
                .collect(java.util.stream.Collectors.groupingBy(
                    Employee::getDepartment,
                    java.util.stream.Collectors.averagingInt(Employee::getSalary)))
                .forEach((dept, avg) -> System.out.printf("  %s: %.0f만원%n", dept, avg));
        }

        // === 3. CSVWriter: 객체 -> CSV ===
        // 가장 단순한 쓰기: String[]로 한 줄씩 직접 작성
        System.out.println("\n=== CSVWriter: 객체 -> CSV ===");
        StringWriter stringWriter = new StringWriter();
        try (CSVWriter writer = new CSVWriter(stringWriter)) {
            // 헤더 쓰기 (자동 추가되지 않으므로 명시적으로 작성)
            writer.writeNext(new String[]{"이름", "부서", "직급", "연봉", "입사년도"});

            // 데이터 쓰기
            // List.of(): 불변 리스트 생성 (Java 9+)
            List<Employee> newEmployees = List.of(
                new Employee("한소희", "마케팅팀", "시니어", 7000, 2019),
                new Employee("오세진", "개발팀", "주니어", 4800, 2024)
            );

            // 각 객체를 String[]로 변환하여 한 줄씩 쓰기
            // CSVWriter는 큰따옴표/쉼표가 포함된 필드를 자동 이스케이프
            for (Employee emp : newEmployees) {
                writer.writeNext(new String[]{
                    emp.getName(), emp.getDepartment(), emp.getPosition(),
                    String.valueOf(emp.getSalary()), String.valueOf(emp.getJoinYear())
                });
            }
        }
        System.out.println(stringWriter.toString());

        // === 4. StatefulBeanToCsv: 객체 -> CSV (Bean 매핑) ===
        // 어노테이션을 활용한 자동 매핑 쓰기 (헤더는 어노테이션의 column 속성에서 추출)
        System.out.println("=== StatefulBeanToCsv ===");
        StringWriter beanWriter = new StringWriter();
        StatefulBeanToCsv<Employee> beanToCsv = new StatefulBeanToCsvBuilder<Employee>(beanWriter)
            // 구분자 지정 (기본값은 쉼표지만 명시적으로)
            .withSeparator(',')
            .build();

        // write(List): 컬렉션을 한 번에 출력
        beanToCsv.write(List.of(
            new Employee("윤아름", "기획팀", "미드", 5500, 2021),
            new Employee("서준혁", "개발팀", "시니어", 8000, 2017)
        ));
        System.out.println(beanWriter.toString());

        // 출력:
        // === CSVReader 기본 읽기 ===
        // 헤더: [이름, 부서, 직급, 연봉, 입사년도]
        //   홍길동 (개발팀, 시니어) - 연봉: 7500만원
        //   김영희 (기획팀, 주니어) - 연봉: 4500만원
        //   ...
        //
        // === CsvToBean: CSV -> 객체 ===
        //   Employee{name='홍길동', dept='개발팀', pos='시니어', salary=7500, year=2018}
        //   ...
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 읽기는 두 층이다 — `CSVReader` 는 `String[]`, `CsvToBean` 은 그 위에서 어노테이션으로 객체를 만든다.
- `CSVReader` 는 헤더를 모르므로 루프 전 `readNext()` 한 번으로 헤더를 떼어 낸다.
- Bean 에는 기본 생성자가 있어야 하고, 숫자 필드는 OpenCSV 가 문자열에서 변환한다.
- 쓰기도 두 층이다 — `CSVWriter` 는 헤더까지 손으로, `StatefulBeanToCsv` 는 어노테이션에서 헤더를 뽑는다.
- `parse()` 는 전부를 메모리에 올리므로 큰 파일에는 한 줄씩 처리하는 길을 고른다.
- 부서별 평균 줄의 차례는 약속되지 않으니 차례에 기대는 검사를 하지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
