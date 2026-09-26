# web-api/38 — `requestAnimationFrame` 과 프레임 예산 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — `--virtual-time-budget` 없이 **실제 시간**으로 돌렸고, 페이지는 같은 기계의 로컬 서버(A)에서 열었다.\
> ★ 명세는 **HTML(update the rendering · animation frames)** 과 **W3C Intersection Observer** 를 받아 읽었다. **시간은 찍지 않았다** — 간격은 범주, 나머지는 순서 · 참/거짓 · 횟수다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.** 헤드리스에는 모니터가 없다.

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 위치 로그 두 판 · 간격 격자 25칸 · 숨김 · timestamp 두 줄 · `LayoutCount` 12칸 | ★ **판에 매일 수 있는 칸** — 간격 범주(실제 시간 — 경계에서 먼 조건을 골랐다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 실제 화면의 주사율 · ms 예산 · 합성 스레드 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 태스크 끝 → scroll → rAF → (스타일 · 레이아웃) → RO → (페인트) → IO — 나에서는 레이아웃이 태스크로

**출력**

```text
$ python3 wa36b-net.py page wa36b-38-order.html
가 쓰기만	ScrollLayer → ⟨태스크 끝⟩ → EventDispatch(scroll) → ⟨scroll⟩ → EventDispatch(scrollend) → FireAnimationFrame → ⟨rAF⟩ → UpdateLayoutTree → Layout → PrePaint → IntersectionObserverController::computeIntersections → ⟨ResizeObserver⟩ → PrePaint → IntersectionObserverController::computeIntersections → Paint → IntersectionObserverController::computeIntersections → ⟨IntersectionObserver⟩
나 쓰고 곧바로 읽기	ScrollLayer → UpdateLayoutTree → Layout → ⟨offsetWidth=140⟩ → ⟨태스크 끝⟩ → EventDispatch(scroll) → ⟨scroll⟩ → EventDispatch(scrollend) → FireAnimationFrame → ⟨rAF⟩ → PrePaint → IntersectionObserverController::computeIntersections → ⟨ResizeObserver⟩ → PrePaint → IntersectionObserverController::computeIntersections → Paint → IntersectionObserverController::computeIntersections → ⟨IntersectionObserver⟩
(exit 0)
```

**왜 그런가**

- **판 가** — `⟨태스크 끝⟩ → ⟨scroll⟩ → FireAnimationFrame → ⟨rAF⟩ → UpdateLayoutTree → Layout → … → ⟨ResizeObserver⟩ → … → Paint → … → ⟨IntersectionObserver⟩`. HTML update the rendering 의 순서(scroll 단계 → rAF → 스타일 · 레이아웃과 RO 반복 → IO 갱신 → 그리기) 그대로다.
- **판 나** — `UpdateLayoutTree → Layout` 이 **`⟨offsetWidth=140⟩` 앞, 태스크 안**으로 옮겨 갔고 렌더링 단계에서는 사라졌다. 읽기가 레이아웃을 **당겨 왔다.**

### 2. 0 · 10 · 20 → `≈1` · 30 → `≈2` · 100 → `≥5`

**출력**

```text
$ python3 wa36b-net.py page wa36b-38-gap.html | sed -n '1,6p'
조건	판1	판2	판3	판4	판5
보통	≈1	≈1	≈1	≈1	≈1
콜백 안에서 10ms 바쁨	≈1	≈1	≈1	≈1	≈1
콜백 안에서 20ms 바쁨	≈1	≈1	≈1	≈1	≈1
콜백 안에서 30ms 바쁨	≈2	≈2	≈2	≈2	≈2
콜백 안에서 100ms 바쁨	≥5	≥5	≥5	≥5	≥5
(exit 0)
```

**왜 그런가**

- 콜백이 길어지면 **다음 틀이 그만큼 늦게** 온다 — 예산을 넘긴 증상은 **간격의 증가**로 보인다. 다섯 판 다 같았다.
- **20ms 가 `≈1`** — 16.7ms 보다 길게 붙들었는데 간격이 25ms 미만이었다. 이 헤드리스는 **다음 틀을 16.7 배수로 맞춰 미루지 않았다.** 실제 화면에서의 모양은 못 쟀다.

### 3. (가) 0번 · (나) 같다 · (다) 더 크다(다음 틀)

**출력**

```text
$ python3 wa36b-net.py page wa36b-38-gap.html | sed -n '7,$p'
탭 숨김	보일 때 200ms 동안 rAF 가 돌았나 = true · 숨긴 뒤 visibilityState = hidden · 숨긴 동안(setInterval 100ms 세 번) rAF 호출 = 0번 · 되돌린 뒤 200ms 동안 돌았나 = true
한 태스크에서 건 rAF 둘이 같은 timestamp 를 받았나 = true
rAF 안에서 건 rAF 가 더 큰 timestamp 를 받았나 = true
(exit 0)
```

**왜 그런가**

- **(가)** 숨긴 동안 rAF **0번** — 그동안 `setInterval` 은 세 번 울렸다. 되돌리자 다시 돌았다.
- **(나)** 한 틀의 rAF 들은 **같은 틀 시각**을 받는다.
- **(다)** 안에서 건 rAF 는 **다음 틀**이다(A6).

### 4. +20 · +1 · +1 · 0

**출력**

```text
$ python3 wa36b-net.py page wa36b-38-layout.html
가 쓰기·읽기 20번 교차	LayoutCount 증가(세 번) = 20 · 20 · 20
나 쓰기 20번 → 읽기 1번	LayoutCount 증가(세 번) = 1 · 1 · 1
다 쓰기 20번 → 다음 틀	LayoutCount 증가(세 번) = 1 · 1 · 1
라 아무것도 안 함	LayoutCount 증가(세 번) = 0 · 0 · 0
(exit 0)
```

**왜 그런가**

- **교차(가)는 읽기마다 레이아웃** — 20번 쓰고 20번 읽으니 +20.
- **(나) 모아 쓰고 한 번 읽기 · (다) 쓰기만 하고 틀에 맡기기 — 둘 다 +1.** 다는 **틀의 렌더링 단계**가 한 번 돌린 것이다(A1 의 판 가). 나는 **태스크 안**에서 한 번이다(A1 의 판 나).
- **(라) 0** — 계수기는 헛돌지 않았다(대조).

### 5. 「Filter non-renderable documents」 — 타이머는 렌더링 단계 밖이다

- update the rendering 첫머리가 「**Remove from docs any Document object doc for which … doc's visibility state is "hidden"**」이다. rAF 콜백을 부르는 단계는 그 **뒤**에 있으므로 숨은 문서는 **그 단계까지 오지 않는다.**
- `setInterval` 은 **타이머 태스크**다 — 렌더링 단계와 무관하게 이벤트 루프가 돌린다.

### 6. 시작할 때의 핸들 목록 — 마이크로태스크는 「빌 때까지」

- 「run the animation frame callbacks」는 **먼저 `callbackHandles` = 지금 있는 핸들의 목록**을 받아 두고 그것만 돈다. 콜백 안에서 건 rAF 는 **그 목록에 없어** 다음 틀로 간다.
- JS 36편 (2)의 체크포인트는 「**While the event loop's microtask queue is not empty**」 — 도중에 붙은 것까지 **같은 비우기**에서 돈다. 그래서 마이크로태스크를 이어 걸면 렌더링이 굶고(목록의 **40번 주제**), rAF 를 이어 걸면 **틀마다 한 번**이다.

### 7. 강제하지 않는다 — 60Hz 는 예다

- 명세 — 「**This specification does not mandate any particular model for selecting rendering opportunities.**」 60Hz 면 약 16.7ms · 못 따라가면 30 · 안 보이면 4 또는 그 이하는 **예시**다.
- **잰 것** — 바쁨이 길어지면 간격 범주가 옮는다(A2) · 숨으면 0 번(A3). **20ms 가 `≈1`** 은 「**이 헤드리스가 16.7 배수로 맞추지 않았다**」까지만 말한다 — 몇 fps 인지 · 실제 화면에서 어떤지는 말하지 않는다.

### 8. 가상 시간은 간격이 가짜다 · 한 판의 ms 는 근거가 아니다

- **가상 시간**에서는 브라우저가 시계를 **건너뛰며** 돌린다 — 틀 간격이 실제가 아니다. 이 편의 주제가 바로 그 간격이다.
- **ms 대신 범주** — 한 판의 절댓값은 기계 부하에 흔들린다(가이드 규칙 24). 「16.7 의 몇 배 근처」로 접으면 **다섯 판 · 세 캡처가 같았다.**
- **헤드리스라서 못 잰 것** — 모니터 주사율에 묶인 실제 틀 · 틀 떨굼 · 합성 스레드의 일.

### 9. `--dump-dom` 이 틀을 못 기다렸다 → `LayoutCount` 로 +20 대 +1

- 10편 (7)은 **`--dump-dom`** 으로 돌려 **판마다 rAF 가 0\~2번**만 불렸다 — 두 틀짜리 실험이 서지 않았다.
- 이 편은 CDP 로 **실제 시간의 틀**을 기다리며 **`LayoutCount`** 를 셌다 — 교차 **+20**, 틀에 맡기기 **+1**(A4).
- **말하지 않는 것** — **시간**(한 번의 레이아웃이 얼마나 걸리나)과 **나 · 다의 비용 차이**. 횟수는 같고 **자리만** 다르다.

### 10. scroll 뒤 rAF · rAF 뒤 RO · 페인트 뒤 IO — IO 알림은 태스크다

- 35편의 `scroll → rAF → IO` 는 A1 의 `⟨scroll⟩ → ⟨rAF⟩ → … → ⟨IntersectionObserver⟩` 와 같은 줄이다.
- 36편의 「틀 번호는 rAF 가 올린다」 — rAF 가 **RO 보다 앞**(`⟨rAF⟩ → UpdateLayoutTree → Layout → … → ⟨ResizeObserver⟩`)이라 성립한다.
- **IO 알림이 페인트 뒤** — 교차 계산은 틀 안에서 했지만 명세가 알림을 **「Queue a task on the IntersectionObserver task source」** 로 건다. 그래서 **다음 태스크**에서 불렸다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--window-size=1000,800` · 실제 시간) · Python 3 표준 라이브러리 `http.server`(서버 A). **엔진은 Chrome 하나다.**

★ **하네스** — [36번 주제](../36-resize-observer/3-answer.md)의 `wa36b-net.py` — 부탁 창구로 `Tracing`(`devtools.timeline`, 렌더러 주 스레드의 두 표지 사이만) · `Performance.getMetrics` · `Target.createTarget`(새 탭)을 불렀다.

```sh
# wa36b-38-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa36b-net.py page wa36b-38-order.html
python3 wa36b-net.py page wa36b-38-gap.html
python3 wa36b-net.py page wa36b-38-layout.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 위치 로그 두 판 | 캡처 3판 | 동작 방식 (1) · A1 · A10 |
| 간격 격자 5조건 × 5판 | 캡처 3판 | 동작 방식 (2) · A2 · A7 · A8 |
| 숨김 · timestamp | 캡처 3판 | 동작 방식 (3) · A3 · A5 · A6 |
| `LayoutCount` 4모양 × 3번 | 캡처 3판 | 동작 방식 (5) · A4 · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 바쁨 20ms 의 간격 범주 | `≈1` | 헤드리스의 박자 — 헤드풀 · 판이 바뀌면 달라질 수 있다 |
| Tracing 이벤트 이름 | `FireAnimationFrame` · `UpdateLayoutTree` · `Layout` · `PrePaint` · `Paint` · `IntersectionObserverController::computeIntersections` | 구현의 이름 — 판이 오르면 바뀔 수 있다 |
| `scrollend` 가 같은 틀 | 난다 | CSSOM View 를 받지 않았다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 실제 화면(헤드풀 · 모니터). ③ ms 예산. ④ 숨은 탭의 긴 경향.
