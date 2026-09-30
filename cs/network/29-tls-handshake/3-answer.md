# network/29-tls-handshake — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. TLS 1.3 전체 핸드셰이크

```text
  Client                                         Server
  ClientHello (+key_share, +SNI, +ALPN,
               +supported_versions)  -------->
                                                 ServerHello (+key_share)
                                     ~~~~ 여기부터 암호화 ~~~~
                                                 {EncryptedExtensions}
                                                 {CertificateRequest*}
                                                 {Certificate}
                                                 {CertificateVerify}
                                                 {Finished}
                                     <--------   [Application Data*]
  {Certificate*} {CertificateVerify*}
  {Finished}                         -------->
  [Application Data]                 <------->   [Application Data]
```

- ServerHello까지는 평문이다. 그 뒤 메시지는 모두 handshake traffic 키로 암호화된다(`{}`)(RFC 8446 §1.2, Figure 1).
- 애플리케이션 데이터는 application traffic 키로 암호화된다(`[]`).
- `*`는 상황에 따라 보내는 메시지다. 예를 들어 클라이언트 인증서는 서버가 요청할 때만 보낸다.

### 2. 1-RTT의 비결과 실패 시

- 1.2에서 클라이언트는 서버가 고른 암호군과 키 교환 파라미터(ServerKeyExchange)를 먼저 들어야 했다. 그 뒤에야 ClientKeyExchange를 보낼 수 있어 왕복이 2번이었다.
- 1.3에서 클라이언트는 서버가 고를 만한 그룹을 **추측**한다. 그리고 그 그룹의 ECDHE 공개값을 ClientHello의 `key_share`에 미리 넣는다.
  - 서버가 받아들이면 ServerHello 한 번으로 양쪽이 공유 비밀을 계산한다. 그래서 1-RTT다.
- 추측이 틀리면 서버가 **HelloRetryRequest**로 원하는 그룹을 알려 준다. 클라이언트는 ClientHello를 다시 보내야 해서 1 RTT가 추가된다(§2.1, §4.1.4).
- 공통 파라미터가 아예 없으면 `handshake_failure` 또는 `insufficient_security`로 중단한다(§4.1.1).
- 한 연결에서 HRR은 한 번뿐이다. 두 번째 HRR을 받으면 클라이언트는 `unexpected_message`로 끊는다(§4.1.4).

### 3. 0-RTT의 약한 두 성질

RFC 8446 §2.3 IMPORTANT NOTE의 두 가지다.

- **전방 비밀성 없음**
  - 0-RTT 데이터는 PSK(보통 이전 연결에서 받은 재개 PSK, 외부 PSK일 수도 있음)에서 유도한 키로만 암호화된다. 이번 연결의 새 ECDHE가 섞이지 않는다.
  - 그래서 PSK(티켓 암호화 키 등)가 나중에 새면 녹화된 0-RTT 데이터를 풀 수 있다.
- **연결 간 재전송 보호 없음**
  - 1-RTT 데이터는 서버의 Random이 키 유도에 섞이므로 연결마다 키가 다르다.
  - 0-RTT 데이터는 ServerHello를 받기 전에 보내므로 이 보호를 못 받는다.
  - 그래서 공격자가 첫 비행을 녹화해 다시 보내면 서버가 다시 처리할 수 있다.

### 4. 0-RTT 결제 API 보호

- **TLS 층**(RFC 8446 §8)
  - 서버의 각 인스턴스는 같은 0-RTT 핸드셰이크를 최대 한 번만 받는다(MUST). 방법은 단일 사용 티켓이나 ClientHello 기록과 시간 창이다.
  - 인스턴스 사이까지 막는 것은 SHOULD라서, 여러 인스턴스·지역 사이의 중복은 남을 수 있다.
- **HTTP 층**(RFC 8470)
  - 클라이언트는 다른 정보가 없으면 safe 메서드만 early data로 보낸다. 결제 같은 unsafe 요청은 보내면 안 된다(MUST NOT, §4).
  - TLS를 종단하는 프록시는 early data로 받은 요청에 `Early-Data: 1`을 붙여 넘긴다(§5.1).
  - 원 서버는 재전송되면 안 되는 요청이면 `425 Too Early`로 거절한다(§5.2). 그러면 클라이언트는 핸드셰이크 완료 후 다시 보낸다.
  - 멱등하다는 것만으로는 부족하다. safe 메서드라도 부작용이 있는 자원이 있으니 자원별로 판단한다(§3).
  - nginx 예: `proxy_set_header Early-Data $ssl_early_data;`
- **애플리케이션 층**
  - 결제 요청에 멱등 키를 둔다. 같은 키의 두 번째 요청은 첫 결과를 돌려준다.
  - 이것은 0-RTT가 아니어도 클라이언트 재시도 때문에 필요하다(§8 "second class of attack ... cannot be prevented at the TLS layer").

### 5. 다운그레이드 방지 — Finished와 transcript

- 중간자가 ClientHello의 암호군 목록을 바꾸면, 클라이언트가 보낸 ClientHello와 서버가 받은 ClientHello가 달라진다.
- handshake traffic 키는 **ClientHello…ServerHello의 transcript 해시**를 넣은 Derive-Secret으로 유도된다(§7.1).
  - 그래서 양쪽의 handshake 키부터 달라진다.
  - 단, Extract 단계 자체와 단계 사이의 `derived`에는 transcript가 들어가지 않는다. transcript는 각 traffic secret을 뽑을 때 들어간다.
- 그러면 실패가 어디서 드러나는지는 고정돼 있지 않다.
  - 키가 달라 첫 암호화 레코드부터 복호가 안 될 수 있다(`bad_record_mac`, §5.2).
  - 그 단계를 넘더라도 Finished(transcript 전체의 MAC, §4.4.4) 검증에서 실패한다(`decrypt_error`).
- 서버는 CertificateVerify로 transcript에 서명하므로, 중간자는 이 서명을 다시 만들 수도 없다.
- 버전 다운그레이드에는 한 겹이 더 있다. 1.3 서버가 1.2 이하로 협상할 때는 ServerHello.random의 마지막 8바이트에 표식(`44 4F 57 4E 47 52 44 01` 등)을 넣는다. 그래서 1.3 클라이언트가 강제 하향을 알아챈다(§4.1.3).

### 6. SNI와 Host 헤더

- 서버는 **인증서를 보내기 전에** 어느 도메인인지 알아야 한다.
- HTTP `Host` 헤더는 TLS 핸드셰이크가 끝난 뒤 암호화된 채널로 온다. 그래서 인증서 선택 시점에는 쓸 수 없다.
- 그래서 ClientHello에 `server_name`을 싣는다(RFC 6066 §3).
- SNI가 빠져도 **반드시 실패하지는 않는다**. 서버 설정에 따라 셋으로 갈린다.
  - 기본 서버의 인증서에 대상 이름이 들어 있으면 → 성공한다.
  - 기본 인증서에 대상 이름이 없으면 → 클라이언트의 호스트명 검증이 실패한다. 에러는 **클라이언트 쪽**에서 난다. Java는 `CertificateException: No subject alternative DNS name matching ... found.`, Node는 `ERR_TLS_CERT_ALTNAME_INVALID`다.
  - 서버가 SNI를 요구하거나 이름 없는 핸드셰이크를 거절하면 → 서버가 alert로 끊는다(`missing_extension`·`unrecognized_name` 등, RFC 8446 §9.2, RFC 6066 §3).

### 7. ALPN 불일치

- ALPN을 지원하는 서버라면, 겹치는 프로토콜이 없으므로 치명 alert `no_application_protocol`(120)을 보내고 핸드셰이크를 끝낸다(SHALL, RFC 7301 §3.2).
- 서버가 ALPN을 아예 처리하지 않으면 응답에 ALPN이 없다. 핸드셰이크는 끝나지만 "협상 안 됨"이다. `h2`가 필수인 클라이언트(gRPC 등)는 그 뒤 스스로 실패한다.
- 협상이 성공하면 선택 결과는 TLS 1.3에서 **EncryptedExtensions**에 실린다. 암호화된 채로 온다(RFC 8446 §4.2 표: ALPN은 CH, EE).
- 서버는 자기 선호 순서로 고른다(SHOULD, RFC 7301 §3.2). 추가 왕복은 없다.

### 8. 오래된 JDK만 handshake_failure

- 의심할 것
  - (1) 서버가 TLS 1.2 미만을 껐는데 클라이언트가 1.0/1.1만 쓴다. RFC상 이 경우 alert는 `protocol_version`이지만 구현에 따라 다르게 보일 수 있다.
  - (2) 공통 암호군이 없다. 예: 서버가 AEAD 암호군만 허용하는데 클라이언트에 그게 없다.
  - (3) 공통 그룹·서명 알고리즘이 없다.
- 확인 명령
  - TLS 1.2 이하: `openssl s_client -connect host:443 -tls1_2 -cipher '...'`
  - TLS 1.3: `openssl s_client -connect host:443 -tls1_3 -ciphersuites '...'`
  - `-cipher`는 1.3 암호군에 적용되지 않는다(OpenSSL `s_client` 문서).
  - 클라이언트에서는 `-Djavax.net.debug=ssl:handshake`로 ClientHello에 실린 버전·암호군 목록을 본다.
  - `-msg -state`로 어느 메시지 뒤에 누가 alert를 보냈는지 본다.
- 대처: JDK를 올리는 것이 1순위다. 서버 하한을 낮추는 것은 기한을 정한 예외로만 한다.

### 9. 전방 비밀성

- 사라진 것은 1.2의 **정적 RSA 키 전송**과 정적 DH다(§1.2).
  - 정적 RSA에서는 클라이언트가 pre-master secret을 서버 인증서의 RSA 공개키로 암호화해 보냈다(RFC 5246 §7.4.7.1).
  - 그래서 서버 개인키가 나중에 유출되면, 녹화해 둔 과거 트래픽을 모두 풀 수 있었다.
- 1.3의 공개키 기반 키 교환은 (EC)DHE뿐이다. 연결마다 임시 키쌍을 만들고 버린다.
  - 서버 인증서 개인키는 서명(CertificateVerify)에만 쓴다.
  - 그래서 개인키가 유출돼도 **과거 세션 키는 복원되지 않는다**. 이것이 전방 비밀성이다.
- 1.3에서도 전방 비밀성이 없는 경우
  - **PSK 단독 모드(`psk_ke`)**: (EC)DHE를 섞지 않는다. PSK가 새면 그 연결의 애플리케이션 데이터가 풀린다(§2.2, §4.2.9). `psk_dhe_ke`를 쓰면 전방 비밀성이 생긴다.
  - **0-RTT 데이터**: PSK에서 유도한 키로만 암호화된다(§2.3).

### 10. 첫 요청까지의 왕복 수

```text
                         TCP    TLS    합계 (요청을 보내기까지)
  TLS 1.2 전체            1      2      3 RTT
  TLS 1.3 전체            1      1      2 RTT   (HRR이면 3)
  TLS 1.3 0-RTT 재개       1      0      1 RTT   (요청이 ClientHello와 같이 감)
```

- 전형적인 경우의 계산이다. TLS 1.2 False Start, TCP Fast Open 같은 최적화는 뺐다.
- TCP 3-way에서 클라이언트는 SYN-ACK를 받은 뒤 ACK와 함께 ClientHello를 보낼 수 있다. 그래서 TCP는 1 RTT로 센다.
- 응답을 받기까지는 여기에 1 RTT가 더 붙는다.
- TCP Fast Open이나 QUIC(37번)은 이 TCP 1 RTT까지 줄이려는 시도다.
