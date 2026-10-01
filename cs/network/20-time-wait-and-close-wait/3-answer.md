# network/20-time-wait-and-close-wait — 정답

## 정답

### 1. 어느 쪽에, 무엇을 기다리나

- **TIME-WAIT**: 먼저 닫은 쪽(능동 종료). 상대 FIN에 ACK를 보낸 뒤, 2MSL 동안 **커널이 스스로** 기다린다. 끝나면 커널이 정리한다.
- **CLOSE-WAIT**: 나중에 닫는 쪽(수동 종료). 상대 FIN을 받고 ACK한 뒤, **내 앱이 close()하기를** 기다린다. 앱이 닫기 전에는 끝나지 않는다.

### 2. TIME-WAIT의 두 이유

```text
  (1) 마지막 ACK 유실
  A(TIME-WAIT) --- ACK ---X
               <-- FIN ---  B가 재전송
               --- ACK -->  A가 상태를 기억하므로 다시 ACK 가능
      TIME-WAIT가 없으면: A는 모르는 연결로 보고 RST -> B는 에러로 종료

  (2) 옛 세그먼트의 오염
  옛 연결 (같은 4-튜플)의 지연 세그먼트 X가 망에 떠돎
  새 연결이 곧바로 같은 4-튜플로 열림 -> X가 새 연결의 윈도 안이면 데이터로 받아들여짐
      TIME-WAIT가 2MSL 동안 그 4-튜플을 막아 두면 X는 그 사이 사라짐
```

- 연결 정보가 없는 쪽은 RST 아닌 세그먼트에 RST로 답한다(RFC 9293 §3.5.2).
- 능동 종료 쪽은 2×MSL 머물러야 한다(MUST-13, §3.6.1).

### 3. 시간

- RFC: 2×MSL. MSL은 2분이므로 4분이다(RFC 9293 §3.4.2, §3.6.1).
- 리눅스: 60초 고정(`TCP_TIMEWAIT_LEN (60*HZ)`). sysctl로 바꿀 수 없다.
- `tcp_fin_timeout`은 **TIME-WAIT와 무관**하다. 앱이 놓아 버린(orphan) FIN-WAIT-2 소켓을 얼마나 유지할지다(ip-sysctl). 줄여도 TIME-WAIT는 60초 그대로다.

### 4. 한 목적지당 연결률

```text
  ip_local_port_range 기본 32768 ~ 60999 -> 28,232개
  각 포트가 TIME-WAIT로 60초 묶임
  28,232 / 60 ≈ 470 연결/초
```

- 이쪽이 먼저 닫고, 같은 (목적지 IP, 목적지 포트)로, 출발 IP 하나에서 새 연결을 계속 연다는 조건의 대략값이다.
- 넘으면 `connect()`가 `EADDRNOTAVAIL`("Cannot assign requested address")로 실패한다(connect(2)).

### 5. 서버 쪽 TIME-WAIT 5만 개

- **포트 고갈이 아니다.** 서버 쪽 4-튜플의 로컬 포트는 리스닝 포트(:443 등) 하나이고, 원격 IP·포트가 다양해서 서로 겹치지 않는다. 임시 포트를 쓰지 않는다.
- **fd 고갈도 아니다.** 앱은 이미 close()했고, 커널이 작은 미니 소켓으로만 들고 있다(ss(8) `bucket`).
- 메모리도 작다(Bernat 2014). `tcp_max_tw_buckets`를 넘지 않는지만 보면 된다.

### 6. close()를 안 하면

- 커널은 FIN에 ACK하고 CLOSE-WAIT로 간다. 앱의 `read()`는 0(EOF)을 받는다.
- 앱이 close()하지 않으면 **CLOSE-WAIT에 무기한** 남는다. RFC 상태 기계에서 CLOSE-WAIT를 정상적으로 벗어나는 길은 사용자 CLOSE뿐이다(→ LAST-ACK). 커널에 CLOSE-WAIT 전용 타이머는 없다.
- 예외적으로 `SO_KEEPALIVE`를 켰다면 keepalive probe 실패나 RST로 TCP 상태가 정리될 수 있다(리눅스 `tcp_keepalive_timer`). 그래도 fd는 앱이 close()할 때까지 남는다.
- fd도 열린 채다. 이 연결 하나가 fd 하나를 계속 차지한다.
- 상대 쪽에서는 이 연결이 FIN-WAIT-2로 보이고, 상대 리눅스는 orphan이면 `tcp_fin_timeout` 뒤 정리한다. 내 쪽은 그대로다.

### 7. `Too many open files` 진단

```bash
ss -tanp state close-wait               # 어떤 프로세스, 어떤 상대 주소에서 쌓이나
ls /proc/<PID>/fd | wc -l               # fd 수
grep 'open files' /proc/<PID>/limits    # 한도
ss -tan state close-wait | wc -l        # 시간에 따라 계속 느는지
```

- `EMFILE`은 프로세스 fd 한도(`RLIMIT_NOFILE`)에 닿았다는 뜻이다(accept(2), getrlimit(2)).
- CLOSE-WAIT가 단조 증가하면 누수다. **상대 주소**로 어떤 클라이언트 코드인지 좁힌다.
- 의심할 코드
  - 예외 경로에서 close()를 건너뛰는 코드(try-with-resources·finally 부재)
  - 닫지 않은 HTTP 응답·스트림, 반납하지 않은 풀 연결
  - `read()`의 0/-1을 종료로 처리하지 않고 루프를 도는 코드
- `ulimit -n`을 올리는 것은 시간을 벌 뿐이다.

### 8. TIME-WAIT 줄이기

1. **연결 재사용**(keep-alive·커넥션 풀) — 연결 자체를 덜 만든다. 위험 없음, 근본 해법.
2. **먼저 닫는 쪽 설계** — 포트가 귀한 쪽이 먼저 닫지 않게 한다.
3. **4-튜플 공간 넓히기** — 목적지 IP·포트 여러 개, 출발 IP 여러 개(`IP_BIND_ADDRESS_NO_PORT`), `ip_local_port_range` 확대.
4. **`tcp_tw_reuse`** — 타임스탬프로 안전할 때 TIME-WAIT 소켓을 **나가는 연결**에 재사용한다. 들어오는 연결(서버)에는 효과가 없다. 리눅스 기본값은 **2(loopback만)**다(커널 문서 ip-sysctl. tcp(7) 맨페이지의 "disabled"는 옛 설명).
5. **`SO_LINGER {1, 0}` + close** — RST로 끊어 TIME-WAIT를 없앤다. 미전송 데이터가 버려지고 상대는 에러를 본다. 최후의 수단.
- `tcp_tw_recycle`은 NAT 뒤 클라이언트를 막는 문제로 Linux 4.12에서 제거됐다.

### 9. `Address already in use`

- 원인: 이전 프로세스의 연결들이 그 포트를 로컬 포트로 쓴 채 TIME-WAIT에 남아 있다. 새 프로세스의 리스닝 소켓에 `SO_REUSEADDR`가 없어 bind가 `EADDRINUSE`로 실패한다. 리눅스 TIME-WAIT가 60초라 1분 뒤엔 성공한다.
- 해결: bind **전에** `SO_REUSEADDR`를 켠다. 활성 리스닝 소켓이 없으면 같은 주소에 bind할 수 있다(socket(7)).
- 그래도 실패하면 다른 프로세스가 실제로 LISTEN 중인지 `ss -ltnp`로 본다.

### 10. `allowHalfOpen: true`와 CLOSE-WAIT

- Node의 기본값(`allowHalfOpen: false`)에서는 상대 FIN을 받으면 대기 중인 쓰기를 마친 뒤 **Node가 자동으로 내 FIN을 보낸다**(Node `net` 문서).
- `allowHalfOpen: true`면 자동으로 보내지 않는다. 상대 FIN 뒤에도 이쪽은 쓸 수 있게 열어 두는 것이다.
- 이때 `'end'` 핸들러에서 `socket.end()`(또는 `destroy()`)를 부르지 않으면, 커널 연결은 CLOSE-WAIT에 남고 fd도 열린 채다.
- 요청마다 이 경로를 타면 CLOSE-WAIT가 쌓여 결국 `EMFILE`이 된다.
