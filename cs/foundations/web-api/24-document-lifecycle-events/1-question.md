# web-api/24 — 문서 수명주기 이벤트: `DOMContentLoaded`/`load`·`visibilitychange`·`pagehide`/`pageshow` 와 bfcache — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `defer`·`async`·모듈과 `DOMContentLoaded` 의 순서는 [HTML 08번 주제](../../languages/html/syntax/08-script-loading/1-question.md)가 정본이다. 여기는 **떠날 때와 돌아올 때**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 HTML 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 링크를 눌러 떠나기 (예측)

```js
// wa24b-24-q1.js
// 질문용 — 실행 대상 아님
// 첫쪽에 beforeunload · pagehide · visibilitychange · pageshow · load 리스너(unload 는 안 달았다)
// 첫쪽의 링크를 진짜 마우스로 눌러 둘째쪽으로 간다
// 떠나는 첫쪽이 받는 것은? pagehide 의 persisted 는? 도착한 둘째쪽의 pageshow persisted 와 load 는?
```

- 떠나는 첫쪽이 받는 이벤트를 순서대로 적어라. `pagehide` 의 `persisted` 는?
- 도착한 둘째쪽의 `pageshow` 와 `load` 는?

### 2. 뒤로 돌아오기 (예측)

```js
// wa24b-24-q2.js
// 질문용 — 실행 대상 아님
// 첫쪽 → (링크) → 둘째쪽 → 뒤로(Page.navigateToHistoryEntry)
// 떠나는 둘째쪽이 받는 이벤트를 순서대로? 돌아온 첫쪽이 받는 이벤트를 순서대로?
// 돌아온 첫쪽에서 load 가 다시 나나?
```

- 떠나는 둘째쪽과 돌아온 첫쪽이 받는 이벤트를 각각 순서대로 적어라.
- 돌아온 첫쪽에서 `load` 는?

### 3. `unload` 리스너 한 줄 (예측)

```js
// wa24b-24-q3.js
// 질문용 — 실행 대상 아님
// 첫쪽에 한 줄을 더한다
addEventListener("unload", () => 적기("unload"));
// 같은 여정(첫쪽 → 둘째쪽 → 뒤로 · 그다음 앞으로)에서
// 두 쪽의 pagehide persisted 와 pageshow persisted 는? CDP 의 Page.backForwardCacheNotUsed 는 무엇을 말하나?
// 페이지 쪽 performance.getEntriesByType("navigation")[0].notRestoredReasons 는?
```

- 두 쪽의 `persisted` 는 어떻게 바뀌나?
- CDP 와 페이지는 이유를 각각 무엇이라고 말하나?

### 4. 탭을 닫는 두 방법 (예측)

```js
// wa24b-24-q4.js
// 질문용 — 실행 대상 아님
// 첫쪽 탭을 두 방법으로 닫는다 — CDP Target.closeTarget · CDP Page.close
// 각각 beforeunload · pagehide · visibilitychange 가 나나? unload 리스너가 있으면 unload 는?
```

- 두 방법의 이벤트 칸을 채워라. 어느 칸이 갈리나?

### 5. 다른 탭이 앞으로 오면 (예측)

```js
// wa24b-24-q5.js
// 질문용 — 실행 대상 아님
// 첫쪽 탭이 있는 상태에서 새 탭을 하나 연다(Target.createTarget) — 그다음 첫쪽 탭을 다시 앞으로(Target.activateTarget)
// 첫쪽은 무엇을 받나? pagehide 는?
```

- 첫쪽이 받는 것은? 돌아올 때는?

### 6. 서버가 이미지를 붙잡으면 (예측)

```js
// wa24b-24-q6.js
// 질문용 — 실행 대상 아님
// <head> 의 평범한 스크립트 · <script defer> · <img>(서버는 페이지가 /go 를 줄 때까지 이미지를 안 준다)
// DOMContentLoaded 리스너가 /go 를 준다 · img 의 load · window 의 load
// 줄의 순서와 각 줄의 readyState 는? DOMContentLoaded 때 이미지 complete 는?
```

- 다섯 줄의 순서와 `readyState` 를 적어라.

### 7. 「떠날 때」는 어느 이벤트로 잡나 (왜)

- 이 편의 격자에서 **모든 떠남과 탭 가림에서** 난 열은 무엇인가? `pagehide`·`beforeunload`·`unload` 는 각각 어느 줄에서 빠졌나?

### 8. bfcache 에 못 들어가는 조건은 누가 정하나 (경계)

- HTML 명세가 정하는 것과 Chrome 이 정하는 것을 갈라라. `no-store` 와 `Permissions-Policy: unload=()` 는 이 판에서 어땠나?

### 9. 되살아난 페이지 (경계)

- 「초기화는 `load` 에서」라는 코드가 되살아난 페이지에서 무엇을 놓치나? 대신 무엇을 보나?

### 10. 다른 주제와 잇기 (연결)

- [HTML 08번 주제](../../languages/html/syntax/08-script-loading/1-question.md)가 잰 순서와 문항 6은 어디서 만나나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라 — 왜 못 보나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
