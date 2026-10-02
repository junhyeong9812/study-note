# reliability/45-chaos-and-resilience-testing — 장애 주입·카오스 실험·게임 데이 — 정리 (힌트)

## 해결하는 문제

"Redis가 죽어도 클라이언트가 다시 붙는다", "한 존이 빠지면 페일오버된다" — 설계 문서에 적힌 가정이 **실제로 성립하는지** 아무도 해 본 적이 없다. 그러면 처음 확인하는 날이 진짜 사고 날이다.

```text
 가정만 있는 시스템                              장애를 미리 주입하는 시스템
 설계서: "자동 재연결된다"                         평일 낮, 작은 범위에 Redis 재시작을 주입
 사고 날: 재연결 안 됨 → 전면 장애                   "재연결 안 됨"을 실험에서 발견 → 고침
 원인 파악·수정 ── 사고 시간에                       사고 날: 이미 고쳐진 경로로 버틴다
```

- *카오스 엔지니어링(Chaos Engineering)*: 운영 환경의 거친 조건을 견디는 능력에 대한 **확신을 쌓기 위해** 시스템에 실험을 하는 분야(Principles of Chaos Engineering, Basiri 외 2016).
- *장애 주입(fault injection)*: 서버 종료, 네트워크 끊기, 지연·오류 응답처럼 실제 사고와 같은 사건을 일부러 만드는 것.
- *게임 데이(game day)*: 운영과 비슷한 환경에서 사건을 흉내 내고, 시스템과 **사람·절차**의 대응을 함께 연습하는 날(AWS Well-Architected REL12-BP05).

쉬운 예: 소방 훈련이다.
- 비상구 안내도만 붙여 두면, 진짜 불이 났을 때 그 문이 잠겨 있다는 것을 처음 안다.
- 훈련 날 실제로 걸어 나가 보면 잠긴 문이 드러난다.

똑같은 구조다.\
실무 예: Netflix Chaos Monkey(운영 VM 인스턴스를 무작위로 종료), Chaos Kong(AWS 리전 하나의 장애 흉내), FIT(서비스 간 요청을 실패시켜 우아한 저하 확인) — Basiri 외 2016.

## 동작·원리

### 1. 실험의 네 단계 — 정상 상태를 반증하려고 한다

```text
 1. 정상 상태 정의  ── 측정 가능한 출력 (처리량·오류율·지연 분위수)
 2. 가설            ── "대조군과 실험군 모두 정상 상태가 유지된다"
 3. 변수 주입       ── 실제 사건을 흉내: 서버 죽음, 디스크 고장, 연결 끊김, 트래픽 급증
 4. 반증 시도       ── 두 군의 정상 상태 차이를 찾는다
        │
        ├─ 차이 없음 → 확신이 쌓인다
        └─ 차이 있음 → 약점 발견 → 개선 대상
```

- 출처: Principles of Chaos Engineering(2019-03 갱신), Basiri 외 IEEE Software 33(3) 2016 "Running a Chaos experiment".
- *정상 상태(steady state)*: 내부 속성이 아니라 시스템의 **측정 가능한 출력**. Netflix는 초당 재생 시작 수(SPS)를 쓴다. 원칙 문서: 카오스는 시스템이 "어떻게" 동작하는지가 아니라 "동작한다"는 것을 검증한다.
- *대조군·실험군*: 같은 조건에서 장애를 넣은 쪽과 넣지 않은 쪽. 차이를 장애의 효과로 본다. 논문의 가상 예: 일부 사용자만 골라 두 군으로 나누고, 실험군의 북마크 서비스 요청만 실패시켜 SPS를 비교한다.

### 2. 고급 원칙 다섯

| 원칙 | 뜻 |
|---|---|
| 정상 상태 행동에 가설을 세운다 | 처리량·오류율·지연 분위수 같은 출력 |
| 실제 사건을 바꿔 가며 넣는다 | 영향·빈도로 우선순위. 하드웨어 고장, 잘못된 응답, 트래픽 급증·확장 같은 "고장 아닌" 사건도 |
| 운영에서 실험한다 | 실제 트래픽만이 요청 경로를 정확히 담는다 |
| 자동화해 계속 돌린다 | 시스템이 바뀌면 지난 실험의 확신이 줄어든다 |
| 폭발 반경을 최소화한다 | 단기 피해를 최소로, 그리고 가둔다 |

- "운영에서"는 목표이지 첫걸음이 아니다. 시작은 스테이징·작은 범위, 근무 시간이다. Netflix도 Chaos Monkey를 **평상 근무 시간에만** 돌린다(엔지니어가 바로 대응하도록 — Basiri 외 2016). Chaos Kong은 월 1회 주기로 돌렸다.

### 3. 무엇을 주입하나 — 계층별

```text
 인프라   │ 인스턴스·컨테이너 종료, 존·리전 빼기, 디스크 가득 채우기
 네트워크 │ 연결 끊기, 지연·패킷 손실(netem), DNS 실패, 파티션
 의존성   │ 하류 서비스 오류·지연 응답, 재시작, 느린 DB
 애플리케이션│ 예외 주입, 스레드풀 고갈, 잘못된 설정값
 사람·절차│ 담당자 부재, 런북 따라 하기, 지휘권 인계 (게임 데이)
```

### 4. 실험: "Redis가 재시작돼도 클라이언트는 곧 정상 상태로 돌아온다"

- 정상 상태: 0.5초 구간마다 성공한 `INCR` 수.
- 대조군: `redis-a`(장애 없음). 실험군: `redis-b`(실험 2.6초쯤 밖에서 `docker restart -t 0`).
- 클라이언트 두 종류(RESP를 소켓으로 직접 말한다)
  - naive: 처음 연 소켓만 쓴다. 실패를 삼키고 같은 소켓을 계속 쓴다.
  - resilient: 연결 타임아웃·읽기 타임아웃 각 300ms(쓰기에는 이 타임아웃이 걸리지 않는다), 입출력 예외나 EOF가 나면 소켓을 닫고 다음 호출에서 새로 연결, 백오프 50→400ms. Redis가 오류 응답(`-ERR …`)을 보내면 `false`만 돌려주고 소켓은 그대로 쓴다.

```java
public boolean incr() {                                 // resilient
    try {
        if (s == null) { s = new Socket(); s.connect(new InetSocketAddress(host, 6379), 300); s.setSoTimeout(300);
                         in = new BufferedReader(new InputStreamReader(s.getInputStream())); out = s.getOutputStream(); }
        out.write("*2\r\n$4\r\nINCR\r\n$1\r\nk\r\n".getBytes(StandardCharsets.US_ASCII)); out.flush();
        String r = in.readLine();
        if (r == null) throw new EOFException("서버가 연결을 닫음");
        backoff = 50; return r.startsWith(":");
    } catch (IOException e) {
        try { if (s != null) s.close(); } catch (IOException ignore) {}
        s = null;                                       // 다음 호출에서 새로 연결
        try { Thread.sleep(backoff); } catch (InterruptedException ie) {}
        backoff = Math.min(backoff * 2, 400);
        return false;
    }
}
```

(실험, Redis 7.4.9 `redis:7-alpine` 일회용 컨테이너 2개 + JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 같은 Docker 네트워크, 2026-10-01 — `[host]` 줄은 장애 주입 스크립트의 출력)

```text
[host] 15:09:46.829 redis-b 재시작 완료
== 클라이언트: naive (0.5초 구간별 성공 INCR 수, 장애 주입 ≈ 2.0초)
구간(초)   0.0  0.5  1.0  1.5  2.0  2.5  3.0  3.5  4.0  4.5  5.0  5.5  6.0  6.5  7.0  7.5
대조군    85   88   88   91   90   90   91   91   91   91   91   90   91   92   91   90
실험군    85   89   89   90    7    0    0    0    0    0    0    0    0    0    0    0
뒤 절반(4~8초) 성공: 대조군 727, 실험군 0 → 가설 반증됨 — 약점 발견
[host] 15:09:55.839 redis-b 재시작 완료
== 클라이언트: resilient (0.5초 구간별 성공 INCR 수, 장애 주입 ≈ 2.0초)
구간(초)   0.0  0.5  1.0  1.5  2.0  2.5  3.0  3.5  4.0  4.5  5.0  5.5  6.0  6.5  7.0  7.5
대조군    73   89   90   91   90   90   88   90   91   90   91   90   90   88   90   91
실험군    72   89   90   91   15   44   89   90   91   91   90   90   90   90   90   91
뒤 절반(4~8초) 성공: 대조군 721, 실험군 723 → 가설 유지(반증 실패)
```

- 관찰 1 — naive: 같은 방식으로 재시작한 resilient 실행에서는 주입 뒤 두 구간 안에 클라이언트 성공이 회복됐는데, naive 클라이언트는 실험이 끝날 때까지 **0**이었다(Redis 프로세스 자체가 언제 다시 준비됐는지는 이 실험에서 따로 재지 않았다 — 회복 구간에는 재연결·백오프 시간도 들어 있다). 끊긴 소켓을 계속 쓰기 때문이다. 오류를 삼켜서 예외 로그도 없다.
- 관찰 2 — resilient: 두 구간(15, 44)만 떨어졌다가 3.0초 구간부터 대조군과 같아졌다.
- 관찰 3 — 대조군이 있어서 "실험군만 떨어졌다"를 말할 수 있다. 두 군이 함께 떨어졌다면 장애 주입이 아니라 환경(호스트 부하) 탓을 의심한다.
- 관찰 4 — 한 번 더 돌렸을 때도 naive 실험군은 2.0초 구간부터 0, resilient는 `17 43` 뒤 회복이었다. 점검 재실행 2회도 같은 모양이었다(naive는 2.5초 구간부터 끝까지 0, resilient 두 구간 `27 31`·`33 24` 뒤 회복). 떨어진 두 구간의 값은 실행마다 다르다(15~44).
- 해석: 장애 주입 시각은 스크립트상 2.6초인데 실험군은 2.0초 구간(2.0~2.5초)부터 떨어졌다. 컨테이너 기동 시간만큼 JVM의 0초가 늦게 시작해서 두 시계가 어긋난다. 주입 시각은 같은 시계(앱 로그)에 남겨야 정확하다.

## 쓰이는 자료구조·알고리즘

- **시간 구간 버킷(히스토그램)** — 정상 상태를 구간별 성공 수 배열로 잰다. 분위수가 필요하면 지연 히스토그램(HDR 등).
- **대조군·실험군 비교 = 가설 검정의 틀** — 두 표본의 차이가 잡음보다 큰가. 실험에서는 단순 기준(실험군 ≥ 대조군의 90%)을 썼다. 운영 규모에서는 통계 검정·신뢰 구간을 쓴다.
- **지수 백오프** — resilient 클라이언트의 재연결 간격 → [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md).
- **무작위 선택** — Chaos Monkey는 인스턴스를 무작위로 고른다. 실험군 사용자도 무작위·소수 비율로 고른다(폭발 반경).

## 적용 — 풀어나가는 법

### 1. 첫 실험을 고르는 순서

1. 최근 포스트모템과 설계서의 **가정**을 모은다. "자동 재연결", "페일오버 30초", "캐시가 죽어도 DB가 버틴다".
2. 영향 × 빈도로 고른다. 처음엔 되돌리기 쉬운 것(인스턴스 하나 종료, 의존성 하나 지연).
3. 정상 상태 지표와 **중단 조건**을 정한다(예시: 실험군 오류율이 2%를 넘으면 즉시 중단·원복).
4. 스테이징 → 운영의 작은 비율 → 넓게. 근무 시간에, 대응할 사람이 있을 때.
5. 결과를 포스트모템처럼 기록한다. 약점이면 조치 항목, 아니면 자동화해서 계속 돌린다.

### 2. 게임 데이

```text
 준비   시나리오(예: 주 DB 페일오버), 범위, 중단 조건, 관찰자, 롤백 방법
 실행   장애 주입 → 온콜은 실제처럼 대응(런북, 사고 지휘, 공지)
 관찰   탐지까지 시간, 런북이 맞았나, 누가 무엇을 몰랐나
 회고   조치 항목: 시스템 결함 + 절차·문서 결함
```

- AWS Well-Architected REL12-BP05가 꼽는 안티패턴: 절차를 문서로만 두고 연습하지 않는다, 사업 의사결정자를 빼고 한다.
- 게임 데이는 사람의 연습이기도 하다. 과거 포스트모템을 재연하는 Wheel of Misfortune(SRE 15장)도 같은 계열이다.

### 3. 도구와 명령 (개념 예)

```bash
# 컨테이너·프로세스 종료 / 재시작
docker restart -t 0 <container>                 # 위 실험
kubectl delete pod <pod> --grace-period=1       # 파드 하나 죽이기 (--grace-period=0은 --force 없이는 kubectl이 1로 바꾼다 — kubectl delete.go)
# 네트워크 지연·손실 (NET_ADMIN 권한 필요)
tc qdisc add dev eth0 root netem delay 200ms loss 5%
tc qdisc del dev eth0 root
# 의존성 일시 정지(응답 없음 흉내 — 연결은 살아 있음)
docker pause <container>; sleep 10; docker unpause <container>
```

- 라이브러리 수준 주입: 테스트에서 하류 클라이언트를 지연·오류를 내는 가짜로 바꾼다. 서비스 메시(Envoy 등)의 fault 필터로 요청 일부에 지연·오류를 넣는 방법도 있다(→ [50-sidecar-ambassador-and-service-mesh](../50-sidecar-ambassador-and-service-mesh/2-summary.md)).
- 관리형 도구(AWS Fault Injection Service, Gremlin, Chaos Mesh 등)는 중단 조건·범위 제한을 기능으로 준다. 도구보다 먼저 가설과 중단 조건을 정한다.

### 4. 실험이 찾는 전형적 약점

- 재연결 로직 없음(위 실험), 타임아웃 없음 → 스레드 고갈(05·28), 재시도 폭풍(06), 폴백 미설정, 단일 장애점, 헬스체크가 의존성을 봐서 전 인스턴스 동시 unhealthy(47).
- Principles 문서가 꼽은 약점 예: 서비스 불가 시 부적절한 폴백, 잘못 맞춘 타임아웃으로 인한 재시도 폭풍, 하류가 과도한 트래픽을 받아 생기는 장애, 단일 장애점이 죽어 생기는 연쇄 장애.

## 장애 시나리오와 대처

### 1. ⚠ 가정한 페일오버가 실제로는 안 됨을 사고 때 발견

- 현상: Redis 주 서버가 바뀌었는데 애플리케이션은 계속 실패한다. Redis 자체는 1분 안에 정상이다.
- 보이는 형태: 위 실험의 naive처럼 오류가 0에서 회복되지 않는다. 애플리케이션 재시작으로만 복구된다. 오류를 삼키는 코드라 로그도 비어 있다.
- 원인: 클라이언트가 끊긴 연결을 버리지 않는다(재연결·타임아웃 없음). 또는 DNS·엔드포인트를 캐시해 옛 주 서버를 계속 본다.
- 대처: 같은 장애를 평소에 주입해 본다(실험군·대조군). 재연결·타임아웃·백오프를 넣고 다시 주입해 회복 시간을 잰다. 회복 시간을 SLO처럼 기록한다.

### 2. 실험이 실제 사고가 됐다 — 폭발 반경 관리 실패

- 현상: 카오스 실험 중 전체 사용자 오류율이 올랐는데 중단하는 데 20분 걸렸다.
- 보이는 형태: 실험군 비율 설정 실수(1% 대신 100%), 중단 버튼이 없음, 실험 담당이 자리에 없음.
- 원인: 중단 조건·범위 제한·근무 시간 원칙을 빠뜨렸다.
- 대처: 자동 중단 조건(지표 임계 → 원복)을 실험 정의에 넣는다. 작은 비율부터. 근무 시간에만 자동 실행. 실험도 사고 관리(26) 대상으로 다룬다.

### 3. 정상 상태 지표를 잘못 골라 약점을 놓친다

- 현상: 실험은 늘 "통과"인데 실제 사고는 난다.
- 보이는 형태: 정상 상태 지표가 CPU·메모리 같은 내부 속성이다. 사용자 오류율·지연 분위수를 보지 않는다.
- 원인: 원칙 문서가 말하는 "측정 가능한 출력" 대신 내부 상태를 봤다.
- 대처: 사용자 관점 지표(성공률, p99, 업무 지표 — Netflix의 SPS 같은)로 정상 상태를 정의한다.

### 4. 한 번 해 보고 끝 — 시스템이 바뀌어 다시 깨진다

- 현상: 작년 게임 데이에서 통과한 페일오버가 올해 사고에서 실패했다. 그 사이 클라이언트 라이브러리를 바꿨다.
- 보이는 형태: 마지막 실험 날짜가 오래됐다. 변경 이력에 관련 구성 요소의 교체.
- 원인: 시스템은 계속 바뀌고, 지난 실험의 확신은 시간이 갈수록 줄어든다(Basiri 외 2016).
- 대처: 실험을 자동화해 정기·지속 실행한다. 주요 변경(라이브러리 교체, 인프라 이전) 뒤에는 관련 실험을 다시 돈다.

## 핵심 문장

- 카오스 엔지니어링은 장애를 일부러 넣어 "견딘다"는 확신을 쌓는 실험이다. 정상 상태를 정의하고, 대조군과 실험군의 차이로 가설을 반증하려 한다.
- 정상 상태는 내부 속성이 아니라 측정 가능한 출력(성공률·지연 분위수·업무 지표)이다.
- 실험에서 Redis를 재시작하자, 재연결하는 클라이언트는 두 구간만 떨어졌다가 대조군과 같아졌지만, 끊긴 소켓을 계속 쓰는 클라이언트는 끝까지 성공 0이었다.
- 폭발 반경을 작게, 중단 조건을 먼저, 근무 시간에. 운영 실험은 목표이고 시작은 작은 범위다.
- 게임 데이는 시스템과 함께 사람·런북·사고 지휘를 연습한다. 한 번이 아니라 자동화해 계속 돌린다.

## 관련 주제·근거

- 선행
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 게임 데이에서 연습할 사고 대응
- 후속·연결
  - [44-runbooks-and-operational-readiness](../44-runbooks-and-operational-readiness/2-summary.md) — 게임 데이에서 런북을 검증, PRR의 "의존이 죽으면" 증거
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md), [10-circuit-breaker](../10-circuit-breaker/2-summary.md), [28-bulkhead](../28-bulkhead/2-summary.md) — 실험이 검증하는 방어선
  - [25-high-availability-topology](../25-high-availability-topology/2-summary.md), [46-disaster-recovery](../46-disaster-recovery/2-summary.md)
  - [distributed/03-partial-failure-and-timeouts](../../distributed/03-partial-failure-and-timeouts/2-summary.md) — 부분 실패
  - [testing 영역](../../testing/README.md) — 테스트 일반
- 논문·문서
  - Basiri, Behnam, de Rooij, Hochstein, Kosewski, Reynolds, Rosenthal, "Chaos Engineering", IEEE Software 33(3):35–41, 2016 (arXiv 1702.05843) — Chaos Monkey(근무 시간만), Chaos Kong(월 1회), FIT, SPS, 네 단계, 북마크 서비스 가상 실험
  - Principles of Chaos Engineering(2019-03 갱신) <https://principlesofchaos.org/>
  - AWS Well-Architected Reliability Pillar REL12-BP05 "Conduct game days regularly" <https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_game_days_resiliency.html>
  - Google SRE 책 15장 — Wheel of Misfortune(과거 포스트모템 재연)
- 실험 목록
  - Redis 재시작 카오스 실험: `Chaos.java`(RESP 직접 구현 naive·resilient 클라이언트, 대조군 redis-a·실험군 redis-b, 0.5초 구간 성공 수), 호스트에서 `docker restart -t 0 sn-rl-w26-redis-b`(시작 2.6초 뒤). Redis 7.4.9 + JDK 21.0.12, 각 2회 실행(점검 재실행 2회 추가)
