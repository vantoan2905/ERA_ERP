# Module Regional

Module `regional` chứa phần riêng theo quốc gia. Code cắm vào hệ thống qua ba đường: `doc_events` và `regional_overrides` trong `hooks.py`, hàm `setup` được `Company.install_country_fixtures` gọi động theo tên nước, và các report. Có nghiệp vụ thực sự ở Italy (e-invoice) và UAE (reverse charge, VAT 201); South Africa và United States chủ yếu là custom field cộng một report.

## Phạm vi

Đọc được 5 doctype trong `regional/doctype/`.

| Gói quốc gia | File chính | Nội dung | Sơ đồ |
|---|---|---|---|
| `italy` | `utils.py`, `setup.py`, `e-invoice.xml`, doctype `Import Supplier Invoice`, report `electronic_invoice_register` | Kiểm tra, sinh, xuất XML e-invoice, nhập hóa đơn nhà cung cấp | Class. 2 sequence e-invoice, 1 sequence import |
| `united_arab_emirates` | `utils.py`, `setup.py`, doctype `UAE VAT Settings`, report `uae_vat_201` | Reverse charge trên Purchase Invoice, báo cáo VAT 201 | Class. 2 sequence |
| `south_africa` | `setup.py`, doctype `South Africa VAT Settings`, report `vat_audit_report` | Custom field, báo cáo VAT Audit | Class. 1 sequence |
| `united_states` | `setup.py`, report `irs_1099`, print format `irs_1099_form` | Custom field, báo cáo 1099 | 1 sequence |
| `australia` | `setup.py` | Chỉ tạo Tax Rule trong `update_regional_tax_settings` | Gộp vào sequence fixture |
| `turkey` | `setup.py` | `setup` chỉ có `pass`, không có nghiệp vụ | Không vẽ |

Phần không theo gói quốc gia: `Lower Deduction Certificate` (class), `address_template/setup.py`, `check_deletion_permission` và `rename_vat_settings` trong `regional/__init__.py`.

## Class diagram

```mermaid
classDiagram
    class ImportSupplierInvoice {
        +string company
        +string item_code
        +string supplier_group
        +string tax_account
        +string zip_file
        +string status
        +string invoice_series
        +process_file_data()
        +import_xml_data()
        +import_zip_file()
        +prepare_data_for_import()
        +create_invoice_from_file()
    }
    class UAEVATSettings {
        +string company
        +validate()
        +validate_company_region()
        +validate_accounts()
    }
    class UAEVATAccount {
        +string account
    }
    class SouthAfricaVATSettings {
        +string company
        +validate()
        +validate_company_unchanged()
        +validate_accounts()
    }
    class SouthAfricaVATAccount
    class LowerDeductionCertificate {
        +string certificate_no
        +string supplier
        +string pan_no
        +date valid_from
        +date valid_upto
        +float rate
        +float certificate_limit
        +validate()
        +validate_changes_after_use()
        +is_used()
    }
    class VATAuditReport {
        +run()
        +get_sa_vat_accounts()
        +get_invoice_data()
        +get_items_based_on_tax_rate()
    }
    class Company
    class Supplier
    ImportSupplierInvoice --> Company : company
    UAEVATSettings --> Company : company
    UAEVATSettings *-- UAEVATAccount : uae_vat_accounts
    SouthAfricaVATSettings --> Company : company
    SouthAfricaVATSettings *-- SouthAfricaVATAccount : vat_accounts
    LowerDeductionCertificate --> Company : company
    LowerDeductionCertificate --> Supplier : supplier
    VATAuditReport ..> SouthAfricaVATAccount : doc theo company
```

`VATAuditReport` là class Python của report, không phải doctype. `SouthAfricaVATAccount` nằm ở `accounts/doctype/`.

## Sequence diagram

### Cài fixture theo quốc gia

Khi Company đổi hoặc nhận nước lần đầu, controller tìm hàm `setup` theo tên module rút từ `country`. Nước không có gói thì `ImportError` được bỏ qua.

```mermaid
sequenceDiagram
    participant Co as Company
    participant Reg as regional.country.setup
    participant CF as Custom Field
    participant Tax as taxes_setup.py
    participant TR as Tax Rule
    Co->>Reg: install_country_fixtures: setup(company, False)
    alt Italy
        Reg->>CF: make_custom_fields, setup_report, add_permissions
    else United Arab Emirates
        Reg->>CF: make_custom_fields, add_print_formats, add_custom_roles_for_reports, add_permissions
    else South Africa
        Reg->>CF: make_custom_fields, add_permissions
    else United States
        Reg->>CF: chỉ khi là Company US đầu tiên: make_custom_fields, add_print_formats
    else không có gói
        Reg-->>Co: ImportError, bỏ qua
    end
    Co->>Tax: create_default_tax_template: setup_taxes_and_charges
    Tax->>Tax: from_detailed_data
    Tax->>Reg: update_regional_tax_settings(country, company)
    opt Australia
        Reg->>TR: make_records Tax Rule
    end
```

Nguồn: [company.py:995](../../apps/erpnext/erpnext/setup/doctype/company/company.py#L995), [taxes_setup.py:120](../../apps/erpnext/erpnext/setup/setup_wizard/operations/taxes_setup.py#L120)

### Italy: kiểm tra và sinh e-invoice

`validate_regional` là hàm rỗng có `allow_regional`; với Italy, hook `regional_overrides` thay bằng `sales_invoice_validate`. Khi submit, hook `doc_events` sinh file XML và đính vào Sales Invoice; khi cancel thì xóa file.

```mermaid
sequenceDiagram
    actor User
    participant SI as Sales Invoice
    participant AC as AccountsController
    participant IT as italy/utils.py
    participant Tpl as e-invoice.xml
    participant File as File
    User->>SI: save()
    SI->>AC: validate: validate_regional(self)
    AC->>IT: allow_regional: sales_invoice_validate(doc)
    IT->>IT: validate_address, kiểm tra fiscal_regime, tax_id, fiscal_code, thuế
    User->>SI: submit()
    SI->>IT: on_submit: sales_invoice_on_submit(doc, method)
    opt công ty Italy và không phải opening
        IT->>IT: kiểm tra mode_of_payment và mã trong payment_schedule
        IT->>IT: prepare_and_attach_invoice: get_progressive_name_and_number
        IT->>IT: prepare_invoice, get_invoice_summary
        IT->>Tpl: render_template(doc, item_meta)
        IT->>File: save file XML private
    end
    User->>SI: cancel()
    SI->>IT: on_cancel: sales_invoice_on_cancel(doc, method)
    opt công ty Italy và không phải opening
        IT->>File: get_e_invoice_attachments, remove_file
    end
```

Nguồn: [utils.py:221](../../apps/erpnext/erpnext/regional/italy/utils.py#L221), [utils.py:321](../../apps/erpnext/erpnext/regional/italy/utils.py#L321), [accounts_controller.py:1996](../../apps/erpnext/erpnext/controllers/accounts_controller.py#L1996)

### Italy: xuất và sinh lại e-invoice

Report Electronic Invoice Register gọi API để tải zip các file XML đã đính kèm; `generate_single_invoice` thay file cũ bằng file mới nhưng giữ số progressive.

```mermaid
sequenceDiagram
    actor User
    participant Rep as electronic_invoice_register.js
    participant IT as italy/utils.py
    participant SI as Sales Invoice
    participant File as File
    User->>Rep: xuất e-invoice
    Rep->>IT: export_invoices(filters)
    IT->>SI: get_list(get_conditions(filters))
    IT->>File: get_e_invoice_attachments(invoices)
    IT->>IT: download_zip(attachments, zip_filename)
    IT-->>User: file zip
    User->>IT: generate_single_invoice(docname)
    IT->>SI: get_doc, has_permission
    IT->>IT: prepare_and_attach_invoice(doc, True)
    IT->>File: get_progressive_name_and_number: remove_file file cũ
    IT->>File: lưu file XML mới
    IT-->>User: file_url
```

Nguồn: [utils.py:34](../../apps/erpnext/erpnext/regional/italy/utils.py#L34), [utils.py:379](../../apps/erpnext/erpnext/regional/italy/utils.py#L379)

### Italy: Import Supplier Invoice

Người dùng đính kèm file zip XML; job nền tạo Supplier, Address và Purchase Invoice nháp cho từng hóa đơn. Mỗi hóa đơn có savepoint riêng, file `.p7m` đã ký không được hỗ trợ.

```mermaid
sequenceDiagram
    actor User
    participant ISI as Import Supplier Invoice
    participant Q as RQ long queue
    participant Sup as Supplier, Contact, Address
    participant PI as Purchase Invoice
    participant File as File
    User->>ISI: process_file_data()
    ISI->>ISI: status = Processing File Data
    ISI->>Q: enqueue_doc(import_xml_data)
    Q->>ISI: import_xml_data, import_zip_file
    loop mỗi file trong zip
        alt đuôi p7m hoặc đọc lỗi
            ISI->>ISI: log_signed_file hoặc log_unreadable_file
        else đọc được
            ISI->>ISI: prepare_data_for_import
            loop mỗi DatiGeneraliDocumento
                ISI->>ISI: savepoint, create_invoice_from_file
                ISI->>Sup: create_supplier, create_address
                ISI->>PI: validate_invoice_not_imported, create_purchase_invoice
                ISI->>File: attach_file_to_invoice
            end
        end
    end
    ISI->>ISI: status: File Import Completed, Partially Completed hoặc Error
    ISI-->>User: publish import_invoice_update
```

Nguồn: [import_supplier_invoice.py:194](../../apps/erpnext/erpnext/regional/doctype/import_supplier_invoice/import_supplier_invoice.py#L194), [import_supplier_invoice.py:133](../../apps/erpnext/erpnext/regional/doctype/import_supplier_invoice/import_supplier_invoice.py#L133)

### UAE: reverse charge trên Purchase Invoice

Khi `reverse_charge` là Y, thuế trên tài khoản VAT được trừ khỏi tổng phải trả lúc validate, còn lúc ghi sổ thì thêm dòng GL cho tài khoản VAT đó.

```mermaid
sequenceDiagram
    actor User
    participant PI as Purchase Invoice
    participant UAE as united_arab_emirates/utils.py
    participant VAT as UAE VAT Account
    participant GC as PurchaseInvoiceGLComposer
    participant GL as GL Entry
    User->>PI: save()
    PI->>UAE: validate: update_grand_total_for_rcm(doc, method)
    opt country UAE, có thuế, reverse_charge Y
        UAE->>VAT: get_tax_accounts(company)
        UAE->>UAE: trừ vat_tax khỏi tổng thuế
        UAE->>PI: update_totals: grand_total, in_words, set_payment_schedule
    end
    PI->>UAE: validate_returns(doc, method)
    User->>PI: submit()
    PI->>GC: get_gl_entries: compose()
    GC->>UAE: allow_regional: make_regional_gl_entries(gl_entries, doc)
    opt country UAE và reverse_charge Y
        UAE->>VAT: get_tax_accounts(company)
        loop mỗi dòng taxes Total hoặc Valuation and Total
            UAE->>UAE: make_gl_entry: credit nếu Add, debit nếu Deduct
        end
    end
    UAE-->>GC: gl_entries
    GC-->>PI: gl_entries đã gộp
    PI->>GL: make_gl_entries
```

Nguồn: [utils.py:91](../../apps/erpnext/erpnext/regional/united_arab_emirates/utils.py#L91), [utils.py:148](../../apps/erpnext/erpnext/regional/united_arab_emirates/utils.py#L148), [gl_composer.py:42](../../apps/erpnext/erpnext/accounts/doctype/purchase_invoice/services/gl_composer.py#L42)

### UAE: báo cáo VAT 201

Script report chỉ chạy cho công ty UAE, gom số liệu đầu ra theo Emirate và số liệu đầu vào theo từng ô của tờ khai.

```mermaid
sequenceDiagram
    actor User
    participant Rep as uae_vat_201.py
    participant SI as Sales Invoice
    participant PI as Purchase Invoice
    User->>Rep: execute(filters)
    Rep->>Rep: validate_company, validate_company_region
    Rep->>Rep: get_data: append_vat_on_sales
    Rep->>SI: standard_rated_expenses_emiratewise
    Rep->>SI: get_tourist_tax_return_total, get_zero_rated_total, get_exempt_total
    Rep->>PI: get_reverse_charge_total, get_reverse_charge_tax
    Rep->>Rep: append_vat_on_expenses
    Rep->>PI: get_standard_rated_expenses_total, get_reverse_charge_recoverable_total
    Rep-->>User: columns, data
```

Nguồn: [uae_vat_201.py:12](../../apps/erpnext/erpnext/regional/report/uae_vat_201/uae_vat_201.py#L12)

### South Africa: VAT Audit Report

Report lấy danh sách tài khoản VAT từ `South Africa VAT Settings` (đặt tên theo company), rồi xử lý lần lượt Purchase Invoice và Sales Invoice.

```mermaid
sequenceDiagram
    actor User
    participant Rep as VATAuditReport
    participant VAT as South Africa VAT Account
    participant Inv as Purchase Invoice, Sales Invoice
    User->>Rep: execute: run()
    Rep->>Rep: validate_company_region, has_permission
    Rep->>VAT: get_sa_vat_accounts
    alt chưa có tài khoản
        Rep-->>User: throw Please set VAT Accounts
    else có tài khoản
        loop mỗi doctype
            Rep->>Inv: get_invoice_data(doctype)
            opt có hóa đơn
                Rep->>Inv: get_invoice_items, get_items_based_on_tax_rate
                Rep->>Rep: get_data(doctype)
            end
        end
    end
    Rep-->>User: columns, data
```

Nguồn: [vat_audit_report.py:24](../../apps/erpnext/erpnext/regional/report/vat_audit_report/vat_audit_report.py#L24)

### United States: IRS 1099

Report cộng khoản đã trả cho Supplier có `irs_1099 = 1` trong một fiscal year, lấy từ GL Entry của phiếu thanh toán và Purchase Invoice đã trả ngay.

```mermaid
sequenceDiagram
    actor User
    participant Rep as irs_1099.py
    participant GL as GL Entry
    participant PI as Purchase Invoice
    participant Sup as Supplier
    User->>Rep: execute(filters)
    Rep->>Rep: has_permission, validate_company_region
    Rep->>GL: get_payments: is_payment_voucher
    Rep->>PI: get_payments: is_paid = 1, base_paid_amount
    Rep->>Rep: union_all
    Rep->>Sup: inner join, irs_1099 = 1, group by supplier
    Rep-->>User: columns, data
```

Nguồn: [irs_1099.py:22](../../apps/erpnext/erpnext/regional/report/irs_1099/irs_1099.py#L22), [irs_1099.py:67](../../apps/erpnext/erpnext/regional/report/irs_1099/irs_1099.py#L67)

## Giới hạn

- `hooks.py` có `regional_overrides` cho `France`, trỏ tới `erpnext.regional.france.utils.test_method`, nhưng thư mục `regional/france` không tồn tại trong cây mã này. Khóa override `erpnext.tests.test_regional.test_method` chỉ dùng cho `tests/test_regional.py`, và test đó chạy với country khác nên không chạm tới đường dẫn này.
- `Saudi Arabia` chỉ dùng lại `update_itemised_tax_data` của UAE qua hook, không có gói riêng. `check_deletion_permission` chỉ chặn với `Nepal`, cũng không có gói riêng.
- `update_itemised_tax_data` (Italy, UAE) chỉ gán `tax_rate`, `tax_amount`, `total_amount` lên từng dòng, được `controllers/taxes_and_totals.py` gọi khi dựng phần thuế chi tiết; không vẽ riêng.
- Override chọn theo `get_region()`, dựa trên `frappe.local.flags.company`. `validate_regional` và `update_itemised_tax_data` được bọc `temporary_flag("company", ...)`, còn lệnh gọi `make_regional_gl_entries` trong `PurchaseInvoiceGLComposer.compose` thì không, và grep không thấy nơi nào khác đặt cờ này trên đường gọi đó. Theo code, override GL của UAE vì thế chọn theo `frappe.flags.country` hoặc country của System Settings, không theo Company. Site có System Settings khác UAE thì dòng GL reverse charge có thể không được thêm dù Company ở UAE. Chưa chạy thử.
- `Lower Deduction Certificate` chỉ có validate, không gắn với gói quốc gia. Việc dùng nó nằm ở `accounts/doctype/tax_withholding_entry/`, xem tài liệu `accounts`.
- `uae_vat_201.py` và `vat_audit_report.py` chỉ đọc đến mức hàm và doctype được truy vấn, không đọc từng điều kiện lọc.
- Print format (`tax_invoice`, `detailed_tax_invoice`, `simplified_tax_invoice`, `purchase_einvoice`, `irs_1099_form`), `address_template/setup.py` (cập nhật Address Template từ file HTML, gọi trong `install_fixtures.install`) và `rename_vat_settings` (hook `Company.after_rename`) không vẽ.
- `italy/setup.py` phần lớn là khai báo custom field (`get_custom_fields`), chỉ đọc đầu và cuối.
