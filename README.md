# MessageBackend (Python)

基于 FastAPI 的后端服务，满足如下要求：
- 使用本地 SQLite 简单数据库保存每次请求的 `token` 和 `message`；
- 将 `gettoken`、`getmessage` 分别实现为独立方法，提供手动调用接口；
- 默认定时任务配置：
  - gettoken：0-7 不执行；8-23 每 10 分钟执行一次；
  - getmessage：0-7 不执行；8-19 每小时执行一次；20-23 每 10 分钟执行一次；
- 消息全部保存在文件夹（`data/messages`）；文字消息也保存在数据库；图片/语音/视频保存路径存数据库；
- 提供查询数据库消息的 API 接口。

## 运行步骤（Windows）

1. 安装依赖：
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate
   pip install -r requirements.txt
   ```

2. 启动服务：
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. 接口说明：
   - 手动获取 token：`POST http://localhost:8000/manual/gettoken`
   - 手动获取消息：`POST http://localhost:8000/manual/getmessage`
   - 列出消息：`GET http://localhost:8000/messages?limit=100&offset=0`

> 数据库存储文件：`data/app.db`；消息文件目录：`data/messages`。