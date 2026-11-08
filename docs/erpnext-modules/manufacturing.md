# Module Manufacturing

Module quản lý sản xuất, từ định mức (BOM), dự báo và lập kế hoạch (Sales Forecast, Master Production Schedule, Production Plan) đến thực thi (Work Order, Job Card, Workstation, Plant Floor). Module nối với `stock` (Stock Entry, Stock Reservation Entry, Bin, sổ kho), `selling` (Sales Order), `buying` (Purchase Order, Material Request), `subcontracting` và `accounts` (GL Entry qua Stock Entry).

## Phạm vi

Đọc được 51 doctype trong `manufacturing/doctype/`. Phần lớn logic của BOM, Production Plan và Work Order đã tách sang thư mục `services/`, class doctype chỉ gọi tiếp.

| Nhóm chức năng | Doctype / file chính | Sơ đồ |
|---|---|---|
| Định mức | BOM, Routing, Operation, BOM Creator (`bom/bom.py`, `bom/services/costing.py`, `bom_creator/bom_plan.py`) | Class: Định mức. Sequence: Submit BOM, Cập nhật giá một BOM, BOM Creator |
| Công cụ BOM | BOM Update Tool, BOM Update Log, BOM Update Batch (`bom_update_log.py`, `bom_updation_utils.py`) | Class: Định mức. Sequence: Replace BOM, Update Cost |
| Lập kế hoạch | Production Plan, Production Plan Schedule (`production_plan/services/*`, `scheduling/*`) | Class: Kế hoạch. Sequence: Lập và submit, Tạo Work Order, Tạo Material Request, Xếp lịch |
| Dự báo | Sales Forecast, Master Production Schedule, report `material_requirements_planning_report` | Class: Kế hoạch. Sequence: Dự báo đến MRP |
| Thực thi | Work Order (`work_order/services/*`, `work_order/mapper.py`) | Class: Thực thi. Sequence: Submit Work Order, Chuyển vật tư và nhập thành phẩm |
| Công đoạn | Job Card, Job Card Time Log (`job_card/job_card.py`, `job_card/mapper.py`, `page/shop_floor/shop_floor.py`) | Class: Thực thi. Sequence: Chấm công Job Card, Job Card bán thành phẩm và gia công |
| Xưởng | Workstation, Workstation Type, Plant Floor, Downtime Entry | Class: Thực thi. Sequence: Plant Floor |
| Khác | Blanket Order, Manufacturing Settings | Không vẽ, xem Giới hạn |

## Class diagram

Class không ghi cha đều kế thừa trực tiếp `Document`. Service class như `BOMCostingService`, `OperationsService` không phải doctype nên không vẽ ở đây, mà xuất hiện trong sequence.

### Định mức

```mermaid
classDiagram
    class WebsiteGenerator
    class BOM {
        +string item
        +float quantity
        +bool is_active
        +bool is_default
        +bool with_operations
        +float raw_material_cost
        +float operating_cost
        +float total_cost
        +validate()
        +on_submit()
        +on_cancel()
        +manage_default_bom()
        +update_cost()
        +calculate_cost()
        +update_exploded_items()
        +check_recursion()
    }
    class BOMItem {
        +string item_code
        +string bom_no
        +float qty
        +float rate
        +float amount
        +bool do_not_explode
    }
    class BOMOperation {
        +string operation
        +string workstation
        +string workstation_type
        +float time_in_mins
        +float hour_rate
        +string bom_no
    }
    class BOMExplosionItem {
        +string item_code
        +float stock_qty
        +float rate
        +float qty_consumed_per_unit
    }
    class BOMSecondaryItem {
        +string item_code
        +string secondary_item_type
        +float stock_qty
        +float cost_allocation_per
        +string valuation_type
    }
    class Routing {
        +string routing_name
        +bool disabled
        +validate()
        +calculate_operating_cost()
    }
    class Operation {
        +string workstation
        +float total_operation_time
        +int batch_size
        +bool is_corrective_operation
    }
    class SubOperation {
        +string operation
        +float time_in_mins
    }
    class BOMUpdateTool {
        +string current_bom
        +string new_bom
    }
    class BOMUpdateLog {
        +string update_type
        +string status
        +string current_bom
        +string new_bom
        +int current_level
        +validate()
        +on_submit()
        +clear_old_logs()
    }
    class BOMUpdateBatch {
        +int level
        +int batch_no
        +text boms_updated
        +string status
    }
    class BOMCreator {
        +string item_code
        +string status
        +int revision
        +bool track_semi_finished_goods
        +validate()
        +on_submit()
        +make_new_revision()
        +enqueue_create_boms()
        +create_boms()
        +get_bom_plan()
    }
    class BOMCreatorItem {
        +string item_code
        +string bom_no
        +int node_id
        +int parent_node_id
        +bool bom_created
    }
    class BOMCreatorOperation {
        +string operation
        +int operation_id
        +int bom_node_id
        +float time_in_mins
    }

    WebsiteGenerator <|-- BOM
    BOM *-- BOMItem : items
    BOM *-- BOMOperation : operations
    BOM *-- BOMExplosionItem : exploded_items
    BOM *-- BOMSecondaryItem : secondary_items
    BOM --> Routing : routing
    BOM --> BOMCreator : bom_creator
    BOMItem --> BOM : bom_no
    BOMItem --> Operation : operation
    BOMOperation --> BOM : bom_no
    BOMOperation --> Operation : operation
    Routing *-- BOMOperation : operations
    Operation *-- SubOperation : sub_operations
    SubOperation --> Operation : operation
    BOMUpdateTool --> BOM : current_bom
    BOMUpdateTool --> BOM : new_bom
    BOMUpdateLog --> BOM : current_bom
    BOMUpdateLog --> BOM : new_bom
    BOMUpdateLog *-- BOMUpdateBatch : bom_batches
    BOMCreator *-- BOMCreatorItem : items
    BOMCreator *-- BOMCreatorOperation : operations
    BOMCreatorItem --> BOM : bom_no
```

### Kế hoạch

```mermaid
classDiagram
    class BOM
    class WorkOrder
    class ProductionPlan {
        +string company
        +string get_items_from
        +string status
        +float total_planned_qty
        +float total_produced_qty
        +bool reserve_stock
        +validate()
        +on_submit()
        +on_cancel()
        +get_items()
        +get_sub_assembly_items()
        +make_work_order()
        +make_material_request()
        +update_produced_pending_qty()
        +set_status()
    }
    class ProductionPlanItem {
        +string item_code
        +string bom_no
        +float planned_qty
        +float pending_qty
        +float produced_qty
        +string sales_order
    }
    class ProductionPlanSubAssemblyItem {
        +string production_item
        +string bom_no
        +float qty
        +string type_of_manufacturing
        +string supplier
        +string production_plan_item
    }
    class MaterialRequestPlanItem {
        +string item_code
        +string warehouse
        +string material_request_type
        +float quantity
        +float requested_qty
        +string from_bom
    }
    class ProductionPlanSalesOrder {
        +string sales_order
        +string customer
        +float grand_total
    }
    class ProductionPlanMaterialRequest {
        +string material_request
        +date material_request_date
    }
    class ProductionPlanItemReference {
        +string item_reference
        +string sales_order
        +float qty
    }
    class ProductionPlanMaterialRequestWarehouse {
        +string warehouse
    }
    class ProductionPlanSchedule {
        +string production_plan
        +string plan_row
        +string operation
        +string workstation
        +datetime from_time
        +datetime to_time
    }
    class SalesForecast {
        +string company
        +date from_date
        +int demand_number
        +string frequency
        +string status
        +validate()
        +generate_demand()
        +generate_manual_demand()
        +on_cancel()
    }
    class SalesForecastItem {
        +string item_code
        +date delivery_date
        +float demand_qty
    }
    class MasterProductionSchedule {
        +string company
        +string sales_forecast
        +date from_date
        +date to_date
        +validate()
        +get_actual_demand()
        +get_demand_data()
        +on_update()
    }
    class MasterProductionScheduleItem {
        +string item_code
        +string bom_no
        +date delivery_date
        +float planned_qty
        +date order_release_date
        +int cumulative_lead_time
    }

    ProductionPlan *-- ProductionPlanItem : po_items
    ProductionPlan *-- ProductionPlanSubAssemblyItem : sub_assembly_items
    ProductionPlan *-- MaterialRequestPlanItem : mr_items
    ProductionPlan *-- ProductionPlanSalesOrder : sales_orders
    ProductionPlan *-- ProductionPlanMaterialRequest : material_requests
    ProductionPlan *-- ProductionPlanItemReference : prod_plan_references
    ProductionPlan *-- ProductionPlanMaterialRequestWarehouse : warehouses
    ProductionPlanSchedule --> ProductionPlan : production_plan
    ProductionPlanItem --> BOM : bom_no
    ProductionPlanSubAssemblyItem --> BOM : bom_no
    MaterialRequestPlanItem --> BOM : from_bom
    SalesForecast *-- SalesForecastItem : items
    SalesForecast *-- SalesForecastItem : selected_items
    MasterProductionSchedule --> SalesForecast : sales_forecast
    MasterProductionSchedule *-- MasterProductionScheduleItem : items
    MasterProductionSchedule *-- MasterProductionScheduleItem : select_items
    MasterProductionSchedule *-- ProductionPlanSalesOrder : sales_orders
    MasterProductionSchedule *-- ProductionPlanMaterialRequest : material_requests
    MasterProductionScheduleItem --> BOM : bom_no
    WorkOrder --> ProductionPlan : production_plan
    WorkOrder --> MasterProductionSchedule : mps
```

### Thực thi

```mermaid
classDiagram
    class BOM
    class WorkOrder {
        +string production_item
        +string bom_no
        +float qty
        +float produced_qty
        +float material_transferred_for_manufacturing
        +string status
        +bool reserve_stock
        +bool track_semi_finished_goods
        +validate()
        +before_submit()
        +on_submit()
        +on_close_or_cancel()
        +create_job_card_from_wo()
        +update_work_order_qty()
        +update_status()
        +update_required_items()
    }
    class WorkOrderItem {
        +string item_code
        +string source_warehouse
        +float required_qty
        +float transferred_qty
        +float consumed_qty
        +float stock_reserved_qty
    }
    class WorkOrderOperation {
        +string operation
        +string workstation
        +string status
        +float completed_qty
        +float time_in_mins
        +float actual_operating_cost
    }
    class WorkOrderAdditionalItem {
        +string item_code
        +float qty
        +float rate
    }
    class JobCard {
        +string work_order
        +string operation
        +string workstation
        +float for_quantity
        +float total_completed_qty
        +float manufactured_qty
        +string status
        +bool is_corrective_job_card
        +validate()
        +on_submit()
        +on_cancel()
        +start_timer()
        +complete_job_card()
        +update_work_order()
        +set_manufactured_qty()
        +make_stock_entry_for_semi_fg_item()
    }
    class JobCardTimeLog {
        +string employee
        +datetime from_time
        +datetime to_time
        +float time_in_mins
        +float completed_qty
    }
    class JobCardItem {
        +string item_code
        +float required_qty
        +float transferred_qty
        +float consumed_qty
    }
    class JobCardOperation {
        +string sub_operation
        +string status
        +float completed_qty
    }
    class JobCardScheduledTime {
        +datetime from_time
        +datetime to_time
        +float time_in_mins
    }
    class JobCardSecondaryItem {
        +string item_code
        +string secondary_item_type
        +float stock_qty
    }
    class Workstation {
        +string workstation_name
        +string status
        +float hour_rate
        +int production_capacity
        +string plant_floor
        +validate()
        +start_job()
        +complete_job()
    }
    class WorkstationType {
        +string workstation_type
        +float hour_rate
    }
    class PlantFloor {
        +string floor_name
        +string warehouse
        +string company
        +validate()
        +make_stock_entry()
    }
    class DowntimeEntry {
        +string workstation
        +string operator
        +datetime from_time
        +datetime to_time
        +string stop_reason
    }

    WorkOrder --> BOM : bom_no
    WorkOrder *-- WorkOrderItem : required_items
    WorkOrder *-- WorkOrderOperation : operations
    WorkOrder *-- WorkOrderAdditionalItem : non_stock_items
    WorkOrder *-- WorkOrderAdditionalItem : secondary_items
    WorkOrderOperation --> Workstation : workstation
    WorkOrderOperation --> WorkstationType : workstation_type
    JobCard --> WorkOrder : work_order
    JobCard --> BOM : bom_no
    JobCard --> BOM : semi_fg_bom
    JobCard --> JobCard : for_job_card
    JobCard --> Workstation : workstation
    JobCard --> WorkstationType : workstation_type
    JobCard *-- JobCardTimeLog : time_logs
    JobCard *-- JobCardItem : items
    JobCard *-- JobCardOperation : sub_operations
    JobCard *-- JobCardScheduledTime : scheduled_time_logs
    JobCard *-- JobCardSecondaryItem : secondary_items
    Workstation --> WorkstationType : workstation_type
    Workstation --> PlantFloor : plant_floor
    DowntimeEntry --> Workstation : workstation
```

## Sequence diagram

### Submit BOM

Khi lưu, BOM kiểm tra và tính giá qua `BOMCostingService`, trải phẳng vật tư qua `BOMExplodedItemsService`. Khi submit, BOM quyết định BOM mặc định và ghi lại vào Item.

```mermaid
sequenceDiagram
    actor User
    participant B as BOM
    participant CS as BOMCostingService
    participant ES as BOMExplodedItemsService
    participant I as Item
    participant BC as BOM Creator
    User->>B: save
    B->>B: validate() rồi _validate_setup()
    B->>B: _validate_materials_and_cost()
    B->>CS: calculate_cost()
    CS->>CS: calculate_op_cost(), calculate_rm_cost(), calculate_secondary_items_costs()
    B->>ES: update_exploded_items(save=False)
    B->>CS: update_cost(update_parent=False)
    B->>B: _validate_uoms_and_goods()
    B->>B: on_update() rồi check_recursion()
    User->>B: submit
    B->>B: on_submit() rồi manage_default_bom()
    alt is_default và is_active
        B->>I: _set_as_default_bom() đặt default_bom
    else chưa có BOM mặc định đã submit
        B->>I: đặt is_default và default_bom
    else trường hợp còn lại
        B->>I: _unset_default_bom()
    end
    opt có bom_creator
        B->>BC: update_bom_creator_status() rồi set_status(save=True)
    end
```

Nguồn: [bom.py:298](../../apps/erpnext/erpnext/manufacturing/doctype/bom/bom.py#L298), [bom.py:720](../../apps/erpnext/erpnext/manufacturing/doctype/bom/bom.py#L720), [costing.py:147](../../apps/erpnext/erpnext/manufacturing/doctype/bom/services/costing.py#L147)

### Cập nhật giá một BOM

`update_cost` chạy đồng bộ, tính lại giá và đi ngược lên các BOM cha đã submit khi `total_cost` thay đổi.

```mermaid
sequenceDiagram
    actor User
    participant B as BOM
    participant CS as BOMCostingService
    participant PB as BOM cha
    User->>B: update_cost()
    B->>CS: update_cost(update_parent, from_child_bom, update_hour_rate, save)
    CS->>B: set_plc_conversion_rate()
    CS->>CS: calculate_cost(save_updates, update_hour_rate)
    CS->>CS: calculate_exploded_cost()
    CS->>B: db_update()
    opt total_cost đổi và update_parent
        CS->>CS: _update_parent_boms()
        loop mỗi BOM cha có BOM Item docstatus 1
            CS->>PB: update_cost(from_child_bom=True)
        end
    end
    CS-->>User: msgprint nếu không phải from_child_bom
```

Nguồn: [costing.py:77](../../apps/erpnext/erpnext/manufacturing/doctype/bom/services/costing.py#L77), [bom.py:1264](../../apps/erpnext/erpnext/manufacturing/doctype/bom/bom.py#L1264)

### BOM Update Tool: Replace BOM

Công cụ tạo và submit một BOM Update Log. Hook `on_submit` đẩy job nền, job này thay `bom_no` trên BOM Item và BOM Operation rồi tính lại mọi BOM tổ tiên, con trước cha.

```mermaid
sequenceDiagram
    actor User
    participant BUT as bom_update_tool
    participant Log as BOMUpdateLog
    participant Q as Queue
    participant U as bom_updation_utils
    participant B as BOM
    User->>BUT: enqueue_replace_bom(boms)
    BUT->>U: get_ancestor_boms() để kiểm tra quyền write
    BUT->>Log: create_bom_update_log(boms) rồi submit()
    Log->>Log: validate_boms_are_specified(), validate_same_bom()
    Log->>Log: validate_bom_items(), validate_not_a_semi_finished_goods_operation_bom()
    Log->>Q: on_submit() rồi frappe.enqueue(run_replace_bom_job)
    Q->>Log: run_replace_bom_job(doc, boms) đặt In Progress
    Log->>U: replace_bom(boms, log_name)
    U->>U: update_new_bom_in_bom_items(current_bom, new_bom)
    U->>U: sort_children_first(get_ancestor_boms(new_bom))
    loop mỗi BOM tổ tiên
        U->>B: update_exploded_items()
        U->>B: calculate_cost(save_updates=True)
        U->>B: db_update(), save_version()
    end
    alt thành công
        Log->>Log: db_set status Completed
    else có lỗi
        Log->>U: handle_exception(doc)
    end
```

Nguồn: [bom_update_tool.py:35](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_tool/bom_update_tool.py#L35), [bom_update_log.py:167](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_log/bom_update_log.py#L167), [bom_updation_utils.py:17](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_log/bom_updation_utils.py#L17)

### BOM Update Tool: Update Cost

Cập nhật giá toàn bộ BOM theo từng cấp, từ BOM lá trở lên. Mỗi cấp chia batch 7.000 BOM vào queue `long`. Cron `0/15 * * * *` chuyển sang cấp kế tiếp khi mọi batch của cấp hiện tại xong.

```mermaid
sequenceDiagram
    actor User
    participant Sch as Scheduler
    participant BUT as bom_update_tool
    participant Log as BOMUpdateLog
    participant Q as Queue long
    participant U as bom_updation_utils
    participant B as BOM
    alt thủ công
        User->>BUT: enqueue_update_cost()
    else daily_maintenance, bật update_bom_costs_automatically
        Sch->>BUT: auto_update_latest_price_in_all_boms()
    end
    BUT->>Log: create_bom_update_log(update_type=Update Cost) rồi submit()
    Log->>Log: validate_bom_cost_update_in_progress()
    Log->>Q: on_submit() rồi frappe.enqueue(process_boms_cost_level_wise)
    Q->>U: get_leaf_boms()
    Q->>Log: queue_bom_cost_jobs(current_boms, update_doc, level)
    loop mỗi batch
        Log->>Q: append bom_batches rồi enqueue update_cost_in_level
        Q->>U: update_cost_in_level(doc, bom_list, batch_name)
        U->>B: update_cost_in_boms() rồi calculate_cost(), db_update()
    end
    Sch->>Log: resume_bom_cost_update_jobs()
    opt không còn batch Pending ở cấp hiện tại
        Log->>U: get_next_higher_level_boms(current_boms, processed_boms)
        alt còn BOM cha
            Log->>Q: process_boms_cost_level_wise(update_doc, parent_boms)
        else hết
            Log->>Log: status Completed, xóa BOM Update Batch
        end
    end
```

Nguồn: [bom_update_tool.py:66](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_tool/bom_update_tool.py#L66), [bom_update_log.py:191](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_log/bom_update_log.py#L191), [bom_update_log.py:257](../../apps/erpnext/erpnext/manufacturing/doctype/bom_update_log/bom_update_log.py#L257)

### BOM Creator: tạo BOM từ thiết kế

BOM Creator đã submit đẩy job vào queue `short`. Plan chọn theo `track_semi_finished_goods`, rồi tạo và submit từng BOM theo thứ tự node.

```mermaid
sequenceDiagram
    actor User
    participant BC as BOMCreator
    participant Q as Queue short
    participant Plan as OperationPlan hoặc PartTreePlan
    participant B as BOM
    User->>BC: enqueue_create_boms()
    BC->>BC: validate_can_create_boms()
    BC->>Plan: get_bom_plan() rồi validate_can_make_boms()
    BC->>BC: db_set status In Progress
    BC->>Q: frappe.enqueue_doc(create_boms)
    Q->>BC: create_boms()
    BC->>Plan: make_boms()
    Plan->>Plan: get_existing_boms(), get_bom_order()
    loop mỗi node chưa có BOM
        Plan->>B: make_bom(node_id, boms)
        B->>B: insert(), submit()
    end
    alt thành công
        BC->>BC: set_status(save=True)
    else có lỗi
        BC->>BC: rollback, status Failed, ghi error_log
    end
```

Nguồn: [bom_creator.py:438](../../apps/erpnext/erpnext/manufacturing/doctype/bom_creator/bom_creator.py#L438), [bom_creator.py:470](../../apps/erpnext/erpnext/manufacturing/doctype/bom_creator/bom_creator.py#L470), [bom_plan.py:42](../../apps/erpnext/erpnext/manufacturing/doctype/bom_creator/bom_plan.py#L42)

### Lập và submit Production Plan

Người dùng lấy Sales Order hoặc Material Request, sinh dòng thành phẩm, bán thành phẩm và nguyên vật liệu. Khi submit, kế hoạch cập nhật Bin, Sales Order Item và có thể giữ chỗ tồn kho.

```mermaid
sequenceDiagram
    actor User
    participant PP as ProductionPlan
    participant SOS as SalesOrderSourcingService
    participant SAS as SubAssemblyService
    participant MR as material_request service
    participant Bin as Bin
    participant RS as ProductionPlanStockReservation
    User->>PP: get_open_sales_orders()
    PP->>SOS: get_open_sales_orders() rồi add_so_in_table()
    User->>PP: get_items()
    alt get_items_from là Sales Order
        PP->>SOS: get_so_items()
    else Material Request
        PP->>SOS: get_mr_items()
    end
    User->>PP: get_sub_assembly_items(manufacturing_type)
    PP->>SAS: _collect_row_sub_assembly_items(), set_default_supplier_for_subcontracting_order()
    User->>MR: get_items_for_material_requests(doc, warehouses)
    MR-->>User: danh sách mr_items
    User->>PP: submit
    PP->>PP: before_submit() rồi validate_sales_order_planned_qty()
    PP->>Bin: on_submit() rồi update_bin_qty()
    PP->>PP: update_sales_order(), add_reference_to_raw_materials()
    opt bật reserve_stock
        PP->>RS: update_stock_reservation() rồi reserve_stock_for_production_plan()
        RS->>RS: reserve() rồi make_stock_reservation_entries()
    end
```

Nguồn: [production_plan.py:372](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/production_plan.py#L372), [sales_order_planning.py:121](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/sales_order_planning.py#L121), [sub_assembly.py:19](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/sub_assembly.py#L19), [material_request.py:168](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/material_request.py#L168)

### Production Plan tạo Work Order và Purchase Order gia công

Từ kế hoạch đã có, `make_work_order` tạo Work Order nháp cho thành phẩm và bán thành phẩm tự làm, gom dòng `Subcontract` thành Purchase Order theo nhà cung cấp.

```mermaid
sequenceDiagram
    actor User
    participant PP as ProductionPlan
    participant WS as WorkOrderCreationService
    participant Qty as ProductionPlanWorkOrderQuantities
    participant WO as WorkOrder
    participant PO as Purchase Order
    User->>PP: make_work_order()
    PP->>PP: validate_plan_is_open()
    PP->>WS: make_work_order()
    WS->>WS: make_work_order_for_finished_goods()
    WS->>Qty: get_pending_quantities(doc)
    WS->>WO: create_work_order(item) rồi set_work_order_operations(), set_required_items(), insert()
    WS->>WS: make_work_order_for_subassembly_items()
    loop mỗi sub_assembly_items
        alt type_of_manufacturing là Subcontract
            WS->>WS: gom vào subcontracted_po theo supplier
        else Material Request
            WS->>WS: bỏ qua
        else In House
            WS->>WO: create_work_order(work_order_data)
        end
    end
    WS->>WS: make_subcontracted_purchase_order()
    WS->>PO: _create_subcontract_po() rồi set_service_items_for_finished_goods(), insert()
    WS-->>User: show_list_created_message()
```

Nguồn: [work_order_planning.py:96](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/work_order_planning.py#L96), [work_order_quantities.py:84](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/work_order_quantities.py#L84)

### Production Plan tạo Material Request

`make_material_request` gom `mr_items` theo Sales Order và loại Material Request, trừ phần đã yêu cầu và phần đang nháp.

```mermaid
sequenceDiagram
    actor User
    participant PP as ProductionPlan
    participant MS as MaterialRequestService
    participant MRq as Material Request
    User->>PP: make_material_request()
    PP->>PP: load_from_db(), check_permission(), validate_plan_is_open()
    PP->>MS: make_material_request()
    MS->>MS: validate_mr_subcontracted()
    MS->>MS: get_draft_requested_qty()
    loop mỗi mr_items còn qty_to_request lớn hơn 0
        MS->>MS: _add_item_to_material_request()
        MS->>MRq: _new_material_request(type) nếu khóa chưa có
        MS->>MRq: append items theo _material_request_item()
    end
    MS->>MS: _submit_material_requests()
    loop mỗi Material Request
        MS->>MRq: set_missing_values(), save()
        opt submit_material_request
            MS->>MRq: submit()
        end
    end
```

Nguồn: [production_plan.py:627](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/production_plan.py#L627), [material_request.py:58](../../apps/erpnext/erpnext/manufacturing/doctype/production_plan/services/material_request.py#L58)

### Xếp lịch Production Plan

`plan_adapter` dựng đồ thị công việc từ kế hoạch và chạy `SchedulingEngine`. `get_schedule_preview` chỉ trả đề xuất, `apply_schedule` mới ghi Production Plan Schedule. Job Card sau đó dùng các block này qua `get_plan_schedule_blocks`.

```mermaid
sequenceDiagram
    actor User
    participant PA as plan_adapter
    participant PP as ProductionPlan
    participant L as loaders
    participant E as SchedulingEngine
    participant PPS as Production Plan Schedule
    User->>PA: apply_schedule(production_plan, start_date, use_item_dates, item_dates)
    PA->>PP: check_permission(write)
    PA->>PA: validate_plan_for_scheduling(plan)
    PA->>PA: run_engine() rồi build_plan_tasks(plan)
    PA->>L: get_workstation_resources()
    PA->>L: get_booked_load(resources, start_date, exclude_plan)
    PA->>E: schedule(tasks, anchor=start_date)
    E->>E: schedule_forward(tasks, anchor)
    E-->>PA: ScheduleResult
    PA->>PA: build_proposal(), validate_complete_proposal()
    PA->>PPS: replace_schedule_entries() xóa cũ rồi insert
    PA->>PP: update_plan_row_dates()
    PA->>PP: notify_update()
```

Nguồn: [plan_adapter.py:36](../../apps/erpnext/erpnext/manufacturing/scheduling/plan_adapter.py#L36), [plan_adapter.py:101](../../apps/erpnext/erpnext/manufacturing/scheduling/plan_adapter.py#L101), [engine.py:40](../../apps/erpnext/erpnext/manufacturing/scheduling/engine.py#L40)

### Submit Work Order

Khi submit, Work Order kiểm tra hạn mức theo kế hoạch, cập nhật Bin và Sales Order, sinh Job Card cho từng công đoạn và xử lý giữ chỗ tồn kho. Work Order chưa ghi sổ kho ở bước này.

```mermaid
sequenceDiagram
    actor User
    participant WO as WorkOrder
    participant Qty as ProductionPlanWorkOrderQuantities
    participant Bin as Bin
    participant OS as OperationsService
    participant JC as JobCard
    participant RS as WorkOrderStockReservation
    participant SR as StockReservation
    User->>WO: submit
    WO->>Qty: before_submit() rồi validate_work_order(self)
    WO->>WO: create_serial_no_batch_no()
    WO->>WO: on_submit(), update_work_order_qty_in_so()
    WO->>Bin: update_ordered_qty(), update_reserved_qty_for_production(), update_planned_qty()
    WO->>OS: create_job_card_from_wo() rồi create_job_card()
    loop mỗi operations và mỗi batch
        OS->>OS: prepare_data_for_job_card() rồi get_plan_schedule_blocks(row)
        OS->>JC: create_job_card(work_order, row, auto_create=True)
        alt có schedule_blocks
            JC->>JC: _apply_schedule_blocks()
        else bật capacity planning
            JC->>JC: schedule_time_logs(row)
        end
        JC->>JC: insert()
    end
    WO->>WO: update_subcontracting_inward_order_received_items()
    opt reserve_stock
        WO->>RS: update_stock_reservation()
        RS->>SR: reserve_stock_for_work_order() rồi _reserve_or_transfer()
    end
```

Nguồn: [work_order.py:675](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/work_order.py#L675), [operations.py:116](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/services/operations.py#L116), [mapper.py:475](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/mapper.py#L475), [reservation.py:582](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/services/reservation.py#L582)

### Chuyển vật tư và nhập thành phẩm

Đây là nơi Work Order đi vào sổ kho và sổ cái. `make_stock_entry` tạo Stock Entry, class theo `purpose` cập nhật Work Order, rồi `StockEntry` ghi Stock Ledger Entry và GL Entry.

```mermaid
sequenceDiagram
    actor User
    participant WOM as work_order.mapper
    participant SE as StockEntry
    participant MS as ManufactureStockEntry
    participant WO as WorkOrder
    participant PP as ProductionPlan
    participant SLE as Stock Ledger Entry
    participant GL as GL Entry
    User->>WOM: make_stock_entry(work_order_id, purpose, qty)
    WOM->>SE: _new_manufacture_stock_entry(), get_items()
    User->>SE: submit Stock Entry purpose Manufacture
    SE->>MS: on_submit() rồi update_job_card_and_work_order()
    MS->>WO: update_work_order_qty()
    WO->>WO: set_process_loss_qty(), _update_qty_for_purpose()
    opt có production_plan
        WO->>PP: update_production_plan_status() rồi update_produced_pending_qty()
    end
    MS->>WO: update_status() rồi update_required_items()
    MS->>WO: update_planned_qty()
    SE->>SE: update_stock_reservation_entries()
    SE->>SLE: update_stock_ledger() rồi make_sl_entries()
    SE->>SE: make_stock_reserve_for_wip_and_fg()
    SE->>GL: make_gl_entries() rồi StockEntryGLComposer.compose()
    SE->>SE: repost_future_sle_and_gle()
    SE->>SE: update_project_consumed_material_cost()
```

Nguồn: [mapper.py:232](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/mapper.py#L232), [stock_entry.py:415](../../apps/erpnext/erpnext/stock/doctype/stock_entry/stock_entry.py#L415), [manufacturing.py:1175](../../apps/erpnext/erpnext/stock/doctype/stock_entry/services/manufacturing.py#L1175), [status.py:197](../../apps/erpnext/erpnext/manufacturing/doctype/work_order/services/status.py#L197)

### Chấm công Job Card và cập nhật Work Order

Người vận hành bắt đầu qua `start_timer`, kết thúc qua `complete_job_card`, có thể gọi từ trang Shop Floor. Khi submit, Job Card đẩy số lượng và thời gian vào dòng Work Order Operation.

```mermaid
sequenceDiagram
    actor Op as Operator
    participant SF as shop_floor
    participant JC as JobCard
    participant WS as Workstation
    participant WO as WorkOrder
    Op->>JC: start_timer(start_time, employees)
    JC->>JC: validate_transfer_qty(), validate_not_already_started()
    JC->>JC: add_time_logs(from_time, employees)
    JC->>JC: validate() rồi set_status()
    JC->>WS: update_workstation_status() db_set status
    Op->>SF: complete_and_submit(job_card, qty, for_quantity, pending_qty, process_loss_qty, end_time)
    SF->>JC: _record_session() rồi complete_job_card(auto_submit=0)
    JC->>JC: validate_complete_job_card_qty(), set_for_quantity()
    JC->>JC: add_completion_time_logs() rồi add_time_logs()
    SF->>JC: submit()
    JC->>JC: on_submit() rồi validate_inspection(), validate_transfer_qty()
    JC->>JC: validate_job_card(), validate_later_operations()
    JC->>WO: update_work_order()
    alt is_corrective_job_card
        JC->>WO: update_corrective_in_work_order() rồi calculate_operating_cost(), save()
    else có operation_id
        JC->>WO: update_work_order_data() rồi update_operation_status()
        JC->>WO: calculate_operating_cost(), set_actual_dates(), save()
    end
    JC->>WO: set_transferred_qty() rồi set_transferred_qty_in_work_order()
```

Nguồn: [job_card.py:2041](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/job_card.py#L2041), [job_card.py:2076](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/job_card.py#L2076), [job_card.py:1211](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/job_card.py#L1211), [shop_floor.py:141](../../apps/erpnext/erpnext/manufacturing/page/shop_floor/shop_floor.py#L141)

### Job Card bán thành phẩm và gia công ngoài

Với Work Order `track_semi_finished_goods`, Job Card có `finished_good` tự sinh Stock Entry `Manufacture`, hoặc thuê ngoài qua Purchase Order khi `is_subcontracted`. Cả hai đường đều quay lại `set_manufactured_qty`.

```mermaid
sequenceDiagram
    actor User
    participant JC as JobCard
    participant SE as StockEntry
    participant MS as ManufactureStockEntry
    participant PO as Purchase Order
    participant SCR as Subcontracting Receipt
    participant WO as WorkOrder
    alt tự sản xuất
        User->>JC: make_stock_entry_for_semi_fg_item(auto_submit)
        JC->>JC: build_manufacture_stock_entry()
        JC->>SE: populate_manufacture_stock_entry() rồi make_stock_entry()
        User->>SE: submit Stock Entry
        SE->>MS: on_submit() rồi _update_job_card_on_manufacture()
        MS->>JC: set_consumed_qty_in_job_card_item(), set_manufactured_qty(), update_work_order()
    else gia công ngoài
        User->>PO: make_subcontracting_po(source_name)
        PO-->>User: Purchase Order nháp có job_card
        User->>SCR: submit Subcontracting Receipt
        SCR->>JC: update_job_card() rồi set_manufactured_qty()
    end
    JC->>JC: get_manufactured_qty()
    JC->>WO: update_semi_finished_good_details()
    opt finished_good trùng production_item
        JC->>WO: db_set produced_qty rồi db_set status
    end
    JC->>JC: set_status(update_status=True)
```

Nguồn: [job_card.py:2172](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/job_card.py#L2172), [job_card.py:311](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/job_card.py#L311), [mapper.py:17](../../apps/erpnext/erpnext/manufacturing/doctype/job_card/mapper.py#L17)

### Từ Sales Forecast đến đơn hàng theo MRP

Sales Forecast sinh dòng nhu cầu và map sang Master Production Schedule. MPS lấy nhu cầu thực tế và lead time. Report MRP đọc MPS và tạo Purchase Order, Work Order qua `make_order`.

```mermaid
sequenceDiagram
    actor User
    participant SF as SalesForecast
    participant MPS as MasterProductionSchedule
    participant MRP as material_requirements_planning_report
    participant PO as Purchase Order
    participant WO as WorkOrder
    User->>SF: generate_demand() rồi generate_manual_demand()
    User->>SF: submit
    User->>SF: create_mps(source_name)
    SF->>MPS: get_mapped_doc đặt sales_forecast, from_date
    User->>MPS: save
    MPS->>MPS: validate(), validate_sales_forecast_not_used()
    MPS->>SF: on_update() rồi update_sales_forecast_status()
    User->>MPS: get_actual_demand()
    MPS->>MPS: get_demand_data() rồi get_sales_orders_data(), get_material_requests_data()
    MPS->>MPS: get_item_wise_mps_data(), update_item_details()
    MPS->>MPS: get_cumulative_lead_time(), add_mps_data()
    User->>MRP: execute(filters với mps)
    MRP->>MPS: đọc sales_orders và sales_forecast theo filter mps
    User->>MRP: make_order(selected_rows, company, warehouse, mps)
    MRP->>PO: make_purchase_orders()
    MRP->>WO: make_work_orders() đặt mps rồi insert()
```

Nguồn: [sales_forecast.py:151](../../apps/erpnext/erpnext/manufacturing/doctype/sales_forecast/sales_forecast.py#L151), [master_production_schedule.py:50](../../apps/erpnext/erpnext/manufacturing/doctype/master_production_schedule/master_production_schedule.py#L50), [material_requirements_planning_report.py:1411](../../apps/erpnext/erpnext/manufacturing/report/material_requirements_planning_report/material_requirements_planning_report.py#L1411)

### Plant Floor

Plant Floor chỉ là lớp xem và tiện ích. Trang hiển thị máy theo `plant_floor` và tồn kho kho xưởng, `make_stock_entry` trả về Stock Entry chưa lưu. Trạng thái Workstation do Job Card đổi.

```mermaid
sequenceDiagram
    actor User
    participant VP as visual_plant.js
    participant W as workstation.py
    participant PF as PlantFloor
    participant Bin as Bin
    participant SE as StockEntry
    User->>VP: mở Plant Floor
    VP->>W: get_workstations(plant_floor, ...)
    W->>W: frappe.get_list(Workstation) rồi get_color_map()
    W-->>VP: danh sách máy và màu trạng thái
    User->>PF: get_stock_summary(warehouse, start, item_code, item_group)
    PF->>Bin: get_stock_details(warehouse)
    Bin-->>PF: tồn và số giữ chỗ
    User->>PF: make_stock_entry(kwargs)
    PF->>PF: get_item_details(kwargs)
    PF->>SE: new_doc rồi set_missing_values()
    SE-->>User: Stock Entry chưa lưu
```

Nguồn: [plant_floor.py:46](../../apps/erpnext/erpnext/manufacturing/doctype/plant_floor/plant_floor.py#L46), [plant_floor.py:90](../../apps/erpnext/erpnext/manufacturing/doctype/plant_floor/plant_floor.py#L90), [workstation.py:411](../../apps/erpnext/erpnext/manufacturing/doctype/workstation/workstation.py#L411)

## Giới hạn

- **Master Production Schedule:** `on_submit` gọi `enqueue_mrp_creation`, và hàm này enqueue method `make_mrp`. Không tìm thấy định nghĩa `make_mrp` trong `erpnext/`. Doctype JSON cũng không có `is_submittable`, nên hook này có vẻ không chạy, vì vậy không đưa vào sơ đồ.
- **Blanket Order, Manufacturing Settings:** không vẽ. Blanket Order là thỏa thuận khung, liên quan chính đến selling và buying. Manufacturing Settings chỉ chứa cấu hình.
- **Doctype bảng con hoặc danh mục không có trong class diagram:** BOM Creator Material, BOM Website Item, BOM Website Operation, Workstation Cost, Workstation Operating Component, Workstation Operating Component Account, Workstation Working Hour.
- **Report và dashboard:** chỉ đọc `make_order`, `make_purchase_orders`, `make_work_orders` của report MRP. Thân `execute` và các truy vấn theo filter `mps` chỉ đọc lướt, nên bước đọc MPS trong sơ đồ có thể chưa đủ. Các report khác không đọc.
- **Trang frontend:** không đọc `shop_floor.js`, nên chưa xác nhận nút nào gọi hàm nào. `page/production_plan_visualizer`, `page/bom_comparison_tool` không đọc. `visual_plant.js` chỉ đọc đoạn gọi `get_workstations`.
- **Đọc lướt:** `work_order/services/required_items.py`, `reservation.py`, `production_plan/services/bom_explosion.py`, `sub_assembly_queries.py`, `planning_queries.py`, `scheduling/engine.py`, `loaders.py`, phần lớn `plan_adapter.py`, `bom_creator/operation_plan.py`, `part_tree_plan.py`, và phần tính toán của `job_card.py`. `stock/doctype/stock_entry/services/material_transfer.py` chỉ đọc phần `on_submit`.
- **Luồng chuyển vật tư:** sơ đồ vẽ nhánh `Manufacture`. Nhánh `Material Transfer for Manufacture` đi qua `MaterialTransferForManufactureStockEntry.update_job_card_and_work_order`, thêm `add_additional_items`, không gọi `update_planned_qty`.
- **Hủy và đóng:** `on_cancel`, `on_close_or_cancel`, `close_work_order`, `stop_unstop` không vẽ riêng.
- **Comment lệch code:** `resume_bom_cost_update_jobs` ghi "every 5 minutes" nhưng `hooks.py` dùng cron `0/15 * * * *`. `queue_bom_cost_jobs` ghi 20k nhưng `batch_size` là 7.000. Tài liệu theo code.
- **Rút gọn service:** `WorkOrder.update_status` và `update_work_order_qty` chỉ gọi tiếp `StatusService`. Sơ đồ ghi theo class doctype để dễ theo dõi.
