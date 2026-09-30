# network/53-network-incidents — 실사건 세 가지: Facebook BGP·DNS 전면 장애 · Let's Encrypt 교차 서명 루트 만료 · Pakistan Telecom의 YouTube 하이재킹 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

leaf 노트는 메커니즘을 **하나씩** 설명한다.\
BGP는 13번, DNS는 27·28번, 체인 검증은 30번이다.\
실제 장애는 메커니즘 여러 개가 **사슬**로 이어져 커진다.\
그리고 증상은 사슬의 **끝**에서 보인다. 원인은 사슬의 **처음**에 있다.

```text
  leaf 노트:   [BGP]   [DNS]   [재시도]   [원격 접속]      <- 각각 따로 이해
  실사건:      [BGP] -> [DNS] -> [재시도 폭증] -> [복구 도구 불통]
                원인                              증상이 보이는 곳
```

쉬운 예: 정전 사고다.\
"엘리베이터가 멈췄다"는 신고가 먼저 온다.\
원인은 변전소 차단기다. 그런데 관리실 전화도 같은 전기를 써서 먹통이다.\
사고 보고서는 이 사슬을 시간 순서로 복원한다.

똑같은 구조다.\
Facebook 2021에서 사용자는 "DNS 실패"를 봤다. 원인은 백본 작업 명령이었다. 복구 도구도 같은 망에 의존했다.

이 노트는 공개된 1차 사후 분석으로 세 사건을 복원한다.
- **Facebook(2021-10-04)**: 망 **안쪽** 작업 하나가 BGP 철회와 DNS 소멸로 번졌다.
- **Let's Encrypt DST Root CA X3 만료(2021-09-30)**: 인증서는 멀쩡한데 **경로 구축** 구현 차이로 구형 클라이언트만 실패했다.
- **Pakistan Telecom–YouTube(2008-02-24)**: 망 **바깥**의 다른 AS가 더 구체적인 경로를 광고해 트래픽을 빼앗았다.

  - *사후 분석(postmortem)*: 장애 뒤 타임라인·원인·교훈을 적어 공개하거나 공유하는 문서다.
  - *1차 출처*: 당사자(Meta, Let's Encrypt, OpenSSL)나 직접 관측자(Cloudflare, RIPE NCC)가 쓴 문서다.

## 동작·원리

### 사건 1 — Facebook BGP·DNS 전면 장애 (2021-10-04)

#### 타임라인 (UTC, Cloudflare 관측)

```text
  15:40  Facebook(AS32934)의 BGP 경로 변화가 몰림            "그때 문제가 시작됐다"
  15:50  facebook.com DNS가 1.1.1.1·8.8.8.8 등에서 해석 불가 (SERVFAIL)
  15:51  Cloudflare 내부 사고 개설: "Facebook DNS lookup returning SERVFAIL"
  15:58  Facebook DNS 대역 185.89.218.0/23, 129.134.30.0/23 경로 광고가 멈춘 것 확인
   ...   (약 5시간 동안 DNS 불가)
  21:00  Facebook 망에서 BGP 활동 재개
  21:17  BGP 활동 최고점
  21:20  DNS 다시 해석됨
  21:28  "인터넷에 다시 연결된 것으로 보이고 DNS도 동작"
```

- Meta는 첫 공지(10-04)에서 원인을 "데이터센터 사이 트래픽을 조율하는 백본 라우터의 설정 변경"이라고 적었다. 다음 날 글(10-05)에서 세부를 밝혔다.

#### 메커니즘 — 사슬 복원

```text
  (1) 백본 용량 점검 명령           Meta: "전 세계 백본 용량의 가용성을 평가하려던 명령이
       |                          의도치 않게 백본의 모든 연결을 끊었다"
       |  감사 도구가 막아야 했는데   "감사 도구의 버그 때문에 명령을 제대로 멈추지 못했다"
       v
  (2) 데이터센터 사이 연결 전부 단절
       |
       v
  (3) 작은 시설(엣지)의 DNS 서버:    Meta: "DNS 서버는 데이터센터와 통신할 수 없으면
      "데이터센터와 말이 안 된다"      그 BGP 광고를 끈다" (건강하지 않은 망의 신호로 보고)
       |
       v
  (4) DNS 서버 대역의 BGP 경로 철회   -> 인터넷에서 권한 DNS 서버로 가는 길이 사라짐 (13번)
       |                              DNS 서버 자체는 동작 중이었다
       v
  (5) 전 세계 리졸버: 권한 서버에 못 닿음 -> SERVFAIL (27번)
       |  캐시가 만료된 순서대로 해석 실패가 번짐 (28번)
       v
  (6) 사용자 앱·브라우저의 재시도      -> 1.1.1.1 질의가 평소의 30배 (Cloudflare)
       |
       v
  (7) Meta 내부: "DNS 전체 소실이 장애 조사·해결에 쓰는 내부 도구 다수를 망가뜨렸다"
       |  주 접속과 대역외(out-of-band) 접속이 모두 끊겨 엔지니어를 데이터센터 현장으로 보냄
       |  시설은 물리·시스템 보안이 높아 들어가기도, 장비를 바꾸기도 어렵게 설계됨
       v
  (8) 복구: 백본 복구 뒤 서비스를 한꺼번에 켜면 전력·부하 급변으로 새 장애 위험
          Meta: 데이터센터 전력 사용이 "수십 메가와트" 규모로 떨어져 있었다
          평소 "storm" 훈련 경험으로 부하를 점진적으로 되돌림
```

- (3)~(4)는 **좋은 의도의 자동화**다. 한 DNS 시설이 고립되면 그 시설을 경로에서 빼는 것은 합리적이다. 그런데 **모든 시설이 동시에** 같은 판단을 하자 전부 사라졌다.
- (4)에서 서버는 살아 있었다. "서버가 죽었다"가 아니라 "서버로 가는 **길**이 사라졌다"다. 13번 장애 시나리오 2와 같은 사건이다.
- (7)은 복구 경로가 장애 대상과 **같은 의존성**(내부 DNS·백본)을 가졌을 때 생긴다.
- Meta는 보안과 복구 속도의 교환을 이렇게 평했다: 평소의 보안 강화가 드문 사건의 느린 복구보다 가치 있다.

  - *백본(backbone)*: 데이터센터들을 잇는 조직 내부의 광역망이다. Meta는 "전 세계를 가로지르는 수만 마일의 광케이블"이라고 설명한다.
  - *경로 철회(withdraw)*: BGP UPDATE로 "이 접두사로는 더 이상 나를 거쳐 오지 말라"고 알리는 것이다(13번).
  - *storm 훈련*: Meta가 큰 시스템 장애를 모의하는 훈련의 이름이다.

#### 밖에서 보인 신호

| 신호 | 어디서 보였나 | 연결 leaf |
|---|---|---|
| `dig facebook.com` → `status: SERVFAIL` | 모든 공용 리졸버 | [27](../27-dns-resolution/2-summary.md) · [52](../52-network-symptom-index/2-summary.md) |
| AS32934의 BGP 경로 변화 급증, DNS 대역 광고 소멸 | BGP 수집기·looking glass | [13](../13-routing-protocols-ospf-bgp/2-summary.md) |
| 리졸버 질의량 30배 | 공용 리졸버 운영자 지표 | [28](../28-dns-caching-and-ttl/2-summary.md) |
| Twitter·Signal 등 다른 서비스로 질의 증가 | Cloudflare 관측 | — |
| 사용자 앱: 이름 해석 실패 (`UnknownHostException`·`ENOTFOUND`·`EAI_AGAIN` 류) | 클라이언트 | [52](../52-network-symptom-index/2-summary.md) |

### 사건 2 — Let's Encrypt DST Root CA X3 만료 (2021-09-30)

#### 배경 — 왜 오래된 루트에 기댔나

```text
  2021년 9월 당시 Let's Encrypt 기본 체인 (서버가 보내는 것)

    [리프] --issuer--> [중간 R3] --issuer--> [ISRG Root X1 (DST가 교차 서명한 사본)]
                                                     |
                                                     | issuer
                                                     v
                                             [DST Root CA X3]  <- 2021-09-30 만료
                                             (옛 기기 루트 스토어에 널리 있음)

  같은 R3는 자체 서명 ISRG Root X1으로도 올라갈 수 있다:
    [리프] --> [R3] --> [ISRG Root X1 (자체 서명, 새 루트 스토어에 있음)]
```

- 새 CA의 루트(ISRG Root X1)는 처음엔 옛 기기의 루트 스토어에 없다. 그래서 이미 널리 신뢰받는 루트(DST Root CA X3)가 **교차 서명**해 줘서 호환성을 얻었다(LE 문서).
- DST Root CA X3가 2021-09-30에 만료되면서, 이 교차 서명 경로로만 신뢰를 얻던 클라이언트가 문제가 됐다.

  - *교차 서명(cross-sign)*: 한 CA의 인증서(여기서는 ISRG Root X1의 공개키)에 다른 CA가 서명해 준 사본이다. 같은 공개키에 발급자가 다른 인증서가 둘 생기므로 **경로가 둘**이 된다(30번).

#### 누가 왜 실패했나

```text
  클라이언트 종류                   루트 스토어                결과
  -----------------------------   ------------------------   -----------------------------------
  최신 OS·브라우저, OpenSSL 1.1.0+  ISRG Root X1 있음           만료된 DST 경로를 버리고 X1 경로 사용 -> 정상
  OpenSSL 1.0.2 기반 클라이언트      ISRG Root X1 있어도         **실패**: 서버가 준(untrusted) 체인을 우선해
                                  DST Root CA X3도 있음        만료된 DST로 가는 경로를 고르고 만료로 보고
  Android 7.1.1 미만              X1 없음, DST 있음            대체로 정상: Android는 신뢰 앵커의 notAfter를
                                                             일부러 보지 않음 -> DST 교차 서명 경로 유효
  아주 오래된 기기(iPhone 4 등)     X1 없음                     인증서 경고 (LE 문서의 예)
```

- OpenSSL 블로그(2021-09-13): OpenSSL 1.0.2는 상대가 준 untrusted 체인을 **항상** 선호한다("always prefers the untrusted chain"). 그 체인에 만료된 신뢰 루트로 가는 경로가 있으면 그 경로를 골라 만료를 보고한다. 같은 글은 최신 CA 번들에 자체 서명 ISRG Root X1도 들어 있어, 검증하는 클라이언트가 만료되지 않은 대체 경로를 찾을 수 있다고 적는다. 1.0.2에는 그것이 적용되지 않는다.
- LE 문서: OpenSSL 1.0.x는 ISRG Root X1을 신뢰하더라도 Android 호환 체인을 받으면 실패한다. OpenSSL 1.1.0 이상이 필요하다.
- 즉 **인증서가 만료된 것이 아니라 경로 구축이 만료된 경로를 고른 것**이다. RFC 5280은 경로 **검증**만 정하고 경로 **구축**은 구현에 맡긴다(30번 §4).

#### Android 예외 — 만료 뒤에도 유효한 교차 서명

- LE(2020-12-21): Android는 신뢰 앵커의 notAfter를 **일부러** 쓰지 않는다. 그래서 DST Root CA X3가 자기 만료일보다 늦게까지 유효한 교차 서명을 발급해 줄 수 있었다.
- 대상은 ISRG Root X1을 신뢰하지 않는 Android 7.1.1 미만 기기였다.
- 이 교차 서명은 2024-09-30에 만료됐다. LE는 2024-02-08부터 기본 체인에서 이것을 뺐다(LE 2023-07-10 공지).
- LE 2023 공지 기준, ISRG Root X1을 신뢰하는 Android 기기 비율은 3년 동안 66%에서 93.9%로 올랐다.

#### 대처 (OpenSSL 블로그의 세 가지)

```text
  1. 클라이언트 트러스트 스토어에서 만료된 DST Root CA X3를 지운다.
     ISRG Root X1 자체 서명이 없으면 넣는다.
  2. -trusted_first 옵션 / X509_V_FLAG_TRUSTED_FIRST 플래그로
     "상대가 준 체인보다 트러스트 스토어를 먼저" 보게 한다.
  3. 서버가 Let's Encrypt의 대체 체인(DST 교차 서명 없는 것)을 쓰게 한다.
```

- 1·2는 **클라이언트** 쪽, 3은 **서버** 쪽 대처다. 서버 운영자는 3을 하면 옛 Android를 잃는다. 누구를 살릴지의 선택이다.
- OpenSSL 블로그는 다음 1.0.2 릴리스(1.0.2zb, 유료 지원 고객 전용)에서 빌드 옵션 `-DOPENSSL_TRUSTED_FIRST_DEFAULT`로 trusted-first를 기본으로 켤 수 있게 한다고 예고했다. OpenSSL 1.1.0부터는 `-trusted_first`가 기본으로 켜져 있고 끌 수 없다(openssl-verification-options(1)).

#### 밖에서 보인 신호

| 신호 | 어디서 보였나 | 연결 leaf |
|---|---|---|
| `certificate has expired`, 그런데 `openssl x509 -dates`로 본 리프는 유효 | 구형 OpenSSL 기반 클라이언트(curl·스크립트·임베디드) | [30](../30-x509-and-chain-validation/2-summary.md) · [52](../52-network-symptom-index/2-summary.md) |
| 같은 서버가 브라우저·최신 클라이언트에서는 정상 | 사용자 신고의 모양 | [30](../30-x509-and-chain-validation/2-summary.md) |
| `openssl s_client -showcerts`에 DST가 발급한 ISRG Root X1 사본이 보임 | 서버가 보내는 체인 | [30](../30-x509-and-chain-validation/2-summary.md) · [32](../32-mtls-and-cert-operations/2-summary.md) |
| 날짜 경계(2021-09-30)에 한꺼번에 시작 | 에러 시계열 | [32](../32-mtls-and-cert-operations/2-summary.md) |

### 사건 3 — Pakistan Telecom의 YouTube BGP 하이재킹 (2008-02-24)

#### 타임라인 (UTC, RIPE NCC RIS 사례 연구)

```text
  이전    YouTube(AS36561)가 208.65.152.0/22 광고
  18:47  Pakistan Telecom(AS17557)이 208.65.153.0/24 광고 시작
         PCCW Global(AS3491)이 이 광고를 전파
  20:07  YouTube가 같은 208.65.153.0/24 광고 시작                  (같은 길이로 경쟁)
  20:18  YouTube가 208.65.153.0/25, 208.65.153.128/25 광고 시작     (더 긴 접두사로 역전)
  20:51  하이재킹 접두사 광고에 17557이 한 번 더 붙어(prepend) 보임
  21:01  PCCW가 AS17557이 출발지인 접두사를 모두 철회
```

- 배경(RIPE): 파키스탄은 YouTube 웹사이트 차단을 목표로 했다. 당시 `youtube.com`의 DNS에는 IP가 셋 있었고, 모두 208.65.153.x였다.
- 그 차단용 경로가 **어떻게** 파키스탄 밖으로 나갔는지(내부용 경로가 새었다는 설명)는 널리 알려져 있으나, 이 노트가 읽은 RIPE 사례 연구에는 적혀 있지 않다 [?].

#### 메커니즘 — 최장 접두사 매칭

```text
  전 세계 라우터의 포워딩 테이블 (목적지 208.65.153.238)

    208.65.152.0/22  -> YouTube 방향       (22비트 일치)
    208.65.153.0/24  -> 파키스탄 방향       (24비트 일치)  <- 더 길다 -> 선택

  YouTube의 반격
    208.65.153.0/24  -> YouTube / 파키스탄  (같은 길이 -> BGP 선택 규칙으로 갈림)
    208.65.153.0/25  -> YouTube            (25비트 일치)  <- 가장 길다 -> (받은 라우터에서) 선택
    208.65.153.128/25 -> YouTube
```

- 라우터는 목적지에 맞는 경로 중 **가장 긴 접두사**를 쓴다(08번). BGP로 배운 경로도 같다(13번).
- 그래서 더 구체적인 광고 하나가, 원래 주인의 더 짧은 광고를 **이긴다**.
- 같은 /24로는 BGP 경로 선택(정책·AS_PATH 길이 등)에 따라 망마다 결과가 갈린다. /25는 그 광고를 **받은** 라우터에서는 길이로 이긴다(RIPE: "every router that receives these announcements").
- BGP는 기본적으로 "이 AS가 이 대역을 광고할 권한이 있나"를 검사하지 않는다. 상위 ISP(PCCW)가 고객 광고를 걸렀다면 퍼지지 않았다. RIPE의 교훈도 이것이다: 적절한 라우팅 설정으로 무단 광고의 확산을 막을 수 있다.
- 한계: RIPE RIS 관측에서 /25는 /24보다 훨씬 적게 퍼졌다. 사건 뒤 조회에서 /22는 RIS 피어 112곳, /24는 105곳이 봤지만 /25는 21곳만 봤다. 그래서 /25 반격이 모든 곳에 닿지는 않는다. 그 이유로 흔히 드는 "/24보다 긴 접두사를 거르는 관행"은 RIPE 글에 적혀 있지 않다 [?].

  - *하이재킹(hijack)*: 권한 없는 AS가 남의 대역을 광고해 트래픽을 끌어가는 것이다(13번).
  - *prepend*: AS_PATH에 자기 AS 번호를 일부러 더 붙여 경로를 길어 보이게 하는 것이다. 덜 선호되게 만드는 데 쓴다.

#### 밖에서 보인 신호

| 신호 | 어디서 보였나 | 연결 leaf |
|---|---|---|
| YouTube 접속 실패(연결 타임아웃 류) — 서버는 멀쩡 | 전 세계 사용자 | [52](../52-network-symptom-index/2-summary.md) · [15](../15-tcp-handshake-and-backlog/2-summary.md) |
| 외부 traceroute가 파키스탄 쪽으로 빠짐 | 외부 관측점 | [09](../09-icmp-ping-traceroute/2-summary.md) |
| 원래 /22보다 **더 구체적인** /24가 다른 출발 AS(17557)로 보임 | RIS 등 BGP 수집기 | [13](../13-routing-protocols-ospf-bgp/2-summary.md) · [08](../08-routing-and-longest-prefix-match/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **트라이와 최장 접두사 매칭** — YouTube 사건의 본체다. /24가 /22를, /25가 /24를 이긴 이유다. [data-structure/20-radix-trie](../../data-structure/20-radix-trie/2-summary.md) · [08](../08-routing-and-longest-prefix-match/2-summary.md)
- **그래프 경로 탐색과 백트래킹** — 인증서 체인은 "서명" 간선의 그래프다. 교차 서명으로 경로가 둘이 되면 만료 경로에서 되돌아와 다른 경로를 봐야 한다. OpenSSL 1.0.2는 상대가 준 경로를 우선해 그러지 못했다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [30](../30-x509-and-chain-validation/2-summary.md)
- **경로 벡터(BGP)** — 광고와 철회가 이웃을 따라 전 세계로 퍼진다. 광고를 끄는 순간 모든 경로에서 사라진다. [13](../13-routing-protocols-ospf-bgp/2-summary.md)
- **TTL 캐시** — Facebook 사건에서 리졸버 캐시가 만료되는 순서대로 해석 실패가 번졌다. 캐시는 장애를 **늦출** 뿐 막지 못한다. [28](../28-dns-caching-and-ttl/2-summary.md)
- **헬스체크 기반 제어 루프** — "내가 건강하지 않으면 나를 빼라"는 루프다. 각자 옳은 판단도 **모두가 동시에** 하면 전체가 사라진다. 전체 철회를 막는 하한(최소 유지 개수)이 필요하다.
- **재시도와 증폭** — 실패한 요청을 클라이언트들이 동시에 재시도해 질의량이 30배가 됐다. [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 사후 분석을 읽는 순서

```text
  1) 타임라인      관측 시각(누가 봤나)과 원인 시각을 구분한다
  2) 첫 사건        사슬의 처음 — 무엇이 바뀌었나 (명령·광고·만료)
  3) 증폭 지점      좋은 의도의 자동화·재시도·캐시 만료
  4) 보인 신호      밖에서 무엇으로 알 수 있었나 -> 52번 색인과 대조
  5) 복구를 늦춘 것  복구 도구의 의존성, 물리 접근, 부하 복귀
  6) 교훈          "누가 무엇을 바꿨나"가 아니라 "무엇이 그것을 막지 못했나"
```

### 2. 세 사건에서 내 시스템으로 옮길 점검 목록

- **Facebook 형**
  - 자동 철회·자동 격리 로직에 "전부 빠지는 것"을 막는 하한이 있나.
  - 권한 DNS가 한 망·한 사업자에만 있나. 서로 다른 망에 분산했나(27번).
  - 장애 대응 도구(원격 접속·대시보드·채팅·문서)가 장애 대상 망과 DNS에 의존하나.
  - 파괴적 명령에 감사 도구가 있다면, 그 감사 도구 자체를 시험하나.
  - 클라이언트 재시도에 지수 백오프·지터가 있나.
- **Let's Encrypt 형**
  - 체인 속 **모든** 인증서(중간·교차 서명 루트 포함)의 만료를 감시하나(30·32번).
  - 오래된 TLS 라이브러리(OpenSSL 1.0.x, 임베디드)를 쓰는 클라이언트 목록이 있나.
  - 클라이언트 쪽 트러스트 스토어를 갱신할 수 있나. 컨테이너 이미지의 CA 번들은 언제 갱신됐나.
- **YouTube 형**
  - 우리 대역의 ROA를 발행했나. 상위 ISP가 RPKI 출발지 검증을 하나(13번).
  - 우리 대역을 **지금** 어느 AS가 광고하는지 외부에서 감시하나(RIPEstat·BGP 감시 서비스).

### 3. 재현·확인 명령

```bash
# BGP: 대역을 누가 광고하나 (공개 조회 — RIPEstat Data API의 routing-status 예)
curl -s 'https://stat.ripe.net/data/routing-status/data.json?resource=208.65.152.0/22' | head

# DNS: 권한 서버 도달성 — 위임 사슬을 따라가 어디서 끊기나
dig +trace facebook.com
dig @a.ns.facebook.com facebook.com +norecurse     # 권한 서버에 직접

# TLS: 서버가 보내는 체인과 각 인증서의 발급자·만료
openssl s_client -connect example.com:443 -servername example.com -showcerts </dev/null \
  | grep -E '^ *[0-9]+ s:|^ *i:|NotAfter'

# 대처 2(-trusted_first)를 1.0.2 클라이언트에서 확인 — 1.1.0 이상에서는 이미 기본이라 결과가 같다
openssl verify -trusted_first -CAfile isrg-root-x1.pem -untrusted chain.pem leaf.pem
```

- RIPEstat `routing-status` 데이터 호출은 작성 시점(2026-09-30)에 응답하는 것을 확인했다. 결과는 RIS 수집기 기준이다.
- 명령별 상세는 [50-network-diagnostics](../50-network-diagnostics/2-summary.md)에서 다룬다.

## 장애 시나리오와 대처

### 1. "DNS 장애"로 보이지만 원인은 BGP — Facebook 형

- **현상**: 우리 서비스의 모든 도메인이 전 세계에서 동시에 해석되지 않는다. 서버·DNS 프로세스는 모두 살아 있다.
- **보이는 형태**
  - `dig`의 `status: SERVFAIL`. 공용 리졸버 전부에서 같다.
  - `dig @<권한 NS 주소>`가 타임아웃이다. 권한 NS 주소로 가는 외부 traceroute가 중간에서 끝난다.
  - BGP 수집기에서 우리 AS의 DNS 대역 광고가 사라졌다.
- **원인**: 권한 DNS 서버 대역의 BGP 경로가 철회됐다. Facebook에서는 백본 단절을 본 DNS 시설들이 자동으로 광고를 거뒀다.
- **대처**
  - SERVFAIL이면 "리졸버가 권한 서버에 못 닿았다"부터 확인한다. 권한 서버의 **도달성**(경로)과 **동작**(프로세스)을 따로 본다(27·13번).
  - 자동 철회에 하한을 둔다. 권한 DNS를 다른 망·사업자에 분산한다.

### 2. 장애 대상 망에 의존하는 복구 도구 — Facebook 형

- **현상**: 원인을 알았는데 고칠 수가 없다. 원격 접속·내부 대시보드·사내 메신저가 모두 안 된다.
- **보이는 형태**: 내부 도구의 로그인·이름 해석 실패. 담당자들이 연락 수단부터 찾는다.
- **원인**: 복구 경로가 장애 대상과 같은 DNS·백본에 의존했다. Meta는 "DNS 전체 소실이 내부 도구 다수를 망가뜨렸다"고 적었다. 현장 시설은 보안상 들어가기도 바꾸기도 어렵다.
- **대처**
  - 대역외(out-of-band) 접속 경로와 연락 수단을 따로 둔다. 단, Meta는 이번에 "주 접속과 대역외 접속이 모두 끊겼다"고 적었다. 대역외 경로가 장애 대상 망·DNS와 정말 독립인지 시험해야 한다. 이 대책은 일반론이고, Meta 글이 대책으로 명시한 것은 아니다.
  - 복구 절차를 "주 시스템이 전혀 없는 상태"에서 훈련한다. Meta의 storm 훈련이 부하 복귀에 도움이 됐다.

### 3. 리프는 유효한데 `certificate has expired` — Let's Encrypt 형

- **현상**: 2021-09-30부터 일부 서버 간 호출·임베디드 장비만 TLS 실패다. 브라우저는 정상이다.
- **보이는 형태**
  - OpenSSL·curl `certificate has expired`(검증 코드 10).
  - `openssl x509 -noout -dates`로 본 리프는 유효기간 안이다.
  - 실패하는 쪽의 OpenSSL 버전이 1.0.x다.
- **원인**: 체인 중 교차 서명 루트(DST Root CA X3)가 만료됐다. OpenSSL 1.0.2는 서버가 준 체인을 우선해 그 만료 경로를 골랐다. 다른 경로(자체 서명 ISRG Root X1)가 있었는데도 되돌아가지 않았다.
- **대처**
  - 클라이언트: 만료된 루트를 트러스트 스토어에서 지우고 새 루트를 넣는다. 또는 `X509_V_FLAG_TRUSTED_FIRST`를 켠다. 근본적으로 OpenSSL 1.1.0 이상으로 올린다.
  - 서버: 대체 체인을 쓸 수 있다. 대신 옛 Android 호환을 잃는다.
  - 감시: **체인 속 모든 인증서**의 notAfter를 감시한다(30번 장애 시나리오 2).

### 4. 특정 대역만 전 세계에서 도달 불가 — YouTube 형

- **현상**: 우리 서비스 IP 중 일부 대역만 많은 지역에서 접속되지 않는다. 서버는 정상이다.
- **보이는 형태**
  - 클라이언트는 connect 타임아웃. 우리 서버 캡처에는 SYN이 오지 않는다.
  - 외부 traceroute가 엉뚱한 국가·ISP로 빠진다.
  - BGP 수집기에 우리 대역보다 **더 구체적인** 접두사가 **다른 출발 AS**로 보인다.
- **원인**: 다른 AS가 더 구체적인 접두사를 광고했다. 최장 접두사 매칭으로 그 광고가 이긴다. 상위 ISP가 거르지 않았다.
- **대처**
  - 즉시: 같은 길이 또는 더 긴 접두사를 광고해 되찾는다(YouTube는 /24 → /25). 문제 AS의 상위 ISP에 연락한다(PCCW가 철회해 끝났다).
  - 평소: ROA 발행, 상위 ISP의 필터·RPKI 검증 확인, 외부 BGP 감시 경보(13번).

### 5. 재시도가 장애를 키운다 — Facebook 형의 바깥쪽

- **현상**: 한 서비스의 장애 동안 공용 리졸버·다른 서비스의 부하가 치솟는다.
- **보이는 형태**: 리졸버 질의량 30배(Cloudflare 관측). 다른 소셜 서비스로의 질의 증가.
- **원인**
  - 사용자 앱과 브라우저가 실패한 이름 해석과 요청을 공격적으로 재시도했다(Cloudflare).
  - 리졸버는 SERVFAIL을 캐시해도 되지만(MAY) 5분을 넘기면 안 된다(MUST NOT, RFC 2308 §7.1). 어느 쪽이든 클라이언트의 재시도 질의는 리졸버에 그대로 도착한다. 30배는 그 도착량이다.
- **대처**
  - 클라이언트 재시도에 지수 백오프·지터·상한을 둔다([ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)).
  - 리졸버 쪽은 serve-stale(RFC 8767)로 만료된 답을 더 줄 수 있다(28번). 최대 stale 타이머의 제안값이 1~3일이라(§5), 몇 시간짜리 장애도 시간상으로는 덮을 수 있다.
  - 한계는 시간이 아니라 조건이다. 장애 전에 그 리졸버 캐시에 있던 이름에만 통하고, 리졸버가 이 기능을 켰을 때만 동작한다(MAY, §4). 캐시에 없던 이름은 여전히 SERVFAIL이다.

## 핵심 문장

- 실사건은 메커니즘의 **사슬**이다. 증상은 사슬의 끝(DNS 실패·인증서 만료 에러·접속 불가)에서 보이고, 원인은 처음(명령·만료·광고)에 있다.
- Facebook 2021: 백본 점검 명령이 모든 연결을 끊었고, DNS 시설들이 스스로 BGP 광고를 거둬 권한 DNS가 인터넷에서 사라졌다. 서버는 살아 있었고 **길**이 없었다.
- 같은 자동화도 **모두가 동시에** 발동하면 전체 소멸이 된다. 자동 철회에는 하한이, 복구 도구에는 독립된 의존성이 필요하다.
- Let's Encrypt 2021: 인증서가 아니라 **경로 구축**이 문제였다. OpenSSL 1.0.2는 상대가 준 체인의 만료된 교차 서명 경로를 고르고 되돌아가지 않았다.
- YouTube 2008: 더 구체적인 접두사가 이긴다는 최장 접두사 매칭이, 권한 검사 없는 BGP와 만나 하이재킹이 됐다. 방어는 필터와 RPKI, 복구는 더 긴 접두사 광고였다.

## 관련 주제·근거

- 선행
  - [52-network-symptom-index](../52-network-symptom-index/2-summary.md) — 사건마다 보인 신호를 원인 leaf로 잇는 색인
  - [13-routing-protocols-ospf-bgp](../13-routing-protocols-ospf-bgp/2-summary.md) — BGP·하이재킹·Facebook 2021(장애 시나리오 1·2)
  - [27-dns-resolution](../27-dns-resolution/2-summary.md) · [28-dns-caching-and-ttl](../28-dns-caching-and-ttl/2-summary.md) — SERVFAIL, 캐시 만료, serve-stale
  - [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) — 교차 서명·경로 구축(§4)·만료(장애 시나리오 2)
  - [08-routing-and-longest-prefix-match](../08-routing-and-longest-prefix-match/2-summary.md) — 최장 접두사 매칭
- 연결
  - [32-mtls-and-cert-operations](../32-mtls-and-cert-operations/2-summary.md) — 만료 감시·인벤토리
  - [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)
  - [50-network-diagnostics](../50-network-diagnostics/2-summary.md) — 재현·확인 명령 상세
- Facebook 2021-10-04
  - Meta Engineering, "Update about the October 4th outage"(2021-10-04) <https://engineering.fb.com/2021/10/04/networking-traffic/outage/>
  - Meta Engineering, "More details about the October 4 outage"(2021-10-05) — 백본 명령·감사 도구 버그·DNS의 BGP 광고 해제·내부 도구·현장 접근·전력·storm 훈련 <https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/>
  - Cloudflare, "Understanding how Facebook disappeared from the Internet"(2021-10-04) — UTC 타임라인, AS32934, DNS 대역, 1.1.1.1 질의 30배 <https://blog.cloudflare.com/october-2021-facebook-outage/>
- Let's Encrypt DST Root CA X3 만료
  - Let's Encrypt, "DST Root CA X3 Expiration (September 2021)" — 영향받는 클라이언트, OpenSSL 1.0.x, 대처 <https://letsencrypt.org/docs/dst-root-ca-x3-expiration-september-2021/>
  - Let's Encrypt, "Extending Android Device Compatibility for Let's Encrypt Certificates"(2020-12-21) — Android의 신뢰 앵커 notAfter 무시, 7.1.1 미만 <https://letsencrypt.org/2020/12/21/extending-android-compatibility/>
  - Let's Encrypt, "Shortening the Let's Encrypt Chain of Trust"(2023-07-10) — 2024-02-08 기본 체인 변경, 2024-09-30 교차 서명 만료, Android 66%→93.9% <https://letsencrypt.org/2023/07/10/cross-sign-expiration.html>
  - OpenSSL, "Old Let's Encrypt Root Certificate Expiration and OpenSSL 1.0.2"(2021-09-13) — untrusted 체인 우선 동작, 대처 셋 <https://openssl-library.org/post/2021-09-13-letsencryptrootcertexpire/>
- Pakistan Telecom–YouTube 2008-02-24
  - RIPE NCC, "YouTube Hijacking: A RIPE NCC RIS case study"(2008) — UTC 타임라인, AS·접두사, 교훈 <https://www.ripe.net/publications/news/industry-developments/youtube-hijacking-a-ripe-ncc-ris-case-study>
- RFC 5280 §6.1(경로 검증 — 구축은 범위 밖) <https://www.rfc-editor.org/rfc/rfc5280> · RFC 4271(BGP-4) <https://www.rfc-editor.org/rfc/rfc4271> · RFC 6811(출발지 검증) <https://www.rfc-editor.org/rfc/rfc6811> · RFC 8767(serve-stale — §4 MAY, §5 최대 stale 타이머 1~3일 제안) <https://www.rfc-editor.org/rfc/rfc8767> · RFC 2308 §7.1(SERVFAIL 캐시 5분 상한) <https://www.rfc-editor.org/rfc/rfc2308>
