# Module Subcontracting

Module quản lý gia công theo hai chiều: thuê ngoài (Subcontracting Order, Subcontracting Receipt) và nhận gia công cho khách (Subcontracting Inward Order). Module nối với `buying` (Purchase Order, Purchase Receipt), `selling` (Sales Order), `stock` (Stock Entry, Stock Reservation Entry, sổ kho), `manufacturing` (BOM, Work Order, Job Card) và `accounts` (GL Entry).

## Phạm vi

Đọc được 13 doctype trong `subcontracting/doctype/`. Logic dùng chung nằm ở `controllers/subcontracting_controller.py` và `controllers/subcontracting_inward_controller.py`.

| Nhóm chức năng | Doctype / file chính | Sơ đồ |
|---|---|---|
| Danh mục | Subcontracting BOM | Class diagram |
| Thuê gia công | Subcontracting Order và 3 bảng con (`subcontracting_order.py`) | Class diagram; Sequence: tạo và submit, chuyển nguyên liệu |
| Nhận hàng gia công | Subcontracting Receipt và 2 bảng con, `services/gl_composer.py`, `mapper.py` | Class diagram; Sequence: submit Subcontracting Receipt |
| Nhận gia công | Subcontracting Inward Order và 4 bảng con, `SubcontractingInwardController` | Class diagram; Sequence: tạo và submit, nhận nguyên liệu, sản xuất, giao và trả |

## Class diagram

`StockEntry` là class ngoài module, kế thừa thật `StockController` và `SubcontractingInwardController`, nên được đưa vào để thể hiện đường gọi của Inward Order. `SubcontractingBOM` và các bảng con kế thừa trực tiếp `Document`.

### Thuê gia công

```mermaid
classDiagram
    class AccountsController
    class StockController {
        +make_gl_entries()
        +make_sl_entries()
        +repost_future_sle_and_gle()
        +update_stock_reservation_entries()
    }
    class SubcontractingController {
        +validate()
        +validate_items()
        +create_raw_materials_supplied_or_received()
        +set_consumed_qty_in_subcontract_order()
        +update_stock_ledger()
        +make_sl_entries_for_supplier_warehouse()
    }
    class SubcontractingOrder {
        +string purchase_order
        +string supplier
        +string supplier_warehouse
        +string status
        +float per_received
        +bool reserve_stock
        +validate()
        +on_submit()
        +on_cancel()
        +update_status()
        +populate_items_table()
        +update_subcontracted_quantity_in_po()
        +make_raw_material_reservations()
    }
    class SubcontractingOrderItem {
        +string item_code
        +string bom
        +float qty
        +float received_qty
        +float rm_cost_per_qty
        +float service_cost_per_qty
        +string job_card
    }
    class SubcontractingOrderServiceItem {
        +string item_code
        +string fg_item
        +float qty
        +float rate
        +string purchase_order_item
    }
    class SubcontractingOrderSuppliedItem {
        +string main_item_code
        +string rm_item_code
        +float required_qty
        +float total_supplied_qty
        +float consumed_qty
        +float stock_reserved_qty
    }
    class SubcontractingReceipt {
        +string supplier
        +date posting_date
        +bool is_return
        +string return_against
        +string status
        +float per_returned
        +validate()
        +on_submit()
        +on_cancel()
        +get_gl_entries()
        +auto_create_purchase_receipt()
        +update_job_card()
    }
    class SubcontractingReceiptItem {
        +string item_code
        +string subcontracting_order
        +string subcontracting_order_item
        +float qty
        +float rejected_qty
        +float rate
        +string job_card
    }
    class SubcontractingReceiptSuppliedItem {
        +string main_item_code
        +string rm_item_code
        +float consumed_qty
        +float rate
        +string subcontracting_order
    }
    class SubcontractingBOM {
        +string finished_good
        +string finished_good_bom
        +string service_item
        +float conversion_factor
        +bool is_active
        +validate()
        +set_conversion_factor()
    }

    AccountsController <|-- StockController
    StockController <|-- SubcontractingController
    SubcontractingController <|-- SubcontractingOrder
    SubcontractingController <|-- SubcontractingReceipt
    SubcontractingOrder *-- SubcontractingOrderItem : items
    SubcontractingOrder *-- SubcontractingOrderServiceItem : service_items
    SubcontractingOrder *-- SubcontractingOrderSuppliedItem : supplied_items
    SubcontractingReceipt *-- SubcontractingReceiptItem : items
    SubcontractingReceipt *-- SubcontractingReceiptSuppliedItem : supplied_items
    SubcontractingReceipt --> SubcontractingReceipt : return_against
    SubcontractingReceiptItem --> SubcontractingOrder : subcontracting_order
    SubcontractingReceiptSuppliedItem --> SubcontractingOrder : subcontracting_order
```

### Nhận gia công

```mermaid
classDiagram
    class StockController
    class SubcontractingController
    class SubcontractingInwardController {
        +validate_subcontracting_inward()
        +on_submit_subcontracting_inward()
        +on_cancel_subcontracting_inward()
        +update_inward_order_item()
        +update_inward_order_received_items()
        +create_stock_reservation_entries_for_inward()
        +update_inward_order_status()
    }
    class StockEntry {
        +string purpose
        +string subcontracting_inward_order
        +string work_order
        +on_submit()
        +on_cancel()
    }
    class SubcontractingInwardOrder {
        +string sales_order
        +string customer
        +string customer_warehouse
        +string status
        +float per_produced
        +float per_delivered
        +float per_raw_material_received
        +validate()
        +on_submit()
        +update_status()
        +populate_items_table()
        +make_work_order()
        +make_rm_stock_entry_inward()
        +make_subcontracting_delivery()
    }
    class SubcontractingInwardOrderItem {
        +string item_code
        +string bom
        +float qty
        +float produced_qty
        +float delivered_qty
        +float returned_qty
        +update_manufacturing_qty_fields()
    }
    class SubcontractingInwardOrderReceivedItem {
        +string main_item_code
        +string rm_item_code
        +float required_qty
        +float received_qty
        +float consumed_qty
        +float work_order_qty
        +float billed_qty
    }
    class SubcontractingInwardOrderSecondaryItem {
        +string item_code
        +string fg_item_code
        +float produced_qty
        +float delivered_qty
    }
    class SubcontractingInwardOrderServiceItem {
        +string item_code
        +string fg_item
        +float qty
        +float rate
        +string sales_order_item
    }

    StockController <|-- SubcontractingController
    StockController <|-- StockEntry
    SubcontractingInwardController <|-- StockEntry
    SubcontractingController <|-- SubcontractingInwardOrder
    SubcontractingInwardOrder *-- SubcontractingInwardOrderItem : items
    SubcontractingInwardOrder *-- SubcontractingInwardOrderReceivedItem : received_items
    SubcontractingInwardOrder *-- SubcontractingInwardOrderSecondaryItem : secondary_items
    SubcontractingInwardOrder *-- SubcontractingInwardOrderServiceItem : service_items
    StockEntry --> SubcontractingInwardOrder : subcontracting_inward_order
```

## Sequence diagram

### Tạo và submit Subcontracting Order

Subcontracting Order được tạo từ Purchase Order đã bật `is_subcontracted`, thủ công hoặc tự động khi bật `auto_create_subcontracting_order`. Khi submit, đơn cập nhật `subcontracted_qty` trên Purchase Order và có thể giữ chỗ nguyên liệu. Chứng từ này không ghi sổ.

```mermaid
sequenceDiagram
    actor User
    participant PO as Purchase Order
    participant SCO as SubcontractingOrder
    participant SC as SubcontractingController
    participant Bin as Bin
    participant SR as StockReservation
    alt bật auto_create_subcontracting_order
        User->>PO: submit
        PO->>PO: auto_create_subcontracting_order()
    else thủ công
        User->>PO: make_subcontracting_order(source_name)
    end
    PO->>SCO: get_mapped_subcontracting_order() rồi populate_items_table()
    User->>SCO: save
    SCO->>SC: validate()
    SC->>SC: validate_items(), create_raw_materials_supplied_or_received()
    SCO->>SCO: validate_purchase_order_for_subcontracting()
    SCO->>SCO: validate_service_items(), set_missing_values()
    User->>SCO: submit
    SCO->>SCO: on_submit() rồi update_status()
    SCO->>Bin: update_ordered_qty_for_subcontracting(), update_reserved_qty_for_subcontracting()
    SCO->>PO: update_subcontracted_quantity_in_po()
    SCO->>SCO: make_raw_material_reservations()
    opt bật reserve_stock
        SCO->>SR: make_stock_reservation_entries() hoặc transfer_reservation_entries_to()
    end
```

Nguồn: [mapper.py:236](../../apps/erpnext/erpnext/buying/doctype/purchase_order/mapper.py#L236), [subcontracting_order.py:127](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_order/subcontracting_order.py#L127), [subcontracting_order.py:141](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_order/subcontracting_order.py#L141)

### Chuyển nguyên liệu cho bên gia công

`make_rm_stock_entry` tạo Stock Entry mục đích `Send to Subcontractor`, chuyển từ kho nguồn sang `supplier_warehouse`. Khi submit, Stock Entry ghi sổ và cập nhật `supplied_items`, trạng thái đơn.

```mermaid
sequenceDiagram
    actor User
    participant SC as subcontracting_controller
    participant SE as StockEntry
    participant SS as SendToSubcontractorStockEntry
    participant SCO as SubcontractingOrder
    participant SLE as Stock Ledger Entry
    participant GL as GL Entry
    User->>SC: make_rm_stock_entry(subcontract_order, rm_items)
    SC-->>User: Stock Entry nháp với sco_rm_detail
    User->>SE: submit
    SE->>SS: on_submit()
    SS->>SCO: update_subcontract_order_supplied_items()
    SE->>SE: update_stock_reservation_entries()
    SE->>SE: update_wo_reservation_for_subcontracting()
    SE->>SLE: update_stock_ledger() rồi make_sl_entries()
    SE->>SCO: reserve_stock_for_subcontracting() rồi make_raw_material_reservations()
    SE->>SCO: update_subcontracting_order_status() rồi set_subcontracting_order_status()
    SE->>GL: make_gl_entries()
    SE->>SE: repost_future_sle_and_gle()
```

Nguồn: [subcontracting_controller.py:1445](../../apps/erpnext/erpnext/controllers/subcontracting_controller.py#L1445), [stock_entry.py:415](../../apps/erpnext/erpnext/stock/doctype/stock_entry/stock_entry.py#L415), [subcontracting.py:189](../../apps/erpnext/erpnext/stock/doctype/stock_entry/services/subcontracting.py#L189)

### Submit Subcontracting Receipt

Đây là bước ghi sổ chính của thuê gia công: tăng kho thành phẩm, giảm nguyên liệu tại `supplier_warehouse`, và lập bút toán qua `SubcontractingReceiptGLComposer`. Sau đó đơn gốc, Job Card và Purchase Receipt (nếu bật) được cập nhật.

```mermaid
sequenceDiagram
    actor User
    participant SCR as SubcontractingReceipt
    participant SC as SubcontractingController
    participant SCO as SubcontractingOrder
    participant SLE as Stock Ledger Entry
    participant GLC as SubcontractingReceiptGLComposer
    participant GL as GL Entry
    participant JC as Job Card
    User->>SCR: make_subcontracting_receipt() rồi save
    SCR->>SC: validate()
    SCR->>SCR: set_missing_values(), calculate_items_qty_and_amount()
    User->>SCR: submit
    SCR->>SCR: on_submit(), validate_bom_required_qty()
    SCR->>SCO: update_prevdoc_status() cập nhật received_qty, per_received
    SCR->>SC: set_subcontracting_order_status(), set_consumed_qty_in_subcontract_order()
    SCR->>SCR: update_stock_reservation_entries()
    SCR->>SC: update_stock_ledger()
    SC->>SC: update_ordered_and_reserved_qty()
    SC->>SC: make_sl_entries_for_supplier_warehouse()
    SC->>SLE: make_sl_entries()
    SCR->>GLC: make_gl_entries() rồi get_gl_entries(), compose()
    GLC->>SLE: đọc stock_value_difference
    GLC-->>SCR: process_gl_map()
    SCR->>GL: make_gl_entries(gl_entries)
    SCR->>SCR: repost_future_sle_and_gle(), update_status()
    opt bật auto_create_purchase_receipt
        SCR->>SCR: auto_create_purchase_receipt() rồi make_purchase_receipt()
    end
    SCR->>JC: update_job_card() rồi set_manufactured_qty()
```

Nguồn: [subcontracting_receipt.py:209](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_receipt/subcontracting_receipt.py#L209), [subcontracting_controller.py:1277](../../apps/erpnext/erpnext/controllers/subcontracting_controller.py#L1277), [gl_composer.py:20](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_receipt/services/gl_composer.py#L20)

### Tạo và submit Subcontracting Inward Order

Đơn nhận gia công được tạo từ Sales Order. Khi lưu, đơn kiểm tra ít nhất một nguyên liệu do khách cung cấp và kho khách thuộc đúng khách hàng. Khi submit, đơn cập nhật `subcontracted_qty` trên Sales Order Item.

```mermaid
sequenceDiagram
    actor User
    participant SO as Sales Order
    participant SIO as SubcontractingInwardOrder
    participant SC as SubcontractingController
    participant SOI as Sales Order Item
    User->>SO: make_subcontracting_inward_order(source_name)
    SO->>SO: check_on_hold_or_closed_status(), is_so_fully_subcontracted()
    SO->>SIO: get_mapped_subcontracting_inward_order() rồi populate_items_table()
    User->>SIO: save
    SIO->>SC: validate() rồi create_raw_materials_supplied_or_received(received_items)
    SIO->>SIO: set_is_customer_provided_item()
    SIO->>SIO: validate_customer_provided_items()
    SIO->>SIO: validate_customer_warehouse(), validate_service_items()
    User->>SIO: submit
    SIO->>SIO: on_submit() rồi update_status()
    SIO->>SOI: update_subcontracted_quantity_in_so()
```

Nguồn: [mapper.py:1179](../../apps/erpnext/erpnext/selling/doctype/sales_order/mapper.py#L1179), [subcontracting_inward_order.py:69](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L69), [subcontracting_inward_order.py:78](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L78)

### Nhận nguyên liệu từ khách

`make_rm_stock_entry_inward` tạo Stock Entry mục đích `Receive from Customer`. Khi submit, nguyên liệu vào kho, `received_qty` được cập nhật và mỗi dòng sinh một Stock Reservation Entry gắn với Inward Order.

```mermaid
sequenceDiagram
    actor User
    participant SIO as SubcontractingInwardOrder
    participant SE as StockEntry
    participant SIC as SubcontractingInwardController
    participant SLE as Stock Ledger Entry
    participant GL as GL Entry
    participant SRE as Stock Reservation Entry
    User->>SIO: make_rm_stock_entry_inward()
    SIO-->>User: Stock Entry nháp, purpose Receive from Customer
    User->>SE: submit
    SE->>SIC: validate_subcontracting_inward()
    SE->>SLE: update_stock_ledger()
    SE->>GL: make_gl_entries()
    SE->>SIC: on_submit_subcontracting_inward()
    SIC->>SIO: update_inward_order_received_items_for_raw_materials_receipt()
    SIC->>SRE: create_stock_reservation_entries_for_inward()
    SIC->>SIO: update_inward_order_status() rồi set_subcontracting_inward_order_status()
    SIO->>SIO: update_status()
```

Nguồn: [subcontracting_inward_order.py:343](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L343), [subcontracting_inward_controller.py:20](../../apps/erpnext/erpnext/controllers/subcontracting_inward_controller.py#L20), [subcontracting_inward_controller.py:1067](../../apps/erpnext/erpnext/controllers/subcontracting_inward_controller.py#L1067)

### Sản xuất cho Inward Order

Số lượng Work Order bị chặn theo nguyên liệu đã nhận. Reservation chuyển từ Inward Order sang Work Order. Stock Entry `Manufacture` cập nhật lại sản lượng trên đơn.

```mermaid
sequenceDiagram
    actor User
    participant SIO as SubcontractingInwardOrder
    participant WO as WorkOrder
    participant SR as StockReservation
    participant SE as StockEntry
    participant SIC as SubcontractingInwardController
    participant SIOI as SubcontractingInwardOrderItem
    User->>SIO: make_work_order()
    SIO->>SIO: get_production_items(), get_pending_work_order_qty()
    SIO->>WO: create_work_order(item)
    WO->>WO: set_work_order_operations(), set_required_items(), insert()
    User->>WO: submit
    WO->>SIO: update_subcontracting_inward_order_received_items()
    opt reserve_stock
        WO->>SR: reserve_stock_for_work_order() rồi transfer_reservation_entries_to()
    end
    User->>SE: submit Stock Entry purpose Manufacture
    SE->>SIC: on_submit_subcontracting_inward()
    SIC->>SIOI: update_inward_order_item() rồi update_manufacturing_qty_fields()
    SIC->>SIO: update_inward_order_received_items_for_manufacture()
    SIC->>SIO: update_inward_order_secondary_items()
    SIC->>SIO: update_inward_order_status()
```

Nguồn: [subcontracting_inward_order.py:236](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L236), [work_order.py:751](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/work_order.py#L751), [subcontracting_inward_controller.py:685](../../apps/erpnext/erpnext/controllers/subcontracting_inward_controller.py#L685)

### Giao hàng và trả hàng Inward Order

Thành phẩm giao qua Stock Entry `Subcontracting Delivery`, trả về qua `Subcontracting Return`, nguyên liệu thừa trả khách qua `Return Raw Material to Customer`. Ba nhánh dùng cùng khung `on_submit` của Stock Entry.

```mermaid
sequenceDiagram
    actor User
    participant SIO as SubcontractingInwardOrder
    participant SE as StockEntry
    participant SLE as Stock Ledger Entry
    participant SIC as SubcontractingInwardController
    alt giao thành phẩm
        User->>SIO: make_subcontracting_delivery()
    else khách trả thành phẩm
        User->>SIO: make_subcontracting_return()
    else trả nguyên liệu
        User->>SIO: make_rm_return()
    end
    SIO-->>User: Stock Entry nháp
    User->>SE: submit
    SE->>SE: update_stock_reservation_entries()
    SE->>SLE: update_stock_ledger()
    SE->>SIC: on_submit_subcontracting_inward()
    alt purpose Return Raw Material to Customer
        SIC->>SIO: update_inward_order_received_items() cộng returned_qty
    else purpose Subcontracting Delivery hoặc Return
        SIC->>SIO: update_inward_order_item() cộng delivered_qty hoặc returned_qty
    end
    SIC->>SIO: update_inward_order_status()
```

Nguồn: [subcontracting_inward_order.py:454](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L454), [subcontracting_inward_order.py:531](../../apps/erpnext/erpnext/subcontracting/doctype/subcontracting_inward_order/subcontracting_inward_order.py#L531), [subcontracting_inward_controller.py:685](../../apps/erpnext/erpnext/controllers/subcontracting_inward_controller.py#L685)

## Giới hạn

- Không vẽ sequence cho Subcontracting BOM vì là danh mục. Hàm tra cứu chính là `get_finished_good_bom`.
- Trả hàng thuê gia công (`make_subcontract_return`, `make_subcontract_return_against_rejected_warehouse`) chỉ gọi `make_return_doc` trong `controllers/sales_and_purchase_return.py`, không đọc tiếp. `make_return_stock_entry_for_subcontract` và `get_materials_from_supplier` cũng không vẽ.
- Hủy chứng từ (`on_cancel`) không vẽ riêng. Thứ tự gọi gần như đối xứng nhưng có khác biệt, xem code khi cần.
- Đọc lướt `SubcontractingController` (1660 dòng): phần tính nguyên liệu `__set_supplied_or_received_items`, backflush, serial và batch không vẽ chi tiết. Đọc lướt `SubcontractingInwardController` (1279 dòng): phần validate theo `purpose` và `adjust_inward_reservations` không vẽ.
- `make_purchase_receipt` trong `subcontracting_receipt/mapper.py` chỉ đọc phần đầu nên sơ đồ dừng ở tên hàm.
- `SalesInvoice.update_billed_qty_in_scio` cập nhật `billed_qty` của Received Item. Luồng lập hóa đơn cho nguyên liệu khách cấp không đọc đủ nên không vẽ.
- Điểm nghi vấn trong code: `SubcontractingController.set_subcontracting_order_status` có dòng `self.__get_subcontract_orders` thiếu dấu gọi hàm, nên dòng đó không có tác dụng. Chưa chạy thử để xác nhận ảnh hưởng.
- `SubcontractingInwardOrder.update_status` chia cho `total_to_be_received` và `total_to_be_produced` không kèm kiểm tra bằng 0. `validate_customer_provided_items` có thể khiến trường hợp này không xảy ra, nhưng chưa xác minh.
- `make_rm_stock_entry` mặc định `order_doctype` là Subcontracting Order, và còn có nhánh Purchase Order. Sơ đồ chỉ vẽ nhánh mặc định.
