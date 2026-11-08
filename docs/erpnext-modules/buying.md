# Module Buying

Module `buying` quản lý nhà cung cấp, hỏi giá, báo giá nhà cung cấp, đơn mua và chấm điểm nhà cung cấp. Module nhận yêu cầu từ `stock` (Material Request) và `crm` (Opportunity), đẩy luồng sang `stock` (Purchase Receipt, Bin), `accounts` (Purchase Invoice, budget) và nối ngược với `selling` qua drop ship.

## Phạm vi

Đọc được 19 doctype trong `buying/doctype/`. Mục "Sơ đồ" chỉ tới tiêu đề trong file này.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Nhà cung cấp | Supplier, Customer Number At Supplier, `supplier/supplier.py` | Class: Chứng từ mua. Sequence: Lưu Supplier |
| Hỏi giá | Request for Quotation, RFQ Item, RFQ Supplier, `request_for_quotation/mapper.py` | Class: Chứng từ mua. Sequence: Tạo và gửi RFQ, Nhà cung cấp báo giá qua portal |
| Báo giá nhà cung cấp | Supplier Quotation, Supplier Quotation Item, `supplier_quotation/mapper.py` | Class: Chứng từ mua. Sequence: Submit Supplier Quotation, Supplier Quotation sang Purchase Order |
| Đơn mua | Purchase Order, Purchase Order Item, `purchase_order/mapper.py`, `purchase_order/services/` | Class: Chứng từ mua. Sequence: Submit Purchase Order, Purchase Order sang Purchase Receipt và Purchase Invoice, Đổi trạng thái, Drop ship |
| Chấm điểm | Supplier Scorecard, Period, Criteria, Standing, Variable và ba bảng con Scoring | Class: Supplier Scorecard. Sequence: Làm mới Scorecard, Tính điểm Period |

## Class diagram

Class ngoài module (ví dụ `SalesOrder`, `MaterialRequest`) chỉ để đích của quan hệ nên để trống. Controller cha chỉ ghi method.

### Chứng từ mua

```mermaid
classDiagram
    class TransactionBase
    class StockController
    class SubcontractingController
    class BuyingController {
        +validate()
        +set_missing_values()
        +on_submit()
        +on_cancel()
        +validate_budget()
    }
    class Supplier {
        +string supplier_name
        +string supplier_group
        +string supplier_type
        +bool on_hold
        +string hold_type
        +bool prevent_rfqs
        +bool warn_rfqs
        +bool prevent_pos
        +validate()
        +on_update()
        +is_blocked_for()
        +create_primary_contact()
        +create_primary_address()
    }
    class RequestforQuotation {
        +string company
        +date transaction_date
        +string status
        +string vendor
        +string opportunity
        +string email_template
        +validate()
        +on_submit()
        +on_cancel()
        +validate_supplier_list()
        +send_to_supplier()
        +supplier_rfq_mail()
        +update_supplier_contact()
    }
    class RequestforQuotationItem {
        +string item_code
        +float qty
        +string material_request
        +string material_request_item
    }
    class RequestforQuotationSupplier {
        +string supplier
        +string contact
        +string email_id
        +bool send_email
        +bool email_sent
        +string quote_status
    }
    class SupplierQuotation {
        +string supplier
        +date transaction_date
        +date valid_till
        +string status
        +string opportunity
        +validate()
        +on_submit()
        +on_cancel()
        +update_rfq_supplier_status()
        +get_ordered_status()
    }
    class SupplierQuotationItem {
        +string item_code
        +float qty
        +float rate
        +float ordered_qty
        +string request_for_quotation
        +string request_for_quotation_item
    }
    class PurchaseOrder {
        +string supplier
        +date transaction_date
        +date schedule_date
        +string status
        +float per_received
        +float per_billed
        +bool is_subcontracted
        +validate()
        +on_submit()
        +on_cancel()
        +validate_supplier()
        +update_prevdoc_status()
        +update_ordered_qty()
        +update_status()
        +update_dropship_received_qty()
    }
    class PurchaseOrderItem {
        +string item_code
        +float qty
        +float received_qty
        +string supplier_quotation
        +string supplier_quotation_item
        +string material_request
        +string sales_order
        +string blanket_order
    }
    class SalesOrder
    class MaterialRequest
    class BlanketOrder
    TransactionBase <|-- Supplier
    StockController <|-- SubcontractingController
    SubcontractingController <|-- BuyingController
    BuyingController <|-- RequestforQuotation
    BuyingController <|-- SupplierQuotation
    BuyingController <|-- PurchaseOrder
    RequestforQuotation *-- RequestforQuotationItem : items
    RequestforQuotation *-- RequestforQuotationSupplier : suppliers
    SupplierQuotation *-- SupplierQuotationItem : items
    PurchaseOrder *-- PurchaseOrderItem : items
    RequestforQuotationSupplier --> Supplier : supplier
    SupplierQuotation --> Supplier : supplier
    PurchaseOrder --> Supplier : supplier
    SupplierQuotationItem --> RequestforQuotation : request_for_quotation
    PurchaseOrderItem --> SupplierQuotation : supplier_quotation
    PurchaseOrderItem --> SupplierQuotationItem : supplier_quotation_item
    PurchaseOrderItem --> MaterialRequest : material_request
    PurchaseOrderItem --> SalesOrder : sales_order
    PurchaseOrderItem --> BlanketOrder : blanket_order
```

### Supplier Scorecard

```mermaid
classDiagram
    class Supplier
    class SupplierScorecard {
        +string supplier
        +string period
        +string supplier_score
        +string status
        +string weighting_function
        +bool prevent_rfqs
        +bool prevent_pos
        +validate()
        +on_update()
        +calculate_total_score()
        +update_standing()
        +apply_standing()
        +notify_standing()
    }
    class SupplierScorecardPeriod {
        +string scorecard
        +string supplier
        +date start_date
        +date end_date
        +float total_score
        +validate()
        +calculate_variables()
        +calculate_criteria()
        +calculate_score()
        +calculate_weighted_score()
        +get_eval_statement()
    }
    class SupplierScorecardScoringCriteria {
        +string criteria_name
        +float score
        +float weight
        +float max_score
        +string formula
    }
    class SupplierScorecardScoringStanding {
        +string standing_name
        +float min_grade
        +float max_grade
        +bool prevent_pos
        +bool warn_pos
    }
    class SupplierScorecardScoringVariable {
        +string variable_label
        +float value
        +string param_name
        +string path
    }
    class SupplierScorecardCriteria {
        +string criteria_name
        +float max_score
        +float weight
        +string formula
        +validate()
        +validate_variables()
        +validate_formula()
    }
    class SupplierScorecardStanding {
        +string standing_name
        +string standing_color
        +float min_grade
        +float max_grade
    }
    class SupplierScorecardVariable {
        +string variable_label
        +bool is_custom
        +string param_name
        +string path
        +validate()
        +validate_path_exists()
    }
    SupplierScorecard --> Supplier : supplier
    SupplierScorecard *-- SupplierScorecardScoringCriteria : criteria
    SupplierScorecard *-- SupplierScorecardScoringStanding : standings
    SupplierScorecardPeriod --> SupplierScorecard : scorecard
    SupplierScorecardPeriod --> Supplier : supplier
    SupplierScorecardPeriod *-- SupplierScorecardScoringCriteria : criteria
    SupplierScorecardPeriod *-- SupplierScorecardScoringVariable : variables
    SupplierScorecardScoringCriteria --> SupplierScorecardCriteria : criteria_name
    SupplierScorecardScoringStanding --> SupplierScorecardStanding : standing_name
    SupplierScorecardScoringVariable --> SupplierScorecardVariable : variable_label
```

## Sequence diagram

### Lưu Supplier

Supplier là master, luồng đáng chú ý là tạo Contact, Address chính và gán role cho portal user.

```mermaid
sequenceDiagram
    actor User
    participant S as Supplier
    participant Party as accounts/party.py
    participant M as customer/mapper.py
    participant Portal as Portal User
    User->>S: insert()
    S->>S: validate() đặt flags.is_new_doc
    S->>Party: validate_party_accounts()
    S->>S: validate_supplier_group(), validate_internal_supplier()
    S->>S: validate_primary_contact_and_address()
    S->>Portal: add_role_for_user() gọi add_role_for_portal_user
    S->>S: on_update()
    opt chưa có supplier_primary_contact và có mobile_no hoặc email_id
        S->>M: create_primary_contact() gọi make_contact()
    end
    opt is_new_doc và có address_line1
        S->>M: create_primary_address() gọi make_address()
    end
    S->>Portal: link_portal_users_to_contacts()
```

Nguồn: [supplier.py:154](../../apps/erpnext/erpnext/buying/doctype/supplier/supplier.py#L154), [supplier.py:125](../../apps/erpnext/erpnext/buying/doctype/supplier/supplier.py#L125)

### Tạo và gửi RFQ

RFQ lấy dòng từ Material Request và khi submit thì gửi mail, đồng thời tạo User và Contact cho nhà cung cấp nếu chưa có.

```mermaid
sequenceDiagram
    actor User
    participant M as request_for_quotation/mapper.py
    participant R as Request for Quotation
    participant SS as Supplier
    participant U as User và Contact
    participant Comm as Communication
    User->>M: get_item_from_material_requests_based_on_supplier(source_name)
    M->>R: get_mapped_doc() từ Material Request
    User->>R: submit()
    R->>R: before_validate() gọi set_data_for_supplier()
    R->>SS: validate() gọi ensure_supplier_is_not_blocked()
    R->>SS: validate_supplier_list() đọc prevent_rfqs, warn_rfqs
    R->>R: on_submit() db_set status Submitted, đặt quote_status Pending
    R->>R: send_to_supplier()
    loop mỗi dòng suppliers có send_email và email_id
        R->>U: update_supplier_contact() gọi create_user(), link_supplier_contact()
        U->>SS: update_user_in_supplier() thêm portal_users
        R->>R: update_supplier_part_no()
        R->>Comm: supplier_rfq_mail() gọi send_email()
        R->>R: lưu email_sent bằng 1
    end
```

Nguồn: [mapper.py:180](../../apps/erpnext/erpnext/buying/doctype/request_for_quotation/mapper.py#L180), [request_for_quotation.py:169](../../apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.py#L169), [request_for_quotation.py:200](../../apps/erpnext/erpnext/buying/doctype/request_for_quotation/request_for_quotation.py#L200)

### Nhà cung cấp báo giá qua portal

Portal user của Supplier gửi báo giá; item và UOM lấy từ dòng RFQ, chỉ `qty` và `rate` lấy từ nhà cung cấp.

```mermaid
sequenceDiagram
    actor Portal as Portal User
    participant M as request_for_quotation/mapper.py
    participant R as Request for Quotation
    participant SQ as Supplier Quotation
    Portal->>M: create_supplier_quotation(doc)
    M->>M: kiểm tra session user thuộc Portal User của Supplier
    M->>R: get_quotable_rfq() yêu cầu docstatus 1 và supplier được mời
    M->>SQ: validate_existing_supplier_quotation() khóa RFQ, chặn báo giá trùng
    M->>SQ: frappe.get_doc() với ignore_pricing_rule bằng 1
    M->>R: add_items() kiểm tra dòng thuộc RFQ
    M->>SQ: create_rfq_items()
    opt rate gửi lên bằng 0
        M->>SQ: đặt discount_percentage bằng 100
    end
    M->>SQ: run_method("set_missing_values"), save()
    M-->>Portal: tên Supplier Quotation
```

Nguồn: [mapper.py:60](../../apps/erpnext/erpnext/buying/doctype/request_for_quotation/mapper.py#L60), [mapper.py:142](../../apps/erpnext/erpnext/buying/doctype/request_for_quotation/mapper.py#L142)

### Submit Supplier Quotation

Submit cập nhật `quote_status` của nhà cung cấp trên RFQ; hết hạn do job daily đổi trực tiếp status.

```mermaid
sequenceDiagram
    actor User
    participant Sch as Scheduler
    participant SQ as Supplier Quotation
    participant BC as BuyingController
    participant RS as Request for Quotation Supplier
    User->>SQ: submit()
    SQ->>BC: validate()
    SQ->>SQ: set_status(), validate_for_items(), validate_with_previous_doc(), validate_valid_till()
    SQ->>SQ: on_submit() gọi set_status(update=True)
    SQ->>SQ: update_rfq_supplier_status(1)
    loop mỗi RFQ trong get_request_for_quotations()
        SQ->>RS: frappe.get_all() tìm dòng theo supplier
        alt không có dòng
            SQ-->>User: throw Supplier not found
        else có dòng
            SQ->>RS: set_value quote_status Received hoặc Pending
        end
    end
    Sch->>SQ: set_expired_status() đặt Expired khi quá valid_till và chưa có Purchase Order
```

Nguồn: [supplier_quotation.py:138](../../apps/erpnext/erpnext/buying/doctype/supplier_quotation/supplier_quotation.py#L138), [supplier_quotation.py:201](../../apps/erpnext/erpnext/buying/doctype/supplier_quotation/supplier_quotation.py#L201), [supplier_quotation.py:273](../../apps/erpnext/erpnext/buying/doctype/supplier_quotation/supplier_quotation.py#L273)

### Supplier Quotation sang Purchase Order

Mapper chặn báo giá hết hạn và chỉ map dòng còn số lượng chưa đặt.

```mermaid
sequenceDiagram
    actor User
    participant M as supplier_quotation/mapper.py
    participant SQ as Supplier Quotation
    participant PO as Purchase Order nháp
    User->>M: make_purchase_order(source_name, target_doc, args)
    M->>SQ: get_status()
    alt status là Expired
        M-->>User: throw has expired
    else còn hiệu lực
        M->>SQ: get_ordered_items()
        M->>M: get_qty_already_mapped()
        M->>PO: get_mapped_doc() validation docstatus 1, map supplier_quotation_item
        M->>PO: update_item() đặt stock_qty, qty còn lại
        M->>PO: set_missing_values() gọi get_schedule_dates, calculate_taxes_and_totals
        M-->>User: Purchase Order nháp
    end
```

Nguồn: [mapper.py:17](../../apps/erpnext/erpnext/buying/doctype/supplier_quotation/mapper.py#L17)

### Submit Purchase Order

Validate kiểm tra cờ Scorecard của Supplier; submit cập nhật chứng từ trước và `Bin`, không ghi `GL Entry` hay `Stock Ledger Entry`.

```mermaid
sequenceDiagram
    actor User
    participant PO as Purchase Order
    participant BC as BuyingController
    participant S as Supplier
    participant Prev as SQ Item, MR Item, SO Item
    participant SQ as Supplier Quotation
    participant Bin as Bin
    participant BO as Blanket Order
    User->>PO: submit()
    PO->>BC: validate() gồm ensure_supplier_is_not_blocked
    PO->>S: validate_supplier() đọc prevent_pos, warn_pos
    PO->>PO: validate_with_previous_doc(), validate_minimum_order_qty()
    PO->>BO: validate_against_blanket_order()
    PO->>BC: on_submit() gọi update_last_purchase_rate
    opt is_against_so
        PO->>PO: update_status_updater() thêm đích Sales Order Item và Packed Item
    end
    PO->>Prev: update_prevdoc_status() cập nhật ordered_qty
    PO->>SQ: set_status(update=True)
    PO->>Bin: update_requested_qty(), update_ordered_qty()
    PO->>BC: validate_budget()
    PO->>PO: validate_approving_authority(), update_linked_doc()
    PO->>BO: update_blanket_order()
    PO->>PO: SubcontractingService.auto_create_subcontracting_order()
```

Nguồn: [purchase_order.py:200](../../apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.py#L200), [purchase_order.py:450](../../apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.py#L450), [purchase_order.py:434](../../apps/erpnext/erpnext/buying/doctype/purchase_order/purchase_order.py#L434)

### Purchase Order sang Purchase Receipt và Purchase Invoice

Hai mapper chỉ tạo bản nháp; Purchase Receipt và Purchase Invoice ghi sổ khi submit ở module `stock` và `accounts`.

```mermaid
sequenceDiagram
    actor User
    participant M as purchase_order/mapper.py
    participant PR as Purchase Receipt nháp
    participant PI as Purchase Invoice nháp
    User->>M: make_purchase_receipt(source_name, target_doc, args)
    M->>M: get_qty_already_mapped()
    M->>PR: get_mapped_doc() bỏ dòng delivered_by_supplier, closed
    M->>PR: update_item() tính qty còn lại hoặc theo max_receivable_qty
    M->>PR: set_missing_values()
    M-->>User: Purchase Receipt nháp
    User->>M: make_purchase_invoice(source_name, target_doc, args)
    M->>M: get_mapped_purchase_invoice()
    M->>PI: get_mapped_doc() với postprocess
    M->>PI: set_missing_values()
    M-->>User: Purchase Invoice nháp
```

Nguồn: [mapper.py:31](../../apps/erpnext/erpnext/buying/doctype/purchase_order/mapper.py#L31), [mapper.py:128](../../apps/erpnext/erpnext/buying/doctype/purchase_order/mapper.py#L128)

### Đổi trạng thái Purchase Order

Close, On Hold và mở lại đi qua `StatusService` của Purchase Order.

```mermaid
sequenceDiagram
    actor User
    participant PO as Purchase Order
    participant SS as StatusService
    participant BO as Blanket Order
    participant Bin as Bin
    participant Sub as SubcontractingService
    User->>PO: update_status(status)
    PO->>SS: update_status(status)
    SS->>SS: check_modified_date()
    opt mở lại từ Closed
        SS->>BO: validate_parent_reopen(), validate_reopen_against_blanket_order()
    end
    SS->>PO: set_status(update=True, status=status)
    SS->>Bin: update_requested_qty(), update_ordered_qty()
    opt status là Closed hoặc vừa mở lại
        SS->>Sub: update_subcontracting_order_status()
    end
    SS->>BO: update_blanket_order()
    SS->>PO: notify_update()
```

Nguồn: [status.py:24](../../apps/erpnext/erpnext/buying/doctype/purchase_order/services/status.py#L24)

### Cập nhật số lượng drop ship

Với dòng `delivered_by_supplier`, người dùng ghi nhận số đã giao trên Purchase Order và Sales Order được tính lại `delivered_qty`.

```mermaid
sequenceDiagram
    actor User
    participant PO as Purchase Order
    participant DS as DropShipService
    participant SO as Sales Order
    participant SS as StatusService (Sales Order)
    User->>PO: update_dropship_received_qty(data)
    PO->>PO: check_permission("write")
    PO->>DS: update_dropship_received_qty(data)
    loop mỗi dòng trong data
        DS->>DS: kiểm tra delivered_by_supplier và giới hạn qty
        DS->>PO: db_set received_qty, add_comment
    end
    DS->>PO: update_receiving_percentage(), set_status(update=True)
    DS->>SO: update_delivered_qty_in_sales_order() gọi update_delivery_status()
    SO->>SS: update_delivery_status() gọi get_drop_ship_delivered_qty()
    DS->>SO: set_status(update=True), notify_update()
```

Nguồn: [drop_ship.py:14](../../apps/erpnext/erpnext/buying/doctype/purchase_order/services/drop_ship.py#L14), [drop_ship.py:81](../../apps/erpnext/erpnext/buying/doctype/purchase_order/services/drop_ship.py#L81)

### Làm mới Supplier Scorecard

Job `daily_maintenance` tạo các Period còn thiếu cho mỗi Scorecard rồi lưu lại để tính điểm, gán Standing và đẩy cờ sang Supplier.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant SF as supplier_scorecard.py
    participant SC as Supplier Scorecard
    participant P as Supplier Scorecard Period
    participant S as Supplier
    Sch->>SF: refresh_scorecards()
    loop mỗi Scorecard, trong savepoint refresh_scorecard
        SF->>SC: make_all_scorecards(docname)
        SF->>S: create_scorecard_periods() check_permission("write")
        loop end_date trước hôm nay
            SF->>P: get_overlapping_period_end()
            opt không chồng lấn
                SF->>P: make_supplier_scorecard(), insert(), submit()
            end
        end
        opt scp_count lớn hơn 0
            SF->>SC: save()
            SC->>SC: validate() gọi calculate_total_score(), update_standing()
            SC->>S: apply_standing() set_value các cờ STANDING_FLAGS
            SC->>SC: on_update() gọi notify_standing() khi status đổi
        end
    end
```

Nguồn: [supplier_scorecard.py:202](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard/supplier_scorecard.py#L202), [supplier_scorecard.py:228](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard/supplier_scorecard.py#L228), [supplier_scorecard.py:168](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard/supplier_scorecard.py#L168)

### Tính điểm Supplier Scorecard Period

`validate` của Period chạy hàm biến, thế vào công thức tiêu chí và tính `total_score`.

```mermaid
sequenceDiagram
    participant Caller as create_scorecard_periods
    participant P as Supplier Scorecard Period
    participant Var as supplier_scorecard_variable.py
    participant Eval as frappe.safe_eval
    Caller->>P: insert()
    P->>P: validate() lấy supplier từ scorecard
    P->>P: validate_overlapping_period(), validate_criteria_weights()
    P->>P: calculate_variables()
    loop mỗi dòng variables
        alt path chứa dấu chấm
            P->>P: import_string_path(path)
        else hàm chuẩn
            P->>Var: getattr(variable_functions, path)
        end
        P->>P: gán var.value
    end
    P->>P: calculate_criteria()
    loop mỗi dòng criteria
        P->>P: get_eval_statement(formula)
        P->>Eval: tính score, chặn trong 0 và max_score
    end
    P->>P: calculate_score() ra total_score
```

Nguồn: [supplier_scorecard_period.py:48](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard_period/supplier_scorecard_period.py#L48), [supplier_scorecard_period.py:73](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard_period/supplier_scorecard_period.py#L73), [supplier_scorecard_period.py:82](../../apps/erpnext/erpnext/buying/doctype/supplier_scorecard_period/supplier_scorecard_period.py#L82)

## Giới hạn

- Không vẽ: Buying Settings (cấu hình), Customer Number At Supplier (bảng con của Supplier, không có quan hệ nghiệp vụ khác), Purchase Receipt Item Supplied (Purchase Order hiện không có Table trỏ tới doctype này trong JSON).
- `PurchaseOrder.on_cancel` không có sơ đồ riêng; thêm phần `DropShipService.set_received_qty_to_zero_for_drop_ship_items` và `unlink_inter_company_doc`.
- `purchase_order/mapper.py` còn `make_inter_company_sales_order`, `make_subcontracting_order`, `make_purchase_invoice_from_portal` chưa vẽ; `supplier_quotation/mapper.py` còn `make_quotation` và `make_purchase_invoice` (đã đánh dấu deprecated). `make_supplier_quotation_from_rfq` chưa vẽ.
- Chỉ đọc lướt: `validate_budget`, `update_requested_qty`, `update_last_purchase_rate`, các hàm tính biến trong `supplier_scorecard_variable.py`, `supplier_overview.py`, `buying/report/`.
- Bước ghi sổ của Purchase Receipt và Purchase Invoice thuộc module `stock` và `accounts`, không vẽ ở đây.
- Trong "Làm mới Supplier Scorecard", `SupplierScorecard.on_update` cũng gọi `create_scorecard_periods` với cờ `in_rescore` để tránh lặp, sơ đồ không vẽ nhánh này.
