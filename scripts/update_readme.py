#!/usr/bin/env python3
"""核对文中那个独享「已购小火箭」账号的商品页此刻有没有货,把结果写进 README 的 DAILY 区块。
只用标准库。本仓库不抓取、不保存、不展示任何账号或密码,也不列别的共享站。
GitHub Actions 每 6 小时跑一次;有货 / 缺货没变就不改 README(不为刷时间提交)。"""
import re, sys, os, datetime, urllib.request, urllib.parse

README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
TZ = datetime.timezone(datetime.timedelta(hours=8))
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
# 与维护者有关联的独享账号商品页:能直接打开 = 有货;被带回分类页 = 暂时缺货
SHOP = "https://www.taozi277.com/idshop"
SHOP_ITEMS = ["https://www.taozi277.com/item-id-553", "https://www.taozi277.com/item-id-910", "https://www.taozi277.com/item-id-875"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.geturl(), r.read(400000).decode("utf-8", "ignore")


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


def build(in_stock, now):
    stamp = now.strftime("%Y-%m-%d %H:%M")
    head = "不想每次碰运气:[桃子出海 · 苹果ID自助下单](" + SHOP + ") 有独享的「已购小火箭」美区账号(一人一号、带密保、可以自己改密码)"
    if in_stock:
        tail = ",**" + stamp + " 核对时有货**,付款后自动发货。"
        b = badge("独享已购小火箭", "有货", "22c55e")
    else:
        tail = ",**" + stamp + " 核对时暂时缺货**,回货后页面上会重新出现,可以过几小时再看。"
        b = badge("独享已购小火箭", "暂时缺货", "lightgrey")
    return b + "\n\n" + head + tail


def state(block):
    return "有货" if "核对时有货" in block else "缺货" if "暂时缺货" in block else "未知"


def main():
    now = datetime.datetime.now(TZ)
    src = open(README, encoding="utf-8").read()
    m = re.search(r"<!-- DAILY:START -->\n(.*?)\n<!-- DAILY:END -->", src, re.S)
    if not m:
        sys.exit("README 缺 DAILY 标记")
    s = stock()
    if s is None:                                          # 没查成就不动 README,不猜
        print("stock check failed, README unchanged", file=sys.stderr)
        return
    if state(m.group(1)) == ("有货" if s else "缺货"):
        print("stock state unchanged, README not touched")
        return
    open(README, "w", encoding="utf-8").write(src[:m.start(1)] + build(s, now) + src[m.end(1):])
    print("README updated:", "有货" if s else "缺货")


if __name__ == "__main__":
    main()
