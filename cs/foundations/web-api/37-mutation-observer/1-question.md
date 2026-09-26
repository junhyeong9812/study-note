# web-api/37 — `MutationObserver`: 관측 옵션 · 레코드 묶음 · 마이크로태스크 타이밍 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 노드를 넣고 옮기는 법은 [03번 주제](../03-node-creation-insertion-removal/1-question.md), 조각과 레코드 수는 [05번 주제](../05-documentfragment-and-template/1-question.md), 마이크로태스크 줄 자체는 [JS 갈래 36번](../../languages/js/syntax/36-event-loop-and-microtasks/1-question.md)이 물었다. 여기는 **MO 가 언제 · 무엇을 묶어 오나**와 **옵션이 무엇을 가르나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이고, 규칙은 **DOM 명세 §4.3 을 받아 읽어** 맞대었다. **비용은 재지 않았다.**
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 동기 블록의 변경 다섯 번 (예측)

```js
// wa36b-37-q1.js
// 질문용 — 실행 대상 아님
const mo = new MutationObserver(rs => 적기(`MO 콜백 · 레코드 ${rs.length}개`));
mo.observe(host, { childList: true, attributes: true });
setTimeout(() => 적기("setTimeout"), 0);
host.setAttribute("data-k", "1"); host.append(i()); host.setAttribute("data-k", "3"); host.append(i()); host.setAttribute("data-k", "5");
적기("동기 끝");
// 적히는 순서와 콜백 수 · 레코드 수는?
```

- 순서 · 콜백 수 · 레코드 수는?

### 2. `then` 을 거는 자리 셋 (예측)

```js
// wa36b-37-q2.js
// 질문용 — 실행 대상 아님 (문항 1 과 같은 관찰자 · 같은 다섯 변경)
// (가) Promise.resolve().then(() => 적기("then")) 을 첫 변경 「전」에 건다
// (나) 다섯 변경을 다 한 「뒤」에 건다
// (다) 첫 변경 뒤 · 둘째 변경 전에 건다
// 판마다 then 과 MO 콜백 중 어느 쪽이 먼저 적히나? (다) 에서 MO 가 받는 레코드는 몇 개인가?
```

- 판마다 `then` 과 MO 콜백의 순서는?

### 3. 옵션과 변경의 짝 넷 (예측)

```js
// wa36b-37-q3.js
// 질문용 — 실행 대상 아님
// 나무: host(data-a="1" data-b="1") > [ 글 "처음" , child(data-a="1") > 글 "처음" ]  — 관찰 대상은 host
// 옵션 (가) { characterData: true }        변경: host 의 글을 바꾼다 (host.firstChild.data = "나중")
// 옵션 (나) { attributes: true }           변경: child 의 data-a 를 바꾼다
// 옵션 (다) { attributeFilter: ["data-a"] } 변경: host 의 data-b 를 바꾼다
// 옵션 (라) { attributeOldValue: true }    변경: host 의 data-a 를 "2" 로
// 각각 — 레코드가 오나? (라) 의 oldValue 는?
```

- (가)\~(라) 각각 레코드가 오나?

### 4. 옵션을 어디까지 빼도 되나 (경계)

- `observe(host)` · `observe(host, {})` · `observe(host, { subtree: true })` 는 각각 무엇을 하나? `{ attributeOldValue: true }` 만 준 것과 `{ attributes: false, attributeOldValue: true }` 는 왜 다르게 끝나나?

### 5. 콜백이 오기 전에 큐를 건드리면 (예측)

```js
// wa36b-37-q5.js
// 질문용 — 실행 대상 아님
// (가) 속성을 두 번 바꾼 뒤, 콜백이 오기 전에 mo.takeRecords() — 꺼낸 레코드 수와 그 뒤의 콜백 횟수는?
// (나) 이미 "같음" 인 속성에 setAttribute("y", "같음") — { attributes, attributeOldValue } 로 관찰 중
// (다) 속성을 한 번 바꾸고 콜백 전에 mo.disconnect() — 콜백은? 그 뒤 takeRecords() 는?
```

- (가)\~(다) 각각은?

### 6. 대입 한 번 · 이동 한 번의 레코드 (예측)

```js
// wa36b-37-q6.js
// 질문용 — 실행 대상 아님
// 자식이 둘 있는 요소를 { childList: true } 로 관찰하고 한 번씩:
a.textContent = "하나";                          // (가)
a.innerHTML = "<i></i><i></i><i></i>";           // (나)
a.append(i(), i(), i());                         // (다)
// (라) body 를 { childList, subtree } 로 관찰하고 a 의 자식 하나를 b.append(그 자식) 으로 옮긴다
// 각각 — 레코드 몇 개 · 레코드마다 제거 몇 · 추가 몇?
```

- (가)\~(라) 각각 레코드 몇 개 · 무엇을 담나?

### 7. 남의 스크립트가 넣은 `.ad` (예측)

```js
// wa36b-37-q7.js
// 질문용 — 실행 대상 아님
// slot 을 { childList: true, subtree: true } 로 관찰 중. 「남의 스크립트」가 한 태스크에서:
slot.innerHTML = '<section><div class="ad">①</div></section>';
slot.append(div(".ad", "②"));
const 셋 = div(".ad", "③"); slot.append(셋); 셋.remove();
// 콜백 한 번에서 — (가) addedNodes 중 matches(".ad") 인 것 · (나) 거기에 추가된 요소 안 querySelectorAll(".ad") 를 더한 것
//                  (다) (나) 중 isConnected 인 것 — 각각 몇 개 · 어느 것?
```

- (가)\~(다) 각각 몇 개 · 어느 것?

### 8. 알림 마이크로태스크를 거는 규칙 (왜)

- DOM 명세의 「queue a mutation observer microtask」는 **이미 걸려 있을 때** 무엇을 하나? 그 규칙이 문항 1 의 콜백 수와 문항 2 (다)의 순서를 어떻게 정하나?

### 9. 옛 Mutation events 와 무엇이 다른가 (경계)

- 변경마다 **그 자리에서 동기로** 알리는 방식과 비교해 MO 가 얻는 것과 잃는 것은 각각 무엇인가(문항 1 · 5 의 결과로)?

### 10. 다른 주제와 잇기 (연결)

- [03번 주제](../03-node-creation-insertion-removal/1-question.md)의 「삽입이 곧 이동」은 MO 에게 몇 개의 사건으로 보이나 — 문항 6 의 어느 줄이 근거인가?
- [05번 주제](../05-documentfragment-and-template/1-question.md)의 「조각 한 번 = 레코드 1개」와 문항 6 의 (나)는 같은 성질의 어느 두 얼굴인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
