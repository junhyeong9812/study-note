# html/syntax/36 — `picture`: 아트 디렉션과 포맷 대체 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [33번 주제](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★★★ **`picture`·`source` 절과 「Images」 절은 이 배치의 사본에 없다** — `source` 고르기의 명세층은 **판정 보류**. 사본에 있는 것 — 콘텐츠 카테고리 목록 · 렌더링 절 · HTML-AAM.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑤ 의 「받은 파일 · 요청 수」다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `picture` — 320 두 칸 정사각 · 나머지 가로(2 / 6) · `srcset` 만 — 320·dpr 1 만 정사각 · 320·dpr 2 는 가로(1 / 6)

**출력**

```text
$ python3 html33b-run.py 격자 html33b-36-art.html
뷰포트 · dpr    picture(media) 가 받은 파일   img srcset 만 가 받은 파일
320 · dpr 1     c400x400.png                  c400x400.png
320 · dpr 2     c400x400.png                  c800x400.png
800 · dpr 1     c800x400.png                  c800x400.png
800 · dpr 2     c800x400.png                  c800x400.png
1400 · dpr 1    c800x400.png                  c800x400.png
1400 · dpr 2    c800x400.png                  c800x400.png
정사각형(c400x400)을 받은 칸 — picture 2 / 6 · srcset 만 1 / 6
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`media` 는 조건 하나로 정한다** — `(max-width: 600px)` 가 참인 320 칸은 DPR 과 상관없이 정사각.
- ★★★ **`srcset` 만은 밀도로 정한다** — 320·dpr 1 은 `c400x400`(400w ÷ 320 = 1.25 ≥ 1), 320·dpr 2 는 `c800x400`(800 ÷ 320 = 2.5 ≥ 2). **자르기는 고려되지 않는다.**

### 2. 가로 둘 → 풀어 줌 → 처음 표지 → **`c400x400?k=p` 새 요청** → 줄인 뒤 표지 → 끝 · `picture` 는 정사각 · `srcset` 만은 가로 그대로

**출력**

```text
$ python3 html33b-run.py 격자 html33b-36-resize.html
  서버    받음  i/c800x400.png?k=p
  서버    받음  i/c800x400.png?k=s
  서버    풀어 줌
  서버    표지  처음 · 1400 · picture c800x400.png?k=p · srcset 만 c800x400.png?k=s
  서버    받음  i/c400x400.png?k=p
  서버    표지  줄인 뒤 · 320 · picture c400x400.png?k=p · srcset 만 c800x400.png?k=s
  서버    표지  끝
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`media` 가 참이 되자 `picture` 는 다른 `source` 를 골라 새로 받았다.**
- ★★★ **`srcset` 만은 다시 안 받았다** — [35번](../35-srcset-and-sizes/2-summary.md) (4) 와 같은 모양(큰 것 유지).

### 3. `t1` webp · `t2` png(첫 `source`) · `t3` 404 로 깨짐(`img` 로 안 넘어감) · `t4` `img` 의 png · `t5` 요청 0·0×0 / 모두 4 개 · 모르는 `type` 의 요청 0

**출력**

```text
$ python3 html33b-run.py 격자 html33b-36-type.html
picture                         서버가 받은 파일                  currentSrc        상자      naturalWidth
t1 x-nope, webp, img(png)       f200.webp                         f200.webp         200×100   200
t2 png, webp, img(png)          g200.png                          g200.png          200×100   200
t3 webp(파일 없음), img(png)    nope.webp                         nope.webp         1000×24   0
t4 x-nope, img(png)             f200.png                          f200.png          200×100   200
t5 img 없는 picture · webp      (없음)                            (img 없음)        0×0       —
type="image/x-nope" 인 source 의 파일(g200.png)을 받은 요청 = 0
서버가 받은 이미지 요청 = 4
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **모르는 `type` 은 건너뛰고 요청하지 않는다** — `x-nope` 둘의 `g200.png` 요청 **0.**
- ★★★ **처음 맞는 `source`** — `t2` 는 `image/png` 가 먼저 맞아 뒤의 `webp` 를 안 봤다.
- ★★★ **깨져도 안 넘어간다** — `t3` 는 `nope.webp` 404 뒤 `f200.png` 를 요청하지 않았다. 상자 `1000×24` 는 **블록으로 놓인 대체 글자 한 줄**이다(`img { display: block }` · `alt="가"`).
- ★★ **`img` 없는 `picture`** — 요청 0 · 0×0.

### 4. 320 — `q1` 정사각 · `"auto 400 / 400"` · 300×300 그대로 · `q2` 정사각 · `"auto 800 / 400"` · 300×150 → 300×300(움직임) / 1000 — 둘 다 가로 · `"auto 800 / 400"` · 300×150 그대로 · 움직인 칸 1 / 4

**출력**

```text
$ python3 html33b-run.py 격자 html33b-36-dims.html
[320 · dpr 1]
  picture                         고른 파일     로드 전 aspect-ratio  로드 전 상자  로드 뒤 상자  아래 요소가 움직였나
  q1 source 에 width/height 있음  c400x400.png  "auto 400 / 400"      300×300       300×300       아니오 (316 → 316)
  q2 source 에 width/height 없음  c400x400.png  "auto 800 / 400"      300×150       300×300       예 (522 → 672)
[1000 · dpr 1]
  picture                         고른 파일     로드 전 aspect-ratio  로드 전 상자  로드 뒤 상자  아래 요소가 움직였나
  q1 source 에 width/height 있음  c800x400.png  "auto 800 / 400"      300×150       300×150       아니오 (166 → 166)
  q2 source 에 width/height 없음  c800x400.png  "auto 800 / 400"      300×150       300×150       아니오 (372 → 372)
움직인 칸 = 1 / 4
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **고른 `source` 에 `width`/`height` 가 있으면 그것이 로드 전 비율**이다(`q1` 320 칸).
- ★★★ **없으면 `img` 의 속성**(`q2`) — 가로 비율로 자리를 잡았다가 정사각이 오며 **늘었다.**
- ★ 명세 사본은 「`img` 의 **dimension attribute source**」라고만 적는다 — 그 정의는 사본에 없어 **관찰까지.**

### 5. `picture` — `generic` · `""` · `false` · `source` — `generic` · `""` · `false` · `img` — `image` · 「초록 사각형」 · `false` / 둘 다 `inline`

**출력**

```text
$ python3 html33b-form.py page html33b-36-ax.html
요소    역할            이름              무시
pic     generic         ""                false
src1    generic         ""                false
img1    image           "초록 사각형"     false
img1.currentSrc = f200.webp
display — picture inline · source inline
(exit 0)
```

```text
$ python3 html33b-form.py ax html33b-36-ax.html
RootWebArea    이름='36 picture 의 접근성 노드'
  generic        이름=''
    generic        이름=''
      generic        이름=''
      image          이름='초록 사각형'
(exit 0)
```

**왜 그런가**

- ★★★ **이름은 `img` 의 `alt` 에서만** — `source` 의 `title` 은 이름이 되지 않았다.
- ★★ **`generic`** — HTML-AAM 의 「Not mapped」는 「노출할 필요가 없다 · 그려지면 generic SHOULD」. 둘 다 `inline` 으로 **그려지는** 판이라 **어긋나지 않는다**(판별).

### 6. 「같은 그림의 크기」로 여긴다 — 필요한 밀도에 맞는 후보를 자르기와 상관없이 고른다 · 320·dpr 2 칸

- A1 — `srcset` 만 쓴 쪽이 320 칸에서 **DPR 에 따라 자르기가 바뀌었다.** 게다가 창을 바꿔도 큰 것을 유지했다(A2).
- `media` 는 **조건이 참이면 그 `source`** — 이 판에서 칸마다 조건대로였다.

### 7. 확인하는 것 — 「이 포맷을 아나」 · 확인하지 않는 것 — 「그 파일이 있나 · 정말 그 포맷인가」 / `t1`(모르는 `type` 건너뜀) · `t3`(깨져도 안 넘어감)

- `x-nope` 는 요청 0 — 판정이 **요청 전에** 끝났다.
- `webp` 는 알아서 골랐고, 파일이 없어도 **그것으로 끝났다.**

### 8. 처음 맞는 것 — 원하는 포맷을 **위에** 적는다

- A3 `t2` — `image/png` 가 위에 있어서 `webp` 는 쓰이지 않았다. 흔한 순서는 **`avif` → `webp` → `img`(png/jpeg)** 다(이 판은 AVIF 를 받지 못했다 — 머리말).

### 9. `alt` — `img` · 크기 스타일 — `img` · `width`/`height` — 각 `source` 와 `img` / `img` 를 빼면 **아무것도 없다**(요청 0 · 0×0)

- A3 `t5` · A4 · A5 가 근거다. `picture` 는 **`inline` 틀**이다.

### 10. 흐름 · 구절 · **임베디드** — 사본의 「Embedded content」 목록에 `picture` 가 있다

- 이 배치가 연 사본(`dom` 절) — 「audio canvas embed iframe img math object **picture** svg video」.
- ★ [05번](../05-content-categories-and-models/2-summary.md) (1) 의 그림은 임베디드 칸에 `picture(는 아님)` 이라 적었다 — **이 사본과 다르다.** 그 그림은 명세 정의를 옮긴 것이라 스스로 밝히므로 **다시 대조할 자리**다(이 편은 05번을 고치지 않는다).

### 11. 요청 수 — 구현(관찰) · 깨진 뒤 — 구현 · 트리 역할 — 명세(판별 — 맞다) · `width`/`height` 조건 — 관찰(정의는 판정 보류) · AVIF — 구현

- 이 배치가 **판정할 수 있는 것은 트리 역할 하나**다(HTML-AAM 사본).
- 나머지 넷은 **`picture`·`source`·「Images」 절이 사본에 없어** 이 판의 Chrome 동작으로만 적는다 — **이탈로 세지 않는다.**

### 12. 정본 경계

- **`srcset`/`sizes` 의 계산** — [35번](../35-srcset-and-sizes/2-summary.md).
- **자리 예약** — [34번](../34-img-alt-size-and-loading/2-summary.md).
- **`video` 의 `source` 목록** — 목록의 **37번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 칸마다 **새 탭 · 캐시 끔 · CDP 뷰포트/DPR**. **엔진은 이것 하나다.** 하네스는 [33번](../33-output-progress-meter/3-answer.md)의 `html33b-run.py`·`html33b-form.py`·`html33b-make-images.py` 다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

★ **포맷** — `f200.webp` 는 생성기가 Chrome 의 `canvas.toDataURL('image/webp')` 로 만든 진짜 WebP 다([34번](../34-img-alt-size-and-loading/2-summary.md)의 「예시 데이터」). AVIF 는 인코더가 없어 만들지 못했다(정리 파일의 `command -v` 블록 · `canvas` 의 `image/avif` → `image/png`).

**흔들림 확인** — 캡처 세 판의 재대조는 [33번](../33-output-progress-meter/3-answer.md)의 `## 실행 검증` 에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **아트 디렉션 여섯 칸 × 두 방식** | 3 | 동작 방식 (1) · A1 |
| **줄인 뒤** | 3 | 동작 방식 (2) · A2 |
| **`picture` 다섯** | 3 | 동작 방식 (3) · A3 |
| **`source` 의 속성 2 칸 × 둘** | 3 | 동작 방식 (4) · A4 |
| **트리 노드 셋** | 3 | 동작 방식 (5) · A5 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 고른 `source` 의 파일이 깨졌을 때 | `img` 로 안 넘어감 | 선택 절이 사본에 없다 |
| 창을 바꾼 뒤 | `media` 는 다시 · `srcset` 만은 유지 | 구현의 선택일 수 있다 |
| `canvas` 의 AVIF | `image/png` 로 돌아옴 | 판이 오르면 바뀔 수 있다 |

**안 돌려 본 것** — ① **AVIF 파일.** ② **`source` 안의 `w` 서술자 + `sizes`.** ③ **한 `source` 에 `media` 와 `type` 을 같이.**

**못 잰 것** — ① **그 선택이 명세의 규칙인가**(사본 없음). ② **포맷마다의 화질.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥**.

## 용어 풀이

- **아트 디렉션** — 조건마다 다른 자르기·구도.
- **포맷 대체** — 새 포맷을 먼저, 모르면 옛 포맷.
- **처음 맞는 `source`** — 위에서부터 조건이 맞는 첫 칸.
