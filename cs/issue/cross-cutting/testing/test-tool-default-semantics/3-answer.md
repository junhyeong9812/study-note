# cs/issue/testing/test-tool-default-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **비선점 타임아웃.** JUnit 5 `@Timeout`의 기본 스레드 모드(SAME_THREAD)는 테스트를 같은 스레드에서 실행하고, 시간이 넘으면 다른 스레드가 그 스레드에 **인터럽트만 보낸다** — 강제로 끊지 못하고, 실패 판정은 메서드가 **끝난 뒤**에 난다.\
그래서 인터럽트를 확인하지 않는 CPU 루프(무한 루프·폭주하는 계산)는 실패가 아니라 **무한 대기**가 된다 — 20초 제한인 테스트가 10분 넘게 돌았다(`sleep`·블로킹 I/O처럼 인터럽트에 반응하는 코드는 제때 끊긴다).\
어노테이션이 없는 테스트엔 제한이 아예 없다.\
`junit.jupiter.execution.timeout.thread.mode.default=SEPARATE_THREAD`로 선점형(별도 스레드에서 실행하고 시간이 되면 테스트를 실패 처리 — 단 멈추지 않는 작업 스레드 자체는 계속 돌 수 있다)으로 바꾸고, `timeout.testable.method.default`로 전역 기본 제한을 둔다(개별 `@Timeout`이 우선).\
무한 루프는 단언으로는 못 막고 **시간 제한만** 막는다.
   > **preemptive timeout** — 제한 시간이 되면 실행 중인 작업을 끊고 실패시키는 타임아웃. 비선점형은 작업이 스스로 끝나야 판정한다.

2. **중첩 클래스 섀도잉.** 하위 테스트가 부모 계약 테스트의 `@Nested` 내부 클래스와 같은 이름의 내부 클래스를 선언하면, 상속된 중첩 클래스가 **가려져** 러너가 부모 쪽을 발견하지 못한다.\
그 결과 계약 테스트가 **실행되지 않는다** — 실패도 에러도 없이 개수만 줄어, 전체는 초록이다(이름을 바꾸자 58 → 61).\
실패는 눈에 띄지만 소실은 통과 개수를 자세히 보지 않으면 영원히 모른다.\
교정은 이름 변경 + 전 테스트를 스캔해 충돌을 찾는 린트를 필수 검사로 넣는 것이다.
   > **shadowing** — 하위 범위의 같은 이름 선언이 상위 범위의 선언을 가려 보이지 않게 하는 것.

3. **patch는 조회 경로에.** `patch("a.b.name")`은 **모듈 `a.b`의 네임스페이스에서 `name`을 바꾼다** — 코드가 그 이름을 **조회하는 곳**에 걸어야 효과가 있다.\
헬퍼 모듈이 `from asyncio import create_subprocess_exec`처럼 이름을 자기 네임스페이스로 가져오면 실제 조회는 헬퍼 모듈에서 일어나므로, `asyncio` 쪽에 건 mock은 빗나간다(반대로 호출 시점에 `asyncio.create_subprocess_exec`로 모듈 속성을 조회하면 원래 patch도 맞는다) → mock 대상을 헬퍼로 옮긴다(빗나간 메커니즘 설명은 일반론 — 원 기록은 "헬퍼 도입 후 mock이 안 맞음 → 대상을 헬퍼로 변경"까지).\
모듈을 분리하면 `jest.mock('옛/경로')`도 빗나간다.\
문자열 경로는 코드가 아니라 **데이터**라서 리팩토링 도구의 이름 변경이 따라가지 않는다 — 이름을 바꾼 뒤 없는 심볼을 patch하는 픽스처가 한 파일 전체를 setup 에러로 만들었다.\
설정값(포트 등)을 테스트에 복제하는 것도 같은 결합이다 → 테스트가 설정 모듈을 읽는다.

4. **lifespan 미실행.** FastAPI(ASGI)의 lifespan(startup → yield → shutdown)은 서버가 lifespan 이벤트를 보낼 때만 돈다.\
`TestClient`는 **`with` 컨텍스트로 쓸 때만** 이 이벤트를 보내고, httpx `ASGITransport`는 요청만 전달하고 lifespan을 트리거하지 않는다.\
그래서 기동 시 등록하던 전역 레지스트리가 테스트에선 비어 "미등록" 오류가 나고, 정리를 lifespan에만 둔 자식 프로세스는 테스트 후 **누수**된다.\
테스트 픽스처에서 등록을 직접 하거나, 픽스처 finalizer에서 정리(shutdown)를 직접 보장한다.
   > **lifespan** — ASGI 앱의 기동·종료 훅. 서버(또는 그것을 흉내 내는 테스트 도구)가 이벤트를 보내야 실행된다.

5. **호이스팅과 TDZ.** `vi.mock` 호출은 import보다 먼저 실행되도록 **파일 최상단으로 끌어올려진다**.\
그런데 팩토리가 참조하는 `const push = vi.fn()`은 원래 자리에 남아 있어, 팩토리가 실행될 때(모듈이 처음 import될 때)는 아직 초기화 전(TDZ)이다 — 팩토리 본문이 그 변수를 **즉시** 읽으면 오류가 난다(나중에 호출되는 함수 안에서만 읽으면 호출 시점엔 초기화돼 있어 오류가 안 날 수도 있다).\
`const { push } = vi.hoisted(() => ({ push: vi.fn() }))`는 그 변수 생성도 **같이 끌어올려** 팩토리보다 먼저 만들어지게 보장한다.
   > **TDZ** — temporal dead zone. `let`/`const`가 선언은 됐지만 초기화 전이라 접근하면 오류가 나는 구간.

6. **Mockito 스텁 상태 머신.** 같은 호출을 두 번 스텁하면 **마지막 것만** 유효하고, 엄격 스텁 설정이 아니면 경고도 없다 — 복붙한 중복 스텁이 의도와 다른 값을 돌려도 테스트는 통과했다.\
스텁은 "마지막 호출을 기억했다가 `willReturn`으로 완성"하는 상태 머신이라, `given(a.x()).willReturn(makeMock())`에서 `makeMock()` 안에서 또 `given(...)`을 하면 앞의 스텁이 미완 상태로 남아 `UnfinishedStubbingException`이 난다 → mock을 먼저 만들어 변수로 넘긴다.\
`body(Object)`와 `body(T)`처럼 오버로드된 메서드에 제네릭 `any()`를 넘기면 **컴파일러가 정적으로 고른 오버로드**(대개 가장 구체적인 것)가 스텁되는데, 운영 코드가 부르는 오버로드와 다르면 deep stub·`any()` 스텁이 매칭되지 않는다 → `any(byte[].class)`처럼 타입을 명시하거나, fluent HTTP 클라이언트는 mock 대신 **서버 목**(요청 기대·응답 지정·verify)을 쓴다.

7. **기본값은 부분 재현이다.** `dictConfig`의 `disable_existing_loggers: True`(기본값)는 설정에 이름이 없는 기존 로거를 비활성화하고, 설정에 root 구성이 있으면 root 핸들러도 교체해, pytest가 붙인 캡처 핸들러까지 무력화할 수 있다(호출 순서에 따라 다름) → 로거 호출 자체를 patch해 검증하거나 설정 테스트는 핸들러 존재·레코드 속성으로 본다.\
`@DataJpaTest` 같은 슬라이스는 **관련 자동설정만** 로드하고 사용자 `@Configuration`은 가져오지 않는다 → 필요한 설정을 `@Import`로 명시.\
테스트 컨테이너 DB는 **서버 기본값**(최대 패킷 크기 등)으로 떠서 운영엔 없는 실패(큰 마이그레이션의 패킷 초과)를 낸다 → 기동 옵션을 기존 베이스와 동일화.\
공통 교훈: 테스트 도구는 운영 기동 경로의 **일부만** 재현하고 나머지는 자기 기본값으로 채운다 — 테스트가 이상하게 실패하거나 조용히 통과하면 먼저 "도구가 무엇을 빼고/바꿔 띄웠나"를 본다.

## 문제 구조 (추상화 코드)

### 변형 A — 비선점 타임아웃 (끝나지 않는 코드가 무한 대기)
① 문제 코드
```kotlin
@Test @Timeout(20)                       // 기본 SAME_THREAD: 초과 시 인터럽트만, 판정은 끝난 뒤
fun prefixQuery() { naiveIndex.query(bigInput) }   // O(n²) 변종·x=0 무한 루프 → 영원히 대기
@Test fun noLimit() { skipped.insertAll(input) } // 레벨 상한 없는 변종 → 제한 자체가 없음
```
② 고친 코드
```kotlin
// 빌드 공용 설정 (개별 @Timeout 우선)
tasks.test {
    systemProperty("junit.jupiter.execution.timeout.thread.mode.default", "SEPARATE_THREAD")
    systemProperty("junit.jupiter.execution.timeout.testable.method.default", "30s")
}
```
무엇이 깨졌나: 타임아웃이 선점형이라는 가정이 틀려, 시간 제한이 무한 루프를 끊지 못했다.

### 변형 B — 중첩 테스트 클래스 이름 충돌로 소실
① 문제 코드
```kotlin
abstract class PolicyContractTest { @Nested inner class Delay { /* 계약 테스트 */ } }
class FixedPolicyTest : PolicyContractTest() {
    @Nested inner class Delay { /* 하위 전용 */ }  // 부모 Delay 를 가림 → 계약 테스트 미실행
}
```
② 고친 코드
```kotlin
class FixedPolicyTest : PolicyContractTest() {
    @Nested inner class FixedDelay { /* 하위 전용 */ }
}
// 린트: 하위 테스트의 중첩 클래스 이름이 부모 계약 클래스의 것과 겹치면 실패
```
무엇이 깨졌나: 상속된 테스트가 가려져 실패 대신 조용히 사라졌다.

### 변형 C — mock 대상이 조회 경로와 어긋남
① 문제 코드
```python
# 코드: 헬퍼 도입 후 호출은 app.deploy.git._run 안에서
with patch("asyncio.create_subprocess_exec"):          # 빗나감
    ...
with patch("app.main.init_cache"):                     # 이름 변경 후 없는 심볼 → setup 에러 상시화
    ...
assert cfg_port == 8081                                # 설정값 복제
```
② 고친 코드
```python
with patch("app.deploy.git._run"):                     # 조회되는 곳에 건다
    ...
with patch("app.main.init_status_cache"):              # 새 이름
    ...
assert cfg_port == app.config.BLUE_PORT                # 설정을 읽는다
```
```ts
jest.mock("src/utils/auth");                           // 모듈 분리 후 새 경로 (grep 범위에 테스트 폴더 포함)
```
무엇이 깨졌나: mock·설정이 구현 위치에 문자열로 결합돼, 위치가 바뀌자 테스트만 어긋났다.

### 변형 D — 테스트 클라이언트가 lifespan을 실행하지 않음
① 문제 코드
```python
client = TestClient(app)                                    # with 없이 → lifespan 미실행
transport = httpx.ASGITransport(app=app)                    # lifespan 트리거 없음
# 기동에서 하던 registry.register(...) 가 비어 "미등록", 자식 프로세스 정리 코드도 안 돎
```
② 고친 코드
```python
@pytest.fixture
def make_client(request):
    registry.register_all()                                 # 기동 초기화를 테스트에서 명시
    client = TestClient(app)
    request.addfinalizer(app.state.sessions.shutdown)       # terminate → wait → kill 직접 보장
    return client
```
무엇이 깨졌나: 테스트 도구가 운영 기동 경로의 초기화·정리 단계를 재현하지 않았다.

### 변형 E — 모킹 호이스팅(TDZ)
① 문제 코드
```ts
const push = vi.fn();
vi.mock("router-lib", () => ({ router: { push } }));   // 최상단으로 끌어올려짐, 팩토리가 push 를 즉시 읽음 → TDZ
```
② 고친 코드
```ts
const { push } = vi.hoisted(() => ({ push: vi.fn() }));          // 변수 생성도 함께 끌어올림
vi.mock("router-lib", () => ({ router: { push } }));
```
무엇이 깨졌나: 선언 순서대로 실행된다는 직관과 달리 mock 선언이 먼저 실행됐다.

### 변형 F — Mockito 스텁 상태 머신·오버로드 매칭
① 문제 코드
```java
given(repo.find(id)).willReturn(a);
given(repo.find(id)).willReturn(b);              // 마지막만 유효, 경고 없음
given(outer.inner()).willReturn(mockInner());    // mockInner() 안에서 given(...) → UnfinishedStubbing
RestClient client = mock(RestClient.class, RETURNS_DEEP_STUBS);
given(client.post().body(any()).retrieve()...);  // any() 로 컴파일러가 고른 오버로드 ≠ 운영 코드의 body(Object)
```
② 고친 코드
```java
given(repo.find(id)).willReturn(b);              // 중복 제거
Inner inner = mockInner();                       // 먼저 만들고
given(outer.inner()).willReturn(inner);          // 변수로 전달
RestClient.Builder builder = RestClient.builder();
MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
Adapter adapter = new Adapter(builder.build());  // 서버 목: 요청 기대 → 응답 지정 → verify()
server.expect(requestTo(URL)).andExpect(method(POST)).andRespond(withSuccess(json, APPLICATION_JSON));
given(crypto.decrypt(any(byte[].class), anyString()));   // 모호한 매처는 타입 명시
```
무엇이 깨졌나: 스텁이 호출 기록 기반 상태 머신이라는 것과, 매처가 오버로드를 특정하지 못한다는 것을 몰랐다.\
같은 구조: 테스트가 red 단계에서 "예측한 이유"로 실패하는지 확인하다가 미완 스텁을 발견 — red의 이유도 검증 대상이다.

### 변형 G — 로깅·슬라이스·컨테이너의 부분 기동
① 문제 코드
```python
logging.config.dictConfig({"version": 1, "disable_existing_loggers": True, ...})
with caplog.at_level("INFO"): handle(req)
assert "access" in caplog.text                  # 로거 비활성화·핸들러 교체로 캡처가 비어 실패
```
```java
@DataJpaTest class RepoTest { }                 // 사용자 설정 빈(쿼리 도구·감사·ID 생성기) 없음
static DbContainer db = new DbContainer("db:8");  // 서버 기본 패킷 크기 → 큰 마이그레이션 실패
```
② 고친 코드
```python
with patch("app.access_log.logger") as log:     # 로거 호출 자체를 검증
    handle(req)
log.info.assert_called_once()
```
```java
@DataJpaTest @Import({QueryConfig.class, AuditingConfig.class, IdSourceConfig.class}) class RepoTest { }
static DbContainer db = new DbContainer("db:8")
    .withCommand("--character-set-server=utf8mb4", "--max-connections=1000", "--max-allowed-packet=64M");  // 기존 베이스와 동일
```
무엇이 깨졌나: 테스트 도구가 설정·빈·서버 옵션을 자기 기본값으로 채워, 운영과 다른 환경에서 테스트가 돌았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
