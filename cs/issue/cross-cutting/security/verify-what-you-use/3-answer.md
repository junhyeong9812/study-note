# cs/issue/security/verify-what-you-use — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `parser-differential`

## 정답
<!-- 질문 1:1 대응 -->

1. **파서 차이.** 같은 바이트열을 두 파서가 서로 다른 구조로 읽는 현상이다.\
관대한 JSON 언마샬은 모르는 필드를 **버리고**, 중복 키는 **뒤엣것**을 취한다.\
검증기가 이렇게 읽으면 "검증기에는 안 보이는 필드"나 "검증기가 본 값과 다른 두 번째 값"을 소비자는 그대로 쓸 수 있다 — 무시된 필드는 곧 무시된 결박이다.\
base64 디코더가 개행을 건너뛰는 것, YAML의 `"\x24"` 같은 이스케이프를 원문 바이트 스캔이 못 보는 것, null이 빈 문자열로 디코드돼 부재와 구별되지 않는 것도 같은 구조다.
   > **parser differential** — 검증 측과 사용 측 파서의 해석 차이. 한쪽을 속이는 입력을 만드는 대표적 공격 표면.

2. **관대한 정규화의 fail-open.** 정규화는 여러 표기를 하나로 "접는" 연산이다.\
보안 모드 값에서 `" AUDIT "`는 계약상 **거부(기동 실패)** 해야 할 오타·변형인데, `trim().lowercase()`가 이를 정상값 `audit`으로 접어 **느슨한 모드로 기동**시켰다 — 무서명 요청이 200으로 통과했다.\
보안에 영향을 주는 설정값은 원문 그대로 **정확 비교**(대소문자 구분·공백 불허)하고, 공백뿐인 키는 빈 값으로 거부한다.\
정규화를 되돌리면 모드 테스트가 실패하는지(뮤테이션)로 이 방어가 실제로 물리는지 확인한다.

3. **계층 간 정규화 불일치.** 인가 필터가 "원문 경로"로 `/internal/**` 여부를 판정하고 라우터는 `%2e%2e`·중복 슬래시를 정규화한 뒤 컨트롤러를 고르면, 필터에는 "내부 경로 아님"으로 보이고 라우터에는 내부 컨트롤러로 가는 요청이 생긴다 — **인가 우회**다.\
필터는 라우터와 **같은 출처의 정규화된 경로**로 판정하고 `..`·인코딩 변형 테스트를 둔다.\
서명도 같다: 서명자가 디코드된 경로로, 검증자가 원문(raw) 경로로 canonical 문자열을 만들면 인코딩 문자가 든 경로에서 서명이 어긋난다(원 기록: 당시 고정 ASCII 경로라 실버그는 없었고 리뷰에서 계약 위반으로 잡음) — 경로 표현을 한 가지로 계약하고(원문 경로), 서명자→검증자 방향의 **고정 테스트 벡터**로 교차 검증한다.
   > **canonical form** — 서명·비교를 위해 약속한 단 하나의 표현. 양쪽이 같은 규칙으로 만들어야 한다.

4. **문자열 검사 vs 실제 hop.** URL 문자열이 `https://`여도 서버가 302로 `http://`나 다른 호스트로 보내면 HTTP 클라이언트는 **기본적으로 따라간다**.\
검사한 것은 첫 URL 문자열이고, 실제로 통신한 것은 리다이렉트 이후의 hop이다.\
그래서 리다이렉트 훅에서 **매 hop의 scheme**을 검사한다.\
1차 수정이 주입받은 클라이언트의 기존 리다이렉트 훅을 **덮어써서** 호출자가 걸어 둔 정책(예: "리다이렉트 전면 금지")을 지워 버렸다 — 새 fail-open이다.\
훅은 교체가 아니라 **합성**한다: 우리 검사를 먼저 하고, 기존 훅이 있으면 이어서 호출한다.\
기존 훅이 없던 경우도 "정책 없음"이 아니라 **기본 정책**(Go는 10회 초과 리다이렉트 중단)이었으므로 그것까지 보존하고, 공유 클라이언트 필드를 직접 바꾸면 다른 호출자에게도 번지므로 복사본에 건다.

5. **재검증은 창을 좁힐 뿐.** 파일 **경로**를 다시 여는 한, 마지막 검증과 실제 사용 사이의 변경을 원리적으로 배제할 수 없다 — 재검증 시점을 늦추면 창이 짧아질 뿐이다.\
해결은 "검증한 그 바이트"를 사용하는 것이다: 검증한 내용을 해시 이름 파일로 **O_EXCL 생성 후 재해시**해 굳히고, 실행(내리기 포함)에는 그 **불변 스냅샷**(격리 디렉터리·0600·fsync·재대조·사용 후 삭제)을 넘긴다.\
재사용 시 링크가 아닌 일반 파일인지(lstat) 확인하고, 스냅샷이 없을 때 "호스트의 원본 파일로 대신 실행"하던 폴백은 명시적 opt-in + 경고로만 남긴다.
   > **TOCTOU** — time-of-check to time-of-use. 검사와 사용 사이에 대상이 바뀌어 검사가 무의미해지는 경쟁.

6. **개행 두 함정 + 삭제식 정규화.** `id=$(printf 'abc\n')`는 후행 개행을 **벗긴 값**을 돌려준다 — 검증을 셸 쪽 값으로 하면 원본(`abc\n`)이 아니라 가공본(`abc`)을 검증한 셈이다.\
또 `^[A-Za-z0-9-]+$`의 `$`는 많은 정규식 엔진(Python `re`·Perl·PCRE 계열 등)에서 "끝 **또는 마지막 개행 앞**"이라 `abc\n`도 통과한다 — 절대 끝 앵커(`\z`, Python은 `\Z` 또는 `fullmatch`)로 **원본**을 검증해야 한다.\
(엔진마다 다르다 — POSIX ERE(bash `=~` 등)의 `$`는 문자열 끝만, Ruby의 `$`는 모든 줄 끝에 매칭된다. 쓰는 엔진의 앵커 의미를 확인한다.)\
불량 문자를 지워서 쓰는 정규화(`tr -cd 'A-Za-z0-9_-'`)는 `a.b`와 `ab`처럼 **다른 입력을 같은 이름으로 충돌**시킨다 — 불량 입력은 지우지 말고 거부한다.

7. **한 번 읽기 + 표시=대상.** 파일을 두 번 읽어 한 번은 해시, 한 번은 내용을 만들면 그 사이 변경·개행 처리 차이로 **식별자와 내용이 다른 것**을 가리킬 수 있다 — 한 번 읽은 버퍼에서 둘 다 만들고, 발행 전 "디코드==원본·재해시 일치"를 스스로 단언한다.\
배포할 정의도 워크플로가 도는 브랜치가 아니라 **배포 대상 커밋**에서 가져와야 "배포한 커밋"과 "실행한 정의"가 같다.\
승인 화면도 같은 원리다: 사람의 승인은 화면에 보인 정보에 대한 검증이므로, 화면의 대상이 실제 실행 대상과 다르면 **승인이 다른 것에 대해 이뤄진다**(아래 방안 3).

## 문제 구조 (추상화 코드)

### 변형 A — 관대한 정규화가 거부값을 허용값으로 접음
① 문제 코드
```kotlin
fun parseMode(raw: String): Mode = when (raw.trim().lowercase()) {   // " AUDIT " → "audit"
    "enforce" -> Mode.ENFORCE
    "audit"   -> Mode.AUDIT          // 계약상 기동 거부여야 할 값이 느슨한 모드로
    else      -> error("invalid mode")
}
```
② 고친 코드
```kotlin
fun parseMode(raw: String): Mode = when (raw) {    // 원문 정확 비교 (대소문자·공백 불허)
    "enforce" -> Mode.ENFORCE
    "audit"   -> Mode.AUDIT
    else      -> error("invalid mode")             // 기동 실패
}
require(key.isNotBlank())                          // 공백뿐인 키 거부
// 뮤테이션: trim 을 되돌리면 모드 테스트가 FAIL 하는지 확인
```
무엇이 깨졌나: 검증 전 가공이 "틀린 입력"을 "맞는 입력"으로 바꿔, 엄격 계약이 조용히 완화됐다.

### 변형 B — 인가 계층과 라우팅 계층·서명자와 검증자의 경로 해석 차이
① 문제 코드
```kotlin
// 인가 필터: 원문 URI 로 판정
if (request.uri.rawPath.startsWith("/internal/")) verifySignature(request)
// 라우터: 정규화된 경로로 컨트롤러 선택 → "/x/%2e%2e/internal/routes" 가 내부 컨트롤러로
```
```go
// 서명자: 디코드된 경로 / 검증자: raw 경로 → canonical 불일치
canonical := method + "\n" + req.URL.Path + "\n" + bodyDigest + "\n" + ts
```
② 고친 코드
```kotlin
val path = exchange.request.path.pathWithinApplication().value()   // 라우터 매칭과 같은 경로 출처
if (path.startsWith("/internal/")) verifySignature(request)
// 라우터가 인코딩·`..`·중복 슬래시를 실제로 어떻게 다루는지는 프레임워크·버전·방화벽 설정마다 다르다 —
// 가정하지 말고 변형 요청 테스트로 두 계층의 판정이 같은지 확인
// 테스트: "..", "%2e%2e", 중복 슬래시 변형이 모두 인가를 거치는지
```
```go
canonical := method + "\n" + req.URL.EscapedPath() + "\n" + bodyDigest + "\n" + ts  // 원문 경로로 통일
// EscapedPath 는 RawPath 가 Path 의 유효한 인코딩일 때만 원문을, 아니면 재인코딩 값을 준다 — 양쪽이 같은 함수를 쓰는 것이 핵심
// 서명자 산출 hex 를 검증자가 통과시키는 고정 벡터(golden vector) 교차 테스트
```
무엇이 깨졌나: 같은 요청을 판정 계층과 사용 계층이 다른 문자열로 봤다(필터-라우터 쪽은 설계 확인 라운드에서 막은 형태 — 실사고 아님).

### 변형 C — 파서 차이 (관대한 JSON·base64·이스케이프 전 원문 검사)
① 문제 코드
```go
var m Manifest
json.Unmarshal(body, &m)                 // 미지 필드 무시·중복 키 last-wins
raw, _ := base64.StdEncoding.DecodeString(m.Content)   // 개행을 건너뜀
if bytes.Contains(raw, []byte("$")) { reject() }       // YAML "\x24" 는 원문에 '$' 없음
```
② 고친 코드
```go
dec := json.NewDecoder(bytes.NewReader(body))
dec.DisallowUnknownFields()                  // 중복 키 검출은 표준 라이브러리에 없어 별도 구현, null·빈 값·부분 조합 → 422
if err := dec.Decode(&m); err != nil { reject() }
raw, err := base64.StdEncoding.Strict().DecodeString(m.Content)   // Strict 도 CR·LF 는 여전히 무시한다
if err != nil || base64.StdEncoding.EncodeToString(raw) != m.Content { reject() }  // 왕복 동일성이 개행·변형을 잡는다
var doc yaml.Node
yaml.Unmarshal(raw, &doc)                    // Node 직접 순회: 문서 1개, 앵커·별칭·병합 키·중복 키 거절
walkScalars(&doc, func(v string) {           // 디코드 후 값(소비자가 볼 문자열)에서 '$' 금지
    if strings.Contains(v, "$") && !isAllowedExact(v) { reject() }
})
```
무엇이 깨졌나: 검증기는 관대한 해석으로, 소비자는 다른 해석으로 같은 입력을 읽었다.

### 변형 D — 검증과 사용 사이의 재열람 (TOCTOU)
① 문제 코드
```go
validate(readFile(hostPath))       // 배포 시작 시 검증
// ... 수 분 뒤 (드레인 후)
runDown(hostPath)                  // 같은 경로를 다시 열어 사용, 존재(Stat)만 확인
// 기록이 없으면 호스트 파일로 대신 실행하는 폴백
```
② 고친 코드
```go
name := "def.sha256-" + fullHex(sha256(validated)) + ".yml"
writeExcl(dir, name, validated, 0o600)              // O_EXCL 생성 → fsync → 재해시 대조
snap := snapshotFor(down, validated)                // 격리 tmp·O_EXCL·0600·재대조, 사용 후 삭제
fi, err := os.Lstat(snap); if err != nil || !fi.Mode().IsRegular() { reject() }   // 링크 거절(오류도 거절)
runDown(snap)
// 폴백은 명시적 opt-in + WARN, 작업 디렉터리 0700·상위 링크 금지
```
무엇이 깨졌나: 경로를 다시 여는 한 "검증한 것"과 "쓰는 것"이 같다는 보장이 없었다.

### 변형 E — 식별자와 내용을 다른 읽기·다른 시점에서 산출
① 문제 코드
```python
revision = sha256(open(path, "rb").read())
content  = b64encode(open(path, "rb").read())      # 두 번째 읽기 — 같은 바이트라는 보장 없음
# 배포 정의는 워크플로 브랜치에서 checkout, 배포 대상은 특정 커밋
# 정의 안의 기본값 문법 ${IMAGE:-latest} → 주입 실패 시 조용히 latest
```
② 고친 코드
```python
with open(path, "rb") as f:
    raw = f.read()                                  # 한 번 읽기
revision = "sha256:" + sha256(raw).hexdigest()
content  = b64encode(raw)
assert b64decode(content) == raw and sha256(b64decode(content)).hexdigest() == revision[7:]
# checkout ref = 배포 대상 커밋, 정의에서 기본값 문법 금지 — 값이 없으면 뜨지 않게
```
무엇이 깨졌나: 식별자가 가리키는 내용과 실제 실어 보낸 내용이 서로 다른 읽기에서 왔다.

### 변형 F — 문자열 검사 vs 실제 전송 hop
① 문제 코드
```go
if !strings.HasPrefix(url, "https://") { return errInsecure }
resp, _ := client.Get(url)                 // 302 → http:// 도 따라감
// 1차 수정: client.CheckRedirect = httpsOnly   ← 호출자가 둔 기존 정책을 덮어씀
```
② 고친 코드
```go
c := *client                                               // 공유 객체를 바꾸지 않도록 복사본에 설정
prev := c.CheckRedirect
c.CheckRedirect = func(req *http.Request, via []*http.Request) error {
    if req.URL.Scheme != "https" { return errInsecure }    // 매 hop 검사 먼저
    if prev != nil { return prev(req, via) }               // 기존 정책과 합성
    if len(via) >= 10 { return errors.New("too many redirects") }  // nil 일 때의 기본 정책(10회 제한)도 보존
    return nil
}
```
무엇이 깨졌나: 첫 문자열만 검사하고 실제 통신 경로는 검사하지 않았다(그리고 고치면서 공유 객체의 정책을 지웠다).

### 변형 G — 셸 개행 strip·정규식 `$`·삭제식 정규화
① 문제 코드
```bash
sid=$(jq -r '.session_id' <<<"$input")                 # 후행 개행 제거된 값
[[ "$sid" =~ ^[A-Za-z0-9_-]+$ ]] || exit 1             # 가공본을 검증
state_path="$dir/$(printf '%s' "$sid" | tr -cd 'A-Za-z0-9_-')"   # 삭제식 → a.b / ab 충돌
```
② 고친 코드
```bash
# 원본을 jq 쪽에서 절대 끝 앵커로 검증
sid=$(jq -r '.session_id | select(test("^[A-Za-z0-9-]+\\z"))' <<<"$input")
[ -n "$sid" ] || { stateless=1; }                      # 불량 id 는 지우지 않고 거부(상태 없음)
state_path="$dir/$sid"
```
무엇이 깨졌나: 검증한 값(가공본)과 사용한 값이 달랐고, `$`는 개행 앞에서도 끝으로 인정됐으며, 삭제식 정규화는 다른 입력을 같은 키로 만들었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~G)은 "검증기를 사용자와 **같은 대상·같은 해석**에 결박한다"이다.\
같은 원리(검증 대상 ≠ 사용 대상)에 다른 방안이 쓰인 사례:

### 방안 1 — 사전 게이트와 실제 파서의 문법 단일화
```python
# 문제: 파서를 부를지 정하는 사전 검사가 파서 문법의 일부만 앎
def contains_grammar(q: str) -> bool:
    return bool(re.search(r"\b(adj|near)\d+\b", q, re.I)) or "&&" in q or "||" in q
    # 파서는 * ? % 도 연산자로 아는데 게이트가 모름 → 단독 와일드카드가 일반 키워드로 처리
# 고친: 게이트가 파서와 같은 문법 집합을 본다
    ... or any(ch in q for ch in "*?%")
```
결박 대상이 "바이트"가 아니라 **문법 정의**다 — 게이트와 파서가 문법을 따로 가지면 게이트를 통과한(또는 못 한) 입력이 파서에서 다른 의미가 된다.

### 방안 2 — 실행 전 검사는 "실행 전 상태"만 본다
```bash
# 문제: 사전 훅이 "git add … && git commit" 복합 명령을 검사
staged=$(git diff --cached --name-only)   # 훅 시점엔 add 미실행 → 항상 빈 값 → 가드 스킵
# 고친: 명령이 만들 상태를 명령 인자에서 추정
#   add 인자의 실존 파일, add -A / . 는 작업트리 porcelain 스캔(pathspec 한정)
```
검증 시점에 **대상이 아직 존재하지 않는** 경우다 — 사후 훅(실제 커밋 시점 검사)이 더 정확하다는 대안도 있었다.

### 방안 3 — 승인 화면의 표시 = 실제 결정 대상, 불확실하면 참고용으로 축소
```bash
# 문제: 승인 사유에 훅 cwd 의 현재 브랜치·upstream 만 표시
#       git -C·refspec·pushRemote 에서 실제 발행 대상과 다름, detached HEAD 는 "HEAD" 로 표시
branch=$(git rev-parse --abbrev-ref HEAD)
# 고친
branch=$(git symbolic-ref --short -q HEAD || echo "(detached)")
reason="참고용 로컬 컨텍스트(cwd=…) — ⚠ 실제 push 대상·범위가 아님 / 명령: <원본 명령>"
# 사유 문구는 정적화 — 리모트 URL·설정·stderr 같은 원시 값은 싣지 않음(자격증명 유출 방지)
```
사람의 승인도 검증이다 — 화면이 보여준 대상과 실행될 대상이 다르면 승인이 다른 것에 대해 이뤄진다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 같은 바이트·같은 해석에 결박 | 검증기와 사용자가 같은 입력을 본다 | 엄격 파서·스냅샷·단일 정규형 구현 | 정상 변형까지 거절(의도된 소음) | 신뢰 경계를 넘는 입력·배포 정의·서명 |
| 1. 게이트·파서 문법 단일화 | 사전 분기와 실제 파서가 따로 있다 | 문법 정의 공유 | 한쪽만 갱신하면 재발 | 파서 앞에 빠른 경로 판정이 있을 때 |
| 2. 실행 전 상태만 봄을 인정 | 검사가 실행 전에만 가능하다 | 인자·작업트리로 추정 | 추정이 틀리면 누락 | 사후 검사 지점을 쓸 수 없는 훅 |
| 3. 표시를 정직하게 축소 | 실제 대상을 정확히 계산할 수 없다 | 문구 설계 | 사람이 참고용 표시를 대상으로 오인 | 사람 승인 UI |

**결론**: 검증기가 사용자와 **같은 입력을 같은 규칙으로** 볼 수 있으면 기본 방안(결박)이 가장 강하다.\
검증 지점과 사용 지점이 구조적으로 분리돼 있으면(게이트 vs 파서) **정의를 단일 출처로** 묶고(1), 검사 시점에 대상이 아직 없으면 그 한계를 인정하고 인자로 추정하거나 사후 지점으로 옮긴다(2).\
사람이 결정하는 표면은 정확히 계산할 수 없는 값을 **대상인 척 보여주지 않는다**(3).
