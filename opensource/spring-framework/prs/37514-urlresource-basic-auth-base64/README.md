# PR #37514 - Use the standard Base64 alphabet for UrlResource Basic auth

## 0. 정향

이 문서는 `spring-core`의 `UrlResource`가 URL에 박힌 자격증명(`http://user:pass@host/...`)으로 `Authorization: Basic` 헤더를 만들 때 **RFC가 요구하는 표준 Base64가 아니라 URL-safe Base64로 인코딩하던** 결함의 해설이다.\
수정은 메서드 이름 한 단어(`getUrlEncoder` -> `getEncoder`)지만, 그 한 단어가 틀려 있을 때 일어나는 일은 "비밀번호가 맞는데 서버가 401을 돌려주는" 인증 실패다.\
그리고 그 실패는 특정 자리에 `~`가 든 비밀번호에서만 일어나므로, 거의 아무도 마주치지 않는다.

> **Base64** — 임의의 바이트를 64개의 글자만으로 적기 위한 인코딩. 3바이트(24비트)를 6비트씩 4조각으로 잘라 각 조각의 값(0~63)을 글자 하나로 바꾼다.\
> 예: `"ali"` 3바이트는 `YWxp` 4글자가 된다.

> **HTTP Basic 인증** — `사용자:비밀번호`를 Base64로 인코딩해 `Authorization: Basic <값>` 헤더에 실어 보내는 가장 단순한 HTTP 인증 방식.\
> 예: `alice:secret`은 `Authorization: Basic YWxpY2U6c2VjcmV0`으로 나간다.

다 읽으면 다음 셋을 설명할 수 있어야 한다.

- "표준 알파벳과 URL-safe 알파벳은 어디가 다르고, 왜 그 차이가 `~` 하나로만 드러나는가"
- "왜 기존 테스트는 이 결함을 잡지 못했는가"
- "이 코드는 어떻게 해서 틀린 인코더를 갖게 됐는가"

상태: **OPEN**(2026-10-19 제출, main 대상, 라벨 `status: waiting-for-triage`).\
CI는 Build Pull Request / DCO / Backport Bot 전부 SUCCESS(2026-10-19 `gh pr view` 확인 기준).

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md) -
[이해 게이트 기록](gates.md).

## 1. 배경 - UrlResource는 클라이언트다

`UrlResource`는 `java.net.URL`을 감싼 `Resource` 구현이다.\
`http:` URL이면 `getInputStream()`을 부를 때 실제로 HTTP 연결을 열어 원격 서버에서 내용을 받아 온다.\
즉 이 클래스가 등장하는 장면에서 **Spring은 서버가 아니라 클라이언트**다.\
이 방향을 놓치면 결함이 "Spring이 잘못 해독한다"로 읽히는데, 실제로는 "Spring이 잘못 적어서 보낸다"이다(이해 게이트에서 가장 오래 걸린 지점이 바로 이 방향이었다 - [gates.md](gates.md)).

URL에 userinfo가 있으면 Spring이 그것을 꺼내 Basic 인증 헤더로 바꿔 실어 준다.\
그 일을 하는 곳이 `customizeConnection` 하나다.

```java
@Override
protected void customizeConnection(URLConnection con) throws IOException {
	super.customizeConnection(con);
	String userInfo = this.url.getUserInfo();        // "http://alice:se~ret@host/" -> "alice:se~ret"
	if (userInfo != null) {
		String encodedCredentials = Base64.getUrlEncoder().encodeToString(userInfo.getBytes());
		con.setRequestProperty(AUTHORIZATION, "Basic " + encodedCredentials);
	}
}
```
(수정 전 UrlResource.java:259-267)

> **userinfo** — URL에서 호스트 앞 `@` 이전에 오는 `사용자:비밀번호` 부분.\
> 예: `http://alice:secret@example.com/a`의 userinfo는 `alice:secret`이다.

누가 무엇을 하는지 세로로 놓으면 이렇다.

```text
  Spring 애플리케이션 (클라이언트)
  new UrlResource("http://alice:se~ret@host/resource")
              |
              v
  customizeConnection
    userInfo = "alice:se~ret"
    getBytes()            -> 바이트 12개          <- 여기는 정상
    Base64 인코더          -> 글자 16개            <- 결함은 여기 (어느 알파벳으로 적나)
    Authorization 헤더에 실음
              |
              v   HTTP 요청
  원격 HTTP 서버
    헤더를 RFC 7617 대로 표준 Base64 디코더로 푼다
    -> 사용자/비밀번호 확인 -> 200 또는 401
```

## 2. 수정 전 동작 - 두 알파벳은 두 글자만 다르다

Base64에는 알파벳이 둘 있다.\
RFC 4648이 §4에 표준 알파벳을, §5에 "URL and Filename Safe" 알파벳을 정의한다.\
URL-safe 알파벳은 URL이나 파일명에서 특수한 의미를 갖는 `+`와 `/`를 피하려고 만든 것이고, 그 둘만 바꿨다.

| 6비트 값 | 0~61 | 62 | 63 | 패딩 |
|---|---|---|---|---|
| RFC 4648 §4 표준 (`Base64.getEncoder()`) | A-Z a-z 0-9 | `+` | `/` | `=` |
| RFC 4648 §5 URL-safe (`Base64.getUrlEncoder()`) | 같음 | `-` | `_` | `=` |

> **알파벳(alphabet)** — Base64에서 6비트 값 0~63을 각각 어떤 글자로 적을지 정한 64칸짜리 표.\
> 예: 표준 표에서는 값 62가 `+`, URL-safe 표에서는 `-`다.

그리고 HTTP Basic 인증의 규격인 RFC 7617 §2 step 4는 어느 표를 쓸지 못 박아 둔다 - "encoding this octet sequence using Base64 ([RFC4648], Section 4)".\
**표준 알파벳**이다.\
그런데 수정 전 코드는 `getUrlEncoder()`, 즉 §5를 쓰고 있었다.

두 표가 0~61에서 같으므로, 인코딩 결과에 값 62나 63인 조각이 하나도 없으면 두 인코더의 출력은 글자 하나까지 같다.\
그래서 대부분의 자격증명에서는 이 결함이 존재하지 않는 것과 같다.

## 3. 문제 - 어떤 비밀번호가 401을 받나

### 발화 조건 - ASCII에서는 3바이트 묶음의 마지막 조각뿐

자격증명이 ASCII라면 값 62/63이 나올 수 있는 자리가 매우 좁다.\
ASCII 바이트는 최상위 비트가 항상 0이기 때문이다.\
3바이트 묶음을 6비트 4조각으로 자를 때 각 조각이 가질 수 있는 최댓값을 계산하면 이렇다.

```text
  바이트:  0aaaaaaa  0bbbbbbb  0ccccccc       (ASCII: 최상위 비트 0)

  조각 1 = 0aaaaa                  최댓값 011111 = 31
  조각 2 = aa 0bbb                 최댓값 110111 = 55
  조각 3 = bbbb 0c                 최댓값 111101 = 61
  조각 4 = cccccc                  최댓값 111111 = 63   <- 62/63 은 여기서만 나온다
```

-> 조각 1~3에는 반드시 어딘가에 0 비트가 끼어 있어 62(`111110`)나 63(`111111`)이 될 수 없다.

조각 4는 셋째 바이트의 하위 6비트 그대로다.\
하위 6비트가 `111110`(62)인 ASCII는 `>`(0x3E)와 `~`(0x7E), `111111`(63)인 것은 `?`(0x3F)와 DEL(0x7F)이다.\
여기서 URL userinfo에 그대로 쓸 수 있는 문자를 거르면 `~` 하나만 남는다.\
`?`는 URL에서 쿼리의 시작이라 userinfo가 거기서 잘리고, DEL과 `>`는 userinfo에 합법인 문자가 아니다(log 기록: raw `>`는 `new URL` 폴백 경로에서만 통과).

> **6비트 조각** — Base64가 글자 하나로 바꾸는 단위. 바이트(8비트)가 아니다.\
> 예: `se~` 3바이트는 6비트 조각 4개 `28 54 21 62`가 된다.

정리하면 **실사용에서 이 결함이 발화하는 조건은 "3바이트 묶음의 셋째 자리에 `~`가 있는 자격증명"** 이고, 그때 표준이면 `+`가 나와야 할 자리에 `-`가 나간다.\
`/`와 `_`의 차이는 합법 ASCII userinfo로는 만들어지지 않는다.

### 실제 예 - `alice:se~ret`

`alice:se~ret`는 3바이트씩 `ali` / `ce:` / `se~` / `ret`로 묶이고, 셋째 묶음의 셋째 자리가 `~`다.

```text
  s = 0x73 = 01110011
  e = 0x65 = 01100101
  ~ = 0x7E = 01111110

  24비트:   011100 110110 010101 111110
  값:         28     54     21     62
  표준:        c      2      V      +     -> "c2V+"
  URL-safe:    c      2      V      -     -> "c2V-"
```

| 자격증명 | 표준(RFC 7617이 요구) | URL-safe(수정 전 실제 송신) |
|---|---|---|
| `alice:secret` | `YWxpY2U6c2VjcmV0` | `YWxpY2U6c2VjcmV0` (같음) |
| `alice:se~ret` | `YWxpY2U6c2V+cmV0` | `YWxpY2U6c2V-cmV0` |

`~`의 위치가 한 칸만 달라도 이 일은 일어나지 않는다.\
`alice:s~cret`라면 `~`의 비트가 이웃 바이트와 섞여 62가 되지 않는다.

### 증상 - 맞는 비밀번호로 401

서버는 RFC대로 표준 디코더로 헤더를 푼다.\
`-`는 표준 알파벳에 없는 글자이므로, 디코더가 거부하거나 다른 바이트로 읽는다.\
어느 쪽이든 결과는 같다 - **비밀번호가 맞는데 인증이 실패한다.**

> **401 Unauthorized** — 요청에 유효한 인증 정보가 없다는 HTTP 응답 코드.\
> 예: 서버가 헤더를 풀었더니 비밀번호가 다르게 나오면 401을 돌려준다.

이 실패는 무음은 아니지만 **오도한다.**\
사용자는 401을 보고 비밀번호를 의심하지, 클라이언트 라이브러리의 Base64 알파벳을 의심하지 않는다.

### 왜 아무도 못 봤나

1. **발화 조건이 좁다.**\
   `~`가 들어간 비밀번호여야 하고, 그 `~`가 3바이트 묶음의 셋째 자리여야 한다.\
   확률로 치면 `~`가 든 비밀번호의 일부에서만 일어난다.
2. **기존 테스트의 자격증명이 `alice:secret`이다.**\
   이 자격증명에는 값 62/63인 조각이 하나도 없어서 두 알파벳의 결과가 같다.\
   테스트는 결함 경로를 통과하지만 결함을 볼 수 없는 입력을 쓰고 있었다([tests.md](tests.md)).

### 기원 - 이관 과정에서 짝을 잘못 고른 메서드

이 기능은 gh-1822로 들어왔다.

| 커밋 | 내용 | 인코더 |
|---|---|---|
| `ac9ca412c8e` (Denis Kostin 작성 2018-05-08, 2023-08-22 커밋) | `getInputStream()` 안에서 userinfo로 헤더 생성 | `Base64Utils.encodeToString` -> 내부적으로 `Base64.getEncoder()` (표준) |
| `f95a1f49dfe` (Stephane Nicoll, 2023-08-22, "Polish") | 헤더 생성을 `customizeConnection` 오버라이드로 이동, `Base64Utils` 제거 | `Base64.getUrlEncoder()` (URL-safe) |

`Base64Utils`는 6.0.5에서 deprecated됐고(`5448e810215`, "Deprecate Base64Utils in favor of Java's Base64"), polish가 그것을 JDK `java.util.Base64`로 옮기면서 메서드를 골랐다.\
그런데 polish 직전의 `Base64Utils`에는 짝이 둘 있었다.

```java
public static String encodeToString(byte[] src) {          // 원본이 쓰던 것
	...
	return Base64.getEncoder().encodeToString(src);
}

public static String encodeToUrlSafeString(byte[] src) {   // URL-safe 는 이쪽
	return Base64.getUrlEncoder().encodeToString(src);
}
```
(`f95a1f49dfe^`의 Base64Utils.java)

원본이 쓴 `encodeToString`의 대응은 `getEncoder()`인데 polish는 `encodeToUrlSafeString`의 대응인 `getUrlEncoder()`를 골랐다.\
커밋 메시지는 "Polish"뿐이고 URL-safe를 의도했다는 언급이 없다.\
**라이브러리가 바뀌어서 동작이 달라진 것이 아니라, 옮기는 사람이 짝을 잘못 고른 이관 실수다.**\
(이해 게이트 중 사용자가 정확히 이것 - "라이브러리 자체가 바뀌여서 그런거지?" - 를 물었고, 그 답으로 이 대조를 확인했다.)

덧붙여 같은 polish 커밋이 추가한 테스트 `useUserInfoToSetBasicAuth`는 헤더를 `Base64.getDecoder()`, 즉 **표준 디코더**로 풀어 검사한다.\
테스트를 쓴 사람은 표준 알파벳을 가정하고 있었던 셈이고, 그 가정이 깨지지 않는 입력(`alice:secret`)을 골랐기 때문에 테스트가 어긋남을 드러내지 못했다.

두 커밋이 같은 날 26분 간격으로 커밋됐으므로, 표준 인코더 버전이 단독으로 릴리스된 적은 없을 것으로 보인다(릴리스 태그로는 확인하지 않음).\
그래서 이 PR은 "깨진 것을 되돌리는" 성격과 동시에 "처음부터 의도했던 동작을 처음으로 실현하는" 성격을 갖는다.

## 4. 수정 해설 - 한 단어

```java
@Override
protected void customizeConnection(URLConnection con) throws IOException {
	super.customizeConnection(con);
	String userInfo = this.url.getUserInfo();
	if (userInfo != null) {
		String encodedCredentials = Base64.getEncoder().encodeToString(userInfo.getBytes());
		con.setRequestProperty(AUTHORIZATION, "Basic " + encodedCredentials);
	}
}
```
(UrlResource.java:259-267)

같은 입력을 수정 전후에 넣어 보면 이렇다.

```text
       수정 전                               수정 후
+------------------------------+     +------------------------------+
| "alice:se~ret"               |     | "alice:se~ret"               |
| getBytes() -> 12 바이트      |     | getBytes() -> 12 바이트      |
| getUrlEncoder (RFC 4648 §5)  |     | getEncoder (RFC 4648 §4)     |
|   값 62 -> '-'               |     |   값 62 -> '+'               |
| Basic YWxpY2U6c2V-cmV0       |     | Basic YWxpY2U6c2V+cmV0       |
+------------------------------+     +------------------------------+
  서버 표준 디코더: 거부/오해석         서버 표준 디코더: alice:se~ret
  -> 401                               -> 인증 성공
```

**바뀌는 것은 값 62/63 조각의 글자뿐이다.**\
0~61의 글자와 패딩 규칙이 두 인코더에서 같으므로, `alice:secret`처럼 62/63 조각이 없는 자격증명은 수정 전후 헤더가 바이트까지 같다.\
기존 사용자 중 이 수정으로 동작이 바뀌는 사람은 지금까지 401을 받던 사람뿐이다.

**한 줄로 모든 접속 경로가 고쳐진다.**\
`customizeConnection`은 `getInputStream()`뿐 아니라 `AbstractFileResolvingResource`의 `exists()` / `isReadable()` / `contentLength()` / `lastModified()`가 HEAD 요청을 열 때와 그 405 폴백까지 8곳에서 호출된다.\
헤더를 만드는 곳이 이 메서드 하나이므로 수정 지점도 하나다([structure.md](structure.md) 1절).

**프레임워크 안에 이미 정답이 있었다.**\
spring-web의 `HttpHeaders.encodeBasicAuth`는 `Base64.getEncoder()`를 쓴다(HttpHeaders.java:2202).\
Basic 인증 값을 URL-safe로 만드는 곳은 프레임워크 안에서 `UrlResource` 하나였다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다.

> **red(레드)** — 고치기 전에 새 테스트를 돌려 일부러 실패를 확인하는 단계.\
> 예: 여기서 실패하지 않으면 그 테스트는 이 결함을 겨냥하지 못한 것이다.

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 새 테스트 `useStandardBase64AlphabetForBasicAuth` | red - `expected "Basic YWxpY2U6c2V+cmV0" but was "Basic YWxpY2U6c2V-cmV0"` | green |
| `ResourceTests` | 69건 중 신규 1건만 실패 | `UrlResourceTests` 15/15 |
| `spring-core` 전체 | - | **5,328 tests, 0 failures, 0 errors** |
| checkstyleMain / checkstyleTest | - | 통과 |
| blind 테스트 워커(diff 미열람) | - | **45/45 PASS** (GET 3경로 + HEAD 4경로 x 자격증명 5종 + userinfo 없음) |

stakes는 **높음**으로 판정했다.\
변경은 한 줄이고 복구도 쉽지만, 대상이 인증 자격증명 헤더 경로(보안·권한)라 표의 하한을 그대로 따랐다.\
그래서 리뷰는 **듀얼 리뷰 루프**(Opus 워커와 codex 병렬, 그 뒤 codex 종합 감사)에 blind 테스트 워커를 더했다.\
설계 선검증은 생략했는데, 새로 만드는 동작 불변식이 없고 기존 RFC 계약을 복원하는 것이기 때문이다.

> **blind 테스트 워커** — 구현 diff를 보지 않고 명세서만 읽고 테스트를 설계·실행하는 독립 검증자.\
> 예: 구현을 본 사람은 구현이 하는 일을 테스트하게 되므로, 일부러 명세만 주고 "무엇이 맞아야 하는가"에서 출발하게 한다.

## 6. 리뷰 - 지적 0건, 그러나 결과가 비어 있지는 않았다

#37268처럼 리뷰가 결함 모델을 뒤집는 일은 이번에는 없었다.\
**양측 모두 코드 finding 0건**이었고, 루프 1회로 clean 종결됐다.\
그래도 리뷰가 남긴 것이 넷 있다.

**(1) 발주.**\
base `49adc91c7e4`..`d40f67bb08f`의 diff와 spec을 담은 읽기 전용 미러를 만들어 Opus 워커와 codex를 병렬로 돌리고, 동시에 blind 테스트 워커를 띄웠다.\
보안 스캔은 0건이었다.

**(2) Opus - finding 0, 열린 질문 둘.**

- **OQ1(HEAD 경로 미테스트)**: 새 테스트는 GET(`getInputStream`)만 확인한다.\
  HEAD 경로 8곳은 같은 오버라이드를 동적 디스패치로 거치므로 따로 테스트할 필요는 없다고 봤고, spec §5도 grep을 요구했지 테스트를 요구하지 않았다.\
  조치 없이 종결 - 그리고 이 빈칸은 blind 워커가 실행으로 메웠다.
- **OQ2(charset)**: 프로덕션은 `getBytes()`로 플랫폼 기본 charset을 쓰고 기존 테스트는 ISO-8859-1로 디코드한다.\
  ASCII에서는 같고 charset은 spec §4가 범위에서 뺐으므로 종결.

Opus는 테스트 기대값도 손으로 다시 계산했다 - `se~` = `0x73 0x65 0x7E` -> `011100 110110 010101 111110` -> `c 2 V +`.

**(3) codex - finding 0, 열린 질문 하나.**\
OQ3은 "실행 결과가 packet에 없어 확인하지 못했다"였고, 메인이 가진 실행 증거(수정 전 FAIL, 후 15/15, 5,328/0, checkstyle)로 해소했다.

**(4) codex 종합 감사 - A1.**\
blind 테스트 결과가 아직 pending인데 종결할 수 없다는 절차 지적이었다.\
수용해 blind 결과를 회수한 뒤 종결했다.

blind 워커가 돌려준 것은 통과 숫자만이 아니었다.

| blind 워커 보고 | 무엇을 바꿨나 |
|---|---|
| 45/45 PASS, 7경로 x 자격증명 5종 + userinfo 없음 5/5 | OQ1의 HEAD 경로 빈칸을 실행으로 덮음 |
| spec §5 예시 `admin:p?ss~~`는 `?` 때문에 URL에 못 넣음 - `getUserInfo()`가 `admin:p`만 돌려준다 | spec 문구 정정(docs). 실제 테스트는 이미 `alice:se~ret`로 바꿔 둔 상태였다 |
| ASCII로는 `/`를 만들 수 없어 `/` 케이스는 UTF-8 비ASCII(`user:~aÿ`)로 구성 | 3절의 "`/` 차이는 합법 ASCII로 불가"를 독립적으로 재확인 |

마지막 둘은 메인이 착수 직후 스모크로 이미 알아낸 사실과 일치했다.\
명세 초안을 쓸 때 고른 예시 자격증명 `admin:p?ss~~`가 URL 파서를 통과하지 못한다는 것을, 구현 쪽에서도 명세만 본 쪽에서도 각각 발견한 것이다.

> **반증 질문** — "이 결론이 틀렸다면 어디서 드러나는가"를 일부러 묻는 검증 습관.\
> 예: "다른 호출 경로도 이 메서드를 거치는가"를 grep과 HEAD 실행으로 확인했다.

## 7. 교훈

1. **재현 입력은 실제 진입 API를 통과하는지까지 확인한다.**\
   착수 전 조사에서 쓴 예시 `admin:p?ss~~`는 Base64 차이를 만들기는 했지만, `?` 때문에 URL에 넣는 순간 userinfo가 잘려 결함 경로에 도달하지 못한다.\
   인코더만 따로 떼어 실험하면 맞아 보이는 입력이, 실제로 사용자가 들어오는 문(URL 파서)에서는 걸러진다.
2. **"공유되는 입력"으로 쓴 테스트는 두 구현을 구분하지 못한다.**\
   `alice:secret`은 표준과 URL-safe가 같은 출력을 내는 입력이라, 그 테스트는 처음부터 이 결함에 대해 검출력 0이었다.\
   테스트 입력을 고를 때는 "올바른 구현과 그럴듯한 틀린 구현이 다른 답을 내는가"를 물어야 한다.
3. **이관(migration) polish는 동작 변경이 숨기 좋은 자리다.**\
   deprecated API를 JDK 대응물로 바꾸는 일은 기계적으로 보이지만, 짝이 둘 이상인 API에서는 고르는 순간 의미가 갈린다.\
   이번 기원은 그 선택 하나였고, 커밋 메시지 "Polish"는 리뷰어에게 동작 변경을 의심할 이유를 주지 않았다.
4. **비트 단위로 내려가면 발화 조건이 닫힌다.**\
   "62/63이 나오면 다르다"에서 멈추면 "어떤 비밀번호든 가끔"으로 들린다.\
   ASCII의 최상위 비트 0을 넣어 조각별 최댓값을 계산하면 "셋째 자리의 `~` 하나"로 좁혀지고, 그 좁힘이 그대로 테스트 자격증명 선택과 영향 범위 서술의 근거가 됐다.

## 출처

작업 폴더: spring-framework-fork `docs/plans/2026-10-18/io2-urlresource-basic-auth-base64/`(requirement-spec.md, log.md, pr-body.md).\
코드 기준: 커밋 `d40f67bb08f`(base upstream/main `49adc91c7e4`). 기원은 `ac9ca412c8e`, `f95a1f49dfe`를 `git show`로 확인.\
PR: https://github.com/spring-projects/spring-framework/pull/37514 (상태는 2026-10-19 확인 값).
