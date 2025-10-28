from quart import Blueprint, request
from utils import get_logger, Response, crypt_password, Redis
from decorators import admin
from models import User

users_bp = Blueprint('users', __name__, url_prefix='/admin/users')

logger = get_logger(__name__)
cache = Redis.get()

@users_bp.route('/list', methods=['GET'])
@admin
async def list_users():
    try:
        users = await User.all().values('id', 'username', 'email', 'is_admin')
        return Response.success("用户列表获取成功", {"users": users})
    except Exception as e:
        logger.error(f"获取用户列表错误: {str(e)}")
        return Response.error("服务器内部错误", 500)


@users_bp.route('/add', methods=['POST'])
@admin
async def add_user():
    try:
        data = await request.get_json()
        if not data:
            data = await request.form
            if not data:
                return Response.error("请求数据错误", 400)
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        if not username or not email or not password:
            return Response.error("用户名、邮箱和密码不能为空", 400)

        if len(password) < 8:
            return Response.error("密码长度不能少于8个字符", 400)
        
        is_active = data.get('is_active', True)
        is_admin = data.get('is_admin', False)

        if '@' not in email:
            return Response.error("无效的邮箱格式", 400)
        
        existing_user = await User.get_or_none(email=email)
        if existing_user:
            return Response.error("用户已存在", 400)
        
        new_user = User(
            username=username,
            email=email,
            password=crypt_password(password),
            is_admin=is_admin,
            is_active=is_active
        )
        await new_user.save()
        return Response.success("用户添加成功")
    except Exception as e:
        logger.error(f"添加用户错误: {str(e)}")
        return Response.error("服务器内部错误", 500)


@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@admin
async def delete_user(user_id: int):
    try:
        user = await User.get_or_none(id=user_id)
        if not user:
            return Response.error("用户不存在", 404)

        await user.delete()
        await cache.delete(f"token:{user.email}")
        return Response.success("用户删除成功")
    except Exception as e:
        logger.error(f"删除用户错误: {str(e)}")
        return Response.error("服务器内部错误", 500)


@users_bp.route('/edit/<int:user_id>', methods=['POST'])
@admin
async def edit_user(user_id: int):
    try:
        data = await request.get_json()
        if not data:
            data = await request.form
            if not data:
                return Response.error("请求数据错误", 400)
        
        user = await User.get_or_none(id=user_id)
        if not user:
            return Response.error("用户不存在", 404)

        username = data.get('username')
        email = data.get('email')
        is_admin = data.get('is_admin')
        password = data.get('password')
        is_active = data.get('is_active')

        if username:
            user.username = username
        if email:
            user.email = email
        if password:
            user.password = crypt_password(password)
        if is_admin is not None:
            user.is_admin = is_admin
        if is_active is not None:
            user.is_active = is_active

        await user.save()
        await cache.delete(f"token:{user.email}")
        return Response.success("用户信息更新成功")
    except Exception as e:
        logger.error(f"编辑用户错误: {str(e)}")
        return Response.error("服务器内部错误", 500)