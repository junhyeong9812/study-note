# html/syntax/31 — 파일 업로드: `accept`/`multiple`/`capture` 와 `enctype=multipart/form-data` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 File Upload 상태·항목 목록·이름·값 쌍 변환·multipart 절로 접지했다(앞 배치가 받아 둔 사본). **`capture` 는 그 명세에 없다.**\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 서버가 받은 부분이다** — 27 칸을 미리 선언하고 「거부된 칸」을 스크립트가 센다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 거부된 칸 0 / 27 — 넣은 파일 그대로 · 깃발 0 / 27 · `change` 27 번 모두 `isTrusted=true` · `t2.png` 는 `image/png`

**출력**

```text
$ python3 html29b-form.py 시도 html29b-31-accept.html | sed -n '1,7p'
[files · p1.png]
  페이지  change(a1 · isTrusted=true) → change(a2 · isTrusted=true) → change(a3 · isTrusted=true) → 넣은 뒤 a1:files=1,valid=true a2:files=1,valid=true a3:files=1,valid=true → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 3개 · 경계로 갈라 필드만 적는다)
          필드  a1=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · a2=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · a3=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png)
[files · t1.txt]
(exit 0)
```

```text
$ python3 html29b-form.py 시도 html29b-31-accept.html | sed -n '/^길 · 파일/,$p'
길 · 파일             a1 image/png            a2 .png                 a3 image/*
files · p1.png        받음 p1.png             받음 p1.png             받음 p1.png
files · t1.txt        받음 t1.txt             받음 t1.txt             받음 t1.txt
files · t2.png        받음 t2.png             받음 t2.png             받음 t2.png
drop · p1.png         받음 p1.png             받음 p1.png             받음 p1.png
drop · t1.txt         받음 t1.txt             받음 t1.txt             받음 t1.txt
drop · t2.png         받음 t2.png             받음 t2.png             받음 t2.png
chooser · p1.png      받음 p1.png             받음 p1.png             받음 p1.png
chooser · t1.txt      받음 t1.txt             받음 t1.txt             받음 t1.txt
chooser · t2.png      받음 t2.png             받음 t2.png             받음 t2.png
넣은 뒤 validity.valid 가 false 인 칸 = 0 / 27 · change 이벤트 = 27번 (isTrusted=true 27번)
거부된 칸 = 0 / 27  (「받음 이름」= 서버가 받은 부분의 filename · 「— (빈 부분)」= 이름 빈 부분)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **27 칸 전부 「받음」** — `accept` 가 무엇이든, 길이 무엇이든 **넣은 파일의 이름**이 서버의 `filename` 이다.
- ★★ **`validity.valid` 가 `false` 인 칸 0** — `accept` 에 맞는 제약이 명세에 없다(A4).
- ★★ **`change` 27 번 · `isTrusted=true` 27 번** — 스크립트 길도 브라우저가 낸 `change` 다.
- ★★ **`t2.png` → `부분 Content-Type: image/png`** — 내용은 `xyz\n`(4 바이트)인데 이름이 `.png` 다(A6).

### 2. urlencoded — `f=p1.png` · multipart — 67 바이트 · `filename=p1.png` · `image/png` · `text/plain` — `f=p1.png`

**출력**

```text
$ python3 html29b-form.py 시도 html29b-31-enctype.html
[갑 · enctype 없음]
  페이지  click(갑보냄 · detail=1) → submit(submitter=갑보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「t=%EA%B0%80&f=p1.png」
          필드  t=「가」 · f=「p1.png」
[을 · multipart/form-data]
  페이지  click(을보냄 · detail=1) → submit(submitter=을보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 2개 · 경계로 갈라 필드만 적는다)
          필드  t=「가」 · f=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png)
[병 · text/plain]
  페이지  click(병보냄 · detail=1) → submit(submitter=병보냄)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「t=가\r\nf=p1.png\r\n」
          필드  t=「가」 · f=「p1.png」
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **urlencoded** — `Content-Type=application/x-www-form-urlencoded` · 본문 `「t=%EA%B0%80&f=p1.png」` — **파일 이름 글자만.**
- ★★★ **multipart** — 부분 2개 · `f=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png)` · `t` 부분엔 `Content-Type` 이 없다.
- **`text/plain`** — 본문 `「t=가\r\nf=p1.png\r\n」` — 이름만.

### 3. `multiple` 은 `selectMultiple` · 부분 둘 / `multiple` 없는 칸에 둘 — 스크립트는 첫째만 · 끌어다 놓기는 0 / `capture` — IDL 없음

**출력**

```text
$ python3 html29b-form.py 시도 html29b-31-multiple.html
[chooser 로 m1 에 둘 · m2 에 하나]
  페이지  click(m1 · detail=1) → chooser(selectMultiple) → click(m2 · detail=1) → chooser(selectSingle) → files.length m1=2 m2=1 m3=0 m4=0 → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 5개 · 경계로 갈라 필드만 적는다)
          필드  m1=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · m1=「abc\n」 (filename=「t1.txt」 · 부분 Content-Type: text/plain) · m2=「abc\n」 (filename=「t1.txt」 · 부분 Content-Type: text/plain) · m3=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m4=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)
[setFileInputFiles 로 m2(multiple 없음)에 둘]
  페이지  files.length m1=0 m2=1 m3=0 m4=0 → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 4개 · 경계로 갈라 필드만 적는다)
          필드  m1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m2=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · m3=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m4=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)
[drop 으로 m2(multiple 없음)에 둘]
  페이지  files.length m1=0 m2=0 m3=0 m4=0 → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 4개 · 경계로 갈라 필드만 적는다)
          필드  m1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m2=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m3=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m4=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)
[drop 으로 m1(multiple)에 둘]
  페이지  files.length m1=2 m2=0 m3=0 m4=0 → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 5개 · 경계로 갈라 필드만 적는다)
          필드  m1=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · m1=「abc\n」 (filename=「t1.txt」 · 부분 Content-Type: text/plain) · m2=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m3=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m4=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)
[capture 칸 m3·m4 를 chooser 로]
  페이지  click(m3 · detail=1) → chooser(selectSingle) → click(m4 · detail=1) → chooser(selectSingle) → capture in HTMLInputElement.prototype=false · capture IDL m3=undefined m4=undefined · getAttribute m3=user · files.length m1=0 m2=0 m3=1 m4=1 → click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 4개 · 경계로 갈라 필드만 적는다)
          필드  m1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m2=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · m3=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png) · m4=「abc\n」 (filename=「t1.txt」 · 부분 Content-Type: text/plain)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **고르기 창** — `m1` 은 **`selectMultiple`**, `m2`·`m3`·`m4` 는 `selectSingle`. `m1` 에 둘 → **`m1` 부분 둘**(부분 5개).
- ★★★ **`multiple` 없는 `m2` 에 둘** — `setFileInputFiles` 는 **`m2=1`**(`p1.png`) · 끌어다 놓기는 **`m2=0`**(빈 부분). **`multiple` 인 `m1` 에 끌어다 놓으면 `m1=2`**.
- **고르지 않은 칸** — 칸마다 `filename=「」 · application/octet-stream` 부분 **하나**.
- ★★★ **`capture`** — `'capture' in HTMLInputElement.prototype=false` · `m3.capture`·`m4.capture` 는 **`undefined`** · `getAttribute('capture')` 는 `user`. 고르기 창도 `selectSingle` 로 **다른 칸과 같다.**

### 4. should(권고) — 「받지 않는 파일을 고르지 못하게 해야 한다」 · 제약은 없다(`required` 의 「비었으면 missing」 하나뿐)

- 명세 — `accept` 는 「받아들일 파일 형식의 **힌트**」이고, 「UA 는 받지 않는 파일을 사용자가 **고르지 못하게 해야 한다(should)**」. **must 가 아니다.**
- File Upload 상태의 **제약 검증 문장은 하나** — 「`required` 이고 고른 파일 목록이 **비었으면** missing」. 형식에 대한 제약이 **없어서** A1 의 깃발이 0 이다. **폼 검증으로 막을 수 없다**([29번](../29-constraint-validation/2-summary.md)의 제약 검증 목록 밖).

### 5. 「이름·값 쌍 목록으로 바꾸기」의 「값이 `File` 이면 그 이름」 · urlencoded 와 `text/plain`

- 명세 — 「`application/x-www-form-urlencoded` 와 `text/plain` 인코딩 알고리즘은 **값이 글자인 이름·값 쌍 목록**을 받는다 … 항목의 값이 **`File` 이면 그 `File` 의 이름**을 값으로」.
- multipart 는 이 변환을 **거치지 않고** 항목 목록을 RFC 7578 로 싼다 — 그래서 내용이 간다(A2).

### 6. `image/png` 를 받는다 · 형식은 내용(바이트)을 읽어 가른다

- A1 — 글자 파일 `t2.png` 가 **`부분 Content-Type: image/png`** 로 갔다. 이 판의 Chrome 은 형식을 **이름의 확장자**에서 붙였다(관찰 — `File` 의 형식을 정하는 규칙은 [web-api 31번](../../../../web-api/31-blob-file-and-object-url/2-summary.md) 쪽이다).
- 사용자는 이름을 마음대로 바꾼다 — **이름도 `Content-Type` 도 사용자의 입력**이다. 서버는 **내용의 첫 바이트**(PNG 는 `89 50 4E 47`)처럼 **파일 자체**를 봐야 한다(해석 — 이 판은 서버 쪽 판별기를 안 만들었다).

### 7. 스크립트 길 — 첫째 하나만 · 끌어다 놓기 — 하나도 안 넣음 · 「`multiple` 이 없으면 파일은 하나를 넘으면 안 된다(must)」

- A3 — `setFileInputFiles` 는 `m2=1`, 끌어다 놓기는 `m2=0`.
- 명세 — 「`multiple` 속성이 없으면 고른 파일 목록에 파일이 **하나를 넘으면 안 된다**」. 두 길이 **다른 방법으로** 그 문장을 지켰다 — **자르기**(구현) 대 **거절**(구현). 어느 쪽을 해야 하는지는 명세가 말하지 않는다.

### 8. 잰 것 — 데스크톱 Chrome 에 IDL 이 없다 · 고르기 창이 같다 / 못 잰 것 — 휴대폰의 카메라 / WHATWG HTML 에서 `capture` 0 건

- **잰 것** — `'capture' in HTMLInputElement.prototype=false` · `.capture` 는 `undefined` · 고르기 창 `mode` 가 `capture` 없는 칸과 **같다**(A3). 이 판의 Chrome 은 그 속성을 **인식하지 않았다.**
- **못 잰 것** — 모바일에서 `capture="user"` 가 **전면 카메라를 바로 여나.** 기기가 없다.
- **명세** — 받아 둔 WHATWG HTML `input` 절 전문에 `capture` 가 **0 건**이다. 정의는 W3C 의 HTML Media Capture 에 있고 **이 배치는 그 문서를 열지 않았다.** 그래서 「명세가 데스크톱에서 무시하라고 한다」고 **적지 않는다.**

### 9. 어느 쪽도 말할 수 없다 — 가로챈 창은 목록을 보여 주지 않는다

- `chooser` 길은 **진짜 클릭으로 창을 열게 한 뒤** CDP 가 그 창을 가로채 파일을 넣는다. **운영체제 창의 필터 목록**은 화면에 없다. 명세의 「고르지 못하게 해야 한다」가 지켜지는 곳이 **바로 그 창**이라, 이 판은 **「못 잰 것」** 으로 남긴다.
- 말할 수 있는 것은 **「창을 지난 파일을 칸·검증·서버가 다시 거르지 않는다」**(A1)까지다.

### 10. 끌어다 놓기의 통째 거절 — 구현 · 빈 칸의 `application/octet-stream` — 명세 · 형식이 확장자에서 — 구현(관찰) · 거부 0 / 27 — 이 판의 관찰

- **통째 거절** — 명세는 「하나를 넘으면 안 된다」만 적는다 → 방법은 **구현**(A7).
- **`application/octet-stream`** — 항목 목록 만들기의 「고른 파일이 없으면 **이름 빈 `File`, `application/octet-stream`**」 → **명세**.
- **형식이 확장자에서** — HTML 명세가 정하지 않는다 → **구현**.
- **거부 0 / 27** — should 인 필터를 이 판의 세 길이 **아무도 적용하지 않은 결과** → **관찰**(실제 창은 못 봤다).

### 11. 정본 경계

- **`enctype` 여섯 칸** — [21번](../21-form-submission-model/2-summary.md)의 (1).
- **빈 파일 칸** — [24번](../24-input-types-choice-special/2-summary.md)의 (2).
- **`FormData` 에 `File`·`Blob` 을 넣을 때의 `filename`·`Content-Type`** — [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md)의 (3).
- **받은 `File` 의 미리보기·오브젝트 URL** — [web-api 31번](../../../../web-api/31-blob-file-and-object-url/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [29번](../29-constraint-validation/3-answer.md)의 `html29b-form.py`(`files`·`drop`·`chooser` 단계)다.\
★ **`drop`** — 칸 한가운데에 `Input.dispatchDragEvent` 로 `dragEnter` → `dragOver` → `drop` 을 보냈다(`data.files` 에 파일 경로 · `dragOperationsMask=1`). **운영체제의 끌기가 아니라 CDP 가 합성한 끌기**다.\
★ **`chooser`** — `Page.setInterceptFileChooserDialog(enabled)` 뒤 진짜 마우스로 칸을 누르고, `Page.fileChooserOpened` 의 `backendNodeId` 에 `DOM.setFileInputFiles`.

**흔들림 확인** — 캡처 세 판의 재대조는 [29번](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`accept` 격자 27 칸** | 3 | 동작 방식 (1) · A1 |
| **`enctype` 세 폼** | 3 | 동작 방식 (2) · A2 |
| **`multiple`·`capture` 다섯 시도** | 3 | 동작 방식 (3) · A3 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `multiple` 없는 칸에 둘 | 스크립트 — 첫째 · 끌어다 놓기 — 거절 | 명세는 방법을 정하지 않는다 |
| 부분 형식 | 이름의 확장자 | HTML 명세 밖 |
| `capture` IDL | 없음 | 모바일 판·다른 판에서 달라질 수 있다 |

**안 돌려 본 것** — ① **`accept` 토큰의 대소문자·중복.** ② **`webkitdirectory`.** ③ **큰 파일.** ④ **`required` 인 파일 칸**(명세 문장만 — 「비었으면 missing」).

**못 잰 것** — ① **운영체제 고르기 창의 필터.** ② **모바일의 카메라·사진첩.** ③ **운영체제의 실제 끌기.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥** · **창 ⑦ 은 24번 인용**.

## 용어 풀이

- **고르기 창(picker)** — 파일 칸이 여는 창. `multiple` 이면 여러 개 고르기로 열린다.
- **이름·값 쌍으로 바꾸기** — urlencoded·`text/plain` 이 쓰는 변환. `File` 은 이름이 된다.
- **부분 `Content-Type`** — multipart 의 파일 부분에 붙는 형식. 이 판은 확장자에서.
