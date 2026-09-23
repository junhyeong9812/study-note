# cs/issue/cross-cutting/reliability/resource-bounding-last-defense — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답

<!-- 질문 1:1 대응 -->

1. 클라이언트 타임아웃은 **연결(connection)** 을 끊을 뿐, 서버가 이미 시작한 **작업(work)** 을 멈추지 않는다. 서버는 요청을 받으면 그 처리를 자기 자원(CPU·GPU·메모리) 위에서 진행하는데, 클라이언트가 사라져도 그 작업은 별개의 실행 흐름이라 계속 돈다. 실제로 wrapper가 5초에 연결을 끊어도 모델 서빙 런타임은 서버측 생성을 이어가 3만 토큰 넘게 뽑았다. 즉 "요청을 취소했다"는 클라이언트의 관점일 뿐, 서버 자원은 여전히 물려 있다.
   > **클라이언트측 통제 vs 서버측 통제** — 전자는 자기 대기를 포기하는 것, 후자는 자원 소비 자체를 끊는 것. 자원 보호는 후자에서만 가능하다.

2. 상한은 **자원을 실제로 생성·소비하는 쪽(서버)** 에 둬야 한다. 넷의 공통 원리: *"소비를 시작시키는 그 지점에서, 소비량의 최대치를 미리 못박는다."* num_predict는 토큰 생성량을, body limit은 메모리 적재량을, 세마포어는 동시 실행 수를, single-flight는 동시 작업 수를 각각 상한선으로 고정한다. 모두 "얼마까지 허용할지"를 자원 소유자가 결정하고, 그 이상은 만들지 않거나 거절한다.

3. **큐잉**은 초과 요청을 대기줄에 쌓아 나중에 처리하고, **fast-fail**은 즉시 거절한다. 자원이 1개(GPU 1장)인데 큐를 두면 두 문제가 생긴다: (a) 하류(모델 서빙 런타임)가 이미 요청을 하나씩 직렬화하는데 래퍼가 또 큐를 두면 같은 일을 두 겹으로 하고, (b) 줄이 길어지면 뒤에 온 사용자 요청이 앞선 무거운 작업의 대기줄에 **인질로** 잡힌다. "넘치면 즉시 503/409"는 자원을 지키고(대기 자체를 안 만듦) 실패를 시끄럽게 만들어(호출자가 바로 재시도·백오프 판단) 오히려 안전하다.
   > **fast-fail(빠른 실패)** — 수용 못 할 요청을 대기시키지 않고 즉시 거절 응답을 돌려주는 것. 대기줄이 자원을 잠식하는 것을 막는다.

4. 인증 안 된 아무나 **거대한 본문**을 보내 서버 메모리를 압박(자원 고갈 시도)할 수 있다 — 비밀 검증이 본문을 다 읽은 *뒤에* 일어나므로, 검증에 실패할 요청조차 메모리를 이미 물어버린다. 막으려면 상한 검사를 **본문을 읽기 전**에 놓는다: 헤더에 선언된 `content-length`를 먼저 보고 상한(예: 4KB) 초과면 읽지도 않고 413으로 거절, 그다음 실제로 읽은 크기를 한 번 더 재확인(선언값 위조 대비). 검사를 인증·적재보다 앞으로 당기는 것이 핵심이다.
   > **413 Payload Too Large** — 본문이 서버가 허용한 상한을 넘었다는 HTTP 상태 코드.

5. 각각 실패한다: **클라이언트 타임아웃** — 연결만 끊고 서버 생성을 못 멈춘다(Q1). **프롬프트 소프트 스위치**(`/no_think` 문자열) — 서빙 런타임의 챗 템플릿이 그것을 특별 취급하지 않으면 그냥 일반 텍스트로 흘러 아무 효과가 없다(주술). 모델 제어는 런타임의 공식 API(`think:false`)로 해야 한다. **상위 프레임워크 기본값** — 기본이 무제한이면(타임아웃 없음, `0.0.0.0` 전체 바인딩) 설정을 깜빡하는 순간 그대로 노출된다. 그래서 이런 것들 위가 아니라 **자원 지점의 하드 상한**이 최후 방어선이 된다("num_predict가 최후 방어선").

6. `complete()`를 빠뜨리면 **열린 연결과 그 연결을 붙들고 있는 스레드**가 샌다 — 응답이 끝났다고 서버에 알리지 못해 자원이 반납되지 않는다. 스트리밍은 "응답을 여러 조각으로 나눠 흘리는" 열린 자원이므로, 정상 종료(`complete()`)든 오류 종료(`completeWithError`)든 **반드시 닫아야** 그 자원이 회수된다. "열었으면 닫는다"는 파일·소켓·락과 같은 계열의 자원 경계다.
   > **자원 누수(resource leak)** — 다 쓴 자원(연결·스레드·메모리)을 반납하지 않아 시간이 갈수록 고갈되는 것.

7. 요청마다 백그라운드 작업(goroutine)을 무한정 띄우면, 요청이 몰릴 때 그 수가 무제한으로 늘어 **메모리·연결이 고갈**된다. "서비스별 최대 1개"로 유계화하면 진행 중일 때 새 요청은 즉시 409로 거절되므로, 동시에 존재하는 백그라운드 작업 수의 상한이 서비스 수만큼으로 고정된다. **무한정 쌓일 수 있는 것에는 상한이 필요하다** — 이 프로젝트에서는 그 대상이 goroutine(배포 오케스트레이터), 본문 바이트(공개 경로), 생성 토큰(모델 호출 래퍼), 동시 요청 수(래퍼의 세마포어)로 각각 나타났고, 방어는 전부 "상한을 못박고 초과는 거절"이었다.
   > **유계(bounded)** — 최댓값이 정해져 있어 무한정 커질 수 없는 상태. 무계(unbounded) 자원은 고갈의 원천이다.

## 문제 구조 (추상화 코드)

### 변형 A — 서버측 생성량 상한 + 넘치면 즉시 거절
① 문제 코드
```python
payload = {"prompt": "... /no_think", "format": schema}     # 프롬프트 속 소프트 스위치는 런타임이 무시
resp = await http.post(MODEL_URL, json=payload, timeout=5)  # 5초에 연결만 끊김 → 서버는 수만 토큰 계속 생성
```
② 고친 코드
```python
sem = asyncio.Semaphore(2)                                   # 자원(GPU 1장)에 맞춘 동시 처리 상한
async def rewrite(req):
    if sem.locked():
        raise Busy()                                         # 줄 세우지 않고 즉시 503
    async with sem:
        payload = {"stream": False, "think": False,          # 제어는 런타임 공식 필드로
                   "format": schema,
                   "options": {"num_predict": 512}}          # 서버측 생성량 상한 = 최후 방어선
        return await http.post(MODEL_URL, json=payload)
```
무엇이 깨졌나: 클라이언트 타임아웃을 상한으로 믿었지만, 연결을 끊는 것은 서버의 생성을 멈추지 않았다.\
같은 구조: 모델에 싣는 대화 이력·문서 문맥도 최근 N턴·최대 문자 수로 유계화했다.

### 변형 B — 크기를 클라이언트가 정하는 입력에 서버 상한이 없음
① 문제 코드
```ts
export async function handler(req) {
  const body = await req.text();          // 비밀 검증 전에 본문 전체를 메모리에 적재
  if (!verify(req.headers, body)) return new Response(null, { status: 401 });
  // ...
}
```
② 고친 코드
```ts
const MAX_BODY_BYTES = 4096;
export async function handler(req) {
  const declared = Number(req.headers.get("content-length") ?? 0);
  if (declared > MAX_BODY_BYTES) return new Response(null, { status: 413 });   // 읽기 전에 거절
  const body = await req.text();
  if (body.length > MAX_BODY_BYTES) return new Response(null, { status: 413 }); // 선언값 위조 대비 재확인
  if (!verify(req.headers, body)) return new Response(null, { status: 401 });
  // ...
}
```
무엇이 깨졌나: 상한 검사가 적재·인증보다 뒤에 있어, 거절될 요청도 자원을 먼저 소비했다.\
같은 구조(아래는 같은 방안의 다른 입력 표면):
```python
# 목록 길이·페이지 오프셋도 클라이언트가 정하는 크기 → 서버 상한 (계획 단계로 기록된 잠재 이슈)
class ReportReq(BaseModel):
    items: list[constr(max_length=100)] = Field(max_length=500)
    page: int = Field(ge=1); size: int = Field(ge=1)
    @model_validator(mode="after")
    def window(self):
        if self.page * self.size > MAX_RESULT_WINDOW:        # from+size 가 검색엔진 한도를 넘으면 500 이던 것
            raise ValueError("window exceeded")              # → 400
        return self
```
```java
// 전역 멀티파트 상한을 관리자 대용량 업로드용으로 올리면 익명 공개 엔드포인트도 그 크기까지 디스크 스풀된 뒤에야 거부된다
@Order(HIGHEST_PRECEDENCE)                                   // 멀티파트 파서보다 먼저
class PreParseSizeFilter extends OncePerRequestFilter {
  protected void doFilterInternal(req, res, chain) {
    long len = parseLong(req.getHeader("Content-Length"));   // 헤더 직접 파싱
    if (isMultipart(req) && !isAdminPath(req) && len > 50 * MB) { res.setStatus(413); return; }
    chain.doFilter(req, res);                                // 전역 상한은 backstop 으로 유지
  }
}
// 기록된 한계: Content-Length 없는(chunked) 업로드는 필터를 우회해 전역 상한에만 의존
// 테스트 함정: 테스트용 가짜 요청의 getContentLength 는 content 기반 → 헤더를 직접 파싱해야 검증된다
```
```java
// 대용량 파일을 힙에 올리지 않는다 (설계 근거로 기록 — 실제 OOM 발생 기록은 없음)
byte[] all = file.getBytes();                                // 문제: 파일 전체를 힙에 적재
file.transferTo(part);                                       // 고친: 디스크 스풀 → part 스트리밍
Files.move(part, target, ATOMIC_MOVE, REPLACE_EXISTING);     // 같은 디렉토리에서 원자 교체
// 설정: 멀티파트 임계값 0(항상 디스크 스풀), 스풀 위치는 업로드 루트 아래(tmpfs·다른 파일시스템 회피)
```
같은 구조: HTTP 서버에 읽기·유휴 타임아웃과 헤더 크기 상한이 없어 느린 연결이 인증 전에 자원을 오래 무는 문제 → 연결 계층에 상한 명시(구체 값은 원문에 미기록).

### 변형 C — 하류 호출에 타임아웃이 없어 호출 스레드가 무한 대기
① 문제 코드
```java
RestClient client = builder.build();                         // 연결·읽기 타임아웃 기본값 = 무한
client.get().uri(path).retrieve().body(Resp.class);          // 상대가 멈추면 스레드가 영원히 묶임
Process p = new ProcessBuilder(cmd).start();
p.waitFor();                                                 // 자식이 멈추면 무한 블록
```
② 고친 코드
```java
RestClient client = dedicatedBuilder                         // 공용 빌더 대신 이 호출 전용 빌더
    .requestFactory(factory(connect = 5s, read = 10s)).build();   // 공용 경로는 장시간이 정상이라 불변
// 저장소 접근은 단일 창구로 모으고 경로별 타임아웃(조회 5s / 대량 적재 60s)
Process p = new ProcessBuilder(cmd).start();
drainAsync(p.getInputStream());                              // 출력은 별도 스레드로 소비 (파이프 버퍼 막힘 방지)
if (!p.waitFor(120, SECONDS)) p.destroyForcibly();           // 대기에 상한
```
무엇이 깨졌나: 타임아웃이 "있다"고 가정한 곳의 기본값이 무한이었다(타임아웃 존재 여부는 실제 빌더 코드로 확인해야 한다).\
같은 구조: 상위의 `future.result(timeout=300)`은 대기만 포기할 뿐 워커 안의 DB 세션을 끊지 못한다 → 드라이버 자체에 `read_timeout`·`write_timeout`을 거는 계획(적용 결과 미기록).

### 변형 D — 열었으면 닫는다 (예외 경로 포함)
① 문제 코드
```python
client = SearchClient()
result = client.index_batch(docs)
client.close()                                               # 성공 경로에서만 close → 예외 시 연결 누적
# (이 사례의 finally 교정은 분석 문서의 계획 — 적용 결과 미기록)
```
```java
emitter.send(chunk);                                         // 스트림을 열고 complete() 를 빠뜨림 → 연결·스레드 누수
```
② 고친 코드
```python
client = SearchClient()
try:
    result = client.index_batch(docs)
finally:
    client.close()
```
```java
try { for (var c : chunks) emitter.send(c); emitter.complete(); }
catch (Exception e) { emitter.completeWithError(e); }
```
무엇이 깨졌나: 반납이 정상 경로에만 있어, 실패가 반복될수록 연결·스레드가 누적됐다.

### 변형 E — 요청마다 무한정 띄우던 백그라운드 작업
① 문제 코드
```go
func (m *Master) Deploy(svc string) {
    go m.run(svc)                                            // 요청마다 goroutine → 몰리면 무한 증가
}
```
② 고친 코드
```go
var busy sync.Mutex                                          // 에이전트: 배포 1건만
func (a *Agent) Deploy(w http.ResponseWriter, r *http.Request) {
    if !busy.TryLock() { w.WriteHeader(409); return }        // 대기 없이 즉시 거절
    defer busy.Unlock()
    // ...
}
// 마스터: 서비스별 inFlight 표식으로 서비스당 최대 1개 (동시 goroutine 수 ≤ 서비스 수)
// 부수 요청(로그 전송)도 300ms 타임아웃 + 실패 시 30초 백오프 — 부수 작업이 본 요청을 인질로 잡지 않게
```
무엇이 깨졌나: 동시에 존재할 수 있는 작업 수에 상한이 없었다.

### 변형 F — 입력 크기에 비례하는 처리의 단계별 상한 (클라이언트·배치측)
① 문제 코드
```rust
fn search(root: &Path, q: &str) -> Vec<Hit> {
    let mut hits = vec![];
    walk(root, |line| { if matches(line, q) { hits.push(line.to_string()); } true });   // 거대 저장소 = 무제한
    hits
}
```
② 고친 코드
```rust
walk(root, |lnum, line| {
    if hits.len() >= limit { return Ok(false); }             // sink 에서 조기 중단 (limit 500)
    hits.push(Hit { line: lnum, text: cap_line(line) });     // 라인 길이도 cap
    Ok(hits.len() < limit)
});
```
무엇이 깨졌나: 입력이 외부에 의해 무한정 커질 수 있는데 처리 단계에 상한이 없어, 메모리·렌더·응답성이 입력 크기에 비례해 무너졌다.\
같은 구조:\
- 폭주한 하위 작업이 수천 항목을 로그 → 카드당 표시 행 200 컷 + 완료 항목 기본 접힘(전체 DOM 재렌더 방지).\
- 백필이 전 기록을 동시에 메모리에 적재 → 탐지 후 본문 drop, 워커가 재읽기(메모리 상한 = 한 건분).\
- 동기·무제한 재귀 복사 → 비동기 blocking 스레드 + 최대 깊이 256.\
- 축출 없는 트리 캐시 → 닫을 때 축출 + keep-set 상한(표시 중인 항목은 축출 안 함).\
- 이미지 base64 data URL 상주 → object URL + 언마운트 시 revoke. 터미널 스크롤백 10k행 → 3000행.\
- 재동기 스냅샷에 종료된 세션을 전량 무기한 보유 → 종료 세션은 헤더만(생략 표식으로 "생략 ≠ 빈 것" 구분) + TTL 30분·최대 32개 프루닝. (링 버퍼가 개수만 제한하고 바이트는 무제한인 부분은 해결 미기록.)\
- 스트리밍 소비 배치 크기 무상한 → 적체가 클수록 한 번에 더 많이 가져와 하류 저장소를 압박, 재시작이 장애를 재생산 → 트리거당 최대 오프셋 상한(`maxOffsetsPerTrigger`) + 복구 절차(생산 중지 → 상한 걸고 재실행 → 따라잡은 뒤 저속 재개).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "자원을 소비하는 지점에 상한을 못박고, 넘치면 거절·절단한다"이다. 같은 원리(외부 입력에 비례해 커지는 자원은 서버·소유자 쪽 상한만이 막는다)에 다른 방안이 쓰인 사례:

### 방안 1 — bounded 채널 + 가득 차면 즉시 에러 / 적재 단계 tail-read
```rust
// 문제: 원격이 입력을 안 읽으면 unbounded 큐가 메모리 한도 없이 증가
// 고친: bounded 채널 + try_send (호출자 비블록, 가득 차면 에러)
match input_tx.try_send(chunk) {
    Ok(()) => Ok(()),
    Err(TrySendError::Full(_))   => Err("input buffer full"),
    Err(TrySendError::Closed(_)) => Err("session closed"),
}
// 영속 파일 로드: 파일 전체 read 후 cap → 적재 단계가 무제한
let mut f = File::open(path)?;
f.seek(SeekFrom::End(-(STORE_CAP as i64)))?;                 // 꼬리만 읽는다 (파일이 작으면 처음부터)
f.take(STORE_CAP).read_to_end(&mut buf)?;
```
최종 버퍼에 cap을 걸어도 적재 단계가 무제한이면 방어가 안 된다.\
메시지 **개수** 상한만으로는 거대한 메시지 하나를 못 막으므로 청크 크기(8KB)·바이트 예산을 병행한다.

### 방안 2 — bounded 큐 + 생산자 대기(역압)
```rust
let (tx, rx) = mpsc::channel(256);                           // 청크 ≤ 패킷 최대치 → 256청크 ≈ 수MB
// 읽기 루프
tx.send(chunk).await?;                                       // 가득 차면 생산자가 대기 → 원격 읽기 정지 → 원격 스로틀
// 외곽에 select!(cancel) — 정체된 소비자가 종료(teardown)를 막지 못하게
```
무손실이 우선인 출력(명령 실행 결과)에 쓴다.\
대가: 수신자를 비우지 않고 들고만 있으면 읽기 루프 전체가 멈춘다("비울 게 아니면 들고 있지 말 것").\
검증: 느린 소비자(청크당 1ms)로 768청크를 흘려 전 바이트 무손실·순서 보존 확인.

### 방안 3 — 소비자별 bounded 큐 + drop-oldest
```python
q = asyncio.Queue(maxsize=256)                               # 브로드캐스트 소비자(탭)마다
def offer(q, data):
    try: q.put_nowait(data)
    except asyncio.QueueFull:
        try: q.get_nowait()                                  # 가장 오래된 것 버림
        except asyncio.QueueEmpty: pass
        try: q.put_nowait(data)
        except asyncio.QueueFull: pass
# 재접속 replay 버퍼도 200KB tail 로 상한
```
생산자가 느린 소비자를 기다리지 않는 fan-out에서, 가장 느린 소비자가 메모리를 무한히 늘리는 것을 막는다.\
터미널처럼 "최신 화면"이 중요해 손실을 수용할 수 있을 때만 맞다(ack 기반 흐름 제어는 후속 과제로 남김).

### 방안 4 — 인증 전 입력에 크기·시간 상한, 검증 후 재공급
```java
// 최우선 필터: 인증 전에는 본문을 읽지 않는다
if (!hasSignature(req)) return reject(req);                  // 무서명은 본문 읽기 전 즉시 판정
return join(req.getBody(), HARD_LIMIT)                       // 서명 요청만 하드 크기 제한 후 결합
    .map(buf -> { byte[] b = copy(buf); release(buf); return b; })
    .flatMap(b -> verify(req, b) ? chain.filter(withCachedBody(req, b)) : reject(req));
// 리액티브 본문은 한 번만 소비되므로 검증 후 데코레이터로 재공급
// 하류 서버도 인증 전 단계에 읽기 타임아웃 (느린 전송 DoS 대비)
```
(설계 선검증·리뷰에서 발견한 항목)

### 방안 5 — 시도별 타임아웃 × 재시도의 합성 → 요청 전체 deadline 전파
```python
# 문제: 호출마다 5초 → 재시도 1회면 최대 10초 (계약은 "5초 예산")
raw = await chat(..., timeout=5)
# 고친: 재시도 포함 요청 전체를 하나의 데드라인으로
async with asyncio.timeout(5):
    raw = await chat(...)
    # ... 스키마 위반 시 재시도도 같은 예산 안에서
```
```text
설계 규칙: 각 시도의 타임아웃 = min(계층값, D − now)
          내부 deadline = 외부 예산 − 응답 후처리 여유(α)   (예: 3s 예산 → 내부 2.5s)
          남은 시간이 "완주 하한"보다 작으면 다음 시도를 시작하지 않는다
```
시도 **시작** 시점만 보는 재시도 금지 규칙은 시도 **중** 초과를 못 막는다 — 계층 각각은 맞아도 합성이 예산을 넘는다.\
(설계 규칙 쪽 사례는 설계 리뷰 발견, 런타임 사고 아님)

### 방안 6 — 컨테이너 메모리 상한 부재 시 호스트 OOM이 흔적을 숨긴다
```text
증상: 컨테이너가 일정 주기로 무한 재기동, "초기화 완료" 로그가 한 번도 없음
      컨테이너 상태: exit=0, OOMKilled=false            ← cgroup 한도에 걸린 게 아니라는 뜻일 뿐
진단: dmesg -T | grep -i "out of memory"              ← 호스트 커널이 죽였다면 흔적은 여기에만
부수: 재기동마다 수백 GB 인덱스를 다시 읽는 루프가 디스크 I/O 를 독점 → 같은 호스트 이웃 서비스 정지
교정: 로딩 피크 자체를 줄이는 코드 수정 (서비스 힙 축소 같은 대증요법은 선택하지 않음)
```
상한이 없으면 사망 주체가 호스트 커널이 되어, 컨테이너 층의 상태 보고가 정상처럼 보인다.

### 방안 7 — 워커 프로세스 전역 캐시로 대형 리소스 1회 로드
```python
_cache = {}                                                   # 프로세스 전역 (풀은 워커 프로세스를 재사용)
def worker(batch):
    global _cache                                             # 사용보다 앞에 선언
    if "transformer" not in _cache:
        _cache["transformer"] = make_transformer()           # 대형 사전 파싱을 워커당 1회
    t = _cache["transformer"]
    # ...
# 문제였던 것: 배치마다 재파싱(임시 객체가 결과의 3~5배) × N 워커 동시 피크 → 스왑 → 결과 대기 타임아웃
```
누수가 아니라 **동시 할당 피크**가 물리 메모리를 넘은 경우 — 상한을 거는 대신 피크 자체를 없앤다.

### 방안 8 — 입력 크기에 비례하는 작업의 고정 타임아웃 (미해결로 기록)
```text
문제: 고정 타임아웃이 입력 크기 최상위 구간(수십 MB 입력)의 작업만 반복적으로 잘라냄 (1차 + 재시도 모두 실패)
처리: 부분 실패는 성공 위장 없이 "완료 마커 없음"으로 남김
기록된 선택지: 타임아웃 상향 또는 입력 청킹 — 별도 작업으로 보류
```
같은 원리의 역방향 — 시간 상한도 자원 상한이지만, 작업량이 입력에 비례하면 고정값은 정상 작업의 꼬리를 자른다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 소비 지점 상한 + 거절·절단 | 소비 지점을 자원 소유자가 통제한다 | 상한값 선정 | 상한이 정상 요청을 자르면 기능 저하 | 서버·공개 경로·생성형 작업 전반 |
| 1. bounded + try_send 에러 / tail-read | 호출자가 에러를 처리할 수 있다 | 가득 참 에러 처리 | 개수 상한만이면 거대 메시지 통과 | 호출자를 막으면 안 되는 입력 경로 |
| 2. bounded + 생산자 대기 | 생산자를 멈춰도 된다(역압이 원격까지 전달) | 소비 지연이 생산 정지로 전파 | 비우지 않는 수신자가 전체 루프를 멈춤 | 무손실이 필요한 출력 |
| 3. 소비자별 bounded + drop-oldest | 오래된 데이터는 버려도 된다 | 데이터 손실 | 느린 소비자가 중간 내용을 잃음 | 최신 상태만 중요한 fan-out |
| 4. 인증 전 크기·시간 상한 | 인증이 본문에 의존한다 | 본문 복사·재공급 | 재공급 누락 시 하류가 빈 본문 | 서명 검증 게이트웨이 |
| 5. 요청 전체 deadline | 사용자 계약이 전체 지연이다 | 남은 시간 계산·전파 | 후처리 여유를 안 남기면 관측 지연 초과 | 재시도·다계층 호출 |
| 6. 상한 부재 진단(커널 로그) + 피크 교정 | 호스트를 다른 서비스와 공유한다 | 커널 로그 확인·피크 계산 | 컨테이너 상태만 보면 정상 종료로 오진 | 대형 메모리 서비스의 공유 호스트 |
| 7. 워커 전역 캐시 | 워커 프로세스가 재사용된다 | 워커당 상주 메모리 | 캐시 대상이 변하면 갱신 필요 | 배치마다 같은 대형 리소스를 쓰는 풀 |
| 8. 크기 비례 타임아웃·청킹 | 작업량이 입력 크기에 비례한다 | 크기 측정·분할 | 고정값이면 최상위 입력만 반복 실패 | 입력 크기 편차가 큰 배치 |

**결론**: 공통 원리는 "무한정 커질 수 있는 것에는 소유자 쪽 상한"이고, 방안은 **넘쳤을 때 무엇을 희생할지**로 갈린다.\
손실이 안 되면 역압(2), 호출자를 막으면 안 되면 즉시 에러(1), 최신만 중요하면 drop-oldest(3)를 고른다.\
시간 상한은 개별 호출이 아니라 **요청 전체**에 걸어야 합성이 예산을 넘지 않고(5), 작업량이 입력에 비례하면 고정값 대신 크기에 맞춘다(8).\
상한을 걸 수 없거나 걸기 전이라면 피크 자체를 줄이는 것(7)과, 상한이 없을 때 사망 흔적이 어디 남는지 아는 것(6)이 보완책이다.
