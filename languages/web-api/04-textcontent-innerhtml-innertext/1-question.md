# web-api/04 — `textContent` 대 `innerHTML` 대 `innerText`: 파싱·비용·XSS — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 비용을 묻는 문항에서는 **숫자를 외우지 마라.** 이 주제의 수치는 흔들린다 — **자릿수와 순위**만 답하면 된다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 특히 `innerText` 는 엔진 차이가 남아 있을 수 있는 자리다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 셋을 나란히 읽으면 (예측)

```html
<div id="box">
  <p>보이는 문단</p>
  <p style="display: none">숨은 문단</p>
  <span hidden>hidden 속성</span>
  <style>.z { color: red }</style>
  <p>줄<br>바꿈<span style="text-transform: uppercase">abc</span></p>
</div>
```

- `box.textContent`·`box.innerText`·`box.innerHTML` 이 각각 무엇을 주는지 적어라.
- `<style>` 안의 글자는 셋 중 어디에 나오는가?
- `<br>` 과 `text-transform: uppercase` 는 각각 어느 쪽에 어떻게 반영되는가?
- 셋 중 소스의 들여쓰기 공백이 보이는 것은 무엇인가?

### 2. 안 보이는 요소에서 읽으면 (예측)

```js
const p2 = box.querySelectorAll('p')[1];   // style="display: none"
p2.textContent
p2.innerText
box.cloneNode(true).innerText
```

- 세 줄의 결과를 각각 예측하라.
- 부모를 통해 읽을 때와 그 요소 자신으로 읽을 때가 갈리는 이유는 무엇인가?
- 문서에서 떼어낸 복제본에서 읽으면 무엇과 같아지는가?
- 이 성질이 테스트에서 만드는 함정은 무엇인가?

### 3. 잘못된 마크업을 넣으면 (예측)

```js
div.innerHTML = '<p>가<div>나</div>';
div.innerHTML = '<b><i>가</b>나</i>';
div.innerHTML = '<td>셀</td>';
table.innerHTML = '<tr><td>셀';
```

- 네 줄 뒤 각각을 다시 읽으면 무엇이 나오는가?
- 세 번째와 네 번째가 갈리는 이유는 무엇인가?
- 이 규칙의 정본은 어느 갈래이고, 이 주제는 어디까지 다루는가?
- 같은 모양을 `appendChild` 로 만들면 결과가 어떻게 다른가?

### 4. 위험한 문자열을 넣으면 (예측)

```js
const payload = '<script>A()<\/script>'
              + '<img src="data:image/gif;base64,zzz" onerror="B()">'
              + '<svg onload="C()"></svg>';
viaHTML.innerHTML = payload;
viaText.textContent = payload;
```

- `A`·`B`·`C` 는 각각 몇 번 불리는가?
- `viaHTML` 의 자식 요소는 몇 개이고 태그는 무엇인가?
- 안 불린 것이 있다면 그 노드는 트리에 **있는가**?
- 그 `<script>` 노드를 다른 부모로 옮기면 실행되는가? `createElement('script')` 로 만든 것은?

### 5. 셋으로 같은 문자열을 쓰면 (예측)

```js
const s = '한 줄\n다음 줄 <b>굵게</b>';
a.textContent = s;
b.innerText = s;
c.innerHTML = s;
```

- 셋의 `innerHTML` 을 다시 읽으면 각각 무엇인가?
- 셋의 `children.length` 와 `childNodes.length` 는 각각 몇인가?
- 셋 중 요소를 하나도 안 만드는 것은 무엇이고, 그것이 왜 중요한가?
- `c.textContent = ''` 뒤에 원래 있던 노드는 어떻게 되는가?

### 6. 비용 (예측)

```js
// 2000개 항목을 네 방식으로 만든다
for (…) host.innerHTML += '<span>…</span>';
let s = ''; for (…) s += '<span>…</span>'; host.innerHTML = s;
for (…) host.appendChild(만든span());
const f = frag(); for (…) f.appendChild(만든span()); host.appendChild(f);
```

- 네 방식의 **자릿수 순위**를 매겨라. 혼자 크게 다른 것은 무엇이고 왜인가?
- 읽기에서 `textContent`·`innerHTML`·`innerText` 의 순위는 어떻게 되는가?
- `innerText` 읽기만 큰 이유는 무엇인가?
- 측정값이 `0.00 ms` 로 나온 칸은 무슨 뜻인가?

### 7. 「렌더에 의존한다」는 말의 뜻 (왜)

- `innerText` 가 답하기 위해 먼저 끝나야 하는 단계는 무엇인가?
- CSS 를 바꾸면 같은 트리에서 답이 바뀌는 예를 들어라.
- 명세는 「렌더되지 않는 요소」에 대해 무엇이라고 정하는가?
- 텍스트를 비교·검색하는 코드에서 `innerText` 를 피하라는 이유는 무엇인가?

### 8. `<script>` 를 막으면 안전한가 (경계)

- 실측에서 `<script>` 가 안 돈 것은 **명세의 어떤 규정** 때문인가?
- 같은 문자열에서 실제로 돈 것은 무엇이었나?
- 「태그 하나만 걸러내면 된다」가 왜 틀렸는지 **면적**이라는 말로 설명하라.
- `insertAdjacentHTML` 은 `innerHTML` 보다 안전한가?

### 9. 안전하게 쓰는 법 (경계)

- XSS 면적을 0 으로 만드는 한 줄은 무엇인가?
- 마크업이 꼭 필요할 때 이 문서가 권하지 **않는** 방법은 무엇인가?
- `Trusted Types`·Sanitizer API 를 이 문서가 대안으로 확정하지 않은 이유는 무엇인가?
- 자식을 비울 때 `innerHTML = ''` 대신 무엇을 쓰고 왜인가?

### 10. 다른 주제와 잇기 (연결)

- `innerHTML` 로 영역을 통째로 갈면 [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 라이브 컬렉션과 정적 스냅샷은 각각 어떻게 되는가?
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 `appendChild` 와 여기의 `innerHTML` 은 **무엇을 검사하느냐**에서 어떻게 갈리는가?
- `innerText` 읽기가 [목록의 **10번 주제**](../10-layout-thrashing/)(레이아웃 스래싱)의 씨앗이 되는 이유는 무엇인가?
- 이 문서가 「`DocumentFragment` 가 빠르다」를 **주장하지 않은** 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
