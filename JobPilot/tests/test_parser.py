import unittest
from jobpilot.parser import heuristic_parse

SAMPLE = """
公司名称：星海互动科技有限公司
招聘岗位：游戏音频策划
工作地点：杭州
网申截止时间：2026年9月10日
岗位职责：负责游戏音乐、音效和互动音频方案，参与AIGC内容工具建设。
"""


class ParserTest(unittest.TestCase):
    def test_basic_fields(self):
        item = heuristic_parse(
            url="https://example.com/job/1",
            title="游戏音频策划 - 星海互动招聘",
            text=SAMPLE,
            source_type="text",
        )
        self.assertEqual(item["company"], "星海互动科技有限公司")
        self.assertEqual(item["role"], "游戏音频策划")
        self.assertEqual(item["location"], "杭州")
        self.assertIn("2026", item["deadline"])
        self.assertGreaterEqual(item["match_score"], 50)

    def test_career_home_does_not_treat_official_site_as_role(self):
        item = heuristic_parse(
            url="https://example.com/campus",
            title="科大讯飞招聘 · 官网",
            text="科大讯飞校园招聘 2027届校园招聘 搜索职位 全部职位",
            source_type="browser",
            page_context={"site_name": "科大讯飞招聘", "headings": ["校园招聘"]},
        )
        self.assertEqual(item["company"], "科大讯飞")
        self.assertEqual(item["role"], "招聘主页")
        self.assertEqual(item["page_kind"], "career_home")

    def test_campaign_title_extracts_brand_but_not_fake_role(self):
        item = heuristic_parse(
            url="https://example.com/2027",
            title="顺丰科技人才27届提前批",
            text="顺丰科技2027届校园招聘 提前批 职位列表 工作地点 北京 深圳",
            source_type="browser",
            page_context={},
        )
        self.assertEqual(item["company"], "顺丰科技")
        self.assertEqual(item["role"], "招聘主页")
        self.assertIn(item["page_kind"], {"career_home", "campaign"})

    def test_login_page_uses_site_brand(self):
        item = heuristic_parse(
            url="https://example.com/login",
            title="登录",
            text="登录 手机号 密码 验证码 忘记密码",
            source_type="browser",
            page_context={"site_name": "科大讯飞招聘"},
        )
        self.assertEqual(item["company"], "科大讯飞")
        self.assertEqual(item["role"], "招聘登录页")
        self.assertEqual(item["page_kind"], "login")

    def test_jobposting_context_has_highest_priority(self):
        item = heuristic_parse(
            url="https://example.com/jobs/123",
            title="职位详情 - 某招聘系统",
            text="职位详情 欢迎投递",
            source_type="browser",
            page_context={
                "site_name": "某招聘系统",
                "headings": ["职位详情"],
                "job_posting": {
                    "title": "储备干部",
                    "company": "顺丰科技有限公司",
                    "location": "深圳 广东",
                    "deadline": "2026-09-30",
                },
            },
        )
        self.assertEqual(item["company"], "顺丰科技有限公司")
        self.assertEqual(item["role"], "储备干部")
        self.assertIn("深圳", item["location"])
        self.assertEqual(item["deadline"], "2026-09-30")
        self.assertEqual(item["page_kind"], "job_detail")


if __name__ == '__main__':
    unittest.main()
