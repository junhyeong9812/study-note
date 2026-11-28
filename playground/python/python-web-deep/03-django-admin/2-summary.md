# python/python-web-deep/03 — Django Admin 커스터마이징 — 정리 (힌트)

> 출처 — study-site 항목 `python/django-admin`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/django-admin.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Django Admin 은 「가게 창고의 재고 장부」이고, `ModelAdmin` 은 「장부 양식 설계도」다.**
장부를 처음 받으면 품목 이름만 한 줄씩 적혀 있다.
주인은 양식을 고쳐 칸(가격 · 재고 · 상태)을 늘리고, 옆에 「품절만 보기」 색인 탭을 붙이고, 여러 품목에 한꺼번에 「배송 완료」 도장을 찍고, 주문서 안에 주문 품목 명세를 같이 적게 만든다.
Django Admin 도 똑같은 구조다.
모델을 등록하면 기본 관리자 화면이 생기고, `ModelAdmin` 을 상속한 클래스에 옵션을 적어 그 화면을 바꾼다.

> **Django Admin** — Django 가 모델을 바탕으로 자동으로 만들어 주는 관리자(운영자용) 웹 화면.\
> 예: 상품 · 주문 · 고객을 웹 화면에서 목록으로 보고 고친다.

> **ModelAdmin** — 모델 하나의 관리자 화면 설정을 담는 Django 클래스. 상속해서 옵션을 적는다.\
> 예: `class ProductAdmin(admin.ModelAdmin): list_display = [...]`

| 비유 | 실체 |
|---|---|
| 장부 양식 설계도 | `ModelAdmin` 을 상속한 클래스 |
| 장부의 칸 | `list_display` |
| 색인 탭 | `list_filter` · `SimpleListFilter` |
| 한꺼번에 찍는 도장 | `actions` |
| 주문서 안의 품목 명세 | `inlines` |
| 장부 한 장의 구역 나누기 | `fieldsets` |

```text
 models.py 의 모델 ──등록──▶ 기본 관리자 화면
                              │
        ModelAdmin 옵션 ──────┤
                              ▼
   ┌ 목록 페이지 ─────────────────────────┐   ┌ 상세 페이지 ────────────┐
   │ 컬럼(list_display) · 필터 사이드바    │   │ 구역(fieldsets)         │
   │ 검색 · 정렬 · 일괄 작업(actions)      │   │ 관련 모델 편집(inlines) │
   └──────────────────────────────────────┘   └─────────────────────────┘
```

## 이 주제가 답하려는 질문

1. 모델을 관리자 화면에 어떻게 올리고, 그 화면을 어디서 고치나?
2. 목록 페이지에 무엇을 보여 주고, 어떻게 거르고, 찾고, 한꺼번에 처리하나?
3. 상세 페이지에서 필드를 어떻게 묶고, 관련 모델을 어떻게 함께 고치나?
4. 필드 이름만으로 안 되는 컬럼과 필터는 어떻게 만드나?

## 동작 방식

### (1) 등록 — 모델을 관리자 화면에 올리기

**언제 쓰나** — 어떤 모델이든 관리자 화면에 보이게 하려면 가장 먼저 등록한다.

```text
admin.site.register(Product)          ──▶ 기본 설정 화면
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin)  ──▶ ProductAdmin 의 옵션이 적용된 화면
```

- 첫 줄은 모델만 넘겨 기본 설정으로 등록한다.
- 둘째 꼴은 데코레이터로 등록하면서 설정 클래스를 같이 붙인다. 원본은 이 방식을 권장한다.
- 설정 클래스 몸통이 `pass` 뿐이면 기본 설정과 같은 화면이 된다.

> **데코레이터** — 함수나 클래스 정의 바로 위에 `@이름` 을 붙여 그 정의를 감싸거나 등록하는 파이썬 문법.\
> 예: `@admin.register(Product)` 는 바로 아래 클래스를 `Product` 의 설정으로 등록한다.

### (2) 목록 페이지 옵션

**언제 쓰나** — 목록 화면의 컬럼 · 필터 · 검색 · 정렬 · 쪽 나눔을 정할 때 쓴다.

```text
list_display   = ['name', 'price', ...]   ──▶ 목록 표의 컬럼
list_filter    = ['category', ...]        ──▶ 오른쪽 필터 사이드바
search_fields  = ['name', 'category__name'] ─▶ 검색창 (icontains)
ordering       = ['-created_at']          ──▶ 기본 정렬 (- 는 내림차순)
list_editable  = ['price', 'stock', ...]  ──▶ 목록에서 바로 수정
list_per_page  = 25                       ──▶ 한 쪽에 25개
date_hierarchy = 'created_at'             ──▶ 날짜로 좁혀 가는 네비게이션
```

- `list_display` 에 적은 필드가 표의 컬럼이 된다.
- `list_filter` 에 적은 필드마다 사이드바에 필터가 생긴다.
- `search_fields` 는 적은 필드들에서 검색어를 찾는다. 원본 주석대로 `icontains`(대소문자 무시, 포함 검색)를 쓴다.
- `category__name` 처럼 `__` 로 이으면 관련 모델의 필드까지 건너가 찾는다.
- `ordering` 의 `-` 는 내림차순이다. `-created_at` 이면 최근 것부터 나온다.
- `list_editable` 에 적은 필드는 상세 페이지에 들어가지 않고 목록에서 바로 고친다.
- `list_per_page` 는 한 쪽의 항목 수, `date_hierarchy` 는 날짜 필드로 연 · 월 · 일을 골라 들어가는 네비게이션이다.

> **icontains** — 대소문자를 가리지 않고 「이 글자를 포함하나」로 찾는 Django 조회 방식.\
> 예: 검색어 `django` 는 「Django 마스터」에 걸린다.

### (3) 계산된 컬럼 — `@admin.display`

**언제 쓰나** — 모델 필드에 그대로 없는 값(재고에서 계산한 상태 등)을 컬럼으로 보일 때 쓴다.

```text
@admin.display(description='재고 상태', ordering='stock')
def stock_status(self, obj):            obj.stock 이 0   ──▶ '품절'
    ...                                 obj.stock < 10  ──▶ '부족 (3)'
                                        그 밖           ──▶ '충분 (50)'
list_display 에 'stock_status' 를 넣으면 ──▶ 「재고 상태」 컬럼
```

- `ModelAdmin` 의 메서드는 행 하나(`obj`)를 받아 그 칸에 보일 값을 돌려준다.
- `description` 은 컬럼 머리글이다.
- `ordering='stock'` 은 이 계산 컬럼을 누르면 실제 필드 `stock` 으로 정렬하라는 뜻이다. 계산 결과 자체는 데이터베이스 필드가 아니라서 정렬 기준을 따로 알려 준다.
- 원본의 Inline 예는 데코레이터 대신 `item_count.short_description = '상품 수'` 처럼 함수에 속성을 달아 머리글을 정한다. 하는 일은 `description` 과 같다.

### (4) 액션 — 선택한 항목 일괄 작업

**언제 쓰나** — 목록에서 체크한 여러 항목에 같은 일을 한꺼번에 할 때 쓴다.

```text
목록에서 주문 체크 ──▶ 액션 고르기 ──▶ mark_as_shipped(self, request, queryset)
                                         │ queryset = 체크한 주문들
                                         ▼
                        queryset.update(status='shipped')  → 바뀐 개수
                        self.message_user(request, 'N개 주문이 배송 처리됨')
```

- `actions` 에 메서드 이름 문자열을 적고, 메서드에 `@admin.action(description=...)` 을 붙인다. `description` 이 액션 목록에 보이는 이름이다.
- 액션 메서드는 `request` 와 `queryset`(선택된 항목들)을 받는다.
- `queryset.update(...)` 는 바뀐 행의 수를 돌려준다. 원본은 그 수를 `updated` 에 받아 `message_user` 로 화면에 알린다.
- `mark_as_cancelled` 는 `queryset.filter(status='pending')` 으로 한 번 더 거른 뒤 바꾼다. 그래서 대기 중인 주문만 취소되고, 메시지의 수는 고른 수보다 작을 수 있다.
- `export_csv` 는 DB 를 바꾸지 않고 `HttpResponse` 를 만들어 돌려준다. `Content-Disposition` 머리에 `attachment` 를 주어 `orders.csv` 파일로 내려받게 한다.

> **queryset** — 데이터베이스에서 가져올 행들의 묶음을 나타내는 Django 객체. 거르거나 한꺼번에 고칠 수 있다.\
> 예: `queryset.filter(stock=0)` 은 재고가 0 인 행만 남긴다.

### (5) 인라인 — 부모 화면에서 자식 모델 편집

**언제 쓰나** — 주문을 고치면서 그 주문의 품목 · 메모를 같은 화면에서 고칠 때 쓴다.

```text
OrderAdmin.inlines = [OrderItemInline, OrderNoteInline]

주문 상세 페이지
 ├ 주문 필드들
 ├ 품목 (TabularInline: 한 행 = 한 품목, 표)   extra=1, min_num=1, max_num=20
 └ 메모 (StackedInline: 한 항목 = 세로로 쌓인 폼) extra=0
```

- 인라인 클래스는 `model` 에 자식 모델을 적고, 부모 `ModelAdmin` 의 `inlines` 목록에 넣는다.
- `TabularInline` 은 표 형식, `StackedInline` 은 세로로 쌓는 형식이다.
- `extra` 는 미리 보여 줄 빈 폼 수, `min_num` · `max_num` 은 최소 · 최대 항목 수다.
- `readonly_fields` 에 적은 필드(`subtotal`)는 보이기만 하고 고칠 수 없다.
- `autocomplete_fields` 는 관련 항목(`product`)을 고를 때 자동완성 검색을 쓴다.

### (6) fieldsets — 상세 페이지 구역 나누기

**언제 쓰나** — 상세 페이지의 필드가 많아 묶어서 보여 줄 때 쓴다.

```text
fieldsets = [ ('기본 정보', {'fields': (...)}),
              ('주소', {'fields': (...), 'classes': ('collapse',)}),
              ('메타', {...collapse...}) ]
──▶ 제목 붙은 구역 셋. 「주소」 「메타」 는 접힌 채로 둘 수 있다
```

- 목록의 원소 하나가 `(구역 제목, 옵션 사전)` 하나다.
- `'fields'` 는 그 구역에 놓을 필드, `'classes': ('collapse',)` 는 접을 수 있게 한다.
- 원본은 `created_at` · `updated_at` 을 `readonly_fields` 에도 넣어 보기만 하게 한다.
- `autocomplete_fields = ['referred_by']` 로 추천인을 자동완성 검색으로 고른다.

### (7) 커스텀 필터 — `SimpleListFilter`

**언제 쓰나** — 필드 값 그대로가 아니라 「0 초과 10 미만」 같은 조건으로 거를 때 쓴다.

```text
lookups()  ──▶ 사이드바 선택지  ('out','품절') ('low','부족 (10 미만)') ('ok','충분 (10 이상)')
사용자가 '부족' 클릭 ──▶ URL 에 stock_range=low
queryset() ──▶ self.value() == 'low'  → queryset.filter(stock__gt=0, stock__lt=10)
```

- `title` 은 사이드바 제목, `parameter_name` 은 URL 에 실리는 이름이다.
- `lookups` 는 `(값, 보이는 이름)` 쌍 목록을 돌려준다.
- `queryset` 은 `self.value()` 로 고른 값을 보고 걸러진 queryset 을 돌려준다. 아무것도 안 골랐으면 받은 queryset 을 그대로 돌려준다.
- `stock__gt` 는 「보다 크다」, `stock__lt` 는 「보다 작다」, `stock__gte` 는 「크거나 같다」다.
- 만든 필터 클래스는 `list_filter = [StockRangeFilter, 'category', ...]` 처럼 필드 이름과 섞어 넣는다.

### (8) 순수 파이썬 시뮬레이션

**언제 쓰나** — Django 없이 목록 · 필터 · 액션이 무엇을 하는지 흉내 내 볼 때 쓴다(원본 7번).

```text
Product 4개 (재고 50, 3, 0, 15)
 ├ 표 출력: 각 행에 stock_status()      ──▶ 충분 (50) / 부족 (3) / 품절 / 충분 (15)
 ├ 필터: 0 < p.stock < 10 인 것만       ──▶ Django 마스터: 3개
 └ 액션: p.stock == 0 인 것의 개수      ──▶ 1개 상품 비활성화됨
```

- 클래스 `Product` 의 `stock_status()` 가 `@admin.display` 계산 컬럼을 흉내 낸다.
- 리스트 컴프리헨션 `[p for p in products if 0 < p.stock < 10]` 이 `stock__gt=0, stock__lt=10` 을 흉내 낸다.
- 액션 흉내는 품절 상품의 **개수만 세어 출력**한다. 상품의 어떤 값도 바꾸지 않는다.

## 문법 — 형태와 규칙

```python
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'stock', 'stock_status']
    list_filter = ['category']
    actions = ['zero_stock']

    @admin.display(description='재고 상태', ordering='stock')
    def stock_status(self, obj):
        return '품절' if obj.stock == 0 else '있음'

    @admin.action(description='재고를 0 으로')
    def zero_stock(self, request, queryset):
        n = queryset.update(stock=0)
        self.message_user(request, f'{n}개 바뀜')
```

- 설정 클래스는 `admin.ModelAdmin` 을 상속한다.
- 옵션은 클래스 속성(목록 · 문자열 · 수)으로 적는다.
- 계산 컬럼 메서드는 `(self, obj)` 를 받고, 액션 메서드는 `(self, request, queryset)` 을 받는다.
- 액션은 `actions` 목록에 **메서드 이름 문자열**로 넣는다.
- 인라인은 `admin.TabularInline` · `admin.StackedInline` 을 상속하고 `model` 을 적는다.
- 커스텀 필터는 `admin.SimpleListFilter` 를 상속하고 `title` · `parameter_name` · `lookups` · `queryset` 을 채운다.
- 조회 조건은 `필드__연산자` 꼴이다(`stock__gte=10`, `category__name`).

| 옵션 | 어디에 | 하는 일 |
|---|---|---|
| `list_display` | 목록 | 컬럼 |
| `list_filter` | 목록 | 필터 사이드바 |
| `search_fields` | 목록 | 검색 (`icontains`) |
| `ordering` | 목록 | 기본 정렬 |
| `list_editable` | 목록 | 목록에서 바로 수정 |
| `list_per_page` | 목록 | 한 쪽 항목 수 |
| `date_hierarchy` | 목록 | 날짜 네비게이션 |
| `actions` | 목록 | 일괄 작업 |
| `inlines` | 상세 | 관련 모델 함께 편집 |
| `fieldsets` | 상세 | 필드 구역 나누기 |
| `readonly_fields` | 상세 · 인라인 | 읽기 전용 |
| `autocomplete_fields` | 상세 · 인라인 | 관련 항목 자동완성 |

## 어디서 틀리나

### 1. 계산 컬럼은 그냥 정렬되지 않는다

계산 결과는 데이터베이스 필드가 아니다.
그래서 `@admin.display(ordering='stock')` 처럼 정렬에 쓸 실제 필드를 알려 줘야 그 컬럼 머리글로 정렬할 수 있다.

### 2. 액션의 메시지 수 ≠ 고른 수

`mark_as_cancelled` 는 고른 주문 중 `status='pending'` 인 것만 바꾼다.
`update` 는 바뀐 행의 수를 돌려주므로 메시지에는 실제로 취소된 수만 찍힌다.

### 3. 문자열 `list_filter` 로는 범위 조건을 못 만든다

`'category'` 처럼 필드 이름을 적으면 그 필드 값으로 거르는 필터가 생길 뿐이다.
「0 초과 10 미만」 같은 임의 조건은 `SimpleListFilter` 를 만들어야 한다.

### 4. `queryset()` 에서 받은 queryset 을 돌려주지 않으면

원본의 `queryset` 메서드는 세 값 어디에도 안 맞을 때 마지막 줄에서 `return queryset` 을 한다.
이 줄이 빠지면 아무 필터도 안 고른 상태(`self.value()` 가 비었을 때)를 처리하지 못한다.

### 5. 시뮬레이션의 「비활성화」는 아무것도 바꾸지 않는다

원본 7번의 액션 흉내는 `len(out_of_stock)` 을 세어 출력만 한다.
「비활성화됨」이라는 문구와 달리 상품 객체의 값은 그대로다.
진짜 액션은 `queryset.update(...)` 처럼 DB 를 바꾼다.

### 6. 한글이 섞이면 표 줄이 어긋나 보인다

`f"{p.name:<16}"` 의 폭 16 은 **글자 수**다.
한글 한 글자는 화면에서 영문 두 칸쯤을 차지하므로 한글이 많은 줄이 오른쪽으로 밀려 보인다.
원본 출력의 머리글 줄(`이름 … 가격 …`)과 데이터 줄이 맞지 않는 것이 그 결과다.

### 7. 안 쓰는 import

원본은 `datetime` · `timedelta` · `List` 를 가져오지만 어디에서도 쓰지 않는다.
정답 코드 주석은 「날짜 계산용 (예: 최근 가입자 필터)」이라 하지만 그런 필터는 코드에 없다.

### 8. 섹션 1~6 은 문자열 출력일 뿐이다

원본의 섹션 1~6 은 Django 코드를 `print("""...""")` 로 찍을 뿐 실행하지 않는다.
`OrderItem` · `OrderNote` · `Customer` 모델도 정의되어 있지 않다.
실제로 쓰려면 Django 프로젝트의 `admin.py` 에 옮겨야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `search_fields` 는 `icontains` 로 찾는다 | Django 프레임워크(원본 주석). 대소문자 무시가 실제로 어떻게 되는지는 데이터베이스 백엔드에 따를 수 있다(확인 필요) |
| 액션은 「트랜잭션 단위」다 | 원본 정답 코드 주석의 주장이다 → Django 가 액션을 자동으로 트랜잭션으로 감싼다는 근거가 원본에 없어 의심스럽다(확인 필요) |
| `@admin.register` 방식을 권장한다 | 원본의 권장 · 관례. 언어나 프레임워크가 강제하지 않는다 |
| `queryset.update()` 는 바뀐 행 수를 돌려준다 | Django ORM |
| `f"{x:<16}"` 의 폭은 글자 수로 센다 | 파이썬 언어(서식 명세). 화면의 칸 수는 터미널 · 글꼴이 정한다 |
| `0 < p.stock < 10` 은 두 비교의 `and` 다 | 파이썬 언어(연쇄 비교) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 목록에 필드 값을 그대로 보이기 | `list_display` 에 필드 이름 | 같은 값을 돌려주는 메서드 |
| 계산한 값을 컬럼으로 | `@admin.display` 메서드 | 모델에 중복 필드 추가 |
| 필드 값 하나로 거르기 | `list_filter` 에 필드 이름 | `SimpleListFilter` |
| 범위 · 복합 조건으로 거르기 | `SimpleListFilter` | 문자열 `list_filter` |
| 여러 행을 한꺼번에 바꾸기 | `actions` + `queryset.update` | 행마다 상세 페이지 열기 |
| 부모와 자식을 같이 편집 | `inlines` | 자식 모델 화면을 따로 오가기 |
| 필드가 많은 상세 페이지 | `fieldsets` + `collapse` | 한 줄로 늘어놓기 |

## 핵심 문장

1. **Admin 화면은 `ModelAdmin` 을 상속한 클래스의 옵션으로 고친다** — 등록은 `@admin.register`.
2. **목록 페이지는 `list_display` · `list_filter` · `search_fields` · `actions` 로 짠다.**
3. **상세 페이지는 `fieldsets` 로 묶고 `inlines` 로 관련 모델을 함께 편집한다.**
4. **필드 이름으로 안 되는 것은 직접 만든다** — 컬럼은 `@admin.display`, 필터는 `SimpleListFilter`.
5. **액션은 선택된 queryset 을 받아 일괄로 처리하고, 응답을 돌려줄 수도 있다(CSV 내보내기).**

## 관련 자료

- `django-queryset` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [django-signals](../02-django-signals/2-summary.md)
- [django-testing](../06-django-testing/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `django-admin`

## 용어 풀이

- **Django Admin** — 모델을 바탕으로 자동 생성되는 관리자 웹 화면.
- **ModelAdmin** — 모델 하나의 관리자 화면 설정을 담는 클래스.
- **데코레이터** — 정의 위에 `@이름` 을 붙여 감싸거나 등록하는 문법.
- **list_display** — 목록 표의 컬럼 목록.
- **list_filter** — 목록 오른쪽 필터 사이드바에 올릴 필드 · 필터 목록.
- **search_fields** — 검색창이 찾아볼 필드 목록.
- **icontains** — 대소문자를 가리지 않는 포함 검색.
- **list_editable** — 목록에서 바로 고칠 수 있는 필드.
- **date_hierarchy** — 날짜 필드로 연 · 월 · 일을 좁혀 가는 네비게이션.
- **action(액션)** — 목록에서 고른 여러 항목에 하는 일괄 작업.
- **queryset** — 데이터베이스 행 묶음을 나타내는 Django 객체.
- **message_user** — 관리자 화면 위에 알림 메시지를 띄우는 `ModelAdmin` 메서드.
- **inline(인라인)** — 부모 상세 페이지 안에서 자식 모델을 함께 편집하는 장치.
- **TabularInline / StackedInline** — 인라인을 표로 / 세로로 쌓아 보이는 두 형식.
- **fieldsets** — 상세 페이지 필드를 제목 붙은 구역으로 묶는 설정.
- **collapse** — 구역을 접을 수 있게 하는 클래스 이름.
- **readonly_fields** — 보이기만 하고 고칠 수 없는 필드.
- **autocomplete_fields** — 관련 항목을 자동완성 검색으로 고르게 하는 필드.
- **SimpleListFilter** — 선택지와 거르는 조건을 직접 정의하는 필터 클래스.
- **조회 연산자(`__gt` 등)** — `필드__연산자` 꼴로 쓰는 비교 조건.

## 더 들어가면

- `@admin.display` · `@admin.action` 데코레이터는 Django 3.2 에서 들어왔고, 그 전에는 `short_description` 같은 함수 속성을 썼다(확인 필요).
- `list_editable` 의 필드는 `list_display` 에도 있어야 하고, 행의 링크가 걸리는 컬럼(기본은 첫 컬럼)일 수 없다(확인 필요).
- `autocomplete_fields` 를 쓰려면 관련 모델의 `ModelAdmin` 에 `search_fields` 가 있어야 한다(확인 필요).
- 액션 메서드가 `None` 을 돌려주면 목록 페이지로 돌아오고, `HttpResponse` 를 돌려주면 그 응답이 그대로 나간다(확인 필요).
- `queryset.update()` 는 모델의 `save()` 와 저장 시그널을 거치지 않는다(확인 필요).
- `search_fields` 의 앞에 `^` · `=` 를 붙이면 「시작 일치」 · 「정확히 일치」로 바꿀 수 있다(확인 필요).
