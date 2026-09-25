# html/syntax/01 — HTML 문서의 뼈대: `<!DOCTYPE html>`·`<html lang>`·`<head>`/`<body>` 의 필수 요소 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 이 갈래에서 답할 때는 **「화면이 어떻게 보이나」가 아니라 「`--dump-dom` 이 무엇을 뱉나」까지** 말한다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 파일 전체가 글자 두 개일 때 (예측)

```html
<!-- html01b-min.html -->
안녕
```

- 이 파일을 `--dump-dom` 으로 던지면 트리에 노드가 몇 개 있는가?
- 그중 내가 타자한 것은 몇 개인가?
- `document.body` 는 존재하는가?
- 그래서 「필수 요소」라는 말은 무엇을 필수라고 하는 것인가?

### 2. 첫 줄 하나를 지우면 (예측)

```html
<!-- html01b-mode-on.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>모드 스위치</title>
<style>#u { width: 200; height: 40; }</style>
</head>
<body>
<div id="u">단위 없는 길이</div>
<script>
const o = [];
const u = document.getElementById("u");
o.push("document.compatMode      = " + document.compatMode);
o.push("document.doctype         = " + (document.doctype ? document.doctype.name : "null"));
o.push("documentElement.lang     = " + JSON.stringify(document.documentElement.lang));
o.push("#u 계산 width            = " + getComputedStyle(u).width);
o.push("#u 계산 height           = " + getComputedStyle(u).height);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
```

- 위 파일에서 **첫 줄만** 지운 판과 그대로인 판이 있다. 두 판에서 갈리는 값 세 가지를 대라.
- `#u` 의 계산된 `width` 는 각각 얼마인가?
- 트리에서 사라지는 **노드**는 무엇인가?
- 「호환 모드면 박스 모델이 옛날 것으로 바뀐다」는 이 판에서 재현되는가?

### 3. 이 문서의 제목은 무엇인가 (예측)

```html
<!-- html01b-no-title.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<p>제목 요소가 없는 문서</p>
<script>
const o = [];
o.push("document.title           = " + JSON.stringify(document.title));
o.push("head 의 자식 요소         = " + [...document.head.children].map(e => e.localName).join(", "));
o.push("querySelector('title')   = " + document.querySelector("title"));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
```

- `document.title` 과 `document.querySelector("title")` 은 각각 무엇을 돌려주는가?
- 파서는 이 문서에 대해 무엇을 알려 주는가?
- 이것과 앞 질문의 `html`·`head`·`body` 는 무엇이 다른가?
- 「파서가 안 고쳤다」와 「유효하다」는 같은 말인가?

### 4. `<head>` 안에 글자를 한 줄 흘리면 (예측)

```html
<!-- html01b-head-text.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>head 안의 텍스트</title>
여기는 head 안에 쓴 글자다
<meta name="author" content="나">
<link rel="canonical" href="/a">
</head>
<body>
<p>본문</p>
</body>
</html>
```

- 트리에서 `head` 의 자식 요소 목록을 예측하라.
- `<meta name="author">` 와 `<link rel="canonical">` 은 어디에 들어가는가?
- 내가 `</head>` 를 제대로 썼는데도 그렇게 되는 이유는 무엇인가?
- 같은 사고를 내는 다른 입력을 둘 대라.

### 5. 「필수 요소」와 「필수 태그」 (경계)

- 이 둘이 다른 말인 이유를 한 문장으로 답하라.
- `body` 요소와 `<body>` 태그 중 어느 쪽이 필수인가?
- 파서가 만들어 주는 것과 만들어 주지 않는 것을 각각 두 개씩 대라.
- 「생략해도 되는 것」을 생략하면 누가 손해를 보는가?

### 6. DOCTYPE 이 노드인 이유 (왜)

- `document.doctype` 이 `null` 일 수 있다는 것은 무엇을 뜻하는가?
- `<!DOCTYPE html>` 의 `html` 은 무엇의 이름인가?
- 오늘 이 선언이 하는 일을 한 가지로 줄이면 무엇인가?
- 옛 `PUBLIC` 꼴이 갈랐던 세 모드 중 `document.compatMode` 로 구분되지 않는 짝은 무엇인가?

### 7. `<meta charset>` 을 1,252바이트째에 두면 (경계)

- 명세가 말하는 **1024바이트**는 무엇의 한계인가?
- 그 뒤에 둔 선언은 이 판에서 먹었는가, 안 먹었는가?
- 먹었다면 브라우저는 무엇을 더 했는가?
- 선언을 아예 빼면 이 환경에서 무슨 일이 일어나고, 그것을 근거로 쓸 수 있는가?

### 8. validator 가 없을 때 (왜)

- 이 환경에는 마크업 검증기가 없다. 그 자리를 무엇으로 대신하는가?
- 「파서가 고쳤다」가 알려 주는 것과 알려 주지 못하는 것은 각각 무엇인가?
- 그 한계를 보여 주는 이 주제의 사례 하나를 들어라.
- CSS 갈래가 쓰는 「진단 3창」에 대응하는 이 갈래의 창 넷을 대라.

### 9. `lang` 이 넘겨주는 것 (경계)

- `<html lang="ko">` 한 줄이 영향을 주는 곳을 셋 대라.
- 그중 이 환경에서 **확인할 수 없는** 것은 무엇이고 왜인가?
- `lang` 을 조각마다 다시 쓰지 않아도 되는 이유는?
- 「확인 못 했다」를 문서에 어떻게 적어야 하는가?

### 10. 다른 갈래와 잇기 (연결)

- CSS 파서와 HTML 파서는 모르는 것을 만났을 때 각각 무엇을 하는가?
- 둘 다 에러를 안 던지는데 결과가 정반대인 이유를 한 문장으로 답하라.
- HTML 명세가 다른 언어 명세와 다른 점 하나를 대라. 그것이 「구현 정의」 칸에 무엇을 하는가?
- 뼈대가 저절로 생기는 성질이 **위험해지는** 자리는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
