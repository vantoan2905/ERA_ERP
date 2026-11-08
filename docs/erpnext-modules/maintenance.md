# Module Maintenance

Quản lý bảo trì sau bán cho khách hàng: lập lịch bảo trì theo item và ghi nhận các lần đi bảo trì. Module nối với `Sales Order` (selling) khi tạo chứng từ, `Serial No` (stock) cho hạn AMC, `Warranty Claim` (support) và `Event` (frappe). Module không ghi `GL Entry` hay `Stock Ledger Entry`.

## Phạm vi

Đọc được 5 doctype trong `maintenance/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
| --- | --- | --- |
| Lịch bảo trì | `Maintenance Schedule`, `Maintenance Schedule Item`, `Maintenance Schedule Detail` | Class diagram. Sequence: Tạo và submit Maintenance Schedule, Cancel Maintenance Schedule |
| Lần bảo trì | `Maintenance Visit`, `Maintenance Visit Purpose` | Class diagram. Sequence: Tạo Maintenance Visit từ lịch, Submit và cancel Maintenance Visit |

## Class diagram

```mermaid
classDiagram
    class StatusUpdater
    class TransactionBase
    class MaintenanceSchedule {
        +string customer
        +string company
        +date transaction_date
        +string status
        +generate_schedule()
        +create_schedule_list()
        +validate_end_date_visits()
        +validate_serial_no()
        +update_amc_date()
        +get_pending_data()
    }
    class MaintenanceScheduleItem {
        +string item_code
        +date start_date
        +date end_date
        +string periodicity
        +int no_of_visits
        +string sales_person
        +string sales_order
        +string serial_and_batch_bundle
    }
    class MaintenanceScheduleDetail {
        +string item_code
        +date scheduled_date
        +date actual_date
        +string completion_status
        +string sales_person
        +string item_reference
    }
    class MaintenanceVisit {
        +string customer
        +date mntc_date
        +string maintenance_type
        +string completion_status
        +string status
        +update_status_and_actual_date()
        +update_customer_issue()
        +check_if_last_visit()
        +validate_schedule_details()
    }
    class MaintenanceVisitPurpose {
        +string item_code
        +string serial_no
        +string service_person
        +string work_done
        +string prevdoc_doctype
        +string prevdoc_docname
        +string maintenance_schedule_detail
    }

    StatusUpdater <|-- TransactionBase
    TransactionBase <|-- MaintenanceSchedule
    TransactionBase <|-- MaintenanceVisit
    MaintenanceSchedule *-- MaintenanceScheduleItem : items
    MaintenanceSchedule *-- MaintenanceScheduleDetail : schedules
    MaintenanceVisit *-- MaintenanceVisitPurpose : purposes
    MaintenanceScheduleDetail --> MaintenanceScheduleItem : item_reference
    MaintenanceVisit --> MaintenanceSchedule : maintenance_schedule
    MaintenanceVisit --> MaintenanceScheduleDetail : maintenance_schedule_detail
```

## Sequence diagram

### Tạo và submit Maintenance Schedule

`validate` tự sinh các dòng `schedules` khi cần. Submit kiểm tra serial, cập nhật hạn AMC và tạo một `Event` cho mỗi ngày bảo trì.

```mermaid
sequenceDiagram
    actor User
    participant MS as Maintenance Schedule
    participant Holiday as Holiday List
    participant SN as Serial No
    participant Event
    User->>MS: save()
    MS->>MS: validate_end_date_visits()
    MS->>MS: validate_maintenance_detail()
    MS->>MS: validate_sales_order()
    MS->>MS: validate_serial_no_bundle()
    opt chưa có schedules, items đổi hoặc số lượt lệch
        MS->>MS: generate_schedule()
        MS->>MS: create_schedule_list(start_date, end_date, no_of_visit, sales_person)
        MS->>Holiday: validate_schedule_date_for_holiday_list(schedule_date, sales_person, start_date)
    end
    MS->>MS: on_update() đặt status Draft
    User->>MS: submit()
    MS->>MS: on_submit()
    MS->>MS: check_serial_no_added()
    MS->>MS: validate_schedule()
    loop mỗi dòng items
        opt có serial
            MS->>SN: validate_serial_no(item_code, serial_nos, start_date)
            MS->>SN: update_amc_date(serial_nos, end_date)
        end
        loop mỗi scheduled_date
            MS->>Event: add_participant() rồi insert()
        end
    end
    MS->>MS: db_set(status, Submitted)
```

Nguồn: [maintenance_schedule.py:275](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L275), [maintenance_schedule.py:54](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L54), [maintenance_schedule.py:104](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L104)

### Cancel Maintenance Schedule

Trả hạn AMC của serial về ngày kết thúc mới nhất ở các lịch khác và xóa các `Event`.

```mermaid
sequenceDiagram
    actor User
    participant MS as Maintenance Schedule
    participant Other as Maintenance Schedule Item khác
    participant SN as Serial No
    participant Event
    User->>MS: cancel()
    MS->>MS: on_cancel()
    loop mỗi dòng items
        MS->>SN: get_serial_nos_with_row_amc_date(item)
        opt còn serial mang hạn AMC của dòng này
            MS->>Other: get_other_amc_expiry_dates(item_code, serial_nos)
            MS->>SN: update_amc_date(serial_nos, amc_expiry_date)
        end
    end
    MS->>MS: db_set(status, Cancelled)
    MS->>Event: delete_events(ref_type, ref_name)
```

Nguồn: [maintenance_schedule.py:457](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L457), [maintenance_schedule.py:468](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L468)

### Tạo Maintenance Visit từ lịch

Form lịch hỏi item và ngày qua `get_pending_data`, rồi map sang một Maintenance Visit nháp loại Scheduled.

```mermaid
sequenceDiagram
    actor User
    participant Form as Form Maintenance Schedule
    participant MS as Maintenance Schedule
    participant Mapper as get_mapped_doc
    participant MV as Maintenance Visit
    User->>Form: chọn tạo Visit
    Form->>MS: get_pending_data(data_type, s_date, item_name)
    MS-->>Form: item, ngày và tên dòng lịch còn Pending
    Form->>MS: make_maintenance_visit(source_name, target_doc, item_name, s_id)
    MS->>Mapper: get_mapped_doc(Maintenance Schedule, source_name)
    loop dòng Maintenance Schedule Detail thỏa condition()
        Mapper->>MV: update_serial(source, target, parent)
    end
    Mapper->>MV: update_status_and_detail(source, target, parent)
    MS-->>Form: bản nháp Maintenance Visit
```

Nguồn: [maintenance_schedule.py:607](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L607), [maintenance_schedule.py:496](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_schedule/maintenance_schedule.py#L496)

### Submit và cancel Maintenance Visit

Lần bảo trì cập nhật tiến độ dòng lịch và, khi đi từ `Warranty Claim` mà không gắn lịch, cập nhật trạng thái khiếu nại.

```mermaid
sequenceDiagram
    actor User
    participant MV as Maintenance Visit
    participant SN as Serial No
    participant WC as Warranty Claim
    participant MSD as Maintenance Schedule Detail
    User->>MV: save()
    MV->>SN: validate_serial_no()
    MV->>MV: validate_schedule_details()
    MV->>MV: validate_maintenance_date()
    MV->>MV: validate_purpose_table()
    alt submit
        User->>MV: submit()
        MV->>WC: update_customer_issue(1)
        MV->>MV: db_set(status, Submitted)
    else cancel
        User->>MV: cancel()
        MV->>MV: check_if_last_visit()
        opt có Warranty Claim và không còn visit muộn hơn
            MV->>WC: update_customer_issue(0)
        end
        MV->>MV: db_set(status, Cancelled)
    end
    MV->>MV: update_status_and_actual_date()
    MV->>MV: get_submitted_schedule_visits(details)
    MV->>MSD: set_value(completion_status, actual_date)
```

Nguồn: [maintenance_visit.py:147](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_visit/maintenance_visit.py#L147), [maintenance_visit.py:317](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_visit/maintenance_visit.py#L317), [maintenance_visit.py:202](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_visit/maintenance_visit.py#L202), [maintenance_visit.py:153](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_visit/maintenance_visit.py#L153)

## Giới hạn

- `update_customer_issue` chỉ tác động khi Visit không có `maintenance_schedule` và dòng `purposes` có `prevdoc_doctype` là `Warranty Claim`. Nó bỏ qua khiếu nại đã được một visit `Fully Completed` khác đóng (`is_superseded_by_completed_visit`). Luồng tạo Visit từ khiếu nại nằm ở `support.md`.
- Mapper `make_maintenance_schedule` và `make_maintenance_visit` trong `selling/doctype/sales_order/mapper.py` chỉ đọc phần map, không vẽ. Visit tạo từ `Sales Order` có `prevdoc_doctype` khác `Warranty Claim`.
- Thư mục `maintenance/report` chưa đọc. Job `update_maintenance_status` trong `stock/doctype/serial_no/serial_no.py` thuộc stock, không vẽ.
- File `.js` chỉ đọc đoạn gọi `make_maintenance_visit`; tên bước `chọn tạo Visit` là mô tả, không phải tên hàm.
