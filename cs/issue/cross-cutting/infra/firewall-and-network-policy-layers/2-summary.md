# cs/issue/infra/firewall-and-network-policy-layers — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
요청 하나가 서비스에 닿기까지 통과하는 계층 (각각 독립적으로 허용/거부)

 클라이언트
    │
 [1] 클라우드 보안 목록 (Ingress: src IP · src port · dst port)
    │     실패: Source Port = 443  → 클라이언트 출발지 포트는 임의(ephemeral) → 0 매칭 → 전량 드롭
    ▼
 [2] 호스트 iptables
    │   ├─ INPUT  체인 ← ufw 규칙이 사는 곳 (호스트 프로세스 행)
    │   └─ FORWARD → DOCKER 체인 ← docker publish 가 넣는 0.0.0.0/0 ACCEPT (컨테이너 행)
    │     실패: ufw 화이트리스트를 믿었지만 컨테이너 트래픽은 INPUT을 안 지남 → 전 세계 공개
    ▼
 [3] MAC (SELinux 도메인 정책)
    │     실패: nginx(httpd_t) 의 아웃바운드 connect() → EACCES → 즉시 502
    │           같은 호스트의 셸(unconfined) curl 은 200  ← "나는 되는데?" 착시
    ▼
 [4] 애플리케이션 인증·권한·감사
          실패: 인증/감사 off → 네트워크 도달 = 전권, 사후 호출자 추적 불가

[진단 분별]  (nginx 기준 일반론 — 프록시·설정마다 다름)
   빠른 502  = refused / reset / EACCES (능동 거부)
   느린 504  = timeout / DROP        (무응답)
   0 패킷    = 더 바깥 계층(클라우드 목록)에서 이미 버려짐

[교정]  계층마다 따로 연다/닫는다
   [1] Source Port = All (목적지 포트로 제한)
   [2] publish 를 127.0.0.1: 로 좁히거나 제거 (ufw 가 아니라 docker 쪽에서)
   [3] setsebool -P httpd_can_network_connect 1 · 옮긴 설정 파일은 restorecon
   [4] 인증+TLS+감사+역할(삭제 권한 분리) · 스냅샷 저장소 등록
```

## 핵심 문장
- 방화벽은 한 겹이 아니다 — 클라우드 목록·호스트 패킷 필터·컨테이너 런타임 체인·MAC·앱 인증이 **각자** 판정한다.
- ufw의 일반 `allow` 규칙은 INPUT 체인에 들어가고(route 규칙은 별도), Docker publish는 FORWARD→DOCKER 체인에 허용을 넣는다 → **ufw 화이트리스트는 publish된 컨테이너를 보호하지 않는다.**
- SELinux는 일반 권한과 별개로 **프로세스 도메인 단위**로 네트워크 연결을 막는다 — 셸에서 되는 것이 데몬에서 된다는 보장이 아니다.
- 출발지 포트는 클라이언트가 임의로 고른다 — 서비스 포트로 거를 곳은 **목적지** 포트다.
- 네트워크 계층이 뚫렸을 때 마지막 선은 앱 계층의 인증·권한·감사다(최소 권한). 감사가 없으면 사고 후 "누가"를 영영 모른다.
