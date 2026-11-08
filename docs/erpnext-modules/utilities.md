# Module Utilities

Module `utilities` là phần dùng chung, trong đó quan trọng nhất là `TransactionBase`, lớp cha của mọi controller giao dịch trong `controllers/`. Phần còn lại là các tiện ích nhỏ: đổi tên hàng loạt, đồng bộ thống kê YouTube, import Customer/Supplier kèm liên hệ, và các hàm dùng lại ở module khác.

## Phạm vi

Đọc được 4 doctype trong `utilities/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Lớp cha giao dịch | `transaction_base.py` | Class. Sequence: Chọn item trên chứng từ |
| Đổi tên hàng loạt | `Rename Tool` | Class. Sequence: Rename Tool |
| Video | `Video`, `Video Settings`, report `youtube_interactions` | Class. Sequence: Đồng bộ thống kê YouTube |
| Import party | `party_import_provider.py` | Class. Sequence: Import Customer/Supplier |
| Tạo chứng từ hàng loạt | `bulk_transaction.py` | Xem [bulk_transaction.md](bulk_transaction.md) |
| Portal | `Portal User` (bảng con) | Class |
| Hàm dùng chung | `activation.py`, `naming.py`, `query.py`, `product.py`, `regional.py`, `email_template.py` | Không vẽ, xem Giới hạn |

## Class diagram

```mermaid
classDiagram
    class StatusUpdater
    class TransactionBase {
        +on_change()
        +validate_posting_time()
        +validate_uom_is_integer()
        +validate_with_previous_doc()
        +compare_values()
        +validate_rate_with_reference_doc()
        +process_item_selection()
        +fetch_item_details()
    }
    class AccountsController
    class StockController
    class SellingController
    class Video {
        +string title
        +string provider
        +string url
        +string youtube_video_id
        +float view_count
        +float like_count
        +validate()
        +set_video_id()
        +set_youtube_statistics()
    }
    class VideoSettings {
        +bool enable_youtube_tracking
        +string api_key
        +string frequency
        +string last_youtube_update
        +validate()
        +validate_youtube_api_key()
    }
    class RenameTool {
        +string select_doctype
        +string file_to_rename
    }
    class PortalUser {
        +string user
    }
    class ImportProvider
    class PartyImportProvider {
        +get_import_fields()
        +import_row()
        +get_export_rows()
    }
    StatusUpdater <|-- TransactionBase
    TransactionBase <|-- AccountsController
    AccountsController <|-- StockController
    StockController <|-- SellingController
    ImportProvider <|-- PartyImportProvider
```

## Sequence diagram

### Chọn item trên chứng từ

Khi người dùng chọn item trên form, phía client gọi method `process_item_selection` của server để lấy chi tiết item, tính lại giá và thuế trên chính document đó.

```mermaid
sequenceDiagram
    actor User
    participant JS as transaction.js
    participant TB as TransactionBase
    participant GID as get_item_details.py
    User->>JS: chọn item_code trên dòng items
    JS->>TB: process_item_selection(item_idx, reset_item_details, parentfield)
    TB->>TB: get_selected_item_row(parentfield, item_idx)
    opt reset_item_details
        TB->>TB: xóa weight_per_unit, uom, conversion_factor, barcode, pricing_rules
    end
    TB->>GID: fetch_item_details: _get_item_details(ctx, doc)
    GID-->>TB: item_details
    TB->>TB: set_fetched_values
    alt doctype là Request for Quotation
        TB-->>JS: return
    else doctype khác
        TB->>TB: set_item_rate_and_discounts
        TB->>TB: add_taxes_from_item_template, add_free_item
        TB->>TB: handle_internal_parties
        TB->>TB: conversion_factor
        TB->>TB: calculate_taxes_and_totals
    end
```

Nguồn: [transaction_base.py:361](../../apps/erpnext/erpnext/utilities/transaction_base.py#L361)

### Rename Tool

Đọc file CSV đính kèm và chia mỗi 500 dòng thành một job đổi tên; các dòng lỗi được báo qua Notification Log.

```mermaid
sequenceDiagram
    actor User
    participant RT as rename_tool.py
    participant File as File
    participant Q as RQ long queue
    participant FR as frappe bulk_rename
    participant NL as Notification Log
    User->>RT: upload(select_doctype, file_to_rename)
    RT->>RT: validate_access(doctype)
    RT->>File: get_file_to_rename, read_csv_content
    loop mỗi 500 dòng
        RT->>Q: enqueue rename_rows, enqueue_after_commit
    end
    RT->>File: delete_file_to_rename
    Q->>RT: rename_rows(doctype, rows)
    RT->>FR: bulk_rename(doctype, rows)
    FR-->>RT: kết quả từng dòng
    opt có dòng lỗi
        RT->>NL: notify_failed_rows
    end
```

Nguồn: [rename_tool.py:45](../../apps/erpnext/erpnext/utilities/doctype/rename_tool/rename_tool.py#L45)

### Đồng bộ thống kê YouTube

Job `hourly_maintenance` kiểm tra đã đến kỳ theo `frequency` chưa, rồi cập nhật thống kê theo lô 50 video.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant Mod as video.py
    participant VS as Video Settings
    participant YT as YouTube Api
    participant V as Video
    Sch->>Mod: update_youtube_data()
    Mod->>VS: get_single
    alt tracking tắt hoặc is_update_due sai
        Mod-->>Sch: return
    else đến kỳ
        Mod->>Mod: batch_update_youtube_data()
        Mod->>V: get_all provider YouTube có youtube_video_id
        loop mỗi lô tối đa 50 video
            Mod->>YT: get_video_by_id(video_ids)
            YT-->>Mod: statistics
            Mod->>V: set_value like_count, view_count, dislike_count, comment_count
        end
        Mod->>VS: set_single_value last_youtube_update
    end
```

Nguồn: [video.py:75](../../apps/erpnext/erpnext/utilities/doctype/video/video.py#L75)

### Import Customer/Supplier

Đăng ký qua hook `data_import_providers`; Data Import của Frappe giao từng dòng cho provider để tạo party cùng Contact và Address liên kết.

```mermaid
sequenceDiagram
    actor User
    participant Imp as frappe Importer
    participant PIP as PartyImportProvider
    participant Party as Customer hoặc Supplier
    participant Ct as Contact
    participant Ad as Address
    User->>Imp: chạy Data Import
    Imp->>PIP: process_doc: import_row(importer, doc)
    PIP->>PIP: tách contacts, addresses khỏi doc
    PIP->>Party: _persist_party: insert_record, update_record hoặc upsert_record
    loop mỗi dòng contacts
        PIP->>Ct: _create_contacts: dùng lại Contact trùng email hoặc mobile, không thì insert
    end
    opt có primary contact
        PIP->>Ct: _demote_other_primary_contacts, is_primary_contact = 1
        PIP->>Party: db_set primary_contact, mobile_no, email_id
    end
    loop mỗi dòng addresses
        PIP->>Ad: _create_addresses: dùng lại hoặc insert
    end
    opt có primary address
        PIP->>Ad: is_primary_address = 1, save
        PIP->>Party: db_set primary_address
    end
    PIP-->>Imp: party, import_action
```

Nguồn: [party_import_provider.py:40](../../apps/erpnext/erpnext/utilities/party_import_provider.py#L40)

## Giới hạn

- `bulk_transaction.py` nằm ở thư mục này nhưng được viết trong [bulk_transaction.md](bulk_transaction.md) để tránh trùng.
- `TransactionBase` chỉ vẽ một luồng; các hàm validate (`validate_with_previous_doc`, `validate_rate_with_reference_doc`, `validate_uom_is_integer`) được luồng của từng chứng từ gọi, xem tài liệu của module đó.
- `conversion_factor`, `calculate_taxes_and_totals` trong luồng chọn item gọi trên `self`; không đọc chi tiết `calculate_taxes_and_totals` và phần áp bảng giá trong `_apply_price_list`.
- Hàm dùng chung không vẽ vì không có luồng riêng: `activation.get_level`, `get_help_messages` (đo mức sử dụng), `naming.set_by_naming_series`, `query.py` (điều kiện truy vấn), `product.get_price`, `product.get_item_codes_by_attributes`, `regional.temporary_flag`, `email_template.get_email_subject_and_message`, `__init__.get_site_info`, `clear_logs_with_references`.
- `get_export_rows` của `PartyImportProvider`, report `youtube_interactions` và web form `addresses` không vẽ.
- `set_youtube_statistics` chạy khi lưu một Video nếu bật tracking; chỉ gọi API cho một video, không có luồng riêng.
- `Portal User` chỉ có field `user`. Đã thấy dùng trong field `portal_users` của Customer và Supplier.
