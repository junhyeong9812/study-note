# network/32-mtls-and-cert-operations — 정답

## 정답

### 1. mTLS가 바꾸는 것

- API 키·bearer 토큰은 문자열이다. 가진 사람이면 누구나 쓸 수 있고, 로그·설정·메모리 덤프로 새면 그대로 재사용된다.
- mTLS에서 클라이언트는 인증서를 보내고, CertificateVerify로 **그 연결의 transcript에 개인키로 서명**한다.
  - 인증서만 훔쳐서는 안 되고 개인키가 있어야 한다.
  - 서명은 연결마다 달라 재사용할 수 없다.
- 신원이 "알고 있는 비밀 문자열"에서 "**내보내지 않는 개인키 보유**"로 옮겨 간다. 개인키를 HSM·TPM에 두면 복사 자체를 막을 수 있다.

### 2. 클라이언트 인증 핸드셰이크

```text
  C: ClientHello                         ->
  S: ServerHello
     {EncryptedExtensions}
     {CertificateRequest}   서버가 클라이언트 인증 요구 (signature_algorithms 필수, CA 힌트 선택)
     {Certificate}          서버 인증서
     {CertificateVerify}    서버 서명
     {Finished}                          <-
  C: {Certificate}          클라이언트 인증서 체인 (없으면 빈 목록)
     {CertificateVerify}    클라이언트 개인키로 transcript 에 서명
     {Finished}                          ->
```

- CertificateRequest는 EncryptedExtensions 바로 뒤에 온다(RFC 8446 §4.3.2).
- 클라이언트 Certificate는 요청받았을 때만 보낸다.
- CertificateVerify가 "그 인증서의 개인키를 지금 쥐고 있다"를 증명한다.

### 3. 인증서가 없을 때

- 클라이언트는 **빈 Certificate 메시지**(certificate_list 길이 0)를 보낸다. Finished는 여전히 보낸다(MUST, §4.4.2).
- 서버는 재량으로 고른다(§4.4.2.4).
  - 클라이언트 인증 없이 계속한다(비인증 사용자로 취급).
  - `certificate_required` alert로 핸드셰이크를 끊는다.
- 116은 "인증서를 원했는데 오지 않았다"는 뜻이다(§6.2).
- nginx처럼 TLS는 통과시키고 HTTP 400(내부 496)으로 거절하는 구현도 있다.

### 4. 인증 vs 인가

- mTLS가 확인하는 것은 "믿는 CA가 발급했고 개인키를 가졌다"까지다. 곧 **누구인가**다.
- "이 신원이 이 API를 불러도 되나"는 서버가 인증서에서 신원(SAN URI 등)을 꺼내 정책과 대조해야 한다.
- 사내 CA 하나로 모든 워크로드에 인증서를 주고 "그 CA면 통과"만 하면 문제가 생긴다.
  - 어떤 워크로드든 다른 모든 서비스를 호출할 수 있다.
  - 워크로드 하나가 뚫리면 횡적 이동이 자유롭다.
- 신원 → 허용 목록(서비스·경로·메서드) 인가가 필요하다.

### 5. LB 종단 + 신원 헤더

- 위험
  - 앱이 신원 헤더(예: `X-Client-DN`, Envoy `x-forwarded-client-cert`)를 그대로 믿는다.
  - LB를 우회해 앱에 직접 닿거나, LB가 헤더를 지우지 않으면 클라이언트가 **헤더를 위조**해 다른 신원을 사칭할 수 있다.
- 막는 법
  1. LB가 들어온 같은 이름 헤더를 제거하고 자기가 검증한 값으로 덮어쓴다(nginx `proxy_set_header`는 덮어쓴다).
  2. 앱은 LB에서 온 연결만 받는다(네트워크 정책, LB↔앱 구간도 mTLS).

### 6. ACME 단계와 도전 과제

1. `newAccount`: 계정 키로 가입한다(요청은 JWS 서명).
2. `newOrder`: 원하는 이름을 제출한다. authorization 목록과 finalize URL을 받는다.
3. 이름마다 도전 과제 하나를 준비한다.
4. "준비됐다"를 알리면 CA가 직접 확인한다.
5. `finalize`: CSR을 제출한다.
6. 발급된 체인을 certificate URL에서 받는다.

| 도전 | 증명 방법 | 제약 |
|---|---|---|
| http-01 | `http://<도메인>/.well-known/acme-challenge/<token>`에 키 인가 값 | TCP 80으로만 확인(RFC 8555 §8.3) |
| dns-01 | `_acme-challenge.<도메인>` TXT | DNS API 자격 증명이 필요, 전파 대기 |
| tls-alpn-01 | 443에서 ALPN `acme-tls/1`로 특수 인증서 제시 | 80이 막혀도 가능(RFC 8737) |

- 와일드카드는 Let's Encrypt에서 **dns-01만** 된다.

### 7. "갱신 성공"인데 만료 장애

- 의심 대상
  - **프로세스가 옛 인증서를 메모리에 들고 있다.** 파일만 바뀌고 reload가 없었다.
  - LB·CDN·다른 호스트에 **다른 사본**이 있다.
  - 갱신된 것이 다른 인증서다(이름 누락, 인벤토리 불일치).
- 감시 바꾸기
  - 파일이 아니라 **네트워크로 제시되는 인증서**의 notAfter를 본다(`openssl s_client ... | openssl x509 -enddate`).
  - 갱신 훅에 reload를 넣는다.
  - 엔드포인트 스캔으로 모든 사본을 찾는다.

### 8. 중간 CA 도입 후 nginx 400

- 가장 유력한 원인: **중간 CA 인증서를 어디서도 구할 수 없다.** 클라이언트가 리프만 보내고, 서버의 `ssl_client_certificate`(또는 `ssl_trusted_certificate`)에도 중간이 없다.
- `ssl_verify_depth` 기본값 1은 원인이 아니다(중간 1단계인 경우).
  - OpenSSL(1.1.0 이후)에서 depth는 리프와 루트 **사이** 인증서 수 한도다(`SSL_CTX_set_verify(3)`). 기본값 1로도 리프 → 중간 → 루트는 통과한다.
  - 중간이 2단계 이상이면 그때 depth를 올려야 한다.
- 결과는 `$ssl_client_verify = FAILED:...`, HTTP 400(내부 495)이다.
- 고치기
  - 중간 CA를 클라이언트가 보내게 하거나, 서버의 `ssl_client_certificate`(또는 `ssl_trusted_certificate`)에 넣는다.
  - 중간이 2단계 이상이면 `ssl_verify_depth`를 중간 CA 수 이상으로 올린다.

### 9. 공인 인증서의 clientAuth EKU 제거

- Chrome 루트 프로그램이 2026년 6월까지 TLS 서버 인증 PKI와 클라이언트 인증 PKI를 분리하도록 요구했다.
- 공인 CA들이 서버 인증서에서 `clientAuth` EKU를 뺐다.
  - Let's Encrypt는 2026-02-11 기본(classic) 프로필에서 제거했다.
  - 2026-07-08 `tlsclient` 프로필 종료로 clientAuth 인증서 발급을 멈췄다.
- 갱신된 인증서에는 clientAuth가 없어 상대 서버가 용도 불일치로 거절한다(OpenSSL `unsuitable certificate purpose`).
- 옮기는 법
  - 클라이언트 인증용 **사설 CA**를 세운다(또는 클라이언트 인증 전용 PKI를 쓴다).
  - 상대 측과 신뢰할 CA를 다시 합의하고, 그 CA로 발급한 인증서를 배포한다.

### 10. 인벤토리와 만료 타이머

- 열(예시): 이름/SAN, 배포 위치(모든 사본), 발급자, 키 종류, notAfter, 갱신 방식(ACME/수동), 담당자, 용도(서버/클라이언트).
- 수집 경로
  1. CT 로그 검색: 공인 인증서는 도메인으로 전부 찾는다.
  2. 엔드포인트 스캔: 사내 IP:포트에 접속해 제시 인증서를 모은다.
  3. 저장소 스캔: k8s TLS Secret, 키스토어 파일, 클라우드 인증서 서비스.
- 만료 타이머: **우선순위 큐(최소 힙)**가 맞다.
  - 키는 "갱신해야 할 시각"(notAfter − 여유, 또는 ARI 창 안의 무작위 시각)이다.
  - 가장 이른 것만 꺼내 보면 되고, 추가·갱신은 O(log n)이다.
