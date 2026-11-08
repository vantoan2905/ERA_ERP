# Module Assets

Quản lý vòng đời tài sản cố định: mua vào, khấu hao, vốn hóa, sửa chữa, di chuyển, đánh giá lại và thanh lý. Module ghi sổ qua `Journal Entry` và `GL Entry` (accounts), xuất kho qua `Stock Entry` và `Stock Ledger Entry` (stock), nhận tài sản từ `Purchase Receipt`/`Purchase Invoice` (buying) và bán qua `Sales Invoice` (accounts).

## Phạm vi

Đọc được 26 doctype trong `assets/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
| --- | --- | --- |
| Tài sản và khấu hao | `Asset`, `Asset Depreciation Schedule`, `Asset Finance Book`, `Asset Category`, `Asset Shift Allocation`; `asset/depreciation.py`, `asset_depreciation_schedule/deppreciation_schedule_controller.py` | Class: Tài sản và khấu hao. Sequence: Tạo Asset từ chứng từ mua, Lưu Asset và tạo lịch khấu hao, Submit Asset, Cancel Asset, Chuyển CWIP sang Fixed Asset, Ghi khấu hao định kỳ, Phân bổ ca khấu hao |
| Chứng từ làm đổi giá trị | `Asset Capitalization`, `Asset Repair`, `Asset Value Adjustment`; `services/gl_composer.py` của hai doctype đầu | Class: Chứng từ làm đổi giá trị. Sequence: Submit và Cancel Asset Capitalization, Asset Repair (lưu nháp, submit, cancel), Asset Value Adjustment |
| Thanh lý và tách | `asset/depreciation.py`, `asset/mapper.py`, `accounts/doctype/sales_invoice/services/fixed_assets.py`, `accounts/doctype/journal_entry/services/asset_service.py` | Sequence: Bán tài sản, Trả lại hoặc hủy hóa đơn bán, Scrap, Restore, Tách tài sản |
| Di chuyển và bảo trì | `Asset Movement`, `Location`, `Asset Maintenance`, `Asset Maintenance Log`, `Asset Maintenance Team` | Class: Di chuyển và bảo trì. Sequence: Asset Movement, Asset Maintenance và Log |

## Class diagram

### Tài sản và khấu hao

```mermaid
classDiagram
    class AccountsController {
        +get_gl_dict()
    }
    class Asset {
        +string item_code
        +string asset_category
        +string asset_type
        +string location
        +float net_purchase_amount
        +float value_after_depreciation
        +bool calculate_depreciation
        +string status
        +create_asset_depreciation_schedule()
        +make_asset_movement()
        +make_gl_entries()
        +validate_make_gl_entry()
        +set_status()
        +get_status()
        +delete_depreciation_entries()
        +sync_value_after_depreciation()
    }
    class AssetFinanceBook {
        +string finance_book
        +string depreciation_method
        +int total_number_of_depreciations
        +int frequency_of_depreciation
        +date depreciation_start_date
        +float expected_value_after_useful_life
        +float value_after_depreciation
        +float value_adjustment_amount
    }
    class AssetCategory {
        +string asset_category_name
        +bool enable_cwip_accounting
        +bool non_depreciable_category
        +validate_accounts()
    }
    class AssetCategoryAccount {
        +string company_name
        +string fixed_asset_account
        +string accumulated_depreciation_account
        +string depreciation_expense_account
        +string capital_work_in_progress_account
    }
    class StraightLineMethod
    class WDVMethod
    class DepreciationScheduleController {
        +create_depreciation_schedule()
        +clear()
        +create()
        +set_accumulated_depreciation()
    }
    class AssetDepreciationSchedule {
        +string asset
        +string finance_book
        +string depreciation_method
        +float value_after_depreciation
        +string status
        +validate_asset()
        +cancel_depreciation_entries()
        +fetch_asset_details()
    }
    class DepreciationSchedule {
        +date schedule_date
        +float depreciation_amount
        +float accumulated_depreciation_amount
        +string journal_entry
        +string shift
    }
    class AssetShiftAllocation {
        +string asset
        +string finance_book
        +string previous_depreciation_schedule
        +update_depr_schedule()
        +create_new_asset_depr_schedule()
        +restore_previous_depr_schedule()
    }
    class AssetShiftFactor
    class AssetActivity {
        +string asset
        +string user
    }
    class JournalEntry

    AccountsController <|-- Asset
    StraightLineMethod <|-- DepreciationScheduleController
    WDVMethod <|-- DepreciationScheduleController
    DepreciationScheduleController <|-- AssetDepreciationSchedule
    Asset *-- AssetFinanceBook : finance_books
    AssetCategory *-- AssetFinanceBook : finance_books
    AssetCategory *-- AssetCategoryAccount : accounts
    AssetDepreciationSchedule *-- DepreciationSchedule : depreciation_schedule
    AssetShiftAllocation *-- DepreciationSchedule : depreciation_schedule
    Asset --> AssetCategory : asset_category
    Asset --> Asset : split_from
    Asset --> JournalEntry : journal_entry_for_scrap
    AssetDepreciationSchedule --> Asset : asset
    DepreciationSchedule --> JournalEntry : journal_entry
    DepreciationSchedule --> AssetShiftFactor : shift
    AssetShiftAllocation --> Asset : asset
    AssetShiftAllocation --> AssetDepreciationSchedule : previous_depreciation_schedule
    AssetActivity --> Asset : asset
```

### Chứng từ làm đổi giá trị

```mermaid
classDiagram
    class AccountsController
    class StockController {
        +make_sl_entries()
        +repost_future_sle_and_gle()
    }
    class Asset {
        +float net_purchase_amount
        +float additional_asset_cost
        +float total_asset_cost
        +float value_after_depreciation
    }
    class AssetCapitalization {
        +string target_asset
        +string target_item_code
        +string target_fixed_asset_account
        +date posting_date
        +float total_value
        +update_stock_ledger()
        +dispose_consumed_assets()
        +make_gl_entries()
        +update_target_asset()
        +restore_consumed_asset_items()
    }
    class AssetCapitalizationStockItem {
        +string item_code
        +string warehouse
        +float stock_qty
        +float valuation_rate
        +float amount
    }
    class AssetCapitalizationAssetItem {
        +string asset
        +float current_asset_value
        +float asset_value
        +string fixed_asset_account
    }
    class AssetCapitalizationServiceItem {
        +string item_code
        +string expense_account
        +float qty
        +float rate
        +float amount
    }
    class AssetRepair {
        +string asset
        +string repair_status
        +datetime failure_date
        +datetime completion_date
        +bool capitalize_repair_cost
        +float total_repair_cost
        +int increase_in_asset_life
        +decrease_stock_quantity()
        +update_asset_value()
        +make_gl_entries()
        +update_status()
    }
    class AssetRepairConsumedItem {
        +string item_code
        +string warehouse
        +string consumed_quantity
        +float valuation_rate
        +float total_value
    }
    class AssetRepairPurchaseInvoice {
        +string purchase_invoice
        +string expense_account
        +float repair_cost
    }
    class AssetValueAdjustment {
        +string asset
        +string finance_book
        +date date
        +float current_asset_value
        +float new_asset_value
        +float difference_amount
        +string journal_entry
        +make_asset_revaluation_entry()
        +cancel_asset_revaluation_entry()
        +update_asset()
    }

    AccountsController <|-- Asset
    AccountsController <|-- StockController
    StockController <|-- AssetCapitalization
    AccountsController <|-- AssetRepair
    AssetCapitalization *-- AssetCapitalizationStockItem : stock_items
    AssetCapitalization *-- AssetCapitalizationAssetItem : asset_items
    AssetCapitalization *-- AssetCapitalizationServiceItem : service_items
    AssetRepair *-- AssetRepairConsumedItem : stock_items
    AssetRepair *-- AssetRepairPurchaseInvoice : invoices
    AssetCapitalization --> Asset : target_asset
    AssetCapitalizationAssetItem --> Asset : asset
    AssetRepair --> Asset : asset
    AssetValueAdjustment --> Asset : asset
```

### Di chuyển và bảo trì

```mermaid
classDiagram
    class Asset {
        +string location
        +string custodian
        +bool maintenance_required
        +has_pending_repair()
    }
    class AssetMovement {
        +string purpose
        +string company
        +datetime transaction_date
        +string reference_doctype
        +string reference_name
        +validate_movement()
        +set_latest_location_and_custodian_in_asset()
        +get_latest_location_and_custodian()
    }
    class AssetMovementItem {
        +string asset
        +string source_location
        +string target_location
        +string from_employee
        +string to_employee
    }
    class Location {
        +string location_name
        +bool is_group
        +float area
        +string parent_location
    }
    class AssetMaintenance {
        +string asset_name
        +string maintenance_team
        +string company
        +sync_maintenance_tasks()
        +close_unassigned_todos()
    }
    class AssetMaintenanceTask {
        +string maintenance_task
        +string maintenance_status
        +string periodicity
        +date next_due_date
        +date last_completion_date
        +string assign_to
    }
    class AssetMaintenanceLog {
        +string asset_maintenance
        +string task
        +string maintenance_status
        +date due_date
        +date completion_date
        +update_maintenance_task()
        +revert_maintenance_task()
        +update_asset_status()
    }
    class AssetMaintenanceTeam {
        +string maintenance_manager
        +string company
    }
    class MaintenanceTeamMember {
        +string team_member
        +string maintenance_role
    }

    AssetMovement *-- AssetMovementItem : assets
    AssetMovementItem --> Asset : asset
    AssetMovementItem --> Location : target_location
    Asset --> Location : location
    Location --> Location : parent_location
    AssetMaintenance *-- AssetMaintenanceTask : asset_maintenance_tasks
    AssetMaintenance --> Asset : asset_name
    AssetMaintenance --> AssetMaintenanceTeam : maintenance_team
    AssetMaintenanceTeam *-- MaintenanceTeamMember : maintenance_team_members
    AssetMaintenanceLog --> AssetMaintenance : asset_maintenance
    AssetMaintenanceLog --> AssetMaintenanceTask : task
```

## Sequence diagram

### Tạo Asset từ chứng từ mua

Khi submit `Purchase Receipt` hoặc `Purchase Invoice` có `update_stock`, item bật `auto_create_assets` sinh Asset nháp bằng `db_insert`, bỏ qua `validate`.

```mermaid
sequenceDiagram
    actor User
    participant PR as Purchase Receipt or Invoice
    participant BC as BuyingController
    participant Item
    participant Asset
    User->>PR: submit()
    PR->>BC: on_submit()
    BC->>BC: process_fixed_asset()
    opt Purchase Invoice không có update_stock
        BC-->>PR: return
    end
    BC->>BC: get_asset_items()
    BC->>BC: auto_make_assets(asset_items)
    BC->>Item: get_asset_item_details(asset_items)
    loop mỗi dòng is_fixed_asset có auto_create_assets và asset_naming_series
        alt is_grouped_asset
            BC->>BC: make_asset(row, is_grouped_asset=True)
        else tài sản đơn lẻ, lặp theo qty
            BC->>BC: make_asset(row)
        end
        BC->>Asset: set_missing_values()
        BC->>Asset: db_insert()
    end
```

Nguồn: [buying_controller.py:1433](../../apps/erpnext/erpnext/controllers/buying_controller.py#L1433), [buying_controller.py:1497](../../apps/erpnext/erpnext/controllers/buying_controller.py#L1497)

### Lưu Asset và tạo lịch khấu hao

Mỗi lần lưu, `on_update` tạo hoặc tính lại một `Asset Depreciation Schedule` nháp cho từng dòng finance book.

```mermaid
sequenceDiagram
    actor User
    participant Asset
    participant FB as Asset Finance Book
    participant ADS as Asset Depreciation Schedule
    participant Ctrl as DepreciationScheduleController
    User->>Asset: save()
    Asset->>Asset: validate()
    Asset->>Asset: before_save()
    Asset->>Asset: on_update()
    Asset->>Asset: create_asset_depreciation_schedule()
    Asset->>FB: set_depr_rate_and_value_after_depreciation()
    opt split_from có giá trị hoặc không calculate_depreciation
        Asset-->>User: dừng tạo lịch
    end
    loop mỗi dòng finance_books
        Asset->>ADS: get_asset_depr_schedule_doc(asset, Draft, finance_book)
        alt chưa có lịch nháp
            Asset->>Ctrl: create_depreciation_schedule(fb_row)
            Ctrl->>Ctrl: fetch_asset_details()
            Ctrl->>Ctrl: clear()
            Ctrl->>Ctrl: create()
            Ctrl->>Ctrl: set_accumulated_depreciation()
            Asset->>ADS: save()
        else đã có lịch nháp
            Asset->>Asset: evaluate_and_recreate_depreciation_schedule(existing_doc, fb_row)
        end
    end
    Asset->>Asset: validate_expected_value_after_useful_life()
    Asset->>Asset: set_total_booked_depreciations()
```

Nguồn: [asset.py:249](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L249), [asset.py:146](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L146), [deppreciation_schedule_controller.py:28](../../apps/erpnext/erpnext/assets/doctype/asset_depreciation_schedule/deppreciation_schedule_controller.py#L28)

### Submit Asset

Submit sinh `Asset Movement` loại Receipt, ghi sổ từ CWIP sang Fixed Asset nếu đủ điều kiện, rồi kích hoạt lịch khấu hao.

```mermaid
sequenceDiagram
    actor User
    participant Asset
    participant AM as Asset Movement
    participant GLL as general_ledger
    participant GL as GL Entry
    participant ADS as Asset Depreciation Schedule
    User->>Asset: submit()
    Asset->>Asset: before_submit()
    opt Composite Asset chưa có capitalization active
        Asset-->>User: throw
    end
    Asset->>Asset: on_submit()
    Asset->>Asset: validate_in_use_date()
    Asset->>AM: make_asset_movement() rồi insert() và submit()
    AM->>Asset: set_latest_location_and_custodian_in_asset()
    opt chưa booked_fixed_asset, không phải Composite Component, validate_make_gl_entry() đúng
        Asset->>Asset: make_gl_entries()
        Asset->>Asset: check_asset_capitalization_gl_entries()
        opt capitalization chưa ghi Fixed Asset và available_for_use_date không ở tương lai
            Asset->>GLL: make_gl_entries(gl_entries)
            GLL->>GL: có CWIP, nợ Fixed Asset
            Asset->>Asset: db_set(booked_fixed_asset, 1)
        end
    end
    opt calculate_depreciation và không có split_from
        Asset->>ADS: convert_draft_asset_depr_schedules_into_active(asset)
        ADS->>ADS: submit()
        ADS->>ADS: on_submit() đặt status Active
    end
    Asset->>Asset: set_status()
    Asset->>Asset: add_asset_activity(name, subject)
```

Nguồn: [asset.py:260](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L260), [asset.py:1033](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L1033)

### Cancel Asset

Cancel gỡ movement, hủy các bút toán khấu hao, hủy lịch khấu hao và đảo GL của chính Asset.

```mermaid
sequenceDiagram
    actor User
    participant Asset
    participant AM as Asset Movement
    participant JE as Journal Entry
    participant ADS as Asset Depreciation Schedule
    participant GLL as general_ledger
    User->>Asset: cancel()
    Asset->>Asset: on_cancel()
    Asset->>Asset: validate_cancellation()
    Asset->>AM: cancel_movement_entries()
    Asset->>JE: delete_depreciation_entries() gọi cancel()
    Asset->>ADS: cancel_asset_depr_schedules(asset)
    ADS->>ADS: on_cancel() đặt status Cancelled
    Asset->>Asset: set_status()
    opt không phải Composite Component
        Asset->>GLL: make_reverse_gl_entries(voucher_type, voucher_no)
        Asset->>Asset: db_set(booked_fixed_asset, 0)
    end
    Asset->>Asset: add_asset_activity(name, subject)
```

Nguồn: [asset.py:275](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L275), [asset.py:818](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L818)

### Chuyển CWIP sang Fixed Asset hằng ngày

Job `daily_maintenance` ghi sổ cho các Asset đã submit nhưng lúc submit chưa tới `available_for_use_date`. Mỗi Asset chạy trong savepoint riêng.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Job as make_post_gl_entry
    participant Cat as Asset Category
    participant Asset
    participant GLL as general_ledger
    participant Log as Error Log
    Sched->>Job: make_post_gl_entry()
    Job->>Cat: get_all(enable_cwip_accounting)
    loop category bật CWIP, Asset chưa booked_fixed_asset và tới available_for_use_date
        Job->>Job: post_cwip_gl_entry(asset_name)
        alt ghi sổ được
            Job->>Asset: validate_make_gl_entry()
            Job->>Asset: make_gl_entries()
            Asset->>GLL: make_gl_entries(gl_entries)
        else có exception
            Job->>Job: rollback(save_point=cwip_gl_entry)
            Job->>Log: log_error()
        end
    end
```

Nguồn: [asset.py:1218](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L1218), [asset.py:1238](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L1238)

### Ghi khấu hao định kỳ

Job `daily_maintenance` tạo `Journal Entry` loại Depreciation Entry cho các dòng lịch đến hạn. Cập nhật giá trị Asset diễn ra trong `AssetService` khi Journal Entry được submit.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Depr as depreciation.py
    participant ADS as Asset Depreciation Schedule
    participant JE as Journal Entry
    participant GL as GL Entry
    participant Svc as AssetService
    participant Asset
    Sched->>Depr: post_depreciation_entries()
    opt book_asset_depreciation_entry_automatically tắt
        Depr-->>Sched: return
    end
    Depr->>Depr: book_depreciation_entries(date)
    Depr->>ADS: get_depreciable_assets_data(date)
    loop mỗi schedule có dòng đến hạn, commit từng schedule
        Depr->>Depr: _make_depreciation_entry(schedule, date, start, stop)
        loop mỗi dòng chưa có journal_entry và schedule_date không sau date
            Depr->>Depr: _make_journal_entry_for_depreciation()
            Depr->>JE: save() rồi submit() nếu không có workflow
            JE->>GL: make_gl_entries()
            JE->>Svc: update_asset_value()
            Svc->>ADS: update_journal_entry_link_on_depr_schedule(asset, je_row)
            Svc->>Asset: update_value_after_depreciation(asset, depr_amount)
            Svc->>Asset: sync_value_after_depreciation()
        end
        Depr->>Asset: set_status()
        Depr->>Asset: db_set(depr_entry_posting_status, Successful)
    end
    opt có Asset lỗi
        Depr->>Asset: set_depr_entry_posting_status_for_failed_assets(names)
        Depr->>Depr: notify_depr_entry_posting_error(names, logs)
    end
```

Nguồn: [depreciation.py:37](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L37), [depreciation.py:182](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L182), [asset_service.py:58](../../apps/erpnext/erpnext/accounts/doctype/journal_entry/services/asset_service.py#L58)

### Phân bổ ca khấu hao (Asset Shift Allocation)

Đổi số ca trên lịch shift-based. Submit thay lịch Active bằng bản sao mang các dòng mới, cancel khôi phục lịch cũ.

```mermaid
sequenceDiagram
    actor User
    participant ASA as Asset Shift Allocation
    participant ADS as Asset Depreciation Schedule
    participant New as ADS mới
    participant Asset
    User->>ASA: insert()
    ASA->>ADS: get_asset_depr_schedule_doc(asset, Active, finance_book)
    ASA->>ASA: after_insert() gọi fetch_and_set_depr_schedule()
    User->>ASA: save() sau khi sửa shift
    ASA->>ASA: validate_invalid_shift_change()
    ASA->>ASA: update_depr_schedule()
    ASA->>ADS: get_temp_depr_schedule_doc(asset, fb_row, updated_depr_schedule)
    alt submit
        User->>ASA: submit()
        ASA->>ASA: create_new_asset_depr_schedule()
        ASA->>ADS: replace_active_depr_schedule() gọi cancel()
        ASA->>New: submit()
        ASA->>Asset: add_asset_activity(asset, subject)
    else cancel
        User->>ASA: cancel()
        ASA->>ASA: restore_previous_depr_schedule()
        ASA->>ASA: validate_previous_depr_schedule_restorable(active)
        ASA->>ADS: replace_active_depr_schedule() gọi cancel()
        ASA->>New: submit() bản sao previous_depreciation_schedule
    end
```

Nguồn: [asset_shift_allocation.py:44](../../apps/erpnext/erpnext/assets/doctype/asset_shift_allocation/asset_shift_allocation.py#L44), [asset_shift_allocation.py:227](../../apps/erpnext/erpnext/assets/doctype/asset_shift_allocation/asset_shift_allocation.py#L227), [asset_shift_allocation.py:261](../../apps/erpnext/erpnext/assets/doctype/asset_shift_allocation/asset_shift_allocation.py#L261)

### Submit Asset Capitalization

Gộp vật tư, tài sản khác và dịch vụ vào một Target Asset loại Composite Asset còn nháp. Tài sản tiêu thụ bị thanh lý, người dùng submit Target Asset ở bước sau.

```mermaid
sequenceDiagram
    actor User
    participant AC as Asset Capitalization
    participant SLE as Stock Ledger Entry
    participant Depr as depreciation.py
    participant Consumed as Asset tiêu thụ
    participant Composer as AssetCapitalizationGLComposer
    participant GL as GL Entry
    participant Target as Target Asset
    User->>AC: submit()
    AC->>AC: before_submit() gọi validate_source_mandatory()
    AC->>AC: on_submit()
    AC->>AC: make_bundle_using_old_serial_batch_fields()
    AC->>SLE: update_stock_ledger() gọi make_sl_entries()
    AC->>AC: dispose_consumed_assets()
    loop mỗi dòng asset_items
        opt không phải Composite Component
            AC->>Depr: depreciate_asset(asset, posting_date, notes)
        end
        AC->>Consumed: db_set(disposal_date, posting_date)
        AC->>Consumed: set_status(Capitalized)
    end
    AC->>Composer: make_gl_entries() gọi compose()
    Composer->>Depr: get_gl_entries_on_asset_disposal(asset, asset_value)
    Composer-->>AC: gl_entries, nợ tài khoản đích
    AC->>GL: make_gl_entries(gl_entries, merge_entries=False)
    AC->>AC: repost_future_sle_and_gle()
    AC->>Target: update_target_asset() gọi add_to_target_asset_cost(amount)
```

Nguồn: [asset_capitalization.py:113](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/asset_capitalization.py#L113), [asset_capitalization.py:524](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/asset_capitalization.py#L524), [gl_composer.py:20](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/services/gl_composer.py#L20)

### Cancel Asset Capitalization

Chỉ cancel được khi Target Asset chưa submit. Đảo sổ kho và GL, khôi phục tài sản tiêu thụ, trừ chi phí khỏi Target Asset.

```mermaid
sequenceDiagram
    actor User
    participant AC as Asset Capitalization
    participant SLE as Stock Ledger Entry
    participant GLL as general_ledger
    participant Depr as depreciation.py
    participant Consumed as Asset tiêu thụ
    participant Target as Target Asset
    User->>AC: cancel()
    AC->>AC: before_cancel()
    alt Target Asset đã submit
        AC-->>User: throw
    else Target Asset chưa submit
        AC->>AC: on_cancel()
        AC->>SLE: update_stock_ledger()
        AC->>GLL: make_gl_entries() gọi make_reverse_gl_entries(voucher_type, voucher_no)
        AC->>AC: repost_future_sle_and_gle()
        AC->>AC: restore_consumed_asset_items()
        loop mỗi dòng asset_items
            AC->>Consumed: set_status()
            opt calculate_depreciation
                AC->>Depr: reverse_depreciation_entry_made_on_disposal(asset)
                AC->>Depr: reset_depreciation_schedule(asset, notes)
            end
            AC->>Consumed: db_set(disposal_date, None)
        end
        AC->>Target: update_target_asset() với giá trị âm
    end
```

Nguồn: [asset_capitalization.py:121](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/asset_capitalization.py#L121), [asset_capitalization.py:129](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/asset_capitalization.py#L129), [asset_capitalization.py:542](../../apps/erpnext/erpnext/assets/doctype/asset_capitalization/asset_capitalization.py#L542)

### Lưu nháp Asset Repair và cập nhật trạng thái Asset

Mỗi lần lưu nháp, trạng thái Asset được tính lại bằng tác vụ nền sau commit: repair `Pending` làm Asset thành `Out of Order`.

```mermaid
sequenceDiagram
    actor User
    participant AR as Asset Repair
    participant Act as Asset Activity
    participant Q as Queue
    participant Asset
    User->>AR: save()
    AR->>AR: validate()
    AR->>AR: validate_asset()
    AR->>AR: validate_purchase_invoices()
    AR->>AR: calculate_total_repair_cost()
    AR->>AR: on_update()
    opt repair_status đổi
        AR->>Act: add_repair_activity(repair_status)
    end
    opt còn nháp
        AR->>Q: update_status() gọi enqueue(update_asset_status_after_repair, enqueue_after_commit)
        Q->>Asset: update_asset_status_after_repair(asset)
        Asset->>Asset: set_status()
        Asset->>Asset: has_pending_repair()
    end
```

Nguồn: [asset_repair.py:80](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L80), [asset_repair.py:208](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L208), [asset_repair.py:443](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L443)

### Submit Asset Repair

Chỉ submit được khi `repair_status` là Completed. Vật tư xuất qua `Stock Entry` Material Issue. Vốn hóa chi phí là tùy chọn và làm tính lại lịch khấu hao.

```mermaid
sequenceDiagram
    actor User
    participant AR as Asset Repair
    participant SE as Stock Entry
    participant SLE as Stock Ledger Entry
    participant Asset
    participant ADS as Asset Depreciation Schedule
    participant Composer as AssetRepairGLComposer
    participant GL as GL Entry
    User->>AR: submit()
    AR->>AR: check_repair_status()
    AR->>AR: on_submit()
    opt có stock_items
        AR->>SE: decrease_stock_quantity() gọi insert() và submit()
        SE->>SLE: update_stock_ledger()
        SE->>GL: make_gl_entries()
        AR->>AR: set_consumed_items_cost_from_stock_entry()
    end
    opt capitalize_repair_cost
        AR->>Asset: update_asset_value() rồi save()
        AR->>Asset: set_increase_in_asset_life()
        AR->>ADS: reschedule_depreciation(asset, notes)
        AR->>Composer: make_gl_entries() gọi compose()
        Composer-->>AR: gl_entries
        AR->>GL: make_gl_entries(gl_entries, cancel)
    end
    AR->>Asset: add_asset_activity()
    AR->>AR: update_status() gọi enqueue(update_asset_status_after_repair)
```

Nguồn: [asset_repair.py:229](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L229), [asset_repair.py:326](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L326), [gl_composer.py:20](../../apps/erpnext/erpnext/assets/doctype/asset_repair/services/gl_composer.py#L20)

### Cancel Asset Repair

Hủy `Stock Entry` đã sinh và, nếu đã vốn hóa, đảo giá trị Asset, GL và lịch khấu hao.

```mermaid
sequenceDiagram
    actor User
    participant AR as Asset Repair
    participant SE as Stock Entry
    participant Asset
    participant GLL as general_ledger
    participant ADS as Asset Depreciation Schedule
    participant SABB as Serial and Batch Bundle
    User->>AR: cancel()
    AR->>AR: on_cancel()
    AR->>SE: cancel_stock_entry()
    opt capitalize_repair_cost
        AR->>Asset: update_asset_value() với giá trị âm
        AR->>GLL: make_gl_entries(cancel=True)
        AR->>Asset: set_increase_in_asset_life()
        AR->>ADS: reschedule_depreciation(asset, notes)
    end
    AR->>Asset: add_asset_activity()
    AR->>SABB: cancel_sabb()
```

Nguồn: [asset_repair.py:252](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L252), [asset_repair.py:268](../../apps/erpnext/erpnext/assets/doctype/asset_repair/asset_repair.py#L268)

### Asset Movement

Asset Movement không ghi sổ. Khi submit hoặc cancel, `location` và `custodian` của Asset được tính lại từ movement submit mới nhất.

```mermaid
sequenceDiagram
    actor User
    participant AM as Asset Movement
    participant AMI as Asset Movement Item
    participant Asset
    participant Act as Asset Activity
    alt submit
        User->>AM: submit()
        AM->>AM: validate_duplicate_assets()
        loop mỗi dòng assets
            AM->>Asset: validate_asset(d)
            AM->>AMI: validate_movement(d)
            AM->>AM: validate_transaction_date(d)
        end
        AM->>AM: on_submit()
    else cancel
        User->>AM: cancel()
        AM->>AM: on_cancel()
    end
    AM->>AM: set_latest_location_and_custodian_in_asset()
    loop mỗi dòng assets
        AM->>AMI: get_latest_location_and_custodian(asset)
        AM->>Asset: update_asset_location_and_custodian(asset_id, location, employee)
        AM->>Act: log_asset_activity(asset_id, location, employee, previous_custodian)
    end
```

Nguồn: [asset_movement.py:37](../../apps/erpnext/erpnext/assets/doctype/asset_movement/asset_movement.py#L37), [asset_movement.py:134](../../apps/erpnext/erpnext/assets/doctype/asset_movement/asset_movement.py#L134)

### Asset Value Adjustment

Đánh giá lại tài sản bằng một `Journal Entry` giữa Fixed Asset và `difference_account`, sau đó tính lại lịch khấu hao.

```mermaid
sequenceDiagram
    actor User
    participant AVA as Asset Value Adjustment
    participant JE as Journal Entry
    participant GL as GL Entry
    participant Asset
    participant ADS as Asset Depreciation Schedule
    User->>AVA: save()
    AVA->>AVA: validate_asset_not_disposed()
    AVA->>AVA: set_current_asset_value()
    AVA->>AVA: set_difference_amount()
    alt submit
        User->>AVA: submit()
        AVA->>JE: make_asset_revaluation_entry() gọi submit()
        JE->>GL: make_gl_entries()
        AVA->>AVA: db_set(journal_entry, name)
    else cancel
        User->>AVA: cancel()
        AVA->>AVA: before_cancel() gọi validate_asset_not_split()
        AVA->>JE: cancel_asset_revaluation_entry() gọi cancel()
    end
    AVA->>AVA: update_asset()
    AVA->>Asset: update_asset_value_after_depreciation()
    AVA->>ADS: reschedule_depreciation(asset, note)
    AVA->>Asset: set_status()
    AVA->>Asset: add_asset_activity(asset, subject)
```

Nguồn: [asset_value_adjustment.py:150](../../apps/erpnext/erpnext/assets/doctype/asset_value_adjustment/asset_value_adjustment.py#L150), [asset_value_adjustment.py:170](../../apps/erpnext/erpnext/assets/doctype/asset_value_adjustment/asset_value_adjustment.py#L170), [asset_value_adjustment.py:268](../../apps/erpnext/erpnext/assets/doctype/asset_value_adjustment/asset_value_adjustment.py#L268)

### Thanh lý: bán tài sản qua Sales Invoice

Dòng hóa đơn có `is_fixed_asset`. Hóa đơn tách phần chưa bán, khấu hao đến ngày bán, rồi ghi sổ thanh lý cùng hóa đơn.

```mermaid
sequenceDiagram
    actor User
    participant SI as Sales Invoice
    participant Svc as FixedAssetService
    participant Map as mapper.py
    participant Depr as depreciation.py
    participant Asset
    participant Composer as SalesInvoiceGLComposer
    participant GL as GL Entry
    User->>SI: make_sales_invoice(asset, item_code, company, sell_qty)
    User->>SI: submit()
    SI->>Svc: validate_fixed_asset()
    SI->>SI: on_submit()
    SI->>Svc: split_asset_based_on_sale_qty()
    opt qty bán nhỏ hơn asset_quantity
        Svc->>Map: split_asset(asset, remaining_qty)
    end
    SI->>Svc: process_asset_depreciation()
    opt calculate_depreciation và chưa Fully Depreciated
        Svc->>Depr: _depreciate_asset_on_sale() gọi depreciate_asset(asset, disposal_date, notes)
    end
    Svc->>Asset: _update_asset() db_set(disposal_date) và set_status(Sold)
    SI->>Svc: set_asset_disposal_values()
    SI->>Composer: make_gl_entries() gọi get_gl_entries_for_fixed_asset(item, gl_entries)
    Composer->>Depr: get_gl_entries_on_asset_disposal(asset, base_net_amount)
    Composer-->>SI: gl_entries
    SI->>GL: make_gl_entries(gl_entries)
```

Nguồn: [sales_invoice.py:443](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L443), [fixed_assets.py:77](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/services/fixed_assets.py#L77), [gl_composer.py:408](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/services/gl_composer.py#L408), [depreciation.py:661](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L661)

### Thanh lý: trả lại hoặc hủy hóa đơn bán

Hóa đơn trả hàng được submit, hoặc hóa đơn bán bị cancel, đều khôi phục tài sản. Với hóa đơn trả hàng, GL `get_gl_entries_on_asset_regain` được ghi trước khi đảo khấu hao.

```mermaid
sequenceDiagram
    actor User
    participant SI as Sales Invoice
    participant Svc as FixedAssetService
    participant Depr as depreciation.py
    participant Asset
    participant GL as GL Entry
    alt submit hóa đơn is_return
        User->>SI: submit()
        SI->>Svc: set_asset_disposal_values()
        SI->>Depr: make_gl_entries() qua get_gl_entries_on_asset_regain(asset, base_net_amount)
        Depr-->>SI: gl_entries
        SI->>GL: make_gl_entries(gl_entries)
        SI->>Svc: process_asset_depreciation()
    else cancel hóa đơn bán
        User->>SI: cancel()
        SI->>Svc: process_asset_depreciation()
    end
    Svc->>Depr: _restore_asset() gọi reverse_depreciation_entry_made_on_disposal(asset)
    Svc->>Depr: reset_depreciation_schedule(asset, notes)
    Svc->>Asset: _update_asset() db_set(disposal_date, None) và set_status()
    opt cancel hóa đơn bán
        SI->>GL: make_gl_entries_on_cancel()
    end
```

Nguồn: [sales_invoice.py:545](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py#L545), [fixed_assets.py:133](../../apps/erpnext/erpnext/accounts/doctype/sales_invoice/services/fixed_assets.py#L133), [depreciation.py:601](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L601)

### Thanh lý: scrap tài sản

Scrap tính khấu hao đến ngày thanh lý rồi tạo `Journal Entry` loại Asset Disposal. `journal_entry_for_scrap` được đặt trong `AssetService`, không phải trong `create_journal_entry_for_scrap`.

```mermaid
sequenceDiagram
    actor User
    participant Depr as depreciation.py
    participant Asset
    participant ADS as Asset Depreciation Schedule
    participant JE as Journal Entry
    participant GL as GL Entry
    participant Svc as AssetService
    User->>Depr: scrap_asset(asset_name, scrap_date)
    Depr->>Asset: db_set(disposal_date, scrap_date)
    Depr->>Depr: validate_asset_for_scrap(asset, scrap_date)
    opt calculate_depreciation
        Depr->>Depr: depreciate_asset(asset, date, notes)
        Depr->>ADS: reschedule_depreciation(asset, notes, disposal_date)
        Depr->>JE: make_depreciation_entry_on_disposal(asset, disposal_date)
        Depr->>Depr: cancel_depreciation_entries(asset, date)
    end
    Depr->>Depr: create_journal_entry_for_scrap(asset, scrap_date)
    Depr->>Depr: get_gl_entries_on_asset_disposal(asset, scrap_date)
    Depr->>JE: save() rồi submit() nếu không có workflow
    JE->>GL: make_gl_entries()
    JE->>Svc: update_asset_value()
    Svc->>Asset: update_asset_on_disposal() ghi journal_entry_for_scrap
    Svc->>Asset: set_status()
    Depr->>Asset: add_asset_activity(asset, subject)
```

Nguồn: [depreciation.py:373](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L373), [depreciation.py:493](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L493), [depreciation.py:440](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L440), [asset_service.py:108](../../apps/erpnext/erpnext/accounts/doctype/journal_entry/services/asset_service.py#L108)

### Thanh lý: restore tài sản đã scrap

Đảo bút toán khấu hao lúc thanh lý, tính lại lịch, rồi hủy bút toán scrap.

```mermaid
sequenceDiagram
    actor User
    participant Depr as depreciation.py
    participant Asset
    participant ADS as Asset Depreciation Schedule
    participant JE as Journal Entry
    participant GL as GL Entry
    User->>Depr: restore_asset(asset_name)
    Depr->>Depr: reverse_depreciation_entry_made_on_disposal(asset)
    loop dòng lịch có schedule_date bằng disposal_date và có journal_entry
        opt không trùng ngày lịch gốc, hoặc disposal_date ở tương lai
            Depr->>JE: create_reverse_depreciation_entry(asset_name, journal_entry)
            JE->>GL: make_gl_entries()
            Depr->>ADS: update_value_after_depreciation_on_asset_restore(schedule, row, journal_entry)
        end
    end
    Depr->>Asset: sync_value_after_depreciation()
    Depr->>ADS: reset_depreciation_schedule(asset, notes)
    Depr->>Asset: cancel_journal_entry_for_scrap(asset)
    Asset->>JE: cancel()
    JE->>GL: make_gl_entries(1)
    Depr->>Asset: set_status()
    Depr->>Asset: add_asset_activity(asset_name, subject)
```

Nguồn: [depreciation.py:466](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L466), [depreciation.py:520](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L520)

### Tách tài sản (split_asset)

Tách theo số lượng: tạo Asset mới có `split_from`, co giá trị Asset cũ theo tỷ lệ, chép lịch khấu hao và chia lại các `Journal Entry` đã ghi.

```mermaid
sequenceDiagram
    actor Caller as User hoặc FixedAssetService
    participant Map as mapper.py
    participant Old as Asset cũ
    participant New as Asset mới
    participant ADS as Asset Depreciation Schedule
    participant JE as Journal Entry
    participant GL as GL Entry
    Caller->>Map: split_asset(asset_name, split_qty)
    Map->>Map: validate_asset_split(existing_asset, split_qty)
    Map->>New: create_new_asset_from_split(existing_asset, split_qty)
    Map->>New: set_split_asset_values() rồi log_asset_activity() gọi insert() và submit()
    Map->>ADS: update_finance_books() gọi reschedule_depr_for_updated_asset() và submit() lịch mới
    loop dòng lịch đã có journal_entry của Asset mới
        Map->>JE: add_reference_in_jv_on_split(entry_name, new, old, amount)
        JE->>GL: make_gl_entries(1)
        JE->>GL: make_gl_entries()
    end
    Map->>Old: update_existing_asset_after_split(existing_asset, remaining_qty, splitted_asset)
    Map->>Old: set_split_asset_values() rồi save()
    Map->>ADS: reschedule_depr_for_updated_asset() gọi cancel() lịch cũ và submit() lịch mới
```

Nguồn: [mapper.py:195](../../apps/erpnext/erpnext/assets/doctype/asset/mapper.py#L195), [mapper.py:231](../../apps/erpnext/erpnext/assets/doctype/asset/mapper.py#L231), [mapper.py:361](../../apps/erpnext/erpnext/assets/doctype/asset/mapper.py#L361)

### Asset Maintenance và Maintenance Log

Lưu `Asset Maintenance` gán ToDo và sinh `Asset Maintenance Log` cho từng task. Submit log tính kỳ tiếp theo. Hai job hằng ngày cập nhật trạng thái.

```mermaid
sequenceDiagram
    actor User
    participant AM as Asset Maintenance
    participant Task as Asset Maintenance Task
    participant Log as Asset Maintenance Log
    participant Asset
    participant Sched as Scheduler
    User->>AM: save()
    AM->>AM: validate()
    AM->>AM: on_update()
    AM->>AM: assign_tasks(name, assign_to, task, next_due_date)
    AM->>AM: sync_maintenance_tasks()
    AM->>Log: update_maintenance_log(asset_maintenance, item_code, item_name, task)
    User->>Log: submit() với status Completed hoặc Cancelled
    Log->>Task: update_maintenance_task()
    opt Completed
        Log->>Task: calculate_next_due_date(periodicity, end_date, last_completion_date)
    end
    Log->>AM: save() để sinh log kỳ sau
    Log->>Asset: update_asset_status()
    Sched->>Log: update_asset_maintenance_log_status()
    Sched->>Asset: update_maintenance_status()
    Asset->>Asset: has_pending_repair()
    Asset->>Log: has_due_maintenance(asset_name)
    Asset->>Asset: set_status()
```

Nguồn: [asset_maintenance.py:80](../../apps/erpnext/erpnext/assets/doctype/asset_maintenance/asset_maintenance.py#L80), [asset_maintenance_log.py:69](../../apps/erpnext/erpnext/assets/doctype/asset_maintenance_log/asset_maintenance_log.py#L69), [asset_maintenance_log.py:136](../../apps/erpnext/erpnext/assets/doctype/asset_maintenance_log/asset_maintenance_log.py#L136), [asset.py:1189](../../apps/erpnext/erpnext/assets/doctype/asset/asset.py#L1189)

## Giới hạn

- Không có sequence riêng: `Asset Category`, `Asset Shift Factor`, `Asset Maintenance Team`, `Location` (chủ yếu là validate và tính diện tích địa lý), các bảng con. `Location` và `Asset Category` chỉ đọc danh sách method, chưa đọc kỹ thân hàm.
- `Linked Location` không xuất hiện trong sơ đồ: ngoài thư mục doctype của nó, tìm thấy trong `.py`/`.json` chỉ có một patch cũ `v11_0/merge_land_unit_with_location.py`.
- Thuật toán tính số tiền khấu hao (`StraightLineMethod`, `WDVMethod`, phần lớn `deppreciation_schedule_controller.py`) chỉ đọc lướt, sơ đồ dừng ở mức `create_depreciation_schedule`.
- `Asset Capitalization` chỉ đọc tới dòng khoảng 670; các hàm whitelisted lấy chi tiết dòng sau đó không đưa vào sơ đồ.
- Luồng `Stock Entry` và `Journal Entry` chỉ vẽ tới `update_stock_ledger`/`make_gl_entries`, không đi vào bên trong `stock_ledger.py` và `general_ledger.py`. Với `Stock Entry`, chỉ đọc lướt `on_submit`, chưa xác nhận các điều kiện quanh hai lời gọi này.
- Đáng lưu ý: [depreciation.py:450](../../apps/erpnext/erpnext/assets/doctype/asset/depreciation.py#L450) truyền `scrap_date` vào tham số vị trí thứ hai của `get_gl_entries_on_asset_disposal`, mà tham số đó là `selling_amount`. Theo code, `flt()` của một giá trị date trả `0.0` nên phần lãi lỗ vẫn tính với giá bán 0, còn `date` của hàm rơi về ngày hiện tại. Sơ đồ vẽ đúng lời gọi này; chưa chạy thử.
- `make_draft_asset_depr_schedule` ([asset_depreciation_schedule.py:212](../../apps/erpnext/erpnext/assets/doctype/asset_depreciation_schedule/asset_depreciation_schedule.py#L212)) không có nơi gọi trong `.py`/`.json` đã tìm, nên không vẽ.
- Thứ tự giữa hook `update_asset_value` và `make_gl_entries` trong `Journal Entry.on_submit` đã đọc; các bước khác của `on_submit` (`check_credit_limit`, inter-company, invoice discounting) được lược bỏ. Tương tự, `Sales Invoice.on_submit` chỉ vẽ phần liên quan đến tài sản.
- Điều kiện `doc.is_return` trong luồng trả hàng dựa trên `process_asset_depreciation`; luồng cancel một hóa đơn trả hàng (lại khấu hao và đặt `Sold`) không vẽ riêng.
