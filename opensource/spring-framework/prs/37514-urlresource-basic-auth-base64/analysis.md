# PR #37514 - 착수 분석: UrlResource Basic 인증의 URL-safe Base64

## 0. 결론 먼저

`UrlResource#customizeConnection`이 URL userinfo를 `Base64.getUrlEncoder()`(RFC 4648 §5)로 인코딩해 `Authorization: Basic` 헤더에 싣는다.\
RFC 7617 §2는 RFC 4648 §4 표준 알파벳을 요구하므로, 인코딩 결과에 값 62/63 조각이 생기는 자격증명은 `+` 대신 `-`로 나가 서버에서 거절된다.\
수정은 `getEncoder()`로의 한 단어 치환이다.

> **착수 분석(analysis)** — 코드를 고치기 전에 실파일을 읽어 결함의 위치·경로·영향 범위를 확정해 두는 문서.\
> 예: 여기서 헤더 생성 지점이 하나뿐임을 먼저 grep으로 확정했기 때문에 "한 줄로 모든 경로가 고쳐진다"를 사실로 적을 수 있었다.

후보 출처는 spring-core 버그헌트 라운드6의 S급 IO-2다.\
2026-10-18 upstream/main `49adc91c7e4`에서 결함이 현존함(`UrlResource.java:264`)과, 이 결함을 다루는 타인 PR·이슈가 없음을 확인한 뒤 착수했다.

## 1. 무대 - 헤더를 만드는 단일 지점

```java
@Override
protected void customizeConnection(URLConnection con) throws IOException {
	super.customizeConnection(con);
	String userInfo = this.url.getUserInfo();
	if (userInfo != null) {
		String encodedCredentials = Base64.getUrlEncoder().encodeToString(userInfo.getBytes());
		con.setRequestProperty(AUTHORIZATION, "Basic " + encodedCredentials);
	}
}
```
(수정 전 UrlResource.java:259-267)

이 메서드를 부르는 자리는 `getInputStream()`(:246)과 `AbstractFileResolvingResource`의 8곳(exists·isReadable·contentLength·lastModified의 HEAD 요청과 405 폴백)이다.\
그 자리들이 모두 이 오버라이드를 거치므로 헤더 생성 지점은 하나다([structure.md](structure.md) 1절).

## 2. 핵심 이름표

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `UrlResource.customizeConnection` (:259) | 연결마다 userinfo로 인증 헤더 설정 | 결함이 사는 자리 |
| `Base64.getUrlEncoder()` | RFC 4648 §5, 62=`-` 63=`_` | **잘못 고른 인코더** |
| `Base64.getEncoder()` | RFC 4648 §4, 62=`+` 63=`/` | RFC 7617이 요구하는 인코더 |
| `URL.getUserInfo()` | URL 파서가 잘라 둔 `user:pass` | 퍼센트 디코딩 없이 원문 반환(범위 밖) |
| `userInfo.getBytes()` | 플랫폼 기본 charset으로 바이트화 | 정상 단계. charset 문제는 범위 밖 |
| `AbstractFileResolvingResource` 8곳 | HEAD·폴백 연결 | 같은 오버라이드를 거쳐 함께 영향 |
| `HttpHeaders.encodeBasicAuth` (spring-web :2187) | 프레임워크의 다른 Basic 인코딩 | `getEncoder()` 사용 - 선례 |
| `useUserInfoToSetBasicAuth` (ResourceTests :503) | 기존 테스트, `alice:secret` | 두 알파벳 결과가 같아 결함 미검출 |

> **RFC 4648** — Base16/32/64 인코딩을 정의한 규격. §4가 표준 Base64, §5가 URL·파일명 안전 Base64다.\
> 예: RFC 7617은 Basic 인증 값의 인코딩을 "RFC 4648 Section 4"로 지정한다.

## 3. 결함 경로 단계 추적

착수 시 메모에는 `admin:p?ss~~`(표준 `YWRtaW46cD9zc35+` / 현재 `YWRtaW46cD9zc35-`)를 실측 예로 적었다.\
그런데 착수 직후 스모크에서 이 입력은 `?` 때문에 URL에 넣을 수 없음을 확인하고, 실제 진입점을 통과하는 `alice:se~ret`로 교체했다.\
교체한 입력으로 단계를 따라가면 이렇다.

| 단계 | 동작 | 값 |
|---|---|---|
| 1 | `new UrlResource("http://alice:se~ret@host/resource")` | userInfo = `alice:se~ret` |
| 2 | `getBytes()` | `61 6C 69 63 65 3A 73 65 7E 72 65 74` (12바이트) |
| 3 | 3바이트 묶음 | `ali` / `ce:` / `se~` / `ret` |
| 4 | `se~`를 6비트 조각으로 | `011100 110110 010101 111110` = 28 54 21 **62** |
| 5 | URL-safe 표로 글자화 | `c 2 V -` |
| 6 | 헤더 | `Basic YWxpY2U6c2V-cmV0` (표준이면 `...c2V+cmV0`) |
| 7 | 서버 표준 디코더 | `-` 거부 또는 오해석 -> 401 |

## 4. 발화 조건 - 왜 `~` 하나로 좁혀지나

이 분석의 핵심 산수다.\
ASCII 바이트는 최상위 비트가 0이므로 3바이트 묶음의 조각 1~3은 각각 최대 31, 55, 61이고, 62/63은 셋째 바이트의 하위 6비트인 조각 4에서만 나온다.\
하위 6비트가 62/63인 ASCII는 `>` `~`(62)와 `?` DEL(63)이고, 이 중 URL userinfo에 합법인 것은 `~`뿐이다.

> **load-bearing 가정** — 그것이 참이어야 계획 전체가 성립하는, 아직 확인되지 않은 전제.\
> 예: "헤더 생성 지점이 하나뿐"이 거짓이었다면 한 줄 수정 계획이 무너진다.

```text
  조각 1 = 0aaaaa          <= 31
  조각 2 = aa 0bbb         <= 55
  조각 3 = bbbb 0c         <= 61
  조각 4 = cccccc          <= 63   <- '~' (111110) 가 셋째 자리일 때만 62
```

따라서:

- **실사용 발화** = 3바이트 묶음의 셋째 자리(0부터 세면 3k+2 위치)에 `~`가 있는 자격증명.
- **`/` 대 `_` 차이**는 합법 ASCII userinfo로는 만들 수 없다.
- 끝에 1~2바이트가 남아 패딩이 붙는 경우에도 빈 자리가 0으로 채워져 62/63이 되지 않는다.

이 좁힘이 그대로 테스트 자격증명 선택(`alice:secret`의 `c` 자리에 `~`)의 근거가 됐다.

## 5. 계약과 기원

**계약.**\
RFC 7617 §2 step 4: "encoding this octet sequence using Base64 ([RFC4648], Section 4)".\
명세 작성 시 rfc-editor 원문을 WebFetch로 확인했다(2026-10-18).\
§5(URL-safe)는 다른 알파벳이므로 서버 디코더가 거부하거나 다른 바이트로 해석한다.

**기존 테스트.**\
`useUserInfoToSetBasicAuth`는 `alice:secret`을 쓰고, 헤더를 `Base64.getDecoder()`로 풀어 원문과 비교한다.\
`alice:secret`은 두 알파벳 결과가 `YWxpY2U6c2VjcmV0`으로 같아 결함 경로를 지나면서도 결함을 볼 수 없다.

**기원.**\
원 기능 커밋 `ac9ca412c8e`(gh-1822)는 `Base64Utils.encodeToString`, 즉 표준 인코더를 썼다.\
같은 날 polish 커밋 `f95a1f49dfe`가 deprecated된 `Base64Utils`를 `java.util.Base64`로 옮기면서 `encodeToString`의 짝(`getEncoder`)이 아니라 `encodeToUrlSafeString`의 짝(`getUrlEncoder`)을 골랐다.\
커밋 메시지는 "Polish"뿐이라 URL-safe를 의도한 흔적이 없다.\
이 대조는 diff 2 게이트 중 사용자 질문("라이브러리 자체가 바뀌여서 그런거지?")에 답하려고 `f95a1f49dfe^`의 `Base64Utils`를 직접 열어 확정했다.

## 6. 수정안

### 6.1 채택안 - `getEncoder()`로 치환

```java
String encodedCredentials = Base64.getEncoder().encodeToString(userInfo.getBytes());
```

정당화는 세 겹이다.

1. **규격 일치.** RFC 7617 -> RFC 4648 §4.
2. **원 의도 복원.** 원 기능 커밋의 `Base64Utils.encodeToString`과 같은 동작.
3. **프레임워크 선례.** spring-web `HttpHeaders.encodeBasicAuth`(:2202)가 이미 `getEncoder()`.

영향 범위는 값 62/63 조각을 가진 자격증명뿐이다.\
0~61의 글자와 패딩이 두 인코더에서 같으므로 그 밖의 자격증명은 헤더가 바이트까지 같다.

### 6.2 검토했으나 기각한 대안

| 대안 | 기각 이유 |
|---|---|
| `Base64Utils` 복원 | 6.2에서 제거된 API라 불가 |
| `Base64.getMimeEncoder()` | 76자마다 줄바꿈을 넣어 헤더 값으로 부적합 |
| charset 명시·퍼센트 디코딩까지 함께 수정 | 인터뷰에서 범위를 "Base64만"으로 확정. 별개 결함이고 동작 변경 폭이 큼 |

### 6.3 테스트 형태의 트레이드오프

| 결정 | 안 | 선택 |
|---|---|---|
| TO-1 테스트 형태 | (A) 새 메서드 추가, 기존 유지 / (B) 기존 자격증명만 교체 / (C) `@ParameterizedTest` | **A** - 기존 테스트가 "같은 입력은 헤더 불변" 가드 역할을 계속 맡게 |
| TO-2 단언 방식 | (A) 헤더 정확 문자열 / (B) 표준 디코더로 디코드 후 비교 | **A** - 알파벳·패딩을 문자열로 고정, 실패 메시지가 바로 읽힘 |

## 7. 착수 시점의 열린 결정과 그 해소

**인터뷰 4문항.**\
범위 = Base64만, stakes = 높음(인증 헤더 경로, 표 하한), 모드 = lazy, 브랜치 = upstream/main 기반 새 브랜치 `fix/urlresource-basic-auth-base64` -> main PR(백포트는 메인테이너 판단).

**가정 1 - `customizeConnection`이 userinfo 헤더 설정의 유일한 지점이다.**\
착수 직후 grep으로 확인했다.\
`getUserInfo`로 헤더를 만드는 곳은 `UrlResource.java:260-266` 하나이고, `AbstractFileResolvingResource`의 8곳과 `getInputStream`이 모두 이 오버라이드를 거친다.\
성립.

**가정 2 - MockWebServer 기반 기존 하네스로 실제 전송 헤더를 관측할 수 있다.**\
diff 1 적용 후 `ResourceTests` 69건 중 신규 1건만 `...c2V-cmV0`으로 실패한 것으로 확인했다.\
성립.

**예상 밖 발견 - 예시 자격증명이 URL을 통과하지 못한다.**\
명세 초안의 `admin:p?ss~~`는 `?`가 쿼리 구분자라 userinfo가 `admin:p`에서 잘린다.\
메인이 발화 조건 실측 중에 발견해 `alice:se~ret`로 바꿨고, 나중에 blind 워커도 spec 문구만 보고 같은 지적을 했다.

## 8. 범위 밖

> **범위 밖(out of scope)** — 눈에 띄었지만 이번 변경에서 일부러 손대지 않기로 정한 것.\
> 예: 같은 줄의 `getBytes()` charset 문제는 보이지만, 이번 PR은 알파벳 하나로 좁혀 둔다.

- **`getBytes()` 플랫폼 charset** - 비ASCII 자격증명의 바이트열이 환경에 따라 달라진다.
- **userinfo 퍼센트 디코딩 부재** - `p%40ss`가 원문 그대로 인코딩된다.
- **백포트** - 메인테이너 트리아지 소관. PR은 main 대상.

## 출처

착수 시점(2026-10-18~19)의 명세·log를 학습용으로 다듬은 것이다.\
기준 upstream/main `49adc91c7e4`, 결함 위치 `spring-core/src/main/java/org/springframework/core/io/UrlResource.java:264`.\
작업 폴더: spring-framework-fork `docs/plans/2026-10-18/io2-urlresource-basic-auth-base64/`.
