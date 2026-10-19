# PR #37514 - 테스트 해설 (테스트 하나하나)

배치 전체를 먼저 본다.\
이 결함은 **인코딩 결과에 값 62/63 조각이 생기는 자격증명에서만** 드러난다.\
그래서 새 테스트 하나가 "두 알파벳이 갈리는 입력"을 맡고, 기존 테스트 하나가 "두 알파벳이 같은 입력의 동작은 그대로인가"를 맡는 구도가 된다.\
두 축으로 줄 세우면 이렇다.

> **red 테스트 / 가드 테스트** — red는 수정 전에 반드시 실패해야 하는 테스트, 가드는 수정 전후 모두 통과해야 하는 테스트.\
> 예: red 가 없으면 결함을 겨냥하지 못한 것이고, 가드가 깨지면 기존 동작을 망가뜨린 것이다.

| | 두 알파벳 결과가 같은 입력 | 두 알파벳 결과가 다른 입력 |
|---|---|---|
| 디코드 후 원문 비교 | T1 `useUserInfoToSetBasicAuth` (`alice:secret`) - 가드 | - |
| 헤더 정확 문자열 비교 | - | **T2 `useStandardBase64AlphabetForBasicAuth` (`alice:se~ret`) - red** |

같은 배치를 fix 전후 결과까지 넣은 격자로 보면 각 칸이 무엇을 덮는지가 드러난다.

```text
                                  |  fix 전  |  fix 후  |  덮는 것
----------------------------------+----------+----------+--------------------------
T2 alice:se~ret  (정확 문자열)    |  FAIL    |  PASS    |  수정이 결함을 고쳤나
   "...c2V-cmV0" != "...c2V+cmV0" |          |          |
----------------------------------+----------+----------+--------------------------
T1 alice:secret  (디코드 비교)    |  PASS    |  PASS    |  62/63 없는 자격증명의
                                  |          |          |  헤더가 그대로인가
```

-> 오른쪽 위 칸이 비어 있었던 것이 이 결함이 살아남은 이유다. 기존 테스트는 처음부터 왼쪽 칸 하나뿐이었다.

## T2. `useStandardBase64AlphabetForBasicAuth` - red

새로 추가한 유일한 테스트다.\
전문은 이렇다.

```java
@Test
void useStandardBase64AlphabetForBasicAuth() throws Exception {
	startServer(true);
	// "alice:se~ret" encodes to "+" with the standard alphabet but to "-" with the URL-safe one
	UrlResource resource = new UrlResource(
			"http://alice:se~ret@localhost:" + this.server.getPort() + "/resource");
	assertThat(resource.getInputStream()).hasContent("Spring");
	RecordedRequest request = this.server.takeRequest();
	assertThat(request.getHeaders().get("Authorization")).isEqualTo("Basic YWxpY2U6c2V+cmV0");
}
```
(ResourceTests.java:515-524)

이 테스트가 주장하는 것과 수정 전에 red가 되는 이유를 먼저 두 줄로 적어 둔다.

- **주장**: `UrlResource`가 실제로 네트워크에 내보낸 `Authorization` 헤더가 RFC 7617이 요구하는 표준 Base64 문자열과 글자 하나까지 같다.
- **fix 전 red인 이유**: `alice:se~ret`의 셋째 묶음 `se~`가 값 62 조각을 만들고, URL-safe 인코더는 그것을 `-`로 적는다.\
  실측 red는 `expected: "Basic YWxpY2U6c2V+cmV0" but was: "Basic YWxpY2U6c2V-cmV0"`(ResourceTests.java:523).

테스트가 세 국면으로 나뉜다는 것을 먼저 보면 이후 설명이 붙을 자리가 생긴다.

```text
  [1] 가짜 서버 기동
      startServer(true) -> MockWebServer, /resource 에 "Spring" 응답
              |
              v
  [2] 실제 요청
      new UrlResource("http://alice:se~ret@localhost:port/resource")
      getInputStream() -> customizeConnection 이 헤더를 붙이고 GET 송신
      hasContent("Spring") 으로 요청이 정말 끝났는지 확인
              |
              v
  [3] 서버가 받은 것을 꺼내 단언
      server.takeRequest() -> Authorization 헤더 == "Basic YWxpY2U6c2V+cmV0"
```

### 왜 하필 `alice:se~ret`인가

자격증명 선택이 이 테스트의 절반이다.\
[README 3절](README.md)의 계산대로 ASCII 입력에서 값 62/63은 3바이트 묶음의 넷째 조각, 즉 셋째 바이트의 하위 6비트에서만 나오고, URL userinfo에 합법인 문자 중 그 값을 만드는 것은 `~`(하위 6비트 `111110` = 62)뿐이다.\
그래서 `~`를 묶음의 셋째 자리에 놓아야 한다.

```text
  a l i | c e : | s e ~ | r e t
  -----   -----   -----   -----
  묶음1   묶음2   묶음3   묶음4
                      ^
                      셋째 자리 -> 넷째 조각 = 62
```

기존 자격증명 `alice:secret`에서 `c`가 있던 자리(아홉째 글자)에 `~`를 넣은 것이다.\
기존 테스트와 한 글자만 다르므로 "무엇이 차이를 만드는가"가 읽는 사람에게 바로 보인다.

반대로 착수 전 조사에서 쓴 예시 `admin:p?ss~~`는 쓸 수 없었다.\
`?`가 URL의 쿼리 시작이라 `URL.getUserInfo()`가 `admin:p`까지만 돌려주고, 비밀번호 나머지가 잘려 나간다.\
인코더를 단독으로 실험할 때는 표준 `YWRtaW46cD9zc35+` / URL-safe `YWRtaW46cD9zc35-`로 차이가 났지만, 실제 진입점인 URL 파서를 통과하지 못하는 입력이었다.

> **진입 API** — 사용자가 실제로 값을 넣는 문. 이 결함에서는 `new UrlResource(String)`과 그 뒤의 URL 파서다.\
> 예: 인코더에 직접 넣으면 되는 입력도, URL 문자열로 넣으면 파서가 먼저 잘라 낼 수 있다.

### 왜 정확 문자열 비교인가

명세에서 단언 방식을 두 안으로 놓고 골랐다(TO-2).

| 안 | 방식 | fix 전에 어떻게 실패하나 |
|---|---|---|
| **A (채택)** | 헤더 전체를 `"Basic YWxpY2U6c2V+cmV0"`와 `isEqualTo` | 기대값과 실제값 문자열이 그대로 실패 메시지에 찍힌다 |
| B | 기존처럼 `Base64.getDecoder()`로 디코드 후 원문 비교 | `-`가 표준 알파벳에 없어 `IllegalArgumentException`(spec TO-2 기록) |

B도 red는 되지만, 실패가 "디코더가 예외를 던졌다"로 나타나 무엇이 틀렸는지를 한 번 더 해석해야 한다.\
A는 알파벳(`+`)과 패딩 유무까지 문자열 자체로 고정하고, 실패 메시지에 `c2V-` 대 `c2V+`가 나란히 찍힌다.

### 무엇을 검사하는가 - Spring 내부 값이 아니라 네트워크로 나간 헤더

`this.server.takeRequest()`는 MockWebServer가 **실제로 받은** 요청을 꺼낸다.\
그래서 이 테스트는 `customizeConnection` 안의 지역 변수가 아니라 소켓을 건너간 헤더를 본다.\
`hasContent("Spring")` 단언은 요청이 서버에 도달해 응답까지 끝났다는 것을 먼저 확인해, `takeRequest()`가 꺼낼 요청이 있음을 보장한다.

> **MockWebServer** — 테스트 안에서 진짜 HTTP 서버를 띄워 요청을 기록하고 정해 둔 응답을 돌려주는 도구(OkHttp 제공).\
> 예: `takeRequest()`로 서버가 받은 메서드·헤더를 꺼내 단언할 수 있다.

## T1. `useUserInfoToSetBasicAuth` - 무회귀 가드 (전후 green)

2023년 polish 커밋 `f95a1f49dfe`가 함께 추가한 기존 테스트다.

```java
@Test
void useUserInfoToSetBasicAuth() throws Exception {
	startServer(true);
	UrlResource resource = new UrlResource(
			"http://alice:secret@localhost:" + this.server.getPort() + "/resource");
	assertThat(resource.getInputStream()).hasContent("Spring");
	RecordedRequest request = this.server.takeRequest();
	String authorization = request.getHeaders().get("Authorization");
	assertThat(authorization).isNotNull().startsWith("Basic ");
	assertThat(new String(Base64.getDecoder().decode(authorization.substring(6)),
			StandardCharsets.ISO_8859_1)).isEqualTo("alice:secret");
}
```
(ResourceTests.java:503-513)

이 테스트가 결함을 못 잡은 이유와 지금 맡는 역할은 같은 사실의 두 면이다.

- **못 잡은 이유**: `alice:secret`은 표준과 URL-safe가 모두 `YWxpY2U6c2VjcmV0`을 낸다.\
  값 62/63 조각이 하나도 없기 때문이다.\
  흥미로운 점은 이 테스트가 표준 디코더(`getDecoder()`)로 푼다는 것 - 쓴 사람은 표준 알파벳을 가정했지만, 그 가정을 시험하지 않는 입력을 골랐다.
- **지금 맡는 역할**: 수정 후에도 같은 자격증명의 헤더가 바뀌지 않았음을 고정한다(spec §2 보존 항목 "표준/URL-safe 결과가 같은 자격증명의 헤더는 바이트 동일").\
  TO-1에서 기존 테스트의 자격증명을 바꾸는 안(B) 대신 새 테스트를 추가하는 안(A)을 고른 이유가 이 역할을 남기기 위해서다.

## 실측 요약

| 시점 | 대상 | 결과 |
|---|---|---|
| fix 전 | `ResourceTests` | 69건 중 신규 1건만 FAIL (`...c2V-cmV0`) - 가정 2(MockWebServer로 실제 전송 헤더 관측) 성립 |
| fix 후 | `ResourceTests` | BUILD SUCCESSFUL, `UrlResourceTests` 15/15 |
| fix 후 | `spring-core` 전체 + checkstyleMain/Test | **5,328 tests, 0 failures, 0 errors** |
| fix 후 | test 소스 확인 | URL-safe 결과에 의존하는 단언 없음 |

- **diff 규모**: 2파일, 프로덕션 1줄 + 테스트 메서드 1개(+11줄).

## 커밋에 남기지 않은 실행 프로브

커밋한 테스트는 GET 한 경로, 자격증명 한 종류다.\
나머지 경로와 입력은 blind 테스트 워커가 별도 프로그램으로 확인했다(원본: 세션 scratchpad `blind/BlindBasicAuthTest.java`).

> **프로브(probe)** — 커밋하지 않고 한 번 돌려 사실만 확인하고 버리는 임시 실행 코드.\
> 예: JDK `HttpServer`를 띄워 `exists()`가 보내는 HEAD 요청의 헤더를 찍어 보는 작은 `main` 하나.

워커는 구현 diff와 `ResourceTests`를 열지 않고 spec §1·§2·§3·§5만 읽었다.\
repo 빌드 클래스(`spring-core/build/classes/java/main/`)가 로드됐음을 출력으로 증명한 뒤, `new UrlResource("http://<userInfo>@127.0.0.1:<port>/res")`로만 리소스를 만들어 세 가지를 단언했다 - 요청이 서버에 도달했다, 기록된 모든 요청의 헤더가 기대값과 정확히 같다, 기대한 HTTP 메서드가 관측됐다.

| userInfo | 기대 헤더(표준) | URL-safe였다면 | 7경로 결과 |
|---|---|---|---|
| `admin:p~~ss` | `Basic YWRtaW46cH5+c3M=` | `...cH5-c3M=` | 7/7 PASS |
| `user:~aÿ` (UTF-8, `+`와 `/` 모두) | `Basic dXNlcjp+YcO/` | `...p-YcO_` | 7/7 PASS |
| `test:~~~~` (패딩 없음, `+` 둘) | `Basic dGVzdDp+fn5+` | `...p-fn5-` | 7/7 PASS |
| `alice:secret` (두 알파벳 동일) | `Basic YWxpY2U6c2VjcmV0` | 같음 | 7/7 PASS |
| `admin:s3cr3t%3F` (퍼센트 인코딩 원문 유지) | `Basic YWRtaW46czNjcjN0JTNG` | 같음 | 7/7 PASS |
| userinfo 없음 | 헤더 없음 | - | 5/5 PASS |

7경로는 GET 3개(`getInputStream`, `getContentAsByteArray`, `readableChannel`)와 HEAD 4개(`exists`, `isReadable`, `contentLength`, `lastModified`)다.\
합계 **45/45 PASS**.

이 프로브가 덮은 것을 커밋된 테스트와 나란히 놓으면 이렇다.

```text
                     커밋된 테스트 T2          blind 프로브
  경로             : GET 1 개                  GET 3 + HEAD 4
  자격증명         : alice:se~ret 1 종         5 종 + userinfo 없음
  '/' (값 63)      : 없음                      user:~aÿ (UTF-8)
  패딩             : 없음                      있음 / 없음 둘 다
  구현 diff 열람   : 열람함                    열람 안 함
```

워커의 보고 중 두 가지는 테스트 설계에 대한 독립 확인이었다.

- **ASCII로는 `/`(값 63)를 만들 수 없다.**\
  그것을 만드는 ASCII는 `?`와 DEL뿐이고 raw `?`는 authority를 끝낸다.\
  그래서 워커는 `/` 케이스를 UTF-8 비ASCII 바이트로 구성했고, 이것은 플랫폼 charset이 UTF-8일 때만 성립한다(spec §2의 "`getBytes()` 플랫폼 기본 charset 유지"와 정합).
- **spec §5의 예시 `admin:p?ss~~`는 URL에 넣을 수 없다.**\
  메인이 착수 직후 같은 이유로 `alice:se~ret`로 바꿔 둔 상태였고, 이 지적으로 spec 문구도 정정했다.

워커는 수정 전 코드에 대해서는 돌리지 않았다(git 사용 금지 조건).\
"URL-safe였다면 실패했을 것"은 두 알파벳 비교에 근거한 주장이고, 수정 전 red는 커밋된 T2가 실측으로 맡는다.
