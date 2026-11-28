# python/python-web/02 — Django Views (뷰 처리) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 비공개 글 번호로 상세 주소를 열면 (예측)

```python
# 질문용 발췌 — pk=7 인 글은 있지만 status 가 'PB' 가 아니다
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, status='PB')
    post.view_count += 1
    post.save(update_fields=['view_count'])
    return render(request, 'blog/post_detail.html', {'post': post})
```

- `/posts/7/` 을 열면 사용자는 어떤 응답을 받는가?
- 그 글의 `view_count` 는 바뀌는가?

### 2. 제목을 비우고 작성 폼을 보내면 (예측)

```python
# 질문용 발췌 — 로그인한 사용자가 POST 를 보냈고 form.is_valid() 가 False 다
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            ...
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})
```

- 이 요청은 어느 `return` 에 닿는가?
- 사용자 화면에는 무엇이 보이는가?

### 3. `context_object_name` 을 지운 `ListView` (예측)
- `PostListView` 에서 `context_object_name = 'posts'` 줄을 지우면, 템플릿은 글 목록을 어떤 이름으로 꺼내야 하는가?

### 4. 로그인하지 않고 `PUT` 을 보내면 (예측)

```python
# 질문용 발췌
@login_required
@require_http_methods(['GET', 'POST'])
def post_create(request):
    ...
```

- 로그인하지 않은 사용자가 이 뷰에 `PUT` 요청을 보내면, 두 데코레이터 중 어느 쪽의 거절을 먼저 받는가?

### 5. 저장 성공 뒤 `render` 가 아니라 `redirect` 를 하는 까닭 (왜)
- `post_create` 가 저장에 성공했을 때 상세 페이지를 바로 그리지 않고 리다이렉트하는 까닭은 무엇인가?

### 6. `success_url` 에 `reverse_lazy` 를 쓰는 까닭 (왜)
- `PostDeleteView` 의 `success_url` 을 `reverse_lazy('post-list')` 로 쓰는 까닭은 무엇인가?

### 7. 남의 글 수정 주소를 직접 치면 (경계)
- 로그인한 사용자 A 가 사용자 B 의 글 번호로 `/posts/<번호>/edit/` 를 열면 `PostUpdateView` 는 어디서 이 요청을 막는가?

### 8. `/posts/create/` 와 `/posts/abc/` (경계)
- `posts/<int:pk>/` 패턴이 `posts/create/` 보다 먼저 적혀 있는데도 `/posts/create/` 가 작성 화면으로 가는 까닭은 무엇인가?
- `/posts/abc/` 는 어느 패턴에 걸리는가?

### 9. 인증을 붙이는 두 길 (연결)
- FBV 의 `@login_required` 와 CBV 의 `LoginRequiredMixin` 은 같은 일을 각각 어떤 파이썬 문법으로 하는가?

### 10. 목록 뷰의 `select_related` (연결)
- `post_list` 에서 `select_related('author', 'category')` 를 빼고 템플릿이 글마다 작성자 이름을 찍으면 질의 수는 어떻게 되는가?

## 실습

### 실습 1. 블로그 뷰 한 벌 — FBV · 제네릭 CBV · API · 에러 핸들러 · URLconf

**만들 것** — 블로그 글 목록 · 상세 · 작성을 FBV 로, 같은 기능과 수정 · 삭제를 제네릭 CBV 로 만들고, JSON API · 에러 핸들러 · URL 연결까지 한 파일에 갖춘다.

**준비물** — Django 가 설치된 프로젝트가 필요하다. `Post` 모델(`title` · `content` · `category` · `tags` · `status` · `author` · `view_count` · `created_at`)과 `PostForm`, 사용자의 `author_profile` 관계, 템플릿 파일들은 이 파일에 정의하지 않으며 프로젝트의 다른 파일에 있다고 가정한다.

**요구 조건**

1단계 — FBV
1. `post_list` 는 공개 글(`status='PB'`)만 고르고 작성자 · 분류를 JOIN 으로 미리 가져온다.
2. `post_list` 는 목록을 페이지당 10개로 자르고, 쿼리 문자열 `page`(없으면 1)의 페이지를 안전하게 꺼내 `page_obj` 와 전체 개수 `total_count` 를 템플릿에 넘긴다.
3. `post_detail` 은 `pk` 가 맞고 공개인 글을 꺼내며, 없으면 404 가 된다.
4. `post_detail` 은 조회수를 1 올리고 그 컬럼만 저장한 뒤 상세 템플릿을 그린다.
5. `post_create` 는 로그인한 사용자만, GET · POST 요청만 받는다.
6. `post_create` 는 POST 이고 폼이 유효하면 DB 저장을 미룬 객체에 작성자(`request.user.author_profile`)를 채워 저장하고, 다대다 관계를 저장한 뒤 `post-detail` 로 리다이렉트한다.
7. `post_create` 는 GET 이면 빈 폼을, 검증 실패면 받은 폼을 작성 템플릿으로 그린다.
8. `api_posts` 는 공개 글의 `id` · `title` · `created_at` 을 딕셔너리 리스트로 JSON 응답한다.

2단계 — 제네릭 CBV
9. `HomeView` 는 홈 템플릿을 그리고, 컨텍스트에 최신 공개 글 5개를 `latest_posts` 로 더한다.
10. `PostListView` 는 템플릿에서 목록 이름을 `posts` 로 쓰고 페이지당 10개로 자동 페이지네이션한다.
11. `PostListView` 는 공개 글만 보이고, 쿼리 문자열 `q` 가 있으면 제목에 그 글자가 (대소문자 무시로) 든 글만 남기며, 작성자 · 분류를 JOIN 으로 가져온다.
12. `PostDetailView` 는 템플릿에서 객체 이름을 `post` 로 쓰고 공개 글만 보인다.
13. `PostCreateView` 는 로그인 검사를 가장 먼저 하고, 미로그인이면 `/accounts/login/` 으로 보내며, 지정한 다섯 필드로 폼을 만든다.
14. `PostCreateView` 는 검증 통과 시 작성자를 채워 저장하고, 저장된 글의 상세 주소로 보낸다.
15. `PostUpdateView` 는 로그인 사용자 자신의 글만 수정 대상으로 삼는다.
16. `PostDeleteView` 는 로그인 사용자에게 삭제 확인 템플릿을 보이고, 삭제 후 `post-list` 로 보낸다.

3단계 — View 직접 상속
17. `PostAPIView` 는 GET 이면 공개 글의 `id` · `title` 리스트를 JSON 으로 돌려준다.
18. `PostAPIView` 는 POST 이면 요청 본문을 JSON 으로 풀고 `{'status': 'created'}` 를 상태 코드 201 로 돌려준다.

4단계 — 에러 핸들러
19. 404 · 500 전역 핸들러를 `blog.views.custom_404` · `blog.views.custom_500` 으로 등록한다.
20. `custom_404` 는 예외 인자를 받아 404 템플릿을 상태 404 로, `custom_500` 은 500 템플릿을 상태 500 으로 그린다.

5단계 — URLconf
21. 홈 · 목록 · 상세 · 작성 · 수정 · 삭제 · API 일곱 주소를 각 CBV 에 잇고 `home` · `post-list` · `post-detail` · `post-create` · `post-update` · `post-delete` · `api-posts` 이름을 붙인다. 상세 · 수정 · 삭제는 정수 `pk` 를 받는다.

**시작 코드**

```python
# 연습: Django Views — FBV, CBV, Generic Views
# Post 모델 · PostForm 은 프로젝트의 다른 파일에 있다고 가정한다

# === 1. FBV ===
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator


def post_list(request):
    """게시글 목록 - 기본 FBV"""
    posts = None  # TODO: 공개 글 + 작성자·분류 JOIN
    # TODO: 페이지당 10개로 자르고 ?page= (기본 1) 의 페이지를 꺼낸다
    return render(request, 'blog/post_list.html', {
        # TODO: 'page_obj', 'total_count'
    })


def post_detail(request, pk):
    """게시글 상세 - get_object_or_404 사용"""
    # TODO: pk 가 맞고 공개인 글, 없으면 404
    # TODO: 조회수 1 증가, 그 컬럼만 저장
    return render(request, 'blog/post_detail.html', {'post': post})


# TODO: 로그인 필수 + GET/POST 만 허용
def post_create(request):
    """게시글 작성 - POST 처리"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        # TODO: 유효하면 저장 미루기 → 작성자 채우기 → 저장 → M2M 저장 → 상세로 리다이렉트
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {'form': form})


def api_posts(request):
    """JSON 응답 뷰"""
    # TODO: 공개 글의 id·title·created_at 을 리스트로 JSON 응답
    pass


# === 2. CBV ===
from django.views import View
from django.views.generic import (
    TemplateView, ListView, DetailView,
    CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class HomeView(TemplateView):
    template_name = 'blog/home.html'
    # TODO: get_context_data 로 latest_posts (공개 글 5개) 추가


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    # TODO: 목록 이름 'posts', 페이지당 10개
    # TODO: get_queryset — 공개 글, ?q= 제목 검색, 작성자·분류 JOIN


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    # TODO: 객체 이름 'post', 공개 글만


class PostCreateView(CreateView):  # TODO: 로그인 검사를 가장 먼저
    model = Post
    fields = ['title', 'content', 'category', 'tags', 'status']
    template_name = 'blog/post_form.html'
    # TODO: 미로그인 시 '/accounts/login/'
    # TODO: form_valid — 작성자 주입 후 부모에게 저장을 맡긴다
    # TODO: get_success_url — 저장된 글의 'post-detail'


class PostUpdateView(UpdateView):  # TODO: 로그인 필수
    model = Post
    fields = ['title', 'content', 'category', 'tags', 'status']
    template_name = 'blog/post_form.html'
    # TODO: get_queryset — 자기 글만


class PostDeleteView(DeleteView):  # TODO: 로그인 필수
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    # TODO: 삭제 후 'post-list'


# === 3. 커스텀 CBV ===
class PostAPIView(View):
    # TODO: get — 공개 글 id·title 리스트 JSON
    # TODO: post — 본문 JSON 풀기, {'status': 'created'} 를 201 로
    pass


# === 4. 에러 핸들링 뷰 ===
# TODO: handler404, handler500 등록

# TODO: custom_404(request, exception) — 404 템플릿, 상태 404
# TODO: custom_500(request) — 500 템플릿, 상태 500
# 템플릿 경로: 'errors/404.html', 'errors/500.html'


# === 5. urls.py ===
from django.urls import path

urlpatterns = [
    # TODO: home, post-list, post-detail, post-create, post-update, post-delete, api-posts
]

print("Django Views 핵심 정리")
print("="*50)
print("FBV: 단순, 명시적, 데코레이터로 기능 추가")
print("CBV: 재사용성, 상속, Mixin으로 기능 조합")
print("Generic Views: ListView, DetailView, CreateView 등")
print("LoginRequiredMixin / @login_required: 인증 필수")
print("get_object_or_404: 없으면 자동 404 응답")
print("redirect(): URL이름 또는 경로로 리다이렉트")
```

**확인 방법** — `python manage.py check` 로 설정 오류가 없는지 본 뒤 `python manage.py runserver` 로 띄우고 브라우저에서 `/posts/` · `/posts/?q=단어` · `/posts/<번호>/` · `/posts/create/`(로그아웃 상태와 로그인 상태 둘 다) · `/api/posts/` 를 열어 본다. 남의 글 번호로 `/posts/<번호>/edit/` 를 열었을 때 수정 폼이 나오지 않는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
