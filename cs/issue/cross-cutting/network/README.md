# network — 프로토콜·연결·프록시

HTTP·TCP의 경계와 중간 장치(프록시·터널·컨테이너 네트워크)에서 터지는 패턴이다.\
공통 원리: **송신·중계·수신 각 홉이 같은 규격(길이·status·주소·인코딩·캐시)을 공유한다고 가정하지 말고 홉마다 명시적으로 맞춘다.**\
"라이브러리가 대신 처리해 줬다"고 믿은 것이 실제로는 규격 불일치였던 이슈가 많다.

## 공통 원리

```
  클라이언트 ──▶ 프록시/BFF ──▶ 서버
      │              │             │
      │              │             ├─ 헤더 커밋 순간 status 확정
      │              ├─ 헤더·쿠키·스트림 왕복 누락
      └─ 길이 채널(chunked vs Content-Length)·URI 인코딩 불일치
                     ▼
        0바이트 본문 · 잘못된 status · 끊긴 세션
```

## 패턴 카드

- [api-contract-evolution](api-contract-evolution/) — 광고한 capability·버전·문서 보장은 실제 구현과 일치해야 하고, 계약 변경은 소비자·제공자의 배포 순서와 함께 진화해야 한다 — 상대 구현은 소스·스모크로만 확정한다.
- [bind-address-loopback-vs-lan](bind-address-loopback-vs-lan/) — 바인드 주소(loopback vs LAN/wildcard)와 헬스체크·프로브가 보는 주소·도구가 어긋나면 정상 서비스가 unhealthy·접속 불가로 보인다.
- [chunked-vs-content-length](chunked-vs-content-length/) — chunked 전송과 Content-Length 기대가 어긋나면 본문이 0바이트·절단된다 — 송수신 양쪽의 길이 채널을 맞춰야 한다.
- [container-network-addressing](container-network-addressing/) — 컨테이너 네트워크에서 127.0.0.1은 자기 자신이고 호스트 매핑 포트·docker0·내장 DNS·광고 주소는 네트워크 범위에 따라 다르다 — 목적지 주소를 같은 네트워크 기준으로 정한다.
- [half-open-liveness-watchdog](half-open-liveness-watchdog/) — 출력 전용·장기 스트리밍 연결은 상대가 사라져도 TCP 에러가 오지 않는다 — liveness는 앱이 의미 단위(완성 프레임·하트비트) 도착 시각으로 판정한다.
- [http-cache-policy](http-cache-policy/) — immutable·장기 캐시는 콘텐츠 주소화된 URL에만 쓰고, 상태 엔드포인트·버전 없는 정적 자원에는 캐시 정책을 명시해야 배포와 클라이언트가 어긋나지 않는다.
- [http-streaming-status-locked](http-streaming-status-locked/) — 응답 헤더가 커밋되는 순간 status는 확정되므로, 최종 상태를 보려면 커밋 이후가 아니라 가장 바깥 계층에서 확정 시점을 기준으로 관측해야 한다.
- [payload-transfer-cost](payload-transfer-cost/) — 전송 비용은 크기×빈도다 — 바뀌지 않는 대형 본문을 매 틱 재전송하거나 필터 없이 통째로 반환하면 메모리·지연이 누적되므로 메타만 싣고 본문은 요청 시 회수한다.
- [proxy-passthrough](proxy-passthrough/) — 프록시·BFF 계층마다 헤더(XFF·쿠키·prefix·상관 ID)·status·스트림을 명시적으로 왕복시켜야 하며, 전달받은 헤더는 신뢰 홉 기준으로만 믿는다.
- [reverse-tunnel-nat-traversal](reverse-tunnel-nat-traversal/) — NAT·서브넷 단절로 inbound가 불가하면 연결 방향을 역전(outbound 유지형 역터널·브로커)한다.
- [uri-encoding-rules](uri-encoding-rules/) — URI는 ASCII와 예약문자 규칙을 따른다 — 비ASCII·경로 속 슬래시·표준 Base64·이중 인코딩은 도구·컨테이너마다 다르게 처리되므로 경계에서 올바르게 인코딩한다.

> 이 폴더의 메타 태그: `silent-failure`(3) · `resource-bounding`(1) · `least-privilege`(1) · `fail-closed`(1) · `contract-drift`(1) · `encoding`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
