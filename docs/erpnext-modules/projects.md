# Module Projects

Module quản lý dự án, công việc và thời gian làm việc: Project, Task, Timesheet, đơn giá theo Activity Cost và tổng hợp chi phí, doanh thu, biên lợi nhuận của dự án. Module nối với `accounts` (lập hóa đơn từ Timesheet, Purchase Invoice), `selling` (Sales Order), `stock` (vật tư tiêu hao qua Stock Ledger Entry) và `setup` (Employee, Holiday List).

## Phạm vi

Đọc được 15 doctype trong `projects/doctype/`.

| Nhóm chức năng | Doctype / file chính | Sơ đồ |
|---|---|---|
| Dự án | Project, Project Template, Project Template Task, Project Type, Project User (`project/project.py`) | Class diagram; Sequence: tạo Project từ Project Template, cập nhật chi phí |
| Công việc | Task, Task Depends On, Dependent Task, Task Type (`task/task.py`) | Class diagram; Sequence: lưu Task |
| Chấm công | Timesheet, Timesheet Detail, Activity Cost, Activity Type, Projects Settings (`timesheet/timesheet.py`) | Class diagram; Sequence: submit Timesheet |
| Lập hóa đơn | `timesheet.make_sales_invoice`, `accounts/doctype/sales_invoice/services/timesheet_billing.py` | Sequence: lập hóa đơn, hủy hoặc trả hóa đơn |
| Thu thập tiến độ | Project Update, các hàm reminder trong `project.py` | Class diagram; Sequence: thu thập tiến độ |

## Class diagram

Class không ghi cha đều kế thừa trực tiếp `frappe.model.document.Document`. `SalesInvoice`, `SalesOrder` chỉ xuất hiện để thể hiện Link ra ngoài module.

```mermaid
classDiagram
    class NestedSet
    class Project {
        +string project_name
        +string status
        +string percent_complete_method
        +float percent_complete
        +float total_costing_amount
        +float total_billed_amount
        +float gross_margin
        +validate()
        +after_insert()
        +copy_from_template()
        +update_project()
        +update_percent_complete()
        +update_costing()
        +update_billed_amount()
        +calculate_gross_margin()
    }
    class ProjectTemplate {
        +string project_type
        +bool disabled
        +validate()
        +validate_template_tasks()
        +validate_dependencies()
    }
    class ProjectTemplateTask {
        +string task
        +string subject
    }
    class ProjectUser {
        +string user
        +bool welcome_email_sent
        +text project_status
    }
    class ProjectUpdate {
        +string project
        +bool sent
        +date date
    }
    class Task {
        +string subject
        +string project
        +string status
        +string parent_task
        +float progress
        +float task_weight
        +bool is_group
        +bool is_template
        +validate()
        +on_update()
        +update_time_and_costing()
        +update_project()
        +check_recursion()
        +reschedule_dependent_tasks()
        +update_status()
    }
    class TaskDependsOn {
        +string task
        +text subject
    }
    class TaskType {
        +float weight
    }
    class Timesheet {
        +string employee
        +string status
        +string parent_project
        +float total_hours
        +float total_billable_amount
        +float total_billed_amount
        +float per_billed
        +validate()
        +on_submit()
        +on_cancel()
        +update_task_and_project()
        +calculate_total_amounts()
        +calculate_percentage_billed()
        +set_status()
        +unlink_sales_invoice()
    }
    class TimesheetDetail {
        +string activity_type
        +string project
        +string task
        +float hours
        +float billing_hours
        +float billing_rate
        +float costing_rate
        +bool is_billable
        +string sales_invoice
        +update_cost()
        +update_billing_hours()
        +calculate_hours()
        +validate_task_project()
    }
    class ActivityCost {
        +string activity_type
        +string employee
        +float billing_rate
        +float costing_rate
        +validate()
        +check_unique()
    }
    class ActivityType {
        +string activity_type
        +float billing_rate
        +float costing_rate
        +bool disabled
    }
    class SalesInvoice
    class SalesOrder

    NestedSet <|-- Task
    Project *-- ProjectUser : users
    Project --> ProjectTemplate : project_template
    Project --> SalesOrder : sales_order
    ProjectTemplate *-- ProjectTemplateTask : tasks
    ProjectTemplateTask --> Task : task
    ProjectUpdate --> Project : project
    ProjectUpdate *-- ProjectUser : users
    Task --> Project : project
    Task --> Task : parent_task
    Task --> TaskType : type
    Task *-- TaskDependsOn : depends_on
    TaskDependsOn --> Task : task
    Timesheet *-- TimesheetDetail : time_logs
    Timesheet --> Project : parent_project
    Timesheet --> SalesInvoice : sales_invoice
    TimesheetDetail --> Project : project
    TimesheetDetail --> Task : task
    TimesheetDetail --> ActivityType : activity_type
    TimesheetDetail --> SalesInvoice : sales_invoice
    ActivityCost --> ActivityType : activity_type
```

## Sequence diagram

### Submit Timesheet và cập nhật Task, Project

Khi lưu, Timesheet tính giờ và đơn giá theo thứ tự Activity Cost của nhân viên, Activity Cost mặc định, rồi Activity Type. Khi submit, nó cộng dồn số liệu sang Task và Project. Timesheet không ghi GL Entry.

```mermaid
sequenceDiagram
    actor User
    participant TS as Timesheet
    participant TD as TimesheetDetail
    participant AC as Activity Cost
    participant T as Task
    participant P as Project
    User->>TS: insert hoặc save
    TS->>TS: validate()
    TS->>TD: calculate_hours()
    TS->>TS: validate_time_logs()
    TS->>TS: validate_overlap()
    TS->>TS: validate_tasks_not_cancelled()
    TS->>TD: update_cost(employee, currency, exchange_rate)
    opt thiếu costing_rate hoặc billing_rate
        TD->>AC: _get_activity_cost(employee, activity_type, currency)
        AC-->>TD: costing_rate, billing_rate
    end
    TS->>TS: calculate_total_amounts()
    TS->>TS: calculate_percentage_billed()
    User->>TS: submit
    TS->>TS: on_submit() rồi validate_mandatory_fields()
    TS->>TS: update_task_and_project()
    loop mỗi Task trong time_logs
        TS->>T: update_time_and_costing()
        TS->>T: get_task_status() rồi save()
    end
    loop mỗi Project trong time_logs
        TS->>P: update_project() rồi save()
    end
```

Nguồn: [timesheet.py:69](../../apps/erpnext/erpnext/projects/doctype/timesheet/timesheet.py#L69), [timesheet.py:186](../../apps/erpnext/erpnext/projects/doctype/timesheet/timesheet.py#L186), [timesheet_detail.py:74](../../apps/erpnext/erpnext/projects/doctype/timesheet_detail/timesheet_detail.py#L74)

### Lập hóa đơn từ Timesheet

Có hai đường vào: tạo Sales Invoice từ Timesheet, hoặc chọn `project` trên Sales Invoice khi bật `fetch_timesheet_in_sales_invoice`. Khi submit hóa đơn, các dòng Timesheet Detail được gắn `sales_invoice` và Timesheet tính lại `per_billed`, `status`.

```mermaid
sequenceDiagram
    actor User
    participant TS as Timesheet
    participant SI as SalesInvoice
    participant TB as TimesheetBillingService
    participant GL as GL Entry
    participant P as Project
    alt từ Timesheet
        User->>TS: make_sales_invoice(source_name, item_code, customer, currency)
        TS->>SI: append timesheets cho log is_billable chưa có sales_invoice
        TS->>SI: run_method calculate_billing_amount_for_timesheet
        TS-->>User: Sales Invoice nháp
    else từ Project trên hóa đơn
        User->>SI: chọn project rồi save
    end
    User->>SI: save
    SI->>TB: validate_time_sheets_are_submitted()
    SI->>TB: set_billing_hours_and_amount()
    TB->>TS: get_projectwise_timesheet_data(project, name)
    SI->>TB: update_timesheet_billing_for_project()
    opt có project, chưa có timesheets, bật fetch_timesheet_in_sales_invoice
        TB->>TS: get_projectwise_timesheet_data(project)
    end
    TB->>TB: calculate_billing_amount_for_timesheet()
    User->>SI: submit
    SI->>GL: make_gl_entries()
    SI->>TB: update_time_sheet(sales_invoice)
    TB->>TS: _update_time_sheet_detail() rồi calculate_total_amounts()
    TB->>TS: calculate_percentage_billed(), set_status(), db_update_all()
    opt sales_update_frequency là Each Transaction
        SI->>P: update_project() rồi update_billed_amount(), calculate_gross_margin()
    end
```

Nguồn: [timesheet.py:488](../../apps/erpnext/erpnext/projects/doctype/timesheet/timesheet.py#L488), [timesheet_billing.py:47](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/services/timesheet_billing.py#L47), [sales_invoice.py:443](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L443)

### Hủy hoặc trả hóa đơn đã lập từ Timesheet

Hóa đơn trả phải có `return_against`. Khi submit hóa đơn trả, link trên time log bị xóa. Khi hủy hóa đơn trả, link trở lại hóa đơn gốc. Khi hủy hóa đơn thường, link bị xóa.

```mermaid
sequenceDiagram
    actor User
    participant SI as SalesInvoice
    participant TB as TimesheetBillingService
    participant TS as Timesheet
    participant GL as GL Entry
    alt submit hóa đơn trả
        User->>SI: submit với is_return và return_against
        SI->>TB: update_time_sheet(None)
        TB->>TS: _update_time_sheet_detail() rồi calculate_total_amounts()
    else hủy hóa đơn
        User->>SI: cancel
        SI->>SI: before_cancel()
        SI->>TB: update_time_sheet(return_against hoặc None)
        TB->>TS: _should_set_sales_invoice() rồi đặt sales_invoice
        TB->>TS: calculate_percentage_billed(), set_status(), db_update_all()
        SI->>SI: on_cancel()
        SI->>GL: make_gl_entries_on_cancel()
        SI->>TB: unlink_sales_invoice_from_timesheets()
        TB->>TS: unlink_sales_invoice(name) rồi db_update_all()
    end
```

Nguồn: [sales_invoice.py:536](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L536), [timesheet_billing.py:58](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/services/timesheet_billing.py#L58), [timesheet.py:313](../../apps/erpnext/erpnext/projects/doctype/timesheet/timesheet.py#L313)

### Tạo Project từ Project Template

Sau khi insert, Project sao chép các Task template thành Task thật, tính ngày tránh ngày nghỉ, nối phụ thuộc và cha con, rồi liên kết ngược Sales Order.

```mermaid
sequenceDiagram
    actor User
    participant P as Project
    participant PT as Project Template
    participant T as Task
    participant SO as Sales Order
    User->>P: insert
    P->>P: validate() rồi validate_project_template()
    P->>P: after_insert()
    P->>P: copy_from_template()
    opt có project_template và Project chưa có Task
        P->>PT: frappe.get_doc(Project Template)
        loop mỗi dòng template.tasks
            P->>P: create_task_from_template()
            P->>P: calculate_start_date(), calculate_end_date(), update_if_holiday()
            P->>T: insert với template_task
        end
        P->>P: dependency_mapping()
        P->>T: check_depends_on_value() rồi save
        P->>T: check_for_parent_tasks() rồi save
    end
    P->>SO: link_with_sales_order() đặt project
    P->>P: control_access_for_project_users()
```

Nguồn: [project.py:276](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L276), [project.py:132](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L132)

### Lưu Task

Task là cây `NestedSet`. Khi lưu, nó kiểm tra ngày và trạng thái, sau đó đẩy lùi Task phụ thuộc, cập nhật % hoàn thành của Project và đồng bộ `depends_on` của Task cha.

```mermaid
sequenceDiagram
    actor User
    participant T as Task
    participant NS as nestedset
    participant DT as Task phụ thuộc
    participant PT as Task cha
    participant P as Project
    User->>T: save
    T->>T: validate()
    T->>T: validate_dates(), validate_progress(), validate_status()
    T->>T: on_update()
    T->>NS: update_nsm_model() rồi update_nsm()
    T->>T: check_recursion()
    T->>PT: remove_from_previous_parent_depends_on()
    T->>T: reschedule_dependent_tasks()
    loop Task phụ thuộc cùng Project cần dời
        T->>DT: đặt exp_start_date, exp_end_date rồi save()
    end
    T->>P: update_project() rồi update_percent_complete(), update_costing()
    T->>P: update_previous_project()
    T->>T: unassign_todo()
    T->>PT: populate_depends_on()
```

Nguồn: [task.py:84](../../apps/erpnext/erpnext/projects/doctype/task/task.py#L84), [task.py:316](../../apps/erpnext/erpnext/projects/doctype/task/task.py#L316), [project.py:308](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L308)

### Cập nhật chi phí Project từ chứng từ khác

Chi phí Project không chỉ đến từ Timesheet. Stock Controller, Purchase Invoice, Landed Cost Voucher và Repost Item Valuation gọi các hàm cấp module, còn tác vụ định kỳ lưu lại Project.

```mermaid
sequenceDiagram
    participant SC as StockController
    participant PI as PurchaseInvoice
    participant RIV as RepostItemValuation
    participant Sch as Scheduler
    participant P as Project
    participant SLE as Stock Ledger Entry
    SC->>P: update_project_consumed_material_cost() rồi update_consumed_material_cost(projects)
    P->>P: set_consumed_material_cost()
    P->>SLE: get_stock_value_consumed()
    P->>P: get_stock_entry_capitalised_costs()
    P->>P: db_set_cost(total_consumed_material_cost)
    RIV->>P: update_consumed_material_cost_for_vouchers(vouchers)
    PI->>P: update_purchase_cost(projects)
    P->>P: update_purchase_costing()
    P->>P: get_non_stock_purchase_cost(), get_capitalised_landed_cost()
    P->>P: db_set_cost(total_purchase_cost)
    Sch->>P: update_project_sales_billing()
    alt sales_update_frequency là Each Transaction
        P-->>Sch: thoát ngay
    else Monthly ngày 1 hoặc Daily
        P->>P: save() rồi validate(), update_costing()
    end
```

Nguồn: [project.py:1089](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L1089), [project.py:1082](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L1082), [project.py:934](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L934)

### Thu thập tiến độ qua email

Với Project bật `collect_progress`, tác vụ định kỳ tạo Project Update và gửi email hỏi tiến độ, gom trả lời vào bảng `users`, rồi gửi tổng hợp cho hôm trước. Trong `hooks.py`, `hourly_reminder` chạy `hourly`, `project_status_update_reminder` và `collect_project_status` chạy `hourly_maintenance`, `send_project_status_email_to_users` chạy `daily_maintenance`.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant P as project.py
    participant PU as Project Update
    participant C as Communication
    participant Mail as frappe.sendmail
    Sch->>P: hourly_reminder() hoặc project_status_update_reminder()
    P->>P: get_projects_for_collect_progress(frequency, fields)
    loop mỗi Project đến giờ gửi
        P->>P: send_project_update_email_to_users(project)
        opt không phải ngày nghỉ và có users
            P->>PU: insert với sent bằng 0
            P->>Mail: gửi message, subject của Project
        end
    end
    Sch->>P: collect_project_status()
    P->>C: get_uncollected_replies() rồi get_project_update_replies()
    P->>PU: append users rồi save
    Sch->>P: send_project_status_email_to_users()
    P->>Mail: gửi template daily_project_summary
    P->>PU: db_set sent bằng 1
```

Nguồn: [project.py:699](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L699), [project.py:824](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L824), [project.py:855](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L855), [project.py:912](../../apps/erpnext/erpnext/projects/doctype/project/project.py#L912)

## Giới hạn

- Không vẽ sequence cho Activity Cost, Activity Type, Project Type, Task Type, Projects Settings vì chỉ là danh mục. Activity Cost chỉ có `check_unique` và `set_title`, phần dùng đơn giá nằm ở luồng Timesheet.
- `Dependent Task` có doctype và class nhưng không đưa vào sơ đồ. Chưa xác định chỗ dùng.
- Không vẽ: `create_duplicate_project`, `set_project_status`, `create_kanban_board_if_not_exists`, `project_overview*.py` (đọc lướt), `web_form/tasks`, các report trong `projects/report` (không đọc).
- Trong luồng lập hóa đơn, chỉ đọc phần Sales Invoice liên quan đến Timesheet. `make_gl_entries` của Sales Invoice không được đọc sâu, nên không vẽ chi tiết bút toán.
- `get_uncollected_replies` lọc theo Communication nhận về, sơ đồ gộp thành một bước.
- `Timesheet.set_status` đặt `Completed` khi trường đầu phiếu `sales_invoice` có giá trị. Không thấy luồng Python nào trong các file đã đọc ghi trường này, nên chưa chắc nguồn của nó.
