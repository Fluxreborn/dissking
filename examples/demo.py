#!/usr/bin/env python3
"""
DissKing - 使用示例
"""

from diss_king import DissEngine, quick_attack
from pathlib import Path

def demo_basic():
    """基础用法"""
    print("=" * 60)
    print("基础用法演示 - 8种外号模式")
    print("=" * 60)
    
    dk = DissEngine()
    
    test_cases = [
        ("你这段代码写的什么垃圾，重构！", "金发狮王"),
        ("年轻人要谦虚一点，多听听前辈的", "文化斗士"),
        ("我是你领导，按我说的做", "暴躁将军"),
        ("哈哈哈，你这水平也敢提交？", "抽象小鬼"),
        ("你这个方案我看不行，太简单了", "胡同串子"),
        ("准备好输了吗？", "擂台霸主"),
        ("别跟我讲那些虚的，直接说结果", "耿直黑哥"),
        ("您这代码可得好好改改", "相声掌柜"),
    ]
    
    for target, mode in test_cases:
        response = dk.attack(mode, target)
        print(f"\n对方: {target}")
        print(f"外号: {mode}")
        print(f"反击: {response}")


def demo_auto():
    """自动推荐模式"""
    print("\n" + "=" * 60)
    print("自动推荐模式")
    print("=" * 60)
    
    dk = DissEngine()
    
    test_cases = [
        "你这段代码写的什么垃圾",  # -> 金发狮王
        "根据我多年的经验，你应该这样这样做...",  # -> 文化斗士
        "哈哈哈笑死，就这？",  # -> 抽象小鬼
    ]
    
    for target in test_cases:
        mode = dk.recommend_mode(target)
        response = dk.attack(mode, target)
        print(f"\n对方: {target}")
        print(f"推荐外号: {mode}")
        print(f"反击: {response}")


def demo_quick():
    """快速反击"""
    print("\n" + "=" * 60)
    print("快速反击")
    print("=" * 60)
    
    target = "你这方案根本行不通"
    response = quick_attack(target, mode="auto")
    
    print(f"\n对方: {target}")
    print(f"反击: {response}")


def interactive_demo():
    """交互式演示"""
    print("\n" + "=" * 60)
    print("交互模式 - 输入对方的话，输入q退出")
    print("=" * 60)
    
    dk = DissEngine()
    
    while True:
        target = input("\n对方说: ")
        if target.lower() == 'q':
            break
        
        mode = dk.recommend_mode(target)
        response = dk.attack(mode, target)
        
        print(f"推荐外号: {mode}")
        print(f"反击: {response}")


if __name__ == "__main__":
    demo_basic()
    demo_auto()
    demo_quick()
    
    # 取消注释以运行交互模式
    # interactive_demo()
