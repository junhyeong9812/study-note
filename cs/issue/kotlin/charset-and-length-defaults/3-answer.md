# cs/issue/kotlin/charset-and-length-defaults — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `encoding`

## 정답

<!-- 질문 1:1 대응 -->

1. Spring의 `StringHttpMessageConverter`는 문자열 본문을 바이트로 바꿀 때 문자셋을 정해야 하는데, 그 기본값이 (역사적 웹 관례상) **ISO-8859-1**(라틴-1)이다. 한글 "정"은 메모리에서 유니코드 문자지만, 이걸 라틴-1로 인코딩하면 라틴-1에 한글이 없으니 값이 깨진다 — 수신 측 ES가 UTF-8로 읽으려다 `Invalid UTF-8 start byte 0xb7`(0xb7은 UTF-8에서 첫 바이트가 될 수 없는 값)로 거부한다. "문자열 = UTF-8"이 착각인 이유: 문자열은 **추상적 문자의 열**이고, 그것을 어떤 바이트로 만들지는 인코딩이 결정한다. 인코딩을 지정하지 않으면 "정하지 않음"이 아니라 "프레임워크 기본값(여기선 라틴-1)"이 적용된다.
   > **문자 인코딩(character encoding)** — 추상적 문자를 구체적 바이트로 대응시키는 규칙(UTF-8, ISO-8859-1 등). 같은 문자열도 인코딩이 다르면 다른 바이트가 된다.

2. 근본 해법인 이유: 문자열을 넘기면 "문자열 → 바이트" 변환을 **프레임워크의 기본 문자셋**이 하게 되어 제어권을 잃는다. `body.toByteArray()`(코틀린 기본 UTF-8)로 **직접 인코딩한 바이트**를 넘기면, 변환이 이미 우리가 원하는 UTF-8로 끝난 상태라 프레임워크는 그 바이트를 그대로 전송한다 — 기본값이 개입할 여지가 없다. `charset=utf-8` 헤더만 붙이는 것과의 차이: 헤더는 **수신 측에게 "이 바이트를 UTF-8로 읽어라"** 라고 알릴 뿐, **송신 측이 어떤 문자셋으로 바이트를 만들지**는 바꾸지 못한다. 송신이 라틴-1로 깨뜨렸으면 헤더가 UTF-8이어도 이미 깨진 바이트다. 그래서 둘 다 필요하되 핵심은 **송신 인코딩을 바이트 수준에서 직접 고정**하는 것이다.

3. `String.length`가 재는 것은 **UTF-16 코드유닛의 개수**(BMP 문자면 사실상 글자 수)다 — 바이트 수가 아니다. UTF-8에서 한글 한 글자는 **3바이트**이므로, "8192 글자" 버퍼는 실제로 약 24KB다. 상한의 단위는 바이트(8KB)인데 측정을 글자로 하니, 글자 수로는 8192 이하여서 통과하지만 바이트로는 상한을 3배 가까이 초과한다. 즉 **상한을 정의한 단위와 그 상한을 검사하는 단위가 달라서** 검사가 실제로는 아무것도 막지 못했다.
   > **`String.length`(JVM)** — 문자열의 UTF-16 코드유닛 수. ASCII는 1, 대부분의 한글은 1(코드유닛)이지만 UTF-8 바이트로는 3. 바이트 길이와 다르다.

4. 일반 원리: **길이를 요구하는 쪽의 단위와, 그 길이를 재는 쪽의 단위를 일치시켜라.** 바이트로 길이를 요구하는 자리에서 문자 수를 쓰면 값이 어긋난다 — RESP의 `$<len>`은 뒤따르는 벌크 문자열의 **바이트 수**를 선언하므로 여기에 `String.length`(문자 수)를 쓰면 멀티바이트 데이터에서 선언 길이 < 실제 바이트가 되어 프로토콜이 깨진다. HTTP `Content-Length`도 바이트 수라 같은 함정이고, DB `VARCHAR(n)`은 (인코딩·DBMS에 따라) n이 바이트인지 문자인지가 갈려 한글 저장 시 예기치 못한 절단이 난다. 공통 실패 모양: **"글자로 세어 통과했는데 바이트로는 초과/불일치"** → 조용한 절단·파싱 오류·상한 무력화.

5. `core.quotepath=true`(git 기본)는 비ASCII 경로를 사람이 터미널에서 "안전하게" 보도록 `\352\267\270…`(8진수)로 이스케이프해 출력한다. 이걸 그대로 파일 경로로 쓰면 실제 파일명과 달라 "No such file"이 난다. 문자셋 사고와 하나로 묶는 원리는 **"도구·프레임워크의 기본값은 사람 편의를 향한다"** — 라틴 문자셋(과거 웹 호환), 글자 단위 길이(사람이 세는 단위), 이스케이프된 경로(터미널 표시 안전)는 모두 사람에게 편하지만 기계 처리에는 왜곡이다. 도구의 출력을 기계 입력으로 쓸 때는 **"이 출력이 사람용으로 가공됐나, 그 가공을 끄는 옵션이 있나"(`core.quotepath=off` 등)** 부터 확인한다.

6. 반드시 **멀티바이트 문자(여기선 한글, 나아가 이모지 같은 4바이트 문자)** 를 넣는다. ASCII만 썼다면 전부 통과했을 이유: (a) 문자셋 사고 — ASCII는 ISO-8859-1과 UTF-8에서 바이트가 동일해 안 깨진다. (b) 길이 사고 — ASCII는 1글자=1바이트라 `String.length`와 바이트 수가 같아 어긋남이 안 드러난다. (c) quotepath — ASCII 경로는 이스케이프되지 않는다. 즉 **이 세 함정은 정의상 멀티바이트에서만 발현**하므로, 테스트 데이터가 ASCII면 초록불이 거짓 성공 신호가 된다. 그래서 첫 스모크·단위 테스트 데이터에 한글을 심어 둔다(이모지까지 넣으면 surrogate pair 절단도 함께 잡힌다).

## 발생한 문제 / 해결 (추상 원리)

**문제:** JVM·프레임워크·도구의 "사람용 기본값"이 바이트를 왜곡. ① 문자열 본문 전송이 기본 ISO-8859-1로 인코딩돼 한글이 깨짐. ② `String.length`(문자 수)로 바이트 상한을 검사해 상한이 무력화. ③ git이 한글 경로를 8진수 이스케이프해 파일을 못 찾음.

**해결:** ① 문자열을 프레임워크에 맡기지 않고 `toByteArray()`로 UTF-8 바이트를 직접 만들어 전송 + `charset=utf-8` 명시. ② 상한과 측정을 같은 단위(바이트, `toByteArray().size`)로 통일. ③ 기계용 출력을 요구(`git -c core.quotepath=off`). ④ 이 부류는 ASCII로 통과하므로 스모크·테스트 데이터에 멀티바이트 문자를 반드시 포함.

## 문제 구조 (추상화 코드)

### 변형 A — 전송 계층의 기본 문자셋 (문자열 본문을 프레임워크에 맡김)
① 문제 코드
```kotlin
httpClient.post().uri("/_bulk")
    .body(body)                                   // String → 컨버터 기본 문자셋(ISO-8859-1)으로 인코딩
    .retrieve()
```
② 고친 코드
```kotlin
httpClient.post().uri("/_bulk")
    .body(body.toByteArray())                     // UTF-8 바이트를 직접 만든다
    .header("Content-Type", "application/x-ndjson; charset=utf-8")
    .retrieve()
// 같은 클라이언트의 모든 본문 호출에 동일 패턴
```
무엇이 깨졌나: 문자열→바이트 변환을 프레임워크 기본값이 했고, 그 기본값이 UTF-8이 아니었다.

### 변형 B — 파일 I/O의 플랫폼 기본 문자셋
① 문제 코드
```java
try (Writer w = new FileWriter(file)) {           // charset 미지정 → JVM 기본(구버전 JVM은 플랫폼·로케일 의존)
    w.write(json);                                 // JSON escape가 non-ASCII를 그대로 통과 → 인코딩 책임이 Writer로
}
```
② 고친 코드
```java
try (Writer w = new FileWriter(file, StandardCharsets.UTF_8)) {
    w.write(json);
}
// 테스트: 기본 charset이 UTF-8인 CI에선 수정 전후 모두 green
//  → 파일을 raw 바이트로 비교 (UTF-8을 가정하는 readString은 write 버그를 가린다)
```
무엇이 깨졌나: 비UTF-8 기본 인코딩 플랫폼에서 non-ASCII가 mojibake가 되어 설정 매칭이 실패했다.\
같은 구조(기록만, 수정 보류): charset 미지정 `InputStreamReader`로 문서 앞부분을 읽는 형식 감지기가 UTF-16 문서의 `00 3C 00 21`을 1바이트 charset으로 읽어 DOCTYPE을 못 보고 오판 — 수정안은 첫 4바이트/BOM 스니핑(고정 UTF-8은 다른 인코딩 회귀).

### 변형 C — 길이 단위: 상한은 바이트, 측정은 글자
① 문제 코드
```kotlin
const val LIMIT_BYTES = 8 * 1024
if (buffer.length + paragraph.length > LIMIT_BYTES) flush()     // length = UTF-16 코드유닛 수
```
② 고친 코드
```kotlin
val paragraphBytes = paragraph.toByteArray().size               // 상한과 같은 단위(UTF-8 바이트)
if (bufferBytes > 0 && bufferBytes + paragraphBytes > LIMIT_BYTES) flush()
bufferBytes += paragraphBytes + 2
```
무엇이 깨졌나: 한글(UTF-8 3바이트/글자)에서 글자 수 기준 통과가 바이트 기준 상한 초과였다.\
같은 구조: 입력 길이 검사의 바이트 계산이 `escape()` 길이 휴리스틱(한글 2B)에서 UTF-8 인코더(한글 3B)로 바뀌며 같은 `byteLimit`에서 허용 글자 수가 조용히 줄었다 — 프론트 계산 인코딩과 저장 쪽 기준 인코딩의 정합 확인이 필요.
```js
if (escape(ch).length > 4) total += 2;          // Before: 한글 2B
new TextEncoder().encode(value).length           // After:  한글 3B
```

### 변형 D — 분할 경계가 문자 경계가 아님
① 문제 코드
```rust
let title = &line[..80];                          // 바이트 인덱스 → 멀티바이트 문자 중간이면 panic
```
```kotlin
val pieces = text.chunked(size)                   // UTF-16 단위 → surrogate pair(이모지)를 찢을 수 있음
```
② 고친 코드
```rust
let title: String = line.chars().take(MAX).collect();          // 문자(코드포인트) 단위
```
```kotlin
var end = minOf(start + size, text.length)
if (end < text.length && Character.isHighSurrogate(text[end - 1])) end -= 1   // 반쪽이면 한 칸 당김
pieces.add(text.substring(start, end)); start = end
```
무엇이 깨졌나: 자르는 단위(바이트·코드유닛)가 문자 경계를 보장하지 않았다.\
같은 구조 — 바이트 창으로 읽은 조각을 텍스트 판정에 씀:
```rust
// 문제: 3바이트 문자로 시작하는 파일을 2바이트 창으로 읽음 → 완전한 문자 없음 → binary:true
//       max_bytes = 0 → 빈 응답 + truncated → max_bytes로 전진하는 호출자가 무한 루프
// 고친:
const MIN_READ: usize = 4;                        // UTF-8 최대 4바이트 — 한 글자보다 작은 창 금지
let want = req.max_bytes.max(MIN_READ);           // 요청보다 많이 올 수 있다
let chunk = read_until_char_boundary(file, want); // 문자 경계에서 멈춘다(적게 올 수 있다)
// 계약: 호출자는 max_bytes가 아니라 응답의 chunk.bytes로 전진
// UTF-8로 안 풀리면 lossy 대체 대신 binary:true + 내용 없음
```

### 변형 E — 보존해야 할 바이트를 편의용 텍스트 API에 통과시킴
① 문제 코드
```rust
let msg = String::from_utf8_lossy(&out);          // 비UTF-8 메시지 손상
let msg = msg.trim_end_matches('\n').to_string() + "\n";   // 빈 메시지 → "\n", 후행 빈 줄 뭉갬
```
② 고친 코드
```rust
fn message_bytes(id: &str) -> Result<Vec<u8>> {
    let obj = run_bytes(&["cat-file", "commit", id])?;             // 원시 객체 바이트
    match obj.windows(2).position(|w| w == b"\n\n") {             // 헤더 끝 이후가 메시지
        Some(i) => Ok(obj[i + 2..].to_vec()), None => Ok(Vec::new()) }
}
run_io(&["commit-tree", "-F", "-"], Some(&bytes))?;                // stdin도 &[u8] 그대로
// 사용자가 새로 입력한 메시지만 정규화, 기존 메시지는 바이트 그대로
```
무엇이 깨졌나: "그대로 보존"이 계약인 데이터가 trim·lossy 디코딩·정규화로 조용히 바뀌었다.\
같은 구조 — 관대한 디코딩이 판정을 사문화:
```ts
const text = await file.text();                   // 잘못된 UTF-8을 U+FFFD로 치환할 뿐 throw 안 함 → catch 안내 경로 사문화
// 고친:
function decodeStrict(buf: ArrayBuffer): string | null {
  try { return new TextDecoder("utf-8", { fatal: true }).decode(buf); } catch { return null; }
}
```

### 변형 F — 도구의 사람용 출력을 기계 입력으로 씀
① 문제 코드
```kotlin
run("git", "diff", "--name-status", "$prev..$head")    // core.quotepath=true(기본) → 비ASCII 경로를 "\352\267\270…"로
    .lines().map { File(repoDir, it) }                  // No such file
```
② 고친 코드
```kotlin
run("git", "-c", "core.quotepath=off", "diff", "--name-status", "$prev..$head")
// ls-files · show 등 경로를 출력하는 모든 호출에 동일 옵션
```
무엇이 깨졌나: 터미널 표시용 이스케이프가 파일 경로로 재사용됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "코드가 경계에서 인코딩·길이 단위·경계 단위를 직접 못 박는다"이다. 같은 원리(기본값·단위가 값을 조용히 왜곡)에 다른 방안이 쓰인 사례:

### 방안 1 — 저장소별 허용 문자 차이를 적재 직전에 제거
```python
# 문제: errors="ignore"는 '디코딩 불가 바이트'만 버린다 — NUL(U+0000)은 유효한 코드포인트라 통과
text = open(path, encoding="utf-8", errors="ignore").read()
db.insert(text)                                   # 텍스트 컬럼이 NUL을 거부 → INSERT 실패 (검색 엔진 쪽은 허용)
# 고친
text = open(path, encoding="utf-8", errors="ignore").read().replace("\x00", "")
```
디코딩 단계의 방어는 "유효한 문자열"을 보장할 뿐 "저장소가 받는 문자열"을 보장하지 않는다.

### 방안 2 — 클라이언트 세션의 기본값을 접속 옵션으로 명시
```sh
# 문제: DB CLI 클라이언트가 기본 문자셋으로 세션을 열어 utf8mb4 데이터가 변환 손실 → 한글이 '?'
mysql -h <host> -u <user> -p appdb
# 고친
mysql --default-character-set=utf8mb4 -h <host> -u <user> -p appdb
```
```sh
# 같은 구조(연결 문자열 기본값): URI의 경로 DB가 인증 DB(authSource) 기본값이 됨
mongosh "mongodb://<user>@<host>/appdb"            # 사용자는 admin에 정의 → 인증 실패
mongosh "mongodb://<user>@<host>/"  --eval 'db.getSiblingDB("appdb")...'   # 인증은 기본(admin), 대상 DB는 따로 선택
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 코드 경계에서 인코딩·단위 명시 | 변환을 우리 코드가 수행한다 | 호출마다 명시 | 새 호출 경로가 명시를 빠뜨림 | 전송·파일 I/O·길이 상한·분할 |
| 1. 적재 직전 저장소 금지 문자 제거 | 저장소가 유효 문자열 일부를 거부한다 | 데이터 일부(NUL) 손실 | 저장소마다 금지 문자가 달라 누락 | 여러 저장소에 같은 텍스트를 적재 |
| 2. 클라이언트 접속 옵션 명시 | 변환을 클라이언트 세션이 수행한다 | 매 접속 옵션 | 옵션 없는 접속에서 재발(데이터는 멀쩡, 보기만 깨짐) | 운영 조회·CLI 점검 |

**결론**: 변환이 **어디서 일어나는지**가 방안을 고른다.\
우리 코드가 바이트를 만들면 코드에서 못 박고(기본), 저장소가 받는 문자 집합이 더 좁으면 적재 직전에 걸러내고(1), 클라이언트 세션이 변환하면 접속 옵션으로 명시한다(2).\
공통 진단: 조회 결과가 깨져 보일 때 "데이터가 깨졌나, 보는 창(세션 charset)이 깨졌나"부터 가른다.
