#!/usr/bin/env python3
"""
初始化数据库脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    """主函数"""
    from src.storage.database import DatabaseManager
    
    print("=== 初始化工商业光伏新闻数据库 ===")
    
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    
    try:
        # 初始化数据库
        await db_manager.initialize()
        print("✅ 数据库初始化成功")
        
        # 获取统计信息（测试连接）
        stats = await db_manager.get_stats()
        print(f"📊 数据库统计:")
        print(f"   总文章数: {stats.get('total_articles', 0)}")
        print(f"   已处理文章: {stats.get('processed_articles', 0)}")
        print(f"   未处理文章: {stats.get('unprocessed_articles', 0)}")
        print(f"   近7天文章: {stats.get('recent_articles_7d', 0)}")
        
        print("\n✅ 数据库连接测试成功")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())