# web-api/06 — 속성(attribute) 대 성질(property): `getAttribute`/`setAttribute` 와 IDL 프로퍼티의 반영 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이 주제에는 흔들리는 칸이 없다.** 수치를 재지 않으므로 **답은 전부 한 글자까지 고정**이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 다만 이 주제의 결론은 **명세가 속성마다 못 박은 계약**이라 이식성보다 계약을 먼저 읽는다.
> ★ 선행은 [01번 주제](../01-document-and-node-tree/2-summary.md)와 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**([요소와 속성 문법](../../languages/html/syntax/02-elements-and-attributes/2-summary.md))이다. 「속성이 트리에 어떤 글자로 담기는지」는 안다고 본다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 칸을 양쪽에서 써 보면 (예측)

```js
el.getAttribute('id')
el.setAttribute('id', 'b2');   el.id
el.id = 'c3';                  el.getAttribute('id')
el.removeAttribute('id');      // 두 창구에 각각 물으면?
```

- 처음 세 줄에서 두 창구의 대답이 갈리는 줄이 있는가?
- 마지막 줄 뒤 `getAttribute('id')` 와 `el.id` 는 각각 무엇인가?
- 이 꼴에 드는 속성을 셋 더 대라.
- 이 꼴에서 두 표면 중 무엇을 써야 하는가?

### 2. 이름이 다른 둘 (예측)

```js
el.class            //  ?
el.className        //  ?
label.for           //  ?
label.htmlFor       //  ?
```

- 네 줄의 결과를 각각 예측하라.
- 첫째·셋째 줄이 **예외가 아닌** 이유는 무엇인가?
- 이름이 갈린 이유는 무엇인가?
- 이 꼴에 드는 것이 **둘뿐**인가?

### 3. 세 칸을 나란히 두면 (예측)

```js
// <input id="in" value="초기"> 를 form 안에 두고
inp.setAttribute('value', 'A');
inp.value = 'B';
inp.setAttribute('value', 'C');
form.reset();
```

- 네 단계마다 `getAttribute('value')` · `.value` · `.defaultValue` 세 칸을 적어라.
- **어느 줄에서** 두 칸이 갈라지는가?
- 갈라진 뒤에 다시 이어 붙이는 방법이 있는가?
- `value` 속성을 **반영하는** 성질은 무엇인가?

### 4. 체크박스를 속성으로 켜면 (예측)

```js
// <input id="ck" type="checkbox" checked>
ck.click();
ck.setAttribute('checked', 'checked');
ck.checked = true;  ck.removeAttribute('checked');
```

- 세 단계마다 `getAttribute('checked')` · `.checked` · `.defaultChecked` 를 적어라.
- `click()` 한 번으로 속성이 바뀌는가?
- 두 번째 줄로 체크가 **켜지는가**?
- `checked="false"` 라고 쓰면 어떻게 되는가?

### 5. 같은 `href` 를 두 창구로 (예측)

```html
<base href="https://example.org/a/b/">
<a id="lk" href="sub/page.html?q=1#n">링크</a>
```

```js
lk.getAttribute('href')
lk.href
lk.href = '../up.html';   // 그 뒤 속성과 프로퍼티는?
```

- 앞의 두 줄의 결과를 각각 적어라.
- 셋째 줄 뒤에 **왕복이 맞는가**?
- `lk.protocol`·`pathname`·`search`·`hash` 는 무엇을 돌려주는가?
- 원문이 필요한 경우와 절대 URL 이 필요한 경우를 각각 하나씩 들어라.

### 6. 없는 것을 물으면 (예측)

```js
const b = document.createElement('div');
b.getAttribute('id')        b.id
b.getAttribute('tabindex')  b.tabIndex
b.getAttribute('hidden')    b.hidden
b.getAttribute('data-x')    b.dataset.x
```

- 여덟 칸을 각각 적어라.
- **속성 쪽 대답은 몇 가지인가?** 성질 쪽은?
- `if (el.getAttribute('title') === '')` 는 언제 참이 되는가?
- 「있는지 없는지」를 물으려면 무엇을 써야 하는가?

### 7. `value` 가 반영이 아닌 이유 (왜)

- 명세가 이것을 「버그」가 아니라 **설계**로 두는 이유를 사용자 입장에서 한 문장으로 적어라.
- 명세가 그 상태에 붙인 **이름**은 무엇인가?
- 만약 `value` 가 양방향 반영이었다면 어떤 일이 벌어지는가?
- 같은 설계가 걸린 성질을 `value`·`checked` 말고 하나 더 들어라.

### 8. 배선이 없거나 이상한 이름 (경계)

```js
d.dataUserId                            // <div data-user-id="7">
d.foo = 1;        d.getAttribute('foo')
d.setAttribute('bar', '2');   d.bar
inp.setAttribute('type', 'bogus');   inp.type
inp.setAttribute('maxlength', '-3'); inp.maxLength
d.setAttribute('CLASS', 'q');  d.className
```

- 여섯 줄의 결과를 각각 예측하라.
- 넷째·다섯째 줄에서 **속성과 프로퍼티가 영영 어긋나는** 이유는 무엇인가?
- 둘째·셋째 줄에 **에러가 없는 것**이 왜 위험한가?
- 여섯째 줄에서 대문자가 어디로 갔는가? 그 규칙의 정본은 어느 갈래인가?

### 9. 성질에만 있는 것은 어디까지 따라오나 (경계)

```js
inp.value = '사용자가 친 것';  ck.click();
copy.innerHTML = fm.innerHTML;
const c2 = fm.cloneNode(true);
const c3 = document.importNode(fm, true);
```

- 세 복사본의 `input.value` 와 `checkbox.checked` 를 각각 적어라.
- **어느 경로만** 상태를 잃는가? 그 이유를 한 문장으로.
- 잃지 않는 쪽은 **구현의 친절인가 명세의 계약인가**?
- `--dump-dom` 으로 그 문서를 찍으면 무엇이 보이는가?

### 10. 다른 주제와 잇기 (연결)

- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 `innerHTML` 과 이 주제의 창 ④ 가 만나는 자리를 한 문장으로 적어라.
- [05번 주제](../05-documentfragment-and-template/2-summary.md)의 `cloneNode`·`importNode` 에 이 주제가 무엇을 덧붙였는가?
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 「라이브 컬렉션」이 이 주제의 어느 표면에 그대로 걸리는가?
- [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)가 이 주제에서 **넘겨받는 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
