# python/python-data-science/12 — Plotly 인터랙티브 차트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 파일의 주석과 문자열 속 주석 (예측)

```python
# 질문용 발췌
# 섹션 제목 출력: Plotly Express의 한 줄 차트 생성 패턴
print("=== Plotly Express: 빠른 차트 생성 ===")
# Plotly Express는 DataFrame 기반의 고수준 API로 빠른 EDA에 적합
print("""
import plotly.express as px
import pandas as pd
import numpy as np

# 내장 데이터셋
df = px.data.iris()
tips = px.data.tips()
gapminder = px.data.gapminder()

# --- 산점도 ---
fig = px.scatter(
    df, x='sepal_width', y='sepal_length',
    color='species',        # 색상 구분
""")
```

- 이 부분이 찍는 처음 몇 줄에 `# 섹션 제목 출력` 줄과 `# 색상 구분` 중 어느 것이 나타나는가?
- 제목 줄과 `import plotly.express as px` 사이에는 무엇이 있는가?

### 2. 섹션과 섹션 사이 (예측)

```python
# 질문용 발췌
print("""
...
    title='동아시아 1인당 GDP 추이'
)
fig.show()
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: Plotly Express의 다양한 차트 종류
print("=== 다양한 Plotly Express 차트 ===")
```

- `fig.show()` 줄과 다음 섹션 제목 사이에 빈 줄은 몇 개 찍히는가?

### 3. `fig` 에 일곱 번 대입하고 `show` 를 한 번 부르면 (예측)

```python
# 질문용 발췌 — 문자열에서 꺼내 실제로 돌린다고 하자
fig = px.histogram(tips, x='total_bill', nbins=30, color='time', marginal='box')
fig = px.box(tips, x='day', y='total_bill', color='smoker', notched=True)
fig = px.violin(tips, x='day', y='total_bill', color='sex', box=True, points='all')
fig = px.imshow(df_corr, text_auto='.2f', color_continuous_scale='RdBu_r')
fig = px.pie(tips, names='day', values='total_bill', hole=0.3)
fig = px.scatter_3d(px.data.iris(), x='sepal_length', y='sepal_width', z='petal_length', color='species')
fig = px.scatter(gapminder, x='gdpPercap', y='lifeExp', size='pop', color='continent', animation_frame='year')
fig.show()
```

- 화면에 뜨는 차트는 몇 개이고 어느 것인가?

### 4. 예제 파일을 그대로 돌렸을 때 (경계)

- 원본 예제 파일을 `python` 으로 돌리면 브라우저에 차트가 열리는가?
- 차트를 실제로 보려면 무엇을 해야 하는가?

### 5. 서브플롯의 네 번째 칸만 `'domain'` 인 까닭 (왜)

- `make_subplots` 의 `specs` 에서 파이를 넣을 칸만 `{'type': 'domain'}` 으로 적는 까닭은 무엇인가?

### 6. Express 와 Graph Objects 를 고르는 기준 (왜)

- 한 줄이면 되는 Express 를 두고 굳이 `go.Figure` 와 `add_trace` 로 조립하는 때는 언제인가?

### 7. Dash 레이아웃의 id 와 콜백의 연결 (연결)

- `dcc.Graph(id='gdp-graph')` · `dcc.Slider(id='year-slider')` 와 `@callback` 의 `Output` · `Input` 은 어떻게 이어지고, `update_graph` 의 두 인자에는 무엇이 들어오는가?

### 8. `fig.show()` 만으로 남에게 보여 줄 수 있나 (경계)

- 내가 만든 인터랙티브 차트를 다른 사람도 확대 · 호버하며 보게 하려면 `fig.show()` 말고 무엇이 필요한가?

### 9. Plotly Express 와 Seaborn 의 다리 (연결)

- 원본의 비교 문장으로 볼 때 Plotly Express 는 Seaborn 과 무엇이 닮았고 무엇이 다른가?

## 실습

### 실습 1. Plotly · Dash 예제 코드를 섹션별로 출력하는 안내 스크립트

**만들 것** — Plotly Express · 여러 Express 차트 · Graph Objects · Subplots · Dash · 라이브러리 비교의 여섯 섹션을 차례로 출력하는 스크립트를 만든다.
섹션마다 제목 줄을 찍고, Plotly 코드는 세 따옴표 문자열에 담아 글자 그대로 출력한다.

**준비물** — 스크립트 자체는 `print` 만 쓰므로 표준 Python 으로 돌아간다.
문자열 속 코드를 따로 실제로 돌려 보려면 `plotly` · `pandas` · `numpy` (Dash 섹션은 `dash`)가 필요하다.

**요구 조건**

1. 섹션은 여섯 개이고, 섹션 사이마다 `print()` 로 빈 줄을 하나 더 넣는다.
2. 1단계 — 제목 `=== Plotly Express: 빠른 차트 생성 ===` 아래, 문자열 하나에 다음 코드를 담아 출력한다: `px.data` 의 `iris` · `tips` · `gapminder` 불러오기 → iris 산점도(`color` 로 종 구분, `size` 로 크기 매핑, `hover_data` 로 호버 정보, `title`, `template`) → `fig.show()` 와 `fig.write_html('scatter.html')` → tips 막대 그래프(요일별 `total_bill`, 성별 색, `barmode='group'`) → 한국 · 일본 · 중국만 `query` 로 거른 라인 차트(나라별 색, `markers=True`).
3. 2단계 — 제목 `=== 다양한 Plotly Express 차트 ===` 아래 문자열에 히스토그램(`nbins`, `marginal='box'`) · 박스플롯(`notched=True`) · 바이올린(`box=True`, `points='all'`) · 상관계수 히트맵(`select_dtypes` → `corr` → `px.imshow`, `text_auto`) · 도넛 파이(`hole`) · 3D 산점도(`z`) · 연도별 애니메이션 산점도(`animation_frame`, `animation_group`, `log_x`, `size_max`, `range_y`)를 차례로 담고 끝에 `fig.show()` 를 둔다.
4. 3단계 — 제목 `=== Plotly Graph Objects: 세밀한 제어 ===` 아래 문자열에 `go.Figure()` 생성 → `np.linspace` 로 만든 `x` 에 대해 `sin(x)` 트레이스(`mode='lines'`)와 `cos(x)` 트레이스(`mode='lines+markers'`, 점선) 추가 → `update_layout`(제목 · 축 제목 · 테마 · 범례 위치 · 크기 · `hovermode='x unified'`) → `fig.show()` 를 담는다.
5. 4단계 — 제목 `=== Subplots: 서브플롯 ===` 아래 문자열에 2×2 `make_subplots`(칸 제목 넷, 네 번째 칸만 `'domain'`) → (1,1) 선 · (1,2) 막대 · (2,1) 무작위 산점 · (2,2) 파이를 `row` · `col` 로 추가 → `update_layout`(범례 끄기 · 제목) → `fig.show()` 를 담는다.
6. 5단계 — 제목 `=== Dash: 대시보드 기초 ===` 아래 문자열에 `Dash(__name__)` 앱 생성 → `app.layout` 에 제목 · 대륙 드롭다운 · 연도 슬라이더 · 그래프(각각 id) → 드롭다운과 슬라이더의 `value` 를 입력, 그래프의 `figure` 를 출력으로 하는 `@callback` 함수 `update_graph(continent, year)` (대륙 · 연도로 거른 뒤 산점도를 돌려준다) → `if __name__ == '__main__':` 아래 `app.run(debug=True)` 를 담는다.
7. 6단계 — 제목 `=== Plotly vs Matplotlib/Seaborn ===` 아래에는 문자열 블록 없이 Plotly · Matplotlib · Seaborn · Plotly Express 를 한 줄씩 비교하는 네 줄을 `print` 로 찍는다.

**시작 코드**

```python
# Plotly - 인터랙티브 시각화
# pip install plotly pandas numpy

print("=== Plotly Express: 빠른 차트 생성 ===")
print("""
import plotly.express as px
import pandas as pd
import numpy as np

# 내장 데이터셋
# TODO: iris → df, tips → tips, gapminder → gapminder

# --- 산점도 ---
# TODO: px.scatter(df, x='sepal_width', y='sepal_length', ... title='Iris 산점도', template='plotly_white')
# TODO: 브라우저로 띄우기, 'scatter.html' 로 저장

# --- 막대 그래프 ---
# TODO: px.bar(tips, ..., title='요일별 총 결제액') — barmode 후보 'stack', 'group', 'overlay'
fig.show()

# --- 라인 차트 ---
df_line = gapminder.query("country in ['South Korea', 'Japan', 'China']")
# TODO: px.line(df_line, ..., title='동아시아 1인당 GDP 추이')
fig.show()
""")

print()
print("=== 다양한 Plotly Express 차트 ===")
print("""
import plotly.express as px

tips = px.data.tips()
gapminder = px.data.gapminder()

# TODO: 히스토그램 / 박스플롯 / 바이올린 / 히트맵(color_continuous_scale='RdBu_r') / 파이(hole=0.3)
# TODO: 3D 산점도 / 애니메이션(size_max=60, range_y=[25, 90])
fig.show()
""")

print()
print("=== Plotly Graph Objects: 세밀한 제어 ===")
print("""
import plotly.graph_objects as go
import numpy as np

# 기본 구조: Figure → Trace(데이터) + Layout(레이아웃)
# TODO: 빈 Figure

x = np.linspace(0, 10, 100)
# TODO: sin(x) 트레이스 — line=dict(color='blue', width=2)
# TODO: cos(x) 트레이스 — line=dict(color='red', dash='dash')

# TODO: update_layout(... legend=dict(x=0.01, y=0.99), width=800, height=400, hovermode=...)
fig.show()
""")

print()
print("=== Subplots: 서브플롯 ===")
print("""
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

# TODO: make_subplots(rows=2, cols=2, subplot_titles=['Line', 'Bar', 'Scatter', 'Pie'], specs=...)
# TODO: (1,1) go.Scatter(x=[1,2,3,4], y=[10,15,13,17], mode='lines')
# TODO: (1,2) go.Bar(x=['A','B','C'], y=[20,14,23])
# TODO: (2,1) go.Scatter(x=np.random.randn(100), y=np.random.randn(100), mode='markers')
# TODO: (2,2) go.Pie(labels=['A','B','C'], values=[30,50,20])

fig.update_layout(height=600, showlegend=False, title='서브플롯 예시')
fig.show()
""")

print()
print("=== Dash: 대시보드 기초 ===")
print("""
# pip install dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# TODO: 앱 생성

df = px.data.gapminder()

# TODO: app.layout = html.Div([...]) — H1('GDP Dashboard'), Dropdown(id='continent-dropdown'),
#       Slider(id='year-slider', step=5), Graph(id='gdp-graph')

# TODO: @callback(Output(...), [Input(...), Input(...)])
# TODO: def update_graph(continent, year): ... return fig

# 실행: python app.py → http://127.0.0.1:8050
# TODO: if __name__ == '__main__': ...
""")

print()
print("=== Plotly vs Matplotlib/Seaborn ===")
# TODO: 비교 네 줄
```

**확인 방법** — `python plotly-interactive.py` 로 돌려 섹션 제목 여섯 개가 차례로 나오고, 섹션 사이에 빈 줄이 둘씩 있고, 맨 끝에 비교 네 줄이 찍히는지 본다.
문자열 속 코드를 따로 `.py` 로 옮겨 패키지를 깔고 돌리면 브라우저에서 차트(또는 Dash 는 `http://127.0.0.1:8050`)를 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
