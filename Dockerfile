FROM python:3.9-slim

# 安装依赖
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app

# 启动 FastAPI 服务
CMD ["uvicorn", "docgate.core.main:app", "--host", "0.0.0.0", "--port", "8000"]
