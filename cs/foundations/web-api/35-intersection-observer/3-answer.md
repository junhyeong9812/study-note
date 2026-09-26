# web-api/35 — `IntersectionObserver`: 루트·`rootMargin`·`threshold` 와 지연 로딩 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 페이지와 iframe 은 같은 기계의 로컬 서버(A·B)에서 열었고 **바깥 인터넷으로는 요청하지 않았다.** 명령은 블록마다 배너로 실려 있다.\
> ★ **명세 원문(W3C Intersection Observer)은 이 판에서 열지 못했다** — 「왜 그런가」는 관찰에서 읽은 것이고, 명세대로인지 판정하지 않는다. **비용은 재지 않았다.**\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 교차 격자 168칸 · 가장자리 넷 · 순서 · overflow 상자 · iframe · 노출 집계 | ★ **판에 매일 수 있는 칸** — 휠 한 번의 `scroll` 호출 수(61 · 61 · 60 — 대소만 근거) · `innerHeight` 713 |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 비용 · 탭 가림 · 진짜 손가락 스크롤 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 온다 — `isIntersecting: false` · `intersectionRatio: 0`

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-grid.html
뷰포트 높이 innerHeight = 713
threshold	rootMargin	크기	관찰 시작	아래 300 밖	아래 100 밖	위 100 들어옴	바닥에서 50 위까지	맨 위에 붙음	위로 100 지나감
0	0px	작음 200	F 0.00	—	—	T 0.50	—	—	F 0.00
0	0px	큼 1200	F 0.00	—	—	T 0.08	—	—	F 0.00
0	200px	작음 200	F 0.00	—	T 0.50	—	—	—	—
0	200px	큼 1200	F 0.00	—	T 0.08	—	—	—	—
0	-50px	작음 200	F 0.00	—	—	T 0.21	—	—	F 0.00
0	-50px	큼 1200	F 0.00	—	—	T 0.03	—	—	F 0.00
0.5	0px	작음 200	F 0.00	—	—	T 0.50	—	—	F 0.00
0.5	0px	큼 1200	F 0.00	—	—	—	T 0.55	—	F 0.00
0.5	200px	작음 200	F 0.00	—	T 0.50	—	—	—	—
0.5	200px	큼 1200	F 0.00	—	—	—	T 0.72	—	F 0.08
0.5	-50px	작음 200	F 0.00	—	—	—	T 0.83	—	F 0.00
0.5	-50px	큼 1200	F 0.00	—	—	—	—	—	—
1	0px	작음 200	F 0.00	—	—	—	T 1.00	—	F 0.00
1	0px	큼 1200	F 0.00	—	—	—	—	—	—
1	200px	작음 200	F 0.00	—	—	T 1.00	—	—	F 0.50
1	200px	큼 1200	F 0.00	—	—	—	—	—	—
1	-50px	작음 200	F 0.00	—	—	—	—	—	—
1	-50px	큼 1200	F 0.00	—	—	—	—	—	—
[0,.25,.5,.75,1]	0px	작음 200	F 0.00	—	—	T 0.50	T 1.00	—	F 0.00
[0,.25,.5,.75,1]	0px	큼 1200	F 0.00	—	—	T 0.08	T 0.55	—	F 0.00
[0,.25,.5,.75,1]	200px	작음 200	F 0.00	—	T 0.50	T 1.00	—	—	T 0.50
[0,.25,.5,.75,1]	200px	큼 1200	F 0.00	—	T 0.08	T 0.25	T 0.72	T 0.76	T 0.08
[0,.25,.5,.75,1]	-50px	작음 200	F 0.00	—	—	T 0.21	T 0.83	T 0.63	F 0.00
[0,.25,.5,.75,1]	-50px	큼 1200	F 0.00	—	—	T 0.03	T 0.43	—	F 0.00
콜백이 온 칸 = 68 / 168
rootMargin 200px 이 0px 과 다른 칸 = 23 / 56
rootMargin -50px 이 0px 과 다른 칸 = 13 / 56
큰 요소 · threshold 1 — 관찰 시작 뒤 콜백이 온 칸 = 0 / 18
(exit 0)
```

**왜 그런가**

- **`관찰 시작` 열이 24벌 전부 `F 0.00`** — 요소가 뷰포트 아래 300px 밖이라 안 보이는데 **`observe()` 직후 한 번** 왔다. 「지금 상태를 한 번, 그 뒤로 줄을 넘을 때마다」.
- 그래서 첫 콜백을 「보이게 됐다」로 처리하면 **안 보이는 것까지** 불러온다 — `isIntersecting`(또는 비율)으로 가른다.

### 2. 관찰 시작 한 번뿐 — 0.5 면 「바닥에서 50 위까지」와 「위로 100 지나감」

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-grid.html | sed -n '1,2p;16p;18p;20p;30p'
뷰포트 높이 innerHeight = 713
threshold	rootMargin	크기	관찰 시작	아래 300 밖	아래 100 밖	위 100 들어옴	바닥에서 50 위까지	맨 위에 붙음	위로 100 지나감
1	0px	큼 1200	F 0.00	—	—	—	—	—	—
1	200px	큼 1200	F 0.00	—	—	—	—	—	—
1	-50px	큼 1200	F 0.00	—	—	—	—	—	—
큰 요소 · threshold 1 — 관찰 시작 뒤 콜백이 온 칸 = 0 / 18
(exit 0)
```

**왜 그런가**

- **`threshold: 1` · 큰 요소 — 여백 셋 모두 관찰 시작 뒤 `—`, 관찰 시작 뒤 콜백이 온 칸 0 / 18.** 1200 > 713 이라 **다 들어올 수 없다.**
- **`threshold: 0.5` 로 바꾸면**(A1 의 전체 격자, `0.5 · 0px · 큼 1200` 줄) — 「바닥에서 50 위까지」 `T 0.55` · 「위로 100 지나감」 `F 0.00`. 절반을 넘을 수는 있어서 왔다.

### 3. `0.2083` — 왼쪽 끝에 붙어 좌우도 잘렸다

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-edge.html
innerWidth=1000 · innerHeight=713
요소 left=0	rootMargin 0px	rootBounds 좌0 위0 우985 아래713	겹친 사각형 300×100	intersectionRatio 0.5000
요소 left=0	rootMargin -50px	rootBounds 좌50 위50 우935 아래663	겹친 사각형 250×50	intersectionRatio 0.2083
요소 left=100	rootMargin 0px	rootBounds 좌0 위0 우985 아래713	겹친 사각형 300×100	intersectionRatio 0.5000
요소 left=100	rootMargin -50px	rootBounds 좌50 위50 우935 아래663	겹친 사각형 300×50	intersectionRatio 0.2500
(exit 0)
```

**왜 그런가**

- **`-50px` 의 `rootBounds` 는 네 변이 다 50 씩 들어왔다**(좌50 · 위50 · 우935 · 아래663). 요소가 왼쪽 끝에 붙어 있으니 **겹친 사각형 250×50 → `0.2083`**. 왼쪽에서 100 떨어뜨리면 **300×50 → `0.2500`**.
- **여백을 바꾸면**(A1 격자의 `0 · …· 작음 200` 세 줄) — `0px` 는 그 자리에서 `T 0.50`, **`200px` 는 한 자리 앞(「아래 100 밖」)에서 이미 `T 0.50`** 이 와서 그 자리는 `—`.
- ★ 뷰포트 root 의 오른쪽은 **985** — 스크롤 막대를 뺐다.

### 4. `scrollTo` 부름 → 돌아옴 → `scroll` → rAF → IO · `scroll` 이 더 많다

**출력**

```text
$ python3 wa32b-net.py scroll wa32b-35-count.html | sed -n '6p'
scrollTo 한 번 — scrollTo 부름 → scrollTo 돌아옴 → scroll → rAF → IO
(exit 0)
```

```text
$ python3 wa32b-net.py scroll wa32b-35-count.html | sed -n '1,5p'
준비 — scrollY=0
CDP Input.synthesizeScrollGesture — yDistance -1200 · speed 1200 · mouse
제스처 뒤 scrollY=1200
scroll 리스너 61번 · IO 콜백 9번
scroll 리스너가 IO 콜백보다 많이 불렸나 = true
(exit 0)
```

**왜 그런가**

- **`scrollTo` 안에서는 아무것도 안 불렸다** — 그 뒤에 `scroll` 이 **rAF 보다 먼저**, IO 가 **rAF 보다 뒤**에 왔다.
- **휠 1200px 한 번에 `scroll` 61번 · IO 9번 → `true`**(`scroll` 은 다른 판에서 60 — 값은 움직였고 대소는 세 판 모두 같았다). `scroll` 은 움직인 프레임마다, IO 는 **줄(다섯)을 넘을 때만**. 값은 제스처에 매이므로 **대소만** 근거로 쓴다.

### 5. 150 에서 상자만 `T 0.50` · 300 에서 뷰포트만 `T 1.00`

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-root.html
관찰 시작(scrollTop 0 — 요소는 상자 아래 200 밖)	root=뷰포트 F 0.00 · root=상자 F 0.00
scrollTop 150 — 상자 아래 50 밖	root=상자 T 0.50
scrollTop 300 — 상자 안에 다 들어옴	root=뷰포트 T 1.00
scrollTop 700 — 상자 위로 100 지나감	root=뷰포트 F 0.00
(exit 0)
```

**왜 그런가**

- **관찰 시작 — 둘 다 `F 0.00`**(A1 의 첫 알림과 같다).
- **scrollTop 150 — root=상자 `T 0.50`** — 상자의 여백 100 이 **상자 사각형을 넓혀** 50px 밖의 요소를 반쯤 잡았다. **root=뷰포트는 조용** — 요소가 **상자에 잘려** 있고, 뷰포트 여백은 그 잘림을 넓히지 않는다.
- **scrollTop 300 — root=뷰포트 `T 1.00`**(상자 안에 다 들어와서야). **700 — root=뷰포트 `F 0.00`**, root=상자는 조용했다(0 줄을 다시 안 넘은 것으로 읽힌다).

### 6. 같은 출처 200px 만 `true` — 다른 출처는 여백이 안 먹었다

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-iframes.html
같은 출처 A 의 iframe	rootMargin 0px → F 0.00	rootMargin 200px → T 1.00
다른 출처 B 의 iframe	rootMargin 0px → F 0.00	rootMargin 200px → F 0.00
(exit 0)
```

**왜 그런가**

- **여백 0 은 둘 다 `F`**(iframe 이 뷰포트 아래 100 에 있다). **여백 200 — 같은 출처 `T 1.00` · 다른 출처 `F 0.00`.** 같은 코드인데 **출처만 달라서** 갈렸다 — 다른 출처 iframe 안에서는 `rootMargin` 이 **무시된 것으로 보인다.** 명세 문장은 열지 못했다.

### 7. 0 줄이 없다 — 판정은 안 하고, 비율과 내가 건 줄로 판단한다

- **그 칸들** — `threshold: 0.5` · 200px · 큰 요소 「위로 100 지나감」 `F 0.08`, `threshold: 1` · 200px · 작은 요소 「위로 100 지나감」 `F 0.50`(A1). 공통으로 **`threshold` 에 0 이 없다** — 비율이 **가장 낮은 줄 아래**로 내려간 자리다. 같은 자리의 `[0,.25,.5,.75,1]` 벌은 `T 0.08`·`T 0.50` 이었다.
- **주장하지 않는다** — 명세의 `isIntersecting` 정의를 **열지 못했다.**
- **코드에서는** — 「조금이라도 보이나」는 **`threshold` 에 0 을 넣고** 보거나, **`intersectionRatio` 를 내가 건 줄과 직접 견준다.**

### 8. 잰 것은 호출 수 — 비용은 재지 않았다

- **잰 것** — 휠 1200px 한 번에 **`scroll` 61번 · IO 9번**(A4)과 **순서**. IO 는 **줄을 넘을 때만** 불렸다.
- **재지 않은 것** — **시간 · 메인 스레드 점유 · 교차 계산의 비용.** 그래서 「싸다」는 이 편의 결론이 아니다(가이드 규칙 4).
- **호출 수가 못 보는 것** — **한 번 불릴 때의 비용**(`scroll` 리스너 안의 `getBoundingClientRect()` 는 레이아웃을 부를 수 있다 — [10번 주제](../10-layout-thrashing/2-summary.md)의 몫)과, **브라우저가 매 프레임 교차를 계산하는 일.**

### 9. IO 는 머문 시간을 모른다 · 가림은 교차가 아니다

**출력**

```text
$ python3 wa32b-net.py quiet wa32b-35-expose.html
70% 보이다가 0.3초 만에 치움 → 노출 0
70% 보인 채 1.3초 → 노출 1
치웠다가 다시 70% · 1.3초 → 노출 1 (한 번 센 뒤 unobserve)
(exit 0)
```

**왜 그런가**

- **IO 는 「0.5 줄을 넘었다 / 내려갔다」 순간만** 알린다 — 0.3초 스친 것도 1.3초 머문 것도 **같은 한 번**이다. **1초는 타이머(`setTimeout`)가 쟀다** — 0.3초는 0, 1.3초는 1, 한 번 센 뒤 `unobserve` 로 더 안 셌다.
- **가시성** — 탭이 가려졌을 때 IO 가 무엇을 알리는지 **이 판은 던지지 않았다.** 그래서 「보였다」의 조건에 **`visibilityState === "visible"`** 을 직접 넣었다(24편의 `visibilitychange` 로 타이머도 끊는다). 50% · 1초라는 수치는 **설계 권고층**이다.

### 10. 줄을 넘을 때만 대 매 프레임 — 상자 안 목록은 root 를 그 상자로

- **09편 (10)** — `scroll` 이 올 때마다 **직접 재서** 매 프레임 값을 얻는다. **IO 는 줄을 넘을 때만** 알린다(A1 — 168칸 중 68칸). **패럴랙스처럼 매 프레임 값이 필요하면** `scroll`(passive — 19편) + rAF 쪽이다.
- **무한 스크롤이 스크롤 상자 안이면 root 를 그 상자로** 준다 — **A5 의 scrollTop 150 줄**: root=상자는 여백으로 미리 잡았고(`T 0.50`), root=뷰포트는 **여백이 있어도** 상자에 잘려 못 잡았다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless(`--window-size=1000,800` · `innerHeight` 713) · Python 3 표준 라이브러리 `http.server`(서버 A·B). **엔진은 Chrome 하나다.**

★ **하네스** — [32번 주제](../32-server-sent-events/2-summary.md)의 (1). 호출 수만 `scroll` 모드(CDP `Input.synthesizeScrollGesture`)로 넣었고, 나머지는 페이지가 `scrollTo` 뒤 animation frame 두 장 + 태스크 하나를 두 번 기다린다.

```sh
# wa32b-35-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
python3 wa32b-net.py quiet wa32b-35-grid.html
python3 wa32b-net.py quiet wa32b-35-edge.html
python3 wa32b-net.py scroll wa32b-35-count.html
python3 wa32b-net.py quiet wa32b-35-root.html
python3 wa32b-net.py quiet wa32b-35-iframes.html
python3 wa32b-net.py quiet wa32b-35-expose.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 교차 격자 168칸 | 캡처 3판 | 동작 방식 (1)·(3) · A1 · A2 · A7 · A10 |
| 가장자리 넷 | 캡처 3판 | 동작 방식 (2) · A3 |
| 휠 호출 수 · 순서 | 캡처 3판 | 동작 방식 (4) · A4 · A8 |
| overflow 상자 | 캡처 3판 | 동작 방식 (5) · A5 · A10 |
| iframe 둘 | 캡처 3판 | 동작 방식 (6) · A6 |
| 노출 집계 | 캡처 3판 | 동작 방식 (7) · A9 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `isIntersecting` 이 가장 낮은 줄 아래에서 `false` | 두 칸 | 명세 대조가 남았다 |
| 교차 출처 iframe 의 `rootMargin` | 무시됨 | 명세 대조가 남았다 |
| 휠 한 번의 호출 수 | `scroll` 61 · 61 · 60 · IO 9 | 제스처 · 프레임에 매인다 — 캡처 세 판에서 움직였다 |
| 스크롤 막대를 뺀 `rootBounds` | 우 985 | 스크롤 막대 폭은 플랫폼에 매인다 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② 비용(시간). ③ 탭 가림 · `trackVisibility` · `scrollMargin`. ④ 명세 원문 대조.
