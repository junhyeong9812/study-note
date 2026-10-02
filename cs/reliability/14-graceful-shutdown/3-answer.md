# reliability/14-graceful-shutdown — 정답

## 정답

### 1. 전파 대기를 빼면

- 앱은 닫혔는데 LB는 아직 이 인스턴스로 요청을 보낸다. 사용자는 502·연결 거절을 본다.
- 쿠버네티스는 두 갈래를 **동시에** 시작한다.
  - 갈래 A: EndpointSlice에서 파드를 terminating·ready=false로 표시 → kube-proxy·인그레스·LB가 각자 주기로 반영.
  - 갈래 B: preStop → SIGTERM → 앱 종료.
  - 문서 표현: "At the same time as the kubelet is starting graceful shutdown of the Pod, the control plane evaluates whether to remove that shutting-down Pod from EndpointSlice objects".
- 서로를 기다리지 않으므로 B가 A보다 빨리 끝나는 틈이 생긴다. `preStop` sleep이나 앱 안의 전파 대기가 그 틈을 메운다.

### 2. 훅 없음 vs 우아한 종료

(실험, JDK 21 컨테이너 2개, 집필 2회 + 점검 2회의 범위)

| | stop 소요 | 종료 코드 | 실패 / 보낸 요청 |
|---|---|---|---|
| 훅 없음(`nohook`) | 0.4~0.6초 | 143 | 55~56 / 69~70 |
| 우아한 종료(`graceful`) | 6.0~6.5초 | 143 | 0 / 69~70 |

- 훅이 없어도 JVM은 SIGTERM을 받으면 끝난다(143 = 128 + 15). 다만 처리 중 요청을 기다리지 않는다.
- 이 실험엔 LB가 없어서, 컨테이너가 사라진 뒤의 요청도 연결 타임아웃으로 실패했다.

### 3. 닫았는데도 새 요청을 받는다

- 받는다. 실험에서 드레이닝 중 **새 요청 38~39건**을 받았다(`드레이닝 중 새로 받은 요청 39`).
- 이유: 리스닝 소켓을 닫으면 **새 연결**만 막힌다. 클라이언트의 keep-alive 연결은 열려 있고, 그 연결로 다음 요청이 온다.
- 기한 3초(`graceful3`): `stop 반환: 처리 중 7`(점검 재실행에서는 8) — 트래픽이 계속 와서 기한에 7~8건이 남았다. 실패는 16/69였다.
- "처리 중 0을 기다린다"는 트래픽이 빠졌을 때만 성립한다.

### 4. `Connection: close`의 경계

- 실험 `gracefulclose`: 종료 전체가 2.5~2.7초 만에 끝났다(전파 대기 1초 포함). 그러나 실패 34~35/69.
- 연결을 끊어 준 클라이언트가 **갈 다른 인스턴스**가 없었다. 새 연결은 닫힌 리스닝 소켓에 거절됐다.
- 조건: LB에서 이 인스턴스가 먼저 빠져 있어야 한다. 그래야 다시 연결한 클라이언트가 다른 인스턴스로 간다. 순서는 "LB 제외(전파 대기) → 연결 끊기"다.

### 5. 매번 유예 시간을 채우고 137

- 의심: SIGTERM이 앱에 닿지 않는다.
  - 셸 형식 CMD로 `sh`가 PID 1로 남았다. Docker 문서: 셸 형식 ENTRYPOINT의 실행 파일은 "will not receive Unix signals". 단, 셸에 따라(bash 등) 단일 명령을 exec로 바꿔 앱이 PID 1이 되기도 하므로 `/proc/1/cmdline`으로 확인한다.
  - 또는 앱이 PID 1인데 SIGTERM 핸들러가 없다(pid_namespaces(7): init은 핸들러를 건 신호만 받는다).
- 실험 `pid1sh`: 서버 로그에 `SIGTERM 수신` 줄이 없었다. `docker stop -t 3`이 3.4~3.6초 걸렸고 종료 코드 137이었다.
- 확인: `cat /proc/1/cmdline`, `docker inspect`의 Entrypoint·Cmd, 종료 코드와 `OOMKilled`(OOM도 137이므로 구분).
- 대처: exec 형식 ENTRYPOINT, 스크립트 마지막을 `exec java ...`, 또는 `tini`·`docker run --init`.

### 6. Spring Boot 기본값과 시간 합

- 3.3: `immediate`. 3.4: `graceful`(ServerProperties 소스 v3.3.0 → v3.4.0).
- 드레이닝 기한 `spring.lifecycle.timeout-per-shutdown-phase` 기본 30초. 쿠버네티스 유예 기본 30초.
- `preStop` 10초가 유예 시간 안에서 먼저 쓰인다. 남은 20초 안에 Spring이 30초 기한을 다 쓰려 하면 유예가 먼저 끝나 SIGKILL이 온다. 버린 건수 보고 없이 죽는다.
- 대처: 유예를 늘리거나(예: 45초) Spring 기한을 줄인다(예: 20초).

### 7. 시간 부등식

```text
 유예 시간 ≥ 전파 대기 + 드레이닝 기한 + 정리 시간 + 여유
```

- 바깥에서 정해진 것부터 정한다.
  - 전파 대기: LB·kube-proxy 반영 시간을 환경에서 잰다.
  - 드레이닝 기한: 가장 긴 정상 요청 시간 기준(원본 ops-patterns/19: 평균으로 잡으면 잘린다).
- 유예 시간을 이 합으로 정한다. 유예 시간이 조직 정책으로 고정돼 있으면 드레이닝 기한을 역산한다.

### 8. 컨슈머·백그라운드 작업

- 현상: 배포 뒤 같은 메시지가 두 번 처리되거나, 오프셋은 넘어갔는데 결과가 없다.
- 원인: 처리 완료와 오프셋 커밋 시점이 종료에 끊겨 어긋났다.
- 종료 순서에 넣을 것: 새 메시지 가져오기 중지 → 처리 중 메시지 완료 → 오프셋 커밋 → 컨슈머 close → 풀 닫기.
- 다시 처리돼도 되도록 멱등 처리를 함께 둔다. 기한 안에 못 끝나는 긴 작업은 체크포인트로 재개 가능하게 만든다(31번).
