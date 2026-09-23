# cs/issue/cross-cutting/security/secret-ownership-least-privilege — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답

<!-- 질문 1:1 대응 -->

1. 정본은 **비밀이 실제로 쓰이는 곳(.env)** 이어야 한다. 사람이 보는 md 대장은 *사본*이고, 사본은 실제 값과 어긋날 수 있다. 사본에서 `grep`으로 값을 긁으면(예: "첫 32자리 hex"를 집기) 표 구조가 조금만 달라도 엉뚱한 값을 집는다 — 실제로 원하던 배포용 비밀이 아니라 표 첫 행의 다른 용도 비밀이 잡혀 배포 서버가 401로 거절했다. 정본(운영 서버의 .env)에서 직접 등록하면 사본-실제 불일치라는 사고 자체가 없어진다.
   > **정본(source of truth)** — 어떤 값의 진짜 기준이 되는 단 하나의 위치. 나머지는 전부 사본이며, 사본은 정본과 어긋날 수 있다.

2. 비밀을 두 서버가 각각 저장·검증하면, 교체할 때 **두 곳을 모두** 갱신해야 한다. 사람은 언젠가 한 곳만 고치고 다른 곳을 잊는다 — 그 순간 한 서버는 새 비밀을, 다른 서버는 옛 비밀을 들고 있어 검증이 어긋난다. 복사본이 늘수록 교체 비용과 실수 확률이 함께 는다. 그래서 "한 곳만 잊는다"는 우연이 아니라 **복제된 상태를 사람이 동기화하는 구조가 만드는 필연**이다.
   > **rotation(로테이션)** — 유출·주기 만료에 대비해 비밀 값을 새 값으로 교체하는 것. 복사본이 많을수록 비싸고 위험하다.

3. 중계 서버는 **비밀을 저장하지도 검증하지도 않고 받은 헤더를 그대로 넘긴다(pass-through)**, 판정은 진짜 소유자(backend)가 한다. 이유: 만약 프록시도 검증하면 비밀이 두 서버에 살게 되어 Q2의 교체 문제가 생긴다. 검증 로직을 소유자 한 곳에만 두면, 비밀은 그 한 곳에만 존재하고 교체도 그 한 곳만 고치면 끝난다. 프록시는 비밀의 값을 알 필요조차 없이 그냥 통로가 된다.
   (유일한 방법은 아니다 — 검증자가 공개키만 갖는 서명 방식이나 서비스 간 mTLS처럼 공유 비밀 자체를 없애는 설계도 있다. 이 사례에서는 pass-through가 가장 작은 변경이었다.)
   > **pass-through(패스스루)** — 받은 것을 열거나 바꾸지 않고 그대로 통과시키는 중계 방식. 통로는 내용의 책임을 지지 않는다.

4. **최소 권한(least privilege)** = 각 구성요소에 그 일에 꼭 필요한 권한만 준다. master는 "요청을 받아 어느 agent로 보낼지 정하기"만 하는데, agent와 같은 강력한 권한(docker.sock = 호스트 도커 제어권)을 쥐고 있었다. 침해 반경 관점의 위험: master는 **외부 요청을 받는 입구**라 취약점 하나로 뚫릴 수 있고, 뚫리면 그 즉시 호스트 도커 전체 + 마운트된 저장소 3개로 피해가 번진다. 하는 일에 비해 쥔 권한이 너무 컸다.
   > **침해 반경(blast radius)** — 한 지점이 뚫렸을 때 피해가 미치는 범위. 권한을 줄이면 반경이 줄어든다.

5. 권한을 **하는 일에 맞게 줄이면** 입구(master)가 뚫려도 거기엔 위험한 권한이 없어 번질 곳이 없다 — docker.sock·저장소 마운트를 agent에게만 주고 master는 마운트 0개로 만든다(compose의 `profiles`로 서비스를 분리). 이때 "설정 하나 재사용"이라는 편의와 "역할별 권한 분리"라는 최소 권한이 충돌한다. 답은 명확하다 — **편의가 최소 권한을 침식하면 편의를 버린다.** 보안 경계는 편의보다 우선한다.

6. 시크릿이 `.env`에 있고 `.env`가 **git 미추적(untracked) 파일**이면, `git reset --hard`는 *추적 파일만* 되돌리므로 .env를 건드리지 않는다 — 그래서 배포가 코드를 최신 커밋으로 되돌려도 시크릿은 그 호스트에 그대로 살아남는다. 여기서 두 원칙이 만난다: "정본은 실사용처"(그래서 시크릿은 각 호스트의 .env에 산다)와 "그 실사용처는 git 밖"(그래서 코드 배포·되돌리기와 시크릿 수명이 분리된다). 시크릿을 git에 넣지 않는 것이 곧 정본을 실사용처에 두는 것과 같은 결정이다.

7. **상수시간 비교**는 문자열이 몇 글자째에서 틀렸는지에 따라 비교 시간이 달라지지 않게 한다 — 단순 `==`는 앞 글자부터 비교하다 틀리면 일찍 멈춰, 측정 가능한 환경이면 공격자가 그 시간차로 비밀을 한 글자씩 알아낼 수 있다(타이밍 공격). 단 Go의 `subtle.ConstantTimeCompare`처럼 길이가 다르면 즉시 0을 돌려주는 구현은 길이 정보를 드러내므로, 길이도 숨기려면 양쪽을 고정 길이로 해시한 뒤 비교한다. **fail-closed**(비밀이 비어 있으면 무조건 거절)는 "설정을 깜빡하면 그냥 통과"라는 최악의 기본값을 막는다 — 설정 부재가 곧 무방비가 되지 않게, 없으면 아예 닫는다. 둘 다 "비밀을 소유한 쪽이 그 검증을 **제대로** 한다"의 구체형이다 — 소유는 보관만이 아니라 올바른 판정 책임까지 포함한다.
   > **상수시간 비교(constant-time compare)** — 입력이 어디서 틀리든(같은 길이 안에서) 항상 같은 시간을 쓰는 비교. 타이밍 공격을 막는다.
   > **fail-closed** — 설정이 빠지거나 애매하면 "일단 열기"가 아니라 "아예 닫기"를 기본값으로 삼는 것.

8. (추가) **명령행은 공개 게시판이다.** 프로세스의 argv는 `/proc/<pid>/cmdline`·`ps`로 같은 호스트의 다른 사용자에게 보인다(리눅스 기본 설정 — `/proc`의 `hidepid`로 제한하지 않았을 때).\
   그래서 토큰·첫 프롬프트 같은 민감 입력은 argv가 아니라 권한 0600 파일(경로만 env로 전달)·stdin·암호화된 세션 채널로 보낸다.\
   "이벤트에 비밀 없음" 같은 주장은 한 표면만 보고 할 수 없다 — argv·훅 원본 payload·도구 출력·비정상 종료 메시지·하위 명령 stderr 등 **모든 출력 표면**에서 반증해야 하고, 증명이 안 되는 표면은 주장 범위를 좁혀 문서화한다(카나리 토큰으로 노출 0건 확인).
   > **카나리 토큰** — 노출 여부를 추적하려고 일부러 심는 식별 가능한 가짜 비밀. 산출물에서 발견되면 누출 경로가 있다는 뜻이다.

9. (추가) **작업 트리에서 지워도 히스토리에는 남는다.** git 객체는 불변이라, 코드에서 비밀·개인정보를 지운 커밋을 만들어도 과거 커밋에서 그대로 읽힌다.\
   공개·공유 전에는 히스토리를 재작성(치환 규칙으로 전 커밋 스크럽)하고, `log --all -S`·전 커밋 grep으로 0건을 확인한다.\
   재작성은 로컬 참조만 바꾸므로, 원격의 **모든 브랜치·태그 참조를 각각** 덮어써야 한다 — 한 브랜치만 밀면 다른 원격 브랜치에 남는다.\
   그래도 완전 삭제는 보장되지 않는다 — 호스팅 서비스는 PR 참조·포크·캐시·커밋 해시 직접 접근으로 옛 객체를 남길 수 있고(서비스 측 정리 요청 필요), 이미 복제한 사람의 사본은 회수할 수 없다. 그래서 한 번 노출된 **비밀은 재작성과 별개로 교체(rotation)** 해야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 사본(문서)에서 비밀 값을 긁어 등록
① 문제 코드
```sh
# 사람이 보는 비밀 대장(md 표)에서 "첫 32자리 hex" 를 집음
SECRET=$(grep -oE '[0-9a-f]{32}' secrets-ledger.md | head -1)    # 표 첫 행의 다른 비밀이 잡힘
register_ci_secret DEPLOY_KEY "$SECRET"                            # → 배포 서버 401
```
② 고친 코드
```sh
# 정본 = 실제로 쓰이는 서버의 .env (git 미추적)
register_ci_secret DEPLOY_KEY "$(read_from_prod_env DEPLOY_KEY)"    # 운영 서버 .env 에서 키 이름으로 직접
```
무엇이 깨졌나: 정본이 아닌 사본에서, 구조가 어긋날 수 있는 패턴 매칭으로 값을 골랐다.\
같은 구조: 정본이 git 밖(.env, 미추적)이면 배포의 `git reset --hard`(추적 파일만 되돌림)에도 비밀이 살아남는다.

### 변형 B — 중계 서버가 비밀을 저장·검증
① 선택하지 않은 코드 (중계도 검증하는 구조)
```ts
// 중계(front)
if (req.headers["x-shared-key"] !== process.env.SHARED_KEY) return res.status(401);  // 비밀이 두 곳에 삶
await fetch(BACKEND + "/sync", { headers: { "x-shared-key": process.env.SHARED_KEY } });
```
② 고친 코드
```ts
// 중계: 저장도 검증도 하지 않고 받은 헤더를 그대로 전달 (pass-through)
await fetch(BACKEND + "/sync", { headers: { "x-shared-key": req.headers["x-shared-key"] ?? "" } });
// 검증은 소유자(backend) 한 곳만 — 교체도 한 곳만
```
무엇을 피했나: 비밀의 복사본이 늘어 교체 때 한 곳을 잊는 구조.

### 변형 C — 라우팅만 하는 입구가 위험 권한을 보유
① 문제 코드
```yaml
services:
  master:                               # 외부 요청을 받는 입구, 하는 일 = 라우팅
    volumes: ["/var/run/docker.sock:/var/run/docker.sock", "repo-a:/r/a", "repo-b:/r/b", "repo-c:/r/c"]
  agent:
    volumes: ["/var/run/docker.sock:/var/run/docker.sock", "repo-a:/r/a", "repo-b:/r/b", "repo-c:/r/c"]
```
② 고친 코드
```yaml
services:
  master:
    profiles: ["master"]
    volumes: []                          # 마운트 0개 — 검증: inspect 로 Mounts 비어 있음
  agent:
    profiles: ["agent"]
    volumes: ["/var/run/docker.sock:/var/run/docker.sock", "repo-a:/r/a", "repo-b:/r/b", "repo-c:/r/c"]
```
무엇이 깨졌나: 서비스 정의 하나를 재사용하는 편의가 입구에 불필요한 권한을 줬다 — 입구가 뚫리면 호스트 전체로 번진다.

### 변형 D — 비밀 비교의 타이밍·빈 값
① 피한 코드 (전형적 실수 형태)
```go
func Verify(got, configured string) bool { return got == configured }   // 조기 종료 비교, "" == "" 통과
```
② 고친 코드
```go
func Verify(got, configured string) bool {
    if configured == "" { return false }                                             // 미설정 = 거절 (fail-closed)
    return subtle.ConstantTimeCompare([]byte(got), []byte(configured)) == 1         // 상수시간
}
```
무엇을 피했나: 비교 시간으로 비밀이 새는 것, 설정 누락이 무방비가 되는 것.

### 변형 E — 커밋되는 예시 파일·클라이언트 번들에 실값
① 문제 코드
```sh
# .env.example (커밋 대상)
DB_HOST=<실제 내부 주소>
DB_USER=<실제 계정>
```
```ts
export const DEV_SEED_USERS = [{ email: "<실제 주소>" }];    // 프로덕션 번들에 포함 → 타인에게 OTP 발송 가능
```
② 고친 코드
```sh
DB_HOST=<placeholder>
DB_USER=<placeholder>
```
```ts
const seed = process.env.NODE_ENV !== "production" ? DEV_SEED_USERS : [];
// 빌드 시 NODE_ENV 정적 치환 + 데드코드 제거가 전제 — 아니면 배열이 번들에 그대로 남는다.
// 확실히 하려면 시드를 개발 전용 모듈로 분리해 프로덕션 빌드가 import 하지 않게 한다.
```
무엇이 깨졌나: 공개 채널(저장소·클라이언트 번들)에 실값·개발 데이터를 넣었다.

## 검증 기록
- 2026-09-23: 원 사례 원문 + 코드 대조 작성 (Claude 초안).
- 2026-09-24: B2 전환 — 사례 링크·파일 근거를 추상화 코드로 교체, 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~E)은 "비밀의 정본을 하나로 두고, 복사본·과다 권한을 없앤다"이다. 같은 원리(비밀·권한의 노출면 최소화)에 다른 방안이 쓰인 사례:

### 방안 1 — 비밀 필드를 타입에서 없애고 OS 보안 저장소를 정본으로
```rust
#[derive(Serialize, Deserialize)]
pub struct Connection { pub id: String, pub host: String, pub port: u16, pub user: String,
                        pub auth_kind: String, pub key_path: Option<String>, pub has_stored_secret: bool }
// 비밀번호·passphrase 필드 없음 → 레이아웃·설정 JSON 어디로 직렬화돼도 평문 누출 불가
// 비밀은 OS 키체인(account = 연결 id), 재접속 시 백엔드가 id 로 조회 (UI 왕복 없음)
// 키체인 부재·잠김 → 평문 폴백 없이 세션 전용
// 터미널 출력(비밀이 섞일 수 있음)의 디스크 영속은 기본 OFF (opt-in)
#[test] fn serialized_connection_never_contains_a_secret() { /* "password": 키 부재 확인 */ }
```

### 방안 2 — 민감 입력은 argv 대신 파일·stdin·암호화 채널
```rust
// 문제: remote_start(prompt) → 원격 명령 argv 에 첫 메시지
// 고친: prompt 파라미터 제거, 같은 문장은 암호화된 터미널 채널로 전송
//       훅 토큰은 0600 파일, 경로만 env 로 → curl -H @"$HDR_FILE"
//       브리지는 훅 원본 payload 를 버리고 번역된 필드만 전달
```

### 방안 3 — 격리 실행: 빈 설정 볼륨 + 토큰 env 주입 + 사후 누출 스캔
```python
run_dir = fresh_empty_config_volume()                       # 자격·세션·메모리를 통째로 담는 설정 디렉토리를 비움
env = {"AUTH_TOKEN": read_env_file(OUTSIDE_REPO, mode=0o600, single_key=True)}
try:
    run(container, env=env, volumes=[run_dir])
finally:
    if scan_tree(run_dir, needles=all_secret_values(), overlap=True):   # 청크 경계 겹침 스트리밍 스캔
        write(run_dir / "SECRET-LEAK.txt"); set_failed()
    errors = mask_text(errors)                                          # 오류 문자열도 마스킹
```

### 방안 4 — 코드 비내장 + 히스토리 재작성 + 모든 원격 참조 정리
```sh
# 1) 데이터는 데이터 파일이 소유: 템플릿의 하드코딩 연락처 → 프로필 파일에서 로드, 없으면 플레이스홀더
# 2) 전 히스토리 치환
git filter-repo --replace-text rules.txt --force         # 실행 후 origin 제거됨 → 재등록
git log --all -S '<비밀>' ; git grep '<비밀>' $(git rev-list --all)   # 0건 확인
# 3) 원격은 참조마다 개별로 덮어씀 (한 브랜치만 밀면 다른 원격 브랜치에 잔존)
git tag backup/pre-rewrite <old-head>                   # 백업 태그 보존 (비밀을 담고 있으므로 로컬 전용 — push 금지)
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git push --force origin "$b"; done
# 로컬 heads 만 돌면 원격에만 있는 브랜치·태그가 누락 — 원격 참조 목록(ls-remote)과 대조해 전수 처리
# 호스팅 측 PR 참조·포크·캐시는 이것으로 안 지워짐 → 노출된 비밀은 교체(rotation)
# 곁가지: `. ./.env` 는 (줄에 export 가 없으면) 셸 변수일 뿐 자식 프로세스에 안 감 → set -a; . ./.env; set +a
#         필수 비밀의 기본값은 CHANGE_ME (fail-loud)
```

### 방안 5 — 권한 단위를 "역할별 wrapper"로 (인자로 역할을 받는 공유 프로시저 금지)
```sql
-- 문제: 공유 프로시저 acquire(kind, lease) 에 EXECUTE → 인자만 바꿔 다른 역할의 락 해제, 0초 lease, 미지 kind
-- 고친:
CREATE PROCEDURE acquire_impl(...) SQL SECURITY DEFINER ...  -- 아무에게도 EXECUTE 없음
CREATE PROCEDURE acquire_as_agent(IN lease INT) BEGIN CALL acquire_impl('AGENT', lease); END;  -- 역할별 GRANT
-- impl 안 단일 IF:
IF p_kind IS NULL OR p_lease IS NULL OR p_kind NOT IN ('AGENT','CUTOFF') OR p_lease < 1 THEN SET p_ok = 0;
-- NULL NOT IN (...) 은 FALSE 가 아니라 UNKNOWN → IS NULL 을 먼저 따로 거절해야 ELSE(획득)로 새지 않음
DROP PROCEDURE acquire;   -- 구 프로시저 제거 = 그 EXECUTE 권한도 제거
```
논증 리뷰는 통과(clean)했지만 실제 DB에 교차 계정 익스플로잇을 돌린 실행 리뷰가 뚫었다 — red-first 프로브를 회귀 테스트로 남김.

### 방안 6 — 비밀 토큰은 URL 쿼리 대신 fragment + Referrer-Policy
```ts
// 문제: 결과 페이지 링크 ?token=...  → 접근 로그·브라우저 히스토리·다음 요청 Referer 로 유출
// 고친: 링크는 #token=... (fragment 는 서버 요청·Referer 에 실리지 않음 — 단 브라우저 히스토리에는 남으므로
//       읽은 뒤 history.replaceState 로 지우고, 토큰은 1회성·짧은 만료로)
const token = new URLSearchParams(window.location.hash.slice(1)).get("token");   // malformed 는 catch
export const metadata = { referrer: "no-referrer" };
await fetch("/api/result", { method: "POST", body: JSON.stringify({ token }) });  // BFF 에는 body 로
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 정본 하나·복사본 제거·최소 권한 | 비밀·권한의 소유자를 정할 수 있다 | 역할 분리·설정 정리 | 편의 재사용이 권한을 다시 늘림 | 서비스 간 공유 비밀·컨테이너 권한 |
| 1. 타입 수준 부재 + OS 키체인 | 로컬 앱, OS 보안 저장소 사용 가능 | 키체인 부재 시 세션 전용으로 기능 저하 | 새 직렬화 구조에 비밀 필드를 다시 추가 | 자격을 저장하는 데스크톱 앱 |
| 2. argv 회피 | 대체 채널(파일·stdin·암호화 세션)이 있다 | 채널 구현 | 다른 출력 표면(stderr·payload)으로 새는 것은 별도 | 자식·원격 프로세스에 비밀 전달 |
| 3. 격리 실행 + 사후 스캔 | 실행마다 깨끗한 환경을 만들 수 있다 | 볼륨 생성·스캔 시간 | 스캔 needle 에 없는 비밀은 못 잡음 | 에이전트·자동화 실행 |
| 4. 히스토리 재작성 | 공개·공유 전, 재작성 합의 가능 | 해시 변경·원격 참조 전수 정리 | 원격 참조 하나라도 남기거나 호스팅 측 사본이 남으면 잔존(비밀은 교체 병행) | 이미 커밋된 비밀·개인정보 |
| 5. 역할별 wrapper | DB 권한 모델(DEFINER) 사용 가능 | 프로시저 수 증가 | NULL·경계값 검사 누락 | DB 안의 공유 자원 조작 |
| 6. fragment + no-referrer | 토큰을 브라우저가 받아 스크립트로 넘길 수 있다 | 클라이언트 파싱 | 스크립트 없이 서버 렌더만 하는 페이지엔 부적합 | 메일 링크의 1회성 토큰 |

**결론**: 먼저 "이 비밀·권한의 정본과 소유자는 누구인가"를 정하는 기본 방안이 모든 방안의 전제다.\
그 위에서 비밀이 **어느 채널로 새는가**에 따라 방안이 갈린다 — 직렬화(1), 프로세스 명령행(2), 실행 산출물(3), VCS 히스토리(4), URL(6).\
권한 쪽은 "빌려주는 경로"를 가장 좁은 인터페이스로 만든다(5) — 인자로 역할을 받는 범용 입구는 인자 조작이 곧 권한 상승이다.
