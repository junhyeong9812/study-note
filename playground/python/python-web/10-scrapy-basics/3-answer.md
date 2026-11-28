# python/python-web/10 — Scrapy (크롤링 프레임워크) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 제목 · 링크는 문자열, 날짜는 빈 문자열, 작성자는 `None`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `title` → `'첫 글'`
- `link` → `'/a/1'` (상대 주소 그대로)
- `date` → `''`
- `author` → `None`

**왜 그런가**

`::text` 는 텍스트 노드를, `::attr(href)` 는 속성 값을 고르고 `.get()` 은 첫 결과를 문자열로 준다.
`.date` 요소가 없으니 결과가 비고, `default=''` 를 줬으므로 `''` 가 나온다.
`.author-name` 도 없지만 기본값을 주지 않았으므로 `None` 이다.
`link` 는 아직 절대 주소가 아니며, 절대 주소로 바꾸는 일은 `response.follow` 가 한다.
근거: 2-summary 「동작 방식 (2)」 ③ · ④.

### 2. Validation 만 불리고, 파일에는 들어가지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`ValidationPipeline`(100) 의 `process_item` 만 불리고, 그 안에서 `DropItem` 이 나서 `CleaningPipeline`(200) · `JsonWriterPipeline`(300) 은 이 Item 을 받지 않는다.
따라서 `output.json` 에 들어가지 않는다.

**왜 그런가**

실행 차례는 딕셔너리에 적은 순서가 아니라 숫자로 정해지며, 작은 숫자가 먼저다 — 100 → 200 → 300.
`not item.get('title')` 이 참이라 `raise DropItem(...)` 이 일어나고, `DropItem` 이 나면 뒤 Pipeline 은 그 Item 을 처리하지 않는다.
근거: 2-summary 「동작 방식 (5)」 ① · ③.

### 3. `title` 은 `'첫 글'`, `content` 는 `'가\n나'`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `item['title']` → `'첫 글'`
- `item['content']` → `'가\n나'` (「가」와 「나」 사이에 줄바꿈 하나)

**왜 그런가**

넣는 시점에 `title_in = MapCompose(str.strip)` 이 각 값의 앞뒤 공백을 지워 `['첫 글', '둘째']` 가 쌓인다.
`title_out` 이 따로 없으므로 `default_output_processor = TakeFirst()` 가 쓰여 첫 값 `'첫 글'` 만 남는다.
`content` 도 넣을 때 `['가', '나']` 가 되고, 꺼낼 때 `content_out = Join('\n')` 이 줄바꿈으로 이어 붙인다.
근거: 2-summary 「동작 방식 (4)」 ① · ③ ~ ⑥.

### 4. 상대 URL 을 현재 페이지 기준 절대 URL 로 바꿔 주기 때문이다

카드의 `href` 는 `/a/1` 처럼 도메인이 빠진 상대 주소인 경우가 많다.
`response.follow` 는 이 값을 현재 응답의 주소 기준으로 절대 주소로 바꿔 요청을 만든다.
그래서 주소를 손으로 이어 붙일 필요 없이 `callback` 과 `meta` 만 붙여 넘기면 된다.
근거: 2-summary 「동작 방식 (3)」 ①.

### 5. 목록에서 얻은 값을 다음 콜백까지 들고 가는 통로가 `meta` 이기 때문이다

제목과 날짜는 목록 카드에서 이미 꺼냈다.
상세 페이지 응답은 별개의 요청 · 콜백에서 처리되므로, 앞 콜백의 지역 변수를 볼 수 없다.
요청의 `meta` 에 실은 딕셔너리는 그 응답의 `response.meta` 로 다시 꺼낼 수 있으므로, 상세 페이지에서 같은 값을 다시 찾을 필요가 없다.
근거: 2-summary 「동작 방식 (3)」 ②.

### 6. `articles` 는 8, 다른 스파이더는 `settings.py` 의 16

`custom_settings` 는 그 스파이더에만 적용되고 `settings.py` 의 값보다 우선한다.
그래서 `articles` 는 동시 요청 8 로 돌고, `custom_settings` 가 없는 `articles_v2` 는 `settings.py` 의 16 을 따른다.
근거: 2-summary 「동작 방식 (6)」 ①.

### 7. 카드가 아니라 문서 전체를 찾는다

XPath 의 `//` 는 「문서 어디서든」이라, 카드를 `selector` 로 잡아 두어도 문서 전체의 `tag` span 을 고른다.
그러면 카드마다 다른 기사의 태그까지 몽땅 들어간다.
`.//` 처럼 점을 붙여야 「지금 고른 노드(카드) 아래」로 범위가 좁혀진다.
근거: 2-summary 「동작 방식 (2)」 ⑦ · ⑧, 「어디서 틀리나 3」.

### 8. 고르지 못한다

`@class="article-body"` 는 class 속성 문자열 전체가 `article-body` 와 같아야 맞는다.
`"article-body wide"` 는 문자열이 다르므로 맞지 않고, `content` 는 빈 리스트가 되어 본문이 빈 문자열이 된다.
CSS 선택자 `.article-body` 는 클래스 하나만 들어 있어도 맞으므로 이 경우에는 CSS 쪽이 고를 수 있다.
근거: 2-summary 「어디서 틀리나 4」.

### 9. 제너레이터는 값을 여러 번, 섞어서 내보낼 수 있다

`return` 은 값 하나를 돌려주고 함수를 끝내지만, `yield` 는 값을 하나 내보내고 다음 차례를 기다린다.
그래서 `parse` 는 카드마다 상세 요청을 하나씩 내보내고, 마지막에 다음 페이지 요청까지 내보낼 수 있다.
Scrapy 엔진은 내보낸 것이 요청이면 대기열에, Item 이면 Pipeline 으로 보낸다.
근거: 2-summary 「동작 방식 (1)」 ③, 「핵심 문장 1」.

### 10. 빠를수록 상대 서버를 몰아붙이기 쉬워서 브레이크가 필요하다

Twisted 기반 비동기라 응답을 기다리는 동안 다른 요청을 동시에 진행하므로, 같은 시간에 훨씬 많은 요청이 상대 서버로 간다.
그 속도를 그대로 두면 서버에 부하를 준다.
`DOWNLOAD_DELAY` 로 요청 간격을 두고, `AUTOTHROTTLE_ENABLED` 로 서버 상태에 맞춰 속도를 조절하며, `ROBOTSTXT_OBEY = True` 로 사이트가 막아 둔 곳은 긁지 않는다.
근거: 2-summary 「동작 방식 (1)」 ⑤ · 「동작 방식 (6)」 ② ~ ⑤, 「어디서 틀리나 9」.

## 실습 정답

### 실습 1. 기사 목록을 훑는 Scrapy 크롤러 한 벌 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 일곱 필드 | `class ArticleItem(scrapy.Item)` 의 `title = scrapy.Field()` … `view_count = scrapy.Field()` |
| 2. 이름 · 도메인 · 시작 주소 | `name = 'articles'` · `allowed_domains` · `start_urls` |
| 3. 스파이더 전용 설정 | `custom_settings` 의 `DOWNLOAD_DELAY` · `CONCURRENT_REQUESTS` · `ROBOTSTXT_OBEY` |
| 4. 카드에서 제목 · 링크 · 날짜 | `article.css('h2.title::text').get()` · `'a::attr(href)'` · `.get(default='')` |
| 5. 상세 요청 + 데이터 전달 | `response.follow(link, callback=self.parse_detail, meta={...})` |
| 6. 다음 페이지 | `next_page = ...get()` → `if next_page:` → `response.follow(next_page, callback=self.parse)` |
| 7. 본문 · 태그 XPath | `response.xpath('//div[@class="article-body"]//text()').getall()` · `'//span[@class="tag"]/text()'` |
| 8. Item 내보내기 | `yield ArticleItem(...)` 의 `response.meta[...]` · `response.url` · `.get('익명')` · `' '.join(content).strip()` · `.re_first(r'\d+')` |
| 9. 기본 출력 처리 | `default_output_processor = TakeFirst()` |
| 10. 필드별 프로세서 | `title_in` · `content_in` = `MapCompose(str.strip)`, `content_out = Join('\n')`, `tags_out = lambda self, values: values` |
| 11. 로더 스파이더 | `ArticleSpiderWithLoader.parse` 의 `ArticleLoader(item=ArticleItem(), selector=article)` · `add_css` · `add_xpath('tags', './/span...')` · `add_value('view_count', 0)` · `load_item()` |
| 12. 검사 | `ValidationPipeline.process_item` 의 `raise DropItem(...)` |
| 13. 정제 | `CleaningPipeline.process_item` 의 `int(...)` · `[tag.strip() for tag in ...]` |
| 14. JSON 저장 | `JsonWriterPipeline.open_spider` · `process_item` 의 `dict(item)` · `close_spider` 의 `json.dump(..., ensure_ascii=False, indent=2)` · `spider.logger.info(...)` |
| 15. 설정 · 명령 주석 | `# === 5. settings.py ===` 의 `ITEM_PIPELINES` 100 · 200 · 300 과 `# === 6. 실행 명령어 ===` |
| 16. 정리 출력 | 끝의 `print(...)` 줄들 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web/reference/scrapy-basics.py`

```python
# [웹 프레임워크] Scrapy (크롤링 프레임워크)
# 설명: Scrapy Spider, Item, Pipeline, 선택자, 대규모 크롤링
# 팁: Scrapy는 비동기(Twisted 기반)로 매우 빠르다. DOWNLOAD_DELAY와 AUTOTHROTTLE로 서버 부하를 방지한다. scrapy shell로 선택자를 인터랙티브하게 테스트할 수 있다. Pipeline의 숫자가 작을수록 먼저 실행된다. robots.txt를 반드시 준수한다.

# Scrapy - 대규모 크롤링 프레임워크
# pip install scrapy
# scrapy startproject myspider

# scrapy: Spider/Item/Selector 등 크롤링 컴포넌트 제공
import scrapy
# ItemLoader: 정제 처리 + 출력 가공을 추상화
from scrapy.loader import ItemLoader
# 프로세서: 입력/출력 데이터 변환 함수
from itemloaders.processors import TakeFirst, MapCompose, Join
# DropItem: Pipeline에서 항목을 버릴 때 사용
from scrapy.exceptions import DropItem
import json


# === 1. Item 정의 (items.py) ===
# Item: 크롤링할 데이터의 구조 (dict와 유사하지만 필드 검증 가능)
class ArticleItem(scrapy.Item):
    # Field(): 필드 메타정보 보관 (현재는 비어있음)
    title = scrapy.Field()
    url = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    content = scrapy.Field()
    tags = scrapy.Field()
    view_count = scrapy.Field()


# === 2. Spider 정의 (spiders/article_spider.py) ===
# Spider: 크롤링 로직을 정의하는 클래스
class ArticleSpider(scrapy.Spider):
    # name: 스파이더 식별자 (scrapy crawl <name>)
    name = 'articles'
    # allowed_domains: 외부 도메인 이탈 방지
    allowed_domains = ['example.com']
    # start_urls: 크롤링 시작점
    start_urls = ['https://example.com/articles?page=1']

    # 설정 오버라이드 (settings.py 값보다 우선)
    custom_settings = {
        'DOWNLOAD_DELAY': 1,             # 요청 간 1초 대기
        'CONCURRENT_REQUESTS': 8,        # 동시 요청 수
        'ROBOTSTXT_OBEY': True,          # robots.txt 준수
    }

    # parse: 기본 콜백 (start_urls의 응답이 전달됨)
    def parse(self, response):
        """목록 페이지 파싱"""
        # CSS 선택자
        # response.css(): CSS 선택자로 SelectorList 반환
        for article in response.css('.article-card'):
            # ::text 의사선택자 - 텍스트 노드 추출
            title = article.css('h2.title::text').get()       # 텍스트
            # ::attr() - 속성값 추출
            link = article.css('a::attr(href)').get()          # 속성
            # get(default=...): 없을 때 기본값
            date = article.css('.date::text').get(default='')  # 기본값

            # 상세 페이지로 이동
            # response.follow: 상대 URL 자동 처리
            yield response.follow(
                link,
                callback=self.parse_detail,
                # meta: 다음 콜백에 전달할 사용자 데이터
                meta={'title': title, 'date': date}  # 데이터 전달
            )

        # 다음 페이지
        next_page = response.css('.pagination .next a::attr(href)').get()
        if next_page:
            # 자기 자신을 콜백으로 - 재귀적 페이지 순회
            yield response.follow(next_page, callback=self.parse)

    def parse_detail(self, response):
        """상세 페이지 파싱"""
        # XPath 선택자
        # response.xpath(): XPath 표현식 사용
        content = response.xpath(
            '//div[@class="article-body"]//text()'
        ).getall()                                   # 모든 텍스트
        tags = response.xpath(
            '//span[@class="tag"]/text()'
        ).getall()

        # yield Item: Pipeline으로 전달
        yield ArticleItem(
            # 이전 콜백에서 meta로 전달받은 값 사용
            title=response.meta['title'],
            url=response.url,
            author=response.css('.author-name::text').get('익명'),
            date=response.meta['date'],
            content=' '.join(content).strip(),
            tags=tags,
            # re_first: 정규식 첫 매칭만 추출
            view_count=response.css('.views::text').re_first(r'\d+')  # 정규식
        )


# === 3. ItemLoader (정제된 데이터 로딩) ===
# ItemLoader: 입력 처리 + 출력 처리 자동화
class ArticleLoader(ItemLoader):
    # default_output_processor: 모든 필드의 기본 출력 처리
    default_output_processor = TakeFirst()  # 리스트의 첫 번째 값

    # <field>_in: 해당 필드 입력 처리 (값 추가 시점)
    title_in = MapCompose(str.strip)        # 입력 처리: 공백 제거
    content_in = MapCompose(str.strip)
    # <field>_out: 출력 처리 (load_item 시점)
    content_out = Join('\n')                # 출력 처리: 줄바꿈으로 합치기
    tags_out = lambda self, values: values  # 리스트 그대로


# ItemLoader 사용 예시
class ArticleSpiderWithLoader(scrapy.Spider):
    name = 'articles_v2'
    start_urls = ['https://example.com/articles']

    def parse(self, response):
        for article in response.css('.article-card'):
            # ItemLoader 인스턴스 (item + selector)
            loader = ArticleLoader(item=ArticleItem(), selector=article)
            # add_css/xpath: 선택자로 값 추출 후 입력 프로세서 적용
            loader.add_css('title', 'h2::text')
            loader.add_css('url', 'a::attr(href)')
            loader.add_css('author', '.author::text')
            loader.add_css('date', '.date::text')
            loader.add_xpath('tags', './/span[@class="tag"]/text()')
            loader.add_value('view_count', 0)  # 직접 값 추가
            # load_item: 출력 프로세서 적용 후 Item 반환
            yield loader.load_item()


# === 4. Pipeline (pipelines.py) ===
# Pipeline: 크롤링된 Item을 후처리하는 체인
class ValidationPipeline:
    """데이터 유효성 검사"""
    # process_item: 모든 Item마다 호출되는 핵심 메서드
    def process_item(self, item, spider):
        if not item.get('title'):
            # DropItem 발생 시 이후 Pipeline 중단
            raise DropItem(f'제목 없는 항목 제거: {item}')
        return item


class CleaningPipeline:
    """데이터 정제"""
    def process_item(self, item, spider):
        # 타입 변환
        if item.get('view_count'):
            item['view_count'] = int(item['view_count'])
        # 리스트 정제
        if item.get('tags'):
            item['tags'] = [tag.strip() for tag in item['tags']]
        return item


class JsonWriterPipeline:
    """JSON 파일로 저장"""
    # open_spider: 스파이더 시작 시 호출 (파일 열기 등)
    def open_spider(self, spider):
        self.file = open('output.json', 'w', encoding='utf-8')
        self.items = []

    # close_spider: 스파이더 종료 시 호출 (정리)
    def close_spider(self, spider):
        json.dump(self.items, self.file, ensure_ascii=False, indent=2)
        self.file.close()
        # spider.logger: 스파이더 로거 사용
        spider.logger.info(f'총 {len(self.items)}개 항목 저장')

    def process_item(self, item, spider):
        # dict()로 변환 후 누적
        self.items.append(dict(item))
        return item


# === 5. settings.py ===
# ITEM_PIPELINES = {
#     'myspider.pipelines.ValidationPipeline': 100,   # 숫자 = 우선순위
#     'myspider.pipelines.CleaningPipeline': 200,
#     'myspider.pipelines.JsonWriterPipeline': 300,
# }
# DOWNLOAD_DELAY = 1
# CONCURRENT_REQUESTS = 16
# USER_AGENT = 'MyBot/1.0'
# ROBOTSTXT_OBEY = True
# AUTOTHROTTLE_ENABLED = True


# === 6. 실행 명령어 ===
# scrapy crawl articles                          # 기본 실행
# scrapy crawl articles -o output.json           # JSON 출력
# scrapy crawl articles -o output.csv            # CSV 출력
# scrapy shell 'https://example.com'             # 대화형 셸
# scrapy view 'https://example.com'              # 브라우저로 보기

print("Scrapy 핵심 정리")
print("="*50)
print("Spider: 크롤링 로직 정의 (parse 메서드)")
print("Item: 데이터 구조 정의")
print("Pipeline: 데이터 정제/저장 체인")
print("CSS 선택자: ::text, ::attr(href)")
print("XPath: //div[@class='name']/text()")
print("response.follow(): 상대 URL 자동 처리")
print("DOWNLOAD_DELAY: 서버 부하 방지")
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `scrapy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 콜백은 `yield` 로 요청과 Item 을 섞어 내보내고, 다음 페이지 요청의 콜백을 `self.parse` 로 두어 목록을 끝까지 훑는다.
- 목록에서만 보이는 제목 · 날짜는 `meta` 로 상세 콜백에 넘기고 `response.meta[...]` 로 꺼낸다.
- 없는 값은 `.get(default='')` · `.get('익명')` 으로 막고, 조회수는 `.re_first(r'\d+')` 로 숫자만 뽑은 뒤 `CleaningPipeline` 이 `int` 로 바꾼다.
- 로더에서는 카드 기준으로 찾도록 XPath 앞에 `.` 을 붙이고, 태그는 `tags_out` 으로 리스트를 그대로 둔다.
- `ITEM_PIPELINES` 의 숫자를 100 · 200 · 300 으로 두어 검사가 저장보다 먼저 돌게 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `scrapy` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
