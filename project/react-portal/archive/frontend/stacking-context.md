# Stacking Context

> **한 줄**: z-index는 전역 숫자 경쟁이 아니다. **같은 stacking context 안에서만** 비교된다. 부모가 stacking context를 만들면, 자식의 z-index가 아무리 커도 부모 밖의 요소를 이길 수 없다.

## 이해의 흐름 — 처음 질문에서 시작하기

> 전체 Q&A: [03-internals-qa Q1](../learning/pr1/03-internals-qa.md)

### "Portal은 z-index를 활용하는 기능 같은데?"

```text
처음 그린 그림                         실제 — 순서가 반대
Portal = z-index를 크게 줘서           ① z-index만으로는 못 이김 (부모 층에 갇힘)
         맨 위로 올리는 기능               .card(z:1) 층 안의 모달(z:9999) < header(z:2)
                                       ② 그래서 DOM을 body로 옮겨 층을 탈출 (Portal)
                                       ③ 옮긴 뒤, body 최상위에서 z-index로 순서 정리 (layers.js)
```

**Portal은 z-index를 쓰는 기능이 아니라, z-index만으로는 안 되는 문제를 푸는 기능이다.** z-index는 옮긴 **다음** 단계에서 쓴다.

## 브라우저가 실제로 하는 일

화면을 그릴 때 브라우저는 요소들을 **층(stacking context)** 단위로 묶고, 층 안에서 순서를 정한 뒤, 층 자체를 한 덩어리로 부모 층에 끼워 넣는다.

```
루트 stacking context (html)
├ header       z-index: 2   ────────────────┐ 이 둘끼리 비교
└ .card        z-index: 1   ────────────────┘ → header가 위
   └ (.card가 만든 stacking context)
      └ .modal z-index: 9999  ← .card 층 "안에서만" 9999
                                → .card 층 전체가 header 아래이므로 modal도 header 아래
```

## 무엇이 stacking context를 만드나 (주요)

- 루트 요소 (`html`)
- `position: relative | absolute` + `z-index`가 `auto`가 아닌 값
- `position: fixed | sticky` (z-index 무관)
- flex/grid 아이템 + `z-index`가 `auto`가 아닌 값
- `opacity` < 1
- `transform`, `filter`, `perspective`, `clip-path`, `mask` 가 `none`이 아닌 값
- `isolation: isolate`
- `will-change`에 위 속성 지정
- `contain: layout | paint`

`transform: translateZ(0)`나 `opacity: 0.99`처럼 **의도치 않게** 만드는 경우가 흔하다.

## z-index는 positioned 요소에만

```css
.a { z-index: 10; }                     /* position: static(기본) → 무시됨 */
.b { position: relative; z-index: 10; } /* 적용됨 */
```
flex/grid 아이템은 예외로 position 없이도 적용된다.

## 한 층 안의 그리기 순서 (아래 → 위)

1. 층을 만든 요소의 배경·테두리
2. 음수 z-index 자식
3. 일반 블록 요소 (위치 지정 안 된 것)
4. float
5. 인라인 요소
6. `z-index: auto | 0`인 위치 지정 요소
7. 양수 z-index 자식 (작은 값부터)

같은 값이면 **DOM 순서상 뒤의 것**이 위.

## 해결책: 같은 층으로 올린다

부모의 층에 갇힌 요소를 위로 올리려면 z-index를 키우는 게 아니라 **층을 벗어나야** 한다.
- DOM을 body 최상위로 옮긴다 (**Portal**) → 모든 모달·툴팁이 루트 층에서 공정하게 비교된다.
- 그다음 그 안에서 z-index 규칙(레이어 스택)으로 순서를 정한다.

## 이 프로젝트에서

- 데모 카드 `position: relative; z-index: 1` (`demo/style.css`) → 층을 만듦 → 안의 모달은 `z-index: 9999`여도 헤더(`z-index: 2`) 아래.
- portal 컨테이너는 전부 body 직속 → 루트 층에서 비교. `src/layers.js`가 열린 순서대로 `1000 + i` 부여.
- portal 컨테이너에 `position: relative` (`src/portal.js`) → z-index가 적용되도록.

## 흔한 함정

- **z-index 숫자 인플레이션**: 9999, 99999… 층 문제는 숫자로 못 푼다.
- **애니메이션용 transform이 층을 만듦**: 부모에 `transform`을 넣자 자식 드롭다운이 갑자기 가려진다.
- **position 없이 z-index**: 아무 효과 없음 (flex/grid 아이템 제외).
- **디버깅**: 개발자 도구 Layers 패널(Chrome)이나 Elements의 Computed에서 해당 속성을 확인한다.
