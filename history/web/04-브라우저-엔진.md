# 브라우저와 렌더링 엔진 전쟁

> 원본: `~/project/web-history/04-브라우저-엔진.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·표준번호·코드는 원문 그대로다.\
> 용어 블록의 「예:」, 「대가는 무엇인가」, 트레이드오프 표는 원문에 없는 보충 설명이다.

## 한눈에 — 쉽게 말하면

원문이 이 편을 한 줄로 요약한 문장은 이렇다.

> 1994년 Netscape의 등장부터 오늘날 Blink 독점 우려까지 — 브라우저는 두 번의 전쟁을 거치며 렌더링 엔진(Trident·Gecko·WebKit·Blink)과 JS 엔진(V8)의 계보를 만들어 냈다. 누가, 언제, 왜 이겼고 졌는가.

**브라우저 엔진 = 똑같은 설계도를 받아 집을 짓는 여러 시공사.**

- 설계도(HTML·CSS)는 한 장인데, 그걸 읽고 실제 집을 올리는 시공사는 여럿이다.
- 시공사마다 도면 해석이 조금씩 다르면, 같은 도면으로 지은 집의 모양이 달라진다.
- 그래서 건축주(웹 개발자)는 "A사 집에서는 문이 닫히는데 B사 집에서는 안 닫힌다"를 매번 겪는다.
- 시공사가 한 곳만 남으면 집 모양은 통일된다.\
  대신 그 회사가 도면 규칙을 자기 편한 대로 바꿔도 말릴 사람이 없어진다.

이 시공사 이야기가 **똑같은 구조로** 브라우저 엔진의 30년이다.\
도면은 HTML·CSS 표준이고, 시공사는 Trident·Gecko·WebKit·Blink다.

```text
          설계도 = HTML/CSS 표준
                    |
     +---------+---------+---------+
     v         v         v         v
 [Trident]  [Gecko]  [WebKit]  [Blink]
    IE      Firefox   Safari    Chrome
     |         |         |         |
     v         v         v         v
   같은 페이지인데 조금씩 다른 화면이 나온다
```

실무에서 이게 무슨 뜻이냐면 — 원문이 마지막에 드는 우려가 여기서 나온다.\
과거 "**IE6에서만 도는 웹**"이 "**Chrome에서만 도는 웹**"으로 **재현될 수 있다**는 것이다.

> **렌더링(레이아웃) 엔진** — HTML·CSS를 읽어 화면 픽셀로 바꾸는 부품.\
> 예: `<h1>제목</h1>`을 받아 "굵은 32px 글자를 여기에 그린다"까지 정하는 것이 렌더링 엔진이 하는 일이다.

> **JS(JavaScript) 엔진** — 페이지 안의 JavaScript 코드를 실제로 실행하는 부품.\
> 예: 버튼을 눌렀을 때 숫자가 올라가는 동작은 JS 엔진이 돌린다.

> **점유율(market share)** — 전체 사용자 중 그 브라우저를 쓰는 사람의 비율.\
> 예: 점유율 86%면 웹 사용자 100명 중 86명이 그 브라우저를 켠다는 뜻이다.

이 문서가 따라가는 줄거리는 한 줄로 이렇다 — **독점 → 정체 → 도전 → 수렴 → 다시 독점 우려**.

## 전체 타임라인

원문의 연표를 그대로 옮긴 것이다.

| 시기 | 사건 |
|------|------|
| 1994-10 | **Netscape Navigator** 출시 — Mosaic 개발자들이 세운 회사, 초기 웹의 사실상 표준 브라우저 |
| 1995-08-16 | **Internet Explorer 1.0** 출시 — Spyglass Mosaic 라이선스 기반. **1차 브라우저 전쟁** 개전 |
| 1996 | Netscape 점유율 약 86% (IE 약 10%) |
| 1997 | IE 4.0 + **Trident(MSHTML)** 엔진 — Windows 번들 본격화 |
| 1998-01 | Netscape, 소스 공개 → **Mozilla 프로젝트** 발족 (Gecko의 씨앗) |
| 1998-05-18 | **미국 정부, Microsoft 반독점 제소** (US v. Microsoft) — IE 끼워팔기가 쟁점 |
| 1998-11 | **AOL, Netscape 인수** 발표 (1999 완료) — Netscape의 사실상 패배 |
| 2001-08-27 | **IE 6** 출시. 직후 IE 점유율 90% 중반대 정점 → **IE6 정체기** 시작 |
| 2001~2002 | Apple, **KHTML을 포크해 WebKit** 개발 시작 (Safari 2003 탑재) |
| 2004-06 | **WHATWG** 결성(Apple·Mozilla·Opera) — HTML5의 출발점 |
| 2004-11-09 | **Firefox 1.0** 출시 — **2차 브라우저 전쟁** 개전 |
| 2008-09-02 | **Google Chrome** 출시 + **V8** JS 엔진 — 성능 경쟁 점화 |
| 2013-04-03 | **Google, WebKit을 포크해 Blink** 발표 (Opera도 동반 전향) |
| 2017-05 | Chrome, 2차 전쟁 승리 선언 (전 세계 점유율 60%+ ) |
| 2018-12-06 | **Microsoft Edge, Chromium/Blink 전향** 발표 |
| 2020-01-15 | Chromium 기반 새 Edge 정식 출시 — EdgeHTML 독자 엔진 종료 |

오늘날 살아남은 주류 렌더링 엔진은 **Blink·WebKit·Gecko 셋뿐**이며, 그중 Blink 계열이 시장의 70% 이상을 차지한다.\
이 문서는 그 수렴이 어떻게 일어났는지를 따라간다.

## 1차 브라우저 전쟁 (1995–2001): Netscape vs Internet Explorer

*(이 편의 「시대 배경」에 해당한다)*

### 배경 — 웹을 연 Netscape

1994년 10월, NCSA Mosaic을 만들었던 마크 안드레센(Marc Andreessen)과 짐 클라크(Jim Clark)가 세운 회사가 **Netscape Navigator**를 출시했다.\
비상업적 용도 무료 정책에 힘입어 폭발적으로 퍼졌고, **1996년에는 점유율 약 86**%로 초기 웹을 사실상 지배했다.\
당시 "인터넷에 접속한다"는 곧 "Netscape를 켠다"와 동의어였다.

점유율을 그림으로 놓으면 이 시기의 공기가 바로 보인다.

```text
1996년 점유율 (원문 수치)
Netscape  ████████████████████████████████████████████  약 86%
IE        █████                                          약 10%
```

즉 이 시점의 웹은 "Netscape에서 잘 보이면 끝"인 세계였다.

### Microsoft의 반격 — 끼워팔기

Microsoft는 뒤늦게 Spyglass로부터 Mosaic 코드를 사들여 **1995년 8월 16일 Internet Explorer 1.0**을 내놓았다.\
단독 제품으로는 Netscape에 한참 밀렸지만, Microsoft에게는 결정적 무기가 있었다 — **Windows 번들**.\
IE를 OS에 통합해 무료로 끼워 넣고, OEM(PC 제조사)이 다른 브라우저를 기본 설치하거나 IE를 제거하기 어렵게 만들었다.\
운영체제 독점을 브라우저 시장으로 지렛대 삼은 것이다.

> **번들(bundle)** — 다른 제품에 끼워 함께 배포하는 것.\
> 예: Windows를 사면 IE가 이미 깔려 있어서, 사용자가 브라우저를 따로 받을 이유가 없어진다.

> **OEM(주문자 상표 부착 생산)** — 여기서는 완성 PC를 만들어 파는 제조사를 가리킨다.\
> 예: PC 회사가 공장에서 Windows를 깔 때 어떤 브라우저를 기본으로 둘지가 곧 점유율이 된다.

전과 후를 나란히 놓으면 이렇다.

```text
번들 이전 (제품으로 경쟁)         번들 이후 (유통으로 경쟁)
+--------------------------+      +--------------------------+
| 사용자가 브라우저를      |      | PC를 켜면 IE가 이미      |
| 직접 내려받아 설치       |      | 깔려 있다                |
|                          |      |                          |
| -> 사용자가 고른 것만    |      | -> 안 깔아도 쓸 수       |
|    깔린다                |      |    있다                  |
+--------------------------+      +--------------------------+
```

이 전략은 통했지만 대가가 따랐다.\
**1998년 5월 18일, 미국 법무부와 20개 주가 Microsoft를 반독점법(셔먼법) 위반으로 제소**했다(US v. Microsoft).\
핵심 쟁점은 "IE를 Windows에 끼워파는 것이 불법 독점인가"였고, 1999년 11월 5일 법원은 Microsoft가 OS 독점을 남용했다는 사실 인정(findings of fact)을 내렸다.

> **반독점법(셔먼법)** — 한 회사가 시장을 독차지해 경쟁을 막는 행위를 금지하는 미국 법률.\
> 예: 압도적 1위 회사가 자기 지위를 이용해 다른 시장까지 장악하면 여기에 걸린다.

> **사실 인정(findings of fact)** — 재판에서 법원이 "무슨 일이 실제로 있었는가"를 먼저 확정해 두는 단계.\
> 예: 처벌 수위를 정하기 전에 "Microsoft가 OS 독점을 남용했다"는 사실 자체를 법원이 못박은 것이다.

### 결말 — Netscape의 몰락

법정 다툼과 별개로 시장의 승부는 이미 기울어 있었다.\
**1998년 11월 AOL이 Netscape를 인수**하면서 독립 기업으로서의 Netscape는 끝났다.\
다만 Netscape는 패배 직전인 1998년 1월, 브라우저 소스 코드를 공개하며 **Mozilla 프로젝트**를 띄웠다 — 이것이 훗날 Firefox와 Gecko 엔진으로 부활하는 불씨가 된다.\
2001~2002년 무렵 IE는 90% 중반대 점유율로 시장을 사실상 독점했고, 1차 전쟁은 Microsoft의 완승으로 끝났다.

## 무엇이 바뀌었나

### IE6 정체기 (2001–2006): 경쟁이 사라지자 멈춘 웹

**무엇** — 승리한 자는 더 이상 달리지 않았다.\
**2001년 8월 IE6 출시 이후, Microsoft는 약 5년간 새 브라우저를 거의 내지 않았다**(2006년 IE7까지 사실상 메이저 릴리스 공백).\
경쟁이 사라지자 개발 동력도 사라진 것이다.

시간 축으로 그리면 공백이 눈에 보인다.

```text
2001-08  IE6 출시  ──┐
                     │
  2002 ............. │  새 메이저 릴리스 없음
  2003 ............. │
  2004 ............. │   (이 사이에 Firefox 1.0 이 나온다, 2004-11-09)
  2005 ............. │
                     │
2006     IE7      ──┘
```

**왜 문제였나** — IE6가 표준에 한참 못 미친 채로 시장을 독점했다는 점이다.\
독자적인 박스 모델, 비표준 CSS 해석, ActiveX 의존 등으로 "**IE6에서만 도는 웹**"이 양산됐다.\
점유율이 절대적이다 보니 개발자들은 표준이 아니라 IE6에 맞춰 사이트를 만들 수밖에 없었고, 이는 이후 10년 넘게 웹 개발자를 괴롭히는 "IE6 호환 부채"로 남았다.

> **박스 모델(box model)** — 요소의 내용·안쪽 여백·테두리·바깥 여백을 합쳐 가로세로 크기를 계산하는 규칙.\
> 예: 같은 CSS인데 브라우저마다 이 계산 규칙이 다르면 레이아웃이 통째로 어긋난다 — IE6의 "독자적인 박스 모델"이 그런 경우였다.

> **ActiveX** — Windows 전용으로 브라우저 안에서 실행되던 Microsoft의 확장 기술.\
> 예: 사이트가 여기에 기대면 그 페이지는 Windows의 IE 밖에서는 돌지 않는다.

**대가는 무엇인가** — 정체된 독점은 혁신을 멈출 뿐 아니라 생태계를 표준에서 멀어지게 한다는 교훈을 남긴 시기다.

### 2차 브라우저 전쟁 (2004–2017): Firefox와 Chrome의 협공

#### Firefox 2004 — 도전의 시작

**무엇** — Mozilla 프로젝트는 무겁던 Netscape 스위트를 버리고 브라우저 단일 기능에 집중한 **Firefox 1.0을 2004년 11월 9일 출시**했다.

**왜 이게 나은가** — 속도, 탭 브라우징, 팝업 차단, 그리고 무엇보다 **확장 기능**(add-on)과 표준 준수를 무기로 정체된 IE에 균열을 냈다.\
2000년대 후반 Firefox는 20~30%대 점유율까지 올라서며 IE의 독점을 실질적으로 깨뜨린 첫 주자가 됐다.

> **확장 기능(add-on)** — 브라우저에 사용자가 기능을 덧붙이는 작은 프로그램.\
> 예: 광고 차단기나 번역 도구를 설치해 브라우저 자체를 바꾸는 것.

#### Chrome 2008 — 판을 바꾼 신예

**무엇** — **2008년 9월 2일, Google이 Chrome을 출시**했다. Chrome은 두 가지로 차별화했다.

- **속도** — 새로 만든 **V8 JavaScript 엔진**이 경쟁자들보다 압도적으로 빨랐다(아래 JS 엔진 절 참조).
- **단순함과 자동 업데이트** — 미니멀한 UI, 프로세스 분리(탭별 샌드박스), 그리고 사용자가 의식하지 못하는 사이 항상 최신으로 갱신되는 **무중단 자동 업데이트**.

> **샌드박스(sandbox)** — 프로그램을 격리된 울타리 안에서만 돌게 해 바깥을 건드리지 못하게 하는 것.\
> 예: 탭 안의 스크립트가 내 PC의 파일을 마음대로 건드리지 못하는 이유가 이것이다.

**왜 이게 나은가** — 자동 업데이트는 "구버전 고착"이라는 IE6의 실패를 구조적으로 차단했다.

앞 시대와 나란히 놓으면 차이가 분명하다.

```text
IE6 방식 (사용자가 올린다)        Chrome 방식 (알아서 올라간다)
+--------------------------+      +--------------------------+
| 새 버전이 나와도         |      | 백그라운드로 받아        |
| 사용자가 안 받으면       |      | 다음 실행 때 최신        |
| 구버전이 남는다          |      | -> 구버전이 쌓이지 않음  |
+--------------------------+      +--------------------------+
```

Google 검색·광고와의 연계까지 더해지며 Chrome은 빠르게 치고 올라갔고, **2017년 5월 무렵 전 세계 점유율 60%를 넘기며 2차 전쟁의 승자**가 됐다.\
Firefox가 문을 열었고 Chrome이 들어와 시장을 가져간 셈이다.

### 렌더링 엔진 계보: 한 페이지를 그리는 심장

브라우저 전쟁의 이면에는 **렌더링(레이아웃) 엔진**의 계보가 흐른다.\
HTML·CSS를 파싱해 화면 픽셀로 바꾸는 이 엔진이 브라우저의 정체성이다.

계보를 세로로 펼치면 이렇다 — 원문 도식의 노드 문구와 화살표 방향을 그대로 옮기되, **화살표의 종류가 다른 곳에는 라벨을 붙였다**.

```text
[갈래 1 — Mosaic 에서 뻗은 두 줄기. 화살표의 종류가 다르다]

NCSA Mosaic (1993)
   |
   +--(IE 제품 계보 — IE 1.0이 Spyglass Mosaic 기반)--> Trident / MSHTML (IE, 1997)
   |
   +--(Mosaic 개발자들이 세운 회사: 사람)--> Netscape 엔진
                                               |
                                        (1998 소스 공개)
                                               v
                                            Gecko
                                     (Mozilla/Firefox, 1998~)

[갈래 2 — KDE 진영에서 따로 출발한 줄기. 전부 코드 포크다]

KHTML (KDE Konqueror, 1998)
   |
   v  (Apple 이 2001년경 포크)
WebKit (Apple Safari, 2001~)
   |
   v  (Google 이 2013년 포크)
Blink (Google Chrome, 2013 포크)

[갈래 3 — 독자 엔진을 버리고 Blink 로 갈아탄 경우. 코드 파생이 아니라 '전향'이다]

Presto (Opera, 2003)   ...(2013 전향)...>  Blink
Trident                ...(2019 전향)...>  Blink
```

그림 해설 (한 단계씩):

- Mosaic에서 뻗는 두 화살표는 **종류가 다르다**.\
  위쪽은 **IE 제품의 계보**다 — 원문이 말하는 것은 "Microsoft가 Spyglass로부터 Mosaic 코드를 사들여 IE 1.0을 내놓았다"까지이고, **Trident 자체는 원문이 Microsoft의 독자 엔진이라 한다**(IE 4.0, 1997).\
  아래쪽은 Mosaic을 만들던 **사람들**이 나가서 세운 회사다.
- KHTML → WebKit → Blink 는 셋 다 **코드 포크**다 — 있던 소스를 갈라 자기 엔진으로 키운 관계다.
- 맨 아래 두 줄은 화살표 모양이 다르다.\
  Presto와 Trident는 Blink에서 갈라진 것이 아니라, 자기 엔진을 접고 **Blink를 쓰기로 갈아탄** 것이다.

> **포크(fork)** — 남의 소스 코드를 통째로 복사해 와서 자기 방향으로 따로 키우는 것.\
> 예: WebKit 코드를 복사해 Google이 자기 요구대로 고쳐 나간 결과가 Blink다.

#### Trident (Microsoft, 1997)

IE 4.0(1997)과 함께 등장한 Microsoft의 독자 엔진(내부명 MSHTML).\
Windows에 깊이 묶여 있었고, IE6 정체기를 거치며 표준에서 멀어졌다.\
후속작 EdgeHTML(2015, Edge용)으로 한 번 갈라졌으나 2019년 Blink 전향으로 계보 자체가 끝났다.

#### Gecko (Mozilla, 1998~)

1998년 공개된 Netscape 코드를 토대로 Mozilla가 새로 만든 오픈소스 엔진.\
**표준 준수와 크로스 플랫폼**을 기치로 삼아 Firefox를 떠받쳤다.\
상용 회사가 아닌 비영리 재단이 끄는 엔진으로, 오늘날까지 살아남은 **Blink 계열이 아닌 유일한 주류 엔진**이다.\
(Mozilla는 Rust 기반 차세대 실험 엔진 Servo도 만들어, 그 성과 일부를 Gecko에 역수혈했다.)

> **크로스 플랫폼(cross-platform)** — 같은 프로그램이 Windows·macOS·Linux 어디서나 도는 성질.\
> 예: 같은 Firefox를 어느 운영체제에서 켜도 페이지가 같게 보이는 것.

#### WebKit (Apple, 2001~) — KHTML의 후예

WebKit의 뿌리는 의외로 KDE 진영이다.\
리눅스 데스크톱 KDE의 Konqueror 브라우저가 쓰던 **KHTML 엔진을 Apple이 2001년경 포크**해 WebKit을 만들었고, **2003년 Safari**에 탑재했다.\
가볍고 표준 준수가 우수해 빠르게 평판을 얻었고, 특히 **모바일(iPhone Safari, 2007)에서 사실상 표준**이 됐다.\
오늘날에도 iOS의 모든 브라우저는 정책상 WebKit을 써야 한다.

#### Blink (Google, 2013) — WebKit의 포크

초기 Chrome(2008)은 **WebKit을 빌려 썼다**.\
그러나 Chrome의 멀티프로세스 구조(Chromium)와 Apple의 Safari가 점점 갈라지면서 유지보수 비용이 커졌고, **2013년 4월 3일 Google은 WebKit을 포크해 독자 엔진 Blink를 발표**했다.\
같은 시기 Opera도 자체 엔진 Presto를 버리고 Blink로 갈아탔다.\
이후 Edge(2019), Brave, Vivaldi, Samsung Internet 등 대부분의 브라우저가 Blink 계열로 모이며 현재의 구도가 형성됐다.

#### Presto (Opera, 2003)

Opera의 독자 엔진으로 표준 준수(Acid 테스트 만점)에서 앞섰지만 시장 점유는 작았다.\
**2013년 Opera가 Blink로 전향**하며 Presto 계보도 종료됐다.

### JavaScript 엔진 전쟁: V8이 불붙인 JIT 경쟁

렌더링 엔진이 "그리기"라면 **JavaScript 엔진**은 "움직이기"다.\
2008년은 JS 엔진 성능 경쟁이 한꺼번에 폭발한 해였다.

원문 도식을 옮기면 이렇다 — 넷이 각각 화살표를 내어 같은 결과로 모인다.

```text
V8
(Chrome, 2008)              --+
                              |
Nitro / SquirrelFish          |
(Safari, 2008-06)           --+
                              |
TraceMonkey                   +--> JIT(Just-In-Time) 컴파일 경쟁
(Firefox 3.5, 2008-08)      --+    = JS 실행 속도 수십 배 향상
                              |
Chakra                        |
(IE9, 2011)                 --+
```

> **JIT(Just-In-Time) 컴파일** — 프로그램을 미리 기계어로 번역해 두는 대신, 실행하기 직전에 그 자리에서 번역하는 방식.\
> 예: 미리 통째로 번역해 두지 않고, 실행 직전에 그 자리에서 기계어로 번역한다.

> **인터프리터(interpreter)** — 소스 코드를 한 줄씩 읽어 그때그때 해석해 실행하는 방식.\
> 예: 같은 반복문을 100만 번 돌면 100만 번 다시 해석하므로 느리다.

각 엔진을 한 줄씩 풀면 이렇다.

- **V8 (Google, 2008)** — Chrome과 함께 등장.\
  JS 소스를 인터프리터로 한 줄씩 돌리던 관행을 깨고, **실행 직전 기계어로 컴파일**(JIT)해 당대 경쟁자를 압도하는 속도를 냈다.\
  "JS는 느리다"는 통념을 무너뜨렸고, 훗날 **Node.js**의 심장이 되어 JS를 서버까지 끌고 나갔다.
- **Nitro / SquirrelFish (Apple, 2008-06)** — WebKit의 JavaScriptCore에 JIT를 더한 엔진.\
  V8보다 앞선 그해 6월 등장.
- **TraceMonkey (Mozilla, 2008-08)** — SpiderMonkey에 추가된 첫 JIT(추적 기반).\
  Firefox 3.5에 탑재. 이후 JägerMonkey·IonMonkey·WarpMonkey로 세대 교체.
- **Chakra (Microsoft, 2011)** — IE9에 탑재된 JIT 엔진. 2008년부터 개발됐다.

**왜 이게 나은가** — V8이 쏘아 올린 이 **JIT 경쟁**으로 브라우저의 JS 실행 속도는 불과 몇 년 만에 수십 배 빨라졌다.

**왜 하필 이때였나** — Gmail·Google Maps 같은 **무거운 자바스크립트 웹 애플리케이션**(AJAX)이 보편화되면서, JS 속도가 곧 사용자 경험이 되었기 때문이다.

## 표준 수렴, Edge의 전향, 그리고 독점 우려

### 표준의 수렴 — WHATWG와 HTML5

**무엇** — IE6 정체기 동안 W3C는 XHTML·시맨틱 웹에 골몰하며 실제 개발자의 요구와 멀어졌다.\
이에 **2004년 Apple·Mozilla·Opera가 WHATWG를 결성**해 실용적인 **HTML5**를 직접 밀어붙였고, 결국 W3C도 이를 받아들였다(HTML은 이후 WHATWG의 "Living Standard"로 일원화).

> **W3C / WHATWG** — 웹 표준을 만드는 두 단체. 앞은 국제 표준화 컨소시엄, 뒤는 브라우저 제작사들이 모여 만든 실무 조직이다.\
> 예: 오늘날 HTML 명세의 정본은 WHATWG의 "Living Standard" 쪽이다.

> **Living Standard** — 버전을 끊어 발표하지 않고 계속 고쳐 나가는 표준 문서 형식.\
> 예: 버전 번호를 붙여 "완성"을 선언하지 않고, 오늘자 문서가 곧 현재 표준이다.

**왜 이게 나은가** — 동시에 **Acid2(2005)·Acid3(2008)** 같은 공개 표준 준수 테스트가 경쟁 지표가 되면서, 엔진들은 "표준 준수"를 마케팅 포인트로 삼아 서로를 끌어올렸다.\
2차 전쟁은 표준 위에서 벌어진 전쟁이었고, 그 결과 웹은 IE6식 파편화에서 벗어나 수렴해 갔다.

> **Acid 테스트** — 브라우저가 표준을 얼마나 지키는지 점수로 보여 주는 공개 시험 페이지.\
> 예: 만점을 받으면 "우리 엔진이 표준을 가장 잘 따른다"고 광고할 수 있었다.

### Edge의 Blink 전향 (2019)

**무엇** — 수렴의 종착점은 상징적이었다.\
Microsoft는 2015년 Edge용으로 EdgeHTML을 새로 만들었지만 Chrome의 벽을 넘지 못했고, **2018년 12월 6일 Edge를 Chromium/Blink 기반으로 다시 만들겠다고 발표**, **2020년 1월 15일 새 Edge를 정식 출시**했다.

전후를 나란히 놓으면 이렇다.

```text
전 (2015~2018)                    후 (2020~)
+--------------------------+      +--------------------------+
| Edge                     |      | Edge                     |
|   엔진: EdgeHTML         |      |   엔진: Blink (Chromium) |
|   Microsoft 독자 계보    |      |   Google 이 만든 엔진    |
+--------------------------+      +--------------------------+
  Trident -> EdgeHTML 계보          그 계보는 여기서 끝난다
```

한때 IE로 1차 전쟁을 이겼던 회사가 **독자 엔진을 포기하고 경쟁자의 엔진 위에 자기 브라우저를 올린 것**이다.\
Trident→EdgeHTML로 이어진 Microsoft 독자 엔진 계보는 여기서 끝났다.

## 왜 그렇게 갔나 — 남은 선택지와 트레이드오프

### 엔진 독점(monoculture) 우려

전향의 이점은 분명하다 — 모든 주요 브라우저가 같은 엔진을 쓰면 **"이 브라우저에서만 깨지는 사이트"** 문제가 줄고 호환성이 좋아진다.\
그러나 대가도 분명하다.

오늘날 주류 엔진은 **Blink·WebKit·Gecko 셋뿐**이고, 그중 **Blink 계열이 시장의 70% 이상**을 점한다.\
이 "Blink 독점(Chromium monoculture)"에는 여러 우려가 따른다.

> **모노컬처(monoculture)** — 한 종류만 심어 놓은 밭. 여기서는 주류 엔진이 Blink 계열 하나로 쏠린 상태를 가리킨다.\
> 예: 원문이 드는 우려는 사실상 표준의 사유화·표준 권력의 이동·다양성의 상실 셋이다.

- **사실상 표준의 사유화** — Blink의 동작이나 버그가 "표준"으로 굳으면, 명세가 아니라 **Google의 구현이 곧 웹의 규칙**이 된다.\
  과거 "IE6에서만 도는 웹"이 "Chrome에서만 도는 웹"으로 재현될 수 있다.
- **표준 권력의 이동** — 표준 제정이 W3C에서 브라우저 벤더가 주도하는 WHATWG로 옮겨가면서, 절대 다수 점유율을 가진 Google의 영향력이 과대해졌다.
- **다양성의 상실** — 독립 엔진이 줄수록 새로운 아이디어와 견제가 사라진다.\
  Gecko(Mozilla)의 생존이 웹 생태계 다양성의 마지막 보루로 거론되는 이유다.

원문이 든 이점과 우려를 한 표로 마주 놓으면 이렇다.

| | 엔진이 하나로 수렴할 때 |
|---|---|
| 얻는 것 | "이 브라우저에서만 깨지는 사이트" 문제가 줄고 호환성이 좋아진다 |
| 잃는 것 | 사실상 표준의 사유화 · 표준 권력의 이동 · 다양성의 상실 |

### 순환하는 역사

결국 브라우저의 역사는 **독점 → 정체 → 도전 → 수렴 → 다시 독점 우려**라는 순환을 보여 준다.

```text
   독점  ──>  정체  ──>  도전  ──>  수렴  ──>  다시 독점 우려
   (IE6)     (5년 공백)  (Firefox   (표준·     (Blink 70%+)
                          ·Chrome)   Edge 전향)
     ^                                              |
     |                                              |
     +----------------- 같은 자리로 ----------------+
```

IE가 그랬듯, 한 엔진의 독점은 호환성이라는 편익과 혁신 정체·표준 사유화라는 비용을 동시에 안고 있다.

## 남긴 것 — 오늘 우리가 쓰는 것

- **살아남은 주류 렌더링 엔진 셋** — Blink·WebKit·Gecko.\
  우리가 쓰는 거의 모든 브라우저가 이 셋 중 하나 위에 서 있다.
- **V8** — Chrome의 JS 엔진이자 **Node.js**의 심장. JS를 서버까지 끌고 나간 물건이다.
- **자동 업데이트** — Chrome이 "구버전 고착"이라는 IE6의 실패를 구조적으로 차단하려 도입한 장치다.
- **WHATWG의 Living Standard** — 오늘날 HTML 표준의 단일 출처.
- **iOS의 WebKit 정책** — iOS의 모든 브라우저는 정책상 WebKit을 써야 한다.
- **"IE6 호환 부채"라는 교훈** — 정체된 독점이 생태계를 표준에서 어떻게 멀어지게 하는지를 보여 준 사례로 계속 인용된다.

## 용어 풀이

- **렌더링(레이아웃) 엔진** — HTML·CSS를 파싱해 화면 픽셀로 바꾸는 부품. 브라우저의 정체성.
- **JavaScript 엔진** — 페이지 안의 JS 코드를 실행하는 부품. 렌더링이 "그리기"라면 이쪽은 "움직이기".
- **Trident(MSHTML)** — IE 4.0(1997)과 함께 나온 Microsoft의 독자 렌더링 엔진.
- **Gecko** — 1998년 공개된 Netscape 코드를 토대로 Mozilla가 만든 오픈소스 엔진. Firefox의 엔진.
- **Servo** — Mozilla가 만든 Rust 기반 차세대 실험 엔진. 성과 일부가 Gecko로 역수혈됐다.
- **KHTML** — KDE의 Konqueror 브라우저가 쓰던 엔진(1998). WebKit의 뿌리.
- **WebKit** — Apple이 KHTML을 포크해 만든 엔진(2001~). Safari와 iOS의 엔진.
- **Blink** — Google이 2013년 WebKit을 포크해 만든 엔진. Chrome·Edge·Brave 등이 쓴다.
- **Presto** — Opera의 독자 엔진(2003). 2013년 Blink 전향으로 종료.
- **EdgeHTML** — Microsoft가 2015년 Edge용으로 만든 엔진. 2020년 새 Edge와 함께 종료.
- **Chromium** — 원문이 "Chrome의 멀티프로세스 구조"를 가리켜 부른 이름. Edge가 2020년 이 기반으로 옮겨 왔다.
- **포크(fork)** — 남의 소스를 복사해 와 자기 방향으로 따로 키우는 것.
- **V8** — Google이 만든 JS 엔진(2008). JIT로 속도를 올렸고 Node.js의 심장이 됐다.
- **Nitro / SquirrelFish** — WebKit의 JavaScriptCore에 JIT를 더한 Apple의 엔진(2008-06).
- **TraceMonkey** — SpiderMonkey에 추가된 Mozilla의 첫 JIT(2008-08, Firefox 3.5).
- **SpiderMonkey** — Mozilla의 JS 엔진 계보. JägerMonkey·IonMonkey·WarpMonkey로 세대 교체됐다.
- **Chakra** — IE9(2011)에 탑재된 Microsoft의 JIT 엔진.
- **JIT(Just-In-Time) 컴파일** — 실행 직전에 기계어로 번역해 돌리는 방식.
- **WHATWG** — 2004년 Apple·Mozilla·Opera가 결성한 표준 조직. HTML5의 출발점.
- **Living Standard** — 버전을 끊지 않고 계속 갱신하는 표준 문서 형식.
- **Acid2 / Acid3** — 2005·2008년의 공개 표준 준수 테스트. 엔진 경쟁의 지표가 됐다.
- **모노컬처(monoculture)** — 한 종류만 남은 생태계. 여기서는 Blink 계열 편중을 가리킨다.
- **번들(bundle)** — 다른 제품에 끼워 함께 배포하는 유통 방식.
- **샌드박스(sandbox)** — 프로그램을 격리된 울타리 안에서만 돌게 하는 보호 장치.
- **US v. Microsoft** — 1998년 5월 18일 제소된 미국 정부의 Microsoft 반독점 소송.

## 참고 출처

- [Browser wars (Wikipedia)](https://en.wikipedia.org/wiki/Browser_wars)
- [History of the web browser (Wikipedia)](https://en.wikipedia.org/wiki/History_of_the_web_browser)
- [Netscape (web browser) (Wikipedia)](https://en.wikipedia.org/wiki/Netscape_(web_browser))
- [United States v. Microsoft Corp. (Wikipedia)](https://en.wikipedia.org/wiki/United_States_v._Microsoft_Corp.)
- [Comparison of browser engines (Wikipedia)](https://en.wikipedia.org/wiki/Comparison_of_browser_engines)
- [KHTML (Wikipedia)](https://en.wikipedia.org/wiki/KHTML)
- [Presto (browser engine) (Wikipedia)](https://en.wikipedia.org/wiki/Presto_(browser_engine))
- [Microsoft Edge (Wikipedia)](https://en.wikipedia.org/wiki/Microsoft_Edge)
- [JavaScript engine (Wikipedia)](https://en.wikipedia.org/wiki/JavaScript_engine)
- [SpiderMonkey (Wikipedia)](https://en.wikipedia.org/wiki/SpiderMonkey)
- [Acid3 (Wikipedia)](https://en.wikipedia.org/wiki/Acid3)
- [History of Web Browser Engines from 1990 until today (eylenburg.github.io)](https://eylenburg.github.io/browser_engines.htm)
- [Chromium and the browser monoculture problem (DEV Community)](https://dev.to/kenbellows/chromium-and-the-browser-monoculture-problem-420n)
- [Operation convergence: how the W3C and WHATWG fell out (Josh Tumath)](https://joshtumath.github.io/2013/07/16/operation-convergence-the-story-of-how-the-w3c-and-whatwg-fell-out.html)
- [Browser History (Mozilla/Firefox.com)](https://www.mozilla.org/en-US/firefox/browsers/browser-history/)
