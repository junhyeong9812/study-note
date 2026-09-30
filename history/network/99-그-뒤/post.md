# 네트워크 — 그 뒤 (2026-09 기준)

> 이 문서는 **재서술이 아니라 새로 쓴 것**이다.\
> 앞의 여섯 편은 `~/project/network-history/`를 정본으로 두고 옮긴 것이지만, 이 편에는 대조할 원본이 없다.\
> 그래서 문장마다 원문 대신 **출처**를 근거로 둔다 — 출처로 확인하지 못한 것은 적지 않았다.\
> 기준일은 **2026-09-20**이고, 다루는 범위는 **원본이 멈춘 2022년 6월 이후**다.

## 원본이 멈춘 자리

원본 6편에서 **연도가 붙은 마지막 사건**은 06편의 이 줄이다.

> 2021년 5월 QUIC 전송(RFC 9000), **2022년 6월 HTTP/3(RFC 9114)·QPACK 표준화**.
> — `~/project/network-history/06-현대-네트워킹.md` 5절

다른 편의 마지막 사건도 그보다 앞이다.

| 편 | 원문이 다루는 마지막 사건 |
|----|--------------------------|
| 02 프로토콜 스택 | TCP 혼잡 제어 계보(Reno → CUBIC → BBR) |
| 03 주소·DNS·라우팅 | IPv4 고갈(2011) 이후의 IPv6 전환·BGP·애니캐스트 |
| 04 네트워크 보안 | NIST SP 800-207 제로트러스트 아키텍처(2020) |
| 05 응용 프로토콜 | gRPC(2015) · JSON RFC 8259(2017) |
| 06 현대 네트워킹 | **HTTP/3 RFC 9114(2022-06)**, 그리고 "다음 진화"로만 언급된 eBPF 기반 사이드카리스 메시 |

그래서 이 문서가 메우는 간격은 **2022년 6월 ~ 2026년 9월, 약 4년 3개월**이다.

한 가지 미리 못 박아 둘 것이 있다.\
아래에 나오는 **RFC가 발행됐다는 말은 "널리 쓰인다"는 뜻이 아니다.**\
IETF의 RFC 발행은 *명세가 합의됐다*는 사건이고, 실제 배포는 별개로 측정해야 하는 문제다.\
이 문서는 둘을 나눠 적었다 — 명세는 RFC 번호와 상태로, 배포는 그 수치를 잰 출처와 조건으로.\
그리고 RFC의 **상태**는 rfc-editor의 info 페이지가 표시하는 성숙도 등급(**Proposed Standard** · **Internet Standard** · **Best Current Practice**)으로 통일해 적는다.\
RFC 본문에 적힌 "Internet Standards Track"과 이 등급은 서로 다른 층위의 이름이다 — 앞은 **트랙 이름**, 뒤는 **그 트랙 안에서의 성숙도 단계**다.\
두 말이 섞이면 초보자는 다른 등급으로 읽게 되므로, 이 문서는 **성숙도 쪽으로 통일**한다.

## 그 뒤 무슨 일이 있었나

### 1. TCP가 41년 만에 문서를 갈아입었다 (2022-08)

원본 02편은 TCP를 **RFC 793(1981)** 기준으로 설명한다.\
그 RFC 793이 **2022년 8월 RFC 9293으로 대체**됐다.

- 상태: **Internet Standard (STD 7)** — 표준 등급 자체는 그대로다.
- RFC 9293은 RFC 793과 그 뒤 40년간 793을 고쳐 온 RFC들(879·2873·6093·6429·6528·6691)을 **한 문서로 합쳤다**.
- 1절(Purpose and Scope)의 표현: *"The purpose of this document is to bring together all of the IETF Standards Track changes and other clarifications that have been made to the base TCP functional specification (RFC 793) and to unify them into an updated version of the specification."*

> **주의해서 읽을 것.**\
> 이것은 **TCP가 바뀐 사건이 아니라, TCP를 적어 둔 종이가 정리된 사건**이다.\
> 3-way 핸드셰이크도 혼잡 제어도 달라지지 않았다.\
> 다만 "TCP의 정본이 무엇이냐"를 물을 때 오늘의 답은 RFC 793이 아니라 **RFC 9293**이다.

### 2. QUIC 계열이 가족을 늘렸다

원본 06편은 QUIC을 RFC 9000 하나로 다룬다.\
그 뒤 QUIC 위에 얹히는 명세들이 줄줄이 나왔다.

| RFC | 제목 | 상태 | 발행 |
|-----|------|------|------|
| RFC 9369 | QUIC Version 2 | Proposed Standard | 2023-05 |
| RFC 9484 | Proxying IP in HTTP | Proposed Standard | 2023-10 |

- **RFC 9369(QUIC v2)** 는 기능을 더한 버전이 아니다.\
  버전 협상이 실제로 동작하는지 확인하고, 중간 장비가 "QUIC v1의 바이트 모양"에 굳어 버리는 것(**ossification**)을 막으려고 만든 **거의 같은 내용의 다른 버전**이다.
- **RFC 9484(Proxying IP in HTTP)** 는 HTTP 위로 **임의의 IP 패킷**을 터널링한다.\
  초록의 표현: UDP 프록시와 비슷하지만 *"allows transmitting arbitrary IP packets"*.\
  1절은 **기존 방식의 한계**를 이렇게 적는다 — CONNECT는 TCP 터널을, 그와 비슷한 UDP용 방식(RFC 9484가 참조하는 RFC 9298)은 UDP를 만들지만, *"these mechanisms cannot tunnel other IP protocols [IANA-PN] nor convey fields of the IP header."*\
  1절은 또 *"This protocol supports all existing versions of HTTP by using HTTP Datagrams"* 라고 적는다 — HTTP/2·HTTP/3·HTTP/1.x에서 모두 동작한다.

> RFC 9484가 서 있는 자리를 원본 06편의 말로 옮기면 이렇다.\
> 4절의 VPN·오버레이가 하던 일(IP 패킷을 남의 망 위로 실어 나르기)을 **HTTP 연결 위에서** 한다.\
> 즉 HTTP가 응용 프로토콜에서 **터널 전송 수단**으로도 쓰이게 됐다.

### 3. TLS의 정본이 RFC 8446에서 RFC 9846으로 옮겼다 (2026-07)

원본 04편은 TLS 1.3을 **RFC 8446(2018)** 으로 적는다.\
그 자리가 2026년에 바뀌었다.

- **RFC 9846 — The Transport Layer Security (TLS) Protocol Version 1.3**, **Proposed Standard**, **2026년 7월**.
- 헤더의 `Obsoletes:` 줄: **5077, 5246, 6961, 7627, 8422, 8446**.
- 즉 TLS 1.3의 원래 명세(8446)뿐 아니라 **TLS 1.2의 명세(RFC 5246)까지 함께 obsolete 처리**됐다.

> **여기서 흔한 오해 하나를 끊어 두자.**\
> "RFC 5246이 obsolete 됐다"는 **TLS 1.2가 금지됐다는 뜻이 아니다.**\
> obsolete 는 *그 문서가 더 이상 최신 정본이 아니다*라는 문서 상태 표시다.\
> 실제로 TLS 1.0·1.1을 **금지**한 것은 별도의 **RFC 8996**(Best Current Practice, BCP 195, 2021년 3월)이고, 그것은 원본이 멈춘 시점 이전의 일이다.\
> RFC 8996은 4절 *"TLS 1.0 MUST NOT be used."* · 5절 *"TLS 1.1 MUST NOT be used."* 라고 적는다.

### 4. 포스트 양자 암호가 초안에서 RFC가 됐다 (2026-08)

원본 04편의 공개키 이야기는 Diffie–Hellman·RSA·타원곡선에서 끝난다.\
그 뒤 양자 컴퓨터를 가정한 **키 합의 방식**이 TLS 표준 트랙에 들어왔다.

- **RFC 10024 — Post-Quantum Traditional (PQ/T) Hybrid Key Agreement Mechanisms for TLS 1.3**, **Proposed Standard**, **2026년 8월**.
- 정의한 것은 세 가지 **하이브리드** 방식 — `X25519MLKEM768` · `SecP256r1MLKEM768` · `SecP384r1MLKEM1024`.
- 초록의 표현: 격자 기반 **ML-KEM**(Module-Lattice-Based Key Encapsulation Mechanism)을 **ECDHE**(기존 타원곡선 키 교환)와 **결합**한다.

> **"하이브리드"가 핵심이다.**\
> 새 방식이 기존 방식을 *대체*한 것이 아니라, 둘을 **같이** 써서 **어느 한쪽이 깨져도 나머지가 버티게** 한 설계다.\
> 명세가 그렇게 적고 있으므로(post-quantum **과** ECDHE의 결합), "이제 TLS가 양자내성이 됐다"로 읽으면 안 된다.

### 5. ECH — SNI 평문 노출이 표준으로 막혔다 (2026-03)

원본 04편은 TLS 핸드셰이크에서 무엇이 감춰지고 무엇이 드러나는지를 다루지만, **SNI**(어느 호스트에 접속하는지 알려 주는 평문 필드) 문제의 해법까지는 가지 않는다.

- **RFC 9849 — TLS Encrypted Client Hello**, **Proposed Standard**, **2026년 3월**.
- 하는 일: 클라이언트가 **ClientHello 자체를 서버의 공개키로 암호화**해서, **SNI·ALPN** 같은 필드를 망 관찰자로부터 가린다.
- **1절(Introduction)** 이 밝히는 한계: 같은 TLS 설정을 공유하는 서버들이 하나의 **익명 집합(anonymity set)** 을 이룬다.\
  1절의 표현 — *"Usage of this mechanism reveals that a client is connecting to a particular service provider, but does not reveal which server from the anonymity set terminates the connection."*

> 이 절은 원본 06편 5절의 "미들박스의 실명(失明)"과 같은 방향의 사건이다.\
> QUIC이 전송 헤더를 가렸다면, ECH는 **TLS 핸드셰이크에 마지막으로 남아 있던 평문 단서**를 가린다.\
> 다만 익명 집합이 작으면 가려지는 정도도 작다 — **10.1절**이 직접 그렇게 적는다.\
> 10.1절의 예: 서버가 이름마다 다른 ECHConfig를 쓰면 *"each anonymity set has size k = 1"* 이 된다.

### 6. DNS가 "접속 방법"까지 알려 주기 시작했다 (2023-11)

원본 03편의 DNS는 **이름 → 주소** 변환기다.\
RFC 9460은 여기에 **접속 조건**을 얹었다.

- **RFC 9460 — Service Binding and Parameter Specification via the DNS (SVCB and HTTPS Resource Records)**, **Proposed Standard**, **2023년 11월**.
- 새 레코드 종류 **SVCB**·**HTTPS** 를 정의한다.
- 클라이언트가 연결을 맺기 **전에** 어떤 프로토콜(예: HTTP/2·HTTP/3)로 붙을 수 있는지, 어떤 포트를 쓰는지를 **DNS 조회 한 번으로** 알 수 있게 한다.
- **암호화 키는 RFC 9460이 정의하지 않았다.** 초록은 이를 확장 여지로만 적고(*"extensible to support future uses (such as keys for encrypting the TLS ClientHello)"*), `ech` SvcParamKey는 레지스트리에 **RESERVED**로만 올려 두었다.
- 두 모드 — **AliasMode**(다른 엔드포인트로 위임)와 **ServiceMode**(엔드포인트별 파라미터 제공).

> 이 레코드가 5절의 ECH와 맞물린다.\
> ECH가 쓰려면 클라이언트가 **접속 전에** 서버의 공개키를 알아야 하는데, 그 키를 나르는 자리가 HTTPS 레코드다.\
> 다만 **그 자리를 실제로 정의한 것은 RFC 9460이 아니라 RFC 9848**(Bootstrapping TLS Encrypted ClientHello with DNS Service Bindings, Proposed Standard, 2026년 3월)이다.\
> RFC 9848은 1절에서 이 SvcParam이 *"intended to serve as the primary bootstrap mechanism for ECH"* 라고 적는다.\
> 3절(SvcParam for ECH Configuration)은 *"SvcParamKey conveys the ECH configuration of an alternative endpoint"* 라고 정의한다.\
> 원본 03편이 "DNS는 전화번호부"라고 설명한 그 전화번호부가, **번호와 함께 통화 조건까지 적은 장부**가 된 셈이다.

### 7. HTTP/2의 다중화가 공격 표면이 됐다 — Rapid Reset (2023-10)

원본 06편은 HTTP/2의 다중화를 **문제(HoL 블로킹)를 가진 해법**으로 설명한다.\
2023년 가을, 그 다중화가 **가용성 공격의 도구**로 쓰였다.

- Cloudflare가 **2023년 10월 10일** 기술 분석을 공개했다(CVE-2023-44487, 통칭 **HTTP/2 Rapid Reset**).
- 메커니즘: 클라이언트는 `RST_STREAM` 프레임으로 스트림 하나를 취소할 수 있다.\
  Cloudflare의 설명 — *"When a client cancels a stream, it instantly gets the ability to open another stream in its place and can send another request immediately."*
- 공격은 **요청을 보내자마자 즉시 취소하기를 반복**해, 서버가 취소 처리를 따라잡지 못하게 만든다.\
  Cloudflare의 표현 — 서버가 `RST_STREAM`을 *"tear down state quickly enough"* 하지 못하고 *"any kind of delay or lag in tidying up"* 이 생길 때 문제가 된다.
- 규모: Cloudflare가 자사 네트워크에서 관측한 정점이 **초당 약 2억 100만 요청(201 million requests per second)**, 이전 자사 최고 기록의 약 3배였다고 적는다.

> **수치를 읽을 때의 조건.**\
> 이 숫자는 **Cloudflare가 자사 네트워크에서 관측해 2023년 10월 10일에 공개한 값**이고, "인터넷 전체"의 값이 아니다.\
> 다른 사업자가 같은 공격에 대해 내놓은 수치가 있다면, 그것은 **그 사업자의 망에서 잰 별개의 값**이다 — 서로 더하거나 곧바로 비교할 수 있는 값이 아니다.

> 원본 04편의 DDoS 절과 이어 읽을 자리다.\
> 04편이 다룬 DDoS는 주로 **대역폭**을 채우는 공격이었는데, Rapid Reset은 대역폭이 아니라 **요청 처리 상태**를 고갈시킨다.\
> Cloudflare는 이 공격에 쓰인 봇넷이 *"merely 20,000 machines"* 규모였다고 적는다 — 적은 자원으로 큰 부하를 만드는 **비대칭**이 이 공격의 성격이다.

### 8. 사이드카가 선택 사항이 됐다 — 서비스 메시의 데이터 평면 교체

원본 06편 6절은 서비스 메시를 **"Pod마다 Envoy 사이드카"** 모델로 설명하고, 그 비용(메모리·지연 홉) 때문에 *"eBPF·사이드카리스(ambient) 메시로의 다음 진화"* 가 올 것이라고 적는다.\
그 "다음"이 실제로 왔다.

| 사건 | 날짜 | 무엇 |
|------|------|------|
| Cilium, CNCF **Graduated** 승격 | 2023-10-11 | eBPF 기반 네트워킹·보안·관측 프로젝트가 인큐베이팅을 졸업 |
| Kubernetes **Gateway API v1.0** GA | 2023-10-31 | `Gateway`·`GatewayClass`·`HTTPRoute`가 v1으로 승격 |
| Istio **ambient 모드** GA | 2024-11-07 | Istio v1.24에서 `ztunnel`·waypoint·API가 **Stable** 선언 |

- CNCF는 Cilium을 *"an eBPF-powered open source, cloud native solution for providing, securing, and observing network connectivity between workloads"* 로 소개하며, 이 프로젝트가 *"pioneered sidecarless service mesh"* 했다고 적는다.
- Istio 측 표현: *"Istio's ambient data plane mode has reached General Availability, with the ztunnel, waypoints and APIs being marked as Stable by the Istio TOC."* — 그리고 *"Stable status in 1.24 indicates the features of ambient mode are now fully ready for broad production workloads."*
- Gateway API v1.0 발표문의 표현: *"This API version denotes a high level of confidence in the API surface and provides guarantees of backwards compatibility."*

> **"사이드카가 없어졌다"로 읽으면 안 된다.**\
> Istio가 GA 선언한 것은 **ambient 라는 또 하나의 데이터 평면 모드**이고, 사이드카 모드는 그대로 남아 있다.\
> 출처가 말하는 것은 *"ambient 모드가 프로덕션에 쓸 만큼 안정됐다"* 까지다.

## 원문이 「예정」이라 한 것은 어떻게 됐나

원본 6편이 앞날에 대해 적은 문장은 많지 않다.\
확인된 것만 적는다.

| 원문의 표현 | 어디 | 그 뒤 |
|------------|------|-------|
| *"이 오버헤드가 7절 eBPF·사이드카리스(ambient) 메시로의 다음 진화를 낳는다"* | 06편 6절 | **왔다.** Cilium이 CNCF Graduated(2023-10-11), Istio ambient가 v1.24에서 GA(2024-11-07). |
| *"다음 세대(eBPF 기반 사이드카리스 메시, AI 트래픽을 위한 엣지 추론)는 이 유연성과 가시성·효율의 균형을 다시 맞추는 작업이 될 것이다"* | 06편 영향과 의의 | 앞쪽(사이드카리스 메시)은 위와 같다. **뒤쪽(AI 트래픽을 위한 엣지 추론)의 진행은 1차 출처로 확인하지 못해 적지 않는다.** |

## 아직 안 끝난 것

아래는 **RFC가 아니다.** 2026-09-20 기준으로 IETF 데이터트래커에 올라 있는 상태를 그대로 옮긴다.

| 문서 | 무엇 | 상태 (2026-09-20 기준) |
|------|------|------------------------|
| `draft-ietf-quic-multipath-21` | Managing multiple paths for a QUIC connection | **RFC Editor 큐**(IESG 통과, 발행 대기) · Proposed Standard 목표 |
| `draft-ietf-deleg-11` | Extensible Delegation for DNS (DELEG·DELEGPARAM 레코드) | **WG Last Call** · Standards Track 목표 · 개정 2026-07-23 |
| `draft-ietf-sidrops-aspa-verification` | ASPA 객체 기반 BGP AS_PATH 검증 | **Active Internet-Draft**(RFC 아님) · Proposed Standard 목표 · 개정 2026-08-24 · IESG state "I-D Exists" |
| `draft-ietf-ccwg-bbr-06` | BBR Congestion Control | **Active Internet-Draft** · 목표 상태 **Experimental** · 개정 2026-07-06 |

> **BBR 항목을 특히 조심해서 읽을 것.**\
> 원본 02편은 혼잡 제어 계보를 "Reno → CUBIC → BBR"로 적는다.\
> 그런데 BBR은 2026년 9월 현재까지도 **RFC가 아니고**, IETF에서의 목표 상태도 표준 트랙이 아니라 **Experimental**이다.\
> "널리 배포된 것"과 "표준이 된 것"이 다르다는 것을 보여 주는 자리다 — 이 문서 머리말이 미리 못 박은 그 구분이다.

DELEG도 같은 종류의 주의가 필요하다.\
자료에 따라 "DNS에 DELEG 레코드가 생겼다"고 적힌 것을 볼 수 있지만, **2026-09-20 기준 DELEG는 WG Last Call 단계의 인터넷 드래프트**이고 RFC로 발행되지 않았다.

### 이 문서가 싣지 않은 것 — 배포율 수치

HTTP/3·IPv6·RPKI의 **실제 배포 비율**은 이 문서에 적지 않았다.\
측정 조건(기간·표본·관측 지점)까지 함께 확인할 수 있는 1차 수치를 확보하지 못했기 때문이다.\
어떤 수치를 보든 **누가·언제·어느 망에서 쟀는지**를 같이 보라 — CDN 한 곳의 트래픽 비율과 전 세계 사이트 수 비율은 서로 다른 것을 재는 값이다.

## 용어 풀이

> **ossification(경화)** — 중간 장비가 프로토콜의 특정 바이트 모양에 맞춰 굳어, 프로토콜을 바꾸기 어려워지는 현상.\
> 예: RFC 9369이 QUIC v2를 만든 이유 — *"there is the potential for middleboxes to ossify on the version bytes that are usually 0x00000001."*

> **ML-KEM** — Module-Lattice-Based Key Encapsulation Mechanism.\
> 격자 문제에 기반한 키 캡슐화 방식으로, 양자 컴퓨터를 가정한 공격에 견디도록 설계됐다.\
> 예: RFC 10024가 정의한 `X25519MLKEM768`은 ML-KEM-768과 X25519(기존 타원곡선 키 교환)를 **함께** 쓴다.

> **하이브리드 키 합의(PQ/T hybrid)** — 포스트 양자 방식과 기존(traditional) 방식을 결합해, 둘 중 하나가 깨져도 남은 하나가 보호하도록 한 키 합의.\
> 예: RFC 10024의 제목 자체가 "Post-Quantum Traditional (PQ/T) Hybrid Key Agreement Mechanisms for TLS 1.3"이다.

> **ECH(Encrypted Client Hello)** — TLS 핸드셰이크의 첫 메시지인 ClientHello를 서버 공개키로 암호화해 SNI·ALPN을 가리는 확장.\
> 예: RFC 9849가 정의한다.\
> 같은 설정을 공유하는 서버들이 **익명 집합**을 이루고, 관찰자는 그 집합까지만 알게 된다.

> **SVCB / HTTPS 레코드** — 이름에 대해 주소뿐 아니라 **접속 파라미터**(프로토콜·포트·암호화 키 등)를 실어 주는 DNS 레코드.\
> 예: RFC 9460이 레코드 자체와 AliasMode(위임)·ServiceMode(파라미터 제공) 두 모드를 정의하고, ECH 공개키를 싣는 `ech` 파라미터는 RFC 9848이 정의한다.

> **RST_STREAM** — HTTP/2에서 스트림 하나를 취소하라고 알리는 프레임.\
> 예: Rapid Reset 공격은 요청 직후 이 프레임을 반복해 보내 서버의 상태 정리를 밀어붙인다.

> **ambient 모드 / ztunnel** — Istio가 사이드카 프록시 대신 노드 단위 구성 요소로 트래픽을 처리하는 데이터 평면 모드와 그 구성 요소.\
> 예: Istio v1.24에서 ztunnel·waypoints·API가 Stable로 선언됐다(2024-11-07).

> **WG Last Call / RFC Editor 큐** — IETF 문서가 RFC가 되기까지 거치는 단계 이름.\
> 예: 2026-09-20 기준 DELEG는 WG Last Call, QUIC 멀티패스는 RFC Editor 큐에 있다 — **둘 다 아직 RFC가 아니다.**

## 출처

모두 2026-09-20에 직접 열어 본문 주장과 대조했다.\
RFC의 상태 등급은 각 RFC의 [rfc-editor info 페이지](https://www.rfc-editor.org/info/rfc9460/)가 표시하는 값을 그대로 옮겼다.

### 1차 출처 — 표준 문서 (IETF)

- [RFC 9293 — Transmission Control Protocol (TCP)](https://www.rfc-editor.org/rfc/rfc9293.txt) · Internet Standard (STD 7) · 2022-08
- [RFC 9369 — QUIC Version 2](https://www.rfc-editor.org/rfc/rfc9369.txt) · Proposed Standard · 2023-05
- [RFC 9460 — Service Binding and Parameter Specification via the DNS (SVCB and HTTPS RRs)](https://www.rfc-editor.org/rfc/rfc9460.txt) · Proposed Standard · 2023-11
- [RFC 9484 — Proxying IP in HTTP](https://www.rfc-editor.org/rfc/rfc9484.txt) · Proposed Standard · 2023-10
- [RFC 9298 — Proxying UDP in HTTP](https://www.rfc-editor.org/rfc/rfc9298.txt) · Proposed Standard · 2022-08 · RFC 9484 1절이 "기존 방식"으로 가리키는 UDP 프록시 명세
- [RFC 9846 — The Transport Layer Security (TLS) Protocol Version 1.3](https://www.rfc-editor.org/rfc/rfc9846.txt) · Proposed Standard · 2026-07 · Obsoletes 5077, 5246, 6961, 7627, 8422, 8446
- [RFC 9848 — Bootstrapping TLS Encrypted ClientHello with DNS Service Bindings](https://www.rfc-editor.org/rfc/rfc9848.txt) · Proposed Standard · 2026-03 · `ech` SvcParamKey 정의
- [RFC 9849 — TLS Encrypted Client Hello](https://www.rfc-editor.org/rfc/rfc9849.txt) · Proposed Standard · 2026-03
- [RFC 8996 — Deprecating TLS 1.0 and TLS 1.1](https://www.rfc-editor.org/rfc/rfc8996.txt) · Best Current Practice (BCP 195) · 2021-03
- [RFC 10024 — Post-Quantum Traditional (PQ/T) Hybrid Key Agreement Mechanisms for TLS 1.3](https://www.rfc-editor.org/rfc/rfc10024.txt) · Proposed Standard · 2026-08

### 1차 출처 — IETF 데이터트래커 (진행 중 문서의 상태)

- [draft-ietf-quic-multipath — Managing multiple paths for a QUIC connection](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/) · 확인일 2026-09-20
- [draft-ietf-deleg — Extensible Delegation for DNS](https://datatracker.ietf.org/doc/draft-ietf-deleg/) · 확인일 2026-09-20
- [draft-ietf-sidrops-aspa-verification — BGP AS_PATH Verification Based on ASPA Objects](https://datatracker.ietf.org/doc/draft-ietf-sidrops-aspa-verification/) · 확인일 2026-09-20
- [draft-ietf-ccwg-bbr — BBR Congestion Control](https://datatracker.ietf.org/doc/draft-ietf-ccwg-bbr/) · 확인일 2026-09-20
- [draft-ietf-tls-ecdhe-mlkem (→ RFC 10024)](https://datatracker.ietf.org/doc/draft-ietf-tls-ecdhe-mlkem/) · 확인일 2026-09-20
- [draft-ietf-tls-esni (→ RFC 9849)](https://datatracker.ietf.org/doc/draft-ietf-tls-esni/) · 확인일 2026-09-20

### 1차 출처 — 벤더·재단 발표

- [HTTP/2 Rapid Reset: deconstructing the record-breaking attack — Cloudflare Blog](https://blog.cloudflare.com/technical-breakdown-http2-rapid-reset-ddos-attack/) · 2023-10-10
- [Cloud Native Computing Foundation Announces Cilium Graduation — CNCF](https://www.cncf.io/announcements/2023/10/11/cloud-native-computing-foundation-announces-cilium-graduation/) · 2023-10-11
- [Gateway API v1.0: GA Release — Kubernetes Blog](https://kubernetes.io/blog/2023/10/31/gateway-api-ga/) · 2023-10-31
- [Fast, Secure, and Simple: Istio's Ambient Mode Reaches General Availability in v1.24 — Istio Blog](https://istio.io/latest/blog/2024/ambient-reaches-ga/) · 2024-11-07

### 2차 출처

없음.\
본문의 사실 주장은 모두 위의 1차 출처에서 확인했다.\
(검색 결과·뉴스 요약은 1차 출처를 찾아가는 길잡이로만 썼고, 본문 근거로 쓰지 않았다.)

## 이어서 읽기

- [06 현대 네트워킹](06-현대-네트워킹.md) — 이 문서의 2·7·8절이 이어지는 자리
- [04 네트워크 보안](04-네트워크-보안.md) — 3·4·5절이 이어지는 자리
- [03 주소·DNS·라우팅](03-주소-DNS-라우팅.md) — 6절과 DELEG 항목이 이어지는 자리
