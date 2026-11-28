# rust/rust-io/09 — CSV 데이터 처리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 빈 줄이 낀 문자열을 `from_str` 으로 읽으면 (예측)

```rust
// 질문용 발췌
let r = CsvReader::from_str("id, name\n1, kim\n\n2, lee\n");
println!("{:?}", r.headers);
println!("{}", r.rows.len());
```

- 두 줄에 각각 무엇이 찍히나?

### 2. `True` 와 `abc` 가 든 행 (예측)

```rust
// 질문용 발췌
let a = vec!["Kim".to_string(), "Dev".to_string(), "50000".to_string(), "True".to_string()];
let b = vec!["Lee".to_string(), "Dev".to_string(), "abc".to_string(), "true".to_string()];
println!("{:?}", Employee::from_csv_row(&a).map(|e| e.active));
println!("{}", Employee::from_csv_row(&b).is_err());
```

- 두 줄에 각각 무엇이 찍히나?

### 3. `95000.0` 을 `CsvWriter` 로 쓰면 (예측)

```rust
// 질문용 발췌
let mut w = CsvWriter::new(vec!["name", "salary"]);
let s = 95000.0_f64;
w.add_row(vec!["Alice", &s.to_string()]);
print!("{}", w.to_string());
```

- 찍히는 텍스트는 정확히 어떤 줄들인가?

### 4. 칸을 자른 뒤 `trim()` 을 거치는 까닭 (왜)
- 예제 데이터에서 `trim()` 을 빼면 `get_column("department")` 이 왜 빈 결과를 돌려주나?

### 5. 값 안에 쉼표가 든 행 (경계)
- `Kim, "Seoul, Korea", 50000.0, true` 같은 줄을 이 `CsvReader` 가 읽으면 그 행은 어떻게 갈라지나?

### 6. `filter_map(… .ok())` 로 직원을 모으는 방식 (왜)
- 급여 칸이 깨진 행이 섞여 있을 때 이 방식이 왜 위험할 수 있나?

### 7. 헤더보다 칸이 적은 행 (경계)
- 칸이 하나 모자란 행은 `to_maps` 의 맵에서 어떤 모양이 되나?

### 8. 부서별 출력의 차례 (경계)
- 부서별 평균을 찍는 줄들의 차례가 실행마다 같다고 믿어도 되나?

### 9. `from_csv_row` 와 `csv` 크레이트의 `deserialize()` (연결)
- `serde` 와 통합된 `csv` 크레이트를 쓰면 손수 쓴 `from_csv_row` 의 어떤 일이 사라지나?

### 10. 대용량 CSV 와 `CsvReader::from_str` (연결)
- 수 GB 파일이라면 `from_str` 방식과 레코드 단위 스트리밍 중 왜 뒤의 것을 고르나?

## 실습

### 실습 1. CSV 를 읽어 구조체로 바꾸고, 분석하고, 다시 쓰기

**만들 것** — 외부 크레이트 없이 CSV 문자열을 헤더와 행으로 읽는 파서, 행을 `Employee` 구조체로 바꾸는 매핑, 간단한 분석, 그리고 다시 CSV 문자열로 쓰는 Writer 를 만든다.

**준비물** — 표준 라이브러리만 필요하다. 정답 코드는 실제 `csv` · `serde` 크레이트를 쓰지 않고 그 패턴을 순수 Rust 로 흉내 낸 것이다.

**요구 조건**

1단계 — `CsvReader`
1. `CsvReader` 는 `headers: Vec<String>` 과 `rows: Vec<Vec<String>>` 을 가진다.
2. `from_str(input: &str)` 은 첫 줄을 쉼표로 잘라 칸마다 앞뒤 공백을 지운 헤더로 삼는다. 첫 줄이 없으면 헤더는 빈 `Vec` 이다.
3. 나머지 줄 중 공백뿐인 줄은 건너뛰고, 각 줄을 같은 방식으로 잘라 `rows` 에 넣는다.
4. `get_column(name)` 은 헤더에서 그 이름의 위치를 찾아 행마다 그 칸의 값(`&str`)을 모은다. 칸이 없는 행은 건너뛰고, 이름이 없으면 빈 `Vec` 을 돌려준다.
5. `to_maps()` 는 행마다 헤더와 값을 짝지은 `HashMap<&str, &str>` 을 만들어 `Vec` 으로 돌려준다.

2단계 — `CsvWriter`
6. `new(headers: Vec<&str>)` 는 헤더를 `String` 으로 바꿔 두고 빈 행 목록으로 시작한다.
7. `add_row(values: Vec<&str>)` 는 값을 `String` 으로 바꿔 한 행을 쌓는다.
8. `to_string()` 은 헤더 줄과 각 행을 쉼표로 이어 줄마다 줄바꿈을 붙인 `String` 을 돌려준다.

3단계 — `Employee`
9. `Employee` 는 `name` · `department`(`String`), `salary`(`f64`), `active`(`bool`) 를 가지며 `Debug` · `Clone` 을 derive 한다.
10. `from_csv_row(row: &[String])` 은 칸이 4개보다 적으면 `Err("필드 부족")` 을 돌려준다.
11. `salary` 파싱에 실패하면 `"salary 파싱 에러: …"` 메시지의 `Err` 를 곧장 돌려준다.
12. `active` 파싱에 실패하면 `false` 로 둔다.
13. `to_csv_row()` 는 네 필드를 쉼표로 이은 한 줄을 돌려준다.

4단계 — `main`
14. `=== CSV 읽기 ===` 아래에 시작 코드의 데이터를 읽어 헤더, 행 수, `name` 컬럼, 행마다의 맵을 찍는다.
15. `=== 구조체로 변환 ===` 아래에 행들을 `Employee` 로 바꿔(실패한 행은 버린다) 하나씩 `{:?}` 로 찍는다.
16. `=== 데이터 분석 ===` 아래에 평균 급여를 소수점 없이 찍고, 부서별로 인원과 평균 급여를 찍고, `활성 직원: 활성/전체` 를 찍는다. 부서별 묶음은 `HashMap` 의 `entry(…).or_default()` 로 만든다.
17. `=== CSV 쓰기 ===` 아래에 `CsvWriter` 로 직원들을 다시 CSV 로 만들어 찍는다(숫자 · 불리언은 `to_string()` 으로 `&str` 에 맞춘다).
18. 마지막에 실제 `csv` 크레이트 사용법을 주석 꼴로 찍는다(시작 코드에 채워 두었다).

**시작 코드**

```rust
// [입출력 & 직렬화] CSV 데이터 처리 — 연습 파일
use std::collections::HashMap;

struct CsvReader {
    // TODO: 헤더와 행 필드
}

impl CsvReader {
    fn from_str(input: &str) -> Self {
        // TODO: 첫 줄 = 헤더, 나머지(빈 줄 제외) = 행. 칸마다 trim
        todo!()
    }

    fn get_column(&self, name: &str) -> Vec<&str> {
        // TODO: 헤더 위치 찾기 → 행마다 그 칸 모으기
        todo!()
    }

    fn to_maps(&self) -> Vec<HashMap<&str, &str>> {
        // TODO: 헤더와 값을 짝지어 맵으로
        todo!()
    }
}

struct CsvWriter {
    // TODO: 헤더와 행 필드
}

impl CsvWriter {
    fn new(headers: Vec<&str>) -> Self {
        // TODO
        todo!()
    }

    fn add_row(&mut self, values: Vec<&str>) {
        // TODO
    }

    fn to_string(&self) -> String {
        // TODO: 헤더 줄 + 각 행, 쉼표로 잇고 줄마다 '\n'
        todo!()
    }
}

// TODO: derive
struct Employee {
    // TODO: name, department, salary, active
}

impl Employee {
    fn from_csv_row(row: &[String]) -> Result<Self, String> {
        // TODO: 칸 수 검증 → salary 는 실패 시 Err, active 는 실패 시 false
        todo!()
    }

    fn to_csv_row(&self) -> String {
        // TODO
        todo!()
    }
}

fn main() {
    println!("=== CSV 읽기 ===");
    let csv_data = "\
name, department, salary, active
Alice, Engineering, 95000.0, true
Bob, Marketing, 72000.0, true
Charlie, Engineering, 88000.0, false
Diana, Marketing, 81000.0, true
Eve, Engineering, 102000.0, true";

    // TODO: 파서 생성 → 헤더 · 행 수 · name 컬럼 · 맵 출력

    println!("\n=== 구조체로 변환 ===");
    // TODO: 실패한 행은 버리고 Employee 목록 만들기 → 출력

    println!("\n=== 데이터 분석 ===");
    // TODO: 평균 급여({:.0}) · 부서별 인원과 평균 · 활성 직원 수

    println!("\n=== CSV 쓰기 ===");
    // TODO: CsvWriter 로 다시 쓰고 출력

    // 아래는 미리 채워 둔 부분이다
    println!("=== 실제 csv 크레이트 ===");
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
    println!("// 헤더 없이:");
    println!("// csv::ReaderBuilder::new().has_headers(false).from_reader(rdr)");
    println!("// 구분자 변경:");
    println!("// csv::ReaderBuilder::new().delimiter(b'\\t').from_reader(rdr)");
}
```

**확인 방법** — `rustc serde-csv.rs && ./serde-csv` 로 돌려, 헤더 네 개와 행 수 5, 직원 다섯 명의 구조체 출력, 평균 급여 · 부서별 두 줄 · 활성 직원 수, 그리고 쉼표 뒤 공백 없는 CSV 가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
