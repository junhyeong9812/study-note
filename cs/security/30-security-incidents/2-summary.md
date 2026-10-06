# security/30-security-incidents — 실사건: Heartbleed(2014) · Equifax Struts 미패치(2017) · Capital One(2019) · Log4Shell(2021) · xz 백도어(2024) — 무엇이 깨졌나 → 원리 leaf → 막았을 통제 — 정리 (힌트)

## 해결하는 문제

다섯 사건은 모두 **한 곳이 깨졌는데 피해는 다른 곳들이 키웠다.**

```text
  사건            처음 깨진 곳                         피해를 키운 것                              원리 leaf
  ────            ──────────                          ────────────                               ────────
  Heartbleed      길이 필드를 믿은 경계 밖 읽기          약 2년간 배포된 판, 로그에 흔적 없음         24 메모리 안전
  Equifax 2017    공개·패치된 Struts 취약점 미적용       낡은 알림 수신자 목록, 만료 인증서로 꺼진 탐지,  25 공급망 · 26 감사
                                                       분리 안 된 DB, 평문 자격 증명
  Capital One     설정 오류로 서버가 명령을 대신 실행    그 서버 역할의 넓은 저장소 권한               22 SSRF · 01 최소 권한
  Log4Shell       로그 메시지 안 문자열을 lookup으로 실행  어디에 들어 있는지 아무도 모르는 전이 의존성   23 파서 공격 · 25 SBOM
  xz 2024         유지보수자 권한으로 릴리스 tarball 변조  배포판 빌드 파이프라인이 그대로 받음          25 공급망
```

쉬운 예: 아파트 화재다.\
불은 한 집의 전기 배선에서 났다(처음 깨진 곳). 그런데 방화문이 열려 고정돼 있었고, 화재 경보기는 배터리가 빠져 있었고, 대피 안내도는 옛 구조였다.\
그래서 한 집의 불이 건물 전체 사고가 됐다.

똑같은 구조다.\
"취약점 하나"는 출발점이다. 사고의 크기는 **탐지·분리·권한·자산 목록** 같은 운영 통제가 정했다.\
이 노트는 사건마다 원문 사실을 옮기고, "무엇이 깨졌나 → 어느 leaf의 원리 → 막았을 통제"로 잇는다.

  - *1차 출처*: 당사자·조사 기관이 직접 쓴 문서 — NVD 레코드, OpenSSL 보안 권고, 미 회계감사원(GAO) 보고서, 회사 공지, 법원 제출 공소장, 미 법무부·통화감독청(OCC) 발표, 미 사이버안전검토위원회(CSRB) 보고서, oss-security 메일링 리스트 원문.
  - *표기*: 날짜·수치는 원문 그대로 옮긴다. 원문에 없는 연결은 "해석"이라고 쓴다. 이 노트는 공개 보고서 수준의 원인·영향·교훈만 다룬다. 공격 절차의 재현 가능한 세부는 쓰지 않는다.
  - *CVSS*: 취약점 심각도 점수(0~10). 이 노트의 점수는 NVD가 매긴 CVSS 3.1 기본 점수다.
  - *CISA KEV*: 미 CISA의 "실제 악용이 확인된 취약점" 목록(Known Exploited Vulnerabilities).

## 동작·원리

### 사건 1 — Heartbleed: OpenSSL 하트비트 경계 밖 읽기 (CVE-2014-0160, 2014-04-07 공개)

출처
- NVD CVE-2014-0160 <https://nvd.nist.gov/vuln/detail/CVE-2014-0160> (API로 2026-10-07 조회)
- OpenSSL Security Advisory [07 Apr 2014] "TLS heartbeat read overrun (CVE-2014-0160)" <https://www.openssl.org/news/secadv/20140407.txt>
- heartbleed.com — Heartbleed 문답 안내 페이지(2026-10-07 열람본은 "Page updated 2025-03-07", 판권 표기 Blackduck) <https://heartbleed.com/>

#### 사실 (원문)

| 항목 | 원문 |
|---|---|
| 결함 | "A missing bounds check in the handling of the TLS heartbeat extension can be used to reveal up to 64k of memory to a connected client or server."(OpenSSL 권고) |
| 영향 판 | NVD: "OpenSSL 1.0.1 before 1.0.1g". OpenSSL 권고: "Only 1.0.1 and 1.0.2-beta releases of OpenSSL are affected including 1.0.1f and 1.0.2-beta1." |
| 영향 | NVD: 프로세스 메모리의 민감 정보를 얻을 수 있다, "as demonstrated by reading private keys" |
| 수정 | OpenSSL 1.0.1g. 바로 올릴 수 없으면 `-DOPENSSL_NO_HEARTBEATS`로 재컴파일(OpenSSL 권고). 1.0.1g는 2014-04-07 공개(heartbleed.com) |
| 노출 기간 | heartbleed.com: 2011년 12월에 코드에 들어갔고, 2012-03-14 OpenSSL 1.0.1 릴리스로 퍼졌다 |
| 흔적 | heartbleed.com: "Exploitation of this bug does not leave any trace of anything abnormal happening to the logs." |
| 64KB의 뜻 | heartbleed.com: "There is no total of 64 kilobytes limitation to the attack, that limit applies only to a single heartbeat." |
| 발견 | OpenSSL 권고는 Google Security의 Neel Mehta에게 감사를 표한다. heartbleed.com은 Codenomicon 팀과 Neel Mehta가 독립적으로 발견했다고 적는다 |
| 점수·목록 | NVD 게시 2014-04-07, CVSS 3.1 7.5(`AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`), CISA KEV 등재 2022-05-04 |

#### 원리 — 상대가 말한 길이를 믿었다

```text
  하트비트 요청:  [선언 길이 = N] [실제 payload = 몇 바이트]
  응답 만들기:     N 바이트를 payload 시작에서부터 복사해 되돌려 줌
                   ↑ 실제 payload 길이와 N을 대조하지 않음
  결과:           payload 뒤에 있던 프로세스 메모리(키·세션·비밀번호가 있을 수 있음)가 응답에 실림
  수정:           선언 길이가 실제 레코드 길이보다 크면 버린다
```

- 원리 leaf: [24-memory-safety-exploits](../24-memory-safety-exploits/2-summary.md) 4절(힙 over-read)·장애 1. 24의 실험에서 일반 빌드는 경계 밖 64바이트 읽기를 오류 없이(exit 0) 끝냈고, AddressSanitizer 빌드만 `heap-buffer-overflow READ of size 64`를 보고했다.
- 해석: 흔적이 없었던 것은 프로그램 입장에서 정상 처리였기 때문이다. 그래서 사후 대응은 "새었는지 확인"이 아니라 "새었다고 보고 키를 바꾸는 것"이 됐다.
- TLS 프로토콜 자체의 결함이 아니라 한 구현의 메모리 안전 결함이다. TLS 본문은 [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md).

#### 막았을 통제 (해석)

| 층 | 통제 | leaf |
|---|---|---|
| 코드 | 신뢰 못 할 입력의 길이 필드를 실제 길이와 대조 | [24](../24-memory-safety-exploits/2-summary.md) 적용 |
| 테스트 | 퍼징 + AddressSanitizer 빌드(heartbleed.com은 Codenomicon이 보안 테스트 도구를 개선하다 찾았다고 적는다) | [24 장애 1](../24-memory-safety-exploits/2-summary.md) |
| 피해 반경 | 키 회전·인증서 재발급 절차가 평소에 돌고 있음, 전방 비밀성(과거 세션 키는 서버 개인키로 복원 불가) | [09](../09-randomness-and-key-management/2-summary.md) · [07](../07-key-exchange-forward-secrecy/2-summary.md) |
| 자산 | 어느 서버·장비가 어떤 OpenSSL 판을 쓰나 | [25](../25-supply-chain-security/2-summary.md) |

### 사건 2 — Equifax: 공개·패치된 Struts 취약점 미적용 (2017)

출처
- 미 GAO, "DATA PROTECTION: Actions Taken by Equifax and Federal Agencies in Response to the 2017 Breach", GAO-18-559, 2018년 8월 <https://www.gao.gov/products/gao-18-559> (gao.gov는 2026-10-07 접속 거부라 Internet Archive 사본 PDF를 읽었다)
- NVD CVE-2017-5638 <https://nvd.nist.gov/vuln/detail/CVE-2017-5638>
- Apache Struts 보안 공지 S2-045 <https://cwiki.apache.org/confluence/display/WW/S2-045>

#### 사실 — 타임라인 (GAO-18-559가 전한 Equifax의 설명)

| 시점 | 원문 내용 |
|---|---|
| 2017-03 | US-CERT가 Apache Struts 취약점을 공개. Equifax는 알림을 시스템 관리자들에게 돌렸지만 "the recipient list for the notice was out-of-date" — 패치 담당자에게 닿지 않았다 |
| 2017-03-10 | 미상의 개인들이 US-CERT가 "just 2 days earlier" 공개한 취약점이 있는지 Equifax 시스템을 스캔. 온라인 분쟁 포털 서버가 취약 판임을 발견하고 명령 실행을 확인. "No data was taken at this time." |
| 공개 1주 뒤 | Equifax가 네트워크를 스캔했지만 "the scan did not detect the vulnerability on the online dispute portal" |
| 2017-05-13 | 별도 사건으로 공격자들이 포털에 접근해 데이터 추출 시작 |
| ~2017-07-29 | 공격자는 포털의 DB 3개에서, 평문으로 저장된 자격 증명을 써서 관련 없는 DB 48개로 확장. 질의 약 9,000건. 암호화된 웹 프로토콜로 조금씩 반출. "The attack lasted for about 76 days before it was discovered." |
| 2017-07-29 | 네트워크 관리자가 정기 점검 중 트래픽 검사 장비의 설정 오류를 발견. 원인은 만료된 디지털 인증서로, 침해가 일어나기 "about 10 months" 전에 만료돼(발견일이 아니라 침해 기준) 그동안 암호화 트래픽을 검사하지 못했다. 인증서 교체 후 검사가 재개되자 침입 징후 확인 |
| 2017-07-30 | 의심 활동이 계속돼 포털을 오프라인으로 |
| 2017-09-07 | 침해 발표 |
| 2017-10-02 | 영향 인원을 1억 4,300만에서 1억 4,550만으로 정정(한 질의가 데이터를 반환하지 않았다고 잘못 판단했던 것) |

#### 사실 — 규모와 요인 (원문)

- 규모: 미국 소비자 "at least 145.5 million"과 미국 밖 "nearly 1 million"의 개인정보. 신용카드 번호 약 209,000명, 분쟁 문서(개인정보 포함) 약 182,000명. 2018-03-01에는 이름·부분 운전면허 정보가 도난된 약 240만 명을 추가로 밝혔다(일부는 기존 1억 4,550만에 포함 — 2018년 8월 기준 정확한 중복 수 미확정).
- Equifax가 꼽은 요인 넷(GAO 인용): **Identification**(패치 설치 때 포털의 Struts를 식별 못 함 — 낡은 수신자 목록, 스캔 미탐지), **Detection**(만료 인증서로 검사 장비가 제 기능을 못 함), **Segmentation**(DB가 서로 분리되지 않음), **Data Governance**(다른 DB 접근용 자격 증명이 평문으로 저장됨). 그리고 하나 더: DB 질의 빈도 제한이 없어 "approximately 9,000 such queries—many more than would be needed for normal operations"가 가능했다.
- 취약점(NVD): Struts 2 2.3.x(2.3.32 전)·2.5.x(2.5.10.1 전)의 Jakarta Multipart 파서가 파일 업로드 중 잘못된 예외 처리·오류 메시지 생성으로 조작된 `Content-Type` 등 헤더를 통해 원격 명령 실행을 허용. NVD 게시 2017-03-11, CVSS 3.1 9.8, CISA KEV 등재 2021-11-03. Apache 권고(S2-045)는 2.3.32 또는 2.5.10.1로 업그레이드를 권했다.

#### 원리 — 패치는 있었고, "어디에 깔렸나"가 없었다

```text
  공개(US-CERT) ──알림──▶ 낡은 수신자 목록 ──✗──▶ 포털 담당자 (못 받음)
                └──스캔──▶ 포털을 못 찾음 ───────────────────────────────▶ 패치 안 됨
  공격자: 3/10 스캔 → 5/13 진입 → DB 3개 → 평문 자격 증명 → DB 48개 → 질의 ~9,000건 → 조금씩 반출
  탐지:   검사 장비는 있었지만 인증서 만료로 암호화 트래픽 미검사(~10개월) → 7/29 인증서 교체 후에야 발견
```

- 원리 leaf: [25-supply-chain-security](../25-supply-chain-security/2-summary.md) 장애 1(미패치 구성 요소). 25가 적듯 도구보다 "누가 언제까지 올리는가"라는 절차가 핵심이었다.
- 해석: 네 요인 중 셋(Detection·Segmentation·Data Governance)은 취약점이 아니라 **피해 반경**을 정했다. 진입은 Struts였지만, 1억 4,550만 명 규모는 분리 부재·평문 자격 증명·질의 제한 부재가 만들었다([01](../01-security-principles/2-summary.md) 최소 권한·심층 방어).
- 해석: 탐지 장비의 인증서 만료는 [network/32](../../network/32-mtls-and-cert-operations/2-summary.md) 장애 1(갱신 누락)과 같은 운영 결함이다. 다만 여기서는 서비스가 멈추지 않고 **조용히 검사만 멈췄다** — [29](../29-security-symptom-index/2-summary.md) 9절의 "에러가 없는 증상"이다.

#### 막았을 통제 (해석)

| Equifax 요인 | 통제 | leaf |
|---|---|---|
| Identification | SBOM·자산 목록으로 "어디에 Struts가 있나"를 질의, 자산마다 소유자, 보안 패치 SLA | [25](../25-supply-chain-security/2-summary.md) |
| Detection | 인증서 만료를 지표·알람으로, 검사 장비가 "검사한 바이트 수 0"이 되면 알람 | [network/32](../../network/32-mtls-and-cert-operations/2-summary.md) · [26](../26-security-logging-and-audit/2-summary.md) |
| Segmentation | DB·서비스 분리, 포털 역할은 자기 DB만 | [01](../01-security-principles/2-summary.md) · [15](../15-access-control-models/2-summary.md) |
| Data Governance | 자격 증명을 평문으로 두지 않음, 시크릿 저장소·짧은 수명 자격 증명 | [09](../09-randomness-and-key-management/2-summary.md) |
| 질의 빈도 | 계정별 질의 상한·이상 탐지 | [28](../28-dos-and-abuse/2-summary.md) |

### 사건 3 — Capital One: 설정 오류 서버를 통한 클라우드 저장소 유출 (2019)

출처
- Capital One, "Information on the Capital One cyber incident" <https://www.capitalone.com/digital/facts2019/> (2026-10-07 열람)
- 미 법무부 워싱턴 서부지검 보도자료(2019-07-29) "Seattle Tech Worker Arrested for Data Theft Involving Large Financial Services Company"와 첨부 공소장(Case 2:19-mj-00344, 2019-07-29 제출) <https://www.justice.gov/usao-wdwa/pr/seattle-tech-worker-arrested-data-theft-involving-large-financial-services-company> (justice.gov는 2026-10-07 접속 거부라 Internet Archive 사본을 읽었다. 공소장은 스캔 PDF라 페이지 이미지로 읽었다)
- 미 법무부 워싱턴 서부지검 보도자료(2022-06-17) "Former Seattle tech worker convicted of wire fraud and computer intrusions" (Internet Archive 사본)
- 미 OCC 보도자료 NR 2020-101(2020-08-06) "OCC Assesses $80 Million Civil Money Penalty Against Capital One" <https://www.occ.gov/news-issuances/news-releases/2020/nr-occ-2020-101.html>
- Wyden·Warren 상원의원 보도자료(2019-10-24) "Wyden and Warren to FTC: Investigate Amazon's Negligence in Capital One Hack" (Internet Archive 사본)
- AWS Security Blog(2019-11-19) "Add defense in depth against open firewalls, reverse proxies, and SSRF vulnerabilities with enhancements to the EC2 Instance Metadata Service" <https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/>

#### 사실 — 타임라인과 규모 (원문)

| 시점 | 원문 내용 |
|---|---|
| 2019-03-22·23 | 무단 접근이 일어난 날(회사 공지: "This occurred on March 22 and 23, 2019") |
| 2019-04-21 | 공소장: GitHub 파일(타임스탬프 2019-04-21)에 특정 서버의 IP, 명령 세 개, 700개가 넘는 폴더·버킷 목록. Capital One 로그에 그 날 목록 명령이 실행된 기록 |
| 2019-07-17 | 외부인이 Capital One의 책임 있는 공개(Responsible Disclosure) 주소로 "leaked s3 data" 메일(공소장). 회사 공지: "The configuration vulnerability was reported to us by an external security researcher through our Responsible Disclosure Program on July 17, 2019." |
| 2019-07-19 | 회사가 침해를 확인 |
| 2019-07-29 | 피의자 체포, 공소장 제출, 회사 발표 |
| 2020-08-06 | OCC가 8천만 달러 민사 제재금 부과 |
| 2022-06-17 | 배심 유죄 평결(전신 사기, 보호된 컴퓨터 무단 접근 5건, 보호된 컴퓨터 손상). 접근 장치 사기·가중 신원 도용은 무죄 |

- 규모(회사 공지): 미국 약 1억 명, 캐나다 약 600만 명. 신용카드 고객의 사회보장번호 약 140,000개, 연결 은행 계좌번호 약 80,000개, 캐나다 사회보험번호 약 100만 개. "no credit card account numbers or log-in credentials were compromised". 2021-01-27에 사회보장번호가 포함된 약 4,700명을 추가로 확인(2021-02-22 갱신).
- 2022 법무부 보도자료: 회사는 8천만 달러 제재금을 받고 고객 소송을 1억 9천만 달러에 합의했다. 피고인은 직접 만든 도구로 AWS 계정을 훑어 "misconfigured accounts"를 찾았고, Capital One을 포함해 30개가 넘는 기관의 데이터를 내려받았다.

#### 사실 — 무엇이 깨졌나: 원문이 쓴 말

- 2019 법무부 보도자료: "The intrusion occurred through a misconfigured web application firewall that enabled access to the data."
- 공소장(¶10~11): "A firewall misconfiguration permitted commands to reach and be executed by that server, which enabled access to folders or buckets of data in Capital One's storage space at the Cloud Computing Company." 첫 명령은 `*****-WAF-Role`이라는 계정의 보안 자격 증명을 얻었고, 둘째는 그 역할로 버킷 이름을 나열했고, 셋째는 그 역할에 권한이 있는 버킷에서 데이터를 복사했다.
- OCC: 제재 사유는 "the bank's failure to establish effective risk assessment processes prior to migrating significant information technology operations to the public cloud environment and the bank's failure to correct the deficiencies in a timely manner."
- "SSRF"라는 말은 공소장·회사 공지·OCC 발표에 없다. Wyden·Warren 보도자료(2019-10-24)가 "a hacker stole the personal information of 100 million Americans from Capital One using a popular cyberattack technique known as a 'server side request forgery' (SSRF)"라고 썼다.

#### 원리 — 서버가 대신 요청하고, 그 서버의 역할이 넓었다 (해석)

```text
  외부 ──요청──▶ [WAF 역할의 서버 (설정 오류)] ──대신 요청──▶ 인스턴스 메타데이터 ──▶ *-WAF-Role 임시 자격 증명
                                                                                        │
  외부 ◀──────────────────────── 자격 증명으로 직접 ───────────────────────────────────────┘
       ──▶ 버킷 목록 나열 ──▶ 그 역할이 읽을 수 있는 버킷 복사 (700개가 넘는 폴더·버킷 목록)
```

- 해석: 공소장은 "명령이 서버에 닿아 실행됐고 첫 명령이 역할 자격 증명을 얻었다"까지만 적는다. 그 자격 증명이 인스턴스 메타데이터(`169.254.169.254`)에서 왔고 경로가 SSRF였다는 것은 상원의원 서한 같은 이후 문서와 원리([22-ssrf](../22-ssrf/2-summary.md))에 기댄 해석이다.
- 원리 leaf: [22](../22-ssrf/2-summary.md) 장애 1(메타데이터 접근 로그 뒤 자격 증명 오용) · [02](../02-threat-modeling/2-summary.md) 장애 2(서버에서 나가는 요청을 위협 모델에 그리지 않음) · [01](../01-security-principles/2-summary.md) 장애 3(자격 증명 하나로 모든 버킷).
- 해석: WAF 역할에 수많은 데이터 버킷 읽기 권한이 있었다는 점이 피해 크기를 정했다. 진입 결함과 피해 반경은 다른 통제다.
- AWS는 2019-11-19 IMDSv2(세션 토큰을 `PUT`으로 받아야 하는 메타데이터 방식)를 발표했다. 블로그 제목 자체가 "open firewalls, reverse proxies, and SSRF vulnerabilities"에 대한 심층 방어다. IMDSv2의 동작·홉 제한은 [22](../22-ssrf/2-summary.md) 적용 4.

#### 막았을 통제 (해석)

| 층 | 통제 | leaf |
|---|---|---|
| 진입 | 서버발 요청의 목적지 허용 목록, 메타데이터·사설 대역 차단, egress 정책 | [22](../22-ssrf/2-summary.md) · [network/48](../../network/48-firewalls-and-network-policy/2-summary.md) |
| 자격 증명 | IMDSv2 필수(토큰 + 작은 홉 제한) | [22](../22-ssrf/2-summary.md) 적용 4 |
| 피해 반경 | 역할마다 필요한 버킷만(최소 권한), 데이터 버킷 접근은 그 서비스 역할로 한정 | [01](../01-security-principles/2-summary.md) · [15](../15-access-control-models/2-summary.md) |
| 탐지 | 역할이 평소 쓰지 않는 API(버킷 나열)·TOR 출구 출처에 알람 — 공소장 ¶13은 "the *****-WAF-Role account does not, in the ordinary course of business, invoke the List Buckets Command"라고 적는다 | [26](../26-security-logging-and-audit/2-summary.md) |
| 거버넌스 | 클라우드 이전 전 위험 평가(OCC 제재 사유) | [02](../02-threat-modeling/2-summary.md) |

### 사건 4 — Log4Shell: 로그 메시지 안 문자열을 lookup으로 실행 (CVE-2021-44228, 2021-12-10 공개)

출처
- NVD CVE-2021-44228 <https://nvd.nist.gov/vuln/detail/CVE-2021-44228> · CVE-2021-44832 (API로 2026-10-07 조회)
- Apache Logging Services 보안 페이지 <https://logging.apache.org/security.html> (2026-10-07 열람)
- 미 CSRB, "Review of the December 2021 Log4j Event", 2022-07-11 <https://www.cisa.gov/sites/default/files/publications/CSRB-Report-on-Log4-July-11-2022_508.pdf> (cisa.gov는 2026-10-07 접속 거부라 Internet Archive 사본 PDF를 읽었다)

#### 사실 — 타임라인 (CSRB 보고서 원문)

| 시점 | 원문 내용 |
|---|---|
| 2013 | Log4j 2 정식 출시(2014) 전에, 표준 절차로 커뮤니티가 낸 "JNDI Lookup plugin support" 기능을 받아들임 |
| 2021-11-24 | Alibaba Cloud 보안팀 엔지니어가 Apache Software Foundation(ASF)에 JNDI 기능의 취약점을 보고 |
| 2021-12-05·06 | ASF가 수정을 저장소에 커밋(12-05), 릴리스 후보 2.15.0-rc1 태그(12-06). 이때는 보안 권고를 내지 않음 |
| 2021-12-09 | 보고자가 WeChat에서 이 취약점이 논의된다고 ASF에 알림. 그 게시물에 가려진 개념 증명 스크린샷 |
| 2021-12-10 | ASF가 일정을 앞당겨 2.15.0 공개, CVE-2021-44228 공개. 같은 날 CISA 성명. (CISA KEV 등재 2021-12-10과 CVSS 3.1 10.0은 NVD 레코드) |

#### 사실 — 영향과 평가 (원문)

- NVD 설명: "An attacker who can control log messages or log message parameters can execute arbitrary code loaded from LDAP servers when message lookup substitution is enabled. From log4j 2.15.0, this behavior has been disabled by default. From version 2.16.0 (along with 2.12.2, 2.12.3, and 2.3.1), this functionality has been completely removed." 또 "this vulnerability is specific to log4j-core". NVD CVSS 3.1 10.0(`AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H`).
- Apache 보안 페이지: 영향 판 `[2.0-beta9, 2.3.1) ∪ [2.4, 2.12.2) ∪ [2.13.0, 2.15.0)`, "Applications using only the log4j-api JAR file without the log4j-core JAR file are not impacted". 발견자는 Alibaba Cloud Security Team의 Chen Zhaojun.
- 후속 CVE가 이어졌다(CVE-2021-45046·45105·44832 — 판별 정리는 [23](../23-deserialization-and-parser-attacks/2-summary.md) 적용 4). 마지막 CVE-2021-44832의 수정판을 NVD는 "2.17.1, 2.12.4, and 2.3.2"로, 2026-10-07에 연 Apache 보안 페이지는 2.17.0(Java 8 이상)·2.12.3·2.3.1로 적어 두 출처가 다르다. Java 8 이상에서 2.17.1 이상이면 두 기준을 모두 만족한다.
- CSRB의 평가
  - "there is no comprehensive 'customer list' for Log4j, or even a list of where it is integrated as a sub-system" — 방어자는 어디에 Log4j를 쓰는지부터 찾아야 했다.
  - 한 연방 부처는 대응에 33,000시간을 썼다고 보고했다.
  - 악용은 "occurred at lower levels than many experts predicted"였고, 위원회는 그 시점까지 중요 기반 시설에 대한 중대한 Log4j 기반 공격을 알지 못했다.
  - "The Board assesses that Log4j is an 'endemic vulnerability' and that vulnerable instances of Log4j will remain in systems for many years to come, perhaps a decade or longer."

#### 원리 — 데이터가 명령 문법을 지나갔다

```text
  사용자 입력 (헤더·검색어·사용자 이름)
        │  log.info("user-agent={}", ua)
        ▼
  포맷된 메시지 안에서 ${...}를 다시 찾아 치환 (message lookup, log4j-core 2.14.1까지 기본)
        │
        ▼
  JNDI lookup → 외부 디렉터리 서버 조회 → 원격 코드 로드
```

- 원리 leaf: [23](../23-deserialization-and-parser-attacks/2-summary.md) 4절·장애 1. 23의 실험은 JNDI 없이 무해한 `${java:version}`·`${sys:…}`만으로, log4j-core 2.14.1이 로그 메시지 안의 lookup을 실행하고 2.24.3은 하지 않음을 보였다.
- 해석: [18-injection](../18-injection/2-summary.md)과 같은 모양이다. 파라미터 바인딩(`{}`)으로 데이터를 넣었는데도, 바인딩 **뒤의** 문자열을 다시 해석하는 단계가 있었다. 데이터와 명령의 문맥 분리가 한 단계 뒤에서 깨졌다.
- 해석: 피해가 커진 이유는 결함의 크기보다 **분포**다. "사용자 입력을 로그에 남기는 거의 모든 경로"가 입구였고, log4j-core는 직접 고르지 않은 전이 의존성·셰이딩된 jar로 퍼져 있었다(CSRB의 "customer list" 부재).

#### 실험: 배포물 안의 log4j-core 판 찾기 (`JarInventory.java`)

CSRB가 지적한 "어디에 있나"를 작은 예로 확인했다. 가짜 jar 넷을 만들었다(실제 log4j 코드는 없다 — `pom.properties`와 빈 클래스 이름만). 파일 이름에 `log4j`가 없는 것도 있다.

```java
static final String POM = "META-INF/maven/org.apache.logging.log4j/log4j-core/pom.properties";

static void scan(String where, InputStream in, List<String> out) throws IOException {
    ZipInputStream z = new ZipInputStream(in);
    for (ZipEntry e; (e = z.getNextEntry()) != null; ) {
        if (e.getName().equals(POM)) {                                   // 합쳐진(평평한)·셰이딩된 jar 안의 메타데이터
            Properties p = new Properties();
            p.load(new ByteArrayInputStream(z.readAllBytes()));
            out.add(where + " -> log4j-core " + p.getProperty("version"));
        } else if (e.getName().endsWith(".jar")) {                       // Spring Boot fat jar의 BOOT-INF/lib/*.jar
            scan(where + "!/" + e.getName(), new ByteArrayInputStream(z.readAllBytes()), out);
        }
    }
}
// 찾은 판을 2.17.1과 비교해 표시한다
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-07 — 결정적 출력. 첫 네 줄은 만든 가짜 jar 목록 `ls jars`)

```text
billing-service.jar
orders-app.jar
report-tool.jar
vendor-sdk-shaded.jar
billing-service.jar -> log4j-core 2.14.1   << 2.17.1 미만: 올릴 대상
orders-app.jar!/BOOT-INF/lib/log4j-core-2.16.0.jar -> log4j-core 2.16.0   << 2.17.1 미만: 올릴 대상
vendor-sdk-shaded.jar -> log4j-core 2.17.1   ok
log4j-core 발견 3건 (jar 파일 이름에 log4j가 없는 것 포함)
```

- 관찰: 파일 이름이 `billing-service.jar`·`vendor-sdk-shaded.jar`처럼 log4j와 무관해도 안의 메타데이터로 찾았다. fat jar 안의 중첩 jar도 한 단계 들어가 찾았다.
- 관찰: `log4j-api`만 든 `report-tool.jar`는 목록에 없다. Apache 페이지대로 api만 쓰는 앱은 이 CVE와 무관하다.
- 한계: 셰이딩 도구가 `pom.properties`를 지우거나 패키지 이름을 바꾸면 이 방법으로는 못 찾는다. 그때는 클래스 이름·내용 해시로 찾는 도구가 필요하다. 비교 기준 2.17.1은 Java 8 이상 기준이다. Java 7·6용 보안 판(2.12.x·2.3.x 계열)은 따로 판정해야 하는데 이 코드는 그것을 "미만"으로 표시한다.
- 해석: 빌드 때 SBOM을 만들어 두면 이 스캔은 "질의"가 된다([25](../25-supply-chain-security/2-summary.md)). CSRB 권고에도 SBOM 도구·채택 개선이 들어 있다(권고 12 "Improve Software Bill of Materials (SBOM) tooling and adoptability").

#### 막았을 통제 (해석)

| 층 | 통제 | leaf |
|---|---|---|
| 설계 | 로그 메시지 같은 데이터 문맥에서 해석 기능을 끈다(2.15.0의 기본값 변경, 2.16.0의 제거가 이것) | [23](../23-deserialization-and-parser-attacks/2-summary.md) · [18](../18-injection/2-summary.md) |
| 자산 | SBOM으로 전이 의존성까지 판 질의 | [25](../25-supply-chain-security/2-summary.md) |
| 피해 반경 | 앱 서버의 egress 차단(외부 디렉터리 서버 조회가 나가지 못함) | [22](../22-ssrf/2-summary.md) · [network/48](../../network/48-firewalls-and-network-policy/2-summary.md) |
| 탐지 | 접근 로그의 `${` 패턴, 앱 서버발 비정상 아웃바운드(LDAP 389 등) | [23 장애 1](../23-deserialization-and-parser-attacks/2-summary.md) · [29](../29-security-symptom-index/2-summary.md) 8절 |

### 사건 5 — xz/liblzma 백도어: 정상 릴리스 tarball에 심긴 악성 코드 (CVE-2024-3094, 2024-03-29 공개)

출처
- Andres Freund, "backdoor in upstream xz/liblzma leading to ssh server compromise", oss-security, 2024-03-29 <https://www.openwall.com/lists/oss-security/2024/03/29/4>
- NVD CVE-2024-3094 <https://nvd.nist.gov/vuln/detail/CVE-2024-3094> (API로 2026-10-07 조회)
- CISA Alert(2024-03-29) "Reported Supply Chain Compromise Affecting XZ Utils Data Compression Library, CVE-2024-3094" (cisa.gov 접속 거부라 Internet Archive 사본)
- Lasse Collin(XZ Utils 유지보수자), "XZ Utils backdoor" <https://tukaani.org/xz-backdoor/> (2026-10-07 열람)

#### 사실 (원문)

- 발견 경위(Freund): 몇 주 동안 Debian sid에서 liblzma 주변의 이상 증상 — "logins with ssh taking a lot of CPU, valgrind errors" — 을 보다가 원인을 찾았다. "The upstream xz repository and the xz tarballs have been backdoored."
- 관찰된 지연(Freund): 존재하지 않는 사용자로 로컬 ssh 접속 시간이 `real 0m0.299s`(이전) → `real 0m0.807s`(백도어 liblzma 설치 후).
- 위치(Freund): 백도어의 한 부분은 "*solely in the distributed tarballs*" — 5.6.0·5.6.1 릴리스 tarball의 빌드 스크립트(`m4/build-to-host.m4`)에 git에 없는 줄이 있었다. 코드의 대부분은 저장소의 테스트 파일 두 개에 난독화된 형태로 커밋돼 있었다.
- 경로(Freund): openssh는 liblzma를 직접 쓰지 않는다. Debian 등 여러 배포판이 systemd 알림을 위해 openssh를 패치했고, libsystemd가 lzma에 의존한다.
- 범위(Freund): "Luckily xz 5.6.0 and 5.6.1 have not yet widely been integrated by linux distributions, and where they have, mostly in pre-release versions."
- NVD: "Malicious code was discovered in the upstream tarballs of xz, starting with version 5.6.0." CVSS 3.1 10.0(NVD·Red Hat 모두). NVD 레코드에 CISA KEV 등재 표기는 없다(2026-10-07 조회).
- CISA(2024-03-29): XZ Utils 5.6.0·5.6.1에 악성 코드. 개발자·사용자에게 "XZ Utils 5.4.6 Stable" 같은 오염되지 않은 판으로 내리고, 악성 활동을 찾아 보고하라고 권고.
- Collin: "XZ Utils 5.6.0 and 5.6.1 release tarballs contain a backdoor. These tarballs were created and signed by Jia Tan." 깨끗한 새 릴리스는 2024-05-29.

#### 원리 — 서명된 정상 릴리스가 악성일 때

```text
  git 저장소 ─────────────────────────────────┐      (테스트 파일로 위장한 난독화 데이터만 — 혼자서는 무해)
                                              ▼
  릴리스 tarball = git 내용 + 빌드 스크립트 한 줄 ──▶ 배포판 패키지 빌드 ──▶ liblzma ──▶ libsystemd ──▶ (패치된) sshd
                   ↑ git에 없음                     (x86-64 Linux 패키지 빌드 등 조건에서만 주입)
  검증:  tarball 서명 ✓ (유지보수자 권한자가 서명) · 해시 고정 ✓ (악성 바이트의 해시가 고정될 뿐)
  발견:  sshd 로그인 0.3초 → 0.8초, valgrind 오류 — 성능 이상을 끝까지 판 한 사람
```

- 원리 leaf: [25](../25-supply-chain-security/2-summary.md) 장애 2(정상 버전에 백도어). 서명과 해시 고정은 "이 바이트를 그 사람이 냈다"를 증명할 뿐, 그 사람이 악의가 없다는 것은 증명하지 않는다.
- 해석: 배포 tarball과 저장소 태그의 소스 대조, 그리고 재현 빌드(같은 소스·조건으로 독립적으로 만든 결과물끼리 비교)가 이 부류를 겨냥한 통제다. Freund는 GitHub가 저장소에서 직접 만드는 "source code" 링크에는 이 줄이 없다고 적었다.
- 해석: 탐지는 보안 도구가 아니라 **성능 이상**에서 왔다. [29](../29-security-symptom-index/2-summary.md)의 표에 없는 모양의 증상이다. 이상을 원인까지 추적하는 문화가 마지막 방어선이었다.

#### 막았을 통제 (해석)

| 층 | 통제 | leaf |
|---|---|---|
| 빌드 | 릴리스 tarball 대신 저장소 태그에서 빌드, tarball과 태그의 소스 대조, 재현 빌드(독립 빌드 결과물끼리 비교) | [25](../25-supply-chain-security/2-summary.md) |
| 도입 속도 | 갓 나온 판을 바로 쓰지 않음(`minimumReleaseAge`), 개발판(sid·rawhide)과 운영 분리 — 실제로 안정판 대부분은 영향 밖이었다 | [25](../25-supply-chain-security/2-summary.md) |
| 의존성 표면 | sshd 같은 민감 프로세스에 불필요한 라이브러리를 링크하지 않음(해석 — 경로는 배포판 패치의 libsystemd였다) | [01](../01-security-principles/2-summary.md) |
| 대응 | 영향 판 목록화 → 오염 안 된 판으로 롤백(CISA 권고 5.4.6) | [25](../25-supply-chain-security/2-summary.md) |

### 다섯 사건 비교

| | Heartbleed | Equifax | Capital One | Log4Shell | xz |
|---|---|---|---|---|---|
| 처음 깨진 것 | 구현의 경계 검사 | 패치 적용 절차 | 서버 설정(대신 요청) | 데이터 문맥의 해석 기능 | 유지보수자 신뢰·릴리스 과정 |
| 원리 leaf | 24 | 25 | 22 | 23 · 18 | 25 |
| 공개 → 패치 | 같은 날(1.0.1g) | 패치는 있었음 | (설정 문제) | 같은 날(2.15.0), 후속 CVE 3개 | 공개 당일 롤백 권고 |
| 탐지 | 외부 연구자 | 내부 점검(인증서 교체 후) | 외부 제보(책임 있는 공개) | 외부 보고 → 공개 | 개발자의 성능 이상 추적 |
| 피해를 키운 것 | 약 2년 노출, 무흔적 | 분리 부재·평문 자격 증명·꺼진 탐지 | 역할의 넓은 권한 | 어디 있는지 모름 | (조기 발견으로 제한적) |
| 공통 통제 | 키 회전 절차 | SBOM·소유자·만료 알람 | 최소 권한·IMDSv2 | SBOM·egress | 재현 빌드·도입 지연 |

- 해석: 다섯 중 넷의 탐지가 외부 또는 우연이었다. 탐지 통제가 정상 동작한 것은 Equifax의 검사 장비뿐인데, 그것도 인증서 만료로 꺼져 있다가 교체 뒤에야 작동했다.

## 쓰이는 자료구조·알고리즘

- **경계 검사(길이 필드 대조)** — 선언 길이 ≤ 실제 길이. Heartbleed의 수정 한 줄([24](../24-memory-safety-exploits/2-summary.md)).
- **의존성 그래프 탐색** — 전이 의존성까지 내려가 판을 찾는 것(Log4Shell). SBOM은 이 그래프를 미리 펼쳐 둔 목록이다([25](../25-supply-chain-security/2-summary.md)). 위 실험의 중첩 jar 재귀가 그 축소판이다.
- **문맥 인코딩·분리** — 데이터 문맥과 명령 문맥을 섞지 않는다. 치환을 한 번만 하고 결과를 다시 해석하지 않는다(Log4Shell, [18](../18-injection/2-summary.md)).
- **CIDR 대역 판정** — 서버발 요청의 목적지가 링크 로컬(`169.254.0.0/16`)·사설 대역인지(Capital One, [22](../22-ssrf/2-summary.md)).
- **해시·서명 대조** — 같은 소스로 독립적으로 빌드한 결과물끼리의 해시 비교(재현 빌드)와 tarball·태그 소스 대조, 서명은 출처만 증명(xz, [04](../04-hash-functions-and-digests/2-summary.md) · [06](../06-public-key-and-signatures/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 읽는 순서

```text
  ① 진입 결함은 무엇인가                → leaf 원리 (24·25·22·23)
  ② 공개부터 악용까지, 악용부터 탐지까지 → 시간이 어디서 갔나 (Equifax: 3/8 공개 → 5/13 진입 → 7/29 탐지, 약 76일)
  ③ 무엇이 피해 반경을 정했나            → 권한·분리·자격 증명 저장 (진입 결함과 다른 통제)
  ④ 탐지는 누가 했나                    → 내부 통제인가, 외부·우연인가
  ⑤ "우리 시스템이면?"                  → ①~④를 우리 자산 목록·권한·알람에 대입
```

- ②의 Equifax 날짜: GAO는 3월 10일 스캔이 US-CERT 공개 "2일 뒤"라고 적는다. 그래서 공개를 3월 8일로 계산했다(해석).

### 2. 우리 시스템에 대입하는 점검 — 취약 예 → 고친 예

```java
// 취약: 상대가 준 길이를 그대로 믿는다 (Heartbleed 모양)
static byte[] echo(ByteBuffer req) {
    int claimed = req.getShort() & 0xFFFF;          // 상대가 선언한 길이
    byte[] out = new byte[claimed];
    req.get(out);                                   // Java는 BufferUnderflowException을 던진다 — C였다면 옆 메모리를 읽었다
    return out;
}

// 고친 예: 선언 길이를 실제 남은 길이와 대조하고, 어긋나면 버린다
static byte[] echoChecked(ByteBuffer req) {
    if (req.remaining() < 2) throw new IllegalArgumentException("short record");
    int claimed = req.getShort() & 0xFFFF;
    if (claimed > req.remaining()) throw new IllegalArgumentException("length mismatch: " + claimed + " > " + req.remaining());
    byte[] out = new byte[claimed];
    req.get(out);
    return out;
}
```

(실험 `Echo.java`, OpenJDK 21.0.12, docker `--network none`, 2026-10-07 — 선언 64, 실제 4바이트 `bird`)

```text
echo: java.nio.BufferUnderflowException
echoChecked: java.lang.IllegalArgumentException: length mismatch: 64 > 4
ok: bird
```

- Java는 배열·버퍼 경계를 런타임이 검사하므로 같은 실수가 메모리 유출 대신 예외로 끝난다. 그래도 예외를 잡아 삼키고 0을 채워 응답하는 식이면 프로토콜 오류가 조용히 지나간다. 길이 대조를 명시적으로 두고, 어긋나면 레코드를 버린다(OpenSSL 1.0.1g의 수정 방향).

```yaml
# 탐지가 "조용히 꺼짐"을 알람으로 (Prometheus 규칙 예 — 지표 이름은 예시)
groups:
- name: detection-health
  rules:
  - alert: InspectionCertExpiringSoon          # Equifax: 검사 장비 인증서가 침해 ~10개월 전부터 만료 상태였다
    expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 21
  - alert: InspectedBytesZero                  # 검사 장비가 아무것도 검사하지 않는다
    expr: sum(rate(ids_inspected_bytes_total[15m])) == 0
  - alert: RoleUnusualApi                      # Capital One: 그 역할이 평소 부르지 않는 API
    expr: sum by (role) (increase(cloud_api_calls_total{api="ListBuckets", role=~".*-waf-.*"}[1h])) > 0
```

- `probe_ssl_earliest_cert_expiry`는 Prometheus blackbox_exporter가 내는 지표로, 프로브가 접속한 TLS 대상이 **제시한** 인증서의 만료다. 검사 장비가 내부에서 쓰는 인증서는 그 인증서를 제시하는 엔드포인트를 프로브하거나, 장비·인증서 저장소에서 만료일을 따로 수집해야 감시된다. 나머지 두 지표 이름은 예시다 — 자기 환경의 검사 장비·클라우드 감사 로그 수집기가 내는 이름으로 바꾼다.
- 21일·15분·1시간은 예시 값이다.

### 3. 사고가 났을 때 순서 — 다섯 사건의 공통 교훈

1. 영향 판·영향 자산을 목록화한다(SBOM·자산 목록 — Log4Shell·xz·Equifax).
2. 새었을 수 있는 비밀을 회전한다(흔적이 없어도 — Heartbleed, 역할 자격 증명 — Capital One). 절차는 [09](../09-randomness-and-key-management/2-summary.md) 적용 4.
3. 패치·롤백한다. 롤백 대상 판이 오염되지 않았는지 확인한다(xz: CISA 권고 5.4.6).
4. 감사 로그로 범위를 산정한다. Equifax 조사는 공격자가 지우지 않은 로그로 명령을 재구성했다(GAO: "electronic logs that had not been damaged or erased by the attackers")([26](../26-security-logging-and-audit/2-summary.md)).
5. 사후 검토에서 진입 결함과 피해 반경 통제를 따로 고친다([reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md)).

## 장애 시나리오와 대처

다섯 사건에서 뽑은, 우리 조직에서 같은 모양으로 날 수 있는 장애다.

### 1. 보안 패치 알림이 담당자에게 닿지 않는다 (Equifax형) ⚠

- **현상**: 공개된 취약점 공지에 "적용 완료"로 답했는데 몇 달 뒤 그 경로로 침해된다.
- **보이는 형태**: 사후 조사에서 해당 서버가 패치 대상 목록에 없었다. 알림 메일의 수신자 목록이 조직 변경 전 그대로다. 스캐너가 그 자산을 못 봤다.
- **원인**: "어디에 무엇이 깔렸나"를 사람의 기억과 메일 목록에 맡겼다(GAO: 낡은 수신자 목록, 스캔 미탐지).
- **대처**: 자산마다 소유자를 둔 목록과 SBOM, 보안 패치 SLA. 스캔 결과에 "스캔하지 못한 자산" 수를 같이 보고한다([25 장애 1](../25-supply-chain-security/2-summary.md)).

### 2. 탐지 장치가 조용히 꺼져 있다 (Equifax형) ⚠

- **현상**: 침입이 몇 달 동안 이어졌는데 경보가 한 번도 울리지 않았다.
- **보이는 형태**: 검사 장비는 "정상 동작"으로 표시. 실제로는 인증서 만료로 암호화 트래픽을 통과시키고 있었다(GAO: 약 10개월). 에러 로그 없음.
- **원인**: 탐지 장치의 건강 상태를 "프로세스가 떠 있나"로만 봤다. 검사량을 보지 않았다.
- **대처**: 탐지 장치의 검사량·인증서 만료일을 지표로 두고 "0으로 떨어짐"에 알람(적용 2). [29](../29-security-symptom-index/2-summary.md) 장애 5와 같은 교훈이다.

### 3. 서버 역할의 자격 증명이 밖에서 쓰인다 (Capital One형)

- **현상**: 인스턴스 역할의 임시 자격 증명이 그 인스턴스가 아닌 곳(TOR 출구·VPN)에서 쓰인다.
- **보이는 형태**: 클라우드 감사 로그에 그 역할이 평소 부르지 않는 API(버킷 나열) 호출. 앱 로그에 메타데이터 주소 요청([22 장애 1](../22-ssrf/2-summary.md)).
- **원인**: 서버가 외부 입력으로 요청을 대신 보낼 수 있었고, 메타데이터가 토큰 없이 응답했고, 그 역할의 권한이 넓었다.
- **대처**: 즉시 그 역할 자격 증명 무효화·회전. 목적지 허용 목록, IMDSv2 필수, 역할 권한 축소. 역할별 "평소 API" 기준선과 이탈 알람.

### 4. 취약 라이브러리가 어디 있는지 모른다 (Log4Shell형) ⚠

- **현상**: 긴급 공지가 떴는데 "우리 서비스가 그 라이브러리를 쓰나"에 며칠째 답하지 못한다.
- **보이는 형태**: 직접 의존성 목록에는 없다. 그런데 fat jar·셰이딩된 SDK·벤더 제품 안에 들어 있다(위 실험: 파일 이름에 log4j가 없는 jar에서 2.14.1·2.16.0 발견).
- **원인**: 전이 의존성과 배포물 내용을 목록으로 갖고 있지 않다(CSRB: "no comprehensive 'customer list'").
- **대처**: 빌드마다 SBOM 생성·보관, 배포물 스캔, 벤더에 SBOM 요구. 패치 전까지는 egress 차단 같은 피해 반경 통제로 시간을 번다([23 장애 1](../23-deserialization-and-parser-attacks/2-summary.md)).

### 5. 서명·해시가 맞는 공식 판이 악성이다 (xz형)

- **현상**: 공식 서명이 있는 새 판으로 올린 뒤 특정 프로세스가 느려지거나 이상 동작한다.
- **보이는 형태**: 서명 검증 통과, 체크섬 일치. 성능 저하(xz: ssh 로그인 0.299초 → 0.807초)·valgrind 오류 같은 비보안 증상.
- **원인**: 서명은 "누가 냈나"만 증명한다. 릴리스 권한을 가진 사람이 악성 바이트를 냈다.
- **대처**: 갓 나온 판의 도입 지연, 저장소 태그에서 직접 빌드·tarball과 태그의 소스 대조·재현 빌드, 성능 이상을 원인까지 추적. 의심되면 직전 판으로 롤백([25 장애 2](../25-supply-chain-security/2-summary.md)).

## 핵심 문장

- Heartbleed(CVE-2014-0160, NVD 7.5): 하트비트 길이 필드를 믿은 경계 밖 읽기로 요청당 최대 64KB의 프로세스 메모리가 샜고, 로그에 흔적이 없었다. 수정은 길이 대조였고, 대응은 "새었다고 보고" 키를 바꾸는 것이었다.
- Equifax(GAO-18-559): 패치가 있던 Struts 취약점이 낡은 알림 목록과 스캔 미탐지로 남았고, 약 76일간 탐지되지 않았다. 1억 4,550만 명 규모는 분리 부재·평문 자격 증명·약 10개월 만료된 검사 장비 인증서가 만들었다.
- Capital One(2019): 공소장은 "방화벽 설정 오류로 명령이 서버에 닿았고 첫 명령이 WAF 역할 자격 증명을 얻었다"고 적는다. SSRF라는 분류는 이후 문서의 것이고, 피해 크기는 그 역할의 넓은 버킷 권한이 정했다.
- Log4Shell(CVE-2021-44228, NVD 10.0): 로그 메시지 안의 lookup이 데이터를 명령으로 바꿨다. CSRB는 사용처 목록이 없던 것을 대응의 걸림돌로, Log4j를 "endemic vulnerability"로 평가했다.
- xz(CVE-2024-3094): 백도어 일부는 릴리스 tarball에만 있었고 서명도 정상이었다. 발견은 ssh 로그인 0.3초 → 0.8초라는 성능 이상을 끝까지 판 한 개발자에게서 왔다.

## 관련 주제·근거

- 선행: [29-security-symptom-index](../29-security-symptom-index/2-summary.md) · [24-memory-safety-exploits](../24-memory-safety-exploits/2-summary.md) · [25-supply-chain-security](../25-supply-chain-security/2-summary.md) · [22-ssrf](../22-ssrf/2-summary.md) · [23-deserialization-and-parser-attacks](../23-deserialization-and-parser-attacks/2-summary.md) · [26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md) · [01-security-principles](../01-security-principles/2-summary.md)
- 다른 영역 실사건: [network/53-network-incidents](../../network/53-network-incidents/2-summary.md) · [engineering-practice/20-practice-incidents](../../engineering-practice/20-practice-incidents/2-summary.md) · [data-structure/44-ds-incidents](../../data-structure/44-ds-incidents/2-summary.md) · 사고 대응: [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md)
- 1차 출처
  - NVD CVE-2014-0160 · CVE-2017-5638 · CVE-2021-44228 · CVE-2021-44832 · CVE-2024-3094 — NVD API 2.0으로 2026-10-07 조회(게시일·CVSS 3.1·CISA KEV 등재일) <https://nvd.nist.gov/>
  - OpenSSL Security Advisory [07 Apr 2014] <https://www.openssl.org/news/secadv/20140407.txt> · heartbleed.com <https://heartbleed.com/>
  - GAO-18-559 Data Protection(2018-08) <https://www.gao.gov/products/gao-18-559> (Internet Archive 사본 PDF) · Apache Struts S2-045 <https://cwiki.apache.org/confluence/display/WW/S2-045>
  - Capital One "Information on the Capital One cyber incident" <https://www.capitalone.com/digital/facts2019/> · 미 법무부 WDWA 보도자료 2019-07-29·2022-06-17과 공소장 Case 2:19-mj-00344 (Internet Archive 사본) · OCC NR 2020-101 <https://www.occ.gov/news-issuances/news-releases/2020/nr-occ-2020-101.html> · Wyden·Warren 보도자료 2019-10-24 (Internet Archive 사본) · AWS Security Blog 2019-11-19(IMDSv2)
  - Apache Logging Services Security <https://logging.apache.org/security.html> · CSRB "Review of the December 2021 Log4j Event"(2022-07-11) (Internet Archive 사본 PDF)
  - oss-security 2024-03-29 Andres Freund <https://www.openwall.com/lists/oss-security/2024/03/29/4> · CISA Alert 2024-03-29(Internet Archive 사본) · tukaani.org "XZ Utils backdoor" <https://tukaani.org/xz-backdoor/>
- 실험
  - `JarInventory.java`·`MakeFakes.java` — 가짜 jar 넷(평평한 jar·fat jar 중첩·셰이딩 SDK·api만)에서 log4j-core 판 찾기. 코드 `scratchpad/sec/syn/inv/`, 명령 `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk sh -c 'java MakeFakes.java && java JarInventory.java jars'`(OpenJDK 21.0.12). 결정적 출력. 실제 log4j 코드는 쓰지 않았다.
  - Heartbleed 모양 over-read는 [24](../24-memory-safety-exploits/2-summary.md) 실험, 로그 lookup은 [23](../23-deserialization-and-parser-attacks/2-summary.md) 실험, SSRF 가드는 [22](../22-ssrf/2-summary.md) 실험에서 옮겼다(새로 돌리지 않음).
