# html/syntax/31 — 파일 업로드: `accept`/`multiple`/`capture` 와 `enctype=multipart/form-data` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「File Upload state」](https://html.spec.whatwg.org/multipage/input.html#file-upload-state-(type=file))(★ `accept` — 「UA 는 받지 않는 파일을 **고르지 못하게 해야 한다(should)**」 · 파일 이름에 **경로 성분이 없어야 한다** · `multiple` 이 없으면 **파일은 하나 이하** · 끌어다 놓기로도 바꿀 수 있다), [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set)(★ 고른 파일이 없으면 **이름 빈 `File`, `application/octet-stream`**), [「Converting an entry list to a list of name-value pairs」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#converting-an-entry-list-to-a-list-of-name-value-pairs)(★ **`File` 이면 그 이름을 값으로**), [「Multipart form data」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#multipart-form-data)(RFC 7578 · 같은 이름은 **별개의 필드**). **명세 본문은 앞 배치가 2026-09-26 에 받아 둔 사본**으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.\
> ★★★ **`capture` 는 WHATWG HTML 에 없다** — 받아 둔 `input` 절 전문에서 `capture` 를 찾으면 **0 건**이다. 그 속성은 W3C 의 별도 문서(HTML Media Capture)가 정의하고, **이 배치는 그 문서를 열지 않았다.** 그래서 (3) 의 `capture` 줄에는 **명세층이 없다** — 「Chrome 이 이 판에서 그 속성을 무엇으로 다뤘나」만 적는다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 파일은 **세 길**로 넣었다 — CDP `DOM.setFileInputFiles`(스크립트 쪽 길) · CDP `Input.dispatchDragEvent`(끌어다 놓기를 흉내 낸 입력) · **파일 고르기 창 가로채기**(진짜 마우스로 칸을 누르고 열린 창에 파일을 넣는다). 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 파일 칸은 가장 오래된 표면이라 Baseline 조회 대상이 아니다.
> **선행** — [21번 주제](../21-form-submission-model/2-summary.md)(★ **`enctype` × `method` 격자** — GET 은 `enctype` 을 안 본다) · [24번 주제](../24-input-types-choice-special/2-summary.md)(★ **고른 파일이 없는 파일 칸도 실린다** — urlencoded 는 `f1=` · multipart 는 `filename=「」` 부분 하나).
> **경계** — ★★ **같은 본문을 스크립트로 만드는 쪽**(`FormData` 에 `Blob`·`File` 을 넣을 때 `filename`·`Content-Type` 이 어디서 오나)은 [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md)의 (3)·(4), **받은 `File` 을 읽고 미리보고 올리는 쪽**(`Blob`·`FileReader`·오브젝트 URL)은 [web-api 31번](../../../../web-api/31-blob-file-and-object-url/2-summary.md)이다 — 여기는 **마크업의 파일 칸이 무엇을 받고 무엇을 보내나**까지. `enctype` 의 여섯 칸은 21번이 쟀다 — 여기는 **파일 칸이 있을 때** 세 `enctype` 만.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다** — 파일 칸이 무엇을 받아들였는지는 **서버가 받은 부분의 `filename`** 으로 판정한다. 짝으로 **창 ②**(`files.length` · `validity` · 파일 고르기 창의 `mode`)가 페이지 쪽을 본다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | CDP 포트·프로필 경로·서버 포트 · **올린 파일의 절대 경로** | 출력에는 안 들어간다(서버는 `filename` 만 받는다 — 명세가 경로 성분을 금한다) |
| **죽였다** | `multipart/form-data` 의 **경계(boundary) 문자열** | 실행마다 바뀐다 — 하네스가 경계로 갈라 **필드만** 적는다([21번](../21-form-submission-model/2-summary.md)과 같다) |
| **죽였다** | PNG 부분의 **원시 바이트** | UTF-8 이 아니라 「(바이트 67개)」로 적는다 — 개수는 안 흔들린다 |
| **안 흔들린다** | 부분의 `filename` · 부분 `Content-Type` · 부분 수 · `files.length` · 고르기 창의 `mode` · 「거부된 칸 N / M」 | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 서버가 **어느 파일을** 받았나(`filename`) · **본문 모양**(`enctype` 별) · 같은 이름의 **부분 수**((1)\~(3)) |
| **② 노드 프로브**(`files.length` · `validity` · `change` 기록) | ★ **쓴다** | 칸이 **받아들였나** · 깃발이 **섰나** · `change` 가 **사용자 입력으로** 왔나(`isTrusted`)((1)·(3)) |
| **파일 고르기 창의 `mode`**(CDP `Page.fileChooserOpened`) | 쓴다 | `multiple` 이 **창을 여러 개 고르기로** 여나((3)) |
| **⑦ 접근성 트리** | **부적용** — 24번 인용 | 파일 칸의 역할(`button`)은 [24번](../24-input-types-choice-special/2-summary.md)이 찍었다 |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★★ **제5의 상태 — 「고르기 창이 거르나」를 서버로 물었다.** 운영체제의 파일 고르기 창은 headless 에서 **뜨지 않는다**(가로채면 CDP 이벤트만 온다). 그래서 **창이 `accept` 로 목록을 거르는지는 못 본다.** 대신 **창이 무엇을 받든 칸과 서버가 그것을 막나**를 물었다. ★ **바꾼 창이 못 보는 것** — 실제 창의 **「모든 파일」 선택지**나 **필터 목록**. 그것은 「못 잰 것」으로 남긴다.
- ★★ **18-A — 몇 군데 물었나.** (1) 은 **`accept` 셋 × 파일 셋 × 넣는 길 셋 = 27 곳**을 물었다. 「거절이 없다」가 결론이라 **그 27 곳을 미리 선언**하고 「거부된 칸 N / 27」을 스크립트가 센다.

## 한눈에 — 쉽게 말하면

**★ 파일 칸은 「우편물 접수 창구」다. `accept` 는 창구 앞의 안내문(「사진만 받습니다」)이고, 문지기가 아니다. `multipart` 는 소포 상자다 — 상자가 없으면(urlencoded) 봉투에 **소포의 이름표만** 적혀 간다.**

우체국 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **안내문 「사진만 받습니다」** | **`accept`** — 고르기 창에 주는 **힌트** · 명세는 「고르지 못하게 **해야 한다(should)**」까지 |
| **소포 상자** | **`enctype="multipart/form-data"`** — 파일의 **내용**이 부분으로 간다 |
| **봉투(상자 없음)** | **urlencoded · `text/plain`** — 파일 자리에 **이름만** 간다 |
| **여러 개 접수** | **`multiple`** — 같은 이름으로 **부분이 여러 개** |
| **빈 접수증** | 고른 파일이 없음 — 이름 빈 부분 하나([24번](../24-input-types-choice-special/2-summary.md)) |
| **「카메라로 찍어 오세요」 메모** | **`capture`** — 이 판의 Chrome 은 **읽지도 않았다**(IDL 이 없다) |

- ★★★ **거부된 칸 0 / 27** — `accept="image/png"`·`".png"`·`"image/*"` 칸 모두 **`.txt` 를 받았고 서버에 그대로 갔다.** 세 길 모두, `validity` 깃발도 **0 칸**((1)).
- ★★★ **urlencoded·`text/plain` 이면 파일 자리에 `p1.png` 라는 글자만 간다** — 본문 67 바이트는 **multipart 에서만**((2)).
- ★★ **끌어다 놓기로 파일 둘을 `multiple` 없는 칸에 놓으면 아무것도 안 들어갔다** — 스크립트 길(`setFileInputFiles`)은 **첫째 하나**를 넣었다((3)).
- ★★ **`capture` 는 `'capture' in HTMLInputElement.prototype` 이 `false`** — 데스크톱 Chrome 에 그 속성의 IDL 이 없다((3)).

```text
  파일 하나가 서버에 닿기까지 — 어디서도 accept 를 다시 보지 않는다 (이 판)

  사용자 ──(고르기 창 · 끌어다 놓기)──> 파일 칸 ──> 폼 제출 ──> 서버
             │ accept = 창의 힌트           │ files 목록       │ enctype 이 본문 모양을 정한다
             │ (창이 거르는지는 못 봤다)     │ validity 깃발 없음 │   multipart  → 이름 + 형식 + 내용
             └ 이 판: 창을 거치든 말든       └ 27 곳 모두 받음   │   urlencoded → 이름만 (f=p1.png)
               .txt 가 들어갔다                                  │   text/plain → 이름만
                                                                 └ 부분 Content-Type 은 이름의 확장자에서
```

> **파일 고르기 창(file picker)** — 파일 칸을 누르면 뜨는 운영체제 창. 명세의 「picker」.\
> 예: `accept="image/*"` 면 휴대폰은 카메라·사진첩을 먼저 보여 줄 수 **있다**(명세의 예시 문장 — 이 판은 못 본다).

## 이 주제가 답하려는 질문

1. **`accept` 는 무엇을 막나** — 고르기 창 · 끌어다 놓기 · 스크립트 길에서, 그리고 서버에서.
2. **파일이 서버에 「내용째」 가려면 무엇이 필요하나** — `enctype` 별로 무엇이 가나.
3. **`multiple`·`capture` 는 무엇을 바꾸나** — 창 · 목록 · 서버의 부분 수.

## 동작 방식

### (1) 창 ⑤ — `accept` 셋 × 파일 셋 × 넣는 길 셋

**언제 쓰나** — 「`accept="image/*"` 를 달았는데 PDF 가 올라왔다」·「확장자를 바꾼 파일이 통과했다」를 가를 때.

세 파일 — `p1.png`(진짜 PNG) · `t1.txt`(글자) · `t2.png`(**글자인데 이름만 `.png`**). 세 길 — `files`(CDP `DOM.setFileInputFiles`) · `drop`(CDP 끌어다 놓기) · `chooser`(진짜 마우스로 칸을 눌러 뜬 고르기 창에 넣기). 시도마다 세 칸에 **같은 파일**을 넣고 제출한다.

```html
<!-- html29b-31-accept.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 accept 와 넣는 길</title>
<script src="html29b-rec.js"></script>
<style>input[type=file] { display: block; width: 300px; height: 40px; margin: 6px; }</style>
</head>
<body>
<form id="폼" action="/r" method="post" enctype="multipart/form-data">
  <input type="file" id="a1" name="a1" accept="image/png">
  <input type="file" id="a2" name="a2" accept=".png">
  <input type="file" id="a3" name="a3" accept="image/*">
  <button id="보냄">보냄</button>
</form>
<script>
addEventListener("change", e => 적기("change(" + e.target.id + " · isTrusted=" + e.isTrusted + ")"), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 칸들 = ["a1", "a2", "a3"];
const 파일 = ["p1.png", "t1.txt", "t2.png"];
const 길 = ["files", "drop", "chooser"];
const 넣은뒤 = "['a1','a2','a3'].map(id => { const e = document.getElementById(id); return id + ':files=' + e.files.length + ',valid=' + e.validity.valid; }).join(' ')";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [];
for (const g of 길) for (const f of 파일) {
  const 단계 = 칸들.map(id => [g, "#" + id, [f]]);
  단계.push(["js", "(() => { 적기('넣은 뒤 ' + " + 넣은뒤 + "); return 1; })()"]);
  단계.push(["click", "#보냄"]);
  window.__시도.push({ 이름: g + " · " + f, 단계 });
}
window.__종합 = 결과 => {
  const O = [(칸("길 · 파일", 22) + 칸들.map(id => 칸(id + " " + document.getElementById(id).accept, 24)).join("")).trimEnd()];
  let 거부 = 0, 전체 = 0;
  for (const r of 결과) {
    const 서버 = r.서버.join("\n");
    let 행 = 칸(r.이름, 22);
    for (const id of 칸들) {
      const m = 서버.match(new RegExp(id + "=「[^」]*」 \\(filename=「([^」]*)」"));
      const 받음 = m && m[1] !== "";
      전체++; 거부 += !받음;
      행 += 칸(받음 ? "받음 " + m[1] : "— (빈 부분)", 24);
    }
    O.push(행.trimEnd());
  }
  const 무효 = 결과.map(r => (r.기록.find(x => x.startsWith("넣은 뒤")) || "").split(" ").filter(x => x.includes("valid=false")).length).reduce((a, b) => a + b, 0);
  const 변경 = 결과.map(r => r.기록.filter(x => x.startsWith("change(")).length).reduce((a, b) => a + b, 0);
  O.push("넣은 뒤 validity.valid 가 false 인 칸 = " + 무효 + " / " + 전체 + " · change 이벤트 = " + 변경 + "번 (isTrusted=true " + 결과.map(r => r.기록.filter(x => x.includes("isTrusted=true")).length).reduce((a, b) => a + b, 0) + "번)");
  O.push("거부된 칸 = " + 거부 + " / " + 전체 + "  (「받음 이름」= 서버가 받은 부분의 filename · 「— (빈 부분)」= 이름 빈 부분)");
  return O.join("\n");
};
</script>
</body>
</html>
```

한 시도의 전문(첫 시도) —

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

- ★★★ **거부된 칸 0 / 27** — `t1.txt` 도 `image/png`·`.png`·`image/*` 세 칸 모두에 **들어갔고 서버가 `filename=「t1.txt」` 로 받았다.** 세 길이 **한 칸도 다르지 않다.**
- ★★★ **`validity.valid` 가 `false` 인 칸도 0 / 27** — `accept` 에 맞지 않는 파일에 **깃발이 없다.** 명세의 File Upload 상태에 **`accept` 로 된 제약이 없다**(제약은 `required` 의 「고른 파일이 비었으면 missing」 하나뿐이다). **폼 검증으로도 못 막는다.**
- ★★ **`change` 는 27 번 모두 `isTrusted=true`** — 스크립트 길(`setFileInputFiles`)조차 **사용자 입력처럼** `change` 를 냈다. 페이지 쪽 코드는 **어느 길로 들어왔는지 가를 수 없다.**
- ★★ **고르기 창 길(`chooser`)도 거르지 않았다** — 진짜 클릭으로 창이 열렸고(`chooser(selectSingle)` — 한 시도의 전문), 창에 넣은 `.txt` 가 그대로 들어갔다. ★ **이것은 「실제 운영체제 창도 거르지 않는다」가 아니다** — 가로챈 창은 **목록을 보여 주지 않는다.** 명세의 「고르지 못하게 **해야 한다(should)**」는 **실제 창의 몫**이고, 이 판은 그것을 **못 본다.**
- ★ **끌어다 놓기가 거르지 않은 것** — 명세는 끌어다 놓기로 목록을 바꾸는 길을 적으면서 **거기서 `accept` 를 보라는 문장을 따로 두지 않는다.** 위 「should」가 끌어다 놓기에도 걸리는지는 문장이 가리지 않으므로 **이탈로 세지 않는다.**
- ★★ **`t2.png` 는 부분 `Content-Type: image/png` 로 갔다** — 내용은 `xyz\n` 글자다. **형식은 이름의 확장자에서 왔다**(이 판의 관찰 — 형식을 정하는 규칙은 [web-api 31번](../../../../web-api/31-blob-file-and-object-url/2-summary.md)의 `File` 쪽이다). **서버가 `Content-Type` 을 믿으면 안 되는 이유**가 이 한 줄이다.

```text
  accept 가 닿는 곳과 안 닿는 곳

  accept="image/png"    고르기 창에 힌트 ─> (실제 창의 필터 — 못 봤다)
                        칸 · validity   ─> 닿지 않는다   .txt 가 들어간다 · 깃발 없음
                        제출 · 서버      ─> 닿지 않는다   filename=t1.txt · Content-Type=text/plain
                        t2.png          ─> 이름이 .png 면 Content-Type 도 image/png (내용은 글자)
```

### (2) 창 ⑤ — 파일 칸이 있는 폼 × `enctype` 셋

**언제 쓰나** — 「파일을 올렸는데 서버에 파일 이름만 왔다」를 가를 때.

```html
<!-- html29b-31-enctype.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 enctype 과 파일</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r" method="post">
  <input name="t" value="가"><input type="file" id="갑파일" name="f"><button id="갑보냄">보냄</button>
</form>
<form id="을" action="/r" method="post" enctype="multipart/form-data">
  <input name="t" value="가"><input type="file" id="을파일" name="f"><button id="을보냄">보냄</button>
</form>
<form id="병" action="/r" method="post" enctype="text/plain">
  <input name="t" value="가"><input type="file" id="병파일" name="f"><button id="병보냄">보냄</button>
</form>
<script>
window.__시도 = [
  { 이름: "갑 · enctype 없음", 단계: [["files", "#갑파일", ["p1.png"]], ["click", "#갑보냄"]] },
  { 이름: "을 · multipart/form-data", 단계: [["files", "#을파일", ["p1.png"]], ["click", "#을보냄"]] },
  { 이름: "병 · text/plain", 단계: [["files", "#병파일", ["p1.png"]], ["click", "#병보냄"]] },
];
</script>
</body>
</html>
```

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

- ★★★ **`enctype` 이 없으면(urlencoded) `f=p1.png`** — 본문이 `「t=%EA%B0%80&f=p1.png」` 이고 **67 바이트는 한 바이트도 없다.** 명세의 「이름·값 쌍 목록으로 바꾸기」 — 「항목의 값이 **`File` 이면 그 `File` 의 이름**을 값으로」. urlencoded·`text/plain` 두 인코딩이 이 변환을 거친다.
- ★★★ **`multipart/form-data` 만 내용이 간다** — `f=「(바이트 67개)」 (filename=「p1.png」 · 부분 Content-Type: image/png)`. 명세 — 항목 목록을 RFC 7578 로 **그대로** 싸고, 글자 필드 부분에는 `Content-Type` 을 **붙이지 않는다**(`t` 줄에 없다).
- ★★ **`text/plain` 도 이름만** — `「t=가\r\nf=p1.png\r\n」`. (1) 의 변환을 같이 거친다.
- ★ **에러도 경고도 없다** — 세 폼 모두 제출이 됐다. 「파일이 안 올라왔다」는 **서버 쪽에서만** 드러난다. ★ GET 이면 `enctype` 을 아예 안 본다([21번](../21-form-submission-model/2-summary.md)의 「어디서 틀리나」 4) — **POST + multipart** 둘 다 있어야 한다.

```text
  같은 파일 칸 · 같은 파일 (p1.png 67 바이트) — 서버가 받은 f

  enctype 없음 (urlencoded)   f=p1.png                                   ← 이름만
  multipart/form-data         f=(67바이트) · filename=p1.png · image/png  ← 내용째
  text/plain                  f=p1.png                                   ← 이름만
```

### (3) 창 ⑤ + 창 ② — `multiple` · 파일 둘 · `capture`

**언제 쓰나** — 「여러 장을 올렸는데 하나만 왔다」·「`capture` 를 달았는데 데스크톱에서 아무 일도 없다」를 가를 때.

```html
<!-- html29b-31-multiple.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>31 multiple 과 capture</title>
<script src="html29b-rec.js"></script>
<style>input[type=file] { display: block; width: 300px; height: 40px; margin: 6px; }</style>
</head>
<body>
<form id="폼" action="/r" method="post" enctype="multipart/form-data">
  <input type="file" id="m1" name="m1" multiple>
  <input type="file" id="m2" name="m2">
  <input type="file" id="m3" name="m3" capture="user" accept="image/*">
  <input type="file" id="m4" name="m4" capture="zzz">
  <button id="보냄">보냄</button>
</form>
<script>
const 적어 = 식 => ["js", "(() => { 적기(" + 식 + "); return 1; })()"];
const 개수 = "['m1','m2','m3','m4'].map(id => id + '=' + document.getElementById(id).files.length).join(' ')";
window.__시도 = [
  { 이름: "chooser 로 m1 에 둘 · m2 에 하나", 단계: [["chooser", "#m1", ["p1.png", "t1.txt"]], ["chooser", "#m2", ["t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "setFileInputFiles 로 m2(multiple 없음)에 둘", 단계: [["files", "#m2", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "drop 으로 m2(multiple 없음)에 둘", 단계: [["drop", "#m2", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "drop 으로 m1(multiple)에 둘", 단계: [["drop", "#m1", ["p1.png", "t1.txt"]], 적어("'files.length ' + " + 개수), ["click", "#보냄"]] },
  { 이름: "capture 칸 m3·m4 를 chooser 로", 단계: [["chooser", "#m3", ["p1.png"]], ["chooser", "#m4", ["t1.txt"]],
    적어("'capture in HTMLInputElement.prototype=' + ('capture' in HTMLInputElement.prototype) + ' · capture IDL m3=' + String(document.getElementById('m3').capture) + ' m4=' + String(document.getElementById('m4').capture) + ' · getAttribute m3=' + document.getElementById('m3').getAttribute('capture') + ' · files.length ' + " + 개수), ["click", "#보냄"]] },
];
</script>
</body>
</html>
```

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

- ★★★ **`multiple` 은 고르기 창을 「여러 개」로 연다** — `m1` 을 누르니 **`chooser(selectMultiple)`**, `m2` 는 `selectSingle`. 파일 둘이 **`m1` 이름의 부분 둘**로 갔다(`부분 5개`). 명세 — 「같은 이름의 항목은 **별개의 필드**로 다룬다」.
- ★★★ **`multiple` 없는 칸에 파일 둘 — 길마다 다르다.** **`setFileInputFiles`** 는 **첫째(`p1.png`) 하나**를 넣었고, **끌어다 놓기**는 **아무것도 안 넣었다**(`m2=0` · 빈 부분). `multiple` 칸(`m1`)에 끌어다 놓으면 **둘 다** 들어갔다. 명세 — 「`multiple` 이 없으면 목록에 파일이 **하나를 넘으면 안 된다(must)**」. 두 길 다 그 문장을 지켰고, **지키는 방법**(자르기 · 통째 거절)이 달랐다.
- ★★ **고른 파일이 없는 칸은 빈 부분 하나씩** — `m3=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)`. [24번](../24-input-types-choice-special/2-summary.md)의 (2) 와 같고, `multiple` 칸(`m1`)도 **하나**다. 명세 — 「고른 파일이 없으면 **이름 빈 `File`**, 형식 `application/octet-stream`, 빈 본문으로 항목 하나」.
- ★★★ **`capture` 는 데스크톱 Chrome 에서 IDL 조차 없다** — `'capture' in HTMLInputElement.prototype` 이 **`false`** 이고 `m3.capture` 는 `undefined`, 속성 글자(`getAttribute`)만 `user` 로 남았다. 고르기 창도 `selectSingle` 로 **똑같이** 열렸다. ★ **이것은 「못 잰 것」과 다르다** — 휴대폰에서 카메라가 뜨나는 **못 쟀지만**, 이 판의 Chrome 이 **그 속성을 인식하지 않는다**는 것은 **잰 것**이다. 그리고 앞 머리말대로 **WHATWG HTML 에는 `capture` 가 없다.**

```text
  파일 둘을 넣는 세 길 × multiple (이 판)

                           multiple 있음 (m1)     multiple 없음 (m2)
  고르기 창 (chooser)      selectMultiple · 2     selectSingle (창이 하나만 받게 열린다)
  setFileInputFiles        (안 던졌다)            1  ← 첫째만
  끌어다 놓기 (drop)        2                      0  ← 통째 거절
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 파일을 내용째 올리기 | `<form method="post" enctype="multipart/form-data">` + `<input type="file" name="f">` | 둘 중 하나라도 빠지면 **이름만** 간다 |
| 고르기 창에 힌트 | `accept="image/png,.png"` | **막지 않는다** — 0 / 27 |
| 여러 개 | `multiple` | 같은 `name` 으로 부분이 여러 개 |
| 필수 | `required` | 고른 파일이 없을 때만 missing — **형식은 안 본다** |
| 카메라 | `capture="user"` | 이 판의 Chrome 은 IDL 이 없다 |

### 어디서 헷갈리나

- **`accept` 의 토큰은 다섯 꼴** — `audio/*` · `video/*` · `image/*` · 매개변수 없는 MIME · `.` 으로 시작하는 확장자. 쉼표로 가르고 중복을 두지 않는다.
- **`accept` 는 확장자와 MIME 을 같이 쓰라고 명세가 권한다** — 플랫폼마다 한쪽만 쓰기 때문이다.
- **부분 `Content-Type` 은 브라우저가 붙인다** — 이 판은 **이름의 확장자**에서 붙였다.

## 어디서 틀리나

### 1. `accept="image/*"` 로 이미지만 올라온다고 믿는다

**아무것도 안 막는다**((1) — 거부 0 / 27 · 깃발 0). 형식 검사는 **서버가 내용을 읽어서** 한다.

### 2. 서버가 부분의 `Content-Type` 을 믿는다

**이름만 바꾸면 바뀐다**((1) — 글자 파일 `t2.png` 가 `image/png` 로 갔다).

### 3. `enctype` 을 빼고 파일 칸을 둔다

**파일 이름 글자만 간다**((2) — `f=p1.png`). 에러가 없어서 **서버 로그를 봐야** 안다.

### 4. `multiple` 없는 칸에 끌어다 놓은 파일 여러 개 중 하나는 들어갈 거라 여긴다

**하나도 안 들어갔다**((3) — `m2=0`). 여러 개를 받으려면 `multiple`.

### 5. 「파일 필드가 왔으니 파일을 올렸다」

**고르지 않아도 부분 하나가 온다**((3) — `filename=「」`) · [24번](../24-input-types-choice-special/2-summary.md)의 5 와 같다. **`filename` 이 빈지** 본다.

### 6. 데스크톱에서 `capture` 를 달면 웹캠이 뜰 거라 여긴다

**이 판의 Chrome 은 그 속성을 모른다**((3) — IDL 없음 · 고르기 창 그대로).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `accept` — 힌트 · 「받지 않는 파일을 고르지 못하게 **해야 한다(should)**」 · **제약(깃발)은 없다** | (1) |
| **명세(HTML)** | 이름·값 쌍으로 바꿀 때 `File` → **그 이름** · urlencoded·`text/plain` 이 이 변환을 쓴다 | (2) |
| **명세(HTML)** | multipart — RFC 7578 · 같은 이름은 별개 필드 · 글자 필드엔 `Content-Type` 없음 | (2)·(3) |
| **명세(HTML)** | `multiple` 이 없으면 파일은 **하나 이하(must)** · 고른 파일이 없으면 이름 빈 `File`·`application/octet-stream` | (3) |
| **명세(HTML)** | 파일 이름에 **경로 성분이 없어야 한다** | (1) — 서버가 받은 `filename` 이 전부 이름뿐 |
| **명세 없음** | **`capture`** — WHATWG HTML 에 없다(W3C HTML Media Capture — 이 배치는 안 열었다) | (3) |
| **구현(Chrome)** | 스크립트 길의 둘 → 첫째만 · 끌어다 놓기의 둘 → 통째 거절 · 부분 형식을 **이름의 확장자**에서 · 데스크톱에 `capture` IDL 없음 · 스크립트 길도 `change` 가 `isTrusted=true` | (1)·(3) |
| **이 판의 관찰** | 거부된 칸 **0 / 27** · 깃발 0 / 27 | (1) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **운영체제 고르기 창이 `accept` 로 목록을 거르나** | headless 에서는 창이 뜨지 않는다 — 가로채면 CDP 이벤트만 온다. 명세의 should 가 지켜지는지는 **실제 창의 몫** |
| ★★ **휴대폰에서 `capture`·`accept="image/*"` 가 카메라를 띄우나** | 모바일 기기가 없다 — 「못 잰 것」 |
| **실제 끌어다 놓기와 CDP 의 흉내가 같은가** | CDP 가 브라우저 안에서 끌기 이벤트를 합성한다 — 운영체제의 끌기와 같은 길인지는 이 판이 가를 수 없다 |
| **큰 파일 · 진행률** | 이 판의 파일은 67 바이트 이하다 |

## 언제 쓰고 언제 안 쓰나

- **`accept`** — 사용자를 **돕는** 힌트로 쓴다(맞는 파일을 먼저 보여 주게). **검사로 쓰지 않는다.** 확장자와 MIME 을 **같이** 적는다.
- **`multipart/form-data`** — 파일 칸이 있으면 **언제나** + `method="post"`.
- **`multiple`** — 여러 개를 받을 때. 서버는 **같은 이름의 부분 여러 개**를 받을 준비를 한다.
- **서버** — 이름·`Content-Type` 을 믿지 않고 **내용을 읽어** 형식을 가른다 · `filename` 이 빈 부분은 「안 올림」으로 읽는다.
- **`capture`** — 모바일 전용 힌트로만. 데스크톱의 웹캠이 필요하면 스크립트 API 쪽이다(이 목록 밖).

## 핵심 문장

1. **`accept` 는 고르기 창에 주는 힌트다 — 칸도 폼 검증도 서버도 다시 보지 않는다(이 판: 거부 0 / 27 · 깃발 0).**
2. **파일의 내용은 `method="post"` + `enctype="multipart/form-data"` 일 때만 간다 — urlencoded·`text/plain` 이면 파일 이름 글자만 간다.**
3. **부분의 `Content-Type` 은 이 판에서 이름의 확장자가 정했다 — 서버가 믿을 것이 못 된다.**
4. **`multiple` 이 없으면 칸은 파일 하나까지다 — 스크립트 길은 첫째만, 끌어다 놓기는 통째로 거절했다.**
5. **고른 파일이 없는 칸도 이름 빈 부분 하나를 보낸다.**
6. **`capture` 는 WHATWG HTML 의 속성이 아니고, 이 판의 데스크톱 Chrome 은 IDL 조차 없다.**

## 관련 자료

- [21번 주제](../21-form-submission-model/2-summary.md) — `method` × `enctype` 여섯 칸의 정본 · GET 은 `enctype` 을 안 본다.
- [24번 주제](../24-input-types-choice-special/2-summary.md) — 고른 파일이 없는 파일 칸(urlencoded `f1=` · multipart `filename=「」`) · 파일 칸의 역할.
- [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md) — ★ **스크립트로 같은 본문을 만드는 쪽**. (3) 이 `FormData` 에 넣은 `Blob`·`File` 의 `filename`·`Content-Type` 이 어디서 오나를 잰다. 여기는 **마크업의 칸**이 만드는 쪽이다.
- [web-api 31번](../../../../web-api/31-blob-file-and-object-url/2-summary.md) — ★ **받은 `File` 을 다루는 쪽**(미리보기 · 올리기 · 오브젝트 URL). 여기는 `File` 이 **칸에 들어오기까지**와 **폼이 보내는 것**까지.
- [29번 주제](../29-constraint-validation/2-summary.md) — 제약 검증 · 서버 검증을 대체 못 한다 · 파일 칸의 제약은 `required` 하나.

## 용어 풀이

- **파일 고르기 창(picker)** — 파일 칸을 누르면 뜨는 창. 명세는 File Upload 칸이 반드시 지원하라고 한다.
- **고른 파일 목록(selected files)** — 칸이 들고 있는 `File` 들. `input.files`.
- **항목 목록(entry list)** — 제출할 이름·값의 목록. 값이 글자 또는 `File`.
- **이름·값 쌍으로 바꾸기** — urlencoded·`text/plain` 용 변환. `File` 은 이름이 된다.
- **부분(part)** — multipart 본문의 한 칸. `Content-Disposition` 에 `name`·`filename`.
- **`isTrusted`** — 이벤트를 브라우저가 냈나(DOM 의 정의). 이 편은 `true` 인 쪽만 봤다 — 스크립트 길(`setFileInputFiles`)도 브라우저가 `change` 를 낸다.
- **HTML Media Capture** — `capture` 를 정의한 W3C 문서. 이 배치는 열지 않았다.

## 더 들어가면

- **왜 `accept` 가 must 가 아니라 should 인가** — 명세의 예시가 답에 가깝다 — 확장자만 쓰는 플랫폼과 MIME 만 쓰는 플랫폼이 있어서 **UA 가 정확히 거를 수 없는 경우**가 있다(「확장자는 모호하다」는 문장이 이어진다). 그래서 명세는 **작성자에게 둘 다 적으라고** 권한다(해석이다).
- **`webkitdirectory`** — 폴더째 고르기. 명세 밖의 속성이다. 이 판은 던지지 않았다.
- **폼 제출 대신 `fetch`** — 같은 multipart 본문을 스크립트로 만드는 쪽은 [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md)의 (4).
