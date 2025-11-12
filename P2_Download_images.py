"""Instagram 图片下载器 - 调试版本"""
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import requests
from playwright.sync_api import Response, sync_playwright


class MediaCollector:
    def __init__(self) -> None:
        self.media_urls: Dict[str, str] = {}
        self._ordered_ids: List[str] = []
        self.post_ids: set[str] = set()
        self.total_posts: int | None = None
        self._dirty = False
        self.intercepted_urls = []  # 新增：记录所有拦截的URL

    def ingest_payload(self, payload: Dict) -> None:
        print(f"开始处理 payload，keys: {list(payload.keys())}")
        user = payload.get("data", {}).get("user")
        if not user:
            print("没有找到 user 数据")
            return

        print(f"找到 user 数据")
        media = user.get("edge_owner_to_timeline_media") or {}
        if self.total_posts is None:
            self.total_posts = media.get("count")
            print(f"总帖子数: {self.total_posts}")

        edges = media.get("edges") or []
        print(f"找到 {len(edges)} 条边")
        before = len(self.media_urls)
        for i, edge in enumerate(edges):
            node = edge.get("node") or {}
            node_id = node.get("id")
            if node_id:
                self.post_ids.add(node_id)
            self._capture_node(node)
            print(f"处理第 {i+1} 个节点，ID: {node_id}")

        if len(self.media_urls) > before:
            self._dirty = True
            print(f"新增 {len(self.media_urls) - before} 个媒体URL")

    def _capture_node(self, node: Dict) -> None:
        display_url = node.get("display_url")
        node_id = node.get("id")
        if display_url and node_id and node_id not in self.media_urls:
            self.media_urls[node_id] = display_url
            self._ordered_ids.append(node_id)
            print(f"捕获媒体: ID={node_id}, URL={display_url[:50]}...")

        sidecar = node.get("edge_sidecar_to_children") or {}
        children = sidecar.get("edges", [])
        if children:
            print(f"发现轮播图，包含 {len(children)} 个子媒体")
        for child in children:
            child_node = child.get("node") or {}
            child_id = child_node.get("id")
            child_url = child_node.get("display_url")
            if child_id and child_url and child_id not in self.media_urls:
                self.media_urls[child_id] = child_url
                self._ordered_ids.append(child_id)
                print(f"捕获子媒体: ID={child_id}, URL={child_url[:50]}...")

    def consume_dirty_flag(self) -> bool:
        dirty = self._dirty
        self._dirty = False
        return dirty

    def iter_media(self):
        for media_id in self._ordered_ids:
            yield media_id, self.media_urls[media_id]

    def media_items(self) -> List[Tuple[str, str]]:
        return list(self.iter_media())


def extract_username(profile_url: str) -> str:
    parsed = urlparse(profile_url)
    if not parsed.netloc:
        raise ValueError("Invalid profile URL")
    username = parsed.path.strip("/")
    if not username:
        raise ValueError("Could not determine username from URL")
    print(f"提取用户名: {username}")
    return username


def auto_scroll(page, collector: MediaCollector, pause_ms: int = 1500) -> None:
    idle_loops = 0
    max_scrolls = 20  # 防止无限滚动
    
    for scroll_count in range(max_scrolls):
        print(f"滚动第 {scroll_count + 1} 次")
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(pause_ms)

        if collector.total_posts and len(collector.post_ids) >= collector.total_posts:
            print(f"已加载所有 {collector.total_posts} 个帖子")
            break

        if collector.consume_dirty_flag():
            idle_loops = 0
            print("检测到新数据，重置空闲计数")
            continue

        idle_loops += 1
        print(f"空闲循环: {idle_loops}/6")
        if idle_loops >= 3:  # 降低阈值以更快退出
            print("连续3次滚动未发现新数据，停止滚动")
            break

    print(f"滚动完成，共收集 {len(collector.media_urls)} 个媒体URL")


def wait_for_initial_payload(collector: MediaCollector, timeout_ms: int = 10000) -> None:
    print("等待初始数据加载...")
    deadline = time.time() + timeout_ms / 1000
    while collector.total_posts is None and time.time() < deadline:
        time.sleep(0.5)
        print("仍在等待初始数据...")
    
    if collector.total_posts is None:
        print("⚠️ 初始数据加载超时")
    else:
        print(f"✅ 初始数据加载成功，总帖子数: {collector.total_posts}")


def download_instagram(profile_url: str, output_dir: str = "downloads", headful: bool = True):
    """下载 Instagram 图片"""
    
    username = extract_username(profile_url)
    collector = MediaCollector()

    print(f"启动浏览器 (headless={not headful})...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
			executable_path="D:/chromium-win64/chrome-win/chrome.exe",
                headless=not headful,
                proxy={"server": "http://127.0.0.1:7890"}
            )
            context = browser.new_context()
            
            # 设置用户代理，模拟真实浏览器
            context.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })

            def handle_response(response: Response) -> None:
                url = response.url
                collector.intercepted_urls.append(url)
                
                # 放宽拦截条件，捕获更多请求
                if any(keyword in url for keyword in ["graphql", "api", "query", "web_profile"]):
                    print(f"拦截到相关请求: {url}")
                    try:
                        data = response.json()
                        if "data" in data:
                            print(f"✅ 处理有效数据，URL: {url}")
                            collector.ingest_payload(data)
                        else:
                            print(f"⚠️ 响应中没有 data 字段")
                    except Exception as e:
                        print(f"❌ 解析 JSON 失败 {url}: {e}")
                else:
                    # 只打印前几个其他请求以避免过多输出
                    if len(collector.intercepted_urls) <= 10:
                        print(f"其他请求: {url}")

            context.on("response", handle_response)
            page = context.new_page()
            
            print(f"导航到 {profile_url}...")
            page.goto(profile_url, wait_until="networkidle")
            
            # 检查页面是否加载成功
            page_title = page.title()
            print(f"页面标题: {page_title}")
            
            # 检查是否有登录墙或错误页面
            if "登录" in page_title or "log in" in page_title.lower():
                print("❌ 遇到登录页面，可能需要先登录")
            elif "错误" in page_title or "error" in page_title.lower():
                print("❌ 页面加载错误")
            else:
                print("✅ 页面加载成功")
            
            print(f"等待初始数据...")
            wait_for_initial_payload(collector)
            
            print(f"开始自动滚动...")
            auto_scroll(page, collector)
            
            print(f"总共拦截了 {len(collector.intercepted_urls)} 个请求")
            print(f"收集到 {len(collector.media_urls)} 个媒体 URL")
            
            browser.close()

    except Exception as e:
        print(f"❌ 浏览器操作出错: {e}")
        return 0

    if not collector.media_items():
        print("❌ 没有收集到媒体 URL。可能的原因：")
        print("   - 账号是私密的")
        print("   - 网络请求没有被正确拦截")
        print("   - Instagram 页面结构已更改")
        print("   - 代理设置有问题")
        return 0

    # 下载图片
    target_dir = Path(output_dir) / username
    target_dir.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    downloaded = 0
    print(f"开始下载 {len(collector.media_items())} 个媒体...")
    
    for i, (media_id, url) in enumerate(collector.media_items()):
        suffix = Path(urlparse(url).path).suffix or ".jpg"
        destination = target_dir / f"{media_id}{suffix}"
        
        if destination.exists():
            print(f"跳过已存在的文件: {destination}")
            continue

        try:
            print(f"下载第 {i+1} 个媒体: {url[:50]}...")
            with session.get(url, stream=True, timeout=60, proxies=proxies) as resp:
                resp.raise_for_status()
                with open(destination, "wb") as handle:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            handle.write(chunk)
            print(f"✅ 已保存: {destination}")
            downloaded += 1
        except Exception as e:
            print(f"❌ 下载失败 {url}: {e}")

    print(f"下载完成！共下载 {downloaded} 张图片到 {target_dir}")
    return downloaded


if __name__ == "__main__":
    if len(sys.argv) > 1:
        profile_url = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "F:/Machine_Learning/GenAI/P2/Downloads"
        headful = len(sys.argv) > 3 and sys.argv[3].lower() == "true"
    else:
        profile_url = "https://www.instagram.com/grapeot/"
        output_dir = "F:/Machine_Learning/GenAI/P2/Downloads"
        headful = True
    
    print("=" * 50)
    print("开始下载 Instagram 图片...")
    print(f"目标URL: {profile_url}")
    print(f"输出目录: {output_dir}")
    print(f"显示浏览器: {headful}")
    print("=" * 50)
    
    download_instagram(profile_url, output_dir, headful)
