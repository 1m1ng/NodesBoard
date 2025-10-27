from functools import wraps
from quart import g, request
from utils import Response, decode_token, Redis

cache = Redis.get()


# 装饰器：验证用户是否已登录
def logged(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return Response.error("未提供令牌", 401)
        if token.startswith("Bearer "):
            token = token[7:]
        else:
            return Response.error("令牌格式无效", 401)
        
        payload = decode_token(token)
        if not payload:
            return Response.error("无效或过期的令牌", 401)
        
        email = payload.get('email')
        if not email or await cache.get(f"token:{email}") != token:
            return Response.error("无效或过期的令牌", 401)
        
        g.user = payload  # 将用户数据存储到全局上下文中
        return await func(*args, **kwargs)
    return wrapper

# 装饰器：验证用户是否为管理员
def admin(func):
    @logged
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not hasattr(g, 'user'):
            return Response.error("用户未登录", 403)
        
        if not g.user.get('is_admin'):
            return Response.error("权限不足，仅管理员可访问", 403)
        
        return await func(*args, **kwargs)
    return wrapper
