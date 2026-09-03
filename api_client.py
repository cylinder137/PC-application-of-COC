# -*- coding: utf-8 -*-
"""造物集后端 API 封装（zaowuji-activator 使用）

统一处理：{ code, data, message } 响应解包；code=0 视为成功。
默认指向生产环境 https://collectionofcreations.uk/api
（本地联调可传 base='http://localhost:8080/api'）
"""
import requests

DEFAULT_BASE = 'https://collectionofcreations.uk/api'


class ZaowujiError(RuntimeError):
    """业务错误（携带后端 message）"""


class ZaowujiAPI:
    def __init__(self, base: str = DEFAULT_BASE, timeout: int = 20):
        self.base = base.rstrip('/')
        self.timeout = timeout
        self.s = requests.Session()
        self.s.headers['User-Agent'] = 'zaowuji-activator/0.1'
        # 反爬签名头：桌面端非浏览器，浏览器端 sign 仅前端自校验，后端未强制——留空即可

    # ---------- 内部 ----------
    def _req(self, method: str, path: str, **kw) -> dict:
        kw.setdefault('timeout', self.timeout)
        try:
            r = self.s.request(method, self.base + path, **kw)
        except requests.RequestException as e:
            raise ZaowujiError(f'网络请求失败: {e}') from e
        try:
            j = r.json()
        except ValueError as e:
            raise ZaowujiError(f'响应不是合法 JSON (HTTP {r.status_code})') from e
        if j.get('code') != 0:
            raise ZaowujiError(j.get('message') or f'业务错误 code={j.get("code")}')
        return j.get('data')

    # ---------- 产品 ----------
    def list_products(self) -> list:
        """上架产品列表 [{id,name,code,description,version,coverUrl,downloadUrl,price,status,sort}]"""
        return self._req('GET', '/products')

    # ---------- RSA 公钥 ----------
    def public_key(self) -> dict:
        """RSA 公钥 {algorithm, pem}（用于本地离线验签）"""
        return self._req('GET', '/license-key/public-key')

    # ---------- 订单 ----------
    def create_order(self, product_id: int, contact: str = '', remark: str = '') -> dict:
        """创建订单 → {orderNo, ...}（需人工核验支付后订单才可激活）"""
        return self._req('POST', '/orders', json={
            'productId': product_id,
            'contact': contact or 'zaowuji-activator',
            'remark': remark,
        })

    def get_order(self, order_no: str) -> dict:
        """订单详情（status: 0待支付 1已支付…）"""
        return self._req('GET', f'/orders/{order_no}')

    # ---------- 激活 ----------
    def activate(self, product_id: int, machine_code: str, order_no: str) -> dict:
        """提交激活 → 签发激活码 {licenseKey, sign, ...}"""
        return self._req('POST', '/activations', json={
            'productId': product_id,
            'machineCode': machine_code,
            'orderNo': order_no,
        })

    def list_activations(self, machine_code: str) -> list:
        """本机激活记录（按机器码）"""
        return self._req('GET', '/activations', params={'machineCode': machine_code})

    def verify(self, code: str) -> dict:
        """在线核验激活码有效性"""
        return self._req('GET', '/license-key/verify', params={'code': code})

    # ---------- 静态资源 ----------
    def pay_qr_url(self, product_id: int) -> str:
        """产品收款码图片接口地址（GET 返回图片二进制流；未配置返回 404）"""
        return f'{self.base}/products/{product_id}/pay-qr'

    def fetch_pay_qr(self, product_id: int) -> bytes:
        """拉取产品收款码图片二进制（桌面端展示用）"""
        r = self.s.get(self.pay_qr_url(product_id), timeout=15)
        if r.status_code != 200:
            raise ZaowujiError(f'收款码获取失败 (HTTP {r.status_code})')
        return r.content
