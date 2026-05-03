#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
组织架构数据初始化脚本
创建完整的公司部门、岗位、角色和用户数据
运行后请删除此脚本
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nanoid import generate
from passlib.context import CryptContext
from sqlalchemy import text

from app.database import AsyncSessionLocal
from core.dept.model import Dept
from core.post.model import Post
from core.role.model import Role
from core.menu.model import Menu  # noqa: F401 - Role relationship 需要
from core.permission.model import Permission  # noqa: F401 - Role relationship 需要
from core.user.model import User
from core.user.user_role_model import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gen_id() -> str:
    return generate(size=21)


def hash_pw(password: str) -> str:
    return pwd_context.hash(password)


DEFAULT_PASSWORD = hash_pw("123456")


async def seed():
    async with AsyncSessionLocal() as db:
        # ========== 1. 角色 ==========
        roles = {}
        role_defs = [
            ("admin", "系统管理员", 0, 100, "系统管理员，拥有所有权限"),
            ("manager", "部门经理", 1, 80, "部门经理，管理部门内所有事务"),
            ("team_lead", "团队主管", 1, 60, "团队主管，管理团队日常工作"),
            ("employee", "普通员工", 1, 20, "普通员工，基础操作权限"),
            ("hr", "人事专员", 1, 50, "人事专员，管理人事相关事务"),
            ("finance", "财务专员", 1, 50, "财务专员，管理财务相关事务"),
        ]
        for code, name, role_type, priority, desc in role_defs:
            r = Role(id=gen_id(), name=name, code=code, role_type=role_type,
                     status=True, priority=priority, description=desc)
            roles[code] = r
            db.add(r)

        # ========== 2. 部门（树形结构） ==========
        depts = {}

        # --- 顶层公司 ---
        company_id = gen_id()
        company = Dept(id=company_id, name="智启科技有限公司", code="ZQ",
                       dept_type="company", status=True, level=0,
                       path=f"/{company_id}/",
                       description="智启科技有限公司总部", sort=1)
        depts["company"] = company
        db.add(company)

        # --- 一级部门 ---
        dept_l1_defs = [
            ("tech", "技术研发部", "TECH", "department", "负责产品研发和技术创新", 1),
            ("product", "产品部", "PROD", "department", "负责产品规划和设计", 2),
            ("market", "市场营销部", "MKT", "department", "负责市场推广和品牌建设", 3),
            ("sales", "销售部", "SALES", "department", "负责客户开发和销售业务", 4),
            ("hr_dept", "人力资源部", "HR", "department", "负责招聘、培训和员工关系", 5),
            ("finance_dept", "财务部", "FIN", "department", "负责财务管理和预算控制", 6),
            ("admin_dept", "行政部", "ADMIN", "department", "负责行政事务和后勤保障", 7),
            ("qa", "质量保障部", "QA", "department", "负责产品质量和测试", 8),
        ]
        for key, name, code, dtype, desc, sort in dept_l1_defs:
            did = gen_id()
            d = Dept(id=did, name=name, code=code, dept_type=dtype, status=True,
                     level=1, parent_id=company_id,
                     path=f"/{company_id}/{did}/",
                     description=desc, sort=sort)
            depts[key] = d
            db.add(d)

        # --- 二级部门（技术研发部下） ---
        tech_sub_defs = [
            ("backend", "后端开发组", "TECH-BE", "team", "负责后端服务开发", 1),
            ("frontend", "前端开发组", "TECH-FE", "team", "负责前端界面开发", 2),
            ("mobile", "移动开发组", "TECH-MB", "team", "负责移动端应用开发", 3),
            ("devops", "运维组", "TECH-OPS", "team", "负责系统运维和部署", 4),
            ("ai", "AI研发组", "TECH-AI", "team", "负责人工智能算法研发", 5),
        ]
        tech_id = depts["tech"].id
        for key, name, code, dtype, desc, sort in tech_sub_defs:
            did = gen_id()
            d = Dept(id=did, name=name, code=code, dept_type=dtype, status=True,
                     level=2, parent_id=tech_id,
                     path=f"/{company_id}/{tech_id}/{did}/",
                     description=desc, sort=sort)
            depts[key] = d
            db.add(d)

        # --- 二级部门（销售部下） ---
        sales_sub_defs = [
            ("sales_domestic", "国内销售组", "SALES-CN", "team", "负责国内市场销售", 1),
            ("sales_overseas", "海外销售组", "SALES-OS", "team", "负责海外市场拓展", 2),
        ]
        sales_id = depts["sales"].id
        for key, name, code, dtype, desc, sort in sales_sub_defs:
            did = gen_id()
            d = Dept(id=did, name=name, code=code, dept_type=dtype, status=True,
                     level=2, parent_id=sales_id,
                     path=f"/{company_id}/{sales_id}/{did}/",
                     description=desc, sort=sort)
            depts[key] = d
            db.add(d)

        # --- 二级部门（产品部下） ---
        prod_sub_defs = [
            ("prod_design", "UI/UX设计组", "PROD-UX", "team", "负责产品UI/UX设计", 1),
            ("prod_plan", "产品规划组", "PROD-PL", "team", "负责产品需求分析和规划", 2),
        ]
        prod_id = depts["product"].id
        for key, name, code, dtype, desc, sort in prod_sub_defs:
            did = gen_id()
            d = Dept(id=did, name=name, code=code, dept_type=dtype, status=True,
                     level=2, parent_id=prod_id,
                     path=f"/{company_id}/{prod_id}/{did}/",
                     description=desc, sort=sort)
            depts[key] = d
            db.add(d)

        # ========== 3. 岗位 ==========
        posts = {}
        post_defs = [
            # (key, name, code, post_type, post_level, desc, dept_key)
            ("ceo", "总经理", "CEO", 0, 0, "公司总经理，全面负责公司运营", "company"),
            ("cto", "技术总监", "CTO", 0, 0, "技术总监，负责技术战略和研发管理", "tech"),
            ("cfo", "财务总监", "CFO", 0, 0, "财务总监，负责财务战略和资金管理", "finance_dept"),
            ("cmo", "市场总监", "CMO", 0, 0, "市场总监，负责市场战略和品牌管理", "market"),
            ("hr_director", "人力资源总监", "HRD", 0, 0, "人力资源总监，负责人才战略", "hr_dept"),
            ("sales_director", "销售总监", "SD", 0, 0, "销售总监，负责销售战略", "sales"),
            ("product_director", "产品总监", "PD", 0, 0, "产品总监，负责产品战略", "product"),
            ("tech_manager", "技术经理", "TM", 0, 1, "技术经理，管理开发团队", "tech"),
            ("be_lead", "后端主管", "BE-LEAD", 1, 2, "后端开发组主管", "backend"),
            ("fe_lead", "前端主管", "FE-LEAD", 1, 2, "前端开发组主管", "frontend"),
            ("mb_lead", "移动端主管", "MB-LEAD", 1, 2, "移动开发组主管", "mobile"),
            ("ops_lead", "运维主管", "OPS-LEAD", 1, 2, "运维组主管", "devops"),
            ("ai_lead", "AI主管", "AI-LEAD", 1, 2, "AI研发组主管", "ai"),
            ("be_dev", "后端开发工程师", "BE-DEV", 1, 3, "后端开发工程师", "backend"),
            ("fe_dev", "前端开发工程师", "FE-DEV", 1, 3, "前端开发工程师", "frontend"),
            ("mb_dev", "移动开发工程师", "MB-DEV", 1, 3, "移动开发工程师", "mobile"),
            ("ops_eng", "运维工程师", "OPS-ENG", 1, 3, "运维工程师", "devops"),
            ("ai_eng", "AI工程师", "AI-ENG", 1, 3, "AI算法工程师", "ai"),
            ("pm", "产品经理", "PM", 2, 2, "产品经理，负责产品需求和规划", "prod_plan"),
            ("ui_designer", "UI设计师", "UI", 2, 3, "UI/UX设计师", "prod_design"),
            ("qa_lead", "测试主管", "QA-LEAD", 1, 2, "测试主管", "qa"),
            ("qa_eng", "测试工程师", "QA-ENG", 1, 3, "测试工程师", "qa"),
            ("hr_specialist", "人事专员", "HR-SP", 3, 3, "人事专员，负责招聘和员工关系", "hr_dept"),
            ("hr_manager", "人事经理", "HR-MGR", 3, 1, "人事经理，管理人事团队", "hr_dept"),
            ("fin_specialist", "财务专员", "FIN-SP", 3, 3, "财务专员，负责日常财务工作", "finance_dept"),
            ("fin_manager", "财务经理", "FIN-MGR", 3, 1, "财务经理，管理财务团队", "finance_dept"),
            ("mkt_specialist", "市场专员", "MKT-SP", 2, 3, "市场专员，负责市场推广", "market"),
            ("mkt_manager", "市场经理", "MKT-MGR", 2, 1, "市场经理，管理市场团队", "market"),
            ("sales_rep", "销售代表", "SALES-REP", 2, 3, "销售代表", "sales"),
            ("sales_manager", "销售经理", "SALES-MGR", 2, 1, "销售经理，管理销售团队", "sales"),
            ("admin_specialist", "行政专员", "ADM-SP", 3, 3, "行政专员，负责行政事务", "admin_dept"),
            ("admin_manager", "行政经理", "ADM-MGR", 3, 1, "行政经理，管理行政团队", "admin_dept"),
        ]
        for key, name, code, ptype, plevel, desc, dept_key in post_defs:
            p = Post(id=gen_id(), name=name, code=code, post_type=ptype,
                     post_level=plevel, status=True, description=desc,
                     dept_id=depts[dept_key].id)
            posts[key] = p
            db.add(p)

        # ========== 4. 用户 ==========
        users = {}
        user_role_records = []

        user_defs = [
            # (key, username, name, gender, email, mobile, user_type, dept_key, post_key, role_keys, manager_key)
            # --- 高管 ---
            ("ceo", "zhangwei", "张伟", 1, "zhangwei@zqtech.com", "13800000001", 0, "company", "ceo", ["admin"], None),
            ("cto", "liming", "李明", 1, "liming@zqtech.com", "13800000002", 0, "tech", "cto", ["admin", "manager"], "ceo"),
            ("cfo", "wangfang", "王芳", 2, "wangfang@zqtech.com", "13800000003", 0, "finance_dept", "cfo", ["manager", "finance"], "ceo"),
            ("cmo", "zhaojun", "赵军", 1, "zhaojun@zqtech.com", "13800000004", 0, "market", "cmo", ["manager"], "ceo"),
            ("hrd", "sunli", "孙丽", 2, "sunli@zqtech.com", "13800000005", 0, "hr_dept", "hr_director", ["manager", "hr"], "ceo"),
            ("sd", "zhouyong", "周勇", 1, "zhouyong@zqtech.com", "13800000006", 0, "sales", "sales_director", ["manager"], "ceo"),
            ("pd", "wuying", "吴莹", 2, "wuying@zqtech.com", "13800000007", 0, "product", "product_director", ["manager"], "ceo"),

            # --- 技术研发部 中层 ---
            ("tech_mgr", "chenlong", "陈龙", 1, "chenlong@zqtech.com", "13800000010", 1, "tech", "tech_manager", ["manager", "team_lead"], "cto"),
            ("be_lead", "huanghai", "黄海", 1, "huanghai@zqtech.com", "13800000011", 1, "backend", "be_lead", ["team_lead"], "tech_mgr"),
            ("fe_lead", "linxue", "林雪", 2, "linxue@zqtech.com", "13800000012", 1, "frontend", "fe_lead", ["team_lead"], "tech_mgr"),
            ("mb_lead", "xujie", "徐杰", 1, "xujie@zqtech.com", "13800000013", 1, "mobile", "mb_lead", ["team_lead"], "tech_mgr"),
            ("ops_lead", "magang", "马刚", 1, "magang@zqtech.com", "13800000014", 1, "devops", "ops_lead", ["team_lead"], "tech_mgr"),
            ("ai_lead", "luowen", "罗文", 1, "luowen@zqtech.com", "13800000015", 1, "ai", "ai_lead", ["team_lead"], "tech_mgr"),

            # --- 后端开发组 ---
            ("be1", "yangfei", "杨飞", 1, "yangfei@zqtech.com", "13800000020", 1, "backend", "be_dev", ["employee"], "be_lead"),
            ("be2", "liuyan", "刘燕", 2, "liuyan@zqtech.com", "13800000021", 1, "backend", "be_dev", ["employee"], "be_lead"),
            ("be3", "zhangpeng", "张鹏", 1, "zhangpeng@zqtech.com", "13800000022", 1, "backend", "be_dev", ["employee"], "be_lead"),
            ("be4", "wangxin", "王鑫", 1, "wangxin@zqtech.com", "13800000023", 1, "backend", "be_dev", ["employee"], "be_lead"),

            # --- 前端开发组 ---
            ("fe1", "zhangjing", "张静", 2, "zhangjing@zqtech.com", "13800000025", 1, "frontend", "fe_dev", ["employee"], "fe_lead"),
            ("fe2", "liwei", "李伟", 1, "liwei@zqtech.com", "13800000026", 1, "frontend", "fe_dev", ["employee"], "fe_lead"),
            ("fe3", "chenyue", "陈悦", 2, "chenyue@zqtech.com", "13800000027", 1, "frontend", "fe_dev", ["employee"], "fe_lead"),

            # --- 移动开发组 ---
            ("mb1", "sunhao", "孙浩", 1, "sunhao@zqtech.com", "13800000030", 1, "mobile", "mb_dev", ["employee"], "mb_lead"),
            ("mb2", "zhouli", "周丽", 2, "zhouli@zqtech.com", "13800000031", 1, "mobile", "mb_dev", ["employee"], "mb_lead"),

            # --- 运维组 ---
            ("ops1", "wuqiang", "吴强", 1, "wuqiang@zqtech.com", "13800000035", 1, "devops", "ops_eng", ["employee"], "ops_lead"),
            ("ops2", "zhengkai", "郑凯", 1, "zhengkai@zqtech.com", "13800000036", 1, "devops", "ops_eng", ["employee"], "ops_lead"),

            # --- AI研发组 ---
            ("ai1", "tangmin", "唐敏", 2, "tangmin@zqtech.com", "13800000040", 1, "ai", "ai_eng", ["employee"], "ai_lead"),
            ("ai2", "hanjie", "韩杰", 1, "hanjie@zqtech.com", "13800000041", 1, "ai", "ai_eng", ["employee"], "ai_lead"),
            ("ai3", "fengyu", "冯宇", 1, "fengyu@zqtech.com", "13800000042", 1, "ai", "ai_eng", ["employee"], "ai_lead"),

            # --- 产品部 ---
            ("pm1", "gaoxin", "高欣", 2, "gaoxin@zqtech.com", "13800000050", 1, "prod_plan", "pm", ["employee"], "pd"),
            ("pm2", "songbo", "宋波", 1, "songbo@zqtech.com", "13800000051", 1, "prod_plan", "pm", ["employee"], "pd"),
            ("ui1", "xiaoyu", "肖雨", 2, "xiaoyu@zqtech.com", "13800000052", 1, "prod_design", "ui_designer", ["employee"], "pd"),
            ("ui2", "caojie", "曹洁", 2, "caojie@zqtech.com", "13800000053", 1, "prod_design", "ui_designer", ["employee"], "pd"),

            # --- 质量保障部 ---
            ("qa_lead_u", "panwei", "潘伟", 1, "panwei@zqtech.com", "13800000055", 1, "qa", "qa_lead", ["team_lead"], "cto"),
            ("qa1", "yeling", "叶玲", 2, "yeling@zqtech.com", "13800000056", 1, "qa", "qa_eng", ["employee"], "qa_lead_u"),
            ("qa2", "duanfeng", "段峰", 1, "duanfeng@zqtech.com", "13800000057", 1, "qa", "qa_eng", ["employee"], "qa_lead_u"),

            # --- 市场营销部 ---
            ("mkt_mgr", "jianghua", "蒋华", 1, "jianghua@zqtech.com", "13800000060", 1, "market", "mkt_manager", ["manager"], "cmo"),
            ("mkt1", "helan", "何兰", 2, "helan@zqtech.com", "13800000061", 1, "market", "mkt_specialist", ["employee"], "mkt_mgr"),
            ("mkt2", "luming", "陆明", 1, "luming@zqtech.com", "13800000062", 1, "market", "mkt_specialist", ["employee"], "mkt_mgr"),

            # --- 销售部 ---
            ("sales_mgr", "rengang", "任刚", 1, "rengang@zqtech.com", "13800000065", 1, "sales", "sales_manager", ["manager"], "sd"),
            ("sales1", "fanli", "范丽", 2, "fanli@zqtech.com", "13800000066", 1, "sales_domestic", "sales_rep", ["employee"], "sales_mgr"),
            ("sales2", "shijun", "石军", 1, "shijun@zqtech.com", "13800000067", 1, "sales_domestic", "sales_rep", ["employee"], "sales_mgr"),
            ("sales3", "donghui", "董辉", 1, "donghui@zqtech.com", "13800000068", 1, "sales_overseas", "sales_rep", ["employee"], "sales_mgr"),
            ("sales4", "yuxia", "余霞", 2, "yuxia@zqtech.com", "13800000069", 1, "sales_overseas", "sales_rep", ["employee"], "sales_mgr"),

            # --- 人力资源部 ---
            ("hr_mgr", "pengna", "彭娜", 2, "pengna@zqtech.com", "13800000070", 1, "hr_dept", "hr_manager", ["manager", "hr"], "hrd"),
            ("hr1", "tianjing", "田静", 2, "tianjing@zqtech.com", "13800000071", 1, "hr_dept", "hr_specialist", ["hr", "employee"], "hr_mgr"),
            ("hr2", "guoqiang", "郭强", 1, "guoqiang@zqtech.com", "13800000072", 1, "hr_dept", "hr_specialist", ["hr", "employee"], "hr_mgr"),

            # --- 财务部 ---
            ("fin_mgr", "caiyun", "蔡云", 2, "caiyun@zqtech.com", "13800000075", 1, "finance_dept", "fin_manager", ["manager", "finance"], "cfo"),
            ("fin1", "weihua", "魏华", 1, "weihua@zqtech.com", "13800000076", 1, "finance_dept", "fin_specialist", ["finance", "employee"], "fin_mgr"),
            ("fin2", "xiemei", "谢梅", 2, "xiemei@zqtech.com", "13800000077", 1, "finance_dept", "fin_specialist", ["finance", "employee"], "fin_mgr"),

            # --- 行政部 ---
            ("adm_mgr", "hanxiao", "韩晓", 2, "hanxiao@zqtech.com", "13800000080", 1, "admin_dept", "admin_manager", ["manager"], "ceo"),
            ("adm1", "qinyu", "秦宇", 1, "qinyu@zqtech.com", "13800000081", 1, "admin_dept", "admin_specialist", ["employee"], "adm_mgr"),
            ("adm2", "dengfei", "邓菲", 2, "dengfei@zqtech.com", "13800000082", 1, "admin_dept", "admin_specialist", ["employee"], "adm_mgr"),
        ]

        # 第一遍：创建所有用户（不设 manager_id，因为可能引用尚未创建的用户）
        for key, username, name, gender, email, mobile, utype, dept_key, post_key, role_keys, _ in user_defs:
            u = User(
                id=gen_id(),
                username=username,
                password=DEFAULT_PASSWORD,
                name=name,
                gender=gender,
                email=email,
                mobile=mobile,
                user_type=utype,
                user_status=1,
                is_active=True,
                is_superuser=(key == "ceo"),
                dept_id=depts[dept_key].id,
                post_id=posts[post_key].id,
            )
            users[key] = u
            db.add(u)

            # 用户-角色关联
            for rk in role_keys:
                ur = UserRole(id=gen_id(), user_id=u.id, role_id=roles[rk].id)
                user_role_records.append(ur)
                db.add(ur)

        # 第二遍：设置 manager_id
        for key, _, _, _, _, _, _, _, _, _, manager_key in user_defs:
            if manager_key and manager_key in users:
                users[key].manager_id = users[manager_key].id

        # 设置部门领导
        dept_lead_map = {
            "company": "ceo",
            "tech": "cto",
            "product": "pd",
            "market": "cmo",
            "sales": "sd",
            "hr_dept": "hrd",
            "finance_dept": "cfo",
            "admin_dept": "adm_mgr",
            "qa": "qa_lead_u",
            "backend": "be_lead",
            "frontend": "fe_lead",
            "mobile": "mb_lead",
            "devops": "ops_lead",
            "ai": "ai_lead",
            "sales_domestic": "sales_mgr",
            "sales_overseas": "sales_mgr",
            "prod_design": "pd",
            "prod_plan": "pd",
        }
        for dept_key, user_key in dept_lead_map.items():
            if dept_key in depts and user_key in users:
                depts[dept_key].lead_id = users[user_key].id

        await db.commit()

        # 统计
        print("=" * 50)
        print("组织架构数据初始化完成！")
        print(f"  角色: {len(roles)} 个")
        print(f"  部门: {len(depts)} 个")
        print(f"  岗位: {len(posts)} 个")
        print(f"  用户: {len(users)} 个")
        print(f"  用户角色关联: {len(user_role_records)} 条")
        print(f"  默认密码: 123456")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
