# -*- coding: utf-8 -*-
"""造物集·官方激活工具 —— v0.1 基础页面（tkinter，零额外 GUI 依赖）

运行：python main.py  （依赖 requests；API 默认生产环境，可用 --api 覆盖）

功能：产品列表(官网实时) / 机器码采集 / 创建订单 / 显示收款码 / 立即激活 / 本地保存激活码
"""
import argparse
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from api_client import ZaowujiAPI, ZaowujiError
from machine import get_machine_code, get_fingerprint_source

APP_TITLE = '造物集 · 官方激活工具'
APP_VERSION = '0.1.0'
LICENSE_FILE = os.path.join(os.path.expanduser('~'), '.zaowuji', 'licenses.json')

# Element Plus 风格配色
BG = '#f5f7fa'
CARD = '#ffffff'
BRAND = '#2563eb'
TEXT = '#1f2937'
MUTED = '#6b7280'
BORDER = '#e5e7eb'


def load_local_licenses() -> dict:
    """本地激活码记录 {productCode: {licenseKey, productName, activatedAt}}"""
    try:
        with open(LICENSE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_local_licenses(data: dict) -> None:
    os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
    with open(LICENSE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ActivatorApp:
    def __init__(self, root: tk.Tk, api: ZaowujiAPI):
        self.root = root
        self.api = api
        self.products = []
        self.current: dict | None = None
        self.machine_code = get_machine_code()
        self.order_no: str | None = None

        root.title(f'{APP_TITLE} v{APP_VERSION}')
        root.geometry('980x640')
        root.minsize(860, 560)
        root.configure(bg=BG)
        self._build_ui()
        self.log(f'API 地址: {api.base}')
        self.log(f'机器码: {self.machine_code[:16]}…')
        threading.Thread(target=self._load_products, daemon=True).start()

    # ================= UI =================
    def _build_ui(self):
        # 顶栏
        head = tk.Frame(self.root, bg=CARD, height=56)
        head.pack(fill='x')
        head.pack_propagate(False)
        tk.Label(head, text='🔑 造物集 · 官方激活工具', font=('Microsoft YaHei UI', 15, 'bold'),
                 bg=CARD, fg=TEXT).pack(side='left', padx=18, pady=10)
        tk.Label(head, text=f'v{APP_VERSION}', font=('Microsoft YaHei UI', 9),
                 bg=CARD, fg=MUTED).pack(side='left', pady=10)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=2, uniform='col')
        body.columnconfigure(1, weight=3, uniform='col')
        body.rowconfigure(0, weight=1)

        # ---- 左：产品列表 ----
        left = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        tk.Label(left, text='选择要激活的软件', font=('Microsoft YaHei UI', 12, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', padx=14, pady=(12, 6))

        cols = ('name', 'version', 'price')
        self.tree = ttk.Treeview(left, columns=cols, show='headings', selectmode='browse')
        self.tree.heading('name', text='软件')
        self.tree.heading('version', text='版本')
        self.tree.heading('price', text='价格')
        self.tree.column('name', width=170, anchor='w')
        self.tree.column('version', width=70, anchor='center')
        self.tree.column('price', width=80, anchor='center')
        style = ttk.Style()
        style.configure('Treeview', rowheight=30, font=('Microsoft YaHei UI', 10))
        style.configure('Treeview.Heading', font=('Microsoft YaHei UI', 10, 'bold'))
        self.tree.pack(fill='both', expand=True, padx=12, pady=4)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        self.desc_var = tk.StringVar(value='← 从左侧选择软件开始')
        tk.Label(left, textvariable=self.desc_var, wraplength=300, justify='left',
                 font=('Microsoft YaHei UI', 9), bg=CARD, fg=MUTED,
                 anchor='nw').pack(fill='x', padx=14, pady=(4, 12))

        # ---- 右：激活流程 ----
        right = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky='nsew', padx=(6, 0))

        tk.Label(right, text='激活流程', font=('Microsoft YaHei UI', 12, 'bold'),
                 bg=CARD, fg=TEXT).pack(anchor='w', padx=14, pady=(12, 8))

        # 机器码区
        mc_frame = tk.Frame(right, bg=CARD)
        mc_frame.pack(fill='x', padx=14, pady=2)
        tk.Label(mc_frame, text='本机机器码', font=('Microsoft YaHei UI', 9), bg=CARD,
                 fg=MUTED).pack(anchor='w')
        mc_row = tk.Frame(mc_frame, bg=CARD)
        mc_row.pack(fill='x', pady=(2, 0))
        self.mc_var = tk.StringVar(value=self.machine_code)
        tk.Entry(mc_row, textvariable=self.mc_var, font=('Consolas', 9), state='readonly',
                 readonlybackground='#f9fafb', relief='solid', bd=1).pack(side='left', fill='x', expand=True)
        tk.Button(mc_row, text='复制', command=self._copy_machine_code,
                  font=('Microsoft YaHei UI', 9), bg=BRAND, fg='white',
                  relief='flat', padx=10, cursor='hand2').pack(side='left', padx=(6, 0))

        # 订单区
        order_frame = tk.Frame(right, bg=CARD)
        order_frame.pack(fill='x', padx=14, pady=(10, 2))
        tk.Label(order_frame, text='① 创建订单（生成后请扫码支付）', font=('Microsoft YaHei UI', 9),
                 bg=CARD, fg=TEXT).pack(anchor='w')
        row1 = tk.Frame(order_frame, bg=CARD)
        row1.pack(fill='x', pady=4)
        tk.Label(row1, text='联系方式:', font=('Microsoft YaHei UI', 9), bg=CARD,
                 fg=MUTED).pack(side='left')
        self.contact_var = tk.StringVar(value='')
        tk.Entry(row1, textvariable=self.contact_var, font=('Microsoft YaHei UI', 9), width=24,
                 relief='solid', bd=1).pack(side='left', padx=6)
        self.btn_create = tk.Button(row1, text='创建订单', command=self._create_order,
                                    font=('Microsoft YaHei UI', 9), bg=BRAND, fg='white',
                                    relief='flat', padx=14, cursor='hand2', state='disabled')
        self.btn_create.pack(side='left', padx=6)
        row2 = tk.Frame(order_frame, bg=CARD)
        row2.pack(fill='x')
        self.order_var = tk.StringVar(value='订单号: —')
        tk.Label(row2, textvariable=self.order_var, font=('Consolas', 10), bg=CARD,
                 fg=TEXT).pack(side='left')
        tk.Button(row2, text='刷新订单状态', command=self._refresh_order,
                  font=('Microsoft YaHei UI', 9), relief='flat', bd=1,
                  cursor='hand2', state='disabled').pack(side='left', padx=(10, 0))
        self.order_status_var = tk.StringVar(value='')
        tk.Label(row2, textvariable=self.order_status_var, font=('Microsoft YaHei UI', 9),
                 bg=CARD, fg=MUTED).pack(side='left', padx=8)

        # 收款码区
        pay_frame = tk.Frame(right, bg=CARD)
        pay_frame.pack(fill='x', padx=14, pady=(10, 2))
        self.qr_canvas = tk.Label(pay_frame, text='（收款码：创建订单后可点击查看）',
                                  font=('Microsoft YaHei UI', 9), bg='#f9fafb', fg=MUTED,
                                  width=46, height=10, relief='solid', bd=1)
        self.qr_canvas.pack(side='left')
        self.qr_hint = tk.Label(pay_frame, text='', font=('Microsoft YaHei UI', 9), bg=CARD,
                                fg=MUTED, justify='left', anchor='nw', wraplength=220)
        self.qr_hint.pack(side='left', padx=12, fill='both', expand=True)

        # 激活区
        act_frame = tk.Frame(right, bg=CARD)
        act_frame.pack(fill='x', padx=14, pady=(10, 4))
        row3 = tk.Frame(act_frame, bg=CARD)
        row3.pack(fill='x')
        self.btn_activate = tk.Button(row3, text='② 立即激活（已支付后）', command=self._activate,
                                      font=('Microsoft YaHei UI', 10, 'bold'), bg='#16a34a',
                                      fg='white', relief='flat', padx=16, pady=4, cursor='hand2',
                                      state='disabled')
        self.btn_activate.pack(side='left')
        self.lic_var = tk.StringVar(value='激活码: —')
        tk.Label(row3, textvariable=self.lic_var, font=('Consolas', 9), bg=CARD,
                 fg='#16a34a').pack(side='left', padx=10)

        # 日志
        log_frame = tk.Frame(right, bg=CARD)
        log_frame.pack(fill='both', expand=True, padx=14, pady=(8, 12))
        tk.Label(log_frame, text='操作日志', font=('Microsoft YaHei UI', 9), bg=CARD,
                 fg=MUTED).pack(anchor='w')
        self.log_text = tk.Text(log_frame, height=7, font=('Consolas', 9), bg='#0f172a',
                                fg='#e2e8f0', relief='flat', state='disabled')
        self.log_text.pack(fill='both', expand=True, pady=(2, 0))

    # ================= 行为 =================
    def log(self, msg: str):
        def _do():
            self.log_text.configure(state='normal')
            self.log_text.insert('end', msg + '\n')
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
        self.root.after(0, _do)

    def _load_products(self):
        try:
            data = self.api.list_products()
        except ZaowujiError as e:
            self.log(f'❌ 拉取产品失败: {e}')
            self.root.after(0, lambda: messagebox.showerror('加载失败', str(e)))
            return
        self.products = data

        def _fill():
            self.tree.delete(*self.tree.get_children())
            for p in data:
                self.tree.insert('', 'end', iid=str(p['id']), values=(
                    p['name'], p.get('version') or '—', f"¥{p['price']}"))
            self.log(f'✅ 已加载 {len(data)} 个在售软件')
        self.root.after(0, _fill)

    def _on_select(self, _evt=None):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        self.current = next((p for p in self.products if p['id'] == pid), None)
        if not self.current:
            return
        p = self.current
        desc = p.get('description') or ''
        self.desc_var.set(f"{p['name']}  v{p.get('version') or '—'}  ¥{p['price']}\n\n{desc}")
        self.order_no = None
        self.order_var.set('订单号: —')
        self.order_status_var.set('')
        self.lic_var.set('激活码: —')
        self.btn_create.configure(state='normal')
        self.btn_activate.configure(state='disabled')
        self.qr_canvas.configure(image='', text='（收款码：创建订单后可点击查看）')
        self.log(f'已选择软件: {p["name"]} (id={pid})')

    def _copy_machine_code(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.machine_code)
        self.log('机器码已复制到剪贴板')

    def _create_order(self):
        if not self.current:
            return
        self.btn_create.configure(state='disabled')
        pid = self.current['id']
        contact = self.contact_var.get().strip()

        def work():
            try:
                data = self.api.create_order(pid, contact)
                no = data['orderNo']
                self.order_no = no

                def _ok():
                    self.order_var.set(f'订单号: {no}')
                    self.btn_create.configure(state='normal')
                    self.btn_activate.configure(state='normal')
                    self.log(f'✅ 订单创建成功: {no}')
                    self.log('请使用微信/支付宝扫码支付，管理员核验后点击「立即激活」')
                    self._show_qr()
                self.root.after(0, _ok)
            except ZaowujiError as e:
                self.root.after(0, lambda: (self.log(f'❌ 创建订单失败: {e}'),
                                            self.btn_create.configure(state='normal')))
        threading.Thread(target=work, daemon=True).start()

    def _show_qr(self):
        """拉取当前产品收款码显示（后端接口 GET /products/{id}/pay-qr）"""
        if not self.current:
            return
        pid = self.current['id']

        def work():
            try:
                img_bytes = self.api.fetch_pay_qr(pid)
                img = tk.PhotoImage(data=img_bytes)
                self.root.after(0, lambda: self._set_qr(img))
            except Exception as e:
                self.root.after(0, lambda: self.qr_hint.configure(
                    text=f'收款码加载失败: {e}\n\n请先让管理员在后台为该产品配置收款码图片。'))
        threading.Thread(target=work, daemon=True).start()

    def _set_qr(self, img: tk.PhotoImage):
        # 缩放显示
        w, h = img.width(), img.height()
        if w > 200 or h > 200:
            scale = min(200 / w, 200 / h)
            img = img.subsample(max(1, int(1 / scale)))
        self.qr_canvas.configure(image=img, text='')
        self.qr_canvas.image = img
        self.qr_hint.configure(text='请使用手机扫码支付对应金额\n支付后联系管理员核验（后台人工确认）\n核验通过后点击「立即激活」')

    def _refresh_order(self):
        if not self.order_no:
            return
        no = self.order_no

        def work():
            try:
                data = self.api.get_order(no)
                status = data.get('status')
                label = {0: '待支付', 1: '已支付(可激活)', 4: '已签发'}.get(status, f'状态{status}')
                self.root.after(0, lambda: self.order_status_var.set(label))
            except ZaowujiError as e:
                self.root.after(0, lambda: self.order_status_var.set(f'查询失败: {e}'))
        threading.Thread(target=work, daemon=True).start()

    def _activate(self):
        if not self.current or not self.order_no:
            return
        if not messagebox.askyesno('确认激活', '请确认已扫码支付且管理员已核验通过？\n点击确定将提交本机机器码并签发激活码。'):
            return
        self.btn_activate.configure(state='disabled')
        pid = self.current['id']

        def work():
            try:
                data = self.api.activate(pid, self.machine_code, self.order_no)
                key = data.get('licenseKey', '')
                sign = data.get('sign', '')
                local = load_local_licenses()
                local[self.current['code']] = {
                    'licenseKey': key,
                    'productName': self.current['name'],
                    'activatedAt': data.get('issuedAt', ''),
                }
                save_local_licenses(local)

                def _ok():
                    self.lic_var.set('✅ 激活成功')
                    self.log(f'🎉 激活成功! 激活码: {key}')
                    self._copy_to_clipboard(key)
                    self.btn_activate.configure(state='normal')
                self.root.after(0, _ok)
            except ZaowujiError as e:
                self.root.after(0, lambda: (self.log(f'❌ 激活失败: {e}'),
                                            self.btn_activate.configure(state='normal'),
                                            messagebox.showerror('激活失败', str(e))))
        threading.Thread(target=work, daemon=True).start()

    def _copy_to_clipboard(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)


def main():
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument('--api', default=None, help='后端 API 地址（默认生产 https://collectionofcreations.uk/api）')
    args = parser.parse_args()

    api = ZaowujiAPI(args.api) if args.api else ZaowujiAPI()

    root = tk.Tk()
    ActivatorApp(root, api)
    root.mainloop()


if __name__ == '__main__':
    main()
