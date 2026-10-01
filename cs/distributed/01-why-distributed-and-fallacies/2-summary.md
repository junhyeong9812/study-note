# distributed/01-why-distributed-and-fallacies — 왜 여러 대로 나누나, 그리고 처음 만들 때 믿는 8가지 착각 — 정리 (힌트)

## 해결하는 문제

컴퓨터 한 대로는 안 되는 일이 있다. MIT 6.5840 첫 강의(2026, L1)는 이유를 네 가지로 든다.

```text
  한 대로 안 되는 이유                     여러 대로 나누면
  ─────────────────────────────           ─────────────────────────────
  처리량이 모자란다                  →    병렬 처리로 용량을 늘린다
  한 대가 죽으면 서비스가 멈춘다      →    복제로 장애를 견딘다
  장치가 원래 여러 곳에 있다(센서 등) →    물리적 위치에 맞춰 둔다
  한 곳이 뚫리면 전부 뚫린다          →    격리로 보안을 높인다
```

- *분산 시스템(distributed system)*: 여러 컴퓨터가 네트워크로 협력해 하나의 서비스를 내는 것(6.5840 L1의 정의).
- 대가가 있다. 같은 강의가 "만들기 어렵다"의 이유로 동시성, 복잡한 상호작용, 성능 병목, **부분 실패**를 꼽는다.
  - *부분 실패(partial failure)*: 시스템의 일부만 고장 나고 나머지는 멀쩡한 상태. 한 대짜리 프로그램에서는 거의 없던 일이다(DDIA 1판 8장 "Faults and Partial Failures").

쉬운 예: 혼자 하는 가게와 지점이 여러 개인 가게.
- 혼자 하면 내가 아프면 문을 닫는다. 대신 "내가 한 일"은 내가 다 안다.
- 지점이 여러 개면 한 곳이 문을 닫아도 장사는 된다. 대신 지점끼리 전화로만 연락한다.
- 전화가 안 받아지면 그 지점이 문을 닫았는지, 통화 중인지, 전화선이 끊겼는지 알 수 없다.

똑같은 구조다.\
분산은 용량과 내결함성을 얻는 대신 **"상대가 무엇을 했는지 확실히 알 수 없는 상태"**를 떠안는다.\
처음 분산 코드를 쓰는 사람은 이 불확실성을 없는 셈 치는 가정을 몇 가지 한다. 그것이 Peter Deutsch가 정리한 **분산 컴퓨팅의 8가지 오류**다.

실무 예:
- 주문 서비스가 결제 서비스를 HTTP로 부른다. 타임아웃을 안 걸었다. 결제 서비스가 멈추자 주문 서비스의 스레드가 전부 기다리다 주문 서비스까지 멈춘다.
- 화면 하나를 그리려고 상품 100개를 원격 조회 100번으로 가져온다. 로컬에서는 빨랐는데 운영에서는 느리다.
- DB 페일오버로 주소가 바뀌었는데, 앱이 옛 IP를 쥐고 있어 계속 실패한다.

## 동작·원리

### 1. 한 대와 여러 대 — 실패가 어떻게 다르게 보이나

```text
  한 대 (단일 프로세스)                       여러 대 (네트워크로 연결)
  ┌───────────────────────┐                 ┌────────┐   요청    ┌────────┐
  │ f() 호출 → 반환 또는 예외 │                 │ 노드 A │ ───────→ │ 노드 B │
  │ 하드웨어가 고장 나면       │                 │        │ ←─────── │        │
  │  보통 전체가 멈춘다        │                 └────────┘   응답?   └────────┘
  │ (커널 패닉·블루스크린)     │                 B가 죽었나? 느린가? 요청이 사라졌나?
  └───────────────────────┘                 응답이 사라졌나? → A는 구분 못 한다
   "되거나, 안 되거나"                          "됐는지 안 됐는지 모른다"가 생긴다
```

- DDIA 8장: 한 컴퓨터는 내부 오류가 나면 **틀린 결과를 내기보다 통째로 멈추도록** 설계한다. 그래서 "되거나 안 되거나"다.
- 슈퍼컴퓨터는 부분 실패를 **전체 실패로 키워서** 다룬다. 한 노드가 고장 나면 작업 전체를 멈추고 체크포인트에서 다시 시작한다(DDIA 8장 "Cloud Computing and Supercomputing").
- 인터넷 서비스는 그럴 수 없다. 온라인이라 멈추면 안 되고, 범용 장비라 늘 무언가는 고장 나 있다. 그래서 **부분 실패를 견디는 코드를 소프트웨어로 짜야 한다**(같은 절).

### 2. 8가지 오류 — 목록과 코드에서 보이는 모양

Deutsch가 정리한 원문 목록(nighthacks.com에 실린 판):

| # | 착각 | 실제 | 코드에서 보이는 모양 |
|---|---|---|---|
| 1 | 네트워크는 믿을 만하다 | 요청·응답이 사라지거나 늦는다 | 타임아웃 없는 호출, 재시도 없는 호출, 재시도하는데 멱등이 아닌 호출 |
| 2 | 지연은 0이다 | 왕복마다 시간이 든다 | 루프 안의 원격 호출(N번 왕복), 수다스러운(chatty) API |
| 3 | 대역폭은 무한하다 | 링크·NIC·큐에 한계가 있다 | 응답에 필요 없는 필드까지 통째로, 페이지네이션 없는 목록 |
| 4 | 네트워크는 안전하다 | 도청·위조·중간자가 있다 | 내부망이라고 평문 HTTP, 인증 없는 내부 API |
| 5 | 토폴로지는 바뀌지 않는다 | 주소·경로·노드가 바뀐다 | IP 하드코딩, DNS 결과를 영원히 캐시 |
| 6 | 관리자는 한 명이다 | 팀·회사마다 정책이 다르다 | 방화벽·프록시·인증서 정책 충돌을 모름 |
| 7 | 전송 비용은 0이다 | 직렬화 CPU, 망 사용료가 든다 | 큰 JSON 반복 직렬화, 리전 간 트래픽 비용 무시 |
| 8 | 네트워크는 균질하다 | 장비·버전·프로토콜이 섞인다 | 구버전·신버전이 섞인 배포에서 메시지 형식 불일치 |

- 역사(위키백과가 인용한 2004년 Van Den Hoogen 기사 기준): Deutsch가 1994년에 7개를 정리했고, 1997년 무렵 James Gosling이 8번째를 더했다. 그중 4개는 그 전에 Bill Joy와 Dave Lyon이 "The Fallacies of Networked Computing"으로 정리한 것이다.
- 위키백과는 각 오류의 결과를 이렇게 정리한다. 1번을 무시하면 **네트워크 장애 동안 무한히 기다리며 자원을 붙잡고**, 복구 뒤에도 멈춘 작업을 재시도하지 못하거나 수동 재시작이 필요해진다.
- 이 노트는 1·2번을 아래 실험으로 본다. 4번은 network 영역(TLS·mTLS), 5·6번은 network 영역(DNS 캐시·방화벽)에서 이어진다.

### 3. 응답이 안 올 때 가능한 여섯 가지 — "믿을 만하다"가 깨지는 방식

DDIA 8장 "Unreliable Networks"가 드는 여섯 경우를 시간축으로 그리면 이렇다(그림 8-1은 그중 요청 유실·상대 죽음·응답 유실 세 경우를 그린다).

```text
  A(요청자)                  네트워크                  B(응답자)
  ──────────────────────────────────────────────────────────────
  ① 요청 ─────────────X                                          요청이 사라짐
  ② 요청 ──────────[큐에서 대기 중 …] ──────────→                늦게 도착
  ③ 요청 ──────────────────────────────→  ✝                      B가 죽어 있음
  ④ 요청 ──────────────────────────────→  (GC로 멈춤 … 나중에 응답) B가 잠시 멈춤
  ⑤ 요청 ──────────────────────────────→  처리 완료
           X───────────── 응답                                    응답이 사라짐
  ⑥ 요청 ──────────────────────────────→  처리 완료
     …… 응답이 [큐에서 대기 중] ……                                 응답이 늦음
  ──────────────────────────────────────────────────────────────
  A가 보는 것: 여섯 경우 모두 "아직 응답이 없다" 하나뿐
```

- *비동기 패킷 네트워크(asynchronous packet network)*: 보낸 패킷이 **언제 도착할지, 도착하기는 할지** 보장하지 않는 네트워크. 인터넷과 대부분의 데이터센터 내부망(이더넷·IP)이 여기에 해당한다(DDIA 8장).
- A는 ①~⑥을 구분할 수 없다. 할 수 있는 일은 **타임아웃**뿐이다. 타임아웃이 나도 B가 요청을 받았는지는 여전히 모른다(⑤·⑥).
- 이 노트는 여기까지 짚는다. 결과를 모르는 상태를 어떻게 다루는지는 03에서 본다.
- 참고(6.5840 L2 RPC 노트): 클라이언트 RPC 라이브러리가 보는 실패는 "응답을 끝내 못 받았다" 하나다. 서버가 요청을 봤는지는 모른다. 그래서 원격 호출은 같은 기계 안의 함수 호출처럼 동작하지 않는다.

### 실험: 응답 없는 서버를 타임아웃 없이 부르기 / 왕복 1000번 vs 1번

두 착각(1번·2번)을 코드로 확인했다.
- A. 연결은 받아 주지만 응답을 영원히 안 보내는 서버를 만든다(멈춘 프로세스와 같은 모양). Java 21 `HttpClient`로 부른다.
  - `HttpRequest`에 `timeout()`을 안 주면 어떻게 되나? Java 21 문서: "타임아웃을 설정하지 않은 효과는 무한 Duration을 준 것과 같다. 즉, 영원히 막힌다."
- B. 같은 1000건을 (1) 프로세스 안 `HashMap`에서, (2) Redis에 `GET` 1000번 왕복으로, (3) `MGET` 한 번으로 읽는다.

```java
// A-1: 타임아웃 없음
HttpRequest noTimeout = HttpRequest.newBuilder(uri).GET().build();
client.send(noTimeout, HttpResponse.BodyHandlers.ofString());          // 영원히 기다린다

// A-2: 요청 타임아웃 1초
HttpRequest withTimeout = HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(1)).GET().build();
client.send(withTimeout, HttpResponse.BodyHandlers.ofString());        // 1초 뒤 HttpTimeoutException

// B: 왕복 1000번 vs 1번 (RESP 프로토콜을 소켓에 직접 씀)
for (int i = 0; i < 1000; i++) { cmd(out, "GET", "w01:k" + i); out.flush(); readReply(in); }
cmd(out, mget); out.flush(); readReply(in);                            // MGET w01:k0 … w01:k999
```

(실험, Temurin 21.0.12 컨테이너 → Redis 7.4.9 컨테이너, 같은 호스트의 Docker 브리지 네트워크, 2026-10-01)

```text
[A-1] 타임아웃 없음: 1초 경과, 호출 스레드 상태=WAITING
[A-1] 타임아웃 없음: 2초 경과, 호출 스레드 상태=WAITING
[A-1] 타임아웃 없음: 3초 경과, 호출 스레드 상태=WAITING
[A-1] 타임아웃 없음: 4초 경과, 호출 스레드 상태=WAITING
[A-1] 타임아웃 없음: 5초 경과, 호출 스레드 상태=WAITING
[A-2] 타임아웃 1초: 1002 ms 뒤 HttpTimeoutException: request timed out
[A] 서버가 받은 연결 수 = 2 (연결은 성립했다 — 서버는 살아 있다)
[B] 1000건 조회: 프로세스 안 HashMap 0.287 ms | Redis GET 1000번 왕복 55.5 ms (왕복당 55.5 µs) | Redis MGET 1번 1.58 ms
[B] 정리: DEL 지운 키 수 = 1000
```

- 관찰 A: 타임아웃이 없으면 호출 스레드가 5초 내내 `WAITING`이다. 실험은 5초에서 끊었을 뿐, 서버가 응답하지 않는 한 계속 기다린다. 연결은 성립했으니 "서버가 죽었다"는 신호도 오지 않는다.
- 관찰 B: 같은 호스트의 가상 네트워크인데도 왕복이 한 번에 수십 µs 든다. 1000번 왕복은 한 번 왕복(`MGET`)보다 35배 느렸다.
  - 시간 값은 실행마다 다르다. 세 번 돌렸을 때 `GET` 1000번은 42~59 ms, `MGET`은 1.4~1.9 ms, 배율은 23~43배였다(사실 점검 때 세 번 더 돌린 값: `GET` 45~116 ms, `MGET` 1.3~3.6 ms, 27~35배 — 절댓값은 호스트 부하에 따라 컸지만 순서와 수십 배 차이는 같았다). 순서(메모리 ≪ 1번 왕복 ≪ 1000번 왕복)는 같았다.
  - 다른 데이터센터·대륙이면 왕복 하나가 훨씬 길다. etcd 3.6 튜닝 문서는 미국 대륙 안 왕복을 130 ms, 미국–일본을 350~400 ms로 예를 든다. 그 경우 1000번 왕복은 분 단위가 된다(계산).

### 4. 세 목표는 서로 싸운다

6.5840 L1의 정리:

```text
          내결함성(fault tolerance)
               ╱          ╲
     복제본에 보내야 한다     캐시가 최신인지 물어봐야 한다
             ╱                ╲
     일관성(consistency) ──── 성능(performance)
          통신이 필요하다 ↔ 통신은 느리고 늘리기 어렵다
```

- 내결함성과 일관성은 **통신**을 요구한다. 통신은 느리다(2번 착각의 반대).
- 그래서 많은 설계가 속도를 위해 일관성을 일부 포기한다. 예: `read(x)`가 가장 최근 `write(x)`를 못 볼 수 있다.
- 이후 단원(복제·일관성·합의)이 이 세 축 사이의 설계점들이다.

## 쓰이는 자료구조·알고리즘

이 단원은 "무엇이 깨지나"를 보는 모델 단원이다. 대응 도구만 미리 이름을 붙여 둔다.

| 착각 | 대응 도구 | 들어 있는 것 |
|---|---|---|
| 1 믿을 만하다 | 타임아웃, 재시도 + 지수 백오프·지터, 멱등 키 | 타이머(최소 힙·타이밍 휠), 키→결과 해시 맵 |
| 2 지연 0 | 배치(`MGET`), 파이프라이닝, 캐시 | 요청 묶음 버퍼, 근처 복사본 |
| 3 대역폭 무한 | 페이지네이션, 압축, 필드 선택 | 커서(정렬 키) |
| 5 토폴로지 고정 | 서비스 디스커버리, 짧은 DNS TTL | 이름 → 주소 매핑 + 만료 시각 |
| 8 균질 | 하위 호환 스키마(필수 아닌 필드만 추가, 받는 쪽은 모르는 필드를 무시), 버전 협상 | 버전 번호가 붙은 메시지 |

- 재시도 백오프: [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)
- 멱등 키 저장소: [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
- DNS 캐시와 TTL: [network/28-dns-caching-and-ttl](../../network/28-dns-caching-and-ttl/2-summary.md)

## 적용 — 풀어나가는 법

원격 호출 하나를 쓸 때마다 묻는 순서다.

1. **기다리는 상한이 있나?** — 연결 타임아웃과 요청(응답) 타임아웃을 둘 다 건다. 하나만 걸면 나머지 구간에서 무한 대기가 남는다.
2. **실패하면 다시 보내나? 다시 보내도 안전한가?** — 조회는 대체로 안전하다. 결제·주문 생성은 멱등 키 없이 재시도하면 두 번 실행될 수 있다(03).
3. **왕복이 몇 번인가?** — 루프 안의 원격 호출을 찾는다. 묶을 수 있으면 묶는다.
4. **얼마나 보내나?** — 목록에 상한, 응답에 필요한 필드만.
5. **평문인가?** — 내부망도 TLS(network/29·32).
6. **주소를 어떻게 얻나?** — IP 하드코딩 금지. DNS를 쓰면 캐시 시간을 안다.
7. **상대 버전이 섞여도 되나?** — 롤링 배포 중에는 구·신 버전이 동시에 돈다.

```java
// 1·2를 지킨 기본형 (Java 21 java.net.http)
HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofMillis(500))          // 연결 단계 상한
        .build();
HttpRequest req = HttpRequest.newBuilder(URI.create(base + "/products?ids=" + joinedIds)) // 3: 한 번에 묶어 조회
        .timeout(Duration.ofSeconds(2))                   // 응답 대기 상한 (없으면 영원히)
        .GET()
        .build();
HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
```

- `connectTimeout`은 **새 연결을 맺어야 할 때** 연결 단계에 거는 상한이다(Java 21 `HttpClient.Builder` 문서: "In the case where a new connection needs to be established…"). 재사용 연결에는 걸릴 일이 없다(해석). 응답 대기는 `HttpRequest.timeout`이 맡는다.
- 구버전 `HttpURLConnection`도 기본 읽기 타임아웃이 0이고, 0은 무한을 뜻한다(Java 21 `URLConnection.setReadTimeout` 문서).

진단 명령:
- 어디서 막혔나: `jcmd <pid> Thread.print` → 원격 호출에서 `WAITING`·`TIMED_WAITING`인 스레드 수를 센다.
- 연결이 얼마나 쌓였나: `ss -tnp state established '( dport = :8080 )'`
- 구간별 시간: `curl -o /dev/null -s -w 'connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://…`
- 왕복 지연 감 잡기: `ping`, `mtr`(경로별 손실·지연) — [network/50-network-diagnostics](../../network/50-network-diagnostics/2-summary.md) 참고.

## 장애 시나리오와 대처

### 1. 타임아웃 없는 호출 → 무한 대기 → 호출자까지 멈춤 (⚠ 무한 대기)

- **현상**: 하류 서비스 하나가 멈추자 그걸 부르는 서비스의 응답이 전부 멈춘다. 하류가 되살아나도 바로 회복되지 않는다.
- **보이는 형태**: 스레드 덤프에 같은 원격 호출에서 `WAITING`인 스레드가 풀 크기만큼 있다. 요청 큐가 차고 상류에서 504가 난다. 에러 로그는 오히려 조용하다(예외가 안 나므로).
- **원인**: 1번 착각. 기다림에 상한이 없어 스레드가 반환되지 않는다(위 실험 A-1).
- **대처**: 연결·응답 타임아웃을 모두 건다. 하류별로 스레드 풀을 나눈다(벌크헤드). 반복 실패면 즉시 거절한다(서킷 브레이커, [ops-patterns/02-circuit-breaker](../../ops-patterns/02-circuit-breaker/2-summary.md)).

### 2. 응답이 사라졌는데 "실패"로 처리 → 데이터 불일치 (⚠ 데이터 불일치)

- **현상**: 외부 결제는 승인됐는데 내부 주문은 "결제 실패"다. 또는 재시도로 두 번 결제됐다.
- **보이는 형태**: 대사(reconciliation)에서 "외부엔 있고 내부엔 없는" 건이 나온다. 고객 문의 "돈은 빠졌는데 주문이 없어요".
- **원인**: 그림의 ⑤·⑥. 타임아웃은 "실패"가 아니라 "모름"인데 실패로 확정했다. 재시도했다면 멱등하지 않은 연산을 두 번 실행했다.
- **대처**: 타임아웃 결과를 "모름(pending)"으로 기록하고 조회·대사로 확정한다. 재시도는 멱등 키와 함께. 자세한 것은 03.

### 3. 루프 안 원격 호출 → 운영에서만 느림 (2번 착각)

- **현상**: 로컬·개발 환경에서는 빠른 화면이 운영에서 수 초 걸린다. 항목 수에 비례해 느려진다.
- **보이는 형태**: 분산 트레이싱에서 같은 하류 호출 스팬이 수십~수백 개 줄지어 있다. 각 스팬은 짧은데 합이 길다.
- **원인**: 왕복 지연 × 호출 수. 위 실험에서 같은 호스트 안에서도 1000번 왕복이 한 번 묶음보다 23~43배 느렸다.
- **대처**: 묶음 API(`ids=` 여러 개, `MGET`), 파이프라이닝, 병렬 호출(전체 시간 = 가장 느린 하나), 캐시. DB 쪽의 같은 문제는 N+1([database/23-orm-and-n-plus-one](../../database/23-orm-and-n-plus-one/2-summary.md)).

### 4. 주소가 바뀌었는데 옛 주소로 계속 (5번 착각)

- **현상**: DB·서비스 페일오버 뒤 일부 앱만 계속 실패한다. 재시작하면 낫는다.
- **보이는 형태**: `Connection refused`·`No route to host`가 옛 IP로 찍힌다.
- **원인**: IP를 설정에 박아 뒀거나, 이름 조회 결과를 오래 캐시했다. JDK 21(Temurin)의 `java.security` 주석은 보안 관리자가 없으면 성공한 조회를 30초, 실패한 조회를 10초 캐시한다고 적는다. 커넥션 풀이 옛 연결을 붙잡고 있는 경우도 있다.
- **대처**: 이름으로 접속하고 캐시 시간을 확인한다. 풀에 연결 최대 수명을 둔다([database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)). 반쯤 열린 연결은 TCP keepalive·user timeout으로 정리한다([network/21](../../network/21-tcp-keepalive-and-user-timeout/2-summary.md)).

## 핵심 문장

- 분산하는 이유는 용량(병렬), 내결함성(복제), 물리적 위치, 격리다. 대가는 부분 실패다.
- 한 컴퓨터는 "되거나 안 되거나"지만, 네트워크 너머의 호출은 "됐는지 모른다"가 생긴다.
- 응답이 없을 때 요청 유실·대기·상대 죽음·상대 멈춤·응답 유실·응답 지연을 요청자는 구분할 수 없다. 할 수 있는 건 타임아웃뿐이다.
- Java 21 `HttpClient`는 요청 타임아웃을 주지 않으면 영원히 기다린다. 원격 호출마다 상한을 건다.
- 같은 호스트 안에서도 왕복 1000번은 묶음 1번보다 수십 배 느렸다. 지연은 0이 아니다.
- 내결함성·일관성·성능은 서로 싸운다. 이후 단원은 그 사이의 설계점이다.

## 관련 주제·근거

- 선행
  - [network/49-what-happens-when-url](../../network/49-what-happens-when-url/2-summary.md) — 요청 하나가 지나는 구간과 구간별 실패
- 후속
  - [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md) — 동기·비동기 모델, crash·비잔틴
  - [03-partial-failure-and-timeouts](../03-partial-failure-and-timeouts/2-summary.md) — 결과를 모르는 상태와 타임아웃 고르기
  - [25-impossibility-results](../25-impossibility-results/2-summary.md) — 두 장군·FLP
- 연결
  - [network/03-latency-bandwidth-bdp](../../network/03-latency-bandwidth-bdp/2-summary.md) — 2·3번 착각의 수치 감각
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) · [network/48-firewalls-and-network-policy](../../network/48-firewalls-and-network-policy/2-summary.md) — 4·6번 착각
  - [ops-patterns/failure-at-scale](../../ops-patterns/failure-at-scale/2-summary.md) — 규모가 커지면 바뀌는 실패 양상
- 근거
  - Peter Deutsch, "The Eight Fallacies of Distributed Computing" <https://nighthacks.com/jag/res/Fallacies.html>
  - 위키백과 "Fallacies of distributed computing" — 오류별 결과, 역사(Deutsch 1994 7개, Gosling 1997 8번째; Van Den Hoogen 2004 인용) <https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing>
  - MIT 6.5840 Spring 2026 Lecture 1 노트(분산의 이유·어려움·세 목표의 상충) <https://pdos.csail.mit.edu/6.824/notes/l01.txt>, Lecture 2 노트(RPC 실패 모양) <https://pdos.csail.mit.edu/6.824/notes/l-rpc.txt>
  - DDIA 1판 8장 "Faults and Partial Failures", "Unreliable Networks"(그림 8-1)
  - Java SE 21 API: `HttpRequest.Builder.timeout`, `HttpClient.Builder.connectTimeout`, `URLConnection.setReadTimeout` <https://docs.oracle.com/en/java/javase/21/docs/api/java.net.http/java/net/http/HttpRequest.Builder.html>
  - Temurin 21 `$JAVA_HOME/conf/security/java.security` — `networkaddress.cache.ttl` 주석(보안 관리자 없으면 30초), `networkaddress.cache.negative.ttl=10`
  - etcd v3.6 "Tuning" 문서 — 왕복 예시(미국 대륙 130 ms, 미국–일본 350~400 ms) <https://etcd.io/docs/v3.6/tuning/>
- 실험 목록
  - `Fallacies.java` — (A) 응답 없는 서버를 Java 21 `HttpClient`로 타임아웃 없이/1초로 호출, (B) Redis 7.4.9에 `GET` 1000번 vs `MGET` 1번 vs `HashMap`. 환경: `eclipse-temurin:21-jdk`(21.0.12) 컨테이너, 공용 `sn-dw-redis`(키 `w01:` 접두사, 실험 끝에 삭제), 같은 호스트 Docker 브리지.
