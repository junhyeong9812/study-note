# python/python-data-science/12 — Plotly 인터랙티브 차트 — 정리 (힌트)

> 출처 — study-site 항목 `python/plotly-interactive`(항목 데이터 `data/python/data-science.json`) · 정답 코드 study-practice `python/python-data-science/reference/plotly-interactive.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Plotly 차트는 「종이 지도」가 아니라 「지도 앱」이다.**
종이 지도는 인쇄된 그대로만 본다.
지도 앱은 손가락으로 확대하고, 끌어서 옮기고, 핀을 누르면 가게 정보가 뜬다.
링크를 보내면 받은 사람도 똑같이 확대하고 눌러 볼 수 있다.
Plotly 도 똑같은 구조다.
Matplotlib 그림이 종이 지도라면, Plotly 그림은 브라우저에서 확대(줌) · 이동(팬) · 마우스 올리기(호버)가 되는 지도 앱이다.

> **인터랙티브(interactive)** — 보는 사람이 조작하면 화면이 반응하는 성질이다.\
> 예: 차트 위에 마우스를 올리면 그 점의 값이 뜬다.

| 비유 | 실체 |
|---|---|
| 종이 지도 | Matplotlib 의 정적 그림 |
| 지도 앱 | Plotly 의 `fig` (Figure) |
| 핀을 눌러 정보 보기 | 호버 (`hover_data`, `hovermode`) |
| 손가락으로 확대 · 끌기 | 줌 · 팬 |
| 지도 링크 보내기 | `fig.write_html('scatter.html')` |
| 관제실 화면 — 다이얼을 돌리면 지도가 바뀜 | Dash 대시보드 + 콜백 |

```text
  DataFrame ──► px.scatter(...)  ──┐
                                   ├──► Figure(fig) ──► fig.show()        (브라우저에서 조작)
  go.Figure() + add_trace(...) ────┘                └─► fig.write_html() (HTML 파일로 공유)

  Dash: [드롭다운] [슬라이더] ──입력 바뀜──► 콜백 함수 ──새 fig──► [그래프]
```

## 이 주제가 답하려는 질문

1. DataFrame 하나로 인터랙티브 차트를 가장 빨리 만들려면 무엇을 쓰나?
2. 선 색 · 점선 · 여러 데이터 겹치기 · 호버 방식처럼 세밀하게 손대려면 무엇을 쓰나?
3. 여러 차트를 한 화면에 격자로 놓으려면 어떻게 하나?
4. 사용자가 값을 고르면 차트가 바뀌는 대시보드는 어떤 구조로 짜나?

## 동작 방식

### (1) Plotly Express — 열 이름을 인자에 꽂으면 차트가 나온다

**언제 쓰나** — 데이터가 DataFrame 에 있고, 빨리 모양을 보고 싶을 때(탐색 단계) 쓴다.
원본의 팁대로 「한 줄로 인터랙티브 차트를 생성한다」.

```text
df (열: sepal_width, sepal_length, species, petal_length, petal_width)
        │
        ▼
px.scatter(df, x='sepal_width', y='sepal_length',
           color='species', size='petal_length',
           hover_data=['petal_width'], title=..., template='plotly_white')
        │
        ▼
fig  ──► fig.show()                 브라우저에서 인터랙티브 차트가 열린다
     └─► fig.write_html('scatter.html')   HTML 파일로 저장된다
```

- `x` · `y` 에 열 이름을 넣으면 그 열이 가로축 · 세로축이 된다.
- `color='species'` 는 종(species)마다 다른 색으로 점을 칠한다.
- `size='petal_length'` 는 그 열 값에 따라 점 크기를 달리한다.
- `hover_data=['petal_width']` 는 마우스를 올렸을 때 그 열 값도 보여 준다.
- `template='plotly_white'` 는 테마(배경 · 격자의 꾸밈 세트)를 고른다.
- `fig.show()` 는 차트를 띄우고, `fig.write_html(...)` 은 파일로 남긴다.

> **호버(hover)** — 마우스 포인터를 요소 위에 올려 두는 동작이다.\
> 예: 점 위에 포인터를 올리면 `petal_width` 값이 말풍선으로 뜬다.

원본은 내장 데이터셋 셋을 쓴다: `px.data.iris()` (붓꽃) · `px.data.tips()` (식당 팁) · `px.data.gapminder()` (나라별 연도 · GDP · 기대수명 · 인구).
막대 그래프 `px.bar(tips, x='day', y='total_bill', color='sex', barmode='group')` 는 요일별 결제액을 성별로 나란히 세운다.
`barmode` 에는 `'stack'`(쌓기) · `'group'`(나란히) · `'overlay'`(겹치기)를 넣는다.
라인 차트는 `gapminder.query("country in ['South Korea', 'Japan', 'China']")` 로 세 나라만 거른 뒤 `px.line(..., color='country', markers=True)` 로 나라별 선을 긋고 점도 찍는다.

### (2) Express 의 여러 차트 — 함수만 바꾸면 차트 종류가 바뀐다

**언제 쓰나** — 분포 · 비교 · 상관 · 비율 · 3차원 · 시간 변화처럼 보고 싶은 것이 다를 때 함수를 고른다.

```text
px.histogram  ─ 분포         nbins=30 (막대 개수), marginal='box' (옆에 작은 요약 그림)
px.box        ─ 분포 비교    notched=True (중앙값 부근을 오목하게)
px.violin     ─ 분포 모양    box=True (안에 박스), points='all' (점 전부 표시)
px.imshow     ─ 행렬 히트맵  text_auto='.2f' (칸에 소수 둘째 자리 숫자), color_continuous_scale='RdBu_r'
px.pie        ─ 비율         names= (조각 이름), values= (크기), hole=0.3 (가운데 구멍 → 도넛)
px.scatter_3d ─ 3차원 산점   z= 가 하나 더 붙는다
px.scatter    ─ 애니메이션   animation_frame='year', animation_group='country'
```

- `marginal` 에는 `'rug'` · `'violin'` · `'box'` 를 넣는다.
- 히트맵은 `tips.select_dtypes(include='number').corr()` 로 숫자 열끼리의 상관계수 표를 먼저 만들고 그 표를 `px.imshow` 에 넘긴다.
- 애니메이션은 `animation_frame='year'` 로 연도마다 한 장면을 만들고, `animation_group='country'` 로 장면 사이에서 같은 나라를 같은 점으로 잇는다.
- 같은 호출의 `log_x=True` 는 가로축을 로그 눈금으로, `size_max=60` 은 가장 큰 점의 크기 상한을, `range_y=[25, 90]` 은 세로축 범위를 정한다.
- 세로축 범위를 고정하면 장면이 바뀌어도 축이 흔들리지 않는다 (원본에 근거 없음 — 추론).

원본 이 블록에서 `fig` 는 일곱 번 다시 대입되고, `fig.show()` 는 맨 끝에 한 번만 있다.
그래서 이 코드를 그대로 돌리면 화면에 뜨는 것은 마지막에 대입된 애니메이션 차트뿐이다 — 앞의 Figure 들은 만들어지기만 하고 이름 `fig` 에서 밀려난다.

### (3) Graph Objects — 그림을 부품부터 조립한다

**언제 쓰나** — 원본 팁대로 「세밀한 제어가 필요할 때」 쓴다.
선마다 색 · 굵기 · 점선을 따로 주거나, 데이터 묶음을 하나씩 얹고 싶을 때다.

```text
fig = go.Figure()                         빈 도화지
   │
   ├─ fig.add_trace(go.Scatter(y=sin, mode='lines',         name='sin(x)', line=dict(...)))
   ├─ fig.add_trace(go.Scatter(y=cos, mode='lines+markers', name='cos(x)', line=dict(dash='dash')))
   │                                       ▲ 트레이스(데이터) 두 개가 겹쳐 그려진다
   └─ fig.update_layout(title=..., xaxis_title=..., yaxis_title=...,
                        legend=dict(x=0.01, y=0.99), width=..., height=...,
                        hovermode='x unified')               ▲ 레이아웃(바깥 틀)
   │
   ▼
fig.show()
```

- 원본 주석의 「기본 구조: Figure → Trace(데이터) + Layout(레이아웃)」이 이 그림이다.
- `go.Figure()` 로 빈 그림을 만든다.
- `add_trace` 를 부를 때마다 트레이스가 하나씩 얹힌다.
- `mode='lines'` 는 선만, `'lines+markers'` 는 선과 점을 함께 그린다.
- `name` 은 범례에 뜰 이름이다.
- `line=dict(...)` 로 그 트레이스의 선 꾸밈(색 · 굵기 · 점선)을 정한다.
- `update_layout` 은 데이터가 아닌 틀 — 제목 · 축 제목 · 테마 · 범례 위치 · 크기 · 호버 방식 — 을 정한다.
- `hovermode='x unified'` 는 같은 x 위치의 여러 트레이스 값을 한 말풍선에 묶어 보여 주는 호버 방식이다.

> **트레이스(trace)** — 차트에 그려지는 데이터 한 묶음이다.\
> 예: `go.Scatter(x=x, y=np.sin(x))` 하나가 트레이스 하나다.

> **레이아웃(layout)** — 데이터를 뺀 차트의 틀(제목 · 축 · 범례 · 크기)이다.\
> 예: `fig.update_layout(title='삼각함수')`.

### (4) Subplots — 한 그림을 격자로 나눈다

**언제 쓰나** — 서로 다른 차트 여러 개를 한 화면에 나란히 놓을 때 쓴다.

```text
make_subplots(rows=2, cols=2, subplot_titles=[...],
              specs=[[{'type':'xy'}, {'type':'xy'}],
                     [{'type':'xy'}, {'type':'domain'}]])

 ┌──────────────┬──────────────┐
 │ (1,1) Line   │ (1,2) Bar    │   add_trace(trace, row=1, col=1) …
 │   xy         │   xy         │
 ├──────────────┼──────────────┤
 │ (2,1) Scatter│ (2,2) Pie    │   add_trace(go.Pie(...), row=2, col=2)
 │   xy         │   domain     │
 └──────────────┴──────────────┘
```

- `rows` · `cols` 로 칸 수를, `subplot_titles` 로 칸마다 제목을 정한다.
- `specs` 는 칸마다 종류를 적는 2차원 목록이다.
- `'xy'` 칸은 x축 · y축이 있는 칸이고, 선 · 막대 · 산점도가 들어간다.
- 파이는 축이 없어 `'domain'` 칸에 넣는다 — 원본 주석은 「Pie는 domain」이라고만 적었고, 「축이 없어서」는 풀이다 (원본에 근거 없음 — 추론).
- 트레이스는 `add_trace(트레이스, row=, col=)` 로 칸을 골라 넣는다.
- 마지막 `update_layout(height=600, showlegend=False, title=...)` 은 전체 그림에 한 번 적용된다.
- (2,1) 칸의 점은 `np.random.randn(100)` 이라 돌릴 때마다 위치가 달라진다.

> **서브플롯(subplot)** — 한 Figure 안에 격자로 나뉜 작은 차트 칸이다.\
> 예: 2×2 서브플롯이면 칸이 네 개다.

### (5) Dash — 입력이 바뀌면 함수가 새 차트를 돌려준다

**언제 쓰나** — 사용자가 드롭다운 · 슬라이더로 조건을 고르면 차트가 바뀌는 웹 대시보드를 만들 때 쓴다.
원본 팁대로 「콜백 기반 대시보드」다.

```text
app = Dash(__name__)
app.layout = html.Div([
    html.H1(...)                                   제목
    dcc.Dropdown(id='continent-dropdown', ...)     ──┐ 입력 1 (value)
    dcc.Slider(id='year-slider', ...)              ──┤ 입력 2 (value)
    dcc.Graph(id='gdp-graph')                      ◄─┼──── 출력 (figure)
])                                                   │
                                                     ▼
@callback(Output('gdp-graph','figure'),
          [Input('continent-dropdown','value'), Input('year-slider','value')])
def update_graph(continent, year):   ← 입력 순서대로 인자를 받는다
    filtered = df[(df['continent']==continent) & (df['year']==year)]
    return px.scatter(filtered, ...)  ← 돌려준 fig 가 그래프의 figure 가 된다

python app.py  →  http://127.0.0.1:8050
```

- `app.layout` 은 화면 구조다 — `html.*` 는 HTML 요소, `dcc.*` 는 드롭다운 · 슬라이더 · 그래프 같은 부품이다.
- 부품마다 `id` 를 붙인다.
- `Output('gdp-graph', 'figure')` 는 「id 가 `gdp-graph` 인 부품의 `figure` 속성을 채운다」는 뜻이다.
- `Input('continent-dropdown', 'value')` 는 「그 부품의 `value` 가 바뀌면 함수를 다시 부른다」는 뜻이다.
- 함수 인자 `continent` · `year` 는 `Input` 목록의 순서와 맞는다.
- 드롭다운은 `options` 를 대륙 목록에서 만들고 처음 값은 `'Asia'`, `clearable=False` 로 비울 수 없게 한다.
- 슬라이더는 연도의 최솟값 ~ 최댓값, `step=5`, 처음 값은 최댓값, `marks` 는 연도마다 눈금 글자다.
- `if __name__ == '__main__':` 아래 `app.run(debug=True)` 로 서버를 띄우고, 원본 주석대로 `http://127.0.0.1:8050` 으로 접속한다.

> **콜백(callback)** — 어떤 일이 일어났을 때 대신 불러 달라고 맡겨 둔 함수다.\
> 예: 슬라이더를 움직이면 Dash 가 `update_graph` 를 부른다.

### (6) 이 예제 스크립트가 실제로 하는 일 — 코드를 「출력」한다

**언제 알아야 하나** — 예제 파일을 돌렸는데 차트가 안 뜬다고 놀라지 않으려면 알아야 한다.

```text
print("=== 섹션 제목 ===")          → 제목 한 줄
print("""                           → 문자열이 줄바꿈으로 시작 → 제목 아래 빈 줄 하나
import plotly.express as px          → 코드 줄이 글자 그대로 찍힌다
    color='species',  # 색상 구분     → 문자열 안의 # 도 글자일 뿐이라 그대로 찍힌다
fig.show()                           
""")                                 → 문자열이 줄바꿈으로 끝남 + print 의 줄바꿈 → 빈 줄 하나
print()                              → 빈 줄 하나 더
print("=== 다음 섹션 ===")
```

- 파일의 모든 Plotly 코드는 세 따옴표 문자열 안에 있다 — 실행되지 않고 글자로 출력만 된다.
- 문자열 바깥의 `# …` 줄은 파이썬 주석이라 출력되지 않는다.
- 문자열 안의 `# …` 는 문자열의 일부라 그대로 출력된다.
- 섹션 사이에는 빈 줄이 두 개 생긴다(문자열 끝 줄바꿈 + `print()`).
- 마지막 섹션은 문자열 블록 없이 비교 문장 네 줄을 `print` 로 바로 찍는다.
- 그래서 이 파일은 Plotly 를 깔지 않아도 돌아가고, 차트를 보려면 문자열 속 코드를 따로 파일로 옮겨 돌려야 한다.

## 문법 — 형태와 규칙

```python
import plotly.express as px
import plotly.graph_objects as go

df = px.data.iris()

# Express: 한 줄
fig1 = px.scatter(df, x='sepal_width', y='sepal_length', color='species')
fig1.write_html('iris.html')

# Graph Objects: 조립
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=[1, 2, 3], y=[3, 1, 2], mode='lines', name='A'))
fig2.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3], mode='lines+markers', name='B'))
fig2.update_layout(title='두 선', hovermode='x unified')
fig2.show()
```

- `px.<차트>(DataFrame, x='열', y='열', color='열', ...)` — 열 이름을 문자열로 넘긴다.
- `go.Figure()` → `add_trace(go.<트레이스>(...))` 여러 번 → `update_layout(...)` 순서로 조립한다.
- 서브플롯은 `make_subplots(rows=, cols=, specs=)` 로 만들고 `add_trace(..., row=, col=)` 로 칸을 고른다.
- 저장은 `fig.write_html('파일.html')`, 띄우기는 `fig.show()` 다.
- Dash 는 `app.layout` 에 부품 트리를, `@callback(Output(id, 속성), [Input(id, 속성), ...])` 로 입력 → 출력 흐름을 적는다.

| 인자 | 어디서 | 넣는 값 (원본에 나온 것) |
|---|---|---|
| `barmode` | `px.bar` | `'stack'` · `'group'` · `'overlay'` |
| `marginal` | `px.histogram` | `'rug'` · `'violin'` · `'box'` |
| `mode` | `go.Scatter` | `'lines'` · `'lines+markers'` · `'markers'` |
| `hovermode` | `update_layout` | `'x unified'` |
| `specs` 의 `type` | `make_subplots` | `'xy'` · `'domain'` |
| `template` | px · `update_layout` | `'plotly_white'` |
| `hole` | `px.pie` | `0.3` (도넛) |

## 어디서 틀리나

### 1. 예제 파일을 돌리면 차트가 뜰 거라고 기대한다

원본 파일은 Plotly 코드를 문자열로 `print` 만 한다.
돌리면 코드 글자가 찍힐 뿐이다.
차트를 보려면 문자열 속 코드를 따로 `.py` 로 옮겨 `plotly` · `pandas` · `numpy` (Dash 는 `dash` 까지)를 깔고 돌린다.

### 2. Express 로 다 되는데 처음부터 go 로 짠다

팁: Plotly Express 는 한 줄로 인터랙티브 차트를 만든다.
DataFrame 이 있고 열을 축 · 색 · 크기에 꽂기만 하면 되는 경우 go 로 트레이스를 하나하나 만들 까닭이 없다.

### 3. 세밀한 제어가 필요한데 Express 만 붙든다

팁: go(Graph Objects)는 세밀한 제어가 필요할 때 쓴다.
트레이스마다 선 모양 · 표시 방식 · 범례 이름을 따로 주거나, 서로 다른 데이터를 한 그림에 하나씩 얹으려면 `go.Figure` + `add_trace` 가 맞다.

### 4. `fig` 를 덮어쓰고 `show()` 를 한 번만 부른다

여러 차트를 같은 이름 `fig` 에 차례로 대입하고 끝에서 `fig.show()` 를 한 번 부르면 마지막 차트만 뜬다.
차트마다 보고 싶으면 대입 뒤마다 `show()` 를 부르거나 이름을 나눈다.

### 5. 서브플롯의 파이 칸을 `'xy'` 로 둔다

파이를 넣을 칸은 `specs` 에서 `{'type': 'domain'}` 으로 적어야 한다 — 원본 주석 「Pie는 domain」.
그대로 `'xy'` 로 두면 파이를 넣을 수 없다 (어떤 오류가 나는지는 확인 필요).

### 6. Dash 의 id 와 콜백의 id 가 어긋난다

`Output` · `Input` 의 첫 인자는 `app.layout` 에 붙인 `id` 와 글자까지 같아야 한다.
함수 인자는 `Input` 목록 순서로 들어오므로, 순서를 바꾸면 `continent` 자리에 연도가 들어온다.

### 7. 차트를 보여 줄 때 화면 캡처만 보낸다

팁: `write_html()` 로 HTML 파일을 공유하면 누구나 인터랙티브하게 볼 수 있다.
`fig.show()` 는 내 브라우저에 띄울 뿐이고, 남에게 조작 가능한 차트를 주려면 HTML 파일을 보낸다.

### 8. 대시보드가 필요한데 정적 차트를 여러 장 만든다

팁: Dash 로 콜백 기반 대시보드를 만들 수 있다.
「대륙 × 연도」처럼 조합마다 차트를 미리 그리지 말고, 입력이 바뀔 때 콜백이 필요한 차트 하나를 새로 만들게 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 세 따옴표 문자열 안의 줄바꿈 · `#` 가 글자 그대로 출력된다 | Python 언어 (문자열 리터럴 규칙) |
| `print()` 가 끝에 줄바꿈 하나를 붙인다 | Python 언어 (`print` 의 기본 `end`) |
| `@callback(...)` 을 함수 위에 붙이는 문법 | 데코레이터 문법은 Python 언어, 입력 → 함수 호출 연결은 Dash 라이브러리 |
| `fig.show()` 가 브라우저에서 차트를 연다 | Plotly 라이브러리 + 실행 환경 (노트북 등에서는 다르게 뜰 수 있음 — 확인 필요) |
| Dash 앱 주소가 `http://127.0.0.1:8050` 이다 | Dash 의 기본 설정 (원본 주석) — 언어와 무관 |
| `px.data.iris()` 등 내장 데이터셋 | Plotly 패키지 |
| `np.random.randn(100)` 이 돌릴 때마다 다르다 | NumPy (시드를 고정하지 않았으므로) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| DataFrame 을 빨리 탐색 | Plotly Express | go 로 트레이스 직접 조립 |
| 트레이스별 선 모양 · 겹치기 · 호버 방식 조정 | Graph Objects | Express 인자만으로 버티기 |
| 여러 차트를 한 화면 격자로 | `make_subplots` | 차트 파일 여러 개 |
| 조작 가능한 차트를 남에게 공유 | `write_html` | 화면 캡처 |
| 사용자가 조건을 골라 보는 화면 | Dash (layout + callback) | 조합마다 정적 차트 |
| 논문 · 출판용 정적 그림 | Matplotlib | Plotly (원본 비교 문장 기준) |
| 간결한 통계 시각화를 정적으로 | Seaborn | — |

원본 비교 문장:
- Plotly: 인터랙티브, 웹 기반, 줌/팬/호버, 대시보드(Dash)
- Matplotlib: 정적, 출판용, 세밀한 커스텀, 가장 범용적
- Seaborn: 통계 시각화 특화, Matplotlib 기반, 간결한 API
- Plotly Express: Seaborn 처럼 간단 + Plotly 의 인터랙티브

## 핵심 문장

1. **Plotly 차트는 브라우저에서 줌 · 팬 · 호버가 되는 인터랙티브 차트다.**
2. **Express 는 DataFrame 의 열 이름을 인자에 꽂는 한 줄 API, Graph Objects 는 Figure = 트레이스 + 레이아웃을 손으로 조립하는 API 다.**
3. **서브플롯은 `specs` 로 칸 종류를 정하고 `row` · `col` 로 트레이스를 넣는다 — 파이 칸은 `domain` 이다.**
4. **Dash 는 layout(부품과 id) + callback(Input → 함수 → Output)으로 움직이는 대시보드다.**
5. **이 예제 파일은 코드를 문자열로 출력할 뿐이다 — 문자열 안의 것은 실행되지 않는다.**

## 관련 자료

- [seaborn-plots](../11-seaborn-plots/2-summary.md)
- [time-series](../13-time-series/2-summary.md)
- `sklearn-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/data-science.json` 의 `plotly-interactive`

## 용어 풀이

- **Plotly** — 웹 기반 인터랙티브 차트를 만드는 파이썬 라이브러리다.
- **Plotly Express (`px`)** — DataFrame 열을 인자로 받아 한 줄에 차트를 만드는 고수준 API 다.
- **Graph Objects (`go`)** — Figure · 트레이스 · 레이아웃을 직접 다루는 저수준 API 다.
- **Figure (`fig`)** — 트레이스와 레이아웃을 담은 차트 한 장이다.
- **트레이스(trace)** — 그려지는 데이터 한 묶음이다.
- **레이아웃(layout)** — 제목 · 축 · 범례 · 크기 같은 차트의 틀이다.
- **인터랙티브** — 보는 사람의 조작에 반응하는 성질이다.
- **호버(hover)** — 포인터를 요소 위에 올려 두는 동작, 또는 그때 뜨는 정보다.
- **줌 · 팬** — 확대 · 끌어서 옮기기다.
- **템플릿(template)** — 차트 꾸밈을 한 번에 바꾸는 테마 묶음이다.
- **서브플롯(subplot)** — 한 Figure 를 격자로 나눈 칸이다.
- **`specs` / `'xy'` / `'domain'`** — 서브플롯 칸의 종류 지정 / 축이 있는 칸 / 축 없이 영역만 차지하는 칸이다.
- **히트맵** — 행렬 값을 색 칸으로 칠한 그림이다.
- **도넛 차트** — 가운데에 구멍(`hole`)을 낸 파이 차트다.
- **애니메이션 프레임** — `animation_frame` 열의 값마다 만들어지는 한 장면이다.
- **Dash** — 파이썬으로 웹 대시보드를 만드는 프레임워크다.
- **`dcc`** — Dash 의 드롭다운 · 슬라이더 · 그래프 같은 부품 모음이다.
- **콜백(callback)** — 입력이 바뀌면 프레임워크가 대신 불러 주는 함수다.
- **`Input` / `Output`** — 콜백이 지켜볼 (부품 id, 속성) / 콜백 반환값을 넣을 (부품 id, 속성)이다.

## 더 들어가면

- `px.*` 함수도 결국 `go.Figure` 를 돌려준다고 알려져 있다 — 그래서 Express 로 만든 `fig` 에 `update_layout` · `add_trace` 를 이어 붙일 수 있다 (확인 필요).
- 트레이스 전체에 같은 설정을 한 번에 주는 `fig.update_traces(...)` 도 있다 (확인 필요).
- `write_html` 에는 plotly.js 를 파일에 넣을지 정하는 옵션(`include_plotlyjs`)이 있어 파일 크기가 달라진다 (확인 필요).
- PNG 같은 정적 이미지로 내보내는 `fig.write_image` 는 별도 패키지(kaleido)가 필요하다 (확인 필요).
- 예전 Dash 버전에서는 `app.run_server(...)` 를 썼고, 새 버전에서 `app.run(...)` 으로 바뀌었다 (버전 경계는 확인 필요).
- `@callback` 을 앱 객체 없이 쓰는 방식과 `@app.callback` 방식이 둘 다 있다 (확인 필요).
