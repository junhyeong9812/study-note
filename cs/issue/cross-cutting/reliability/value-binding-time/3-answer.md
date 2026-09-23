# cs/issue/cross-cutting/reliability/value-binding-time — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 추출 블록·대표 원문 기준. 복습 전 읽지 말 것.

태그: `environment-drift`

## 정답

<!-- 질문 1:1 대응 -->

1. 컨테이너의 환경변수는 컨테이너가 **생성될 때** 정해진다. `restart`는 이미 만들어진 같은 컨테이너를 멈췄다 다시 켤 뿐이라 `env_file`을 다시 읽지 않는다.\
`up -d`는 설정이 바뀐 것을 감지하면 컨테이너를 **새로 만들고**, 그때 바뀐 `.env`가 읽힌다. 확실히 하려면 `--force-recreate`를 쓴다.
   > **바인딩 시점(binding time)** — 이름·설정이 구체적인 값에 묶여 이후 그 사본이 쓰이기 시작하는 순간.

2. B의 `session`은 **None**이다. `from A import session`은 import하는 순간의 객체(None)를 B의 로컬 이름에 묶는다. 나중에 `init()`이 A 모듈의 전역을 새 객체로 **재할당**해도 B가 가진 이름은 옛 객체를 계속 가리킨다.\
`import A` 후 `A.session`으로 쓰면 매번 A 모듈의 속성을 **사용 시점에** 찾으므로 재할당된 새 값이 보인다(지연 바인딩).
   > **이른 바인딩 vs 지연 바인딩** — 값을 가져오는 순간 사본을 고정하느냐, 쓸 때마다 원천에서 다시 찾느냐.

3. 공개 환경변수는 빌드 도구가 **빌드 시점에 번들 안의 문자열로 치환**한다. 실행 중에는 그 변수를 참조하는 코드가 이미 사라지고 리터럴만 남아 있어서, 런타임 env를 바꿔도 되살릴 방법이 없다.\
로컬은 `.env.local`이 있는 곳에서 빌드했고, 도커 빌드는 `.dockerignore`가 그 파일을 빼서 빌드 컨텍스트에 값이 없었다. 테스트도 값이 있는 환경에서 돌아 그린이었다(그린 위장).

4. (a) 모듈이 import될 때 한 번 평가 (b) 컨테이너 생성 시점의 inode·소스 경로 (c) 부모 프로세스가 기동할 때 적재한 환경 사본 (d) 이미지 빌드 시점의 레이어 (e) 작업(스레드·세션)이 만들어질 때 (f) 첫 produce 때 브로커 기본값으로 — 이후 앱의 선언적 설정은 이미 있는 토픽을 바꾸지 않는다.\
모두 "그 시점에 만든 사본"이 이후 원천 변경과 끊어진다는 같은 구조다.

5. 단일 파일 bind mount는 경로가 아니라 **생성 시점의 inode**를 컨테이너에 노출한다. `sed -i`나 에디터의 원자적 저장은 새 파일을 쓴 뒤 rename으로 **바꿔 끼우므로** 새 inode가 생기고, 컨테이너는 옛 inode를 계속 본다.\
그래서 호스트에서는 같은 inode에 내용을 **덮어쓰기**(in-place 쓰기)해야 하고, 컨테이너 안에서 rename으로 교체하려 하면 "Resource busy"가 난다. 마운트 소스 경로 자체를 옮겼다면 컨테이너를 재생성해야 마운트가 갱신된다.
   > **inode** — 파일시스템이 파일 실체를 가리키는 번호. 이름(경로)은 inode를 가리키는 링크일 뿐이다.

6. 작업 목록을 시작 시 전부 만들면 **그 순간의 배치 크기로 잘린 배치들**이 이미 존재하므로, 나중에 배치 크기를 바꿔도 만들어진 작업은 바뀌지 않는다(오프셋 계산도 옛 배치 크기에 묶인다). 워커 풀은 생성자 인자로 받은 크기로 **생성 시 고정**되고, 다시 만드는 코드가 없으면 바꿀 수 없다.\
둘 다 "생성 시점"에 값이 박제되는 구조라서, 실행 중 조절 UI는 동작하는 척만 하게 된다.

7. ① 사용 시점 재독은 **실행 중에 바뀌어야 하는 값**(토큰, 런타임 on/off 정책, 늦게 초기화되는 전역)에 맞다. ② 바인딩 시점 재통과는 **한 번 정해지면 되는 값**인데 원천이 바뀐 경우(컨테이너 env·mount, 부모 프로세스 env, 이미지에 구운 파일)에 맞다. 무엇을 다시 만들어야 하는지(컨테이너인가, 부모 프로세스인가, 이미지인가)를 정확히 짚는 것이 핵심이다. ③ 바인딩 시점에 값 공급은 **나중에 바꿀 수 없는 값**(빌드 인라인, 정적 생성 데이터, 첫 생성 시 기본값)에 맞다. 빌드 컨텍스트에 값을 넣거나 기동 순서·사전 생성으로 올바른 값이 먼저 가도록 한다.

## 문제 구조 (추상화 코드)

> 같은 방안의 사건들: **바인딩 시점을 알아내고, 사용 시점에 읽게 하거나 원천을 그 사본이 보는 자리에서 고친다.**

### 변형 A — import 시점 박제 (모듈 전역 복사·모듈 상수)

① 문제 코드
```python
# db.py
session_factory = None
def init(): 
    global session_factory
    session_factory = make_factory()     # 앱 기동 때 재할당

# handlers.py
from db import session_factory           # import 순간의 None을 복사
async def on_message(msg):
    async with session_factory() as s:   # → "DB 미초기화"
        ...
```
② 고친 코드
```python
import db
async def on_message(msg):
    if db.session_factory is None:              # 가드 + 원인 보존
        raise RuntimeError("db not initialized")
    async with db.session_factory() as s:       # 사용 시점에 모듈 속성으로 찾는다
        ...
```
무엇이 깨졌나: `from X import y`는 이름을 그 순간의 객체에 묶어, 이후 재할당이 보이지 않았다.

① 문제 코드
```ts
const AUTH_HEADERS = { "Content-Type": "application/json" };   // 모듈 로드 때 한 번 평가
export const search = (q) => fetch(url, { headers: AUTH_HEADERS });  // 토큰 없음
```
② 고친 코드
```ts
const authHeaders = () => ({ "Content-Type": "application/json",
                             "access-token": getCookie("token") });   // 호출 때마다 평가
export const search = (q) => fetch(url, { headers: authHeaders() });
```
무엇이 깨졌나: 갱신되는 값(쿠키 토큰)을 모듈 상수에 담으려 했다. 같은 상수를 쓰던 20여 개 API 함수가 전부 토큰 없이 호출됐다.

### 변형 B — 컨테이너 생성 시점 박제 (bind mount의 inode·소스 경로)

① 문제 코드
```sh
# 호스트
sed -i 's/upstream_a/upstream_b/' ./proxy/site.conf   # rename → 새 inode
docker exec proxy nginx -s reload                      # 미반영 — 원문은 원인을 "파일 캐시 또는 inode"로 확정 못 함(inode 고정은 일반론적 설명)
# 컨테이너 안에서 고치려 하면: sed -i → "Resource busy", :ro면 "Read-only file system"
# 설정 디렉토리를 옮긴 뒤에도 컨테이너는 옛 경로 파일을 마운트 중
```
② 고친 코드
```sh
printf '%s\n' "$NEW_CONF" > ./proxy/site.conf   # 같은 inode에 in-place 쓰기
docker exec proxy nginx -s reload
# 소스 경로가 바뀌었으면: 재생성으로 마운트 갱신 후 확인
docker compose down && docker compose up -d
docker inspect -f '{{json .Mounts}}' proxy
```
무엇이 깨졌나: 단일 파일 bind mount는 생성 시점의 inode·경로에 묶여 있어, rename 편집과 경로 이전이 컨테이너에 도달하지 않았다.

같은 구조:
- 컨테이너 쪽에서 마운트된 파일을 복사·덮어쓰기 → busy / read-only → 호스트 원본을 고친 뒤 재시작 또는 reload.

### 변형 C — 컨테이너 생성 시점 박제 (env) + 미치환 플레이스홀더

① 문제 코드
```sh
echo "SMTP_HOST=..." >> .env
docker compose restart app          # env_file을 다시 읽지 않음 → 옛 env
```
```properties
datasource.secondary.url=${SECONDARY_DB_URL}   # .env에 키 없음 → 리터럴 그대로
# lazy 풀이라 기동은 성공, 첫 로그인 때 "driver does not accept jdbcUrl ${SECONDARY_DB_URL}" → 500
```
② 고친 코드
```sh
cp .env .env.bak && echo "SECONDARY_DB_URL=..." >> .env   # 템플릿(.env.example)도 동기화
docker compose up -d app                                    # 재생성으로 env 재적재
# 기록된 과제: 필수 설정 누락을 기동 시점에 fail-fast
```
무엇이 깨졌나: env는 생성 시점에 고정되고, 미정의 플레이스홀더는 리터럴로 남아 늦은 초기화 경로에서야 터졌다.

## 검증 기록

- 2026-09-24: 추출 블록·대표 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

> 같은 원리("바인딩 시점에 박제")에 대해 사건마다 다른 대응을 썼다.

### 방안 1 — 사용 시점(매 반복)에 공유 플래그를 다시 읽는다

① 문제 코드
```rust
let persist = settings.save_output;           // 세션 생성 때 복사
spawn(move || loop {
    sleep(2s);
    if persist { flush_to_disk(&buf); }       // 토글을 OFF로 바꿔도 기존 세션은 계속 저장
});
```
② 고친 코드
```rust
spawn(move || loop {
    sleep(2s);
    if state.enabled.load(Ordering::Relaxed) { flush_to_disk(&buf); }   // 매 tick 런타임 플래그 확인
});
// 프론트 토글·초기화 때 백엔드 플래그를 동기화
```

### 방안 2 — 바인딩 시점을 다시 통과시킨다 (재생성·부모 재기동·재빌드)

```sh
# 컨테이너 env: restart가 아니라 재생성
docker compose up -d --force-recreate app          # 공유 키 교체면 관련 서비스 동시 재생성
# --volumes-from 으로 띄운 보조 컨테이너는 삭제 후 재생성

# pass-through env: 값은 부모 프로세스의 기동 시 사본 → 부모부터 재기동
restart deploy-agent
tr '\0' '\n' < /proc/$(pidof deploy-agent)/environ | grep MODE    # 실제 적재값 확인
redeploy app

# 이미지에 구운 파일(플러그인): 재시작이 아니라 재빌드
docker compose up -d --build search
```
① 문제 코드는 모두 같은 모양이다 — 원천(.env·호스트 파일·빌드 컨텍스트)만 고치고 **사본을 가진 주체**(컨테이너·부모 프로세스·이미지)는 그대로 둔다.

### 방안 3 — 바인딩 시점에 올바른 값을 공급한다

① 문제 코드
```dockerfile
# .dockerignore 가 .env.local 을 제외 → 빌드 컨텍스트에 공개 env 없음
RUN npm run build          # BASE_PATH 가 빈 값으로 번들에 인라인
```
② 고친 코드
```ts
// base path 상수 모듈 — 단일 소스
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "/base-path";   // env 없으면 리터럴 폴백
// 검증: env 없이 빌드(도커와 같은 조건)해서 번들 청크에 값이 박혔는지 확인
// 테스트는 env 있는 로컬에서만 통과하던 것을 교정
```

같은 방안의 다른 시점:
```ts
// 정적 생성은 빌드 때 데이터를 fetch → 빌드 환경엔 백엔드 컨테이너 DNS가 없음
export const dynamic = "force-dynamic";      // 요청 시점으로 미루기 (또는 로컬 JSON 폴백)
```
```yaml
# 첫 produce 때 브로커가 기본 파티션 1개로 자동 생성 → 앱의 파티션 3 선언은 무시됨
app:
  depends_on:
    broker: { condition: service_healthy }   # 기동 순서 보장
# 또는 토픽을 --partitions 3 으로 사전 생성
```

### 방안 4 — 반영될 수 없는 런타임 조절은 제거한다

① 문제 코드
```python
batch_size = self.throttle.batch_size                  # 한 번만 읽음
batches = [rows[i:i + batch_size] for i in range(0, n, batch_size)]   # 작업 목록 사전 물질화
with ProcessPoolExecutor(max_workers=self.throttle.max_workers) as ex:  # 풀 크기 생성 시 고정
    ...
# 대시보드의 속도 조절·중지 버튼 = 동작하는 척
```
② 고친 코드
```python
BATCH_SIZE, MAX_WORKERS = FIXED_BATCH, FIXED_WORKERS   # 고정값 사용, 반영되지 않는 UI는 제거
# 장기안(미적용): lazy 배치 생성 또는 max_pending 으로 동시 submit 제한
# (다른 경로는 매 반복 throttle 재읽기로 batch_size 만 동작 — 방안 1)
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 지연 바인딩·원천을 사본 위치에서 수정 | 사용 시점에 원천을 찾을 수 있다 | 매 호출 조회 | 누군가 다시 이른 바인딩(복사)을 추가 | 늦게 초기화되는 전역·갱신되는 토큰·마운트 파일 |
| 1. 매 반복 공유 플래그 재독 | 실행 중 작업이 반복 루프를 돈다 | 원자 플래그·동기화 | 반복 사이에는 반영 안 됨 | 런타임에 꺼져야 하는 정책(보안 opt-in 등) |
| 2. 바인딩 시점 재통과 | 사본을 가진 주체를 다시 만들 수 있다 | 재생성·재기동·재빌드 중단 시간 | 재생성 대상을 잘못 짚으면(부모 대신 자식) 그대로 | 한 번 정해지면 되는 env·mount·이미지 내용 |
| 3. 바인딩 시점에 값 공급 | 값이 빌드·생성 전에 알려져 있다 | 빌드 컨텍스트·순서 관리 | 폴백 리터럴이 틀리면 조용히 틀린 값 | 빌드 인라인·정적 생성·첫 생성 기본값 |
| 4. 반영 불가 조절 제거 | 재생성 코드를 만들 가치가 없다 | 런타임 조절 기능 상실 | 필요가 생기면 재설계 | 조절 UI가 동작하는 척만 하는 경우 |

**결론**: 실행 중 바뀌어야 하는 값이면 사용 시점에 읽게 한다(기본·1).\
한 번 정해지면 되는 값인데 원천이 바뀌었으면, 사본을 가진 주체를 정확히 짚어 그 바인딩 시점을 다시 통과시킨다(2) — 확인은 원천이 아니라 실행 주체 쪽(프로세스 environ·컨테이너 inspect·번들 내용)에서 한다.\
나중에 바꿀 수 없는 값이면 바인딩 시점에 올바른 값이 먼저 가도록 공급한다(3).\
어느 쪽도 싸게 만들 수 없는 런타임 조절은 동작하는 척하게 두지 말고 제거한다(4).
