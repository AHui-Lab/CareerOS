import unittest
from unittest.mock import AsyncMock, patch

from jobpilot.careervault import normalize_experience
from jobpilot.resume import generate_tailored_resume, local_generate_resume


class ProjectBriefTests(unittest.IsolatedAsyncioTestCase):
    def source(self):
        return normalize_experience({
            'id': 'sample', 'type': 'project', 'title': '工具',
            'summary': '旧版独立设计全部架构', 'facts': '旧版效率提升90%',
            'details': {'project_pitch': '求职管理工具。',
                        'personal_contribution': '我提出日程联动需求。',
                        'project_outcome': '完成一次正常检查，异常场景尚未验证。',
                        'hr_intro': '口述练习不进简历。'}})

    def test_brief_supersedes_archive_and_preserves_scope(self):
        exp = self.source()
        self.assertNotIn('90%', exp['description'])
        self.assertNotIn('口述', str(exp))
        data = local_generate_resume({}, [exp], {})
        bullets = data['sections'][0]['items'][0]['bullets']
        self.assertEqual(len(bullets), 3)
        self.assertIn('异常场景尚未验证', bullets[-1])
        self.assertIn(bullets[-1], data['autofill']['project_experience'])

    def test_partial_brief_does_not_restore_old_claims(self):
        exp = normalize_experience({'id':'partial', 'type':'project', 'facts':'旧夸张结论',
                                    'details':{'personal_contribution':'参与试玩'}})
        self.assertEqual(exp['description'], '参与试玩')

    def test_legacy_text_is_not_cut_mid_sentence(self):
        text = '我参与测试，' * 40 + '但尚未验证异常情况。'
        data = local_generate_resume({}, [{'id':'old', 'category':'project', 'highlights':[text]}], {})
        self.assertEqual(data['sections'][0]['items'][0]['bullets'], [text])
        self.assertEqual(len(data['review_notes']), 1)

    async def test_ai_and_autofill_share_three_bullet_limit(self):
        fake = {'sections':[{'title':'项目经历', 'items':[{'source_id':'sample', 'bullets':['用途','动作','有限结果','额外功能']}]}],
                'autofill':{'project_experience':'旧的长版介绍'}, 'selected_experience_ids':['sample']}
        with patch('jobpilot.resume.ai_enabled', return_value=True), patch('jobpilot.resume._chat_json', new=AsyncMock(return_value=fake)):
            data = await generate_tailored_resume({}, [self.source()], {})
        self.assertEqual(data['mode'], 'ai')
        self.assertEqual(data['sections'][0]['items'][0]['bullets'], ['用途','动作','有限结果'])
        self.assertNotIn('旧的长版', data['autofill']['project_experience'])


if __name__ == '__main__':
    unittest.main()
