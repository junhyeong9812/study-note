# cs/issue/cross-cutting/reliability/fail-closed-guard — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `fail-closed`

## 정답
<!-- 질문 1:1 대응 -->

1. **기본값은 "문제 없음"과 구별되지 않는다.** 가드가 "위험 표지(예: 이력 치환 참조)가 있나"를 조회하는데, 조회가 실패하자 `unwrap_or_default()`가 빈 문자열을 돌려줬다 — 빈 결과는 "표지 없음"과 똑같이 읽혀 **히스토리 재작성이 진행**됐다.\
   교정: 오류를 전파(`?`)해 중단한다. 안전망(백업 참조) 생성 실패도 진행 금지.\
   반대로 오래된 백업을 지우는 부가 작업은 실패를 삼키는 best-effort가 맞다 — 부가 작업의 실패가 핵심 경로를 깨면 안 되기 때문이다. 같은 코드라도 **무엇을 지키는 자리인가**가 방향을 정한다.
   > **fail-closed** — 판정할 수 없으면 거부(닫힘) 쪽으로 기우는 기본값. 반대는 fail-open.

2. **못 읽음 → 없음 → 가장 위험한 판정.** 권한 등으로 프로세스 정보를 못 읽은 항목을 목록에서 지우자 "아무것도 안 돈다"가 되어, 두 프로세스가 같은 파일에 동시에 append하는 작업이 허용될 뻔했다.\
   기준은 **오답의 비용과 불가역성**이다. 잘못된 busy는 버튼이 잠깐 회색일 뿐(되돌릴 수 있음)이고, 잘못된 free는 파일을 파괴한다(되돌릴 수 없음) — 그러므로 모름은 차단한다.\
   교정: 결과를 3분기로 나눈다 — NotFound(이미 종료) = 버림 / 그 외 오류 = `opaque`로 남겨 차단 / 빈 명령줄(커널 스레드) = 버림. 스캔 자체가 불가하면 전체를 "판정 불가"로 차단한다. 대비: 숨김 목록처럼 오답을 되돌릴 수 있는 곳은 fail-open으로 뒀다.

3. **"값이 있을 때만 검사" = 값을 안 만들면 검사가 꺼진다.** 발급부가 토큰 식별자(jti) 없이 발급하자 `jti != null && !active` 조건이 항상 거짓이 되어, 재로그인 뒤에도 이전 토큰이 계속 유효했다 — 단일 활성 세션 검증이 조용히 꺼진 것이다. 흐름 전체를 도는 통합 테스트에서만 드러났다.\
   "키가 설정돼 있으면 검사"하는 인증도 같다 — 키 환경변수가 빠지면 **무인증 개방**이 된다. 교정: 키 미설정도 401 + 서버 기동 거부, 키 변수 이름도 하나로 통합.\
   같은 구조: 빈/공백 토큰 통과, 조건 단락평가로 검사 건너뜀, 보안 모드 설정의 기본값이 "dev"라 설정 누락 시 운영에 인증 우회 미들웨어가 붙는 구조(권고: 기본값 제거 + 운영 환경 검증).

4. **default 분기는 새 값의 기본 착지점이다.** 대상별로 다르게 처리해야 하는데 `else`가 가장 흔한 경로로 흐르면, 대상이 하나 더 생기는 순간 **엉뚱한 대상에 부작용**을 낸다(다른 서비스 요청이 핵심 서비스의 배포 슬롯·라우트를 덮을 수 있었다). 검색 유형 분기에 새 유형이 없어 일반 검색으로 폴백한 사례는 0건을 냈다.\
   빌더가 미지원 필드에 `None`을 반환하고 호출자가 `if q:`로 조용히 건너뛰자, must 조건 없이 filter만 남은 bool 질의가 **filter에 걸리는 전체 문서**를 돌려줬다 — 조건 소실이 곧 전체 반환이다. 로그에는 "쿼리 생성 완료"가 함께 찍혀 오해를 키웠다.\
   교정: 알려진 값만 명시 분기하고 그 외는 시작 전에 요란하게 거절한다(부작용 0). `None`은 경고가 아니라 예외로 격상한다.

5. **열거 + 실패 시 안전측 = 경로마다 새 누수.** 허용 쪽 조건을 열거하고 "판별 실패 시 안전 쪽"을 기대하면, 판별 경로(저장소 판별 실패·심링크·빈 정규화 결과·잘못된 cwd·대소문자 변환…)가 하나 늘 때마다 **그 경로의 실패가 허용으로 새는** 지점이 생긴다 — 리뷰 루프마다 새 fail-open이 나왔다.\
   반전: 기본값을 거부로 두고 허용은 **양성 조건 두 개**(저장소 안의 순수 문서 / 어떤 저장소에도 속하지 않음)가 증명될 때만 준다. 그러면 새 경로의 실패는 자동으로 거부로 떨어진다.\
   오류 메시지는 사람용이라 로케일에 따라 바뀐다 — 영문 문자열을 매칭하던 판정이 한국어 로케일에서 깨졌다. 판정은 **종료 코드·파일 구조 같은 기계 신호**로 한다.
   > **allowlist(허용 목록)** — 명시한 것만 허용하고 나머지는 전부 거부. 새 기능·새 경로가 기본 거부된다.

6. **모름의 종류를 나눈다.** "입력 파싱 실패 = 차단"을 균일 적용하자 파서 오류 하나로 모든 명령이 마비됐다(가용성 붕괴). 반대로 정제 파이프라인 실패 시 대상을 못 찾아 조용히 허용하는 구멍도 있었다.\
   구분: **대상인지 자체를 모름** = 통과 + 경고(가용성) / **대상인데 허가 여부를 모름** = 차단(안전). 실패 원인도 사용자 조치 가능(차단 + 조치 안내)과 환경 원인(진행 + 경고)으로 나눠야 신호가 산다.\
   과차단 완화: "어느 파일을 쥐었는지 모르는 프로세스 하나"가 디렉토리 전체를 막자, **프로세스 시작 시각 이전에 마지막으로 쓰인 파일은 그 프로세스 것일 수 없다**는 사실로 차단 범위를 좁혔다(시작 시각 − ε 이후 기록만 차단). 시작 시각을 못 읽으면 다시 전체 차단 — 좁히는 근거가 없으면 닫힌다.

7. **폴백은 특정 오류에만.** 잘못된 signal 값으로 프로세스 그룹 kill이 `EINVAL`을 내자 폴백이 고정 SIGHUP을 보내 프로세스를 죽이고, 응답은 요청 signal로 "성공"을 보고했다. 폴백은 "배달 대상 없음(`ESRCH`)"에만 정당하고, "요청 자체가 거부됨"을 다른 동작으로 재시도하면 의도와 다른 부수효과가 난다. 응답은 **실제로 한 일**을 보고해야 한다.\
   토큰 서명키를 분리하며 둔 이중키 폴백도 같다: 만료(`Expired`)는 즉시 401, 서명 불일치일 때만 다른 키 + 일회용 식별자 등록 여부로 재검증.\
   필수 설정에 기본값을 두거나(`lang='ko'` 기본 인자 → 호출 누락이 항상 한국어 파일명), 검증기가 잘못된 날짜를 보정하거나(`2024-13-45` → `2024-12-31`), CLI가 여분 인자를 무시하면(다른 위치에 파일 212개 생성), 모두 **오류가 다른 의미의 정상 동작으로 둔갑**한다 — 판정 불가를 통과시킨 것과 같다.

## 문제 구조 (추상화 코드)

### 변형 A — 조회·판독 실패를 "없음"으로 삼킴
① 문제 코드
```rust
let refs = run(cwd, &["list-refs", "refs/replace/"]).unwrap_or_default();   // 실패 → ""
if refs.is_empty() { rewrite_history()?; }                                  // "" = 없음 = 진행

let procs: Vec<_> = pids.filter_map(|p| read_cmdline(p).ok()).collect();    // 못 읽음 = 제거
if !procs.iter().any(|p| p.uses(file)) { allow_append(file) }
```
② 고친 코드
```rust
if !run(cwd, &["list-refs", "refs/replace/"])?.is_empty() { return Err(Unsafe); }   // 오류 전파

let procs = pids.filter_map(|p| match read_cmdline(p) {
    Ok(c) if c.is_empty() => None,                 // 커널 스레드
    Ok(c)                 => Some(Proc::known(c)),
    Err(e) if e.not_found() => None,               // 이미 종료
    Err(_)                => Some(Proc::opaque()), // 모름 → 남겨서 차단
});
if !scan.ok { return Verdict::Blocked(Undecidable); }
```
무엇이 깨졌나: 판정 불가가 판정 결과("없음")와 같은 값으로 표현됐다.\
같은 구조: "파일을 연 프로세스" 신호(fd 스캔)가 활성 중에도 0.3%만 적중 — 매번 열고 닫는 writer는 순간 스냅샷에 거의 안 잡히므로, 약한 신호의 "없음"은 증거가 아니다(판정 하중을 명령줄·시작 시각 신호로 이동).\
같은 구조: 캐시 저장소 연결 실패 시 `client = None` → 경고만 남기고 차단 목록 검사 자체를 생략(해결: 필수 연결화 또는 원 저장소 직접 조회 fallback).

### 변형 B — 검증·계측·게이트의 "확인 실패" = 음성
① 문제 코드
```python
ledger.append(request_id)                 # 원장에 먼저 기록
result = run(); write_result(result)      # 여기서 예외 → 원장엔 있고 결과엔 없음 → 사용량 영구 누락
ok = verify_hash(path) if exists else True   # 검증기 크래시 → match 취급
def creds_in_volume(): return rc == 0 and found   # rc≠0 → False("없음")
if preflight.get("ok"): ...               # truthy 검사
status = "ok"                             # 누출 감지 이후에도 ok
```
② 고친 코드
```python
write_result(result); ledger.append(request_id)     # 결과 먼저, 원장 나중
def creds_in_volume(): return None if rc != 0 else found   # tri-state: 모름 = None
if preflight.get("ok") is not True: fail()
try: ...
finally: status = finalize(all_checks)              # 모든 검사 뒤 최종 상태 결정
# 래퍼: started 선기록 — 기록 실패 시 실행 안 함(exit 97), 실행 후 종료 기록
```
```sh
case "$PHASE" in await|verify) block ;; impl|done) : ;; *) block ;; esac   # enum 밖 = 차단
sed -i "s/^X=.*/X=$v/" "$state" || { warn; block; }                             # 상태 쓰기 실패 = 차단 (처방 — 원 기록은 수정 상세 미기록)
```
무엇이 깨졌나: 관측 불가가 "0·False·일치"로 위장돼 정상으로 집계됐다.

### 변형 C — 불확실 상태·default 분기가 넓은 쪽으로
① 문제 코드
```go
mode, err := store.Mode(id)
if err != nil || mode == "" { mode = Dev }            // 저장 장애 = 승인 우회
switch { case isBlueGreen(req): dispatchBlueGreen(req)  // 대상을 안 봄 → 다른 서비스가 핵심 슬롯 덮음
         default: runDefault(req) }
```
```python
def field_query(field, v):
    if field in NUMBER_FIELDS: ...
    log.warning("unsupported"); return None          # 분기 빈칸
q = field_query(f, v)
if q: builder.add_must(q)                            # 조용히 skip → filter 만 = 전체 반환
```
② 고친 코드
```go
mode, err := store.Mode(id)                           // store 는 기본값을 지어내지 않고 ErrNoMode
if err != nil { return Decision{Operational, ApprovalRequired, FailClosed: true} }
switch req.Target {
case TargetCore:    dispatchBlueGreen(req)
case TargetGateway: runSinglePath(req)
default:            return Unexecuted, errors.New("unknown target: fail-closed")   // 부작용 0
}
```
```python
if q is None: raise QueryBuildError(field)           # 조건 소실 = 예외
# else: raise ValidationError(search_type)           # 모르는 유형은 폴백 대신 거부
```
무엇이 깨졌나: "모르는 값"이 가장 흔한 경로·가장 넓은 권한으로 흘렀다.\
같은 구조: 파서가 문법 오류를 `parsing_failed=True` 플래그로 바꿨는데 다음 단계가 플래그를 안 봐서 400 대신 200/빈 결과. 보고서 대상 오타에 `else` 없이 `None` → HTTP 200 + null.

### 변형 D — 보안 검사가 "값이 있을 때만" 실행
① 문제 코드
```java
if (apiKey != null && !apiKey.equals(header)) return unauthorized();   // 키 미설정 = 무인증
if (userId != null && jti != null && !registry.isActive(userId, jti)) return unauthorized();
if (token == null || token.isBlank()) { chain.doFilter(req, res); return; }   // 빈 토큰 통과
```
```python
ENV_MODE: str = Field(default="dev")    # 누락 시 인증 우회 목(mock) 미들웨어 등록
```
② 고친 코드
```java
if (apiKey == null) throw new IllegalStateException("key required");   // 기동 거부
if (!apiKey.equals(header)) return unauthorized();
String jti = UUID.randomUUID().toString();                              // 발급부가 항상 생성
token = builder.id(jti).build(); registry.register(userId, jti);        // 이전 jti 폐기
```
무엇이 깨졌나: 검사의 전제값이 빠지면 검사 자체가 꺼지는 구조였다.

### 변형 E — 공유 인프라를 가리키는 기본값이 서로 다름
① 문제 코드
```ini
# 생산자 서비스 .env 기본값           # 소비자 서비스 .env 기본값
QUEUE_REPLICA_PORT=6381               QUEUE_PRIMARY_PORT=6381   # 한쪽 replica 포트 = 다른 쪽 primary 포트
```
② 고친 코드 (절차)
```sh
# 배포 체크: 두 서비스가 같은 인스턴스를 보는지 확인
ping_queue "$PRODUCER_URL"; ping_queue "$CONSUMER_URL"; stream_len stream:events
```
무엇이 깨졌나: 명시 설정이 누락되면 각자 기본값으로 다른 인스턴스에 붙고, 메시지가 안 와도 에러가 없다(잠재 충돌로 기록, 실제 오연결 기록은 없음).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(변형 A~E)은 "판정 불가는 오류로 전파하거나 거부한다"이다. 같은 원리에 다른 방안이 쓰인 사례:

### 방안 1 — 판독 실패 = 위험 + 사용 직전 재검증 + 판정 범위 좁히기
```rust
enum Verdict { Free, Busy, Unknown(Reason) }       // Unknown = 전 행 차단
fn names_session(argv) -> Option<Uuid> { flag_value(argv, &["--resume", "-r", "--session-id"]) }  // 플래그 문맥의 값만
fn spawn(uuid) { if classify(uuid) != Free { return Err(Busy) } /* 직전 재분류 */ ... }

// 과차단 완화: 프로세스는 시작 후에만 쓸 수 있다
let threshold = match start_time(pid) {            // /proc stat 시작 tick ÷ HZ + 부팅 시각
    Some(t) => Threshold::After(t - EPSILON_60S),
    None    => return Some(Threshold::All),        // `?` 로 None 을 흘리면 "차단 없음"으로 뒤집힘
};
// 부팅 시각은 uptime 을 앞뒤 두 번 읽어 차이 > 1s(서스펜드) 면 None → 전체 차단
```

### 방안 2 — 폴백은 특정 오류에만, 응답은 실제 수행 결과
```rust
if !SIGNAL_ALLOWLIST.contains(&sig) { return Err(InvalidSignal) }   // 사전 검증
match killpg(pgid, sig) {
    Err(ESRCH) => { fallback_hup(); Response::Killed { signal: SIGHUP } }   // 실제로 보낸 신호
    Err(e)     => Err(e),                                               // EINVAL·EPERM 은 폴백 금지
    Ok(())     => Response::Killed { signal: sig },
}
```
```java
} catch (ExpiredTokenException e) { reject(TOKEN_EXPIRED); return; }          // 만료 = 폴백 금지
  catch (TokenException e) {
    if (verifyWithSecondaryKey(header)) { chain.doFilter(req, res); return; }   // 서명 불일치만
    reject(TOKEN_INVALID); return; }
```

### 방안 3 — 열거 대신 기본 거부(불변식 반전)
```sh
classify() {                                   # 기본 = 보호 대상(GUARDED)
  is_pure_doc_in_repo "$p" && { echo FREE; return; }
  outside_any_repo "$p"    && { echo FREE; return; }
  echo GUARDED                                  # 정규화 실패·빈 값·잘못된 cwd 도 여기로
}
# 저장소 판별: 메시지 문자열 대신 .git 조상 탐색(로케일 무관, 깊이 상한)
case "$MODE" in auto-a|auto-b) exit 0 ;; esac   # 글롭 auto-* 금지(손상값 통과)
# 첫 매칭에서 끝나는 case 는 순서가 곧 정책 — 차단 블록을 접두사 매칭보다 먼저
```
```python
ALLOWED_TOOLS = {...}; run(tools=ALLOWED_TOOLS)
assert set(init_event.tools) <= ALLOWED_TOOLS     # 관측된 표면 ⊆ 허용 목록, 벗어나면 incomplete
```

### 방안 4 — "모름"의 종류를 나눈다
```text
대상인지 판정 불가 (입력 파싱 실패)      → 통과 + 경고 1줄     (가용성)
대상인데 허가 판정 불가 (정규화·락 실패) → 차단               (안전)
정제 결과 공백 + 원문에 대상 흔적        → 보수적 차단 폴백
실패 원인: 사용자 조치 가능 → 차단 + 안내 / 환경 원인 → 진행 + 경고
```
```java
// "모르면 true" 분기 제거: 판정할 수 있으면 판정, 정말 모를 때만 관대
Type elem = sourceType.genericArgument(0);        // 컨테이너가 알려주지 않던 원소 타입을 직접 해석
if (elem.resolve() == null) return true;          // raw·와일드카드·미해결만 관대 유지
return canConvertElements(elem, targetType);
```

### 방안 5 — 필수 설정·인자는 기본값 없이 fail-fast
```yaml
app.crypto.key: ${CRYPTO_KEY}      # 기본값 없음 → 누락 시 기동 실패(의도)
# 단, 형식만 맞는 임의 값을 넣으면 복호화가 조용히 깨진다 — 실제 키만 주입
```
```python
def export(wb, client, bucket, lang): ...     # 기본 인자 lang='ko' 제거 → 호출 누락이 TypeError
if len(sys.argv) != 3: sys.exit("usage: render <src> <out>")   # 여분 인자 무시 금지(처방)
```
```yaml
# 이미지 기본 CMD(인터프리터 REPL)로 조용히 떠서 즉시 종료·재시작 반복 → 명령을 명시
command: server --host 0.0.0.0 --port 8000
```

### 방안 6 — 검증은 보정 대신 거부
```python
# 문제: "2024-13-45" → 2024-12-31 로 clamp, 파싱 불가면 None → 날짜 조건 소실
# 고친(계획): 불법 날짜는 400 거부, clamp 유지 시 응답에 보정 사실 표시, from > to 경계 테스트
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 오류 전파·거부 | 판정 불가가 드물다 | 가용성 일부 | 의존성 장애 시 기능 정지(의도된 소음) | 파괴적·보안 결정의 가드 |
| 1. 모름=위험 + 직전 재검증 + 범위 좁히기 | 외부 상태를 추정해야 한다 | 신호 수집·재분류 비용 | 좁히는 근거의 한계(아직 한 줄도 안 쓴 세션은 놓침) | 외부 프로세스·파일 점유 판정 |
| 2. 폴백을 특정 오류로 한정 | 오류 종류를 구분할 수 있다 | 오류 분류 코드 | 분류 누락 시 폴백이 안 걸림(안전 쪽) | 대체 경로가 있는 연산·다중 키 검증 |
| 3. 기본 거부(allowlist) | 허용 조건을 양성으로 증명할 수 있다 | 과게이트 | 정당한 새 경로가 막힘(안전 쪽) | 판별 경로가 계속 늘어나는 분류기·도구 표면 |
| 4. 모름의 종류 분리 | "대상 여부"와 "허가 여부"를 나눌 수 있다 | 규칙 이원화 | 분류를 잘못하면 그 칸이 fail-open | 전 명령에 걸리는 게이트(가용성 중요) |
| 5. 필수값 fail-fast | 누락은 배포 시점에 고칠 수 있다 | 기동 실패 소음 | 형식만 맞는 잘못된 값은 못 잡음 | 설정·인자·이미지 명령 |
| 6. 보정 대신 거부 | 사용자가 입력을 고칠 수 있다 | 400 응답 증가 | 없음(오류가 드러날 뿐) | 결과의 정확성이 중요한 검색·조회 |

**결론**: 되돌릴 수 없는 결정을 지키는 가드는 기본적으로 닫는다(기본·3·5·6).\
외부 상태를 추정하는 판정은 닫되 **판정 범위를 좁히는 근거**로 과차단을 줄인다 — 근거가 없으면 다시 닫힌다(1).\
모든 명령에 걸리는 게이트는 균일한 fail-closed가 가용성을 죽이므로 "무엇을 모르는가"로 방향을 나눈다(4).\
폴백은 가드를 우회하는 또 하나의 경로이므로 특정 오류에만 건다(2).
