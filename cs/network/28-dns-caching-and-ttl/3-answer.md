# network/28-dns-caching-and-ttl — 정답

## 정답

### 1. DNS 캐시 층

```text
  앱 런타임 캐시 (JVM InetAddress)      자체 정책 — DNS TTL 무시
  OS 캐시 (systemd-resolved, nscd)      TTL 따름 (구성에 따라 층 자체가 없음)
  클러스터·노드 DNS (CoreDNS cache)     TTL 따름, 단 자체 최대 TTL로 자름 (기본 3600/1800)
  재귀 리졸버                            TTL 따름
  권한 서버                              원본 — TTL을 정한다
```

- TTL을 따르는 층은 남은 TTL을 넘겨받는다. 그래서 층이 늘어도 낡음 상한은 원래 TTL 근처다.
- 자체 타이머 층은 그 위에 시간을 더한다.

### 2. 남은 TTL과 최악의 낡음

- 클라이언트는 300 − 200 = **100초**를 받는다. 리졸버가 남은 TTL을 적어 주기 때문이다.
- JVM이 이 답을 받은 순간부터 30초를 더 들고 있을 수 있다.
- 최악의 경우를 보자. 권한 서버에서 레코드가 바뀌기 직전에 리졸버가 옛 값을 막 캐시했다면(남은 300초) 리졸버에서 300초가 걸린다. 그 끝에 JVM이 받아 30초를 더한다. 합이 **약 330초**다.
- 요점: TTL을 존중하지 않는 층의 시간은 합산된다.

### 3. 부정 캐시

- 캐시된 것은 **NXDOMAIN**(그 이름이 없다는 답)이다.
- 시간은 응답 AUTHORITY 절에 온 SOA의 MINIMUM 필드와 SOA 레코드 TTL 중 작은 값이다(RFC 2308 §3, §5).
- 대처는 레코드를 먼저 만든 뒤 조회·헬스체크를 켜는 것이다. 운영하는 리졸버라면 캐시를 비운다.

### 4. NXDOMAIN vs NODATA

- NXDOMAIN: 이름 자체가 없다. RCODE가 Name Error다(RFC 2308 §1).
- NODATA: 이름은 있으나 요청한 타입 레코드가 없다. RCODE는 NOERROR이고 답 절이 비어 있다.
  - 예: A만 있는 이름에 AAAA를 물으면 NODATA다.
- 둘 다 부정 캐시 대상이다.

### 5. IP 이전 절차

1. 지금 TTL을 낮춘다(예시: 60초).
2. **옛 TTL(86400초 = 1일)만큼 기다린다.** 그 전에 캐시된 사본은 옛 TTL로 저장돼 있다.
3. 레코드를 바꾼다. 이제 퍼지는 시간의 상한은 60초 근처다.
4. 안정된 뒤 TTL을 다시 올린다.

남는 위험:
- JVM 캐시처럼 TTL을 무시하는 층.
- 이미 맺어 둔 커넥션 풀의 연결.
- TTL 하한을 강제로 올려 둔 리졸버(예: Unbound `cache-min-ttl` — 문서도 "domain owner intended"보다 오래 캐시된다고 경고한다).

그래서 옛 서버는 한동안 살려 두거나 새 서버로 프록시한다.

### 6. ndots:5 증폭

- `tcpdump -ni any port 53`에 이런 질의가 먼저 보인다.
  - `api.example.com.<ns>.svc.cluster.local`
  - `api.example.com.svc.cluster.local`
  - `api.example.com.cluster.local`
  - 셋 다 NXDOMAIN이다. 그 뒤에 `api.example.com.`이 답을 받는다. A·AAAA 각각이다.
- 원인: 파드 resolv.conf의 `ndots:5`. 점이 5개보다 적은 이름은 검색 목록을 먼저 붙여 본다(resolv.conf(5)).
- 대처
  - 외부 이름을 끝에 점을 붙인 FQDN으로 쓴다.
  - 파드 `dnsConfig.options`로 `ndots`를 낮춘다.
  - 추가로 노드 로컬 DNS 캐시로 부하를 흡수한다.

### 7. JVM TTL 설정

- `networkaddress.cache.ttl`은 시스템 속성이 아니라 **보안 속성**이다. `-D`로 주면 읽히지 않는다(AWS SDK 문서).
- 올바른 방법
  1. `$JAVA_HOME/conf/security/java.security` 파일에 적는다.
  2. 시작 직후, 어떤 조회보다 먼저 `Security.setProperty("networkaddress.cache.ttl", "5")`를 부른다.
- 대체 경로로 `-Dsun.net.inetaddr.ttl=5`가 있다. 보안 속성이 없을 때 쓰이는 JDK 내부 속성이다.

### 8. DNS 밖의 캐시

- **커넥션 풀·keep-alive 연결**: 이미 맺은 TCP 연결은 옛 IP에 붙어 있다. DNS가 바뀌어도 연결은 모른다.
  - 대처: 풀의 최대 수명(max lifetime), 오류 시 풀 비우기.
- 그 밖에 애플리케이션이 해석한 IP를 필드에 저장해 둔 경우, 프록시의 upstream 해석 결과 고정도 있다.
  - 예: nginx는 `proxy_pass`·`upstream server`에 변수 없이 쓴 이름을 설정 적재 시점에 푼다. 실행 중 IP 변경을 따라가려면 `server ... resolve`와 `resolver`가 필요하다(nginx upstream 문서 "without the need of restarting nginx"). upstream은 공유 메모리에 있어야 하므로 `zone`도 둔다. 오픈소스 nginx는 1.27.3부터 쓸 수 있고, 그 전에는 상용 구독 전용이었다.

### 9. 짧은 TTL과 serve-stale

- 캐시가 살아 있는 동안은 권한 서버가 죽어도 답이 나온다. 만료 순간부터 재질의가 실패한다(SERVFAIL).
- TTL이 짧을수록 캐시가 빨리 비어 먼저 무너진다.
- serve-stale(RFC 8767)
  - 리졸버가 권한 서버에 닿지 못하면 만료된 답을 돌려준다.
  - 그 답에는 0보다 큰 TTL을 붙인다(MUST). 권장값은 30초다.
  - 만료 뒤 보관 기간은 1~3일을 제안한다(§5 예시 방법).
- 대가: 장애 중에는 바뀐 레코드를 반영하지 못한다.
