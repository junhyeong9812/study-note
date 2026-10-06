# security/30-security-incidents — 정답

## 정답

### 1. 처음 깨진 곳과 피해를 키운 것

- Heartbleed: 하트비트 길이 필드를 믿은 경계 밖 읽기 / 약 2년 배포된 판(2012-03-14 1.0.1 → 2014-04-07 1.0.1g)과 로그에 흔적이 없음.
- Equifax: 공개·패치된 Struts 취약점 미적용 / 낡은 알림 수신자 목록·스캔 미탐지, 만료 인증서로 꺼진 트래픽 검사, 분리 안 된 DB, 평문 자격 증명, 질의 빈도 제한 부재.
- Capital One: 설정 오류로 서버가 외부 명령을 실행(대신 요청) / 그 서버 역할(`*****-WAF-Role`)의 넓은 버킷 권한.
- Log4Shell: 로그 메시지 안 문자열을 lookup으로 실행 / 어디에 들어 있는지 모르는 전이 의존성·셰이딩 jar.
- xz: 릴리스 권한자가 tarball에 악성 코드 / 배포판 빌드 파이프라인이 tarball을 그대로 받음(조기 발견으로 피해는 제한적).
- 나눠 보는 이유: 진입 결함을 막는 통제(경계 검사·패치·목적지 허용 목록)와 피해 반경을 줄이는 통제(최소 권한·분리·자격 증명 보관·탐지)는 다르다. 진입은 언젠가 뚫린다고 보면, 사고의 크기는 뒤쪽 통제가 정한다.

### 2. Heartbleed

- 결함(OpenSSL 권고): "A missing bounds check in the handling of the TLS heartbeat extension can be used to reveal up to 64k of memory to a connected client or server."
- 영향 판: NVD "OpenSSL 1.0.1 before 1.0.1g". OpenSSL 권고 "Only 1.0.1 and 1.0.2-beta releases ... including 1.0.1f and 1.0.2-beta1". 수정 1.0.1g(바로 못 올리면 `-DOPENSSL_NO_HEARTBEATS`로 재컴파일).
- NVD: 프로세스 메모리의 민감 정보를 얻을 수 있고 "as demonstrated by reading private keys". CVSS 3.1 7.5, KEV 2022-05-04 등재.
- 64KB는 전체 상한이 아니다. heartbleed.com: "There is no total of 64 kilobytes limitation to the attack, that limit applies only to a single heartbeat." 요청을 반복하면 더 읽는다.
- 흔적: "Exploitation of this bug does not leave any trace of anything abnormal happening to the logs." 그래서 "새었는지 확인"할 수 없었고, 대응은 새었다고 보고 키 회전·인증서 재발급을 하는 것이 됐다(해석).

### 3. Equifax 타임라인과 규모 (GAO-18-559)

- 2017-03: US-CERT 공개. 알림의 수신자 목록이 낡아 패치 담당자에게 닿지 않음. 공개 1주 뒤 스캔이 포털의 취약점을 못 찾음.
- 2017-03-10: 미상의 개인들이 US-CERT가 "2일 전" 공개한 취약점을 찾아 스캔, 포털에서 명령 실행 확인. 데이터 반출은 없었음.
- 2017-05-13: 별도 사건으로 진입, 데이터 추출 시작. DB 3개 → 평문 자격 증명으로 48개 추가. 질의 약 9,000건.
- 2017-07-29: 정기 점검에서 검사 장비의 만료 인증서를 교체하자 침입 징후 발견. 2017-07-30 포털 오프라인. 2017-09-07 발표. 2017-10-02 영향 인원 1억 4,300만 → 1억 4,550만 정정.
- 규모: 미국 소비자 최소 1억 4,550만, 미국 밖 약 100만. 신용카드 번호 약 209,000, 분쟁 문서 약 182,000.
- "약 76일": 공격(5-13 시작)이 발견(7-29)되기까지 이어진 기간("The attack lasted for about 76 days before it was discovered"). "약 10개월": 트래픽 검사 장비의 인증서가 침해 전에 이미 만료돼 있던 기간 — 그동안 암호화 트래픽이 검사되지 않았다.

### 4. 네 요인과 통제

- Identification(패치 때 포털의 Struts를 식별 못 함): SBOM·자산 목록·소유자·패치 SLA — 25.
- Detection(만료 인증서로 검사 장비 무력화): 인증서 만료·검사량 알람 — network/32, 26.
- Segmentation(DB 분리 없음): DB·서비스 분리, 최소 권한 — 01, 15.
- Data Governance(평문 자격 증명): 시크릿 저장소·짧은 수명 자격 증명 — 09.
- 덧붙인 하나(질의 빈도 제한 없음, 약 9,000건): 계정별 질의 상한·이상 탐지 — 28.
- 나누기: 진입 결함을 정한 것은 Identification이다. 피해 반경을 정한 것은 Detection(얼마나 오래)·Segmentation·Data Governance·질의 빈도(얼마나 넓고 많이)다(해석).

### 5. Capital One — 원문과 해석의 구분

- 2019 법무부 보도자료: "The intrusion occurred through a misconfigured web application firewall that enabled access to the data."
- 공소장 ¶10~11: "A firewall misconfiguration permitted commands to reach and be executed by that server, which enabled access to folders or buckets of data." 첫 명령은 `*****-WAF-Role` 계정의 보안 자격 증명을 얻었고, 둘째는 버킷 이름을 나열, 셋째는 그 역할에 권한이 있는 버킷에서 복사했다.
- 회사 공지: "configuration vulnerability", 2019-03-22·23에 발생, 2019-07-17 책임 있는 공개 프로그램으로 제보, 07-19 확인. 미국 약 1억 명·캐나다 약 600만 명.
- OCC(2020-08-06, 8천만 달러): 퍼블릭 클라우드로 IT 운영을 옮기기 전 효과적인 위험 평가 절차를 세우지 못했고 결함을 제때 고치지 못함.
- "SSRF"라는 말은 위 문서들에 없다. Wyden·Warren 보도자료(2019-10-24)가 SSRF라고 썼다. 자격 증명이 인스턴스 메타데이터에서 왔다는 설명은 이런 이후 문서와 원리(22)에 기댄 해석이다.
- 피해 크기: WAF 역할이 많은 데이터 버킷을 읽을 수 있었던 넓은 권한. 진입이 같아도 역할 권한이 좁았다면 피해가 작았다(해석, 01 최소 권한).

### 6. Log4Shell — CSRB

- 2013: Log4j 2 정식 출시(2014) 전, 커뮤니티가 낸 "JNDI Lookup plugin support"를 표준 절차로 받아들임.
- 2021-11-24: Alibaba Cloud 보안팀 엔지니어가 ASF에 보고.
- 2021-12-05·06: 수정 커밋, 2.15.0-rc1 태그. 보안 권고는 아직 없음.
- 2021-12-09: 보고자가 WeChat에서 논의 중이라고 ASF에 알림(가려진 개념 증명 스크린샷).
- 2021-12-10: 2.15.0과 CVE 공개, 같은 날 CISA 성명·KEV 등재, NVD 10.0.
- 걸림돌: "there is no comprehensive 'customer list' for Log4j, or even a list of where it is integrated as a sub-system" — 어디에 쓰는지부터 찾아야 했다. 연이은 추가 취약점으로 인한 혼란과 "patching fatigue", 연구자 스캔과 공격 스캔의 구분 어려움도 들었다. 한 연방 부처는 33,000시간을 썼다.
- "endemic vulnerability": 취약한 Log4j가 "many years to come, perhaps a decade or longer" 시스템에 남을 것이라는 평가다. 한 번의 긴급 패치로 끝나는 사건이 아니라는 뜻이다. 동시에 악용은 많은 전문가 예상보다 낮은 수준이었다고 적었다.

### 7. `JarInventory.java`

- 걸린 것: `billing-service.jar`(평평한 jar 안 log4j-core 2.14.1 — 올릴 대상), `orders-app.jar!/BOOT-INF/lib/log4j-core-2.16.0.jar`(fat jar 안 중첩 — 올릴 대상), `vendor-sdk-shaded.jar`(2.17.1 — ok). 파일 이름에 log4j가 없어도 내부 `pom.properties`로 찾았다.
- 안 걸린 것: `report-tool.jar`(log4j-api만). Apache 페이지대로 api만 쓰면 이 CVE와 무관하다.
- 놓치는 경우: 셰이딩 도구가 `pom.properties`를 지우거나 패키지를 바꾼 경우(클래스 이름·해시로 찾아야 함). jar가 아닌 형식으로 들어 있는 경우 — 이 코드는 폴더 바로 아래의 `.jar` 파일만 연다. `.war`·`.ear` 파일 자체, 하위 폴더, 컨테이너 이미지 레이어는 보지 않는다(열어 들어간 jar 안의 중첩 `.jar`는 재귀로 끝까지 들어간다).
- 판 차이: NVD는 CVE-2021-44832 수정을 "2.17.1, 2.12.4, and 2.3.2"로, 2026-10-07의 Apache 페이지는 2.17.0·2.12.3·2.3.1로 적는다. Java 8 이상에서 2.17.1 이상이면 두 기준을 다 만족하므로 그것을 기준으로 잡았다. Java 7·6 계열 보안 판은 따로 판정해야 하는데 이 코드는 그것을 "미만"으로 표시한다(한계).

### 8. xz 백도어

- 위치: 백도어의 한 부분은 "solely in the distributed tarballs" — 5.6.0·5.6.1 릴리스 tarball의 빌드 스크립트(`m4/build-to-host.m4`)에 git에 없는 줄. 코드의 대부분은 저장소에 테스트 파일로 위장해 난독화된 채 커밋돼 있었다(Freund).
- 서명·해시가 못 막은 이유: tarball은 릴리스 권한을 가진 사람이 만들고 서명했다(Collin: "created and signed by Jia Tan"). 서명은 출처만, 해시 고정은 "그 바이트"만 증명한다. 악성 바이트에도 정상 서명과 고정 해시가 붙는다.
- 발견 계기: Debian sid에서 ssh 로그인이 CPU를 많이 쓰고 valgrind 오류가 났다. 존재하지 않는 사용자로 로컬 접속 시간이 0.299초 → 0.807초. 이 성능 이상을 원인까지 추적했다.
- 막았을 통제: 저장소 태그에서 직접 빌드·tarball과 태그의 소스 대조·재현 빌드(독립 빌드 결과물끼리 비교), 갓 나온 판 도입 지연(개발판과 운영 분리 — Freund는 대부분 배포판의 정식판에는 아직 들어가지 않았다고 적었다), 롤백(CISA 권고 5.4.6) (25 장애 2).

### 9. 사용 여부에 답하지 못한다

- Log4Shell형이다(CSRB의 "customer list" 부재). 직접 의존성이 아닌 전이 의존성·fat jar·셰이딩 SDK·벤더 제품 안에 들어 있을 수 있다. Equifax의 Identification 요인과도 같은 모양이다.
- 당장: 배포물 스캔(위 실험처럼 내부 메타데이터·중첩 jar까지), 벤더 문의. 패치 전까지 egress 차단 같은 피해 반경 통제로 시간을 벌고, 접근 로그에서 시도 흔적을 찾는다(23 장애 1).
- 근본: 빌드마다 SBOM 생성·보관, 자산마다 소유자, 보안 패치 SLA, 벤더에 SBOM 요구(25).

### 10. 탐지의 출처와 "조용히 꺼짐" 알람

- Heartbleed: 외부 연구자(Codenomicon 팀·Google의 Neel Mehta).
- Equifax: 내부 정기 점검 — 단, 만료된 검사 장비 인증서를 교체한 뒤에야.
- Capital One: 외부인의 책임 있는 공개 제보(2019-07-17).
- Log4Shell: 외부 연구자의 보고(2021-11-24) → 공개.
- xz: 개발자의 성능 이상 추적.
- 알람 예: 검사 장비의 검사 바이트 수가 15분 동안 0이면 알람, 장비 인증서 만료 21일 전 알람(값은 예시). "프로세스가 떠 있다"가 아니라 "일을 하고 있다"를 본다.
- 같은 교훈: [29](../29-security-symptom-index/2-summary.md) 9절(에러가 없는 증상)과 장애 시나리오 5("에러가 없다"를 "안전하다"로 읽기). 거부·검사·검증 수가 0으로 떨어지는 것을 신호로 삼는다.
