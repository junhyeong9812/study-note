# database/35-bulk-file-import-export — 정답

## 정답

### 1. split과 RFC 4180

- `"서울, 강남구"`가 두 열로 쪼개져 오른쪽 열이 밀린다. 로컬 재현(예시): `'1,홍길동,"서울, 강남구",x'.split(',')` → 5칸.
- 따옴표 안의 줄바꿈 때문에 한 레코드가 두 "줄"로 나뉜다. 줄 단위로 읽으면 열 개수가 맞지 않는다.
- 규칙
  - 쉼표·따옴표·줄바꿈을 품은 필드는 `"`로 감싸야 한다(should).
  - 감싼 필드 안의 `"`는 `""`로 적어야 한다(must).
  - 레코드는 CRLF로 끝난다. 따옴표 안의 CRLF는 데이터다(ABNF `escaped`).
- RFC 4180은 **Informational**이다. 공식 명세가 없는 상황에서 대부분의 구현이 따르는 듯한 형식을 기록한 문서다.

### 2. 상태 기계

```text
  START ── " ──> QUOTED ── " ──> QUOTE ── " ──> QUOTED  ("" = 문자 ")
    │                                    ├─ , → 필드 끝 → START
    └─ 그 밖 ──> UNQUOTED                 └─ \n → 레코드 끝 → START
                   ├─ , → 필드 끝 → START
                   └─ \n → 레코드 끝 → START
  QUOTED 안에서는 , 와 \n 도 데이터
```

- 상태는 넷(START, UNQUOTED, QUOTED, QUOTE)이다.
- 따옴표 안에서 파일이 끝나면 "닫히지 않은 따옴표" 오류다(로컬 재현: `line 1: unterminated quote`). 필드 길이 상한이 없으면 그 전에 파일 끝까지를 한 필드로 쌓는다.

### 3. CP949를 UTF-8로

| 읽는 방법 | 반응 |
|---|---|
| Java `Files.readAllLines(p, UTF_8)` | `MalformedInputException: Input length = 1`(엄격) |
| Java `new String(bytes, UTF_8)` | 예외 없이 `ȫ�浿`처럼 �로 치환(관대) |
| PostgreSQL `COPY` | `ERROR: invalid byte sequence for encoding "UTF8": 0xb1`, 적재 0행 |

- 모두 로컬 재현 결과다.
- 가장 위험한 것은 **관대 디코더**다. 에러 없이 저장되고, �로 바뀐 원래 바이트는 되찾을 수 없다. `Charset.decode`·`new String`은 항상 치환한다(Charset 문서). `CharsetDecoder`에 `CodingErrorAction.REPORT`를 걸어 예외로 받는다.

### 4. 똠, CP949, EUC-KR

- 똠은 CP949 확장 영역(`8C 63`)이다. EUC-KR(KS X 1001 완성형)에는 없다. 로컬 재현(예시)
  - Java 8 `EUC-KR` → `MalformedInputException`
  - PostgreSQL `ENCODING 'EUC_KR'` → `invalid byte sequence for encoding "EUC_KR": 0x8c 0x63`
  - MySQL 8.4 `CHARACTER SET euckr` → 정상으로 읽혔다
- 관계: CP949(UHC)는 EUC-KR의 확장이다. EUC-KR 바이트는 CP949로 읽어도 같다. 그 반대는 성립하지 않는다.
- WHATWG의 `euc-kr` 레이블(`ks_c_5601-1987`·`windows-949` 포함)은 인덱스가 "KS X 1001 + UHC = Windows Codepage 949"다. 즉 사실상 CP949다.
- PostgreSQL에서는 `ENCODING 'UHC'`(별칭 `WIN949`)를 쓴다. `'CP949'`라는 이름은 인식되지 않았다(로컬 재현). Java에서는 `MS949`(또는 `x-windows-949`)다.

### 5. BOM 두 얼굴

- 공통 원인: UTF-8 BOM(`EF BB BF`, U+FEFF).
- 엑셀: BOM이 있는 UTF-8 CSV는 그냥 열리고, 없으면 가져오기 기능으로 열어야 한다(Microsoft 지원 문서).
  - 대처: 사람용 내보내기에 BOM을 붙인다.
- 서버: 많은 디코더가 BOM을 지우지 않아 첫 필드가 `﻿id`·`﻿1`이 된다. 로컬 재현
  - PostgreSQL `HEADER MATCH` → `got "﻿id", expected "id"`
  - 헤더 없는 파일 → `invalid input syntax for type bigint: "﻿1"`
  - MySQL → ERROR 1366
  - Java `readAllLines` 첫 줄이 U+FEFF로 시작
  - 대처: 파서 입구에서 첫 문자 U+FEFF를 지운다. WHATWG `decode`·Node `TextDecoder('utf-8')`는 기본으로 지운다. `Buffer.toString`은 남겼다.

### 6. 네 가지 적재 결과 (로컬 재현)

| 방법 | 결과 |
|---|---|
| PostgreSQL 17 COPY 기본 | `invalid input syntax for type bigint: "X"` → **0행** |
| PostgreSQL 17 `ON_ERROR ignore` | "X" 행은 건너뜀(NOTICE). 그러나 `4,d,e`에서 `missing data for column "memo"` → **0행**. 형 변환 오류만 건너뛴다 |
| MySQL 8.4 strict | `ERROR 1366 Incorrect integer value: 'X'` → **0행** |
| MySQL 8.4 `IGNORE` | **4행 적재.** `'X'` → `id = 0`, 빠진 열 → 그 열의 기본값(`memo`는 `NULL`). 경고 1366·1261만 남는다 |

- 마지막이 가장 위험하다. 형 변환·열 개수 오류는 "건너뛰기"가 아니라 값을 바꿔 넣는다(PRIMARY KEY·UNIQUE 중복 행은 버린다). `LOAD DATA LOCAL`도 `REPLACE`가 없으면 `IGNORE`처럼 동작한다(MySQL 8.4 LOAD DATA 문서).

### 7. 10행 실패를 알리는 가져오기

- 화면: "성공 29,990 / 실패 10"과 오류 파일(줄 번호·열·값·사유). 전부 되돌릴지, 좋은 행만 넣을지, 검증만 할지 정책을 명시한다.
- 단계
  1. 인코딩: BOM·제공자가 밝힌 인코딩 우선. 없으면 엄격 UTF-8 시도, 실패 시 CP949. 엄격 UTF-8 성공이 UTF-8을 증명하지는 않으니(CP949 `C8 AB`도 유효한 UTF-8) 미리보기·사용자 확인을 둔다.
  2. 파싱: 상태 기계, 필드·행 상한, 헤더 이름 검증(BOM 제거 후). 오류 위치는 레코드 시작 줄로 보고한다.
  3. 검증: 형·필수·범위·중복을 행마다 확인해 오류 목록에 쌓는다.
  4. 정책: 전부/좋은 행만/검증만.
  5. 적재: 배치 트랜잭션, 업로드 ID로 멱등. 끝나면 파일 행 수와 적재 행 수를 대조한다.

### 8. OOM

- 의심: `readAllBytes`·`readAllLines`·"모든 행을 List에 모아 검증 후 저장". `readAllBytes`는 배열을 못 잡으면 `OutOfMemoryError`라고 Files 문서에 적혀 있다.
- 스트리밍으로도 폭주하는 입력: **닫히지 않은 따옴표**. 파서가 파일 끝까지를 한 필드로 쌓는다. 한 줄이 비정상적으로 긴 파일도 같다.
- 막기
  - 필드·행 길이 상한을 둔다. 로컬 재현의 파서는 `maxField`를 넘으면 `field too long`을 던진다.
  - 업로드 크기 상한을 둔다.
  - 1000행 단위 배치로 DB에 흘려보낸다.

### 9. CSV 수식 주입

- CSV 인용은 "어디까지가 한 필드인가"의 구분 규칙일 뿐이다. 스프레드시트는 인용을 벗긴 셀 값이 `=`로 시작하면 수식으로 해석한다.
  - 로컬 재현: PostgreSQL `COPY TO`가 `"=HYPERLINK(""…"")"`를 그대로 내보냈다. `-2+3`은 인용도 안 됐다.
- 위험 시작 문자(OWASP): `=` `+` `-` `@` 탭(0x09) CR(0x0D) LF(0x0A), 일부 로캘의 전각 `＝＋－＠`.
  - 구분자·따옴표로 새 셀을 시작해 셀 머리에 위험 문자를 올리는 경우도 고려한다.
- 완화: 필드를 따옴표로 감싸고, 앞에 `'`를 붙이고, `"`를 `""`로 이스케이프한다.
- 한계
  - 엑셀은 저장 후 다시 열면 이 이스케이프를 지울 수 있다. OWASP는 엑셀용으로 따옴표 안 탭 접두를 적지만 탭이 데이터에 남는다.
  - "모든 스프레드시트·모든 후속 소비자에게 안전한 방법은 없다"(OWASP). 사람용과 기계용 내보내기를 나눈다.
