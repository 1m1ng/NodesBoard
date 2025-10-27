from quart import Blueprint, request
import time
from utils.config import Config
from models import User
from utils import decrypt_password, generate_token, get_logger, Response, decode_token, Redis
import redis.asyncio

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

logger = get_logger(__name__)
cache = Redis.get()


@auth_bp.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    if not data:
        data = await request.form
        if not data:
            return Response.error("请求数据错误", 400)
    email = data.get('email')
    if not email:
        return Response.error("邮箱不能为空", 400)
    password = data.get('password')
    if not password:
        return Response.error("密码不能为空", 400)
    ip = request.remote_addr
    if not ip:
        return Response.error("无法获取客户端IP地址", 400)
    
    # 检查IP是否被锁定
    try: 
        lock_time = await cache.get(f"ip_lock:{ip}")
        if lock_time:
            if (time.time() - float(lock_time)) < Config.LOCK_DURATION:
                return Response.error("登录失败次数过多，IP已被锁定。", 403)
            else:
                await cache.delete(f"ip_lock:{ip}")
                await cache.delete(f"ip_attempts:{ip}")

        user = await User.get_or_none(email=email)
        if user and decrypt_password(user.password) == password:
            # 登录成功，清除失败次数
            await cache.delete(f"ip_attempts:{ip}")
            
            payload = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
            token = generate_token(payload)
            await cache.set(f"token:{user.email}", token, ex=Config.TOKEN_EXPIRE_SECONDS)
            
            logger.info(f"用户 {email} 登录成功，IP: {ip}")
            return Response.success("登录成功", {"token": token})
        else:
            # 登录失败，记录失败次数
            failed_attempts = await cache.get(f"ip_attempts:{ip}")
            failed_attempts = int(failed_attempts) + 1 if failed_attempts else 1
            
            if failed_attempts >= Config.MAX_LOGIN_ATTEMPTS:
                await cache.set(f"ip_lock:{ip}", str(time.time()), ex=Config.LOCK_DURATION)
                await cache.delete(f"ip_attempts:{ip}")
                logger.warning(f"IP {ip} 因登录失败次数过多被锁定。")
                return Response.error("登录失败次数过多，IP已被锁定。", 403)

            await cache.set(f"ip_attempts:{ip}", str(failed_attempts), ex=Config.LOCK_DURATION)
            logger.warning(f"用户 {email} 登录失败，IP: {ip}，失败次数: {failed_attempts}")
        return Response.error("邮箱或密码错误", 401)
    except redis.asyncio.RedisError as e:
        logger.error(f"Redis错误: {str(e)}")
        return Response.error("服务器内部错误", 500)
    
@auth_bp.route('/logout')
async def logout():
    try:
        token = request.headers.get('Authorization')
        if not token:
            raise
        if token.startswith("Bearer "):
            token = token[7:]
        else:
            raise
        payload = decode_token(token)
        if not payload:
            raise
        email = payload.get('email')
        if not email or await cache.get(f"token:{email}") != token:
            raise

        await cache.delete(f"token:{email}")
        logger.info(f"用户 {email} 已注销")
        return Response.success("注销成功")
    except redis.asyncio.RedisError as e:
        logger.error(f"Redis错误: {str(e)}")
        return Response.error("服务器内部错误", 500)
    except Exception as e:
        return Response.error("无效或过期的令牌", 401)
