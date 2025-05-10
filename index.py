import argparse
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility
from metamask import Setup as SetupMetamask, Auto as AutoMetamask, EXTENSION_URL

URL_PROJECT = 'https://bytenova.ai/rewards'

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        self.setup_metamask = SetupMetamask(node, profile)

    def _run(self):
        self.setup_metamask._run()
        self.node.new_tab(f'{URL_PROJECT}?invite_code=Ljdm0oFIR')

class Auto:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.password = profile.get('password')
        self.seeds = profile.get('seeds')
        self.auto_metamask = AutoMetamask(node, profile)

    def connect_wallet(self):
        self.node.new_tab(f'{URL_PROJECT}?invite_code=Ljdm0oFIR')
        is_connected = self.node.ask_ai('Tôi đã kết nối ví chưa? Trả lời bằng 1 từ true hoặc false')

        if 'true' in is_connected:
            self.node.log(f'Đã connect ví')
            return True
        elif is_connected == None:
            if self.node.find(By.CSS_SELECTOR, '[alt="score"]'):
                self.node.log(f'Đã connect ví')
                return True    
        
        self.node.log(f'Cần connect ví')
        actions = [
            (self.node.find_and_click, By.CSS_SELECTOR, '[alt="Connect Wallet"]'),
            (self.node.find_and_click, By.XPATH, '//p[text()="MetaMask"]'),
            (self.node.switch_tab, f'{EXTENSION_URL}', 'url'),
            (self.node.go_to, f'{EXTENSION_URL}/popup.html', 'get'),
            (self.node.find_and_click, By.XPATH, '//button[text()="Connect"]', False),
            (self.node.find_and_click, By.XPATH, '//button[text()="Confirm"]'),
            (self.node.switch_tab, f'{URL_PROJECT}'),
            (self.node.find, By.CSS_SELECTOR, '[alt="score"]'),
        ]

        if self.node.execute_chain(actions=actions, message_error=f"connect_wallet thất bại"):
            self.node.log(f'Connect ví thành công')
            return True
        else:
            self.node.check_window_handles()
            input('enter')
            self.node.snapshot("connect_wallet thất bại")
            return False
        
    def check_in(self):
        self.node.find_and_click(By.XPATH, '//button[text()="Quest"]')
        button = self.node.find(By.XPATH, '//button[text()="Check-In"]')
        self.node.scroll_to(button)
        if button.is_enabled():
            self.node.find_and_click(By.XPATH, '//button[text()="Check-In"]')
            self.node.switch_tab(f'{EXTENSION_URL}')
            self.node.go_to(f'{EXTENSION_URL}/popup.html', 'get')
            if not self.node.find_and_click(By.XPATH, '//button[text()="Confirm"]'):
                self.node.snapshot(f'Có thể không đủ fee gas BNB')
            self.node.switch_tab(f'{URL_PROJECT}')
            self.node.reload_tab()
            return self.check_in()
        else:
            self.node.log(f'Đã check-in hôm nay')

        days = self.node.find_all(By.CSS_SELECTOR, '[class="text-\\[13px\\] text-\\[\\#9799A1\\]"]')
        if days:
            self.node.snapshot(f'Đã check-in {days[-1].text}')
        else:
            self.node.snapshot('Check-in thất bại')
    def _run(self):
        self.auto_metamask._run()
        if not self.auto_metamask.change_network(network_name='Binance Smart Chain',
                                        rpc_url='https://bsc-dataseed.binance.org/',
                                        chain_id='56',
                                        symbol='BNB',
                                        block_explorer_url='https://bscscan.com',
                                        ):
            self.node.snapshot(f'Chuyển network thất bại')
        
        self.connect_wallet()
        self.check_in()
        input('Nhấn Enter để tiếp tục')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    parser.add_argument('--disable-gpu', action='store_true', help="Tắt GPU")
    args = parser.parse_args()

    profiles = Utility.get_data('profile_name', 'password', 'seeds')
    if not profiles:
        print("Không có dữ liệu để chạy")
        exit()

    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    browser_manager.config_extension('meta-wallet-*.crx')
    # browser_manager.run_browser(profiles[1])
    browser_manager.run_terminal(
        profiles=profiles,
        max_concurrent_profiles=4,
        block_media=True,
        auto=args.auto,
        headless=args.headless,
        disable_gpu=args.disable_gpu,
    )