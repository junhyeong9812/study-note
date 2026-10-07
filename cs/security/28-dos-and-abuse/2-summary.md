# security/28-dos-and-abuse — 볼륨·프로토콜·애플리케이션 계층 DoS와 남용 — 정리 (힌트)

## 해결하는 문제

서비스 거부(DoS)는 **비대칭**을 노린다.\
공격자가 싼 자원(패킷·연결·요청)을 조금 쓰면, 서버가 비싼 자원(대역폭·커넥션·CPU·DB)을 많이 쓴다.

```text
  공격자 비용 ───(작다)───▶ [ 서버 ] ───(크다)───▶ 자원 고갈 → 정상 사용자 거부
  어느 자원을 고갈시키나 = 어느 계층을 치나
   볼륨(L3/4)   : 대역폭 ── 위조 UDP 증폭(DNS·memcached)로 회선을 채운다
   프로토콜(L4) : 커넥션 상태 ── SYN flood로 반쯤 열린 연결을 쌓는다
   애플리케이션(L7): CPU·DB ── 비싼 엔드포인트·느린 요청(slowloris)으로 워커를 묶는다
```

- *DoS*: 정상 사용자가 서비스를 못 쓰게 만드는 것. *DDoS*: 분산된 여러 출처에서 동시에.
- 계층마다 고갈 자원이 다르니 방어도 다른 층에 둔다. 볼륨은 망 앞단(DDoS 방어·CDN), 프로토콜은 커널·LB, 애플리케이션은 앱·리미터.
- *남용(abuse)*: 기술적 과부하가 아니라 **정상 기능을 악용**하는 것. 쿠폰 대량 발급, 크리덴셜 스터핑(10번), 스크래핑. 과부하와 남용은 겹친다.

쉬운 예: 식당에 전화를 건다.\
① 수천 명이 동시에 전화해 회선을 다 채우거나(볼륨), ② 전화만 걸고 말을 안 해 상담원을 붙잡거나(slowloris), ③ "코스 전부를 하나하나 설명해 달라"는 비싼 요청을 반복한다(앱 계층). 셋 다 정상 손님이 못 건다. 방어는 각각 회선 증설·침묵 통화 끊기·주문당 설명 제한이다.

실무 예:
- SYN flood로 SYN 큐(반쯤 열린 연결)가 차서, CPU는 멀쩡한데 연결이 안 된다(network/15).
- slowloris로 헤더를 찔끔찔끔 보내 워커를 전부 묶는다.
- 비싼 리포트 엔드포인트를 반복 호출해 DB가 과부하된다.
- HTTP/2 Rapid Reset(CVE-2023-44487, 2023): 스트림을 열자마자 취소해 동시 스트림 한도를 우회(network/36).

## 동작·원리

### 1. 세 계층 — 무엇을 고갈시키나

```text
  볼륨형(증폭): 작은 요청 → 큰 응답. 출발지를 피해자로 위조.
    공격자 ──(작은 질의, src=피해자)──▶ 공개 서버(DNS·memcached·NTP) ──(큰 응답)──▶ 피해자
    증폭 계수 = 응답/요청. memcached는 수만 배까지.
  프로토콜형: 연결 상태 테이블을 채운다 (SYN flood → SYN 큐).
  애플리케이션형: 요청당 서버 일이 많은 곳을 친다 (검색·리포트·정규식·암호 연산).
```

- 볼륨형은 **대역폭**을 채운다. GitHub 2018-02-28 사건: memcached UDP 증폭으로 **1.35 Tbps, 1억 2,690만 pps**, 증폭 계수 최대 51,000배, 17:21~17:26 UTC 불가·17:30까지 간헐 불가(GitHub 사후 보고). Akamai로 트래픽을 돌려 방어.
- 프로토콜형은 **상태**를 채운다. SYN flood는 ACK를 안 보내 SYN 큐를 채운다. 방어는 SYN cookie(network/15 §4가 정본).
- 애플리케이션형은 **CPU·DB·워커**를 묶는다. 정상처럼 보여 망 앞단에서 거르기 어렵다.

### 2. 느린 요청 — slowloris

```text
  정상:  GET / HTTP/1.1\r\nHost: x\r\n...\r\n\r\n   ← 빨리 끝맺는다
  slowloris: GET / HTTP/1.1\r\nHost: x\r\n  X-a: b\r\n  (끝맺지 않고 질질, 연결 유지)
  → 워커가 "헤더 다 받을 때까지" 기다리며 묶인다. 연결 수백 개면 워커 풀 고갈.
```

(실험, Python 3.12-slim(3.12.14), `--network none`, 2026-10-07 — 127.0.0.1 로컬 서버와 느린 로컬 클라이언트, 헤더를 2초 간격으로 5줄 보내되 끝맺지 않고 10초 뒤 연결을 닫음)

```text
  read_timeout=None: 헤더 미완성인 채 클라이언트가 연결을 닫음(EOF) (10.0s, 110바이트)   ← 연결을 10초간 붙잡음
  read_timeout=1.0: 수신 타임아웃 → 서버가 연결을 끊음 (1.0s, 25바이트)
    클라이언트: 1번째에 서버가 끊어 송신 실패
```

- 관찰: 수신 타임아웃이 없는 서버는 클라이언트가 찔끔찔끔 보내는 **10초 내내 연결을 붙잡고** 있었다(그 사이 워커 하나가 묶인다). 헤더는 끝내 완성되지 않았고, 클라이언트가 스스로 연결을 닫아서야 풀렸다.
  - 참고: 집필 때 코드는 이 경우(EOF로 루프 종료)를 "헤더 완성 처리"로 잘못 찍었다. 점검 재실행에서 EOF를 따로 구분하도록 라벨만 고쳐 다시 돌린 출력이 위 줄이다(시간·바이트 수는 같음). 1초 수신 타임아웃을 건 서버는 **1.0초에 끊었다** — 공격 연결이 워커를 오래 못 쥔다.
- 해석: slowloris 방어의 핵심은 "요청을 **제시간에** 끝맺지 않으면 끊는다"이다. 단일 연결 타임아웃 + 최소 수신 속도가 그 역할을 한다.

### 3. 비싼 입력 — 알고리즘 복잡도 공격

- 입력 하나가 서버 일을 지수·제곱으로 키우면, 작은 요청이 큰 비용을 낸다.
  - 엔티티 폭탄(23번): 641바이트 → 10^10 확장.
  - ReDoS: 백트래킹 정규식에 특정 입력이 지수 시간. `(a+)+$`에 긴 `aaaa...!`.
  - 해시 충돌 DoS: 공격자가 같은 버킷에 몰리는 키를 보내 연산당 O(1)을 O(n)으로, n개 삽입 전체를 O(n²)로 만든다(Java 8+ `HashMap`은 한 버킷이 커지면 트리로 바꿔 완화한다. 키가 `Comparable`(예: `String`)이면 O(log n)이지만, 해시가 같고 비교 순서가 없는 키면 트리의 양쪽을 다 뒤질 수 있다 — OpenJDK 21 `HashMap.TreeNode.find`).
  - 압축 폭탄: 작은 zip이 풀면 수 GB.
- 공통 방어: **입력 크기·깊이·시간 상한**, 선형 시간 정규식 엔진, 무작위화한 해시 시드.

### 4. 토큰 버킷 — 남용을 자원 비용에 비례해 막는다

```text
  용량 cap의 통에 초당 rate개 토큰이 찬다.
  요청은 cost개를 쓴다(비싼 엔드포인트는 cost가 크다). 없으면 429로 거절.
  → 평소 버스트는 cap까지 통과, 지속 남용은 rate로 묶인다.
```

(실험, OpenJDK 21.0.12 Temurin, `--network none`, 2026-10-07 — 키별 토큰버킷 용량 20·보충 5/s, 60초 시뮬레이션)

```text
60초, 키별 토큰버킷(용량 20, 보충 5/s)
  정상(1건/s, cost1)            허용   60  429    0  DB비용    60
  남용(50건/s, cost1)           허용  319  429 2681  DB비용   319
  남용(5건/s, 리포트 cost10)       허용   31  429  269  DB비용   310
```

- 관찰 1: 정상 사용자(1건/s)는 **한 건도 안 막혔다**(허용 60, 429 0). 이 실험의 고른 1건/s 패턴에서는 리미터가 정상 트래픽을 건드리지 않았다. 평균이 보충 속도(5/s)보다 낮아도 정상 요청이 한순간 용량(20)을 넘게 몰리면 그 몫은 429가 된다.
- 관찰 2: 초당 50건을 쏜 남용자는 허용 319건 뒤 2,681건이 429로 막혔다. 초기 버스트(용량 20)만 통과하고 그 뒤는 보충 속도(5/s)로 묶였다.
- 관찰 3: 비싼 리포트(cost 10)는 허용 31건으로 더 일찍 막혔다 — **DB에 간 비용**은 cost1 남용(319)과 비슷한 310으로 수렴했다. 비용 가중치가 "비싼 엔드포인트일수록 더 적게 통과"를 만든다.
- 토큰 버킷의 다섯 세는 법·분산 경합·제품별 구현은 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)가 정본이다.

### 5. 거절도 공짜가 아니다 — 방어의 역설

- 리미터·방어 자체가 자원을 쓴다. 429를 만들어 보내는 데도 CPU·커넥션이 든다.
- 429가 재시도 폭풍을 부른다 — 막힌 클라이언트가 즉시 재시도하면 더 큰 부하. 지수 백오프+지터로 받아야 한다(reliability/06).
- 그래서 방어는 **가능한 한 앞단에서, 싸게** 건다: 망 앞단(볼륨), LB·커널(프로토콜), 게이트웨이(앱). 비싼 검증은 싼 검증을 통과한 뒤에 한다(OWASP DoS Cheat Sheet: "validation that is cheap in resources first").

## 쓰이는 자료구조·알고리즘

- **토큰 버킷 / 리키 버킷** — 남용 제한의 기본. [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md)
- **상태 테이블(연결 추적)** — SYN 큐·conntrack. 프로토콜형이 채우는 대상. [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) · [network/11-nat-and-conntrack](../../network/11-nat-and-conntrack/2-summary.md)
- **해시맵 최악 복잡도** — 충돌 공격이 O(1)을 O(n)으로. 무작위 시드로 방어. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **백트래킹 vs 오토마타 정규식** — ReDoS. 선형 시간 엔진(RE2류)이 방어. ([language/02-lexing-and-regular-languages](../../language/02-lexing-and-regular-languages/2-summary.md))
- **지수 백오프 + 지터** — 429 뒤 재시도. [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 순서 (계층별로 앞단부터)

1. **볼륨**: CDN·DDoS 방어 서비스를 앞단에 둔다. 공개 UDP 서비스를 열어 두지 않는다(증폭 반사판이 되지 않게).
2. **프로토콜**: SYN cookie 유지(network/15), conntrack 한도·타임아웃, LB에서 연결 수 제한.
3. **느린 요청**: 서버·프록시에 헤더/바디 수신 타임아웃과 최소 속도(아래 2).
4. **앱·남용**: 키별 토큰 버킷, 비싼 엔드포인트는 cost 가중·페이지네이션·쿼리 상한, 인증·캡차로 사람/봇 구분.
5. **거절 설계**: 429 + `Retry-After`, 클라이언트는 백오프+지터. 과부하 시 우선순위 셰딩(reliability/12).

### 2. 느린 요청 방어 (서버 설정)

```nginx
# nginx: 수신 타임아웃·바디 크기 (기본값 — 확인한 판)
client_header_timeout 60s;   # 헤더 받는 시간
client_body_timeout   60s;   # 바디 청크 사이 간격
client_max_body_size  1m;    # 바디 상한 (기본 1m)
keepalive_timeout     75s;
limit_conn_zone $binary_remote_addr zone=perip:10m;
limit_conn perip 20;          # IP당 동시 연결 (예시 값) — 헤더를 다 받은 처리 중 연결만 센다(nginx 문서)
                              #   → 헤더를 끝맺지 않는 slowloris 연결에는 안 걸린다. 그건 위 타임아웃 몫
```

```apache
# Apache mod_reqtimeout 기본값
RequestReadTimeout handshake=0 header=20-40,MinRate=500 body=20,MinRate=500
# 헤더: 처음 20초, 데이터가 오면 500바이트마다 1초씩 늘리되 최대 40초 — 그 안에 못 끝내면 408
# 바디: 처음 20초, 500바이트마다 1초씩 연장 (상한 없음)
```

- 실험처럼 "제시간에 못 끝내면 끊는다"가 slowloris의 직접 방어다.

### 3. 토큰 버킷 — 키별·cost 가중 (Java)

- 키별 토큰 버킷 구현·분산 판(Redis Lua)은 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) §2·§3이 정본이다. 보안 관점의 추가는 **키 선택**과 **cost**다.

```java
// 비싼 엔드포인트는 cost를 크게 (실험: cost10이면 더 일찍 막힌다)
double cost = switch (endpoint) { case "/report" -> 10; case "/search" -> 3; default -> 1; };
if (!bucket(keyFor(request)).tryAcquire(cost))
    return status(429).header("Retry-After", "1");   // 백오프 유도
```

- 키 선택 주의: IP로만 세면 NAT·회사 공유 IP 하나가 통째로 막힌다(reliability/11 §4). 인증 사용자는 사용자 ID, 익명은 IP+경로 등으로 세분한다.

### 4. 진단

```bash
# 프로토콜형: 반쯤 열린 연결, SYN cookie
ss -tan state syn-recv | wc -l
nstat -az | grep -i syncookie
# 앱형: 429 비율, 느린 요청
grep -c ' 429 ' access.log
# 어떤 엔드포인트가 비싼가 (요청당 시간)
awk '{print $7, $NF}' access.log | sort | tail
```

## 장애 시나리오와 대처

### 1. SYN flood → 연결 안 됨, CPU는 여유 (⚠ 커리큘럼)

- **현상**: 정상 사용자의 연결이 느리거나 실패. 서버 CPU·앱 로그는 조용함.
- **보이는 형태**: `ss -tan state syn-recv` 폭증, 커널 `Possible SYN flooding ... Sending cookies`, `TcpExtSyncookiesSent` 증가(network/15 §4 정본).
- **원인**: 위조 출발지 SYN으로 SYN 큐를 채운다. 마지막 ACK가 안 온다.
- **대처**: `tcp_syncookies=1` 유지, `tcp_synack_retries` 축소, 대규모는 망 앞단 DDoS 방어.

### 2. slowloris → 워커 풀 고갈

- **현상**: 동시 접속이 많지도 않은데 새 요청이 안 받아진다.
- **보이는 형태**: 연결 수는 한도 근처인데 각 연결이 "헤더 수신 중"으로 오래 머묾. 실험의 `read_timeout=None`처럼 연결이 오래 붙잡힘.
- **원인**: 헤더/바디를 느리게 보내 워커를 점유. 수신 타임아웃·최소 속도 없음.
- **대처**: 수신 타임아웃(nginx `client_header_timeout`, Apache `mod_reqtimeout`), 헤더 수신 전 연결도 세는 IP당 연결 제한(방화벽·LB 단 — nginx `limit_conn`은 헤더를 다 받은 연결만 센다), 이벤트 기반 프록시를 앞단에.

### 3. 비싼 엔드포인트 반복 호출 → DB 과부하

- **현상**: 특정 API 호출이 늘면 DB가 느려지고 전체가 끌려 내려간다.
- **보이는 형태**: 그 엔드포인트의 느린 쿼리 급증, DB 커넥션 풀 포화, 앱 지연.
- **원인**: 페이지네이션·상한 없는 조회, 리포트·집계를 요청마다 계산, cost 구분 없는 리미터.
- **대처**: cost 가중 토큰 버킷(실험), 페이지 크기·쿼리 시간 상한, 무거운 작업은 비동기·사전 계산·캐시. DB 타임아웃(database/22).

### 4. 볼륨/증폭 DDoS → 회선 포화

- **현상**: 서버에 트래픽이 닿기도 전에 회선이 막혀 전면 불가.
- **보이는 형태**: 업스트림 대역폭 포화, 특정 UDP 포트(53·11211)로의 거대한 응답.
- **원인**: 위조 출발지로 공개 서버에서 증폭된 응답이 피해자에게 쏟아짐(GitHub 2018 memcached).
- **대처**: 앱 혼자 못 막는다 — CDN·DDoS 방어 서비스로 흡수/필터. 자사가 반사판이 되지 않게 공개 UDP 서비스를 닫는다.

### 5. 방어가 역풍 — 429 재시도 폭풍 / 리미터가 전부 막음

- **현상**: 리미터를 켠 뒤 오히려 부하가 늘거나, 리미터 고장으로 정상 요청까지 전부 막힌다.
- **보이는 형태**: 429 급증 직후 요청량이 더 늘어남(즉시 재시도). 또는 리미터 장애 시 fail-open/closed 선택 미정으로 전면 차단·전면 통과.
- **원인**: 클라이언트가 백오프 없이 재시도. 리미터 실패 모드 미설계.
- **대처**: `Retry-After` + 지수 백오프+지터(reliability/06), 리미터 실패 시 정책을 명시(과부하 보호가 목적이면 조심스러운 fail-open, 보안 게이트면 fail-closed — 01번), 과부하 시 우선순위 셰딩(reliability/12).

## 핵심 문장

- DoS는 비대칭을 노린다 — 공격자의 싼 자원이 서버의 비싼 자원을 고갈시킨다.
- 계층마다 고갈 자원이 다르다: 볼륨은 대역폭(망 앞단), 프로토콜은 연결 상태(커널·LB), 앱은 CPU·DB(앱·리미터).
- slowloris 방어는 "제시간에 못 끝맺는 요청을 끊는다"이다 — 실험에서 1초 수신 타임아웃이 연결을 1.0초에 끊었다.
- 토큰 버킷은 버스트 용량 안의 정상 트래픽은 통과시키고(실험 고른 1건/s에서 429 0) 지속 남용을 보충 속도로 묶는다. cost 가중으로 비싼 엔드포인트를 더 일찍 막는다.
- 거절도 공짜가 아니다 — 429는 백오프+지터로 받고, 방어는 앞단에서 싸게 건다.

## 관련 주제·근거

- 선행
  - [network/15-tcp-handshake-and-backlog](../../network/15-tcp-handshake-and-backlog/2-summary.md) — SYN flood·SYN cookie·accept 큐(정본)
- 연결
  - [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md) — 토큰 버킷 구현·분산 경합(정본) · [12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md) · [06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)
  - [network/11-nat-and-conntrack](../../network/11-nat-and-conntrack/2-summary.md) · [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)(Rapid Reset) · [network/47-cdn-and-edge](../../network/47-cdn-and-edge/2-summary.md)
  - [security 23-deserialization-and-parser-attacks](../23-deserialization-and-parser-attacks/2-summary.md)(엔티티 폭탄) · [10-authentication-basics](../10-authentication-basics/2-summary.md)(크리덴셜 스터핑) · [01-security-principles](../01-security-principles/2-summary.md)(fail-safe)
  - [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
  - [security 29-security-symptom-index](../29-security-symptom-index/2-summary.md) · [30-security-incidents](../30-security-incidents/2-summary.md)
- 1차 출처
  - NVD CVE-2023-44487 HTTP/2 Rapid Reset(게시 2023-10-10, CVSS 3.1 7.5, CISA KEV) <https://nvd.nist.gov/vuln/detail/CVE-2023-44487>
  - GitHub Engineering, "February 28th DDoS Incident Report"(2018) — memcached UDP 증폭 1.35 Tbps·126.9 Mpps, 증폭 최대 51,000배, 17:21~17:26 UTC 불가·17:30까지 간헐, Akamai로 전환 <https://github.blog/2018-03-01-ddos-incident-report/>
  - OWASP Denial of Service Cheat Sheet — 계층 분류, "validation that is cheap in resources first", 느린 공격 타임아웃 <https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html>
  - Apache `mod_reqtimeout` 기본값 `handshake=0 header=20-40,MinRate=500 body=20,MinRate=500` <https://httpd.apache.org/docs/2.4/mod/mod_reqtimeout.html> · nginx core 기본값(`client_max_body_size 1m`, `client_header_timeout 60s`) <https://nginx.org/en/docs/http/ngx_http_core_module.html>
- 실험(로컬, `--network none`)
  - slowloris(Python 3.12.14): 수신 타임아웃 없으면 헤더 미완성인 채 연결 10초 점유(클라이언트가 닫을 때까지), 1초 타임아웃이면 1.0초에 끊음
  - 토큰 버킷(OpenJDK 21.0.12, 용량 20·보충 5/s): 정상 1건/s는 429 0, 50건/s 남용은 319 허용·2681 차단, cost10 리포트는 31 허용으로 더 일찍 차단
