# network/46-load-balancers-and-proxies — 질문

## 질문

1. (왜) L4 LB와 L7 LB는 각각 무엇을 단위로 백엔드를 고르나? 클라이언트가 keep-alive 연결 하나로 요청 100건을 보낼 때, 백엔드 3대에 어떻게 퍼지는지 둘을 비교하라.
2. (예측) nginx 1.27 뒤 백엔드 3대 중 be1만 300ms 느려졌다. 동시 12개 작업자가 20ms짜리 요청 600건을 보낸다. 라운드로빈과 `least_conn`에서 be1이 받는 몫과 전체 걸린 시간을 예측하라. "least_conn이 가장 무난한 기본값"이라는 말은 맞나?
3. (예측) nginx 오픈소스 기본 `upstream`(설정 없이 서버 3대)에서 be2 프로세스가 죽었다. 사용자는 502를 보나? `proxy_next_upstream off`일 때, 그리고 `max_fails=0`까지 줬을 때는 어떻게 달라지나? 액세스 로그의 `$upstream_addr`에 무엇이 찍히나?
4. (경계) 백엔드 100대에서 1대가 빠질 때 mod-N, 해시 링, Maglev(M=65537)는 각각 키의 몇 %를 옮기나? Maglev가 링보다 더 옮기는데도 L4 LB에 쓰이는 이유는 무엇인가? M은 왜 소수인가?
5. (장애 진단) 공유 DB가 6초 느려졌을 뿐인데 서비스 전체가 503을 냈다. DB를 쓰지 않는 API도 실패했다. 원인, 확인 방법, 대처를 말하라. LB가 "전부 비정상"일 때 AWS ALB·Envoy·nginx 오픈소스는 각각 어떻게 하나?
6. (예측) 클라이언트(172.28.0.2)가 `X-Forwarded-For: 203.0.113.9`를 넣어 보낸다. 프록시 두 단(127.0.0.1)을 거쳐 안쪽 nginx의 realip가 동작한다. `set_real_ip_from 127.0.0.1` + `real_ip_recursive on` / 같은 설정 + `off` / `set_real_ip_from 0.0.0.0/0` + `on`에서 `$remote_addr`는 각각 무엇이 되나?
7. (경계) nginx `ip_hash`와 `hash $remote_addr consistent`에 (a) 한 /24 대역 안의 서로 다른 주소 250개에서 온 요청 300건, (b) 요청의 60%가 NAT 주소 하나에서 오는 경우를 넣으면 분포는 어떻게 되나?
8. (장애 진단) 배포 때마다 몇 초씩 502가 튄다. nginx 에러 로그에 `upstream prematurely closed connection`이 보인다. 원인과 대처는? 같은 순간 GET은 성공했는데 응답이 느렸고 POST는 502였다. 왜인가?
9. (연결) 헬스체크 3종(liveness·readiness·startup)에 각각 무엇을 넣고 무엇을 빼야 하나? Kubernetes 문서와 Spring Boot Actuator 문서의 권고가 어디서 갈리는지 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
