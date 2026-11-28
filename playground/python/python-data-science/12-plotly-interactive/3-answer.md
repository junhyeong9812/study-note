# python/python-data-science/12 — Plotly 인터랙티브 차트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 문자열 속 `# 색상 구분` 만 찍히고, 제목 아래에 빈 줄이 하나 있다

**출력**

```text
=== Plotly Express: 빠른 차트 생성 ===

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
```

**왜 그런가**

- 문자열 바깥의 `# 섹션 제목 출력 …` 은 파이썬 주석이라 실행 때 버려진다.
- 세 따옴표 문자열 안의 `# 색상 구분` · `# 내장 데이터셋` 은 문자열의 글자라 그대로 찍힌다.
- 문자열이 `"""` 바로 뒤 줄바꿈으로 시작하므로 제목 줄 아래에 빈 줄이 하나 생긴다.
- 근거: 2-summary 「동작 방식 (6)」.

### 2. 빈 줄 두 개

**출력**

```text
fig.show()


=== 다양한 Plotly Express 차트 ===
```

**왜 그런가**

- 문자열이 `fig.show()` 뒤 줄바꿈으로 끝나고, `print` 가 줄바꿈을 하나 더 붙여 빈 줄 하나가 생긴다.
- 이어지는 `print()` 가 빈 줄 하나를 더 찍는다.
- 근거: 2-summary 「동작 방식 (6)」.

### 3. 하나 — 마지막의 애니메이션 산점도만 뜬다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

일곱 개의 Figure 가 차례로 만들어지지만 `fig.show()` 는 끝에서 한 번만 불린다.
그 순간 `fig` 가 가리키는 것은 마지막에 대입된 `animation_frame='year'` 산점도다.

**왜 그런가**

- 대입할 때마다 이름 `fig` 가 새 Figure 를 가리키고, 앞의 Figure 는 아무도 띄우지 않는다.
- 차트마다 보려면 대입 뒤마다 `show()` 를 부르거나 이름을 나눠야 한다.
- 근거: 2-summary 「동작 방식 (2)」 끝 문단 · 「어디서 틀리나 4」.

### 4. 열리지 않는다 — 코드 글자만 찍힌다

- 원본 파일의 Plotly · Dash 코드는 모두 세 따옴표 문자열 안에 있어 실행되지 않고 `print` 로 글자만 출력된다.
- 차트를 보려면 문자열 속 코드를 따로 `.py` 파일로 옮겨 `plotly` · `pandas` · `numpy` (Dash 는 `dash` 까지)를 깔고 돌린다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 1」.

### 5. 파이는 축이 있는 `xy` 칸이 아니라 축 없는 `domain` 칸에 들어가기 때문이다

- `'xy'` 칸은 x축 · y축이 있는 칸이라 선 · 막대 · 산점도가 들어간다.
- 파이는 축 없이 영역만 차지하므로 그 칸만 `'domain'` 으로 적는다.
- 원본은 「Pie는 domain」이라고만 적었고, 축이 없어서라는 까닭은 풀이다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 6. 트레이스마다 세밀하게 손댈 때 go 를 쓴다

- Express 는 DataFrame 열을 인자에 꽂아 한 줄로 차트를 만드는 빠른 탐색용이다.
- go 는 Figure 에 트레이스를 하나씩 얹고(`add_trace`), 트레이스마다 `mode` · `name` · `line=dict(...)` (색 · 굵기 · 점선)을 따로 주고, `update_layout` 으로 범례 위치 · 크기 · `hovermode` 같은 틀을 정할 때 쓴다.
- 원본 팁: 「go(Graph Objects)는 세밀한 제어가 필요할 때 사용한다」.
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」 · 「어디서 틀리나 2 · 3」.

### 7. 같은 id 로 이어지고, 인자에는 `Input` 순서대로 드롭다운 값 · 슬라이더 값이 들어온다

- `Output('gdp-graph', 'figure')` 는 id 가 `gdp-graph` 인 그래프의 `figure` 속성에 함수의 반환값을 넣는다.
- `Input('continent-dropdown', 'value')` · `Input('year-slider', 'value')` 는 두 부품의 `value` 가 바뀌면 함수를 다시 부르게 한다.
- `update_graph(continent, year)` 의 첫 인자에는 드롭다운에서 고른 대륙, 둘째 인자에는 슬라이더의 연도가 들어온다.
- 함수는 그 두 값으로 데이터를 걸러 새 산점도를 돌려주고, 그것이 그래프에 그려진다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 8. `fig.write_html(...)` 로 만든 HTML 파일을 보낸다

- `fig.show()` 는 내 브라우저에 차트를 띄울 뿐이다.
- 원본 팁: 「write_html()로 HTML 파일을 공유하면 누구나 인터랙티브하게 볼 수 있다」.
- 화면 캡처를 보내면 종이 지도처럼 정적인 그림이 될 뿐이다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 7」.

### 9. 간단함은 Seaborn 을 닮았고, 인터랙티브는 Plotly 쪽이다

- 원본 문장: 「Plotly Express: Seaborn처럼 간단 + Plotly의 인터랙티브」.
- Seaborn 은 통계 시각화 특화, Matplotlib 기반, 간결한 API — 즉 결과는 정적 그림이다.
- Plotly Express 는 Seaborn 처럼 짧은 호출로 그리지만, 결과가 줌 · 팬 · 호버가 되는 웹 기반 차트다.
- 근거: 2-summary 「언제 쓰고 언제 안 쓰나」의 원본 비교 문장.

## 실습 정답

### 실습 1. Plotly · Dash 예제 코드를 섹션별로 출력하는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 섹션 여섯 개, 사이마다 빈 줄 | 섹션 앞마다 `print()` |
| 2. 1단계 Express 빠른 차트 | `print("=== Plotly Express: 빠른 차트 생성 ===")` 다음 문자열 — `px.data.iris()` · `px.scatter(... hover_data=...)` · `fig.write_html('scatter.html')` · `px.bar(... barmode='group')` · `gapminder.query(...)` · `px.line(... markers=True)` |
| 3. 2단계 다양한 차트 | `print("=== 다양한 Plotly Express 차트 ===")` 다음 문자열 — `px.histogram` · `px.box` · `px.violin` · `select_dtypes(...).corr()` + `px.imshow` · `px.pie(... hole=0.3)` · `px.scatter_3d` · `px.scatter(... animation_frame='year' ...)` · `fig.show()` |
| 4. 3단계 Graph Objects | `print("=== Plotly Graph Objects: 세밀한 제어 ===")` 다음 문자열 — `go.Figure()` · `fig.add_trace(go.Scatter(...))` 두 번 · `fig.update_layout(... hovermode='x unified')` |
| 5. 4단계 Subplots | `print("=== Subplots: 서브플롯 ===")` 다음 문자열 — `make_subplots(... specs=...)` · `add_trace(..., row=, col=)` 네 번 · `update_layout(height=600, showlegend=False, ...)` |
| 6. 5단계 Dash | `print("=== Dash: 대시보드 기초 ===")` 다음 문자열 — `Dash(__name__)` · `app.layout = html.Div([...])` · `@callback(Output('gdp-graph', 'figure'), [Input(...), Input(...)])` · `def update_graph(continent, year)` · `app.run(debug=True)` |
| 7. 6단계 비교 네 줄 | `print("=== Plotly vs Matplotlib/Seaborn ===")` 와 이어지는 `print("Plotly: …")` 등 네 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/plotly-interactive.py`

```python
# [데이터 과학 & 수학] Plotly 인터랙티브 차트
# 설명: Plotly, 인터랙티브 차트, 대시보드 기초 구조
# 팁: Plotly Express는 한 줄로 인터랙티브 차트를 생성한다. go(Graph Objects)는 세밀한 제어가 필요할 때 사용한다. Dash로 콜백 기반 대시보드를 만들 수 있다. write_html()로 HTML 파일을 공유하면 누구나 인터랙티브하게 볼 수 있다.

# Plotly - 인터랙티브 시각화
# pip install plotly pandas numpy

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
    size='petal_length',    # 크기 매핑
    hover_data=['petal_width'],  # 호버 정보
    title='Iris 산점도',
    template='plotly_white'  # 테마
)
fig.show()  # 브라우저에서 인터랙티브 차트 열림
fig.write_html('scatter.html')  # HTML 파일로 저장

# --- 막대 그래프 ---
fig = px.bar(
    tips, x='day', y='total_bill',
    color='sex', barmode='group',  # 'stack', 'group', 'overlay'
    title='요일별 총 결제액'
)
fig.show()

# --- 라인 차트 ---
df_line = gapminder.query("country in ['South Korea', 'Japan', 'China']")
fig = px.line(
    df_line, x='year', y='gdpPercap',
    color='country', markers=True,
    title='동아시아 1인당 GDP 추이'
)
fig.show()
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: Plotly Express의 다양한 차트 종류
print("=== 다양한 Plotly Express 차트 ===")
# 히스토그램, 박스, 바이올린, 히트맵, 파이, 3D 산점, 애니메이션 예시
print("""
import plotly.express as px

tips = px.data.tips()
gapminder = px.data.gapminder()

# --- 히스토그램 ---
fig = px.histogram(
    tips, x='total_bill', nbins=30,
    color='time', marginal='box',  # 'rug', 'violin', 'box'
    title='결제액 분포'
)

# --- 박스플롯 ---
fig = px.box(
    tips, x='day', y='total_bill',
    color='smoker', notched=True,
    title='요일별 결제액 분포'
)

# --- 바이올린 ---
fig = px.violin(
    tips, x='day', y='total_bill',
    color='sex', box=True, points='all',
    title='Violin Plot'
)

# --- 히트맵 ---
df_corr = tips.select_dtypes(include='number').corr()
fig = px.imshow(
    df_corr, text_auto='.2f',
    color_continuous_scale='RdBu_r',
    title='상관관계 히트맵'
)

# --- 파이 차트 ---
fig = px.pie(
    tips, names='day', values='total_bill',
    title='요일별 매출 비율',
    hole=0.3  # 도넛 차트
)

# --- 3D 산점도 ---
fig = px.scatter_3d(
    px.data.iris(), x='sepal_length', y='sepal_width',
    z='petal_length', color='species'
)

# --- 애니메이션 ---
fig = px.scatter(
    gapminder, x='gdpPercap', y='lifeExp',
    size='pop', color='continent',
    animation_frame='year',  # 연도별 애니메이션
    animation_group='country',
    log_x=True, size_max=60,
    range_y=[25, 90],
    title='국가별 GDP vs 기대수명 변화'
)
fig.show()
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: graph_objects는 trace 단위로 세밀한 제어 가능
print("=== Plotly Graph Objects: 세밀한 제어 ===")
# Figure에 Trace를 add_trace()로 추가하고 update_layout()으로 레이아웃 설정
print("""
import plotly.graph_objects as go
import numpy as np

# 기본 구조: Figure → Trace(데이터) + Layout(레이아웃)
fig = go.Figure()

# 여러 Trace 추가
x = np.linspace(0, 10, 100)
fig.add_trace(go.Scatter(
    x=x, y=np.sin(x),
    mode='lines',
    name='sin(x)',
    line=dict(color='blue', width=2)
))
fig.add_trace(go.Scatter(
    x=x, y=np.cos(x),
    mode='lines+markers',
    name='cos(x)',
    line=dict(color='red', dash='dash')
))

# 레이아웃 설정
fig.update_layout(
    title='삼각함수',
    xaxis_title='x',
    yaxis_title='y',
    template='plotly_white',
    legend=dict(x=0.01, y=0.99),
    width=800, height=400,
    hovermode='x unified'  # 호버 모드
)
fig.show()
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: make_subplots로 격자형 서브플롯 구성
print("=== Subplots: 서브플롯 ===")
# row/col 인자로 추가 위치를 지정하고 specs로 type 정의
print("""
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=['Line', 'Bar', 'Scatter', 'Pie'],
    specs=[[{'type': 'xy'}, {'type': 'xy'}],
           [{'type': 'xy'}, {'type': 'domain'}]]  # Pie는 domain
)

# (1,1) 라인
fig.add_trace(
    go.Scatter(x=[1,2,3,4], y=[10,15,13,17], mode='lines'),
    row=1, col=1
)

# (1,2) 바
fig.add_trace(
    go.Bar(x=['A','B','C'], y=[20,14,23]),
    row=1, col=2
)

# (2,1) 산점도
fig.add_trace(
    go.Scatter(x=np.random.randn(100), y=np.random.randn(100),
               mode='markers'),
    row=2, col=1
)

# (2,2) 파이
fig.add_trace(
    go.Pie(labels=['A','B','C'], values=[30,50,20]),
    row=2, col=2
)

fig.update_layout(height=600, showlegend=False, title='서브플롯 예시')
fig.show()
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: Dash 프레임워크로 인터랙티브 대시보드 구축
print("=== Dash: 대시보드 기초 ===")
# layout으로 UI 구조를, @callback으로 입력→출력 흐름을 정의
print("""
# pip install dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Dash 앱 생성
app = Dash(__name__)

df = px.data.gapminder()

app.layout = html.Div([
    html.H1('GDP Dashboard'),

    # 드롭다운
    dcc.Dropdown(
        id='continent-dropdown',
        options=[{'label': c, 'value': c}
                 for c in df['continent'].unique()],
        value='Asia',
        clearable=False
    ),

    # 슬라이더
    dcc.Slider(
        id='year-slider',
        min=df['year'].min(),
        max=df['year'].max(),
        step=5,
        value=df['year'].max(),
        marks={str(y): str(y) for y in df['year'].unique()}
    ),

    # 그래프
    dcc.Graph(id='gdp-graph')
])

# 콜백: 입력 변경 → 그래프 업데이트
@callback(
    Output('gdp-graph', 'figure'),
    [Input('continent-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(continent, year):
    filtered = df[(df['continent'] == continent) & (df['year'] == year)]
    fig = px.scatter(
        filtered, x='gdpPercap', y='lifeExp',
        size='pop', hover_name='country',
        log_x=True, size_max=60,
        title=f'{continent} - {year}'
    )
    return fig

# 실행: python app.py → http://127.0.0.1:8050
if __name__ == '__main__':
    app.run(debug=True)
""")

# 줄바꿈 출력
print()
# 섹션 제목 출력: 시각화 라이브러리 비교 (용도별 선택 기준)
print("=== Plotly vs Matplotlib/Seaborn ===")
# Plotly는 인터랙티브 웹 차트에 강하다
print("Plotly: 인터랙티브, 웹 기반, 줌/팬/호버, 대시보드(Dash)")
# Matplotlib은 출판/논문 그래프에 적합한 가장 범용적인 도구
print("Matplotlib: 정적, 출판용, 세밀한 커스텀, 가장 범용적")
# Seaborn은 통계 시각화 특화로 간결한 API 제공
print("Seaborn: 통계 시각화 특화, Matplotlib 기반, 간결한 API")
# Plotly Express는 간결함과 인터랙티브를 모두 가짐
print("Plotly Express: Seaborn처럼 간단 + Plotly의 인터랙티브")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== Plotly Express: 빠른 차트 생성 ===

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
    size='petal_length',    # 크기 매핑
    hover_data=['petal_width'],  # 호버 정보
    title='Iris 산점도',
    template='plotly_white'  # 테마
)
fig.show()  # 브라우저에서 인터랙티브 차트 열림
fig.write_html('scatter.html')  # HTML 파일로 저장

# --- 막대 그래프 ---
fig = px.bar(
    tips, x='day', y='total_bill',
    color='sex', barmode='group',  # 'stack', 'group', 'overlay'
    title='요일별 총 결제액'
)
fig.show()

# --- 라인 차트 ---
df_line = gapminder.query("country in ['South Korea', 'Japan', 'China']")
fig = px.line(
    df_line, x='year', y='gdpPercap',
    color='country', markers=True,
    title='동아시아 1인당 GDP 추이'
)
fig.show()


=== 다양한 Plotly Express 차트 ===

import plotly.express as px

tips = px.data.tips()
gapminder = px.data.gapminder()

# --- 히스토그램 ---
fig = px.histogram(
    tips, x='total_bill', nbins=30,
    color='time', marginal='box',  # 'rug', 'violin', 'box'
    title='결제액 분포'
)

# --- 박스플롯 ---
fig = px.box(
    tips, x='day', y='total_bill',
    color='smoker', notched=True,
    title='요일별 결제액 분포'
)

# --- 바이올린 ---
fig = px.violin(
    tips, x='day', y='total_bill',
    color='sex', box=True, points='all',
    title='Violin Plot'
)

# --- 히트맵 ---
df_corr = tips.select_dtypes(include='number').corr()
fig = px.imshow(
    df_corr, text_auto='.2f',
    color_continuous_scale='RdBu_r',
    title='상관관계 히트맵'
)

# --- 파이 차트 ---
fig = px.pie(
    tips, names='day', values='total_bill',
    title='요일별 매출 비율',
    hole=0.3  # 도넛 차트
)

# --- 3D 산점도 ---
fig = px.scatter_3d(
    px.data.iris(), x='sepal_length', y='sepal_width',
    z='petal_length', color='species'
)

# --- 애니메이션 ---
fig = px.scatter(
    gapminder, x='gdpPercap', y='lifeExp',
    size='pop', color='continent',
    animation_frame='year',  # 연도별 애니메이션
    animation_group='country',
    log_x=True, size_max=60,
    range_y=[25, 90],
    title='국가별 GDP vs 기대수명 변화'
)
fig.show()


=== Plotly Graph Objects: 세밀한 제어 ===

import plotly.graph_objects as go
import numpy as np

# 기본 구조: Figure → Trace(데이터) + Layout(레이아웃)
fig = go.Figure()

# 여러 Trace 추가
x = np.linspace(0, 10, 100)
fig.add_trace(go.Scatter(
    x=x, y=np.sin(x),
    mode='lines',
    name='sin(x)',
    line=dict(color='blue', width=2)
))
fig.add_trace(go.Scatter(
    x=x, y=np.cos(x),
    mode='lines+markers',
    name='cos(x)',
    line=dict(color='red', dash='dash')
))

# 레이아웃 설정
fig.update_layout(
    title='삼각함수',
    xaxis_title='x',
    yaxis_title='y',
    template='plotly_white',
    legend=dict(x=0.01, y=0.99),
    width=800, height=400,
    hovermode='x unified'  # 호버 모드
)
fig.show()


=== Subplots: 서브플롯 ===

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=['Line', 'Bar', 'Scatter', 'Pie'],
    specs=[[{'type': 'xy'}, {'type': 'xy'}],
           [{'type': 'xy'}, {'type': 'domain'}]]  # Pie는 domain
)

# (1,1) 라인
fig.add_trace(
    go.Scatter(x=[1,2,3,4], y=[10,15,13,17], mode='lines'),
    row=1, col=1
)

# (1,2) 바
fig.add_trace(
    go.Bar(x=['A','B','C'], y=[20,14,23]),
    row=1, col=2
)

# (2,1) 산점도
fig.add_trace(
    go.Scatter(x=np.random.randn(100), y=np.random.randn(100),
               mode='markers'),
    row=2, col=1
)

# (2,2) 파이
fig.add_trace(
    go.Pie(labels=['A','B','C'], values=[30,50,20]),
    row=2, col=2
)

fig.update_layout(height=600, showlegend=False, title='서브플롯 예시')
fig.show()


=== Dash: 대시보드 기초 ===

# pip install dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Dash 앱 생성
app = Dash(__name__)

df = px.data.gapminder()

app.layout = html.Div([
    html.H1('GDP Dashboard'),

    # 드롭다운
    dcc.Dropdown(
        id='continent-dropdown',
        options=[{'label': c, 'value': c}
                 for c in df['continent'].unique()],
        value='Asia',
        clearable=False
    ),

    # 슬라이더
    dcc.Slider(
        id='year-slider',
        min=df['year'].min(),
        max=df['year'].max(),
        step=5,
        value=df['year'].max(),
        marks={str(y): str(y) for y in df['year'].unique()}
    ),

    # 그래프
    dcc.Graph(id='gdp-graph')
])

# 콜백: 입력 변경 → 그래프 업데이트
@callback(
    Output('gdp-graph', 'figure'),
    [Input('continent-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(continent, year):
    filtered = df[(df['continent'] == continent) & (df['year'] == year)]
    fig = px.scatter(
        filtered, x='gdpPercap', y='lifeExp',
        size='pop', hover_name='country',
        log_x=True, size_max=60,
        title=f'{continent} - {year}'
    )
    return fig

# 실행: python app.py → http://127.0.0.1:8050
if __name__ == '__main__':
    app.run(debug=True)


=== Plotly vs Matplotlib/Seaborn ===
Plotly: 인터랙티브, 웹 기반, 줌/팬/호버, 대시보드(Dash)
Matplotlib: 정적, 출판용, 세밀한 커스텀, 가장 범용적
Seaborn: 통계 시각화 특화, Matplotlib 기반, 간결한 API
Plotly Express: Seaborn처럼 간단 + Plotly의 인터랙티브
````

**풀이 요점**

- 정답 코드는 Plotly 를 실행하지 않고, 코드를 세 따옴표 문자열로 출력하는 안내 스크립트다.
- 문자열 안의 `#` 주석은 글자로 찍히고, 문자열 바깥 주석은 찍히지 않는다.
- 문자열이 줄바꿈으로 시작 · 끝나고 `print()` 가 더해져 섹션 사이에 빈 줄이 둘 생긴다.
- 담긴 코드는 Express(한 줄) → go(조립) → Subplots(격자) → Dash(콜백) 순으로 제어 수준이 올라간다.
- 마지막 섹션만 문자열 블록 없이 비교 문장을 바로 찍는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
