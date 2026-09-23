# cs/issue/testing/test-isolation-and-determinism — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **재사용 픽스처의 대가.** reuse 컨테이너는 이전 실행과 **다른 브랜치**의 상태(마이그레이션 이력·잔여 데이터)를 그대로 들고 있다.\
다른 브랜치가 V38을 먼저 적용한 컨테이너를 재사용하면, 머지 브랜치의 V33~37은 "해결됐지만 적용되지 않은 마이그레이션"으로 검증 실패한다(가짜 실패).\
아직 배포 안 한 마이그레이션을 고치면 컨테이너에 남은 옛 체크섬과 어긋나 컨텍스트 로드가 실패하고 전 테스트가 에러가 난다.\
반대로 테스트 설정에서 필요한 옵션(자리표시자 치환 끄기)이 빠진 결함은 이미 마이그레이션이 적용된 reuse 컨테이너에선 **드러나지 않고** fresh 컨테이너에서만 파싱 실패로 표면화했다(가짜 성공).
   > **test fixture reuse** — 테스트 인프라(컨테이너 등)를 실행 사이에 살려 두고 다시 쓰는 것. 빠르지만 상태가 누적된다.

2. **전부 에러면 픽스처부터.** 통합 테스트가 한꺼번에 에러라면 코드 결함보다 **재사용 컨테이너의 누적 상태**를 먼저 의심하고, 재사용을 끄거나 컨테이너를 모두 지우고 fresh로 다시 돌려 본다.\
재사용은 설정 해시 **라벨**로 후보 컨테이너를 찾는다 — 정지된(exited) 컨테이너 하나를 지워도, 같은 해시 라벨로 **살아 있는** 컨테이너가 남아 있으면 그것이 계속 재사용돼 같은 에러가 이어진다(후보 조건의 세부는 라이브러리·버전마다 다를 수 있다).\
그래서 그 해시 라벨의 컨테이너를 `-a`(실행 중·정지 모두)로 **전부** 지워야 한다.\
컨테이너 기동 명령(옵션)을 바꾸면 해시가 바뀌어 새 컨테이너가 뜬다는 점도 알아 둔다.

3. **영속 경로 하나의 누수.** 소켓 경로만 분리하고 상태 디렉터리를 공유하면, 두 번째 인스턴스가 **하나뿐인 장부**를 함께 읽고 압축한다(실제 발생).\
새 인스턴스가 이전 인스턴스의 장부를 읽어 그 세션들을 자기 것으로 인수하면, 인수한 세션엔 실제 터미널이 없어 붙기(attach)가 거부된다 — 특정 e2e가 결정론적으로 실패한 유력 원인으로 기록됐다(확정은 아님).\
격리는 "주요 경로 몇 개"가 아니라 프로세스가 쓰는 **모든 영속 경로**여야 한다 — 테스트는 실행별 디렉터리 + 상태 디렉터리 환경변수 통째 교체로 격리했고, 테스트가 개발자의 실제 상태 디렉터리에 쓰면 안 된다는 규칙을 남겼다.

4. **happens-before 부재.** 테스트 스레드가 `close()`에서 `cancelled = true`를 쓰고 태스크 스레드가 `checkCancelled()`로 읽는데, 둘 사이에 동기화가 없으면 **어느 쪽이 먼저 보일지 보장이 없다**.\
submit 직후 바로 close하면 가끔 태스크가 먼저 게이트를 통과해 기대한 취소 예외가 나지 않는다(로컬 5만 회 중 4회, 부하 CI에선 더 잦음).\
`Thread.sleep` 마진은 확률을 낮출 뿐 여전히 타이밍 의존이고 느리다.\
테스트에서 스레드를 띄우는 지점(`doExecute`)을 오버라이드해 **태스크를 캡처만** 하고, close 후 테스트 스레드에서 직접 실행하면 순서가 구조적으로 고정된다 — 운영 취소 경로는 그대로 검증하면서 5만 회 0실패.
   > **happens-before** — 한 스레드의 쓰기가 다른 스레드의 읽기에 반드시 보이도록 보장하는 순서 관계. 락·volatile·스레드 시작/join 등이 만든다.

5. **경합을 못 만드는 하네스.** ① 작업을 `chunked()`로 나누면 충돌해야 할 **중복 쌍이 같은 스레드**에 몰려 순차 실행된다 → 인덱스 라운드로빈 배분(20/20 위반 재현).\
② 경합 창이 좁으면 적은 시도로는 안 걸린다 → 라운드 확대(500회), 배리어로 동시 출발.\
③ 가짜 시계는 순식간에 감기는데 실제 스레드가 따라오지 못해 결과가 매번 다르다.\
"시계를 주입했으면 일도 시계에 태워라" — 시계가 틱할 때 **그 틱이 작업을 촉발**하게 만들어(스크립트된 티커) 단일 스레드에서 결정적으로 진행시키라는 뜻이다.

6. **관측 시점 미확정.** 동시성 제한 1에서 같은 스레드가 두 작업을 제출하면 제한 로직이 **제출 스레드 자체를 블록**해 테스트가 멈춘다(7분 정지).\
"태스크 본문 실행됨" latch 뒤에 측정하면 permit 반납은 `finally`에 있어 아직 안 일어났을 수 있다 — 버그가 있어도 통과할 수 있다 → 태스크 스레드를 `join()`.\
`join(5000)`은 타임아웃이어도 예외 없이 반환하므로 반드시 뒤에 `isAlive() == false`를 단언한다.\
캐시의 쓰기 버퍼는 읽기 히트가 드레인을 보장하지 않으므로, 단언 전에 유계 예산 안에서 **완전 드레인**(크기가 한도 이하로 수렴할 때까지)시킨다.\
스레드 안의 예외는 `AtomicReference`로 캡처해 메인에서 단언한다 — 하네스도 검증 대상이다.

7. **시드·실데이터 결합.** 테스트가 시드 데이터의 ID·이름을 상수로 참조하면, 다른 작업의 재시드가 **컴파일 연결 없이** 그 테스트를 깬다 — 변경 범위만 도는 부분 스위트는 이 원격 결합을 보지 못한다.\
재시드 때는 시드 상수를 참조하는 테스트를 전수 grep하고, 초록 선언은 전체 스위트로 하며, 머지 후 실패는 베이스 브랜치 단독 실행으로 "우리 탓/원래 있던 탓"을 귀속한 뒤 고친다.\
시드 검증은 총 개수 대신 **결정적 노드의 존재·가시성·순서**로 단언하면 다른 시드 변경에 덜 깨진다.\
매일 갱신되는 실데이터에 정확한 개수를 단언하면 매일 실패한다 → "기대값 이상"·허용 범위 단언, 대형 쿼리에 맞춘 타임아웃, 세션 범위 클라이언트 재사용, 병렬 대신 순차 실행.\
다만 "재색인 중이면 500도 허용" 같은 완화는 그 자체가 그린 위장이 될 수 있다(일반론 — 원 기록엔 이 위험 언급이 없다).

## 문제 구조 (추상화 코드)

### 변형 A — 재사용 컨테이너가 실행 이력을 누적
① 문제 코드
```java
static final DbContainer DB = new DbContainer("db:8").withReuse(true);   // 실행·브랜치 간 공유
// 다른 브랜치가 V38 적용 → 이 브랜치의 V33~37 "not applied" 검증 실패
// 미배포 마이그레이션 수정 → 옛 체크섬 잔존 → 컨텍스트 로드 실패
// 테스트 설정 누락(placeholder 치환)은 이미 적용된 컨테이너에선 드러나지 않음
```
② 고친 코드
```sh
# 전부 에러면 먼저: 재사용 끄고 fresh 로 재현
REUSE_ENABLE=false ./run-it.sh
# 실행 중·정지 컨테이너를 해시 라벨로 전부 제거
docker ps -a --filter "label=org.testcontainers.hash=$HASH" -q | xargs -r docker rm -f
# IT 앞에 사전 정리 단계(잔여 데이터 제거)
```
무엇이 깨졌나: 테스트 결과가 코드가 아니라 컨테이너의 이력에 좌우됐다.

### 변형 B — 영속 경로 일부만 격리
① 문제 코드
```rust
fn state_dir() -> PathBuf { env_or("XDG_STATE_HOME", initial_state()) }   // override 는 이것뿐
// 테스트: 소켓만 임시 경로로, 상태 디렉터리는 공유 → 이전 인카네이션 장부 인수 → attach 거부
```
② 고친 코드
```sh
# e2e: 실행(pid)별 디렉터리 + 상태 디렉터리 환경변수를 통째 교체
tmp=$(mktemp -d); XDG_STATE_HOME="$tmp/state" SOCKET="$tmp/sock" run_daemon
# 규칙: 테스트는 개발자의 실제 상태 디렉터리에 쓰지 않는다
```
무엇이 깨졌나: 격리하지 않은 한 경로를 통해 인스턴스끼리 상태를 공유했다.

### 변형 C — 스레드 간 순서 미보장 → 테스트 seam으로 직렬화
① 문제 코드
```java
Future<?> future = executor.submit(task);
executor.close();                                   // 다른 스레드의 cancelled 읽기와 순서 보장 없음
assertThrows(CancellationException.class, future::get);   // 간헐 실패
```
② 고친 코드
```java
AtomicReference<Runnable> captured = new AtomicReference<>();
Executor executor = new Executor() {
    @Override protected void doExecute(Runnable r) { captured.set(r); }   // 스레드 대신 캡처
};
executor.submit(task);
executor.close();                                   // cancelled = true
assertThrows(CancellationException.class, captured.get()::run);   // 같은 스레드에서 실행 → 결정적
```
무엇이 깨졌나: 판정이 스케줄러의 선택에 달려 있었다.

### 변형 D — 경합 재현 하네스가 경합을 못 만듦
① 문제 코드
```kotlin
ops.chunked(ops.size / THREADS).forEach { chunk -> thread { chunk.forEach(::run) } }   // 중복 쌍이 한 스레드로
repeat(1) { runRound() }                                                              // 좁은 창엔 부족
fakeClock.advance(10.minutes)                   // 가짜 시계는 순식간, 실스레드는 못 따라감
```
② 고친 코드
```kotlin
ops.forEachIndexed { i, op -> queues[i % THREADS].add(op) }   // 라운드로빈 배분
repeat(500) { barrier.await(); runRound() }                   // 배리어 동시 출발 + 라운드 확대
val ticker = ScriptedTicker(); ticker.onTick { worker.step() } // 시계가 일을 촉발 (단일 스레드)
```
무엇이 깨졌나: 충돌해야 할 연산이 실제로 겹쳐 실행될 기회가 없었다.

### 변형 E — 관측 시점에 상태가 확정되지 않음
① 문제 코드
```java
started.await();                        // 본문 실행됨 — permit 반납(finally)은 아직일 수 있음
assertThat(limiter.available()).isEqualTo(1);
t.join(5000);                           // 타임아웃이어도 조용히 반환
```
② 고친 코드
```java
AtomicReference<Throwable> failure = new AtomicReference<>();
Thread t = new Thread(() -> { try { body(); } catch (Throwable e) { failure.set(e); } });
t.start();
t.join(5000);
assertThat(t.isAlive()).isFalse();      // 정말 끝났는가
assertThat(failure.get()).isNull();
drainFully(cache, budget);              // 비동기 쓰기 버퍼를 한도 이하로 수렴시킨 뒤 단언
assertThat(cache.size()).isLessThanOrEqualTo(capacity);
```
무엇이 깨졌나: 하네스의 타이밍을 결함 유무로 읽었다.\
같은 구조: 동시성 제한 1에서 제출 스레드가 블록돼 테스트 정지 → 리플렉션 폴링 대신 인라인 실행 seam으로 결정론 테스트.

### 변형 F — 외부 상태(시드·실데이터)에 결합한 단언
① 문제 코드
```java
static final String SEED_PARENT = "NODE_202";              // 다른 작업의 재시드가 소멸시킴
assertThat(repo.count()).isEqualTo(EXACT_COUNT);             // 매일 갱신되는 실데이터
```
```python
client = httpx.Client(base_url=BASE)                         # 기본 5초 — 대형 쿼리 초과
```
② 고친 코드
```java
assertThat(seedTree.find(SEED_PARENT_V2)).isPresent();       // 결정적 노드 존재·순서로 단언
assertThat(repo.count()).isGreaterThanOrEqualTo(BASELINE);   // 하한
// 재시드 체크리스트: 시드 상수 참조 테스트 전수 grep → 전체 스위트로 초록 선언
// 머지 후 실패: 베이스 브랜치 단독 실행으로 귀속 판정 후 수정
```
```python
@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE, timeout=60.0) as c:     # 세션 재사용 + 긴 타임아웃, 순차 실행
        yield c
```
무엇이 깨졌나: 테스트 입력이 고정되지 않아(다른 작업의 시드, 매일 바뀌는 데이터) 결과가 비결정적이었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
