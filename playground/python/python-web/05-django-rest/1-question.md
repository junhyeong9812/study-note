# python/python-web/05 — Django REST Framework (DRF) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 본문 길이에 따라 달라지는 `summary` (예측)

```python
# 질문용 발췌
def get_summary(self, obj):
    return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content
```

- `content` 가 250자인 글의 `summary` 는 몇 글자인가?
- `content` 가 딱 200자인 글의 `summary` 끝에는 `...` 가 붙는가?

### 2. 로그인하지 않은 사용자가 보내는 요청 (예측)

```python
# 질문용 발췌
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            qs = qs.filter(status='PB')
        return qs
```

- 비로그인으로 `GET /api/posts/` 를 보내면 응답 목록에는 어떤 글이 들어가는가?
- 그 목록 응답의 한 페이지에는 글이 최대 몇 개 담기는가?
- 비로그인으로 `POST /api/posts/` 를 보내면 요청이 통과하는가?

### 3. 라우터가 `@action` 두 개에 붙이는 주소 (예측)

```python
# 질문용 발췌
@action(detail=True, methods=['post'])
def publish(self, request, pk=None): ...

@action(detail=False, methods=['get'])
def popular(self, request): ...

router.register('posts', PostViewSet, basename='post')
# urls.py: path('api/', include(router.urls))
```

- `publish` 와 `popular` 는 각각 어떤 URL 과 HTTP 메서드로 불리는가?
- `GET /api/posts/5/publish/` 를 보내면 `publish` 가 실행되는가?

### 4. 태그 필드가 `tags` 와 `tag_ids` 둘인 까닭 (왜)

- 같은 모델 필드 `tags` 를 가리키는 시리얼라이저 필드를 왜 읽기용과 쓰기용 둘로 나눴는가?

### 5. 작성자를 `perform_create` 에서 채우는 까닭 (왜)

- 글쓴이를 요청 본문에서 받지 않고 `perform_create` 에서 `request.user` 로 채우는 까닭은 무엇인가?

### 6. `validate()` 가 맡는 범위 (경계)

- 「게시 상태면 카테고리가 필요하다」 규칙을 `validate_status` 가 아니라 `validate` 에 두는 까닭은 무엇인가?
- 이미 카테고리가 있는 글에 PATCH 로 `status` 만 `'PB'` 로 보내면 이 검증을 통과하는가?

### 7. 로그인한 다른 사용자의 수정 요청 (경계)

- 지금의 `PostViewSet` 에서 로그인한 사용자 B 가 사용자 A 의 글에 `PUT` 을 보내면 막히는가?
- `IsAuthorOrReadOnly` 를 뷰에 붙인 뒤에도 `GET /api/posts/` 목록 요청에서 `has_object_permission` 이 불리는가?

### 8. `popular` 액션에서 빠지는 것 (경계)

- `GET /api/posts/popular/?search=django` 에서 `search` 는 결과에 반영되는가?
- `popular` 의 응답에는 `count` · `next` 같은 페이지 정보가 붙는가?

### 9. `queryset` 의 `select_related` · `prefetch_related` 와 직렬화 (연결)

- 글 목록을 직렬화할 때 `select_related('author__user', 'category')` 와 `prefetch_related('tags')` 는 어떤 문제를 막는가?

### 10. 전역 설정과 뷰 속성, 인증과 권한 (연결)

- `settings.py` 의 `DEFAULT_PERMISSION_CLASSES` 와 뷰의 `permission_classes` 가 둘 다 있으면 어느 쪽이 적용되는가?
- 인증과 권한은 요청 처리에서 각각 무엇을 정하는가?

## 실습

### 실습 1. 게시글 API 한 벌 만들기 — Serializer 부터 권한까지

**만들 것** — 게시글(`Post`)과 태그(`Tag`)를 다루는 REST API 를 Serializer · ViewSet · Router · 전역 설정 · 커스텀 페이지네이션 · 커스텀 권한 순서로 한 파일에 만든다.

**준비물** — `djangorestframework` 와 `django-filter` 를 설치한 Django 프로젝트가 필요하다.
`Post` · `Tag` 모델(글의 `author`(→ `user`) · `category`(→ `name`) · `tags` 관계, `status` · `view_count` 필드, `publish()` 메서드)과 사용자의 `author_profile` 관계는 이미 있다고 가정하며, 이 파일은 모델을 만들지 않는다.

**요구 조건**

1단계 — Serializer

1. `TagSerializer` 는 `Tag` 모델의 `id` · `name` 만 주고받는다.
2. `PostSerializer` 의 `tags` 는 태그를 `TagSerializer` 모양의 목록으로 응답에만 넣는다.
3. `tag_ids` 는 입력에서만 태그 PK 목록을 받아 모델의 `tags` 에 연결한다.
4. `author_name` 은 `author.user.get_full_name` 을, `category_name` 은 `category.name` 을 읽기 전용으로 응답에 넣는다.
5. `summary` 는 메서드로 계산한다: 본문이 200자를 넘으면 앞 200자 뒤에 `'...'` 를 붙이고, 아니면 본문 그대로다.
6. `view_count` · `created_at` · `updated_at` 은 응답에만 나오고 입력하면 무시된다.
7. 제목이 5자 미만이면 시작 코드에 적힌 메시지로 거부한다.
8. `status` 가 `'PB'` 인데 `category` 가 없으면 시작 코드에 적힌 메시지로 거부한다.

2단계 — ViewSet

9. `PostViewSet` 은 CRUD 를 모두 제공하고, 작성자(`author__user`) · 카테고리를 함께 조인하고 태그를 미리 가져오는 쿼리셋을 기본 데이터로 쓴다.
10. 읽기는 누구나, 쓰기는 로그인한 사용자만 허용한다.
11. `status` · `category` · `author` 정확 일치 필터, `title` · `content` 검색, `created_at` · `view_count` 정렬을 켜고, 기본 정렬은 최신 글부터다.
12. 글을 만들 때 작성자를 로그인 사용자의 `author_profile` 로 채운다.
13. 로그인하지 않은 요청에는 `status='PB'` 인 글만 보인다.
14. `POST /api/posts/{pk}/publish/` 는 그 글의 `publish()` 를 부르고 `{'status': '게시됨'}` 을 돌려준다.
15. `GET /api/posts/popular/` 는 조회수 상위 10개 글을 직렬화해 돌려준다.

3단계 — Router

16. `DefaultRouter` 에 `posts` 접두어로 `PostViewSet` 을 `basename='post'` 로 등록하고, 라우터 URL 전체를 `api/` 아래에 둔다.

4단계 — 전역 설정

17. `REST_FRAMEWORK` 에 인증(세션 · 토큰, JWT 줄은 주석으로 남김), 기본 권한(읽기 누구나 · 쓰기 로그인), 페이지 번호 방식 페이지네이션(한 페이지 20개), 쓰로틀(비로그인 시간당 100회 · 로그인 시간당 1000회)을 적는다.

5단계 — 커스텀 Pagination

18. `CustomPagination` 은 기본 10개, `?page_size=` 로 조절 가능, 최대 100개이며, 응답을 `count` · `total_pages` · `current_page` · `results` 꼴로 돌려준다.

6단계 — 커스텀 Permission

19. `IsAuthorOrReadOnly` 는 객체 수준에서 읽기 메서드는 허용하고, 그 밖에는 글 작성자의 사용자와 요청 사용자가 같을 때만 허용한다.
20. 파일 끝의 정리 출력 줄은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```python
# Django REST Framework (DRF) - API 구축
# pip install djangorestframework

# === 1. Serializer 정의 ===
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        # TODO: Tag 모델, id · name 필드
        pass


class PostSerializer(serializers.ModelSerializer):
    # TODO: tags — 응답 전용 중첩 태그 목록
    # TODO: tag_ids — 입력 전용 태그 PK 목록 (모델의 tags 에 연결)
    # TODO: author_name — author.user.get_full_name (읽기 전용)
    # TODO: category_name — category.name (읽기 전용)
    # TODO: summary — 메서드로 계산하는 필드

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt',
            'status', 'author', 'author_name',
            'category', 'category_name',
            'tags', 'tag_ids',
            'view_count', 'summary',
            'published_at', 'created_at', 'updated_at'
        ]
        # TODO: view_count · created_at · updated_at 을 읽기 전용으로

    def get_summary(self, obj):
        # TODO: 200자를 넘으면 앞 200자 + '...', 아니면 그대로
        pass

    def validate_title(self, value):
        # TODO: 5자 미만이면 거부 — 메시지: '제목은 5자 이상이어야 합니다.'
        return value

    def validate(self, data):
        # TODO: status 가 'PB' 인데 category 가 없으면 거부 — 메시지: '게시 상태의 글은 카테고리가 필요합니다.'
        return data


# === 2. ViewSet ===
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend


class PostViewSet(viewsets.ModelViewSet):
    """게시글 CRUD API ViewSet"""
    # TODO: queryset (author__user · category 조인, tags 미리 가져오기)
    # TODO: serializer_class
    # TODO: permission_classes

    # TODO: filter_backends · filterset_fields · search_fields · ordering_fields · ordering

    def perform_create(self, serializer):
        # TODO: author 를 로그인 사용자의 author_profile 로 채워 저장
        pass

    def get_queryset(self):
        # TODO: 비로그인이면 status='PB' 만
        pass

    # TODO: 데코레이터 — 객체 하나 대상, POST
    def publish(self, request, pk=None):
        # TODO: 글을 꺼내 publish() 하고 {'status': '게시됨'} 응답
        pass

    # TODO: 데코레이터 — 컬렉션 대상, GET
    def popular(self, request):
        # TODO: 조회수 상위 10개를 직렬화해 응답
        pass


# === 3. Router ===
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# TODO: posts 접두어로 PostViewSet 등록 (basename='post')

# urls.py
from django.urls import path, include
urlpatterns = [
    # TODO: api/ 아래에 router.urls 포함
]


# === 4. 인증 설정 (settings.py) ===
REST_FRAMEWORK = {
    # TODO: DEFAULT_AUTHENTICATION_CLASSES (Session, Token / JWT 는 주석)
    # TODO: DEFAULT_PERMISSION_CLASSES
    # TODO: DEFAULT_PAGINATION_CLASS · PAGE_SIZE
    # TODO: DEFAULT_THROTTLE_CLASSES · DEFAULT_THROTTLE_RATES
}


# === 5. 커스텀 Pagination ===
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    # TODO: page_size · page_size_query_param · max_page_size

    def get_paginated_response(self, data):
        # TODO: count · total_pages · current_page · results 꼴 응답
        pass


# === 6. 커스텀 Permission ===
from rest_framework.permissions import BasePermission

class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # TODO: 읽기 메서드면 허용, 아니면 작성자 본인만
        pass


print("Django REST Framework 핵심 정리")
print("="*50)
print("Serializer: 직렬화/역직렬화 + 유효성 검사")
print("ModelSerializer: 모델 기반 자동 시리얼라이저")
print("ViewSet: CRUD 자동 생성, @action으로 커스텀 엔드포인트")
print("Router: ViewSet URL 자동 매핑")
print("인증: Session, Token, JWT")
print("페이지네이션: PageNumber, LimitOffset, Cursor")
```

**확인 방법** — Serializer · ViewSet · 권한 · 페이지네이션은 앱의 모듈로, `urlpatterns` 는 `urls.py` 로, `REST_FRAMEWORK` 는 `settings.py` 로 나눠 넣는다.
`python manage.py runserver` 로 띄운 뒤 브라우저로 `/api/` 를 열어 API 루트에 `posts` 가 보이는지, `/api/posts/` · `/api/posts/popular/` · `/api/posts/?search=django` 가 응답하는지 본다.
로그인하지 않은 채 목록에 공개글만 나오는지, 4자 제목으로 글을 만들면 오류 메시지가 오는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
