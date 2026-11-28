# java/java-data-processing/05 — CSV OpenCSV (CSV 처리) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 헤더 한 번 읽고 루프를 돌면 (예측)

```java
// 질문용 발췌 — CSV_DATA 는 헤더 1줄 + 데이터 5줄
try (CSVReader reader = new CSVReader(new StringReader(CSV_DATA))) {
    String[] header = reader.readNext();
    String[] line;
    while ((line = reader.readNext()) != null) {
        System.out.printf("  %s (%s, %s) - 연봉: %s만원%n", line[0], line[1], line[2], line[3]);
    }
}
```

- `while` 몸통은 몇 번 돌고, 첫 바퀴에 찍히는 줄은 무엇인가?

### 2. 헤더 읽기를 빼먹으면 (예측)

```java
// 질문용 발췌 — 위와 같은 CSV_DATA, header 줄을 지웠다
try (CSVReader reader = new CSVReader(new StringReader(CSV_DATA))) {
    String[] line;
    while ((line = reader.readNext()) != null) {
        System.out.printf("  %s (%s, %s) - 연봉: %s만원%n", line[0], line[1], line[2], line[3]);
    }
}
```

- 첫 바퀴에 찍히는 줄은 무엇인가?

### 3. 부서별 평균 연봉의 개발팀 값 (예측)

```java
// 질문용 발췌 — 개발팀 연봉: 7500, 9000, 5000
employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment,
             Collectors.averagingInt(Employee::getSalary)))
    .forEach((dept, avg) -> System.out.printf("  %s: %.0f만원%n", dept, avg));
```

- 개발팀 줄은 어떻게 찍히는가?

### 4. `Employee` 에 기본 생성자가 꼭 있어야 하는 까닭 (왜)

- 인자 있는 생성자가 이미 있는데 왜 `public Employee() {}` 를 따로 두어야 하나?

### 5. 헤더를 손으로 쓰는 쪽과 안 쓰는 쪽 (왜)

- `CSVWriter` 예제는 헤더를 `writeNext` 로 직접 쓰는데 `StatefulBeanToCsv` 예제는 왜 쓰지 않나?

### 6. `parse()` 가 버티지 못하는 곳 (경계)

- 수백만 행짜리 CSV 에서 `parse()` 는 어디서 문제가 되고, 대신 무엇을 써야 하나?

### 7. 부서 줄의 차례 (경계)

- 부서별 평균 연봉 줄이 CSV 에 처음 나온 부서 차례대로 찍힌다고 믿어도 되나?

### 8. 인덱스 접근과 두 매핑 어노테이션 (연결)

- `CSVReader` 예제의 `line[3]` 같은 인덱스 접근은 `@CsvBindByName` · `@CsvBindByPosition` 중 어느 쪽과 같은 생각이고, 다른 쪽은 어떤 약점을 덜어 주나?

## 실습

### 실습 1. 직원 CSV 를 읽고, 객체로 바꾸고, 다시 쓰기

**만들 것** — 문자열 CSV 를 `CSVReader` 로 한 줄씩 읽고, `CsvToBean` 으로 `Employee` 목록을 만들어 부서별 평균 연봉을 낸 뒤, `CSVWriter` 와 `StatefulBeanToCsv` 두 길로 객체를 CSV 텍스트로 다시 쓴다.

**준비물** — OpenCSV 라이브러리(`com.opencsv:opencsv:5.9`)가 클래스패스에 있어야 한다.

**요구 조건**

1단계 — Bean 준비
1. `Employee` 의 다섯 필드를 헤더 `이름 · 부서 · 직급 · 연봉 · 입사년도` 에 이름으로 짝짓는다.
2. OpenCSV 가 객체를 만들 수 있게 인자 없는 생성자를 둔다.

2단계 — `CSVReader` 로 읽기
3. `CSV_DATA` 를 `StringReader` 로 감싼 `CSVReader` 를 try-with-resources 로 연다.
4. 첫 줄을 헤더로 읽어 `헤더: [...]` 꼴로 찍는다.
5. 남은 줄을 `null` 이 나올 때까지 읽으며 `이름 (부서, 직급) - 연봉: …만원` 꼴로 찍는다.

3단계 — `CsvToBean` 으로 객체 만들기
6. 새 `CSVReader` 로 `CsvToBean<Employee>` 를 만든다 — 타입을 `Employee` 로 정하고 셀 앞쪽 공백을 무시한다.
7. `parse()` 로 `List<Employee>` 를 받아 객체마다 한 줄씩 찍는다.
8. 스트림으로 부서별 평균 연봉을 구해 `부서: 평균만원`(소수점 없이) 꼴로 찍는다.

4단계 — `CSVWriter` 로 쓰기
9. `StringWriter` 를 감싼 `CSVWriter` 로 헤더 한 줄을 직접 쓴다.
10. 직원 두 명(한소희 · 오세진)을 `String[]` 로 바꿔 한 줄씩 쓰고, 다 쓴 문자열을 찍는다.

5단계 — `StatefulBeanToCsv` 로 쓰기
11. 쉼표 구분자로 `StatefulBeanToCsv<Employee>` 를 만들어 직원 두 명(윤아름 · 서준혁)의 목록을 한 번에 쓰고, 그 문자열을 찍는다.

**시작 코드**

```java
// 의존성: implementation 'com.opencsv:opencsv:5.9'
import com.opencsv.*;
import com.opencsv.bean.*;
import com.opencsv.exceptions.CsvValidationException;
import java.io.*;
import java.util.*;

class Employee {
    // TODO: 각 필드에 헤더 이름을 짝짓는 어노테이션을 단다
    private String name;
    private String department;
    private String position;
    private int salary;
    private int joinYear;

    // TODO: OpenCSV 가 쓸 인자 없는 생성자

    public Employee(String name, String department, String position, int salary, int joinYear) {
        this.name = name;
        this.department = department;
        this.position = position;
        this.salary = salary;
        this.joinYear = joinYear;
    }

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

    @Override
    public String toString() {
        return String.format("Employee{name='%s', dept='%s', pos='%s', salary=%d, year=%d}",
            name, department, position, salary, joinYear);
    }
}

public class CsvOpenCsvDemo {
    static final String CSV_DATA = """
        이름,부서,직급,연봉,입사년도
        홍길동,개발팀,시니어,7500,2018
        김영희,기획팀,주니어,4500,2022
        이철수,개발팀,리드,9000,2015
        박민수,디자인팀,미드,6000,2020
        최지은,개발팀,주니어,5000,2023
        """;

    public static void main(String[] args) throws Exception {
        System.out.println("=== CSVReader 기본 읽기 ===");
        // TODO: CSVReader 로 헤더를 읽어 찍고, 남은 줄을 null 까지 읽어 찍는다

        System.out.println("\n=== CsvToBean: CSV -> 객체 ===");
        // TODO: CsvToBeanBuilder 로 CsvToBean<Employee> 를 만들고 parse() 한다
        // TODO: 객체마다 "  " + emp 를 찍는다
        System.out.println("\n부서별 평균 연봉:");
        // TODO: groupingBy + averagingInt 로 부서별 평균을 "  %s: %.0f만원%n" 꼴로 찍는다

        System.out.println("\n=== CSVWriter: 객체 -> CSV ===");
        StringWriter stringWriter = new StringWriter();
        // TODO: CSVWriter 로 헤더와 두 직원(한소희 마케팅팀 시니어 7000 2019, 오세진 개발팀 주니어 4800 2024)을 쓴다
        System.out.println(stringWriter.toString());

        System.out.println("=== StatefulBeanToCsv ===");
        StringWriter beanWriter = new StringWriter();
        // TODO: StatefulBeanToCsv 로 두 직원(윤아름 기획팀 미드 5500 2021, 서준혁 개발팀 시니어 8000 2017)을 한 번에 쓴다
        System.out.println(beanWriter.toString());
    }
}
```

**확인 방법** — OpenCSV 를 클래스패스에 두고 컴파일 · 실행한 뒤, 콘솔에 다섯 구역(기본 읽기 · 객체 목록 · 부서별 평균 · CSVWriter 결과 · StatefulBeanToCsv 결과)이 차례로 찍히는지, 기본 읽기 구역에 헤더 줄이 데이터처럼 끼지 않았는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
