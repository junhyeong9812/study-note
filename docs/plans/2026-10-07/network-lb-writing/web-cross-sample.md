# 웹 교차 표본 — network/46-load-balancers-and-proxies (V5)

- 일시: 2026-10-07
- 방법: 노트 2-summary.md에서 1차 출처가 붙은 주장 중 사실 점검 packet이 대조하지 않은 것(이미 대조: Maglev 생성 시간, nginx sticky 1.29.6, ALB fail open)을 골라, 출처 URL을 curl(기본 헤더, 개인 식별 정보 없음)로 받아 HTML→텍스트 변환 후 원문 문장과 대조. 원문 사본: `scratchpad/net46/final/src/`.
- 줄 번호는 판정 단계 수정 반영 후의 2-summary.md 기준.
- 결과: 18건 — 일치 18 · 불일치 0 · 확인 불가 0. (별도로 codex 지적 판정에서 AWS ELB 동작·NLB 리스너·NLB 대상 그룹 속성·ALB 스티키·Maglev §3.3/§3.4 원문을 열어 5건을 반영 — 판정 표 참고.)

| # | 노트(:줄) | 주장 | 출처 | 원문 인용 | 판정 |
|---|---|---|---|---|---|
| 1 | 2-summary:501 | nginx `ip_hash`는 IPv4 앞 세 옥텟 또는 IPv6 전체를 키로 쓴다 | nginx upstream 모듈 | "The first three octets of the client IPv4 address, or the entire IPv6 address, are used as a hashing key." | 일치 |
| 2 | 2-summary:501 | 서버를 잠시 빼야 하면 해시 유지를 위해 `down`으로 표시하라 | nginx upstream 모듈 | "If one of the servers needs to be temporarily removed, it should be marked with the down parameter in order to preserve the current hashing of client IP addresses." | 일치 |
| 3 | 2-summary:193 | `hash … consistent`는 ketama, 빼면 대부분의 키가 다른 서버로 갈 수 있다 | nginx upstream 모듈 | "may result in remapping most of the keys to different servers … If the consistent parameter is specified, the ketama consistent hashing method will be used instead." | 일치 |
| 4 | 2-summary:296 | nginx 오픈소스 `max_fails` 기본 1, `fail_timeout` 기본 10초 | nginx upstream 모듈 | "By default, the number of unsuccessful attempts is set to 1." / "By default, the parameter is set to 10 seconds." | 일치 |
| 5 | 2-summary:428 | POST·LOCK·PATCH는 상류에 보낸 뒤 다음 서버로 넘기지 않음, `non_idempotent`로 허용, 1.9.13부터 | nginx proxy 모듈 | "requests with a non-idempotent method (POST, LOCK, PATCH) are not passed to the next server if a request has been sent to an upstream server (1.9.13); enabling this option explicitly allows retrying such requests" | 일치 |
| 6 | 2-summary:598 | `proxy_next_upstream_tries` 기본 0 = 무제한 | nginx proxy 모듈 | "Default: proxy_next_upstream_tries 0; … The 0 value turns off this limitation." | 일치 |
| 7 | 2-summary:452 | `real_ip_recursive off`(기본)면 헤더 마지막 주소, `on`이면 신뢰 주소가 아닌 마지막 주소 | nginx realip 모듈 | "Default: real_ip_recursive off; … If recursive search is disabled, … replaced by the last address sent in the request header field … If recursive search is enabled, … replaced by the last non-trusted address" | 일치 |
| 8 | 2-summary:127 | HAProxy는 `leastconn`을 LDAP·SQL 같은 긴 세션에 권하고 HTTP 같은 짧은 세션엔 잘 맞지 않는다고 적는다 | HAProxy 3.0 설정 문서 `balance` | "Use of this algorithm is recommended where very long sessions are expected, such as LDAP, SQL, TSE, etc... but is not very well suited for protocols using short sessions such as HTTP." | 일치 |
| 9 | 2-summary:295 | HAProxy `inter` 2초, `fall` 3, `rise` 2 | HAProxy 3.0 설정 문서 | "If left unspecified, the delay defaults to 2000 ms." / "This value defaults to 3 if unspecified." / "This value defaults to 2 if unspecified." | 일치 |
| 10 | 2-summary:343 | Envoy panic threshold 기본 50% | Envoy "Panic threshold" | "The default panic threshold is 50%." | 일치 |
| 11 | 2-summary:224 | Envoy Maglev `table_size`는 소수, 5000011 이하, 기본 65537 | Envoy `cluster.proto` | "The table size must be prime number limited to 5000011. If it is not specified, the default is 65537." | 일치 |
| 12 | 2-summary:294 | Kubernetes probe 기본: 간격 10초, 타임아웃 1초, 실패 3회, 성공 1회 | Kubernetes "Liveness, Readiness, and Startup Probes" | "periodSeconds … Default to 10 seconds." / "timeoutSeconds … Defaults to 1 second." / "successThreshold … Defaults to 1." / "failureThreshold … Defaults to 3." | 일치 |
| 13 | 2-summary:293 | ALB 헬스체크(instance·ip) 간격 30초, 타임아웃 5초, 비정상 2회, 정상 5회 | ALB 대상 그룹 헬스체크 | "The default is 5 seconds if the target type is instance or ip" / "default is 30 seconds if the target type is instance or ip" / HealthyThresholdCount "The default is 5." / UnhealthyThresholdCount "The default is 2." | 일치 |
| 14 | 2-summary:392 | ALB 등록 해제 지연 기본 300초 | ALB 대상 그룹 속성 | "By default, Elastic Load Balancing waits 300 seconds before completing the deregistration process" | 일치 |
| 15 | 2-summary:455 | ALB `routing.http.xff_header_processing.mode` 기본 `append`, `preserve`·`remove` | ALB X-Forwarded 헤더 | "values for this attribute are append, preserve, and remove. The default value for this attribute is append." | 일치 |
| 16 | 2-summary:449 | RFC 7239 §8.1: 클라이언트 포함 경로의 어느 노드든 고칠 수 있어 믿을 수 없다, 신뢰 프록시 목록도 약점 | RFC 7239 §8.1 | "cannot be relied upon to be correct, as it may be modified … by every node on the way to the server, including the client making the request. … whitelist them as trusted. This approach has at least two weaknesses." | 일치 |
| 17 | 2-summary:307·345 | Spring: liveness는 외부 시스템 검사에 의존하면 안 됨, readiness 기본 미포함, 전 인스턴스 unready면 ClusterIP·NodePort는 연결을 받지 않음 | Spring Boot Actuator Endpoints | "The “liveness” probe should not depend on health checks for external systems." / "Spring Boot does not include any additional health checks in the readiness probe." / "a Kubernetes Service with type=ClusterIP or NodePort does not accept any incoming connections. There is no HTTP error response (503 and so on)" | 일치 |
| 18 | 2-summary:221 | Maglev 칸 수 ⌊M/N⌋ 또는 ⌈M/N⌉, M을 100×N보다 크게 해 차이 1% 안 | Eisenbud 외 NSDI 2016 §3.4 | "Each backend will take either ⌊M/N⌋ or ⌈M/N⌉ entries … In practice, we choose M to be larger than 100 × N to ensure at most a 1% difference in hash space assigned to backends." | 일치 |
