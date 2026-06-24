"""
腾讯云 4核4G3M 轻量服务器 38元/年 秒杀脚本 (定时无阻塞轮询版)
活动页面: https://cloud.tencent.com/act/pro/warmup-202606?fromSource=gwzcw.12021631.12021631.12021631&utm_medium=cpc&utm_id=gwzcw.12021631.12021631.12021631&msclkid=c4927764dc3712355f6b1d5fe7cc4564
抢购接口: POST https://act-api.cloud.tencent.com/dianshi/do-goods
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import aiohttp

# ===================== 需要填写的参数 =====================

# 浏览器 Cookie 字符串
COOKIES = "8029747040huifiuiegugfiubjk8********************" # 在开发者工具中搜索
TARGET_TIME = "10:00:00"
# 目标抢购时间, 格式 "HH:MM:SS", 设为 None 则立即抢购
# 上午场: "10:00:00"  下午场: "15:00:00"
REGION_IDS = [1] # 目标地域, 1=广州, 4=上海, 8=北京, 可同时抢购多个地域，列表中添加多个即可

BUSSID = 23768 # 业务 ID, 每天需要更新，在开发者工具中搜索："end_date": "2026-06-24",其中2026-06-24改为当前日期，然后里面有个id字段是23开头的，复制这个字段
ADVANCE_MS = 1500  # 提前多少毫秒发送，1500是成功抢到的参数

# 发送请求的固定时间间隔 (单位：毫秒)
INTERVAL_MS = 100 # 100是成功抢到的参数

ACTIVITY_ID = 163657332947307 # 6月份是这个，后继月份这个数值可能会变，在开发者工具中搜索："end_date": "2026-06-24",其中2026-06-24改为当前日期，然后里面有个activity_id字段
GOODS_ACT_ID = "1843055693251603" # 6月份是这个，后继月份这个数值可能会变，在开发者工具中搜索："end_date": "2026-06-24",其中2026-06-24改为当前日期，然后里面有个act_id字段
FROMURL = "https://cloud.tencent.com/act/pro/warmup-202606?fromSource=gwzcw.15235128.15235128.15235128&utm_medium=cpc&utm_id=gwzcw.15235128.15235128.15235128#MS" # 6月份是这个，后继月份这个数值可能会变
# ===========================================================




_server_offset = 0.0


def compute_csrf(skey: str) -> str:
    if not skey:
        return ""
    n = 5381
    for ch in skey:
        n += (n << 5) + ord(ch)
    return str(2147483647 & n)


def parse_cookies(cookies_str: str) -> dict:
    cookies = {}
    for item in cookies_str.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


async def sync_server_time(session: aiohttp.ClientSession, csrf: str) -> float:
    global _server_offset
    url = "https://act-api.cloud.tencent.com/dianshi/query-seckill-by-date"
    headers = {"X-Csrf-Token": csrf}

    best_offset = float('inf')
    for i in range(5):
        local_before = time.time()
        try:
            async with session.post(url, json={
                "activity_id": ACTIVITY_ID,
                "preview": 0,
                "seckill_type": "block",
                "goods_type": "goods",
                "days": 2,
            }, headers=headers) as resp:
                local_after = time.time()
                server_date = resp.headers.get("Date") or resp.headers.get("date")
                if server_date:
                    server_time = parsedate_to_datetime(server_date).timestamp()
                    local_mid = (local_before + local_after) / 2
                    offset = server_time - local_mid
                    if abs(offset) < abs(best_offset):
                        best_offset = offset
        except Exception:
            pass
        await asyncio.sleep(0.1)

    if best_offset != float('inf'):
        _server_offset = best_offset
        print(f"[*] 服务器时间校准完成: 本地时钟偏移 {_server_offset*1000:+.0f}ms")
    else:
        _server_offset = 0
        print("[!] 时间校准失败, 使用本地时间")
    return _server_offset


def get_server_now() -> datetime:
    return datetime.now() + timedelta(seconds=_server_offset)


async def wait_until(target_time: str):
    now = get_server_now()
    target = datetime.strptime(target_time, "%H:%M:%S").replace(
        year=now.year, month=now.month, day=now.day
    )
    advance = timedelta(milliseconds=ADVANCE_MS)
    target_adjusted = target - advance

    if now >= target_adjusted:
        target = target + timedelta(days=1)
        target_adjusted = target - advance

    print(f"[*] 目标时间: {target.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] 实际触发时间 (含提前量): {target_adjusted.strftime('%H:%M:%S.%f')[:-3]}")

    while True:
        now = get_server_now()
        if now >= target_adjusted:
            break
        remaining = target_adjusted - now
        total_secs = remaining.total_seconds()
        if total_secs <= 10:
            print(f"\r[*] 倒计时: {total_secs:.3f}s  ", end="", flush=True)
            await asyncio.sleep(0.01)
        else:
            print(f"\r[*] 倒计时: {int(total_secs)}s  ", end="", flush=True)
            await asyncio.sleep(0.5)
    print(f"\n[!] 时间到 ({get_server_now().strftime('%H:%M:%S.%f')[:-3]}), 开始持续派发抢购请求...")


def build_payload(region_id: int) -> dict:
    return {
        "activity_id": ACTIVITY_ID,
        "agent_channel": {
            "fromChannel": "", "fromSales": "", "isAgentClient": False,
            "fromUrl": FROMURL
        },
        "business": {"id": BUSSID, "from": "lightningDeals"},
        "goods": [{
            "act_id": GOODS_ACT_ID,
            "type": "bundle_budget_mc_lg4_01",
            "goods_param": {
                "BlueprintId": "LINUX_UNIX", "area": 1, "ddocUnionConnect": 0,
                "goodsNum": 1, "imageId": "lhbp-eqora508", "scenario": "0",
                "timeSpanUnit": "12m", "zone": "", "regionId": region_id,
                "type": "bundle_budget_mc_lg4_01"
            }
        }],
        "preview": 0
    }


async def do_buy(session: aiohttp.ClientSession, region_id: int, csrf: str, req_id: int):
    """后台运行的单次独立请求任务，不阻塞主循环"""
    payload = build_payload(region_id)
    headers = {"X-Csrf-Token": csrf}
    
    try:
        async with session.post(
            "https://act-api.cloud.tencent.com/dianshi/do-goods",
            json=payload, headers=headers, ssl=False,
            timeout=aiohttp.ClientTimeout(total=5) # 加上5秒超时防止挂死
        ) as resp:
            result = await resp.json()
            code = result.get("code")
            msg = result.get("msg", "")[:100]
            ts = get_server_now().strftime("%H:%M:%S.%f")[:-3]
            region_map = {1: "广州", 4: "上海", 8: "北京"}
            name = region_map.get(region_id, str(region_id))

            if code == 0:
                print(f"\n[{ts}] [任务#{req_id}] 🎉 抢购成功! 地域: {name}")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                # 抢购成功后，强制结束整个事件循环
                asyncio.get_running_loop().stop()
            else:
                print(f"[{ts}] [任务#{req_id}] {name} 返回 -> code={code}  {msg}")
    except Exception as e:
        ts = get_server_now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts}] [任务#{req_id}] 异常: {e}")


async def main():
    if not COOKIES:
        print("[!] 请先设置 COOKIES!")
        return

    cookies = parse_cookies(COOKIES)
    skey = cookies.get("skey", "") or cookies.get("p_skey", "")
    csrf = compute_csrf(skey)
    print(f"[*] 计算得到 csrf: {csrf}")

    if not skey:
        print("[!] 未找到 skey, 请更新 Cookie")
        return

    # 因为不限制并发了，将连接池调大，确保底层能同时处理大量未返回的连接
    connector = aiohttp.TCPConnector(limit=500, limit_per_host=500)
    async with aiohttp.ClientSession(cookies=cookies, connector=connector) as session:
        
        await sync_server_time(session, csrf)

        if TARGET_TIME:
            await wait_until(TARGET_TIME)

        print(f"\n{'=' * 50}")
        print(f"[*] 策略: 每 {INTERVAL_MS}ms 派发一次任务 (无需等待上次结束)")
        print(f"{'=' * 50}\n")

        req_count = 0
        interval_seconds = INTERVAL_MS / 1000.0

        # 主循环：只管定时发射任务，绝不等待
        while True:
            loop_start = time.time()
            req_count += 1
            
            for rid in REGION_IDS:
                # 使用 create_task 把它丢到后台执行，完全不占用主流程时间
                asyncio.create_task(do_buy(session, rid, csrf, req_count))

            # 精准控制 50ms 间隔 (减去本轮循环代码极其微弱的执行时间)
            elapsed = time.time() - loop_start
            sleep_time = max(0.0, interval_seconds - elapsed)
            await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # 捕捉成功时强制 stop 循环引发的正常退出
        print("[*] 脚本已安全停止。")
