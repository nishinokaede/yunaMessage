from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .db import get_db
from .tasks.gettoken import run_gettoken
from .tasks.getmessage import run_getmessage
from fastapi.staticfiles import StaticFiles
from .config import MESSAGE_DIR, FILE_BASE_URL


app = FastAPI(title="MessageBackend (Python)")


class MessageOut(BaseModel):
    msg_id: str
    msg_type: str
    text_content: Optional[str] = None
    grp: Optional[str] = None
    member_id: Optional[str] = None
    member_name: Optional[str] = None
    url: Optional[str] = None        # 媒体文件返回可访问的URL
    created_at: str
    published_at: Optional[str] = None


scheduler: AsyncIOScheduler | None = None


@app.on_event("startup")
async def on_startup():
    # 初始化数据库
    get_db().init_db()

    # 启动定时器
    global scheduler
    scheduler = AsyncIOScheduler()

    # gettoken: 8-23 每10分钟
    scheduler.add_job(
        func=run_gettoken,
        trigger=CronTrigger(minute="*/10", hour="8-23"),
        id="job_gettoken",
        replace_existing=True,
    )

    # getmessage: 8-19 每小时（整点）
    scheduler.add_job(
        func=run_getmessage,
        trigger=CronTrigger(minute="0", hour="8-19"),
        id="job_getmessage_hourly",
        replace_existing=True,
    )

    # getmessage: 20-23 每10分钟
    scheduler.add_job(
        func=run_getmessage,
        trigger=CronTrigger(minute="*/10", hour="20-23"),
        id="job_getmessage_evening",
        replace_existing=True,
    )

    scheduler.start()

    # 挂载静态文件目录以提供本地文件服务（/data/messages/...）
    app.mount("/data/messages", StaticFiles(directory=str(MESSAGE_DIR)), name="data-messages")


@app.on_event("shutdown")
async def on_shutdown():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)

def _trigger_job(job_id: str):
    global scheduler
    if not scheduler:
        raise HTTPException(status_code=503, detail="scheduler not running")
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    job.modify(next_run_time=datetime.now())


@app.post("/manual/getToken")
async def manual_gettoken():
    _trigger_job("job_gettoken")
    return JSONResponse({"ok": True, "status": "in_progress"})


@app.post("/manual/getMessage")
async def manual_getmessage():
    # 仅触发一个获取消息的任务以避免重复并发运行
    _trigger_job("job_getmessage_hourly")
    return JSONResponse({"ok": True, "status": "in_progress"})


@app.get("/messages", response_model=List[MessageOut])
async def list_messages(limit: int = 100, offset: int = 0, msg_id: str | None = None, date: str | None = None):
    """
    - 当传入 date=YYYYMMDD 时，仅返回该日期的记录，按 msg_id 升序排序。
    - 文本消息忽略 file_path；媒体消息返回基于文件服务器的 URL。
    """
    db = get_db()
    rows = db.list_messages(limit=limit, offset=offset, msg_id=msg_id)

    # 可选按日期过滤（优先使用 published_at 前缀，回退到文件名中的发布时间）
    if date is not None:
        if len(date) != 8 or not date.isdigit():
            raise HTTPException(status_code=400, detail="date 参数需要为YYYYMMDD八位数字")
        def _match_date(r):
            pub = (r.get("published_at") or "")
            if pub.startswith(date):
                return True
            fp = r.get("file_path") or ""
            # 期望文件名形如：{msg_id}_{typeIndex}_{YYYYMMDDHHmmss}.ext
            try:
                import os
                name = os.path.basename(fp)
                stem = os.path.splitext(name)[0]
                parts = stem.split("_")
                if len(parts) >= 3:
                    ts = parts[2]
                    return ts.startswith(date)
            except Exception:
                return False
            return False
        rows = [r for r in rows if _match_date(r)]

    # 构造返回：仅返回所需字段；文本消息不返回URL；媒体消息返回URL
    result: List[dict] = []
    for r in rows:
        mt = r.get("message_type")
        fp = r.get("file_path")
        url = None
        if mt in ("image", "audio", "video") and fp:
            import os
            member_name = r.get("member_name") or ""
            filename = os.path.basename(fp)
            url = f"{FILE_BASE_URL}/data/messages/{member_name}/{filename}"
        result.append({
            "msg_id": r.get("msg_id") or "",
            "msg_type": mt,
            "text_content": r.get("text_content"),
            "grp": r.get("grp"),
            "member_id": r.get("member_id"),
            "member_name": r.get("member_name"),
            "url": url,
            "created_at": r.get("created_at"),
            "published_at": r.get("published_at"),
        })

    # 始终按 msg_id 升序（优先数字，其次字符串）
    def _msg_id_key(x):
        s = str(x.get("msg_id") or "")
        return (0, int(s)) if s.isdigit() else (1, s)
    result.sort(key=_msg_id_key)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)