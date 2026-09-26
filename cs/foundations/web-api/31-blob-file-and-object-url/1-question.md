# web-api/31 — `Blob`·`File`·`FileReader` 와 오브젝트 URL: 미리보기·업로드·저장 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `FormData` 의 파일 칸 규칙은 [30번 주제](../30-request-body-and-content-type/1-question.md), bfcache 는 [24번 주제](../24-document-lifecycle-events/1-question.md)가 물었다. 마크업 쪽 파일 입력(`accept`·`multiple`)은 **HTML 갈래 31번**(폴더는 아직 없다)이다. 여기는 **파일을 넘기는 길**과 **오브젝트 URL 이 언제까지 읽히나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 File API·Fetch 명세 문장이다. **메모리는 재지 않았다.** 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 파일 입력의 `File` (예측)

```js
// wa28b-31-q1.js
// 질문용 — 실행 대상 아님
// 파일 입력에 73바이트 PNG(3×2) 하나를 넣었다 — CDP DOM.setFileInputFiles
const f = document.querySelector("input").files[0];
f instanceof File; f instanceof Blob; f.name; f.size; f.type;
f.slice(0, 8);                                       // 무엇이 돌아오나 — 그 size 는?
new Uint8Array(await f.slice(0, 8).arrayBuffer());   // 바이트는?
```

- 각 값은? `slice` 가 돌려주는 것의 종류는?

### 2. 미리보기 둘 (예측)

```js
// wa28b-31-q2.js
// 질문용 — 실행 대상 아님
const url = URL.createObjectURL(f);          // 모양은? (무엇으로 시작하고, 뒤에 몇 글자?)
img.src = url;                               // load 인가 error 인가 — naturalWidth×naturalHeight 는?
const fr = new FileReader();
for (const t of ["loadstart", "progress", "load", "loadend"]) fr.addEventListener(t, () => 적기(t));
fr.readAsDataURL(f);
적기("(readAsDataURL 이 돌아옴 · readyState=" + fr.readyState + ")");
// 적히는 순서는? 결과는 무엇으로 시작하나?
```

- URL 의 모양 · `<img>` 결과 · 적히는 순서 · 결과의 앞부분은?

### 3. 올리기 둘 (예측)

```js
// wa28b-31-q3.js
// 질문용 — 실행 대상 아님
const fd = new FormData(); fd.append("f", f);
await fetch("/echo?id=u1", { method: "POST", body: fd });
await fetch("/echo?id=u2", { method: "POST", body: f });
// 서버가 받은 Content-Type 과 바이트 수는 각각? 두 번째가 받은 바이트는 원본과 같은가?
```

- 서버가 받은 두 요청의 `Content-Type` · 바이트 수 · 파일 칸 머리는?

### 4. 풀기 전과 뒤 (예측)

```js
// wa28b-31-q4.js
// 질문용 — 실행 대상 아님
const u2 = URL.createObjectURL(f);
await fetch(u2);                 // 풀기 전
URL.revokeObjectURL(u2);
await fetch(u2);                 // 푼 뒤
img.src = u2;                    // 푼 뒤 — load 인가 error 인가
URL.revokeObjectURL(u2); URL.revokeObjectURL("blob:" + location.origin + "/없는-것"); URL.revokeObjectURL("아무 글자");
// 각 줄의 결과는? 마지막 줄은 예외를 던지나?
```

- 각 줄의 결과는?

### 5. 풀지 않은 URL 을 다른 문서가 (예측)

```js
// wa28b-31-q5.js
// 질문용 — 실행 대상 아님
// 첫 탭(출처 A)이 만든 뒤 풀지 않은 URL 하나를 — 다른 문서가 fetch(url) 한다
//   ① 같은 출처 A 의 다른 탭  ② 다른 출처 B 의 탭
//   ③ 첫 탭이 다른 문서로 떠난 뒤 ①   (그리고 첫 탭에서 뒤로 — 스크립트 상태가 남아 있나?)
//   ④ 첫 탭을 닫은 뒤 ①
//   ⑤ unload 리스너를 단 넷째 탭이 만든 URL — 그 탭이 떠나기 전 · 떠난 뒤 ①
// 각각 then 인가 catch 인가?
```

- 다섯 자리(와 뒤로 가기)의 결과를 적어라.

### 6. `<a download>` 로 저장 (예측)

```js
// wa28b-31-q6.js
// 질문용 — 실행 대상 아님
// 풀지 않은 그 URL 로 저장 — CDP Browser.setDownloadBehavior({ behavior: "allow", … })
const a = document.createElement("a"); a.href = url; a.download = "wa28b-31-saved.png";
document.body.append(a); a.click();
// 떨어진 파일의 이름과 크기는? 원본과 바이트가 같은가?
```

- 떨어진 파일의 이름 · 크기 · 원본과 같은가?

### 7. blob URL 을 장부에서 지우는 때 (왜)

- File API 명세는 blob URL 을 **언제** 지우나? 문항 5의 ③과 ⑤는 무엇이 갈랐나?

### 8. 「`revokeObjectURL` 을 안 하면 무엇이 남나」 (경계)

- 이 편이 **관찰한 것**과 **관찰하지 않은 것**을 갈라 답하라.

### 9. `FileReader` 대 `blob.text()` · 데이터 URL 대 오브젝트 URL (경계)

- 결과가 같은데 무엇이 다른가? 미리보기를 다른 출처에 넘겨야 하면 어느 쪽인가?

### 10. 다른 주제와 잇기 (연결)

- [30번 주제](../30-request-body-and-content-type/1-question.md) 문항 3의 `f.append("b", new Blob(["x"]))` 와 이 편의 `fd.append("f", f)` 는 원문의 `filename` 이 어떻게 다른가?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
