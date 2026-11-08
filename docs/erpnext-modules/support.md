# Module Support

Xử lý yêu cầu hỗ trợ (`Issue`), khiếu nại bảo hành (`Warranty Claim`) và cam kết mức dịch vụ (`Service Level Agreement`). SLA gắn được vào nhiều doctype khác `Issue` qua hook `validate` toàn cục. Module nối với `Communication` (frappe), `Maintenance Visit` (maintenance), `Serial No` (stock), `Task` (projects).

## Phạm vi

Đọc được 11 doctype trong `support/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
| --- | --- | --- |
| Yêu cầu hỗ trợ | `Issue`, `Issue Priority`, `Issue Type`, `Support Settings`, `Support Search Source` | Class diagram. Sequence: Lưu Issue và áp SLA, Communication cập nhật Issue, Tách Issue, Tạo Issue từ Communication, Tự đóng Issue |
| Mức dịch vụ | `Service Level Agreement`, `Service Level Priority`, `Service Day`, `Pause SLA On Status`, `SLA Fulfilled On Status` | Class diagram. Sequence: Cấu hình SLA, Đánh dấu SLA quá hạn, Reset SLA |
| Bảo hành | `Warranty Claim` | Class diagram. Sequence: Warranty Claim và tạo Maintenance Visit |

## Class diagram

```mermaid
classDiagram
    class TransactionBase
    class Issue {
        +string subject
        +string status
        +string customer
        +string raised_by
        +string priority
        +string service_level_agreement
        +datetime response_by
        +datetime sla_resolution_by
        +string agreement_status
        +set_lead_contact()
        +restore_staff_only_fields()
        +record_resolution_metrics()
        +create_communication()
        +split_issue()
    }
    class IssuePriority {
        +string description
    }
    class IssueType
    class ServiceLevelAgreement {
        +string service_level
        +string document_type
        +string entity_type
        +string entity
        +bool default_service_level_agreement
        +bool apply_sla_for_resolution
        +string holiday_list
        +bool enabled
        +check_priorities()
        +check_support_and_resolution()
        +validate_condition()
        +get_service_level_agreement_priority()
        +create_custom_fields()
        +create_docfields()
    }
    class ServiceLevelPriority {
        +string priority
        +bool default_priority
        +float response_time
        +float resolution_time
    }
    class ServiceDay {
        +string workday
        +string start_time
        +string end_time
    }
    class PauseSLAOnStatus {
        +string status
    }
    class SLAFulfilledOnStatus {
        +string status
    }
    class SLADeadline {
        +get()
        +get_previous_hold_seconds()
        +get_resumed_hold_seconds()
    }
    class WarrantyClaim {
        +string customer
        +string serial_no
        +string item_code
        +string status
        +date complaint_date
        +string warranty_amc_status
        +datetime resolution_date
        +set_resolution()
        +set_warranty_amc_status()
        +validate_no_active_visits()
    }
    class SupportSettings
    class SupportSearchSource {
        +string source_name
        +string source_type
        +string base_url
    }

    TransactionBase <|-- WarrantyClaim
    ServiceLevelAgreement *-- ServiceLevelPriority : priorities
    ServiceLevelAgreement *-- ServiceDay : support_and_resolution
    ServiceLevelAgreement *-- PauseSLAOnStatus : pause_sla_on
    ServiceLevelAgreement *-- SLAFulfilledOnStatus : sla_fulfilled_on
    SupportSettings *-- SupportSearchSource : search_apis
    Issue --> ServiceLevelAgreement : service_level_agreement
    Issue --> IssuePriority : priority
    Issue --> IssueType : issue_type
    Issue --> Issue : issue_split_from
    ServiceLevelAgreement --> IssuePriority : default_priority
    ServiceLevelPriority --> IssuePriority : priority
```

## Sequence diagram

### Lưu Issue và áp SLA

Hook `doc_events["*"]["validate"]` gọi `apply` cho mọi doctype, chạy sau `Issue.validate`. Không có SLA thì `before_save` vẫn ghi số liệu giải quyết.

```mermaid
sequenceDiagram
    actor User
    participant Issue
    participant Apply as service_level_agreement.py
    participant SLA as Service Level Agreement
    participant Deadline as SLADeadline
    participant Comm as Communication
    User->>Issue: save()
    Issue->>Issue: validate()
    Issue->>Issue: set_lead_contact(email_id)
    Issue->>Apply: apply(doc, method)
    Apply->>Apply: stays_resolved(doc)
    Apply->>SLA: get_active_service_level_agreement_for(doc)
    alt không có SLA phù hợp
        Apply->>Issue: remove_sla_if_applied(doc)
    else có SLA
        Apply->>Apply: process_sla(doc, sla)
        Apply->>Issue: handle_status_change(doc, apply_sla_for_resolution, hold_statuses, fulfillment_statuses)
        Apply->>SLA: get_response_and_resolution_duration(doc)
        Apply->>Deadline: set_response_by(doc, start_date_time, priority)
        opt apply_sla_for_resolution
            Apply->>Deadline: set_resolution_by(doc, start_date_time, priority)
        end
        Apply->>Issue: update_agreement_status(doc, apply_sla_for_resolution)
    end
    Issue->>Issue: before_save()
    opt không có service_level_agreement
        Issue->>Apply: record_resolution_metrics() gọi handle_status_change(doc)
    end
    Issue->>Issue: on_update()
    opt via_customer_portal và cờ create_communication
        Issue->>Comm: create_communication()
    end
    Issue->>Issue: on_change()
    opt status đổi sang Resolved hoặc Closed
        Issue->>Issue: close_all_assignments(doctype, name)
    end
```

Nguồn: [service_level_agreement.py:523](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L523), [service_level_agreement.py:568](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L568), [service_level_agreement.py:584](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L584), [issue.py:77](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L77)

### Communication cập nhật Issue

Frappe đổi `status` và `first_responded_on` của Issue bằng `db_set`. Các hook của ERPNext đảo lại thay đổi đó để `handle_status_change` đọc được trạng thái trước, rồi lưu Issue.

```mermaid
sequenceDiagram
    actor Sender as Người gửi hoặc nhận email
    participant Comm as Communication
    participant Apply as service_level_agreement.py
    participant Issue
    participant IssueMod as issue.py
    Sender->>Comm: on_update()
    Comm->>Issue: update_parent_document_on_communication(doc)
    opt Received
        Comm->>Issue: db_set(status, Open)
    end
    Comm->>Issue: update_first_response_time(parent, communication)
    Comm->>Apply: on_communication_update(doc, status)
    alt Received, parent Open và status đã đổi
        Apply->>Issue: set_value(status, trạng thái trước)
    else Sent và first_responded_on vừa được đặt
        Apply->>Issue: first_responded_on None, on_first_reply True
    else trường hợp khác hoặc parent không có SLA
        Apply-->>Comm: return
    end
    opt thuộc một trong hai nhánh trên
        Apply->>Issue: handle_status_change(parent, for_resolution, hold, fulfillment)
        Apply->>Issue: update_response_and_resolution_metrics(parent, for_resolution)
        Apply->>Issue: update_agreement_status(parent, for_resolution)
        Apply->>Issue: save(ignore_permissions=True)
    end
    Comm->>IssueMod: set_first_response_time(communication, method)
    opt là phản hồi đầu tiên và có SLA
        IssueMod->>Issue: calculate_first_response_time() rồi db_set(first_response_time)
    end
    Comm->>IssueMod: reopen_issue_without_sla(communication, method)
    opt Received, không có SLA và đã có sla_resolution_date
        IssueMod->>Issue: set_value(status, previous_status) rồi save()
    end
```

Nguồn: [service_level_agreement.py:869](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L869), [issue.py:414](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L414), [issue.py:422](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L422), [communication.py:673](../../apps/frappe/frappe/core/doctype/communication/communication.py#L673)

### Tách Issue

Từ một Communication trên timeline, sao Issue thành Issue mới, reset số liệu và SLA, rồi chuyển các Communication từ điểm tách trở đi sang Issue mới.

```mermaid
sequenceDiagram
    actor User
    participant Issue as Issue gốc
    participant New as Issue mới
    participant Comm as Communication
    participant Cmt as Comment
    User->>Issue: split_issue(subject, communication_id)
    Issue->>Issue: check_permission(write)
    Issue->>Issue: get_timeline_communications()
    opt communication_id không thuộc timeline
        Issue-->>User: throw PermissionError
    end
    Issue->>New: deepcopy(self) reset số liệu rồi insert()
    opt Issue gốc có service_level_agreement
        Issue->>New: đặt lại service_level_agreement_creation, agreement_status
    end
    Issue->>Issue: get_timeline_communications(after=communication_date)
    loop mỗi Communication từ điểm tách
        Issue->>Comm: đổi reference_name và timeline_links rồi save()
    end
    Issue->>Cmt: insert()
    Issue-->>User: tên Issue mới
```

Nguồn: [issue.py:201](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L201), [issue.py:168](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L168)

### Tạo Issue từ Communication

Nút trên form Communication tạo Issue mới và liên kết email vào đó.

```mermaid
sequenceDiagram
    actor User
    participant Form as Form Communication
    participant IssueMod as issue.py
    participant Comm as Communication
    participant Issue
    User->>Form: make_issue_from_communication
    Form->>IssueMod: make_issue_from_communication(communication, ignore_communication_links)
    IssueMod->>Comm: has_permission(Communication, doc)
    IssueMod->>IssueMod: get_customer_email(communication)
    IssueMod->>Issue: insert()
    IssueMod->>Comm: link_communication_to_document(doc, Issue, name, ignore_links)
    IssueMod-->>Form: tên Issue
```

Nguồn: [issue.py:374](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L374), [issue.py:399](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L399)

### Tự đóng Issue

Job `daily_maintenance` đóng Issue ở trạng thái Replied quá `close_issue_after_days` ngày không đổi.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant IssueMod as issue.py
    participant Settings as Support Settings
    participant Issue
    Sched->>IssueMod: auto_close_tickets()
    IssueMod->>Settings: get_single_value(close_issue_after_days)
    opt giá trị bằng 0 hoặc trống
        IssueMod-->>Sched: return
    end
    IssueMod->>Issue: chọn status Replied và modified quá hạn
    loop mỗi Issue
        IssueMod->>Issue: get_doc(Issue, issue)
        IssueMod->>Issue: status Closed rồi save()
    end
```

Nguồn: [issue.py:326](../../apps/erpnext/erpnext/support/doctype/issue/issue.py#L326)

### Cấu hình Service Level Agreement

Insert SLA cho doctype khác `Issue` sẽ thêm các field SLA vào doctype đó. Mọi thay đổi cập nhật cache danh sách doctype có SLA, được `apply` đọc.

```mermaid
sequenceDiagram
    actor User
    participant SLA as Service Level Agreement
    participant Meta as DocType đích
    participant Field as DocField hoặc Custom Field
    participant Cache
    User->>SLA: insert()
    SLA->>SLA: before_insert()
    opt document_type khác Issue
        SLA->>SLA: get_service_level_agreement_fields(doctype)
        alt meta.custom
            SLA->>Field: create_docfields(meta, fields)
            SLA->>Meta: save()
        else doctype chuẩn
            SLA->>Field: create_custom_fields(meta, fields)
        end
    end
    SLA->>SLA: validate_selected_doctype()
    SLA->>SLA: validate_doc()
    SLA->>Meta: validate_status_field()
    SLA->>SLA: check_priorities()
    SLA->>SLA: check_support_and_resolution()
    SLA->>SLA: validate_condition()
    SLA->>Cache: after_insert() gọi set_documents_with_active_service_level_agreement()
    SLA->>Cache: on_update() gọi set_documents_with_active_service_level_agreement()
```

Nguồn: [service_level_agreement.py:69](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L69), [service_level_agreement.py:230](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L230), [service_level_agreement.py:509](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L509)

### Đánh dấu SLA quá hạn

Job `hourly` đánh dấu `Failed` cho chứng từ đang mở đã quá hạn, không tính chứng từ đang giữ. Job `daily_maintenance` tắt SLA đã qua `end_date`.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Job as service_level_agreement.py
    participant Settings as Support Settings
    participant Doc as Issue hoặc doctype có SLA
    participant SLA as Service Level Agreement
    Sched->>Job: fail_overdue_agreements()
    Job->>Settings: get_single_value(track_service_level_agreement)
    Job->>SLA: get_sla_doctypes()
    loop mỗi doctype
        Job->>Doc: get_overdue_documents(doctype)
        loop mỗi chứng từ
            Job->>Doc: fail_agreement_if_overdue(doctype, name)
            Job->>Job: is_overdue(doc)
            opt vẫn quá hạn sau khi khóa
                Job->>Doc: db_set(agreement_status, Failed)
            end
        end
    end
    Sched->>Job: check_agreement_status()
    loop mỗi SLA enabled
        opt end_date đã qua
            Job->>SLA: set_value(enabled, 0)
        end
    end
```

Nguồn: [service_level_agreement.py:1146](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L1146), [service_level_agreement.py:1171](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L1171), [service_level_agreement.py:331](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L331)

### Reset Service Level Agreement

Nút Reset trên form tính lại thời hạn tính từ thời điểm hiện tại, nếu `Support Settings` cho phép.

```mermaid
sequenceDiagram
    actor User
    participant Job as service_level_agreement.py
    participant Settings as Support Settings
    participant Doc as Issue hoặc doctype có SLA
    participant Cmt as Comment
    User->>Job: reset_service_level_agreement(doctype, docname, reason, user)
    Job->>Settings: get_single_value(allow_resetting_service_level_agreement)
    Job->>Doc: check_permission(write)
    Job->>Cmt: insert()
    Job->>Doc: đặt service_level_agreement_creation rồi save()
    Doc->>Job: apply(doc, method)
    opt có SLA áp dụng
        Job->>Doc: process_sla(doc, sla)
    end
```

Nguồn: [service_level_agreement.py:836](../../apps/erpnext/erpnext/support/doctype/service_level_agreement/service_level_agreement.py#L836)

### Warranty Claim và tạo Maintenance Visit

`Warranty Claim` không submit được, trạng thái thay đổi bằng lưu tay hoặc qua `Maintenance Visit`. Khi đã có visit `Fully Completed`, mapper không trả bản nháp nào.

```mermaid
sequenceDiagram
    actor User
    participant WC as Warranty Claim
    participant SN as Serial No
    participant Mapper as get_mapped_doc
    participant MV as Maintenance Visit
    User->>WC: save()
    WC->>SN: validate_serial_no()
    WC->>SN: warn_if_serial_no_not_delivered_to_customer()
    opt status vừa đổi sang Cancelled
        WC->>MV: validate_no_active_visits()
    end
    WC->>WC: set_resolution()
    WC->>WC: set_warranty_amc_status()
    User->>WC: make_maintenance_visit(source_name, target_doc)
    WC->>MV: tìm visit Fully Completed đã submit
    opt chưa có
        WC->>Mapper: get_mapped_doc(Warranty Claim, source_name)
        Mapper->>MV: tạo bản nháp
        opt claim có item_code
            WC->>MV: map_child_doc() gọi _update_links(source_doc, target_doc, source_parent)
        end
    end
    User->>MV: submit()
    MV->>WC: update_customer_issue(1) rồi db_update()
```

Nguồn: [warranty_claim.py:53](../../apps/erpnext/erpnext/support/doctype/warranty_claim/warranty_claim.py#L53), [warranty_claim.py:147](../../apps/erpnext/erpnext/support/doctype/warranty_claim/warranty_claim.py#L147), [maintenance_visit.py:202](../../apps/erpnext/erpnext/maintenance/doctype/maintenance_visit/maintenance_visit.py#L202)

## Giới hạn

- `Issue Type`, `Issue Priority`, `Support Settings`, `Support Search Source` chỉ là cấu hình, không có sequence. Thư mục `page`, `web_form`, `report` chưa đọc.
- `Issue` kế thừa `Document` và `ServiceLevelAgreement` cũng vậy, nên không vẽ quan hệ `<|--` với class ngoài module. Vì các field SLA có thể thêm vào doctype bất kỳ, sơ đồ dùng tên chung `Issue hoặc doctype có SLA`.
- `handle_status_change` có sáu nhánh chuyển trạng thái (open, hold, fulfilled) và `SLADeadline` tính hold theo giờ làm việc. Sơ đồ chỉ vẽ lời gọi, không vẽ từng nhánh. `add_working_seconds` và `calculate_first_response_time` chỉ đọc qua.
- Thứ tự giữa `update_parent_document_on_communication` và ba hook `on_update` lấy từ `Document.hook` trong `frappe/model/document.py` (controller chạy trước, `doc_events` sau) và thứ tự danh sách trong `hooks.py`. `Communication.on_update` có thêm bước khác ở đầu hàm, không vẽ.
- Frappe gọi `parent.run_method("handle_hold_time", "Replied")` trong `communication.py`, nhưng trong `.py` của ERPNext và Frappe đã tìm không có method này, nên không vẽ.
- Bước `chọn status Replied`, `đổi reference_name`, `tìm visit Fully Completed`, `tạo bản nháp` là mô tả truy vấn hoặc phép gán, không phải tên hàm.
