# python/python-web/10 — Scrapy (크롤링 프레임워크) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 날짜가 없는 카드에서 꺼낸 값들 (예측)

```python
# 질문용 발췌 — 카드 HTML: <div class="article-card"><h2 class="title">첫 글</h2><a href="/a/1">더보기</a></div>
title = article.css('h2.title::text').get()
link = article.css('a::attr(href)').get()
date = article.css('.date::text').get(default='')
author = article.css('.author-name::text').get()
```

- `title` · `link` · `date` · `author` 에는 각각 무엇이 들어가나?

### 2. 제목 없는 Item 이 지나가는 길 (예측)

```python
# 질문용 발췌 — settings.py
ITEM_PIPELINES = {
    'myspider.pipelines.JsonWriterPipeline': 300,
    'myspider.pipelines.ValidationPipeline': 100,
    'myspider.pipelines.CleaningPipeline': 200,
}
```

- `title` 이 빈 Item 하나가 들어오면 세 Pipeline 중 어느 것의 `process_item` 이 불리고, 그 Item 은 `output.json` 에 들어가나?

### 3. ItemLoader 가 만든 `title` 과 `content` (예측)

```python
# 질문용 발췌 — ArticleLoader 의 프로세서는 예제와 같다
loader = ArticleLoader(item=ArticleItem())
loader.add_value('title', ['  첫 글  ', '  둘째  '])
loader.add_value('content', ['  가  ', '  나  '])
item = loader.load_item()
```

- `item['title']` 과 `item['content']` 는 각각 무엇인가?

### 4. 상세 페이지로 갈 때 `response.follow` 를 쓰는 까닭 (왜)

- 카드에서 꺼낸 `href` 가 `/a/1` 같은 값일 때, 왜 `response.follow` 로 요청을 만드나?

### 5. 제목을 `meta` 에 실어 보내는 까닭 (왜)

- `parse_detail` 은 왜 제목과 날짜를 상세 페이지에서 다시 뽑지 않고 `response.meta` 에서 꺼내나?

### 6. `settings.py` 는 16, 스파이더는 8 (경계)

- `CONCURRENT_REQUESTS` 가 `settings.py` 에서 16 이고 `ArticleSpider.custom_settings` 에서 8 이면, `articles` 스파이더는 어느 값으로 돌고 다른 스파이더는 어떻게 되나?

### 7. 카드 안에서 점 없이 쓴 XPath (경계)

- ItemLoader 의 태그 XPath 를 `'.//span[@class="tag"]/text()'` 대신 `'//span[@class="tag"]/text()'` 로 쓰면 어디까지 찾게 되나?

### 8. 클래스가 둘인 본문 div (경계)

- 본문이 `<div class="article-body wide">` 일 때 `//div[@class="article-body"]//text()` 는 본문을 고를 수 있나?

### 9. `parse` 가 `return` 대신 `yield` 를 쓰는 것 (연결)

- 파이썬 제너레이터의 어떤 성질 덕분에 `parse` 하나가 상세 요청 · 다음 페이지 요청 · Item 을 섞어 내보낼 수 있나?

### 10. 서버 부하와 Scrapy 의 속도 (연결)

- Twisted 기반 비동기라 빠르다는 성질은 `DOWNLOAD_DELAY` · `AUTOTHROTTLE` · `ROBOTSTXT_OBEY` 를 켜야 하는 까닭과 어떻게 이어지나?

## 실습

### 실습 1. 기사 목록을 훑는 Scrapy 크롤러 한 벌 만들기

**만들 것** — 기사 목록 → 상세 페이지를 따라가며 기사 Item 을 모으고, ItemLoader 버전 스파이더와 검사 · 정제 · JSON 저장 Pipeline 까지 갖춘 파일 하나.

**준비물** — `pip install scrapy` 로 Scrapy 를 설치해야 한다(`ItemLoader` 의 프로세서는 함께 설치되는 `itemloaders` 에서 가져온다).
대상 주소 `https://example.com/...` 은 자리 채움용이라 실제 기사 구조가 있다고 기대하지 않는다.

**요구 조건**

1단계 — Item
1. `ArticleItem` 에 `title` · `url` · `author` · `date` · `content` · `tags` · `view_count` 일곱 필드를 선언한다.

2단계 — 스파이더 `articles`
2. 이름은 `articles`, 허용 도메인은 `example.com`, 시작 주소는 목록 1페이지다.
3. 이 스파이더에만 요청 간 1초 대기 · 동시 요청 8 · robots.txt 준수를 설정한다.
4. `parse` 는 `.article-card` 마다 제목(`h2.title` 텍스트) · 링크(`a` 의 `href`) · 날짜(`.date` 텍스트, 없으면 빈 문자열)를 꺼낸다.
5. 카드마다 링크로 상세 페이지를 요청하되 콜백은 `parse_detail`, 제목과 날짜는 `meta` 로 넘긴다.
6. `.pagination .next a` 의 `href` 가 있으면 그 페이지를 다시 `parse` 로 요청한다.
7. `parse_detail` 은 XPath 로 `article-body` div 아래 모든 텍스트와 `tag` span 의 텍스트를 전부 꺼낸다.
8. `parse_detail` 은 Item 을 내보낸다 — 제목 · 날짜는 `meta` 에서, 주소는 응답 주소, 작성자는 `.author-name` 텍스트(없으면 `'익명'`), 본문은 텍스트 조각을 공백으로 이어 앞뒤를 다듬은 것, 조회수는 `.views` 텍스트에서 정규식으로 뽑은 첫 숫자다.

3단계 — ItemLoader
9. `ArticleLoader` 는 모든 필드의 기본 출력 처리를 「첫 값」으로 둔다.
10. `title` · `content` 는 넣을 때 앞뒤 공백을 지우고, `content` 는 꺼낼 때 줄바꿈으로 합치며, `tags` 는 리스트 그대로 둔다.
11. 스파이더 `articles_v2` 는 카드마다 로더를 만들어 `title` · `url` · `author` · `date` 는 CSS 로, `tags` 는 카드 기준 상대 XPath 로 채우고, `view_count` 에는 값 `0` 을 직접 넣은 뒤 Item 을 내보낸다.

4단계 — Pipeline 과 설정
12. `ValidationPipeline` 은 제목이 없는 Item 을 `DropItem` 으로 버린다.
13. `CleaningPipeline` 은 조회수가 있으면 정수로 바꾸고, 태그가 있으면 태그마다 앞뒤 공백을 지운다.
14. `JsonWriterPipeline` 은 시작할 때 `output.json` 을 열고, Item 마다 딕셔너리로 모아 두었다가, 끝날 때 한글이 깨지지 않게 들여쓰기해 저장한 뒤 저장 개수를 로그로 남긴다.
15. 주석으로 `ITEM_PIPELINES` 를 검사 → 정제 → 저장 차례가 되도록 적고, 나머지 설정과 실행 명령도 주석으로 적는다.
16. 파일 끝에서 Scrapy 핵심 정리 줄들을 `print` 한다.

**시작 코드**

```python
# Scrapy - 대규모 크롤링 프레임워크
import scrapy
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from scrapy.exceptions import DropItem
import json


# === 1. Item 정의 ===
class ArticleItem(scrapy.Item):
    pass  # TODO: 필드 일곱 개 선언


# === 2. Spider 정의 ===
class ArticleSpider(scrapy.Spider):
    # TODO: name · allowed_domains · start_urls
    custom_settings = {
        # TODO: 요청 간 대기 · 동시 요청 수 · robots.txt 준수
    }

    def parse(self, response):
        """목록 페이지 파싱"""
        for article in response.css('.article-card'):
            title = None  # TODO: 제목 텍스트
            link = None   # TODO: 링크 href
            date = None   # TODO: 날짜 텍스트 (없으면 '')
            # TODO: 상세 페이지 요청 (콜백 + meta)

        # TODO: 다음 페이지가 있으면 다시 parse 로

    def parse_detail(self, response):
        """상세 페이지 파싱"""
        content = []  # TODO: XPath — article-body 아래 모든 텍스트
        tags = []     # TODO: XPath — tag span 텍스트 전부
        # TODO: ArticleItem 을 yield


# === 3. ItemLoader ===
class ArticleLoader(ItemLoader):
    pass  # TODO: 기본 출력 처리 · title_in · content_in · content_out · tags_out


class ArticleSpiderWithLoader(scrapy.Spider):
    name = 'articles_v2'
    start_urls = ['https://example.com/articles']

    def parse(self, response):
        for article in response.css('.article-card'):
            loader = None  # TODO: 로더 만들기 (item + selector)
            # TODO: add_css · add_xpath · add_value
            # TODO: load_item 결과를 yield


# === 4. Pipeline ===
class ValidationPipeline:
    def process_item(self, item, spider):
        # TODO: 제목 없으면 버리기
        return item


class CleaningPipeline:
    def process_item(self, item, spider):
        # TODO: 조회수 정수 변환 · 태그 공백 정리
        return item


class JsonWriterPipeline:
    def open_spider(self, spider):
        pass  # TODO: 파일 열기 · 리스트 준비

    def close_spider(self, spider):
        pass  # TODO: JSON 저장 · 파일 닫기 · 개수 로그

    def process_item(self, item, spider):
        # TODO: dict 로 바꿔 모으기
        return item


# === 5. settings.py ===
# TODO: ITEM_PIPELINES 와 나머지 설정을 주석으로

# === 6. 실행 명령어 ===
# TODO: crawl · -o · shell · view 를 주석으로

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

**확인 방법** — `python scrapy-basics.py` 로 파일을 실행해 import 와 클래스 정의가 오류 없이 지나가고 끝의 정리 줄들이 찍히는지 본다.
스파이더 동작은 `scrapy startproject myspider` 로 만든 프로젝트의 `items.py` · `spiders/` · `pipelines.py` · `settings.py` 에 나눠 넣고, 실제 기사 목록이 있는 주소로 바꾼 뒤 `scrapy crawl articles` 로 돌려 `output.json` 을 본다.
선택자는 먼저 `scrapy shell '주소'` 에서 맞혀 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
