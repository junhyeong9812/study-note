# issue/cross-cutting/infra/load-balancer-defaults-in-backend-switch — 정리 (힌트)

## 전체 흐름

```text
클라이언트 ──keepalive──▶ [nginx 작업자] ──▶ upstream { 옛 앱 · 새 앱 }
                              │
  ① 기술자 한도  요청 1개 = 클라이언트 fd 1 + upstream fd 1
                 worker_connections 8192  >  컨테이너 soft nofile 1024
                 새 앱이 느려져 연결이 쌓임 → accept4()/socket() 실패 (24: No file descriptors available)
                 → 앱에 닿지도 못하고 500        교정: worker_rlimit_nofile 65536 (hard 한도 안)

  ② 수동 장애 판정  server app:port;   ⇒ 기본 max_fails=1 · fail_timeout=10s
                 upstream 구성원 1대 구간에서 시한 초과 1회
                 → 그 서버 10초 제외 → 남은 서버 없음 → 10초 넘게 100% 502
                 교정: server app:port max_fails=0;  생존은 오케스트레이터가(health UP 확인 뒤 넣기)

  ③ reload       include 파일 다시 쓰기 → nginx -t → reload
                 새 작업자 시작 · 옛 작업자는 진행 중 요청을 끝내고 keepalive 연결을 닫음
                 그 연결에 막 실린 요청 → 응답 없이 연결 오류(코드 0)
                 빼기 1회 약 420~450건 · 넣기 약 17~25건
                 대처: 고치지 않고 따로 센다 — 창 [사건 시작, reload 효력 + 1초], 보낸 시각 기준
                       → 다운타임·실패 수에서 빼고 결과 표에 별도 열
```

## 핵심 문장

- 로드밸런서는 측정·전환 경로의 일부다 — 그 기본값이 만든 오류는 앱의 오류처럼 보인다.
- 프록시 요청 하나는 기술자 두 개를 쓴다 — `worker_connections`는 프로세스 기술자 한도 안에서만 뜻이 있다(`worker_rlimit_nofile`).
- nginx의 수동 장애 판정은 기본으로 켜져 있다(실패 1회 · 10초) — 구성원이 하나뿐인 구간에서는 시한 1회가 전면 502가 된다.
- 판정을 끄면 생존 책임은 구성원을 관리하는 쪽(health 확인 뒤 넣기·빼기)으로 옮겨야 한다.
- reload는 진행 중 요청은 지키지만 재사용 중인 keepalive 연결 위의 요청까지 지키지는 않는다 — 고칠 수 없으면 창을 정해 따로 센다.
- 따로 세는 창은 **보낸 시각** 기준이어야 한다 — 창 안에서 보내 시한까지 기다린 요청도 같은 원인이다.
