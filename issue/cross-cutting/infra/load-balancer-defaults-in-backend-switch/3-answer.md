# issue/cross-cutting/infra/load-balancer-defaults-in-backend-switch — 정답

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **기술자 한도에 먼저 닿아 앱에 닿지도 못하고 500이 나간다.**\
   프록시 요청 하나는 클라이언트 쪽 연결 하나와 upstream 쪽 연결 하나, 기술자 두 개를 쓴다 — `worker_connections`는 그 둘을 함께 센다.\
   그런데 작업자 프로세스가 실제로 열 수 있는 수는 프로세스의 `nofile` 한도이고, 컨테이너 기본 soft 한도는 1024였다 — 8192는 설정값일 뿐 닿을 수 없는 숫자였다.\
   새 앱이 합류 직후 느려진 약 40초 동안 연결이 쌓이자 `socket()`·`accept4()`가 `(24: No file descriptors available)`로 203번 실패했고, 클라이언트는 500·연결 실패를 받았다.\
   응답만 보면 "전환 중 앱이 5xx를 냈다"로 읽히지만 앱은 그 요청을 받지도 못했다 — 오류 로그의 errno로 갈랐다.\
   교정은 `worker_rlimit_nofile 65536`(컨테이너 hard 한도 524288 안)으로 작업자 한도를 올리는 것이다.
   > **worker_rlimit_nofile** — nginx 작업자 프로세스의 열린 파일 수 한도(RLIMIT_NOFILE)를 바꾸는 지시어. 없으면 띄운 환경의 soft 한도를 그대로 쓴다.

2. **그 서버가 10초 동안 빠지고, 남은 서버가 없어 그 동안 전부 502다.**\
   upstream `server` 줄의 기본은 `max_fails=1` · `fail_timeout=10s`다 — `fail_timeout` 안에 실패가 `max_fails`번이면 그 서버를 `fail_timeout` 동안 쓰지 않는다(nginx 기본 동작).\
   옛 앱을 빼고 새 앱 하나만 남은 구간에서 요청 하나가 시한을 넘기자 새 앱이 제외됐고, 고를 서버가 없어 들어오는 요청이 모두 502가 됐다 — 첫 스모크에서 약 14초 동안 100% 502가 두 번 나왔다.\
   이 설정은 실패한 요청을 다른 서버로 다시 보내지 않는다(`proxy_next_upstream off` — 쓰기 요청이 멱등이 아니어서) — 서버가 여럿이어도 제외는 남은 서버로 몰아줄 뿐 실패한 요청을 살리지는 않는다.
   > **수동 장애 판정(passive health check)** — 별도 검사 요청 없이 실제 요청의 실패를 보고 서버를 잠시 빼는 방식. nginx 오픈소스판의 기본이다.

3. **생존 판단은 구성원을 관리하는 쪽이 맡는다 — health UP을 확인한 뒤에만 넣는다.**\
   `max_fails=0`은 nginx가 실패 횟수로 서버를 빼지 않게 한다 — 대신 죽은 서버를 빼는 일은 nginx 밖의 누군가가 해야 한다.\
   이 사례에서는 전환을 지휘하는 쪽이 새 앱의 health UP을 확인한 뒤 구성원 파일에 넣고, 내리기 전에 먼저 빼고 비움을 확인했다 — 생존과 구성원 변경이 한 곳에서 결정된다.\
   고친 뒤 다시 잰 같은 절차에서 새 앱 구간 502는 116,315건에서 28건으로 줄었다(5xx 119,442 → 12,888 — 남은 것은 차가운 새 프로세스의 연결 시한 504로, 로드밸런서 몫이 아니다).

4. **옛 작업자가 닫는 keepalive 연결 위에 막 실린 요청이 응답 없이 끝났다.**\
   reload 때 옛 작업자는 처리 중인 요청은 끝내지만, 요청을 기다리며 쉬고 있는(keepalive) 연결은 닫고 내려간다.\
   클라이언트는 그 연결이 아직 살아 있다고 보고 다음 요청을 싣는다 — 서버가 닫는 순간과 클라이언트가 보내는 순간이 겹치면 요청은 응답 없이 연결 오류(응답 코드 0)로 끝난다(일반적인 keepalive 경합).\
   스모크에서 구성원 빼기 reload 1회에 약 420~450건, 넣기 1회에 약 17~25건이었다 — reload 효력이 나는 데는 0.25~0.38초였다.
   > **keepalive 경합** — 서버가 유휴 연결을 닫는 순간과 클라이언트가 그 연결을 재사용하는 순간이 겹쳐 요청이 유실되는 현상. 멱등 요청이면 클라이언트 재시도로 감추지만, 비멱등 요청은 결과를 알 수 없게 된다.

5. **측정용 로드밸런서의 비용으로 보고, 보낸 시각 기준의 창으로 따로 센다.**\
   이 연결 오류는 reload를 몇 번 하느냐에 비례한다 — reload 4번인 절차가 가장 많았다(본측정 큰 부하에서 회차당 476~1,291건, 나머지 절차는 15~409건).\
   그대로 두면 reload가 많은 절차가 다운타임에서 불리해지는데, 그것은 절차의 성질이 아니라 이 로드밸런서의 연결 처리 방식이다 — 운영 로드밸런서는 연결을 서서히 비운다는 것이 기록의 판단이다(이 사례에서 검증하지 않음).\
   그래서 reload 사건마다 창 [사건 시작, reload 효력 + 1초] 안에서 **보낸** 요청의 연결 오류를 "로드밸런서 아티팩트"로 따로 세어 결과 표에 남기고, 다운타임 순위·실패 수에서 뺐다(모든 절차에 같은 규칙).\
   보낸 시각 = 완료 시각 − 지연 — 창 안에서 보내 30초 시한까지 기다리다 끝난 요청도 같은 원인이므로 완료 시각으로 자르면 빠진다.\
   효력 시각을 얻지 못한 사건은 창을 만들 수 없으므로 그 회차를 무효로 했다(조용히 빼지 않는다).

6. **로드밸런서 설정을 측정 전에 고정하고, 고칠 수 없는 몫은 창으로 분리해 남긴다.**\
   ①은 고칠 수 있는 결함이라 고쳤고(기술자 한도), ②는 측정 대상이 아닌 동작이라 끄고 책임을 옮겼고(수동 판정), ③은 끌 수 없어 따로 셌다(reload 연결).\
   어느 것이든 "앱 밖에서 생긴 오류"를 앱·절차의 결과에 섞지 않는다는 같은 기준이다 — 원인을 가를 근거(오류 로그의 errno·upstream 주소·응답 코드 0)를 접근 기록에 남겨야 구분할 수 있다.

## 문제 구조 (추상화 코드)

### 변형 A — 작업자 기술자 한도 < worker_connections
① 문제 코드
```nginx
worker_processes auto;
events { worker_connections 8192; }      # 컨테이너 soft nofile 1024 — 실제 상한은 1024
```
② 고친 코드
```nginx
worker_processes auto;
worker_rlimit_nofile 65536;              # hard 한도 안에서 작업자 한도를 올린다
events { worker_connections 8192; }      # 요청 1개 = 클라이언트 fd + upstream fd
```
무엇이 깨졌나: 연결 수 설정이 프로세스 자원 한도 위에 놓여 있었는데, 한도를 띄운 환경의 기본값에 맡겼다.

### 변형 B — 구성원 1대 구간의 기본 수동 장애 판정
① 문제 코드
```nginx
upstream apps {
  include members.conf;                  # server new-app:8080;   ← 기본 max_fails=1 · fail_timeout=10s
  keepalive 256;
}
location / { proxy_pass http://apps; proxy_next_upstream off; }
```
② 고친 코드
```bash
render_members() {                        # 구성원 렌더는 한 함수(원격에도 같은 함수를 보낸다)
  for s in "$@"; do echo "server $s:8080 max_fails=0;"; done      # nginx는 서버를 빼지 않는다
}
add_member() {                            # 생존 판단은 여기서 — health UP 뒤에만 넣는다
  wait_health "$1" || return 1
  render_members $CURRENT "$1" > members.conf.new && swap_and_reload members.conf.new
}
```
무엇이 깨졌나: 서버가 하나뿐일 때 "실패한 서버를 잠시 뺀다"는 보호가 "모든 요청을 거부한다"가 됐다.

### 변형 C — reload가 닫는 keepalive 연결 (고치지 않고 따로 셈)
```python
# 사건마다 창 [사건 시작, reload 효력 + 1초] — 보낸 시각 기준
for ev in reload_events:
    if ev.effective is None:
        invalidate(run, "lb-artifact-window-missing")      # 창을 못 만들면 조용히 빼지 않는다
        continue
    lo, hi = ev.start, ev.effective + 1.0
    art = [r for r in responses if r.status == 0 and lo <= r.done - r.latency <= hi]
    lb_artifact[ev.id] = len(art)                          # 결과 표에 별도 열
    excluded |= set(art)                                   # 다운타임·실패 수에서 뺀다
```
무엇이 깨졌나: 측정 도구(로드밸런서)의 연결 처리 비용이 측정 대상(전환 절차)의 다운타임으로 기록될 뻔했다.

## 검증 기록
- 2026-10-26: 사건 기록·설정 변경 기록 대조·추상화(Claude 초안) — 변형 A·B는 첫 실서버 스모크에서 발견해 고친 뒤 재스모크로 확인, 변형 C는 측정 전 규칙으로 정해 본측정에 적용. nginx 기본값(`max_fails=1` · `fail_timeout=10s`)과 keepalive 경합의 기제는 일반 지식, "운영 로드밸런서는 연결을 서서히 비운다"는 기록의 판단(미검증).

## 관련 카드
- [nginx-broadband-defense-friendly-fire](../nginx-broadband-defense-friendly-fire/) — 같은 프록시의 다른 기본 보호(레이트리밋·UA 차단)가 자기 트래픽을 막는 경우.
- [performance-measurement-validity](../../testing/performance-measurement-validity/) — 측정값이 유효하려면 측정 도구 자신의 몫을 갈라야 한다 — 부하 생성기의 자원 한계와 같은 축.
- [half-open-liveness-watchdog](../../network/half-open-liveness-watchdog/) — 연결이 살아 있다고 믿는 쪽과 이미 닫은 쪽의 불일치 — keepalive 경합과 같은 계열.

## 방안 비교 — 닫히는 keepalive 연결에 실린 요청: 따로 세기 vs 호출하는 쪽이 한 번 다시 보내기

변형 C와 같은 원리(reload 때 옛 작업자는 쉬고 있는 keepalive 연결을 닫고 내려가므로, 그 연결에 막 실린 요청은 응답 없이 연결 오류로 끝난다)다.\
변형 C는 측정 맥락이라 고치지 않고 따로 셌다 — 이 사례는 운영 경로라 셀 수 없고, 호출하는 쪽이 살려야 했다.

```text
서비스 A (클라이언트, 연결 풀 사용) ──keepalive──▶ [프록시 옛 작업자] ──▶ 옛 인스턴스
                                                      │ 전환(reload) 뒤 옛 작업자는 종료 중
   ① 첫 요청 POST /chat  ─────────────────────────────▶ 옛 인스턴스가 대기자에게 {"type":"retry"} (새 쪽으로 다시 보내라)
                                                      │ 응답을 마친 뒤 옛 작업자가 그 연결을 닫는다
   ② 곧바로 같은 POST 재전송 ── 풀에서 방금 그 연결을 꺼냄 ──▶ ✗ 연결 닫힘 → IOException
        클라이언트 라이브러리는 비멱등(POST) 요청을 자동으로 다시 보내지 않는다
        → "서버 꺼짐"으로 처리되어 재전송이 실패로 끝남
```
이 경합은 설계·구현 리뷰에서 지적됐다 — "재전송은 방금 응답을 마친 연결을 재사용할 가능성이 가장 높은 요청"이라는 것이 요지다.

### 방안 2 — 재전송 요청에 한해, 연결 단계에서 끊기면 잠깐 쉬고 한 번 더 보낸다 (이 사례에서 적용)
```kotlin
fun relay(request: Req, onEvent: (Event) -> Unit) {
    repeat(MAX_RESENDS + 1) { attempt ->
        if (!relayOnce(request, onEvent, isResend = attempt > 0)) return   // retry를 받았으면 true
        if (attempt == MAX_RESENDS) onEvent(Event.Failed)
    }
}

private fun relayOnce(request: Req, onEvent: (Event) -> Unit, isResend: Boolean): Boolean {
    val response = try {
        try {
            client.send(post(request), ofInputStream())
        } catch (error: IOException) {
            if (!isResend) throw error            // 첫 요청의 연결 실패 = 서버가 꺼진 것 — 다시 보내지 않는다
            Thread.sleep(200)                   // 닫히는 연결이 풀에서 빠질 틈
            client.send(post(request), ofInputStream())   // 한 번만
        }
    } catch (error: IOException) {
        throw UpstreamDown(error)
    }
    // ... 이벤트 읽기: start 전에 retry를 받으면 true ...
}
```
단위 재현은 원시 소켓 가짜 서버로 했다 — 첫 연결은 `retry`를 주고 닫고, 두 번째 연결은 요청을 받자마자 응답 없이 리셋(`SO_LINGER 0`)하고, 세 번째 연결에서 정상 응답한다 → 클라이언트는 `start`·`done`을 받고 연결은 3번 열렸다.\
"첫 요청의 연결 실패는 다시 보내지 않고 즉시 서버 꺼짐으로 본다"도 함께 시험했다.\
서버 배포 시험에서는 넘겨진 대기자 7건·2건이 모두 재전송 로그(`resending (1/2)`)와 함께 오류 없이 이어졌다 — 다만 이 경합 자체가 서버에서 일어난 것을 관측하지는 못했다.

| | 변형 C 따로 세기 | 방안 2 재전송에 한해 1회 다시 보내기 |
|---|---|---|
| 전제 | 측정용 경로라 실패를 결과에서 분리만 하면 된다 | 다시 보내는 이유(상대가 "아직 시작 안 함"으로 넘겼다)를 클라이언트가 알고, 같은 요청을 한 번 더 받아도 상대에게 해가 없다 |
| 비용 | 사건 창 계산·결과 표 열 | 클라이언트 코드 몇 줄 · 재전송마다 최대 200ms 지연 |
| 실패 모드 | 운영 경로에는 쓸 수 없다(사용자 요청이 실제로 실패) | 연결이 닫히기 전에 요청이 상대에게 닿았다면 같은 요청이 두 번 처리될 수 있다(이 사례에서 검증하지 않음) · 두 번째도 같은 이유로 끊기면 실패(상한 1회) |
| 맞는 조건 | 전환 절차 비교처럼 프록시 몫을 측정에서 빼야 할 때 | 프로토콜이 "다시 보내라"를 명시하는 인계·재시도 경로에서, 재사용 연결 경합을 클라이언트가 흡수해야 할 때 |

**결론**: keepalive 경합은 프록시를 고쳐 없앨 수 있는 것이 아니라 연결 재사용의 성질이다 — 측정이면 창으로 갈라 세고(변형 C), 운영이면 그 요청을 다시 보내도 되는 조건을 좁혀서(재전송 요청·연결 단계 실패·1회) 호출하는 쪽이 흡수한다.\
첫 요청까지 같은 규칙으로 다시 보내면 "서버가 정말 꺼졌다"를 늦게 알게 되므로, 재사용 연결 경합이 생길 만한 요청(방금 같은 상대에게서 응답을 받은 직후의 재전송)으로 범위를 한정했다.\
검증 기록: 2026-11-20 사건 기록·수정 diff·서버 시험 기록 대조·추상화(Claude 초안). 경합 기제는 리뷰 지적과 단위 재현이고, "클라이언트가 비멱등 요청을 자동 재전송하지 않는다"는 이 사례 클라이언트(JDK HttpClient)에 대한 기록의 판단이다.
