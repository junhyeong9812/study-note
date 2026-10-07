# engineering-practice/17-legal-standards — 법률 표준: 개인정보 의무와 오픈소스 라이선스를 코드·빌드에서 지키기 — 정리 (힌트)

## 해결하는 문제

법률 의무는 법무팀 문서에만 있으면 코드에 닿지 않는다. 코드와 빌드가 의무를 모르는 채로 돌아가면 두 가지가 조용히 쌓인다.

- **라이선스 위반 의존성**: 사내 배포 제품에 조건을 지킬 수 없는 라이선스의 라이브러리가 전이 의존성으로 들어와 있다. 아무도 선언하지 않았으니 아무도 모른다.
- **개인정보 보관 기한 위반**: 탈퇴한 회원 데이터가 운영 DB·백업·로그에 남아 있다. 반대로 법이 5년 보존을 요구하는 거래기록을 탈퇴와 함께 지워 버린다.

쉬운 예: 식당의 식품 기준이다.

```text
  기준이 주방에 닿지 않을 때                    기준이 주방 절차가 될 때
  유통기한 규정은 사장 책상 서랍에               냉장고마다 입고일·폐기일 라벨 (데이터마다 보존 기한)
  납품받은 재료의 원산지 표시 의무를 모름         입고 검수표에 원산지 칸 (의존성마다 라이선스)
  단속 나오면 그때 알게 됨                       매일 마감 때 폐기 목록 출력 (만료 데이터 파기 배치)
```

똑같은 구조다. 법률 표준은 법령 조문을 **데이터 모델의 보존 기한 칸, 빌드의 라이선스 검사, 사고 대응 절차의 기한**으로 바꾸는 일이다.

실무 예:
- 고객사 납품 직전 감사에서 GPL 계열 JDBC 드라이버가 제품 이미지에 들어 있는 것이 발견된다. 직접 넣은 적은 없고 예전 PoC 모듈의 의존성이었다(장애 1).
- 2026-09-11부터 개정 개인정보 보호법이 시행됐다. 유출 "가능성"만 확인돼도 통지해야 하는 경우가 새로 생겼는데, 사고 대응 런북은 2023년 조문 기준이다(장애 5).

이 노트의 법률 내용은 **법령 원문을 정리한 것이며 해석이 섞인 곳은 "해석·법률 자문 아님"으로 표시한다. 법률 자문이 아니다.** 실제 판단은 시행일 기준 현행 원문과 전문가 확인이 필요하다.

기초 — 개인정보 생명주기(수집 근거·제공 vs 위탁·국외 이전·파기), 안전성 확보조치 고시 제5조~제8조, 정보주체 권리, 유출 통지·신고, 관련 법령 — 는 원본 [legal-standards](../../engineering/development-standards/legal-standards/2-summary.md) §1~§7과 조문 부록 [provisions.md](../../engineering/development-standards/legal-standards/provisions.md)에 있다. 원본 묶음의 네 축 관계는 [development-standards/README](../../engineering/development-standards/README.md). 이 노트는 원본에 없던 **라이선스 축**을 더하고, 원본 수집일(2026-08-24) 이후 바뀐 조문을 반영하고, 둘을 코드·빌드로 강제하는 법을 다룬다.

## 동작·원리

### 1. 두 축 — 개인정보는 "처리"에, 라이선스는 "배포"에 의무가 붙는다

```text
  개인정보 축                                         라이선스 축
  법률   개인정보 보호법                                라이선스 원문(SPDX 목록의 텍스트)
   └ 시행령   개인정보 보호법 시행령                    의무가 붙는 행위:
       └ 고시  안전성 확보조치 기준                      복제·배포(convey) / 네트워크 제공(AGPL §13)
              표준 개인정보 보호지침                    의무: 고지 유지 · 소스 제공 · 같은 라이선스
  의무가 붙는 행위: 수집·이용·제공·보관·파기(처리)
  코드에 닿는 곳: 보존 기한·파기 배치·암호화·접속기록      코드에 닿는 곳: 의존성 목록·정책 검사·NOTICE
```

- *법령 위계*: 법률(국회) → 시행령(대통령령) → 고시(행정규칙, 여기서는 개인정보보호위원회 고시). 기한·수치 같은 세부는 아래로 갈수록 구체화된다. 예: 유출 신고의 "72시간"은 법률이 아니라 시행령 제40조에 있다.
- *SPDX*: 소프트웨어 라이선스를 표준 식별자(`MIT`, `Apache-2.0`, `GPL-2.0-only` 등)로 부르는 목록·표현식 규격. 2026-10-05 조회한 목록은 v3.29.0(2026-09-16), 라이선스 740개, 그중 OSI 승인 표시 154개.
- *OSI 승인*: Open Source Initiative가 오픈소스 정의에 맞는다고 승인한 라이선스. SPDX 목록의 `isOsiApproved` 칸으로 확인할 수 있다.
  - 흔한 오해: "GitHub에 소스가 공개돼 있으면 오픈소스다". SPDX 목록에서 `SSPL-1.0`·`BUSL-1.1`·`CC-BY-NC-4.0`·`JSON`은 OSI 승인이 아니다(`isOsiApproved=false`). 공개 여부가 아니라 라이선스 조건이 기준이다.

### 2. 라이선스 유형과 의무가 붙는 순간

```text
             허용형(permissive)        약한 copyleft              강한 copyleft            네트워크 copyleft
  예         MIT, BSD-3-Clause,         LGPL-2.1, MPL-2.0,          GPL-2.0, GPL-3.0          AGPL-3.0
             Apache-2.0                 EPL-2.0
  핵심 의무   저작권·라이선스 고지 유지   수정한 그 라이브러리(파일)    결합 저작물 전체를 같은     GPL 의무 + 네트워크로
             (Apache는 NOTICE·변경 표시) 의 소스 공개 범위가 제한적   라이선스로·소스 제공        이용하게 해도 소스 제공
  의무 시점   배포할 때                  배포할 때                   배포(convey)할 때          수정본을 네트워크로 제공할 때
```

원문 근거(라이선스 텍스트에서 직접 확인).
- MIT: "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."
- Apache-2.0 §4: 배포할 때 (a) 라이선스 사본 제공 (b) 수정한 파일에 변경 표시 (c) 소스 형태의 저작권·특허·상표·출처 고지 유지 (d) 원저작물에 `NOTICE` 파일이 있으면 그 고지를 배포물에 포함.
- GPL-3.0 정의: "convey"는 다른 사람이 복제본을 만들거나 받을 수 있게 하는 전파다. "컴퓨터 네트워크를 통한 사용자와의 상호작용만으로, 복제본 전달 없이는 convey가 아니다."
- LGPL-2.1 §6: 라이브러리와 결합·연결한 저작물을 배포할 때는 라이브러리 소스 제공만이 아니라, 사용자가 라이브러리를 고쳐 다시 연결할 수 있게 하는 방법 중 하나(라이브러리 소스 + 재연결 가능한 목적 코드 제공, 사용자 시스템의 공유 라이브러리를 쓰는 방식, 3년 유효 서면 제안 등)를 지켜야 한다. 고객이 자기 용도로 수정·디버깅용 역공학을 하는 것도 허용해야 한다.
- AGPL-3.0 §13: 프로그램을 **수정**했다면, 그 수정본이 네트워크로 원격 상호작용을 지원하는 경우 원격으로 상호작용하는 사용자에게 대응 소스(Corresponding Source)를 받을 기회를 눈에 띄게 제공해야 한다.
- 호환성: FSF 라이선스 목록은 Apache-2.0을 "GPLv3와 호환, GPLv2와는 비호환"으로 적는다(특허 종료·면책 조항 때문). 서로 다른 라이선스를 한 결합 저작물에 넣을 수 있는지는 이런 호환 판정에 달려 있다.

해석·법률 자문 아님: 서버에서만 실행하고 바이너리를 배포하지 않는 SaaS는 GPL의 "convey"에 해당하지 않는다는 것이 위 정의의 직접적인 읽기다. AGPL은 바로 이 틈을 §13으로 막는다. 사내 배포·고객사 설치형 납품·모바일 앱 배포는 배포에 해당할 수 있다.

### 3. 실험 A: 의존성 라이선스 목록 → 정책 게이트

결제 기능이 있는 사내 배포형 제품(예시)의 `pom.xml`에 의존성 6개를 선언하고, license-maven-plugin으로 전이 의존성까지 라이선스를 뽑은 뒤 정책 검사기를 돌렸다.

(실험, license-maven-plugin 2.4.0 `license:add-third-party` · Maven 3.9.16 · JDK 21.0.12 temurin, 2026-10-05)

```text
Lists of 8 third-party dependencies.
     (Eclipse Public License - v 1.0) (GNU Lesser General Public License) Logback Classic Module (ch.qos.logback:logback-classic:1.5.12 - http://logback.qos.ch/logback-classic)
     (Eclipse Public License - v 1.0) (GNU Lesser General Public License) Logback Core Module (ch.qos.logback:logback-core:1.5.12 - http://logback.qos.ch/logback-core)
     (BSD-3-Clause) Protocol Buffers [Core] (com.google.protobuf:protobuf-java:4.26.1 - https://developers.google.com/protocol-buffers/protobuf-java/)
     (EPL 1.0) (MPL 2.0) H2 Database Engine (com.h2database:h2:2.3.232 - https://h2database.com)
     (The GNU General Public License, v2 with Universal FOSS Exception, v1.0) MySQL Connector/J (com.mysql:mysql-connector-j:9.1.0 - http://dev.mysql.com/doc/connector-j/en/)
     (Apache-2.0) Apache Commons Lang (org.apache.commons:commons-lang3:3.17.0 - https://commons.apache.org/proper/commons-lang/)
     (The JSON License) JSON in Java (org.json:json:20140107 - https://github.com/douglascrockford/JSON-java)
     (MIT License) SLF4J API Module (org.slf4j:slf4j-api:2.0.16 - http://www.slf4j.org)
```

정책 검사기(핵심 부분) — 자유 텍스트 이름을 SPDX ID로 바꾸고, 모르는 이름은 실패로 본다.

```java
// POM의 자유 텍스트 라이선스 이름 → SPDX ID (모르는 이름은 매핑하지 않는다 = 실패)
static final Map<String,String> SPDX = Map.of(
  "Eclipse Public License - v 1.0","EPL-1.0", "EPL 1.0","EPL-1.0",
  "GNU Lesser General Public License","LGPL-2.1-only", "MPL 2.0","MPL-2.0",
  "BSD-3-Clause","BSD-3-Clause", "Apache-2.0","Apache-2.0", "MIT License","MIT",
  "The GNU General Public License, v2 with Universal FOSS Exception, v1.0",
    "GPL-2.0-only WITH Universal-FOSS-exception-1.0");

enum Verdict { ALLOW, REVIEW, DENY }
static Verdict policy(String id) {                       // 예시 정책: 사내 독점 제품으로 "배포"하는 경우
  if (id.matches("MIT|Apache-2.0|BSD-3-Clause")) return Verdict.ALLOW;     // copyleft 없음(고지 유지, Apache는 변경 표시·NOTICE도)
  if (id.matches("EPL-1.0|MPL-2.0|LGPL-2.1-only")) return Verdict.REVIEW;  // 약한 copyleft — 사용 방식 검토
  return Verdict.DENY;                                                      // GPL 계열·비OSI·미확인
}
// 라이선스가 둘 이상 적힌 의존성은 가장 유리한 하나를 고른다(OR로 가정 — 원문으로 확인할 것)
// DENY가 하나라도 있으면 System.exit(1) → 빌드 실패
```

```text
$ java LicenseGate.java THIRD-PARTY.txt
REVIEW ch.qos.logback:logback-classic:1.5.12                   EPL-1.0 OR LGPL-2.1-only
REVIEW ch.qos.logback:logback-core:1.5.12                      EPL-1.0 OR LGPL-2.1-only
ALLOW  com.google.protobuf:protobuf-java:4.26.1                BSD-3-Clause
REVIEW com.h2database:h2:2.3.232                               EPL-1.0 OR MPL-2.0
DENY   com.mysql:mysql-connector-j:9.1.0                       GPL-2.0-only WITH Universal-FOSS-exception-1.0
ALLOW  org.apache.commons:commons-lang3:3.17.0                 Apache-2.0
DENY   org.json:json:20140107                                  UNMAPPED(The JSON License)
ALLOW  org.slf4j:slf4j-api:2.0.16                              MIT
DENY=2
exit=1
```

관찰과 해석.
- **선언한 것은 6개, 목록은 8개다.** `protobuf-java`(mysql-connector-j가 끌고 옴)와 `logback-core`(logback-classic이 끌고 옴)는 `pom.xml`에 없다. 전이 의존성까지 보지 않으면 검사 대상에서 빠진다.
- **DENY 2건.** mysql-connector-j는 GPL-2.0에 예외(`Universal-FOSS-exception-1.0`, SPDX 예외 목록에 있는 ID)가 붙은 라이선스다. 예외의 적용 범위는 원문 검토가 필요하므로 예시 정책은 자동 허용하지 않았다. org.json 20140107의 "The JSON License"는 "The Software shall be used for Good, not Evil." 조항 때문에 FSF가 비자유로 분류하고, SPDX 목록에서도 OSI 승인이 아니다.
- **검사기는 "모르는 이름 = 실패"(fail-closed)다.** 자유 텍스트 이름이 매핑표에 없으면 DENY로 떨어진다. 반대로 모르는 이름을 통과시키면, 새 라이선스가 들어올 때마다 조용히 허용된다.
- **메타데이터는 틀릴 수 있다.** logback 1.5.12의 POM은 `Eclipse Public License - v 1.0`이라고 적는데, logback 공식 라이선스 페이지(2026-10-05 조회)는 "EPL v2.0과 LGPL 2.1의 이중 라이선스"라고 적는다. jar 안에는 라이선스 파일이 없고 MANIFEST `Bundle-License`도 EPL 1.0 URL이다. 도구가 읽는 POM 메타데이터는 출발점일 뿐, 판정 전에 프로젝트의 라이선스 원문을 확인해야 한다(장애 3).
- **버전에 따라 라이선스가 바뀐다.** 같은 org.json도 Maven Central의 20231013·20240303 POM은 라이선스를 "Public Domain"으로 적는다. 버전 업이 라이선스 판정을 바꾼다.

### 4. 실험 B: 법령은 바뀐다 — 노트에 인용한 조문 vs law.go.kr 현행

원본 부록(provisions.md, 수집 2026-08-24)의 인용 블록과 국가법령정보센터 Open API(`lawService.do`, XML)로 받은 현행 조문을 단어 단위로 비교했다.

```java
// 인용 블록과 현행 XML을 정규화(개정 표시 <…>·[…] 제거, 'ㆍ'→'·', 공백 정리) 후 단어 LCS diff
diff("법 제34조", quoted(md, "개인정보 보호법 제34조"), current(Path.of("pipa.xml"), "34", ""));
diff("시행령 제40조", quoted(md, "개인정보 보호법 시행령 제40조"), current(Path.of("pipa_dec.xml"), "40", ""));
diff("대조군 법 제21조", quoted(md, "개인정보 보호법 제21조"), current(Path.of("pipa.xml"), "21", ""));
```

(실험, law.go.kr DRF API 2026-10-05 조회 — 법률 제21445호(2026-03-10 공포, 2026-09-11 시행), 대통령령 제36671호(2026-09-10 공포, 2026-09-11 시행) · JDK 21.0.12)

```text
== 법 제34조 : 바뀐 곳 10
  - [유출 등의]  + [유출등의]
  - [분실·도난·유출(이하 이 조에서 "유출등"이라 한다)되었음을]  + [유출등이 되었음을]
  - []  + [구체적인]
  - []  + [6. 개인정보 유출등으로 인한 제39조에 따른 손해배상과 제39조의2에 따른 법정손해배상의 청구 및 제43조에 따른 분쟁조정 등 피해를 입은 정…]
  - []  + [제1항에도 불구하고 개인정보의 유형, 정보주체에게 미치는 영향 및 유출등의 위험 정도를 고려하여 대통령령으로 정하는 유출등의 가능성이 있음을 알…]
  - [경우 그]  + [경우에는 해당 개인정보의 회수·삭제 등 피해 확산을 방지하기 위한 조치를 포함하여]
  - [③]  + [④]
  - [④ 제1항에]  + [⑤ 제1항·제2항에]
  - [유출등의]  + []
  - [제3항에]  + [제4항에]
== 시행령 제40조 : 바뀐 곳 2
  - [제3항]  + [제4항]
  - [지체 없이]  + [즉시]
== 대조군 법 제21조 : 바뀐 곳 0
```

관찰과 해석.
- 원본 수집일(2026-08-24)에 이 개정은 공포(2026-03-10)는 됐지만 시행(2026-09-11) 전이었다. 수집한 "현행" 조문이 3주 뒤 옛 조문이 됐다. **인용한 조문은 시행일과 함께 기록하고, 공포됐지만 시행 전인 개정도 함께 본다**(원본 README의 "법령은 개정이 잦다 — 시행일을 함께 적는다"와 같은 결론).
- 바뀐 내용(현행 원문 기준, 2026-09-11 시행).
  - 법 제34조 ② 신설: 대통령령으로 정하는 **유출등의 가능성**을 알게 되면 가능성이 있는 정보주체 전부에게 피해 최소화 정보 등을 지체 없이 알려야 한다. 시행령 제39조의2·제39조의3 신설: 불법 접근으로 유출이 의심되지만 정보주체를 특정하기 곤란한 경우 등, 알게 된 때부터 **72시간 이내** 통지(천재지변 등 부득이한 사유면 사유 해소 후 즉시 — 제39조의3 ① 단서. 연락처를 알 수 없는 등 정당한 사유가 있으면 홈페이지 등에 30일 이상 게시로 갈음 — 같은 조 ④). 실제 유출이 확인되면 일반 통지로 갈음하고, 유출이 아니면 그 사실을 즉시 통지.
  - 법 제34조 ① 통지 항목에 6호(손해배상·법정손해배상·분쟁조정 등 권리와 행사 방법)·7호(그 밖에 대통령령으로 정하는 사항) 신설(위 diff 출력은 80자에서 잘려 7호가 보이지 않는다). 신고 조항은 ③ → **④**로 이동.
  - 시행령 제39조·제40조: 72시간 예외 사유 해소 후 "지체 없이" → **"즉시"**.
  - 대조군(제21조 파기)은 바뀌지 않았다. diff 도구가 아무 데서나 차이를 만드는 것이 아님을 확인하는 용도다.
- 같은 개정의 다른 조문(diff 대상 밖, 현행 원문에서 확인).
  - 제30조의3 신설: 사업주·대표자가 개인정보 보호의 최종 책임자로서 전문 인력·예산 지원 등 총괄 관리 조치를 해야 한다.
  - 제64조의2 ②: 고의·중과실 반복 위반, 고의·중과실로 피해 1천만 명 이상, 시정명령 불이행으로 유출 등은 **전체 매출액의 10%** 이하 과징금(① 일반은 3% 이하 유지).
  - 제32조의2 ① 단서: 대통령령 기준에 해당하는 처리자는 개인정보 보호 인증 **의무** — 2027-07-01 시행(부칙 제1조).

참고: 원본 §6의 "신고(…)" 설명과 부록의 제34조 인용은 2023 개정 기준(신고 = 제34조 ③)이다. 2026-09-11 시행 현행 기준으로 신고는 제34조 ④이고, 유출 가능성 통지(제34조 ②)가 추가됐다(law.go.kr 현행 원문). 원본 [Claude 추가] D의 과징금 "전체 매출 3%"도 현행에서는 일반 상한이며, 가중 상한 10%가 새로 생겼다.

### 5. 보존 기한을 데이터 모델로

원본 §2-4·§4의 파기·분리 보관 의무를 코드로 옮기면 "기록 유형마다 보존 기한이 붙은 표"가 된다.

```text
  기록 유형                     보존 근거(현행 원문)                          기한       만료 뒤
  ───────────────────────────  ──────────────────────────────────────────   ───────   ─────────────
  회원 프로필(탈퇴)              법 제21조 ① 불필요해지면 지체 없이 파기          —          지체 없이 파기(지침: 5일 이내)
                                표준지침 제10조 ① "정당한 사유가 없는 한 5일 이내"
  계약·청약철회 기록              전자상거래법 시행령 제6조 ① 2호                  5년        파기
  대금결제·재화 공급 기록          같은 항 3호                                    5년        파기
  소비자 불만·분쟁처리 기록        같은 항 4호                                    3년        파기
  표시·광고 기록                  같은 항 1호                                    6개월      파기
  개인정보처리시스템 접속기록       안전성 확보조치 기준 제8조 ①                    1년 이상(요건에 따라 2년 이상)
  접근 권한 부여·변경·말소 내역     같은 기준 제5조 ③                              최소 3년
```

- 법률의 의무는 "지체 없이"(법 제21조 ①)다. "5일 이내"는 표준지침(보호위원회 고시 — 법 제12조 ①에 따라 "준수를 권장"하는 지침)의 기준이므로, 5일을 법이 준 유예기간으로 읽지 않는다(해석·법률 자문 아님).
- 보존 의무로 남기는 데이터는 **분리**해서 저장·관리한다(법 제21조 ③). 표준지침 제11조는 "물리적 또는 기술적 방법으로 분리"하고 처리방침 등으로 정보주체가 알 수 있게 하라고 한다. 전자상거래법 시행령 제6조 ② 3호도 동의를 철회한 소비자의 거래기록을 별도로 보존하라고 한다.
- 파기는 "복구 또는 재생되지 아니하도록"(법 제21조 ②). 시행령 제16조: 전자적 파일은 복원이 불가능한 방법으로 영구 삭제. 표준지침 제10조 ②는 이를 "현재의 기술수준에서 사회통념상 적정한 비용으로" 복원이 불가능하게 하는 것이라 풀이한다.
- 보존 기간의 **기산점**(언제부터 5년인가)은 시행령 제6조 본문에 적혀 있지 않다 — 거래 시점·대금 완제 시점 등 해석이 갈릴 수 있으므로 법무 확인 대상으로 남긴다 `[?]`.

## 쓰이는 자료구조·알고리즘

- **SPDX 표현식 = 불리언 식 트리**: `EPL-1.0 OR LGPL-2.1-only`, `GPL-2.0-only WITH Universal-FOSS-exception-1.0`, `(MIT AND BSD-3-Clause)` 같은 식을 트리로 파싱해 평가한다. OR는 "이 중 하나를 골라 지키면 된다", AND는 "모두 지켜야 한다", WITH는 라이선스에 예외를 붙인다. 실험 A의 검사기는 OR를 "가장 유리한 하나 선택"으로 평가했다.
- **의존성 그래프 순회**: 직접 의존성에서 시작해 전이 의존성까지 그래프(DAG)를 순회해 라이선스 대상 집합을 만든다. 실험 A에서 선언 6개 → 대상 8개.
- **정책 = 판정 함수 + 기본값 실패**: 라이선스 ID → {허용, 검토, 거부} 함수. 모르는 입력의 기본값을 "거부"로 둔다(fail-closed).
- **단어 LCS diff**: 실험 B의 조문 비교. 두 단어 열의 최장 공통 부분열을 동적 계획법(O(n·m) 표)으로 구하고, 공통 부분열 밖의 단어를 삭제·추가로 출력한다.
- **보존 기한 = 유형별 TTL 표 + 만료 인덱스**: 기록마다 `retain_until`을 저장하고 그 칼럼에 인덱스를 두면, 파기 배치는 `retain_until < now()` 범위 조회 한 번으로 대상을 찾는다.
- 연결: 삭제 전파(백업·로그·파생 복제본)와 키 폐기 삭제(crypto-shredding)는 [data-engineering/12-data-retention-and-erasure](../../data-engineering/12-data-retention-and-erasure/2-summary.md). 로그 속 개인정보 마스킹은 [security/27](../../security/27-pii-classification-masking-retention/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **배포 형태를 적는다.** SaaS(서버에서만 실행), 고객 설치형, 모바일 앱, 라이브러리 배포 — 라이선스 의무가 붙는 행위가 달라진다(§2).
2. **라이선스 정책표를 법무와 정한다.** 허용·검토·거부 목록을 SPDX ID로. 모르는 라이선스는 거부가 기본값.
3. **빌드에 라이선스 목록 + 정책 검사를 건다.** 전이 의존성 포함. 위반이면 빌드 실패. 이중 라이선스·예외는 검토 큐로.
4. **고지 산출물을 만든다.** 배포물에 서드파티 고지(라이선스 텍스트·Apache NOTICE 내용)를 포함한다.
5. **데이터 모델에 보존 기한을 넣는다.** 기록 유형마다 근거 조문과 `retain_until`. 보존 의무 데이터는 분리 저장.
6. **파기 배치와 증빙.** 만료 데이터 파기, 파기 기록(표준지침 제10조 ③ — 기록·관리). 백업·로그·분석 복제본의 파기 경로도 적는다.
7. **법령 변경 감시.** 인용 조문을 시행일과 함께 기록하고, 현행 원문과 주기적으로 대조한다(실험 B). 사고 대응 런북의 기한·통지 항목을 그때마다 고친다.

### 2. 탈퇴 처리 — 분리 보관과 파기 (Java, Spring JDBC 가정)

```java
// PostgreSQL 문법 가정 (INTERVAL, now())
@Transactional
public void withdraw(long memberId, Instant now) {
    // 1) 법정 보존 대상만 분리 저장소로 이동 (법 제21조 ③, 전자상거래법 시행령 제6조)
    jdbc.update("""
        INSERT INTO retained_order_record (order_id, member_ref, amount, paid_at, retain_until, legal_basis)
        SELECT o.id, o.member_id, o.amount, o.paid_at, o.paid_at + INTERVAL '5 years',
               'ECOM_DECREE_6_1_3'
          FROM orders o WHERE o.member_id = ?""", memberId);   // 기산점은 법무 확인 사항(예시는 결제 시각)
    // 2) 보존 근거가 없는 개인정보는 파기 예정 표시 — 법: 지체 없이 / 표준지침 제10조: 정당한 사유 없으면 5일 이내
    //    하루 1회 배치는 destroy_by 뒤 최대 24시간 늦게 지우므로, 그만큼 당겨 4일로 잡는다(예시)
    jdbc.update("UPDATE member SET destroy_by = ? WHERE id = ?", Timestamp.from(now.plus(Duration.ofDays(4))), memberId);
    // 3) 요청 접수 기록(언제·누가·무엇을) — 처리 이력 자체가 기한 준수의 증거
    jdbc.update("INSERT INTO privacy_request_log (member_id, kind, received_at) VALUES (?, 'WITHDRAW', ?)",
                memberId, Timestamp.from(now));
}

// 파기 배치: soft delete 플래그가 아니라 실제 삭제 (법 제21조 ② "복구 또는 재생되지 아니하도록")
@Scheduled(cron = "0 0 3 * * *")
public void destroyExpired() {
    int members = jdbc.update("DELETE FROM member WHERE destroy_by < now()");
    int records = jdbc.update("DELETE FROM retained_order_record WHERE retain_until < now()");
    log.info("destroyed members={} retained_records={}", members, records);   // 파기 기록(표준지침 제10조 ③)
}
```

- 운영 DB에서 지워도 백업·로그·검색 인덱스·분석 복제본에 남는다. 그 경로마다 파기 방법(보관 기간 만료로 자연 소멸, 키 폐기 등)을 정한다(해석·법률 자문 아님 — 백업의 파기 방식에 대한 구체 기준은 이 노트에서 확인하지 못했다 `[?]`).
- `DELETE`도 DB 엔진에 따라 물리 공간이 바로 지워지지는 않는다(예: PostgreSQL의 dead tuple은 VACUUM 전까지 페이지에 남는다 — [database/16-mvcc](../../database/16-mvcc/2-summary.md)). "복원이 불가능한 방법"의 기술적 수준은 표준지침 제10조 ②의 "사회통념상 적정한 비용" 기준으로 판단한다(해석·법률 자문 아님).

### 3. 빌드에 라이선스 검사 걸기 (Maven, license-maven-plugin 2.4.0)

```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>license-maven-plugin</artifactId>
  <version>2.4.0</version>
  <executions>
    <execution>
      <id>third-party</id>
      <goals><goal>add-third-party</goal></goals>   <!-- target/generated-sources/license/THIRD-PARTY.txt -->
    </execution>
  </executions>
</plugin>
```

- 생성된 `THIRD-PARTY.txt`를 실험 A의 정책 검사기 같은 단계에 넘겨 위반이면 실패시킨다. 플러그인 자체에도 허용·금지 라이선스 설정이 있다(플러그인 문서 확인 — 이 노트에서는 실행하지 않았다).
- 결과물 `THIRD-PARTY.txt`는 배포물 고지의 출발점이 된다. Apache-2.0 의존성의 `NOTICE` 내용은 따로 모아 포함한다(§4(d)).

### 4. 진단

- `mvn dependency:tree -Dincludes=<groupId>` — 금지 라이선스 의존성이 어느 경로로 들어왔나.
- 정책 검사의 REVIEW 큐 길이, DENY 예외 승인 목록과 만료일.
- `SELECT count(*) FROM member WHERE destroy_by < now() - interval '1 day'` — 파기 배치가 밀리고 있나(0이어야 한다).
- 인용 조문 목록의 "확인 일자"가 가장 오래된 것.

## 장애 시나리오와 대처

### 1. 라이선스 위반 의존성이 배포물에 들어갔다 (⚠ 커리큘럼)

- 현상: 고객 설치형 제품 감사에서 GPL 계열 라이브러리가 발견된다. 납품이 멈춘다.
- 보이는 형태: 배포 이미지의 jar 목록에 있는데 `pom.xml`에는 없다. 실험 A처럼 전이 의존성으로 들어왔다.
- 원인: 직접 선언한 의존성만 확인했다. 빌드에 라이선스 검사가 없다. 모르는 라이선스를 통과시켰다.
- 대처: 전이 의존성까지 펼친 라이선스 목록 + 정책 검사를 빌드 실패 조건으로 건다(모르는 것 = 실패). 이미 배포된 경우 대체 라이브러리 교체·사용 방식 변경·라이선스 조건 이행 중 무엇이 가능한지 법무와 판단한다(해석·법률 자문 아님 — 대응 방식은 사안마다 다르다).

### 2. 개인정보 보관 기한 위반 — 너무 오래, 또는 너무 일찍 (⚠ 커리큘럼)

- 현상: 탈퇴 2년이 지난 회원의 이메일이 마케팅 발송 목록에 나온다. 또는 분쟁이 생긴 주문의 결제 기록을 탈퇴와 함께 지워 증빙을 못 낸다.
- 보이는 형태: `member` 테이블에 `deleted_at`만 있고 행이 그대로다(soft delete). 보존 기록이 일반 테이블에 섞여 있어 목적 외 조회가 된다.
- 원인: 데이터 모델에 보존 기한·근거·분리 보관 개념이 없다. 탈퇴를 플래그로만 처리했다.
- 대처: 기록 유형마다 `retain_until`과 근거 조문, 보존 의무 데이터는 분리 저장(법 제21조 ③·표준지침 제11조), 만료 파기 배치와 파기 기록. 파기 배치가 밀리면 경보.

### 3. 라이선스 메타데이터를 그대로 믿었다

- 현상: 도구 보고서는 "EPL 1.0"인데 프로젝트 사이트는 "EPL 2.0 또는 LGPL 2.1"이다. 또는 버전을 올렸더니 라이선스가 바뀌었다.
- 보이는 형태: 실험 A의 logback 1.5.12(POM EPL 1.0 vs 공식 페이지 EPL v2.0), org.json(20140107 "The JSON License" vs 20231013 이후 "Public Domain").
- 원인: POM의 라이선스 칸은 자유 텍스트이고 갱신이 늦을 수 있다. 판정이 버전을 고려하지 않았다.
- 대처: 자유 텍스트 → SPDX ID 매핑을 검토된 표로 관리하고, 판정은 (좌표, 버전) 단위로 기록한다. 거부·검토 판정 전에 소스 저장소의 LICENSE 원문을 확인한다.

### 4. AGPL 라이브러리를 수정해 SaaS로 제공했다

- 현상: 내부에서 수정한 AGPL 컴포넌트를 외부 고객이 쓰는 웹 서비스로 운영 중인데 소스 제공 경로가 없다.
- 보이는 형태: 라이선스 목록에 `AGPL-3.0-only`/`-or-later`, 저장소에 해당 컴포넌트의 패치가 있다.
- 원인: "배포하지 않으니 copyleft 의무가 없다"는 판단을 GPL 기준으로만 했다. AGPL §13은 수정본을 네트워크로 제공할 때 대응 소스를 받을 기회를 제공하라고 한다.
- 대처: 정책표에서 AGPL은 SaaS에서도 별도 검토 대상으로 둔다. 수정 여부·제공 방식에 따라 법무 판단(해석·법률 자문 아님).

### 5. 개정 법령을 반영하지 못했다 — 유출 가능성 통지 누락

- 현상: 외부 불법 접근 흔적을 발견했지만 유출된 정보주체를 특정하지 못해 "확정되면 통지하자"고 기다린다.
- 보이는 형태: 사고 대응 런북이 "유출이 확인되면 72시간 이내 통지·신고(법 제34조 ①·③)"만 다룬다. 실험 B처럼 인용 조문이 개정 전 것이다.
- 원인: 2026-09-11 시행 개정으로 유출 **가능성** 통지(법 제34조 ②, 시행령 제39조의2: 불법 접근으로 유출이 의심되나 정보주체 특정이 곤란한 경우 등)가 생겼고, 그 기한은 알게 된 때부터 72시간 이내(시행령 제39조의3 ①)다. 신고 조항 번호도 ④로 바뀌었다.
- 대처: 런북의 인용 조문을 현행 원문으로 고치고 시행일을 적는다. 인용 조문 목록을 주기적으로 law.go.kr 현행과 대조한다(실험 B의 diff 방식). 사고 기록에 "알게 된 시각"을 남겨 72시간 기산점을 증명할 수 있게 한다.

## 핵심 문장

- 개인정보 의무는 "처리"에, 오픈소스 라이선스 의무는 "배포(또는 AGPL의 네트워크 제공)"에 붙는다 — 어느 행위를 하는지부터 적어야 의무가 정해진다.
- 라이선스 검사는 전이 의존성까지, 모르는 라이선스는 실패로 — 실험에서 선언 6개가 대상 8개였고 DENY 2건 중 하나는 매핑되지 않은 자유 텍스트였다.
- 도구가 읽는 라이선스 메타데이터는 틀리거나 버전마다 바뀐다. 판정은 (좌표, 버전) 단위로 원문을 확인해 기록한다.
- 보존 기한은 데이터 모델의 칸이다 — 기록 유형마다 근거 조문·`retain_until`·분리 저장·파기 배치·파기 기록을 둔다.
- 법령은 바뀐다. 인용한 조문은 시행일과 함께 적고 현행 원문과 대조한다 — 2026-09-11 시행 개정으로 유출 가능성 통지가 생기고 신고 조항이 제34조 ④로 옮겨졌다.

## 관련 주제·근거

- 원본(기초): [engineering/development-standards/legal-standards](../../engineering/development-standards/legal-standards/2-summary.md) — 개인정보 생명주기·안전성 확보조치·정보주체 권리·유출 통지와 신고·관련 법령 · 조문 부록 [provisions.md](../../engineering/development-standards/legal-standards/provisions.md)(수집 2026-08-24) · 네 축 개요 [development-standards/README](../../engineering/development-standards/README.md)·[index](../../engineering/development-standards/index.md)
- 선행: [14-quality-standards](../14-quality-standards/2-summary.md) — 기준 → 자동 검사(게이트·기준선) 구조
- 후속·연결
  - [15-security-standards](../15-security-standards/2-summary.md) — 같은 의존성 목록으로 SCA, 안전성 확보조치와 보안 기준의 겹침
  - [16-operational-standards](../16-operational-standards/2-summary.md) — 로그 표준의 개인정보 금지 필드, 접속기록 보관
  - [reliability/18-logs-traces-audit-roles](../../reliability/18-logs-traces-audit-roles/2-summary.md) — 로그 속 개인정보와 삭제 범위, 감사 기록
  - [security 27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md) · [data-engineering/12-data-retention-and-erasure](../../data-engineering/12-data-retention-and-erasure/2-summary.md)
  - [13-build-vs-buy-and-adoption](../13-build-vs-buy-and-adoption/2-summary.md) — OSS 도입 판단(유지보수자·라이선스 건강도)
- 근거 — 법령(law.go.kr 현행 원문, 2026-10-05 조회)
  - 개인정보 보호법(법률 제21445호, 2026-03-10 공포, 2026-09-11 시행) 제21조·제30조의3·제32조의2·제34조·제64조의2·부칙 제1조 <https://www.law.go.kr/법령/개인정보보호법>
  - 개인정보 보호법 시행령(대통령령 제36671호, 2026-09-10 공포, 2026-09-11 시행) 제16조·제39조·제39조의2·제39조의3·제40조
  - 개인정보의 안전성 확보조치 기준(개인정보보호위원회 고시 제2026-9호, 2026-07-01) 제5조·제7조·제8조
  - 표준 개인정보 보호지침(고시 제2025-4호, 2025-04-11) 제10조·제11조
  - 전자상거래 등에서의 소비자보호에 관한 법률 시행령(2026-07-21 시행본) 제6조
  - 정보통신망법(2026-10-02 시행본) 제50조 — 영리목적 광고성 정보 전송의 사전 동의·야간(21시~08시) 별도 동의(마케팅 발송 기능 설계 시)
- 근거 — 라이선스
  - SPDX License List v3.29.0(2026-09-16) <https://spdx.org/licenses/> · `licenses.json`·`exceptions.json`
  - MIT <https://opensource.org/license/mit> · Apache License 2.0 §4 <https://www.apache.org/licenses/LICENSE-2.0> · GPL-3.0 정의("convey") <https://www.gnu.org/licenses/gpl-3.0.html> · AGPL-3.0 §13 <https://www.gnu.org/licenses/agpl-3.0.html>
  - FSF, Various Licenses and Comments about Them — Apache-2.0(GPLv3 호환·GPLv2 비호환), JSON License(비자유) <https://www.gnu.org/licenses/license-list.html> · 같은 판정의 교차 확인: ASF "GPL compatibility" 페이지("the FSF has never considered the Apache License to be compatible with GPL version 2, citing the patent termination and indemnification provisions") <https://www.apache.org/licenses/GPL-compatibility.html>, SPDX `licenses.json`의 `JSON` 항목 `isFsfLibre=false`
  - logback 라이선스 페이지 <https://logback.qos.ch/license.html> · license-maven-plugin 2.4.0 <https://www.mojohaus.org/license-maven-plugin/>
- 실험 목록
  - A. 라이선스 목록·정책 게이트: license-maven-plugin 2.4.0, Maven 3.9.16, temurin 21.0.12 컨테이너 — 의존성 선언 6 → 목록 8, ALLOW 3 · REVIEW 3 · DENY 2, exit 1. logback POM(EPL 1.0)과 공식 페이지(EPL v2.0) 불일치, org.json 버전별 라이선스 표기 차이(Maven Central POM).
  - B. 조문 diff: law.go.kr DRF API XML vs 원본 provisions.md 인용 — 법 제34조 바뀐 곳 10, 시행령 제40조 2, 대조군 제21조 0.
  - C. SPDX 목록 조회: v3.29.0, 740개, OSI 승인 154개, 주요 ID의 `isOsiApproved` 값.
