#!/usr/bin/env python
"""Generate simulated ERPNext data for demos and performance tests.

Every voucher goes through the regular insert()/submit() path, so GL and stock
ledger entries are produced by ERPNext itself. All names are fictional.

Run from the bench root:
    env/bin/python tools/erpnext_seed/seed.py --site demo.localhost setup
    env/bin/python tools/erpnext_seed/seed.py --site demo.localhost generate --max-invoices 20
    env/bin/python tools/erpnext_seed/seed.py --site demo.localhost generate
    env/bin/python tools/erpnext_seed/seed.py --site demo.localhost finalize
    env/bin/python tools/erpnext_seed/seed.py --site demo.localhost report

`generate` commits one posting day at a time and resumes after the last
committed day. The output for a day depends only on the seed, the date and the
data already committed, so a repeat run on a fresh site gives the same result.
"""

import argparse
import json
import math
import os
import random
import statistics
import time
from datetime import date, timedelta
from pathlib import Path

COMPANY = "Công ty TNHH Demo An Phát"
ABBR = "AP"
CURRENCY = "VND"
BANK_ACCOUNT_NAME = "Vietcombank"

PROFILES = {
	"demo": {"customers": 50, "suppliers": 20, "items": 100, "sales": 1500, "purchases": 500},
	"perf": {"customers": 2000, "suppliers": 500, "items": 5000, "sales": 37500, "purchases": 12500},
}

MONTH_WEIGHT = {1: 1.6, 2: 0.7, 3: 0.9, 4: 0.9, 5: 1.0, 6: 0.9, 7: 0.9, 8: 1.0, 9: 1.1, 10: 1.1, 11: 1.3, 12: 1.4}
WEEKDAY_WEIGHT = [1.0, 1.0, 1.0, 1.0, 1.1, 0.6, 0.15]

TERRITORIES = ["Miền Bắc", "Miền Trung", "Miền Nam"]
CUSTOMER_GROUPS = ["Đại lý", "Bán lẻ", "Doanh nghiệp"]
SUPPLIER_GROUPS = ["Nhà sản xuất", "Nhà phân phối", "Nhập khẩu"]
TERMS = {"Thanh toán ngay": 0, "Công nợ 15 ngày": 15, "Công nợ 30 ngày": 30, "Công nợ 45 ngày": 45}
WAREHOUSES = ["Kho Hà Nội", "Kho TP.HCM"]

CATALOG = {
	"Thực phẩm": ["Gạo thơm", "Cà phê rang xay", "Mì ăn liền", "Nước mắm", "Dầu ăn", "Đường tinh luyện", "Bánh quy", "Hạt điều"],
	"Đồ uống": ["Trà xanh", "Nước suối", "Nước ép trái cây", "Sữa tươi", "Sữa đậu nành", "Nước ngọt"],
	"Gia dụng": ["Nồi cơm điện", "Ấm siêu tốc", "Quạt điện", "Bộ nồi inox", "Bình giữ nhiệt", "Chảo chống dính"],
	"Văn phòng phẩm": ["Giấy in A4", "Bút bi", "Sổ tay", "Bìa hồ sơ", "Băng keo", "Kẹp giấy"],
	"Điện tử": ["Tai nghe", "Chuột không dây", "Bàn phím", "Sạc dự phòng", "Loa mini", "Cáp sạc"],
}
PRICE_RANGE = {
	"Thực phẩm": (20_000, 300_000),
	"Đồ uống": (10_000, 150_000),
	"Gia dụng": (150_000, 2_500_000),
	"Văn phòng phẩm": (5_000, 120_000),
	"Điện tử": (80_000, 1_500_000),
}
VARIANTS = ["loại 1", "loại 2", "gói nhỏ", "gói lớn", "cao cấp", "tiêu chuẩn", "tiết kiệm", "đặc biệt"]
BRANDS = ["An Khang", "Bình Minh", "Cát Tường", "Đại Phúc", "Hoàng Long", "Hưng Thịnh", "Kim Ngân", "Lộc Phát", "Minh Tâm", "Nam Việt",
	"Phú Quý", "Sao Mai", "Tân Tiến", "Thành Công", "Thiên Ân", "Trường An", "Việt Hà", "Vĩnh Lợi", "Xuân Mai", "Hải Đăng"]
CUSTOMER_PREFIX = ["Công ty TNHH Thương mại", "Công ty CP Dịch vụ", "Siêu thị", "Cửa hàng", "Đại lý"]
SUPPLIER_PREFIX = ["Công ty CP Sản xuất", "Công ty TNHH Phân phối", "Công ty XNK"]
EXPENSES = {"Salary": 0.09, "Office Rent": 0.03, "Utility Expenses": 0.01, "Marketing Expenses": 0.02}


class Seeder:
	def __init__(self, site, profile_name, seed, end):
		import frappe

		self.frappe = frappe
		self.site = site
		self.profile_name = profile_name
		self.profile = PROFILES[profile_name]
		self.seed = seed
		self.end = end
		self.start = end - timedelta(days=364)
		self.opening_date = self.start - timedelta(days=1)
		self.out = Path(frappe.get_site_path("private", "seed")).resolve()
		self.out.mkdir(parents=True, exist_ok=True)
		self.state_path = self.out / f"state-{profile_name}.json"
		self.timings_path = self.out / f"timings-{profile_name}.jsonl"
		self.timings = []

	# helpers -----------------------------------------------------------------
	def rng(self, *key):
		return random.Random(":".join(map(str, (self.seed, self.profile_name, *key))))

	def acc(self, name):
		full = f"{name} - {ABBR}"
		if not self.frappe.db.exists("Account", full):
			raise SystemExit(f"Account not found: {full}")
		return full

	def wh(self, name):
		return f"{name} - {ABBR}"

	def ensure(self, doctype, name, **values):
		if not self.frappe.db.exists(doctype, name):
			self.frappe.get_doc({"doctype": doctype, **values}).insert()

	def load_state(self):
		if self.state_path.exists():
			return json.loads(self.state_path.read_text())
		return {"last_day": None, "pending": [], "invoices": 0}

	def save_state(self, state):
		tmp = self.state_path.with_suffix(".tmp")
		tmp.write_text(json.dumps(state, ensure_ascii=False))
		os.replace(tmp, self.state_path)

	def flush_timings(self):
		with self.timings_path.open("a") as f:
			f.writelines(json.dumps(t) + "\n" for t in self.timings)
		self.timings = []

	def post(self, doc):
		started = time.perf_counter()
		doc.insert()
		doc.submit()
		self.timings.append({"dt": doc.doctype, "s": round(time.perf_counter() - started, 4)})
		return doc

	def check_site(self):
		companies = self.frappe.get_all("Company", pluck="name")
		if companies and companies != [COMPANY]:
			raise SystemExit(f"Refusing to touch {self.site}: it holds other companies: {companies}")
		return companies

	# setup -------------------------------------------------------------------
	def setup(self):
		frappe = self.frappe
		if not self.check_site():
			self.run_wizard()
		self.ensure_fiscal_years()
		self.ensure_groups()
		rng = self.rng("masters")
		self.ensure_customers(rng)
		self.ensure_suppliers(rng)
		self.ensure_items(rng)
		frappe.db.commit()
		self.post_opening()
		frappe.db.commit()
		self.flush_timings()
		print("setup done:", {d: frappe.db.count(d) for d in ("Customer", "Supplier", "Item", "Item Price", "Warehouse", "Account")})

	def run_wizard(self):
		from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

		year = self.end.year
		result = setup_complete(
			{
				"language": "English",
				"country": "Vietnam",
				"timezone": "Asia/Ho_Chi_Minh",
				"time_zone": "Asia/Ho_Chi_Minh",
				"currency": CURRENCY,
				"company_name": COMPANY,
				"company_abbr": ABBR,
				"chart_of_accounts": "Standard",
				"fy_start_date": f"{year}-01-01",
				"fy_end_date": f"{year}-12-31",
				"bank_account": BANK_ACCOUNT_NAME,
			}
		)
		print("wizard:", result)
		self.frappe.db.commit()
		if not self.frappe.db.exists("Company", COMPANY):
			raise SystemExit("Setup wizard did not create the company; see the output above.")

	def ensure_fiscal_years(self):
		for year in range(self.opening_date.year, self.end.year + 1):
			if not self.frappe.db.exists("Fiscal Year", str(year)):
				self.frappe.get_doc(
					{"doctype": "Fiscal Year", "year": str(year), "year_start_date": f"{year}-01-01", "year_end_date": f"{year}-12-31"}
				).insert()

	def ensure_groups(self):
		for name in TERRITORIES:
			self.ensure("Territory", name, territory_name=name, parent_territory="All Territories")
		for name in CUSTOMER_GROUPS:
			self.ensure("Customer Group", name, customer_group_name=name, parent_customer_group="All Customer Groups")
		for name in SUPPLIER_GROUPS:
			self.ensure("Supplier Group", name, supplier_group_name=name, parent_supplier_group="All Supplier Groups")
		for name in CATALOG:
			self.ensure("Item Group", name, item_group_name=name, parent_item_group="All Item Groups")
		for name in WAREHOUSES:
			self.ensure("Warehouse", self.wh(name), warehouse_name=name, company=COMPANY, parent_warehouse=self.wh("All Warehouses"))
		for name, days in TERMS.items():
			self.ensure("Payment Term", name, payment_term_name=name, invoice_portion=100, due_date_based_on="Day(s) after invoice date", credit_days=days)
			self.ensure(
				"Payment Terms Template",
				name,
				template_name=name,
				terms=[{"payment_term": name, "invoice_portion": 100, "due_date_based_on": "Day(s) after invoice date", "credit_days": days}],
			)

	def party_name(self, prefixes, index):
		brand = BRANDS[index % len(BRANDS)]
		prefix = prefixes[index % len(prefixes)]
		cycle = index // math.lcm(len(BRANDS), len(prefixes))
		return f"{prefix} {brand}" + (f" {cycle + 1}" if cycle else "")

	def ensure_customers(self, rng):
		for i in range(self.profile["customers"]):
			name = self.party_name(CUSTOMER_PREFIX, i)
			self.ensure(
				"Customer",
				name,
				customer_name=name,
				customer_type="Company",
				customer_group=rng.choice(CUSTOMER_GROUPS),
				territory=rng.choice(TERRITORIES),
				payment_terms=rng.choices(list(TERMS), weights=[1, 3, 4, 2])[0],
			)

	def ensure_suppliers(self, rng):
		for i in range(self.profile["suppliers"]):
			name = self.party_name(SUPPLIER_PREFIX, i)
			self.ensure(
				"Supplier",
				name,
				supplier_name=name,
				supplier_type="Company",
				supplier_group=rng.choice(SUPPLIER_GROUPS),
				payment_terms=rng.choices(list(TERMS), weights=[1, 3, 4, 2])[0],
			)

	def ensure_items(self, rng):
		products = [(group, product) for group, names in CATALOG.items() for product in names]
		for i in range(self.profile["items"]):
			code = f"SP-{i + 1:05d}"
			group, product = products[i % len(products)]
			variant = VARIANTS[(i // len(products)) % len(VARIANTS)]
			low, high = PRICE_RANGE[group]
			buy = round(rng.uniform(low, high), -3)
			sell = round(buy * rng.uniform(1.3, 1.8), -3)
			if self.frappe.db.exists("Item", code):
				continue
			self.frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": code,
					"item_name": f"{product} {variant}",
					"item_group": group,
					"stock_uom": "Nos",
					"is_stock_item": 1,
					"valuation_rate": buy,
				}
			).insert()
			for price_list, rate, flag in (("Standard Buying", buy, "buying"), ("Standard Selling", sell, "selling")):
				self.frappe.get_doc(
					{"doctype": "Item Price", "item_code": code, "price_list": price_list, "price_list_rate": rate, "currency": CURRENCY, flag: 1}
				).insert()

	def post_opening(self):
		frappe = self.frappe
		if frappe.db.exists("Stock Reconciliation", {"purpose": "Opening Stock", "docstatus": 1}):
			return
		rng = self.rng("opening")
		items = frappe.get_all("Item", fields=["name", "valuation_rate"], order_by="name")
		rows = [
			{"item_code": item.name, "warehouse": self.wh(w), "qty": rng.randint(60, 140), "valuation_rate": item.valuation_rate}
			for item in items
			for w in WAREHOUSES
		]
		stock_value = sum(r["qty"] * r["valuation_rate"] for r in rows)
		temp = self.acc("Temporary Opening")
		# Stock Reconciliation.submit() goes to a background queue above 100 rows.
		for i in range(0, len(rows), 100):
			doc = frappe.new_doc("Stock Reconciliation")
			doc.update(
				{
					"company": COMPANY,
					"purpose": "Opening Stock",
					"set_posting_time": 1,
					"posting_date": self.opening_date,
					"posting_time": "07:00:00",
					"expense_account": temp,
					"cost_center": f"Main - {ABBR}",
				}
			)
			for row in rows[i : i + 100]:
				doc.append("items", row)
			self.post(doc)
		cash = stock_value * 0.6
		je = frappe.new_doc("Journal Entry")
		je.update({"voucher_type": "Opening Entry", "company": COMPANY, "posting_date": self.opening_date, "is_opening": "Yes", "user_remark": "Vốn góp đầu kỳ (dữ liệu giả lập)"})
		je.append("accounts", {"account": self.acc(BANK_ACCOUNT_NAME), "debit_in_account_currency": cash})
		je.append("accounts", {"account": temp, "debit_in_account_currency": stock_value})
		je.append("accounts", {"account": self.acc("Capital Stock"), "credit_in_account_currency": cash + stock_value})
		self.post(je)
		booked = frappe.db.sql(
			"select coalesce(sum(stock_value_difference), 0) from `tabStock Ledger Entry` where voucher_type='Stock Reconciliation' and is_cancelled=0"
		)[0][0]
		if abs(float(booked) - stock_value) > 1:
			raise SystemExit(f"Opening stock not booked: ledger={booked} expected={stock_value}")

	# reset -------------------------------------------------------------------
	def reset(self):
		"""Delete this company's transactions and the seed checkpoints; masters stay."""
		from frappe.utils.background_jobs import get_queue, get_queue_list

		frappe = self.frappe
		if self.check_site() != [COMPANY]:
			raise SystemExit("Nothing to reset: the seed company does not exist here.")
		for queue_name in get_queue_list():
			queue = get_queue(queue_name)
			for job in queue.get_jobs():
				job_args = job.kwargs.get("kwargs", {})
				if job.kwargs.get("site") == self.site and job_args.get("__doctype") == "Stock Reconciliation":
					job.delete()
					print("removed queued job", job.id)
		record = frappe.new_doc("Transaction Deletion Record")
		record.company = COMPANY
		record.process_in_single_transaction = True
		record.save(ignore_permissions=True)
		record.generate_to_delete_list()
		record.reload()
		record.submit()
		record.start_deletion_tasks()
		self.close_deletion_record(record.name)
		frappe.db.commit()
		for path in self.out.glob("*"):
			path.unlink()
		print("reset done:", {d: frappe.db.count(d) for d in ("Sales Invoice", "Purchase Invoice", "Stock Reconciliation", "Journal Entry", "GL Entry", "Stock Ledger Entry", "Bin", "Customer", "Item")})

	def close_deletion_record(self, name):
		"""A single-transaction deletion can finish with the status still Running,
		which keeps its Redis flags set and blocks every write to those doctypes."""
		record = self.frappe.get_doc("Transaction Deletion Record", name)
		pending = [row.doctype_name for row in record.doctypes if not row.done]
		if pending:
			raise SystemExit(f"{name}: deletion incomplete, pending: {pending}; error: {record.error_log}")
		record.db_set("status", "Completed")
		record.db_set("delete_transactions_status", "Completed")
		record._clear_deletion_cache()

	# generate ----------------------------------------------------------------
	def daily_counts(self, total):
		days = [self.start + timedelta(days=i) for i in range((self.end - self.start).days + 1)]
		weights = [MONTH_WEIGHT[d.month] * WEEKDAY_WEIGHT[d.weekday()] for d in days]
		scale = total / sum(weights)
		raw = [w * scale for w in weights]
		counts = [int(r) for r in raw]
		remainder = sorted(range(len(days)), key=lambda i: (raw[i] - counts[i], -i), reverse=True)
		for i in remainder[: total - sum(counts)]:
			counts[i] += 1
		return dict(zip(days, counts, strict=True))

	def load_refs(self):
		frappe = self.frappe
		self.customers = frappe.get_all("Customer", pluck="name", order_by="name")
		self.suppliers = frappe.get_all("Supplier", pluck="name", order_by="name")
		self.items = frappe.get_all("Item", pluck="name", order_by="name")
		if not self.customers or not self.items:
			raise SystemExit("Run the setup command first.")
		prices = frappe.get_all("Item Price", fields=["item_code", "price_list", "price_list_rate"])
		self.sell = {p.item_code: p.price_list_rate for p in prices if p.price_list == "Standard Selling"}
		self.buy = {p.item_code: p.price_list_rate for p in prices if p.price_list == "Standard Buying"}
		weight_rng = self.rng("weights")
		self.customer_w = [weight_rng.paretovariate(1.3) for _ in self.customers]
		self.supplier_w = [weight_rng.paretovariate(1.5) for _ in self.suppliers]
		self.item_w = [weight_rng.paretovariate(1.5) for _ in self.items]
		self.bank = self.acc(BANK_ACCOUNT_NAME)
		self.warehouses = [self.wh(w) for w in WAREHOUSES]
		self.stock = {(b.item_code, b.warehouse): b.actual_qty for b in frappe.get_all("Bin", fields=["item_code", "warehouse", "actual_qty"])}
		from erpnext.controllers.accounts_controller import get_taxes_and_charges

		self.sales_taxes = get_taxes_and_charges("Sales Taxes and Charges Template", f"Vietnam Tax - {ABBR}")
		self.purchase_taxes = get_taxes_and_charges("Purchase Taxes and Charges Template", f"Vietnam Tax - {ABBR}")

	def add_taxes(self, doc, taxes, template):
		doc.taxes_and_charges = template
		for tax in taxes:
			doc.append("taxes", dict(tax))

	def tick(self):
		self.clock += 1
		seconds = min(8 * 3600 + self.clock, 86399)
		return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"

	def date_ledger_doc(self, doc, day):
		doc.set_posting_time = 1
		doc.posting_date = day
		doc.posting_time = self.tick()

	def make_sale(self, rng, day):
		from erpnext.selling.doctype.sales_order.mapper import make_delivery_note
		from erpnext.stock.doctype.delivery_note.mapper import make_sales_invoice

		warehouse = rng.choice(self.warehouses)
		lines = {}
		for code in rng.choices(self.items, weights=self.item_w, k=rng.randint(1, 5)):
			available = int(self.stock.get((code, warehouse), 0))
			qty = min(rng.randint(1, 20), available)
			if qty > 0 and code not in lines:
				lines[code] = qty
		if not lines:
			return None
		customer = rng.choices(self.customers, weights=self.customer_w)[0]
		so_date = max(day - timedelta(days=rng.randint(0, 5)), self.start)
		so = self.frappe.new_doc("Sales Order")
		so.update({"customer": customer, "company": COMPANY, "currency": CURRENCY, "selling_price_list": "Standard Selling", "transaction_date": so_date, "delivery_date": day, "set_warehouse": warehouse})
		for code, qty in lines.items():
			so.append("items", {"item_code": code, "qty": qty, "rate": self.sell[code], "warehouse": warehouse, "delivery_date": day})
		self.add_taxes(so, self.sales_taxes, f"Vietnam Tax - {ABBR}")
		self.post(so)
		dn = make_delivery_note(so.name)
		self.date_ledger_doc(dn, day)
		self.post(dn)
		for code, qty in lines.items():
			self.stock[(code, warehouse)] -= qty
		si = make_sales_invoice(dn.name)
		self.date_ledger_doc(si, day)
		si.payment_schedule = []
		si.due_date = None
		self.post(si)
		if rng.random() < 0.82:
			days = self.frappe.db.get_value("Sales Invoice", si.name, "due_date") - day
			return {"dt": "Sales Invoice", "name": si.name, "date": str(day + timedelta(days=max(days.days + rng.randint(-5, 12), 0)))}
		return {}

	def make_purchase(self, rng, day):
		from erpnext.buying.doctype.purchase_order.mapper import make_purchase_receipt
		from erpnext.stock.doctype.purchase_receipt.mapper import make_purchase_invoice

		warehouse = rng.choice(self.warehouses)
		candidates = rng.choices(self.items, weights=self.item_w, k=24)
		candidates.sort(key=lambda code: self.stock.get((code, warehouse), 0))
		lines = {code: rng.randint(10, 40) for code in dict.fromkeys(candidates[: rng.randint(3, 6)])}
		supplier = rng.choices(self.suppliers, weights=self.supplier_w)[0]
		po_date = max(day - timedelta(days=rng.randint(2, 10)), self.start)
		po = self.frappe.new_doc("Purchase Order")
		po.update({"supplier": supplier, "company": COMPANY, "currency": CURRENCY, "buying_price_list": "Standard Buying", "transaction_date": po_date, "schedule_date": day, "set_warehouse": warehouse})
		for code, qty in lines.items():
			po.append("items", {"item_code": code, "qty": qty, "rate": self.buy[code], "warehouse": warehouse, "schedule_date": day})
		self.add_taxes(po, self.purchase_taxes, f"Vietnam Tax - {ABBR}")
		self.post(po)
		pr = make_purchase_receipt(po.name)
		self.date_ledger_doc(pr, day)
		self.post(pr)
		for code, qty in lines.items():
			self.stock[(code, warehouse)] = self.stock.get((code, warehouse), 0) + qty
		pi = make_purchase_invoice(pr.name)
		self.date_ledger_doc(pi, day)
		pi.bill_no = f"NCC-{pr.name}"
		pi.bill_date = day
		pi.payment_schedule = []
		pi.due_date = None
		self.post(pi)
		if rng.random() < 0.9:
			days = self.frappe.db.get_value("Purchase Invoice", pi.name, "due_date") - day
			return {"dt": "Purchase Invoice", "name": pi.name, "date": str(day + timedelta(days=max(days.days + rng.randint(-3, 7), 0)))}
		return {}

	def make_payment(self, entry, day):
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry(entry["dt"], entry["name"], bank_account=self.bank)
		pe.posting_date = day
		pe.reference_no = f"UNC-{entry['name']}"
		pe.reference_date = day
		self.post(pe)

	def make_month_expenses(self, rng, day):
		frappe = self.frappe
		first = day.replace(day=1)
		revenue = frappe.db.sql(
			"select coalesce(sum(base_net_total), 0) from `tabSales Invoice` where docstatus=1 and company=%s and posting_date between %s and %s",
			(COMPANY, first, day),
		)[0][0]
		if not revenue:
			return
		je = frappe.new_doc("Journal Entry")
		je.update({"voucher_type": "Journal Entry", "company": COMPANY, "posting_date": day, "user_remark": f"Chi phí vận hành tháng {day.month}/{day.year}"})
		total = 0
		for name, share in EXPENSES.items():
			amount = round(float(revenue) * share * rng.uniform(0.9, 1.1), -3)
			total += amount
			je.append("accounts", {"account": self.acc(name), "debit_in_account_currency": amount, "cost_center": f"Main - {ABBR}"})
		je.append("accounts", {"account": self.bank, "credit_in_account_currency": total})
		je.cheque_no = f"CP-{day:%Y%m}"
		je.cheque_date = day
		self.post(je)

	def generate(self, max_invoices):
		frappe = self.frappe
		self.check_site()
		self.load_refs()
		state = self.load_state()
		sales_counts = self.daily_counts(self.profile["sales"])
		purchase_counts = self.daily_counts(self.profile["purchases"])
		day = date.fromisoformat(state["last_day"]) + timedelta(days=1) if state["last_day"] else self.start
		run_start = time.perf_counter()
		run_invoices = 0
		while day <= self.end:
			if max_invoices is not None and run_invoices >= max_invoices:
				break
			rng = self.rng("day", day)
			self.clock = 0
			try:
				due = [p for p in state["pending"] if p["date"] <= str(day)]
				pending = [p for p in state["pending"] if p["date"] > str(day)]
				added = 0
				for entry in due:
					self.make_payment(entry, day)
				jobs = ["p"] * purchase_counts[day] + ["s"] * sales_counts[day]
				for job in jobs:
					entry = self.make_purchase(rng, day) if job == "p" else self.make_sale(rng, day)
					if entry is None:
						continue
					added += 1
					if entry:
						pending.append(entry)
				if (day + timedelta(days=1)).month != day.month:
					self.make_month_expenses(rng, day)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				print(f"FAILED on {day}; everything up to the previous day is committed.")
				raise
			state.update({"last_day": str(day), "pending": pending, "invoices": state["invoices"] + added})
			self.save_state(state)
			self.flush_timings()
			run_invoices += added
			elapsed = time.perf_counter() - run_start
			print(f"{day} invoices={state['invoices']} run_rate={run_invoices / max(elapsed, 1e-6) * 60:.1f}/min", flush=True)
			day += timedelta(days=1)
		print("complete" if day > self.end else f"stopped after {state['last_day']}", "invoices:", state["invoices"])

	# finalize ----------------------------------------------------------------
	def finalize(self):
		"""Add records that are derived from the finished year of transactions."""
		self.check_site()
		self.make_budgets()
		self.make_bank_transactions()
		self.frappe.db.commit()
		self.flush_timings()
		print("finalize done:", {d: self.frappe.db.count(d) for d in ("Budget", "Bank Transaction")})

	def make_budgets(self):
		frappe = self.frappe
		year = str(self.end.year)
		rng = self.rng("budget")
		for name in EXPENSES:
			account = self.acc(name)
			if frappe.db.exists("Budget", {"account": account, "from_fiscal_year": year, "docstatus": 1}):
				continue
			actual = frappe.db.sql(
				"select coalesce(sum(debit - credit), 0) from `tabGL Entry` where is_cancelled=0 and account=%s and fiscal_year=%s",
				(account, year),
			)[0][0]
			if not actual:
				continue
			budget = frappe.new_doc("Budget")
			budget.update(
				{
					"budget_against": "Cost Center",
					"company": COMPANY,
					"cost_center": f"Main - {ABBR}",
					"account": account,
					"budget_amount": round(float(actual) * rng.uniform(1.03, 1.25), -3),
					"from_fiscal_year": year,
					"to_fiscal_year": year,
					"distribution_frequency": "Monthly",
					"distribute_equally": 1,
					"applicable_on_booking_actual_expenses": 1,
					"action_if_annual_budget_exceeded": "Warn",
					"action_if_accumulated_monthly_budget_exceeded": "Ignore",
				}
			)
			self.post(budget)

	def make_bank_transactions(self):
		frappe = self.frappe
		if frappe.db.count("Bank Transaction"):
			return
		self.ensure("Bank", "Vietcombank", bank_name="Vietcombank")
		name = f"{BANK_ACCOUNT_NAME} - Vietcombank"
		self.ensure(
			"Bank Account",
			name,
			account_name=BANK_ACCOUNT_NAME,
			bank="Vietcombank",
			account=self.acc(BANK_ACCOUNT_NAME),
			company=COMPANY,
			is_company_account=1,
		)
		since = self.end - timedelta(days=30)
		payments = frappe.get_all(
			"Payment Entry",
			filters={"docstatus": 1, "posting_date": [">=", since]},
			fields=["name", "posting_date", "payment_type", "paid_amount", "reference_no", "party_name"],
			order_by="posting_date, name",
		)
		for payment in payments:
			incoming = payment.payment_type == "Receive"
			self.post(
				frappe.get_doc(
					{
						"doctype": "Bank Transaction",
						"date": payment.posting_date,
						"bank_account": name,
						"company": COMPANY,
						"currency": CURRENCY,
						"deposit": payment.paid_amount if incoming else 0,
						"withdrawal": 0 if incoming else payment.paid_amount,
						"description": f"{payment.reference_no} {payment.party_name}",
						"reference_number": payment.reference_no,
					}
				)
			)

	# report ------------------------------------------------------------------
	def report(self):
		from frappe.desk.query_report import run as run_report

		frappe = self.frappe
		self.check_site()
		result = {"profile": self.profile_name, "counts": {}, "checks": {}, "write_seconds": {}, "reports": {}}
		for dt in ("Customer", "Supplier", "Item", "Sales Order", "Delivery Note", "Sales Invoice", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry", "Journal Entry", "Budget", "Bank Transaction", "GL Entry", "Stock Ledger Entry", "Payment Ledger Entry"):
			result["counts"][dt] = frappe.db.count(dt)

		one = lambda q, *a: frappe.db.sql(q, a)[0][0]
		dr, cr = frappe.db.sql("select coalesce(sum(debit),0), coalesce(sum(credit),0) from `tabGL Entry` where is_cancelled=0")[0]
		stock_sle = one("select coalesce(sum(stock_value_difference),0) from `tabStock Ledger Entry` where is_cancelled=0")
		stock_gl = one(
			"""select coalesce(sum(g.debit-g.credit),0) from `tabGL Entry` g join `tabAccount` a on a.name=g.account
			where g.is_cancelled=0 and a.account_type='Stock'"""
		)
		ar = one("select coalesce(sum(outstanding_amount),0) from `tabSales Invoice` where docstatus=1")
		ar_gl = one("select coalesce(sum(debit-credit),0) from `tabGL Entry` where is_cancelled=0 and account=%s", self.acc("Debtors"))
		bank = one("select coalesce(sum(debit-credit),0) from `tabGL Entry` where is_cancelled=0 and account=%s", self.acc(BANK_ACCOUNT_NAME))
		result["checks"] = {
			"gl_debit": float(dr),
			"gl_credit": float(cr),
			"gl_diff": round(float(dr - cr), 2),
			"stock_value_sle": float(stock_sle),
			"stock_value_gl": float(stock_gl),
			"stock_diff": round(float(stock_sle - stock_gl), 2),
			"negative_bins": one("select count(*) from `tabBin` where actual_qty < 0"),
			"sales_outstanding": float(ar),
			"debtors_gl": float(ar_gl),
			"ar_diff": round(float(ar - ar_gl), 2),
			"overdue_sales_invoices": frappe.db.count("Sales Invoice", {"docstatus": 1, "status": "Overdue"}),
			"bank_balance": float(bank),
			"revenue": float(one("select coalesce(sum(base_net_total),0) from `tabSales Invoice` where docstatus=1")),
		}

		if self.timings_path.exists():
			by_dt = {}
			for line in self.timings_path.read_text().splitlines():
				row = json.loads(line)
				by_dt.setdefault(row["dt"], []).append(row["s"])
			for dt, values in sorted(by_dt.items()):
				values.sort()
				result["write_seconds"][dt] = {"n": len(values), "avg": round(statistics.mean(values), 3), "p95": round(values[int(len(values) * 0.95) - 1], 3), "total": round(sum(values), 1)}

		from_date, to_date, year = str(self.start), str(self.end), str(self.end.year)
		period = {"company": COMPANY, "filter_based_on": "Date Range", "period_start_date": from_date, "period_end_date": to_date, "periodicity": "Monthly", "cost_center": [], "project": [], "presentation_currency": CURRENCY}
		ageing = {"company": COMPANY, "report_date": to_date, "ageing_based_on": "Due Date", "calculate_ageing_with": "Report Date", "range": "30, 60, 90, 120"}
		reports = {
			"Trial Balance": {"company": COMPANY, "fiscal_year": year, "from_date": f"{year}-01-01", "to_date": to_date, "presentation_currency": CURRENCY},
			"General Ledger": {"company": COMPANY, "from_date": from_date, "to_date": to_date, "group_by": "Group by Voucher (Consolidated)", "presentation_currency": CURRENCY},
			"Balance Sheet": {**period, "selected_view": "Report", "accumulated_values": 1},
			"Profit and Loss Statement": {**period, "selected_view": "Report"},
			"Accounts Receivable": {**ageing, "party_type": "Customer"},
			"Accounts Payable": {**ageing, "party_type": "Supplier"},
			"Stock Balance": {"company": COMPANY, "from_date": from_date, "to_date": to_date, "valuation_field_type": "Currency"},
			"Stock Ledger": {"company": COMPANY, "from_date": from_date, "to_date": to_date, "valuation_field_type": "Currency"},
			"Gross Profit": {"company": COMPANY, "from_date": from_date, "to_date": to_date, "group_by": "Item Code"},
			"Budget Variance Report": {"company": COMPANY, "from_fiscal_year": year, "to_fiscal_year": year, "period": "Yearly", "budget_against": "Cost Center"},
		}
		for name, filters in reports.items():
			started = time.perf_counter()
			try:
				data = run_report(name, filters=filters, ignore_prepared_report=True)
				result["reports"][name] = {"seconds": round(time.perf_counter() - started, 3), "rows": len(data.get("result") or [])}
			except Exception as exc:
				frappe.db.rollback()
				result["reports"][name] = {"error": f"{type(exc).__name__}: {exc}"[:300]}

		path = self.out / f"report-{self.profile_name}.json"
		path.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str))
		print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
		print("saved:", path)


def main():
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("--site", required=True)
	parser.add_argument("--profile", choices=PROFILES, default="demo")
	parser.add_argument("--seed", type=int, default=20261105)
	parser.add_argument("--end", type=date.fromisoformat, default=date.today() - timedelta(days=1), help="last posting date (default: yesterday)")
	parser.add_argument("command", choices=["setup", "generate", "finalize", "report", "reset"])
	parser.add_argument("--max-invoices", type=int, help="generate: stop after the day that reaches this many invoices in this run")
	args = parser.parse_args()

	os.chdir(Path(__file__).resolve().parents[2] / "sites")
	import frappe

	frappe.init(args.site)
	frappe.connect()
	frappe.set_user("Administrator")
	frappe.flags.mute_emails = True
	try:
		seeder = Seeder(args.site, args.profile, args.seed, args.end)
		if args.command == "generate":
			seeder.generate(args.max_invoices)
		else:
			getattr(seeder, args.command)()
	finally:
		frappe.destroy()


if __name__ == "__main__":
	main()
