# cs/issue/network/bind-address-loopback-vs-lan — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `fail-closed`

## 정답
<!-- 질문 1:1 대응 -->

1. **바인딩 주소.** 서버가 소켓을 `listen`할 때 어느 로컬 주소로 접속을 받을지 정한다. `0.0.0.0`은 그 호스트의 **모든 인터페이스**(루프백 + LAN + 공인 등), LAN IP는 **그 IP로 온 접속만**, `127.0.0.1`은 **자기 자신(루프백)만**. LAN IP에만 바인딩한 서버에 `127.0.0.1`로 접속하면, 커널에 그 주소로 리스닝 중인 소켓이 없으므로 **`connection refused`**가 난다 — 포트 번호는 같아도 "그 주소:포트"에 귀를 열지 않았기 때문이다. 방화벽 차단(무응답/timeout)과 달리 refused는 "그 주소엔 아무도 안 듣는다"는 즉답이다.
   > **바인딩(bind)** — 서버 소켓을 특정 주소:포트에 묶어 그 조합으로 온 접속만 받게 하는 것.

2. **fail-closed vs fail-open.** `${BIND_ADDR:?set-in-env}:8090:8090`은 "이 변수가 비면 기동을 실패시켜라"다 — 설정이 빠지면 **아예 안 뜬다(closed)**. fail-open이라면 값 없을 때 `0.0.0.0`으로 다 열어버려, 설정 누락이 곧 광노출이 된다. 보안 통제는 **실수의 결과가 안전한 쪽으로 기울어야** 하므로, "빠지면 노출"이 아니라 "빠지면 안 뜸"을 기본값으로 삼는다. 누락은 배포 실패로 시끄럽게 드러나지, 조용한 노출로 숨지 않는다.
   > **fail-closed** — 설정·판정이 불확실하면 열지 않고 닫는(거부하는) 안전 기본값.

3. **거짓 음성인가 정직한 보고인가.** 정직한 보고다. 서비스가 LAN IP로 200을 준다고 해서 `127.0.0.1`로도 열려 있다는 뜻이 아니다 — 헬스체크가 실제로 두드린 주소(`127.0.0.1`)로는 **정말로 안 열려 있었다**. 그래서 이건 거짓 음성이 아니라 "그 주소로는 접속 불가"라는 사실의 정확한 보고다. 오히려 이 실패가 **바인딩이 의도대로(루프백 거부) 걸려 있음을 증명**해줬다. 만약 헬스체크가 200을 냈다면 그게 오히려 바인딩이 안 걸렸다는 뜻이었을 것이다.

4. **localhost vs 127.0.0.1.** `localhost`는 이름이라 리졸버가 IP로 푼다. 컨테이너 안 `/etc/hosts` 설정에 따라 `localhost`가 **`::1`(IPv6 루프백)**로 먼저 풀릴 수 있는데, 서버가 IPv4(`127.0.0.1`)로만 바인딩했다면 `::1`로 온 접속은 받지 못해 헬스체크가 실패 → unhealthy. `127.0.0.1`을 명시하면 이름 해석 단계를 건너뛰어 IPv4 루프백으로 확정되므로 이 불일치가 사라진다. 교훈: **헬스 프로브 주소는 이름이 아니라 서버가 실제 바인딩한 주소 계열로 못 박는다**.

5. **왜 (b) 헬스체크를 고쳤나.** LAN IP에만 여는 것은 **의도된 보안 불변식**(fail-closed 하드닝의 결과)이다. (a)처럼 루프백도 열도록 완화하면 보안 결정을 헬스체크 편의 때문에 되돌리는 것이라 본말이 전도된다. 틀린 것은 서비스가 아니라 **프로브가 서비스의 실제 청취 주소를 안 따른 것**이므로, 헬스 URL을 서비스가 여는 LAN 주소로 교정하는 게 맞다. 원칙: *불변식은 놔두고 그 불변식을 위반한 관찰 지점을 고친다*.

6. **`compose up` 종료 0 ≠ 정상.** `docker compose up`의 종료코드 0은 "컨테이너를 **띄웠음**"만 뜻한다 — 그 안 프로세스가 뜨자마자 크래시 루프거나, 떴어도 요청에 200을 못 주는 상태일 수 있다. 그래서 배포는 **헬스 URL을 실제로 폴링(200이 와야 ok, 최대 90초)**해 "떴다"와 "응답한다"를 갈라야 한다. 더 나아가 헬스체크 자체도 얕으면 안 된다 — 얕은 `/health`는 "프로세스 살아있나"만 보지만, 재부팅 후 컨테이너가 GPU를 잃고도 `loaded:true`를 계속 반환해 **6일 내내 healthy로 위장한** 실측 사고가 있었다. 그래서 **깊은 `/health/deep`(GPU로 실제 추론 1건)**로 "약속한 일을 실제로 하나"를 검사한다. "살아있음"과 "일함"은 다르다.
   > **크래시 루프** — 컨테이너가 떴다가 즉시 죽고 재시작을 반복하는 상태.

7. **두 통제의 교차 검증.** backend의 **fail-closed 바인딩(보안)**은 "허가된 LAN 주소로만 연다"를 주장하고, ci-cd의 **배포 후 헬스체크(검증)**는 "정말 응답하나 실제로 찔러본다". 헬스체크가 루프백에서 refused를 만난 순간, 보안 주장("루프백은 막혀 있다")이 **사실임이 실증**됐고, 동시에 헬스체크가 "compose 성공"을 곧이곧대로 안 믿는다는 것도 실증됐다 — 서로가 상대의 정상 동작을 증명했다. 만약 헬스체크가 `compose up` 성공(종료 0)만 믿었다면, "deploy ok"로 넘어가 **루프백 접근이 막힌 사실도, 프로브 주소가 틀린 사실도** 둘 다 놓쳤을 것이다.

## 문제 구조 (추상화 코드)

### 변형 A — fail-closed LAN 바인딩 vs 루프백을 두드리는 배포 헬스체크
① 문제 코드
```yaml
# 서비스 compose
ports:
  - "${BIND_ADDR:?set-in-env}:8090:8090"      # LAN 주소에만 연다 (값 없으면 기동 거부)
```
```go
// 배포 에이전트 (호스트 네트워크)
healthURL := "http://127.0.0.1:8090/health"   // 루프백 → connection refused → deploy_unhealthy
```
② 고친 코드
```go
healthURL := fmt.Sprintf("http://%s:8090/health", svc.BindAddr)   // 서비스가 실제로 여는 주소
// 바인딩(보안 불변식)은 그대로 둔다
```
무엇이 깨졌나: 프로브가 서비스의 실제 청취 주소가 아니라 관성적인 루프백을 봤다.

### 변형 B — 컨테이너 헬스체크의 `localhost`가 IPv6로 풀림
① 문제 코드
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -fsS http://localhost:8090/health || exit 1"]   # localhost → ::1
```
② 고친 코드
```yaml
healthcheck:
  # localhost 금지 — 컨테이너 안에서 ::1로 풀려 IPv4 바인딩 서버가 unhealthy
  test: ["CMD-SHELL", "curl -fsS -m 5 http://127.0.0.1:8090/health || exit 1"]
```
무엇이 깨졌나: 이름 해석 결과의 주소 계열(IPv6)이 서버의 바인딩 계열(IPv4)과 달랐다.

### 변형 C — "컨테이너 띄움"을 "서비스 정상"으로 판정
① 문제 코드
```sh
docker compose up -d && report "deploy ok"          # 종료 0 = 띄웠음일 뿐
```
② 고친 코드
```sh
docker compose up -d
for i in $(seq 1 90); do                             # 최대 90초 폴링
  [ "$(curl -s -o /dev/null -w '%{http_code}' "$HEALTH_URL")" = 200 ] && { report "deploy ok"; exit 0; }
  sleep 1
done
report "deploy unhealthy"
# 헬스 엔드포인트도 얕은 /health(프로세스 생존) 대신 /health/deep(실제 작업 1건 수행)
```
무엇이 깨졌나: 프로세스 기동과 서비스 응답을, 생존과 실제 작업 가능을 구분하지 않았다.

### 변형 D — 컨테이너 안 서버가 루프백에만 바인딩 (포트 매핑이 무력)
① 문제 코드
```python
server = ToolServer("search")                        # 기본 bind 127.0.0.1
server.run(transport="sse", host="0.0.0.0")          # run()은 host를 받지 않음 → TypeError
```
② 고친 코드
```python
server = ToolServer("search", host="0.0.0.0")        # 네트워크 설정은 생성자(또는 환경변수)로만
server.run(transport="sse")
```
무엇이 깨졌나: 포트 매핑 트래픽은 컨테이너의 eth0으로 도착하는데, 서버는 컨테이너 루프백에서만 듣고 있었다.\
같은 구조: 부수로 클라이언트 설정에 전송 타입(`"type": "sse"`)이 빠져 스키마 검증 실패.

### 변형 E — 컨테이너에서 호스트 DB를 `127.0.0.1`로 호출 + 호스트 DB가 루프백 바인딩
① 문제 코드
```properties
DB_URL=${DB_URL:jdbc:mysql://127.0.0.1:3306/app}    # 컨테이너 안에선 컨테이너 자신
# 호스트 DB가 bind-address = 127.0.0.1 이면           # 외부(컨테이너) 접속도 거부된다(기록상 요구 조건)
```
② 고친 코드
```properties
# .env (env_file이 유일한 주입 경로)
DB_URL=jdbc:mysql://<호스트IP>:<publish포트>/app
# 호스트 네이티브 DB: bind-address = 0.0.0.0
```
무엇이 깨졌나: 목적지(컨테이너 루프백)가 호스트가 아니었다 — 같은 이유로 호스트 네이티브 DB의 바인드도 루프백이면 안 된다(목적지·바인드 양쪽을 맞춰야 한다).

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~E)은 "프로브·목적지 주소를 서비스의 실제 바인드 주소에 맞춘다"이다. 같은 원리(바인드·프로브 주소·도구의 불일치)에 다른 방안이 쓰인 사례:

### 방안 1 — 이미지에 없는 도구 대신 런타임 내장 수단 + start_period
```yaml
# 문제: 경량 이미지(JRE·alpine·python slim)에 curl 없음 → 명령 자체 실패 → 항상 unhealthy
test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:8080/health || exit 1"]
# 고친 (이미지별 내장 수단)
test: ["CMD-SHELL", "bash -c 'exec 3<>/dev/tcp/localhost/8090' || exit 1"]              # JRE: TCP 연결성만
test: ["CMD-SHELL", "wget --spider -q http://127.0.0.1:11000/ || exit 1"]              # alpine: busybox
test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health/deep', timeout=20)\" || exit 1"]
start_period: 300s   # 부팅·모델 로딩 시간을 실패로 세지 않음
```
진단 순서: `docker inspect --format '{{json .State.Health}}'`로 프로브 실행 로그를 먼저 본다(서비스가 아픈가 vs 검사가 틀렸나).\
같은 구조: 헬스체크가 다른 모드의 포트를 두드려 정상인데 unhealthy → 모드별 포트 정합.

### 방안 2 — `localhost` ≠ `127.0.0.1` 오리진 (호스트 이름을 서버 기대에 맞춤)
```text
dev 서버: 허용 오리진 = localhost (허용 밖 오리진의 dev 리소스 요청 차단)
문제: 테스트가 http://127.0.0.1:<port> 으로 접속 → JS 로드 차단 → SSR HTML만, 이벤트 안 붙음
고친: 테스트 URL을 http://localhost:<port> 으로 → 하이드레이션 정상
```
주소가 같은 루프백이어도 **오리진 문자열**은 다르다 — 이 경우엔 IP를 명시하는 게 아니라 서버가 허용한 이름을 쓴다.

### 방안 3 — wildcard bind를 기동 시 거절 (fail-closed 검증)
```rust
fn open_listener(cfg: &Config) -> Result<Listener> {
    let addr: IpAddr = cfg.bind.parse().map_err(|_| Error::NotLiteral)?;   // hostname·빈 값 거절
    if addr.is_unspecified() { return Err(Error::Wildcard); }             // 0.0.0.0 / :: 거절
    if !is_private_lan(addr) { return Err(Error::NotPrivate); }
    let l = Listener::bind((addr, cfg.port))?;
    ensure!(l.local_addr()?.ip() == addr);                                 // 실제 주소 재확인
    Ok(l)
}
// 원격 경로·키가 설정돼 있으면 private literal + 출발지 allowlist가 없을 때 기동 거부
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 프로브·목적지를 바인드에 맞춤 | 바인드가 의도된 불변식이다 | 설정 수정 | 바인드가 바뀌면 프로브도 따라 바꿔야 함 | 보안 바인딩을 유지해야 할 때 |
| 1. 런타임 내장 도구 + start_period | 이미지에 도구를 추가하고 싶지 않다 | 이미지별 명령 차이 | TCP 연결성만 보는 방식은 HTTP 레디니스를 증명 못 함 | 남이 만든 경량 이미지 |
| 2. 서버가 허용한 이름 사용 | 서버가 오리진을 문자열로 비교한다 | 없음 | IP 명시 원칙과 충돌해 보임 | dev 서버·CORS 류 오리진 검사 |
| 3. wildcard 거절 기동 검증 | 노출 범위를 코드가 보장해야 한다 | 검증 코드·설정 필수화 | 설정 누락 시 기동 실패(의도된 소음) | LAN 전용 가정이 보안 전제인 리스너 |

**결론**: 바인드가 보안 결정이면 바인드는 두고 **관찰 쪽(프로브 주소·도구·이름)을 맞춘다**(기본·1·2).\
바인드 자체가 틀릴 위험이 크면(설정 오배선으로 wildcard가 될 수 있으면) **기동 시점에 바인드를 검증해 거절**한다(3).\
헬스체크 명령은 서비스와 함께 이미지·주소·포트까지 검증 대상이다 — 먼저 프로브 로그를 보고 "서비스가 아픈가, 검사가 틀렸나"를 가른다.
