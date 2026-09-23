# cs/issue/security/authorization-gate-placement — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답
<!-- 질문 1:1 대응 -->

1. **게이트는 권한 요청 단계에 있다.** 2단계 프로토콜에서 실행 여부는 "권한 요청 RPC의 응답"으로 이미 결정된다.\
   그 RPC가 스텁이라 항상 `Cancelled`를 돌려주면 실행 단계는 호출조차 되지 않으므로, 실행 단계에 둔 검사는 **도달 불가 코드**다.\
   교정은 권한 요청 단계를 진짜 게이트로 만드는 것이다 — 요청을 UI 루프에 넘기고 사용자의 선택을 기다려, 선택되면 `Selected`, 채널이 닫히거나 미응답이면 `Cancelled`(fail-closed).\
   실행 단계는 게이트 없이 실행만 한다(이중 프롬프트 방지). 자동 허용은 모든 도구를 무검증 실행시키므로 선택하지 않은 방법이다.

2. **클라이언트는 UI를 거치지 않고 명령을 직접 부를 수 있다.** UI 잠금은 정상 화면에서만 효력이 있고, 명령 호출 자체는 막지 않는다.\
   게다가 서버가 프론트가 보낸 창 이름을 믿으면, 호출자는 다른 창의 이름을 대고 입력할 수 있다.\
   신원은 **런타임이 보증하는 값**(명령 핸들러가 받는 창 객체 자체)에서 꺼내고, 서버가 "이 세션의 입력 담당자 == 호출 창"일 때만 쓰기를 수행해야 한다.
   > **불변식 강제 위치** — "한 명만 입력한다" 같은 규칙은 상태를 바꾸는 쪽(서버)에서 검사해야 우회 경로가 없다.

3. **제한은 두 경로를 남기고, 제거는 한 경로만 남긴다.** allowlist 옆에 자유 경로 필드가 살아 있으면, 같은 결정("어느 홈으로 띄울까")을 내리는 입력이 둘이다.\
   검사는 한쪽에만 걸리거나 언젠가 어긋난다 — 실제로 자유 경로로 오면 검증 없이 통과했다.\
   필드를 와이어(요청 스키마)에서 없애 내부 파라미터로만 두고, 역직렬화기가 **모르는 필드를 거부**하게 하면 구 클라이언트가 보낸 옛 필드도 조용히 무시되지 않고 명시 오류가 된다.\
   계정 id 하나에서 설정 경로와 부수 경로를 **한 값으로 파생**하면 둘이 어긋날 일도 없다.
   > **deny unknown fields** — 스키마에 없는 필드가 오면 역직렬화를 실패시키는 설정. "조용한 무시"가 옛 경로를 살려두는 것을 막는다.

4. **fork의 브랜치도 이름이 `main`일 수 있다.** 후속 워크플로는 기본 브랜치 컨텍스트(시크릿·신원)로 실행되는데, 비교한 브랜치 이름은 트리거 원본 쪽 값이다.\
   이름 비교만으로는 "우리 저장소의 main"임을 증명하지 못한다. 또 "성공"만 보면 아무 브랜치의 수동 빌드 성공도 main 신원 토큰으로 배포 요청이 된다.\
   출처 증명은 `결론=성공 AND 이벤트=push AND 원본 저장소=이 저장소 AND 브랜치=기본 브랜치` 4항 AND다. 1차 수정은 저장소 가드가 빠져 있었고 재리뷰에서 추가됐다.\
   정본 방어는 수신 쪽의 토큰 클레임 검증이고, CI 조건은 보조층이다.

5. **선점 뒤의 인가는 거절된 요청에도 키를 소모시키고, 일부 경로의 인가는 나머지 경로로 우회된다.** 멱등 선점은 부작용이다 — 인가 실패로 끝난 요청이 이미 키를 예약하면 "부작용 0으로 거절"이 깨진다.\
   오케스트레이션 층에 인가를 두면 그 층을 거치지 않는 분기(재전송 응답 경로)는 검사 없이 통과한다.\
   그래서 인가 대조는 **인증 직후·멱등 선점 이전의 진입 미들웨어**에 둔다. 체인 순서(본문 한도 → 인증 → 토큰 검증 → 인가 대조 → 멱등 선점)가 곧 보안 계약이다.\
   허용 목록은 부분 적재를 금지(하나라도 불성립이면 기동 거부)하고, 대조 키는 이름이 아닌 수치 식별자로 한다.

6. **하류는 게이트웨이의 판단을 그대로 믿는 대리인이 된다.** URL이 `/admin/**`이면 ADMIN 헤더를 붙이는 식이면, 권한이 낮은 사용자가 그 URL을 호출하는 순간 하류에는 ADMIN으로 전달된다.\
   게이트웨이가 넘기는 신원은 요청 경로가 아니라 **인증된 주체(SecurityContext)** 에서 도출해야 한다. 헤더는 추가(add)가 아니라 덮어쓰기(set)로 넣어, 클라이언트가 같은 이름으로 보낸 헤더가 남거나 중복 값이 생기지 않게 한다(하류가 첫 값/마지막 값 중 무엇을 읽는지는 구현마다 다르다).
   > **confused deputy** — 권한을 가진 중개자가 권한 없는 요청자의 요청을 자기 권한으로 대신 수행해 버리는 문제.

7. **필터는 "이 경로가 익명 허용인가"를 모른다.** 인증 필터가 토큰 실패에 곧바로 401을 쓰면, 인가 계층(공개 정책의 유일한 소유자)은 판단할 기회조차 없다.\
   그래서 서버 재기동으로 기존 토큰이 전부 폐기 판정되자, 공개 경로까지 401이 났다.\
   교정은 토큰 실패를 **익명 강등**으로 처리하는 것이다 — 실패 사유만 서버 내부 요청 속성(클라이언트가 조작 불가)에 적고 체인을 계속한다.\
   익명 필터가 익명 권한을 부여 → 인가가 판정 → 거부면 EntryPoint가 속성에서 사유를 복원해 기존의 세분 에러 코드(만료 등)를 그대로 돌려준다.\
   인증은 "누구인가", 인가는 "허용되는가"를 각각 소유한다.

## 문제 구조 (추상화 코드)

### 변형 A — 게이트를 도달 불가 단계에 둠 (2단계 프로토콜)
① 문제 코드
```rust
fn request_permission(&self, _req: PermReq) -> PermResp { PermResp::Cancelled }   // 스텁: 항상 거부
fn write_file(&self, req: WriteReq) -> Result<()> {
    if !ask_user(&req) { return Err(Denied) }                                   // "게이트" — 도달 불가
    fs::write(req.path, req.content)
}
```
② 고친 코드
```rust
async fn request_permission(&self, req: PermReq) -> PermResp {
    let (tx, rx) = oneshot::channel();
    let chosen = if self.ui.send((req, tx)).is_err() { None } else { rx.await.ok().flatten() };
    match chosen { Some(id) => PermResp::Selected(id), None => PermResp::Cancelled }   // 미응답 = 거부
}
fn write_file(&self, req: WriteReq) -> Result<()> { fs::write(req.path, req.content) } // 실행만
```
무엇이 깨졌나: 실제 결정 지점(권한 RPC)이 아닌 곳에 게이트를 두었다.

### 변형 B — 클라이언트가 주장하는 신원
① 문제 코드
```rust
#[command] fn write(id: SessionId, caller_label: String, data: Bytes) -> Result<()> {
    // UI에서만 읽기 전용 창의 입력칸을 잠금. 서버는 caller_label을 그대로 신뢰
    mgr.write(id, &data)
}
```
② 고친 코드
```rust
#[command] fn write(window: Window, id: SessionId, data: Bytes) -> Result<()> {
    let is_driver = rt.sessions.get(&id).map(|s| s.driver == window.label()).unwrap_or(false);
    if is_driver { mgr.write(id, &data) } else { Ok(()) }   // 런타임이 보증한 창 객체로 판정
}
```
무엇이 깨졌나: 불변식을 UI로만 막았고, 신원을 요청 파라미터에서 가져왔다.\
같은 구조: 게이트웨이가 하류 권한 헤더를 URL prefix·정적 기본 헤더로 정함 → `headers.set("X-User-Role", resolveFrom(securityContext))`로 교정(최고 권한 순 매핑, 익명 principal은 ANONYMOUS).

### 변형 C — 같은 결정을 내리는 두 번째 입력 경로
① 문제 코드
```rust
#[derive(Deserialize)]
struct SpawnRequest { account: Option<String>, home_dir: Option<PathBuf> /* 자유 경로 */ }
let home = match (req.account, req.home_dir) {
    (Some(a), _) => allowlist.resolve(&a)?,   // 검사
    (None, Some(p)) => p,                     // 검사 없음 — allowlist 우회
    _ => default_home(),
};
```
② 고친 코드
```rust
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]                 // 옛 필드가 오면 명시 거부
struct SpawnRequest { account: Option<String> }
let home = accounts::resolve(req.account)?;   // 유일한 입구
let (config_dir, watch_root) = derive_both(&home);   // 두 경로를 한 값에서 파생
```
무엇이 깨졌나: allowlist 옆에 같은 효과의 무검사 입력이 남아 있었다.\
같은 구조: CI 후속 워크플로가 트리거 원본의 **브랜치 이름**만 비교 → fork가 `main`을 사칭. 교정은 4항 AND.
```yaml
if: >-
  run.conclusion == 'success' && run.event == 'push' &&
  run.head_repository.full_name == github.repository &&
  run.head_branch == repository.default_branch
```

### 변형 D — 인가가 부작용 이후·일부 경로에만
① 문제 코드
```go
chain(receiver, withAuth, withIdempotency)      // 선점(키 소모)이 먼저
// 인가 대조는 coordinator 안 — 재전송 응답 분기는 coordinator를 거치지 않음
```
② 고친 코드
```go
chain(receiver, withBodyLimit, withAuth, withTokenClaims, withTargetCheck, withIdempotency) // 순서가 계약
func withTargetCheck(next Handler) Handler {
    return func(r Req) Resp {
        if !allowlist.Match(claims(r).RepoID, decodeTarget(r.Body)) { return resp(403, "forbidden") } // 일반 문구
        return next(r)
    }
}
// 기동 시: allowlist 항목 하나라도 불성립이면 기동 거부 (부분 적재 금지)
```
무엇이 깨졌나: 거절된 요청도 멱등 키를 예약했고, 재전송 분기는 인가 층을 우회했다.\
같은 구조: 경로 패턴 기반 인가에서 trailing slash·세그먼트·matrix 파라미터 변형이 다른 규칙에 매칭될 수 있어, 정규화 우회를 회귀 테스트로 고정.

### 변형 E — 앞단 인증 필터가 판정을 조기 확정
① 문제 코드
```java
} catch (ExpiredJwtException e) {
    writeError(res, 401, JWT_EXPIRED); return;          // 공개 경로도 여기서 끝남
}
```
② 고친 코드
```java
} catch (ExpiredJwtException e) {
    req.setAttribute(JWT_FAILURE_ATTR, JWT_EXPIRED);    // 서버 내부 채널
    chain.doFilter(req, res); return;                    // 익명으로 계속 → 인가가 판단
}
// EntryPoint (인가 거부 시): Object reason = req.getAttribute(JWT_FAILURE_ATTR); → 세분 코드 복원
```
무엇이 깨졌나: 인증 계층이 인가 계층의 공개 정책을 덮어썼다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~E)은 "인가를 단일 지점·부작용 이전·보증된 신원으로 옮긴다"이다. 같은 원리(인가 판정이 우회·왜곡되지 않게)에 다른 방안이 쓰인 사례:

### 방안 1 — 보호 장치의 상태는 단일 기록 주체만 쓴다 (자가 우회 차단)
```sh
# 문제: 게이트 상태 파일이 편집 허용 경로 → 감시 대상이 직접 MODE=auto 기록
# 고친: 상태 파일 직접 편집은 하드 거부, 기록은 전용 스크립트 한 경로
set-state spec-approved "$STATE"      # enum 검증·선행조건 확인·원자 쓰기
# 차단 메시지 = 실제로 실행 가능한 복구 명령 (거짓 안내 → 교착 방지)
```
감시 대상이 감시자의 상태를 쓸 수 있으면 통제는 무효다. 쓰기를 막았다면 정당한 기록 경로를 따로 줘야 교착이 없다.

### 방안 2 — URL을 인가 계약으로 취급 (시드 패턴 동기 + 실매칭 테스트)
```text
인가 = DB 경로 패턴 매칭, 미매칭 = deny (fail-closed)
PUT /items/{code}  → PUT /items   로 변경
시드 패턴 /items/*  는 정확히 한 세그먼트 → /items 와 불일치 → 전원 403
교정: URL 변경 체크리스트에 "인가 시드 패턴 동기" + 실 DB 컨테이너로 시드·매칭 통합 테스트
```

### 방안 3 — 거절 가드보다 앞에서 동일 비용 비교 (존재 오라클 제거)
```java
String saltKey     = (user != null) ? user.id()   : loginId;
String storedHash = (user != null) ? user.hash() : FAKE_HASH;   // 실제 해시와 같은 알고리즘·비용 파라미터
boolean ok = hasher.matches(saltKey, raw, storedHash);   // 미존재에서도 같은 비용, 상수시간 비교
if (user == null || !ok) throw new BadCredentialsException("invalid");   // 단일 실패 사유
```
미존재 계정만 해시를 건너뛰면 응답 시간이 계정 존재 오라클이 된다. 헬퍼 추출 리팩토링에서 "호출 순서"까지 등가성 대조 대상이다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 단일 지점·부작용 이전·보증 신원 | 모든 경로가 지나는 층이 있다 | 체인 순서·입력 스키마 관리 | 새 경로·새 필드가 그 층을 우회하면 재발 | 요청 처리 파이프라인 |
| 1. 단일 기록 주체 | 보호 상태를 쓰는 정당한 주체가 하나 | 전용 기록 도구 | 도구를 거치지 않는 쓰기 경로가 남으면 우회 | 감시자·게이트의 상태 파일 |
| 2. URL = 인가 계약 | 인가가 경로 패턴 매칭 | 체크리스트·통합 테스트 | 시드 누락 → 전원 403(안전 측 실패) | DB 기반 동적 RBAC |
| 3. 동일 비용 비교 | 판정 결과가 시간으로 관측 가능 | 미존재에도 해시 1회 | 비교 순서가 리팩토링으로 바뀌면 재발 | 로그인·비밀 비교 |

**결론**: 인가가 "어디서, 누구의 말을 믿고" 판정하는지를 먼저 고정하는 것(기본)이 가장 넓게 통한다.\
보호 상태가 파일·DB 행처럼 쓰기 가능한 자원이면 그 쓰기 권한 자체를 단일 주체로 좁혀야 하고(1), 인가 규칙이 경로 문자열에 기대면 URL 변경이 인가 변경이다(2).\
판정 결과가 부수 채널(시간)로 새지 않게 하는 것은 별개 층의 방어다(3).
