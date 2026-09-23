# cs/issue/cross-cutting/reliability/process-memory-scope — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **시간 경계와 공간 경계.** 메모리 상태는 프로세스가 끝나면 사라지고(시간), 다른 프로세스에서는 보이지 않는다(공간).\
   가정이 깨지는 대표 상황: ① 재배포·재기동(모든 상태 초기화) ② 멀티 인스턴스·스케일아웃(인스턴스마다 다른 상태) ③ 멀티 워커 웹 서버(같은 호스트여도 워커는 별도 프로세스라 힙을 공유하지 않음).
   > **프로세스 로컬 상태** — 한 프로세스의 힙에만 존재해, 그 프로세스의 수명·범위를 넘지 못하는 상태.

2. **재시작 = 전 토큰 폐기.** 레지스트리가 비어 있으니 `isActive()`는 모든 토큰에 false — 이미 발송한 결과 링크가 전부 무효가 되고, 재로그인 전까지 요청이 401이 된다. 이메일 레이트리밋·인증 코드도 재기동으로 초기화된다.\
   오진: 401은 "권한·경로 설정 문제"처럼 보인다 — 실제로 재시작 직후에만 401이 나고 사용자가 직접 켠 서버에선 정상인 사건을, 처음엔 "메뉴 경로라 막힘"으로 오진했다(이후 "만료 토큰의 공개 경로 처리 문제"로 재분석).

3. **인스턴스마다 다른 세계.** 레이트리미터 카운트는 인스턴스별이라 요청이 분산되면 **한도가 N배**가 된다. "동시 1작업" 락도 프로세스 로컬이라 다른 인스턴스에서 **동시에 실행**된다. 한 인스턴스가 발급해 등록한 토큰은 다른 인스턴스 레지스트리에 없어 **401**이 난다.

4. **영속화 설계.** 결과 토큰을 DB로 옮기며 원문 대신 **해시(SHA-256)**를 저장했다 — DB가 유출돼도 토큰으로 쓸 수 없게. 매 발송마다 새 토큰을 발급하고(기존 토큰 재사용 방식 폐기 — 원문을 저장하지 않으니 옛 토큰을 다시 보낼 수도 없다는 점이 맞물린다, 추정), 만료된 토큰은 1시간 주기 정리 스케줄러로 지운다(테이블 무한 증가 방지).\
   재시작 테스트: 영속성 컨텍스트를 flush + clear한 뒤 조회하는 통합 테스트로 "메모리에 남은 객체 없이 DB만으로 검증되는가"를 흉내냈다.

5. **힙 복제 vs page cache.** 워커가 각자 dict로 사전을 로드하면 사본이 워커 수만큼 생긴다(워커 4개면 4배로 추정했다). 파일 기반 저장소는 OS가 파일 페이지를 **page cache에 한 번만** 올리고 모든 프로세스가 그 물리 페이지를 공유하므로, 워커는 connection만 따로 가진다.\
   함께 챙긴 것: 읽기 전용 모드(query_only), 워커별 connection, 검색어와 색인에 **같은 유니코드 정규화**(악센트 제거·한글 합성) 적용. 사전 자체도 활용형 폭주를 정리해 크기를 줄였다.

6. **메모리 속 in-flight 상태.** 요청 ID → 응답 future 맵이 메모리에만 있으니, 재배포가 그 맵을 지워 진행 중이던 사용자 명령은 **응답 받을 곳 없이 timeout**된다.\
   또 "연결됨"은 "새 프로세스"를 증명하지 않는다 — 단순 재연결도 connected가 되어 재배포 완료로 오판한다. 교정: 연결마다 새 세대 ID(uuid) + pid를 보내 **값의 변화**로 확인. 영속 큐는 과제로 남기고, 당장은 재배포 시간 단축·UI 재시도로 대응했다.\
   부수: detach한 재기동 스크립트가 응답 전에 죽지 않게 대기 마진을 두고, pull 실패 시 재기동을 중단했다.

7. **전부 영속화할 필요는 없다.** 영속화 비용(스키마·만료 정리·공유 저장소 운영)이 크고 당장 인스턴스가 하나라면, "단일 인스턴스 전제"를 **문서로 명시**하는 것도 정당한 선택이다 — 이 사례에서도 결과 토큰만 먼저 DB로 옮기고 나머지는 전제 문서화 + 공유 캐시 교체 예정으로 남겼고, 동시 1작업 서버는 단일 워커 기동을 README에 적었다.\
   반드시 남길 것: **어떤 상태가 프로세스 로컬인지 목록**과 **전제가 깨질 때(스케일아웃·재시작) 무엇이 바뀌는지** — 그래야 확장하는 순간 이 목록이 체크리스트가 된다.

## 문제 구조 (추상화 코드)

### 변형 A — 인메모리 토큰·세션 레지스트리가 재기동에 소실
① 문제 코드
```java
class TokenRegistry {
    private final Map<String, String> active = new ConcurrentHashMap<>();
    boolean isActive(String user, String jti) {
        return jti.equals(active.get(user));      // 재시작 후 미존재 → false → 전 토큰 폐기
    }
}
```
② 고친 코드
```java
boolean isActive(String token) {
    return repo.findByHash(sha256(token))         // DB 영속, 원문 대신 해시
               .filter(t -> t.expiresAt().isAfter(now()))
               .isPresent();
}
String issue(User u) { return repo.save(newToken(u, ttl)); }   // 매 발송 새 토큰(재사용 안 함)
@Scheduled(1h) void purgeExpired() { repo.deleteByExpiresAtBefore(now()); }   // 1시간 주기 만료 정리
// 통합 테스트: em.flush(); em.clear(); 후 검증 = 재기동 시뮬레이션
```
무엇이 깨졌나: 프로세스 수명보다 긴 수명이 필요한 상태를 프로세스 메모리에 뒀다.\
같은 구조: 세션 저장소가 메모리에 있어 서버 재시작 뒤 기존 JWT가 전부 revoked → 401(수정 상세 미기록).

### 변형 B — 인스턴스 경계를 넘지 못하는 레이트리미터·락
① 문제 코드
```python
_rate = defaultdict(int)          # 인스턴스별 카운트 → 분산되면 한도 N배
_job_lock = threading.Lock()      # "동시 1작업" — 다른 프로세스에선 free
```
② 고친 코드 (전제 명문화)
```text
# README: 이 서버는 단일 워커로 기동한다
# 레이트리미터·OTP·리셋 허용 목록은 단일 인스턴스 전제 — 공유 캐시로 교체 예정
```
무엇이 깨졌나: 공유 범위가 필요한 상태를 인스턴스 로컬로 둬, 스케일아웃 시 보장이 사라진다.

### 변형 C — 멀티 워커가 읽기 전용 대용량 데이터를 힙에 복제
① 문제 코드
```python
DICT = load_json("synonyms.json")     # 워커마다 사본 → 메모리 × 워커 수
```
② 고친 코드
```python
@lifespan
def init():
    global DB
    DB = sqlite3.connect(path, check_same_thread=False)   # 워커당 connection
    DB.execute("PRAGMA query_only=1")                      # 읽기 전용
# 물리 메모리는 OS page cache 가 한 번만 보유
# 검색어·색인 모두 같은 정규화(악센트 제거 NFD → 한글 합성 NFC)
```
무엇이 깨졌나: 프로세스 간 공유가 안 되는 힙에 공유 데이터를 뒀다(수치는 설계 시 추정).

### 변형 D — 요청-응답 상관 상태를 메모리에 · "연결됨"을 새 프로세스로 오인
① 문제 코드
```python
pending: dict[str, asyncio.Future] = {}
async def call(cmd):
    fut = loop.create_future(); pending[cmd.id] = fut   # 재배포 → 맵 소실 → timeout
    await send(cmd); return await fut
# 재배포 확인: status.connected == True  → 순단 재연결도 "완료"
```
② 고친 코드
```python
before = status().session_id
redeploy()
wait_until(lambda s: s.connected and s.session_id != before)   # 세대 ID(+pid) 변화로 확인
# in-flight: 재배포 시간 단축 + UI 재시도 (영속 큐는 과제)
```
무엇이 깨졌나: 재시작을 넘어야 하는 상관 상태가 메모리에 있었고, 연결 여부를 인스턴스 동일성으로 착각했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
