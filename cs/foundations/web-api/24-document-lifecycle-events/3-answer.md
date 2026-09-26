# web-api/24 — 문서 수명주기 이벤트: `DOMContentLoaded`/`load`·`visibilitychange`·`pagehide`/`pageshow` 와 bfcache — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 페이지는 로컬 서버 A 에서 열었고, 링크는 **CDP 로 넣은 진짜 마우스**로 눌렀다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG HTML — Document lifecycle](https://html.spec.whatwg.org/multipage/document-lifecycle.html) 의 unload a document 와 [Chrome 의 unload 폐기 문서](https://developer.chrome.com/docs/web-platform/deprecating-unload)로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 「떠날 때」 격자 전 칸 · CDP 이유 · 문서별 순서 · 이미지 순서 | **안 실었다** — 두 문서가 섞인 순서(렌더러가 다르다) |
| 캡처를 세 판 돌려 **한 글자도 같았다** | **못 잰 것** — 모바일 백그라운드 · 탭 폐기 · 사용자의 창 닫기 · 속도 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 떠나는 쪽은 창고행(`persisted=true`), 도착한 쪽은 새로 섰다

**출력**

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,14p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
링크로 떠나기     ○            persisted=true    (리스너 없음) hidden            persisted=false ○              —
새로 고침         ○            persisted=false   (리스너 없음) hidden            persisted=false ○              —
탭 닫기(Target)   —            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
뒤로(둘째→첫)    ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    떠난 문서(둘째쪽)  beforeunload → pagehide persisted=true → visibilitychange hidden → freeze
    도착한 문서(첫쪽)  resume → visibilitychange visible → pageshow persisted=true
    페이지에게 물음  null
앞으로(첫→둘째)  ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    페이지에게 물음  null
다른 탭을 앞으로  —            —                (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
그 탭에서 돌아옴  —            —                (리스너 없음) visible           (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

**왜 그런가**

- **첫쪽** — `beforeunload → pagehide(persisted=true) → visibilitychange hidden`(「링크로 떠나기」 줄). 리스너가 없어 `unload` 칸은 부적용.
- **둘째쪽** — 처음 여는 문서라 `pageshow persisted=false` 와 `load` ○.
- ★ HTML 의 unload a document 순서 그대로 — **`pagehide` → 가시성 `hidden` → (salvageable 이 거짓일 때만) `unload`**.

### 2. `resume → visible → pageshow(persisted=true)` · `load` 없음

**출력**

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,2p;7,10p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
뒤로(둘째→첫)    ○            persisted=true    (리스너 없음) hidden            persisted=true  —              —
    떠난 문서(둘째쪽)  beforeunload → pagehide persisted=true → visibilitychange hidden → freeze
    도착한 문서(첫쪽)  resume → visibilitychange visible → pageshow persisted=true
    페이지에게 물음  null
(exit 0)
```

**왜 그런가**

- **둘째쪽(떠남)** — `beforeunload → pagehide persisted=true → visibilitychange hidden → freeze`. 창고에 들어가며 얼었다.
- **첫쪽(돌아옴)** — `resume → visibilitychange visible → pageshow persisted=true`. ★ **`DOMContentLoaded` 도 `load` 도 없다** — 같은 문서가 되살아났다.
- 페이지의 `notRestoredReasons` 는 `null` — 되살아났으니 물을 것이 없다.

### 3. 두 쪽 다 `persisted=false` · CDP 는 `UnloadHandlerExistsInMainFrame`, 페이지는 `masked`

**출력**

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '16,17p;22,27p'
[unload 있음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
뒤로(둘째→첫)    ○            persisted=false   (리스너 없음) hidden            persisted=false ○              BrowsingInstanceNotSwapped(Circumstantial), UnloadHandlerExistsInMainFrame(PageSupportNeeded)
    페이지에게 물음  [{"reason":"masked"}]
앞으로(첫→둘째)  ○            persisted=false   ○            hidden            persisted=false ○              BrowsingInstanceNotSwapped(Circumstantial)
    떠난 문서(첫쪽u)  beforeunload → pagehide persisted=false → visibilitychange hidden → unload
    도착한 문서(둘째쪽)  DOMContentLoaded → load → pageshow persisted=false
    페이지에게 물음  [{"reason":"masked"}]
(exit 0)
```

**왜 그런가**

- ★★ **첫쪽u 는 버려졌다** — `pagehide persisted=false → hidden → unload`, 돌아오면 `DOMContentLoaded → load → pageshow persisted=false`.
- ★★ **CDP** — 첫쪽u 로 돌아올 때 **`UnloadHandlerExistsInMainFrame(PageSupportNeeded)`** + `BrowsingInstanceNotSwapped(Circumstantial)`, 둘째쪽으로 앞으로 갈 때 **`BrowsingInstanceNotSwapped`** 하나 — `unload` 가 없는 **둘째쪽도 빠졌다.**
- ★ **페이지** — `[{"reason":"masked"}]`. 같은 질문을 페이지가 물으면 이유가 가려졌다.
- ★ 이 조건은 **Chrome 구현**이다 — HTML 명세에서 「`unload` 리스너가 있으면 bfcache 불가」 문장은 찾지 못했다.

### 4. `beforeunload` 한 칸만 갈린다

**출력**

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,2p;5,6p;16,17p;20,21p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
탭 닫기(Target)   —            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
[unload 있음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
탭 닫기(Target)   —            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
탭 닫기(Page)     ○            persisted=false   ○            hidden            (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

**왜 그런가**

- **`Target.closeTarget` 은 `beforeunload` 가 없고 `Page.close` 는 있다.** 나머지 — `pagehide persisted=false` · `hidden` · (있으면) `unload` — 는 같다.
- CDP 가 `Page.close` 를 「beforeunload 훅을 돌리며 닫으려 한다」로 적는다. **사용자의 진짜 닫기가 어느 쪽인지는 이 도구가 못 본다.**

### 5. `visibilitychange` 만 — `hidden` 그리고 `visible`

**출력**

```text
$ python3 wa24b-net.py life wa24b-24-grid.html | sed -n '1,2p;13,14p'
[리스너 없음]
동작              beforeunload  pagehide          unload        visibilitychange  pageshow        load            CDP 가 말한 bfcache 불가 이유
다른 탭을 앞으로  —            —                (리스너 없음) hidden            (새 문서 없음)  (새 문서 없음)  —
그 탭에서 돌아옴  —            —                (리스너 없음) visible           (새 문서 없음)  (새 문서 없음)  —
(exit 0)
```

**왜 그런가**

- **탭만 가렸으니 문서는 그대로다** — `pagehide` 도 `beforeunload` 도 없고 `visibilitychange → hidden` 하나. 돌아오면 `visible`.
- ★ 그래서 **`pagehide` 만 달면 탭 전환을 못 잡는다.** 모바일에서는 그 상태에서 앱이 죽을 수 있다(이 편은 못 쟀다).

### 6. `DOMContentLoaded` 는 이미지를 안 기다리고 `load` 는 기다린다

**출력**

```text
$ python3 wa24b-net.py page wa24b-24-order.html
파싱 중 스크립트 · readyState=loading
defer 스크립트 실행 · readyState=interactive
DOMContentLoaded · 이미지 complete=false · readyState=interactive
img load · readyState=interactive
load · 이미지 complete=true · readyState=complete
--- 서버 로그 ---
A GET /img  도착 — /go 를 기다린다
A   go 를 받고 이미지를 보냈다
(exit 0)
```

**왜 그런가**

- **파싱 중 스크립트(`loading`) → `defer`(`interactive`) → `DOMContentLoaded`(이미지 `complete=false`)** — 트리는 다 섰다.
- ★★ **`DOMContentLoaded` 리스너가 `/go` 를 줘야 서버가 이미지를 보낸다** — 그 뒤에 `img load` → **`load`(`complete=true` · `readyState=complete`)**. 순서로 묶었으므로 `load` 가 이미지를 기다린다는 것이 시간 없이 증명된다.

### 7. `visibilitychange → hidden`

- (2)의 격자에서 **떠남 여섯 줄과 「다른 탭을 앞으로」 한 줄, 모두 일곱 줄**에서 `hidden` 이 났다.
- 빠진 자리 — **`pagehide`** 는 탭 가림에서 · **`beforeunload`** 는 `Target.closeTarget` 과 탭 가림에서 · **`unload`** 는 리스너가 있어도 **bfcache 로 갈 때와 `Permissions-Policy: unload=()` 일 때**(그리고 Chrome 이 끄는 중이다).
- 그래서 「떠날 때 저장」은 **`visibilitychange → hidden`**(+ `pagehide`)에 단다.

### 8. 명세는 틀, 조건은 Chrome

- **명세(HTML)** — `pagehide`/`pageshow` 의 `persisted`, **`pagehide → hidden → (salvageable 이 거짓이면) unload`** 순서. 어떤 문서를 창고에 넣을지는 명세 문장으로 확인하지 못했다.
- **Chrome** — `unload` 리스너 → `UnloadHandlerExistsInMainFrame` · 옆 쪽까지 `BrowsingInstanceNotSwapped` · **`no-store` 주 문서는 이 판에서 들어갔다** · **`Permissions-Policy: unload=()` 면 `unload` 가 안 불리고 들어갔다**(동작 방식 (5)).

### 9. `load` 가 다시 안 난다 — `pageshow` 의 `persisted` 를 본다

- 되살아난 문서는 **`load`·`DOMContentLoaded` 없이** `pageshow(persisted=true)` 만 받는다(문항 2). 「돌아왔을 때 새로 고칠 것」(로그인 상태·수량)은 **`pageshow` 에서 `e.persisted` 가 참일 때** 한다.

### 10. 다른 주제와 잇기

- **HTML 08번 주제와 문항 6** — 08편이 **`defer`·모듈이 `DOMContentLoaded` 앞**, `load` 가 `complete` 를 쟀다. 문항 6은 그 끝에 **「`load` 는 이미지까지 기다린다」** 한 칸을 서버 붙잡기로 더했다.
- **도구가 못 보는 것** — ① **모바일의 백그라운드 전환·프로세스 강제 종료**(헤드리스 데스크톱에는 운영체제가 탭을 얼리거나 죽이는 경로가 없다 — 「탭 전환」은 새 탭 열기로만 흉내 냈다) ② **사용자의 진짜 창 닫기**(두 CDP 명령이 `beforeunload` 에서 갈렸다). 그 밖에 탭 폐기 · bfcache 의 속도.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **격자** — 줄마다 **새 탭**에서 시작해 준비 동작 뒤 기록을 비우고 잴 동작을 했다. 뒤로·앞으로는 `Page.navigateToHistoryEntry` 뒤 `Page.frameNavigated` 와 `readyState=complete` 를 기다렸다. **떠난 문서가 늦게 적는 줄**까지 받으려고 기록이 **animation frame 20장 연달아 그대로**일 때까지 기다렸다 — 시험판에서 도착한 쪽의 `pageshow` 만 기다렸을 때 떠난 쪽 `pagehide` 가 그 뒤에 적힌 판이 있었다.\
★ **하네스** — [2-summary.md](2-summary.md)의 (1)에 전문이 있다.

```sh
# wa24b-24-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서(서버 둘과 Chrome 을 한 프로세스가 띄운다)
python3 wa24b-net.py life wa24b-24-grid.html
python3 wa24b-net.py page wa24b-24-order.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 「떠날 때」 격자 4판 20줄 | 캡처 3판 | 동작 방식 (2)\~(5) · A1\~A5 · A7 · A8 |
| 이미지를 붙잡은 순서 | 캡처 3판 | 동작 방식 (6) · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `unload` 가 불리나 | 불렸다 | Chrome 이 단계적으로 끄는 중이다 |
| `unload` 리스너 → bfcache 불가 | `UnloadHandlerExistsInMainFrame` | 명세가 아니라 구현이다 |
| `no-store` 주 문서 | 되살아났다 | 조건이 판마다 바뀐다 |
| `notRestoredReasons` | `masked` | 가리는 규칙이 구현이다 |
| `Target.closeTarget` 의 `beforeunload` | 없음 | 도구의 성질 |

**안 돌려 본 것** — ① Firefox·Safari(엔진이 없다). ② iframe 안의 `unload`. ③ `beforeunload` 확인 창. ④ 모바일 백그라운드·탭 폐기.
