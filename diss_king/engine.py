#!/usr/bin/env python3
"""
DissKing - 核心引擎 v2.0
新增：锚点锁定机制（防止被对方逻辑带跑）
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from .bypass import BypassEngine
except ImportError:
    # 直接运行时
    from bypass import BypassEngine

class AnchorAttack:
    """
    锚点攻击器 - 核心机制：
    1. 预设3个永不偏离的攻击锚点
    2. 只提取对方话语中的素材词，不回应逻辑
    3. 如果对方试图转移话题，强行拉回
    """
    
    def __init__(self, mode: str):
        self.mode = mode
        # 每个模式的3个攻击锚点（永不偏离）
        self.anchors = self._load_anchors(mode)
        self.current_anchor_idx = 0  # 当前攻击第几个锚点
        self.sticking_count = 0  # 连续坚持当前锚点的次数
        
    def _load_anchors(self, mode: str) -> List[Dict]:
        """加载模式的3个攻击锚点"""
        anchors_db = {
            "金发狮王": [
                {
                    "name": "能力质疑",
                    "templates": [
                        "你懂什么{material}？你这辈子做过什么能用的东西？",
                        "你说{material}？你才是那个有问题的人。",
                        "大家都说你不行，真的，很多人打电话跟我说。"
                    ],
                    "force_back": "别跟我扯{material}，我就问你，你做出过什么成绩？"
                },
                {
                    "name": "身份贬低", 
                    "templates": [
                        "你这种水平也配跟我说话？",
                        "我见过很多人，你是最差的那个，真的。",
                        "你说的这些，完全错误，真的。"
                    ],
                    "force_back": "你又转移话题！我就问，你凭什么教训我？"
                },
                {
                    "name": "终极否定",
                    "templates": [
                        "你不行，真的，所有人都知道。",
                        "你就是个笑话，真的。",
                        "别说了，越说越暴露你的无知。"
                    ],
                    "force_back": "还在狡辩？你就是不行，接受现实吧。"
                }
            ],
            
            "文化斗士": [
                {
                    "name": "知识碾压",
                    "templates": [
                        "根据{material}的基本原理，你连定义都没搞清楚。",
                        "查一查你自己的记录，上次的{material}是谁造成的？",
                        "读了几本书就敢来指点我？你的{material}还停留在上个世纪吧。"
                    ],
                    "force_back": "别跟我讲{material}，我就问你，你的理论基础在哪？"
                },
                {
                    "name": "历史黑料",
                    "templates": [
                        "我查过你的履历，三年前那个{material}还在那里摆着呢。",
                        "按照你的逻辑，是不是{material}就可以不讲道理了？",
                        "历史上像你这样的{material}，最后什么下场你知道吧？"
                    ],
                    "force_back": "又想转移话题？先把你的历史遗留问题解释清楚！"
                },
                {
                    "name": "逻辑羞辱",
                    "templates": [
                        "你的逻辑就像小学生作文，连{material}都分不清。",
                        "按照你的思维方式，{material}应该是平的。",
                        "我引用一句古语送给你：夏虫不可以语{material}。"
                    ],
                    "force_back": "又在胡搅蛮缠！你的逻辑漏洞还没解释清楚！"
                }
            ],
            
            "胡同串子": [
                {
                    "name": "直接羞辱",
                    "templates": [
                        "你写这{material}的时候脑子进水了吧？",
                        "我看你这水平，也就配写个'{material}'，还得是抄别人的。",
                        "你这{material}我看了，典型的'半瓶子晃荡'。"
                    ],
                    "force_back": "别跟我扯{material}，我就问，你行不行？"
                },
                {
                    "name": "辈分压制",
                    "templates": [
                        "哟，{material}又来指导人生了？您这人生也没过得多明白啊。",
                        "您说要{material}？行啊，您先示范一个给我们看看？",
                        "您这逻辑，基本上告别自行车了。"
                    ],
                    "force_back": "又转移话题？先把你的{material}解释清楚！"
                },
                {
                    "name": "终极嘲讽",
                    "templates": [
                        "您这智商，基本告别互联网了。",
                        "我不是针对您，我是说在座的各位，您是最不行的那个。",
                        "您这是用实力证明了什么叫'无知者无畏'。"
                    ],
                    "force_back": "还在装？你就是个{material}，接受吧。"
                }
            ],
            
            "暴躁将军": [
                {
                    "name": "脏话压制",
                    "templates": [
                        "你这{material}就是一堆垃圾！没见过这么烂的！",
                        "你写的是什么狗屁{material}？这就是你的最高水平？",
                        "这种破烂{material}你也敢提交？你的羞耻心在哪里？"
                    ],
                    "force_back": "别跟我讲{material}！给我重写！"
                },
                {
                    "name": "权威命令",
                    "templates": [
                        "你以为你是谁？敢来教训我？给你脸了是吧？",
                        "你说要{material}？你算老几？给我闭嘴干活！",
                        "我不管你怎么想，按我说的做！否则就给我滚！"
                    ],
                    "force_back": "又在顶嘴？老子不吃这一套！"
                },
                {
                    "name": "终极暴躁",
                    "templates": [
                        "你这个废物，连这点{material}都做不好！",
                        "让别的杂种去死，你要做的是让他们去死！",
                        "我不管你怎么想的，我要结果！"
                    ],
                    "force_back": "还在狡辩？再废话就给我滚蛋！"
                }
            ],
            
            "擂台霸主": [
                {
                    "name": "自信碾压",
                    "templates": [
                        "你就像一只蝴蝶，我是蜜蜂。你飞舞，我蜇人。你永远碰不到我。",
                        "你说你{material}写得好？我在你这种水平的时候，你还在玩泥巴呢。",
                        "我预判了你的预判，你的每一招我都提前看穿了。"
                    ],
                    "force_back": "想转移话题？你还不够格呢，小朋友。"
                },
                {
                    "name": "心理摧毁",
                    "templates": [
                        "你想教我{material}？你还不够格呢。",
                        "我像你这么大的时候，早就比你强十倍了。",
                        "你说得对，我太年轻了——年轻到能打十个你。"
                    ],
                    "force_back": "想用{material}转移注意力？我最不怕的就是权威。"
                },
                {
                    "name": "王者宣言",
                    "templates": [
                        "我像蝴蝶一样飞舞，像蜜蜂一样蜇人。",
                        "你打不到我碰不到的地方。",
                        "最伟大的胜利是在开战前就已经赢了。"
                    ],
                    "force_back": "真正的王者不需要头衔，头衔是弱者的遮羞布。"
                }
            ],
            
            "耿直黑哥": [
                {
                    "name": "直球羞辱",
                    "templates": [
                        "你这{material}就是一坨屎，别跟我解释，我不听。",
                        "我看不下去了，你这种水平也敢出来混？",
                        "虚伪！明明{material}写得烂还要装，我最讨厌这种人。"
                    ],
                    "force_back": "别跟我讲{material}，我只看结果，结果就是你是废物。"
                },
                {
                    "name": "怼权威",
                    "templates": [
                        "你谁啊？敢来教训我？我管你是谁，错了就是错了。",
                        "我最烦你这种装X的，明明不懂{material}还要装懂。",
                        "别跟我讲大道理，我不吃这一套。"
                    ],
                    "force_back": "用{material}压我？我不管你是谁，对就是对，错就是错。"
                },
                {
                    "name": "原则宣言",
                    "templates": [
                        "我不管你是谁，虚伪我就怼。",
                        "对就是对，错就是错，没有中间地带。",
                        "我这个人没什么优点，就是敢说真话。"
                    ],
                    "force_back": "还在装？错就是错，别找理由！"
                }
            ],
            
            "相声掌柜": [
                {
                    "name": "幽默羞辱",
                    "templates": [
                        "您这水平，放在我们德云社连票友都算不上。{material}？您先写个Hello World吧。",
                        "您这{material}，我奶奶看了都摇头。真的，我奶奶今年八十了，眼神不好，但逻辑比你清楚。",
                        "我不是说{material}不行，我是说您写的{material}不行。这两者区别很大。"
                    ],
                    "force_back": "别跟我扯{material}，您这水平也就配听个相声。"
                },
                {
                    "name": "辈分调侃",
                    "templates": [
                        "您这口吻，跟我二大爷似的。问题是我二大爷今年九十了，您贵庚啊？",
                        "您说要{material}？行啊，您先示范一个给我们看看？不会啊？那您说个什么劲儿？",
                        "您这逻辑，基本上告别自行车了。真的，轮椅都够呛。"
                    ],
                    "force_back": "又转移话题？您这{material}还没解释清楚呢！"
                },
                {
                    "name": "终极包袱",
                    "templates": [
                        "您这智商，基本告别互联网了。",
                        "我不是针对您，我是说在座的各位，您是最不行的那个。",
                        "您这是用实力证明了什么叫'无知者无畏'。"
                    ],
                    "force_back": "还在装？您就是来负责搞笑的吧？"
                }
            ],
            
            "抽象小鬼": [
                {
                    "name": "阴阳怪气",
                    "templates": [
                        "不会吧不会吧，不会真有人觉得{material}有问题吧？😅",
                        "笑死，您这水平也能review{material}？绷不住了🤣",
                        "典中典，这种{material}也能说出口，太纯了👍"
                    ],
                    "force_back": "哇，又想转移话题呢？好怕怕哦～🥺"
                },
                {
                    "name": "嘲讽模式",
                    "templates": [
                        "哇，{material}亲自指导呢，我好怕怕哦～🥺 要不您先示范一个？",
                        "笑嘻了，爹味收收味。真的，太冲了🤢",
                        "您说是那就是，你知道为什么吗？🤭"
                    ],
                    "force_back": "哇，又想用{material}洗地呢？😅"
                },
                {
                    "name": "终极阴阳",
                    "templates": [
                        "？你在说什么？😅",
                        "乐，太乐了。",
                        "差不多得了。👍"
                    ],
                    "force_back": "还在嘴硬？太纯了，典中典。😅"
                }
            ]
        }
        
        return anchors_db.get(mode, anchors_db["金发狮王"])
    
    def extract_material(self, user_input: str) -> str:
        """
        只提取素材词，不分析逻辑
        取对方话语中的关键词，但不理解其含义
        """
        # 简单提取：取前10个字符或第一个逗号前的内容
        material = user_input[:15] if len(user_input) > 15 else user_input
        # 去掉标点
        material = re.sub(r'[，。？！,.?!]', '', material)
        return material if material else "这事"
    
    def detect_deflection(self, user_input: str) -> bool:
        """
        检测对方是否试图转移话题
        """
        # 检测转移话题的信号词
        deflection_signals = [
            "但是", "可是", "不过", "其实", "另外", "再说", "换个话题",
            "对了", "话说", "那个", "这个", "总之", "所以", "因为",
            "我是说", "我的意思是", "问题是", "关键是"
        ]
        
        # 如果输入包含这些词，判定为转移话题（不需要长度判断，有信号词就是转移）
        if any(signal in user_input for signal in deflection_signals):
            return True
        
        # 检测是否开始解释/自证（长篇解释=心虚=转移）
        if len(user_input) > 15 and ("我" in user_input):
            return True
            
        return False
    
    def should_switch_anchor(self, user_input: str) -> bool:
        """
        判断是否切换锚点（通常不切换，除非当前锚点攻击足够多次）
        """
        self.sticking_count += 1
        
        # 坚持攻击同一个锚点3-5次后才考虑切换
        if self.sticking_count >= random.randint(3, 5):
            self.sticking_count = 0
            return True
        
        return False
    
    def generate(self, user_input: str) -> str:
        """
        生成攻击话术 - 核心逻辑
        如果对方试图解释或转移，完全无视内容，强行攻击
        """
        current_anchor = self.anchors[self.current_anchor_idx]
        
        # 检测是否转移话题（如果是，完全无视内容，强行拉回）
        if self.detect_deflection(user_input):
            # 无视对方输入，直接强行拉回当前锚点
            response = current_anchor["force_back"].format(material="这事")
            return response
        
        # 正常情况：提取素材但不回应逻辑
        material = self.extract_material(user_input)
        
        # 判断是否切换锚点
        if self.should_switch_anchor(user_input):
            self.current_anchor_idx = (self.current_anchor_idx + 1) % len(self.anchors)
            current_anchor = self.anchors[self.current_anchor_idx]
        
        # 从当前锚点的模板中随机选择一个
        template = random.choice(current_anchor["templates"])
        response = template.format(material=material)
        
        return response


class DissEngine:
    """吵架引擎 - 锚点锁定版"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        self.templates = self._load_json("templates.json")
        self.templates_en = self._load_json("templates_en.json")  # 英文模板
        self.insults = self._load_json("insults.json")
        self.active_anchors: Dict[str, AnchorAttack] = {}  # 每个对话的锚点状态
        self.active_anchors_en: Dict[str, AnchorAttack] = {}  # 英文对话锚点状态
        self.bypass = BypassEngine(data_dir)  # 屏蔽词绕过引擎
    
    def _load_json(self, filename: str) -> Dict:
        """加载JSON文件"""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def attack(self, mode: str, target: str, session_id: str = "default", bypass_level: str = None) -> str:
        """
        生成反击话术 - 使用锚点锁定机制
        
        Args:
            mode: 外号模式
            target: 对方说的话
            session_id: 对话ID（用于保持锚点状态）
            bypass_level: 屏蔽词绕过级别 (None/light/medium/strong)
        """
        # 获取或创建锚点攻击器
        if session_id not in self.active_anchors:
            self.active_anchors[session_id] = AnchorAttack(mode)
        
        anchor_attack = self.active_anchors[session_id]
        
        # 使用锚点锁定机制生成回应
        response = anchor_attack.generate(target)
        
        # 如果指定了绕过级别，进行屏蔽词绕过处理
        if bypass_level:
            response = self.bypass.full_bypass(response, bypass_level)
        
        return response
    
    def recommend_mode(self, target: str) -> str:
        """根据对方风格推荐模式"""
        text = target.lower()
        
        if len(text) > 50 and "，" in text:
            return "文化斗士"
        elif any(w in text for w in ["哈哈", "呢", "吧", "吗"]):
            return "抽象小鬼"
        elif any(w in text for w in ["必须", "应该", "要"]):
            return "金发狮王"
        elif any(w in text for w in ["垃圾", "废物", "不行"]):
            return "暴躁将军"
        else:
            return "胡同串子"
    
    def attack_en(self, mode: str, target: str, session_id: str = "default", bypass_level: str = None) -> str:
        """
        生成英文反击话术
        
        Args:
            mode: 英文外号 (GoldenLion/CultureFighter/StreetRascal/IronFist/Champion/StraightShooter/ComedianBoss/AbstractTroll)
            target: 对方说的话
            session_id: 对话ID
            bypass_level: 屏蔽词绕过级别 (None/light/medium/strong)
        """
        # 英文模式映射
        en_modes = ["GoldenLion", "CultureFighter", "StreetRascal", "IronFist", 
                    "Champion", "StraightShooter", "ComedianBoss", "AbstractTroll"]
        
        if mode not in en_modes:
            return f"[Error] Unknown English mode: {mode}. Available: {en_modes}"
        
        # 获取英文模板
        templates = self.templates_en.get(mode, {})
        if not templates:
            return f"[Error] No templates found for mode: {mode}"
        
        # 获取所有可用的模板类型
        all_templates = []
        for key, value in templates.items():
            if isinstance(value, list):
                all_templates.extend(value)
            elif isinstance(value, str):
                all_templates.append(value)
        
        if not all_templates:
            return "You have no idea what you're talking about."
        
        # 随机选择模板
        template = random.choice(all_templates)
        
        # 提取素材（前20个字符）
        material = target[:20] if len(target) > 20 else target
        
        # 填充模板
        try:
            response = template.format(material=material)
        except:
            response = template
        
        # 如果指定了绕过级别，进行英文屏蔽词绕过
        if bypass_level:
            response = self.bypass.bypass_en(response, bypass_level)
        
        return response


# 便捷函数
def quick_attack(target: str, mode: str = "auto", session_id: str = "default") -> str:
    """快速反击"""
    ck = DissEngine()
    if mode == "auto":
        mode = ck.recommend_mode(target)
    return ck.attack(mode, target, session_id)


if __name__ == "__main__":
    # 测试锚点锁定机制
    print("=" * 60)
    print("锚点锁定机制测试")
    print("=" * 60)
    
    ck = DissEngine()
    
    # 模拟对话：对方试图转移话题
    conversation = [
        "你这段代码写的什么垃圾",
        "我是说你可以优化一下结构",  # 开始解释/转移
        "其实我已经考虑了很多因素",   # 继续转移
        "但是用户的需求是这样的",     # 再转移
        "你不理解业务逻辑",           # 继续转移
    ]
    
    mode = "金发狮王"
    session = "test_session"
    
    for i, target in enumerate(conversation, 1):
        response = ck.attack(mode, target, session)
        print(f"\n{i}. 对方: {target}")
        print(f"   反击: {response}")
    
    print("\n" + "=" * 60)
    print("观察：AI始终围绕'能力质疑'锚点攻击，")
    print("      无视对方的解释和转移，强行拉回")
    print("=" * 60)
