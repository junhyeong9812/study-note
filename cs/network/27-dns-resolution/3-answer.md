# network/27-dns-resolution — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 왜 나무로 위임하나

- 이름은 수억 개이고 계속 바뀐다. 한 서버·한 관리자가 다 들고 갱신할 수 없다.
- 이름 공간을 나무로 쪼개면 각 영역의 관리자가 자기 데이터만 관리한다. 부모는 "누구에게 물으면 되는지"(NS)만 안다.
- 루트 서버가 아는 것: TLD(`com`, `kr` …)를 맡은 서버들의 이름과 주소.
- 루트 서버가 모르는 것: `www.example.com`의 IP 같은 하위 데이터. 물으면 referral(TLD 서버 목록)을 준다.

### 2. 세 역할과 질의 방식

- 스텁 해석기: 앱 옆의 OS 라이브러리(glibc 등)다. `/etc/resolv.conf`에 적힌 재귀 해석기에 묻는다.
- 재귀 해석기: 사내·통신사·공용 DNS다. 대신 나무를 따라가고 결과를 캐시한다.
- 권한 서버: 영역 원본 데이터를 가진 서버다. 그 영역의 최종 답을 준다.
- 스텁 → 재귀 해석기: **재귀 질의**(RD=1). 최종 답이나 에러만 받는다.
- 재귀 해석기 → 루트·TLD·권한 서버: **반복 질의**. 답, 에러, 또는 referral을 받는다.

### 3. 헤더 비트

- RD(Recursion Desired): 질의자가 재귀를 요청한다.
- RA(Recursion Available): 서버가 재귀를 해 줄 수 있음을 알린다. 서버는 모든 응답에서 이 비트를 켜거나 끈다. "사용"이 아니라 "가능"을 뜻한다(RFC 1034 §4.3.1).
- AA(Authoritative Answer): 이 응답이 그 영역의 권한 서버에서 나왔다.
- TC(TrunCation): 응답이 잘렸다. UDP 512바이트(EDNS 없을 때) 등 한도를 넘었다는 뜻이다(RFC 1035 §4.2.1). 클라이언트는 이를 TCP로 다시 물으라는 신호로 받는다(RFC 7766 §4).
- 재귀 처리 확인: 응답에 RD와 RA가 **둘 다** 켜져 있으면 재귀로 처리된 것이다(RFC 1034 §4.3.1). `dig`의 `flags: qr rd ra`로 본다.

### 4. `www.example.com` A 찾기

```text
재귀 해석기 -> 루트:    www.example.com A?
            <- referral: com의 NS 목록 (+ glue: 그 NS들의 IP)
재귀 해석기 -> com TLD: www.example.com A?
            <- referral: example.com의 NS 목록 (+ glue가 필요하면 같이)
재귀 해석기 -> example.com 권한 서버: www.example.com A?
            <- AA=1, www.example.com. A 192.0.2.10 (TTL 포함)
재귀 해석기 -> 스텁: 답 전달, TTL 동안 캐시
```

- referral: 루트와 TLD의 응답이다. AUTHORITY 절에 NS 레코드가 온다.
- glue: NS 이름이 위임되는 영역 안에 있으면(예: `ns1.example.com`이 `example.com`의 NS) 부모가 그 주소를 ADDITIONAL 절에 같이 준다. 그래야 순환 없이 찾아갈 수 있다(RFC 1034 §4.2.1).
- 출발점인 루트 서버 주소는 루트 힌트에서 얻는다.

### 5. 응답 상태 구분

- `NXDOMAIN`(RCODE 3): 그 **이름 자체가 존재하지 않는다**(권한 서버 기준).
- `NOERROR` + 빈 ANSWER: 이름은 있는데 **그 타입의 레코드가 없다**(예: AAAA 없음). 흔히 NODATA라 부른다.
- `SERVFAIL`(RCODE 2): 서버가 **답을 만들 수 없었다**. 권한 서버에 닿지 못함, 위임 오류, DNSSEC 검증 실패 등이다. 이름이 없다는 뜻이 아니다.

### 6. apex CNAME 불가

- CNAME이 있는 이름에는 다른 데이터가 있으면 안 된다.
  - RFC 1034 §3.6.2: "If a CNAME RR is present at a node, no other data should be present."
  - RFC 2181 §10.1: 별명 이름은 DNSSEC 레코드 외에 "may have no other data".
- 영역의 최상위 노드(apex)에는 그 영역의 NS들과 SOA 하나가 있다(RFC 1034 §4.2.1).
- 그래서 apex에 CNAME을 두면 같은 이름에 SOA·NS와 CNAME이 공존해 규칙을 어긴다.
- 우회
  - 사업자 기능: Cloudflare CNAME flattening(최종 IP를 대신 돌려줌), Route 53 alias 레코드.
  - apex는 A/AAAA로 두고 `www`만 CNAME으로 둔 뒤 HTTP 리다이렉트를 한다.

### 7. 자료구조와 매칭

- 이름 공간은 **라벨을 오른쪽부터 읽는 트라이(역순 라벨 트라이)** 다. `api.example.com` = 루트 → `com` → `example` → `api`.
- 재귀 해석기는 캐시에서 질의 이름의 **가장 가까운(깊은) 조상 영역**의 NS를 찾아 거기서부터 내려간다.
- 이것은 라우팅의 최장 접두사 매칭과 같은 모양이다. 방향만 반대인 **최장 접미사 매칭**이다.

### 8. 특정 도메인만 `SERVFAIL`

- 원인 후보
  1. 그 영역의 권한 서버가 모두 다운이거나 도달 불가다.
  2. 위임 오류(lame delegation): 부모의 NS가 더는 그 영역을 서비스하지 않는 서버를 가리킨다.
  3. DNSSEC 검증 실패(서명 만료, DS·DNSKEY 불일치).
- 좁히는 순서
  1. `dig <이름>`, `dig @8.8.8.8 <이름>` — 해석기 한 곳만의 문제인지 본다. EDE 코드가 있으면 읽는다.
  2. `dig +trace <이름>` — 어느 위임 단계에서 끊기는지 본다.
  3. `dig @<각 NS> <이름> +norecurse` — 권한 서버를 하나씩 직접 친다. AA가 켜진 답이 오는지 본다.
  4. DNSSEC이 의심되면 `dig +cd <이름>`으로 검증을 끈 결과와 비교한다(CD = Checking Disabled, `+cd`는 `+cdflag`의 줄임 — BIND dig 문서, RFC 4035 §3.2.2). CD 없이 SERVFAIL인데 CD를 켜면 답이 오면 DNSSEC 검증 실패다.

### 9. 컨테이너에서만 `UnknownHostException`

- IP로 되니 네트워크 경로는 산다. **이름 해석 구간**만 문제다.
- 확인 순서
  1. 컨테이너 안 `cat /etc/resolv.conf` — nameserver가 없거나 닿지 않는 주소인지 본다. nameserver가 없으면 glibc는 로컬 머신의 네임 서버를 쓴다(resolv.conf(5)). 컨테이너 안에는 보통 그런 서버가 없다.
  2. `getent hosts <이름>` — OS 경로로 해석되는지 본다.
  3. `dig @<resolv.conf의 서버> <이름>` — 해석기에 UDP/TCP 53이 닿는지 본다.
  4. 런타임 DNS 설정(도커 `--dns`, 쿠버네티스 `dnsPolicy`/`dnsConfig`)을 확인한다.

### 10. 긴 TXT만 실패

- 응답이 UDP 한도를 넘어 잘렸다. TC 비트가 켜진다.
- 클라이언트가 TCP 53으로 다시 묻는데(RFC 7766 §4), 방화벽이 TCP 53을 막아 실패한다.
- DNS 구현은 UDP와 TCP를 둘 다 지원해야 한다(MUST, RFC 7766 §5). 네트워크 정책이 이를 깨뜨린 것이다.
- 대처: 해석기·권한 서버 사이 경로에서 TCP 53을 허용한다.
