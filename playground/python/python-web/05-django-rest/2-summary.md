# python/python-web/05 — Django REST Framework (DRF) — 정리 (힌트)

> 출처 — study-site 항목 `python/django-rest`(항목 데이터 `data/python/web-frameworks.json`) · 정답 코드 study-practice `python/python-web/reference/django-rest.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 외부 라이브러리 `rest_framework` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

## 한눈에 — 쉽게 말하면

**DRF 는 「주문을 받는 식당 홀」이다.**
손님은 정해진 주문서 양식에 맞춰 주문을 적는다.
홀 직원은 주문서가 제대로 채워졌는지 확인하고 주방에 넘긴 뒤, 나온 음식을 접시에 담아 내놓는다.
입구의 안내판은 어느 테이블을 어느 직원이 맡는지 알려 준다.
출입문에서는 손님이 누구인지 확인하고, 한 사람이 한 시간에 너무 많이 주문하지 못하게 막는다.
Django REST Framework(DRF)도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주문서 양식 | `Serializer` — 어떤 필드를 주고받는지 정한다 |
| 주문서 칸 확인 | `validate_<필드>()` · `validate()` |
| 홀 직원 | `ViewSet` — 요청을 받아 처리한다 |
| 직원이 하는 일 목록 | `list` · `create` · `retrieve` · `update` · `partial_update` · `destroy` |
| 메뉴에 없는 특별 주문 | `@action` 으로 붙인 커스텀 엔드포인트 |
| 입구 안내판 | `Router` — URL 을 `ViewSet` 에 이어 준다 |
| 출입 확인 | 인증 · 권한 |
| 시간당 주문 수 제한 | 쓰로틀링 |
| 한 번에 내놓는 접시 수 | 페이지네이션 |

```text
요청  GET /api/posts/?search=django
  │
  ▼
Router ── URL 과 메서드를 보고 ──▶ PostViewSet.list
                                     │ ① 인증: 누구인가
                                     │ ② 권한: 해도 되나
                                     │ ③ 쓰로틀: 너무 자주 오지 않았나
                                     ▼
                                get_queryset() → 필터·검색·정렬 → 페이지로 자르기
                                     ▼
                                PostSerializer: 모델 객체 → dict
                                     ▼
응답  JSON  {"count": …, "next": …, "previous": …, "results": [ … ]}
```

> **API** — 프로그램끼리 정해진 주소와 형식으로 데이터를 주고받는 창구.\
> 예: `GET /api/posts/` 를 보내면 글 목록 JSON 이 돌아온다.

## 이 주제가 답하려는 질문

1. 모델 객체를 JSON 으로, 들어온 JSON 을 모델 객체로 어떻게 바꾸고 검사하나?
2. 목록 · 생성 · 조회 · 수정 · 삭제와 그 URL 을 어떻게 한 번에 만드나?
3. 누가 무엇을 할 수 있는지, 한 번에 몇 개를 돌려줄지, 얼마나 자주 받을지는 어디서 정하나?
4. 기본 CRUD 밖의 동작(글 게시하기, 인기 글 보기)은 어떻게 붙이나?

## 동작 방식

### (1) Serializer — 모델과 JSON 사이의 번역기

**언제 쓰나** — 모델을 응답 JSON 으로 내보낼 때와, 요청 JSON 을 검사해 모델에 저장할 때 쓴다.
`serializers` 모듈이 모델 ↔ JSON 변환과 유효성 검사를 맡는다.

> **직렬화** — 객체를 JSON 같은 전송용 형식으로 바꾸는 일.\
> 예: `Post` 객체 → `{"id": 1, "title": "첫 글"}`.

> **역직렬화** — 들어온 JSON 을 검사해 파이썬 값 · 모델 객체로 바꾸는 일.\
> 예: `{"title": "첫 글", "tag_ids": [1, 2]}` → 검증된 데이터 → `Post` 저장.

```text
읽기 (응답)                         쓰기 (요청)
Post 객체                           요청 JSON
  │ fields 목록대로 꺼냄               │ fields 목록대로 받음
  │ read_only 필드 포함                │ write_only 필드 포함, read_only 필드 무시
  │ source 를 따라 깊이 접근           │ 필드별 변환 → validate_<필드>() → validate()
  ▼                                    ▼
dict → JSON                         validated_data → save() → create()/update()
```

1. 읽을 때는 `Meta.fields` 에 적힌 필드를 모델 객체에서 꺼내 dict 로 만든다.
2. 쓸 때는 들어온 값을 필드마다 바꾸고 검사한 뒤 `validated_data` 를 만든다.
3. `save()` 를 부르면 새 객체면 `create()`, 기존 객체면 `update()` 가 돈다.

`ModelSerializer` 는 `Meta.model` 의 필드를 자동으로 시리얼라이저 필드로 매핑하고, `create` · `update` 도 자동으로 구현한다.
그래서 `TagSerializer` 는 `model = Tag` 와 `fields = ['id', 'name']` 만 적으면 끝난다.

`PostSerializer` 는 자동 매핑 위에 필드를 더 얹는다.

| 필드 | 옵션 | 하는 일 |
|---|---|---|
| `tags` | `TagSerializer(many=True, read_only=True)` | 태그를 `{id, name}` 목록으로 중첩해 응답에만 넣는다 |
| `tag_ids` | `PrimaryKeyRelatedField(many=True, write_only=True, source='tags')` | 입력에서 태그 PK 목록을 받아 모델의 `tags` 에 연결한다 |
| `author_name` | `CharField(source='author.user.get_full_name', read_only=True)` | 점 표기로 관계를 따라가 메서드 결과까지 꺼낸다 |
| `category_name` | `CharField(source='category.name', read_only=True)` | 카테고리 이름을 응답에 넣는다 |
| `summary` | `SerializerMethodField()` | `get_summary()` 의 반환값을 넣는다 |

- `many=True` 는 값 하나가 아니라 목록을 다룬다는 뜻이다.
- `read_only` 필드는 응답에만 나오고 입력에서는 무시된다.
- `write_only` 필드는 입력에만 쓰이고 응답에는 나오지 않는다.
- `source` 는 시리얼라이저 필드 이름과 모델 속성 이름을 다르게 이어 준다.
- `Meta.read_only_fields` 에 적은 `view_count` · `created_at` · `updated_at` 은 응답에만 나오고 입력하면 무시된다.

`tags` 와 `tag_ids` 는 같은 모델 필드 `tags` 를 가리키지만 방향이 다르다.
응답에서는 태그 이름까지 보여 주는 중첩 객체가 편하고, 입력에서는 PK 숫자 목록이 편하기 때문이다.

`SerializerMethodField` 는 이름이 `summary` 면 `get_summary(self, obj)` 를 찾아 부른다.
`get_summary` 는 본문이 200자를 넘으면 앞 200자에 `'...'` 를 붙이고, 넘지 않으면 본문을 그대로 돌려준다.
조건식(`A if 조건 else B`)은 `+` 보다 늦게 묶이므로 `(content[:200] + '...') if … else content` 로 읽힌다.

### (2) 검증 — `validate_<필드>()` 와 `validate()`

**언제 쓰나** — 필드 타입 검사만으로 부족한 업무 규칙을 넣을 때 쓴다.

```text
입력 {"title": "짧", "status": "PB"}
  │ 필드별 변환 (타입·필수 여부)
  ▼
validate_title("짧")  ── 5자 미만 ──▶ ValidationError('제목은 5자 이상이어야 합니다.')
  │ 통과하면
  ▼
validate(data)  ── status == 'PB' 이고 category 없음 ──▶ ValidationError('게시 상태의 글은 카테고리가 필요합니다.')
  │ 통과하면
  ▼
validated_data
```

1. `validate_<필드>(self, value)` 는 그 필드 값 하나만 받아 검사하고, 통과하면 값을 돌려준다.
2. `validate(self, data)` 는 필드 검사가 끝난 dict 전체를 받으므로 여러 필드를 엮어 검사(교차 검증)할 수 있다.
3. 어느 쪽이든 `serializers.ValidationError` 를 던지면 저장되지 않고 오류 응답이 된다.

「게시(`'PB'`)면 카테고리가 필요하다」는 `status` 와 `category` 두 필드를 함께 봐야 하므로 `validate()` 에 둔다.

### (3) ViewSet — CRUD 를 한 클래스에

**언제 쓰나** — 한 모델의 목록 · 생성 · 조회 · 수정 · 삭제를 한꺼번에 API 로 열 때 쓴다.

> **ViewSet** — 여러 동작(action)을 메서드로 모은 뷰 클래스. URL 은 라우터가 붙인다.\
> 예: `PostViewSet` 하나가 목록 · 생성 · 조회 · 수정 · 삭제를 모두 처리한다.

`ModelViewSet` 은 `list` · `create` · `retrieve` · `update` · `partial_update` · `destroy` 를 자동으로 제공한다.
`update` 는 전체 수정(PUT), `partial_update` 는 일부 수정(PATCH)이다.

```text
class PostViewSet(viewsets.ModelViewSet):
    queryset           ─▶ 기본 데이터 (어떤 글들을 다루나)
    serializer_class   ─▶ 어떤 양식으로 주고받나
    permission_classes ─▶ 누가 해도 되나
    filter_backends …  ─▶ 어떻게 거르고 찾고 정렬하나
    perform_create()   ─▶ 저장 직전에 값 끼워 넣기
    get_queryset()     ─▶ 요청마다 데이터 범위 바꾸기
```

- `queryset` 의 `select_related('author__user', 'category')` 는 외래키 관계를 한 쿼리의 JOIN 으로 함께 가져온다.
- `prefetch_related('tags')` 는 다대다 관계를 별도 쿼리 한 번으로 모아 가져온다.
- 둘이 없으면 글 20개를 직렬화할 때 `author_name` · `category_name` · `tags` 를 읽으려고 글마다 쿼리가 더 나간다.

> **N+1 문제** — 목록 1번 조회 뒤 항목마다 관련 데이터를 따로 조회해 쿼리가 N+1 번 나가는 문제.\
> 예: 글 20개 목록 + 글마다 카테고리 조회 20번 = 21번.

- `permission_classes = [IsAuthenticatedOrReadOnly]` 는 읽기는 누구나, 쓰기는 로그인한 사용자만 허용한다.
- `perform_create(self, serializer)` 는 생성 직전에 불린다.
  여기서 `serializer.save(author=self.request.user.author_profile)` 로 작성자를 넣는 것이 흔한 패턴이다.
  작성자를 클라이언트가 보내게 하면 남의 이름으로 글을 쓸 수 있으니, 서버가 아는 로그인 사용자로 채운다.
- `get_queryset()` 은 요청마다 불려 데이터 범위를 정한다.
  `super().get_queryset()` 으로 기본 쿼리셋을 받은 뒤, 로그인하지 않았으면 `status='PB'`(공개) 글만 남긴다.
- `get_object()` 는 URL 의 pk 로 객체 하나를 꺼내며, 이때 객체 수준 권한 검사도 한다.

### (4) 필터 · 검색 · 정렬

**언제 쓰나** — 목록을 쿼리스트링으로 거르고 찾고 정렬하게 할 때 쓴다.

| 속성 | 쿼리 예 | 하는 일 |
|---|---|---|
| `filterset_fields = ['status', 'category', 'author']` | `?status=PB` | 값이 정확히 같은 것만 (`DjangoFilterBackend`) |
| `search_fields = ['title', 'content']` | `?search=django` | 부분 일치 검색 (`SearchFilter`) |
| `ordering_fields = ['created_at', 'view_count']` | `?ordering=-view_count` | 정렬 허용 필드, `-` 는 내림차순 (`OrderingFilter`) |
| `ordering = ['-created_at']` | (없음) | 기본 정렬: 최신 글부터 |

- `filter_backends` 에 적은 백엔드만 켜진다.
- `DjangoFilterBackend` 는 DRF 본체가 아니라 `django_filters` 패키지(django-filter)에서 온다.
- 이 백엔드들은 `list` 가 안에서 부르는 `filter_queryset()` 을 통해 적용된다.

### (5) `@action` — 커스텀 엔드포인트

**언제 쓰나** — CRUD 다섯 동작에 없는 동작을 같은 ViewSet 에 붙일 때 쓴다.

```text
@action(detail=True,  methods=['post'])  def publish  ─▶ POST /api/posts/{pk}/publish/
@action(detail=False, methods=['get'])   def popular  ─▶ GET  /api/posts/popular/
```

1. `detail=True` 는 객체 하나를 대상으로 하므로 URL 에 `{pk}` 가 들어간다.
2. `detail=False` 는 컬렉션(목록 전체)을 대상으로 하므로 `{pk}` 가 없다.
3. URL 끝 조각은 메서드 이름(`publish` · `popular`)이다.
4. `methods` 에 적은 HTTP 메서드만 받는다.
   목록에 없는 메서드로 오면 405(Method Not Allowed)로 거절된다.

- `publish` 는 `get_object()` 로 글을 꺼내 `post.publish()` 를 부르고 `Response({'status': '게시됨'})` 를 돌려준다.
- `popular` 는 `get_queryset().order_by('-view_count')[:10]` 으로 조회수 상위 10개를 고르고, `get_serializer(popular, many=True)` 로 직렬화한다.
- `get_serializer` 는 요청 같은 컨텍스트를 담아 시리얼라이저를 만들어 준다.
- `Response` 는 DRF 응답 객체로, 클라이언트가 원하는 형식(JSON 등)으로 내보내는 콘텐츠 협상을 알아서 한다.

`popular` 는 `get_queryset()` 을 쓰므로 비로그인이면 공개글만 대상이 된다.
그러나 `filter_queryset()` 과 페이지네이션(`paginate_queryset()`)은 부르지 않는다.
그래서 `?search=` · `?ordering=` 은 적용되지 않고, 응답은 페이지 정보 없이 글 목록(최대 10개)만 담은 리스트다.

### (6) Router — URL 자동 생성

**언제 쓰나** — ViewSet 의 동작마다 URL 을 손으로 적지 않고 한 줄로 등록할 때 쓴다.

`DefaultRouter` 는 ViewSet 의 URL 패턴을 자동으로 만들고, 등록한 API 목록을 보여 주는 API 루트 뷰도 제공한다.
`router.register('posts', PostViewSet, basename='post')` 는 `posts` 라는 URL 접두어를 `PostViewSet` 에 잇는다.
`basename` 은 URL 이름(`post-list` · `post-detail` 꼴)의 앞부분이 된다.
`urlpatterns` 에 `path('api/', include(router.urls))` 를 넣어 전체를 `/api/` 아래에 둔다.

| URL | 메서드 | ViewSet 동작 |
|---|---|---|
| `/api/posts/` | GET | `list` |
| `/api/posts/` | POST | `create` |
| `/api/posts/{pk}/` | GET | `retrieve` |
| `/api/posts/{pk}/` | PUT | `update` |
| `/api/posts/{pk}/` | PATCH | `partial_update` |
| `/api/posts/{pk}/` | DELETE | `destroy` |
| `/api/posts/{pk}/publish/` | POST | `publish` (커스텀) |
| `/api/posts/popular/` | GET | `popular` (커스텀) |

### (7) 전역 설정 — 인증 · 권한 · 페이지네이션 · 쓰로틀링

**언제 쓰나** — 모든 뷰에 공통으로 적용할 기본값을 `settings.py` 의 `REST_FRAMEWORK` dict 에 적을 때 쓴다.

> **인증(authentication)** — 요청을 보낸 사람이 누구인지 알아내는 일.\
> 예: 세션 쿠키나 토큰 헤더를 보고 `request.user` 를 정한다.

> **권한(permission)** — 알아낸 사람이 그 동작을 해도 되는지 판단하는 일.\
> 예: 비로그인 사용자의 POST 를 거절한다.

| 키 | 값 | 뜻 |
|---|---|---|
| `DEFAULT_AUTHENTICATION_CLASSES` | `SessionAuthentication`, `TokenAuthentication` (JWT 는 주석) | 인증 방식. 여러 개를 함께 둘 수 있다 |
| `DEFAULT_PERMISSION_CLASSES` | `IsAuthenticatedOrReadOnly` | 기본 권한 정책 |
| `DEFAULT_PAGINATION_CLASS` | `PageNumberPagination` | 기본 페이지네이션 |
| `PAGE_SIZE` | `20` | 한 페이지 항목 수 |
| `DEFAULT_THROTTLE_CLASSES` | `AnonRateThrottle`, `UserRateThrottle` | 요청 빈도 제한 |
| `DEFAULT_THROTTLE_RATES` | `'anon': '100/hour'`, `'user': '1000/hour'` | 비로그인 시간당 100회, 로그인 시간당 1000회 |

- 인증 방식은 Session · Token · JWT 가 있고, JWT 는 `rest_framework_simplejwt` 라는 별도 패키지의 클래스다.
- 뷰 클래스에 `permission_classes` 같은 속성을 적으면 그 뷰에서는 전역 기본값 대신 뷰의 값이 쓰인다.
- 기본 `PageNumberPagination` 의 응답은 `count` · `next` · `previous` · `results` 키를 가진다.
- 페이지네이션 방식에는 PageNumber · LimitOffset · Cursor 가 있다.

> **페이지네이션** — 긴 목록을 페이지로 잘라 일부만 돌려주는 일.\
> 예: `?page=2` 로 21번째~40번째 글을 받는다.

> **쓰로틀링** — 한 클라이언트가 정해진 시간에 보낼 수 있는 요청 수를 제한하는 일.\
> 예: 비로그인 사용자가 한 시간에 101번째 요청을 보내면 거절된다.

### (8) 커스텀 Pagination 과 커스텀 Permission

**언제 쓰나** — 응답 모양이나 페이지 크기, 객체별 접근 규칙을 프로젝트에 맞게 바꿀 때 쓴다.

`CustomPagination` 은 `PageNumberPagination` 을 상속한다.

- `page_size = 10` — 기본 페이지 크기.
- `page_size_query_param = 'page_size'` — 클라이언트가 `?page_size=` 로 크기를 바꿀 수 있다.
- `max_page_size = 100` — 그래도 100을 넘지는 못한다.
- `get_paginated_response(data)` 를 덮어써 응답을 `count` · `total_pages` · `current_page` · `results` 꼴로 바꾼다.

`IsAuthorOrReadOnly` 는 `BasePermission` 을 상속한다.
`BasePermission` 을 상속한 클래스는 `has_permission`(요청 수준)과 `has_object_permission`(객체 수준)을 구현할 수 있다.

```text
has_object_permission(request, view, obj)
  │ request.method 가 SAFE_METHODS(GET · HEAD · OPTIONS) 인가?
  ├─ 예  ─▶ True  (읽기는 누구나)
  └─ 아니오 ─▶ obj.author.user == request.user  (본인 글만 수정·삭제)
```

1. 읽기 메서드면 바로 허용한다.
2. 쓰기 메서드면 글의 작성자 사용자와 요청 사용자가 같을 때만 허용한다.
3. 객체 수준 검사는 `get_object()` 안에서 불리므로, 객체 하나를 다루는 동작(`retrieve` · `update` · `destroy` · `publish`)에서만 작동한다.

이 두 클래스는 정의만으로는 아무 일도 하지 않는다.
뷰의 `pagination_class` · `permission_classes` 나 전역 설정에 넣어야 적용된다.

## 문법 — 형태와 규칙

```python
from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'price']
        read_only_fields = ['id']

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

router = DefaultRouter()
router.register('books', BookViewSet, basename='book')
```

- `ModelSerializer` 는 안쪽 `class Meta` 에 `model` 과 `fields` 를 적는다.
- 필드 옵션: `read_only=True` · `write_only=True` · `many=True` · `source='점.표기.경로'`.
- `SerializerMethodField()` 로 선언한 필드 `x` 는 `get_x(self, obj)` 가 값을 만든다.
- 필드 하나 검증은 `validate_<필드>(self, value)`, 여러 필드 검증은 `validate(self, data)` 이며, 실패하면 `serializers.ValidationError` 를 던지고 통과하면 값을 돌려준다.
- `ModelViewSet` 에는 최소한 `queryset` 과 `serializer_class` 가 필요하다.
- 훅: `perform_create(self, serializer)` · `get_queryset(self)`.
- 커스텀 동작: `@action(detail=True|False, methods=['post'])` 를 메서드에 단다.
- 라우터: `router.register(접두어, ViewSet, basename=…)` → `include(router.urls)`.
- 전역 설정: `settings.py` 의 `REST_FRAMEWORK = {…}`.

## 어디서 틀리나

### 1. 만든 Pagination · Permission 을 붙이지 않는다

`CustomPagination` 과 `IsAuthorOrReadOnly` 는 정의만 되어 있고 `PostViewSet` 이나 전역 설정 어디에도 들어가 있지 않다.
그래서 목록 응답은 전역 `PageNumberPagination`(한 페이지 20개, `count` · `next` · `previous` · `results`)을 따른다.
권한도 `IsAuthenticatedOrReadOnly` 뿐이라, 로그인만 하면 남의 글을 PUT · PATCH · DELETE 할 수 있다.
본인 글만 고치게 하려면 `permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]` 처럼 직접 넣어야 한다.

### 2. 객체 수준 권한은 목록에서 불리지 않는다

`has_object_permission` 은 `get_object()` 안에서 불린다.
`list` 는 `get_object()` 를 부르지 않으므로, 목록에서 「보면 안 되는 글」을 가리려면 `get_queryset()` 에서 걸러야 한다.
이 예제가 비로그인 사용자에게 공개글만 보이는 일을 권한 클래스가 아닌 `get_queryset()` 에 둔 것도 그래서다.

### 3. PATCH 에서 `validate()` 가 헛걸린다

`validate(self, data)` 의 `data` 에는 이번 요청에 들어온 필드만 있다.
PATCH(부분 수정)로 `status` 만 `'PB'` 로 보내면, 그 글에 이미 카테고리가 있어도 `data.get('category')` 는 `None` 이라 오류가 난다.
부분 수정까지 맞게 하려면 `data` 에 없을 때 `self.instance` 의 값을 보는 식으로 고쳐야 한다.

### 4. 커스텀 액션은 필터 · 검색 · 페이지네이션을 거치지 않는다

`popular` 는 `get_queryset()` 만 부르고 `filter_queryset()` · `paginate_queryset()` 은 부르지 않는다.
그래서 `?search=` · `?ordering=` 이 무시되고, 응답에 페이지 정보가 없다.
필요하면 `self.filter_queryset(self.get_queryset())` 처럼 직접 불러야 한다.

### 5. `perform_create` 는 프로필이 있다고 가정한다

`self.request.user.author_profile` 은 로그인 사용자에게 작성자 프로필이 연결되어 있어야 한다.
프로필이 없는 사용자가 글을 만들면 이 줄에서 예외가 나 서버 오류가 된다 (원본에 근거 없음 — 추론).
권한(`IsAuthenticatedOrReadOnly`)이 비로그인 생성을 먼저 막아 주므로, 비로그인 사용자는 여기까지 오지 않는다.

### 6. `tags` 하나로 읽기 · 쓰기를 다 하려 한다

`tags` 는 `read_only=True` 인 중첩 시리얼라이저라 입력으로 보내도 무시된다.
입력은 `write_only=True, source='tags'` 인 `tag_ids` 로 PK 목록을 보내야 한다.
반대로 `tag_ids` 는 응답에 나오지 않으므로 응답에서 태그를 보려면 `tags` 를 본다.

### 7. ViewSet 이 「다섯 동작」만 준다고 외운다

원본 팁은 「ViewSet 은 list/create/retrieve/update/destroy 를 한 번에 제공한다」고 적었고, 라우터 주석도 `/api/posts/{id}/` 를 (retrieve, update, destroy) 로 적었다.
원본의 주장 → 다섯 동작 → 정답 코드 주석에는 `partial_update` 까지 여섯이 있다.
`update` 가 PUT, `partial_update` 가 PATCH 를 맡으므로 「수정이 둘」이라고 기억하는 편이 정확하다.

### 8. `summary` 는 200자가 아니라 최대 203자다

`get_summary` 는 200자를 넘는 본문을 앞 200자로 자른 뒤 `'...'` 세 글자를 붙인다.
딱 200자인 본문은 `> 200` 조건에 걸리지 않으므로 그대로 나가고 `'...'` 도 붙지 않는다.

### 9. 정답 코드의 모델은 다른 곳에 있다

예제는 `Post` · `Tag` 를 import 하지 않고 쓰며, `Post.publish()` · `author.user` · `category.name` · `user.author_profile` 이 있다고 가정한다.
Django 앱의 `models.py` 에 이 모델과 관계가 있어야 이 코드가 뜻을 가진다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `content[:200]` 은 앞 200자를 자르고, 짧으면 전부 돌려준다 | Python 언어(슬라이스 규칙) |
| `A + B if 조건 else C` 는 `(A + B) if 조건 else C` 로 묶인다 | Python 언어(연산자 우선순위) |
| `ModelSerializer` 가 필드를 자동 매핑하고 `create` · `update` 를 구현한다 | DRF 라이브러리 |
| `ModelViewSet` 이 여섯 동작을 제공하고 라우터가 그 URL 을 만든다 | DRF 라이브러리 |
| `SAFE_METHODS` 는 `GET` · `HEAD` · `OPTIONS` 다 | DRF 라이브러리의 정의 |
| `select_related` 는 JOIN, `prefetch_related` 는 별도 쿼리로 가져온다 | Django ORM (실제 SQL 모양은 데이터베이스 백엔드에 따라 다를 수 있다 — 확인 필요) |
| `DjangoFilterBackend` | DRF 가 아니라 django-filter 패키지 |
| JWT 인증 | DRF 가 아니라 `rest_framework_simplejwt` 패키지 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 모델 하나의 CRUD API 전체 | `ModelViewSet` + `DefaultRouter` | 동작마다 함수 뷰와 URL 을 손으로 쓰기 |
| 모델 필드를 그대로 주고받기 | `ModelSerializer` | 필드를 하나하나 선언하는 일반 `Serializer` |
| 다른 필드에서 계산한 값 | `SerializerMethodField` · `source` | 모델에 응답 전용 필드를 새로 만들기 |
| 작성자 · 소유자 채우기 | `perform_create` 에서 `request.user` 주입 | 클라이언트가 보낸 `author` 믿기 |
| 사용자에 따라 보이는 글 범위 | `get_queryset()` 에서 걸러내기 | 객체 수준 권한만으로 목록 가리기 |
| 본인 글만 수정 · 삭제 | `has_object_permission` 커스텀 권한을 뷰에 붙이기 | `IsAuthenticatedOrReadOnly` 만 두기 |
| CRUD 밖의 동작(게시, 인기 글) | `@action` | 별도 ViewSet 을 또 만들기 |
| 여러 필드를 엮는 규칙 | `validate()` | `validate_<필드>()` (다른 필드를 못 본다) |

## 핵심 문장

1. **Serializer 는 모델 ↔ JSON 번역과 검증을 맡는다** — `read_only` · `write_only` · `source` 로 읽기와 쓰기 모양을 따로 정한다.
2. **ModelViewSet 하나가 CRUD 를, Router 가 그 URL 을 만든다** — CRUD 밖의 동작은 `@action` 의 `detail` 로 `{pk}` 유무를 정한다.
3. **요청마다 바뀌는 일은 훅에 둔다** — 작성자 주입은 `perform_create`, 보이는 범위는 `get_queryset`.
4. **인증은 「누구인가」, 권한은 「해도 되나」다** — 전역 설정은 기본값이고, 뷰의 속성이 있으면 그것이 이긴다.
5. **만든 클래스는 붙여야 작동한다** — 커스텀 Pagination · Permission 도, 커스텀 액션의 필터 · 페이지네이션도 저절로 끼지 않는다.

## 관련 자료

- [django-models](../01-django-models/2-summary.md)
- [django-views](../02-django-views/2-summary.md)
- [flask-api](../07-flask-api/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/web-frameworks.json` 의 `django-rest`

## 용어 풀이

- **DRF (Django REST Framework)** — Django 위에서 REST API 를 만드는 라이브러리.
- **REST** — URL 로 자원을, HTTP 메서드(GET · POST · PUT · PATCH · DELETE)로 동작을 나타내는 API 설계 방식.
- **API** — 프로그램끼리 정해진 주소와 형식으로 데이터를 주고받는 창구.
- **직렬화 / 역직렬화** — 객체 → 전송 형식 / 전송 형식 → 검증된 값 · 객체.
- **Serializer(시리얼라이저)** — 직렬화 · 역직렬화와 검증을 맡는 클래스.
- **ModelSerializer** — 모델 필드를 자동 매핑하고 `create` · `update` 를 구현한 시리얼라이저.
- **중첩 시리얼라이저** — 필드 값으로 다른 시리얼라이저를 써서 관계 객체를 통째로 넣는 것.
- **SerializerMethodField** — `get_<필드>()` 메서드로 값을 만드는 읽기 전용 필드.
- **교차 검증** — 여러 필드 값을 함께 보고 하는 검증.
- **ViewSet / ModelViewSet** — 여러 동작을 모은 뷰 클래스 / 모델 CRUD 여섯 동작을 갖춘 ViewSet.
- **`@action`** — ViewSet 에 커스텀 엔드포인트를 붙이는 데코레이터.
- **Router / DefaultRouter** — ViewSet 의 URL 을 자동으로 만드는 객체 / 거기에 API 루트 뷰를 더한 것.
- **인증 / 권한** — 누구인가를 알아내는 일 / 해도 되는지 판단하는 일.
- **SAFE_METHODS** — 데이터를 바꾸지 않는 메서드 묶음 `GET` · `HEAD` · `OPTIONS`.
- **객체 수준 권한** — 특정 인스턴스 하나에 대한 접근 판단(`has_object_permission`).
- **페이지네이션** — 목록을 페이지로 잘라 돌려주는 일.
- **쓰로틀링** — 시간당 요청 수 제한.
- **N+1 문제** — 목록 조회 뒤 항목마다 관련 데이터를 따로 조회해 쿼리가 늘어나는 문제.
- **`select_related` / `prefetch_related`** — 외래키를 JOIN 으로 / 다대다 · 역참조를 별도 쿼리로 미리 가져오는 쿼리셋 메서드.
- **콘텐츠 협상** — 클라이언트가 원하는 형식에 맞춰 응답 형식을 고르는 일.

## 더 들어가면

- `ModelViewSet` 은 `GenericViewSet` 에 `ListModelMixin` · `CreateModelMixin` 같은 믹스인을 합친 것이다 — 필요한 동작만 골라 조합할 수 있다 (확인 필요).
- 읽기 전용 API 는 `ReadOnlyModelViewSet` 으로 `list` · `retrieve` 만 열 수 있다 (확인 필요).
- 동작마다 다른 시리얼라이저를 쓰려면 `get_serializer_class()` 를 덮어쓴다 (확인 필요).
- `TokenAuthentication` 을 쓰려면 `rest_framework.authtoken` 을 `INSTALLED_APPS` 에 넣고 마이그레이션해 토큰 테이블을 만들어야 한다 (확인 필요).
- 인증에 실패했을 때 401 과 403 중 무엇이 오는지는 첫 번째 인증 클래스가 `WWW-Authenticate` 헤더를 주는지에 따라 갈린다 (확인 필요).
- `CursorPagination` 은 정렬 필드를 기준으로 커서를 넘겨, 데이터가 계속 추가되는 목록에서도 항목이 겹치거나 빠지지 않게 한다 (확인 필요).
- 쓰로틀 횟수는 Django 캐시에 기록되므로, 서버 프로세스가 여럿이면 공유 캐시를 써야 제한이 정확하다 (확인 필요).
