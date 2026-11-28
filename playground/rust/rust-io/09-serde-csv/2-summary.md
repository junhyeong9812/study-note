# rust/rust-io/09 — CSV 데이터 처리 — 정리 (힌트)

> 출처 — study-site 항목 `rust/serde-csv`(항목 데이터 `data/rust/io-serde.json`) · 정답 코드 study-practice `rust/rust-io/reference/serde-csv.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**CSV 처리는 「칸 이름이 적힌 출석부를 베껴 적고 다시 정리하는 일」이다.**
출석부의 맨 윗줄에는 「이름 · 부서 · 급여 · 재직」 같은 칸 이름이 있다.
그 아래 한 줄이 한 사람이고, 칸과 칸 사이는 쉼표로 나뉜다.
읽을 때는 맨 윗줄로 칸 이름을 익히고, 나머지 줄을 쉼표에서 잘라 칸마다 값을 얻는다.
쓸 때는 거꾸로 칸 값들을 쉼표로 이어 한 줄을 만든다.
Rust 의 CSV 처리도 똑같은 구조다.

> **CSV** — 쉼표로 값을 나눈 줄들로 표를 적는 텍스트 형식.\
> 예: `name, salary` 아래에 `Alice, 95000.0` 같은 줄이 이어진다.

> **헤더** — CSV 의 첫 줄에 적힌 컬럼(칸) 이름들.\
> 예: `name, department, salary, active`.

| 비유 | 실체 |
|---|---|
| 출석부 맨 윗줄 | `headers: Vec<String>` |
| 사람 한 줄 | `rows` 의 한 원소 `Vec<String>` |
| 쉼표에서 자르기 | `split(',')` |
| 칸 앞뒤 여백 지우기 | `trim()` |
| 한 사람을 카드에 옮겨 적기 | `Employee::from_csv_row` |
| 정리한 줄을 다시 쓰기 | `CsvWriter::to_string` |

```text
"name, salary\nAlice, 95000.0"
        │ lines()            → 줄로 나눈다
        ▼
 ["name, salary", "Alice, 95000.0"]
        │ split(',') + trim()
        ▼
 headers = ["name", "salary"]
 rows    = [["Alice", "95000.0"]]
        │ from_csv_row
        ▼
 Employee { name: "Alice", salary: 95000.0, ... }
```

## 이 주제가 답하려는 질문

1. 쉼표로 나뉜 문자열을 어떻게 헤더와 행으로 나누나?
2. 문자열 칸을 `f64` · `bool` 같은 타입을 가진 구조체로 옮길 때 실패는 어떻게 다루나?
3. 구조체 목록을 다시 CSV 문자열로 쓰려면 무엇을 해야 하나?
4. 실제 `csv` 크레이트는 이 손수 만든 파서와 무엇이 다른가?

## 동작 방식

### (1) 읽기 — 줄로 나누고 쉼표에서 자른다

**언제 쓰나** — 메모리에 올라온 CSV 문자열 전체를 헤더와 행으로 나눌 때 쓴다.

```text
input.lines()
   │
   ├─ next()  → 첫 줄 → split(',') → 각 칸 trim().to_string() → headers
   │            (줄이 하나도 없으면 unwrap_or_default() → 빈 Vec)
   │
   └─ 나머지 줄 → filter(빈 줄 아님) → split(',') → trim → rows
```

- `lines()` 가 입력을 줄 단위 이터레이터로 바꾼다.
- `next()` 로 첫 줄만 꺼내 헤더로 쓴다.
- 입력이 비어 첫 줄이 없으면 `unwrap_or_default()` 가 빈 `Vec` 을 준다.
- 남은 줄 중 `trim()` 했을 때 비어 있는 줄은 `filter` 로 버린다.
- 각 줄을 `split(',')` 로 자르고, 칸마다 `trim()` 으로 앞뒤 공백을 지워 `String` 으로 만든다.

원본 데이터는 `Alice, Engineering` 처럼 쉼표 뒤에 공백이 있다.
`trim()` 이 없으면 헤더가 `" department"` 처럼 공백을 달고 남아 `"department"` 로 찾을 수 없다.

이 파서는 **인용부호와 이스케이프를 지원하지 않는다**(정답 코드 주석이 밝힌 한계다).
값 안에 쉼표가 있으면 그 쉼표에서도 잘려 칸 수가 늘어난다.

예제의 데이터 문자열은 `"\` 로 시작한다.
문자열 리터럴 안에서 줄 끝의 `\` 는 그 줄바꿈을 지우는 이스케이프라, 첫 줄이 바로 `name, …` 로 시작한다.

### (2) 컬럼 뽑기와 행을 맵으로 바꾸기

**언제 쓰나** — 한 컬럼의 값만 모으거나, 각 행을 「헤더 이름 → 값」 으로 찾아보고 싶을 때 쓴다.

```text
get_column("name")
   headers.iter().position(|h| h == "name") ─┬─ Some(0) → 행마다 row.get(0) → ["Alice", "Bob", …]
                                             └─ None    → vec![]

to_maps()
   행마다 headers.iter().zip(row.iter()) → (헤더, 값) 쌍 → HashMap<&str, &str>
```

- `position` 이 헤더에서 이름이 같은 첫 위치를 찾는다.
- 없는 이름이면 `None` 이라 빈 `Vec` 을 돌려준다(패닉하지 않는다).
- 있으면 행마다 `row.get(i)` 로 값을 꺼내는데, `get` 은 칸이 모자라면 `None` 을 주고 `filter_map` 이 그 행을 건너뛴다.
- `to_maps` 는 헤더와 값을 `zip` 으로 짝짓는다.
- `zip` 은 둘 중 짧은 쪽이 끝나면 멈추므로, 값이 모자란 행은 키가 적은 맵이 되고 남는 값은 버려진다.
- 반환 값은 `&str` 을 빌린 것이라 `CsvReader` 보다 오래 살 수 없다.

`HashMap` 은 키의 순서를 지키지 않는다.
그래서 맵을 `{:?}` 로 찍으면 키 순서가 헤더 순서와 다를 수 있다.

### (3) 문자열 행을 구조체로 — 타입을 가진 레코드

**언제 쓰나** — 문자열 칸을 `f64` · `bool` 같은 실제 타입으로 바꿔 계산에 쓸 때 쓴다.

```text
row: &[String]
   │ row.len() < 4 ? ──예──→ Err("필드 부족")
   │ 아니오
   ▼
 name       = row[0].clone()
 department = row[1].clone()
 salary     = row[2].parse::<f64>()  ── 실패 → map_err 로 메시지 → ? 로 즉시 Err 반환
 active     = row[3].parse::<bool>() ── 실패 → unwrap_or(false)
   ▼
 Ok(Employee { … })
```

- 칸이 4개보다 적으면 인덱싱 전에 `Err("필드 부족")` 으로 끝낸다(인덱스 패닉을 막는다).
- `salary` 는 `parse` 실패를 `map_err` 로 `"salary 파싱 에러: …"` 문자열로 바꾸고 `?` 로 곧장 돌려보낸다.
- `active` 는 파싱에 실패해도 에러가 아니고 `false` 가 된다.
- `bool` 의 `parse` 는 `"true"` 와 `"false"` 만 받는다 — `"True"` 나 `"yes"` 는 실패해 `false` 가 된다.
- 두 칸이 실패를 다루는 방식이 다르다: 급여는 「틀리면 거부」, 재직은 「틀리면 기본값」이다.

> **구조체 매핑** — CSV 한 행의 칸들을 구조체의 필드에 하나씩 대응시키는 일.\
> 예: 3번째 칸 `"95000.0"` → `salary: 95000.0`.

`main` 은 행들을 이렇게 모은다:

```rust
let employees: Vec<Employee> = reader.rows.iter()
    .filter_map(|row| Employee::from_csv_row(row).ok())
    .collect();
```

- `.ok()` 가 `Result` 를 `Option` 으로 바꾸면서 `Err` 의 메시지를 버린다.
- 그래서 실패한 행은 **아무 말 없이 빠진다**.

반대 방향인 `to_csv_row` 는 `format!("{},{},{},{}", …)` 로 네 필드를 쉼표로 잇는다.

### (4) 모은 레코드로 분석하기

**언제 쓰나** — 구조체 목록을 합계 · 평균 · 그룹으로 요약할 때 쓴다.

```text
employees ─ map(salary).sum() ─→ 총액 ─ / len() as f64 ─→ 평균 → {:.0} 로 소수점 없이

by_dept: HashMap<&str, Vec<&Employee>>
   for emp: entry(&emp.department).or_default().push(emp)
            (키가 없으면 빈 Vec 을 넣고, 그 Vec 에 push)

filter(|e| e.active).count() ─→ 활성 직원 수
```

- 평균은 `f64` 합을 `len() as f64` 로 나눈다.
- `{:.0}` 은 소수점 아래 0자리로 반올림해 찍는다.
- `entry(…).or_default()` 는 「없으면 기본값(빈 `Vec`)을 넣고, 있든 없든 그 값을 가변 참조로 준다」.
- 그룹 맵도 `HashMap` 이라 부서가 찍히는 순서는 정해져 있지 않다.

원본 데이터의 급여 다섯 개를 손으로 더하면 438000, 평균은 87600 이다(직접 계산한 값 — 실행하지 않음).

### (5) 쓰기 — 칸을 쉼표로 이어 붙인다

**언제 쓰나** — 메모리의 레코드를 CSV 텍스트로 내보낼 때 쓴다.

```text
CsvWriter::new(["name", "salary"])
   add_row(["Alice", "95000"])   ← 값은 모두 &str 로 맞춰 넣는다
   to_string()
      headers.join(",") + "\n"
      각 행 join(",")   + "\n"
   ▼
 "name,salary\nAlice,95000\n"
```

- `new` 는 헤더 `&str` 들을 `String` 으로 바꿔 둔다.
- `add_row` 는 행을 쌓기만 하고 칸 수가 헤더와 같은지 검사하지 않는다(「일치 가정」).
- `to_string` 은 헤더 줄과 각 행을 `join(",")` 으로 잇고 줄마다 `\n` 을 붙인다 — 마지막 줄 뒤에도 `\n` 이 붙는다.
- 쉼표 뒤에 공백을 넣지 않으므로, 읽을 때의 `"name, department"` 와 달리 `"name,department"` 로 나간다.
- 값에 쉼표가 있어도 따옴표로 감싸지 않는다 — 다시 읽으면 칸이 어긋난다.

숫자를 쓸 때는 `emp.salary.to_string()` 을 거친다.
`f64` 를 `{}`(Display)로 바꾸면 소수 부분이 0일 때 `95000.0` 이 아니라 `95000` 이 된다.
반면 `{:?}`(Debug)로 구조체를 찍으면 `95000.0` 으로 나온다.
그래서 읽은 파일과 쓴 파일의 숫자 꼴이 달라진다.

### (6) 실제 `csv` 크레이트 — 같은 일을 라이브러리가 맡는다

**언제 쓰나** — 실제 파일 · 인용부호 · 대용량을 다룰 때는 손수 만든 파서 대신 크레이트를 쓴다.

원본이 밝힌 의존성은 `csv = "1"` 과 `serde = { version = "1", features = ["derive"] }` 다.

```text
읽기  csv::Reader::from_path("data.csv")?
        └ rdr.deserialize()  → 레코드마다 Result<Employee, _>  → result? 로 꺼냄
쓰기  csv::Writer::from_path("output.csv")?
        └ wtr.serialize(Employee { … })?  → wtr.flush()?
설정  csv::ReaderBuilder::new()
        ├ .has_headers(false)   헤더 없는 파일
        └ .delimiter(b'\t')     탭 구분 등 다른 구분자
```

- `csv` 크레이트는 `serde` 와 통합되어 있어 행을 구조체로 **직접 역직렬화**한다 — 손수 쓴 `from_csv_row` 가 하던 매핑과 파싱을 맡는다.
- `deserialize()` 는 레코드를 하나씩 내주는 반복이라, 대용량 CSV 를 레코드 단위로 **스트리밍** 처리할 수 있다.
- 손수 만든 `CsvReader` 는 `from_str` 에서 모든 행을 `rows` 에 올린 뒤에야 쓸 수 있다.
- `ReaderBuilder` 로 구분자 · 헤더 유무 · 인용부호 등을 바꿀 수 있다.
- `Writer` 는 마지막에 `flush()` 로 쌓인 내용을 내보낸다.

> **역직렬화** — 텍스트(바이트) 꼴의 데이터를 프로그램의 값(구조체 등)으로 되살리는 일.\
> 예: CSV 한 행 → `Employee` 값.

> **스트리밍** — 전체를 메모리에 올리지 않고 한 덩이씩 읽으며 처리하는 방식.\
> 예: `for result in rdr.deserialize()` 로 레코드를 하나씩 다룬다.

## 문법 — 형태와 규칙

```rust
fn split_line(line: &str) -> Vec<String> {
    line.split(',').map(|s| s.trim().to_string()).collect()
}

fn main() {
    let text = "a, b\n1, x\n\n2, y";
    let mut lines = text.lines();
    let headers = lines.next().map(split_line).unwrap_or_default();
    let rows: Vec<Vec<String>> = lines
        .filter(|l| !l.trim().is_empty())
        .map(split_line)
        .collect();
    let n: Result<f64, _> = rows[0][0].parse();
    let flag: bool = "nope".parse().unwrap_or(false);
    println!("{:?} {} {:?} {}", headers, rows.len(), n, flag);
}
```

- `str::lines()` — 줄 단위 이터레이터.
- `str::split(',')` — 구분자에서 자르는 이터레이터. 구분자 자체는 결과에 없다.
- `str::trim()` — 앞뒤 공백을 지운 `&str`.
- `Option::unwrap_or_default()` — `None` 이면 타입의 기본값(`Vec` 이면 빈 `Vec`).
- `str::parse::<T>()` — `Result<T, _>` 를 돌려준다. 타입은 변수 선언이나 구조체 필드로 정해진다.
- `Result::map_err(f)` — 에러 값만 바꾼다. 뒤에 `?` 를 붙이면 `Err` 일 때 함수가 곧장 그 에러를 돌려준다.
- `Result::unwrap_or(v)` — `Err` 면 `v` 를 쓴다.
- `Result::ok()` — `Result` → `Option`, 에러 내용은 버린다.
- `iter.zip(other)` — 두 이터레이터를 짝짓고 짧은 쪽에서 멈춘다.
- `HashMap::entry(k).or_default()` — 없으면 기본값을 넣고 가변 참조를 준다.
- `slice.join(",")` — 문자열 조각들을 구분자로 이어 하나의 `String` 으로.
- `{:.0}` — 소수점 0자리로 찍는 서식.

## 어디서 틀리나

### 1. `trim()` 을 빼먹는다
`"a, b"` 를 `split(',')` 만 하면 두 번째 칸이 `" b"` 다.
헤더 이름으로 찾는 `get_column("b")` 가 `position` 에서 `None` 을 받아 빈 `Vec` 을 돌려준다 — 에러 없이 조용히 빈다.

### 2. 값 안의 쉼표 · 인용부호
이 파서는 인용부호를 모른다.
`"Seoul, Korea"` 같은 값은 두 칸으로 갈라지고 따옴표도 값에 남는다.
쓰기도 마찬가지로 쉼표가 든 값을 감싸지 않는다.
실제 데이터에는 인용부호를 처리하는 `csv` 크레이트를 쓴다 — `ReaderBuilder` 로 인용부호 설정도 바꿀 수 있다.

### 3. `.ok()` 로 실패한 행이 소리 없이 사라진다
`filter_map(|row| … .ok())` 는 급여가 깨진 행을 그냥 버린다.
결과 개수가 줄어도 왜 줄었는지 알 수 없다.
몇 행이 버려졌는지 세거나 에러를 따로 모으는 편이 안전하다.

### 4. `bool` 파싱은 대소문자를 가린다
`"True"` · `"TRUE"` · `"1"` 은 `bool` 로 파싱되지 않는다.
`unwrap_or(false)` 가 붙어 있어 이것도 에러 없이 `false` 가 된다 — 재직 중인 사람이 비재직으로 집계될 수 있다.

### 5. 숫자를 썼다 다시 읽으면 꼴이 바뀐다
`95000.0` 을 `to_string()` 하면 `95000` 이다.
`f64` 로 다시 파싱하면 같은 값이지만, 문자열로 비교하거나 사람이 볼 때는 다르다.

### 6. `HashMap` 출력 순서를 믿는다
`to_maps` 의 맵과 부서별 그룹 출력은 순서가 정해져 있지 않다.
순서가 필요하면 정렬하거나 순서를 지키는 자료구조를 쓴다.

### 7. 큰 파일을 통째로 올린다
`CsvReader::from_str` 은 입력 전체와 모든 행을 메모리에 둔다.
대용량 CSV 는 레코드 단위로 스트리밍 처리한다 — `csv` 크레이트의 `deserialize()` 반복이 그 방식이다.

### 8. 손으로 매핑하는 코드를 늘 새로 쓴다
`from_csv_row` 처럼 칸 번호로 필드를 채우는 코드는 컬럼 순서가 바뀌면 깨진다.
`csv` 크레이트는 `serde` 와 통합되어 구조체를 직접 역직렬화할 수 있으니, 매핑을 손으로 쓸 까닭이 줄어든다.

### 9. 헤더와 칸 수가 다른 행
`add_row` 는 칸 수를 검사하지 않고, `to_maps` 의 `zip` 은 남는 칸을 버린다.
어느 쪽도 에러를 내지 않으므로 칸 수 검증은 호출하는 쪽의 몫이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `HashMap` 순회 · 출력 순서는 정해져 있지 않다 | 표준 라이브러리 — 순서를 **보장하지 않는다**는 것이 보장이다. 실제 순서는 구현과 실행에 따라 다르다 |
| `bool` 의 `parse` 는 `"true"` · `"false"` 만 받는다 | 표준 라이브러리 `FromStr for bool` 의 동작 |
| `f64` 의 Display 는 `95000.0` 을 `95000` 으로, Debug 는 `95000.0` 으로 찍는다 | 표준 라이브러리의 서식 구현 (정확한 규칙이 문서로 보장되는 범위는 확인 필요) |
| `zip` 은 짧은 쪽에서 멈춘다 | 표준 라이브러리 `Iterator::zip` 의 정의 |
| 인용부호 · 이스케이프를 지원하지 않는다 | 이 예제 `CsvReader` · `CsvWriter` 구현의 한계 — CSV 형식이나 `csv` 크레이트의 성질이 아니다 |
| `csv` 크레이트의 `Reader` · `Writer` · `ReaderBuilder` API | `csv` 크레이트(원본은 버전 `"1"` 을 적었다) — 언어가 아니라 크레이트가 정한다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 쉼표 · 따옴표가 없는 작은 문자열을 빨리 쪼개 보기 | `lines()` + `split(',')` + `trim()` | 의존성을 늘리는 크레이트 |
| 실제 CSV 파일(값 안의 쉼표 · 인용부호) | `csv` 크레이트 | 손수 만든 `split(',')` 파서 |
| 행을 타입을 가진 구조체로 | `csv` + `serde` 의 역직렬화 | 칸 번호에 기대는 손 매핑 |
| 대용량 파일 | 레코드 단위 스트리밍(`deserialize()` 반복) | 전체를 `Vec` 에 올리는 `from_str` |
| 탭 구분 · 헤더 없는 파일 | `ReaderBuilder` 의 `delimiter` · `has_headers` | 구분자를 하드코딩한 파서 |
| 깨진 행을 놓치면 안 될 때 | 에러를 모으거나 세기 | `.ok()` 로 버리기 |

## 핵심 문장

1. **CSV 읽기는 「첫 줄 = 헤더, 나머지 = 행, 쉼표에서 자르고 공백 지우기」다.**
2. **구조체 매핑은 문자열 칸을 타입으로 파싱하는 일이고, 칸마다 실패를 거부할지 기본값으로 채울지 정해야 한다.**
3. **쓰기는 칸을 쉼표로 잇는 일이지만, 인용부호 처리 없이는 값 안의 쉼표가 표를 깨뜨린다.**
4. **실제 `csv` 크레이트는 `serde` 로 구조체를 직접 역직렬화하고, 레코드 단위로 스트리밍하며, `ReaderBuilder` 로 형식을 바꾼다.**

## 관련 자료

- `serde-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `file-read-write` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [bufread-bufwrite](../02-bufread-bufwrite/2-summary.md)
- 원본: study-site 항목 데이터 `data/rust/io-serde.json` 의 `serde-csv`

## 용어 풀이

- **CSV** — 쉼표로 값을 나눈 줄들로 표를 적는 텍스트 형식.
- **헤더** — CSV 첫 줄의 컬럼 이름들.
- **레코드 · 행** — 헤더 아래 한 줄, 곧 데이터 한 건.
- **구분자** — 칸을 나누는 문자. 기본은 쉼표, 탭 등으로 바꿀 수 있다.
- **인용부호** — 쉼표 등이 든 값을 하나의 칸으로 묶는 따옴표.
- **구조체 매핑** — 행의 칸을 구조체 필드에 대응시키는 일.
- **역직렬화** — 텍스트 데이터를 프로그램의 값으로 되살리는 일.
- **직렬화** — 프로그램의 값을 텍스트(바이트)로 내보내는 일.
- **스트리밍** — 전체를 올리지 않고 한 덩이씩 읽으며 처리하는 방식.
- **`serde`** — Rust 의 직렬화 · 역직렬화 틀. `derive` 기능으로 구조체에 그 능력을 붙인다.
- **`ReaderBuilder`** — `csv` 크레이트에서 구분자 · 헤더 유무 · 인용부호 등을 정해 `Reader` 를 만드는 빌더.
- **Display / Debug** — `{}` 와 `{:?}` 서식이 쓰는 두 출력 방식.

## 더 들어가면

- `rdr.deserialize()` 로 `Employee` 를 받으려면 구조체에 `#[derive(serde::Deserialize)]`, `wtr.serialize` 에는 `#[derive(serde::Serialize)]` 가 붙어야 한다 — 예제의 `Employee` 는 `Debug, Clone` 만 derive 해서 그대로는 크레이트와 쓸 수 없다 (확인 필요).
- `csv` 크레이트는 헤더 이름과 구조체 필드 이름을 맞춰 매핑하는 것으로 알려져 있어, 컬럼 순서가 바뀌어도 견딘다 (확인 필요).
- 문자열 칸의 앞뒤 공백을 자동으로 지우는 `trim` 설정이 `ReaderBuilder` 에 있다고 알려져 있다 (확인 필요).
- 인용부호를 쓰는 CSV 관례는 RFC 4180 으로 정리되어 있으며, 값 안의 따옴표는 두 번 겹쳐 적는다 (확인 필요).
- 예제의 `to_csv_row` 는 `main` 에서 쓰이지 않아 컴파일러가 쓰이지 않는 코드 경고를 낼 수 있다 (확인 필요).
- `CsvWriter` 의 메서드 이름 `to_string` 은 `Display` 를 구현해서 얻는 `ToString::to_string` 과 이름만 같은 고유 메서드다 — `impl Display` 로 바꾸면 `{}` 로 바로 찍을 수 있다 (확인 필요).
