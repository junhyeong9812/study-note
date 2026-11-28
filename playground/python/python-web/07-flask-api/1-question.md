# python/python-web/07 — Flask RESTful API (marshmallow, JWT) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 회원가입 성공 응답의 `user` 안에 들어가는 키 (예측)

```python
# 질문용 발췌
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True, validate=validate.Length(min=6))

# POST /api/register  {"username": "kim", "email": "kim@ex.com", "password": "secret1"}
return {'message': '회원가입 성공', 'user': user_schema.dump(user)}, 201
```

- 응답 본문의 `user` 에는 어떤 키들이 들어가고, 빠지는 키는 무엇인가?

### 2. 제목만 보내 글을 고치면 (예측)

```python
# 질문용 발췌 — 글 7 의 title='옛 제목', content='본문'
# PUT /api/posts/7  {"title": "새 제목"}   (작성자 본인의 access 토큰)
data = post_schema.load(request.get_json(), partial=True)
post.title = data.get('title', post.title)
post.content = data.get('content', post.content)
db.session.commit()
return {'post': post_schema.dump(post)}
```

- 응답의 `title` · `content` 는 각각 무엇이고, 상태 코드는 몇인가?

### 3. 토큰을 엉뚱한 문에 내밀면 (예측)

```python
# 질문용 발췌
class TokenRefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self): ...

class PostListResource(Resource):
    @jwt_required()
    def post(self): ...
```

- 로그인에서 받은 refresh 토큰으로 `POST /api/posts` 를 보내면 글이 만들어지는가?

### 4. 비밀번호를 해시로만 저장하는 까닭 (왜)

- `User` 가 비밀번호를 그대로 저장하지 않고 `generate_password_hash` 결과만 저장하며, 로그인 때 `check_password_hash` 로 비교하는 까닭은 무엇인가?

### 5. identity 를 `str` 로 넣고 `int` 로 꺼내는 까닭 (왜)

- 로그인에서 `identity=str(user.id)` 로 넣은 값을 글 수정에서 `int(get_jwt_identity())` 로 바꿔 비교하는 까닭은 무엇인가?

### 6. 토큰을 1시간짜리와 30일짜리 둘로 나눈 까닭 (왜)

- access 토큰 하나를 30일짜리로 주지 않고 1시간 access 와 30일 refresh 로 나누면 무엇을 얻는가?

### 7. 다른 사용자의 글을 지우려 할 때의 상태 코드 (경계)

- 유효한 access 토큰을 가진 사용자가 남이 쓴 글에 `DELETE` 를 보내면 401 · 403 · 404 중 무엇이 오고, 왜 그 코드인가?

### 8. 이미 등록된 이메일로 다시 가입하면 (경계)

- 사용자명은 새것이고 이메일만 기존 사용자와 같다면, 이 요청은 어느 단계에서 어떻게 막히는가?

### 9. 이 파일을 다른 모듈이 import 하는 순간 (경계)

- 다른 파이썬 파일이 이 모듈을 import 하면, 서버가 뜨는가, 그리고 끝의 `print` 줄들은 찍히는가?

### 10. `Resource` 메서드 이름과 HTTP 요청의 다리 (연결)

- `GET /api/posts/3` 과 `PUT /api/posts/3` 은 같은 클래스에 닿는데, 어떤 규칙으로 서로 다른 메서드가 불리고 `3` 은 어떻게 메서드에 들어가는가?

## 실습

### 실습 1. 회원 · 토큰 · 게시글 CRUD 를 갖춘 Flask REST API 만들기

**만들 것** — 회원가입 · 로그인 · 토큰 갱신과, 로그인한 사용자만 글을 쓰고 자기 글만 고치고 지울 수 있는 게시글 API 를 한 파일로 만든다.

**준비물** — `pip install flask flask-restful marshmallow flask-jwt-extended flask-sqlalchemy` 로 다섯 패키지를 깐다(werkzeug 는 Flask 와 함께 깔린다). DB 는 개발용 SQLite 파일 `api.db` 다.

**요구 조건**

1단계 — 앱과 설정

1. `Flask` 앱을 만들고 DB URI 를 `sqlite:///api.db` 로, JWT 서명 키를 설정한다.
2. access 토큰 만료를 1시간, refresh 토큰 만료를 30일로 설정한다.
3. `SQLAlchemy` · `Api` · `JWTManager` 를 앱에 붙여 만든다.

2단계 — 모델

4. `User` 는 `id`(기본 키) · `username`(유일 · 필수, 80자) · `email`(유일 · 필수, 120자) · `password_hash`(필수) 열을 가진다.
5. `User.set_password` 는 비밀번호를 해시로 바꿔 저장하고, `check_password` 는 입력 비밀번호가 맞는지 참/거짓을 돌려준다.
6. `Post` 는 `id` · `title`(필수, 200자) · `content`(필수, 긴 글) · `author_id`(`user.id` 외래 키, 필수) · `created_at`(DB 현재 시각 기본값) 열과, `User` 로 이어지는 `author` 관계(역참조 `posts`)를 가진다.

3단계 — 스키마

7. `UserSchema` — `id` 는 응답에만, `password` 는 요청에만 나오게 한다.
8. `UserSchema` — `username` 은 필수 3~80자, `email` 은 필수 이메일 꼴, `password` 는 필수 6자 이상이다.
9. `UserSchema` — 이미 있는 사용자명이면 `'이미 사용 중인 사용자명입니다.'` 로 검증 오류를 낸다.
10. `PostSchema` — `id` · `author_id` · `created_at` 은 응답에만, `title` 은 필수 1~200자, `content` 는 필수다.
11. `PostSchema` — `author_name` 은 메서드로 계산해 작성자의 `username` 을, 작성자가 없으면 `None` 을 낸다.
12. 단건용 `user_schema` · `post_schema` 와 리스트용 `posts_schema` 인스턴스를 만든다.

4단계 — 인증 API

13. 가입: 본문을 `UserSchema` 로 검증하고, 실패하면 `{'errors': …}` 와 400, 성공하면 사용자를 저장하고 `{'message': '회원가입 성공', 'user': …}` 와 201 을 돌려준다.
14. 로그인: 사용자명으로 찾아 없거나 비밀번호가 틀리면 `{'message': '잘못된 인증 정보'}` 와 401, 맞으면 사용자 id 를 문자열 identity 로 한 access · refresh 토큰과 `user` 를 돌려준다.
15. 갱신: refresh 토큰만 받아, 그 identity 로 새 access 토큰을 `{'access_token': …}` 로 돌려준다.

5단계 — 게시글 API

16. 목록(`GET`): 쿼리 문자열 `page`(기본 1) · `per_page`(기본 10) · `q`(기본 빈 문자열)를 읽고, `q` 가 있으면 제목을 대소문자 무시 부분 일치로 거른다.
17. 목록은 최신 글 먼저 정렬해 페이지로 나누고 `posts` · `total` · `pages` · `current_page` 를 돌려준다.
18. 작성(`POST`): access 토큰이 있어야 하며, 검증 실패면 400, 성공하면 토큰의 사용자를 작성자로 넣어 저장하고 `{'post': …}` 와 201 을 돌려준다.
19. 단건 조회(`GET`): 없는 번호면 404, 있으면 `{'post': …}` 를 돌려준다.
20. 수정(`PUT`): access 토큰 필수 · 없는 글 404 · 작성자가 아니면 `{'message': '권한 없음'}` 과 403 · 일부 필드만 보내도 되며 보내지 않은 필드는 원래 값을 유지한다.
21. 삭제(`DELETE`): access 토큰 필수 · 없는 글 404 · 작성자가 아니면 403 · 지우면 `{'message': '삭제 완료'}` 와 200 을 돌려준다.

6단계 — 라우트와 실행

22. `/api/register` · `/api/login` · `/api/refresh` · `/api/posts` · `/api/posts/<int:post_id>` 에 각 Resource 를 등록한다.
23. 직접 실행할 때만 앱 컨텍스트에서 테이블을 만들고 디버그 모드로 개발 서버를 띄운다.

**시작 코드**

```python
# Flask RESTful API - marshmallow + JWT
from flask import Flask, request, jsonify
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# TODO: DB URI · JWT 서명 키 · access(1시간) / refresh(30일) 만료 설정

# TODO: db · api · jwt 확장 초기화


# === 1. 모델 ===
class User(db.Model):
    # TODO: id · username · email · password_hash 열

    def set_password(self, password):
        pass  # TODO: 해시로 저장

    def check_password(self, password):
        pass  # TODO: 해시와 비교


class Post(db.Model):
    # TODO: id · title · content · author_id(외래 키) · created_at · author 관계
    pass


# === 2. 스키마 ===
class UserSchema(Schema):
    # TODO: id(응답 전용) · username · email · password(요청 전용)

    # TODO: username 중복 검사
    pass


class PostSchema(Schema):
    # TODO: id · title · content · author_id · author_name(메서드 필드) · created_at

    def get_author_name(self, obj):
        pass  # TODO


# TODO: user_schema · post_schema · posts_schema


# === 3. 인증 API ===
class RegisterResource(Resource):
    def post(self):
        pass  # TODO: load → 저장 → dump, 201 / 검증 실패 400


class LoginResource(Resource):
    def post(self):
        pass  # TODO: 확인 실패 401 / 성공 시 토큰 두 개


class TokenRefreshResource(Resource):
    # TODO: refresh 토큰만 허용
    def post(self):
        pass  # TODO: 새 access 토큰


# === 4. CRUD API ===
class PostListResource(Resource):
    def get(self):
        pass  # TODO: page · per_page · q → 검색 · 정렬 · 페이지

    # TODO: access 토큰 필수
    def post(self):
        pass  # TODO: 토큰의 사용자를 작성자로 저장, 201


class PostResource(Resource):
    def get(self, post_id):
        pass  # TODO: 없으면 404

    # TODO: access 토큰 필수
    def put(self, post_id):
        pass  # TODO: 404 · 403 · 부분 수정

    # TODO: access 토큰 필수
    def delete(self, post_id):
        pass  # TODO: 404 · 403 · 삭제


# === 5. 라우트 등록 ===
# TODO: 다섯 URL 에 Resource 등록


if __name__ == '__main__':
    # TODO: 앱 컨텍스트에서 테이블 생성 후 디버그 서버 실행
    pass

print("Flask RESTful API 핵심 정리")
print("="*50)
print("Flask-RESTful: Resource 클래스로 REST API 구축")
print("marshmallow: 스키마 기반 직렬화/유효성 검사")
print("Flask-JWT-Extended: JWT 인증 (access + refresh 토큰)")
print("@jwt_required(): 인증 필수 엔드포인트")
print("get_jwt_identity(): 현재 사용자 ID 조회")
print("partial=True: 부분 업데이트 허용 (PUT/PATCH)")
```

**확인 방법** — 파일을 `python 파일이름.py` 로 띄운 뒤 다른 터미널에서 아래 차례로 요청을 보내고, 각 응답의 상태 코드와 본문 키가 요구 조건과 맞는지 본다.

```bash
curl -i -X POST localhost:5000/api/register -H "Content-Type: application/json" \
     -d '{"username":"kim","email":"kim@ex.com","password":"secret1"}'
curl -i -X POST localhost:5000/api/login -H "Content-Type: application/json" \
     -d '{"username":"kim","password":"secret1"}'
# 받은 access 토큰을 ACCESS 에 넣고
curl -i -X POST localhost:5000/api/posts -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ACCESS" -d '{"title":"첫 글","content":"본문"}'
curl -i "localhost:5000/api/posts?q=첫"
curl -i -X PUT localhost:5000/api/posts/1 -H "Content-Type: application/json" \
     -H "Authorization: Bearer $ACCESS" -d '{"title":"고친 제목"}'
```

- 다른 사용자로 가입 · 로그인해 그 토큰으로 1번 글을 `PUT` · `DELETE` 해 403 이 오는지, 없는 번호를 `GET` 해 404 가 오는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
