# web-api/35 — `IntersectionObserver`: 루트·`rootMargin`·`threshold` 와 지연 로딩 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「디스패치 계수기」([24번 주제](../24-document-lifecycle-events/2-summary.md)의 창 ④)를 스크롤 자리마다 돌린 「교차 격자」다** — `threshold`(0 · 0.5 · 1 · `[0,.25,.5,.75,1]`) × `rootMargin`(0 · `200px` · `-50px`) × 요소 크기(뷰포트보다 작음 200 / 큼 1200) = **24벌**을 스크롤 **일곱 자리**(관찰 시작 + 여섯)에 세워, 자리마다 **콜백이 왔나 · `isIntersecting` · `intersectionRatio`** 를 적는다(168칸). 스크립트가 **「콜백이 온 칸 N / M」과 「rootMargin 이 바꾼 칸 N / M」** 을 마지막 줄로 찍는다.\
> ★★ **기준 소스 — 명세 원문을 이 판에서 열지 못했다.** 정본은 [W3C Intersection Observer](https://www.w3.org/TR/intersection-observer/) 인데, 이 배치는 **외부 네트워크를 쓰지 않았고** 앞 배치의 명세 사본에 없다. 그래서 **이 편의 규칙 서술은 전부 「이 판의 관찰」이고, 「명세대로다 / 명세에서 벗어났다」를 판정하지 않는다**(가이드 규칙 5 — 특히 (3)의 `isIntersecting`). 기준일 2026-09-26.\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless(`--window-size=1000,800` · 이 판의 `innerHeight` **713**)에서 받은 것이다. 스크롤은 `window.scrollTo` 뒤 **animation frame 두 장 + 태스크 하나**를 두 번 기다렸고, 호출 수를 셀 때만 **CDP `Input.synthesizeScrollGesture`**(진짜 휠 제스처)를 썼다. 하네스는 [32번 주제](../32-server-sent-events/2-summary.md)의 (1)이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[09번 주제](../09-element-geometry/2-summary.md)의 (10)** — `getBoundingClientRect()` 로 **「화면 안에 있나」를 직접 재는** 쪽. 여기는 그것을 **브라우저에게 알려 달라고 하는** 쪽이다. ★★ **[19번 주제](../19-passive-and-scroll/2-summary.md)** — `scroll` 리스너는 **막을 수 없는(passive) 알림**이고 합성 스레드가 스크롤을 먼저 한다는 것. 여기서는 그 `scroll` 리스너가 **몇 번 불리나**를 IO 콜백과 나란히 센다.\
> **경계** — ★★★ **「IO 가 스크롤 리스너보다 싸다」는 이 편이 주장하지 않는다 — 재지 않았다**(가이드 규칙 4). 센 것은 **호출 수**다((4)). ★ 마크업 쪽 **`loading="lazy"`** 는 **HTML 갈래 34번**(`img` — `loading`·`decoding`, 폴더는 아직 없다)의 몫이다. ★ **노출 집계(50% 이상 1초)는 설계 권고층**이다 — 광고 업계의 관례 수치로 흔히 쓰지만 이 편은 **그 형태를 한 번 돌려 볼 뿐**이다((7)).\
> 이 본문은 Claude 작성이다(원고 없음). 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 교차 격자 168칸 · 집계 네 줄 · 가장자리 넷 · 순서 한 줄 · overflow 상자 · iframe 둘 · 노출 집계 셋 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **흔들렸다** | **`scroll` 리스너 호출 수** — 캡처 세 판에서 **61 · 61 · 60** | 제스처의 속도 · 프레임 수에 매인다. 그래서 **값이 아니라 「`scroll` 이 IO 보다 많았다」(참/거짓 — 세 판 모두 `true`)** 를 근거로 쓴다(가이드 규칙 24). IO 콜백 9번은 세 판 같았다. 재대조는 이 칸만 `--rule` 로 정규화했다 |
| ★ **판에 매일 수 있는 칸** | `innerHeight = 713` | 창 크기 플래그 · 헤드리스 판에 매인다. 격자의 자리는 **그 값에서 계산**하므로 칸의 모양은 안 바뀐다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 **`scroll` 리스너 호출 수 하나**다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `IntersectionObserverEntry` 의 `isIntersecting` · `intersectionRatio` · `innerHeight` · `scrollY` |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | 같은 요소를 **두 관찰자**(root=상자 · root=뷰포트)로 · 같은 iframe 코드를 **두 출처**로 |
| **창 ④ 디스패치 계수기 → 교차 격자** | ★★★ **본체** | 자리마다 콜백이 **왔나 · 몇 번 · 무엇을 들고** · 호출 순서 |
| ★★ **「비용」을 호출 수로** | ★★ **제5의 상태 — 같은 질문을 다른 창으로** | 「어느 쪽이 싸나」를 시간으로 재지 않고 **「스크롤 한 번에 몇 번 불리나」** 로 물었다((4)). ★ 바꾼 창이 못 보는 것 — **한 번 불릴 때의 비용**(콜백 안의 일 · 브라우저가 교차를 계산하는 비용 · 레이아웃) |
| 서버 요청 로그 | **부적용** | 네트워크를 안 쓴다(iframe 페이지를 받는 것뿐) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **비용 — 시간 · 메인 스레드 점유** | **재지 않았다**(머리말) |
| ★★ **명세 문장** | 원문을 열지 못했다(머리말) |
| **`transform` · `clip-path` · 겹침으로 가려진 요소**(`trackVisibility`) | 던지지 않았다 — IO 는 **겹친 다른 요소**를 기본으로 안 본다 |
| **진짜 손가락 스크롤 · 관성** | 휠 제스처 한 번과 `scrollTo` 뿐이다 |
| **`loading="lazy"` 이미지가 언제 불러지나** | 마크업 쪽 — HTML 갈래 34번의 몫 |

## 한눈에 — 쉽게 말하면

**★ `IntersectionObserver` 는 「무대 조명 담당에게 부탁한 쪽지」다. 「이 배우가 조명 안에 반쯤 들어오면 알려 줘요」(`threshold: 0.5`)라고 적어 두면, 조명 담당(브라우저)이 **줄을 넘을 때만** 알려 준다. 배우가 조명 안에서 계속 움직여도 줄을 안 넘으면 조용하다. 조명 범위를 넉넉히(`rootMargin: 200px`) 잡으면 무대에 오르기 전에 미리 알려 주고, 좁게(`-50px`) 잡으면 한가운데 와야 알려 준다. 배우가 조명보다 크면 — 「몸 전체가 조명 안(`threshold: 1`)」은 영원히 안 온다.**

| 비유 | 실체 |
|---|---|
| 조명 범위 | root(기본 = 뷰포트) + `rootMargin` 으로 넓히거나 좁힌 사각형 |
| 「반쯤 들어오면」 | `threshold` — 비율의 **줄**. 콜백은 줄을 **넘을 때만** 온다 |
| 쪽지를 건 순간의 첫 보고 | `observe()` 직후 **한 번은 꼭 온다** — 안 보여도 `isIntersecting: false` 로 |
| 조명보다 큰 배우 | 뷰포트보다 큰 요소 — 비율이 1 이 될 수 없다 |
| 무대 옆 작은 무대(액자) | `overflow` 상자를 root 로 · iframe |
| 스스로 매 순간 재기 | `scroll` 리스너 + `getBoundingClientRect()`(09편 (10)) |

```text
   스크롤 자리 여섯 — 작은 요소(200) · threshold 0 · rootMargin 0 (이 판)

   자리                 요소와 뷰포트                         콜백
   관찰 시작            ░ 뷰포트 ░          요소 ▇ (아래 300 밖)   F 0.00  ← 안 보여도 한 번
   아래 300 밖          ░ 뷰포트 ░          ▇                     —
   아래 100 밖          ░ 뷰포트 ░     ▇                          —
   위 100 들어옴        ░ 뷰포트 ▇░                               T 0.50  ← 줄(0)을 넘음
   바닥에서 50 위까지   ░ 뷰 ▇ 포트 ░                             —       ← 줄을 안 넘음
   맨 위에 붙음         ▇ 뷰포트 ░                                —
   위로 100 지나감  ▇   ░ 뷰포트 ░                                F 0.00  ← 다시 줄을 넘음
```

## 이 주제가 답하려는 질문

1. **콜백은 언제 오나** — 관찰 시작 · 줄(`threshold`)을 넘을 때 · 넘지 않을 때 · 줄에 닿을 수 없을 때.
2. **root 와 `rootMargin` 은 무엇을 바꾸나** — 뷰포트 · `overflow` 상자 · iframe · 음수 여백.
3. **스크롤 이벤트로 재는 방식과 무엇이 다른가** — 호출 수 · 순서 · 그리고 「노출」처럼 **시간이 걸린 조건**은 누가 재나.

## 동작 방식

### (1) ★★★ 본체 — 교차 격자

**요소 하나를 문서 2000px 자리에 두고**, 벌마다 높이를 바꾸고 새 관찰자를 만든다. 자리는 **`innerHeight` 에서 계산**한다(「아래 300 밖」 = 요소 위끝이 뷰포트 바닥보다 300 아래).

```html
<!-- wa32b-35-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 grid</title>
<style>
  body { margin: 0; height: 5000px; }
  #t { position: absolute; top: 2000px; left: 0; width: 300px; background: #cde; }
</style>
<div id="t"></div>
<script>
// 교차 격자 — threshold × rootMargin × 요소 크기. 칸마다 새 관찰자로 관찰을 시작하고 스크롤 여섯 자리를 차례로 간다
// 한 칸 = 그 자리에서 불린 콜백(여럿이면 + 로) — T/F = isIntersecting · 숫자 = intersectionRatio(소수 둘째 자리)
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const t = document.getElementById("t"), T = 2000;
const 문턱들 = [["0", 0], ["0.5", 0.5], ["1", 1], ["[0,.25,.5,.75,1]", [0, 0.25, 0.5, 0.75, 1]]];
const 여백들 = ["0px", "200px", "-50px"];
const 크기들 = [["작음 200", 200], ["큼 1200", 1200]];
window.__끝 = async () => {
  const H = innerHeight, 줄 = [`뷰포트 높이 innerHeight = ${H}`];
  const 자리 = h => [["관찰 시작", T - H - 300], ["아래 300 밖", T - H - 300], ["아래 100 밖", T - H - 100],
                     ["위 100 들어옴", T - H + 100], ["바닥에서 50 위까지", T - H + h + 50], ["맨 위에 붙음", T], ["위로 100 지나감", T + h + 100]];
  줄.push(["threshold", "rootMargin", "크기", ...자리(0).map(x => x[0])].join("\t"));
  const 표 = {};
  let 온칸 = 0, 칸수 = 0, 큰1 = 0, 큰1수 = 0;
  for (const [tn, tv] of 문턱들) for (const m of 여백들) for (const [sn, h] of 크기들) {
    t.style.height = h + "px";
    const 자리들 = 자리(h), 칸 = [];
    let 받음 = [];
    scrollTo(0, 자리들[0][1]); await 틀();
    const io = new IntersectionObserver(es => { for (const e of es) 받음.push((e.isIntersecting ? "T " : "F ") + e.intersectionRatio.toFixed(2)); },
                                        { threshold: tv, rootMargin: m });
    for (const [k, [, y]] of 자리들.entries()) {
      if (k === 0) io.observe(t); else scrollTo(0, y);
      await 틀(); await 틀();
      칸.push(받음.length ? 받음.join("+") : "—");
      칸수++; if (받음.length) 온칸++;
      if (sn.startsWith("큼") && tn === "1" && k > 0) { 큰1수++; if (받음.length) 큰1++; }
      받음 = [];
    }
    io.disconnect();
    if (칸.length !== 7) throw new Error("칸 수");
    표[tn + "|" + m + "|" + sn] = 칸;
    줄.push([tn, m, sn, ...칸].join("\t"));
  }
  const 다름 = m => { let n = 0, all = 0; for (const [tn] of 문턱들) for (const [sn] of 크기들) {
    const a = 표[tn + "|0px|" + sn], b = 표[tn + "|" + m + "|" + sn]; for (let k = 0; k < 7; k++) { all++; if (a[k] !== b[k]) n++; } } return `${n} / ${all}`; };
  줄.push(`콜백이 온 칸 = ${온칸} / ${칸수}`);
  줄.push(`rootMargin 200px 이 0px 과 다른 칸 = ${다름("200px")}`);
  줄.push(`rootMargin -50px 이 0px 과 다른 칸 = ${다름("-50px")}`);
  줄.push(`큰 요소 · threshold 1 — 관찰 시작 뒤 콜백이 온 칸 = ${큰1} / ${큰1수}`);
  return 줄.join("\n");
};
</script>
```

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

- ★★★ **콜백이 온 칸 68 / 168.** 나머지 100칸은 **자리가 바뀌었는데도 줄을 안 넘어** 조용했다.
- ★★★ **`관찰 시작` 열은 24벌 전부 `F 0.00`** — 요소가 뷰포트 아래 300px 밖이라 안 보이는데도 **`observe()` 직후 콜백이 한 번 왔다.** 「보이게 되면 알려 줘」가 아니라 **「지금 상태를 한 번 알려 주고, 그 뒤로 줄을 넘을 때마다」** 다.
- ★★★ **큰 요소(1200) · `threshold: 1` — 관찰 시작 뒤 콜백이 온 칸 0 / 18.** `rootMargin` 이 무엇이든 여섯 자리 전부 `—` 다. **뷰포트(713)보다 큰 요소는 다 들어올 수가 없다** — 같은 큰 요소가 0.5 줄에서 받은 값도 `0.55`(여백 0) · `0.72`(200px)였다.
- ★★ **`rootMargin: 200px` 은 「아래 100 밖」에서 이미 `T`** — 넓힌 조명이 요소를 먼저 잡았다. 그 대신 **「위로 100 지나감」에서도 아직 걸려 있어** threshold 0 은 `—` 다. **`rootMargin 200px` 이 `0px` 과 다른 칸 23 / 56 · `-50px` 은 13 / 56.**
- ★ **자리가 바뀌어도 줄을 안 넘으면 `—`** — 작은 요소 · threshold 0 은 「위 100 들어옴」에서 `T` 뒤 「맨 위에 붙음」까지 **보이는 양이 늘어도 조용했다.** 비율의 변화를 보려면 **줄을 여럿**(`[0,.25,.5,.75,1]`) 걸어야 한다 — 그 벌은 자리마다 거의 다 왔다.

```text
   큰 요소(1200 > 뷰포트 713) · threshold 1 (이 판)

   요소 ████████████████████████  1200
   뷰포트    ░░░░░░░░░░░░░         713     ← 요소가 뷰포트에 다 들어올 수 없다
   → 관찰 시작의 F 0.00 한 번 뒤로 콜백 없음 (여섯 자리 × 여백 셋 = 0 / 18)
   처방: 큰 요소는 threshold 를 「요소 비율」 대신 0 이나 작은 값으로 · 또는 보이는 높이(px)로 판단
```

### (2) ★★ `rootMargin: -50px` 은 네 변을 다 좁힌다

**격자의 작은 요소 · threshold 0 · `-50px` 은 「위 100 들어옴」에서 `T 0.21`** 이다 — 위아래만 생각하면 50px 이 보이니 0.25 일 것 같다. 같은 자리에서 **요소의 왼쪽 자리 × 여백**을 바꿔, 관찰 시작의 첫 알림이 주는 `rootBounds` 와 겹친 사각형을 읽는다.

```html
<!-- wa32b-35-edge.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 edge</title>
<style>
  body { margin: 0; height: 5000px; }
  #t { position: absolute; top: 2000px; width: 300px; height: 200px; background: #cde; }
</style>
<div id="t"></div>
<script>
// 요소의 위 100px 이 뷰포트 바닥 위로 들어온 자리 — 요소의 왼쪽 자리 × rootMargin 을 바꿔
// 관찰 시작의 첫 알림(지금 상태)에서 intersectionRatio 와 rootBounds 를 읽는다
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const t = document.getElementById("t");
window.__끝 = async () => {
  const 줄 = [`innerWidth=${innerWidth} · innerHeight=${innerHeight}`];
  scrollTo(0, 2000 - innerHeight + 100); await 틀();
  for (const left of [0, 100]) for (const m of ["0px", "-50px"]) {
    t.style.left = left + "px"; await 틀();
    const e = await new Promise(r => { const io = new IntersectionObserver(([x]) => { io.disconnect(); r(x); }, { rootMargin: m }); io.observe(t); });
    const b = e.rootBounds, i = e.intersectionRect;
    줄.push(`요소 left=${left}\trootMargin ${m}\trootBounds 좌${b.left} 위${b.top} 우${b.right} 아래${b.bottom}` +
            `\t겹친 사각형 ${i.width}×${i.height}\tintersectionRatio ${e.intersectionRatio.toFixed(4)}`);
  }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-35-edge.html
innerWidth=1000 · innerHeight=713
요소 left=0	rootMargin 0px	rootBounds 좌0 위0 우985 아래713	겹친 사각형 300×100	intersectionRatio 0.5000
요소 left=0	rootMargin -50px	rootBounds 좌50 위50 우935 아래663	겹친 사각형 250×50	intersectionRatio 0.2083
요소 left=100	rootMargin 0px	rootBounds 좌0 위0 우985 아래713	겹친 사각형 300×100	intersectionRatio 0.5000
요소 left=100	rootMargin -50px	rootBounds 좌50 위50 우935 아래663	겹친 사각형 300×50	intersectionRatio 0.2500
(exit 0)
```

- ★★ **`-50px` 의 `rootBounds` 는 좌50 · 위50 · 우935 · 아래663** — **네 변이 다 50 씩 들어왔다.** 요소가 왼쪽 끝(left=0)에 붙어 있으면 **겹친 사각형이 250×50** 이라 `0.2083`, 왼쪽에서 100 떨어뜨리면 **300×50** 이라 `0.2500` 이다. **음수 여백은 좌우까지 잘라 먹는다.**
- ★ **`rootBounds` 의 오른쪽이 `innerWidth`(1000)가 아니라 985** — 뷰포트 root 는 **스크롤 막대를 뺀** 사각형이었다.
- 같은 이유로 격자의 **`-50px` · 작은 요소 · threshold 1 은 여섯 자리 전부 `—`** — 왼쪽 끝에 붙은 요소는 폭 방향에서 이미 다 들어올 수 없다.

```text
   rootMargin -50px — 뷰포트(1000×713 쯤)를 네 변에서 50씩 좁힌 사각형

   ┌───────────────────────────────┐ 뷰포트
   │  ┌─────────────────────────┐  │
   │  │  root 사각형             │  │
   ▇▇▇│▇▇▇ ← 요소의 왼쪽 50px 은 밖(겹친 사각형 250×50)
   │  └─────────────────────────┘  │
   └───────────────────────────────┘
   ★ 요소가 가장자리에 붙어 있으면 「다 보이는데」 비율이 1 이 안 된다
```

### (3) ★★ `isIntersecting` 은 「겹치나」가 아니라 「가장 낮은 줄을 넘었나」처럼 왔다

- 격자의 **`threshold: 0.5` · 200px · 큰 요소 「위로 100 지나감」 → `F 0.08`**, **`threshold: 1` · 200px · 작은 요소 「위로 100 지나감」 → `F 0.50`**. **비율이 0 보다 큰데(기하로는 겹치는데) `isIntersecting` 이 `false`** 다.
- 같은 자리에서 **`threshold: 0` 이 걸린 벌은 `T`**(또는 `—` — 여전히 `T`)였다. 이 판에서 `isIntersecting` 은 **「비율이 가장 낮은 줄 이상인가」** 와 같이 움직였다.
- ★★ **이것이 명세대로인지 이 편은 판정하지 않는다** — 명세의 `isIntersecting` 정의를 **열지 못했다**(머리말). **처방은 판정과 무관하다** — 「보이나」는 **`intersectionRatio` 와 내가 건 줄로** 판단한다. `threshold` 에 0 을 넣지 않은 관찰자에게서 `isIntersecting` 을 「겹치나」로 읽지 않는다.

### (4) ★★ `scroll` 리스너 대 IO 콜백 — 호출 수와 순서

```html
<!-- wa32b-35-count.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 count</title>
<style>
  body { margin: 0; height: 4000px; }
  #t { position: absolute; top: 1000px; left: 0; width: 300px; height: 200px; background: #cde; }
</style>
<div id="t"></div>
<script>
// 스크롤 한 번(하네스가 CDP 로 진짜 휠 제스처를 넣는다) 동안 — scroll 리스너 호출 수 대 IO 콜백 호출 수
// 그리고 scrollTo 한 번의 순서 — scroll 리스너 · rAF · IO 콜백이 어느 순서로 불리나
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const t = document.getElementById("t");
let 스크롤 = 0, 콜백 = 0, 순서 = null;
addEventListener("scroll", () => { 스크롤++; if (순서) 순서.push("scroll"); }, { passive: true });
const io = new IntersectionObserver(es => { 콜백++; if (순서) 순서.push("IO"); }, { threshold: [0, 0.25, 0.5, 0.75, 1] });
window.__준비 = async () => { io.observe(t); await 틀(); await 틀(); 스크롤 = 0; 콜백 = 0; return "준비 — scrollY=" + scrollY; };
window.__결과 = async () => {
  await 틀(); await 틀();
  const 줄 = [`제스처 뒤 scrollY=${Math.round(scrollY)}`, `scroll 리스너 ${스크롤}번 · IO 콜백 ${콜백}번`,
              `scroll 리스너가 IO 콜백보다 많이 불렸나 = ${스크롤 > 콜백}`];
  scrollTo(0, 0); await 틀(); await 틀();
  순서 = ["scrollTo 부름"];
  scrollTo(0, 1000 - innerHeight + 100);
  순서.push("scrollTo 돌아옴");
  requestAnimationFrame(() => 순서.push("rAF"));
  await 틀(); await 틀();
  줄.push("scrollTo 한 번 — " + 순서.join(" → "));
  return 줄.join("\n");
};
</script>
```

**휠 제스처 한 번**(CDP 로 1200px)

```text
$ python3 wa32b-net.py scroll wa32b-35-count.html | sed -n '1,5p'
준비 — scrollY=0
CDP Input.synthesizeScrollGesture — yDistance -1200 · speed 1200 · mouse
제스처 뒤 scrollY=1200
scroll 리스너 61번 · IO 콜백 9번
scroll 리스너가 IO 콜백보다 많이 불렸나 = true
(exit 0)
```

**`scrollTo` 한 번의 순서**

```text
$ python3 wa32b-net.py scroll wa32b-35-count.html | sed -n '6p'
scrollTo 한 번 — scrollTo 부름 → scrollTo 돌아옴 → scroll → rAF → IO
(exit 0)
```

- ★★ **같은 1200px 동안 `scroll` 리스너 61번(다른 판은 60) · IO 콜백 9번**(줄 다섯) — **`scroll` 이 더 많이 불렸다(`true`).** `scroll` 은 **스크롤이 움직인 프레임마다**, IO 는 **줄을 넘은 때만** 온다. `scroll` 쪽 값은 판마다 움직였다(머리말) — **근거는 대소**다.
- ★★★ **이것은 호출 수이지 비용이 아니다.** 「IO 가 싸다」는 **재지 않았다** — 한 번의 IO 콜백 뒤에는 **브라우저가 매 프레임 교차를 계산하는 일**이 있고, 이 판은 그것을 **못 본다**(머리말 제5의 상태).
- ★★ **순서 — `scrollTo` 부름 → `scrollTo` 돌아옴 → `scroll` → rAF → IO.** **`scroll` 도 IO 도 `scrollTo` 안에서 안 불렸다** — 둘 다 그 뒤에 왔고, `scroll` 이 **rAF 보다 먼저**, IO 가 **rAF 보다 뒤**였다. **rAF 에서 무언가를 바꿔도 IO 가 그것을 같은 차례에 봤는지는 재지 않았다.**

```text
   scrollTo 한 번 — 이 판의 순서

   스크립트          scrollTo(0, y) → 돌아옴            (여기서는 아무 이벤트도 안 난다)
   다음 렌더링 단계  ├ scroll 리스너                    ← 스크롤이 움직인 프레임마다
                     ├ rAF 콜백
                     └ (교차 계산) → IO 콜백            ← 줄을 넘었을 때만
   ★ 셀 수 있는 것: scroll 61 대 IO 9 (휠 1200px) · 셀 수 없는 것: 각각의 비용
```

### (5) ★★ root 가 `overflow` 상자일 때

**300px 상자 안 500px 자리의 요소**를 두 관찰자가 본다 — **root=상자**(`rootMargin: 100px`)와 **root=뷰포트**(같은 여백). 상자는 뷰포트 안에 통째로 보인다.

```html
<!-- wa32b-35-root.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 root</title>
<style>
  body { margin: 0; }
  #box { height: 300px; width: 400px; overflow: auto; }
  #pad { height: 2000px; position: relative; }
  #t { position: absolute; top: 500px; width: 300px; height: 100px; background: #cde; }
</style>
<div id="box"><div id="pad"><div id="t"></div></div></div>
<script>
// root 를 overflow 상자로 — 같은 요소를 두 관찰자로 본다: root=상자(rootMargin 100px) · root=뷰포트(rootMargin 100px)
// 상자는 뷰포트 안에 통째로 보인다. 상자 안을 굴린다
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const box = document.getElementById("box"), t = document.getElementById("t");
let 받음 = [];
const 적기 = 쪽 => es => { for (const e of es) 받음.push(`${쪽} ${e.isIntersecting ? "T" : "F"} ${e.intersectionRatio.toFixed(2)}`); };
new IntersectionObserver(적기("root=상자"), { root: box, rootMargin: "100px" }).observe(t);
new IntersectionObserver(적기("root=뷰포트"), { rootMargin: "100px" }).observe(t);
window.__끝 = async () => {
  const 줄 = [];
  for (const [말, y] of [["관찰 시작(scrollTop 0 — 요소는 상자 아래 200 밖)", 0], ["scrollTop 150 — 상자 아래 50 밖", 150],
                          ["scrollTop 300 — 상자 안에 다 들어옴", 300], ["scrollTop 700 — 상자 위로 100 지나감", 700]]) {
    box.scrollTop = y; await 틀(); await 틀();
    줄.push(말 + "\t" + (받음.length ? 받음.sort().join(" · ") : "—"));
    받음 = [];
  }
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-35-root.html
관찰 시작(scrollTop 0 — 요소는 상자 아래 200 밖)	root=뷰포트 F 0.00 · root=상자 F 0.00
scrollTop 150 — 상자 아래 50 밖	root=상자 T 0.50
scrollTop 300 — 상자 안에 다 들어옴	root=뷰포트 T 1.00
scrollTop 700 — 상자 위로 100 지나감	root=뷰포트 F 0.00
(exit 0)
```

- ★★ **상자 아래 50px 밖(scrollTop 150)에서 root=상자만 `T 0.50`** — 상자의 `rootMargin` 이 **상자 사각형을 넓혔다.** 뷰포트 쪽은 **그 여백으로도 못 잡았다** — 요소가 **상자의 스크롤 영역에 잘려** 뷰포트까지 보이지 않기 때문이다.
- ★★ **root=뷰포트는 요소가 상자 안에 다 들어와서야(scrollTop 300) `T 1.00`**, 상자 위로 지나가자 `F 0.00`. **뷰포트 root 의 `rootMargin` 은 상자의 잘림을 넓혀 주지 않는다.**
- ★ **root=상자는 scrollTop 700(상자 위로 100 지나감)에서 조용했다** — 넓힌 상자 사각형과의 관계가 **0 줄을 다시 넘지 않은 것**으로 읽힌다(이 자리의 비율은 콜백이 없어 찍히지 않았다).
- ★ **스크롤 컨테이너 안의 목록(무한 스크롤)은 root 를 그 상자로** 준다 — 뷰포트 root 로는 **상자의 여백 미리 잡기가 안 된다.**

### (6) ★★ 교차 출처 iframe 에서는 `rootMargin` 이 안 먹었다

**같은 코드**(iframe 안에서 root 없이 · 여백 0 과 200px)를 **같은 출처 A 의 iframe** 과 **다른 출처 B 의 iframe** 에 넣고, 두 iframe 을 뷰포트 바닥 아래 100px 에 둔다.

```html
<!-- wa32b-35-frame.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 frame</title>
<style> body { margin: 0; } #t { height: 100px; width: 200px; background: #cde; } </style>
<div id="t"></div>
<script>
// iframe 안의 요소 — root 를 안 주고(최상위 뷰포트) rootMargin 0px · 200px 둘로 관찰해 첫 알림을 부모에게 보낸다
const 받음 = {};
for (const m of ["0px", "200px"])
  new IntersectionObserver(es => {
    if (m in 받음) return;
    받음[m] = `${es[0].isIntersecting ? "T" : "F"} ${es[0].intersectionRatio.toFixed(2)}`;
    if (Object.keys(받음).length === 2) parent.postMessage({ 출처: location.origin, 받음 }, "*");
  }, { rootMargin: m }).observe(document.getElementById("t"));
</script>
```

```html
<!-- wa32b-35-iframes.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 iframes</title>
<style> body { margin: 0; } iframe { border: 0; width: 300px; height: 200px; position: absolute; } </style>
<script>
// 같은 출처(A) iframe 과 다른 출처(B) iframe 을 뷰포트 바닥 아래 100px 에 나란히 둔다
// 안쪽 요소는 뷰포트 밖이지만 rootMargin 200px 이면 걸리는 자리다 — 두 iframe 이 무엇을 보고하나
window.__끝 = () => new Promise(r => {
  const 줄 = [], 이름 = { [window.__A]: "같은 출처 A 의 iframe", [window.__B]: "다른 출처 B 의 iframe" };
  addEventListener("message", e => {
    줄.push(`${이름[e.data.출처]}\trootMargin 0px → ${e.data.받음["0px"]}\trootMargin 200px → ${e.data.받음["200px"]}`);
    if (줄.length === 2) r(줄.sort().join("\n"));
  });
  for (const [k, base] of [window.__A, window.__B].entries()) {
    const f = document.createElement("iframe");
    f.src = base + "/wa32b-35-frame.html";
    f.style.top = (innerHeight + 100) + "px";
    f.style.left = (k * 320) + "px";
    document.body.append(f);
  }
});
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-35-iframes.html
같은 출처 A 의 iframe	rootMargin 0px → F 0.00	rootMargin 200px → T 1.00
다른 출처 B 의 iframe	rootMargin 0px → F 0.00	rootMargin 200px → F 0.00
(exit 0)
```

- ★★★ **같은 출처 iframe 은 200px 여백으로 `T 1.00`, 다른 출처 iframe 은 `F 0.00`** — 여백 0 은 둘 다 `F`. **다른 출처 iframe 안에서는 `rootMargin` 이 무시된 것으로 보인다** — 광고 · 위젯처럼 **남의 출처 iframe 안에서 「미리 불러오기」를 걸면 여백 없이 동작한다.** 명세 문장은 열지 못했다 — 이 판의 관찰로 적는다.

```text
   iframe 안의 요소 — 뷰포트 바닥 아래 100 · root 없음 (이 판)

                          rootMargin 0px    rootMargin 200px
   같은 출처 A 의 iframe   F 0.00            T 1.00   ← 여백이 최상위 뷰포트를 넓혔다
   다른 출처 B 의 iframe   F 0.00            F 0.00 ★ ← 여백이 안 먹었다
```

### (7) 노출 집계 — 「50% 이상이 1초」는 IO 와 타이머가 나눠 잰다

**설계 권고층**이다 — 수치(50% · 1초)는 관례이고, 이 편은 **그 형태를 한 번 돌려 본다.** IO 는 **줄을 넘은 순간**만 알려 주므로 **머문 시간은 타이머**가 잰다.

```html
<!-- wa32b-35-expose.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>35 expose</title>
<style>
  body { margin: 0; height: 4000px; }
  #ad { position: absolute; top: 2000px; width: 300px; height: 200px; background: #cde; }
</style>
<div id="ad"></div>
<script>
// 노출 집계 — 「50% 이상이 1초 이어지면 한 번」. IO 는 문턱을 넘은 순간만 알려 주므로 머문 시간은 타이머가 잰다
const 틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0))));
const 쉬기 = ms => new Promise(r => setTimeout(r, ms));
const ad = document.getElementById("ad");
let 노출 = 0, 타이머 = null;
const io = new IntersectionObserver(([e]) => {
  if (e.intersectionRatio >= 0.5 && document.visibilityState === "visible") {
    if (!타이머) 타이머 = setTimeout(() => { 노출++; 타이머 = null; io.unobserve(ad); }, 1000);   // 한 번 세면 그만 본다
  } else { clearTimeout(타이머); 타이머 = null; }
}, { threshold: [0.5] });
io.observe(ad);
const 절반넘게 = () => scrollTo(0, 2000 - innerHeight + 140);    // 200 중 140 이 보인다 — 70%
const 치움 = () => scrollTo(0, 0);
window.__끝 = async () => {
  const 줄 = [];
  await 틀();
  절반넘게(); await 틀(); await 쉬기(300); 치움(); await 틀();
  줄.push(`70% 보이다가 0.3초 만에 치움 → 노출 ${노출}`);
  절반넘게(); await 틀(); await 쉬기(1300);
  줄.push(`70% 보인 채 1.3초 → 노출 ${노출}`);
  치움(); await 틀(); 절반넘게(); await 틀(); await 쉬기(1300);
  줄.push(`치웠다가 다시 70% · 1.3초 → 노출 ${노출} (한 번 센 뒤 unobserve)`);
  return 줄.join("\n");
};
</script>
```

```text
$ python3 wa32b-net.py quiet wa32b-35-expose.html
70% 보이다가 0.3초 만에 치움 → 노출 0
70% 보인 채 1.3초 → 노출 1
치웠다가 다시 70% · 1.3초 → 노출 1 (한 번 센 뒤 unobserve)
(exit 0)
```

- ★★ **70% 보이다가 0.3초 만에 치우면 0 · 1.3초 머물면 1 · 한 번 센 뒤에는 더 안 센다(`unobserve`).** IO 는 「0.5 줄을 넘었다 / 내려갔다」 두 번만 알렸고, **1초는 `setTimeout` 이 쟀다.**
- ★ **`document.visibilityState === "visible"` 을 같이 본다** — 탭이 가려졌을 때 IO 가 무엇을 알리는지는 **이 판이 던지지 않았다.** 그래서 「보였다」의 조건에 가시성을 직접 넣었다. 가려진 동안의 타이머를 끊으려면 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 `visibilitychange` 를 같이 건다.

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   const io = new IntersectionObserver((entries, observer) => { … }, {
     root: null | 스크롤 상자 요소,        ← null = 최상위 뷰포트
     rootMargin: "200px" | "0px 0px -50px" …,   ← CSS margin 꼴 · 음수면 좁힌다(네 변)
     threshold: 0 | 0.5 | [0, 0.25, …, 1],
   });
   io.observe(요소) · io.unobserve(요소) · io.disconnect() · io.takeRecords()
   entry.isIntersecting · entry.intersectionRatio · entry.boundingClientRect
   entry.intersectionRect · entry.rootBounds · entry.target · entry.time
```

### 어디서 헷갈리나

- **`observe()` 하면 곧바로 한 번 온다** — 안 보여도((1)).
- **줄을 넘을 때만 온다** — 보이는 양이 늘어도 줄 사이에 있으면 조용하다((1)).
- **`isIntersecting` 과 `intersectionRatio > 0` 은 같은 뜻이 아니었다**((3)).
- **음수 `rootMargin` 은 좌우도 좁힌다**((2)).

## 어디서 틀리나

### 1. 첫 콜백을 「보이게 됐다」로 처리한다

**`observe()` 직후 `F 0.00` 이 한 번 온다**((1)). `isIntersecting`(또는 비율)을 보고 가른다 — 안 그러면 **안 보이는 이미지를 전부 불러온다.**

### 2. 큰 요소에 `threshold: 1` 을 건다

**영원히 안 온다**((1) — 0 / 18). 큰 요소는 **0 이나 작은 값**, 또는 보이는 **높이(px)** 로 판단한다.

### 3. `threshold: 0.5` 관찰자에서 `isIntersecting` 으로 「조금이라도 보이나」를 판단한다

**비율 0.08 에 `false` 가 왔다**((3)). `isIntersecting` 을 「겹치나」로 쓰려면 `threshold` 에 **0 을 같이** 건다.

### 4. 스크롤 컨테이너 안의 목록을 뷰포트 root 로 관찰하며 `rootMargin` 으로 미리 불러오기를 기대한다

**상자의 잘림은 뷰포트 여백으로 안 넓어진다**((5)). root 를 **그 상자**로 준다.

### 5. 다른 출처 iframe(광고 · 위젯) 안에서 `rootMargin` 으로 미리 불러온다

**여백이 안 먹었다**((6)).

### 6. 「IO 는 싸니까 요소마다 관찰자를 하나씩」

**비용은 재지 않았다**((4)). 이 판이 말하는 것은 **호출이 적었다**는 것뿐이다. 관찰자 하나에 요소 여럿을 `observe` 할 수 있다 — 콜백이 **`entries` 배열**을 받는 이유다.

### 7. 노출을 IO 콜백 한 번으로 센다

**IO 는 머문 시간을 모른다**((7)) — 0.3초 스친 것도 「0.5 줄을 넘었다」로 온다. 타이머와 가시성을 같이 본다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `observe()` 직후 한 번 온다 · 줄을 넘을 때만 온다 | ★ **이 판의 관찰** — 명세 원문은 열지 못했다 |
| 뷰포트보다 큰 요소는 `threshold: 1` 이 안 온다 | ★ **이 판의 관찰**(0 / 18) — 기하로 보면 비율이 1 이 될 수 없다 |
| 음수 `rootMargin` 이 네 변을 좁힌다 · 뷰포트 root 는 스크롤 막대를 뺀다 | ★ **이 판의 관찰**(`rootBounds` 좌50 · 우935 · 겹친 사각형 250×50) |
| 겹치는데 가장 낮은 줄 아래면 `isIntersecting: false` | ★ **이 판의 관찰 — 명세대로인지 판정하지 않는다** |
| `scroll` → rAF → IO 순서 · `scrollTo` 안에서는 안 불린다 | ★ **이 판의 관찰**(한 번의 `scrollTo`) |
| 휠 1200px 에 `scroll` 61(60) · IO 9 | ★ **이 판의 관찰 — `scroll` 쪽 값은 판마다 움직였다.** 대소만 근거 |
| root=상자의 여백은 상자를 넓히고, 뷰포트 여백은 상자의 잘림을 못 넓힌다 | ★ **이 판의 관찰** |
| 교차 출처 iframe 에서 `rootMargin` 무시 | ★ **이 판의 관찰** — 명세 문장은 열지 못했다 |
| 노출 = 50% · 1초 | **설계 권고층**(관례 수치) |
| 비용 | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 이미지 · 동영상 지연 로딩 | 마크업이면 `loading="lazy"`(HTML 34) · 스크립트면 IO + `rootMargin` 으로 미리 · 한 번 불렀으면 `unobserve` | `scroll` 리스너에서 `getBoundingClientRect()`(09편) |
| 무한 스크롤 | 목록 끝의 표지 요소 하나를 IO 로 · 스크롤 상자 안이면 **root 를 그 상자로** | 뷰포트 root + 여백(상자 안에서는 안 넓어진다) |
| 노출 집계 | IO(줄 0.5) + 타이머(1초) + `visibilityState` | IO 콜백 한 번 = 노출 한 번 |
| 스크롤 위치에 따라 매 프레임 그림을 바꾸기(패럴랙스) | `scroll`(passive) + rAF — 매 프레임 값이 필요하다 | IO(줄을 넘을 때만 온다) |
| 큰 요소가 「다 보였나」 | 보이는 높이(`intersectionRect.height`)로 | `threshold: 1` |

## 핵심 문장

1. **IO 는 「지금 상태 한 번 + 줄을 넘을 때마다」 알린다** — 168칸 중 68칸만 왔고, `observe()` 직후에는 **안 보여도** 왔다.
2. **뷰포트보다 큰 요소는 `threshold: 1` 이 영원히 안 온다**(0 / 18).
3. **`rootMargin` 은 root 사각형을 넓히거나 좁힌다** — 음수면 **네 변 모두**, root 가 상자면 **상자를**, 다른 출처 iframe 안에서는 **안 먹었다.**
4. **`isIntersecting` 을 「겹치나」로 읽지 마라** — 줄 아래에서는 비율이 0 보다 커도 `false` 가 왔다. `intersectionRatio` 와 내가 건 줄로 판단한다.
5. **센 것은 호출 수다** — 휠 한 번에 `scroll` 이 IO 보다 많이 불렸다. **비용은 재지 않았다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 35번)
- [09번 주제](../09-element-geometry/2-summary.md) — (10) `getBoundingClientRect()` 로 「화면 안에 있나」를 **직접** 재는 쪽. 여기는 **브라우저가 알려 주는** 쪽
- [19번 주제](../19-passive-and-scroll/2-summary.md) — `scroll`·`wheel` 리스너와 passive. 여기는 그 `scroll` 이 **몇 번 불리나**를 IO 와 견준다
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — 창 ④ 디스패치 계수기의 정본 · `visibilitychange`(노출 집계에서 같이 본다)
- **HTML 갈래 34번**(`img` — `loading`·`decoding`·`fetchpriority`) — 폴더는 아직 없다. 마크업 쪽 지연 로딩은 그쪽 몫
- 목록의 **36번 주제**(`ResizeObserver` — 폴더는 아직 없다) — 크기 변화를 알려 주는 짝

## 용어 풀이

- **`IntersectionObserver`(IO)** — 요소가 root 사각형과 얼마나 겹치는지 **줄을 넘을 때** 알려 주는 관찰자.
- **root** — 겹침을 재는 기준 사각형. 기본은 최상위 뷰포트, 아니면 스크롤 상자 요소.
- **`rootMargin`** — root 사각형을 넓히거나(양수) 좁히는(음수) 여백. CSS `margin` 꼴.
- **`threshold`** — 비율의 줄. 콜백은 줄을 넘을 때만 온다.
- **`intersectionRatio`** — 요소 넓이 중 root 안에 든 넓이의 비율(0\~1).
- **`isIntersecting`** — 이 판에서는 「가장 낮은 줄 이상인가」와 같이 움직인 값((3)).
- **교차 격자** — `threshold` × `rootMargin` × 크기 24벌을 스크롤 일곱 자리에 세운 표. 이 편의 본체.
- **노출 집계** — 「몇 % 이상이 몇 초」를 채운 경우만 세는 것. 관례 수치는 설계의 몫.

## 더 들어가면

- ★★ **명세 원문 대조** — 첫 알림 · `isIntersecting` 의 정의 · 교차 출처 iframe 의 `rootMargin` 을 **명세 문장과 맞대는 일**이 남았다.
- **`trackVisibility`·`delay`**(Intersection Observer v2 — 겹쳐 가려진 것까지 본다) — 던지지 않았다.
- **`scrollMargin`**(스크롤 상자 안쪽 여백) — 던지지 않았다.
