# Module Telephony

Module `telephony` lưu lịch sử cuộc gọi (`Call Log`), tự liên kết cuộc gọi với Contact, Lead, Customer theo số điện thoại và đẩy popup realtime cho nhân viên. Module nối với `crm` (tra số điện thoại), `communication` (lịch trực) và `setup` (Employee). Trong app này không có code tạo Call Log; bản ghi đến từ bên ngoài, ví dụ app tích hợp tổng đài.

## Phạm vi

Đọc được 5 doctype trong `telephony/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Cuộc gọi | `Call Log`, `Telephony Call Type` | Class. Sequence: 3 luồng cuộc gọi |
| Liên kết hội thoại cũ | `call_log.py` (`link_existing_conversations`) | Sequence: Liên kết cuộc gọi cũ |
| Cấu hình | `Incoming Call Settings`, `Incoming Call Handling Schedule`, `Voice Call Settings` | Class |

## Class diagram

```mermaid
classDiagram
    class CallLog {
        +string id
        +string from
        +string to
        +string status
        +string type
        +string medium
        +string call_received_by
        +string employee_user_id
        +before_insert()
        +after_insert()
        +validate()
        +on_update()
        +trigger_call_popup()
        +notify_call_agents()
        +update_received_by()
    }
    class TelephonyCallType {
        +string call_type
    }
    class DynamicLink {
        +string link_doctype
        +string link_name
    }
    class IncomingCallSettings {
        +string call_routing
        +string greeting_message
        +string agent_busy_message
        +validate()
        +validate_call_schedule_timeslot()
        +validate_call_schedule_overlaps()
    }
    class IncomingCallHandlingSchedule {
        +string day_of_week
        +string from_time
        +string to_time
        +string agent_group
    }
    class VoiceCallSettings {
        +string user
        +string call_receiving_device
        +string greeting_message
        +before_insert()
        +set_user_for_restricted_creator()
    }
    class Employee
    class Customer
    class EmployeeGroup
    CallLog *-- DynamicLink : links
    CallLog --> TelephonyCallType : type_of_call
    CallLog --> Employee : call_received_by
    CallLog --> Customer : customer
    IncomingCallSettings *-- IncomingCallHandlingSchedule : call_handling_schedule
    IncomingCallHandlingSchedule --> EmployeeGroup : agent_group
```

## Sequence diagram

### Cuộc gọi đến và popup

Khi Call Log được tạo, controller liên kết các bên theo số điện thoại rồi đẩy `show_call_popup` cho nhân viên vừa khớp số `to` vừa nằm trong lịch trực của medium.

```mermaid
sequenceDiagram
    participant Ext as Tích hợp ngoài app
    participant CL as Call Log
    participant CRM as crm utils, lead.py
    participant Emp as Employee
    participant RT as frappe realtime
    actor Agent
    Ext->>CL: insert()
    CL->>CRM: before_insert: get_contacts_with_phone_number(number)
    CL->>CL: add_link(Contact), link_customer_of_contact
    CL->>CRM: get_leads_with_phone_number(number)
    CL->>CL: add_link(Lead)
    opt type là Incoming
        CL->>Emp: update_received_by: get_employees_with_number(to)
    end
    CL->>CL: after_insert: trigger_call_popup
    opt type là Incoming
        CL->>CRM: get_scheduled_employees_for_popup(medium)
        CRM-->>CL: user_id theo timeslot hoặc catch_all
        CL->>Emp: get_employees_with_number(to)
        CL->>CL: lấy giao của hai tập
        alt có số khớp nhưng không ai trong lịch
            CL->>CL: add_comment(No employee was scheduled)
        else có người nhận
            CL->>RT: publish_realtime(show_call_popup)
            RT-->>Agent: call_popup.js mở CallPopup
        end
    end
```

Nguồn: [call_log.py:60](../../apps/erpnext/erpnext/telephony/doctype/call_log/call_log.py#L60), [call_log.py:118](../../apps/erpnext/erpnext/telephony/doctype/call_log/call_log.py#L118)

### Cập nhật trạng thái cuộc gọi

Khi Call Log được lưu lại, `on_update` so với bản trước để phát hiện cuộc gọi nhỡ hoặc đã kết thúc. Sự kiện gửi cho nhân viên theo số cũ, không xét lịch trực.

```mermaid
sequenceDiagram
    participant Ext as Tích hợp ngoài app
    participant CL as Call Log
    participant RT as frappe realtime
    actor Agent
    Ext->>CL: save()
    CL->>CL: validate: deduplicate_dynamic_links
    opt Incoming và to đổi
        CL->>CL: update_received_by
    end
    CL->>CL: on_update: get_doc_before_save
    opt to đổi và status chưa kết thúc
        CL->>RT: notify_call_agents(missed)
        RT-->>Agent: sự kiện missed theo id cuộc gọi
        CL->>CL: trigger_call_popup cho số mới
    end
    opt status vừa vào END_CALL_STATUSES
        CL->>RT: notify_call_agents(ended)
        RT-->>Agent: sự kiện ended theo id cuộc gọi
    end
```

Nguồn: [call_log.py:78](../../apps/erpnext/erpnext/telephony/doctype/call_log/call_log.py#L78)

### Ghi tóm tắt cuộc gọi

Nhân viên nghe cuộc gọi được ghi tóm tắt mà không cần quyền write; người khác phải có quyền write.

```mermaid
sequenceDiagram
    actor Agent
    participant JS as call_popup.js
    participant API as add_call_summary_and_call_type
    participant CT as Telephony Call Type
    participant CL as Call Log
    Agent->>JS: nhập summary và call_type
    JS->>API: add_call_summary_and_call_type(call_log, summary, call_type)
    API->>CT: validate_call_type: docstatus phải là 1
    API->>CL: check_permission(read)
    opt employee_user_id khác session user
        API->>CL: check_permission(write)
    end
    API->>CL: type_of_call, summary, save(ignore_permissions=True)
    API->>CL: add_comment(Call Summary)
```

Nguồn: [call_log.py:157](../../apps/erpnext/erpnext/telephony/doctype/call_log/call_log.py#L157)

### Liên kết cuộc gọi cũ

Hook `on_update` của Contact và Lead tìm các Call Log trùng số mới thêm và gắn link; lỗi được rollback về savepoint và ghi log, không chặn việc lưu Contact hay Lead.

```mermaid
sequenceDiagram
    actor User
    participant Doc as Contact hoặc Lead
    participant Mod as call_log.py
    participant CL as Call Log
    User->>Doc: save()
    Doc->>Mod: link_existing_conversations(doc, state)
    Mod->>Mod: get_new_phone_numbers(doc)
    opt có số mới
        Mod->>Mod: savepoint(link_call_logs)
        loop mỗi số, mỗi log chưa liên kết
            Mod->>CL: get_unlinked_call_logs_with_number, get_doc
            CL->>CL: add_link(doctype, name)
            opt Contact và log chưa có customer
                CL->>CL: link_customer_of_contact
            end
            Mod->>CL: save(ignore_permissions=True)
        end
    end
```

Nguồn: [call_log.py:227](../../apps/erpnext/erpnext/telephony/doctype/call_log/call_log.py#L227)

## Giới hạn

- Điểm tạo và cập nhật Call Log không có trong app này: grep `erpnext/` không thấy code Python tạo Call Log ngoài test. Participant "Tích hợp ngoài app" được suy ra, không đọc từ code cụ thể.
- `Incoming Call Settings`, `Voice Call Settings`: trong `erpnext/` không có Python nào đọc các giá trị này ngoài controller, test và patch, nên chỉ có class diagram. Nơi dùng có thể nằm ở app khác, chưa xác nhận.
- Phân quyền `has_permission`, `get_permission_query_conditions` (Call Log, Voice Call Settings) và `get_linked_call_logs` (hook `additional_timeline_content`) không vẽ vì không phải luồng nhiều bước.
- `public/js/telephony.js` và phần giao diện của `call_popup.js` chỉ đọc lướt.
- `_is_call_missed` trong code có ghi chú `FIXME`: logic này chỉ đúng với Exotel.
