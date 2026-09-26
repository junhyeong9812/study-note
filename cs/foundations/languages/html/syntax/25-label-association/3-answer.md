# html/syntax/25 — `label` 연결과 폼 필드 이름: `for`/`id`·감싸기·클릭 위임 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 클릭은 **CDP 의 진짜 마우스**다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「The label element」·「Interactive content」·`click()` 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑦ 과 창 ② 의 짝이다** — 「끊겼다」는 이름·클릭·`labels` **세 물음이 함께 비는 것**으로 선다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 연결된 넷은 셋 다 살고, 끊긴 넷은 셋 다 죽는다 — `for` 가 빗나가면 품은 칸도 끊긴다 · 끊긴 칸 14 / 27

**출력**

```text
$ python3 html25b-form.py 시도 html25b-25-link.html | sed -n '1,/^$/p'
[for/id]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c1"}
  서버    (받은 요청 없음)
[감싸기]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c2"}
  서버    (받은 요청 없음)
[감싸기 + for 같은 칸]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c3"}
  서버    (받은 요청 없음)
[감싸기 + for 가 없는 id]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[감싸기 + for 가 div]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[감싼 안의 첫째 input]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c6a"}
  서버    (받은 요청 없음)
[감싼 안의 둘째 input]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"c6a"}
  서버    (받은 요청 없음)
[라벨 없음 (옆 글자)]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[aria-label 만]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)

(exit 0)
```

```text
$ python3 html25b-form.py 시도 html25b-25-link.html | sed -n '/^연결 방식/,$p'
연결 방식                 글자 클릭 → input    접근 가능한 이름  nameFrom        labels label.control
for/id                    click 1번 · 켜짐      "동의 1"          relatedElement  1      L1
감싸기                    click 1번 · 켜짐      "동의 2"          relatedElement  1      L2
감싸기 + for 같은 칸      click 1번 · 켜짐      "동의 3"          relatedElement  1      L3
감싸기 + for 가 없는 id   click 0번 · 그대로    ""                (없음)          0      —
감싸기 + for 가 div       click 0번 · 그대로    ""                (없음)          0      —
감싼 안의 첫째 input      click 1번 · 켜짐      "동의 6"          relatedElement  1      L6
감싼 안의 둘째 input      click 0번 · 그대로    ""                (없음)          0      —
라벨 없음 (옆 글자)       click 0번 · 그대로    ""                (없음)          0      —
aria-label 만             click 0번 · 그대로    "동의 8"          attribute       0      —

끊긴 칸 = 14 / 27  (칸 셋 — 글자 클릭이 켰나 · 이름이 있나 · labels 가 1 이상인가)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- **`for`/`id` · 감싸기 · 감싸기 + `for` 같은 칸 · 감싼 안의 첫째** — `click 1번 · 켜짐` · 이름 = 라벨 글자 · `nameFrom` = `relatedElement` · `labels` 1 · 포커스가 그 칸.
- ★★★ **감싸기 + `for` 가 없는 `id` · 감싸기 + `for` 가 `div`** — 칸을 **품고도** `click 0번` · 이름 `""` · `labels` 0 · 포커스 `BODY`. `for` 가 **있으면** 명세의 「안에 든 첫 labelable 요소」 문장은 읽히지 않는다(A6).
- **감싼 안의 둘째** — `click 0번` · `labels` 0. 글자를 누르면 **첫째(`c6a`)가 켜지고 포커스도 `c6a`** 로 간다.
- **라벨 없음** — 셋 다 빈다. **`aria-label` 만** — 이름 `"동의 8"`(`attribute`)만 있고 클릭·`labels` 가 빈다.
- **끊긴 칸 = 14 / 27** — 끊긴 넷 × 3 = 12 + `aria-label` 줄의 2.

### 2. 감싼 라벨의 글자는 `click` 둘 — 둘째(`target`=칸)가 라벨을 다시 지난다 · `for` 로 가리킨 라벨은 안 지난다 · 칸 자체는 하나

**출력**

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '1,27p'
[감싼 라벨의 글자]
  페이지  (기록 없음)
  뒤      click @window target=감쌈글자 isTrusted=true detail=1
          click @감쌈 target=감쌈글자 isTrusted=true detail=1
          click @window target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈칸 target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈 target=감쌈칸 isTrusted=true detail=1 checked=true
          change @감쌈칸 checked=true
          → 감쌈칸.checked=true
  서버    (받은 요청 없음)
[for 로 가리킨 라벨]
  페이지  (기록 없음)
  뒤      click @window target=가리킴 isTrusted=true detail=1
          click @가리킴 target=가리킴 isTrusted=true detail=1
          click @window target=가리킴칸 isTrusted=true detail=1 checked=true
          click @가리킴칸 target=가리킴칸 isTrusted=true detail=1 checked=true
          change @가리킴칸 checked=true
          → 가리킴칸.checked=true
  서버    (받은 요청 없음)
[감싼 라벨의 체크박스 자체]
  페이지  (기록 없음)
  뒤      click @window target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈칸 target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈 target=감쌈칸 isTrusted=true detail=1 checked=true
          change @감쌈칸 checked=true
          → 감쌈칸.checked=true
  서버    (받은 요청 없음)
(exit 0)
```

**왜 그런가**

- ★★★ **감싼 라벨의 글자** — 줄 다섯 + `change`. `click @감쌈 target=감쌈글자`(진짜 클릭) 다음에 **`target=감쌈칸`** 인 `click` 이 `window` → 칸 → **라벨** 순으로 한 번 더 돈다. **라벨의 리스너가 두 번 불렸다.** 둘 다 **`isTrusted=true` · `detail=1`**.
- **`for` 로 가리킨 라벨** — 둘째 `click` 이 `window` → 칸 에서 끝난다(라벨이 조상이 아니다).
- **칸 자체** — `click` 하나(칸 → 라벨로 버블)뿐이다. 라벨의 활성화 동작은 **대화형 콘텐츠 자손**(체크박스)을 향한 이벤트에서 아무것도 안 한다(A7).
- 셋 다 끝의 `checked=true`.

### 3. `input.click()` 을 부르면 두 번 뒤집혀 `false` · 걸러서 부르면 한 번 `true` · `preventDefault` 만이면 칸에 안 간다

**출력**

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '28,57p'
[라벨 리스너가 input.click() 을 부름]
  페이지  (기록 없음)
  뒤      click @window target=부름글자 isTrusted=true detail=1
          click @부름 target=부름글자 isTrusted=true detail=1
          click @window target=부름칸 isTrusted=false detail=0 checked=true
          click @부름칸 target=부름칸 isTrusted=false detail=0 checked=true
          click @부름 target=부름칸 isTrusted=false detail=0 checked=true
          change @부름칸 checked=true
          click @window target=부름칸 isTrusted=true detail=1 checked=false
          click @부름칸 target=부름칸 isTrusted=true detail=1 checked=false
          click @부름 target=부름칸 isTrusted=true detail=1 checked=false
          change @부름칸 checked=false
          → 부름칸.checked=false
  서버    (받은 요청 없음)
[라벨 리스너가 걸러서 부름]
  페이지  (기록 없음)
  뒤      click @window target=거름글자 isTrusted=true detail=1
          click @거름 target=거름글자 isTrusted=true detail=1
          click @window target=거름칸 isTrusted=false detail=0 checked=true
          click @거름칸 target=거름칸 isTrusted=false detail=0 checked=true
          click @거름 target=거름칸 isTrusted=false detail=0 checked=true
          change @거름칸 checked=true
          → 거름칸.checked=true
  서버    (받은 요청 없음)
[라벨 click 에서 preventDefault]
  페이지  (기록 없음)
  뒤      click @window target=막음글자 isTrusted=true detail=1
          click @막음 target=막음글자 isTrusted=true detail=1
          → 막음칸.checked=false
  서버    (받은 요청 없음)
(exit 0)
```

**왜 그런가**

- ★★★ **「부름」** — 라벨의 리스너는 **두 번** 불렸다(`target=부름글자` 한 번, 합성 `click` 이 버블해 `target=부름칸` 한 번). 그중 `input.click()` 이 **무언가를 한 것은 첫 번째 한 번** — 두 번째 호출은 칸의 **click in progress flag** 가 켜져 있어 그냥 돌아갔다(명세의 `click()` 단계). 그 뒤 **라벨의 활성화 동작이 진짜 `click` 을 하나 더** 보내 체크를 되돌렸다. `change` 둘 · 끝 **`false`**.
- ★★ **「거름」** — 라벨 자신을 향한 `click` 에서 `preventDefault()` → 활성화 동작이 **안 돈다.** 토글은 `input.click()` 의 한 번뿐 · 끝 **`true`**.
- **「막음」** — 칸에 아무것도 안 간다(줄 둘) · 끝 **`false`**.

### 4. `span`·`href` 없는 `a` 는 켜고, `a[href]`·`button` 은 안 켠다 · 앞에 단추가 있으면 단추가 연결된 컨트롤이다

**출력**

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '58,$p'
[라벨 안의 span]
  페이지  (기록 없음)
  뒤      click @window target=안쪽글자 isTrusted=true detail=1
          click @안쪽 target=안쪽글자 isTrusted=true detail=1
          click @window target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽칸 target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽 target=안쪽칸 isTrusted=true detail=1 checked=true
          change @안쪽칸 checked=true
          → 안쪽칸.checked=true
  서버    (받은 요청 없음)
[라벨 안의 a[href]]
  페이지  (기록 없음)
  뒤      click @window target=안쪽링크 isTrusted=true detail=1
          click @안쪽 target=안쪽링크 isTrusted=true detail=1
          → 안쪽칸.checked=false
  서버    (받은 요청 없음)
[라벨 안의 href 없는 a]
  페이지  (기록 없음)
  뒤      click @window target=안쪽앵커 isTrusted=true detail=1
          click @안쪽 target=안쪽앵커 isTrusted=true detail=1
          click @window target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽칸 target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽 target=안쪽칸 isTrusted=true detail=1 checked=true
          change @안쪽칸 checked=true
          → 안쪽칸.checked=true
  서버    (받은 요청 없음)
[라벨 안의 button]
  페이지  (기록 없음)
  뒤      click @window target=안쪽단추 isTrusted=true detail=1
          click @안쪽 target=안쪽단추 isTrusted=true detail=1
          → 안쪽칸.checked=false
  서버    (받은 요청 없음)
[button 이 체크박스 앞에 있는 라벨의 글자]
  페이지  (기록 없음)
  뒤      click @window target=앞단추글자 isTrusted=true detail=1
          click @앞단추 target=앞단추글자 isTrusted=true detail=1
          click @window target=앞단추단추 isTrusted=true detail=1
          click @앞단추 target=앞단추단추 isTrusted=true detail=1
          → 앞단추칸.checked=false
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

**왜 그런가**

- ★★ **`span` → `true` · `a[href]` → `false` · `href` 없는 `a` → `true` · `button` → `false`**. 막힌 둘은 **대화형 콘텐츠**다.
- ★★★ **`앞단추`** — 둘째 `click` 이 **`앞단추단추`** 로 갔고 `앞단추칸.checked=false`. 단추가 **안에 든 첫 labelable 요소**라 연결된 컨트롤이 됐다.

### 5. 감싼 칸의 자기 값은 빠진다 · 라벨 둘은 잇는다 · `aria-*` 가 이긴다 · `hidden` 라벨은 `labels` 1 인데 이름 `""`

**출력**

```text
$ python3 html25b-form.py page html25b-25-name.html
id  무엇을                    이름            설명    nameFrom        CDP 이름 출처             labels
n1  감싼 라벨 + 자기 value=3  "수량 "         ""      relatedElement  relatedElement:labelwrapped 1
n2  for 로 가리킨 라벨 둘     "앞 뒤"         ""      relatedElement  relatedElement:labelfor   2
n3  라벨 + aria-label         "에어리아"      ""      attribute       attribute:aria-label      1
n4  라벨 + aria-labelledby    "가리킨 글자"   ""      relatedElement  relatedElement:aria-labelledby 1
n5  title 만                  "제목"          ""      title           attribute:title           0
n6  placeholder 만            "자리표시"      ""      placeholder     placeholder:placeholder   0
n7  라벨 + title              "라벨"          "제목"  relatedElement  relatedElement:labelfor   1
n8  감싼 라벨 안에 select     " 매일 5 번"    ""      relatedElement  relatedElement:labelwrapped 1
n9  hidden 라벨               ""              ""      (없음)          (없음)                    1
(exit 0)
```

**왜 그런가**

- **`n1`** — `"수량 "` — 자기 값 `3` 이 **없다**(HTML-AAM 4.1.1 「감싸여 있으면 자기 값을 뺀다」).
- **`n2`** — `"앞 뒤"` · `labels` 2 · **`n3`·`n4`** — `aria-label`·`aria-labelledby` 가 이기고 `labels` 는 1 로 남는다 · **`n5`·`n6`** — `title`·`placeholder` · **`n7`** — 라벨이 이름, `title` 은 **설명** · **`n8`** — 감싼 안의 `select` 가 **고른 값 `5`** 로 이름에 든다.
- ★★ **`n9`** — `labels` **1** · 이름 **`""`** · `nameFrom` 없음. 연결과 이름이 **갈린 유일한 칸**이다(이 판의 관찰).

### 6. 「`for` 가 지정됐으면 그 `id` 의 첫 요소가 labelable 일 때만」 · 「`for` 가 없으면 안의 첫 labelable 자손」 — 앞 문장이 먼저다

- 명세 — ① 「`for` 속성이 **지정됐고** 그 값과 `id` 가 같은 요소가 트리에 있고 **그 첫 요소가 labelable 이면** 그것이 연결된 컨트롤」 · ② 「`for` 가 **지정되지 않았고** 라벨에 labelable 자손이 있으면 **트리 순서로 첫째**」 · 그리고 「그 밖에는 연결된 컨트롤이 **없다**」.
- ★★ **「감싸기 + `for` 가 없는 `id`」** — `for` 가 **지정됐으므로** ② 로 못 간다. ① 의 조건(그 `id` 의 요소가 있다)이 거짓이니 **연결된 컨트롤 없음**. 안의 체크박스는 **평범한 자식**일 뿐이다(A1 의 `click 0번`).

### 7. 대화형 콘텐츠 자손을 향한 이벤트 · `a` 는 `href` 가 있어야 대화형 · 단추가 첫째면 단추가 컨트롤 — 「연결된 컨트롤이 아닌 labelable 자손을 두지 마라」

- 명세 — 「라벨의 **대화형 콘텐츠 자손**과 **그 자손들**을 향한 이벤트에 대해, 라벨의 활성화 동작은 **아무것도 하지 않는 것**이어야 한다」. 링크를 누르면 링크가, 단추를 누르면 단추가 **자기 일을 하게** 두는 것이다(A4).
- **`href` 없는 `a`** — 대화형 콘텐츠 목록은 `a` 를 **「`href` 속성이 있으면」** 으로만 넣는다. 그래서 A4 에서 **위임이 됐다.**
- **단추가 첫째면** — 단추가 연결된 컨트롤이 되어 **글자를 누르면 단추가 눌린다**(A4 의 `앞단추`). 라벨의 콘텐츠 모델 — 「구절 콘텐츠. 단 **연결된 컨트롤이 아닌 labelable 자손은 두지 않는다**」 — 가 이것을 막으려는 규칙이다. **파서는 고치지 않으므로** 문법 검사기(적합성 검사)만 잡는다.

### 8. `isTrusted` 로는 못 가른다(둘 다 `true`) — `target` 으로 가른다 · 명세는 요구하지 않는다

- **이 판의 두 `click` 은 둘 다 `isTrusted=true` · `detail=1`** 이다(A2). 가르는 것은 **`target`** — 진짜 클릭은 라벨(또는 그 글자), 둘째는 **칸**.
- ★ **명세는 요구하지 않는다** — 활성화 동작은 「플랫폼의 라벨 동작과 맞아야 한다」이고, 예시가 「`click` 을 보낼 **수 있다**」·「포커스만 주거나 **아무것도 안 할 수도**」다. **두 번째 `click` 은 이 판의 관찰**이다.

### 9. 이름은 같고 클릭·`labels` 가 다르다 · 함께 달면 이름은 `aria-label`, `labels` 는 1

- **`aria-label` 만** — 이름 ✓ · 글자 클릭 ✗ · `labels` 0(A1).
- **라벨 + `aria-label`** — 이름은 **`aria-label`**(`nameFrom` = `attribute`) · `labels` **1**(A5 의 `n3`). 클릭 위임은 라벨이 계속 준다.

### 10. 갈린 칸은 없다 · 「click 이 간다」와 「isTrusted=true」는 구현 · 「hidden 라벨은 이름 없음」은 관찰

- **이 주제에서 명세와 갈린 칸은 없었다** — 연결된 컨트롤의 두 문장 · 대화형 콘텐츠 · `click()` 의 재진입 방지 · HTML-AAM 의 이름 순서가 전부 문장 그대로였다.
- **「라벨을 누르면 칸에 `click`」** — 명세가 **허용**하고 이 판이 **그렇게 구현**했다(구현) · **「`isTrusted=true`」** — 구현 · **「`hidden` 라벨은 이름을 안 준다」** — HTML-AAM 이 그 경우를 말하지 않으므로 **이 판의 관찰**.

### 11. 트리는 보조 기술의 입력이다 · 플랫폼은 하나(리눅스 headless Chrome)

- 창 ⑦ 은 Chrome 이 보조 기술에 **넘기는 재료**다. 그것을 **소리로 어떻게 읽는지**는 보조 기술이 정하고, 이 판에는 보조 기술이 없다 — **못 잰 것**.
- **플랫폼 하나** — 명세가 「플랫폼마다 다를 수 있다」고 한 라벨 동작을 **한 플랫폼**에서만 쟀다. 모바일 터치·다른 운영체제는 **안 돌려 본 것**이다.

### 12. 정본 경계

- **호출 순서** — [web-api 16번](../../../../web-api/16-event-propagation-phases/2-summary.md) · **`preventDefault`** — [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md).
- **이름 출처 순서 전체** — 목록의 **43번 주제** · **칸 묶음의 이름** — [27번 주제](../27-fieldset-and-legend/2-summary.md)의 `legend`.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800` · `--force-renderer-accessibility`. **엔진은 이것 하나다.**\
★ **하네스** — [21번](../21-form-submission-model/3-answer.md)의 `html21b-form.py`·`html21b-cdp.py`·`html21b-rec.js` 를 복사해 `html25b-` 로 이름을 바꾸고 넷을 더했다 —
① **표 종류 「종합」**(시도를 다 돈 뒤 페이지를 새로 열고 `window.__종합(결과)` 에 **시도마다의 `뒤` 값과 서버가 받은 필드 목록**을 넘긴다 — 격자를 짜고 「N / M」을 세는 것은 페이지다) ·
② **창 ⑦ 의 내부 덤프**([17번](../17-table-structure/3-answer.md)의 `chrome://accessibility` 부품 — 원래 페이지를 `Target.activateTarget` 으로 앞으로 돌린 뒤 받는다) · CDP 이름의 **출처(`sources`)** ·
③ **`key`/`keyhere` 단계**(글자를 실은 키 · 포커스를 옮기지 않는 키) · **콘솔 기록**(`Log.entryAdded` — 28번) ·
④ **`dom` 모드**(같은 로컬 서버에서 연 페이지의 `--dump-dom` — `file://` 의 muted errors 를 피한다).\
★ **제출 감지는 21번과 같다** — 동작 뒤 **`details` 의 `toggle` 작업**을 DOM 조작 작업 원천에 하나 더 넣고, 그것이 돌 때 **`beforeunload` 가 이미 났나**를 본다. 거짓 「안 갔다」는 **「뒤늦게 온 요청 = N」** 줄이 센다 — 이 배치의 모든 시도 블록이 **0** 이다.\
★ **로케일** — 28번의 격자는 `--lang=ko-KR` 로 던졌다. 하네스는 그것을 **환경 변수 `LANGUAGE=ko_KR`** 로 바꿔 넘긴다(리눅스 Chrome 은 `--lang` 플래그를 안 듣는다 — [23번](../23-input-types-number-date/2-summary.md)).

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌려(`capture.sh blocks` · `blocks-r1` · `blocks-r2`) `normalize-shaky.py` 로 첫 판과 견줬다 — **두 번 다 「블록 48개 · 동일 48 · 흔들린 칸 0 · ★고칠 것 0 · 한쪽에만 0」** 이다. 25\~28번의 블록이 전부 이 48개 안에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **연결 방식 아홉 × 세 물음** | 3 | 동작 방식 (1) · A1 |
| **호출 순서 로그 열한 시도** | 3 | 동작 방식 (2)·(3) · A2\~A4 |
| **이름의 출처 아홉** | 3 | 동작 방식 (4) · A5 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 라벨이 칸에 보내는 `click` | 간다 · `isTrusted=true` · `detail=1` | 명세는 플랫폼에 맡긴다 |
| `hidden` 라벨의 이름 | `""`(`labels` 1) | HTML-AAM 이 그 경우를 말하지 않는다 |
| 이름의 앞뒤 공백 | 남긴다(`"수량 "`) | 이름 계산의 공백 처리는 구현이다 |

**안 돌려 본 것** — ① **텍스트 칸의 라벨 클릭**(이 배치는 체크박스로만 쟀다 — 포커스가 칸으로 가는 것은 체크박스에서 봤다). ② **Shadow DOM 을 건너는 `for`**. ③ **키보드로 라벨을 「누르는」 방법** — 이 배치는 마우스만 던졌다.

**못 잰 것** — ① **스크린리더의 읽기.** ② **다른 플랫폼의 라벨 동작.**

**부적용인 창** — **창 ③ · ④ · ⑤ · ⑥** — **잴 것이 없다**(⑤ 는 시도 블록마다 「서버 (받은 요청 없음)」으로 확인했다).

**하네스 전문** — 26\~28번이 같은 파일을 쓴다.

```python
# html25b-form.py
#!/usr/bin/env python3
"""25~28 폼 — 창 ⑤(서버 요청 로그)·창 ⑦(접근성 트리)·창 ②(노드 프로브)를 한 실행기로 묻는다(21편 하네스를 이었다).

사용: html25b-form.py [--lang=xx-YY] 시도 <페이지> | page <페이지> | ax <페이지> | dom <페이지> | curl
     html25b-form.py 로케일 <페이지> <로케일1> <로케일2>
  · 서버 하나(A)를 이 프로세스 안에 띄운다. 포트는 0 — 운영체제가 고른다(출력에는 서버 이름 A 만 적는다).
  · 서버 로그는 「서버 · 메서드 · 경로 · Content-Type · 질의 · 본문 · 필드」만 적는다. 시각·포트는 안 적는다.
    ★ multipart 의 경계(boundary) 문자열은 실행마다 바뀐다 — 싣지 않고 경계로 본문을 갈라 **필드 목록만** 적는다.
    ★ 필드 값은 디코딩해서 「」 안에 적는다. 퍼센트 인코딩된 원문은 「본문」·「질의」 줄에 그대로 둔다.
  · 시도 — 페이지의 window.__시도 = [{이름, 단계: [...]}, ...] 를 하나씩 돈다.
    시도마다 페이지를 새로 열고 → sessionStorage 를 비우고 → 단계를 실행한 뒤
    (시도에 「뒤」 식이 있고 이동이 없었으면 그 식을 평가해 「뒤」 줄로 찍는다)
    ★ 「제출이 일어났나」는 울타리로 가른다(시간 상수 없음) — 폼 제출의 이동은 DOM 조작 작업 원천의 작업으로
      미뤄지므로, 같은 작업 원천에 details 의 toggle 작업을 하나 더 넣고 그것이 돌 때 beforeunload 가 이미 났나를 본다.
      일어났으면 새 문서의 loadEventFired 를 기다린다. 거짓 「안 갔다」는 「뒤늦게 온 요청 = N」 줄이 센다.
    페이지 쪽 기록(click·submit·invalid)은 html25b-rec.js 가 sessionStorage 에 적어 둔다 —
    같은 출처로 이동해도 같은 탭이면 남는다.
  단계 꼴:
    ["js", 식]                     페이지 안에서 평가한다
    ["click", 선택자]              그 요소 한가운데를 진짜 마우스로 누른다
    ["clickat", 선택자, dx, dy]    그 요소 왼쪽 위에서 (dx, dy) 떨어진 점을 누른다
    ["enter", 선택자]              그 요소에 포커스를 두고 진짜 Enter 를 누른다
    ["type", 선택자, 글자]         그 요소에 포커스를 두고 글자를 입력한다(Input.insertText)
    ["key", 선택자, key, code, 가상키코드[, 글자]]  그 요소에 포커스를 두고 키를 누르고 뗀다(글자를 주면 keyDown 에 싣는다)
    ["keyhere", key, code, 가상키코드[, 글자]]      포커스를 옮기지 않고 지금 포커스에 키를 누르고 뗀다
  · 표 종류 「종합」 — 시도를 다 돈 뒤 페이지를 새로 열고 window.__종합(결과) 가 돌려준 글자를 찍는다.
    결과 = [{이름, 기록, 뒤, 필드: [서버가 받은 필드 이름…] | null}] — 표 짜기·칸 세기는 페이지가 한다.
    window.__뒤숨김 = true 면 시도마다의 「뒤」 줄은 찍지 않는다(종합표가 그 값을 쓴다).
  · page 모드(와 「종합」) — window.__대상 = [[열쇠, 선택자], …] 면 접근성 노드를 window.__AX 로,
    window.__내부 = true 면 내부 덤프(htmlId 열쇠)를 window.__INT 로,
    window.__콘솔 = true 면 그때까지 받은 콘솔 기록(Log.entryAdded 의 글자)을 window.__LOG 로 넣어 준다.
  · --lang=xx-YY — Chrome 을 그 로케일로 띄운다(23편 — 환경 변수 LANGUAGE). 이때 로그에 Accept-Language 를 함께 적는다.
"""
import http.server, importlib.util, json, os, shutil, subprocess, sys, threading, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html25b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)

LOG = []
INFO = []          # 요청마다 격자용 요약 — (메서드, 질의 있나, 본문 종류, Content-Type)
LOCK = threading.Lock()
LANG = None
RESULT = '<!DOCTYPE html><meta charset="utf-8"><link rel="icon" href="data:,"><title>받음</title><p>받음</p>'.encode()


def 값(s):
    return "「" + s.replace("\r", "\\r").replace("\n", "\\n") + "」"


def 필드_urlencoded(raw):
    return [(k, v) for k, v in urllib.parse.parse_qsl(raw, keep_blank_values=True)]


def 적기(label, method, path, headers, body):
    out = []
    ct = headers.get("Content-Type")
    u = urllib.parse.urlsplit(path)
    head = f"{label} {method} {u.path}"
    if ct:
        if ct.startswith("multipart/form-data"):
            head += "  Content-Type=multipart/form-data; boundary=(경계)"
        else:
            head += f"  Content-Type={ct}"
    out.append(head)
    if LANG:
        out.append(f"  Accept-Language  {headers.get('Accept-Language', '(없음)')}")
    out.append(f"  질의  {u.query if u.query else '(없음)'}")
    fields = 필드_urlencoded(u.query) if u.query else []
    if method == "POST":
        if ct and ct.startswith("multipart/form-data"):
            b = ct.split("boundary=", 1)[1].encode()
            parts = body.split(b"--" + b)[1:-1]
            out.append(f"  본문  (multipart — 부분 {len(parts)}개 · 경계로 갈라 필드만 적는다)")
            fields = []
            for p in parts:
                h, _, v = p[2:].partition(b"\r\n\r\n")
                v = v[:-2] if v.endswith(b"\r\n") else v
                hs = h.decode().split("\r\n")
                disp = next(x for x in hs if x.lower().startswith("content-disposition"))
                name = disp.split('name="', 1)[1].split('"', 1)[0]
                extra = []
                if 'filename="' in disp:
                    extra.append("filename=" + 값(disp.split('filename="', 1)[1].split('"', 1)[0]))
                for x in hs:
                    if x.lower().startswith("content-type"):
                        extra.append("부분 " + x)
                fields.append((name, v.decode() + ("" if not extra else "\0" + " · ".join(extra))))
        else:
            text = body.decode()
            out.append(f"  본문  {값(text) if text else '(빈 본문)'}")
            if ct == "text/plain":
                fields = [tuple(line.split("=", 1)) for line in text.split("\r\n") if line]
            else:
                fields = 필드_urlencoded(text)
    else:
        out.append("  본문  (없음)")
    shown = []
    for k, v in fields:
        v, _, extra = v.partition("\0")
        shown.append(f"{k}={값(v)}" + (f" ({extra})" if extra else ""))
    out.append("  필드  " + (" · ".join(shown) if shown else "(없음)"))
    kind = "없음" if method != "POST" else ("multipart" if ct and ct.startswith("multipart")
                                             else "글자 그대로" if ct == "text/plain" else "퍼센트 인코딩")
    info = (method, "있음" if u.query else "없음", kind,
            "multipart/form-data" if ct and ct.startswith("multipart") else (ct or "(없음)"),
            [k for k, _ in fields], u.path)
    return out, info


def server(label):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def 기록(self, method, body=b""):
            if not self.path.endswith(".js"):
                lines, info = 적기(label, method, self.path, self.headers, body)
                with LOCK:
                    LOG.extend(lines)
                    INFO.append(info)

        def 받음(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(RESULT)))
            self.end_headers()
            self.wfile.write(RESULT)

        def do_GET(self):
            self.기록("GET")
            if self.path.startswith("/r"):
                return self.받음()
            return super().do_GET()

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            self.기록("POST", self.rfile.read(n))
            return self.받음()

        def log_message(self, *a):
            pass

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def take_log():
    with LOCK:
        out = LOG[:]
        LOG.clear()
        INFO.clear()
    return out


def take_info():
    with LOCK:
        return INFO[:]


def center(c, sid, sel, off=None):
    at = "[r.x + r.width / 2, r.y + r.height / 2]" if off is None else \
         "[r.x + %s, r.y + %s]" % (json.dumps(off[0]), json.dumps(off[1]))
    xy = cdp.evaluate(c, sid, "(() => { const r = document.querySelector(" + json.dumps(sel)
                      + ").getBoundingClientRect(); return " + at + "; })()")
    if not isinstance(xy, list):
        raise RuntimeError("좌표를 못 얻었다: " + sel + " " + str(xy))
    return xy


def focus(c, sid, sel):
    r = cdp.evaluate(c, sid, "(() => { const e = document.querySelector(" + json.dumps(sel)
                     + "); e.focus(); return document.activeElement === e; })()")
    if r is not True:
        raise RuntimeError("포커스를 못 줬다: " + sel)


def 단계(c, sid, st):
    kind = st[0]
    if kind == "js":
        v = cdp.evaluate(c, sid, st[1])
        if isinstance(v, str) and v.startswith("«예외"):
            raise RuntimeError(st[1] + " -> " + v)
    elif kind in ("click", "clickat"):
        x, y = center(c, sid, st[1], st[2:4] if kind == "clickat" else None)
        c.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y}, sid)
        for t in ("mousePressed", "mouseReleased"):
            c.send("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left",
                   "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)
    elif kind == "enter":
        focus(c, sid, st[1])
        for t in ("keyDown", "keyUp"):
            prm = {"type": t, "key": "Enter", "code": "Enter",
                   "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13}
            if t == "keyDown":
                prm["text"] = "\r"
            c.send("Input.dispatchKeyEvent", prm, sid)
    elif kind in ("key", "keyhere"):
        if kind == "key":
            focus(c, sid, st[1])
            st = st[1:]
        key, code, vk = st[1:4]
        text = st[4] if len(st) > 4 else None
        for t in ("keyDown", "keyUp"):
            prm = {"type": t, "key": key, "code": code,
                   "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
            if text and t == "keyDown":
                prm["text"] = text
            c.send("Input.dispatchKeyEvent", prm, sid)
    elif kind == "type":
        focus(c, sid, st[1])
        c.send("Input.insertText", {"text": st[2]}, sid)
    else:
        raise RuntimeError("모르는 단계: " + kind)


FENCE = """new Promise(r => { const d = document.createElement('details');
  d.addEventListener('toggle', () => r(sessionStorage.getItem('떠남') || '안 떠남'), { once: true });
  document.body.append(d); d.open = true; })"""


def 울타리(c, sid):
    """제출이 계획됐나 — 폼 제출의 이동은 DOM 조작 작업 원천의 작업으로 뒤로 미뤄진다.
    같은 작업 원천에 details 의 toggle 작업을 하나 더 넣고, 그것이 돌 때 beforeunload 가 이미 났나를 본다."""
    r = c.send("Runtime.evaluate", {"expression": FENCE, "awaitPromise": True, "returnByValue": True}, sid)
    v = r.get("result", {}).get("value")
    return v == "1" or "exceptionDetails" in r


def goto(c, sid, url):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)


def 너비(s):
    return sum(2 if ord(ch) > 0x1100 else 1 for ch in s)


def 칸(s, w):
    return s + " " * max(w - 너비(s), 1)


def 시도(c, sid, base, page):
    goto(c, sid, base + page)
    trials = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__시도)"))
    kind = cdp.evaluate(c, sid, "window.__표 || ''")
    names = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸목록 || [])"))
    hide = cdp.evaluate(c, sid, "window.__뒤숨김 === true")   # 「뒤」 값을 종합표만 쓰면 시도 줄에는 안 찍는다
    rows = []
    late = 0
    for t in trials:
        goto(c, sid, base + page)
        cdp.evaluate(c, sid, "sessionStorage.clear(); 1")
        # ★ 앞 시도가 「안 갔다」로 적혔는데 요청이 뒤늦게 왔다면 여기서 잡힌다(이 페이지를 연 요청은 뺀다)
        late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
        take_log()
        for st in t["단계"]:
            단계(c, sid, st)
        went = 울타리(c, sid)
        if went:
            c.wait("Page.loadEventFired", sid)
        rec = json.loads(cdp.evaluate(c, sid, "sessionStorage.getItem('기록') || '[]'"))
        after = cdp.evaluate(c, sid, t["뒤"]) if t.get("뒤") and not went else None
        info = take_info()
        log = take_log()
        print(f"[{t['이름']}]")
        print("  페이지  " + (" → ".join(rec) if rec else "(기록 없음)"))
        if after is not None and not hide:
            print("  뒤      " + str(after))
        for line in log:
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        if not log:
            print("  서버    (받은 요청 없음)")
        rows.append((t["이름"], "났다" if any(r.startswith("submit") for r in rec) else "—",
                     "났다" if any(r.startswith("invalid") for r in rec) else "—",
                     str(len(info)) + "번", info, rec, after))
    if kind == "제출":
        print()
        print(칸("시도", 40) + 칸("submit", 8) + 칸("invalid", 9) + "서버가 받은 요청  「" + rows[0][0] + "」과 갈린 칸")
        hit = total = 0
        for r in rows:
            d = sum(1 for i in (1, 2, 3) if r[i] != rows[0][i])
            if r is not rows[0]:
                hit += d
                total += 3
            print(칸(r[0], 40) + 칸(r[1], 8) + 칸(r[2], 9) + 칸(r[3], 18) + ("(기준)" if r is rows[0] else f"{d} / 3"))
        print(f"서버가 받은 시도 = {sum(1 for r in rows if r[4])} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "싣기":
        print()
        print(칸("시도", 30) + 칸("메서드", 8) + 칸("질의", 6) + 칸("본문", 14) + 칸("Content-Type", 36) + "「" + rows[0][0] + "」과 갈린 칸")
        base_i = rows[0][4][0]
        hit = total = 0
        for r in rows:
            m, q, b, ct = r[4][0][:4]
            d = sum(1 for x, y in zip((m, q, b, ct), base_i[:4]) if x != y)
            if r is not rows[0]:
                hit += d
                total += 4
            print(칸(r[0], 30) + 칸(m, 8) + 칸(q, 6) + 칸(b, 14) + 칸(ct, 36) + ("(기준)" if r is rows[0] else f"{d} / 4"))
        print(f"본문에 실린 시도 = {sum(1 for r in rows if r[4][0][2] != '없음')} / {len(rows)}")
        print(f"갈린 칸 = {hit} / {total}")
    elif kind == "실린":
        print()
        print((칸("칸", 34) + "".join(칸(f"({k + 1})", 6) for k in range(len(rows)))).rstrip())
        for label, field in names:
            print((칸(label, 34) + "".join(칸("실림" if r[4] and field in r[4][0][4] else "—", 6) for r in rows)).rstrip())
        for k, r in enumerate(rows):
            n = sum(1 for _, field in names if r[4] and field in r[4][0][4])
            print(f"({k + 1}) {r[0]} — 실린 칸 = {n} / {len(names)}")
    elif kind == "종합":
        print()
        goto(c, sid, base + page)
        넣기(c, sid)
        res = [{"이름": r[0], "기록": r[5], "뒤": r[6], "필드": (r[4][0][4] if r[4] else None)} for r in rows]
        print(cdp.evaluate(c, sid, "window.__종합(" + json.dumps(res, ensure_ascii=False) + ")"))
    goto(c, sid, base + page)
    late += sum(1 for i in take_info() if not (i[0] == "GET" and i[5] == "/" + page and i[1] == "없음"))
    take_log()
    print(f"뒤늦게 온 요청 = {late}")
    return rows


def 넣기(c, sid):
    """page·종합 공용 — 페이지가 선언한 것(__대상·__내부·__콘솔)을 묻고 결과를 페이지에 넣는다."""
    targets = cdp.evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
    ax = {k: cdp.ax_of(c, sid, sel) for k, sel in json.loads(targets)}
    cdp.evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
    if cdp.evaluate(c, sid, "window.__내부 === true"):
        by = {}
        for n in cdp.internal(c, sid):      # 같은 htmlId 가 둘이면 무시되지 않은 노드를 고른다
            hid = n["속성"].get("htmlId")
            if hid and (hid not in by or "ignored" in by[hid]["속성"]):
                by[hid] = n
        cdp.evaluate(c, sid, "window.__INT = " + json.dumps(by, ensure_ascii=False))
    if cdp.evaluate(c, sid, "window.__콘솔 === true"):
        cdp.evaluate(c, sid, "1")           # 앞서 온 이벤트를 다 받아 둔다
        logs = [e["params"]["entry"]["text"] for e in c.events
                if e.get("method") == "Log.entryAdded" and e.get("sessionId") == sid]
        cdp.evaluate(c, sid, "window.__LOG = " + json.dumps(logs, ensure_ascii=False))


def 화면글자(c, sid, sel):
    """창 ⑦ — 그 입력 칸 아래 StaticText 를 트리 순서로 이어 붙인다(선택도구 단추는 뺀다). 화면에 그려진 글자다."""
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": sel}, sid)["nodeId"]
    be = cdp.backend(c, sid, nid)
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    top = next(n for n in nodes if n.get("backendDOMNodeId") == be)
    out = []

    def walk(n):
        role = cdp.val(n, "role")
        if role == "button":
            return
        if role == "StaticText":
            out.append(cdp.val(n, "name"))
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch])
    walk(top)
    return "".join(out)


def 로케일(page, langs):
    """같은 페이지를 로케일마다 새 브라우저로 열어 — 준비 단계(입력) → 화면 글자 → 제출 → 서버 필드."""
    global LANG
    got = {}
    for lang in langs:
        LANG = lang
        env = {**os.environ, "LANGUAGE": lang.replace("-", "_")}
        a = server("A")
        base = f"http://127.0.0.1:{a.server_address[1]}/"
        proc, c = cdp.start((), env)
        try:
            tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
            sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
            for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
                c.send(m, sid=sid)
            goto(c, sid, base + page)
            nav = cdp.evaluate(c, sid, "navigator.language")
            for st in json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__준비 || [])")):
                단계(c, sid, st)
            ids = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸)"))
            screen = {i: 화면글자(c, sid, "#" + i) for i in ids}
            take_log()
            단계(c, sid, ["click", cdp.evaluate(c, sid, "window.__보냄")])
            if 울타리(c, sid):
                c.wait("Page.loadEventFired", sid)
            info = take_info()
            log = take_log()
        finally:
            proc.terminate()
            proc.wait()
            shutil.rmtree(cdp.PROF, ignore_errors=True)
            a.shutdown()
        body = next(l for l in log if l.strip().startswith("본문"))
        fields = dict(urllib.parse.parse_qsl(body.split("「", 1)[1].rsplit("」", 1)[0], keep_blank_values=True))
        al = next(l for l in log if "Accept-Language" in l).split()[-1]
        got[lang] = (nav, al, screen, fields, body.strip(), len(info))
    L1, L2 = langs
    for lang in langs:
        nav, al, _, _, body, n = got[lang]
        print(f"[{lang}]  navigator.language = {nav} · 요청 {n}번")
        print(f"  Accept-Language  {al}")
        print(f"  {body}")
    print()
    ids = list(got[L1][2])
    print(칸("칸", 5) + 칸(f"화면({L1})", 26) + 칸(f"화면({L2})", 26) + 칸(f"서버({L1})", 20) + f"서버({L2})")
    ds = dv = 0
    for i in ids:
        s1, s2 = got[L1][2][i], got[L2][2][i]
        v1, v2 = got[L1][3].get(i, "(없음)"), got[L2][3].get(i, "(없음)")
        ds += s1 != s2
        dv += v1 != v2
        print(칸(i, 5) + 칸(json.dumps(s1, ensure_ascii=False), 26) + 칸(json.dumps(s2, ensure_ascii=False), 26)
              + 칸(json.dumps(v1, ensure_ascii=False), 20) + json.dumps(v2, ensure_ascii=False))
    print(f"화면 글자가 갈린 칸 = {ds} / {len(ids)}")
    print(f"서버 값이 갈린 칸 = {dv} / {len(ids)}")


def main():
    global LANG
    args = sys.argv[1:]
    extra = []
    env = None
    if args and args[0].startswith("--lang="):
        # ★ 리눅스의 Chrome 은 --lang 플래그를 안 듣는다(실측) — 환경 변수 LANGUAGE 로 로케일을 준다
        LANG = args.pop(0).split("=", 1)[1]
        env = {**os.environ, "LANGUAGE": LANG.replace("-", "_")}
    mode = args[0]
    if mode == "로케일":
        로케일(args[1], args[2:4])
        return
    a = server("A")
    base = f"http://127.0.0.1:{a.server_address[1]}/"
    if mode == "dom":
        # 창 ① — 같은 로컬 서버에서 연 페이지의 --dump-dom (file:// 의 muted errors 를 피한다 — 규칙 34)
        prof = cdp.PROF + "-dom"
        r = subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
                            f"--user-data-dir={prof}", "--dump-dom", base + args[1]],
                           capture_output=True, text=True, env=env)
        shutil.rmtree(prof, ignore_errors=True)
        sys.stdout.write(r.stdout)
        a.shutdown()
        sys.exit(r.returncode)
    if mode == "curl":
        # 폼을 거치지 않고 같은 본문을 직접 보낸다 — 브라우저도, 검증도 없다
        body = "addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5"
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--data", body, base + "r"]
        print("보낸 명령  curl -s -o /dev/null -w '%{http_code}' --data '" + body + "' http://127.0.0.1:<A>/r")
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("  응답 코드 " + r.stdout + " · curl exit " + str(r.returncode))
        for line in take_log():
            print(("  서버    " if line.startswith("A ") else "        ") + line)
        a.shutdown()
        return
    proc, c = cdp.start(extra, env)
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
            c.send(m, sid=sid)
        if mode == "시도":
            시도(c, sid, base, args[1])
        elif mode == "page":
            goto(c, sid, base + args[1])
            넣기(c, sid)
            take_log()
            print(cdp.evaluate(c, sid, "window.__끝()"))
        elif mode == "ax":
            goto(c, sid, base + args[1])
            cdp.dump_tree(c, sid)
        else:
            sys.exit("모드는 시도 | page | ax | dom | curl")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(cdp.PROF, ignore_errors=True)
        a.shutdown()


if __name__ == "__main__":
    main()
```

```python
# html25b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙는 공용 부품 — html25b-form.py 가 불러 쓴다(21편 판 + 17편 판의 내부 덤프를 되살렸다).

사용(단독):
  html25b-cdp.py ax   <url|파일>   접근성 트리 전체를 트리 순서로 찍는다
  html25b-cdp.py page <url|파일>   페이지의 window.__대상 = [[열쇠, 선택자], ...] 마다
                              접근성 노드(역할·이름·설명·무시 여부)를 받아 window.__AX 로 넣고
                              window.__끝() 이 돌려준 문자열을 찍는다(표 짜기·칸 세기는 페이지가 한다)

★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 묻는다.
★ CDP 포트와 프로필 경로는 실행마다 다르다 — 출력에는 안 들어간다.
★ start(extra, env) — 추가 플래그·환경 변수를 주면 그것으로 띄운다(23편의 로케일은 환경 변수 LANGUAGE).
★ internal(c, sid) — chrome://accessibility 의 「blink」 내부 트리 덤프(17편) — CDP 에 없는 nameFrom(이름의 출처)이 거기 있다.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-html25b-{os.getpid()}")
# ★ 포트는 0 — Chrome 이 빈 포트를 고르고 프로필의 DevToolsActivePort 에 적는다.
#   고정 범위에서 무작위로 고르면 같은 기계의 다른 작업과 겹칠 수 있다(뒤 브라우저가 앞에 붙는다).
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--force-renderer-accessibility", "--remote-debugging-port=0",
         f"--user-data-dir={PROF}", "about:blank"]


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(method + " " + json.dumps(r["error"], ensure_ascii=False))
                return r.get("result", {})
            self.events.append(r)

    def post(self, method, params=None, sid=None):
        """응답을 안 기다리고 보낸다 — 디버거 대기 중인 새 창은 run 전까지 답을 안 한다."""
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))

    def wait(self, method, sid=None, pred=lambda p: True):
        """이미 받아 둔 이벤트부터 뒤지고, 없으면 올 때까지 막고 기다린다."""
        while True:
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid) \
                        and pred(e.get("params", {})):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start(extra=(), env=None):
    shutil.rmtree(PROF, ignore_errors=True)
    proc = subprocess.Popen(["google-chrome"] + FLAGS[:-1] + list(extra) + FLAGS[-1:],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def open_page(c, url):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable", "Log.enable"):
        c.send(m, sid=sid)
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)
    return sid


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def val(node, key):
    return (node.get(key) or {}).get("value", "")


def ax_of(c, sid, selector):
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": selector}, sid)["nodeId"]
    if not nid:
        return {"없음": True}
    nodes = c.send("Accessibility.getPartialAXTree",
                   {"nodeId": nid, "fetchRelatives": True}, sid)["nodes"]
    n = next(x for x in nodes if x.get("backendDOMNodeId") and
             x["backendDOMNodeId"] == backend(c, sid, nid))
    kids = [x for x in nodes if x.get("parentId") == n["nodeId"]]
    props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])}
    src = ""
    for x in (n.get("name") or {}).get("sources", []):   # 이름을 실제로 준 출처 — 값이 있고 밀려나지 않은 첫 줄
        if (x.get("value") or {}).get("value") and not x.get("superseded"):
            src = x.get("type", "") + ":" + (x.get("attribute") or x.get("nativeSource") or "")
            break
    return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"), "이름출처": src,
            "무시": bool(n.get("ignored")), "속성": props,
            "표지": [val(x, "name") for x in kids if val(x, "role") == "ListMarker"]}


def backend(c, sid, nid):
    return c.send("DOM.describeNode", {"nodeId": nid}, sid)["node"]["backendNodeId"]


def dump_tree(c, sid):
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    SKIP = {"InlineTextBox"}

    def walk(n, d):
        role = val(n, "role")
        ignored = n.get("ignored")
        if role not in SKIP and not ignored:
            name = val(n, "name")
            props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])
                     if p["name"] in ("level", "selected", "disabled", "multiselectable", "multiline", "checked")
                     or (p["name"] == "url" and role == "link")}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r} {extra}".rstrip())
            d += 1
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch], d)

    for n in nodes:
        if not n.get("parentId"):
            walk(n, 0)


INTERNAL_JS = r"""(async (title) => {
  const until = async (f, what, n = 500) => { for (let i = 0; i < n; i++) { const v = f(); if (v) return v;
    await new Promise(r => setTimeout(r, 20)); }
    throw new Error("내부 덤프 — " + what + " 을 못 기다렸다: pre=" + JSON.stringify([...document.querySelectorAll('#pages pre')].map(q => q.textContent.slice(0, 80)))); };
  const b = await until(() => [...document.querySelectorAll('#pages button')].find(x =>
    x.id.endsWith('showOrRefreshTree') && x.getAttribute('aria-label') === 'Show accessibility tree for ' + title), '단추');
  // ★ 줄이 처음 그려질 때는 모드가 전부 disabled 다 — 「Web: true」로 바뀐 뒤에 눌러야 덤프가 온다
  await until(() => document.querySelector('[aria-label="Web for ' + title + '"][aria-pressed="true"]'), '모드');
  const a = document.getElementById('filter-allow'); a.value = '*'; a.dispatchEvent(new Event('change'));
  // ★ 첫 요청이 빈 트리(「-」)로 돌아오는 판이 있다 — 덤프가 찰 때까지 새로고침 단추를 다시 누른다
  const api = document.getElementById('apiType').value;
  if (api !== 'blink') throw new Error('apiType = ' + api);
  let p = null;
  for (let k = 0; k < 40 && !p; k++) {
    const r = [...document.querySelectorAll('#pages button')].find(x => x.id === b.id) || b;
    r.click();
    try { p = await until(() => { const q = document.querySelector('#pages pre');
      return q && q.textContent.includes('id#=') ? q : null; }, '덤프', 25); } catch (e) { p = null; }
  }
  if (!p) throw new Error('내부 덤프 — 40 번 눌러도 빈 트리다');
  return p.textContent;
})"""


def internal(c, sid):
    """창 ⑦ 의 내부 덤프 — 같은 브라우저의 chrome://accessibility 에 두 번째 창을 열어 받는다."""
    title = evaluate(c, sid, "document.title")
    href = evaluate(c, sid, "location.href")
    sid2 = open_page(c, "chrome://accessibility")
    # ★ 새 창이 앞으로 오면 원래 페이지가 뒤로 밀려 빈 트리(「-」)가 돌아온다 — 원래 페이지를 다시 앞으로
    for t in c.send("Target.getTargets")["targetInfos"]:
        if t["type"] == "page" and t["url"] == href:
            c.send("Target.activateTarget", {"targetId": t["targetId"]})
    text = evaluate(c, sid2, INTERNAL_JS + "(" + json.dumps(title) + ")")
    out = []
    heads = list(re.finditer(r"(\+*)id#=(-?\d+) (\S+)", text or ""))
    if not heads:
        raise RuntimeError("내부 덤프를 못 받았다: " + str(text)[:300])
    for i, m in enumerate(heads):
        body = text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        attrs = {}
        for k, v in re.findall(r"(\w[\w-]*)(?:=('[^']*'|\S+))?", body):
            attrs[k] = v.strip("'") if v else True
        out.append({"깊이": len(m.group(1)) // 2, "역할": m.group(3), "속성": attrs})
    return out


def main():
    mode, url = sys.argv[1], sys.argv[2]
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    proc, c = start()
    try:
        sid = open_page(c, url)
        if mode == "ax":
            dump_tree(c, sid)
        elif mode == "page":
            targets = evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: ax_of(c, sid, s) for k, s in json.loads(targets)}
            evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            print(evaluate(c, sid, "window.__끝()"))
        else:
            sys.exit("모드는 ax | page")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

```javascript
// html25b-rec.js
// 페이지 쪽 기록 — 같은 탭의 sessionStorage 에 적는다(같은 출처로 이동해도 남는다)
const 적기 = s => {
  const a = JSON.parse(sessionStorage.getItem("기록") || "[]");
  a.push(s);
  sessionStorage.setItem("기록", JSON.stringify(a));
};
addEventListener("click", e => {
  const t = e.target.closest("button, input");
  if (t) 적기("click(" + (t.id || t.name) + " · detail=" + e.detail + ")");
}, true);
addEventListener("invalid", e => 적기("invalid(" + e.target.name + ")"), true);
addEventListener("beforeunload", () => sessionStorage.setItem("떠남", "1"));
addEventListener("submit", e => 적기("submit(submitter=" + (e.submitter ? e.submitter.id || e.submitter.name : "null") + ")"), true);
```

```bash
# capture.sh
#!/usr/bin/env bash
# html25b 묶음(HTML 25~28 폼) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 출력 디렉토리를 첫머리에서 절대경로로 정규화한다(규칙 25).
# ★ set -o pipefail — 없으면 파이프 뒤 명령의 종료 코드가 기록된다.
# ★ 자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 — 전부 받아 둔 뒤 필터를 건다.
# ★ grep -c 를 블록의 마지막 명령으로 두지 않는다(0건이면 exit 1).
# ★ 표준 출력만 싣는다 — 표준 오류는 버린다(규칙 18).
# ★ 서버 포트는 운영체제가 고른다 — 출력에는 서버 이름 A 만 나온다. multipart 경계는 하네스가 지운다.
# ★ 페이지는 전부 하네스 안의 로컬 서버로 연다(file:// 의 muted errors — 규칙 34). --dump-dom 도 dom 모드로 같은 서버에서.
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

MARK="sed -n '/^--OUT\$/,/^OUT--\$/{//!p}'"

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

# 출력 블록 — 코드펜스째 뱉는다. 배너 = 실제로 던진 명령 + (있으면) 자르는 필터.
out_block() {  # out_block <블록이름> <열쇠> <명령> [필터]
  local name="$1" key="$2" cmd="$3" pipe="$4" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$cmd" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$cmd"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

form() {  # form <블록이름> <인자…> [-- 필터]
  local name="$1"; shift
  local args="" pipe=""
  while [ $# -gt 0 ]; do
    if [ "$1" = "--" ]; then pipe="$2"; break; fi
    args="$args $1"; shift
  done
  args="${args# }"
  out_block "$name" "form-${args// /_}" "python3 html25b-form.py $args" "$pipe"
}

# 소스 삽입용 블록 — 원고의 펜스 안에 들어가므로 펜스로 감싸지 않는다.
# 배너는 여기서만 찍는다(basename — 규칙 28). 원고에 손으로 쓰면 이중 배너가 된다.
src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_js()   { { printf '// %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version"

# ------------------------------------------------------------ 25 라벨
src_html 25-link-src      html25b-25-link.html
form     25-link-trials   시도 html25b-25-link.html -- "sed -n '1,/^\$/p'"
form     25-link-grid     시도 html25b-25-link.html -- "sed -n '/^연결 방식/,\$p'"
src_html 25-click-src     html25b-25-click.html
form     25-click-base    시도 html25b-25-click.html -- "sed -n '1,27p'"
form     25-click-trap    시도 html25b-25-click.html -- "sed -n '28,57p'"
form     25-click-inner   시도 html25b-25-click.html -- "sed -n '58,\$p'"
src_html 25-name-src      html25b-25-name.html
form     25-name-out      page html25b-25-name.html
src_html 25-demo-src      html25b-25-demo.html
src_html 25-democheck-src html25b-25-democheck.html
form     25-democheck-out dom html25b-25-democheck.html -- "$MARK"

# ------------------------------------------------------------ 26 select·datalist·textarea
src_html 26-sent-src      html25b-26-sent.html
form     26-sent-page     page html25b-26-sent.html
form     26-sent-one      시도 html25b-26-sent.html -- "sed -n '1,6p'"
form     26-sent-multi    시도 html25b-26-sent.html -- "sed -n '7,12p'"
form     26-sent-table    시도 html25b-26-sent.html -- "sed -n '/^칸 /,\$p'"
src_html 26-ta-src        html25b-26-textarea.html
form     26-ta-out        page html25b-26-textarea.html
form     26-ta-dom        dom html25b-26-textarea.html -- "sed -n '/<form/,/<\/form>/p'"
src_html 26-ax-src        html25b-26-ax.html
form     26-ax-out        ax html25b-26-ax.html
src_html 26-demo-src      html25b-26-demo.html
src_html 26-democheck-src html25b-26-democheck.html
form     26-democheck-out dom html25b-26-democheck.html -- "$MARK"

# ------------------------------------------------------------ 27 fieldset·legend
src_html 27-spread-src    html25b-27-spread.html
src_js   27-spec-src      html25b-27-spec.js
form     27-spread-send   시도 html25b-27-spread.html -- "sed -n '/^\[보냄\]\$/,/^\$/p'"
form     27-spread-grid   시도 html25b-27-spread.html -- "sed -n '/^칸 /,\$p'"
src_html 27-name-src      html25b-27-name.html
form     27-name-out      page html25b-27-name.html
src_html 27-demo-src      html25b-27-demo.html
src_html 27-democheck-src html25b-27-democheck.html
form     27-democheck-out dom html25b-27-democheck.html -- "$MARK"

# ------------------------------------------------------------ 28 검증 속성
src_html 28-grid-src      html25b-28-grid.html
src_js   28-spec-src      html25b-28-spec.js
form     28-grid-out      --lang=ko-KR 시도 html25b-28-grid.html -- "sed -n '/^── /,\$p'"
src_html 28-step-src      html25b-28-step.html
form     28-step-out      --lang=ko-KR 시도 html25b-28-step.html -- "sed -n '/^id /,\$p'"
src_html 28-pattern-src   html25b-28-pattern.html
form     28-pattern-out   page html25b-28-pattern.html
src_html 28-length-src    html25b-28-length.html
form     28-length-out    시도 html25b-28-length.html -- "sed -n '/^── /,\$p'"

# ------------------------------------------------------------ 하네스 (25-answer 실행 검증)
src_py   form-py          html25b-form.py
src_py   cdp-py           html25b-cdp.py
src_js   rec-js           html25b-rec.js
src_sh   capture-sh       ../capture.sh
```

## 용어 풀이

- **연결된 컨트롤** — 라벨이 가리키는 칸 하나. `for` 가 있으면 그 `id`, 없으면 안의 첫 labelable 요소.
- **labelable 요소** — 라벨과 이을 수 있는 요소.
- **활성화 동작** — 누르면 일어나는 기본 동작. `preventDefault()` 로 막힌다.
- **click in progress flag** — `click()` 의 재진입을 막는 표시.
- **대화형 콘텐츠** — 사용자 조작용 요소. 라벨은 그것을 향한 이벤트에 아무것도 안 한다.
- **`nameFrom`** — 이름의 출처(내부 덤프).
