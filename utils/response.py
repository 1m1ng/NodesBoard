class Response:
    @staticmethod
    def success(message: str = "Success", data: dict = {}) -> tuple:
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return response, 200

    @staticmethod
    def error(message: str = "未知错误", status_code: int = 400) -> tuple:
        response = {
            "success": False,
            "message": message,
            "data": {}
        }
        return response, status_code
