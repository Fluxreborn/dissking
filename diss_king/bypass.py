#!/usr/bin/env python3
"""
DissKing - 屏蔽词绕过系统
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional

class BypassEngine:
    """
    屏蔽词绕过引擎
    
    功能：
    1. 检测敏感词
    2. 自动转换为绕过形式
    3. 支持多种绕过策略
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "data"
        self.data_dir = Path(data_dir)
        
        bypass_data = self._load_json("bypass.json")
        self.rules = bypass_data.get("绕过规则", {})
        self.converter = bypass_data.get("转换器", {})
        self.emotions = bypass_data.get("情绪词库", {})
    
    def _load_json(self, filename: str) -> Dict:
        """加载JSON文件"""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def bypass_en(self, text: str, level: str = "medium") -> str:
        """
        英文屏蔽词绕过
        
        Args:
            text: 英文文本
            level: light/medium/strong
        """
        # 加载英文绕过规则
        bypass_en = self._load_json("bypass_en.json")
        rules = bypass_en.get("bypass_rules", {})
        emojis = bypass_en.get("emoji_enhancement", {})
        
        if level == "light":
            # 轻度：符号替换
            symbol_map = rules.get("symbol_replacement", {})
            for word, replacement in symbol_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
        
        elif level == "medium":
            # 中度：符号替换 + 创意拼写 + emoji
            symbol_map = rules.get("symbol_replacement", {})
            creative_map = rules.get("creative_spelling", {})
            
            for word, replacement in symbol_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
            for word, replacement in creative_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
            
            # 添加emoji
            emoji_list = emojis.get("sarcastic", ["😅"])
            text = text + " " + random.choice(emoji_list)
        
        elif level == "strong":
            # 重度：所有替换 + emoji
            symbol_map = rules.get("symbol_replacement", {})
            phonetic_map = rules.get("phonetic_bypass", {})
            creative_map = rules.get("creative_spelling", {})
            
            for word, replacement in symbol_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
            for word, replacement in phonetic_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
            for word, replacement in creative_map.items():
                text = re.sub(r'\b' + word + r'\b', replacement, text, flags=re.IGNORECASE)
            
            # 添加愤怒emoji
            emoji_list = emojis.get("angry", ["🤬"])
            text = text + " " + random.choice(emoji_list) + random.choice(emoji_list)
        
        return text
    
    def pinyin_bypass(self, text: str) -> str:
        """拼音缩写绕过"""
        pinyin_map = self.converter.get("拼音替换", {})
        for word, replacement in pinyin_map.items():
            text = text.replace(word, replacement)
        return text
    
    def xieyin_bypass(self, text: str) -> str:
        """谐音替换绕过"""
        xieyin_map = self.converter.get("谐音替换", {})
        for word, replacement in xieyin_map.items():
            text = text.replace(word, replacement)
        return text
    
    def symbol_bypass(self, text: str, symbol: str = "*") -> str:
        """符号替换绕过"""
        # 简单替换：把敏感词中间加符号
        sensitive = ["他妈", "傻逼", "脑残", "废物", "垃圾"]
        for word in sensitive:
            if word in text:
                replacement = word[0] + symbol * (len(word) - 1)
                text = text.replace(word, replacement)
        return text
    
    def emoji_decorate(self, text: str, emotion: str = "讽刺") -> str:
        """添加emoji增强表达"""
        emoji_map = self.converter.get("emoji增强", {})
        emojis = emoji_map.get(emotion, "")
        
        # 随机在句中或句尾添加emoji
        if random.random() > 0.5:
            text = text + emojis
        else:
            # 在句中插入
            mid = len(text) // 2
            text = text[:mid] + emojis + text[mid:]
        
        return text
    
    def full_bypass(self, text: str, level: str = "medium") -> str:
        """
        完整绕过处理
        
        Args:
            text: 原始文本
            level: 绕过强度 (light/medium/strong)
        
        Returns:
            绕过后的文本
        """
        if level == "light":
            # 轻度：只拼音替换
            return self.pinyin_bypass(text)
        
        elif level == "medium":
            # 中度：拼音 + 谐音 + emoji
            text = self.pinyin_bypass(text)
            text = self.xieyin_bypass(text)
            text = self.emoji_decorate(text, "鄙视")
            return text
        
        elif level == "strong":
            # 重度：拼音 + 谐音 + 符号 + emoji
            text = self.pinyin_bypass(text)
            text = self.xieyin_bypass(text)
            text = self.symbol_bypass(text, "*")
            text = self.emoji_decorate(text, "愤怒")
            return text
        
        return text
    
    def generate_insult(self, target: str, emotion: str = "愤怒") -> str:
        """
        生成带绕过的攻击性话术
        
        Args:
            target: 攻击目标
            emotion: 情绪类型
        
        Returns:
            绕过后的攻击性话术
        """
        # 从情绪词库获取词
        emotion_words = self.emotions.get(emotion, {})
        bypass_words = emotion_words.get("绕过", ["辣鸡"])
        
        # 构建话术
        templates = [
            "你这个人真是{word}",
            "没见过这么{word}的",
            "{word}就是{word}，别装了",
            "你{word}的样子真可笑"
        ]
        
        word = random.choice(bypass_words)
        template = random.choice(templates)
        insult = template.format(word=word)
        
        # 添加emoji装饰
        insult = self.emoji_decorate(insult, emotion)
        
        return insult


# 便捷函数
def bypass_text(text: str, level: str = "medium") -> str:
    """快速绕过处理"""
    be = BypassEngine()
    return be.full_bypass(text, level)


def quick_insult(target: str = "你", emotion: str = "愤怒") -> str:
    """快速生成攻击性话术"""
    be = BypassEngine()
    return be.generate_insult(target, emotion)


if __name__ == "__main__":
    print("=== DissKing 屏蔽词绕过系统测试 ===\n")
    
    be = BypassEngine()
    
    # 测试不同绕过级别
    test_text = "你写的代码真他妈垃圾，像个傻逼"
    
    print(f"原文: {test_text}\n")
    
    for level in ["light", "medium", "strong"]:
        result = be.full_bypass(test_text, level)
        print(f"{level}: {result}")
    
    print("\n=== 生成攻击性话术 ===")
    for emotion in ["愤怒", "鄙视", "嘲讽"]:
        insult = be.generate_insult("你", emotion)
        print(f"{emotion}: {insult}")
