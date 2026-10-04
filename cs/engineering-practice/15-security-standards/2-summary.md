# engineering-practice/15-security-standards — 보안 표준: 알려진 취약점이 반복되지 않게 하는 개발 보안 기준과 자동 검사 — 정리 (힌트)

## 해결하는 문제

보안 기준이 없으면 **이미 알려진** 취약점이 팀을 바꿔 가며 반복된다.

- SQL을 문자열로 이어 붙이는 코드는 한 번 고쳐도 다음 기능, 다음 신입의 코드에서 다시 나온다.
- 의존성 버전은 출시할 때 한 번 확인하고 끝난다. 그 버전에 새 취약점이 공개돼도 아무도 모른다.
- "보안 검토 받았나요?"라는 질문에 답할 기준이 없다. 무엇을 확인했는지 말할 수 없다.

쉬운 예: 건물 소방 기준이다.

```text
  기준 없음                              기준 있음
  건물마다 "알아서 조심"                  소방법: 비상구·스프링클러·방화문 (요구사항)
  불이 나면 같은 원인이 또 나옴           준공 검사: 기준표대로 점검 (검증)
                                       정기 점검: 해마다 다시 확인 (운영 과정)
```

- 화재 원인 대부분은 새로운 것이 아니라 알려진 것이다. 기준은 "알려진 원인"을 표로 만들고, 검사는 그 표를 매번 대조한다.

똑같은 구조다. 소프트웨어에서 위험 목록은 OWASP Top 10, 요구사항은 OWASP ASVS, 운영 과정은 NIST SSDF다. 한국 공공 사업에는 행정안전부 고시의 "소프트웨어 보안약점 기준"이 법적 진단 항목으로 붙는다.

실무 예:
- (예시) 2021-12 Log4Shell(CVE-2021-44228) 공개 직후 "우리 서비스가 log4j-core를 쓰는가, 어느 버전인가"를 묻는다. 전이 의존성까지 펼친 의존성 목록이 없으면 저장소와 이미지를 하나씩 열어 봐야 답할 수 있다.
- 정적 분석 도구를 켰더니 경고 수백 건이 나와 아무도 읽지 않는다. 진짜 SQL 인젝션 경고가 그 속에 묻힌다(장애 2).

기초 — Top 10 2025 항목별 공격·방어, ASVS 수준(L1~L3), SSDF 네 그룹(PO·PS·PW·RV) — 는 원본 [security-standards](../../engineering/development-standards/security-standards/2-summary.md) §1~§4에 있다. 이 노트는 그 기준을 **검사 가능한 형태로 개발 흐름에 거는 법**을 다룬다.

## 동작·원리

### 1. 기준의 층 — 무엇이 위험, 무엇을 만족, 어떻게 운영, 무엇이 법적 의무

```text
  인식   OWASP Top 10:2025        "가장 중대한 위험 10가지"         awareness 문서
  요구   OWASP ASVS 5.0.0         "앱이 만족할 검증 요구사항 345개"   L1 / L2 / L3
  과정   NIST SP 800-218 SSDF     "개발 조직이 할 관행"               PO · PS · PW · RV
  의무   행안부 고시 별표 3         "공공 정보시스템 사업에서 제거해야 할 보안약점"
         (행정기관 및 공공기관 정보시스템 구축·운영 지침)   설계 20 · 구현 49
```

- *awareness 문서*: Top 10 스스로 "개발자와 웹 애플리케이션 보안을 위한 표준 인식 문서(standard awareness document)"라고 부른다(top10.owasp.org/2025). 체크리스트로 만든 문서가 아니다.
- *ASVS(Application Security Verification Standard)*: 애플리케이션 보안 검증 요구사항 목록. 5.0.0은 2025-05-30 릴리스(GitHub OWASP/ASVS 릴리스 `v5.0.0_release`), 장은 V1 인코딩·새니타이즈부터 V17 WebRTC까지 17개.
- *SSDF(Secure Software Development Framework)*: NIST SP 800-218. 최종본 v1.1은 2022-02. Rev. 1 초안(SSDF v1.2)이 2025-12-17에 나왔고 의견 수렴은 2026-01-30에 닫혔다(CSRC 페이지, 2026-10-05 확인 시 아직 초안).
- *보안약점(weakness)*: 행안부 고시 정의로 "소프트웨어 결함, 오류 등으로 해킹 등 사이버공격을 유발할 가능성이 있는 잠재적인 보안취약점". 취약점(vulnerability)이 되기 전 단계의 코드 결함을 가리킨다.

Top 10:2025 목록(top10.owasp.org/2025): A01 Broken Access Control · A02 Security Misconfiguration · A03 Software Supply Chain Failures · A04 Cryptographic Failures · A05 Injection · A06 Insecure Design · A07 Authentication Failures · A08 Software or Data Integrity Failures · A09 Security Logging and Alerting Failures · A10 Mishandling of Exceptional Conditions.
- 2025판은 2025-11 OWASP Global AppSec(워싱턴 D.C.)에서 공개됐다(언론·벤더 보도). 최종판 확정일은 `[?]`.

한국 공공 기준(행정안전부 고시 제2025-1호, 2025-01-02 발령, law.go.kr 원문 대조).
- 제50조: 일정 규모 이상(영 제71조제1항) 정보시스템 사업은 별표 3의 보안약점이 없도록 개발해야 한다. 적용 범위는 신규 개발이면 설계 산출물과 소스코드 전체, 유지관리면 변경된 부분. 상용 소프트웨어는 제외.
- 제52조: 보안약점 진단 때 별표 3 항목을 필수 진단 항목으로 포함한다.
- 제53조: 감리법인이 보안약점 제거 여부를 진단하고, 진단도구를 쓰면 정해진 인증·확인을 받은 도구를 쓴다.
- 별표 3: 설계단계 20개 항목(4분류), 구현단계 49개 항목(7분류: 입력데이터 검증 및 표현 17 · 보안기능 16 · 시간 및 상태 2 · 에러처리 3 · 코드오류 5 · 캡슐화 4 · API 오용 2). 첫 항목은 "SQL 삽입"이다.

### 2. 기준 → 자동 검사 지도

기준 문서의 항목 중 상당수는 도구가 대조할 수 있다. 남는 것은 설계·리뷰가 맡는다.

```text
                     코드(내가 쓴 것)             의존성(남이 쓴 것)        빌드·배포 경로
  자동 검사           SAST(정적 분석)              SCA(구성 요소 분석)       시크릿 스캔·서명 검증
                     예: SpotBugs+FindSecBugs    예: OSV 질의, 의존성 스캐너
  잡는 Top 10         A05 Injection, A04 일부     A03 공급망(알려진 CVE)     A08 무결성, A02 일부
  사람(설계·리뷰)      A01 인가 위치, A06 위협 모델링, A10 예외 경로(fail-open) — ASVS 체크리스트
```

- *SAST(Static Application Security Testing)*: 소스·바이트코드를 실행하지 않고 보안약점을 찾는 검사.
- *SCA(Software Composition Analysis)*: 의존성 목록을 알려진 취약점 데이터베이스와 대조하는 검사.
- *OSV(Open Source Vulnerabilities)*: 오픈소스 취약점 데이터베이스와 API(osv.dev). 패키지·버전을 질의하면 해당 권고(advisory) 목록을 준다.
  - 흔한 오해: "도구가 0건이면 안전하다". SAST는 데이터 흐름을 추적할 수 있는 패턴만, SCA는 **이미 공개된** 취약점만 본다. 인가 누락(A01)이나 설계 결함(A06)은 대부분 도구 밖이다.

### 3. 실험 A: 정적 분석이 "알려진 패턴"을 매번 잡는다 — 그리고 소음도 낸다

나쁜 예 두 개와 좋은 예 하나를 한 클래스에 넣고 SpotBugs + FindSecBugs로 검사했다.

```java
public class OrderDao {
    private final Connection conn;
    public OrderDao(Connection conn) { this.conn = conn; }

    // (나쁜 예) 입력을 쿼리 문자열에 이어 붙인다 — A05 Injection
    public ResultSet findByUser(String userId) throws SQLException {
        Statement st = conn.createStatement();
        return st.executeQuery("SELECT * FROM orders WHERE user_id = '" + userId + "'");
    }
    // (좋은 예) 파라미터 바인딩
    public ResultSet findByUserSafe(String userId) throws SQLException {
        PreparedStatement ps = conn.prepareStatement("SELECT * FROM orders WHERE user_id = ?");
        ps.setString(1, userId);
        return ps.executeQuery();
    }
    // (나쁜 예) 예측 가능한 난수로 토큰 생성
    public String resetToken() { return Long.toHexString(new Random().nextLong()); }
}
```

(실험, SpotBugs 4.9.3 + FindSecBugs 1.14.0 via spotbugs-maven-plugin 4.9.3.0, effort=Max·threshold=Low · Maven 3.9.16 · JDK 21.0.12 temurin, 2026-10-05)

```text
[ERROR] High: Random object created and used only once in shop.OrderDao.resetToken() ... DMI_RANDOM_USED_ONLY_ONCE
[ERROR] Medium: new shop.OrderDao(Connection) may expose internal representation ... EI_EXPOSE_REP2
[ERROR] Medium: shop.OrderDao.findByUser(String) may fail to clean up java.sql.Statement on checked exception ... OBL_UNSATISFIED_OBLIGATION_EXCEPTION_EDGE
[ERROR] Medium: shop.OrderDao.findByUserSafe(String) may fail to clean up java.sql.Statement on checked exception ... OBL_UNSATISFIED_OBLIGATION_EXCEPTION_EDGE
[ERROR] Medium: shop.OrderDao.findByUser(String) may fail to close Statement ... ODR_OPEN_DATABASE_RESOURCE
[ERROR] Medium: shop.OrderDao.findByUserSafe(String) may fail to close PreparedStatement ... ODR_OPEN_DATABASE_RESOURCE
[ERROR] Medium: This random generator (java.util.Random) is predictable ... PREDICTABLE_RANDOM
[ERROR] Medium: This use of java/sql/Statement.executeQuery(...) can be vulnerable to SQL injection (with JDBC) ... At OrderDao.java:[line 13] SQL_INJECTION_JDBC
[ERROR] High: shop.OrderDao.findByUser(String) passes a nonconstant String to an execute or addBatch method ... SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE
[ERROR] Failed to execute goal ...spotbugs-maven-plugin:4.9.3.0:check ... failed with 9 bugs and 0 errors
```

관찰과 해석.
- 보안 기준의 두 항목이 도구로 잡혔다: SQL 삽입(13행 `SQL_INJECTION_JDBC`·`SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE`)과 예측 가능한 난수(`PREDICTABLE_RANDOM`). 행안부 별표 3 구현단계의 "SQL 삽입"·"적절하지 않은 난수 값 사용" 항목, Top 10 A05·A04와 대응한다(대응은 해석).
- 좋은 예(`findByUserSafe`)는 SQL 인젝션 경고를 받지 않았다. 도구는 **이어 붙인 문자열이 실행 메서드에 닿는 흐름**을 본다.
- 9건 중 보안 경고(SpotBugs 범주 `SECURITY`)는 3건이다. 나머지 6건은 `BAD_PRACTICE` 3건(자원 미해제 2·`DMI_RANDOM_USED_ONLY_ONCE`), `EXPERIMENTAL` 2건(`OBL_…`), `MALICIOUS_CODE` 1건(`EI_EXPOSE_REP2` 내부 표현 노출)이다(같은 실행의 `target/spotbugsXml.xml` category 속성). effort=Max·threshold=Low로 최대한 넓게 켰기 때문이다. 이대로 게이트를 걸면 소음 때문에 사람이 경고를 읽지 않게 된다(장애 2). 보안 게이트에는 보안 범주만, 품질 경고는 [14-quality-standards](../14-quality-standards/2-summary.md)의 기준선 방식으로 나눠 다룬다.

### 4. 실험 B: 어제 안전한 버전이 오늘 취약하다 — SCA는 한 번이 아니라 계속

OSV API(`POST https://api.osv.dev/v1/querybatch`)에 Maven 좌표와 버전을 보내 권고 목록을 받았다.

```json
{"queries":[
 {"package":{"ecosystem":"Maven","name":"org.apache.logging.log4j:log4j-core"},"version":"2.14.1"},
 {"package":{"ecosystem":"Maven","name":"org.apache.logging.log4j:log4j-core"},"version":"2.17.1"},
 {"package":{"ecosystem":"Maven","name":"org.apache.logging.log4j:log4j-core"},"version":"2.25.2"},
 {"package":{"ecosystem":"Maven","name":"org.apache.commons:commons-text"},"version":"1.9"},
 {"package":{"ecosystem":"Maven","name":"org.apache.commons:commons-text"},"version":"1.10.0"}]}
```

(실험, api.osv.dev 질의, 2026-10-05 — 결과는 질의 날짜에 따라 바뀐다)

```text
log4j-core 2.14.1 7 ['GHSA-3pxv-7cmr-fjr4', 'GHSA-6hg6-v5c8-fphq', 'GHSA-7rjr-3q55-vv33', 'GHSA-8489-44mv-ggj8', 'GHSA-jfh8-c2jp-5v3q', 'GHSA-p6xc-xr62-6r2g', 'GHSA-vc5p-v9hr-52mj']
log4j-core 2.17.1 3 ['GHSA-3pxv-7cmr-fjr4', 'GHSA-6hg6-v5c8-fphq', 'GHSA-vc5p-v9hr-52mj']
log4j-core 2.25.2 4 ['GHSA-3pxv-7cmr-fjr4', 'GHSA-445c-vh5m-36rj', 'GHSA-6hg6-v5c8-fphq', 'GHSA-vc5p-v9hr-52mj']
commons-text 1.9 1 ['GHSA-599f-7c49-w659']
commons-text 1.10.0 0 []
```

권고 상세(`GET /v1/vulns/<id>` 응답의 aliases·summary·published·ranges를 옮겨 적음, 요약은 번역):

| 권고 | CVE | 요약 | 공개 | 영향 범위(log4j-core 2.x 등) |
|---|---|---|---|---|
| GHSA-jfh8-c2jp-5v3q | CVE-2021-44228 | Remote code injection in Log4j | 2021-12-10 | 2.13.0 이상 2.15.0 미만 등 |
| GHSA-vc5p-v9hr-52mj | CVE-2025-68161 | Socket Appender TLS 호스트명 미검증 | 2025-12-18 | 2.0-beta9 이상 2.25.3 미만 |
| GHSA-3pxv-7cmr-fjr4 | CVE-2026-34480 | XmlLayout에서 이벤트가 조용히 유실 | 2026-04-10 | 2.0-alpha1 이상 2.25.4 미만 |
| GHSA-6hg6-v5c8-fphq | CVE-2026-34477 | TLS 설정의 verifyHostName이 조용히 무시됨 | 2026-04-10 | 2.12.0 이상 2.25.4 미만 |
| GHSA-445c-vh5m-36rj | CVE-2026-34478 | Rfc5424Layout 로그 인젝션 | 2026-04-10 | 2.21.0 이상 2.25.4 미만 |
| GHSA-599f-7c49-w659 | CVE-2022-42889 | Commons Text 임의 코드 실행 | 2022-10-13 | 1.5 이상 1.10.0 미만 |

관찰과 해석.
- 2.14.1에는 Log4Shell(CVE-2021-44228)이 들어 있다. 2.17.1은 Log4Shell 계열은 빠졌지만 그 뒤 공개된 권고 3건이 붙었다.
- 2.25.2에는 2025-12·2026-04에 **공개된** 권고 4건이 붙는다. 이 버전을 고른 날의 스캔이 깨끗했어도, 코드 한 줄 바꾸지 않은 채 오늘 다시 스캔하면 결과가 다르다.
- 그래서 SCA는 "PR을 낼 때" 한 번이 아니라 **배포된 버전에 대해 주기적으로** 돌려야 한다(장애 3). 질의의 단위는 "패키지 + 정확한 버전"이다. 이름과 버전을 아는 패키지는 목록 없이도 하나씩 질의할 수 있지만, 전이 의존성까지 펼친 목록(SBOM 같은 자재명세서)이 없으면 **빠짐없이** 질의할 수 없다.
- 버전 범위(`introduced`/`fixed` 이벤트)와 우리 버전을 비교하는 것이 SCA의 핵심 연산이다(자료구조 절).

### 5. 실험 C: ASVS 수준 선택 = 검증 범위의 크기

ASVS 5.0.0 릴리스 태그의 장 파일 17개에서 요구사항 행(`| **x.y.z** | … | 수준 |`)을 셌다.

(실험, GitHub OWASP/ASVS `v5.0.0_release` 태그의 `5.0/en/0x10~0x26` 파일, grep 계수, 2026-10-05)

```text
요구사항 행 345
수준 열 분포:  L1 70 · L2 183 · L3 92
```

- 수준 열은 그 요구사항이 **처음 요구되는** 수준이다. 수준은 누적이므로 L1 목표면 70개, L2 목표면 70 + 183 = 253개, L3 목표면 345개를 검증한다(누적 해석 근거: 원본 §2의 "수준(누적)" 설명, ASVS 5.0.0 "What is the ASVS" 장 "Each ASVS level indicates the security requirements that are required to achieve from that level"). 같은 장은 일부 요구사항이 높은 수준에서 더 엄격한 조건을 갖는다고도 적으므로, 253은 "검증할 요구사항 수"이지 조건의 강도까지 같다는 뜻은 아니다.
- ASVS 5.0.0 문서 자체("For Users Of 4.0" 장)도 "70 L1 requirements out of a total of 345 requirements"라고 적어 계수와 일치한다.
- 참고: 원본 security-standards의 "약 350개"는 릴리스 태그 기준 345개다(위 계수·ASVS 5.0.0 본문).
- "우리 서비스는 ASVS L2"라고 말하는 순간 검증 범위의 **출발 집합**이 253개 항목으로 정해진다. 보안 기준이 검증 가능한 계약이 되는 지점이다.
- 단, 실제 범위는 적용 가능성을 따져 정한다. 같은 장은 조직이 쓰지 않는 장(예: GraphQL·WebSocket·SOAP)을 빼고 맞춤 ASVS를 만들라고 권한다("omitting irrelevant sections"). 이때도 요구사항 번호의 뜻은 유지해야 한다(추적성).

## 쓰이는 자료구조·알고리즘

- **오염 분석(taint analysis)**: 외부 입력(source, 예: 메서드 인자)이 검증 없이 위험한 실행 지점(sink, 예: `Statement.executeQuery`)까지 흐르는지 데이터 흐름 그래프에서 추적한다. 실험 A에서 `findByUser`만 걸리고 `findByUserSafe`는 걸리지 않은 이유다(FindSecBugs의 구체 구현은 `[?]` — 동작은 실험 결과로만 확인).
- **버전 범위 매칭**: OSV 권고의 `ranges.events`는 `introduced`·`fixed`(또는 `last_affected`) 경계의 나열이다. `fixed`가 있으면 우리 버전 v가 구간 [introduced, fixed) 안에 드는지, `last_affected`면 [introduced, last_affected] (끝 포함) 안에 드는지를 생태계별 버전 비교 규칙(Maven은 Maven 버전 정렬)으로 판정한다. 닫는 이벤트가 없으면 introduced 이후 전부가 영향 범위다(OSV 스키마 "Evaluation" 의사코드; `limit` 이벤트는 주로 GIT 범위용 상한). 정렬된 경계 목록에서 이진 탐색으로 구간을 찾을 수 있다.
- **의존성 그래프 순회**: 전이 의존성까지 펼친 그래프(DAG)를 순회해 질의할 (좌표, 버전) 집합을 만든다. [17-legal-standards](../17-legal-standards/2-summary.md)의 라이선스 실험에서도 직접 선언하지 않은 `protobuf-java`가 전이 의존성으로 들어왔다.
- **분류 트리(CWE)**: 보안약점은 CWE(Common Weakness Enumeration) 계층으로 분류된다. 도구 경고·기준 항목·Top 10 항목을 CWE 번호로 서로 대응시킨다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **수준을 정한다.** 서비스의 데이터·손실·규제로 ASVS 목표 수준을 정한다(원본 §2 판단 예). 공공 사업이면 행안부 별표 3이 필수 진단 항목이다.
2. **의존성 목록을 만든다.** 빌드 도구에서 전이 의존성까지 펼친 목록(SBOM)을 산출물로 남긴다. 없으면 SCA가 전이 의존성을 빠뜨리고, 사고 때 영향 범위 산정도 어렵다.
3. **자동 검사를 PR과 정기 작업에 건다.** PR: SAST(보안 범주) + SCA(새로 추가된 의존성). 정기(예: 매일): 배포된 버전의 SCA 재질의.
4. **경고를 분류해 게이트에 건다.** 보안 범주의 높은 심각도만 병합을 막고, 나머지는 기준선으로 관리한다.
5. **예외는 기한과 함께 기록한다.** "위험 수용"은 누가·왜·언제까지를 남긴다.
6. **사람 몫은 체크리스트로.** 인가 위치(A01), 위협 모델링(A06), 예외 경로 fail-closed(A10)는 리뷰 체크리스트(ASVS 해당 장)로 본다.

### 2. 고친 코드 (Java)

```java
// SQL 삽입 제거: 파라미터 바인딩 + 자원 해제(try-with-resources)
public List<Order> findByUser(String userId) throws SQLException {
    String sql = "SELECT id, amount FROM orders WHERE user_id = ?";
    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        ps.setString(1, userId);
        try (ResultSet rs = ps.executeQuery()) {
            List<Order> out = new ArrayList<>();
            while (rs.next()) out.add(new Order(rs.getLong("id"), rs.getLong("amount")));
            return out;
        }
    }
}

// 예측 가능한 난수 제거: CSPRNG
private static final SecureRandom RNG = new SecureRandom();
public String resetToken() {
    byte[] b = new byte[32];
    RNG.nextBytes(b);
    return HexFormat.of().formatHex(b);
}
```

### 3. 빌드 설정 (Maven, spotbugs-maven-plugin 4.9.3.0 + FindSecBugs 1.14.0)

```xml
<plugin>
  <groupId>com.github.spotbugs</groupId>
  <artifactId>spotbugs-maven-plugin</artifactId>
  <version>4.9.3.0</version>
  <configuration>
    <effort>Max</effort>
    <threshold>Low</threshold>
    <plugins>
      <plugin><groupId>com.h3xstream.findsecbugs</groupId><artifactId>findsecbugs-plugin</artifactId><version>1.14.0</version></plugin>
    </plugins>
    <!-- 보안 게이트는 SECURITY 범주만 (excludeFilterFile·includeFilterFile로 범주 제한) -->
  </configuration>
</plugin>
```

- 실험은 범주를 제한하지 않았기 때문에 9건이 나왔다. 범주 필터 파일의 문법은 SpotBugs 문서 "Filter file"을 따른다.

### 4. 정기 SCA 질의 (JS, Node 18+ 내장 fetch)

```js
// deps: [{name: "org.apache.logging.log4j:log4j-core", version: "2.25.2"}, ...]
async function osvScan(deps) {
  const body = { queries: deps.map(d => ({ package: { ecosystem: "Maven", name: d.name }, version: d.version })) };
  const res = await fetch("https://api.osv.dev/v1/querybatch", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`OSV ${res.status}`);          // 실패를 '취약점 0건'으로 삼키지 않는다
  const { results } = await res.json();
  return deps.map((d, i) => ({ ...d, vulns: (results[i].vulns ?? []).map(v => v.id) }));
}
```

- 이 코드는 첫 페이지만 읽는다. OSV 문서("POST /v1/querybatch" Pagination 절)에 따르면 한 질의가 1,000건, 전체가 3,000건을 넘으면 결과에 `next_page_token`이 붙는다. 실제로 쓸 때는 토큰이 붙은 질의만 `page_token`을 넣어 다시 질의하고 합친다(토큰을 무시하면 권고가 조용히 빠진다).

- 질의 실패를 0건으로 처리하면 조용한 실패다. 실패는 실패로 알린다.

## 장애 시나리오와 대처

### 1. 기준 부재 → 알려진 취약점 반복 (⚠ 커리큘럼)

- 현상: 지난 분기에 고친 SQL 인젝션과 같은 모양의 결함이 다른 모듈에서 다시 신고된다.
- 보이는 형태: 침투 테스트·버그 바운티 보고서에 같은 CWE가 반복된다. 코드에 `"... WHERE x = '" + input + "'"` 패턴이 여러 곳 남아 있다.
- 원인: 고친 것은 그 한 곳이지 패턴이 아니다. 기준(무엇을 금지하나)과 자동 검사(매번 대조)가 없다.
- 대처: 기준 항목(ASVS·별표 3)을 정하고 SAST 규칙으로 옮겨 PR마다 대조한다(실험 A). 신고가 들어오면 같은 패턴을 전수 검색한다(SSDF RV — 원본 §3).

### 2. 스캐너 소음 → 경고 피로 → 진짜 경고를 놓친다

- 현상: 정적 분석 경고가 수백 건이라 아무도 읽지 않는다.
- 보이는 형태: 실험 A처럼 보안 3건이 품질 경고 6건과 섞여 같은 `[ERROR]` 줄로 나온다. 팀이 게이트를 "경고만"으로 낮춘다.
- 원인: 범주·심각도를 나누지 않고 한 게이트에 걸었다.
- 대처: 보안 범주의 높은 심각도만 병합을 막고, 나머지는 기준선으로 관리한다. 오탐은 이유와 함께 억제하고 억제 수를 본다([14-quality-standards](../14-quality-standards/2-summary.md) 장애 4).

### 3. 출시 때만 스캔 → 새로 공개된 CVE를 모른다

- 현상: 운영 중인 서비스가 공개된 취약점이 있는 버전을 몇 달째 쓰고 있다.
- 보이는 형태: 실험 B의 log4j-core 2.25.2처럼, 출시 때 깨끗하던 버전에 이후 권고가 붙는다. 외부(고객·보안 연구자)가 먼저 알려 준다.
- 원인: SCA를 PR 시점에만 돌렸다. 취약점 데이터베이스는 계속 갱신된다.
- 대처: 배포된 버전 목록으로 정기 재질의하고, 새 권고를 경보로 받는다. 업데이트 운영(자동 PR 도구·EOL 런타임 정리)은 security/25-supply-chain-security — 미작성([보안 영역 표](../../security/README.md)).

### 4. 전이 의존성을 못 봄

- 현상: "우리는 그 라이브러리를 안 쓴다"고 답했는데 실제로는 다른 라이브러리를 통해 들어와 있었다.
- 보이는 형태: `pom.xml`에는 없는데 빌드 산출물(jar·이미지)에는 그 jar가 있다. 의존성 트리 명령(`mvn dependency:tree`)에서야 보인다.
- 원인: 직접 선언한 의존성만 확인했다.
- 대처: 전이 의존성까지 펼친 목록(SBOM)을 빌드 산출물로 남기고 그 목록으로 스캔한다.

### 5. 체크리스트는 통과, 예외 경로는 fail-open

- 현상: 보안 리뷰 체크리스트는 다 채웠는데 인증 서버 타임아웃 때 요청이 승인된다.
- 보이는 형태: `catch` 블록에서 로그만 남기고 진행하는 코드. 장애 중 인가 거부 로그가 0건이 된다.
- 원인: 체크리스트가 정상 경로만 묻는다. 도구도 이 논리 결함은 대부분 못 잡는다.
- 대처: A10(예외 처리)과 ASVS 해당 요구를 리뷰 체크리스트에 넣고, 의존 서버를 죽인 상태의 테스트로 fail-closed를 확인한다(원본 §1 A10).

## 핵심 문장

- Top 10은 인식, ASVS는 검증 요구, SSDF는 개발 과정, 행안부 별표 3은 공공 사업의 필수 진단 항목이다 — 층이 달라 서로 대체되지 않는다.
- 알려진 취약점이 반복되는 이유는 고친 것이 "그 한 곳"이기 때문이다. 기준 항목을 도구 규칙으로 옮겨 PR마다 대조해야 패턴이 막힌다.
- SAST는 흐름으로 잡히는 패턴만, SCA는 이미 공개된 취약점만 본다 — 인가 위치·설계 결함·예외 경로는 사람의 리뷰 몫으로 남는다.
- 의존성 스캔은 시점의 결과다. 같은 버전도 날짜가 바뀌면 결과가 바뀌므로 배포된 버전을 계속 다시 질의해야 한다.
- 보안 게이트에 품질 경고를 섞으면 소음이 진짜 경고를 묻는다.

## 관련 주제·근거

- 원본(기초): [engineering/development-standards/security-standards](../../engineering/development-standards/security-standards/2-summary.md) — Top 10:2025 항목별 공격·방어, ASVS 5.0 수준, SSDF 네 그룹, 세 기준의 연결
- 선행: security/01-security-principles — 미작성([보안 영역 표](../../security/README.md))
- 후속·연결
  - [14-quality-standards](../14-quality-standards/2-summary.md) — 기준 → 자동 검사 구조, 기준선·래칫
  - [16-operational-standards](../16-operational-standards/2-summary.md) — 보안 로그·경보(A09)와 운영 표준
  - [17-legal-standards](../17-legal-standards/2-summary.md) — 안전성 확보조치(법적 의무)와 의존성 라이선스
  - security 18-injection · 22-ssrf · 25-supply-chain-security · 26-security-logging-and-audit — 미작성([보안 영역 표](../../security/README.md))
  - [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) — 감사 기록과 보안 로그의 역할
- 근거
  - OWASP Top 10:2025 <https://top10.owasp.org/2025/>
  - OWASP ASVS 5.0.0 릴리스(2025-05-30) <https://github.com/OWASP/ASVS/releases> · 장 파일 `5.0/en/` (태그 `v5.0.0_release`)
  - NIST SP 800-218 SSDF v1.1(2022-02) <https://csrc.nist.gov/pubs/sp/800/218/final> · SP 800-218 Rev. 1 초안(2025-12-17) <https://csrc.nist.gov/pubs/sp/800/218/r1/ipd>
  - 행정안전부 고시 제2025-1호 「행정기관 및 공공기관 정보시스템 구축·운영 지침」 제2조(정의)·제50조~제53조·별표 3 소프트웨어 보안약점 기준 — law.go.kr 행정규칙 원문(2026-10-05 조회)
  - OSV API — `POST /v1/querybatch`, `GET /v1/vulns/{id}` <https://google.github.io/osv.dev/api/>
  - OSV 스키마 "Evaluation"(introduced·fixed·last_affected·limit 판정) <https://ossf.github.io/osv-schema/> · querybatch 페이지 나눔 <https://google.github.io/osv.dev/post-v1-querybatch/>
  - SpotBugs 4.9.3 <https://spotbugs.readthedocs.io/> · Find Security Bugs 1.14.0 <https://find-sec-bugs.github.io/>
- 실험 목록
  - A. SAST: spotbugs-maven-plugin 4.9.3.0(SpotBugs 4.9.3) + FindSecBugs 1.14.0, Maven 3.9.16, temurin 21.0.12 컨테이너 — 9건(SQL_INJECTION_JDBC·SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE·PREDICTABLE_RANDOM 포함, 바인딩 버전은 인젝션 미검출).
  - B. SCA: api.osv.dev querybatch(2026-10-05) — log4j-core 2.14.1/2.17.1/2.25.2 = 7/3/4건, commons-text 1.9/1.10.0 = 1/0건, 권고 상세의 공개일·범위.
  - C. ASVS 5.0.0 요구사항 계수 — 345행, L1 70·L2 183·L3 92.
  - 법령 원문: law.go.kr DRF API로 행정안전부 고시 원문 조회, 별표 3 항목 수 계수(설계 20·구현 49).
