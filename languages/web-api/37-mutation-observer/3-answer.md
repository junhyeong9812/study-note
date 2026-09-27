# web-api/37 — `MutationObserver`: 관측 옵션 · 레코드 묶음 · 마이크로태스크 타이밍 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 페이지는 같은 기계의 로컬 서버(A)에서 열었고 **바깥 인터넷으로는 요청하지 않았다.**\
> ★ 규칙은 **WHATWG DOM §4.3 을 받아 읽어** 맞대었다 — 이 편의 관찰은 명세 알고리즘과 **전부 맞았다.** **비용은 재지 않았다.**\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 묶음 로그 · 옵션 격자 63칸 · `TypeError` · 가장자리 · 남의 노드 — 시간을 하나도 안 찍는다 | **못 잰 것** — 비용 · 렌더링과의 순서(40번) · 그림자 트리 |
| 캡처를 세 판 돌려 **한 글자도 같았다** | |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 동기 끝 → MO 콜백 1번(레코드 5개) → setTimeout

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-batch.html
가 then → 변경 5번	동기 끝 → then → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → setTimeout
나 변경 5번 → then	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
다 변경 → then → 변경 4번	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
(exit 0)
```

**왜 그런가**

- **나 줄이 문항 1 그대로다** — `동기 끝 → MO 콜백(레코드 5개 …) → then → setTimeout`(문항 1 에는 `then` 이 없다). 레코드 다섯의 `type` 은 **바꾼 순서 그대로**다.
- 변경마다 즉시 오지 않는다 — **동기 코드가 끝난 뒤의 마이크로태스크 한 번**에 묶여 온다. `setTimeout` 은 태스크라 **맨 뒤**다.

### 2. (가) then → MO · (나) MO → then · (다) MO → then, 레코드 5개

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-batch.html
가 then → 변경 5번	동기 끝 → then → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → setTimeout
나 변경 5번 → then	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
다 변경 → then → 변경 4번	동기 끝 → MO 콜백(레코드 5개: attributes,childList,attributes,childList,attributes) → then → setTimeout
(exit 0)
```

**왜 그런가**

- **알림 마이크로태스크는 첫 변경 때 줄에 선다.** (가)는 `then` 이 먼저 섰고, (나)·(다)는 첫 변경이 먼저 섰다.
- **(다)의 MO 가 레코드 5개**인 것 — 둘째 이후의 변경은 **줄에 새로 서지 않고 레코드만 보탰다**(A8).

### 3. (가) 안 온다 · (나) 안 온다 · (다) 안 온다 · (라) 온다 — `old=1`

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-grid.html
옵션	host 에 자식 붙임	child 에 자식 붙임	host data-a	host data-b	child data-a	host 의 글 바꿈	child 의 글 바꿈
{childList}	○	—	—	—	—	—	—
{attributes}	—	—	○	○	—	—	—
{characterData}	—	—	—	—	—	—	—
{childList, subtree}	○	○	—	—	—	—	—
{attributes, subtree}	—	—	○	○	○	—	—
{characterData, subtree}	—	—	—	—	—	○	○
{attributeOldValue}	—	—	○ old=1	○ old=1	—	—	—
{attributeFilter:[data-a]}	—	—	○	—	—	—	—
{attributeFilter:[data-a], subtree}	—	—	○	—	○	—	—
레코드가 온 칸 = 15 / 63
subtree 가 바꾼 칸 = 5 / 28
(exit 0)
```

**왜 그런가**

- **(가) `{characterData}` + host 의 글 — `—`.** 바뀐 것은 host 가 아니라 **host 의 자식 텍스트 노드**다. `{characterData, subtree}` 줄은 `○`.
- **(나) `{attributes}` + child 의 속성 — `—`.** 자손은 **`subtree`** 가 있어야 한다(`{attributes, subtree}` 는 `○`).
- **(다) `{attributeFilter:[data-a]}` + host 의 `data-b` — `—`**(걸러졌다). 필터만 줘도 `attributes` 가 채워져 `data-a` 는 온다.
- **(라) `{attributeOldValue}` + host 의 `data-a` — `○ old=1`.** 격자 전체는 **레코드가 온 칸 15 / 63 · subtree 가 바꾼 칸 5 / 28**.

### 4. 앞의 셋은 같은 `TypeError` — `attributeOldValue` 만은 통과

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-bad.html
observe(host)	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {subtree: true})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object must set at least one of 'attributes', 'characterData', or 'childList' to true.
observe(host, {attributes: false, attributeOldValue: true})	TypeError: Failed to execute 'observe' on 'MutationObserver': The options object may only set 'attributeOldValue' to true when 'attributes' is true or not present.
observe(host, {attributeOldValue: true})	던지지 않음
(exit 0)
```

**왜 그런가**

- **`childList` · `attributes` · `characterData` 중 하나는 참**이어야 한다 — 옵션 없음 · `{}` · `{subtree}` 셋 다 같은 문구로 던졌다. `subtree` 는 **범위**라서 혼자서는 무엇을 볼지 말하지 않는다.
- **`{attributeOldValue: true}` 만** — 명세가 먼저 `attributes` 를 **참으로 채우고** 검사하므로 통과한다. **`attributes: false` 를 명시하면** 채우기가 안 일어나 둘째 검사에서 던진다.

### 5. (가) 2개 · 콜백 0번 · (나) 레코드 1개(`oldValue=같음`) · (다) 콜백 0번 · 0개

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-edge.html
[1] 변경 2번 → 콜백 전에 takeRecords()	꺼낸 레코드 2개 · 그 뒤 콜백 0번
[2] 이미 "같음" 인 속성에 "같음" 을 다시 씀	레코드 1개 · oldValue=같음 · 지금 값=같음
[3] 변경 1번 → 콜백 전에 disconnect()	콜백 0번 · 그 뒤 takeRecords() 0개
[4] 자식 둘 있는 요소에 textContent 대입	레코드 1개 · (제거 2 · 추가 1)
[4] 자식 둘 있는 요소에 innerHTML 대입(요소 셋)	레코드 1개 · (제거 2 · 추가 3)
[4] 자식 둘 있는 요소에 append 로 요소 셋	레코드 1개 · (제거 0 · 추가 3)
[5] a 의 자식을 b 에 append(이동)	레코드 2개 · (a 에서 제거 1 · 추가 0) (b 에서 제거 0 · 추가 1)
(exit 0)
```

**왜 그런가**

- **[1]** 알림 마이크로태스크는 돌지만 **큐가 비어 콜백을 안 불렀다**(「If records is not empty」).
- **[2]** 「change an attribute」에는 **값 비교가 없다** — 같은 값도 레코드.
- **[3]** **`disconnect()` 가 레코드 큐를 비운다** — 끊기 전에 `takeRecords()` 를 불러야 남는다.

### 6. (가)·(나)·(다) 각 1개 · (라) 2개

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-edge.html | sed -n '4,$p'
[4] 자식 둘 있는 요소에 textContent 대입	레코드 1개 · (제거 2 · 추가 1)
[4] 자식 둘 있는 요소에 innerHTML 대입(요소 셋)	레코드 1개 · (제거 2 · 추가 3)
[4] 자식 둘 있는 요소에 append 로 요소 셋	레코드 1개 · (제거 0 · 추가 3)
[5] a 의 자식을 b 에 append(이동)	레코드 2개 · (a 에서 제거 1 · 추가 0) (b 에서 제거 0 · 추가 1)
(exit 0)
```

**왜 그런가**

- **(가) `textContent` — 1개(제거 2 · 추가 1)** · **(나) `innerHTML` — 1개(제거 2 · 추가 3)** · **(다) `append` 셋 — 1개(추가 3)**. 레코드는 **트리를 바꾼 한 번**의 기록이다.
- **(라) 이동 — 2개**: `a 에서 제거 1` · `b 에서 추가 1`.

### 7. (가) 2개(②③) · (나) 3개(①②③) · (다) 2개(①②)

**출력**

```text
$ python3 wa36b-net.py page wa36b-37-watch.html
레코드 4개 · 추가된 요소 3개
가 addedNodes 에서 matches(".ad")	2개 (②③)
나 가 + 추가된 요소 안을 querySelectorAll(".ad")	3개 (①②③)
다 나 중 isConnected 인 것만	2개 (①②)
(exit 0)
```

**왜 그런가**

- **(가)** `addedNodes` 에는 **맨 위 노드**만 있다 — `section` 안의 ①을 놓쳤다.
- **(나)** 안까지 찾으면 ①이 잡히지만, **이미 빠진 ③도 잡힌다** — 레코드는 사건의 기록이다.
- **(다)** `isConnected` 로 **지금 붙은 것만** — ①②. 이 세 단계가 「남의 노드에 반응하기」의 형태다(설계 권고층).

### 8. 「queue a mutation observer microtask」의 「이미 걸려 있으면 돌아간다」

- DOM 명세 — 「**If the surrounding agent's mutation observer microtask queued is true, then return.**」 변경마다 레코드는 **각 관찰자의 큐에 쌓이지만**, 알림 마이크로태스크는 **처음 한 번만** 건다. 알림이 돌 때 깃발을 내리고 큐를 통째로 건넨다.
- 그래서 **(다)에서 MO 의 자리는 첫 변경이 정했다** — 둘째 변경 앞에 건 `then` 보다 앞이다.

### 9. 얻는 것 — 묶음 · 잃는 것 — 「그 자리에서」

- **얻는 것** — 변경 다섯 번에 콜백 **한 번**(A1). 변경하는 코드가 **도중에 끊기지 않는다** — 관찰 코드가 동기 코드 한가운데서 끼어들지 않는다.
- **잃는 것** — **그 순간의 상태**. 콜백이 올 때는 이미 **다음 변경까지 끝난 뒤**다 — A7 의 ③처럼 **넣었다 뺀 노드**가 레코드에만 남는다. 필요하면 `oldValue` 로 그때 값을 받는다.
- ★ 옛 Mutation events 는 **던지지 않았다** — 이 답은 MO 쪽 관찰에서 읽은 대비다.

### 10. 두 사건 — 제거 + 추가 · 「트리를 바꾼 한 번」의 두 얼굴

- **03편의 이동은 MO 에게 레코드 2개**다 — A5 의 `[5]` 줄: `(a 에서 제거 1 · 추가 0) (b 에서 제거 0 · 추가 1)`.
- **05편의 조각 한 번 = 레코드 1개**와 **(나) `innerHTML` 대입 = 레코드 1개(추가 3)** 는 같은 성질이다 — 레코드는 **노드 수가 아니라 트리를 바꾼 횟수**를 센다. 조각은 **넣는 쪽**에서, `innerHTML` 은 **갈아 끼우는 쪽**에서 그 성질이 드러난다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · Python 3 표준 라이브러리 `http.server`(서버 A). **엔진은 Chrome 하나다.**

★ **하네스** — [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py`(`page` 모드).

```sh
# wa36b-37-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa36b-net.py page wa36b-37-batch.html
python3 wa36b-net.py page wa36b-37-grid.html
python3 wa36b-net.py page wa36b-37-bad.html
python3 wa36b-net.py page wa36b-37-edge.html
python3 wa36b-net.py page wa36b-37-watch.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 묶음 · 타이밍 세 판 | 캡처 3판 | 동작 방식 (1) · A1 · A2 · A8 |
| 옵션 격자 63칸 | 캡처 3판 | 동작 방식 (2) · A3 |
| 잘못된 옵션 다섯 판 | 캡처 3판 | 동작 방식 (3) · A4 |
| 가장자리 일곱 | 캡처 3판 | 동작 방식 (4)·(5) · A5 · A6 · A10 |
| 남의 노드 세 방식 | 캡처 3판 | 동작 방식 (6) · A7 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `TypeError` 문구 | Chrome 의 문구 | 명세는 「throw a TypeError」까지만 정한다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 비용. ③ 그림자 트리 · `slotchange` · 옛 Mutation events. ④ 렌더링과의 순서(목록의 **40번 주제**).
