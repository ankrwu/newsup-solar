#!/usr/bin/env python3
"""
测试工商业光伏关键词功能
"""

import sys
sys.path.insert(0, '.')

from config.commercial_solar_keywords import (
    COMMERCIAL_SOLAR_KEYWORDS,
    is_commercial_solar_content,
    classify_content_type,
    extract_project_scale,
    extract_regions,
)

def test_keywords():
    """测试关键词功能"""
    print("=== 测试工商业光伏关键词功能 ===")
    
    # 测试1: 关键词列表
    print(f"\n1. 关键词数量: {len(COMMERCIAL_SOLAR_KEYWORDS)}")
    print("   示例关键词:")
    for i, kw in enumerate(COMMERCIAL_SOLAR_KEYWORDS[:10], 1):
        print(f"     {i}. {kw}")
    
    # 测试2: 内容相关性检测
    print("\n2. 内容相关性检测:")
    
    test_cases = [
        ("This is about commercial solar installation", True),
        ("Industrial PV systems are growing rapidly", True),
        ("Residential solar panels for homes", False),
        ("PPA agreements for business solar projects", True),
        ("General renewable energy news", False),
    ]
    
    for text, expected in test_cases:
        result = is_commercial_solar_content(text)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{text}' -> {result} (期望: {expected})")
    
    # 测试3: 内容类型分类
    print("\n3. 内容类型分类:")
    
    type_test_cases = [
        ("New solar policy announced by government", "policy"),
        ("Market report shows growth in commercial solar", "market"),
        ("Solar company announces new project", "news"),
        ("Technical breakthrough in PV efficiency", "news"),
    ]
    
    for text, expected_type in type_test_cases:
        classification = classify_content_type(text)
        primary_type = "policy" if classification['is_policy'] else \
                      "market" if classification['is_market'] else "news"
        status = "✅" if primary_type == expected_type else "❌"
        print(f"   {status} '{text}' -> {primary_type} (期望: {expected_type})")
        print(f"     找到关键词: {classification['keywords_found']}")
    
    # 测试4: 项目规模提取
    print("\n4. 项目规模提取:")
    
    scale_test_cases = [
        ("50 kW rooftop solar system", "small"),
        ("250 kW commercial installation", "medium"),
        ("5 MW solar farm", "large"),
        ("Small-scale residential project", "small"),
    ]
    
    for text, expected_scale in scale_test_cases:
        scale = extract_project_scale(text)
        status = "✅" if scale == expected_scale else "❌"
        print(f"   {status} '{text}' -> {scale} (期望: {expected_scale})")
    
    # 测试5: 地域提取
    print("\n5. 地域提取:")
    
    region_test_cases = [
        ("Solar project in California, USA", ["us"]),
        ("Chinese solar company expands to Europe", ["china", "europe"]),
        ("APAC region sees solar growth", ["apac"]),
        ("No specific region mentioned", []),
    ]
    
    for text, expected_regions in region_test_cases:
        regions = extract_regions(text)
        status = "✅" if set(regions) == set(expected_regions) else "❌"
        print(f"   {status} '{text}' -> {regions} (期望: {expected_regions})")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_keywords()