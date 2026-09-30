# network/29-tls-handshake — TLS 1.3 핸드셰이크: 1-RTT·0-RTT, 1.2와의 차이, SNI·ALPN — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

TCP는 바이트를 순서대로 옮길 뿐이다.\
중간에서 누가 읽어도, 고쳐도, 상대인 척해도 막지 못한다.\
TLS는 그 위에 세 가지를 얹는다.

```text
  기밀성    : 중간자가 내용을 못 읽는다          (대칭키 암호화, AEAD)
  무결성    : 중간에서 바꾸면 들킨다             (AEAD 태그)
  인증      : 내가 말하는 상대가 진짜 그 서버다   (인증서 + 서명)
```

문제는 두 사람이 **처음 만났다**는 것이다.\
공유한 비밀키가 없다.\
핸드셰이크는 "도청되는 길 위에서 비밀키를 합의하고, 상대가 진짜인지 확인하는" 짧은 대화다.

쉬운 예: 처음 거래하는 가게와 전화로 계좌를 주고받는 상황이다.\
먼저 신분증(인증서)을 확인한다.\
둘만 아는 암호(세션 키)를 정한다.\
그 뒤 대화는 그 암호로 한다.\
암호를 정하는 대화 자체가 도청돼도 암호가 새지 않아야 한다.

똑같은 구조다.\
TLS 핸드셰이크 = 신분 확인 + 키 합의 + "지금까지 대화가 조작되지 않았다"는 확인.

실무 예:
- HTTPS 새 연결의 첫 요청에는 TCP 연결과 TLS 핸드셰이크 왕복이 먼저 붙는다. RTT가 긴 구간일수록 이 비용이 눈에 띈다.
- 한 IP에 도메인 수십 개를 올린 서버(가상 호스팅)는 "어느 도메인 인증서를 줄지"를 핸드셰이크 중에 알아야 한다(SNI).
- HTTP/2를 쓸지 HTTP/1.1을 쓸지도 핸드셰이크에서 정한다(ALPN).

## 동작·원리

### 1. TLS 1.3 전체 핸드셰이크 — 1-RTT

RFC 8446 Figure 1을 줄인 그림이다.

```text
  Client                                              Server
  ClientHello                                                           --+
    + supported_versions (1.3, 1.2 ...)                                   |
    + key_share     (내 ECDHE 공개값)                                      |  1 RTT
    + signature_algorithms                                                |
    + server_name (SNI), ALPN            -------->                        |
                                                       ServerHello        |
                                                       + key_share        |
                                          -- 여기부터 암호화 ({} 표시) --    |
                                          {EncryptedExtensions}  (ALPN)   |
                                          {Certificate}                   |
                                          {CertificateVerify}             |
                                          {Finished}                      |
                                         <--------  [Application Data*] --+
  {Finished}                             -------->
  [Application Data]                     <------->   [Application Data]

  {} = 핸드셰이크 트래픽 키로 암호화     [] = 애플리케이션 트래픽 키로 암호화
```

그림 해설:

- **ClientHello 한 번에 키 재료까지 보낸다.**
  - 클라이언트는 서버가 고를 만한 그룹(예: X25519)을 추측한다. 그리고 그 그룹의 공개값을 `key_share`에 미리 넣는다.
  - 서버는 `ServerHello`에 자기 공개값을 담아 답한다. 이 순간 양쪽이 같은 공유 비밀을 계산할 수 있다.
  - *ECDHE*: 타원곡선 위의 임시(ephemeral) Diffie-Hellman이다. 공개값만 교환해도 양쪽이 같은 비밀을 얻는다. 도청자는 그 비밀을 계산할 수 없다. 원리는 security/07에서 다룬다.
- **ServerHello 뒤 모든 핸드셰이크 메시지는 암호화된다**(RFC 8446 §1.2).
  - 인증서도 암호화되어 간다. TLS 1.2에서는 평문이었다.
  - *EncryptedExtensions*: 암호 파라미터 결정에 필요 없는 확장 응답(ALPN 결과 등)을 담는 메시지다. 1.3에서 새로 생겼다.
- **CertificateVerify**: 서버가 "지금까지의 핸드셰이크 전체"에 인증서 개인키로 서명한 것이다. 인증서의 주인이 지금 이 대화 상대임을 증명한다(§4.4.3).
- **Finished**: 지금까지 주고받은 메시지 전체에 대한 MAC이다(§4.4.4).
  - 중간에서 ClientHello의 목록 하나라도 바꿨다면 양쪽 값이 달라진다.
  - 실제 실패는 더 일찍 날 수도 있다. 핸드셰이크 키가 이미 달라졌다면 첫 암호화 레코드부터 복호가 안 된다(`bad_record_mac`, §5.2).
  - *MAC(메시지 인증 코드)*: 공유 키로 만든 "변조 검사용 태그"다. TLS는 HMAC을 쓴다. [HMAC 노트](../../foundations/security/hmac.md) 참고.
- 클라이언트는 서버의 첫 응답을 받은 직후, 즉 **1 RTT 뒤** 자기 Finished와 함께 요청을 보낼 수 있다.

  - *RTT(Round-Trip Time)*: 패킷이 갔다가 응답이 돌아오는 데 걸리는 시간이다.

**추측이 틀리면 — HelloRetryRequest**(RFC 8446 §2.1, §4.1.4)

```text
  ClientHello (key_share: X25519) -------->   서버: "그 그룹 말고 P-256으로"
                <--------  HelloRetryRequest (P-256 요구)
  ClientHello (key_share: P-256)  -------->   이제 정상 진행            => +1 RTT
```

- 서버가 받아들일 파라미터는 있지만, ClientHello의 정보만으로는 진행할 수 없을 때 보낸다(§4.1.4).
- 한 연결에서 HRR을 두 번 받으면 클라이언트는 `unexpected_message`로 끊는다(§4.1.4).

### 2. TLS 1.2 전체 핸드셰이크 — 2-RTT

RFC 5246 Figure 1이다.

```text
  Client                                         Server
  ClientHello                  -------->                       --+
                                                ServerHello      |  RTT 1
                                                Certificate      |  (평문)
                                          ServerKeyExchange      |
                               <--------    ServerHelloDone    --+
  ClientKeyExchange                                            --+
  [ChangeCipherSpec]                                             |  RTT 2
  Finished                     -------->                         |
                                         [ChangeCipherSpec]      |
                               <--------           Finished    --+
  Application Data             <------->   Application Data
```

- 1.2에서는 서버가 무엇을 고를지 먼저 들어야 키 교환 값을 보낼 수 있다. 그래서 왕복이 하나 더 든다.
  - `TLS_RSA_…` 암호군이면 클라이언트가 pre-master secret을 서버 인증서의 RSA 공개키로 암호화해 보낸다(RFC 5246 §7.4.7.1). 이것이 "정적 RSA 키 전송"이다.
- 1.3은 "클라이언트가 추측해서 미리 보낸다"로 한 왕복을 줄였다.

1.2 → 1.3 주요 차이(RFC 8446 §1.2):

```text
  항목                  TLS 1.2                              TLS 1.3
  전체 핸드셰이크        2-RTT                                1-RTT (HRR 시 2-RTT)
  재개                  세션 ID/티켓, 1-RTT                    PSK, 1-RTT 또는 0-RTT
  키 교환               RSA 키 전송 가능 (전방 비밀성 없음)      (EC)DHE · PSK 단독 · PSK+(EC)DHE
                                                             (정적 RSA·DH 제거)
  암호군 이름            키교환+인증+암호+해시                  AEAD 암호 + 해시만
                        TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 TLS_AES_128_GCM_SHA256
  암호                  CBC·RC4 등 포함                      AEAD만 (정의된 암호군 5개, 부록 B.4)
  인증서                평문으로 전송                         암호화해서 전송
  버전 협상              ClientHello.version 필드              supported_versions 확장
                                                             (legacy_version은 0x0303 고정)
  키 유도               PRF                                  HKDF
  ChangeCipherSpec      필수 메시지                           제거 (중간 장비 호환용 더미만, 부록 D.4)
```

- 1.3 암호군 이름에는 키 교환·서명이 없다. 키 교환은 `supported_groups`/`key_share`, 서명은 `signature_algorithms`로 따로 협상한다.
  - 1.3 암호군 5개: `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`, `TLS_AES_128_CCM_SHA256`, `TLS_AES_128_CCM_8_SHA256`(부록 B.4).
- **전방 비밀성의 범위**: RFC 8446 §1.2의 표현은 "모든 **공개키 기반** 키 교환이 전방 비밀성을 가진다"다.
  - PSK 단독 모드(`psk_ke`)는 (EC)DHE를 섞지 않는다. 그래서 애플리케이션 데이터의 전방 비밀성이 없다(§2.2, §4.2.9).
  - 재개에 전방 비밀성이 필요하면 `psk_dhe_ke`(PSK + (EC)DHE)를 쓴다.

  - *전방 비밀성(forward secrecy)*: 장기 비밀(서버 개인키 등)이 나중에 유출돼도, 과거에 녹음해 둔 트래픽을 풀 수 없는 성질이다. 연결마다 임시 키를 쓰고 버려서 얻는다.
  - *AEAD*: 암호화와 무결성 검사를 한 번에 하는 암호 방식이다. security/03에서 다룬다.

**왜 버전 필드를 1.2로 고정했나**

```text
  ClientHello  legacy_version = 0x0303 (1.2처럼 보임)
               supported_versions = [0x0304 (1.3), 0x0303]   <- 진짜 협상은 여기서
  ServerHello  legacy_version = 0x0303
               supported_versions = 0x0304                   <- "1.3으로 간다"
```

- 예전 방식(버전 필드에 최고 버전)은 많은 서버가 제대로 처리하지 못했다. 모르는 높은 버전을 보면 거절했다("version intolerance", §4.1.2).
- 중간 장비(미들박스)도 새 값을 보면 연결을 깨뜨렸다(§4.1.3).
- 그래서 겉은 1.2처럼 두고, 확장으로 진짜 버전을 협상한다(§4.2.1).
- 같은 이유로 "미들박스 호환 모드"는 1.3 핸드셰이크를 1.2처럼 보이게 더미 ChangeCipherSpec 등을 넣는다(부록 D.4).

### 3. 재개와 0-RTT

첫 연결이 끝날 무렵 서버는 **NewSessionTicket**을 보낸다(§4.6.1).\
다음 연결에서 클라이언트는 그 티켓에서 나온 PSK를 `pre_shared_key`로 제시한다.

  - *PSK(Pre-Shared Key)*: 미리 공유한 키다. 1.3에서는 이전 연결에서 유도한 재개용 비밀도 PSK로 다룬다.

```text
  PSK 재개의 두 모드 (psk_key_exchange_modes, §4.2.9)
    psk_ke      PSK만            -> 새 키 교환 없음, 애플리케이션 데이터 전방 비밀성 없음
    psk_dhe_ke  PSK + (EC)DHE    -> 새 ECDHE가 섞임, 전방 비밀성 있음
```

- 재개가 곧 0-RTT는 아니다. 0-RTT(early data)는 양쪽이 PSK를 공유할 때 **선택적으로** 얹는 기능이다(§2.3).
  - PSK는 이전 연결의 재개 PSK일 수도, 외부에서 미리 받은 PSK일 수도 있다. 이 노트는 흔한 재개 PSK 경우를 그린다.

```text
  Client                                                Server
  ClientHello
    + early_data, + pre_shared_key, + key_share
  (Application Data)   <- 0-RTT 데이터: 첫 비행에 요청을 실어 보냄
                                  -------->
                                                   ServerHello + pre_shared_key
                                                   {EncryptedExtensions + early_data}
                                                   {Finished}
                                  <--------        [Application Data]
  (EndOfEarlyData)
  {Finished}                      -------->
```

(RFC 8446 Figure 4. `()`는 early 트래픽 키로 보호)

- 0-RTT 데이터는 **왕복을 기다리지 않고** 첫 패킷에 실린다.
- 대가가 두 가지 있다(§2.3 IMPORTANT NOTE).
  - **전방 비밀성이 없다.** 0-RTT 데이터는 PSK에서 유도한 키로만 암호화된다.
  - **연결 간 재전송(replay) 보호가 없다.** 1-RTT 데이터는 서버 Random이 섞여서 연결마다 키가 달라진다. 0-RTT 데이터는 ServerHello 전에 보내므로 그 보호를 못 받는다.

```text
  재전송 공격
  공격자: 클라이언트의 [ClientHello + 0-RTT "송금 100만원"]을 녹화
          --> 서버에 그대로 다시 보냄 --> 서버가 한 번 더 처리할 수 있다
```

- RFC 8446 §8의 대처
  - 서버의 각 인스턴스는 같은 0-RTT 핸드셰이크를 최대 한 번만 받아야 한다(MUST). 방법 예: 단일 사용 티켓(§8.1), ClientHello 기록(§8.2).
  - 인스턴스 사이까지 공유 상태로 막는 것은 SHOULD다. 그래서 여러 인스턴스·지역에 걸친 중복은 남을 수 있다.
  - 그래서 클라이언트는 **재전송돼도 안전하다고 판단한 데이터만** 0-RTT로 보내야 한다(MUST).
- HTTP에서는 RFC 8470이 규칙을 정했다.
  - 클라이언트는 다른 정보가 없으면 **safe 메서드**(GET·HEAD 등)만 early data로 보낼 수 있다. unsafe이거나 safe인지 모르는 메서드는 보내면 안 된다(MUST NOT, §4).
  - safe 메서드라도 부작용이 있는 자원이 있으니, 원 서버는 자원별로 판단한다(§3).
  - 프록시는 `Early-Data: 1` 헤더를 붙여 원 서버에 알린다(§5.1).
  - 원 서버는 위험하면 `425 Too Early`로 거절한다(§5.2).
- nginx는 `ssl_early_data`의 기본값이 `off`다.

### 4. 키는 어떻게 만들어지나 — HKDF 키 스케줄

RFC 8446 §7.1 그림을 줄인 것이다.

```text
          0
          |
  PSK --> HKDF-Extract = Early Secret ------> client_early_traffic_secret  (0-RTT 키)
          |
     Derive-Secret(., "derived", "")   <- 빈 문자열의 해시
          |
  (EC)DHE --> HKDF-Extract = Handshake Secret -> {c,s} handshake_traffic_secret  ({} 키)
          |
     Derive-Secret(., "derived", "")
          |
  0 -----> HKDF-Extract = Master Secret ----> {c,s} application_traffic_secret_0 ([] 키)
                                               resumption_master_secret (다음 PSK)
```

- 비밀은 층층이 쌓인다. 새 비밀(PSK, ECDHE 결과)이 들어올 때마다 Extract로 섞는다.
  - 없는 입력은 0으로 채운다. PSK가 없으면 PSK 자리가, `psk_ke`면 (EC)DHE 자리가 0이다. 단계를 건너뛰지는 않는다.
- transcript 해시가 들어가는 곳은 **Extract가 아니라 Derive-Secret**이다.
  - 각 traffic secret은 "그 시점까지의 메시지"의 해시로 뽑는다. 범위는 비밀마다 다르다.
  - 단계 사이를 잇는 `derived`와 binder 키는 빈 문자열("")의 해시를 쓴다.

| 비밀 | Derive-Secret에 넣는 transcript | 보호하는 것 |
|---|---|---|
| client_early_traffic_secret | ClientHello | 0-RTT 데이터 `()` |
| {c,s} handshake_traffic_secret | ClientHello … ServerHello | 핸드셰이크 메시지 `{}` |
| {c,s} application_traffic_secret_0 | ClientHello … server Finished | 애플리케이션 데이터 `[]` |
| resumption_master_secret | ClientHello … client Finished | 다음 연결의 PSK 재료 |
| binder_key, derived | ""(빈 문자열) | PSK binder / 다음 단계로 잇기 |

- 그래서 ClientHello·ServerHello가 바뀌면 handshake 키부터 달라진다. Finished·CertificateVerify는 더 넓은 범위를 확인한다.
  - *transcript 해시*: 지금까지 주고받은 핸드셰이크 메시지를 이어 붙여 해시한 값이다(§4.4.1).

### 5. SNI와 ALPN — ClientHello에 붙는 두 이름표

```text
  ClientHello
    server_name = "api.example.com"      <- SNI: "이 도메인 인증서를 주세요"
    alpn        = ["h2", "http/1.1"]     <- ALPN: 지원하는 앱 프로토콜 목록

  서버(한 IP, 도메인 여러 개)
    SNI로 인증서 선택  -->  Certificate(api.example.com)
    ALPN 중 하나 선택  -->  EncryptedExtensions(alpn = "h2")
```

- **SNI(Server Name Indication, RFC 6066 §3)**
  - TCP 연결은 IP:포트만 안다. 인증서를 고를 시점에 HTTP `Host` 헤더는 아직 안 왔다.
  - 그래서 ClientHello에 호스트 이름을 담는다.
  - IP 주소 리터럴은 넣을 수 없다.
  - 서버가 이름을 모르면 두 가지 중 하나를 한다(SHOULD): 치명 `unrecognized_name`(112)로 끊거나, 그냥 진행한다(기본 인증서 등).
  - TLS 1.3에서 `server_name`은 구현 필수 확장이다(§9.2).
    - 서버는 SNI를 요구할 수 있다(MAY). 그래서 클라이언트는 해당되면 보내야 한다(SHOULD, §4.4.2.2).
    - SNI를 요구하는 서버는 SNI 없는 ClientHello에 `missing_extension`(109)으로 끊는 것이 권장이다(SHOULD, §9.2).
  - SNI는 ClientHello에 **평문**으로 실린다. 이를 암호화하는 ECH(Encrypted Client Hello)가 RFC 9849로 나왔다.
- **ALPN(Application-Layer Protocol Negotiation, RFC 7301)**
  - 클라이언트가 지원 목록을 보낸다.
  - 서버는 **자기 선호 순서**로, 클라이언트도 지원하는 것 중 가장 앞선 것을 고른다(SHOULD, §3.2).
  - ALPN을 지원하는 서버에서 겹치는 게 없으면 치명 alert `no_application_protocol`(120)을 보낸다(SHALL, §3.2).
  - 서버가 ALPN을 아예 처리하지 않으면 응답에 ALPN이 없다. 이때는 "협상 안 됨"이다.
  - HTTP/2를 쓸지가 여기서 정해진다. 추가 왕복은 없다.

### 6. 실패하면 — alert

핸드셰이크가 실패하면 연결을 끊는다. 그 전에 alert 메시지로 이유를 알릴 수 있다(§6).

```text
  alert(번호)                     언제 (RFC 8446 §6.2)
  unexpected_message(10)         순서에 맞지 않는 메시지 (예: HRR 두 번)
  bad_record_mac(20)             레코드 복호 실패 (키가 어긋남)
  handshake_failure(40)          받아들일 파라미터 집합을 못 찾음 (암호군·그룹 등)
  illegal_parameter(47)          필드가 틀렸거나 다른 필드와 모순
  decrypt_error(51)              서명·Finished·PSK binder 검증 실패
  protocol_version(70)           버전은 알지만 지원 안 함 (예: 1.3 전용 서버에 1.2 클라이언트)
  insufficient_security(71)      서버가 더 강한 파라미터를 요구
  missing_extension(109)         필수 확장이 없음 (예: SNI를 요구하는 서버)
  unrecognized_name(112)         SNI의 이름에 해당하는 서버가 없음
  certificate_required(116)      서버가 클라이언트 인증서를 요구했는데 없음 (mTLS, 32번)
  no_application_protocol(120)   ALPN 목록이 안 겹침
  unknown_ca(48) 등               인증서 검증 실패 (30번 노트)
  close_notify(0)                "더 보낼 것 없음" — 정상 종료 알림 (잘림 공격 방지)
```

- 진단은 **누가 보냈나**부터 본다.
  - 서버가 보냈다 = 서버가 내 제안을 거절했다.
  - 클라이언트가 보냈다 = 클라이언트가 서버 응답(인증서 등)을 거절했다.
- 실제 구현이 어느 alert를 고르는지는 제각각이다. 이름만으로 원인을 단정하지 않는다.

## 쓰이는 자료구조·알고리즘

- **핸드셰이크 상태 기계** — 클라이언트·서버가 각각 "다음에 올 수 있는 메시지"를 제한하는 FSM을 가진다(RFC 8446 Appendix A).
  - 클라이언트 예: START → WAIT_SH → WAIT_EE → WAIT_CERT_CR → WAIT_CV → WAIT_FINISHED → CONNECTED.
  - 순서가 틀린 메시지가 오면 `unexpected_message` alert로 끊는다.
  - 이 표를 느슨하게 구현하면 메시지를 건너뛰는 공격이 된다. 유명한 예가 SMACK(State Machine AttaCKs, IEEE S&P 2015 "A Messy State of the Union")이다.
- **HKDF(Extract-and-Expand)** — HMAC 위에 세운 키 유도 함수다(RFC 5869).
  - Extract는 엔트로피를 고른 키로 압축한다.
  - Expand는 라벨과 문맥을 넣어 필요한 만큼 키를 뽑는다.
  - TLS 1.3의 키는 이 사슬로 나온다(§7.1). [HMAC 노트](../../foundations/security/hmac.md) 참고.
- **transcript 해시(연쇄 해시)** — 핸드셰이크 메시지를 누적해 해시한다(§4.4.1). Finished·CertificateVerify·Derive-Secret이 이 값을 쓴다. 변조 검출과 키 분리를 동시에 한다.
- **(EC)DH 키 합의** — 타원곡선 스칼라 곱셈. security/07에서 다룬다.
- **선호 순 목록 교집합** — 암호군·그룹·ALPN 협상은 모두 "클라이언트 목록 ∩ 서버 목록"에서 한쪽 선호 순으로 고르는 문제다.
- **0-RTT 재전송 방지용 기록** — 최근 ClientHello를 저장해 중복을 거절한다(§8.2).
  - 시간 창으로 크기를 제한한 집합이다.
  - RFC는 거짓 양성이 있는 저장소(블룸 필터 등)도 허용한다.
  - 거짓 양성이면 **0-RTT만 거절하고 핸드셰이크는 계속한다**(MUST). 핸드셰이크를 중단하면 안 된다(MUST NOT). 그러면 PSK 재개 1-RTT로 진행되고, 요청은 그 뒤에 다시 온다.
- **세션 티켓 캐시** — 클라이언트는 호스트(SNI)별로 티켓을 저장해 재개에 쓴다. 키-값 맵이다.

## 적용 — 풀어나가는 법

### 1. 연결 비용을 셈한다

```text
  새 연결 HTTPS 요청의 왕복 수 (DNS 제외, TLS 1.2 False Start·TCP Fast Open 제외, 대략)
  TCP 3-way            1 RTT
  + TLS 1.2 전체        2 RTT    -> 요청 전송까지 3 RTT
  + TLS 1.3 전체        1 RTT    -> 2 RTT
  + TLS 1.3 0-RTT 재개   0 RTT    -> 1 RTT (TCP만)
```

RTT가 100ms(예시)면 1.2 → 1.3 전환만으로 첫 요청이 약 100ms 빨라진다.\
그래도 가장 큰 절약은 **연결을 재사용**하는 것이다. keep-alive와 커넥션 풀이 그 방법이다(35번).

### 2. 핸드셰이크를 눈으로 본다

```bash
# 협상된 버전·암호군 요약 (-brief는 ALPN을 출력하지 않는다)
openssl s_client -connect api.example.com:443 -brief </dev/null

# ALPN 결과는 일반 출력의 "ALPN protocol:" 줄에서 본다
openssl s_client -connect api.example.com:443 -alpn h2,http/1.1 </dev/null | grep ALPN

# 버전·암호군을 고정해 서버가 받는지 확인
openssl s_client -connect api.example.com:443 -tls1_2 -cipher 'ECDHE-RSA-AES128-GCM-SHA256' </dev/null
openssl s_client -connect api.example.com:443 -tls1_3 -ciphersuites TLS_AES_128_GCM_SHA256 </dev/null

# SNI를 빼고 연결 -> 어떤 기본 인증서가 오나
openssl s_client -connect 203.0.113.10:443 -noservername -showcerts </dev/null

# 메시지 단위 흐름과 상태 전이
openssl s_client -connect api.example.com:443 -msg -state </dev/null

# 재개·0-RTT 시험 — 1.3 티켓은 핸드셰이크 뒤에 오므로 stdin EOF로 바로 끊기지 않게 한다
printf 'GET / HTTP/1.1\r\nHost: host\r\nConnection: close\r\n\r\n' \
  | openssl s_client -connect host:443 -sess_out s.pem
openssl s_client -connect host:443 -sess_in s.pem -early_data req.txt

# curl로 핸드셰이크 단계와 ALPN 결과 보기
curl -v https://api.example.com/ 2>&1 | grep -E 'TLS|ALPN|SSL connection'
```

- `-cipher`는 TLS 1.2 이하 암호 목록이다. TLS 1.3 암호군은 `-ciphersuites`로 정한다(OpenSSL `s_client` 문서).
- `s_client`는 stdin이 끝나면 연결을 일찍 닫을 수 있다. 특히 TLS 1.3에서 그렇다. 세션을 저장하려면 요청을 보내 서버가 닫게 하거나, `-ign_eof`를 쓴다(문서 "Note on Non-Interactive Use"). 저장 뒤 `-sess_in`으로 붙어 `Reused` 표시를 확인한다.
- `openssl s_client`는 `-servername`을 주지 않아도, `-connect`의 호스트가 DNS 이름이면 SNI를 채운다. OpenSSL 1.1.1부터의 기본 동작이다. IP로 연결하면 SNI가 빠진다.

실패를 읽는 순서:

```text
  1) 어느 단계에서 끊겼나?   -msg -state 로 마지막 메시지 확인 (ClientHello 직후? Certificate 뒤?)
  2) 어떤 alert인가?         handshake_failure / protocol_version / unrecognized_name / no_application_protocol ...
  3) 누가 보냈나?            서버 alert = 서버가 내 제안 거절 / 클라이언트 alert = 내가 서버 응답 거절
  4) 교집합을 맞춘다          버전·암호군·그룹·ALPN 목록을 양쪽에서 출력해 비교
```

### 3. 코드에서

Java — 핸드셰이크 로그와 버전 제한.

```java
// JVM 옵션: -Djavax.net.debug=ssl:handshake   (핸드셰이크 메시지 로그)
SSLParameters p = new SSLParameters();
p.setProtocols(new String[] {"TLSv1.3", "TLSv1.2"});
p.setApplicationProtocols(new String[] {"h2", "http/1.1"});   // ALPN (Java 9+)
p.setServerNames(List.of(new SNIHostName("api.example.com"))); // SNI 명시
p.setEndpointIdentificationAlgorithm("HTTPS");                  // 호스트명 검증 켜기
sslSocket.setSSLParameters(p);
sslSocket.startHandshake();
System.out.println(sslSocket.getSession().getProtocol()          // "TLSv1.3"
    + " " + sslSocket.getApplicationProtocol());                  // "h2"
```

Node.js — `servername`은 호스트 이름이어야 한다(IP 불가).

```js
const tls = require('node:tls');
const sock = tls.connect({
  host: '203.0.113.10', port: 443,
  servername: 'api.example.com',        // SNI. IP로 붙더라도 이름을 따로 준다
  ALPNProtocols: ['h2', 'http/1.1'],
}, () => {
  console.log(sock.getProtocol(), sock.alpnProtocol, sock.isSessionReused());
});
sock.on('error', (e) => console.error(e.code, e.message));
```

### 4. 서버 설정의 순서

1. 버전 하한을 정한다. 예: nginx `ssl_protocols TLSv1.2 TLSv1.3;` — 현재 nginx 기본값과 같다(TLSv1.3이 기본에 든 것은 1.23.4부터).
2. 가상 호스트마다 인증서를 연결한다.
   - SNI가 없거나 모르는 이름이면 기본 서버의 인증서가 나간다(nginx 문서).
   - 이를 막으려면 `ssl_reject_handshake on`인 `default_server`를 둔다.
3. ALPN으로 HTTP/2를 켠다.
4. 0-RTT는 재전송돼도 안전한 요청만 early data로 처리할 수 있을 때만 켠다. 켜면 `Early-Data` 헤더를 원 서버로 넘긴다(nginx `$ssl_early_data`, RFC 8470).

## 장애 시나리오와 대처

### 1. 버전·암호군 불일치 — 핸드셰이크 즉시 실패

- **현상**: 특정 클라이언트(오래된 JDK·임베디드 장비)만 연결이 안 된다.
- **보이는 형태**
  - Java `javax.net.ssl.SSLHandshakeException: Received fatal alert: handshake_failure` 또는 `protocol_version`
  - `openssl s_client` 출력의 `alert handshake failure`
  - OpenSSL 기반 서버 로그의 `no shared cipher`(OpenSSL 에러 사유 `SSL_R_NO_SHARED_CIPHER`)
- **원인**
  - 서버가 TLS 1.0/1.1을 껐는데 클라이언트가 그것만 지원한다. RFC상 이 경우는 `protocol_version`(70)이다.
  - 또는 공통 암호군·그룹·서명 알고리즘이 없다. 이 경우 서버는 `handshake_failure`(40) 또는 `insufficient_security`(71)로 중단한다(MUST, RFC 8446 §4.1.1).
  - 실제 구현이 어느 alert를 보내는지는 제각각이라, 로그의 alert 이름만으로 단정하지 않는다.
- **대처**
  - `openssl s_client -tls1_2 -cipher …` / `-tls1_3 -ciphersuites …`로 서버가 받는 조합을 확인한다.
  - 클라이언트는 `-Djavax.net.debug=ssl:handshake`로 제안 목록을 본다.
  - 클라이언트 런타임을 올리는 것이 우선이다.
  - 서버 하한을 낮추는 것은 보안 후퇴이므로 기한을 정해 예외로만 둔다.

### 2. SNI 누락 — 엉뚱한(기본) 인증서가 올 수 있다

- **현상**: 브라우저에서는 되는데 특정 클라이언트·스크립트에서만 "인증서 이름이 다르다"로 실패한다.
- **보이는 형태**
  - Java `CertificateException: No subject alternative DNS name matching api.example.com found.`
  - Node `ERR_TLS_CERT_ALTNAME_INVALID`
  - curl(OpenSSL 백엔드) `SSL: no alternative certificate subject name matches target hostname 'api.example.com'`
  - `openssl s_client -noservername`으로 재현하면 다른 도메인 인증서가 보인다.
- **원인**
  - 클라이언트가 SNI를 보내지 않았다. 흔한 경우는 IP로 접속했거나, 라이브러리에 호스트 이름을 넘기지 않은 것이다.
  - 서버가 어느 가상 호스트인지 몰라 기본 인증서를 줬다(nginx 문서).
  - 그 인증서에 대상 이름이 없으면 클라이언트의 호스트명 검증이 실패한다.
  - SNI 누락이 곧 실패는 아니다. 기본 인증서에 대상 이름이 들어 있으면 성공한다. 서버가 SNI를 요구하면 인증서 검증 전에 alert로 끊긴다.
- **대처**
  - 클라이언트가 이름으로 접속하게 한다. 또는 SNI를 명시한다(Node `servername`, Java `SNIHostName`).
  - 서버는 기본 서버에서 `ssl_reject_handshake on`으로 이름 없는 핸드셰이크를 명확히 거절한다. 원인이 alert로 일찍 드러난다.

### 3. 0-RTT 재전송 — 요청이 두 번 처리된다

- **현상**: 0-RTT를 켠 뒤 결제·주문이 드물게 두 번 생긴다.
- **보이는 형태**
  - 같은 요청이 짧은 간격으로 두 번 로그에 찍힌다(서로 다른 인스턴스일 수 있다).
  - 그중 하나는 early data로 들어왔다(nginx `$ssl_early_data` = `1`).
- **원인**
  - 0-RTT 데이터는 TLS 층에서 연결 간 재전송 보호가 없다(§2.3).
  - 공격자의 재전송이나 클라이언트의 재시도가 같은 요청을 서버 여러 인스턴스에 전달했다(§8).
- **대처**
  - 클라이언트·프록시는 safe 메서드만 early data로 보낸다(RFC 8470 §4). safe여도 부작용이 있는 자원은 제외한다(§3).
  - 원 서버는 위험한 요청이 early data로 오면 `425 Too Early`로 돌려보낸다(RFC 8470 §5.2).
  - 근본적으로는 쓰기 API에 멱등 키를 둔다([ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).

### 4. ALPN 불일치 — HTTP/2를 기대했는데 아니다

- **현상**: gRPC 클라이언트가 연결 직후 실패한다. 또는 HTTP/2가 안 켜진다.
- **보이는 형태**
  - `no_application_protocol` alert가 온다(ALPN을 지원하는 서버에서 목록이 안 겹칠 때).
  - 또는 `curl -v`에 ALPN 결과가 `http/1.1`이거나 협상 결과가 없다. gRPC는 HTTP/2가 필요해 실패한다.
- **원인**
  - 중간 LB·프록시가 TLS를 종단하면서 `h2`를 광고하지 않았다.
  - 또는 서버에 HTTP/2가 꺼져 있다.
- **대처**
  - TLS를 끝내는 지점(LB)의 ALPN 설정을 확인한다.
  - `openssl s_client -alpn h2`로 **각 홉**을 직접 두드려 본다.

### 5. 핸드셰이크가 느리다 — 첫 요청만 수백 ms

- **현상**: p99 지연이 튀는데, 연결을 새로 맺은 요청에 몰린다.
- **보이는 형태**
  - `curl -w '%{time_connect} %{time_appconnect}'`에서 appconnect(TLS 완료) − connect 구간이 크다.
  - `openssl s_client -msg`에 HelloRetryRequest가 보이고 ClientHello가 두 번 간다.
- **원인**
  - 연결 재사용이 안 된다.
  - 또는 HRR로 1 RTT가 추가됐다. 클라이언트의 `key_share` 추측이 서버가 받는 그룹과 다른 경우다.
  - 또는 서버가 1.2만 지원해 2-RTT가 든다.
- **대처**
  - 커넥션 풀·keep-alive로 핸드셰이크 자체를 줄인다(35번).
  - 세션 재개를 켠다.
  - 서버와 클라이언트의 선호 그룹(예: X25519)을 맞춘다.

## 핵심 문장

- TLS 1.3은 클라이언트가 ClientHello에 키 교환 값(`key_share`)을 **추측해서 미리** 넣어 1-RTT를 만든다. 추측이 틀리면 HRR로 1 RTT가 더 든다. 1.2는 서버 선택을 먼저 들어야 해서 2-RTT다.
- ServerHello 이후의 모든 핸드셰이크 메시지(인증서 포함)는 암호화된다. 정적 RSA·DH가 사라져 **공개키 기반** 키 교환은 전방 비밀성을 가진다. 단 PSK 단독(`psk_ke`) 재개와 0-RTT 데이터는 예외다.
- 각 traffic 키는 그 시점까지의 transcript 해시를 넣은 Derive-Secret으로 나오고, Finished는 transcript의 MAC이다. 그래서 협상을 몰래 바꾸면 핸드셰이크가 깨진다.
- 0-RTT는 한 왕복을 아끼는 대신 전방 비밀성과 연결 간 재전송 보호를 포기한다. HTTP에서는 safe 메서드만, 서버는 425로 거절할 수 있어야 한다.
- SNI는 "어느 인증서를 줄지", ALPN은 "어느 앱 프로토콜을 쓸지"를 추가 왕복 없이 ClientHello에서 정한다. SNI가 빠지면 기본 인증서가 올 수 있고, 그 인증서에 이름이 없으면 호스트명 검증이 실패한다.

## 관련 주제·근거

- 선행
  - [23-socket-api](../23-socket-api/2-summary.md)
  - `security/07-key-exchange-forward-secrecy` — 미작성([security 영역 표](../../security/README.md))
  - `security/03-symmetric-encryption-and-aead` — 미작성([security 영역 표](../../security/README.md))
  - security/05 HMAC — [foundations/security/hmac.md](../../foundations/security/hmac.md)
- 후속
  - [30-x509-and-chain-validation](../30-x509-and-chain-validation/2-summary.md) — 인증서 체인·호스트명 검증.
  - [32-mtls-and-cert-operations](../32-mtls-and-cert-operations/2-summary.md) — `certificate_required`.
  - [35-http-connection-management](../35-http-connection-management/2-summary.md) — 연결 재사용.
  - [37-http3-quic](../37-http3-quic/2-summary.md) — QUIC 안의 TLS 1.3.
  - [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) — 0-RTT 재전송 방어의 애플리케이션 쪽
- 같은 구조: [19-tcp-termination-fin-rst-half-open](../19-tcp-termination-fin-rst-half-open/2-summary.md) — 상태 기계와 "끊는 신호"(RST / alert)로 보는 진단
- RFC 8446 (TLS 1.3) <https://www.rfc-editor.org/rfc/rfc8446>
  - §1.2 1.2와의 주요 차이("all public-key based key exchange mechanisms now provide forward secrecy")
  - §2 Figure 1(전체 핸드셰이크) · §2.1 HRR(Figure 2) · §2.2 PSK 재개(PSK 단독 시 전방 비밀성 없음) · §2.3 0-RTT(Figure 4)와 보안 약화
  - §4.1.1 암호 협상·`handshake_failure` · §4.1.2 ClientHello `legacy_version` 0x0303 · §4.1.3 ServerHello·다운그레이드 방지 · §4.1.4 HelloRetryRequest
  - §4.2.1 supported_versions · §4.2.9 psk_key_exchange_modes(`psk_ke`·`psk_dhe_ke`) · §4.4.2.2 SNI와 인증서 선택 · §4.4.3 CertificateVerify · §4.4.4 Finished · §4.6.1 NewSessionTicket
  - §5.2 복호 실패 → `bad_record_mac` · §6 alert · §7.1 키 스케줄(HKDF, Derive-Secret) · §8 0-RTT 재전송 방지(§8.1 단일 사용 티켓, §8.2 ClientHello 기록·블룸 필터)
  - §9.1 필수 암호군 · §9.2 필수 확장·`missing_extension` · Appendix A 상태 기계 · B.4 암호군 · D.4 미들박스 호환 모드
- RFC 5246 (TLS 1.2) §7.3 Figure 1 · §7.4.7.1 RSA 키 전송 <https://www.rfc-editor.org/rfc/rfc5246>
- RFC 6066 §3 SNI(IP 리터럴 불가, 모르는 이름 처리) <https://www.rfc-editor.org/rfc/rfc6066>
- RFC 7301 §3.2 ALPN 선택(서버 선호 순)·`no_application_protocol` <https://www.rfc-editor.org/rfc/rfc7301>
- RFC 5869 HKDF <https://www.rfc-editor.org/rfc/rfc5869>
- RFC 8470 Early Data in HTTP(§3 서버 판단, §4 safe 메서드만, §5.1 `Early-Data`, §5.2 425) <https://www.rfc-editor.org/rfc/rfc8470>
- RFC 9849 TLS Encrypted Client Hello <https://www.rfc-editor.org/rfc/rfc9849>
- OpenSSL `s_client` 문서(`-cipher`/`-ciphersuites`, `-servername` 기본 동작 1.1.1+, `-brief`, "Note on Non-Interactive Use") <https://docs.openssl.org/3.0/man1/openssl-s_client/> · `apps/lib/s_cb.c` `print_ssl_summary`(ALPN 미포함) <https://github.com/openssl/openssl/blob/openssl-3.0/apps/lib/s_cb.c>
- curl `lib/vtls/openssl.c` — 호스트명 불일치 메시지 <https://github.com/curl/curl/blob/master/lib/vtls/openssl.c>
- nginx `ngx_http_ssl_module`(`ssl_early_data`, `ssl_reject_handshake`, `ssl_protocols`) <https://nginx.org/en/docs/http/ngx_http_ssl_module.html> · "Configuring HTTPS servers"(SNI 없을 때 기본 인증서) <https://nginx.org/en/docs/http/configuring_https_servers.html>
- Node.js `tls` 문서 <https://nodejs.org/api/tls.html>
- Beurdouche 외, "A Messy State of the Union: Taming the Composite State Machines of TLS", IEEE S&P 2015 (SMACK) <https://www.ieee-security.org/TC/SP2015/papers-archived/6949a535.pdf>
- Grigorik, 『High Performance Browser Networking』 "Transport Layer Security" 장 <https://hpbn.co/transport-layer-security-tls/>
