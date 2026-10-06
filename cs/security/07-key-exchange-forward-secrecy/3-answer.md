# security/07-key-exchange-forward-secrecy — 정답

## 정답

### 1. 키 전송 vs 키 합의

- 키 전송(TLS 1.2 `TLS_RSA_…`): 클라이언트가 premaster를 만들고, 서버 RSA 공개키로 암호화해 **보낸다.** 비밀이 (암호화된 채로) 선 위로 지나간다.
- 키 합의(DH): 양쪽이 공개값 A, B만 보낸다. 공유 비밀 g^(ab)는 각자 계산하고 선 위로 지나가지 않는다.
- 결과 차이: 키 전송은 서버 개인키 하나로 녹음된 premaster를 풀 수 있다. 임시 키 합의는 풀 대상이 남지 않는다.

### 2. 장난감 DH

- A = 5^6 mod 23 = 8, B = 5^15 mod 23 = 19.
- Alice: 19^6 mod 23 = 2, Bob: 8^15 mod 23 = 2 → K = 2.
- 실험 출력: `toy DH: A=g^a=8 B=g^b=19  alice B^a=2  bob A^b=2`.
- 도청자는 p, g, A=8, B=19를 본다. A, B만으로 K를 계산해야 한다(계산 DH 문제). 이산 로그로 a 또는 b를 구하면 풀리고, 이 크기는 바로 풀리지만, 2048비트 p나 255비트 곡선에서는 현실적으로 안 된다.

### 3. 녹음 + 나중 유출

```text
  정적 RSA:  녹음 Enc(pub, premaster) + 나중 개인키 → premaster → 세션 키 → 복호 성공
  ECDHE   :  녹음 A, B, 서명 + 나중 개인키 → 서명이 진짜였다는 것만 확인 → a, b 없음 → 복호 불가
```

- ECDHE에서 장기 키는 공개값·핸드셰이크에 **서명**해 상대를 인증하는 데만 쓰인다.
- 실험: `static RSA: leaked long-term key recovers premaster = true`, `ECDHE: ... long-term key not an input`.

### 4. `Server Temp Key` 줄

- TLS 1.2 `AES128-GCM-SHA256`: 줄이 없다 → 임시 키 없음 → 이 암호군은 `Kx=RSA`라 정적 RSA 키 전송 → 전방 비밀성 없음.
- TLS 1.2 `ECDHE-RSA-AES128-GCM-SHA256`: `Server Temp Key: X25519, 253 bits`.
- TLS 1.3 `TLS_AES_256_GCM_SHA384`: `Server Temp Key: X25519, 253 bits`. 1.3 암호군 이름에는 키 교환이 없고 `key_share`로 따로 정한다.
- 실험 환경: OpenSSL 3.0.13, 127.0.0.1 임의 포트, 자체 서명 인증서.

### 5. 서명 없는 DH

- 중간자가 양쪽과 각각 따로 키를 합의한다. 양쪽은 같은 키를 가졌다고 믿지만, 실제로는 중간자가 두 키를 다 쥐고 중계한다.
- TLS 1.3: 키 합의 = `key_share`의 (EC)DHE, 상대 인증 = (인증서 인증일 때) 서버가 `Certificate`까지의 핸드셰이크 기록 해시에 서명하는 `CertificateVerify` + 인증서 체인 검증([network/29](../../network/29-tls-handshake/2-summary.md)).

### 6. 전방 비밀성이 깨지는 경우

- `psk_ke` 재개 모드: (EC)DHE를 섞지 않는다. RFC 8446 부록 E.1이 "forward secrecy property is not satisfied when PSK is used in the psk_ke mode"라고 적는다(예외: 일회용 PSK를 사용 즉시 지우면 전방 비밀성을 얻는다, §8.1). → `psk_dhe_ke`를 쓴다.
- 세션 키를 지우지 않음: 부록 E.1의 조건은 "세션 키 자체가 지워졌다면"이다. 키·임시 개인키를 덤프·로그·디스크에 남기면 장기 키처럼 된다.
- 덧붙여: 오래 사는 세션 티켓 암호화 키도 사실상 장기 키다(티켓 안의 재개 비밀을 풀 수 있다).

### 7. cryptoperiod

- SP 800-57 Part 1 Rev.5 표 1: 임시 키 합의 키 = "키 합의 한 번", 정적 키 합의 키 = 1~2년.
- 임시 키는 한 번 쓰고 버리므로 그 뒤에 무엇이 유출돼도 지난 연결의 키를 재계산할 재료가 없다. 이것이 전방 비밀성의 구현이다.

### 8. 개인키 유출 시 과거 노출 범위

- 확인
  - 그 키를 쓴 서버들이 협상한 암호군 이력: 정적 RSA(`Kx=RSA`)가 쓰인 기간·비율. 접속 로그에 암호군을 남겼다면 그것으로, 없으면 설정 이력으로 추정.
  - TLS 1.3 PSK 재개 모드와 티켓 키 수명.
- 산정: 정적 RSA로 협상된 연결은 녹음됐다면 복호 가능으로 본다. ECDHE 연결은 개인키로 복호되지 않는다(다만 유출 이후에는 사칭이 가능하므로 폐기·교체가 급하다).
- 재발 방지: TLS 1.3 우선, 1.2는 ECDHE만, 재개는 `psk_dhe_ke`, 티켓 키 짧게 회전, 접속 로그에 프로토콜·암호군 기록. 인증서 폐기·교체 절차는 [network/31](../../network/31-revocation-ocsp-ct/2-summary.md)·[network/32](../../network/32-mtls-and-cert-operations/2-summary.md).

### 9. `HIGH:!aNULL`

- 문제: "강한 암호"라는 뜻의 HIGH에는 정적 RSA 키 교환 암호군도 들어 있다. OpenSSL 3.0.13에서 펼치면 `AES256-GCM-SHA384 ... Kx=RSA` 같은 줄이 나온다.
- 확인: `openssl ciphers -v '<설정 문자열>' | awk '$3=="Kx=RSA"'` → 줄이 나오면 정적 RSA 허용. 접속 쪽에서는 `s_client`의 `Server Temp Key` 유무.
- 고침: `ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...`처럼 ECDHE만 나열(`openssl ciphers -v 'ECDHE+AESGCM'`에서 `Kx=RSA` 0줄 확인), 가능하면 TLS 1.3 우선.
