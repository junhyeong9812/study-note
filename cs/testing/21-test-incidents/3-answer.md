# testing/21-test-incidents — 정답

## 정답

### 1. goto fail의 위치·diff·수정 날짜

- 위치: Apple 공개 소스 `Security` 저장소 `libsecurity_ssl/lib/sslKeyExchange.c`의 `SSLVerifySignedServerKeyExchange`. 서명할 데이터의 SHA-1 해시를 갱신하는 `if` 뒤에 `goto fail;`이 한 번 더 들어갔다.
- diff: 태그 `Security-55471`(수정 전)과 `Security-55471.14`(수정 후)의 같은 파일을 비교하면 한 줄 삭제뿐이다.

```text
631d630
<         goto fail;
```

- 수정판 배포(Apple 2014 보안 업데이트 목록): iOS 7.0.6·iOS 6.1.6·Apple TV 6.0.2가 2014-02-21, OS X Mavericks 10.9.2 및 Security Update 2014-001이 2014-02-25.
- NVD 영향 범위: iOS 6.x(6.1.6 전)·7.x(7.0.6 전), Apple TV 6.x(6.0.2 전), OS X 10.9.x(10.9.2 전).

### 2. 왜 "성공"이 되었나 · TLS 1.2

- 함수는 오류 코드를 `err`에 담고, 실패하면 `fail:` 레이블로 모아 `return err;`한다.
- 631행 직전의 `SSLHashSHA1.update(&hashCtx, &signedParams)`가 성공하면 `err = 0`이다. 이어서 조건 없는 `goto fail;`이 실행된다.
- 그래서 `SSLHashSHA1.final`과 `sslRawVerify`(실제 서명 확인)를 건너뛰고 `err = 0`을 돌려준다.
- 호출자(845~848행)는 `if(err) goto fail;`만 확인하고 `/* Signature matches; ... */`로 진행한다. 0 = 서명 일치로 읽는다.
- TLS 1.2: 같은 파일에 `SSLVerifySignedServerKeyExchangeTls12`가 따로 있고, 호출자는 `sslVersionIsLikeTls12(ctx)`이면 그 함수를 부른다(836~843행). Langley 원문: "this doesn't affect TLS 1.2 because there's a different function for verifying the different ServerKeyExchange message in TLS 1.2." 같은 글은 바로 이어서 "the attacker can choose any version that the client will accept"라고 적고, 클라이언트가 TLS 1.2만 켠 경우에는 우회될 것으로 보인다("it appears that would workaround this issue")고 덧붙였다.

### 3. 양성만 vs 음성 포함 (실험 A-2)

- (가) 양성 테스트만: `Tests run: 1, Failures: 0` — `BUILD SUCCESS`. 확인을 건너뛰어도 올바른 서명의 결과(0)는 같다.
- (나) 음성 3개 포함: `Tests run: 4, Failures: 3`.
  - `공격자 키 서명 ==> expected: not equal but was: <0>`
  - `빈 서명 ==> expected: not equal but was: <0>`
  - `변조된 파라미터 ==> expected: not equal but was: <0>`
- 메시지의 뜻: 거부해야 할 입력 세 종류를 모두 0(성공)으로 받았다 — 서명 확인이 아예 돌지 않았다는 강한 단서다.
- 수정판에서는 4개 모두 통과했다. 음성 테스트가 수정 전 빨강 → 수정 후 초록으로 결함을 가리켰다.
- 환경: maven:3.9-eclipse-temurin-21(Maven 3.9.16 · JDK 21.0.11) · JUnit 5.13.4 · surefire 3.5.3.

### 4. Java와 C의 반응 차이

- Java(실험 A-1, javac 21.0.12): `GotoFail.java:13: error: unreachable statement`. JLS 14.22가 도달할 수 없는 문장을 컴파일 오류로 정하기 때문에 이 모양은 빌드되지 않는다.
- C(Langley 원문): 같은 모양의 축약 코드를 `-Wall`로 컴파일했을 때 GCC 4.8.2·Clang 3.3 모두 경고가 없었다. Clang에 `-Wunreachable-code`가 있지만 `-Wall`에 들어 있지 않다.
- 의미
  - 같은 실수가 언어·컴파일러 옵션에 따라 작성 시점의 오류가 되기도, 아무 신호 없는 실행 파일이 되기도 한다.
  - 그래도 컴파일러는 일부만 막는다. Java에서도 조건이 붙은 탈출(`if (조건) break fail;`)은 도달 가능해서 통과한다(A-2가 그 모양).
  - 그래서 도구 경고를 켜는 것과 별개로, 검증 코드에는 음성 테스트가 필요하다. 커버리지 보고서의 미실행 확인 줄도 보조 신호다(A-3: `uncovered lines 5-7 14-16 …`).

### 5. 채널 파일 291의 불일치와 세 요소

- 불일치: Template Type Definitions 파일은 IPC Template Type의 입력을 **21개**로 정의했고, Content Interpreter를 부르는 센서 통합 코드는 **20개**만 넘겼다(RCA 원문: "defined 21 input parameter fields, but the integration code … supplied only 20 input values").
- 2024-07-19 04:09 UTC 배포된 Template Instance 하나가 21번째 필드에 처음으로 비와일드카드 기준을 넣었다. 인터프리터가 21번째(인덱스 0x14)를 읽다가 배열 끝 너머를 읽어 크래시했다.
- RCA 요약 문단의 세 요소(원문): "the mismatch between the 21 inputs validated by the Content Validator versus the 20 provided to the Content Interpreter, the latent out-of-bounds read issue in the Content Interpreter, and the lack of a specific test for non-wildcard matching criteria in the 21st field".

### 6. 여러 층을 통과한 이유 — 동치 분할

- 각 필드의 기준은 두 클래스로 나뉜다: 와일드카드(입력을 읽지 않음)와 비와일드카드(입력을 읽음).
- RCA 소견 3: 자동 시험의 정적 시험 사례 12개는 채널 파일 데이터를 손으로 골랐고, **모든 Template Instance의 21번째 필드가 와일드카드**였다. 21번째 필드의 비와일드카드 클래스가 비어 있었다.
- 스트레스 시험(3월 5일)은 시험용 Template Instance로 했고, 불일치가 크래시로 이어진다는 것을 드러내지 않았다(소견 5).
- 3~4월 운영에 나간 인스턴스 네 개(3월 5일 1개, 4월 8~24일 3개 — PIR)도 21번째 필드를 쓰지 않았다(RCA: "no IPC Template Instances in previous channel versions had made use of the 21st input parameter field").
- 즉 21번째 필드를 **읽는** 경로는 어느 층에서도 실행되지 않았다.
- 실험 B에서 이것을 잡은 시험: "RCA 완화책 3: 필드마다 비와일드카드 기준으로 시험" — `Got unwanted exception: field 21`, 원인 `TypeError: Cannot read properties of undefined (reading 'buf')`. 와일드카드만 쓴 "기존 시험" 12개는 초록이었다.

### 7. 검증기 = 소비자의 대역

- Content Validator는 실제 소비자(Content Interpreter + 통합 코드)를 대신해 "이 콘텐츠는 처리 가능하다"고 판정하는 **대역** 역할이었다.
- 대역은 정의 파일(21개)을 기준으로 판정했고, 실제 소비자는 입력 20개를 받았다. 대역과 실제 구현이 **같은 계약으로 시험되지 않은** 상태다 — stub이 실제 저장소와 다른 계약을 흉내 낸 03-2, 소비자의 기대와 제공자의 실제 응답이 어긋나는 13-1과 같은 구조다.
- 이 구조를 직접 겨냥한 RCA 조치
  - 소견 4: 검증기에 "Template Instance가 인터프리터에 실제로 제공되는 입력보다 많은 필드를 매칭하지 않는지" 검사 추가(2024-08-19까지 예정). 그 전까지 21번째 필드는 와일드카드만 허용.
  - 소견 1: 센서 컴파일 시점에 Template Type이 제공하는 입력 수 검사(7-19 개발, 7-27 운영) — 정의와 생산자를 대조.
  - (보조) 소견 5: 새 Template Instance마다 시험 — 검증기 통과 표본을 실제 소비 경로로 확인.

### 8. 사실과 해석 · 운영 관점의 자리

| 사실(원문) | 해석(이 노트) |
|---|---|
| iOS 7.0.6은 2014-02-21, OS X 10.9.2는 2014-02-25(Apple 목록). Langley 분석은 2014-02-22 | OS X 사용자는 원인이 공개된 뒤 며칠 동안 수정판 없이 있었다 |
| 수정은 631행 한 줄 삭제(diff) | 양성 테스트는 이 결함을 구별할 수 없다(실험 A-2로 모형 확인) |
| RCA: 시험 사례 12개 모두 21번째 필드가 와일드카드 | 21번째 필드의 비와일드카드 동치 클래스가 비어 있었다 |
| RCA: 콘텐츠는 "configuration data; it is not code" | 코드가 아니라는 분류 때문에 코드와 다른 시험·배포 경로를 탔다 |

- 해석은 원문이 직접 말하지 않는 추론이다. 날짜 차이에서 "며칠 공백"은 계산이고, 그 사이 실제 피해가 있었는지는 원문에 없다.
- CrowdStrike의 영향 규모(Microsoft 추정 기기 수)·되돌림과 복구·단계 배포는 운영(신뢰성) 주제다. 커리큘럼이 운영 관점을 reliability/53에 두고, 이 노트는 시험·검증 관점(어떤 시험 입력이 경로를 지나지 않았나)만 다루도록 나눴다. 같은 사실을 두 곳에 길게 쓰면 한쪽만 고쳐질 때 모순이 생긴다.
