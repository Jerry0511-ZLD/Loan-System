"""冒烟测试：用 httpx 打真实接口，验证核心链路是否完整。

运行方式
--------
先启动服务（另开一个终端）：
    cd backend
    .venv/Scripts/python.exe -m uvicorn app.main:app --port 8099

再跑本脚本：
    cd backend
    .venv/Scripts/python.exe tests/test_smoke.py

设计说明
--------
这是阶段 I 的「冒烟测试」——不做穷举，只覆盖最容易出问题、且影响演示的核心路径：
    登录 → 提交申请 → 出决策 → 查多源明细 → 人工复核 → 状态更新
它同时是阶段 II「测试」这一项的起点：后面再加参数化用例、异常用例和评分卡效果评估。

不需要 pytest，直接 python 运行，避免为了跑一个冒烟测试还要额外装测试框架。
"""

import sys

import httpx

BASE = "http://127.0.0.1:8099"

PASSED = []
FAILED = []


def check(name, condition, detail=""):
    """记录一条断言结果，不中断后续检查——一次跑完能看清所有问题，而不是遇到第一个就停。"""
    if condition:
        PASSED.append(name)
        print(f"  [PASS] {name}")
    else:
        FAILED.append(f"{name} {detail}")
        print(f"  [FAIL] {name}  {detail}")


def main():
    client = httpx.Client(base_url=BASE, timeout=30)

    # ---------- 0. 服务可用 ----------
    print("\n[0] 健康检查")
    r = client.get("/health")
    check("GET /health 返回 ok", r.status_code == 200 and r.json().get("status") == "ok", r.text[:120])

    # ---------- 1. 鉴权 ----------
    print("\n[1] 登录与鉴权")
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    check("管理员登录成功", r.status_code == 200 and r.json()["data"]["token"], r.text[:150])
    admin_token = r.json()["data"]["token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    r = client.post("/api/login", json={"username": "demo3", "password": "123456"})
    check("普通用户 demo3 登录成功", r.status_code == 200, r.text[:150])
    user_token = r.json()["data"]["token"]
    user_h = {"Authorization": f"Bearer {user_token}"}

    r = client.get("/api/loans")
    check("不带 token 访问受保护接口返回 401", r.status_code == 401, f"实际 {r.status_code}")

    r = client.get("/api/applications", headers=user_h)
    check("普通用户访问管理端返回 403", r.status_code == 403, f"实际 {r.status_code}")

    # ---------- 2. 脱敏 ----------
    print("\n[2] 敏感字段脱敏")
    r = client.get("/api/me", headers=admin_h)
    me = r.json()["data"]
    check("手机号已脱敏", "*" in me["phone"], me["phone"])
    check("身份证已脱敏", "*" in me["idCard"], me["idCard"])

    # ---------- 3. 提交申请 ----------
    print("\n[3] 提交申请并即时出决策")
    r = client.post(
        "/api/loans",
        headers=user_h,
        json={"product": "p002", "amount": 50000, "term": 12, "purpose": "装修"},
    )
    check("提交申请成功", r.status_code == 200, r.text[:200])
    loan = r.json()["data"]
    app_id = loan["id"]
    check("demo3 结论为转人工（MANUAL）", loan["decisionStatus"] == "MANUAL", loan["decisionStatus"])
    check("转人工时 reviewRequired=true", loan["reviewRequired"] is True, str(loan["reviewRequired"]))
    check("申请单状态为 PENDING", loan["status"] == "PENDING", loan["status"])

    # ---------- 4. 多数据源明细 ----------
    print("\n[4] 多数据源明细")
    r = client.get(f"/api/applications/{app_id}/datasources", headers=admin_h)
    check("多源明细接口可用", r.status_code == 200, r.text[:200])
    if r.status_code == 200:
        body = r.json()["data"]
        names = [s["name"] for s in body["sources"]]
        check("返回三个数据源", len(body["sources"]) == 3, str(names))
        check(
            "三个源分别为征信/运营商/公积金",
            set(names) == {"credit_bureau", "carrier", "housing_fund"},
            str(names),
        )
        check("征信源含逾期次数等字段", "overdue_count_6m" in body["sources"][0]["fields"], str(body["sources"][0])[:120])
        check("同时返回聚合后的特征画像", bool(body["featureProfile"]), str(body["featureProfile"])[:120])
        check("返回引擎版本", body["engine"] == "rule_v0", str(body["engine"]))

    # ---------- 5. 待办筛选 ----------
    print("\n[5] 管理端待办筛选与日期筛选")
    r = client.get("/api/applications", headers=admin_h, params={"reviewRequired": "true"})
    check("按 reviewRequired 筛选可用", r.status_code == 200, r.text[:150])
    if r.status_code == 200:
        ids = [x["id"] for x in r.json()["data"]["list"]]
        check("待办列表包含刚提交的申请单", app_id in ids, f"共 {len(ids)} 条")

    r = client.get(
        "/api/applications",
        headers=admin_h,
        params={"startDate": "2020-01-01", "endDate": "2099-12-31"},
    )
    check("日期区间筛选可用", r.status_code == 200 and r.json()["data"]["total"] > 0, r.text[:150])

    r = client.get("/api/applications", headers=admin_h, params={"startDate": "bad-date"})
    check("非法日期返回 400", r.status_code == 400, f"实际 {r.status_code}")

    # ---------- 6. 人工复核 ----------
    print("\n[6] 人工复核闭环")
    r = client.post(
        f"/api/applications/{app_id}/review",
        headers=admin_h,
        json={"action": "approve", "approvedAmount": 48000, "comment": "公积金正常，人工通过"},
    )
    check("复核通过成功", r.status_code == 200, r.text[:200])
    if r.status_code == 200:
        reviewed = r.json()["data"]
        check("复核后状态为 APPROVED", reviewed["status"] == "APPROVED", reviewed["status"])
        check("复核后不再需要人工", reviewed["reviewRequired"] is False, str(reviewed["reviewRequired"]))
        check("批核额度采用人工填写的值", reviewed["approvedAmount"] == 48000, str(reviewed["approvedAmount"]))

    r = client.get(f"/api/applications/{app_id}/decision", headers=admin_h)
    check("决策明细接口可用", r.status_code == 200, r.text[:150])
    if r.status_code == 200:
        d = r.json()["data"]
        check("最新决策来源为 manual", d["source"] == "manual", d["source"])
        check("最新决策结论为 APPROVED", d["status"] == "APPROVED", d["status"])
        check("决策记录保留了复核意见", "人工通过" in d["comment"], d["comment"])

    r = client.post(
        f"/api/applications/{app_id}/review",
        headers=admin_h,
        json={"action": "reject"},
    )
    check("重复复核返回 409", r.status_code == 409, f"实际 {r.status_code}")

    # ---------- 7. 其他两种结论 ----------
    print("\n[7] 通过 / 拒绝场景")
    r = client.post("/api/login", json={"username": "demo", "password": "123456"})
    demo_h = {"Authorization": f"Bearer {r.json()['data']['token']}"}
    r = client.post("/api/loans", headers=demo_h, json={"product": "p002", "amount": 50000, "term": 12})
    check("demo 结论为通过", r.json()["data"]["decisionStatus"] == "APPROVED", r.text[:150])

    r = client.post("/api/login", json={"username": "demo4", "password": "123456"})
    demo4_h = {"Authorization": f"Bearer {r.json()['data']['token']}"}
    r = client.post("/api/loans", headers=demo4_h, json={"product": "p002", "amount": 50000, "term": 12})
    check("demo4 结论为拒绝", r.json()["data"]["decisionStatus"] == "REJECTED", r.text[:150])

    # ---------- 汇总 ----------
    print("\n" + "=" * 60)
    print(f"通过 {len(PASSED)} 项，失败 {len(FAILED)} 项")
    if FAILED:
        print("失败明细：")
        for f in FAILED:
            print("  -", f)
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
