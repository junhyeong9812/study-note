# java/java-data-processing/06 — Apache POI Excel (엑셀 처리) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 8번 행, `SUM(D4:D8)`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `lastDataRow = 5 + 2 = 7` 이다.
- `summaryRow` 는 `createRow(7 + 1)`, 곧 0부터 센 8번 행(엑셀 9번째 줄)이다.
- 수식 문자열은 `"SUM(D4:D" + 8 + ")"` = `SUM(D4:D8)` 이다.

**왜 그런가**
- 데이터는 POI 행 3~7 에 있다.
- 수식 안 주소는 엑셀 표기라 1부터 세므로 같은 행이 D4~D8 이 된다.
- `lastDataRow` 는 마지막 데이터의 0부터 센 행 번호(7)이고, `+1` 은 그 행을 엑셀 표기로 바꾼 값이자 그다음 행의 POI 번호다.
- 근거: 2-summary 「동작 방식 (1)」의 행 배치 표와 「동작 방식 (3)」.

### 2. `null` 두 칸 뒤에 「합계:」와 수식

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  null	null	합계:	[수식:SUM(D4:D8)]	
```

(칸 사이는 탭이고, 줄 끝에도 탭이 하나 붙는다.)

**왜 그런가**
- 셀이 열 2 · 3 에만 있으므로 `getLastCellNum()` 은 4 이고, `j` 는 0~3 을 돈다.
- 열 0 · 1 은 만들지 않아 `getCell` 이 `null` → `"null\t"` 이 붙는다.
- 열 2 는 `STRING` → `합계:`.
- 열 3 은 `FORMULA` → `getCellFormula()` 가 `=` 없는 수식 문자열을 돌려주어 `[수식:SUM(D4:D8)]`.
- 근거: 2-summary 「동작 방식 (4)」.

### 3. 10 — 그리고 실제 행 개수(9)와 다르다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 마지막으로 만든 행은 평균 행, 0부터 센 9번 행이다.
- `getLastRowNum()` 은 9, `+1` 해서 `행 수: 10` 이 찍힐 것으로 본다.
- 1번 행은 만들지 않았으므로 실제로 존재하는 행은 9개다 — 같지 않다.

**왜 그런가**
- `getLastRowNum()` 은 개수가 아니라 마지막 행의 번호다.
- 중간에 빈 행이 있으면 「번호 + 1」은 개수가 아니다.
- 원본 주석은 `행 수: 11` 이라고 적지만, 코드에서 읽은 행 배치와 맞지 않는다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나」 10.

### 4. 채우기 패턴 `SOLID_FOREGROUND` 를 빼먹었다

- 배경색은 색(`setFillForegroundColor`)과 「단색으로 칠한다」는 패턴(`setFillPattern(FillPatternType.SOLID_FOREGROUND)`)이 함께 있어야 보인다.
- 색만 고르고 패턴을 정하지 않으면 칠이 되지 않는다.
- 근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나」 1.

### 5. 스타일은 워크북 단위라 셀마다 만들면 메모리가 늘고 개수 제한에 걸린다

- `CellStyle` 은 셀이 아니라 워크북에 쌓인다.
- 셀마다 새로 만들면 메모리가 크게 늘고, 워크북당 스타일 개수 제한(원본 주석: 64,000개)에 닿을 수 있다.
- 같은 꾸밈이면 하나를 만들어 여러 셀에 붙이면 된다.
- 근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나」 2.

### 6. 창 밖으로 밀려나 디스크로 간 행은 고칠 수 없다

- 창 크기 100 이면 메모리에는 최근 100행만 남는다.
- 0번 행은 일찍 디스크 임시 파일로 밀려났으므로 다시 손댈 수 없다.
- 그래서 SXSSF 는 위에서 아래로 한 번에 쓰는 경우에 쓴다.
- 근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나」 8.

### 7. XSSF 는 파일 전체를 메모리에 올리므로, SAX 기반 XSSF Event API 를 쓴다

- `new XSSFWorkbook(InputStream)` 은 xlsx 전체를 메모리에 올린다 — 큰 파일이면 메모리가 모자란다.
- 큰 파일 읽기는 흘려 읽는 SAX 기반의 XSSF Event API 를 쓴다.
- SXSSF 는 쓰기용이라 읽기의 답이 아니다.
- 근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」, 「언제 쓰고 언제 안 쓰나」.

### 8. 한글 글꼴에서 너비가 정확하지 않을 수 있다 — 손수 너비를 정한다

- `autoSizeColumn` 은 한글 글꼴에서 너비를 정확히 맞추지 못할 수 있다.
- `sheet.setColumnWidth` 로 손수 너비를 정하는 편이 더 안전하다.
- 근거: 2-summary 「어디서 틀리나」 9.

### 9. 표시 형식은 모양만 바꾸고 값은 숫자 그대로다

- 금액 스타일의 `#,##0` 은 화면에 보이는 모양만 천 단위 구분으로 바꾼다.
- 셀에 저장된 값은 숫자 `7500` 그대로라, `getNumericCellValue()` 로 읽으면 7500 이 나온다.
- 원본은 이를 `(int)` 로 바꿔 소수점 없이 붙인다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」.

### 10. `close()` 와 별개로 디스크 임시 파일을 지우는 일이 `dispose()` 의 몫이다

- `try-with-resources` 는 블록을 나갈 때 워크북을 닫는다(Java 언어가 보장).
- SXSSF 는 창 밖 행을 디스크 임시 파일에 써 두었고, 원본은 그 파일을 지우는 일을 `dispose()` 로 따로 한다.
- 원본 주석에 따르면 `dispose()` 를 부르지 않으면 임시 파일이 남아 디스크 누수가 생긴다.
- 근거: 2-summary 「동작 방식 (5)」, 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 직원 현황 엑셀을 만들고 읽고, 대용량 파일 쓰기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 배경 단색 채우기 | `titleStyle` · `headerStyle` 의 `setFillPattern(FillPatternType.SOLID_FOREGROUND)` |
| 2. 아래쪽 얇은 테두리 | `headerStyle.setBorderBottom(BorderStyle.THIN)` |
| 3. 천 단위 표시 형식 | `moneyStyle.setDataFormat(workbook.createDataFormat().getFormat("#,##0"))` |
| 4. 시트 만들기 | `workbook.createSheet("직원 목록")` |
| 5. 제목 + 병합 | `titleRow` · `titleCell` · `sheet.addMergedRegion(new CellRangeAddress(0, 0, 0, 4))` |
| 6. 헤더 | `sheet.createRow(2)` 와 `headers` 반복문 |
| 7. 데이터 | `for (int i = 0; i < data.length; i++)` 안의 `createRow(i + 3)` · `salaryCell` |
| 8. 합계 행 | `summaryRow` · `sumCell.setCellFormula("SUM(D4:D" + ...)` |
| 9. 평균 행 | `avgRow` · `avgCell.setCellFormula("AVERAGE(D4:D" + ...)` |
| 10. 범위 계산 | `int lastDataRow = data.length + 2;` |
| 11. 열 너비 | `sheet.autoSizeColumn(i)` 반복문 |
| 12. 저장 + 문구 | `workbook.write(fos)` · `"엑셀 생성 완료: "` |
| 13. 자원 닫기 | `try (XSSFWorkbook workbook = ...)` · `try (FileOutputStream fos = ...)` |
| 14. 시트 이름 · 행 수 | `readExcel` 의 `getSheetName()` · `getLastRowNum() + 1` |
| 15. 행 순회 · 빈 행 건너뛰기 | `for (int i = 3; ...)` · `if (row == null) continue;` |
| 16. 셀 종류별 한 줄 | `getLastCellNum()` 반복문 · `switch (cell.getCellType())` · `StringBuilder("  ")` |
| 17. 생성 → 읽기 | `main` 의 `createExcel(filePath)` · `readExcel(filePath)` 와 머리 줄 |
| 18. SXSSF 1만 행 | `new SXSSFWorkbook(100)` · `createSheet("대용량")` · `for (int i = 0; i < 10000; i++)` · `big_data.xlsx` |
| 19. 임시 파일 정리 | `sxssfWorkbook.dispose()` · 완료 문구 |
| 20. 파일 삭제 | `new File(filePath).delete()` · `new File("big_data.xlsx").delete()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-data-processing/reference/excel-poi.java`

```java
// [데이터 처리 & 유틸] Apache POI Excel (엑셀 처리)
// 설명: Apache POI로 엑셀 파일 읽기/쓰기. XSSF(xlsx), 스타일링, 수식, 대용량 처리(SXSSF)
// 팁: XSSFWorkbook은 xlsx, HSSFWorkbook은 xls 형식이다. 대용량(만 행 이상) 쓰기는 SXSSFWorkbook을 사용하여 메모리 절약한다. 읽기에서 대용량은 SAX 기반의 XSSF Event API를 사용한다. autoSizeColumn은 한글 폰트에서 정확하지 않을 수 있으므로 수동 너비 설정이 더 안전하다.

// === Apache POI: 엑셀 읽기/쓰기 & 스타일링 ===
// 의존성: implementation 'org.apache.poi:poi-ooxml:5.2.5'

// 공통 모델 인터페이스 (Workbook, Sheet, Row, Cell, CellStyle, Font 등)
import org.apache.poi.ss.usermodel.*;
// 셀 병합 영역 정의
import org.apache.poi.ss.util.CellRangeAddress;
// xlsx(2007+) 형식 구현체
import org.apache.poi.xssf.usermodel.*;
// 대용량용 스트리밍 워크북 (메모리 절약)
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
// 파일 입출력
import java.io.*;
// 컬렉션 / 배열 유틸
import java.util.*;

public class ExcelPoiDemo {

    // 엑셀 파일 생성: 스타일 적용 + 데이터 + 수식 작성
    static void createExcel(String filePath) throws IOException {
        // try-with-resources: 워크북도 close() 필요 (네이티브 자원 해제)
        try (XSSFWorkbook workbook = new XSSFWorkbook()) {

            // === 1. 스타일 정의 ===
            // CellStyle은 워크북 단위로 생성 (셀마다 새로 만들면 메모리 폭증)
            // 함정: 워크북당 CellStyle 최대 64,000개 제한 → 재사용 필수
            // 제목 스타일: 굵은 글씨 + 흰색 + 진한 파란 배경 + 가운데 정렬
            CellStyle titleStyle = workbook.createCellStyle();
            Font titleFont = workbook.createFont();
            titleFont.setBold(true);
            titleFont.setFontHeightInPoints((short) 16);
            titleFont.setColor(IndexedColors.WHITE.getIndex());
            titleStyle.setFont(titleFont);
            titleStyle.setFillForegroundColor(IndexedColors.DARK_BLUE.getIndex());
            // SOLID_FOREGROUND: 단색 배경. 색상이 안 보이면 이 옵션을 빼먹은 경우가 많음
            titleStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            titleStyle.setAlignment(HorizontalAlignment.CENTER);

            // 헤더 스타일: 굵은 글씨 + 연한 파란 배경 + 아래 테두리
            CellStyle headerStyle = workbook.createCellStyle();
            Font headerFont = workbook.createFont();
            headerFont.setBold(true);
            headerStyle.setFont(headerFont);
            headerStyle.setFillForegroundColor(IndexedColors.LIGHT_CORNFLOWER_BLUE.getIndex());
            headerStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            headerStyle.setBorderBottom(BorderStyle.THIN);

            // 금액 스타일: 천 단위 구분자 표시 (#,##0)
            CellStyle moneyStyle = workbook.createCellStyle();
            // createDataFormat(): 표시 형식만 변경 (실제 값은 숫자 그대로)
            moneyStyle.setDataFormat(workbook.createDataFormat().getFormat("#,##0"));

            // === 2. 시트 & 데이터 작성 ===
            // 시트 생성 (이름 중복 시 예외)
            XSSFSheet sheet = workbook.createSheet("직원 목록");

            // 제목 행 (행 0)
            Row titleRow = sheet.createRow(0);
            Cell titleCell = titleRow.createCell(0);
            titleCell.setCellValue("2024년 직원 현황");
            titleCell.setCellStyle(titleStyle);
            // 셀 병합: (firstRow, lastRow, firstCol, lastCol) - A1:E1 병합
            sheet.addMergedRegion(new CellRangeAddress(0, 0, 0, 4));

            // 헤더 (행 2 - 행 1은 비워둠)
            String[] headers = {"이름", "부서", "직급", "연봉(만원)", "입사년도"};
            Row headerRow = sheet.createRow(2);
            for (int i = 0; i < headers.length; i++) {
                Cell cell = headerRow.createCell(i);
                cell.setCellValue(headers[i]);
                cell.setCellStyle(headerStyle);
            }

            // 데이터: Object[][]로 다양한 타입 혼합 (String/Integer)
            Object[][] data = {
                {"홍길동", "개발팀", "시니어", 7500, 2018},
                {"김영희", "기획팀", "주니어", 4500, 2022},
                {"이철수", "개발팀", "리드", 9000, 2015},
                {"박민수", "디자인팀", "미드", 6000, 2020},
                {"최지은", "개발팀", "주니어", 5000, 2023},
            };

            // 데이터 행 작성 (행 3부터)
            for (int i = 0; i < data.length; i++) {
                Row row = sheet.createRow(i + 3);
                // setCellValue는 String/Number/Date/Boolean 오버로딩
                row.createCell(0).setCellValue((String) data[i][0]);
                row.createCell(1).setCellValue((String) data[i][1]);
                row.createCell(2).setCellValue((String) data[i][2]);

                // 연봉 셀: 숫자 + 금액 포맷 적용
                Cell salaryCell = row.createCell(3);
                salaryCell.setCellValue((Integer) data[i][3]);
                salaryCell.setCellStyle(moneyStyle);

                row.createCell(4).setCellValue((Integer) data[i][4]);
            }

            // === 3. 수식 추가 ===
            // 엑셀 수식을 문자열로 작성 (실제 계산은 엑셀에서 열 때 수행)
            int lastDataRow = data.length + 2;
            // 합계 행
            Row summaryRow = sheet.createRow(lastDataRow + 1);
            summaryRow.createCell(2).setCellValue("합계:");
            Cell sumCell = summaryRow.createCell(3);
            // setCellFormula: 수식 문자열 (앞에 = 붙이지 않음)
            sumCell.setCellFormula("SUM(D4:D" + (lastDataRow + 1) + ")");
            sumCell.setCellStyle(moneyStyle);

            // 평균 행
            Row avgRow = sheet.createRow(lastDataRow + 2);
            avgRow.createCell(2).setCellValue("평균:");
            Cell avgCell = avgRow.createCell(3);
            avgCell.setCellFormula("AVERAGE(D4:D" + (lastDataRow + 1) + ")");
            avgCell.setCellStyle(moneyStyle);

            // 열 너비 자동 조정 (한글은 부정확할 수 있음 → 함정)
            for (int i = 0; i < headers.length; i++) {
                sheet.autoSizeColumn(i);
            }

            // === 4. 파일 저장 ===
            // FileOutputStream에 워크북을 직렬화
            try (FileOutputStream fos = new FileOutputStream(filePath)) {
                workbook.write(fos);
            }
            System.out.println("엑셀 생성 완료: " + filePath);
        }
    }

    // 엑셀 파일 읽기: 셀 타입에 따라 분기 처리
    static void readExcel(String filePath) throws IOException {
        try (FileInputStream fis = new FileInputStream(filePath);
             // XSSFWorkbook(InputStream): xlsx 전체를 메모리에 로드 (대용량은 부적합)
             XSSFWorkbook workbook = new XSSFWorkbook(fis)) {

            // 첫 번째 시트 가져오기
            XSSFSheet sheet = workbook.getSheetAt(0);
            System.out.println("시트 이름: " + sheet.getSheetName());
            // getLastRowNum: 0-based이므로 +1 해야 행 수
            System.out.println("행 수: " + (sheet.getLastRowNum() + 1));

            // 데이터 행 읽기 (행 3부터, 헤더/제목/공백 제외)
            for (int i = 3; i <= sheet.getLastRowNum(); i++) {
                Row row = sheet.getRow(i);
                // null 체크 필수: 빈 행은 row가 null일 수 있음
                if (row == null) continue;

                StringBuilder sb = new StringBuilder("  ");
                for (int j = 0; j < row.getLastCellNum(); j++) {
                    Cell cell = row.getCell(j);
                    if (cell == null) { sb.append("null\t"); continue; }

                    // CellType별 분기 (switch 표현식, Java 14+)
                    // 함정: NUMERIC은 정수/실수 구분 안 됨 → 직접 캐스팅
                    switch (cell.getCellType()) {
                        case STRING -> sb.append(cell.getStringCellValue());
                        case NUMERIC -> sb.append((int) cell.getNumericCellValue());
                        // FORMULA: 수식 자체. 계산 결과는 cell.getNumericCellValue() 등 별도 호출
                        case FORMULA -> sb.append("[수식:" + cell.getCellFormula() + "]");
                        default -> sb.append(cell);
                    }
                    sb.append("\t");
                }
                System.out.println(sb);
            }
        }
    }

    public static void main(String[] args) throws IOException {
        String filePath = "employees.xlsx";

        // 1. 엑셀 생성
        System.out.println("=== 엑셀 생성 ===");
        createExcel(filePath);

        // 2. 엑셀 읽기
        System.out.println("\n=== 엑셀 읽기 ===");
        readExcel(filePath);

        // 3. 대용량 처리 (SXSSF)
        System.out.println("\n=== 대용량 엑셀 (SXSSF) ===");
        // SXSSFWorkbook: 메모리에 100행만 유지, 나머지는 디스크에 임시 저장
        // 윈도우 크기(여기선 100)를 초과한 행은 더 이상 수정 불가
        try (SXSSFWorkbook sxssfWorkbook = new SXSSFWorkbook(100)) {
            Sheet bigSheet = sxssfWorkbook.createSheet("대용량");
            // 1만 행 생성 (실제로는 메모리에 100행만 보유)
            for (int i = 0; i < 10000; i++) {
                Row row = bigSheet.createRow(i);
                row.createCell(0).setCellValue("데이터-" + i);
                row.createCell(1).setCellValue(Math.random() * 10000);
            }
            try (FileOutputStream fos = new FileOutputStream("big_data.xlsx")) {
                sxssfWorkbook.write(fos);
            }
            // dispose(): 임시 파일(/tmp 등) 정리. 호출하지 않으면 디스크 누수
            sxssfWorkbook.dispose(); // 임시 파일 정리
            System.out.println("10,000행 엑셀 생성 완료 (SXSSF 사용)");
        }

        // 정리: 데모용으로 생성한 파일 삭제
        new File(filePath).delete();
        new File("big_data.xlsx").delete();

        // 출력:
        // === 엑셀 생성 ===
        // 엑셀 생성 완료: employees.xlsx
        //
        // === 엑셀 읽기 ===
        // 시트 이름: 직원 목록
        // 행 수: 11
        //   홍길동  개발팀  시니어  7500  2018
        //   김영희  기획팀  주니어  4500  2022
        //   ...
        //
        // === 대용량 엑셀 (SXSSF) ===
        // 10,000행 엑셀 생성 완료 (SXSSF 사용)
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**
- 스타일 셋은 데이터를 쓰기 전에 워크북에서 한 번 만들고, 셀에는 붙이기만 한다.
- 행 번호는 0부터, 수식 범위는 1부터 — `lastDataRow + 1` 이 두 세계를 잇는다.
- 수식은 `=` 없이 넘기고, 계산은 엑셀이 열 때 한다.
- 읽기는 `null` 행 · 셀을 먼저 거르고 `CellType` 으로 나눈다 — 수식 셀은 `FORMULA` 로 잡힌다.
- 대용량 쓰기는 SXSSF 창 크기로 메모리를 묶고, 끝에 `dispose()` 로 임시 파일을 지운다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
