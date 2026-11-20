#!/usr/bin/env python3
"""每天核对 README 里列的公开「小火箭共享账号」页面还能不能打开,把结果写进 README 的 DAILY 区块。
只用标准库。本仓库不抓取、不保存、不展示任何账号或密码,只记录「页面能不能打开、页面上还有没有小火箭字样」。
GitHub Actions 每 6 小时跑一次;核对结果没变、且当天已经记过一次,就不改 README(不为刷时间提交)。"""
import re, sys, os, datetime, urllib.request, urllib.parse

README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
SINCE = datetime.date(2026, 11, 20)                     # 仓库建立日,用来算「已运行天数」
TZ = datetime.timezone(datetime.timedelta(hours=8))
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
# (名称, 地址, 页面自己的说明——转述自各站页面,建仓当天核对)。按域名字母顺序,不代表推荐顺序。
SITES = [
    ("Shadowrocket 账号共享平台", "https://free.iosapp.icu/", "页面写明提供免费 Apple ID 及已购小火箭账号,每 30 分钟更新一次,下载后请及时退出"),
    ("小火箭 ID 共享", "https://id.tangping.icu/", "美区、香港区、台湾区账号;页面显示每个账号的状态和最近验证时间,密码点开才显示"),
    ("小优 ID 共享站", "https://idfree.top/", "写明是公益项目;页面提示苹果近期风控较严,共享账号可能被封;附找不到或装不了小火箭时的处理办法"),
    ("小火箭共享账号(桔子)", "https://ios.juzixp.com/", "美区共享账号;页面提示免费共享账号随时会失效,失效请过几小时再来"),
    ("Shadowrocket 共享账号", "https://shareid.tools12345.com/", "页面很简单,点开显示当前共享账号"),
]
KEY = re.compile(r"小火箭|shadowrocket", re.I)
# 与维护者有关联的独享账号商品页:能直接打开 = 有货;被带回分类页 = 暂时缺货
SHOP = "https://www.taozi277.com/idshop"
SHOP_ITEMS = ["https://www.taozi277.com/item-id-553", "https://www.taozi277.com/item-id-910", "https://www.taozi277.com/item-id-875"]
LOG_KEEP = 14


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.geturl(), r.read(400000).decode("utf-8", "ignore")


def check(url):
    """返回 (代号, 文字)。代号用来比较前后两次有没有变。"""
    err = ""
    for _ in range(2):                                   # 失败重试一次,免得把偶发超时记成打不开
        try:
            status, _final, body = fetch(url)
            if status == 200 and KEY.search(body):
                return "ok", "✅ 能打开"
            if status == 200:
                return "nokey", "⚠️ 能打开,但页面上没找到小火箭字样"
            err = f"HTTP {status}"
        except Exception as e:
            err = type(e).__name__
    return "down", f"❌ 这次没打开({err})"


def stock():
    """有货 True / 缺货 False / 没查成 None(查不成就不写这句,不猜)。"""
    seen = False
    for u in SHOP_ITEMS:
        try:
            status, final, _ = fetch(u)
            seen = True
            if status == 200 and "/item-id-" in final:
                return True
        except Exception:
            continue
    return False if seen else None


def badge(label, value, color):
    q = lambda s: urllib.parse.quote(s.replace("-", "--").replace("_", "__"), safe="")
    return f"![{label}](https://img.shields.io/badge/{q(label)}-{q(value)}-{color})"


def build(results, in_stock, now, old_log):
    stamp = now.strftime("%Y-%m-%d %H:%M")
    day = now.strftime("%Y-%m-%d")
    ok = sum(1 for code, _ in results if code == "ok")
    days = (now.date() - SINCE).days
    lines = [
        f'{badge("最近核对", stamp, "fbbf24")} {badge("能打开的共享页", f"{ok} / {len(SITES)}", "f59e0b" if ok else "lightgrey")} {badge("已运行", f"{days} 天", "0ea5e9")}',
        "",
        f"> 🚀 **{stamp} 核对:{len(SITES)} 个公开的小火箭共享账号页面里,{ok} 个能打开。**",
        "> 本仓库不保存、不展示任何账号和密码;账号在各站自己的页面上,点进去看。核对的只是「页面能不能打开、页面上还有没有小火箭字样」,**不代表里面的账号这一刻能登录**——共享号多人同时在用,被锁、被改密是常态,登不上就换下一个站。",
        "",
        "| 站点 | 地址 | 这次核对 | 页面自己的说明 |",
        "| --- | --- | --- | --- |",
    ]
    for (name, url, note), (_code, text) in zip(SITES, results):
        lines.append(f"| {name} | {url} | {text} | {note} |")
    lines.append("")
    if in_stock is True:
        lines.append(f"不想每次碰运气:[桃子出海 · 苹果ID自助下单]({SHOP}) 有独享的「已购小火箭」美区账号(一人一号、带密保、可以自己改密码),**这次核对时有货**,付款后自动发货。")
    elif in_stock is False:
        lines.append(f"不想每次碰运气:[桃子出海 · 苹果ID自助下单]({SHOP}) 有独享的「已购小火箭」美区账号(一人一号、带密保、可以自己改密码),**这次核对时暂时缺货**,回货后页面上会重新出现,可以过几小时再看。")
    else:
        lines.append(f"不想每次碰运气:[桃子出海 · 苹果ID自助下单]({SHOP}) 有独享的「已购小火箭」美区账号(一人一号、带密保、可以自己改密码),有没有货以页面显示为准。")
    entry = f"- **{day}**:核对 {len(SITES)} 个共享页,{ok} 个能打开" + ("" if ok == len(SITES) else ";没打开的:" + "、".join(n for (n, _u, _t), (c, _x) in zip(SITES, results) if c != "ok"))
    log = [entry] + [l for l in old_log if not l.startswith(f"- **{day}**")]
    lines += ["", "### 核对记录(近 14 天)", ""] + log[:LOG_KEEP]
    return "\n".join(lines)


def signature(block):
    """只比「每个站的核对结果 + 有没有货 + 记录里有哪些日期」;时间戳每次都变,不算变化。"""
    rows = re.findall(r"^\| [^|]+ \| https?://\S+ \| ([^|]+) \|", block, re.M)
    stock_txt = "有货" if "这次核对时有货" in block else "缺货" if "暂时缺货" in block else "未知"
    days = re.findall(r"^- \*\*(\d{4}-\d\d-\d\d)\*\*", block, re.M)
    return [r.strip() for r in rows], stock_txt, days


def main():
    now = datetime.datetime.now(TZ)
    src = open(README, encoding="utf-8").read()
    m = re.search(r"<!-- DAILY:START -->\n(.*?)\n<!-- DAILY:END -->", src, re.S)
    if not m:
        sys.exit("README 缺 DAILY 标记")
    old_log = re.findall(r"^- \*\*\d{4}-\d\d-\d\d\*\*.*$", m.group(1), re.M)
    results = [check(url) for _name, url, _note in SITES]
    if all(code == "down" for code, _ in results):        # 全部打不开多半是运行环境自己断网,不把它写进 README
        print("all sites unreachable from runner, README unchanged", file=sys.stderr)
        return
    new = build(results, stock(), now, old_log)
    if signature(new) == signature(m.group(1)):
        print("nothing changed today, README not touched")
        return
    open(README, "w", encoding="utf-8").write(src[:m.start(1)] + new + src[m.end(1):])
    print("README updated:", [c for c, _ in results])


if __name__ == "__main__":
    main()
