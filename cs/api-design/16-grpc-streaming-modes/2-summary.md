# api-design/16-grpc-streaming-modes — 단항·서버·클라이언트·양방향 스트리밍, 흐름 제어·데드라인·취소 — 정리 (힌트)

## 해결하는 문제

단항 RPC는 요청 하나에 응답 하나다. 그런데 이런 일은 한 번의 요청·응답에 담기 어렵다.

```text
  주문 10만 건 내보내기        응답 하나에 담으면 메시지 한도(grpc-java 기본 4MiB)·메모리·첫 바이트 지연
  시세·배송 위치 실시간 구독   폴링하면 지연과 빈 요청
  센서 수천 개 값 올리기       요청마다 왕복 지연
  채팅·협업 편집              양쪽이 아무 때나 보낸다
```

- 스트리밍 RPC는 하나의 호출 안에서 메시지를 **여러 개** 주고받는다.
- 대신 단항에는 없던 질문이 생긴다.
  - 받는 쪽이 느리면 보내는 쪽은 어떻게 하나 — *흐름 제어·역압*.
  - 중간에 끊기면 어디까지 받았나 — *부분 결과와 재개*.
  - 데드라인은 메시지마다인가, 호출 전체인가.
  - 몇 시간 사는 스트림은 로드 밸런서 입장에서 무엇인가.

쉬운 예: 수도꼭지와 양동이다.
- 물(메시지)을 한 번에 다 받지 않고 흘려 받는다.
- 양동이가 차면 꼭지를 잠가야 한다(흐름 제어). 잠그지 않으면 바닥에 넘친다(메모리 누적).
- 물이 중간에 끊겼는데 "다 받았다"고 착각하면 안 된다(조용한 절단).

똑같은 구조다.\
실무 예: 정산 데이터를 서버 스트리밍으로 내려받는 배치가 중간 `UNAVAILABLE`을 삼키고 "완료"로 기록한다. 느린 모바일 클라이언트에게 무작정 `onNext`를 부르던 서버가 메모리 부족으로 죽는다.

## 동작·원리

### 1. 네 가지 모드

```text
  단항              client ──req──▶ server ──resp──▶                         rpc A(Req) returns (Resp);
  서버 스트리밍      client ──req──▶ server ──r1──r2──r3──…──status──▶         rpc B(Req) returns (stream Resp);
  클라이언트 스트리밍 client ──q1──q2──…──half-close──▶ server ──resp──▶      rpc C(stream Req) returns (Resp);
  양방향            client ══q1═q2═…═▶ server                                rpc D(stream Req) returns (stream Resp);
                    client ◀═r1═r2═…═ server   (두 방향이 독립)
```

- gRPC Core concepts
  - 서버·클라이언트 스트리밍 모두 "gRPC는 한 RPC 호출 안에서 메시지 순서를 보장한다".
  - 양방향은 "두 스트림이 독립적으로 동작하므로 클라이언트와 서버는 원하는 순서대로 읽고 쓸 수 있다".
- 하나의 스트리밍 호출 = HTTP/2 스트림 하나다. 메시지는 그 스트림의 DATA 프레임에 길이 접두로 실리고, 끝에 트레일러로 상태가 온다([15](../15-rpc-and-grpc/2-summary.md)).
  - *half-close*: 한쪽이 "더 보낼 것 없음"을 알린 상태. 반대쪽은 계속 보낼 수 있다.

(실험, grpc-java 1.72.0, 클라이언트 스트리밍 1000개 + 양방향 3개)

```text
  2363ms [client] Upload 응답 1개: received 1000
  2380ms [client] Chat 응답: [echo:a, echo:b, echo:c]
```

### 2. 스트림의 끝은 상태로 판정한다 — 조용한 절단

```text
  서버:  r1 r2 r3 r4 r5 ── onError(UNAVAILABLE "upstream shard down")
  클라:  받은 메시지 5개 + 끝 상태 = UNAVAILABLE
         "메시지가 더 안 온다" ≠ "다 받았다"  ← 끝 상태가 OK(onCompleted)일 때만 완료
```

- 서버 스트리밍은 메시지를 다 보낸 뒤 상태를 보낸다. 중간에 실패해도 그 전 메시지는 이미 클라이언트에 도착해 있다.
- 클라이언트가 예외를 삼키거나, 반복자가 멈춘 것을 "끝"으로 보면 **부분 결과를 전체로 오인**한다.

### 실험: 5개 뒤 `UNAVAILABLE`

```java
// 나쁜 예: 예외를 삼키고 끝으로 취급
try { blocking.withDeadlineAfter(5, SECONDS).ticks(req).forEachRemaining(r -> seen.add(r.getSeq())); }
catch (StatusRuntimeException ignored) { }
log("처리 완료로 기록, 받은 seq=" + seen);

// 좋은 예: onCompleted와 onError를 구분, 마지막 seq를 재개 지점으로
async.ticks(req, new StreamObserver<>() {
    public void onNext(Resp r) { seen2.add(r.getSeq()); }
    public void onError(Throwable t) { log("onError " + Status.fromThrowable(t) + " 마지막 seq=" + last + " → 재개 지점으로 기록"); }
    public void onCompleted() { log("onCompleted, 받은 수 " + seen2.size()); }
});
```

(실험, grpc-java 1.72.0 · JDK 21.0.11, Netty 루프백, 2026-10-04)

```text
  1888ms [server] Ticks 5개 보낸 뒤 onError(UNAVAILABLE)
  1906ms [client] 나쁜 예: 처리 완료로 기록, 받은 seq=[1, 2, 3, 4, 5] (요청은 10개)
  2167ms [server] Ticks 5개 보낸 뒤 onError(UNAVAILABLE)
  2171ms [client] 좋은 예: onError Status{code=UNAVAILABLE, description=upstream shard down, cause=null} 마지막 seq=5 → 재개 지점으로 기록
```

### 3. 데드라인은 호출 전체에 걸린다

```text
  withDeadlineAfter(1s)
  t=0 ─ r1 ─ r2 ─ … ─ r10 ─┤ 1s  DEADLINE_EXCEEDED   (서버는 100ms마다 1개, 30개 예정)
                           └ 이후 서버의 onNext는 버려지거나 예외
```

- 데드라인은 메시지 하나가 아니라 **호출(스트림) 전체**의 시한이다. 몇 시간 사는 구독 스트림에 짧은 데드라인을 걸면 그 시간마다 끊긴다.
- 스트림이 끝나도(데드라인·클라이언트 취소) 서버 코드가 알아서 멈추지는 않는다. gRPC Deadlines 가이드: 서버가 시작한 작업을 멈추는 것은 서버 애플리케이션 책임이다.

### 실험: 데드라인 1초, 서버가 취소를 확인할 때와 안 할 때

```java
// mode=check: 취소 핸들러를 달고, 보낼 때마다 isCancelled 확인
out.setOnCancelHandler(() -> log("onCancelHandler: 클라이언트가 떠났다 → 생산 중단"));
if (out.isCancelled()) { stopProducing(); return; }
// mode=nocheck: 그냥 onNext
out.onNext(Resp.newBuilder().setSeq(n).build());
```

(같은 환경)

```text
  1644ms [client] == 1. 서버 스트리밍 + 데드라인 1s, 서버는 100ms마다 1개(총 30개), mode=nocheck
  1658ms [server] exp.Exp/Ticks grpc-timeout=999330u
  2669ms [client] 받은 수 10 뒤 DEADLINE_EXCEEDED
  2760ms [server] Ticks seq=12 onNext 예외: io.grpc.StatusRuntimeException: CANCELLED: call already cancelled. Use ServerCallStreamObserver.setOnCancelHandler() to disable this exception
  4671ms [server] Ticks 생산 루프 끝(seq 30까지 만듦). 그중 취소 뒤 버려진 onNext 19회
  5170ms [client] == 1b. 같은 조건, mode=check (서버가 취소를 확인)
  5178ms [server] exp.Exp/Ticks grpc-timeout=999416u
  6174ms [client] 받은 수 10 뒤 DEADLINE_EXCEEDED
  6175ms [server] Ticks onCancelHandler: 클라이언트가 떠났다 → 생산 중단
  6186ms [server] Ticks isCancelled=true, seq=11 에서 중단
```

관찰
- 두 경우 모두 클라이언트는 10개를 받고 `DEADLINE_EXCEEDED`.
- 확인하지 않는 서버는 클라이언트가 떠난 뒤에도 30번까지 만들었다. 그중 19번의 `onNext`가 버려졌다(사실 점검 재실행에서는 20번 — 서버 타이머와 취소 도착 순서에 따라 실행마다 1개쯤 다르다). 실제 서비스라면 DB 조회·외부 호출을 그만큼 헛되이 한 것이다.
- grpc-java 1.72.0은 취소된 호출에 `onNext`하면 `CANCELLED: call already cancelled` 예외를 던졌다. 문구가 권하듯 `setOnCancelHandler()`를 달면 이 예외 대신 핸들러로 알린다.
- 확인하는 서버는 취소 직후(클라이언트가 실패를 본 뒤 0~12ms — 집필 실행과 재실행 범위) 생산을 멈췄다.

### 4. 흐름 제어 — 받는 쪽이 정하는 "더 보내도 된다"

```text
  HTTP/2 (RFC 9113)                         grpc-java 위의 애플리케이션
  수신자가 창(window) 크기를 광고             call.isReady()  = 지금 보내도 버퍼가 과하지 않나
  DATA 프레임만 창을 소비                    setOnReadyHandler(…) = 다시 보낼 수 있을 때 불림
  WINDOW_UPDATE로 창을 다시 연다              request(n)          = 클라이언트가 n개 더 받겠다
  초기 창 65,535 옥텟(스트림·연결 각각)        grpc-java Netty 기본 창 1,048,576 (DEFAULT_FLOW_CONTROL_WINDOW, 시작값)

  보내는 쪽 앱 ─onNext─▶ [grpc 버퍼] ─창이 열린 만큼─▶ 선 ─▶ [수신 버퍼] ─request(n)만큼─▶ 받는 쪽 앱
                       ▲ 여기가 무한히 쌓일 수 있다
```

- RFC 9113: 흐름 제어는 연결의 한 홉 사이에서 동작하고, 수신자가 스트림별·연결별 창을 정한다. DATA 프레임만 창을 소비한다. 새 스트림·연결의 초기 창은 65,535 옥텟이다.
- gRPC Flow Control 가이드
  - 흐름 제어는 스트리밍 RPC에만 의미가 있다.
  - 쓰기 호출이 돌아오기 전에 멈출 수도 있고, 쓴 데이터는 곧장 선으로 가지 않고 프레임워크 버퍼에 들어간다.
  - 양쪽이 동기 읽기나 수동 흐름 제어를 쓰면서 둘 다 읽지 않고 많이 쓰면 교착이 생길 수 있다.
- grpc-java의 `onNext`는 막히지 않는다. 창이 닫혀도 메시지를 버퍼에 쌓고 돌아온다. **역압을 지키는 것은 `isReady()`를 보는 애플리케이션 몫이다.**
  - *역압(backpressure)*: 느린 소비자가 생산자의 속도를 늦추게 하는 신호.

### 실험: 느린 소비자에게 20,000개×10KB를 보낸다

```java
// 클라이언트: 수동 흐름 제어 — 10ms마다 1개만 더 요청, 4초 뒤 취소
public void beforeStart(ClientCallStreamObserver<Req> call) { call.disableAutoRequestWithInitial(1); }
public void onNext(Resp r) { ses.schedule(() -> call.request(1), 10, MILLISECONDS); }

// 서버 blind: 그냥 다 보낸다
for (int i = 1; i <= total; i++) out.onNext(msg(i));

// 서버 ready: 보낼 수 있을 때만
out.setOnReadyHandler(() -> {
    while (out.isReady() && sent.get() < total) out.onNext(msg(sent.incrementAndGet()));
    if (sent.get() >= total) out.onCompleted();
});
```

(실험, grpc-java 1.72.0, JDK 21.0.11, 서버·클라이언트 같은 JVM(`-Xmx512m`), 컨테이너 `--cpus=2 --memory=1500m`, 3회 실행, 2026-10-04 — RSS는 프로세스 전체)

```text
  3476ms [server] blind: onNext 20000개 호출 완료 1549ms, 그중 isReady=false였던 호출 19996, RSS 83MB → 292MB
  5323ms [client] 4초 동안 소비한 수 272 → 클라이언트가 취소

  5326ms [client] 4초 동안 소비한 수 300 → 클라이언트가 취소
  5351ms [server] ready: 취소됨. 그때까지 보낸 수 373, 멈춤(isReady=false) 121회, 최대 RSS 90MB (시작 83MB)
```

| | blind (집필 3회 + 재실행 2회 범위) | ready (집필 3회 + 재실행 2회 범위) |
|---|---|---|
| 서버가 `onNext`를 끝낸 시간 | 1366~1624ms에 20,000개 전부 | 끝나지 않음(소비 속도에 맞춰 감) |
| `isReady=false`였는데 보낸 호출 | 19,996 | 0 (멈춤 113~134회) |
| 클라이언트가 4초간 소비 | 271~284개 | 281~307개 |
| 프로세스 RSS | 81~83MB → 292~296MB | 최대 87~90MB |
| 취소 시점까지 보낸 수 | 20,000 | 373(5회 모두) |

관찰
- blind 서버는 소비자가 270개쯤 받는 동안 2만 개(약 200MB)를 버퍼에 쌓았다. RSS가 약 210MB 늘었다. 메시지가 더 크거나 클라이언트가 많으면 이것이 OOM이다.
- ready 서버는 소비량보다 66~92개(약 0.7~0.9MB) 앞서서만 보냈다. 이 차이는 흐름 제어 창(시작값 1MiB)과 버퍼 문턱으로 정해진 것으로 보인다(해석 — 정확한 분해는 확인하지 않았다). grpc-java 1.72.0 Netty 전송은 BDP 기반 창 자동 조정(`autoFlowControl`)이 기본으로 켜져 있어 창이 1MiB에서 커질 수도 있다(grpc-java v1.72.0 `NettyChannelBuilder`·`NettyServerBuilder` 소스).
- 클라이언트가 취소한 뒤 `Stream closed before write could take place` 경고가 났다 — 쓰려던 메시지를 보낼 스트림이 사라졌다. 집필 실행에서는 blind 쪽에서만 봤지만, 사실 점검 재실행에서는 ready 쪽에서도 1회씩 났다. 경고가 났다는 것만으로 blind를 가려낼 수는 없고, 버퍼 누적은 RSS·`isReady=false`인데 보낸 수로 본다.

### 5. 오래 사는 스트림과 로드 밸런싱

```text
  t0: 서버 A·B, 스트림 10개를 고르게 연결           A: ■■■■■  B: ■■■■■
  t1: 서버 C 추가                                  A: ■■■■■  B: ■■■■■  C: (비어 있음)
  t2: A가 배포로 내려감 → A의 스트림 5개가 한꺼번에 재연결 → B·C로 몰림
```

- 스트림은 시작할 때 고른 연결(서버)에 끝날 때까지 붙어 있다. 요청 단위 LB(15번 `round_robin`)도 **새 스트림을 어디로 보낼지**만 정한다.
- 그래서 스트림이 오래 살수록 부하 재조정이 늦고, 서버를 내릴 때 재연결이 한꺼번에 몰린다.
- 대처 도구
  - 서버 `MAX_CONNECTION_AGE`(gRPC Keepalive 가이드, 기본 무한): 연결 수명을 정해 GOAWAY로 주기적으로 갈게 한다. GOAWAY는 보낸 쪽이 처리했거나 앞으로 처리할 수도 있는 스트림 중 가장 큰 ID(last stream ID)를 알린다 — 그보다 큰 번호의 스트림은 처리되지 않았으므로 다른 연결로 다시 보내도 안전하다(RFC 9113 §6.8).
  - 스트림을 "끊겨도 이어 받을 수 있게" 설계한다 — 마지막 seq·재개 토큰.
  - 재연결에 지터를 둔다([reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **크레딧(창) 카운터** — HTTP/2 흐름 제어. 보낼 때 창을 줄이고, `WINDOW_UPDATE`를 받으면 늘린다. 0이면 DATA를 보내지 않는다.
- **유계 버퍼 + 준비 신호** — `isReady()`/`onReady`는 "버퍼가 문턱 아래인가"를 묻는 것이다. 생산자를 소비 속도에 묶는다([reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).
- **요청 크레딧(pull)** — 클라이언트 `request(n)`. Reactive Streams의 `request(n)`과 같은 끌어오기 모델이다.
- **재개 커서** — 마지막으로 처리한 seq(또는 서버가 준 불투명 토큰)를 저장해 다시 연결할 때 그 다음부터 받는다. 페이지네이션의 커서와 같은 생각이다([06-pagination](../06-pagination/2-summary.md)).
- **취소 트리** — 호출 취소가 서버 `Context`·하류 호출로 퍼진다([reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 모드 고르기

| 상황 | 모드 | 주의 |
|---|---|---|
| 큰 결과를 나눠 받기(내보내기) | 서버 스트리밍 | 재개 지점, 끝 상태 확인 |
| 실시간 구독(시세·위치) | 서버 스트리밍(장수) | 데드라인 대신 재연결·keepalive, LB 편중 |
| 대량 업로드·측정값 묶어 보내기 | 클라이언트 스트리밍 | 서버가 받는 속도, 중간 실패 시 어디까지 반영됐나 |
| 대화형(채팅·협업) | 양방향 | 양쪽 흐름 제어, 교착(둘 다 쓰기만 하기) |
| 그 밖 | 단항 | 스트리밍은 LB·재시도·디버깅이 어렵다 — 필요할 때만 |

- 단항 + 페이지네이션으로 충분하면 그쪽이 운영하기 쉽다. 단항은 호출마다 LB가 다시 고르고, 재시도도 호출 단위라 단순하다.

### 2. 서버 스트리밍 — 역압과 취소를 지키는 모양 (Java, grpc-java 1.x)

```java
@Override public void export(ExportRequest req, StreamObserver<Row> raw) {
    var out = (ServerCallStreamObserver<Row>) raw;
    Iterator<Row> rows = repo.streamRows(req.getAfterSeq());     // 재개 지점부터
    out.setOnCancelHandler(() -> repo.close());                  // 취소되면 커서·쿼리 정리
    out.setOnReadyHandler(() -> {
        while (out.isReady() && rows.hasNext()) out.onNext(rows.next());
        if (!rows.hasNext()) out.onCompleted();
    });
}
```

- `setOnReadyHandler`는 버퍼가 비워질 때마다 다시 불린다. 핸들러 안에서 오래 막히는 작업을 하지 않는다.
- 오류는 `onError(Status.UNAVAILABLE.withDescription(...))`처럼 의미 있는 코드로 끝낸다.

### 3. 클라이언트 — 끝 상태 확인과 재개

```java
long last = checkpoint.load();                                    // 마지막으로 처리한 seq
stub.withDeadlineAfter(10, TimeUnit.MINUTES)                       // 내보내기 전체의 시한
    .export(ExportRequest.newBuilder().setAfterSeq(last).build(), new StreamObserver<>() {
        public void onNext(Row r) { handle(r); checkpoint.save(r.getSeq()); }
        public void onError(Throwable t) { scheduleResume(Status.fromThrowable(t)); }   // 완료로 기록하지 않는다
        public void onCompleted() { markDone(); }                                       // 여기서만 완료
    });
```

- 실시간 구독처럼 끝이 없는 스트림은 짧은 데드라인 대신, 연결 생존 확인(클라이언트 keepalive — gRPC 가이드상 기본 꺼짐)과 재연결을 쓴다.

### 4. 진단

```bash
# 서버별 활성 스트림 수와 편중 — 지표 이름은 예시
#   grpc_server_started_total - grpc_server_handled_total  by (pod)
# 버퍼 누적 의심: 프로세스 RSS·Netty direct 메모리와 "isReady=false인데 보낸 수"를 함께 본다
# 스레드 덤프에서 onReady 핸들러가 막혀 있지 않은지
jcmd <pid> Thread.print | grep -A5 onReady
```

## 장애 시나리오와 대처

### 1. 장수 스트림 → LB 재조정 불가·특정 서버 편중 (⚠ 커리큘럼)

- 현상: 서버를 늘려도 기존 구독 연결은 옛 서버에 남는다. 한 서버를 배포로 내리면 그 서버의 구독자가 한꺼번에 재연결해 다른 서버가 순간 포화된다.
- 보이는 형태: 서버별 활성 스트림 수 편차, 배포 직후 재연결 급증과 지연 스파이크.
- 원인: 스트림은 시작 때 고른 연결에 끝까지 붙는다. 요청 단위 LB도 새 스트림만 나눈다.
- 대처: 서버 `MAX_CONNECTION_AGE`로 연결을 주기적으로 갈기, 재연결 지터, 재개 토큰으로 끊겨도 손실 없게. 서버 쪽 스트림 수 상한.

### 2. 스트림 중간 에러 처리 누락 → 조용한 절단 (⚠ 커리큘럼)

- 현상: 내보내기 배치가 "완료"인데 행 수가 원본보다 적다.
- 보이는 형태: 클라이언트 로그에 오류 없음(삼켰다). 서버 로그에는 `UNAVAILABLE` 종료.
- 원인: 끝 상태를 확인하지 않고 "메시지가 더 안 온다"를 완료로 봤다(실험: 10개 중 5개를 받고 "처리 완료").
- 대처: `onCompleted`(OK)에서만 완료로 기록한다. 서버가 끝에 총 건수를 주면 대조한다. 마지막 seq부터 재개한다.

### 3. 백프레셔 무시 → 메모리 누적 (⚠ 커리큘럼)

- 현상: 느린 클라이언트 몇이 붙으면 서버 메모리가 계속 오르다 OOM으로 죽는다.
- 보이는 형태: RSS·direct 메모리 상승, 컨테이너 OOMKilled, 클라이언트 취소 뒤 `Stream closed before write could take place` 경고.
- 원인: `isReady()`를 보지 않고 `onNext`를 계속 불렀다. grpc-java `onNext`는 막히지 않고 버퍼에 쌓는다(실험: 20,000개를 1.5초에 쌓고 RSS 83MB → 292MB).
- 대처: `setOnReadyHandler` + `isReady()` 루프(실험: 최대 RSS 90MB, 취소 때까지 373개만 보냄 — 소비량보다 66~92개 앞섬). 클라이언트는 `request(n)`으로 받을 만큼만.

### 4. 클라이언트는 떠났는데 서버는 계속 만든다

- 현상: 데드라인 초과·사용자 이탈 뒤에도 서버 CPU·DB 부하가 그대로다.
- 보이는 형태: 서버 로그의 `CANCELLED: call already cancelled` 예외 반복(grpc-java).
- 원인: 서버가 취소를 확인하지 않았다(실험: 19~20번 헛된 생산).
- 대처: `setOnCancelHandler`로 자원 정리, 생산 루프에서 `isCancelled()` 확인(실험: 0~12ms 안에 중단).

### 5. 구독 스트림이 정해진 시간마다 끊긴다

- 현상: 실시간 시세 구독이 정확히 30초(예시)마다 끊기고 다시 붙는다.
- 원인: 단항 호출용 데드라인 기본값(예: 공통 스텁 설정)이 스트림에도 걸렸다. 데드라인은 호출 전체에 적용된다(실험: 1초에 10개 받고 끊김).
- 대처: 장수 스트림은 데드라인을 따로 정하고, 생존 확인은 keepalive·애플리케이션 하트비트로 한다. 끊김 자체는 재개 토큰으로 견디게 한다.

## 핵심 문장

- 스트리밍은 한 호출 안에서 메시지를 여러 개 주고받는다. 순서는 한 호출 안에서만 보장된다.
- 스트림의 완료는 "메시지가 멈췄다"가 아니라 "끝 상태가 OK다"로 판정한다. 실험에서 예외를 삼킨 클라이언트는 10개 중 5개로 완료를 기록했다.
- 데드라인은 스트림 전체의 시한이고, 서버는 취소를 스스로 확인해야 멈춘다. 확인하지 않은 서버는 클라이언트가 떠난 뒤 19~20번을 헛되이 만들었다.
- grpc-java `onNext`는 막히지 않는다. `isReady()`를 무시한 서버는 2만 개를 버퍼에 쌓았고, 지킨 서버는 소비량보다 수백 KB만 앞섰다.
- 오래 사는 스트림은 시작 때 고른 서버에 붙어 LB 재조정을 받지 못한다. 연결 수명 제한·재연결 지터·재개 토큰으로 대비한다.

## 관련 주제·근거

- 선행: [15-rpc-and-grpc](../15-rpc-and-grpc/2-summary.md), [network/36-http2-multiplexing](../../network/36-http2-multiplexing/2-summary.md)(HTTP/2 스트림·흐름 제어·GOAWAY)
- 후속·연결: [reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md), [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md), [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md), [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md)(장수 연결의 다른 형태), [18-api-style-selection](../18-api-style-selection/2-summary.md), [20-messaging-protocols](../20-messaging-protocols/2-summary.md)
- 근거
  - gRPC Core concepts — https://grpc.io/docs/what-is-grpc/core-concepts/ (네 가지 모드, 순서 보장, 취소)
  - gRPC Flow Control — https://grpc.io/docs/guides/flow-control/
  - gRPC Deadlines — https://grpc.io/docs/guides/deadlines/
  - gRPC Keepalive — https://grpc.io/docs/guides/keepalive/ (`MAX_CONNECTION_AGE`, 클라이언트 keepalive 기본 꺼짐)
  - RFC 9113 HTTP/2 §5.2 흐름 제어, §6.9 WINDOW_UPDATE(초기 창 65,535), §6.8 GOAWAY — https://www.rfc-editor.org/rfc/rfc9113
  - grpc-java 1.72.0 jar 상수(`javap -constants`): `NettyChannelBuilder/NettyServerBuilder.DEFAULT_FLOW_CONTROL_WINDOW = 1048576`
  - grpc-java v1.72.0 `NettyChannelBuilder.java`(`DEFAULT_AUTO_FLOW_CONTROL` — 환경 변수 `GRPC_EXPERIMENTAL_AUTOFLOWCONTROL`가 없으면 true)·`NettyServerBuilder.java`(`autoFlowControl = true`) — https://github.com/grpc/grpc-java/tree/v1.72.0/netty/src/main/java/io/grpc/netty
- 실험 목록
  - 클라이언트 스트리밍·양방향 기본 동작, 서버 스트리밍 + 데드라인 1초(취소 확인 vs 미확인), 중간 `UNAVAILABLE` 처리(삼킴 vs 구분), 느린 소비자 + `isReady` 무시 vs 준수(3회) — grpc-java 1.72.0 · protobuf-java 3.25.5, maven:3.9-eclipse-temurin-21(JDK 21.0.11), `--cpus=2 --memory=1500m --network none`, Netty 루프백
