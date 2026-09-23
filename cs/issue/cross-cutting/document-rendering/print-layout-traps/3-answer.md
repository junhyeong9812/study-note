# cs/issue/document-rendering/print-layout-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **에러는 없고, 뒤 요소가 페이지 밖으로 나간다.**\
   HTML 파서는 짝이 안 맞는 닫는 태그를 에러 없이 복구한다.\
   `.page`가 예정보다 일찍 닫히면 그 뒤 요소(푸터 등)는 페이지의 자식이 아니라 형제로 배치된다.\
   결과: 푸터 겹침, 쪽 번호 오표기, 다음 쪽 푸터 누락 — 모두 조용히.\
   블록을 통째로 교체하는 편집에서 생기기 쉬워, 검사 스크립트에 "같은 좌표에 중복된 단어" 탐지를 더했다(기존 겹침 검사는 줄 클러스터링이 동일 좌표 중첩을 한 줄로 합쳐 놓쳤다).

2. **본문 마지막 줄을 푸터 구분선이 관통한다.**\
   본문 하한은 `padding-bottom`, 구분선은 `bottom`으로 정해져 서로를 모른다.\
   본문 하한이 구분선 y보다 아래로 가면 겹친다(기록: 좌표 1143.8 < 1151.4).\
   교정: 푸터를 더 아래(10mm → 6mm)로 내려 구분선을 본문 하한 밖으로 뺐다 — 본문 여백을 늘리는 방법은 고아 줄을 만들어 선택하지 않았다.\
   이후 "줄 추가 전에 푸터·여백 여유를 먼저 측정"을 규칙화했다 — 관계를 명시하는 것이 곧 측정 선행이다.

3. **인쇄에서 fixed 요소의 배치는 표준이 느슨하고 엔진마다 달라, 이 렌더러에서는 쪽 여백 쪽에 놓여 클립됐다.**\
   인쇄 조각화(fragmentation)에서 `position: fixed`는 (많은 엔진에서) 매 쪽 반복되지만, 기준 영역·클리핑 처리는 엔진·설정마다 다르다 — 이 사례에선 푸터가 잘리고 텍스트 추출도 0건이 됐다(관측).\
   쪽 번호는 명세에 정의된 `@page { margin: ...; @bottom-right { content: counter(page) } }` 같은 **margin box**로 넣는다 — 단 렌더러의 지원 여부를 확인한다(Chromium 계열은 비교적 최근 버전부터 지원).
   > **paged media** — 연속 화면이 아니라 쪽 단위로 나눠 렌더하는 CSS 모드(인쇄·PDF).

4. **같지 않다 — 다단 컨테이너가 생긴다. 큰 블록의 avoid는 큰 공백을 만든다.**\
   `column-count: 1`도 multi-column 컨테이너를 만들어 쪽 나눔 규칙이 달라지고, 2쪽이 36%만 차고 끊겼다.\
   큰 블록에 `break-inside: avoid`를 걸면 블록이 남은 공간에 안 들어갈 때 통째로 다음 쪽으로 밀려 앞 쪽 하단 절반이 비었다(블록이 한 쪽보다 크면 avoid를 지킬 수 없어 결국 쪼개진다).\
   교정: 다단 규칙 제거, 블록은 `auto`, 줄 단위(항목·제목)와 꼭 필요한 목록만 `avoid`.

5. **height가 원본 비율로 상한 없이 계산되고, 셀에는 기본 여백이 있기 때문이다.**\
   `add_picture(width=...)`만 주면 높이는 원본 비율로 자동 계산된다 — 세로로 긴 이미지는 셀을 뚫는다.\
   워드 표 셀에는 (기본 표 스타일 기준) 좌우 여백(약 108 dxa)이 있어 셀 폭 = 이미지가 쓸 수 있는 폭이 아니다.\
   교정: 원본 비율을 읽어 `max_w × max_h` 박스에 fit한 width·height를 **동시에** 지정하고, 이미지 셀의 여백(`tcMar`)을 0으로, 이후 0.9 배율로 여유를 뒀다.

6. **offset 0(셀 좌상단 고정), 그리고 워드가 열 폭을 자체 계산한다.**\
   문자열 앵커는 `colOff/rowOff = 0`이라 이미지가 셀 좌상단에 붙어 프레임 밖으로 나간다 — 중앙 정렬하려면 `(셀 − 이미지)/2` 오프셋(EMU 정수, 음수 방지)을 가진 앵커를 쓴다.\
   표의 열 격자(`tblGrid`)가 없거나 셀 폭과 맞지 않으면(자동 맞춤이 켜져 있으면 더욱) 워드가 폭을 다시 계산해 지정과 다르게 나온다 — 격자를 명시하고, 셀 폭은 기존 값을 지운 뒤 다시 설정한다(중복 방지).

7. **"에러 없음"이 아니라 실물을 검사해야 한다.**\
   파서 복구·독립 값·인쇄 규칙·라이브러리 기본값은 모두 성공 종료로 끝난다.\
   그래서 검증은 렌더 산출물에서: PDF 좌표 비교(본문 하한 vs 구분선), 쪽 수·쪽 번호, 텍스트 추출, 중복 요소 탐지, 셀 경계 대비 이미지 크기.

## 문제 구조 (추상화 코드)

### 변형 A — 파서 자동 복구가 구조를 바꿈
① 문제 코드
```html
<div class="page">
  <section>...</section></div>   <!-- 블록 교체 편집 중 </div> 중복 -->
  <footer class="footer">3 / 8</footer>
</div>
```
② 고친 코드
```html
<div class="page">
  <section>...</section>
  <footer class="footer">3 / 8</footer>
</div>
<!-- + 검사: 같은 좌표의 중복 단어 탐지 -->
```
깨진 것: 닫는 태그 하나로 푸터가 페이지 밖 형제가 됐고, 파서는 아무 경고도 없었다.

### 변형 B — 서로 모르는 두 값
① 문제 코드
```css
.page   { height: 297mm; padding-bottom: 14mm; position: relative; }
.footer { position: absolute; bottom: 10mm; border-top: 1px solid; }
```
② 고친 코드
```css
.page   { height: 297mm; padding-bottom: 14mm; position: relative; }
.footer { position: absolute; bottom: 6mm; border-top: 1px solid; }  /* 관계: 6mm + 푸터 높이 ≤ 14mm(padding-bottom)여야 구분선이 본문 하한 아래 */
/* 규칙: 본문에 줄을 더하기 전 푸터까지 남은 여유를 먼저 측정 */
```
깨진 것: 본문 하한과 구분선 위치가 독립적으로 정해져 본문이 늘자 겹쳤다.

### 변형 C — 인쇄 CSS 규칙
① 문제 코드
```css
.footer { position: fixed; bottom: 0; }
.content { column-count: 1; }
.section { break-inside: avoid; }
```
② 고친 코드
```css
@page { size: A4; margin: 14mm 16mm 16mm 16mm;
        @bottom-right { content: counter(page); } }
.content { /* 다단 규칙 제거 */ }
.section { break-inside: auto; }
.section li, .section h3 { break-inside: avoid; }
```
깨진 것: 화면용 배치 규칙이 쪽 조각화에서 다르게 동작했다(클립·다단·통째 밀림).

### 변형 D — 문서 라이브러리 기본값
① 문제 코드
```python
cell.paragraphs[0].add_run().add_picture(img, width=col_width)   # height 자동
sheet.add_image(Image(path), "B2")                                # offset 0
```
② 고친 코드
```python
w, h = fit_size(img, max_w=col_width * 0.9, max_h=cell_height)  # 비율 유지 fit
zero_cell_padding(cell)                                         # tcMar = 0
run.add_picture(img, width=w, height=h)

off_x = max(0, (col_px - img_w_px) / 2)
off_y = max(0, (row_px - img_h_px) / 2)
anchor = OneCellAnchor(_from=AnchorMarker(col, int(px_to_emu(off_x)), row, int(px_to_emu(off_y))), ext=size)
sheet.add_image(image, anchor)

set_table_grid(table, col_widths)                                 # 열 격자 명시
```
깨진 것: "셀에 맞춤"을 기본값이 해 줄 거라 가정했지만 기본값은 비율 자동·offset 0·폭 재계산이었다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
