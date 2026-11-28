# rust/rust-io/09 — CSV 데이터 처리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 헤더는 공백이 지워진 두 이름, 행은 빈 줄을 뺀 2개

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
["id", "name"]
2
```

**왜 그런가**
첫 줄 `"id, name"` 을 쉼표에서 자르면 `"id"` 와 `" name"` 이고, `trim()` 이 공백을 지운다.
나머지 줄은 `"1, kim"` · `""` · `"2, lee"` 인데, 빈 줄은 `filter(|l| !l.trim().is_empty())` 가 버린다.
끝의 `\n` 은 `lines()` 가 빈 줄을 따로 만들지 않는다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `True` 는 `false` 가 되고, `abc` 급여는 에러다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Ok(false)
true
```

**왜 그런가**
`bool` 의 `parse` 는 `"true"` · `"false"` 만 받으므로 `"True"` 는 실패하고, `unwrap_or(false)` 가 `false` 를 넣는다 — 그래서 `Ok` 이면서 `active` 는 `false` 다.
`"abc"` 는 `f64` 로 파싱되지 않아 `map_err` 와 `?` 가 `Err` 를 곧장 돌려주므로 `is_err()` 는 `true` 다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 3. 소수 부분이 사라진 `95000` 이 쉼표 뒤 공백 없이 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
name,salary
Alice,95000
```

(마지막 줄 뒤에도 줄바꿈이 하나 있다.)

**왜 그런가**
`f64` 의 `to_string()` 은 Display 서식이라 소수 부분이 0이면 `95000` 으로 바뀐다.
`to_string()` 은 헤더와 각 행을 `join(",")` 으로 이어 공백 없이 쓰고, 줄마다 `\n` 을 붙인다.
근거: 2-summary 「동작 방식 (5)」.

### 4. 헤더가 `" department"` 로 남아 이름이 일치하지 않는다

원본 데이터는 쉼표 뒤에 공백이 있어, `split(',')` 만 하면 두 번째 헤더가 `" department"` 다.
`get_column` 은 `position(|h| h == name)` 으로 완전히 같은 이름을 찾으므로 `None` 을 받고, `None` 이면 빈 `Vec` 을 돌려준다.
에러가 아니라 빈 결과라서 실수를 알아채기 어렵다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 다섯 칸으로 갈라지고 따옴표가 값에 남는다

이 파서는 인용부호를 지원하지 않고 모든 쉼표에서 자른다.
그래서 `Kim` · `"Seoul` · `Korea"` · `50000.0` · `true` 의 다섯 칸이 되고, 따옴표는 값에 그대로 남는다.
칸이 하나씩 밀려 `from_csv_row` 에서는 `salary` 자리에 `Korea"` 가 와 파싱 에러가 난다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 6. 실패한 행이 아무 메시지 없이 결과에서 빠진다

`.ok()` 는 `Err` 를 `None` 으로 바꾸면서 에러 메시지를 버리고, `filter_map` 은 `None` 을 건너뛴다.
그래서 깨진 행이 있어도 직원 수만 줄어들 뿐 어떤 행이 왜 빠졌는지 알 수 없다.
평균이나 인원 같은 분석이 조용히 틀어진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 7. 마지막 헤더 키가 없는, 키가 하나 적은 맵이 된다

`to_maps` 는 `zip` 으로 헤더와 값을 짝짓는데, `zip` 은 짧은 쪽에서 멈춘다.
값이 하나 모자라면 마지막 헤더는 짝이 없어 맵에 들어가지 않는다.
에러는 나지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 9」.

### 8. 믿으면 안 된다

부서별 묶음 `by_dept` 는 `HashMap` 이고, `HashMap` 은 순회 순서를 보장하지 않는다.
`Engineering` 과 `Marketing` 중 무엇이 먼저 찍힐지는 정해져 있지 않다.
순서가 필요하면 정렬하거나 순서를 지키는 자료구조를 쓴다.
근거: 2-summary 「동작 방식 (4)」 · 「구현 세부사항 대 언어 보장」.

### 9. 칸 번호로 필드를 채우고 문자열을 타입으로 파싱하는 손 매핑이 사라진다

`csv` 크레이트는 `serde` 와 통합되어 `rdr.deserialize()` 로 행을 `Employee` 로 직접 역직렬화한다.
`from_csv_row` 가 하던 칸 수 검사, `row[0]` 같은 칸 번호 대응, `parse` 로 `f64` · `bool` 바꾸기를 라이브러리가 맡는다.
결과는 레코드마다 `Result` 로 와서 `result?` 로 꺼낸다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 8」.

### 10. 스트리밍은 전체를 메모리에 올리지 않기 때문이다

`from_str` 은 입력 문자열 전체와 모든 행을 `rows` 에 올린 뒤에야 쓸 수 있다.
레코드 단위 스트리밍(`for result in rdr.deserialize()`)은 한 건씩 읽고 처리하므로 파일 크기만큼의 메모리가 필요 없다.
원본 팁도 대용량 CSV 는 레코드 단위로 스트리밍 처리한다고 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. CSV 를 읽어 구조체로 바꾸고, 분석하고, 다시 쓰기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 헤더 · 행 필드 | `struct CsvReader { headers, rows }` |
| 2. 첫 줄을 헤더로, 없으면 빈 `Vec` | `lines.next().map(… split(',') … trim() …).unwrap_or_default()` |
| 3. 빈 줄 건너뛰고 행으로 | `lines.filter(\|l\| !l.trim().is_empty()).map(…)` |
| 4. 컬럼 값 모으기 | `get_column` — `position` · `filter_map(\|row\| row.get(i) …)` · `None => vec![]` |
| 5. 행마다 맵 | `to_maps` — `headers.iter().zip(row.iter())` |
| 6. Writer 초기화 | `CsvWriter::new` |
| 7. 한 행 쌓기 | `add_row` — `self.rows.push(…)` |
| 8. CSV 문자열 빌드 | `CsvWriter::to_string` — `join(",")` · `push('\n')` |
| 9. 필드와 derive | `#[derive(Debug, Clone)] struct Employee` |
| 10. 칸 수 검증 | `if row.len() < 4 { return Err("필드 부족" …) }` |
| 11. 급여 파싱 실패는 에러 | `row[2].parse().map_err(\|e\| format!("salary 파싱 에러: {}", e))?` |
| 12. 재직 파싱 실패는 `false` | `row[3].parse().unwrap_or(false)` |
| 13. 한 줄로 쓰기 | `to_csv_row` — `format!("{},{},{},{}", …)` |
| 14. 읽기 출력 | `main` 의 `CsvReader::from_str(csv_data)` · `get_column("name")` · `to_maps()` |
| 15. 구조체 변환 | `filter_map(\|row\| Employee::from_csv_row(row).ok())` |
| 16. 분석 | `total_salary` · `avg_salary` · `by_dept.entry(&emp.department).or_default().push(emp)` · `active_count` |
| 17. 다시 쓰기 | `CsvWriter::new(vec![…])` · `writer.add_row(vec![… &emp.salary.to_string(), &emp.active.to_string()])` |
| 18. 크레이트 사용법 출력 | `=== 실제 csv 크레이트 ===` 아래의 `println!` 들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-io/reference/serde-csv.rs`

```rust
// [입출력 & 직렬화] CSV 데이터 처리
// 설명: csv 크레이트 패턴, Reader/Writer, 헤더, 구조체 매핑
// 팁: csv 크레이트는 serde와 통합되어 구조체를 직접 역직렬화할 수 있다. 대용량 CSV는 레코드 단위로 스트리밍 처리한다. ReaderBuilder로 구분자, 헤더 유무, 인용부호 등을 커스터마이즈할 수 있다.

// === CSV 처리 패턴 (순수 Rust 구현) ===
// 실제: csv = "1", serde = { version = "1", features = ["derive"] }

// === 1. 간단한 CSV 파서 ===
// CsvReader: 헤더와 행을 메모리에 로드한 단순 파서
struct CsvReader {
    // 첫 줄을 분리한 컬럼 이름들
    headers: Vec<String>,
    // 본문 행. 각 행은 컬럼 값들의 Vec
    rows: Vec<Vec<String>>,
}

impl CsvReader {
    // 문자열 전체에서 헤더+행 파싱 (간단 구현, 인용부호/이스케이프 미지원)
    fn from_str(input: &str) -> Self {
        // 줄 이터레이터
        let mut lines = input.lines();
        // 첫 줄 = 헤더
        let headers = lines.next()
            .map(|h| h.split(',').map(|s| s.trim().to_string()).collect())
            .unwrap_or_default();

        // 빈 줄 제외하고 각 줄을 컬럼으로 분리
        let rows: Vec<Vec<String>> = lines
            .filter(|l| !l.trim().is_empty())
            .map(|line| line.split(',').map(|s| s.trim().to_string()).collect())
            .collect();

        CsvReader { headers, rows }
    }

    // 특정 컬럼 이름의 값들만 추출
    fn get_column(&self, name: &str) -> Vec<&str> {
        // 헤더 인덱스 찾기
        let idx = self.headers.iter().position(|h| h == name);
        match idx {
            // 그 인덱스 위치의 값들 모으기
            Some(i) => self.rows.iter()
                .filter_map(|row| row.get(i).map(|s| s.as_str()))
                .collect(),
            None => vec![],
        }
    }

    // 행을 헤더-값 맵의 Vec로 변환 (각 행마다 HashMap)
    fn to_maps(&self) -> Vec<std::collections::HashMap<&str, &str>> {
        self.rows.iter().map(|row| {
            // 헤더와 값 zip → 맵
            self.headers.iter().zip(row.iter())
                .map(|(h, v)| (h.as_str(), v.as_str()))
                .collect()
        }).collect()
    }
}

// === 2. CSV Writer ===
// CsvWriter: 헤더 정의 후 행을 누적, 마지막에 문자열로 출력
struct CsvWriter {
    headers: Vec<String>,
    rows: Vec<Vec<String>>,
}

impl CsvWriter {
    // 헤더 슬라이스로 초기화
    fn new(headers: Vec<&str>) -> Self {
        CsvWriter {
            headers: headers.into_iter().map(|h| h.to_string()).collect(),
            rows: Vec::new(),
        }
    }

    // 한 행 추가 (헤더 개수와 일치 가정)
    fn add_row(&mut self, values: Vec<&str>) {
        self.rows.push(values.into_iter().map(|v| v.to_string()).collect());
    }

    // CSV 문자열 빌드
    fn to_string(&self) -> String {
        // 헤더 줄
        let mut output = self.headers.join(",");
        output.push('\n');
        // 본문 줄
        for row in &self.rows {
            output.push_str(&row.join(","));
            output.push('\n');
        }
        output
    }
}

// === 3. 타입 안전한 레코드 ===
// Employee: CSV 행 ↔ 구조체 매핑 예시
#[derive(Debug, Clone)]
struct Employee {
    name: String,
    department: String,
    salary: f64,
    active: bool,
}

impl Employee {
    // CSV 행(문자열 슬라이스 배열) → Employee
    fn from_csv_row(row: &[String]) -> Result<Self, String> {
        // 컬럼 수 검증
        if row.len() < 4 {
            return Err("필드 부족".to_string());
        }
        Ok(Employee {
            name: row[0].clone(),
            department: row[1].clone(),
            // f64 파싱 실패는 에러로
            salary: row[2].parse().map_err(|e| format!("salary 파싱 에러: {}", e))?,
            // bool 파싱 실패는 false로
            active: row[3].parse().unwrap_or(false),
        })
    }

    // Employee → CSV 한 줄 문자열
    fn to_csv_row(&self) -> String {
        format!("{},{},{},{}", self.name, self.department, self.salary, self.active)
    }
}

fn main() {
    // === CSV 읽기 ===
    println!("=== CSV 읽기 ===");
    // 줄 끝 \ 로 줄바꿈 이스케이프
    let csv_data = "\
name, department, salary, active
Alice, Engineering, 95000.0, true
Bob, Marketing, 72000.0, true
Charlie, Engineering, 88000.0, false
Diana, Marketing, 81000.0, true
Eve, Engineering, 102000.0, true";

    // 파서 생성
    let reader = CsvReader::from_str(csv_data);
    println!("헤더: {:?}", reader.headers);
    println!("행 수: {}", reader.rows.len());

    // 컬럼 추출
    let names = reader.get_column("name");
    println!("이름들: {:?}", names);

    // 맵으로 변환
    // 각 행을 헤더 키로 접근 가능한 맵으로
    let maps = reader.to_maps();
    for map in &maps {
        println!("  {:?}", map);
    }

    // === 구조체로 변환 ===
    println!("\n=== 구조체로 변환 ===");
    // 실패한 행은 제거하고 성공만 수집
    let employees: Vec<Employee> = reader.rows.iter()
        .filter_map(|row| Employee::from_csv_row(row).ok())
        .collect();
    for emp in &employees {
        println!("  {:?}", emp);
    }

    // === 데이터 분석 ===
    println!("\n=== 데이터 분석 ===");
    // 총 급여 합산 → 평균 산출
    let total_salary: f64 = employees.iter().map(|e| e.salary).sum();
    let avg_salary = total_salary / employees.len() as f64;
    println!("평균 급여: {:.0}", avg_salary);

    // 부서별 그룹핑
    // entry().or_default(): 없으면 빈 Vec 삽입 후 push
    let mut by_dept: std::collections::HashMap<&str, Vec<&Employee>> =
        std::collections::HashMap::new();
    for emp in &employees {
        by_dept.entry(&emp.department).or_default().push(emp);
    }
    // 그룹별 평균 출력
    for (dept, emps) in &by_dept {
        let avg: f64 = emps.iter().map(|e| e.salary).sum::<f64>() / emps.len() as f64;
        println!("  {} 부서: {}명, 평균 급여: {:.0}", dept, emps.len(), avg);
    }

    // 활성 직원만 카운트
    let active_count = employees.iter().filter(|e| e.active).count();
    println!("활성 직원: {}/{}", active_count, employees.len());

    // === CSV 쓰기 ===
    println!("\n=== CSV 쓰기 ===");
    // 헤더 지정해서 Writer 생성
    let mut writer = CsvWriter::new(vec!["name", "department", "salary", "active"]);
    for emp in &employees {
        // 각 행 추가 (모든 필드를 &str로 통일)
        writer.add_row(vec![&emp.name, &emp.department,
            &emp.salary.to_string(), &emp.active.to_string()]);
    }
    println!("{}", writer.to_string());

    // === 실제 csv 크레이트 사용법 ===
    println!("=== 실제 csv 크레이트 ===");
    // serde 통합으로 구조체 자동 매핑 가능
    println!("// 읽기:");
    println!("// let mut rdr = csv::Reader::from_path(\"data.csv\")?;");
    println!("// for result in rdr.deserialize() {{");
    println!("//     let record: Employee = result?;");
    println!("//     println!(\"{{:?}}\", record);");
    println!("// }}");
    println!("//");
    println!("// 쓰기:");
    println!("// let mut wtr = csv::Writer::from_path(\"output.csv\")?;");
    println!("// wtr.serialize(Employee {{ ... }})?;");
    println!("// wtr.flush()?;");
    println!("//");
    // 헤더/구분자 커스터마이즈
    println!("// 헤더 없이:");
    println!("// csv::ReaderBuilder::new().has_headers(false).from_reader(rdr)");
    println!("// 구분자 변경:");
    println!("// csv::ReaderBuilder::new().delimiter(b'\\t').from_reader(rdr)");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 읽기는 「첫 줄 = 헤더, 빈 줄을 뺀 나머지 = 행」이고, 쉼표 뒤 공백 때문에 칸마다 `trim()` 이 꼭 필요하다.
- `get_column` · `to_maps` 는 `&str` 을 빌려 돌려주므로 복사 없이 `CsvReader` 안의 문자열을 가리킨다.
- `from_csv_row` 는 급여 실패를 `?` 로 거부하고 재직 실패는 `false` 로 채운다 — 칸마다 실패 정책이 다르다.
- `.ok()` 로 모으면 실패한 행이 조용히 빠지고, `HashMap` 출력 순서는 정해져 있지 않다.
- 쓰기는 `join(",")` 일 뿐이라 인용부호 처리가 없고, `f64` 의 `to_string()` 은 `95000.0` 을 `95000` 으로 바꾼다.
- 실제로는 `csv` 크레이트가 `serde` 역직렬화 · 스트리밍 · `ReaderBuilder` 설정으로 이 모든 손 작업을 대신한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
