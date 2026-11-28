# java/java-data-processing/06 — Apache POI Excel (엑셀 처리) — 정리 (힌트)

> 출처 — study-site 항목 `java/excel-poi`(항목 데이터 `data/java/data-processing.json`) · 정답 코드 study-practice `java/java-data-processing/reference/excel-poi.java`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**Apache POI 로 엑셀을 다루는 일은 「모눈종이 공책을 코드로 채우는 일」이다.**
공책(워크북)을 펴고, 장(시트)을 만들고, 줄(행)을 긋고, 칸(셀)에 글씨를 쓴다.
글씨체 · 칸 색칠 같은 꾸밈은 공책 앞에 붙인 「도장 모음」(셀 스타일)에서 골라 찍는다.
도장은 칸마다 새로 파지 않고, 한 번 파 둔 것을 여러 칸에 찍는다.
POI 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 공책 한 권 | `Workbook` (`XSSFWorkbook` · `SXSSFWorkbook`) |
| 공책의 한 장 | `Sheet` |
| 한 줄 | `Row` |
| 한 칸 | `Cell` |
| 도장 | `CellStyle` (+ `Font` · 표시 형식) |
| 여러 칸을 하나로 합친 칸 | 병합 영역 `CellRangeAddress` |
| 칸에 적은 계산식 | 수식 `setCellFormula` |
| 공책을 봉투에 넣어 보내기 | `workbook.write(출력 스트림)` |

```text
Workbook ─┬─ CellStyle 들 (워크북에 한 번 만들고 재사용)
          └─ Sheet "직원 목록"
               ├─ Row 0 ─ Cell 0 ... Cell 4
               ├─ Row 2 ─ Cell 0 ... Cell 4
               └─ ...
```

## 이 주제가 답하려는 질문

1. 코드로 xlsx 파일을 만들고 꾸미고(스타일 · 병합 · 수식) 저장하려면 어떤 순서로 무엇을 부르나?
2. 만든 파일을 다시 읽을 때 행 · 셀이 비어 있거나 셀 종류가 다르면 어떻게 다루나?
3. 만 행이 넘는 큰 파일은 메모리를 아끼려면 어떻게 쓰고 읽나?

## 동작 방식

### (1) 워크북 → 시트 → 행 → 셀 차례로 만들기

**언제 쓰나** — 엑셀 파일을 새로 만들 때 언제나.
셀은 행 없이 못 만들고, 행은 시트 없이 못 만든다.

```text
new XSSFWorkbook()
   │ createSheet("직원 목록")
   ▼
Sheet ── createRow(2) ──► Row(2) ── createCell(0) ──► Cell ── setCellValue("이름")
                                                        └─ setCellStyle(headerStyle)
결과: 엑셀에서 3번째 줄 A열에 "이름"
```

- `createSheet(이름)` 은 시트를 만든다.
  같은 이름의 시트가 이미 있으면 예외가 난다.
- `createRow(n)` · `createCell(n)` 의 번호는 **0부터 센다**.
  그래서 `createRow(2)` 는 엑셀 화면의 3번째 줄이다.
- `setCellValue` 는 문자열 · 숫자 · 날짜 · 불리언을 받도록 오버로딩되어 있다.
  원본은 `Object[][]` 에 문자열과 정수를 섞어 두고, `(String)` · `(Integer)` 로 꺼내 넣는다.
- 원본 예제의 행 배치는 이렇다.

```text
행 번호(0부터) │ 엑셀 줄 │ 내용
──────────────┼────────┼─────────────────────────────
0             │ 1      │ 제목 "2024년 직원 현황" (A~E 병합)
1             │ 2      │ (만들지 않음 — 빈 줄)
2             │ 3      │ 헤더: 이름 · 부서 · 직급 · 연봉(만원) · 입사년도
3 ~ 7         │ 4 ~ 8  │ 직원 5명 데이터
8             │ 9      │ C열 "합계:"  D열 SUM 수식
9             │ 10     │ C열 "평균:"  D열 AVERAGE 수식
```

- 표의 1번 행은 `createRow(1)` 을 부르지 않아 시트에 존재하지 않는다.
  읽을 때 이런 행은 `null` 로 돌아온다 — (4) 에서 다룬다.

> **워크북(Workbook)** — 엑셀 파일 하나에 대응하는 객체.\
> 예: `new XSSFWorkbook()` 은 빈 xlsx 파일 하나를 메모리에 만든다.

### (2) 스타일은 워크북에 만들고 셀에 붙인다

**언제 쓰나** — 굵은 글씨 · 배경색 · 테두리 · 정렬 · 숫자 표시 형식을 줄 때.

```text
workbook.createCellStyle() ──► CellStyle titleStyle
workbook.createFont()      ──► Font titleFont (굵게 · 16pt · 흰색)
titleStyle.setFont(titleFont)
titleStyle.setFillForegroundColor(DARK_BLUE)
titleStyle.setFillPattern(SOLID_FOREGROUND)   ← 이것이 있어야 색이 칠해진다
titleStyle.setAlignment(CENTER)
          │
          ▼
titleCell.setCellStyle(titleStyle)  → 제목 칸이 진한 파랑 바탕에 흰 굵은 글씨
```

- 스타일과 글꼴은 셀이 아니라 **워크북**의 메서드(`createCellStyle` · `createFont`)로 만든다.
  셀에는 만든 스타일을 `setCellStyle` 로 붙이기만 한다.
- 셀마다 새 스타일을 만들면 메모리가 크게 늘고, 워크북당 `CellStyle` 은 최대 64,000개라는 제한(원본 주석의 주장)에도 걸린다.
  그래서 스타일은 미리 몇 개 만들어 두고 **재사용**한다.
- 배경색은 `setFillForegroundColor` 로 색을 고르고 `setFillPattern(FillPatternType.SOLID_FOREGROUND)` 로 「단색으로 칠한다」를 정해야 보인다.
  색이 안 보이면 패턴을 빼먹은 경우가 많다.
- 색은 `IndexedColors.WHITE.getIndex()` 처럼 미리 정해진 색 번호로 고른다.
- 헤더 스타일은 `setBorderBottom(BorderStyle.THIN)` 으로 아래쪽에 얇은 테두리를 단다.
- 금액 스타일은 `workbook.createDataFormat().getFormat("#,##0")` 로 천 단위 구분 표시 형식을 단다.
  **표시 형식은 보이는 모양만 바꾼다** — 셀에 든 값은 숫자 `7500` 그대로다.
  엑셀 화면에는 `7,500` 으로 보인다.

> **셀 스타일(CellStyle)** — 글꼴 · 배경 · 테두리 · 정렬 · 표시 형식을 묶은 꾸밈 묶음.\
> 예: `headerStyle` 하나를 헤더 다섯 칸에 모두 붙인다.

> **표시 형식(data format)** — 값을 화면에 어떤 모양으로 보일지 정한 규칙.\
> 예: `#,##0` 은 `7500` 을 `7,500` 으로 보이게 한다.

### (3) 셀 병합과 수식

**언제 쓰나** — 제목을 여러 열에 걸쳐 놓을 때, 합계 · 평균을 엑셀이 계산하게 할 때.

```text
sheet.addMergedRegion(new CellRangeAddress(0, 0, 0, 4))
          (첫 행, 끝 행, 첫 열, 끝 열) — 모두 0부터
          → A1:E1 이 한 칸이 된다

lastDataRow = data.length + 2 = 7
summaryRow  = createRow(lastDataRow + 1)          → 0부터 센 8번 행
수식 문자열  = "SUM(D4:D" + (lastDataRow + 1) + ")"
                    → 엑셀이 열 때 D4~D8 을 더한다
```

- `CellRangeAddress` 의 네 인자는 (첫 행, 끝 행, 첫 열, 끝 열) 순서이고 모두 0부터 센다.
- 병합해도 값은 왼쪽 위 칸(여기선 행 0 · 열 0)에 넣는다.
- `setCellFormula` 에는 **앞에 `=` 를 붙이지 않은** 수식 문자열을 준다.
- 수식 안의 셀 주소(`D4` 등)는 엑셀 표기라 **1부터 센다**.
  POI 행 번호 3~7 이 엑셀 줄 4~8 이 되는 까닭이다.
  POI 의 0부터 세기와 수식의 1부터 세기를 섞을 때 한 칸씩 어긋나는 실수가 잦다.
- 원본 주석은 「실제 계산은 엑셀에서 열 때 수행」이라고 적는다.
  즉 POI 는 수식 문자열을 적어 둘 뿐이다.

> **수식 셀** — 값 대신 계산식을 담은 셀.\
> 예: `SUM(D4:D8)` 을 담은 합계 칸.

### (4) 저장하고 다시 읽기

**언제 쓰나** — 만든 워크북을 파일로 남길 때, 기존 xlsx 를 읽어 처리할 때.

```text
[저장] try (FileOutputStream fos = ...) { workbook.write(fos); }

[읽기] new XSSFWorkbook(fis)          ← 파일 전체를 메모리에 올린다
        getSheetAt(0)                 ← 첫 시트
        getLastRowNum()               ← 마지막 행의 번호(0부터) → 9
        for i = 3 .. 9:
           row = getRow(i)            ← 없는 행이면 null → 건너뜀
           for j = 0 .. getLastCellNum()-1:
              cell = getCell(j)       ← 없는 셀이면 null → "null" 붙임
              switch getCellType():
                 STRING  → 문자열
                 NUMERIC → (int) 로 잘라 숫자
                 FORMULA → "[수식:" + 수식 문자열 + "]"
```

- 워크북과 스트림은 모두 `try-with-resources` 로 연다.
  원본 주석은 워크북도 `close()` 해야 자원이 풀린다고 적는다.
- `XSSFWorkbook(InputStream)` 은 xlsx 전체를 메모리에 올린다.
  그래서 큰 파일 읽기에는 맞지 않다.
- `getLastRowNum()` 은 마지막 행의 **번호**(0부터)다.
  원본은 여기에 `+1` 을 해 「행 수」로 찍는다.
  중간에 빈 행이 있으면 이 값은 실제로 존재하는 행의 개수와 다르다.
- `getLastCellNum()` 은 그 행의 마지막 셀 번호에 1을 더한 값이다.
  그래서 `j < row.getLastCellNum()` 으로 돌면 마지막 셀까지 돈다.
  합계 행처럼 열 2 · 3 에만 셀이 있으면 4 가 되고, 열 0 · 1 은 `null` 로 돌아온다.
- `getRow` · `getCell` 은 만들지 않은 자리에 `null` 을 돌려준다 — 확인 없이 쓰면 `NullPointerException` 이다.
- `getCellType()` 은 셀 종류를 돌려준다.
  수식 셀은 계산 결과가 숫자여도 `FORMULA` 다.
  `getCellFormula()` 는 수식 문자열을 돌려준다.
- `NUMERIC` 은 정수와 실수를 가르지 않는다 — 값은 `double` 로 나온다.
  원본은 `(int)` 로 직접 잘라서 `7500` 처럼 찍는다.
- 원본의 분기는 `case STRING -> ...` 꼴의 화살표 `switch` 다(원본 주석: Java 14+).

> **셀 종류(CellType)** — 셀에 든 것이 문자열 · 숫자 · 수식 · 빈칸 등 무엇인지 나타내는 열거형.\
> 예: 연봉 칸은 `NUMERIC`, 합계 칸은 `FORMULA`.

### (5) 대용량 — 쓰기는 SXSSF, 읽기는 Event API

**언제 쓰나** — 만 행 이상의 파일을 쓰거나 읽을 때.

```text
new SXSSFWorkbook(100)    ← 창(window) 크기 100
   createRow(0) ... createRow(99)    메모리에 100행
   createRow(100)  → 가장 오래된 행이 디스크 임시 파일로 밀려난다
   ...
   createRow(9999) → 메모리에는 늘 최근 100행만
write(fos)        → 임시 파일 + 메모리 행을 합쳐 xlsx 로
dispose()         → 임시 파일 삭제 (안 하면 디스크에 남는다)
```

- `SXSSFWorkbook(100)` 은 최근 100행만 메모리에 두고 나머지는 디스크 임시 파일로 보낸다.
- 창 밖으로 밀려난 행은 **더 이상 고칠 수 없다**.
  그래서 SXSSF 는 위에서 아래로 한 번에 쭉 쓰는 경우에 맞다.
- 다 쓴 뒤 `dispose()` 를 불러 임시 파일(`/tmp` 등)을 지운다.
  부르지 않으면 디스크에 찌꺼기가 쌓인다(원본 주석: 「디스크 누수」).
- 큰 파일을 **읽을** 때는 SXSSF 가 아니라 SAX 기반의 XSSF Event API 를 쓴다.
  파일 전체를 올리지 않고 흘려 읽는 방식이다.
- 원본은 시트 `"대용량"` 에 1만 행(`"데이터-i"` 문자열, `Math.random() * 10000` 숫자)을 써서 `big_data.xlsx` 로 저장한다.

> **창 크기(window size)** — SXSSF 가 메모리에 붙잡아 두는 최근 행의 수.\
> 예: `new SXSSFWorkbook(100)` 은 100행.

## 문법 — 형태와 규칙

```java
// 의존성: implementation 'org.apache.poi:poi-ooxml:5.2.5'
try (XSSFWorkbook wb = new XSSFWorkbook()) {
    CellStyle bold = wb.createCellStyle();
    Font f = wb.createFont();
    f.setBold(true);
    bold.setFont(f);

    Sheet sh = wb.createSheet("점수");
    Row r = sh.createRow(0);                 // 엑셀 1행
    Cell c = r.createCell(0);                // A열
    c.setCellValue("합");
    c.setCellStyle(bold);
    r.createCell(1).setCellFormula("SUM(C1:E1)");   // = 없이

    try (FileOutputStream out = new FileOutputStream("a.xlsx")) {
        wb.write(out);
    }
}
```

- 의존성은 `org.apache.poi:poi-ooxml` 이다(원본 기준 버전 5.2.5).
- 공통 인터페이스(`Workbook` · `Sheet` · `Row` · `Cell` · `CellStyle` · `Font`)는 `org.apache.poi.ss.usermodel` 에 있다.
- 형식별 구현:

| 클래스 | 형식 · 용도 |
|---|---|
| `XSSFWorkbook` | xlsx (2007 이후 형식) |
| `HSSFWorkbook` | xls (옛 형식) |
| `SXSSFWorkbook` | xlsx 대용량 쓰기 (스트리밍) |
| XSSF Event API | xlsx 대용량 읽기 (SAX 기반) |

- 행 · 열 번호는 0부터, 수식 안 주소는 1부터 센다.
- 스타일 · 글꼴 · 표시 형식은 워크북에서 만든다.
- 배경색은 색 + `SOLID_FOREGROUND` 패턴을 함께 준다.
- 워크북 · 스트림은 `try-with-resources` 로 닫는다.
- 열 너비는 `sheet.autoSizeColumn(열)` 로 내용에 맞춘다.

## 어디서 틀리나

### 1. 배경색을 줬는데 안 보인다
`setFillForegroundColor` 만 부르고 `setFillPattern(SOLID_FOREGROUND)` 를 빼먹으면 칠이 되지 않는다.

### 2. 셀마다 스타일을 새로 만든다
반복문 안에서 `createCellStyle()` 을 부르면 메모리가 늘고 워크북당 스타일 개수 제한(원본 주석: 64,000개)에 걸린다.
스타일은 반복문 밖에서 만들어 재사용한다.

### 3. 0부터 세기와 1부터 세기를 섞는다
`createRow(3)` 은 엑셀 4번째 줄이다.
수식 `SUM(D4:D8)` 의 범위는 엑셀 표기(1부터)로 적는다.
한 칸 어긋나면 합계에서 첫 행이나 끝 행이 빠진다.

### 4. 수식에 `=` 를 붙인다
`setCellFormula` 에는 `=` 없이 `SUM(...)` 만 넘긴다.

### 5. 읽을 때 `null` 을 확인하지 않는다
만들지 않은 행 · 셀은 `getRow` · `getCell` 이 `null` 을 돌려준다.
원본은 빈 행은 `continue`, 빈 셀은 `"null"` 을 붙이고 넘어간다.

### 6. 숫자 셀을 정수로 기대한다
`NUMERIC` 은 정수 · 실수를 가르지 않고 `double` 로 준다.
정수가 필요하면 직접 바꾼다.
`(int)` 캐스팅은 소수점 아래를 버리므로 실수 데이터에는 맞지 않다.

### 7. 큰 파일에 XSSF 를 쓴다
`XSSFWorkbook` 은 전체를 메모리에 둔다.
만 행 이상 쓰기는 `SXSSFWorkbook`, 읽기는 XSSF Event API 를 쓴다.
xls 와 xlsx 를 헷갈려 `HSSFWorkbook` 으로 xlsx 를 다루려 해서도 안 된다.

### 8. SXSSF 에서 지난 행을 고치려 한다 · `dispose()` 를 잊는다
창 밖으로 밀려난 행은 고칠 수 없다.
다 쓴 뒤 `dispose()` 를 부르지 않으면 임시 파일이 남는다.

### 9. `autoSizeColumn` 을 믿는다
한글 글꼴에서는 너비가 정확하지 않을 수 있다.
`sheet.setColumnWidth` 로 손수 너비를 정하는 편이 더 안전하다.

### 10. 원본의 「행 수: 11」 주석
원본은 실행 결과 주석에 `행 수: 11` 이라고 적는다.
그런데 원본 코드가 만드는 마지막 행은 평균 행, 곧 0부터 센 9번 행이다.
`getLastRowNum() + 1` 은 10 이 되어야 한다(원본에 근거 없음 — 추론).
또 1번 행은 만들지 않았으므로 실제로 존재하는 행은 9개다.
`getLastRowNum() + 1` 을 「행 수」라 부르는 것 자체가 빈 행이 있으면 맞지 않는다.

### 11. 수식 셀의 계산 결과
원본 주석은 「계산 결과는 `cell.getNumericCellValue()` 등 별도 호출」이라고 적는다.
그러나 같은 원본이 「실제 계산은 엑셀에서 열 때 수행」이라고도 적는다.
POI 로 만들고 엑셀로 열지 않은 파일이라면 계산된 값이 들어 있지 않을 수 있다(확인 필요).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `try-with-resources` 가 블록을 나갈 때 자원을 닫는다 | Java 언어 명세 |
| `case STRING -> ...` 화살표 `switch` | Java 언어(원본 주석: Java 14+) |
| 행 · 셀 번호가 0부터 | POI 라이브러리 API |
| 수식 안 주소가 1부터, `#,##0` 표시 형식 | 엑셀(스프레드시트) 표기 규칙 |
| 수식은 엑셀이 열 때 계산된다 | 엑셀 프로그램의 동작(원본 주석) |
| 워크북당 `CellStyle` 64,000개 제한 | xlsx 형식 · 엑셀의 제한(원본 주석 — 확인 필요) |
| SXSSF 가 창 밖 행을 임시 파일로 보낸다 · 위치가 `/tmp` 등 | POI 구현 + 운영체제 임시 폴더 |
| `autoSizeColumn` 의 한글 너비가 부정확할 수 있다 | POI 구현과 실행 환경의 글꼴(확인 필요) |
| `poi-ooxml:5.2.5` | 원본이 고른 버전 — 다른 버전의 동작은 확인 필요 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 수천 행 이하 xlsx 를 꾸며서 만든다 | `XSSFWorkbook` | `HSSFWorkbook`(xls 용) |
| 옛 xls 파일을 다룬다 | `HSSFWorkbook` | `XSSFWorkbook` |
| 만 행 이상을 위에서 아래로 쓴다 | `SXSSFWorkbook` + `dispose()` | `XSSFWorkbook`(메모리 부담) |
| 만 행 이상을 읽는다 | XSSF Event API(SAX) | `new XSSFWorkbook(InputStream)` |
| 같은 꾸밈을 여러 칸에 | 미리 만든 `CellStyle` 재사용 | 칸마다 `createCellStyle()` |
| 합계 · 평균을 엑셀에서 갱신되게 | `setCellFormula` | 자바에서 계산한 값만 넣기 |
| 한글 열 너비 | `setColumnWidth` 로 손수 | `autoSizeColumn` 만 믿기 |

## 핵심 문장

1. **워크북 → 시트 → 행 → 셀 순서로 만들고, 행 · 셀 번호는 0부터 센다** — 수식 안 주소만 1부터다.
2. **스타일은 워크북에서 한 번 만들어 여러 셀에 붙인다** — 배경색은 `SOLID_FOREGROUND` 패턴이 있어야 보인다.
3. **표시 형식과 수식은 엑셀이 보여 주고 계산한다** — POI 는 값과 수식 문자열을 적을 뿐이다.
4. **읽을 때는 `null` 행 · 셀과 셀 종류를 확인한다** — `NUMERIC` 은 정수 · 실수를 가르지 않는다.
5. **대용량은 쓰기 SXSSF(창 + 임시 파일 + `dispose`), 읽기 Event API** — XSSF 는 전체를 메모리에 둔다.

## 관련 자료

- [csv-opencsv](../05-csv-opencsv/2-summary.md)
- `batch-processing` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [template-engine](../07-template-engine/2-summary.md)
- 원본: study-site 항목 데이터 `data/java/data-processing.json` 의 `excel-poi`

## 용어 풀이

- **Apache POI** — 자바에서 MS 오피스 파일을 읽고 쓰는 라이브러리.
- **워크북(Workbook)** — 엑셀 파일 하나에 대응하는 객체.
- **시트(Sheet)** — 워크북 안의 한 장.
- **행(Row) · 셀(Cell)** — 시트의 한 줄 · 한 칸.
- **XSSF** — xlsx 형식을 다루는 POI 구현.
- **HSSF** — xls 형식을 다루는 POI 구현.
- **SXSSF** — xlsx 를 창 크기만큼만 메모리에 두고 흘려 쓰는 구현.
- **XSSF Event API** — xlsx 를 SAX 방식으로 흘려 읽는 API.
- **SAX** — 문서를 처음부터 차례로 훑으며 만나는 요소마다 처리하는 XML 읽기 방식.
- **셀 스타일(CellStyle)** — 글꼴 · 배경 · 테두리 · 정렬 · 표시 형식의 묶음.
- **채우기 패턴(FillPatternType)** — 배경을 어떤 무늬로 칠할지. `SOLID_FOREGROUND` 는 단색.
- **표시 형식(data format)** — 값을 보이는 모양의 규칙(`#,##0` 등).
- **병합 영역(CellRangeAddress)** — 여러 칸을 하나로 합칠 범위.
- **수식 셀** — 계산식을 담은 셀.
- **셀 종류(CellType)** — `STRING` · `NUMERIC` · `FORMULA` 등 셀 내용의 종류.
- **창 크기(window size)** — SXSSF 가 메모리에 두는 최근 행 수.
- **`dispose()`** — SXSSF 의 임시 파일을 지우는 메서드.
- **try-with-resources** — 블록을 나갈 때 선언한 자원을 자동으로 닫는 자바 구문.

## 더 들어가면

- 수식 결과를 자바 안에서 얻으려면 `FormulaEvaluator`(`workbook.getCreationHelper().createFormulaEvaluator()`)로 계산시키는 방법이 있다(확인 필요).
- 수식 셀이 마지막으로 계산된 값의 종류는 `getCachedFormulaResultType()` 으로 볼 수 있다(확인 필요).
- 표시 형식을 적용한 「화면에 보이는 글자」를 얻으려면 `DataFormatter.formatCellValue(cell)` 을 쓴다(확인 필요).
- 숫자 셀이 날짜인지는 `DateUtil.isCellDateFormatted(cell)` 로 가린다 — 엑셀 날짜도 내부적으로는 숫자다(확인 필요).
- 실제로 존재하는 행의 개수는 `sheet.getPhysicalNumberOfRows()` 로 얻는다(확인 필요).
- `autoSizeColumn` 은 기본적으로 병합된 셀을 계산에서 빼며, 글꼴 정보가 없는 서버 환경에서는 문제가 날 수 있다(확인 필요).
- `setColumnWidth` 의 단위는 글자 폭의 1/256 이다(확인 필요).
- SXSSF 의 임시 파일 압축은 `setCompressTempFiles(true)` 로 켤 수 있다(확인 필요).
- POI 버전에 따라 `SXSSFWorkbook.close()` 가 임시 파일을 지우는지가 다를 수 있다 — `dispose()` 를 명시적으로 부르는 편이 안전하다(확인 필요).
