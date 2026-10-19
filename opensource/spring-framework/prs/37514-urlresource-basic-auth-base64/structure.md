# PR #37514 - 무대의 실구조와 워크플로우

## 1. 무대 - 실구조

이 결함의 무대는 **`Resource` 추상화가 원격 HTTP URL에 접속할 때 연결을 다듬는 훅 하나**다.\
`UrlResource`가 여는 모든 연결은 한 메서드를 지나가고, 그 메서드 안의 한 줄이 인코더를 고른다.

> **훅 메서드(hook method)** — 상위 클래스가 정해진 시점에 부르도록 비워 두고, 하위 클래스가 오버라이드해 동작을 끼워 넣는 메서드.\
> 예: `AbstractFileResolvingResource.customizeConnection`은 연결을 열 때마다 불리고, `UrlResource`가 이것을 오버라이드해 인증 헤더를 붙인다.

계층을 위에서 아래로 그리면 이렇다.

```text
+------------------------------------------------------------------------------+
| 공개 API (Resource)                                                          |
|   UrlResource.getInputStream()                        UrlResource.java:244   |
|   AbstractFileResolvingResource.exists()              :59 (HEAD), :73 (폴백) |
|   AbstractFileResolvingResource.isReadable()          :143 (HEAD), :149      |
|   AbstractFileResolvingResource.contentLength()       :300 (HEAD), :308      |
|   AbstractFileResolvingResource.lastModified()        :335 (HEAD), :344      |
|      전부 url.openConnection() 직후 customizeConnection(con) 을 부른다      |
+------------------------------------------------------------------------------+
                                    |  동적 디스패치
                                    v
+------------------------------------------------------------------------------+
| UrlResource.customizeConnection(URLConnection)                 :259-267      |
|   super.customizeConnection(con)          캐시 설정 + HttpURLConnection 훅  |
|   userInfo = this.url.getUserInfo()       URL 파서가 잘라 둔 값              |
|   if (userInfo != null)                                                      |
|     bytes = userInfo.getBytes()           플랫폼 기본 charset (범위 밖)       |
|     Base64.getEncoder().encodeToString    <- 수정 전 getUrlEncoder  :264     |
|     con.setRequestProperty("Authorization", "Basic " + ...)                  |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| AbstractFileResolvingResource.customizeConnection(URLConnection)  :363-368  |
|   useCachesIfNecessary(con)                                                  |
|   if HttpURLConnection -> customizeConnection(HttpURLConnection)  :386 (빈) |
+------------------------------------------------------------------------------+
                                    |
                                    v
                      원격 HTTP 서버 (RFC 7617 표준 디코더)
```

이 그림에서 읽어야 할 사실은 셋이다.\
첫째, **헤더를 만드는 곳은 정확히 한 군데다.**\
`getUserInfo`로 헤더를 설정하는 코드는 `UrlResource.java:262` 하나뿐이다(착수 직후 grep으로 load-bearing 가정 1 확인).\
둘째, **그 한 군데를 9개 호출 지점이 공유한다.**\
GET 1곳(`getInputStream`)과 `AbstractFileResolvingResource`의 8곳이다.\
8곳은 HEAD 요청 4곳과, 서버가 HEAD에 405를 돌려줄 때 연결을 다시 여는 폴백 4곳이다.\
셋째, **바이트화(`getBytes()`)와 글자화(Base64)는 별개 단계다.**\
결함은 둘째 단계에만 있다.

> **405 폴백** — 서버가 HEAD 메서드를 지원하지 않는다고(405 Method Not Allowed) 답하면 연결을 새로 열어 GET으로 다시 묻는 경로.\
> 예: `exists()`는 HEAD가 405면 L73에서 연결을 다시 열고, 그때도 `customizeConnection`을 부른다.

호출 지점이 한 메서드로 모이는 모습만 따로 떼면 이렇다.

```text
  getInputStream   exists   isReadable   contentLength   lastModified
     (GET)        (HEAD)     (HEAD)        (HEAD)          (HEAD)
       |          + 폴백     + 폴백        + 폴백          + 폴백
       |            |          |             |               |
       +------------+----------+-------------+---------------+
                                |
                                v
                     customizeConnection   <- 9 곳이 전부 여기로
                                |
                                v
                       인코더 한 줄 (:264)
```

-> 그래서 수정도 한 줄이고, 수정의 효과도 9곳 전부에 미친다. 커밋된 테스트는 GET 하나만 보지만 blind 프로브가 나머지 HEAD 경로를 실행으로 확인했다([tests.md](tests.md)).

## 2. 한 요청의 일생 - 자격증명이 헤더가 되기까지

`alice:se~ret`로 `getInputStream()`을 부를 때 값이 어떻게 바뀌어 가는지를 단계별로 추적한다.

```text
[수정 전]
  new UrlResource("http://alice:se~ret@localhost:8080/resource")
    URL 파서: userInfo = "alice:se~ret"        ('~' 는 unreserved, 그대로 통과)

  getInputStream()
    con = url.openConnection()
    customizeConnection(con)
      getBytes()        -> 61 6C 69 | 63 65 3A | 73 65 7E | 72 65 74
      6비트 조각        -> ... | 28 54 21 62 | ...
      getUrlEncoder     -> "YWxpY2U6c2V-cmV0"                <- 값 62 를 '-' 로
      헤더              -> Authorization: Basic YWxpY2U6c2V-cmV0
    con.getInputStream()  -> 이 시점에 요청이 서버로 간다

  서버
    표준 디코더로 "YWxpY2U6c2V-cmV0" 해석 -> '-' 는 표준 알파벳에 없음
    -> 거부 또는 다른 바이트 -> 401

[수정 후]  같은 시나리오
      getEncoder        -> "YWxpY2U6c2V+cmV0"                <- 값 62 를 '+' 로
  서버
    표준 디코더 -> "alice:se~ret" -> 인증 성공
```

**문제가 생기는 단계는 "바이너리화"가 아니라 "바이너리를 글자로 바꾸는" 단계다.**\
`getBytes()`의 결과는 수정 전후 같다.\
달라지는 것은 그 바이트를 6비트씩 잘라 표에서 글자를 고르는 순간, 그것도 값 62/63인 조각에서만이다.\
이 구분은 계획 게이트 중 사용자가 "바이너리화를 할때 문제가 발생한다는거 맞아?"라고 물었을 때 메인이 바로잡은 지점이기도 하다([gates.md](gates.md)).

> **unreserved 문자** — URL에서 아무 의미 없이 그대로 쓸 수 있는 문자(영문·숫자·`-`·`.`·`_`·`~`).\
> 예: `~`는 unreserved라 userinfo에 퍼센트 인코딩 없이 넣을 수 있고, `getUserInfo()`가 그대로 돌려준다.

## 3. 발화 조건의 산수 - 어떤 자격증명이 갈리나

[README 3절](README.md)의 결론을 입력 쪽에서 다시 정리하면 이렇다.

| 입력 바이트 조건 | 조각 4의 값 | 표준 | URL-safe | userinfo에 넣을 수 있나 |
|---|---|---|---|---|
| 셋째 자리가 `~`(0x7E) | 62 | `+` | `-` | 예 (unreserved) |
| 셋째 자리가 `>`(0x3E) | 62 | `+` | `-` | 아니오 (log: `new URL` 폴백 경로만) |
| 셋째 자리가 `?`(0x3F) | 63 | `/` | `_` | 아니오 (쿼리 시작) |
| 셋째 자리가 DEL(0x7F) | 63 | `/` | `_` | 아니오 |
| 그 밖의 모든 ASCII 조합 | 0~61 | 같음 | 같음 | - |
| 비ASCII(UTF-8 등) | 62/63 가능 | 다름 | 다름 | 플랫폼 charset에 의존 |

마지막 행은 이 PR의 범위를 벗어나는 갈래다.\
비ASCII 바이트는 최상위 비트가 1일 수 있어 조각 1~3에서도 62/63이 나올 수 있다(blind 워커의 `user:~aÿ` -> `dXNlcjp+YcO/` 사례).\
다만 그 바이트열 자체가 `getBytes()`의 플랫폼 기본 charset에 달려 있고, charset은 spec §4가 범위에서 뺐다.

## 4. 기원의 구조 - 같은 날 두 커밋

이 결함은 "코드를 고치다 깨뜨린" 회귀라기보다 "코드를 옮기다 짝을 잘못 고른" 이관 실수다.\
두 커밋이 무엇을 옮겼는지 나란히 놓으면 이렇다.

```text
  ac9ca412c8e  (작성 2018-05-08 Denis Kostin / 커밋 2023-08-22 16:12)
  +----------------------------------------------------------+
  | getInputStream() 안에서만                                |
  |   Base64Utils.encodeToString(url.getUserInfo().getBytes())|
  |     -> 내부적으로 Base64.getEncoder()   (표준)           |
  | 적용 범위: GET 1 경로                                    |
  +----------------------------------------------------------+
                         |
                         |  26 분 뒤
                         v
  f95a1f49dfe  "Polish"  (Stephane Nicoll, 2023-08-22 16:38)
  +----------------------------------------------------------+
  | customizeConnection 오버라이드로 이동                     |
  |   Base64.getUrlEncoder().encodeToString(...)  (URL-safe) |
  | 적용 범위: GET + HEAD + 폴백 9 경로                      |
  | 함께 추가한 테스트: alice:secret + getDecoder() 로 검증   |
  +----------------------------------------------------------+
```

polish는 두 가지를 동시에 했다.\
헤더 생성 위치를 `customizeConnection`으로 옮겨 **적용 범위를 GET 하나에서 9경로로 넓힌 것**은 개선이고, 그 과정에서 `Base64Utils`를 걷어내며 **인코더를 바꾼 것**이 결함이다.\
`Base64Utils`는 그해 1월 `5448e810215`로 6.0.5부터 deprecated(forRemoval)였고, 이후 6.2에서 `a85bf3185e4`로 제거됐다.

| `Base64Utils` (polish 직전) | 대응하는 JDK 호출 |
|---|---|
| `encodeToString(byte[])` - 원본이 쓴 것 | `Base64.getEncoder().encodeToString` |
| `encodeToUrlSafeString(byte[])` | `Base64.getUrlEncoder().encodeToString` |

원본의 짝은 윗줄인데 polish는 아랫줄을 골랐다.\
두 커밋의 커밋 시각이 26분 차이이므로 표준 인코더 버전이 단독으로 릴리스된 적은 없었을 것으로 보인다 - 다만 이것은 커밋 시각에서 나온 추정이고 릴리스 태그로는 확인하지 않았다.

## 5. 스프링 전역에서의 자리

`UrlResource`는 `classpath:`나 `file:`이 아닌 일반 URL 위치를 가리키는 `Resource`다.\
`ResourceLoader`에 `http://...` 위치를 넘기면 이 클래스가 만들어지므로, 설정 파일이나 원격 리소스를 URL로 읽어 오는 애플리케이션 코드가 이 경로를 탄다.

> **Resource 추상화** — 파일·클래스패스·URL 등 위치가 다른 자원을 같은 인터페이스(`getInputStream`, `exists` 등)로 다루게 하는 스프링 코어의 계층.\
> 예: `new UrlResource("http://host/config.properties")`도 `ClassPathResource`처럼 `getInputStream()`으로 읽는다.

Basic 인증 값을 만드는 곳은 프레임워크 안에 둘 있다.

```text
  spring-web   HttpHeaders.encodeBasicAuth (:2187)
                 Base64.getEncoder()   (:2202)         <- 표준 (정답)
  spring-core  UrlResource.customizeConnection (:259)
                 Base64.getUrlEncoder() (수정 전 :264)  <- URL-safe (결함)
```

같은 프레임워크 안에서 같은 RFC를 구현하는 두 자리가 서로 다른 알파벳을 쓰고 있었다.\
수정 후에는 둘이 같아진다.

이 결함이 실제로 사용자에게 닿으려면 조건을 차례로 통과해야 한다.

```text
UrlResource 로 http(s) URL 을 여나?     -- 아니오 -->  해당 없음
        |
       예
        v
URL 에 userinfo 가 있나?               -- 아니오 -->  헤더 자체를 안 만든다
        |
       예
        v
자격증명에 '~' 가 3 바이트 묶음의       -- 아니오 -->  두 알파벳 결과 동일, 정상
셋째 자리에 있나? (ASCII 기준)
        |
       예
        v
  발화 - '+' 대신 '-' 가 나가고, 서버가 맞는 비밀번호를 401 로 거절한다
```

## 6. 범위 밖으로 남긴 인접 결함

같은 메서드 안에서 눈에 띄었지만 spec §4에 따라 손대지 않은 것이 둘 있다(log 완료 요약에 기록).

| 인접 결함 | 내용 | 왜 범위 밖인가 |
|---|---|---|
| charset | `userInfo.getBytes()`가 플랫폼 기본 charset을 쓴다 | 비ASCII 자격증명의 바이트열이 실행 환경에 따라 달라지는 별개 문제 |
| 퍼센트 디코딩 | `getUserInfo()`는 퍼센트 인코딩을 풀지 않아 `p%40ss`가 원문 그대로 인코딩된다 | blind 프로브에서 `admin:s3cr3t%3F`가 `%3F` 그대로 나가는 것으로 관측. 동작 변경 폭이 커 별건 |

> **퍼센트 인코딩** — URL에 직접 못 쓰는 문자를 `%` 뒤 16진수 두 자리로 적는 방식.\
> 예: 비밀번호의 `@`는 URL에서 호스트 구분자라 `%40`으로 적어야 하는데, 지금 코드는 그것을 다시 `@`로 풀지 않고 보낸다.

## 출처

기준: 로컬 브랜치 `fix/urlresource-basic-auth-base64`의 HEAD `d40f67bb08f`(base upstream/main `49adc91c7e4`).\
**본문의 file:line은 수정 후 좌표다** - 수정이 한 줄 치환이라 수정 전과 줄 번호가 같다.
