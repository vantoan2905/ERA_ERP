# Module Setup

Module `setup` chứa dữ liệu nền của toàn hệ thống: Company và các cây danh mục (Item Group, Customer Group, Territory...), Employee, setup wizard, xóa giao dịch theo Company, Email Digest và kiểm tra thẩm quyền duyệt. Khi tạo Company, module gọi sang `accounts` (chart of accounts, tax template), `stock` (Warehouse) và `regional` (fixture theo quốc gia). Các chứng từ của `selling`, `buying`, `stock`, `accounts` gọi ngược lại `Authorization Control` khi submit.

## Phạm vi

Đọc được 40 doctype trong `setup/doctype/`. Doctype `Transaction Deletion Record Details` là bảng con của Transaction Deletion Record nhưng nằm ở `accounts/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Khởi tạo site | `setup_wizard/setup_wizard.py`, `setup_wizard/operations/install_fixtures.py`, `setup_wizard/operations/taxes_setup.py` | Sequence: Setup wizard |
| Company | `Company`, `Department`, `Global Defaults` | Class: Company và tổ chức. Sequence: Tạo Company, Cache doanh số Company |
| Xóa giao dịch | `Transaction Deletion Record` và 3 bảng con, `demo.py` | Class: Transaction Deletion Record. Sequence: 3 luồng xóa, Xóa dữ liệu demo |
| Nhân sự | `Employee`, `Employee Group`, `Holiday List`, `Sales Person` | Class: Company và tổ chức. Sequence: Lưu Employee, Tạo User từ Employee |
| Thông báo định kỳ | `Email Digest` | Class: Email Digest và thẩm quyền. Sequence: Gửi Email Digest |
| Thẩm quyền duyệt | `Authorization Rule`, `Authorization Control` | Class: Email Digest và thẩm quyền. Sequence: Kiểm tra thẩm quyền khi submit |
| Cây danh mục | `Item Group`, `Customer Group`, `Supplier Group`, `Territory` | Class: Cây danh mục. Sequence: Lưu và dùng Item Group |
| Danh mục CRUD | `Brand`, `UOM`, `Currency Exchange`, `Incoterm`, `Terms and Conditions`, `Vehicle`, `Driver`... | Không vẽ, xem Giới hạn |

## Class diagram

### Company và tổ chức

```mermaid
classDiagram
    class NestedSet
    class Company {
        +string company_name
        +string abbr
        +string country
        +string default_currency
        +string create_chart_of_accounts_based_on
        +string chart_of_accounts
        +string existing_company
        +string default_warehouse
        +validate()
        +on_update()
        +on_trash()
        +create_default_accounts()
        +create_default_warehouses()
        +create_default_cost_center()
        +create_default_departments()
        +set_default_accounts()
        +create_default_tax_template()
    }
    class Department {
        +string department_name
        +string company
        +string parent_department
        +bool is_group
        +validate()
        +on_update()
    }
    class Employee {
        +string employee_name
        +string company
        +string status
        +string user_id
        +string reports_to
        +string cell_number
        +bool create_user_automatically
        +bool create_user_permission
        +validate()
        +on_update()
        +after_insert()
        +update_user()
        +update_user_permissions()
        +update_user_status()
    }
    class EmployeeEducation {
        +string school_univ
        +string qualification
    }
    class EmployeeExternalWorkHistory {
        +string company_name
        +string designation
    }
    class EmployeeInternalWorkHistory {
        +string department
        +date from_date
        +date to_date
    }
    class EmployeeGroup {
        +string employee_group_name
    }
    class EmployeeGroupTable {
        +string employee
        +string user_id
    }
    class HolidayList {
        +string holiday_list_name
        +date from_date
        +date to_date
        +string weekly_off
        +float total_holidays
        +validate()
        +get_weekly_off_dates()
        +get_local_holidays()
    }
    class Holiday {
        +date holiday_date
        +string description
        +bool weekly_off
        +bool is_half_day
    }
    class SalesPerson {
        +string sales_person_name
        +string employee
        +string parent_sales_person
        +bool enabled
        +validate()
        +validate_employee_id()
    }
    class GlobalDefaults {
        +string default_company
        +string default_currency
        +string country
        +string demo_company
        +on_update()
    }
    NestedSet <|-- Company
    NestedSet <|-- Department
    NestedSet <|-- Employee
    NestedSet <|-- SalesPerson
    Company --> Company : parent_company
    Company --> HolidayList : default_holiday_list
    Department --> Company : company
    Department --> Department : parent_department
    Employee --> Company : company
    Employee --> Department : department
    Employee --> Employee : reports_to
    Employee --> HolidayList : holiday_list
    Employee *-- EmployeeEducation : education
    Employee *-- EmployeeExternalWorkHistory : external_work_history
    Employee *-- EmployeeInternalWorkHistory : internal_work_history
    EmployeeGroup *-- EmployeeGroupTable : employee_list
    EmployeeGroupTable --> Employee : employee
    HolidayList *-- Holiday : holidays
    SalesPerson --> Employee : employee
    GlobalDefaults --> Company : default_company
```

### Transaction Deletion Record

```mermaid
classDiagram
    class TransactionDeletionRecord {
        +string company
        +string status
        +bool process_in_single_transaction
        +string delete_bin_data_status
        +string delete_transactions_status
        +string error_log
        +validate()
        +before_submit()
        +on_submit()
        +on_cancel()
        +generate_to_delete_list()
        +start_deletion_tasks()
        +enqueue_task()
        +execute_task()
        +delete_company_transactions()
    }
    class TransactionDeletionRecordItem {
        +string doctype_name
    }
    class TransactionDeletionRecordToDelete {
        +string doctype_name
        +string company_field
        +int document_count
        +string child_doctypes
        +bool deleted
    }
    class TransactionDeletionRecordDetails {
        +string doctype_name
        +string docfield_name
        +int no_of_docs
        +bool done
    }
    class Company
    TransactionDeletionRecord --> Company : company
    TransactionDeletionRecord *-- TransactionDeletionRecordItem : doctypes_to_be_ignored
    TransactionDeletionRecord *-- TransactionDeletionRecordToDelete : doctypes_to_delete
    TransactionDeletionRecord *-- TransactionDeletionRecordDetails : doctypes
```

### Email Digest và thẩm quyền

```mermaid
classDiagram
    class StatusUpdater
    class TransactionBase
    class AuthorizationControl {
        +validate_approving_authority()
        +bifurcate_based_on_type()
        +validate_auth_rule()
        +get_appr_user_role()
        +get_value_based_rule()
    }
    class AuthorizationRule {
        +string transaction
        +string based_on
        +string company
        +string system_user
        +string system_role
        +string approving_user
        +string approving_role
        +float value
        +validate()
        +validate_rule()
        +check_duplicate_entry()
    }
    class EmailDigest {
        +string company
        +string frequency
        +bool enabled
        +bool income
        +bool bank_balance
        +bool todo_list
        +send()
        +get_msg_html()
        +set_accounting_cards()
        +get_next_sending()
        +get_from_to_date()
    }
    class EmailDigestRecipient {
        +string recipient
    }
    StatusUpdater <|-- TransactionBase
    TransactionBase <|-- AuthorizationControl
    AuthorizationControl ..> AuthorizationRule : truy van
    EmailDigest *-- EmailDigestRecipient : recipients
```

### Cây danh mục

```mermaid
classDiagram
    class NestedSet
    class ItemGroup {
        +string item_group_name
        +string parent_item_group
        +bool is_group
        +string image
        +validate()
        +check_item_tax()
        +validate_item_group_defaults()
        +on_update()
        +on_trash()
        +delete_child_item_groups_key()
    }
    class CustomerGroup {
        +string customer_group_name
        +string parent_customer_group
        +string default_price_list
        +bool is_group
        +validate()
        +on_update()
    }
    class SupplierGroup {
        +string supplier_group_name
        +string parent_supplier_group
        +string payment_terms
        +bool is_group
    }
    class Territory {
        +string territory_name
        +string parent_territory
        +string territory_manager
        +bool is_group
    }
    class ItemDefault
    class ItemTax
    NestedSet <|-- ItemGroup
    NestedSet <|-- CustomerGroup
    NestedSet <|-- SupplierGroup
    NestedSet <|-- Territory
    ItemGroup --> ItemGroup : parent_item_group
    ItemGroup *-- ItemDefault : item_group_defaults
    ItemGroup *-- ItemTax : taxes
    CustomerGroup --> CustomerGroup : parent_customer_group
    SupplierGroup --> SupplierGroup : parent_supplier_group
    Territory --> Territory : parent_territory
```

## Sequence diagram

### Setup wizard

Frappe chạy tuần tự 4 stage của ERPNext, đăng ký qua hook `setup_wizard_stages`; stage thứ hai tạo Fiscal Year và Company đầu tiên.

```mermaid
sequenceDiagram
    actor User
    participant FW as frappe setup_wizard
    participant SW as setup_wizard.py
    participant IF as install_fixtures.py
    participant Co as Company
    participant GD as Global Defaults
    User->>FW: setup_complete(args)
    FW->>SW: get_setup_stages(args) qua get_stages_hooks
    SW-->>FW: 4 stage
    FW->>SW: stage_fixtures(args)
    SW->>IF: install(country)
    IF->>IF: get_preset_records, make_records
    IF->>IF: set_up_address_templates, add_uom_data
    FW->>SW: setup_company(args)
    SW->>IF: install_company(args)
    IF->>Co: make_records(Fiscal Year, Company)
    Co->>Co: validate, on_update (xem Tạo Company)
    FW->>SW: setup_defaults(args)
    SW->>IF: install_defaults(args)
    IF->>IF: make_records(Standard Buying, Standard Selling)
    IF->>GD: set_global_defaults(args)
    IF->>IF: update_stock_settings()
    opt có args.bank_account
        IF->>IF: create_bank_account(args)
    end
    FW->>SW: capture_user_persona(args)
    opt không phải site sk_hrms
        SW->>SW: capture(user_persona_submitted)
    end
```

Nguồn: [setup_wizard.py:12](../../apps/erpnext/erpnext/setup/setup_wizard/setup_wizard.py#L12), [install_fixtures.py:463](../../apps/erpnext/erpnext/setup/setup_wizard/operations/install_fixtures.py#L463)

### Tạo Company

Lần lưu đầu của Company sinh chart of accounts, kho mặc định, cost center, tax template, phòng ban và gán các tài khoản mặc định; tất cả nằm trong `on_update`.

```mermaid
sequenceDiagram
    actor User
    participant Co as Company
    participant CoA as chart_of_accounts.py
    participant Acc as Account
    participant WH as Warehouse
    participant CC as Cost Center
    participant Tax as taxes_setup.py
    participant Reg as regional country setup
    User->>Co: insert()
    Co->>Co: validate: validate_abbr, validate_coa_input, set_chart_of_accounts
    Co->>Co: on_update: NestedSet.on_update
    opt chưa có Account và không có ignore_chart_of_accounts
        Co->>Co: đặt flags.country_change = True, sync_financial_report_templates
        Co->>CoA: create_default_accounts: create_charts(company, chart, existing_company)
        CoA->>CoA: get_chart(chart_template, existing_company)
        loop mỗi node trong cây
            CoA->>Acc: account.insert()
        end
        CoA->>Acc: rebuild_tree(Account)
        Co->>Co: db_set default_receivable_account, default_payable_account
        Co->>WH: create_default_warehouses: All Warehouses, Stores, Work In Progress, Finished Goods, Goods In Transit
        Co->>Co: db_set default_warehouse = Stores
    end
    opt chưa có Cost Center lá
        Co->>CC: create_default_cost_center: gốc và Main
    end
    opt flags.country_change
        Co->>Reg: install_country_fixtures(name, country)
        Co->>Tax: create_default_tax_template: setup_taxes_and_charges(name, country)
    end
    opt chưa có Department của Company
        Co->>Co: create_default_departments()
    end
    opt không có ignore_chart_of_accounts
        Co->>Co: set_default_accounts, set_mode_of_payment_account
    end
```

Nguồn: [company.py:455](../../apps/erpnext/erpnext/setup/doctype/company/company.py#L455), [chart_of_accounts.py:13](../../apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts/chart_of_accounts.py#L13)

### Yêu cầu xóa giao dịch của Company

Nút xóa trên form Company gọi hàm tạo Transaction Deletion Record, sinh danh sách doctype rồi submit ngay; submit khởi động chuỗi tác vụ nền.

```mermaid
sequenceDiagram
    actor User
    participant Co as company.py
    participant TDR as Transaction Deletion Record
    participant DF as DocField
    participant Cache as Redis cache
    participant Q as RQ long queue
    User->>Co: create_transaction_deletion_request(company)
    Co->>Co: only_for(System Manager), has_permission(delete)
    Co->>TDR: is_deletion_doc_running(company)
    Co->>TDR: insert()
    TDR->>TDR: validate: populate_doctypes_to_be_ignored_table, validate_to_delete_list
    Co->>TDR: generate_to_delete_list()
    TDR->>DF: lấy doctype có Link tới Company
    TDR->>TDR: append doctypes_to_delete, save()
    Co->>TDR: submit()
    TDR->>TDR: before_submit: chặn nếu có bản Queued hoặc Running
    TDR->>TDR: on_submit: status = Queued
    TDR->>TDR: start_deletion_tasks: status = Running
    TDR->>Cache: _set_deletion_cache: deletion_running_doctype theo từng doctype
    TDR->>Q: enqueue_task(Delete Bins)
```

Nguồn: [company.py:1240](../../apps/erpnext/erpnext/setup/doctype/company/company.py#L1240), [transaction_deletion_record.py:662](../../apps/erpnext/erpnext/setup/doctype/transaction_deletion_record/transaction_deletion_record.py#L662)

### Chuỗi tác vụ xóa giao dịch

Mỗi tác vụ chạy trong một job riêng và tự enqueue tác vụ kế; bước cuối xóa theo lô 5000 bản ghi và tự enqueue lại đến khi hết doctype.

```mermaid
sequenceDiagram
    participant Q as RQ long queue
    participant TDR as Transaction Deletion Record
    participant Data as Bảng giao dịch
    participant Logs as Version, Communication, Comment, File
    participant Cache as Redis cache
    Q->>TDR: execute_task(Delete Bins)
    TDR->>TDR: delete_bins, rồi enqueue_task kế tiếp
    Q->>TDR: delete_lead_addresses
    Q->>TDR: reset_company_values
    Q->>TDR: delete_notifications
    Q->>TDR: initialize_doctypes_to_be_deleted_table
    TDR->>TDR: populate_doctypes_table cho dòng có document_count lớn hơn 0
    Q->>TDR: delete_company_transactions
    loop mỗi dòng doctypes chưa done
        alt còn bản ghi
            TDR->>Logs: delete_version_log, delete_communications, delete_comments, unlink_attachments
            TDR->>Data: delete_child_tables, delete_docs_linked_with_specified_company
        else hết bản ghi
            TDR->>TDR: update_naming_series, done = 1, deleted = 1
        end
    end
    alt còn dòng chưa done
        TDR->>Q: enqueue_task(Delete Transactions)
    else đã xong
        TDR->>TDR: status = Completed
        TDR->>Cache: _clear_deletion_cache()
    end
    opt tác vụ ném exception (execute_task)
        TDR->>TDR: rollback, error_log, status = Failed
        TDR->>Cache: _clear_deletion_cache()
    end
```

Nguồn: [transaction_deletion_record.py:612](../../apps/erpnext/erpnext/setup/doctype/transaction_deletion_record/transaction_deletion_record.py#L612), [transaction_deletion_record.py:788](../../apps/erpnext/erpnext/setup/doctype/transaction_deletion_record/transaction_deletion_record.py#L788)

### Chặn lưu chứng từ trong lúc xóa

Hook `doc_events["*"]["validate"]` chặn lưu mọi doctype đang có trong danh sách xóa, dựa trên cờ Redis (TTL 4 giờ).

```mermaid
sequenceDiagram
    actor User
    participant Doc as Chứng từ bất kỳ
    participant Hook as check_for_running_deletion_job
    participant Cache as Redis cache
    User->>Doc: save()
    Doc->>Hook: validate hook
    alt doctype là ledger hoặc nằm trong PROTECTED_CORE_DOCTYPES
        Hook-->>Doc: bỏ qua
    else doctype khác
        Hook->>Cache: get_value(deletion_running_doctype theo doctype)
        alt có cờ
            Hook-->>User: throw Deletion in Progress
        else không có cờ
            Hook-->>Doc: cho lưu tiếp
        end
    end
```

Nguồn: [transaction_deletion_record.py:1129](../../apps/erpnext/erpnext/setup/doctype/transaction_deletion_record/transaction_deletion_record.py#L1129)

### Xóa dữ liệu demo

Dùng Transaction Deletion Record ở chế độ `process_in_single_transaction` (không qua queue), sau đó xóa master demo và Company demo.

```mermaid
sequenceDiagram
    actor User
    participant Demo as demo.py
    participant TDR as Transaction Deletion Record
    participant Co as Company
    participant GD as Global Defaults
    User->>Demo: clear_demo_data()
    Demo->>GD: get_single_value(demo_company)
    Demo->>TDR: create_transaction_deletion_record(company)
    TDR->>TDR: generate_to_delete_list, submit, start_deletion_tasks
    Demo->>Demo: clear_masters: clear_demo_record theo hook demo_master_doctypes
    Demo->>GD: delete_company: demo_company = rỗng
    Demo->>Co: frappe.delete_doc(Company)
    Co->>Co: on_trash: xóa Account, Warehouse, Employee, BOM... theo điều kiện
    opt có exception
        Demo-->>User: rollback, throw Could Not Delete Demo Data
    end
```

Nguồn: [demo.py:12](../../apps/erpnext/erpnext/setup/demo.py#L12), [company.py:898](../../apps/erpnext/erpnext/setup/doctype/company/company.py#L898)

### Cache doanh số Company

Job `daily_maintenance` ghi cache doanh số và lịch sử giao dịch lên Company để dashboard đọc.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant Co as company.py
    participant SI as Sales Invoice
    participant DB as Company
    Sch->>Co: cache_companies_monthly_sales_history()
    Co->>Co: _should_refresh_total_monthly_sales()
    loop mỗi Company
        Co->>SI: update_company_monthly_sales: get_monthly_results
        Co->>DB: set_value sales_monthly_history
        Co->>Co: get_all_transactions_annual_history
        Co->>DB: set_value transactions_annual_history
        opt sales_update_frequency cho phép
            Co->>SI: update_company_current_month_sales: Sum base_grand_total
            Co->>DB: set_value total_monthly_sales
        end
    end
```

Nguồn: [company.py:1068](../../apps/erpnext/erpnext/setup/doctype/company/company.py#L1068)

### Lưu Employee

Khi lưu, Employee kiểm tra dữ liệu và đồng bộ sang User đã liên kết: vai trò Employee, thông tin cá nhân, User Permission, trạng thái enabled.

```mermaid
sequenceDiagram
    actor HR as HR User
    participant Emp as Employee
    participant Usr as User
    participant UP as User Permission
    participant Cache as Redis cache
    HR->>Emp: save()
    Emp->>Emp: validate: set_employee_name, validate_date, validate_status, validate_reports_to
    alt có user_id
        Emp->>Emp: validate_user_details: validate_duplicate_user_id, validate_user_access
    else vừa bỏ user_id
        Emp->>Usr: validate_employee_role(user, ignore_emp_check=True), save
        Emp->>UP: remove_user_permission(Employee)
    end
    Emp->>Emp: on_update: update_nsm_model
    opt có user_id
        Emp->>Usr: update_user: append_roles(Employee), copy tên, ngày sinh, ảnh
        Emp->>UP: update_user_permissions: add hoặc remove Employee, Company
        Emp->>Usr: update_user_status: enabled = (status == Active)
    end
    Emp->>Cache: reset_employee_emails_cache()
```

Nguồn: [employee.py:121](../../apps/erpnext/erpnext/setup/doctype/employee/employee.py#L121), [employee.py:196](../../apps/erpnext/erpnext/setup/doctype/employee/employee.py#L196)

### Tạo User từ Employee

Chạy tự động trong `after_insert` nếu bật `create_user_automatically`, hoặc gọi trực tiếp qua API `create_user`.

```mermaid
sequenceDiagram
    actor HR as HR User
    participant Emp as Employee
    participant API as create_user
    participant Usr as User
    participant UP as User Permission
    HR->>Emp: insert()
    Emp->>Emp: before_insert: validate_auto_user_creation
    opt create_user_automatically và chưa có user_id
        Emp->>API: after_insert: create_user(employee, email, create_user_permission)
        API->>Emp: check_permission(write)
        API->>Usr: new_doc, update từ Employee
        API->>Emp: db_set(user_id, email)
        API->>Usr: append_roles(Employee), insert()
        API->>Emp: save()
        opt create_user_permission
            API->>UP: add_user_permission(Employee), add_user_permission(Company)
        end
    end
```

Nguồn: [employee.py:207](../../apps/erpnext/erpnext/setup/doctype/employee/employee.py#L207), [employee.py:485](../../apps/erpnext/erpnext/setup/doctype/employee/employee.py#L485)

### Gửi Email Digest

Job `daily_maintenance` duyệt các digest đang bật, chỉ gửi khi `get_next_sending()` trùng hôm nay: hằng ngày, thứ Hai đầu tuần hoặc ngày 1 đầu tháng theo `frequency`.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant Mod as email_digest.py
    participant ED as Email Digest
    participant GL as GL Entry và chứng từ
    participant Cache as Redis cache
    participant Mail as frappe.sendmail
    Sch->>Mod: send()
    loop mỗi Email Digest enabled
        Mod->>ED: get_next_sending()
        opt send_date là hôm nay
            Mod->>ED: send()
            loop mỗi dòng recipients
                ED->>ED: get_msg_html: set_title, set_style
                ED->>Cache: set_accounting_cards: đọc card theo khóa
                opt cache trống
                    ED->>GL: gọi get_ theo từng key, ví dụ get_income
                    ED->>Cache: set_value, hết hạn sau 24 giờ
                end
                ED->>ED: lấy events, todo, issue, project theo checkbox
                opt recipient là User enabled
                    ED->>Mail: sendmail(recipient, message)
                end
            end
        end
    end
```

Nguồn: [email_digest.py:952](../../apps/erpnext/erpnext/setup/doctype/email_digest/email_digest.py#L952), [email_digest.py:124](../../apps/erpnext/erpnext/setup/doctype/email_digest/email_digest.py#L124)

### Kiểm tra thẩm quyền khi submit

Chứng từ gọi `Authorization Control` trong `on_submit`. Rule theo user được xét trước, rồi theo role, cuối cùng rule toàn cục; không đủ quyền thì throw và hủy submit. Ví dụ dưới đây là Sales Order.

```mermaid
sequenceDiagram
    actor User
    participant SO as Sales Order
    participant AC as Authorization Control
    participant AR as Authorization Rule
    User->>SO: submit()
    SO->>AC: on_submit: validate_approving_authority(doctype, company, base_grand_total, doc)
    AC->>AR: count
    alt không có rule
        AC-->>SO: return
    else có rule
        AC->>AC: tính av_dis từ items và base_discount_amount
        AC->>AR: based_on theo system_user
        AC->>AC: bifurcate_based_on_type(val=1) cho từng based_on
        AC->>AR: based_on theo system_role
        AC->>AC: bifurcate_based_on_type(val=2) cho từng based_on
        AC->>AC: bifurcate_based_on_type(val=0) cho based_on còn lại
        AC->>AR: validate_auth_rule: rule có value không vượt giá trị chứng từ
        opt tìm thấy rule
            AC->>AR: get_appr_user_role: approving_user, approving_role
            opt session user không thuộc danh sách duyệt
                AC-->>User: throw Can be approved by
            end
        end
    end
```

Nguồn: [authorization_control.py:158](../../apps/erpnext/erpnext/setup/doctype/authorization_control/authorization_control.py#L158), [sales_order.py:583](../../apps/erpnext/erpnext/selling/doctype/sales_order/sales_order.py#L583)

### Lưu và dùng Item Group

Item Group là cây NestedSet; `item_group_defaults` được `get_item_details` dùng làm mức dự phòng khi lấy giá trị mặc định cho Item trên chứng từ.

```mermaid
sequenceDiagram
    actor User
    participant IG as Item Group
    participant Item as item.py
    participant Cache as Redis cache
    participant GID as get_item_details.py
    User->>IG: save()
    IG->>IG: validate: gán parent_item_group về gốc nếu trống
    IG->>Item: validate_item_group_defaults: validate_item_defaults
    IG->>IG: check_item_tax
    IG->>IG: on_update: NestedSet.on_update, validate_one_root
    IG->>Cache: delete_child_item_groups_key: hdel child_item_groups
    GID->>IG: get_item_group_defaults(item, company)
    IG-->>GID: dòng item_group_defaults của company
```

Nguồn: [item_group.py:33](../../apps/erpnext/erpnext/setup/doctype/item_group/item_group.py#L33), [item_group.py:89](../../apps/erpnext/erpnext/setup/doctype/item_group/item_group.py#L89)

## Giới hạn

- Không vẽ vì chỉ là danh mục hoặc validate đơn giản: `Brand`, `Branch`, `Designation`, `UOM`, `UOM Conversion Factor`, `Currency Exchange`, `Incoterm`, `Terms and Conditions`, `Vehicle`, `Driver`, `Driving License Category`, `Party Type`, `Quotation Lost Reason`, `Sales Partner`, `Target Detail`, `Website Item Group`.
- `Holiday List`, `Sales Person`, `Department`, `Customer Group`, `Supplier Group`, `Territory`, `Global Defaults` chỉ đọc lướt danh sách method; không có luồng riêng.
- `setup/utils.py` (`get_exchange_rate`, `welcome_email`) và `setup/install.py` (`after_install`, tạo role, custom field, navbar) không có sơ đồ: chỉ là chuỗi bước cài đặt tuần tự, không có rẽ nhánh nghiệp vụ.
- Import/export CSV danh sách xóa (`process_import_template`, `export_to_delete_template`) không vẽ. Nút Retry trên form Failed gọi lại `start_deletion_tasks`.
- `get_value_based_rule` của Authorization Control không có nơi gọi trong app này (đã grep trong `erpnext/`); trong Authorization Control, field `to_emp`, `to_designation` chỉ được hàm đó đọc.
- `setup_wizard/operations/company_setup.py` và `defaults_setup.py` không được file Python nào trong app import; có vẻ là code cũ. Sơ đồ wizard dùng `install_fixtures.py`.
- Chưa chắc: `clear_demo_data` gọi `start_deletion_tasks` lần hai sau `submit()` trong khi `on_submit` đã gọi rồi. Theo code, lần hai thấy các status không còn Pending nên không xóa thêm, nhưng status có thể giữ Running đến khi `on_trash` của Company xóa bản ghi. Chưa chạy thử.
- Chưa chắc: `EmailDigest.get_users` đọc `self.recipient_list`, field này không có trong JSON hiện tại.
- Bên trong `Warehouse.insert`, `Account.insert` và `sync_financial_report_templates` không đọc sâu.
