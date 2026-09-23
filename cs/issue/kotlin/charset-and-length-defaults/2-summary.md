# cs/issue/kotlin/charset-and-length-defaults — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

**한 문장:** JVM·프레임워크·도구가 "사람 편의"를 위해 고른 기본값(전송 문자셋 ISO-8859-1, `String.length`=문자 수, git `core.quotepath`=8진수 이스케이프)은 기계가 바이트를 다룰 때 데이터를 조용히 왜곡하므로, 경계에서 **인코딩과 단위를 직접 못 박아야** 한다.

```
[사고1 — 전송 문자셋]
문자열 본문 → Spring StringHttpMessageConverter → 기본 ISO-8859-1로 인코딩
   라틴-1에 없는 한글은 '?'로 치환(조용한 손실), 라틴-1에 있는 비ASCII 기호(예: U+00B7 가운뎃점)는
   1바이트 0xB7로 인코딩 → UTF-8 수신 측이 거부 (Invalid UTF-8 start byte 0xb7)
   해법: body.toByteArray()  (UTF-8 바이트로 직접) + charset=utf-8

[사고2 — 문자 수 vs 바이트]
상한 = 8192 바이트,  판단 = buffer.length + paragraph.length > 8192
   String.length = UTF-16 코드유닛 수 ≈ "글자 수".  한글 = UTF-8 3바이트/글자
   → 8192 "글자" 버퍼 = 실제 ~24KB.  상한 초과가 통과됨
   해법: paragraph.toByteArray().size 로 바이트로 측정

[사고3 — 도구의 사람용 출력]
git ls-files/diff → core.quotepath=true(기본) → 한글 경로를 "\352\267\270"로 이스케이프
   그 출력을 파일 경로로 씀 → No such file
   해법: git -c core.quotepath=off  (기계용 출력)
```

**공통 원리:** 세 사고 모두 "기본값은 중립이 아니다"의 사례다. 프레임워크·표준 라이브러리·CLI 도구는 대개 **사람이 읽기 좋은 쪽**으로 기본값을 고른다 — 라틴 문자셋(과거 웹 관례), 글자 단위 길이(사람이 세는 단위), 이스케이프된 경로(터미널에서 안전). 그런데 데이터 파이프라인은 **바이트**를 다루므로 이 편의 기본값이 왜곡을 낳는다.

**세 자리의 교정:**
- **인코딩:** "문자열 = UTF-8"은 착각이다. 전송 계층의 기본 문자셋은 프레임워크마다 다르므로, 문자열을 맡기지 말고 `toByteArray()`로 **UTF-8 바이트를 직접** 만들어 넘기고 `charset=utf-8`을 명시한다.
- **길이 단위:** `String.length`는 UTF-16 코드유닛 수(≈글자 수)다. 바이트 길이를 요구하는 자리(청크 상한·RESP `$len`·Content-Length·바이트 기준 컬럼)에서는 `toByteArray().size`로 **같은 단위**를 쓴다.
- **도구 출력:** 사람용 출력을 기계 입력으로 쓸 땐 이스케이프를 끄는 옵션(`core.quotepath=off`)부터 찾는다.

**어떻게 잡나:** 이 부류는 ASCII 데이터로 테스트하면 전부 통과한다(라틴에서 ASCII는 안 깨지고, ASCII는 1글자=1바이트). 그래서 **첫 스모크·테스트 데이터에 반드시 한글(멀티바이트)을 넣는다.**

## 핵심 문장

- "문자열 = UTF-8"은 착각 — 전송 계층 기본 문자셋은 프레임워크마다 다르다(Spring 문자열 본문 = Content-Type에 charset이 없고 JSON 계열이 아니면 ISO-8859-1).
- 인코딩은 경계에서 못 박는다: 문자열을 맡기지 말고 `toByteArray()`(UTF-8) + `charset=utf-8`.
- `String.length` = UTF-16 코드유닛 수(≈글자 수) ≠ 바이트 수. 한글은 UTF-8 3바이트/글자.
- 바이트 길이를 요구하는 자리(청크 상한·RESP `$len`·Content-Length)에선 바이트로 측정한다.
- 사람용 기본값(문자셋·글자 단위·quotepath)은 기계 처리에서 왜곡을 낳는다 — 기계용으로 명시.
- 이 부류는 ASCII로 통과하니, 스모크·테스트 데이터에 반드시 멀티바이트 문자를 넣어라.
