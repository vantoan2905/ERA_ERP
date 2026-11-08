# Module Bulk Transaction

Module chỉ chứa nhật ký cho việc tạo chứng từ hàng loạt từ list view; logic xử lý nằm ở `erpnext/utilities/bulk_transaction.py`. Hàm `task` gọi các mapper của `selling`, `buying`, `stock`, `accounts` để chuyển đổi chứng từ.

## Phạm vi

Đọc được 2 doctype trong `bulk_transaction/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Tạo chứng từ hàng loạt | `utilities/bulk_transaction.py`, `public/js/bulk_transaction_processing.js` | Sequence: Tạo hàng loạt |
| Chạy lại phần lỗi | `utilities/bulk_transaction.py` (`retry`) | Sequence: Chạy lại giao dịch lỗi |
| Nhật ký | `Bulk Transaction Log` (virtual), `Bulk Transaction Log Detail` | Class. Sequence: Xem nhật ký |

## Class diagram

`Bulk Transaction Log` là virtual doctype, không có bảng riêng: mỗi "bản ghi" là số liệu gộp theo ngày từ `Bulk Transaction Log Detail`. Hai doctype không có Link với nhau, chỉ khớp qua field `date`.

```mermaid
classDiagram
    class BulkTransactionLog {
        +date date
        +int log_entries
        +int succeeded
        +int failed
        +load_from_db()
        +get_list()
        +get_count()
        +db_insert()
        +db_update()
        +delete()
    }
    class BulkTransactionLogDetail {
        +string transaction_name
        +string transaction_status
        +string error_description
        +string from_doctype
        +string to_doctype
        +date date
        +string time
        +int retried
    }
    BulkTransactionLog ..> BulkTransactionLogDetail : gop theo date
```

## Sequence diagram

### Tạo hàng loạt

Người dùng chọn chứng từ đã submit trên list view; server kiểm tra quyền từng chứng từ, bỏ qua chứng từ On Hold hoặc Closed, rồi enqueue một job. Mỗi chứng từ chạy trong một savepoint riêng để lỗi không kéo theo các chứng từ khác.

```mermaid
sequenceDiagram
    actor User
    participant JS as bulk_transaction_processing.js
    participant BT as bulk_transaction.py
    participant Q as RQ queue
    participant Map as Mapper của doctype
    participant Doc as Chứng từ đích
    participant Log as Bulk Transaction Log Detail
    User->>JS: create(listview, from_doctype, to_doctype)
    alt có dòng docstatus 0
        JS-->>User: Selected document must be in submitted state
    else tất cả đã submit
        JS->>BT: transaction_processing(data, from_doctype, to_doctype, args)
        BT->>BT: has_permission từng doctype và từng chứng từ
        BT->>BT: get_statuses, loại On Hold và Closed
        BT->>Q: enqueue job
        Q->>BT: job(deserialized_data, from_doctype, to_doctype, args)
        loop mỗi chứng từ
            BT->>BT: savepoint(before_creation_state)
            BT->>Map: task: mapper[from_doctype][to_doctype]
            Map-->>BT: obj
            BT->>Doc: set_title_field, insert(ignore_mandatory=True)
            alt thành công
                BT->>Log: create_log(status=Success)
            else exception
                BT->>BT: rollback về savepoint
                BT->>Log: create_log(traceback, status=Failed)
            end
        end
        BT-->>User: show_job_status qua msgprint realtime
    end
```

Nguồn: [bulk_transaction.py:10](../../apps/erpnext/erpnext/utilities/bulk_transaction.py#L10), [bulk_transaction.py:140](../../apps/erpnext/erpnext/utilities/bulk_transaction.py#L140), [bulk_transaction.py:169](../../apps/erpnext/erpnext/utilities/bulk_transaction.py#L169)

### Chạy lại giao dịch lỗi

Được gọi từ nút trên form Bulk Transaction Log hoặc từ job `hourly_maintenance` (không truyền `date` thì lấy hôm nay). Log đã có bản Success sau đó thì chỉ đánh dấu `retried`.

```mermaid
sequenceDiagram
    participant Src as Nút Retry hoặc Scheduler
    participant BT as bulk_transaction.py
    participant Log as Bulk Transaction Log Detail
    participant Q as RQ queue
    participant Doc as Chứng từ đích
    Src->>BT: retry(date)
    BT->>BT: only_for(System Manager)
    BT->>Log: get_all Failed, retried = 0, theo date
    alt không có log lỗi
        BT-->>Src: There are no Failed transactions
    else có log lỗi
        BT->>Q: enqueue retry_failed_transactions(failed_docs)
        Q->>BT: retry_failed_transactions
        loop mỗi log
            BT->>Log: succeeded_since(log)
            alt đã thành công ở lần chạy sau
                BT->>Log: update_log(Failed, retried = 1)
            else chưa
                BT->>Doc: savepoint, task(transaction_name, from_doctype, to_doctype)
                alt thành công
                    BT->>Log: update_log(Success, retried = 1)
                else exception
                    BT->>BT: rollback về savepoint
                    BT->>Log: update_log(Failed, retried = 1, traceback)
                end
            end
        end
    end
```

Nguồn: [bulk_transaction.py:75](../../apps/erpnext/erpnext/utilities/bulk_transaction.py#L75), [bulk_transaction.py:100](../../apps/erpnext/erpnext/utilities/bulk_transaction.py#L100)

### Xem nhật ký

Danh sách và form của doctype virtual được tính trực tiếp bằng truy vấn gộp trên bảng detail.

```mermaid
sequenceDiagram
    actor User
    participant FW as Frappe list và form
    participant BTL as Bulk Transaction Log
    participant Det as Bulk Transaction Log Detail
    User->>FW: mở list view
    FW->>BTL: get_list(args)
    BTL->>BTL: has_permission(read), parse_list_filters
    BTL->>Det: group by date, count_with_status
    Det-->>BTL: số liệu theo ngày
    BTL-->>FW: serialize_transaction_log
    User->>FW: mở form một ngày
    FW->>BTL: load_from_db
    alt không có detail của ngày
        BTL-->>FW: DoesNotExistError
    else có detail
        BTL->>Det: đếm Success và Failed
        BTL->>BTL: init_from_dict
    end
```

Nguồn: [bulk_transaction_log.py:33](../../apps/erpnext/erpnext/bulk_transaction/doctype/bulk_transaction_log/bulk_transaction_log.py#L33), [bulk_transaction_log.py:65](../../apps/erpnext/erpnext/bulk_transaction/doctype/bulk_transaction_log/bulk_transaction_log.py#L65)

## Giới hạn

- Bảng mapper trong `task` có 8 doctype nguồn và có thể được mở rộng qua hook `bulk_transaction_task_mapper`; nội dung từng mapper thuộc tài liệu module tương ứng.
- Chứng từ đích được `insert` với `flags.ignore_validate = True` và ở trạng thái Draft; `task` không gọi `submit`.
- `retry_failed_transactions` không truyền `frappe.flags.args` như `job`, nên khi chạy lại `args` ban đầu không được áp dụng. Đây là suy ra từ code, chưa chạy thử.
- `retry` có `only_for("System Manager")`; khi chạy từ scheduler vẫn qua được nếu session là Administrator (`only_for` bỏ qua Administrator). Chưa xác nhận session user của scheduler trong site này.
- `retry` trên scheduler chỉ xử lý log của ngày hôm nay.
