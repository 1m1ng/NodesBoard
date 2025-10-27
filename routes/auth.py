from quart import Blueprint, request, g
import time
from utils.config import Config
from models import User
from utils import decrypt_password, generate_token, get_logger, Response, Redis, crypt_password
import redis.asyncio
from decorators import logged

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
    password = data.get('password')
    if not email or not password:
        return Response.error("邮箱和密码不能为空", 400)
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
    
@auth_bp.route('/logout', methods=['GET', 'POST'])
@logged
async def logout():
    try:
        await cache.delete(f"token:{g.user['email']}")
        logger.info(f"用户 {g.user['email']} 已注销")
        return Response.success("注销成功")
    except Exception as e:
        logger.error(f"注销错误: {str(e)}")
        return Response.error("服务器内部错误", 500)

@auth_bp.route('/change_password', methods=['POST'])
@logged
async def change_password():
    data = await request.get_json()
    if not data:
        data = await request.form
        if not data:
            return Response.error("请求数据错误", 400)
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return Response.error("旧密码和新密码不能为空", 400)
    
    if old_password == new_password:
        return Response.error("新密码不能与旧密码相同", 400)
    
    if len(new_password) < 8:
        return Response.error("新密码长度不能少于8个字符", 400)
    
    try:
        user = await User.get_or_none(id=g.user['user_id'])
        if not user:
            return Response.error("用户不存在", 404)
        
        if decrypt_password(user.password) != old_password:
            return Response.error("旧密码错误", 401)
        
        user.password = crypt_password(new_password)
        await user.save()
        
        await cache.delete(f"token:{user.email}")
        logger.info(f"用户 {user.email} 修改了密码")
        return Response.success("密码修改成功，请重新登录。")
    except Exception as e:
        logger.error(f"修改密码错误: {str(e)}")
        return Response.error("服务器内部错误", 500)
