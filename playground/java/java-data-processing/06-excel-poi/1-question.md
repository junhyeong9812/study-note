# java/java-data-processing/06 — Apache POI Excel (엑셀 처리) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 합계 행의 위치와 수식 문자열 (예측)

```java
// 질문용 발췌
Object[][] data = { /* 직원 5명 */ };
int lastDataRow = data.length + 2;
Row summaryRow = sheet.createRow(lastDataRow + 1);
Cell sumCell = summaryRow.createCell(3);
sumCell.setCellFormula("SUM(D4:D" + (lastDataRow + 1) + ")");
```

- `summaryRow` 는 0부터 센 몇 번 행인가?
- `sumCell` 에 들어가는 수식 문자열은 무엇인가?

### 2. 합계 행을 다시 읽으면 (예측)

```java
// 질문용 발췌 — 합계 행에는 열 2("합계:")와 열 3(SUM 수식)만 만들었다
for (int j = 0; j < row.getLastCellNum(); j++) {
    Cell cell = row.getCell(j);
    if (cell == null) { sb.append("null\t"); continue; }
    switch (cell.getCellType()) {
        case STRING -> sb.append(cell.getStringCellValue());
        case NUMERIC -> sb.append((int) cell.getNumericCellValue());
        case FORMULA -> sb.append("[수식:" + cell.getCellFormula() + "]");
        default -> sb.append(cell);
    }
    sb.append("\t");
}
```

- `sb` 가 `"  "` 로 시작했다면, 이 행에서 만들어지는 줄은 무엇인가?

### 3. 「행 수」로 찍히는 값 (예측)

- 원본 `createExcel` 이 만든 시트를 `readExcel` 로 읽으면 `행 수:` 뒤에 어떤 수가 붙나?
- 그 수는 시트에 실제로 존재하는 행의 개수와 같은가?

### 4. 색을 줬는데 배경이 비어 보이는 까닭 (왜)

- `setFillForegroundColor` 로 색을 정했는데 셀 배경이 칠해지지 않는다면 무엇이 빠졌을 가능성이 큰가?

### 5. 스타일을 반복문 밖에서 만드는 까닭 (왜)

- 원본이 `moneyStyle` 을 데이터 반복문 밖에서 한 번 만들고 다섯 셀에 붙이는 이유는 무엇인가?

### 6. SXSSF 로 쓴 지난 행 (경계)

- `new SXSSFWorkbook(100)` 으로 1만 행을 쓴 뒤 0번 행의 셀 값을 고치려 하면 왜 안 되나?

### 7. 큰 파일을 읽는 방법 (경계)

- 수십만 행짜리 xlsx 를 읽을 때 `new XSSFWorkbook(InputStream)` 이 맞지 않은 까닭은 무엇이고, 대신 무엇을 쓰나?

### 8. `autoSizeColumn` 을 믿을 수 있는 범위 (경계)

- 한글 헤더가 있는 열에 `autoSizeColumn` 을 쓰면 무엇이 걱정되고, 더 안전한 방법은 무엇인가?

### 9. 연봉 셀이 `7,500` 으로 보이는데 읽으면 `7500` 인 까닭 (연결)

- 엑셀 화면의 `7,500` 과 `readExcel` 이 읽은 `7500` 이 다른 것은 셀 값과 표시 형식의 어떤 관계 때문인가?

### 10. `try-with-resources` 와 `dispose()` 를 함께 쓰는 까닭 (연결)

- SXSSF 워크북을 `try-with-resources` 로 열었는데도 원본이 `dispose()` 를 따로 부르는 이유는 무엇인가?

## 실습

### 실습 1. 직원 현황 엑셀을 만들고 읽고, 대용량 파일 쓰기

**만들 것** — 스타일 · 병합 · 수식이 들어간 직원 현황 xlsx 를 만들어 저장한 뒤 다시 읽어 콘솔에 찍고, SXSSF 로 1만 행짜리 파일을 쓴 다음 두 파일을 지우는 프로그램.

**준비물** — Apache POI 의 `org.apache.poi:poi-ooxml` 의존성(원본 기준 5.2.5)과 Java 14 이상(화살표 `switch`).

**요구 조건**

1단계 — 스타일 (`createExcel` 안)
1. 제목 · 헤더 스타일의 배경색이 실제로 칠해지도록 채우기 패턴을 단색으로 정한다.
2. 헤더 스타일에 아래쪽 얇은 테두리를 단다.
3. 금액 스타일은 천 단위 구분 표시 형식(`#,##0`)을 쓴다.

2단계 — 시트와 데이터
4. `"직원 목록"` 시트를 만든다.
5. 0번 행 0번 셀에 `"2024년 직원 현황"` 을 넣고 제목 스타일을 붙인 뒤 A1:E1 을 병합한다.
6. 1번 행은 비워 두고, 2번 행에 헤더 5개를 헤더 스타일로 넣는다.
7. 3번 행부터 직원 5명을 넣는다 — 이름 · 부서 · 직급은 문자열, 연봉 · 입사년도는 숫자, 연봉 셀에는 금액 스타일.

3단계 — 수식
8. 마지막 데이터 다음 행의 C열에 `"합계:"`, D열에 연봉 합계 수식을 넣고 금액 스타일을 붙인다.
9. 그다음 행의 C열에 `"평균:"`, D열에 연봉 평균 수식을 넣고 금액 스타일을 붙인다.
10. 수식 범위는 데이터 행 수에서 계산해 만든다.

4단계 — 마무리와 저장
11. 헤더 5열의 너비를 자동 조정한다.
12. 워크북을 파일로 저장하고 `엑셀 생성 완료: <경로>` 를 찍는다.
13. 워크북과 파일 스트림은 `try-with-resources` 로 닫는다.

5단계 — 읽기 (`readExcel`)
14. 파일을 열어 첫 시트의 이름과 `getLastRowNum() + 1` 을 「행 수」로 찍는다.
15. 3번 행부터 마지막 행까지 돌며, 없는 행은 건너뛴다.
16. 각 행의 셀을 `getLastCellNum()` 까지 돌며, 없는 셀은 `null`, 문자열은 그대로, 숫자는 정수로, 수식은 `[수식:...]` 으로 붙이고 탭으로 구분해 두 칸 들여 한 줄로 찍는다.

6단계 — `main`
17. 생성 → 읽기 순서로 부르고, 각 단계 앞에 `=== 엑셀 생성 ===` · `=== 엑셀 읽기 ===` 머리 줄을 찍는다.
18. `=== 대용량 엑셀 (SXSSF) ===` 를 찍고, 창 크기 100 인 SXSSF 워크북의 `"대용량"` 시트에 1만 행(열 0 `"데이터-i"`, 열 1 0~10000 사이 난수)을 써서 `big_data.xlsx` 로 저장한다.
19. 임시 파일을 정리하고 `10,000행 엑셀 생성 완료 (SXSSF 사용)` 을 찍는다.
20. 끝으로 만든 두 파일을 지운다.

**시작 코드**

```java
// 의존성: implementation 'org.apache.poi:poi-ooxml:5.2.5'
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.usermodel.*;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import java.io.*;
import java.util.*;

public class ExcelPoiDemo {

    static void createExcel(String filePath) throws IOException {
        try (XSSFWorkbook workbook = new XSSFWorkbook()) {

            // === 1. 스타일 정의 (꾸밈 값은 채워 둠) ===
            CellStyle titleStyle = workbook.createCellStyle();
            Font titleFont = workbook.createFont();
            titleFont.setBold(true);
            titleFont.setFontHeightInPoints((short) 16);
            titleFont.setColor(IndexedColors.WHITE.getIndex());
            titleStyle.setFont(titleFont);
            titleStyle.setFillForegroundColor(IndexedColors.DARK_BLUE.getIndex());
            // TODO: 배경이 단색으로 칠해지게
            titleStyle.setAlignment(HorizontalAlignment.CENTER);

            CellStyle headerStyle = workbook.createCellStyle();
            Font headerFont = workbook.createFont();
            headerFont.setBold(true);
            headerStyle.setFont(headerFont);
            headerStyle.setFillForegroundColor(IndexedColors.LIGHT_CORNFLOWER_BLUE.getIndex());
            // TODO: 배경이 단색으로 칠해지게
            // TODO: 아래쪽 얇은 테두리

            CellStyle moneyStyle = workbook.createCellStyle();
            // TODO: 천 단위 구분 표시 형식 "#,##0"

            // === 2. 시트 & 데이터 ===
            // TODO: "직원 목록" 시트 만들기
            // TODO: 0번 행 제목 + 제목 스타일 + A1:E1 병합

            String[] headers = {"이름", "부서", "직급", "연봉(만원)", "입사년도"};
            // TODO: 2번 행에 헤더 (헤더 스타일)

            Object[][] data = {
                {"홍길동", "개발팀", "시니어", 7500, 2018},
                {"김영희", "기획팀", "주니어", 4500, 2022},
                {"이철수", "개발팀", "리드", 9000, 2015},
                {"박민수", "디자인팀", "미드", 6000, 2020},
                {"최지은", "개발팀", "주니어", 5000, 2023},
            };
            // TODO: 3번 행부터 데이터 (연봉 셀에 moneyStyle)

            // === 3. 수식 ===
            // TODO: 합계 행 · 평균 행 (범위는 data.length 로 계산)

            // TODO: 헤더 5열 너비 자동 조정

            // === 4. 저장 ===
            // TODO: 파일로 저장하고 "엑셀 생성 완료: " + filePath 찍기
        }
    }

    static void readExcel(String filePath) throws IOException {
        // TODO: 파일을 열어 시트 이름 · 행 수를 찍고
        // TODO: 3번 행부터 셀 종류별로 한 줄씩 찍기
    }

    public static void main(String[] args) throws IOException {
        String filePath = "employees.xlsx";
        // TODO: 생성 → 읽기
        // TODO: SXSSF 로 1만 행 쓰기 → 저장 → 임시 파일 정리
        // TODO: 두 파일 삭제
    }
}
```

**확인 방법** — poi-ooxml 을 의존성에 넣은 Gradle(또는 Maven) 프로젝트에서 `main` 을 돌려 콘솔에 세 머리 줄 · 시트 이름 · 행 수 · 데이터 줄 · 합계 · 평균 줄이 찍히는지 본다. 파일 모양을 엑셀로 확인하려면 마지막 삭제 두 줄을 잠시 주석 처리하고 `employees.xlsx` 를 열어 병합 제목 · 색 배경 · `7,500` 표시 · 합계 값을 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
