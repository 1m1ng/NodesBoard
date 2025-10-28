from quart import Quart
from quart_cors import cors
import socketio
import asyncio
from routes import auth_bp, users_bp
from tortoise.contrib.quart import register_tortoise
import os
from models import User
import random
import string
from utils import crypt_password, get_logger, Config

logger = get_logger(__name__)


def create_app() -> socketio.ASGIApp:
    # 创建 Quart 应用
    app = Quart(__name__)
    app = cors(app, allow_origin="*")

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)

    if not os.path.exists('data'):
        os.makedirs('data')
    # 配置数据库
    register_tortoise(
        app,
        db_url=Config.DATABASE_URL,
        modules={'models': ['models']},
        generate_schemas=True
    )
    app.before_serving(init_db)
    
    # 配置 Socket.IO
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins="*"
    )
    sio_app = socketio.ASGIApp(sio, app)
    return sio_app

async def init_db():
    if await User.all().count() == 0:
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=crypt_password(password),
            is_admin=True
        )
        await admin_user.save()
        
        logger.info('='*50)
        logger.info("email: admin@example.com")
        logger.info(f"password: {password}")
        logger.info('='*50)

if __name__ == "__main__":
    import uvicorn
    server = uvicorn.Server(
        config=uvicorn.Config(
            app=create_app(),
            host="0.0.0.0",
            port=5000,
            log_level=Config.LOG_LEVEL.lower(),
            workers=Config.WORKERS
        )
    )
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        exit(0)
