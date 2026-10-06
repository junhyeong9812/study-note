# security/22-ssrf — 서버가 대신 요청하게 만들기(SSRF) — 정리 (힌트)

## 해결하는 문제

서버가 사용자가 준 URL로 요청을 대신 보내는 기능(webhook, 미리보기, 이미지 프록시, 가져오기)이 있다.
그 서버는 내부망 안에 있고 방화벽 **안쪽**에서 돈다. 공격자는 바깥에서 못 가는 내부 주소를, 이 서버를 **발판**으로 삼아 두드린다.

```text
  공격자 ──url=http://169.254.169.254/...──▶ [앱 서버(내부망)] ──▶ 클라우드 메타데이터
                                                   │ 방화벽 안쪽이라 닿는다
                                                   ◀── 임시 자격 증명 ── 공격자에게 반환
```

- *SSRF(Server-Side Request Forgery, 서버 측 요청 위조)*: 사용자가 준 URL을 서버가 검증 없이 가져오게 만들어, 개발자가 예상하지 못한 대상으로 요청을 유발하는 결함(CWE-918: "expected destination"을 보장하지 못함). 대상은 외부일 수도 있지만, 가장 큰 위험은 서버만 닿을 수 있는 대상(내부 서비스·메타데이터·localhost)이다. OWASP Top 10 2021 A10, CWE-918.
  - OWASP A10(2021): "SSRF 결함은 웹 애플리케이션이 사용자가 준 URL을 검증하지 않고 원격 리소스를 가져올 때마다 발생한다."
  - 흔한 오해: "외부로 나가는 요청이니 위험하지 않다." 서버는 방화벽 안쪽이라 **외부에서 못 가는 내부 대상**에 닿는다. 그게 핵심 위험이다.
- 21번(SOP/CORS)과 대비: 브라우저에는 SOP가 있지만 서버에는 없다. 서버는 자기 권한으로 어디든 요청한다.

쉬운 예: 외부인이 못 들어가는 사무실에, "이 주소로 서류를 받아다 달라"고 안내 직원(서버)에게 부탁한다.
- 직원은 건물 내부 금고에도 접근 권한이 있어서, 외부인이 직접 못 가는 곳의 서류를 대신 가져온다.

## 동작·원리

### 1. 위험 대상 — 내부 주소 대역

```text
  127.0.0.0/8       루프백(자기 자신의 다른 서비스)
  10/8, 172.16/12, 192.168/16   사설망(RFC 1918) — 내부 서비스
  169.254.0.0/16    링크 로컬 — 169.254.169.254 = 클라우드 메타데이터(AWS IMDS)
  100.64.0.0/10     CGNAT(RFC 6598)
  fc00::/7, ::1, fe80::/10        IPv6 유니크 로컬·루프백·링크 로컬
```

- 내부 주소 판정은 [network/07-ip-addressing-cidr](../../network/07-ip-addressing-cidr/2-summary.md)의 CIDR 대역 비교다. 그 노트가 "SSRF 방어는 이름이 아니라 해석된 실제 주소를 검사해야 한다"고 적는다.
- AWS IMDSv1은 `http://169.254.169.254/latest/meta-data/`를 토큰 없이 응답한다. 역할의 임시 자격 증명이 이 경로에 있어 SSRF의 단골 표적이다.

### 2. 방어는 "요청/객체를 거부하는 것"을 보인다

안전 규칙상 외부·메타데이터로 실제 요청을 보내지 않는다. 거부 **로직**만 로컬에서 테스트한다.

(실험, OpenJDK 21.0.12, `--network none` 컨테이너, 고정 테스트 해석기(실제 DNS 없음), 2026-10-07)

```text
https://api.partner.example/v1/logo                     naive=ALLOW guarded=ALLOW
http://169.254.169.254/latest/meta-data/                naive=DENY  guarded=DENY scheme=http
https://169.254.169.254.partner.example.attacker.test/  naive=ALLOW guarded=DENY host=169.254.169.254.partner.example.attacker.test
https://img.partner.example/a.png                       naive=ALLOW guarded=DENY resolved=10.0.0.5
file:///etc/passwd                                      naive=DENY  guarded=DENY scheme=file
```

- `naive`(문자열에 `partner.example` 포함 검사)는 허용 목록을 쉽게 속는다: `...attacker.test`가 `partner.example`을 포함하면 통과.
- `guarded`는 세 단계로 막는다: ① 스킴 허용 목록(`https`만) ② 호스트 이름 허용 목록 ③ 이름을 해석한 **모든 주소**가 내부 대역이 아닌지. `img.partner.example`은 허용 이름인데 `10.0.0.5`로 해석되어 거부됐다.

### 3. 왜 "이름"이 아니라 "해석된 주소"를 검사하나 — DNS rebinding

```text
  검사 시각: attacker.test → 203.0.113.5 (외부, 허용 통과)
  요청 시각: attacker.test → 127.0.0.1   (공격자가 DNS를 바꿔치기, TTL 0)
            └ TOCTOU: 검사(time of check)와 사용(time of use) 사이에 주소가 바뀐다
```

- *DNS rebinding*: 공격자가 자기 도메인의 DNS 응답을 짧은 TTL로 바꿔, 검사 때는 외부 주소, 실제 연결 때는 내부 주소를 주는 기법.
- OWASP A10: "DNS rebinding과 TOCTOU 경쟁 조건 같은 공격을 피하려면 URL 일관성에 유의하라."
- 대처: 이름을 한 번 해석해 주소를 고정하고, 그 **고정한 주소로 직접 연결**한다(검사한 주소 = 연결한 주소). 또는 전용 egress 프록시가 해석·검사·연결을 한 번에.

### 4. 리다이렉트 — 허용 뒤의 우회

- 허용된 URL이 `302`로 내부 주소(예시: `https://10.0.0.5/admin`)로 리다이렉트하면, 클라이언트가 자동으로 따라가면서 방어를 지나친다.
  - 따라가는지는 클라이언트·스킴에 달렸다. OpenJDK `HttpURLConnection`은 스킴이 바뀌는 리다이렉트(`https`→`http`)는 따라가지 않는다(소스 `followRedirect0`의 프로토콜 비교, 재실험: `http`→`http`는 200으로 따라감, `http`→`https`는 302 그대로). 그래서 `https`만 허용하는 이 가드에 대한 위험한 예는 같은 `https` 스킴의 내부 대상이다.
- JDK 기본값(실험): `HttpClient`는 `followRedirects=NEVER`(안전), `HttpURLConnection`은 `getFollowRedirects()=true`(따라감). 라이브러리마다 다르다 — **확인하고** 리다이렉트를 끄거나, 매 홉마다 다시 검사한다.
- OWASP A10: "HTTP 리다이렉션을 비활성화하라."

### 5. 계층별 방어(deny list만으로는 부족)

```text
  네트워크 계층: egress 방화벽 "기본 거부" — 앱 서버가 필요한 외부 대상에만 나가게
                메타데이터는 IMDSv2 강제(토큰 PUT + 작은 홉 제한) → SSRF 단순 GET 차단
  애플리케이션: 스킴·호스트 허용 목록(양성), 해석 주소 검사, 리다이렉트 금지, 응답 원문 비노출
```

- OWASP A10의 경고: "deny list나 정규식으로 SSRF를 완화하지 마라. 공격자는 우회 목록·도구·기술이 있다." 양성(허용) 목록을 쓴다.
- AWS IMDSv2: 세션 토큰을 `PUT`으로 받아(`X-aws-ec2-metadata-token`) `GET`에 실어야 한다. `PUT` 응답의 홉 제한(IP TTL)은 AWS "Use IMDSv2" 문서 기준 기본 `1`이다. 단 계정 기본값을 IMDSv2로 설정하면 새 인스턴스의 기본 홉 제한은 `2`이고, 홉 제한을 따로 정하지 않았을 때 AMI가 `ImdsSupport: v2.0`이면 `2`(아니면 `1`)다. 컨테이너 환경에서도 AWS는 `2`를 권장한다(판·설정마다 다르니 실제 값을 확인). `X-Forwarded-For`가 붙은 `PUT`은 거부된다. 단순 SSRF GET(헤더·PUT 불가)으로는 토큰을 못 받는다 — 심층 방어.

## 쓰이는 자료구조·알고리즘

- **IP 대역 판정(CIDR)**: 주소를 접두 비트로 대역과 비교한다([network/07](../../network/07-ip-addressing-cidr/2-summary.md), [network/08-routing-and-longest-prefix-match](../../network/08-routing-and-longest-prefix-match/2-summary.md)의 트라이와 같은 비트 접두 비교). `InetAddress.isSiteLocalAddress()`·`isLoopbackAddress()`·`isLinkLocalAddress()`가 이 판정을 돕지만 100.64/10·IPv6 ULA는 직접 비트 검사.
- **허용 목록 = 집합 조회**: 스킴·호스트를 양성 집합에서 찾는다(O(1)). deny 목록(정규식)은 우회된다.
- **이름 해석(DNS)**: 이름 → 주소 매핑. SSRF 방어의 TOCTOU는 이 매핑이 시점마다 달라질 수 있다는 데서 온다([network/27-dns-resolution](../../network/27-dns-resolution/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. URL 가져오기 — 거부 우선 가드

```java
// (취약) 문자열 포함 검사
boolean allowNaive(String url) { return url.contains("partner.example"); }

// (고친 예) 스킴 → 호스트 허용 목록 → 해석된 모든 주소 검사
String guard(String url) throws Exception {
    URI u = new URI(url);
    if (!"https".equals(u.getScheme())) return "DENY scheme";
    if (u.getHost() == null || !ALLOW_HOSTS.contains(u.getHost())) return "DENY host";
    for (InetAddress a : InetAddress.getAllByName(u.getHost()))
        if (isInternal(a)) return "DENY internal " + a.getHostAddress();
    return "ALLOW";
}
boolean isInternal(InetAddress a) {
    if (a.isLoopbackAddress() || a.isLinkLocalAddress() || a.isSiteLocalAddress()
        || a.isAnyLocalAddress() || a.isMulticastAddress()) return true;
    byte[] b = a.getAddress();
    if (b.length == 4 && (b[0] & 0xff) == 100 && (b[1] & 0xc0) == 64) return true; // 100.64/10
    if (b.length == 16 && (b[0] & 0xfe) == 0xfc) return true;                      // fc00::/7
    return false;
}
```

- 실험에서 이 가드가 메타데이터 주소(스킴), 서브도메인 속임수(호스트), 내부로 해석되는 허용 이름(주소), `file://`(스킴)을 모두 거부했다.

### 2. 검사한 주소로 직접 연결(rebinding 차단)

```java
InetAddress[] addrs = InetAddress.getAllByName(host);   // 한 번 해석
for (InetAddress a : addrs) if (isInternal(a)) throw new SecurityException("internal");
// 검사한 바로 그 주소로 연결 — 이름을 다시 해석하지 않는다
HttpClient client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).build();
// 연결 대상 IP를 고정하려면 커스텀 소켓/프록시로 addrs[0]에 직접 연결
```

- 이름을 재해석하면 TOCTOU가 다시 열린다. 검사 시점 주소를 그대로 쓴다.

### 3. 리다이렉트는 끄거나 매 홉 검사

```java
HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).build();
```

- 실험: `HttpClient`는 기본이 `NEVER`지만 `HttpURLConnection`은 기본이 리다이렉트 추적이다. 쓰는 클라이언트의 기본값을 확인한다.

### 4. 클라우드 메타데이터 — IMDSv2 강제

```text
# IMDSv2 필수 설정 (SSRF 단순 GET 차단) — 홉 제한은 호스트 직접 사용이면 1, 컨테이너가 쓰면 AWS 권장 2
HttpTokens=required, HttpPutResponseHopLimit=1
# 토큰을 받아야 메타데이터 접근 가능
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/
```

- 단순 SSRF는 임의 헤더·`PUT`을 못 넣으므로 토큰을 못 받는다. 홉 제한 1은 한 홉 더 거치는 경로(브리지 네트워크의 컨테이너 등)에서 토큰 응답이 닿지 않게 한다 — 그래서 컨테이너가 IMDS를 정당하게 써야 하면 2로 올린다. (실제 메타데이터로 요청하지 않음 — 설정·원리 설명.)

### 5. 응답을 그대로 돌려주지 않는다

- OWASP A10: "원시 응답을 클라이언트에 보내지 마라." 가져온 내용을 그대로 반환하면 내부 서비스 응답이 공격자에게 샌다. 필요한 필드만 추출해 돌려준다.

## 장애 시나리오와 대처

### 1. 메타데이터 접근 로그 뒤 자격 증명 오용

- **현상**: 앱 서버 역할의 임시 키가 엉뚱한 곳에서 쓰인다.
- **보이는 형태**: 앱 로그에 `169.254.169.254` 요청, 메타데이터 접근 흔적, CloudTrail에 그 역할의 비정상 호출.
- **원인**: 사용자 URL을 검증 없이 가져오는 기능 + IMDSv1.
- **대처**: 스킴·호스트·주소 허용 목록, IMDSv2 강제(토큰·작은 홉 제한), egress 방화벽. 유출 시 키 즉시 회전([09](../09-randomness-and-key-management/2-summary.md)).

### 2. 허용 목록을 서브도메인 속임수로 우회

- **현상**: 허용 도메인이 든 URL이 내부로 간다.
- **보이는 형태**: `http://169.254.169.254.partner.example.attacker.test/` 같은 호스트, 또는 `partner.example`을 포함하는 임의 문자열.
- **원인**: 문자열 포함(`contains`)·접두/접미 일치 검사. 실험의 `naive`가 이렇게 뚫렸다.
- **대처**: URL을 파싱해 **호스트 전체**를 허용 집합과 정확히 비교(21번 Origin 검사와 같은 교훈).

### 3. 검사는 통과했는데 내부로 연결(DNS rebinding)

- **현상**: 정적 테스트는 통과하는데 간헐적으로 내부 서비스에 닿는다.
- **보이는 형태**: 같은 호스트가 때때로 내부 주소로 해석됨, 짧은 TTL.
- **원인**: 이름을 검사 후 다시 해석(TOCTOU). 검사 때 외부, 연결 때 내부.
- **대처**: 검사한 주소로 직접 연결, 이름 재해석 금지, egress 프록시에서 해석·검사·연결 일원화.

### 4. ⚠ 리다이렉트로 우회

- **현상**: 허용된 외부 URL인데 내부에 닿는다.
- **보이는 형태**: `302 Location: https://10.0.0.5/...`(예시, 같은 스킴의 내부 주소)를 클라이언트가 따라감.
- **원인**: 리다이렉트 자동 추적 + 홉마다 재검사 없음.
- **대처**: 리다이렉트 비활성화 또는 매 홉 가드 재적용. 쓰는 HTTP 클라이언트의 기본값 확인(실험: `HttpURLConnection` 기본 추적).

### 5. ⚠ deny list·정규식으로 막기

- **현상**: `127.0.0.1`을 막았더니 `0x7f.0.0.1`, `2130706433`(10진), `[::1]`, `0`(=`0.0.0.0`) 등으로 우회된다.
- **원인**: 주소 표기는 여러 형태다. deny 목록·정규식은 전부 못 막는다.
- **대처**: 양성 허용 목록 + 파싱 후 정규화한 주소로 대역 판정(OWASP: deny list로 완화하지 마라).

## 핵심 문장

- SSRF는 서버가 사용자 URL을 대신 가져오게 만들어, 외부에서 못 가는 내부 대상(메타데이터·localhost·내부 서비스)에 서버 권한으로 닿게 하는 결함이다.
- 브라우저와 달리 서버에는 SOP가 없다. 방어는 애플리케이션과 네트워크 계층에서 직접 해야 한다.
- 이름이 아니라 **해석된 실제 주소**를 검사한다. 이름만 검사하면 DNS rebinding(TOCTOU)으로 우회된다.
- deny list·정규식은 우회된다. 스킴·호스트의 양성 허용 목록 + 해석 주소의 CIDR 대역 거부를 쓴다.
- 리다이렉트는 끄거나 매 홉 재검사한다. 응답 원문을 그대로 돌려주지 않는다.
- 클라우드 메타데이터는 IMDSv2(토큰·홉 제한)와 egress 방화벽으로 심층 방어한다.

## 관련 주제·근거

- 선행
  - [21-same-origin-and-cors](../21-same-origin-and-cors/2-summary.md) — 브라우저 SOP. 서버에는 그게 없다
  - [network/07-ip-addressing-cidr](../../network/07-ip-addressing-cidr/2-summary.md) — 내부 주소 대역·CIDR·`169.254.169.254`
- 후속·연결
  - [network/27-dns-resolution](../../network/27-dns-resolution/2-summary.md) — 이름 해석·TTL(rebinding의 토대)
  - [network/08-routing-and-longest-prefix-match](../../network/08-routing-and-longest-prefix-match/2-summary.md) — 접두 비트 매칭
  - [09-randomness-and-key-management](../09-randomness-and-key-management/2-summary.md) — 유출 시 키 회전
  - [security 30 security-incidents](../30-security-incidents/2-summary.md) — Capital One 2019 SSRF
- 1차 출처
  - OWASP Top 10 2021 A10 SSRF — 설명, 네트워크/애플리케이션 계층 예방, 리다이렉트 비활성화, URL 일관성/DNS rebinding/TOCTOU, deny list 금지 <https://top10.owasp.org/2021/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/>
  - OWASP Top 10 2025 — SSRF(CWE-918)는 A01 Broken Access Control에 포함 <https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/>
  - OWASP SSRF Prevention Cheat Sheet <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
  - AWS "Use IMDSv2" — 세션 토큰 PUT, `X-aws-ec2-metadata-token`, 홉 제한 기본 1, `X-Forwarded-For` PUT 거부 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html> · "Configure instance metadata options for new instances" — 계정 기본값 IMDSv2면 홉 제한 2, 무선호 + AMI `ImdsSupport: v2.0`이면 2, 컨테이너 환경 권장 2 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html>
  - RFC 1918(사설망) · RFC 6598(100.64/10 CGNAT) · RFC 3927(169.254/16) · CWE-918 <https://cwe.mitre.org/data/definitions/918.html>
- 실험 목록(2026-10-07, 로컬 전용 — 외부·메타데이터로 실제 요청 안 함, 거부 로직만)
  - A. naive(문자열 포함) vs guarded(스킴·호스트·해석 주소) — OpenJDK 21.0.12 `--network none`, 고정 테스트 해석기: 메타데이터/서브도메인 속임수/내부 해석 이름/`file://` 거부 확인
  - B. 리다이렉트 기본값 — `HttpClient.followRedirects()=NEVER` vs `HttpURLConnection.getFollowRedirects()=true` · 스킴 변경 리다이렉트 미추적(OpenJDK 21.0.12 재실험: `http`→`http` 200, `http`→`https` 302 그대로; 소스 <https://github.com/openjdk/jdk21u/blob/master/src/java.base/share/classes/sun/net/www/protocol/http/HttpURLConnection.java> `followRedirect0`)
  - 코드: `scratchpad/sec/18/ssrf/SsrfGuard.java`, `Redir.java`
