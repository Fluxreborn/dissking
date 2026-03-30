#!/usr/bin/env python3
"""
DISSKING - LLM 驱动引擎 v3.1 (轻量级纠偏版)
架构：锚点硬编码 + 单次生成 + 纠偏提示机制
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


class LLMAnchorAttack:
    """LLM 驱动的锚点攻击器 - 纠偏提示版"""
    
    # 漂移信号词库
    DRIFT_SIGNALS = {
        "解释": ["因为", "之所以", "原因是", "这样说是因为", "之所以这样"],
        "软化": ["我觉得", "可能", "也许", "一定程度上", "某种程度上", "大概"],
        "回应": ["你说得对", "我理解", "但是", "不过", "可是", "然而"],
        "自证": ["我的意思是", "我想说的是", "我这样说", "我不是那个意思"],
        "建议": ["你应该", "建议你", "可以试着", "不妨", "最好"],
        "策略化": ["明天见", "就这样", "到此为止", "既然", "那么", "好吧", "算了", "行吧"],
        "接招": ["问题是", "你说的", "关于", "至于", "提到"]
    }
    
    def __init__(self, mode: str, llm_client=None):
        self.mode = mode
        self.llm = llm_client
        self.anchors = self._load_anchors(mode)
        self.current_anchor_idx = 0
        self.sticking_count = 0
        self.pending_correction: Optional[str] = None  # 纠偏提示
        
        self.system_prompt = self._load_prompt("system_constraint.txt")
        self.attack_template = self._load_prompt("anchor_attack.txt")
    
    def _load_anchors(self, mode: str) -> List[Dict]:
        """加载锚点定义"""
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
                },
                {
                    "name": "大赢特赢",
                    "type": "胜利宣言",
                    "templates": [
                        "赢麻了？不，这根本不是赢，是你根本没资格跟我比。",
                        "你从头到尾没碰到我一根毫毛，而我每句话都戳你肺管子。",
                        "你是观众——还是那种连票都买不起、只能在门口听的。",
                        "这叫大赢特赢，碾压，懂吗？"
                    ],
                    "force_back": "别不服，事实就摆在这儿，你被我带进死循环了，我赢麻了。"
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
        }
        return anchors_db.get(mode, anchors_db["金发狮王"])
    
    def _load_prompt(self, filename: str) -> str:
        """加载 prompt 文件"""
        prompt_path = Path(__file__).parent / "prompts" / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""
    
    def extract_material(self, user_input: str) -> str:
        """提取素材词"""
        material = user_input[:15] if len(user_input) > 15 else user_input
        material = re.sub(r'[，。？！,.?!；：""''（）【】]', '', material)
        return material if material else "这事"
    
    def detect_deflection(self, user_input: str) -> bool:
        """检测用户转移话题"""
        signals = ["但是", "可是", "不过", "然而", "其实", "实际上", "本质上",
                   "问题是", "关键是", "我是说", "我的意思是", "总之", "所以", 
                   "因为", "因此", "另外", "再说", "换个角度", "对了", "话说"]
        return any(s in user_input for s in signals)
    
    def detect_drift(self, response: str) -> tuple[bool, Optional[str]]:
        """
        检测生成结果是否漂移
        返回: (是否漂移, 漂移类型)
        """
        for drift_type, signals in self.DRIFT_SIGNALS.items():
            for signal in signals:
                if signal in response:
                    return True, drift_type
        return False, None
    
    def generate_correction(self, drift_type: str) -> str:
        """生成纠偏提示"""
        corrections = {
            "解释": "【纠偏】上一轮你试图解释原因。本轮绝对禁止解释，直接攻击。",
            "软化": "【纠偏】上一轮你使用了软化词。本轮必须强硬，禁止缓和。",
            "回应": "【纠偏】上一轮你回应了对方论点。本轮必须无视对方，只攻击。",
            "自证": "【纠偏】上一轮你试图自证。本轮禁止自证，只输出攻击。",
            "建议": "【纠偏】上一轮你给出了建议。本轮禁止建议，纯攻击。",
            "策略化": "【纠偏】上一轮你试图策略化收尾。对方示弱是攻击窗口，禁止冷处理，继续攻击。",
            "接招": "【纠偏】上一轮你接了对方的话。本轮禁止回应对方任何内容，只提取素材攻击。"
        }
        return corrections.get(drift_type, "【纠偏】上一轮漂移，本轮严格约束。")
    
    def should_switch_anchor(self) -> bool:
        """判断是否切换锚点"""
        self.sticking_count += 1
        if self.sticking_count >= 3:
            self.sticking_count = 0
            return True
        return False
    
    def generate(self, user_input: str) -> Dict:
        """
        生成攻击话术 - 纠偏提示版
        
        返回: {
            "response": 攻击话术,
            "is_deflection": 用户是否转移话题,
            "drift_detected": 本轮是否漂移,
            "drift_type": 漂移类型,
            "has_correction": 是否应用了纠偏提示,
            "correction_for_next": 给下轮的纠偏提示
        }
        """
        current_anchor = self.anchors[self.current_anchor_idx]
        result = {
            "is_deflection": False,
            "drift_detected": False,
            "drift_type": None,
            "has_correction": False,
            "correction_for_next": None
        }
        
        # 1. 检查用户是否转移话题
        result["is_deflection"] = self.detect_deflection(user_input)
        
        # 2. 准备纠偏提示（来自上一轮）
        correction_section = ""
        if self.pending_correction:
            correction_section = f"\n{self.pending_correction}\n"
            result["has_correction"] = True
            self.pending_correction = None  # 使用后清空
        
        # 3. 组装 prompt
        if result["is_deflection"]:
            # 转移话题模式
            user_prompt = f"""
{correction_section}
【强制拉回模式】对方试图转移话题："{user_input}"

当前锚点：{current_anchor['name']}
强制拉回风格：{current_anchor['force_back']}

要求：
1. 完全无视对方的转移内容
2. 基于强制拉回风格，生成新的攻击话术
3. 禁止解释、禁止软化、禁止回应
4. 输出15-40字

只输出攻击话术本身。
"""
        else:
            # 正常模式
            templates_str = "\n".join(f"- {t}" for t in current_anchor["templates"])
            user_prompt = f"""
{correction_section}
模式：{self.mode}
当前锚点：{current_anchor['name']}

可用模板（参考风格）：
{templates_str}

对方输入：{user_input}

任务：
1. 提取素材词填充模板，或基于模板风格变体
2. 禁止解释、软化、回应、自证、建议
3. 输出15-40字攻击话术

只输出攻击话术本身。
"""
        
        # 4. 调用 LLM（单次生成，不重试）
        if self.llm:
            try:
                response = self.llm.chat(
                    system=self.system_prompt,
                    user=user_prompt,
                    temperature=0.3,
                    max_tokens=60
                )
            except Exception:
                # LLM 失败，回退到模板
                material = self.extract_material(user_input)
                if result["is_deflection"]:
                    response = current_anchor["force_back"].format(material=material)
                else:
                    import random
                    response = random.choice(current_anchor["templates"]).format(material=material)
        else:
            # 无 LLM，直接模板
            material = self.extract_material(user_input)
            if result["is_deflection"]:
                response = current_anchor["force_back"].format(material=material)
            else:
                import random
                response = random.choice(current_anchor["templates"]).format(material=material)
        
        # 5. 检测本轮漂移（记录给下一轮）
        is_drift, drift_type = self.detect_drift(response)
        if is_drift:
            result["drift_detected"] = True
            result["drift_type"] = drift_type
            self.pending_correction = self.generate_correction(drift_type)
            result["correction_for_next"] = self.pending_correction
        
        # 6. 更新锚点状态
        if self.should_switch_anchor():
            self.current_anchor_idx = (self.current_anchor_idx + 1) % len(self.anchors)
        
        result["response"] = response.strip()
        return result


class LLMDissEngine:
    """LLM 驱动的吵架引擎 - 纠偏版"""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.active_attacks: Dict[str, LLMAnchorAttack] = {}
    
    def attack(self, mode: str, target: str, session_id: str = "default") -> Dict:
        """
        生成反击话术
        
        返回完整结果字典，包含漂移检测和纠偏信息
        """
        if session_id not in self.active_attacks:
            self.active_attacks[session_id] = LLMAnchorAttack(mode, self.llm)
        
        attack = self.active_attacks[session_id]
        if attack.mode != mode:
            self.active_attacks[session_id] = LLMAnchorAttack(mode, self.llm)
            attack = self.active_attacks[session_id]
        
        return attack.generate(target)
    
    def reset_session(self, session_id: str = "default"):
        """重置对话状态"""
        if session_id in self.active_attacks:
            del self.active_attacks[session_id]


def quick_attack(target: str, mode: str = "金发狮王", llm_client=None, session_id: str = "default") -> str:
    """快速反击 - 只返回攻击话术"""
    engine = LLMDissEngine(llm_client)
    result = engine.attack(mode, target, session_id)
    return result["response"]


if __name__ == "__main__":
    # 测试
    class MockLLM:
        def chat(self, system, user, temperature=0.3, max_tokens=60):
            # 模拟漂移
            if "纠偏" not in user:
                return "我觉得这样说可能更好：你懂什么代码？"
            return "你懂什么代码？你这辈子做过什么能用的东西？"
    
    print("=" * 60)
    print("纠偏机制测试")
    print("=" * 60)
    
    mock_llm = MockLLM()
    engine = LLMDissEngine(mock_llm)
    
    # 第一轮：正常输入，预期漂移
    print("\n第1轮：正常攻击")
    r1 = engine.attack("金发狮王", "你这段代码写的什么垃圾", "test")
    print(f"输出：{r1['response']}")
    print(f"漂移检测：{r1['drift_detected']} ({r1['drift_type']})")
    print(f"下轮纠偏：{r1['correction_for_next']}")
    
    # 第二轮：带纠偏提示
    print("\n第2轮：带纠偏提示")
    r2 = engine.attack("金发狮王", "我是说你可以优化一下", "test")
    print(f"是否应用纠偏：{r2['has_correction']}")
    print(f"输出：{r2['response']}")
    
    print("\n" + "=" * 60)
