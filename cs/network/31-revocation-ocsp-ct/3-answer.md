# network/31-revocation-ocsp-ct — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. 폐기와 CT가 필요한 이유

- 유효기간은 발급 때 정해진다. 그 사이의 사고는 반영하지 못한다.
  - 사고 예: 개인키 유출, CA 오발급, 도메인 소유 변경.
- 폐기: "만료 전이지만 더는 믿지 말라"를 클라이언트에 전달한다.
- CT: "어떤 인증서가 발급됐는지"를 공개 로그에 남긴다. 도메인 주인이 몰래 발급된 인증서를 **발견**하게 한다.
- 둘은 짝이다. CT로 오발급을 찾고, 폐기로 무효화한다.

### 2. CRL vs OCSP

```text
  CRL : 클라이언트 --GET--> CRL 배포점 --> 서명된 serial 목록 (nextUpdate 까지 캐시) --> 로컬 조회
  OCSP: 클라이언트 --CertID--> OCSP 응답기 --> good/revoked/unknown (nextUpdate 까지 캐시)
```

| 항목 | CRL | OCSP |
|---|---|---|
| 사생활 | CA가 어느 사이트인지 모름 | 응답기가 접속 사이트를 앎 |
| 지연 | 받아 둔 뒤엔 로컬 조회 | 캐시된 응답이 없으면 첫 연결마다 추가 왕복 (stapling 없을 때) |
| 신선도 | 게시 주기(`nextUpdate`)만큼 늦음 | 응답기 갱신 주기만큼 늦음 |
| 크기 | 목록이 커짐 | 응답 하나는 작음 |

### 3. OCSP 상태

- `good`: 요청한 serial의 인증서 중 유효기간 안에서 폐기된 것이 없다(RFC 6960 §2.2).
- `revoked`: 폐기됐다. 일시 보류(`certificateHold`)도 포함한다. 발급한 적 없는 serial에 줄 수도 있다(MAY).
- `unknown`: 이 응답기는 이 인증서를 모른다. 다른 정보원을 시도할지는 클라이언트가 정한다.
- `good`은 **발급 사실을 보장하지 않는다.** RFC는 `good`이 "발급된 적 있음"을 반드시 뜻하지는 않는다고 적는다.

### 4. soft-fail vs hard-fail

- soft-fail(응답 없으면 통과)
  - 폐기된 인증서로 중간자 공격을 하는 사람은 네트워크를 쥐고 있다. OCSP 요청도 막을 수 있다.
  - 그래서 공격 상황에서는 늘 "응답 없음 → 통과"가 된다. 폐기 확인이 가장 필요한 순간에 무력하다.
- hard-fail(응답 없으면 거부)
  - CA 응답기의 가용성·지연이 내 서비스 가용성이 된다. 캐시·스테이플로 상태를 확인할 수 없는 연결은 전부 거부된다. 캐시가 없는 클라이언트라면 응답기 장애 = 전면 장애다.
- 그래서 브라우저는 온라인 조회 대신 사전 배포 방식으로 옮겼다. Chrome은 CRLSet, Firefox는 CRLite다.

### 5. TLS 1.3 stapling 위치

```text
  ClientHello + status_request (ocsp)     -->
                                        <--  {Certificate}
                                               CertificateEntry[0] = 리프
                                                  extensions: status_request = OCSP 응답 (CertificateStatus)
                                               CertificateEntry[1] = 중간
```

- TLS 1.2에서는 별도의 CertificateStatus 메시지였다. TLS 1.3에서는 그 응답이 다루는 인증서(보통 리프)의 CertificateEntry 확장이다(RFC 8446 §4.4.2.1).
- ClientHello의 `status_request`는 비어 있지 않다. `status_type = ocsp(1)`과 OCSPStatusRequest(응답기 목록·확장, 보통 둘 다 비움)를 담는다(RFC 6066 §8).
- 스테이플을 빼는 공격: 클라이언트가 스테이플이 없으면 soft-fail로 넘어가는 점을 노린다.
  - 막는 법: 인증서에 **Must-Staple**(RFC 7633 TLS Feature 확장, `status_request`)을 넣는다. Must-Staple을 지원하는 클라이언트는 스테이플이 없으면 거부해야 한다(SHOULD, RFC 7633 §4.2.3.1 — 다른 경로로 OCSP를 확인했으면 수락할 수도 있다).

### 6. OCSP 응답기 장애 진단

- 실패한 클라이언트
  - 폐기 확인을 **hard-fail**로 요구한다.
  - 서버가 스테이플을 주지 않아 **직접 응답기에 묻는** 클라이언트다.
  - 또는 Must-Staple 인증서인데 서버의 스테이플이 만료·누락된 경우다.
- 서버 쪽 대처
  - stapling을 켠다(`ssl_stapling on`, `resolver`, `ssl_trusted_certificate`).
  - 응답을 `nextUpdate`까지 캐시해 응답기 짧은 장애를 흡수한다.
  - 스테이플 신선도를 감시한다.

### 7. 두 일정과 공통 압박

- Let's Encrypt OCSP 종료
  - 2024-12-05 공지.
  - 2025-01-30 Must-Staple 요청 실패(전에 Must-Staple 인증서를 받은 계정 제외).
  - 2025-05-07 인증서에서 OCSP URL 제거. Must-Staple 요청은 전부 실패.
  - 2025-08-06 응답기 종료. 이후 CRL을 쓴다.
- SC-081v3(2025-04-11 통과) 최대 수명
  - 2026-03-15 200일.
  - 2027-03-15 100일.
  - 2029-03-15 47일.
  - 도메인 검증 재사용 기간도 10일로 준다.
- 공통 압박: 폐기 인프라 대신 **짧은 수명**으로 피해 창을 줄인다. 그래서 갱신이 잦아지고 **자동 갱신과 만료 감시가 필수**가 된다(32번).

### 8. 머클 증명

- 포함 증명: 잎(인증서 항목)에서 뿌리까지 각 층의 **형제 노드 해시** 목록이다. 이걸로 뿌리를 다시 계산해 서명된 STH의 뿌리와 같으면 "이 항목이 로그에 있다"가 증명된다.
- 일관성 증명: 옛 트리(m개 항목)의 뿌리와 새 트리(n개)의 뿌리가 "앞 m개가 같다"는 관계임을 보이는 노드 목록이다. **추가 전용**(과거를 지우거나 바꾸지 않음)을 증명한다.
- 크기가 O(log n)인 이유: 이진 트리의 높이가 log n이고, 층마다 노드 하나(또는 몇 개)만 필요하다.
- 잎은 `0x00`, 내부 노드는 `0x01`을 앞에 붙여 해시한다. 잎과 내부 노드를 혼동시키는 공격을 막는다(RFC 9162 §2.1.1).

### 9. CT의 한계와 쓰임

- CT는 오발급을 **막지 않는다.** 오발급이 **보이게** 한다(RFC 9162 §1).
- SCT는 로그가 "이 인증서를 Maximum Merge Delay 안에 로그에 넣겠다"고 서명한 약속이다.
- Chrome 같은 클라이언트는 정책에 맞는 SCT가 없는 공인 인증서를 거부한다. 그래서 공인 CA는 사실상 모든 인증서를 로그에 올린다.
- 도메인 주인이 할 수 있는 일
  - 로그를 감시해 자기 도메인의 낯선 인증서를 찾는다.
  - CA에 폐기를 요청한다.
  - CAA로 허용 CA를 좁힌다.

### 10. 확인 명령

```bash
openssl x509 -in leaf.pem -noout -ocsp_uri                      # OCSP URL
openssl x509 -in leaf.pem -noout -ext crlDistributionPoints     # CRL 배포점
openssl x509 -in leaf.pem -noout -ext ct_precert_scts           # SCT
openssl s_client -connect host:443 -servername host -status </dev/null | grep -A3 'OCSP response'
                                                                 # stapling 여부
```
