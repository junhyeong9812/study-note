# testing/21-test-incidents — 실사건: Apple goto fail(CVE-2014-1266, 2014) · CrowdStrike 채널 파일 291(2024) — 시험·검증 관점 — 정리 (힌트)

## 해결하는 문제

leaf 노트는 테스트의 빈틈을 **하나씩** 다룬다.\
경계값은 07번, 대역의 계약은 03번, 커버리지의 한계는 16번, 계약 테스트는 13번이다.\
실제 사고에서는 빈틈 여러 개가 **겹쳐서** 결함이 끝까지 지나간다.\
그리고 겹친 층마다 "다른 층이 막아 주겠지"라는 믿음이 하나씩 있다.

```text
  leaf 노트:  [음성 테스트] [도달 불가 코드] [시험 입력의 분포] [정의와 구현의 계약] [검증기 자체의 시험] [단계 배포]  <- 각각 따로
  실사건:
    goto fail     중복된 한 줄 -> 서명 확인을 건너뜀 -> 오류 코드는 0 -> "서명 일치"로 진행 -> 잘못된 서명도 통과
    CrowdStrike   정의 21개·제공 20개 -> 시험 입력은 21번째가 늘 와일드카드 -> 검증기는 정의(21)만 봄 -> 비와일드카드 콘텐츠 -> 범위 밖 읽기
```

쉬운 예: 현관 도어락을 시험한다.\
"맞는 비밀번호로 열린다"만 매일 확인했다.\
"틀린 비밀번호로는 안 열린다"는 한 번도 확인하지 않았다.\
어느 날 배선이 바뀌어 아무 번호로나 열리게 됐다. 매일 하던 시험은 계속 통과했다.

똑같은 구조다.\
Apple의 서명 확인 함수에는 한 줄(`goto fail;`)이 두 번 들어갔다. 그 뒤의 서명 확인이 실행되지 않았다.\
올바른 서명을 넣는 시험은 그래도 통과한다. 결함은 **잘못된 서명을 넣었을 때만** 보인다.

이 노트는 공개 1차 문서로 두 사건을 복원하고, 시험·검증의 빈틈만 본다.
- **Apple goto fail(2014-02)**: TLS 서버 키 교환 메시지의 서명을 확인하지 않는 결함. 1차 출처: Apple 보안 업데이트 문서, NVD CVE-2014-1266, Apple 공개 소스 `sslKeyExchange.c`.
- **CrowdStrike 채널 파일 291(2024-07-19)**: 보안 센서의 콘텐츠 업데이트가 Windows 호스트를 크래시시킨 사건. 1차 출처: CrowdStrike 예비 PIR(2024-07-25 1900 UTC 갱신판), 기술 RCA(2024-08-06).
- 운영 관점(단계 배포 부재·되돌림이 복구가 아닌 이유·영향 규모)은 [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md) 사건 4가 다룬다. 이 노트는 겹치는 사실을 짧게만 쓴다.

  - *음성 테스트(negative test)*: 시스템이 **거부해야 하는** 입력을 넣고 거부하는지 확인하는 테스트다. 검증기·인증·권한 코드에서 핵심이다.
  - *사실과 해석*: 원문에 있는 사실은 출처와 함께 쓴다. 원문이 말하지 않는 추론은 "해석"이라고 표시한다.

## 동작·원리

### 사건 1 — Apple goto fail (CVE-2014-1266, 2014-02)

출처: Apple, "Apple security updates (2014)" 목록 <https://support.apple.com/kb/HT205762>(2026-10-03 현재 <https://support.apple.com/en-us/101445>로 넘어감) · "About the security content of iOS 7.0.6" <https://support.apple.com/en-us/103608> · "About the security content of OS X Mavericks v10.9.2 and Security Update 2014-001" <https://support.apple.com/en-us/103380> · NVD CVE-2014-1266 <https://nvd.nist.gov/vuln/detail/CVE-2014-1266> · Apple 공개 소스 `Security` 저장소의 태그 `Security-55471`(수정 전)과 `Security-55471.14`(수정 후) <https://github.com/apple-oss-distributions/Security> · Adam Langley, "Apple's SSL/TLS bug", 2014-02-22 <https://www.imperialviolet.org/2014/02/22/applebug.html>.

#### 사실 — 날짜

| 날짜 | 사건 | 출처 |
|---|---|---|
| 2014-02-21 | iOS 7.0.6, iOS 6.1.6, Apple TV 6.0.2 배포 | Apple 2014 보안 업데이트 목록 |
| 2014-02-22 | NVD에 CVE-2014-1266 게시. Langley가 원인 분석 글 게시 | NVD(published 2014-02-22) · imperialviolet.org |
| 2014-02-25 | OS X Mavericks 10.9.2 및 Security Update 2014-001 배포 | Apple 2014 보안 업데이트 목록 |

- 영향 범위(NVD 설명 원문): "Apple iOS 6.x before 6.1.6 and 7.x before 7.0.6, Apple TV 6.x before 6.0.2, and Apple OS X 10.9.x before 10.9.2".
- 결함(NVD 설명 원문): `SSLVerifySignedServerKeyExchange` 함수가 "does not check the signature in a TLS Server Key Exchange message". 그래서 중간자 공격자가 "(1) using an arbitrary private key for the signing step or (2) omitting the signing step"으로 SSL 서버를 사칭할 수 있었다.
- Apple 문서의 설명: "Secure Transport failed to validate the authenticity of the connection. This issue was addressed by restoring missing validation steps."
- NVD 점수(2026-10-03 조회): CVSS v3.1 7.4(HIGH), v2 5.8(MEDIUM).
- 날짜 사이의 해석: iOS는 2월 21일, OS X는 2월 25일에 고쳐졌다. 원인 분석은 22일에 공개됐다. 해석: OS X 사용자는 원인이 공개된 뒤 며칠 동안 수정판 없이 있었다.

#### 사실 — 코드

`libsecurity_ssl/lib/sslKeyExchange.c`, 태그 `Security-55471`의 `SSLVerifySignedServerKeyExchange` 일부(618~650행, 원문 그대로):

```c
	hashOut.data = hashes + SSL_MD5_DIGEST_LEN;
    hashOut.length = SSL_SHA1_DIGEST_LEN;
    if ((err = SSLFreeBuffer(&hashCtx)) != 0)
        goto fail;

    if ((err = ReadyHash(&SSLHashSHA1, &hashCtx)) != 0)
        goto fail;
    if ((err = SSLHashSHA1.update(&hashCtx, &clientRandom)) != 0)
        goto fail;
    if ((err = SSLHashSHA1.update(&hashCtx, &serverRandom)) != 0)
        goto fail;
    if ((err = SSLHashSHA1.update(&hashCtx, &signedParams)) != 0)
        goto fail;
        goto fail;
    if ((err = SSLHashSHA1.final(&hashCtx, &hashOut)) != 0)
        goto fail;

	err = sslRawVerify(ctx,
                       ctx->peerPubKey,
                       dataToSign,				/* plaintext */
                       dataToSignLen,			/* plaintext length */
                       signature,
                       signatureLen);
	if(err) {
		sslErrorLog("SSLDecodeSignedServerKeyExchange: sslRawVerify "
                    "returned %d\n", (int)err);
		goto fail;
	}

fail:
    SSLFreeBuffer(&signedHashes);
    SSLFreeBuffer(&hashCtx);
    return err;
```

두 태그의 같은 파일을 받아 비교했다(실행 확인, GNU diff, 2026-10-03):

```text
$ diff Security-55471.c Security-55471.14.c
631d630
<         goto fail;
```

- 수정은 631행 한 줄 삭제가 전부다.
- 호출하는 쪽(같은 파일 845~848행)은 `if(err) goto fail;` 다음에 주석 `/* Signature matches; now replace server key with new key (RSA only) */`으로 진행한다. 즉 **반환값 0 = 서명 일치**로 읽는다.

```text
  update(signedParams) 성공 → err = 0
        │
        ▼
  goto fail;  (631행 — 조건 없음)
        │                         ┌────────────────────────────────┐
        └──────────────────────▶ │ final() · sslRawVerify() 건너뜀  │
                                  └────────────────────────────────┘
        ▼
  fail: return err;   ← err는 직전 단계의 0
        │
        ▼
  호출자: if(err) 아님 → "Signature matches" 경로로 진행
```

- 같은 파일에 TLS 1.2용 함수 `SSLVerifySignedServerKeyExchangeTls12`가 따로 있다. 호출자는 `sslVersionIsLikeTls12(ctx)`이면 그쪽을 부른다(836~843행). Langley는 이 때문에 TLS 1.2는 영향이 없다고 적었다. 다만 바로 이어서 공격자가 클라이언트가 받아들이는 판을 고를 수 있다고 적었다("the attacker can choose any version that the client will accept"). 같은 글은 DHE·ECDHE를 쓰는 사이트만의 문제가 아니라는 점도 적는다("the attacker gets to choose the ciphersuite").

#### 시험 관점 — 원문이 말한 것과 해석

- Langley(원문): "A test case could have caught this, but it's difficult because it's so deep into the handshake. One needs to write a completely separate TLS stack, with lots of options for sending invalid handshakes."
- Langley(원문): 같은 문제를 가진 축약 코드(`goto out;` 뒤의 `ret = f();`)를 `-Wall`로 컴파일하면 GCC 4.8.2·Clang 3.3(Xcode) 모두 경고가 없었고, Clang의 `-Wunreachable-code`는 `-Wall`에 들어 있지 않다고 적었다. 같은 글은 코드 리뷰("review of each change as it goes in")도 효과적이었을 것이라고 적었다.
- 해석
  - **양성 테스트는 이 결함을 볼 수 없다.** 올바른 서명은 확인을 건너뛰어도 "통과"라는 같은 결과를 낸다. 결과가 같으니 테스트가 구별할 방법이 없다.
  - 필요한 것은 **거부해야 할 입력의 목록**이다. NVD 설명의 두 공격 방식(다른 키로 서명, 서명 생략)이 그대로 음성 테스트 두 개가 된다.
  - 서명 확인 줄은 어떤 입력으로도 실행되지 않았다. 라인 커버리지를 봤다면 "실행 안 된 줄"로 보였을 것이다(아래 실험 A-3). 커버리지는 단언의 질은 못 재지만, **아예 안 돈 줄**은 보여 준다([16](../16-coverage-and-its-limits/2-summary.md)).

### 사건 2 — CrowdStrike 채널 파일 291 (2024-07-19)

출처: CrowdStrike, "Falcon Content Update Preliminary Post Incident Report"(이하 PIR, 2024-07-25 1900 UTC 갱신판) <https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/> · "External Technical Root Cause Analysis — Channel File 291"(이하 RCA, 2024-08-06, 12쪽) <https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf>.

#### 사실 — 구성 요소 (RCA 「Background and Terminology」)

```text
  센서 빌드에 컴파일되는 것                             클라우드에서 수시로 내려가는 것
  ┌──────────────────────────────┐                   ┌─────────────────────────────────┐
  │ Template Type (IPC)          │                   │ Template Instance (정규식 기준)   │
  │   통합 코드: 입력 20개를 넘김   │                   │   필드 21개 — 각 칸은 정규식 또는 * │
  └──────────────┬───────────────┘                   └───────────────┬─────────────────┘
                 │                                                   │ Content Validator
  ┌──────────────┴───────────────┐                                   │ "정의 파일"과 대조
  │ Template Type Definitions 파일 │◀──────────────── 기준 ──────────────┘
  │   IPC = 입력 21개라고 적힘      │                                   │
  └──────────────────────────────┘                                   ▼ Channel File 291
                                     ┌─────────────────────────────────────────────┐
                                     │ Content Interpreter (센서 C++ 코드, 커널 드라이버) │
                                     │   입력 배열[0..19] 에서 기준이 가리키는 칸을 읽음   │
                                     └─────────────────────────────────────────────┘
```

- RCA 원문: "The new IPC Template Type defined 21 input parameter fields, but the integration code that invoked the Content Interpreter with Channel File 291's Template Instances supplied only 20 input values to match against."
- RCA는 Rapid Response Content를 "configuration data; it is not code or a kernel driver"라고 적는다. 해석: 코드가 아니라는 이유로 코드와 다른 시험·배포 경로를 탔다.

#### 사실 — 시험·검증 관련 날짜 (PIR·RCA)

| 날짜(UTC 표시는 원문대로) | 사건 | 출처 |
|---|---|---|
| 2024-02-28 | 센서 7.11 정식 배포. IPC Template Type 도입. 센서 콘텐츠 시험 절차를 모두 거침 | PIR |
| 2024-03-05 | 스테이징에서 IPC Template Type 스트레스 시험 통과, 사용 승인. 같은 날 첫 IPC Template Instance 운영 배포 | PIR |
| 2024-04-08 ~ 04-24 | IPC Template Instance 세 개 추가 배포. "performed as expected in production" | PIR |
| 2024-07-19 04:09 UTC | IPC Template Instance 두 개 추가 배포. 그중 하나가 21번째 필드에 **비와일드카드** 기준을 처음 넣음. Content Validator의 버그로 검증 통과 | PIR · RCA |
| 2024-07-19 05:27 UTC | 결함 있는 콘텐츠 되돌림 | PIR |
| 2024-07-19 → 07-27 | 센서 콘텐츠 컴파일러에 Template Type 입력 수 검사 패치 개발(7-19), 운영 투입(7-27) | RCA 소견 1 |
| 2024-07-25 | Content Interpreter에 입력 배열 범위 검사와 "배열 크기 = 콘텐츠가 기대하는 입력 수" 검사 추가 | RCA 소견 2 |
| 2024-08-09까지 | 위 수정의 핫픽스(7.11 이상 Windows 센서) 정식 배포 예정 | RCA 소견 2 |
| 2024-08-19까지 | Content Validator에 "제공되는 입력보다 많은 필드를 매칭하지 않는지" 검사 추가 예정 | RCA 소견 4 |

- 영향 범위(PIR): 7.11 이상 Windows 센서 중 7-19 04:09~05:27 UTC 사이 온라인이었고 업데이트를 받은 호스트. Mac·Linux는 영향 없음. 영향 기기 수·복구 경과는 [reliability/53](../../reliability/53-reliability-incidents/2-summary.md) 사건 4.

#### 사실 — 시험을 빠져나간 층 (RCA 원문 요약)

RCA는 개수 불일치가 "evaded multiple layers of build validation and testing"이라고 적고, 층을 나열한다.

| 층 | 무엇을 했나 (RCA) | 왜 못 잡았나 (RCA) |
|---|---|---|
| 센서 7.11 릴리스 시험 | 수동·자동 시험. 자동 시험은 **정적 시험 사례 12개**를 대표로 골랐다 | 시험용 채널 파일 데이터를 손으로 골랐고, 모든 Template Instance의 21번째 필드가 정규식 **와일드카드**였다 |
| Template Type 스트레스 시험 | 시험용 Template Instance로 자원·성능·탐지량을 봄(3월 5일 통과 — 날짜는 PIR) | 시험용 인스턴스로는 개수 불일치가 크래시로 이어진다는 것이 드러나지 않음 |
| 운영의 첫 배포들(3~4월) | 인스턴스 네 개가 정상 동작 | 21번째 필드를 쓴 인스턴스가 하나도 없었다("no IPC Template Instances in previous channel versions had made use of the 21st input parameter field") |
| Content Validator | 새 인스턴스를 정의 파일과 대조 | 정의(21개)를 기준으로 판단 — 실제로 넘어가는 입력(20개)과 대조하지 않음. RCA 소견 4의 제목: "The Content Validator contained a logic error" |
| Content Interpreter | 기준이 가리키는 입력을 읽음 | 런타임 범위 검사가 없었다(소견 2) |
| 배포 | 콘텐츠를 전 대상에 한 번에 | 소견 6: "Each Template Instance should be deployed in a staged rollout" |

- RCA 요약 문단(원문): 크래시는 "the mismatch between the 21 inputs validated by the Content Validator versus the 20 provided to the Content Interpreter, the latent out-of-bounds read issue in the Content Interpreter, and the lack of a specific test for non-wildcard matching criteria in the 21st field"의 합류였다.
- PIR(원문): 배포 결정의 근거로 "testing performed before the initial deployment of the Template Type (on March 05, 2024), trust in the checks performed in the Content Validator, and previous successful IPC Template Instance deployments"를 든다.
- 크래시 덤프(RCA 원문): `PAGE_FAULT_IN_NONPAGED_AREA (50)`, `IMAGE_NAME: csagent.sys`. 인덱스 레지스터 `r11`이 `0x14`(= 21번째 원소)였고, 입력 포인터 배열 20개 뒤의 21번째 값(`ffffd6030000006a`)이 유효하지 않은 주소였다.

#### 사실 — 시험 관련 조치 (RCA 소견 1~5)

- 소견 1: 센서 컴파일 시점에 Template Type의 입력 수를 검사(7-27 운영).
- 소견 2: 런타임 범위 검사 + 배열 크기 검사. "We have completed fuzz testing of the Channel 291 Template Type".
- 소견 3: "automated tests have been created that test with non-wildcard matching criteria for each field" — 기존 Template Type 전부, 이후 모든 Template Type에 의무. 운영 사용을 더 닮은 시나리오 추가.
- 소견 4: 검증기 검사 추가. 그때까지는 21번째 필드에 와일드카드만 허용.
- 소견 5: Template Type을 처음 시험할 때만이 아니라 **새 Template Instance마다** 시험.

#### 시험 관점 — 해석

- **시험 입력이 그 필드를 한 번도 "쓰지" 않았다.** 와일드카드는 입력을 읽지 않고 통과한다. 21번째 필드에 대해서는 시험 사례 12개가 모두 같은 동치 클래스(와일드카드)였다. 비와일드카드 클래스가 비어 있었다([07](../07-test-design-techniques/2-summary.md)의 동치 분할).
- **검증기와 소비자가 서로 다른 진실을 믿었다.** 검증기는 정의 파일(21)을, 인터프리터는 통합 코드가 넘긴 배열(20)을 믿었다. 두 쪽이 같은 계약으로 시험되지 않았다. 대역과 실제 구현이 다른 계약을 지키는 [03](../03-test-doubles/2-summary.md)·[13](../13-contract-testing/2-summary.md)의 구조와 같다.
- **"운영에서 몇 번 잘 돌았다"는 그 경로가 실행됐다는 뜻이 아니다.** 3~4월 운영에 나간 인스턴스 네 개는 21번째 필드를 쓰지 않았다(PIR은 인스턴스 수만 적고 배포 횟수는 적지 않는다). 운영 이력은 실행된 경로만 보증한다.
- **검증기도 시험 대상이다.** 검증기의 논리 오류가 마지막 그물을 뚫었다. "검증기를 통과했다"는 검증기가 맞을 때만 증거다.

### 두 사건을 나란히 (해석)

| | goto fail | 채널 파일 291 |
|---|---|---|
| 결함의 크기 | 한 줄 | 숫자 하나(21 vs 20) |
| 통과한 시험 | 올바른 서명을 넣는 경로 | 21번째가 와일드카드인 시험 사례 12개, 스트레스 시험, 운영에 나간 인스턴스 네 개 |
| 결함이 보이는 입력 | 잘못된 서명·서명 없음 | 21번째 필드에 비와일드카드 기준 |
| 빠진 시험 | 음성 테스트 | 필드별 비와일드카드 시험, 검증기 대 인터프리터 계약 시험 |
| 도구가 줄 수 있던 신호 | 도달 불가 코드 경고(`-Wall` 밖), 라인 커버리지의 미실행 줄 | 컴파일 시점 개수 검사, 런타임 범위 검사, 퍼징 |
| 출처의 조치 | 중복 줄 삭제(631행) | 컴파일 검사·범위 검사·필드별 시험·검증기 검사·인스턴스별 시험·단계 배포 |

- 공통점: 두 결함 모두 **결과가 "통과"인 쪽으로 기운 경로**에 숨었다. 시험 입력이 그 경로를 지나도 결과가 정상과 같거나(goto fail), 그 경로를 아예 지나지 않았다(291).

### 실험 A: goto fail 모형 — 음성 테스트가 있으면 잡힌다

기존 Docker 이미지(`eclipse-temurin:21-jdk`, `maven:3.9-eclipse-temurin-21`, `node:22-alpine`, `node:22-bookworm-slim`, `postgres:17`)에 C 컴파일러(`gcc`·`cc`·`clang`·`tcc`)가 없었다(`command -v`로 확인). 새 이미지를 받지 않기로 했으므로 **Java와 JavaScript로 같은 구조를 옮겼다.** C의 `goto fail`은 레이블 블록 탈출(`break fail`)로 옮겼다.

#### A-1. Java는 같은 한 줄을 컴파일하지 않는다

```java
fail: {
    if ((err = update(1)) != 0)
        break fail;
    if ((err = update(2)) != 0)
        break fail;
        break fail;                      // 복사·붙여넣기로 한 줄 더
    if ((err = update(3)) != 0)
        break fail;
    err = rawVerify(sigOk);
}
```

(실험, eclipse-temurin:21-jdk · javac 21.0.12, `--network none`, 2026-10-03)

```text
GotoFail.java:13: error: unreachable statement
            if ((err = update(3)) != 0)
            ^
1 error
javac exit=1
```

- Java 언어 명세(JLS 14.22 Unreachable Statements)는 도달할 수 없는 문장을 컴파일 오류로 정한다. 그래서 위 모양은 Java에서 빌드조차 되지 않는다.
- 해석: 같은 실수가 언어에 따라 ①작성 시점 오류(Java)가 되기도, 아무 신호 없는 실행 파일(Langley가 본 `-Wall`의 C)이 되기도 한다. 다만 Java에서도 `if (조건) break fail;`처럼 조건이 붙으면 도달 가능하므로 막히지 않는다. 그래서 A-2는 조건으로 감쌌다.

#### A-2. 양성 테스트만 vs 음성 테스트 포함 (Java · JUnit 5)

```java
public static int verify(PublicKey serverKey, byte[] signedParams, byte[] signature) {
    int err = 0;
    fail: {
        if ((err = step()) != 0) break fail;
        if ((err = step()) != 0) break fail;
        if (BUGGY) break fail;          // goto fail 중복을 javac가 받아들이는 모양으로 옮김
        if ((err = step()) != 0) break fail;
        err = rawVerify(serverKey, signedParams, signature);   // SHA256withRSA 검증, 실패면 -9809
    }
    return err;
}
```

```java
@Test void 서버_키로_서명하면_받아들인다() throws Exception {
    assertEquals(0, KeyExchangeVerifier.verify(server.getPublic(), PARAMS, sign(server.getPrivate(), PARAMS)));
}
@Nested @Tag("negative") class 거부해야_하는_입력 {
    @Test void 다른_키로_서명() throws Exception {          // NVD (1) arbitrary private key
        assertNotEquals(0, KeyExchangeVerifier.verify(server.getPublic(), PARAMS, sign(attacker.getPrivate(), PARAMS)), "공격자 키 서명");
    }
    @Test void 서명_생략() {                                // NVD (2) omitting the signing step
        assertNotEquals(0, KeyExchangeVerifier.verify(server.getPublic(), PARAMS, new byte[0]), "빈 서명");
    }
    @Test void 파라미터_변조() throws Exception {
        byte[] sig = sign(server.getPrivate(), PARAMS);
        byte[] tampered = PARAMS.clone(); tampered[0] ^= 1;
        assertNotEquals(0, KeyExchangeVerifier.verify(server.getPublic(), tampered, sig), "변조된 파라미터");
    }
}
```

(실험, maven:3.9-eclipse-temurin-21 — Maven 3.9.16 · JDK 21.0.11 · JUnit 5.13.4 · surefire 3.5.3, `--network none`, 2026-10-03)

```text
=== 결함판, 양성 테스트만 (-DexcludedGroups=negative)
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
=== 결함판, 음성 테스트 포함
org.opentest4j.AssertionFailedError: 공격자 키 서명 ==> expected: not equal but was: <0>
org.opentest4j.AssertionFailedError: 빈 서명 ==> expected: not equal but was: <0>
org.opentest4j.AssertionFailedError: 변조된 파라미터 ==> expected: not equal but was: <0>
[ERROR] Tests run: 4, Failures: 3, Errors: 0, Skipped: 0
=== 수정판, 음성 테스트 포함
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

- 관찰: 결함판에서 양성 테스트는 초록이다. 음성 테스트 3개는 모두 빨강이고, 메시지가 "거부해야 할 입력을 0(성공)으로 받았다"고 말한다.
- 수정판은 4개 모두 초록이다. 음성 테스트는 수정 **전에** 빨강, 수정 **후에** 초록 — 결함을 가리키는 테스트다.

#### A-3. 같은 모형을 JS로 — 라인 커버리지가 보여 주는 것

Node의 `crypto` 서명으로 같은 구조를 짰다(`verifyBuggy`·`verifyFixed`). JS는 도달 불가 코드를 오류로 다루지 않아 C처럼 그대로 실행된다.

(실험, node:22-alpine · Node v22.23.2 · `node:test`, `--network none`, 2026-10-03)

```text
=== IMPL=buggy NEG=0
✔ 양성: 서버 키로 서명한 파라미터는 받아들인다
ℹ pass 1
ℹ fail 0
=== IMPL=buggy NEG=1
✔ 양성: 서버 키로 서명한 파라미터는 받아들인다
✖ 음성: 다른 키로 서명하면 거부한다
✖ 음성: 서명이 비어 있으면 거부한다
✖ 음성: 파라미터를 바꾸면 거부한다
ℹ pass 1
ℹ fail 3
=== IMPL=fixed NEG=1
ℹ pass 4
ℹ fail 0
```

양성 테스트만 돌린 결함판의 커버리지(`node --test --experimental-test-coverage`):

```text
# file         | line % | branch % | funcs % | uncovered lines
# gotofail.mjs |  58.33 |    50.00 |   50.00 | 5-7 14-16 20-28
```

- 5~7행은 서명 확인 함수 `rawVerify` 본문, 14~16행은 중복 탈출 뒤(세 번째 단계와 `err = rawVerify(...)` 호출), 20~28행은 이 실행에서 부르지 않은 수정판 함수다.
- 관찰: 양성 테스트가 초록인데도 **서명 확인 줄이 한 번도 실행되지 않았다**는 사실이 커버리지 보고서에 보인다. 커버리지는 단언의 질을 못 재지만, 보안 확인 줄이 미실행이라는 신호는 줄 수 있다.

### 실험 B: 채널 파일 291 모형 — 와일드카드 시험은 통과, 필드별 시험이 잡는다

RCA의 용어대로 아주 작은 모형을 JS로 만들었다. 실제 CrowdStrike 코드가 아니다. 정의는 21개, 통합 코드는 입력 20개, 와일드카드 `*`는 입력을 읽지 않는다.

```js
export const DEFINITION = { name: 'IPC', inputCount: 21 };       // 정의 파일: 21개
export const sensorInputs = (evt) =>                              // 통합 코드: 20개만
  Array.from({ length: 20 }, (_, i) => ({ buf: `${evt}-f${i + 1}` }));
export function validate(instance, expectedCount) {              // Content Validator
  if (instance.criteria.length !== expectedCount) throw new Error(`field count ${instance.criteria.length} != ${expectedCount}`);
  return true;
}
export function interpret(instance, inputs, { boundsCheck = false } = {}) {   // Content Interpreter
  return instance.criteria.every((re, i) => {
    if (re === '*') return true;                                  // 와일드카드: 입력을 읽지 않는다
    if (boundsCheck && i >= inputs.length) return false;          // RCA 소견 2의 범위 검사
    return new RegExp(re).test(inputs[i].buf);                    // inputs[20]은 undefined
  });
}
```

(실험, node:22-alpine · Node v22.23.2 · `node:test`, `--network none`, 2026-10-03)

```text
✔ 기존 시험: 21번째 필드가 와일드카드인 인스턴스 12개
✖ 7월 19일형: 21번째 필드에 비와일드카드 — 검증기는 통과시킨다
✖ RCA 완화책 3: 필드마다 비와일드카드 기준으로 시험
✔ RCA 완화책 4: 검증기가 실제로 넘기는 입력 수와 비교
✔ RCA 완화책 2: 런타임 범위 검사가 있으면 크래시 대신 불일치
ℹ tests 5
ℹ pass 3
ℹ fail 2
✖ 7월 19일형: 21번째 필드에 비와일드카드 — 검증기는 통과시킨다
  TypeError: Cannot read properties of undefined (reading 'buf')
✖ RCA 완화책 3: 필드마다 비와일드카드 기준으로 시험
  AssertionError [ERR_ASSERTION]: Got unwanted exception: field 21
    actual: TypeError: Cannot read properties of undefined (reading 'buf')
```

- 관찰 1: 와일드카드만 쓴 시험 12개는 초록이다. 결함이 있어도 그 필드를 읽지 않기 때문이다.
- 관찰 2: "7월 19일형" 시험에서 정의(21)와 대조한 `validate`는 통과했고, 그 뒤 `interpret`가 터졌다. 검증기 통과가 안전을 뜻하지 않았다.
- 관찰 3: 필드마다 비와일드카드 기준을 하나씩 넣는 시험(RCA 소견 3의 방식)은 `field 21`에서 실패한다 — 개발 단계에서 잡히는 빨강이다.
- 관찰 4: 검증기가 실제로 넘어가는 입력 수(20)와 비교하면 `field count 21 != 20`으로 거부하고(소견 4), 런타임 범위 검사가 있으면 예외 대신 "불일치"로 끝난다(소견 2).
- 한계: JS에서 범위 밖 읽기는 `undefined`라 바로 `TypeError`가 난다. C++ 커널 코드에서는 범위 밖 메모리를 읽어 무엇이 나올지 정해지지 않는다(RCA의 덤프에서는 유효하지 않은 주소). 이 모형은 "시험 입력이 경로를 지나가나"만 보여 준다.

## 쓰이는 자료구조·알고리즘

- **제어 흐름 그래프와 도달 불가 노드**: goto fail은 무조건 간선 하나가 `sslRawVerify` 노드로 가는 모든 경로를 끊은 것이다. Java 컴파일러는 JLS 14.22의 도달 가능성 규칙으로 이런 노드를 오류로 만든다. 커버리지 도구는 실행 시점에 "한 번도 방문하지 않은 노드"로 보여 준다([16](../16-coverage-and-its-limits/2-summary.md)).
- **오류 코드 누적 + 단일 출구**: `err`에 상태를 담고 실패하면 `fail:`로 모으는 C 관용구다. 성공 상태(0)를 담은 채로 출구에 닿으면 "성공"이 된다. 기본값이 성공 쪽인 구조라서 경로 누락이 곧 통과가 된다. 해석: 기본값을 실패 쪽(`err = 실패`로 시작, 마지막 확인이 성공일 때만 0)으로 두면 같은 누락이 거부로 끝난다.
- **동치 분할 — 필드별 와일드카드/비와일드카드**: Template Instance의 각 필드는 "입력을 읽지 않음(*)"과 "입력을 읽음(정규식)" 두 클래스로 나뉜다. 필드 21개 × 두 클래스 중 21번째 필드의 비와일드카드 클래스가 시험에서 비어 있었다. RCA 소견 3의 조치는 클래스마다 대표 하나를 넣는 것이다([07](../07-test-design-techniques/2-summary.md)).
- **배열 범위 검사와 개수 불변식**: "정의의 입력 수 = 통합 코드가 넘기는 수 = 콘텐츠가 매칭하는 수". 세 값이 한 곳에서 대조되지 않았다. 조치는 컴파일 시점(정의 대 통합 코드)과 런타임(배열 크기 대 콘텐츠 기대 수) 두 곳의 검사다.
- **퍼징**: RCA 소견 2는 채널 291 Template Type의 퍼즈 시험을 마쳤다고 적는다. 무작위 입력으로 경로를 넓히는 방식은 [14](../14-property-based-testing/2-summary.md)의 무작위 생성과 같은 계열이다.

## 적용 — 풀어나가는 법

### 1. 사고 보고서를 시험 관점으로 읽는 순서

1. **결함이 드러나는 입력**을 한 문장으로 적는다. goto fail은 "잘못된 서명", 291은 "21번째 필드의 비와일드카드 기준".
2. 보고서가 든 **시험 층**을 나열하고, 각 층의 입력이 1의 입력을 포함했는지 본다.
3. 포함하지 않았다면 **왜 빠졌나**: 결과가 정상과 같았나(goto fail), 그 경로를 아예 안 지났나(291), 검증기가 다른 기준을 봤나(291).
4. 사실(원문)과 해석을 표에서 칸으로 나눈다. 수치·시각은 원문 그대로 옮긴다.
5. 내 시스템의 같은 모양을 찾는다(아래 점검 목록).

### 2. 내 시스템으로 옮길 점검 목록

| 질문 | 근거 사건 | leaf |
|---|---|---|
| 서명·토큰·권한·입력 검증 코드마다 "거부해야 할 입력" 테스트가 있나? 그 테스트가 수정 전에 빨강이었나? | goto fail | [07](../07-test-design-techniques/2-summary.md) · [05](../05-tdd/2-summary.md) |
| 보안 확인 줄이 커버리지 보고서에서 미실행으로 남아 있지 않나? | goto fail | [16](../16-coverage-and-its-limits/2-summary.md) |
| 컴파일러·린터의 도달 불가 코드 경고가 켜져 있고, 경고가 빌드를 막나? | goto fail | [12](../12-test-smells-and-xunit-patterns/2-summary.md) |
| 설정·콘텐츠·규칙 데이터의 **각 필드**가 "실제로 값을 읽는" 시험 사례를 하나 이상 갖나? | 291 | [07](../07-test-design-techniques/2-summary.md) |
| 검증기와 소비자(인터프리터·파서)가 같은 계약으로 시험되나? 검증기가 정의 문서가 아니라 소비자가 실제로 받는 모양과 대조하나? | 291 | [03](../03-test-doubles/2-summary.md) · [13](../13-contract-testing/2-summary.md) |
| "운영에서 몇 번 잘 돌았다"를 근거로 쓸 때, 그 배포들이 이번 변경의 경로를 실행했나? | 291 | [19](../19-testing-in-production/2-summary.md) |
| 설정·콘텐츠 배포도 단계 배포(카나리·링)를 거치나? | 291 | [reliability/23](../../reliability/23-deployment-strategies/2-summary.md) · [reliability/53](../../reliability/53-reliability-incidents/2-summary.md) |

### 3. 음성 테스트를 표로 — JUnit 5 파라미터화

```java
@ParameterizedTest(name = "{0}은 거부한다")
@MethodSource("forgedInputs")
void 거부해야_하는_입력(String 이름, byte[] params, byte[] sig) {
    assertNotEquals(0, KeyExchangeVerifier.verify(server.getPublic(), params, sig), 이름);
}
static Stream<Arguments> forgedInputs() throws Exception {
    byte[] tampered = PARAMS.clone(); tampered[0] ^= 1;
    return Stream.of(
        Arguments.of("공격자 키 서명", PARAMS, sign(attacker.getPrivate(), PARAMS)),
        Arguments.of("빈 서명", PARAMS, new byte[0]),
        Arguments.of("변조된 파라미터", tampered, sign(server.getPrivate(), PARAMS)));
}
```

- 실험 A-2의 세 음성 테스트를 표로 옮긴 모양이다(이 파라미터화 판 자체는 실행하지 않았다 — 실행한 것은 A-2의 `@Nested` 판이다).
- 거부 목록은 위협에서 출발해 늘린다. NVD 설명의 두 공격 방식이 첫 두 행이다.

## 장애 시나리오와 대처

### 1. 양성 테스트만 있는 검증기 — goto fail형

- **현상**: 서명·토큰 검증이 사실상 꺼져 있는데 CI는 계속 초록이다. 발견은 외부 연구자·공격으로.
- **보이는 형태**: 검증 함수의 테스트가 "올바른 입력 → 성공"뿐이다. 커버리지 보고서에 확인 줄이 미실행으로 남는다(실험 A-3: 5~7·14~16행).
- **원인**: 확인을 건너뛰어도 올바른 입력의 결과는 같다. 양성 테스트는 확인이 실행됐는지 구별할 수 없다.
- **대처**: 거부해야 할 입력 목록을 음성 테스트로 둔다(다른 키·빈 서명·변조). 수정 전에 빨강인지 확인한다. 도달 불가 코드 경고를 빌드 오류로 올린다.

### 2. 시험 데이터가 그 필드를 한 번도 읽지 않음 — 291형

- **현상**: 시험 사례·스트레스 시험·운영 배포 몇 번이 모두 정상이었는데, 새 설정 한 건에 크래시.
- **보이는 형태**: 시험용 설정 데이터의 해당 필드가 전부 와일드카드·기본값·빈 값이다(RCA: 시험 사례 12개 모두 21번째가 와일드카드).
- **원인**: 손으로 고른 대표 사례가 한 동치 클래스에 몰렸다. 그 필드를 읽는 경로가 시험에서 실행되지 않았다.
- **대처**: 필드마다 "실제 값을 읽는" 사례를 하나씩 둔다(RCA 소견 3). 생성기로 필드 값을 무작위로 채우는 속성 테스트·퍼징을 더한다([14](../14-property-based-testing/2-summary.md)).

### 3. 검증기와 소비자가 다른 정의를 믿음

- **현상**: "검증 통과" 데이터가 소비자에서 터진다.
- **보이는 형태**: 검증기는 정의 문서(21개)와, 소비자는 실제 입력(20개)과 맞춰져 있다. 두 숫자를 한 테스트가 함께 보지 않는다.
- **원인**: 검증기가 소비자의 대역 노릇을 했는데, 대역과 실제가 같은 계약으로 시험되지 않았다([03-2](../03-test-doubles/2-summary.md)와 같은 구조).
- **대처**: 검증기를 통과한 표본을 실제 소비자에 넣는 시험을 둔다(RCA 소견 5: 새 Template Instance마다 시험). 정의·생산자·소비자의 개수를 컴파일 시점에 대조한다(소견 1).

### 4. "코드가 아니라 설정이라서" 시험·단계 배포를 건너뜀

- **현상**: 코드 릴리스는 단계 배포·고객 선택(N/N-1/N-2)을 거치는데, 설정·콘텐츠는 전 대상에 바로 간다.
- **보이는 형태**: PIR에 따르면 센서 릴리스는 내부 도그푸딩 → 얼리 어답터 → 정식 배포였고 고객이 버전을 고를 수 있었다. Rapid Response Content는 그렇지 않았다.
- **원인**: 실행 동작을 바꾸는 데이터를 "설정"으로 분류해 다른 시험·배포 경로를 줬다.
- **대처**: 동작을 바꾸는 데이터는 코드와 같은 단계(시험 → 카나리 → 링)를 거친다(RCA 소견 6). 운영 대처는 [reliability/53](../../reliability/53-reliability-incidents/2-summary.md) 장애 5.

### 5. 운영 이력을 시험 증거로 씀

- **현상**: "같은 종류 인스턴스 네 개가 운영에서 잘 돌았다"를 근거로 새 인스턴스를 그대로 내보낸다.
- **보이는 형태**: 앞선 배포들의 입력이 이번 변경의 경로를 지나지 않았다(PIR·RCA: 앞선 IPC 인스턴스는 21번째 필드를 쓰지 않음).
- **원인**: 운영 이력은 **실행된 경로**만 보증한다. 새 입력이 새 경로를 열면 이력은 증거가 아니다.
- **대처**: 변경이 여는 경로(새 필드·새 분기)를 먼저 적고, 그 경로를 실행한 시험이 있는지 확인한다. 없으면 단계 배포의 첫 링이 그 시험 역할을 한다.

## 핵심 문장

- goto fail은 중복된 `goto fail;` 한 줄(631행)이 서명 확인을 건너뛰게 했고, 오류 변수가 0인 채 "서명 일치"로 진행했다. 수정은 그 한 줄 삭제였다.
- 확인을 건너뛰어도 올바른 입력의 결과는 같다. 그래서 검증 코드의 결함은 **거부해야 할 입력**을 넣는 음성 테스트로만 보인다.
- CrowdStrike 채널 파일 291은 정의 21개와 제공 20개의 불일치, 런타임 범위 검사 부재, 21번째 필드에 비와일드카드 기준을 쓴 시험 부재가 겹친 사건이다(RCA 2024-08-06).
- 시험 사례가 모두 와일드카드였기 때문에 그 필드를 읽는 경로는 시험·스트레스 시험·운영의 인스턴스 네 개 어디에서도 실행되지 않았다.
- 검증기도 시험 대상이다. 검증기가 소비자와 다른 기준을 보면 "검증 통과"는 안전의 증거가 아니다.
- 원문 사실과 해석을 나눠 읽는다. 운영 관점의 교훈(단계 배포·되돌림)은 reliability/53이 다룬다.

## 관련 주제·근거

- 선행: [20-test-symptom-index](../20-test-symptom-index/2-summary.md) — 이 두 사건은 20의 "초록인데 운영 장애"(놓침) 칸이다.
- 관련 leaf: [07-test-design-techniques](../07-test-design-techniques/2-summary.md)(동치 분할·음성 입력) · [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md)(미실행 줄) · [03-test-doubles](../03-test-doubles/2-summary.md)·[13-contract-testing](../13-contract-testing/2-summary.md)(계약 불일치) · [14-property-based-testing](../14-property-based-testing/2-summary.md)(무작위 입력·퍼징) · [15-mutation-testing](../15-mutation-testing/2-summary.md)(검증 줄을 지워도 테스트가 알아채나) · [19-testing-in-production](../19-testing-in-production/2-summary.md)(운영 이력과 단계 배포)
- 다른 영역
  - [reliability/53-reliability-incidents](../../reliability/53-reliability-incidents/2-summary.md) — CrowdStrike 운영 관점(영향 규모·복구·단계 배포), [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md)
  - [network/29-tls-handshake](../../network/29-tls-handshake/2-summary.md) — TLS 핸드셰이크와 ServerKeyExchange의 자리
  - 공개키 서명 — security 06 public-key-and-signatures, 24 memory-safety-exploits는 미작성([security 영역 표](../../security/README.md))
  - [software-design/56-design-incidents](../../software-design/56-design-incidents/2-summary.md) — 설계 관점 사건(Therac-25 등)
- 1차 출처
  - Apple, "Apple security updates (2014)" <https://support.apple.com/kb/HT205762> — iOS 7.0.6·iOS 6.1.6·Apple TV 6.0.2(2014-02-21), OS X Mavericks 10.9.2 및 Security Update 2014-001(2014-02-25)
  - Apple, "About the security content of iOS 7.0.6" <https://support.apple.com/en-us/103608> · "About the security content of OS X Mavericks v10.9.2 and Security Update 2014-001" <https://support.apple.com/en-us/103380>
  - NVD, CVE-2014-1266 <https://nvd.nist.gov/vuln/detail/CVE-2014-1266> — 설명·영향 판·CVSS(NVD API 2.0으로 2026-10-03 조회)
  - Apple 공개 소스, `apple-oss-distributions/Security` 태그 `Security-55471`·`Security-55471.14`, `libsecurity_ssl/lib/sslKeyExchange.c` <https://github.com/apple-oss-distributions/Security>
  - Adam Langley, "Apple's SSL/TLS bug", 2014-02-22 <https://www.imperialviolet.org/2014/02/22/applebug.html> — TLS 1.2 비영향, `-Wall`·`-Wunreachable-code`, 시험의 어려움
  - CrowdStrike, "Falcon Content Update Preliminary Post Incident Report"(2024-07-25 1900 UTC 갱신) <https://www.crowdstrike.com/en-us/blog/falcon-content-update-preliminary-post-incident-report/>
  - CrowdStrike, "External Technical Root Cause Analysis — Channel File 291"(2024-08-06) <https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf>
  - JLS SE 21 §14.22 "Unreachable Statements" <https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.22>
- 실험 목록(모두 scratchpad `ts/20/`, 컨테이너 `--network none`·`--cpus=2`, 2026-10-03)
  - 소스 대조: `src/Security-55471.c`·`src/Security-55471.14.c`(GitHub raw에서 받음) → `diff` 출력 `631d630 <         goto fail;`
  - C 컴파일러 확인: `eclipse-temurin:21-jdk`·`maven:3.9-eclipse-temurin-21`·`node:22-bookworm-slim`·`node:22-alpine`·`postgres:17`에서 `command -v gcc cc clang tcc` → 없음. 새 이미지는 받지 않았다.
  - A-1 `exp/java/GotoFail.java` — `javac GotoFail.java`(eclipse-temurin:21-jdk, javac 21.0.12) → `error: unreachable statement`
  - A-2 `exp/jsig/`(pom + `KeyExchangeVerifier`·`KeyExchangeVerifierTest`) — `mvn -o test -DexcludedGroups=negative -DargLine=-Dbuggy=true` / `mvn -o test -DargLine=-Dbuggy=true` / `mvn -o test`(maven:3.9-eclipse-temurin-21, 공용 로컬 저장소 `ts/m2`) → 1/1 통과, 3/4 실패, 4/4 통과
  - A-3 `exp/js/gotofail.mjs`·`gotofail.test.mjs` — `IMPL=buggy|fixed NEG=0|1 node --test`, 커버리지는 `--experimental-test-coverage --test-coverage-include=gotofail.mjs`(node:22-alpine, Node v22.23.2)
  - B `exp/js/cf291.mjs`·`cf291.test.mjs` — `node --test cf291.test.mjs` → 5개 중 3 통과·2 실패
  - 사실 점검 재실행(같은 코드·같은 이미지, `--network none`, 2026-10-03): 소스 diff `631d630`, A-1 `unreachable statement`, A-2 1/1 통과·4개 중 3 실패·4/4 통과, A-3 커버리지 `58.33 | 50.00 | 50.00 | 5-7 14-16 20-28`, B 5개 중 3 통과·2 실패 — 모두 일치
