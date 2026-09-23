# cs/issue/security/data-interpreted-as-syntax — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **인터프리터가 둘이다.** 첫째는 셸(따옴표·`;`·`$()`를 해석), 둘째는 **실행되는 프로그램 자신의 argv 파서**(선두 `-`를 옵션으로 해석)다.\
   argv 배열로 실행하면 셸을 건너뛰므로 첫째는 사라지지만, 둘째는 그대로 남는다. `--force`라는 브랜치명·경로는 프로그램 입장에서 옵션일 뿐이다.\
   git은 여기에 셋째 층(경로의 pathspec, ref의 revision 문법)까지 있어, 외부 값은 세 겹을 모두 좁혀야 한다.
   > **argument(옵션) 인젝션** — 셸을 거치지 않아도, 데이터가 대상 프로그램의 옵션으로 해석되어 동작을 바꾸는 공격.

2. **각자 다른 틈을 막는다.** `--`는 "여기부터는 옵션이 아니다"를 선언해, 그 뒤의 경로가 `-`로 시작해도 위치 인자로 읽히게 한다.\
   ref처럼 `--` 뒤에 둘 수 없는 값은 **선두 `-`를 거부**하거나, 명령이 지원하면 `--end-of-options`(git 2.24+)로 revision 자리를 보호한다(git은 브랜치 이름의 선두 `-`를 거부하므로 정상 브랜치명은 잃을 게 없다 — 다른 도구는 그 도구의 이름 규칙을 확인).\
   옵션의 **값**이 `-`로 시작할 때(`-m -x`)의 처리는 파서마다 다르다 — POSIX getopt류는 필수 인자 자리의 `-x`를 값으로 받지만, 일부 파서는 새 옵션으로 보거나 거부한다. 이 모호성을 없애려고 지원되는 경우 `--opt=value` 등호형으로 한 토큰에 묶는다.\
   가변 개수 값을 받는 옵션은 (그 파서 규칙상) 다음 옵션이나 `--`가 나올 때까지 토큰을 먹으므로, 그 뒤에 둔 위치 인자(프롬프트)가 옵션 값으로 흡수된다 — 순서를 바꾸거나 종결자를 둔다.
   > **end-of-options(`--`)** — POSIX 유틸리티 관례의 옵션 종결자. 지원하는 프로그램에서 이후 토큰은 피연산자로 취급된다. 지원 여부·추가 의미는 프로그램마다 다르다(git에서는 revision과 경로를 가르는 구분자이기도 하다).

3. **패턴이 실행되어 의도 외 파일까지 매칭된다.** git은 경로 인자를 리터럴이 아니라 pathspec 언어로 해석하므로, `:(glob)…`·`:!…` 같은 이름은 여러 파일을 고르는 식이 된다.\
   add/reset 같은 명령이 사용자가 고른 한 파일이 아니라 여러 파일에 적용된다.\
   모든 git 호출의 단일 관문에서 전역 `--literal-pathspecs`를 항상 붙이면 경로가 글자 그대로 해석된다.
   > **pathspec magic** — git 경로 인자의 `:(…)` 접두 문법. glob·제외·대소문자 무시 등을 켠다.

4. **보간은 셸이 스크립트를 파싱하기 전의 문자열 치환이다.** `${{ }}`가 치환된 순간 입력 문자열은 이미 스크립트의 일부(명령)가 되었고, 셸은 그걸 코드로 파싱한다.\
   그 뒤에 오는 형식 검사 코드는 "이미 명령으로 확정된 주입"을 막을 수 없다. 이 스텝 환경에는 서명 키와 배포 토큰 권한까지 있었다.\
   보간을 전부 `env:`로 옮기면 값은 **환경변수(데이터)** 로만 들어오고, 셸은 인용된 `"$VAR"`만 참조한다 — 주입 차단.\
   형식 검증(`^[0-9a-f]{40}$`)은 역할이 다르다 — 쓰레기 값이 하류로 흘러가는 것을 막는다. 형식 검사 단독안은 검사 시점이 늦어 선택하지 않은 방법이다.

5. **`_`는 임의의 한 글자다.** `LIKE 'SEED_%'`는 `SEED_`로 시작하는 행뿐 아니라 `SEEDX…`처럼 그 자리에 아무 글자나 있는 행까지 매칭한다.\
   실제로 정리 마이그레이션이 의도하지 않은 관리자 행까지 지웠고, FK CASCADE가 그 삭제를 자식 테이블로 전파해 연관 데이터까지 사라졌다.\
   교정은 `ESCAPE`로 `_`를 리터럴로 만들고, 유지 대상은 명시 제외하고, 두 번 적용해도 결과가 같은지(멱등) 행 단위로 확인하는 것이다.\
   "어느 컬럼을 검색할지"는 쿼리의 **구조**다. 바인딩은 값만 데이터로 만들 뿐 구조를 보호하지 못하므로, 요청 문자열을 필드명으로 쓰면 화면이 비공개 컬럼까지 조회할 수 있다 → 코드값을 받아 enum이 필드명 매핑을 소유한다.
   > **바인딩 파라미터** — SQL 구문과 값을 분리해 전달하는 방식. 값은 SQL 구문으로 해석되지 않지만, 테이블명·컬럼명 같은 식별자에는 쓸 수 없고, LIKE 패턴 자리에 바인딩된 값의 `%`·`_`는 여전히 와일드카드다.

6. **모두 "데이터 안의 문자가 문법으로 읽혔다"이다.** `str.format`은 **템플릿 문자열 자체**의 모든 `{}`를 치환 자리로 보므로, 중괄호를 문법으로 쓰는 CSS를 템플릿에 직접 박으면 충돌한다(format **인자 값** 속 `{}`는 다시 파싱되지 않는다).\
   이 사례의 마이그레이션 도구는 기본값으로 SQL 본문의 `${name}`을 placeholder로 치환하므로, HTML 데이터 속 `${…}`가 "정의되지 않은 placeholder" 오류가 된다. 테스트의 재사용 컨테이너는 이미 적용된 상태를 들고 있어 이 오류를 가렸다.\
   `eval()`은 조건 문자열 전체를 파이썬 식으로 실행한다 — 내장 함수를 비워도 임의 코드 실행 경로가 남는다.\
   줄 단위 로그에 검증 전 입력을 쓰면 개행 문자가 **새 로그 레코드**를 만든다(로그 위조).\
   교정은 각각 문법 문자 있는 조각의 분리 조립, placeholder 치환 끄기(운영·테스트 설정 동일), 연산자 테이블 매핑, 입구에서의 형식 검증 + 로그의 모든 외부 필드 구조화·이스케이프다.
   > **로그 인젝션** — 입력에 섞인 개행·구분자로 로그에 가짜 레코드를 끼워 넣는 것.

7. **분리는 특정 해석 단계에서 문법 채널을 안 쓰고, 이스케이프는 문법 채널 안에서 무력화한다.** 종결자·바인딩·리터럴 모드·화이트리스트는 데이터가 **그 단계** 파서의 문법 경로에 들어가지 않게 한다.\
   단 각 수단이 끄는 단계는 하나뿐이다 — `--`는 옵션 해석만 끄고 pathspec·revision 문법은 남기며(→ `--literal-pathspecs`·단일 커밋 검증), 바인딩은 SQL 구문 해석만 끄고 LIKE 패턴의 `%`·`_`는 남긴다(→ ESCAPE). 그래서 "규칙을 몰라도 안전"한 것이 아니라, 값이 거치는 해석 단계를 전부 세고 단계마다 수단을 둬야 한다.\
   이스케이프는 해당 문법의 모든 메타문자를 알아야 하고, 하나라도 빠지면 뚫린다. 그래서 분리를 쓸 수 있으면 분리가 우선이고, 이스케이프가 필요하면 표준 직렬화기(JSON·YAML 라이브러리 등)가 우선이다.\
   손으로 **순차 치환**해 이스케이프할 때는 **이스케이프 문자 자신(백슬래시)을 먼저** 치환해야 한다(한 글자씩 매핑하는 방식이면 순서 문제는 없다). 순서를 거꾸로 하면 따옴표 앞에 붙인 백슬래시가 다시 이스케이프되거나, 원래 있던 백슬래시가 이스케이프 시퀀스로 오인된다.

## 문제 구조 (추상화 코드)

### 변형 A — argv 옵션 인젝션 (선두 `-`, 옵션 값, 가변 옵션)
① 문제 코드
```rust
Command::new("git").args(["worktree", "add", &user_path, &branch]).output()?;  // user_path = "--force"
Command::new("git").args(["log", &user_ref]).output()?;                         // user_ref  = "--output=x"
cmd.push("-m"); cmd.push(model);                                                 // model = "-x" → 옵션 재해석
cmd.extend(["--deny-tools", "A", "B", &prompt]);                                // 가변 옵션이 prompt 흡수
```
② 고친 코드
```rust
Command::new("git").args(["worktree", "add", "--", &user_path, safe_ref(&branch)?]).output()?;
fn safe_ref(r: &str) -> Result<&str> { if r.is_empty() || r.starts_with('-') { Err(Bad) } else { Ok(r) } }
let r = match user_ref { Some(r) if !r.is_empty() && !r.starts_with('-') => r, _ => "--all" };
cmd.push(format!("--model={model}"));                  // 등호형: 한 토큰 (대상 파서가 --opt=value를 지원할 때)
cmd.extend([&prompt, "--deny-tools", "A", "B"]);      // 위치 인자를 가변 옵션 앞으로
// 정렬 옵션 등은 enum 매칭만 허용, 그 외는 고정 기본값 (임의 문자열 플래그 전달 금지)
```
무엇이 깨졌나: 셸은 피했지만 대상 프로그램의 argv 파서가 데이터를 옵션으로 읽었다.\
같은 구조: 모델명·강도 같은 자유 입력을 받지 않고 큐레이션 목록에서만 고르게 하며, 미선택이면 플래그 자체를 붙이지 않는다(후방 호환).

### 변형 B — 프로그램 내부 미니 언어 (pathspec·revision)
① 문제 코드
```rust
fn run_git(args: &[&str]) -> Output { Command::new("git").args(args).output() }
run_git(&["add", user_path]);            // ":(glob)**" → 여러 파일
run_git(&["revert", user_rev]);          // "a..b" → 범위 전체
```
② 고친 코드
```rust
fn run_git(args: &[&str]) -> Result<Output> {                       // 모든 git 호출의 단일 관문
    let out = Command::new("git").arg("--literal-pathspecs").args(args).output()?;
    if !out.status.success() { return Err(stderr(out)) }
    Ok(out)
}
let hash = resolve_commit(user_rev)?;    // rev-parse --verify --end-of-options <r>^{commit}: 검증 호출 자체도 옵션 해석 차단, 단일 커밋만, 범위·비커밋 거부
run_git(&["revert", &hash]);             // 이후엔 검증된 해시로만 실행
run_git(&["show", &format!("{hash}:{path}")]);   // 경로는 "--" 뒤 또는 rev:path 형식으로 격리
// 출력 파싱은 -z (NUL 구분) — 특수 문자 경로의 인용(quote) 처리를 피함
```
무엇이 깨졌나: 경로·리비전이 리터럴이 아니라 git의 미니 언어로 해석됐다.

### 변형 C — 파싱 이전의 문자열 보간 (CI 스크립트)
① 문제 코드
```yaml
- run: |
    SHA="${{ inputs.sha }}"                           # 입력 문자열이 스크립트가 됨
    [[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1          # 이미 늦음
```
② 고친 코드
```yaml
- env:
    INPUT_SHA: ${{ inputs.sha }}                      # 데이터 채널
  run: |
    [[ "$INPUT_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 1    # 형식 검증은 하류 보호 역할
    deploy "$INPUT_SHA"
```
무엇이 깨졌나: 보간이 셸 파싱보다 먼저 일어나 데이터가 코드가 됐다. (검증: 주입 문자열 여러 케이스 스모크 + run 블록 잔여 보간 0 스캔)

### 변형 D — SQL: LIKE 메타문자·쿼리 구조
① 문제 코드
```sql
DELETE FROM items WHERE code LIKE 'SEED_%';          -- _ = 임의 1글자 → 관리자 행까지, CASCADE로 자식 유실
```
```java
cb.like(root.get(request.searchKey()), "%" + kw + "%");   // 요청 문자열이 컬럼을 정함
```
② 고친 코드
```sql
DELETE FROM items
 WHERE code LIKE 'SEED!_%' ESCAPE '!'
   AND code NOT IN (/* 유지 대상 */);                -- 2회 적용해 행 단위 결과 동일 확인
```
```java
enum SearchKey { NAME("name"), AUTHOR("authorName"), CODE("itemCode"); final String field; /*...*/ }
String field = SearchKey.fromCode(request.code()).field;  // 미인식 = 기본 필드로 폴백
String lit = kw.toLowerCase().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");  // 검색어를 리터럴로 받기로 정했다면 LIKE 메타도 이스케이프
cb.like(cb.lower(root.get(field)), "%" + lit + "%", '\\');   // 바인딩만으로는 kw 속 % _ 가 와일드카드로 남음
// 매핑표는 파라미터화 테스트로 고정, 페이지 size 상한
```
무엇이 깨졌나: 리터럴이어야 할 `_`가 와일드카드로, 선택지여야 할 입력이 쿼리 구조로 쓰였다.

### 변형 E — 템플릿·도구의 치환 문법과 충돌
① 문제 코드
```python
HTML_PAGE = "<style>@page { size: A4; }</style><body>{body}</body>"   # CSS가 템플릿 문자열 자체에 박힘
HTML_PAGE.format(body=body)   # CSS의 { } 까지 치환 자리로 파싱 → KeyError
```
```sql
-- 마이그레이션 SQL (기본 placeholder 치환 켜짐)
INSERT INTO pages(body) VALUES ('<div>${title}</div>');   -- 정의되지 않은 placeholder 오류
```
② 고친 코드
```python
ALLOWED_SIZES = ("A4", "A3")
if req.size not in ALLOWED_SIZES: raise HTTPException(400)   # 외부 값은 허용값으로 닫음
HTML_PAGE = "<style>{css}</style><body>{body}</body>"                  # 템플릿엔 치환 자리만
css = "@page { size: %s; margin: 14mm; }\n%s" % (req.size, BASE_CSS)   # 문법 조각 분리 조립
return HTML_PAGE.format(css=css, body=body)                           # 인자 값 속 {} 는 재파싱되지 않음
```
```properties
placeholderReplacement=false    # 운영·테스트 설정 동일하게 (재사용 테스트 컨테이너가 오류를 가림)
```
무엇이 깨졌나: 데이터 속 `{}`·`${}`가 템플릿 도구의 치환 문법으로 읽혔다.

### 변형 F — 조건 문자열 `eval`
① 문제 코드
```python
if eval(rule.condition, {"__builtins__": {}}, {"value": v}): fire(rule)   # 비워도 탈출 경로 남음
```
② 고친 코드
```python
OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq, "!=": operator.ne}
if OPS[rule.op](metrics[rule.metric], rule.threshold): fire(rule)          # metric 필드 필수, 옛 condition 폴백 제거
```
무엇이 깨졌나: 설정 데이터가 범용 언어의 코드로 실행됐다. 곁가지: 설정 스키마를 바꾸고 옛 파서 폴백을 남겨 두면 폴백이 옛 가정을 실행한다.

### 변형 G — 검증 전에 줄 단위 로그에 기록
① 문제 코드
```go
if req.Sha == "" { return 400 }
log.Printf("%s:%s:%s", req.ID, server, req.Sha)   // Sha 안의 "\n" → 가짜 로그 줄
return 202                                        // 형식 검증은 하류가 나중에
```
② 고친 코드
```go
if !regexp.MustCompile(`^[0-9a-f]{7,64}$`).MatchString(req.Sha) { return 422 }  // 로그·접수 전에 거절
slog.Info("accepted", "id", req.ID, "server", server, "sha", req.Sha)       // 같은 줄의 다른 외부 필드(req.ID 등)도 값을 인용·이스케이프하는 구조화 핸들러(Text/JSON)로
return 202
```
무엇이 깨졌나: 신뢰 경계의 입구가 아니라 하류에서 검증해, 그 사이 로그가 위조 가능했고 틀린 값도 접수됐다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~G)은 "데이터 채널을 문법 채널에서 분리한다"이다. 같은 원리에 다른 방안이 쓰인 사례:

### 방안 1 — 이스케이프 (이스케이프 문자 먼저)
```rust
// 직렬화 헤더의 이중따옴표 스칼라 값
for c in s.chars() {
    match c { '\\' => out.push_str("\\\\"), '"' => out.push_str("\\\""), _ => out.push(c) }
}
// 문제였던 코드: 따옴표만 이스케이프 → 경로의 백슬래시가 파서에서 이스케이프 시퀀스로 오인
// 값은 라인 기반 헤더라 단일 라인(제어문자 불가) 전제
```

### 방안 2 — 사용자 입력은 리터럴 매처로 (예방 설계)
```rust
let m = MatcherBuilder::new().case_insensitive(true).fixed_strings(true).build(query)?;  // "foo(bar)" 그대로
// 파일명은 * ? [ 가 있을 때만 glob, 아니면 부분 문자열
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 채널 분리 | 하위 인터프리터가 분리 수단(`--`·바인딩·리터럴 모드·env)을 제공 | 호출 관문 정리 | 분리 수단을 우회하는 새 호출 경로 | 셸·argv·SQL·CI·템플릿 대부분 |
| 1. 이스케이프 | 분리 수단이 없고 문법 안에 값을 넣어야 함 | 메타문자 전수 파악 | 메타문자 하나 누락·순서 오류 | 표준 직렬화기를 쓸 수 없어 포맷 문자열을 직접 생성 |
| 2. 리터럴 매처 | 사용자가 패턴 문법을 쓸 필요가 없음 | 고급 검색 기능 포기 | 패턴 기능이 필요해지면 모드 분기 필요 | 검색·필터 입력 |

**결론**: 하위 인터프리터가 분리 수단을 주면 그것을 우선한다(기본) — 단 각 수단은 해당 해석 단계만 끄므로, 값이 거치는 나머지 단계(pathspec·revision·LIKE 패턴 등)는 단계별로 따로 막는다.\
분리가 불가능할 때만 이스케이프를 쓰되 표준 직렬화기를 우선하고, 손으로 순차 치환한다면 이스케이프 문자를 먼저 치환한다(1).\
사용자에게 패턴 문법이 필요 없다면 처음부터 리터럴 모드로 받아 문법 채널을 열지 않는 것이 가장 싸다(2).
