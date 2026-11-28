# python/python-web/10 — Scrapy (크롤링 프레임워크) — 정리 (힌트)

> 출처 — study-site 항목 `python/scrapy-basics`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/scrapy-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `scrapy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**Scrapy 는 「신문 스크랩 팀」이다.**
조사원은 기사 목록 면을 훑으며 기사마다 본문 면으로 찾아가고, 다음 목록 면도 넘겨 본다.
본문에서 베낀 내용은 정해진 기록 카드에 적는다.
카드는 검수대 → 다듬는 자리 → 철하는 자리를 차례로 지나고, 제목이 빠진 카드는 검수대에서 버려진다.
Scrapy 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 조사원 | `Spider` 클래스 (`parse` 같은 콜백 메서드) |
| 처음 펼칠 목록 면 | `start_urls` |
| 「이 면으로 가 봐」 쪽지 | `response.follow(...)` 가 만드는 요청 |
| 기록 카드 양식 | `scrapy.Item` 과 `scrapy.Field()` |
| 카드 작성 도우미 | `ItemLoader` 와 입력 · 출력 프로세서 |
| 검수대 · 다듬기 · 철하기 | `Pipeline` 클래스들 (숫자 차례로) |
| 버리는 카드 | `raise DropItem(...)` |
| 「한 면 보고 1초 쉬기」 규칙 | `DOWNLOAD_DELAY` |

```text
start_urls ──요청──▶ [Scrapy 엔진] ──응답──▶ parse()
                         ▲                    │ yield 요청(상세 · 다음 페이지)
                         └────────────────────┤
                                              │ yield Item
                                              ▼
                     Pipeline 100 → 200 → 300 → 파일
```

## 이 주제가 답하려는 질문

1. 크롤링 로직은 어디에 쓰고, 한 페이지에서 다른 페이지로 어떻게 넘어가나?
2. HTML 에서 원하는 텍스트 · 속성을 어떻게 꺼내나 (CSS 와 XPath)?
3. 꺼낸 값은 어떻게 다듬고 검사하고 저장하나 (ItemLoader · Pipeline)?
4. 남의 서버에 무리를 주지 않으려면 무엇을 설정하나?

## 동작 방식

### (1) Spider 와 콜백 — 요청을 내고, 응답을 콜백이 받는다

**언제 쓰나** — 어떤 페이지에서 시작해 무엇을 따라가고 무엇을 모을지 정할 때 쓴다.

```text
class ArticleSpider(scrapy.Spider):
    name = 'articles'
    start_urls = [...목록 1페이지...]
    def parse(self, response): ... yield ...

  ① 엔진이 start_urls 로 요청을 보낸다
  ② 응답이 오면 기본 콜백 parse(response) 를 부른다
  ③ parse 가 yield 한 것을 엔진이 하나씩 받는다
       ├ 요청이면 → 대기열에 넣고, 응답이 오면 지정한 callback 을 부른다
       └ Item 이면 → Pipeline 으로 보낸다
```

① `name` 은 스파이더의 식별자이고, `scrapy crawl articles` 의 `articles` 가 이 이름이다.
② `start_urls` 의 응답은 따로 정하지 않으면 `parse` 메서드로 들어간다.
③ `parse` 는 `return` 대신 `yield` 를 쓰는 제너레이터라서, 요청과 Item 을 여러 개 섞어 내보낼 수 있다.
④ `allowed_domains` 는 이 목록 밖의 도메인으로 새어 나가는 것을 막는다.
⑤ Scrapy 는 Twisted 기반의 비동기 방식이라, 응답 하나를 기다리는 동안 다른 요청도 동시에 진행한다 — 그래서 빠르다.

> **콜백** — 「응답이 오면 이 함수를 불러 달라」고 넘겨 둔 함수다.\
> 예: `callback=self.parse_detail` 은 상세 페이지 응답을 `parse_detail` 이 받게 한다.

> **제너레이터** — `yield` 로 값을 하나씩 내보내는 함수다.\
> 예: `parse` 가 기사 카드마다 `yield response.follow(...)` 를 한다.

### (2) 선택자 — CSS 와 XPath 로 값 꺼내기

**언제 쓰나** — 응답 HTML 에서 제목 텍스트 · 링크 주소 · 본문 같은 값을 뽑을 때 쓴다.

```text
<div class="article-card">
  <h2 class="title">안녕</h2>
  <a href="/a/1">더보기</a>
</div>

article.css('h2.title::text').get()     →  '안녕'        (텍스트 노드)
article.css('a::attr(href)').get()      →  '/a/1'        (속성 값)
article.css('.date::text').get(default='') → ''          (없으면 기본값)
response.xpath('//span[@class="tag"]/text()').getall() → ['파이썬', ...] (전부, 리스트)
response.css('.views::text').re_first(r'\d+')  → '1234' 같은 첫 매칭 문자열
```

① `response.css(...)` 와 `response.xpath(...)` 는 선택된 노드들의 목록(SelectorList)을 돌려준다.
② CSS 쪽에서는 `::text` 가 텍스트 노드를, `::attr(이름)` 이 속성 값을 고른다.
③ `.get()` 은 첫 결과 하나를 문자열로, 없으면 `None` 을 돌려준다.
④ `.get(default='')` 나 `.get('익명')` 처럼 기본값을 주면 없을 때 `None` 대신 그 값이 나온다.
⑤ `.getall()` 은 모든 결과를 리스트로 돌려준다 — 본문처럼 텍스트 노드가 여러 조각일 때 쓴다.
⑥ `.re_first(정규식)` 은 결과 텍스트에 정규식을 적용해 첫 매칭만 돌려준다 — 「조회수 1234회」에서 `1234` 만 뽑는 식이다.
⑦ XPath 의 `//` 는 「문서 어디서든」, `.//` 는 「지금 고른 노드 아래에서」다.
⑧ 그래서 카드 하나를 `selector` 로 잡고 그 안의 태그만 찾으려면 `.//span[...]` 처럼 점을 붙여야 한다.
⑨ XPath 의 `//text()` 는 그 노드 아래의 모든 텍스트 노드를, `/text()` 는 바로 아래 텍스트 노드만 고른다.

> **선택자** — 문서에서 원하는 노드를 가리키는 표현식이다.\
> 예: `'.pagination .next a::attr(href)'` 는 다음 페이지 링크의 `href` 를 가리킨다.

> **XPath** — XML · HTML 의 노드를 경로식으로 고르는 언어다.\
> 예: `//div[@class="article-body"]//text()`.

### (3) 페이지 넘기기와 콜백 사이 데이터 전달

**언제 쓰나** — 목록 → 상세로 들어가거나, 목록의 다음 페이지로 넘어갈 때 쓴다.

```text
parse(목록 응답)
  ├ 카드마다: yield response.follow(link, callback=parse_detail,
  │                                 meta={'title': ..., 'date': ...})
  │                 └▶ parse_detail(상세 응답)
  │                       response.meta['title'] 로 꺼내 Item 에 넣는다
  └ next_page 가 있으면: yield response.follow(next_page, callback=self.parse)
                    └▶ parse(다음 목록 응답)  … 다음 링크가 없을 때까지 반복
```

① `response.follow` 는 `/a/1` 같은 상대 URL 을 현재 응답의 주소 기준으로 절대 URL 로 바꿔 요청을 만든다.
② `meta` 에 넣은 딕셔너리는 그 요청의 응답에서 `response.meta` 로 다시 꺼낼 수 있다 — 목록에서만 보이는 제목 · 날짜를 상세 콜백까지 들고 가는 방법이다.
③ 다음 페이지 요청의 콜백을 `self.parse` 자신으로 두면, 다음 링크가 없어질 때까지 목록 페이지를 차례로 훑는다.
④ `if next_page:` 검사가 끝을 정한다 — 마지막 페이지에서는 `.get()` 이 `None` 이라 더 요청하지 않는다.

### (4) ItemLoader — 값 넣기와 꺼내기 사이에 가공 끼우기

**언제 쓰나** — 필드마다 「공백 제거」 「첫 값만」 「줄바꿈으로 합치기」 같은 정제를 반복해서 쓸 때 쓴다.

```text
loader = ArticleLoader(item=ArticleItem(), selector=article)
loader.add_css('title', 'h2::text')    → 선택 결과 리스트 ['  안녕  ']
        │ title_in = MapCompose(str.strip)   (값을 넣는 시점)
        ▼
   내부에 ['안녕'] 으로 쌓임
loader.load_item()
        │ title 의 출력 처리 = default_output_processor = TakeFirst()
        ▼
   item['title'] = '안녕'   (리스트가 아니라 값 하나)
```

① `add_css` · `add_xpath` 는 선택자로 값을 뽑아, 그 필드의 입력 프로세서(`<필드>_in`)를 거쳐 쌓는다.
② `add_value` 는 선택자 없이 값을 직접 넣는다 — 예제의 `add_value('view_count', 0)`.
③ `load_item()` 을 부르면 필드마다 출력 프로세서(`<필드>_out`)를 거쳐 Item 이 완성된다.
④ `<필드>_out` 이 없으면 `default_output_processor` 가 쓰인다 — 예제에서는 `TakeFirst()` 라 리스트의 첫 값만 남는다.
⑤ `MapCompose(str.strip)` 은 리스트의 각 값에 `str.strip` 을 적용한다.
⑥ `Join('\n')` 은 리스트를 줄바꿈으로 이어 붙인 문자열 하나로 만든다 — `content_out`.
⑦ `tags_out = lambda self, values: values` 는 리스트를 그대로 둔다 — 태그는 여러 개라 첫 값만 남기면 안 되기 때문이다.

> **프로세서** — 필드 값 리스트를 받아 바꾼 값을 돌려주는 함수(또는 호출 가능한 객체)다.\
> 예: `TakeFirst()`, `MapCompose(str.strip)`, `Join('\n')`.

### (5) Pipeline — Item 이 지나가는 처리 사슬

**언제 쓰나** — 모은 Item 을 검사하고, 형을 바꾸고, 저장할 때 쓴다.

```text
ITEM_PIPELINES = {Validation: 100, Cleaning: 200, JsonWriter: 300}

Item ─▶ Validation(100) ─▶ Cleaning(200) ─▶ JsonWriter(300)
           │ 제목 없음
           └─ raise DropItem → 여기서 끝. 200 · 300 으로 가지 않는다
```

① 숫자가 작을수록 먼저 실행된다 — 100 → 200 → 300.
② 각 Pipeline 의 `process_item(self, item, spider)` 는 Item 마다 불리고, 돌려준 Item 이 다음 Pipeline 으로 간다.
③ `raise DropItem(...)` 을 하면 그 Item 은 버려지고 뒤의 Pipeline 은 그 Item 을 받지 않는다.
④ `CleaningPipeline` 은 문자열 `'1234'` 로 온 `view_count` 를 `int` 로 바꾸고, 태그마다 `strip()` 을 한다.
⑤ `open_spider` 는 스파이더가 시작할 때, `close_spider` 는 끝날 때 한 번씩 불린다 — 파일을 열고 닫는 자리다.
⑥ `JsonWriterPipeline` 은 Item 을 `dict(item)` 으로 바꿔 리스트에 모아 두었다가, 끝날 때 `json.dump(..., ensure_ascii=False, indent=2)` 로 한꺼번에 쓰고 개수를 로그로 남긴다.
⑦ Pipeline 클래스는 `settings.py` 의 `ITEM_PIPELINES` 에 「경로: 숫자」로 등록해야 쓰인다.

> **DropItem** — Pipeline 에서 「이 Item 은 버린다」를 알리는 예외다.\
> 예: `raise DropItem(f'제목 없는 항목 제거: {item}')`.

### (6) 설정 — 속도와 예의

**언제 쓰나** — 동시 요청 수 · 요청 간격 · robots.txt 준수 여부를 정할 때 쓴다.

```text
settings.py            CONCURRENT_REQUESTS = 16
ArticleSpider.custom_settings  'CONCURRENT_REQUESTS': 8
                                   │ 스파이더 쪽이 우선
                                   ▼
            articles 스파이더는 동시 요청 8 로 돈다
```

① `custom_settings` 는 그 스파이더에만 적용되고 `settings.py` 의 값보다 우선한다.
② `DOWNLOAD_DELAY = 1` 은 요청 사이에 1초를 기다리게 한다.
③ `CONCURRENT_REQUESTS` 는 동시에 진행할 요청 수다.
④ `AUTOTHROTTLE_ENABLED = True` 는 서버 상태에 맞춰 속도를 자동으로 조절하게 한다 — `DOWNLOAD_DELAY` 와 함께 서버 부하를 막는 장치다.
⑤ `ROBOTSTXT_OBEY = True` 는 사이트의 robots.txt 규칙을 지키게 한다 — 반드시 켜 둔다.
⑥ `USER_AGENT = 'MyBot/1.0'` 은 요청에 실을 봇 이름이다.

> **robots.txt** — 사이트가 「봇은 어디를 긁지 말라」고 적어 두는 파일이다.\
> 예: `ROBOTSTXT_OBEY = True` 면 Scrapy 가 이 규칙을 읽고 따른다.

## 문법 — 형태와 규칙

```python
import scrapy

class QuoteItem(scrapy.Item):
    text = scrapy.Field()

class QuoteSpider(scrapy.Spider):
    name = 'quotes'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/list']
    custom_settings = {'DOWNLOAD_DELAY': 1}

    def parse(self, response):
        for q in response.css('.quote'):
            yield QuoteItem(text=q.css('span::text').get(default=''))
        nxt = response.css('.next a::attr(href)').get()
        if nxt:
            yield response.follow(nxt, callback=self.parse)
```

- `Item` 은 `scrapy.Item` 을 상속하고 필드를 `scrapy.Field()` 로 선언한다 — dict 처럼 쓰지만 선언한 필드만 받는다.
- `Spider` 는 `name` 이 필수이고, `start_urls` 와 `parse` 로 출발한다.
- 콜백은 `yield` 로 요청이나 Item 을 내보낸다.
- 값 꺼내기: `.get()` (첫 값) · `.get(default=...)` · `.getall()` (전부) · `.re_first(정규식)`.
- ItemLoader 의 클래스 속성: `default_output_processor`, `<필드>_in`, `<필드>_out`.
- Pipeline 은 상속 없이 `process_item(self, item, spider)` 를 가진 클래스이며, `open_spider` · `close_spider` 를 선택해 둔다.

| 명령 | 하는 일 |
|---|---|
| `pip install scrapy` | 설치 |
| `scrapy startproject myspider` | 프로젝트 뼈대 생성 (`items.py` · `pipelines.py` · `settings.py` · `spiders/`) |
| `scrapy crawl articles` | `name = 'articles'` 스파이더 실행 |
| `scrapy crawl articles -o output.json` | 모은 Item 을 JSON 으로 저장 (`.csv` 면 CSV) |
| `scrapy shell 'URL'` | 응답을 받아 놓고 선택자를 대화형으로 시험 |
| `scrapy view 'URL'` | Scrapy 가 받은 페이지를 브라우저로 열어 보기 |

| 설정 | 예제 값 | 뜻 |
|---|---|---|
| `ITEM_PIPELINES` | 100 · 200 · 300 | Pipeline 등록과 차례(작을수록 먼저) |
| `DOWNLOAD_DELAY` | 1 | 요청 간 대기 초 |
| `CONCURRENT_REQUESTS` | 16 (스파이더에서 8) | 동시 요청 수 |
| `USER_AGENT` | `'MyBot/1.0'` | 봇 이름 |
| `ROBOTSTXT_OBEY` | `True` | robots.txt 준수 |
| `AUTOTHROTTLE_ENABLED` | `True` | 속도 자동 조절 |

## 어디서 틀리나

### 1. 선택자를 코드에서 바로 고치며 맞히려 한다
크롤러를 매번 다시 돌리며 선택자를 고치면 느리고 서버에도 부담이다.
`scrapy shell 'URL'` 로 응답을 한 번 받아 두고 `response.css(...)` 를 대화형으로 시험한 뒤 코드에 옮긴다.

### 2. `.get()` 이 `None` 일 수 있다는 것을 잊는다
`link = article.css('a::attr(href)').get()` 은 링크가 없는 카드에서 `None` 이다.
예제는 그대로 `response.follow(link, ...)` 를 부르므로, 그런 카드가 섞이면 요청을 만들지 못하고 오류가 난다 (원본에 근거 없음 — 추론).
기본값을 주거나 `if link:` 로 걸러야 안전하다.

### 3. 카드 안에서 `//` 로 시작하는 XPath 를 쓴다
카드 하나를 잡은 뒤 `'//span[@class="tag"]'` 를 쓰면 카드가 아니라 문서 전체에서 찾는다.
그래서 예제의 ItemLoader 쪽은 `'.//span[@class="tag"]/text()'` 처럼 점을 붙였다.
반면 `parse_detail` 은 상세 페이지 전체가 대상이라 `//` 로 시작해도 된다.

### 4. `@class="..."` 는 class 속성 문자열 전체와 같아야 맞는다
`//div[@class="article-body"]` 는 `class="article-body"` 인 div 만 고른다.
`class="article-body wide"` 처럼 클래스가 둘 이상이면 문자열이 달라 고르지 못한다.
CSS 의 `.article-body` 는 클래스 하나만 들어 있어도 맞으므로 이 점에서 둘은 다르다.

### 5. 두 스파이더의 선택자가 서로 다르다
`ArticleSpider` 는 작성자를 `.author-name::text` 로, `ArticleSpiderWithLoader` 는 `.author::text` 로 찾는다.
제목도 `h2.title::text` 와 `h2::text` 로 다르다.
같은 사이트를 긁는다면 둘 중 하나는 빈 값을 얻을 수 있다 — 실제 HTML 을 shell 로 확인해야 한다.

### 6. Pipeline 숫자의 방향을 거꾸로 안다
숫자가 작을수록 먼저 실행된다.
검사(100)를 저장(300)보다 뒤에 두면 버려야 할 Item 이 이미 파일에 들어간다.

### 7. `view_count` 의 0 과 「없음」을 가리지 못한다
`CleaningPipeline` 은 `if item.get('view_count'):` 로 검사한다.
값이 `0` 이면 거짓으로 취급되어 변환을 건너뛴다 — 이미 정수라 문제는 없지만, `'0'` 같은 문자열 외의 거짓 값을 「없음」과 섞어 판단한다는 점은 알아 둔다.

### 8. 파일 저장이 끝에서야 일어난다
`JsonWriterPipeline` 은 Item 을 메모리 리스트에 모았다가 `close_spider` 에서 한꺼번에 쓴다.
크롤링이 비정상으로 끝나 `close_spider` 가 불리지 않으면 모은 것을 잃을 수 있다 (원본에 근거 없음 — 추론).
또 `-o output.json` 과 함께 쓰면 같은 이름의 파일을 두 경로가 쓰게 되니 이름을 가른다.

### 9. 「빠르니까」 마음껏 긁는다
Twisted 기반 비동기라 빠른 만큼 상대 서버에 부담을 주기 쉽다.
`DOWNLOAD_DELAY` · `AUTOTHROTTLE_ENABLED` 로 속도를 낮추고, `ROBOTSTXT_OBEY = True` 로 robots.txt 를 반드시 지킨다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| Scrapy 는 Twisted 기반 비동기로 빠르다 | Scrapy 의 구현 선택이다 — 파이썬 언어와 무관하며 속도 수치는 원본에 없다 |
| Pipeline 숫자가 작을수록 먼저 실행된다 | Scrapy 의 설정 규칙이다 |
| `custom_settings` 가 `settings.py` 보다 우선한다 | Scrapy 의 설정 우선순위 규칙이다 |
| `DOWNLOAD_DELAY = 1` 이면 요청 간 1초 대기 | Scrapy 의 설정이다 — 정확히 1초로 고정되는지는 다른 설정에 달렸을 수 있다 (확인 필요) |
| robots.txt 를 지킨다 | `ROBOTSTXT_OBEY` 를 켰을 때 Scrapy 가 지킨다 — robots.txt 자체는 법적 강제가 아니라 사이트의 요청이다 |
| `parse` 가 `yield` 로 값을 여러 개 낸다 | 파이썬 언어(제너레이터)가 보장한다 |
| `dict(item)` 으로 Item 을 딕셔너리로 바꾼다 | Scrapy `Item` 이 dict 와 같은 인터페이스를 주기 때문이다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 페이지 수백 · 수천 개를 따라가며 모은다 | Scrapy Spider + Pipeline | 반복문으로 한 장씩 동기 요청 |
| 목록에서만 보이는 값을 상세 페이지 Item 에 넣는다 | `response.follow(..., meta={...})` | 전역 변수에 임시 보관 |
| 필드마다 같은 정제를 반복한다 | `ItemLoader` + `_in` · `_out` 프로세서 | 콜백마다 `strip()` 을 손으로 반복 |
| 빈 값 · 잘못된 값 걸러내기 | 앞번호 Pipeline 에서 `DropItem` | 저장 뒤에 따로 지우기 |
| 선택자를 맞혀 보기 | `scrapy shell` | 크롤러 전체를 매번 재실행 |
| 남의 서버를 긁는다 | `DOWNLOAD_DELAY` · `AUTOTHROTTLE` · `ROBOTSTXT_OBEY = True` | 지연 없이 최대 동시 요청 |

## 핵심 문장

1. **Spider 의 콜백은 응답을 받아 요청과 Item 을 `yield` 한다** — 요청은 다시 콜백으로, Item 은 Pipeline 으로 간다.
2. **값은 선택자로 꺼낸다** — CSS 는 `::text` · `::attr()`, XPath 는 `//`(전체) · `.//`(현재 노드 아래), `.get()` 은 하나, `.getall()` 은 전부.
3. **`response.follow` 는 상대 URL 을 처리하고, `meta` 로 콜백 사이에 데이터를 넘긴다.**
4. **Pipeline 은 숫자가 작은 것부터 돌고, `DropItem` 이 나면 그 Item 은 뒤로 가지 않는다.**
5. **빠른 만큼 예의를 지킨다** — 요청 지연 · 자동 조절 · robots.txt 준수.

## 관련 자료

- `beautifulsoup` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [selenium](../09-selenium/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `scrapy-basics`

## 용어 풀이

- **Spider** — 시작 URL 과 콜백으로 크롤링 로직을 정의한 클래스.
- **콜백** — 응답이 오면 불러 달라고 넘겨 둔 함수.
- **제너레이터** — `yield` 로 값을 하나씩 내보내는 함수.
- **Item** — 모을 데이터의 필드를 선언한 dict 비슷한 구조.
- **Field** — Item 의 필드 하나를 선언하는 객체.
- **선택자** — 문서에서 노드를 가리키는 표현식(CSS · XPath).
- **SelectorList** — `css()` · `xpath()` 가 돌려주는 선택 결과의 목록.
- **XPath** — 경로식으로 XML · HTML 노드를 고르는 언어.
- **`meta`** — 요청에 실어 응답의 `response.meta` 로 다시 꺼내는 사용자 데이터.
- **ItemLoader** — 필드 값에 입력 · 출력 프로세서를 적용해 Item 을 채우는 도우미.
- **프로세서** — 값 리스트를 받아 가공해 돌려주는 함수.
- **Pipeline** — Item 이 차례로 지나가는 후처리 단계.
- **DropItem** — Pipeline 에서 Item 을 버릴 때 던지는 예외.
- **`custom_settings`** — 스파이더 하나에만 적용되는 설정 덮어쓰기.
- **robots.txt** — 사이트가 봇에게 크롤링 범위를 알리는 파일.
- **Twisted** — Scrapy 가 비동기 네트워크 처리에 쓰는 파이썬 프레임워크.

## 더 들어가면

- 최신 Scrapy 에서는 콜백에 데이터를 넘길 때 `meta` 대신 `cb_kwargs` 를 권하는 흐름이 있다 (확인 필요).
- `tags_out` 처럼 리스트를 그대로 두는 출력 프로세서는 보통 `itemloaders.processors.Identity()` 로 쓴다 (확인 필요).
- `TakeFirst()` 는 `None` 과 빈 문자열을 건너뛰고 첫 「쓸 만한」 값을 고른다 (확인 필요).
- `DOWNLOAD_DELAY` 는 기본적으로 `RANDOMIZE_DOWNLOAD_DELAY` 에 의해 지정 값 근처에서 무작위로 흔들린다 (확인 필요).
- `scrapy startproject` 가 만드는 `settings.py` 에는 `ROBOTSTXT_OBEY = True` 가 들어 있다 (확인 필요).
- 요청을 가로채 헤더를 바꾸거나 재시도하는 일은 다운로더 미들웨어(`DOWNLOADER_MIDDLEWARES`)가 맡는다 (확인 필요).
- 저장은 Pipeline 대신 `FEEDS` 설정으로도 할 수 있다 (확인 필요).
