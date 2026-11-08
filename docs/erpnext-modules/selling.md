# Module Selling

Module `selling` quản lý khách hàng, báo giá, đơn bán và các chứng từ phụ trợ như Proforma Invoice, Installation Note, Product Bundle. Module nhận đầu vào từ `crm` (Lead, Prospect, Opportunity), đẩy luồng sang `stock` (Delivery Note, Packed Item, Stock Reservation Entry, Bin), `accounts` (Sales Invoice, GL Entry) và `buying` (Purchase Order cho drop ship). Blanket Order không nằm ở đây mà ở `manufacturing`, module này chỉ gọi tới.

## Phạm vi

Đọc được 20 doctype trong `selling/doctype/`. Mục "Sơ đồ" chỉ tới tiêu đề trong file này.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Khách hàng và hạn mức tín dụng | Customer, Customer Credit Limit, Sales Team, `customer/customer.py`, `customer/mapper.py` | Class: Khách hàng. Sequence: Lưu Customer, Kiểm tra hạn mức tín dụng |
| Báo giá | Quotation, Quotation Item, `quotation/quotation.py`, `quotation/mapper.py` | Class: Báo giá và đơn bán. Sequence: Submit Quotation, Tạo revision, Declare Lost, Hết hạn Quotation |
| Đơn bán | Sales Order, Sales Order Item, Delivery Schedule Item, `sales_order/sales_order.py`, `sales_order/mapper.py`, `sales_order/services/` | Class: Báo giá và đơn bán. Sequence: Quotation sang Sales Order, Submit Sales Order, Đổi trạng thái |
| Luồng sang chứng từ sau | `sales_order/mapper.py`, Delivery Note, Sales Invoice (ngoài module) | Sequence: Sales Order sang Delivery Note, Sales Order sang Sales Invoice, Sales Order sang Purchase Order |
| Chứng từ phụ trợ | Proforma Invoice, Installation Note, Product Bundle, Party Specific Item, Selling Settings | Class: Chứng từ phụ trợ. Sequence: Proforma Invoice |

## Class diagram

Class ngoài module (ví dụ `Opportunity`, `BlanketOrder`) chỉ để đích của quan hệ nên để trống. Controller cha chỉ ghi method.

### Khách hàng

```mermaid
classDiagram
    class TransactionBase
    class Customer {
        +string customer_name
        +string customer_type
        +string customer_group
        +string territory
        +string lead_name
        +string prospect_name
        +string opportunity_name
        +bool is_internal_customer
        +validate()
        +after_insert()
        +on_update()
        +update_lead_status()
        +link_lead_records()
        +link_address_and_contact()
        +create_primary_contact()
        +validate_credit_limit_on_change()
    }
    class CustomerCreditLimit {
        +string company
        +float credit_limit
        +float overdue_billing_threshold
        +bool bypass_credit_limit_check
    }
    class SalesTeam {
        +string sales_person
        +float allocated_percentage
        +float commission_rate
    }
    class SupplierNumberAtCustomer {
        +string company
        +string supplier_number
    }
    class Lead
    class Prospect
    class Opportunity
    TransactionBase <|-- Customer
    Customer *-- CustomerCreditLimit : credit_limits
    Customer *-- SalesTeam : sales_team
    Customer *-- SupplierNumberAtCustomer : supplier_numbers
    Customer --> Lead : lead_name
    Customer --> Prospect : prospect_name
    Customer --> Opportunity : opportunity_name
```

### Báo giá và đơn bán

`Quotation.party_name` là Dynamic Link theo `quotation_to`, sơ đồ chỉ vẽ trường hợp Customer.

```mermaid
classDiagram
    class StatusUpdater {
        +update_prevdoc_status()
        +update_qty()
        +validate_qty()
        +set_status()
    }
    class TransactionBase
    class AccountsController {
        +validate()
        +on_cancel()
        +ensure_supplier_is_not_blocked()
    }
    class StockController {
        +make_gl_entries()
        +make_sl_entries()
        +update_blanket_order()
    }
    class SellingController {
        +validate()
        +set_missing_values()
        +ensure_customer_is_not_blocked()
        +update_stock_ledger()
        +update_stock_reservation_entries()
    }
    class Quotation {
        +string quotation_to
        +string party_name
        +date valid_till
        +string status
        +bool is_active
        +string revision_of
        +bool is_latest_revision
        +string opportunity
        +validate()
        +on_submit()
        +on_cancel()
        +declare_enquiry_lost()
        +update_opportunity()
        +update_lead()
        +get_ordered_status()
        +validate_revision()
        +deactivate_other_versions()
        +update_latest_revision()
        +reactivate_latest_version()
    }
    class QuotationItem {
        +string item_code
        +float qty
        +float stock_qty
        +float rate
        +float ordered_qty
        +bool is_alternative
        +bool has_alternative_item
        +string prevdoc_docname
    }
    class SalesOrder {
        +string customer
        +date delivery_date
        +float per_delivered
        +float per_billed
        +string status
        +string delivery_status
        +string billing_status
        +bool reserve_stock
        +validate()
        +on_submit()
        +on_cancel()
        +check_credit_limit()
        +update_prevdoc_status()
        +update_status()
        +update_reserved_qty()
        +create_stock_reservation_entries()
    }
    class SalesOrderItem {
        +string item_code
        +float qty
        +float delivered_qty
        +float billed_amt
        +float ordered_qty
        +string prevdoc_docname
        +string quotation_item
        +string blanket_order
    }
    class DeliveryScheduleItem {
        +string sales_order
        +string sales_order_item
        +string item_code
        +date delivery_date
        +float qty
    }
    class SalesTeam {
        +string sales_person
        +float allocated_percentage
        +float commission_rate
    }
    class Customer
    class Opportunity
    class BlanketOrder
    StatusUpdater <|-- TransactionBase
    TransactionBase <|-- AccountsController
    AccountsController <|-- StockController
    StockController <|-- SellingController
    SellingController <|-- Quotation
    SellingController <|-- SalesOrder
    Quotation *-- QuotationItem : items
    SalesOrder *-- SalesOrderItem : items
    SalesOrder *-- SalesTeam : sales_team
    Quotation --> Customer : party_name
    Quotation --> Quotation : revision_of
    Quotation --> Opportunity : opportunity
    SalesOrder --> Customer : customer
    SalesOrderItem --> Quotation : prevdoc_docname
    SalesOrderItem --> BlanketOrder : blanket_order
    DeliveryScheduleItem --> SalesOrder : sales_order
```

### Chứng từ phụ trợ

```mermaid
classDiagram
    class TransactionBase
    class ProformaInvoice {
        +string sales_order
        +string customer
        +date proforma_date
        +string based_on
        +float grand_total
        +string status
        +validate()
        +before_submit()
        +on_submit()
        +on_cancel()
        +generate_and_attach_pdf()
        +render_pdf()
        +get_sales_order_copy()
    }
    class ProformaInvoiceItem {
        +string so_detail
        +string item_code
        +float qty
        +float rate
        +float amount
    }
    class InstallationNote {
        +string customer
        +string company
        +date inst_date
        +string status
        +validate()
        +on_submit()
        +on_cancel()
        +validate_serial_no()
    }
    class InstallationNoteItem {
        +string item_code
        +float qty
        +string prevdoc_docname
        +string prevdoc_detail_docname
    }
    class ProductBundle {
        +string new_item_code
        +string description
        +bool is_active
        +bool disabled
        +validate()
        +on_submit()
        +on_cancel()
        +on_update_after_submit()
        +make_active()
    }
    class ProductBundleItem {
        +string item_code
        +float qty
        +string uom
    }
    class PartySpecificItem {
        +string party_type
        +string party
        +string restrict_based_on
        +string based_on_value
        +validate()
    }
    class SellingSettings {
        +string cust_master_name
        +string so_required
        +string dn_required
        +bool allow_against_multiple_purchase_orders
        +on_update()
        +validate()
    }
    class SalesOrder
    class Customer
    ProformaInvoice *-- ProformaInvoiceItem : items
    ProformaInvoice --> SalesOrder : sales_order
    TransactionBase <|-- InstallationNote
    InstallationNote *-- InstallationNoteItem : items
    InstallationNote --> Customer : customer
    ProductBundle *-- ProductBundleItem : items
```

## Sequence diagram

### Lưu Customer và nối với Lead

Khi Customer mới có `lead_name`, Lead chuyển sang Converted và các Quotation, Opportunity của Lead được trỏ lại sang Customer.

```mermaid
sequenceDiagram
    actor User
    participant C as Customer
    participant L as Lead
    participant QO as Quotation và Opportunity
    participant M as customer/mapper.py
    participant CU as crm/utils.py
    User->>C: insert()
    C->>C: validate() gồm validate_lead_not_converted, validate_credit_limit_on_change, validate_prospect_not_converted
    C->>C: after_insert() gọi update_lead_status()
    opt có lead_name
        C->>L: db_set status Converted
        C->>L: update_prospect()
        C->>QO: link_lead_records() đổi party sang Customer
    end
    C->>C: on_update() gọi validate_name_with_customer_group()
    C->>M: create_primary_contact() gọi make_contact()
    C->>M: create_primary_address() gọi make_address()
    opt flags.is_new_doc
        C->>C: link_address_and_contact()
        C->>CU: copy_communication() gọi copy_comments, link_communications
    end
    C->>C: update_customer_groups()
```

Nguồn: [customer.py:361](../../apps/erpnext/erpnext/selling/doctype/customer/customer.py#L361), [customer.py:303](../../apps/erpnext/erpnext/selling/doctype/customer/customer.py#L303)

### Kiểm tra hạn mức tín dụng

Sales Order gọi lúc submit và lúc mở lại; Delivery Note và Sales Invoice cũng dùng chung hàm module-level `check_credit_limit`.

```mermaid
sequenceDiagram
    actor User
    participant SO as Sales Order
    participant CCL as Customer Credit Limit
    participant CF as customer.py
    participant Mail as frappe.sendmail
    SO->>CCL: đọc bypass_credit_limit_check
    alt không bypass
        SO->>CF: check_credit_limit(customer, company)
        CF->>CF: get_credit_limit() theo Customer, Customer Group, Company
        CF->>CF: get_customer_outstanding()
        alt outstanding lớn hơn hạn mức và user không có role credit_controller
            CF-->>User: msgprint raise_exception kèm nút Send Email
            User->>CF: send_emails()
            CF->>Mail: gửi tới credit_controller_users
        else trong hạn mức hoặc có role
            CF-->>SO: tiếp tục
        end
    else bypass
        SO-->>SO: bỏ qua
    end
```

Nguồn: [sales_order.py:644](../../apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py#L644), [customer.py:594](../../apps/erpnext/erpnext/selling/doctype/customer/customer.py#L594)

### Submit Quotation

Submit Quotation kiểm tra thẩm quyền rồi đồng bộ trạng thái Opportunity, Lead và các phiên bản khác của báo giá.

```mermaid
sequenceDiagram
    actor User
    participant Q as Quotation
    participant SC as SellingController
    participant AC as Authorization Control
    participant O as Opportunity
    participant L as Lead
    User->>Q: submit()
    Q->>SC: validate()
    Q->>Q: set_status(), set_default_valid_till(), validate_valid_till()
    Q->>Q: validate_revision(), validate_lead(), set_customer_name()
    Q->>Q: make_packing_list()
    Q->>Q: before_submit() gọi set_has_alternative_item()
    Q->>AC: on_submit() gọi validate_approving_authority()
    Q->>O: update_opportunity("Quotation") gọi set_status(update=True)
    opt quotation_to là Lead
        Q->>L: update_lead() gọi set_status(update=True)
    end
    Q->>Q: deactivate_other_versions()
    Q->>Q: update_latest_revision()
```

Nguồn: [quotation.py:170](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L170), [quotation.py:417](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L417)

### Tạo revision Quotation

Revision là bản Quotation mới có `revision_of` trỏ về bản gốc, tên dạng `<gốc>-R<n>`, và tại mỗi thời điểm chỉ một phiên bản `is_active`.

```mermaid
sequenceDiagram
    actor User
    participant M as quotation/mapper.py
    participant Src as Quotation gốc
    participant New as Quotation revision
    participant CU as crm/utils.py
    User->>M: make_revision(source_name)
    M->>Src: validate_can_be_revised()
    M->>M: get_mapped_doc() với set_revision_of
    M-->>User: bản nháp
    User->>New: insert()
    New->>New: autoname() gọi get_next_revision_index()
    New->>New: validate_revision() gọi validate_revision_matches_original(), get_newer_versions()
    New->>CU: after_insert() gọi carry_forward_communication()
    User->>New: submit()
    New->>Src: on_submit() gọi deactivate_other_versions()
    New->>Src: update_latest_revision() gọi update_versions()
    opt hủy revision
        User->>New: cancel()
        New->>Src: on_cancel() gọi reactivate_latest_version()
    end
```

Nguồn: [mapper.py:243](../../apps/erpnext/erpnext/selling/doctype/quotation/mapper.py#L243), [quotation.py:210](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L210), [quotation.py:511](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L511)

### Declare Lost cho Quotation

Chỉ Quotation đã submit và chưa có đơn bán nào mới đánh dấu Lost được; các phiên bản khác cũng bị Lost theo.

```mermaid
sequenceDiagram
    actor User
    participant Q as Quotation
    participant V as Quotation phiên bản khác
    participant O as Opportunity
    participant L as Lead
    User->>Q: declare_enquiry_lost(lost_reasons_list, competitors, detailed_reason)
    Q->>Q: check_permission("write"), kiểm tra docstatus bằng 1
    alt không ordered và không có has_ordered_versions
        Q->>Q: db_set status Lost
        Q->>Q: append lost_reasons, competitors
        Q->>V: set_other_versions_as_lost()
        Q->>O: update_opportunity("Lost")
        Q->>L: update_lead()
        Q->>Q: save()
    else đã có Sales Order
        Q-->>User: throw Cannot set as Lost
    end
```

Nguồn: [quotation.py:366](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L366)

### Hết hạn Quotation theo lịch

Job `daily_maintenance` chuyển Quotation quá `valid_till` và chưa có Sales Order sang Expired rồi tính lại Opportunity.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant QF as quotation.py
    participant Q as Quotation
    participant O as Opportunity
    Sch->>QF: set_expired_status()
    QF->>Q: chọn bản submit, status khác Expired và Lost, không có Sales Order
    QF->>Q: frappe.qb.update status Expired
    loop mỗi Quotation hết hạn
        QF->>Q: get_doc()
        Q->>Q: update_opportunity(None)
        Q->>O: update_opportunity_status() gọi set_status(update=True)
    end
```

Nguồn: [quotation.py:617](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L617)

### Quotation sang Sales Order

`make_sales_order` tự tạo Customer nếu Quotation đang gắn với Lead hoặc Prospect chưa chuyển đổi, rồi map các dòng còn lại.

```mermaid
sequenceDiagram
    actor User
    participant M as quotation/mapper.py
    participant LM as lead/mapper.py
    participant P as prospect.py
    participant C as Customer
    participant SO as Sales Order nháp
    participant PS as PaymentScheduleService
    User->>M: make_sales_order(source_name)
    M->>M: validate_quotation_expiry()
    M->>M: _make_customer() gọi get_existing_customer_name()
    alt chưa có Customer và quotation_to là Lead
        M->>LM: create_customer_from_lead() gọi _make_customer()
        LM-->>M: Customer mới
        M->>C: insert()
    else chưa có Customer và quotation_to là Prospect
        M->>P: create_customer_from_prospect() gọi make_customer()
        P-->>M: Customer mới
        M->>C: insert()
    end
    M->>M: validate_target_header(), get_ordered_items(), get_qty_already_mapped()
    M->>SO: get_mapped_doc() với can_map_row, validation docstatus 1 và is_active 1
    M->>SO: set_missing_values() gọi calculate_taxes_and_totals
    opt automatically_fetch_payment_terms
        M->>PS: set_payment_schedule()
    end
    M-->>User: Sales Order nháp
```

Nguồn: [mapper.py:55](../../apps/erpnext/erpnext/selling/doctype/quotation/mapper.py#L55), [mapper.py:62](../../apps/erpnext/erpnext/selling/doctype/quotation/mapper.py#L62)

### Submit Sales Order

Submit Sales Order chỉ cập nhật số lượng giữ chỗ và chứng từ trước, không ghi `GL Entry` hay `Stock Ledger Entry`.

```mermaid
sequenceDiagram
    actor User
    participant SO as Sales Order
    participant SR as SalesOrderStockReservation
    participant QI as Quotation Item
    participant Q as Quotation
    participant O as Opportunity
    participant Bin as Bin
    participant BO as Blanket Order
    User->>SO: submit()
    SO->>SO: validate() gồm validate_delivery_date, validate_po, validate_warehouse
    SO->>SR: validate_reserved_stock(), enable_auto_reserve_stock()
    SO->>BO: validate_against_blanket_order()
    SO->>SO: make_packing_list(), validate_with_previous_doc(), set_status()
    SO->>QI: on_submit() gọi StatusUpdater.update_prevdoc_status() cập nhật ordered_qty
    SO->>SO: check_credit_limit()
    SO->>SR: update_reserved_qty()
    SR->>Bin: update_bin_qty() reserved_qty
    SO->>SO: validate_approving_authority(), update_project()
    SO->>Q: update_prevdoc_status("submit") gọi set_status(update=True)
    Q->>O: update_opportunity("Converted")
    SO->>BO: update_blanket_order() gọi update_ordered_qty()
    opt reserve_stock và không is_subcontracted
        SO->>SR: create_stock_reservation_entries()
    end
```

Nguồn: [sales_order.py:269](../../apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py#L269), [sales_order.py:577](../../apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py#L577), [reservation.py:35](../../apps/erpnext/erpnext/selling/doctype/sales_order/services/reservation.py#L35)

### Sales Order sang Delivery Note

`make_delivery_note` map các dòng còn phải giao; Delivery Note khi submit mới ghi sổ kho và sổ cái, đồng thời đẩy `delivered_qty` ngược về Sales Order.

```mermaid
sequenceDiagram
    actor User
    participant M as sales_order/mapper.py
    participant DN as Delivery Note
    participant SO as Sales Order
    participant SLE as Stock Ledger Entry
    participant GL as GL Entry
    User->>M: make_delivery_note(source_name, target_doc, kwargs)
    opt for_reserved_stock
        M->>M: get_sre_reserved_qty_details_for_voucher(), get_sre_details_for_voucher()
    end
    M->>M: get_qty_already_mapped()
    M->>DN: get_mapped_doc() bỏ dòng closed, delivered_by_supplier, skip_delivery
    M->>DN: set_missing_values() gọi make_packing_list
    M-->>User: Delivery Note nháp
    User->>DN: submit()
    DN->>DN: on_submit() gọi validate_packed_qty(), validate_approving_authority()
    DN->>SO: update_prevdoc_status() cập nhật delivered_qty, per_delivered, status
    DN->>DN: update_pick_list_status(), update_billing_status()
    opt không is_return
        DN->>DN: check_credit_limit()
    end
    DN->>DN: update_stock_reservation_entries()
    DN->>SO: update_stock_ledger() gọi update_reserved_qty()
    DN->>SLE: make_sl_entries()
    opt perpetual inventory
        DN->>GL: make_gl_entries()
    end
    DN->>DN: repost_future_sle_and_gle()
```

Nguồn: [mapper.py:235](../../apps/erpnext/erpnext/selling/doctype/sales_order/mapper.py#L235), [delivery_note.py:542](../../apps/erpnext/erpnext/stock/doctype/delivery_note/delivery_note.py#L542), [selling_controller.py:773](../../apps/erpnext/erpnext/controllers/selling_controller.py#L773)

### Sales Order sang Sales Invoice

`make_sales_invoice` tính phần còn phải xuất hóa đơn theo số lượng và số tiền; Sales Invoice khi submit luôn ghi GL, chỉ ghi kho nếu `update_stock`.

```mermaid
sequenceDiagram
    actor User
    participant M as sales_order/mapper.py
    participant SI as Sales Invoice
    participant SO as Sales Order
    participant SLE as Stock Ledger Entry
    participant GL as GL Entry
    User->>M: make_sales_invoice(source_name, target_doc, args)
    M->>M: get_qty_already_mapped()
    M->>SI: get_mapped_doc() với get_pending_qty, is_amount_billable
    M->>SI: postprocess() gọi set_missing_values, set_advances, make_packing_list
    opt is_subcontracted
        M->>SI: add_self_rm()
    end
    opt automatically_fetch_payment_terms
        M->>SI: PaymentScheduleService.set_payment_schedule()
    end
    M-->>User: Sales Invoice nháp
    User->>SI: submit()
    SI->>SI: on_submit() gọi validate_approving_authority(), check_prev_docstatus()
    SI->>SO: update_prevdoc_status() cập nhật billed_amt, per_billed, status
    SI->>SI: update_billing_status_in_dn()
    opt update_stock bằng 1
        SI->>SI: update_stock_reservation_entries()
        SI->>SLE: update_stock_ledger() gọi make_sl_entries()
    end
    SI->>GL: make_gl_entries()
    opt không is_return và is_opening khác Yes
        SI->>SI: check_credit_limit(), check_overdue_billing_threshold()
    end
```

Nguồn: [mapper.py:452](../../apps/erpnext/erpnext/selling/doctype/sales_order/mapper.py#L452), [sales_invoice.py:443](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L443), [sales_invoice.py:1135](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L1135)

### Sales Order sang Purchase Order

`make_purchase_order` tạo mỗi Supplier một Purchase Order từ các dòng được chọn; bản nào đã có `supplier` thì insert luôn.

```mermaid
sequenceDiagram
    actor User
    participant M as sales_order/mapper.py
    participant SO as Sales Order
    participant PO as Purchase Order
    User->>M: make_purchase_order(source_name, selected_items, target_doc)
    M->>SO: get_doc(), check_permission("read")
    M->>M: dựng items_to_map theo từng dòng được chọn
    loop mỗi supplier
        M->>PO: get_mapped_doc() với filter_items, field_no_map cho rate và discount
        M->>PO: set_missing_values() đặt supplier, currency, conversion_rate
        opt có dòng delivered_by_supplier
            M->>PO: chép shipping_address và customer_contact_person từ Sales Order
        end
        M->>PO: set_delivery_date()
        opt doc.supplier có giá trị
            M->>PO: insert()
        end
    end
    M-->>User: danh sách Purchase Order
```

Nguồn: [mapper.py:755](../../apps/erpnext/erpnext/selling/doctype/sales_order/mapper.py#L755)

### Đổi trạng thái Sales Order

Close, On Hold và mở lại đi qua `StatusService`, tính lại giữ chỗ, đơn gia công và Blanket Order.

```mermaid
sequenceDiagram
    actor User
    participant SOF as sales_order.py
    participant SO as Sales Order
    participant SS as StatusService
    participant SR as SalesOrderStockReservation
    participant Sub as SubcontractingService
    participant BO as Blanket Order
    User->>SOF: update_status(status, name)
    SOF->>SO: get_doc(check_permission "submit"), update_status(status)
    SO->>SS: update_status(status)
    SS->>SS: check_modified_date()
    alt status là Closed
        SS->>SS: _validate_no_reserved_stock()
    else mở lại từ Closed
        SS->>BO: validate_parent_reopen(), validate_reopen_against_blanket_order()
    end
    SS->>SO: set_status(update=True, status=status)
    opt status là Draft
        SS->>SO: check_credit_limit()
    end
    SS->>SR: update_reserved_qty()
    SS->>Sub: update_subcontracting_order_status()
    SS->>SO: notify_update()
    SS->>BO: update_blanket_order()
```

Nguồn: [sales_order.py:900](../../apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py#L900), [status.py:30](../../apps/erpnext/erpnext/selling/doctype/sales_order/services/status.py#L30)

### Proforma Invoice

Proforma Invoice được tạo và submit ngay từ dialog của Sales Order, chỉ sinh PDF và gửi mail, không ghi sổ.

```mermaid
sequenceDiagram
    actor User
    participant PF as proforma_invoice.py
    participant P as Proforma Invoice
    participant SO as Sales Order
    participant File as File
    participant Mail as frappe.sendmail
    User->>PF: make_proforma_invoice(sales_order, items, based_on)
    PF->>PF: validate_feature_enabled()
    PF->>P: insert()
    P->>SO: validate() gọi validate_sales_order(), set_item_values()
    P->>P: clear_generated_values()
    PF->>P: submit()
    P->>P: before_submit() đặt status Issued
    P->>SO: on_submit() gọi generate_and_attach_pdf(), get_sales_order_copy()
    P->>P: render_pdf() db_set grand_total
    P->>File: save_file(), db_set proforma_pdf
    opt gửi mail
        User->>PF: send_proforma_email(proforma_name, recipients)
        PF->>Mail: sendmail kèm file PDF
        PF->>P: db_set sent_on, emailed_to
    end
```

Nguồn: [proforma_invoice.py:249](../../apps/erpnext/erpnext/selling/doctype/proforma_invoice/proforma_invoice.py#L249), [proforma_invoice.py:135](../../apps/erpnext/erpnext/selling/doctype/proforma_invoice/proforma_invoice.py#L135), [proforma_invoice.py:298](../../apps/erpnext/erpnext/selling/doctype/proforma_invoice/proforma_invoice.py#L298)

## Giới hạn

- Blanket Order nằm ở `manufacturing/doctype/blanket_order/`, không vẽ riêng ở đây. Trong các luồng trên nó chỉ xuất hiện qua `validate_against_blanket_order`, `update_blanket_order`, `validate_reopen_against_blanket_order`.
- Không vẽ: Industry Type, Sales Partner Type (danh mục), SMS Center. Selling Settings, Party Specific Item và Product Bundle có trong class diagram nhưng không có sequence riêng vì là cấu hình hoặc không nối chứng từ khác; Product Bundle có versioning qua `make_new_version` và `make_active`.
- Installation Note chỉ đọc lướt `on_submit`, `on_cancel`, không có sequence.
- `sales_order/mapper.py` còn các hàm chưa vẽ: `make_material_request`, `make_project`, `make_work_orders`, `make_production_plan`, `create_pick_list`, `make_maintenance_schedule`, `make_maintenance_visit`, `make_subcontracting_inward_order`, `make_inter_company_purchase_order`. `quotation/mapper.py` có `make_sales_invoice` chưa vẽ.
- `selling/page/` (point_of_sale, sales_funnel), `report/`, `customer_overview.py` không đọc.
- `get_customer_outstanding`, `update_stock_reservation_entries`, `BillingStatusService`, `StockLedgerService` và `general_ledger.make_gl_entries` chỉ đọc lướt: sơ đồ dừng ở tên hàm, không đi vào chi tiết.
- `SalesOrder.on_cancel` không có sơ đồ riêng; thứ tự hook khác `on_submit` (thêm `check_nextdoc_docstatus`, `cancel_stock_reservation_entries`, `unlink_inter_company_doc`).
- Thứ tự `after_insert` trước `on_update` trong luồng Customer dựa trên vòng đời Frappe, không đọc lại trong `frappe/model/document.py`.
- `get_existing_customer_name` tra `Customer.crm_deal` và `set_customer_name` xử lý `quotation_to == "CRM Deal"`, nhưng `customer.json` không có field `crm_deal`. Có thể là custom field do app Frappe CRM thêm, chưa xác nhận.
- Trong `Submit Sales Order`, `update_prevdoc_status` ở `SalesOrder` là override có tham số `flag`; bản không tham số là `StatusUpdater.update_prevdoc_status` gọi qua `super()`. Hai lời gọi đều chạy trong `on_submit`.
