"""
动态内容爬虫支持模块
使用 Playwright 渲染 JavaScript 动态加载的页面
"""

import asyncio
import logging
from abc import abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Playwright 支持标志
PLAYWRIGHT_AVAILABLE = False

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright is available for dynamic content rendering")
except ImportError:
    logger.warning("Playwright not installed. Dynamic content crawling will be disabled.")
    logger.warning("Install with: pip install playwright && playwright install")


class DynamicContentCrawler:
    """
    动态内容爬虫基类
    使用 Playwright 渲染 JavaScript 页面
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        初始化动态爬虫
        
        Args:
            headless: 是否无头模式运行浏览器
            timeout: 页面加载超时时间（毫秒）
        """
        self.headless = headless
        self.timeout = timeout
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
    
    @property
    def is_available(self) -> bool:
        """检查 Playwright 是否可用"""
        return PLAYWRIGHT_AVAILABLE
    
    async def init_browser(self) -> bool:
        """初始化浏览器"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available, cannot initialize browser")
            return False
        
        if self._browser is not None:
            return True
        
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            # 创建浏览器上下文，设置用户代理
            self._context = await self._browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
            )
            
            logger.info("Playwright browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            return False
    
    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            logger.info("Playwright browser closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def fetch_page(self, url: str, wait_for: str = None, 
                         wait_time: int = 2000) -> Optional[str]:
        """
        获取动态渲染后的页面内容
        
        Args:
            url: 页面 URL
            wait_for: 等待特定元素出现的选择器
            wait_time: 额外等待时间（毫秒）
        
        Returns:
            渲染后的 HTML 内容
        """
        if not await self.init_browser():
            return None
        
        page = None
        try:
            page = await self._context.new_page()
            
            # 设置超时
            page.set_default_timeout(self.timeout)
            
            # 访问页面
            logger.debug(f"Navigating to {url}")
            await page.goto(url, wait_until='networkidle')
            
            # 等待特定元素
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=self.timeout)
            
            # 额外等待动态内容加载
            await asyncio.sleep(wait_time / 1000)
            
            # 获取渲染后的 HTML
            content = await page.content()
            
            logger.debug(f"Successfully fetched dynamic content from {url}")
            return content
            
        except Exception as e:
            logger.error(f"Error fetching dynamic content from {url}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
    
    async def fetch_multiple_pages(self, urls: List[str], 
                                    wait_for: str = None,
                                    wait_time: int = 2000) -> Dict[str, str]:
        """
        批量获取多个页面的动态内容
        
        Args:
            urls: URL 列表
            wait_for: 等待特定元素出现的选择器
            wait_time: 额外等待时间（毫秒）
        
        Returns:
            URL -> HTML 内容的字典
        """
        results = {}
        
        for url in urls:
            content = await self.fetch_page(url, wait_for, wait_time)
            if content:
                results[url] = content
            await asyncio.sleep(1)  # 避免请求过快
        
        return results
    
    async def scroll_page(self, url: str, scroll_times: int = 3, 
                          wait_time: int = 1000) -> Optional[str]:
        """
        滚动页面以加载懒加载内容
        
        Args:
            url: 页面 URL
            scroll_times: 滚动次数
            wait_time: 每次滚动后等待时间（毫秒）
        
        Returns:
            滚动后的 HTML 内容
        """
        if not await self.init_browser():
            return None
        
        page = None
        try:
            page = await self._context.new_page()
            page.set_default_timeout(self.timeout)
            
            await page.goto(url, wait_until='networkidle')
            
            # 滚动页面
            for _ in range(scroll_times):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(wait_time / 1000)
            
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error scrolling page {url}: {e}")
            return None
            
        finally:
            if page:
                await page.close()
    
    async def click_and_wait(self, url: str, click_selector: str,
                             wait_for: str = None,
                             wait_time: int = 2000) -> Optional[str]:
        """
        点击元素并等待内容加载
        
        Args:
            url: 页面 URL
            click_selector: 要点击的元素选择器
            wait_for: 点击后等待的元素选择器
            wait_time: 等待时间（毫秒）
        
        Returns:
            点击后的 HTML 内容
        """
        if not await self.init_browser():
            return None
        
        page = None
        try:
            page = await self._context.new_page()
            page.set_default_timeout(self.timeout)
            
            await page.goto(url, wait_until='networkidle')
            
            # 点击元素
            await page.click(click_selector)
            
            # 等待内容加载
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=self.timeout)
            else:
                await asyncio.sleep(wait_time / 1000)
            
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error clicking element on {url}: {e}")
            return None
            
        finally:
            if page:
                await page.close()


class HybridCrawler(DynamicContentCrawler):
    """
    混合爬虫基类
    结合静态爬取和动态渲染两种方式
    """
    
    def __init__(self, prefer_dynamic: bool = False, **kwargs):
        """
        初始化混合爬虫
        
        Args:
            prefer_dynamic: 是否优先使用动态渲染
        """
        super().__init__(**kwargs)
        self.prefer_dynamic = prefer_dynamic
    
    async def fetch_with_fallback(self, url: str, 
                                   static_fetcher=None,
                                   wait_for: str = None) -> Optional[str]:
        """
        使用优先策略获取内容，失败时回退
        
        Args:
            url: 页面 URL
            static_fetcher: 静态获取函数 (async callable)
            wait_for: 动态渲染时等待的选择器
        
        Returns:
            HTML 内容
        """
        if self.prefer_dynamic and self.is_available:
            # 优先尝试动态渲染
            content = await self.fetch_page(url, wait_for=wait_for)
            if content:
                return content
            
            logger.info(f"Dynamic fetch failed for {url}, falling back to static")
        
        # 静态获取
        if static_fetcher:
            try:
                content = await static_fetcher(url)
                if content:
                    return content
            except Exception as e:
                logger.error(f"Static fetch failed for {url}: {e}")
        
        # 如果还没尝试动态渲染，现在尝试
        if not self.prefer_dynamic and self.is_available:
            content = await self.fetch_page(url, wait_for=wait_for)
            if content:
                return content
        
        return None


def check_playwright_installed() -> bool:
    """检查 Playwright 是否已安装"""
    return PLAYWRIGHT_AVAILABLE


async def install_playwright():
    """安装 Playwright 浏览器"""
    import subprocess
    import sys
    
    try:
        # 安装 playwright 包
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'playwright'])
        
        # 安装浏览器
        subprocess.check_call([sys.executable, '-m', 'playwright', 'install', 'chromium'])
        
        logger.info("Playwright installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to install Playwright: {e}")
        return False
