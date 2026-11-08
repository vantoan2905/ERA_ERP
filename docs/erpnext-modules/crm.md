# Module CRM

Module `crm` quản lý giai đoạn trước bán hàng: Lead, Opportunity, Prospect, cùng Contract, Appointment và Email Campaign. Module đẩy luồng sang `selling` (Customer, Quotation) và `buying` (Request for Quotation, Supplier Quotation từ Opportunity), dùng `Contact`, `Address`, `Communication`, `Event` của Frappe và có API đồng bộ với app Frappe CRM.

## Phạm vi

Đọc được 28 doctype trong `crm/doctype/`. Mục "Sơ đồ" chỉ tới tiêu đề trong file này.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Lead | Lead, `lead/lead.py`, `lead/mapper.py` | Class: Lead, Opportunity, Prospect. Sequence: Lưu Lead, Lead sang Customer, Lead sang Prospect |
| Opportunity | Opportunity, Opportunity Item, Competitor Detail, `opportunity/opportunity.py`, `opportunity/mapper.py` | Class: Lead, Opportunity, Prospect. Sequence: Lưu Opportunity, Opportunity sang Quotation, Declare Lost, Email sang Opportunity |
| Prospect | Prospect, Prospect Lead, Prospect Opportunity, `prospect/prospect.py` | Class: Lead, Opportunity, Prospect. Sequence: Lead sang Prospect |
| Contract | Contract, Contract Template, Contract Fulfilment Checklist | Class: Contract. Sequence: Vòng đời Contract |
| Appointment | Appointment, Appointment Booking Settings, Appointment Booking Slots, `www/book_appointment/` | Class: Appointment và Email Campaign. Sequence: Đặt lịch qua portal |
| Email Campaign | Campaign, Campaign Email Schedule, Email Campaign | Class: Appointment và Email Campaign. Sequence: Gửi Email Campaign |
| Tích hợp Frappe CRM | `frappe_crm_api.py`, CRM Settings | Sequence: Đồng bộ từ Frappe CRM |

## Class diagram

Class ngoài module (ví dụ `Customer`, `SellingController`) chỉ để đích của quan hệ nên để trống. Controller cha chỉ ghi method.

### Lead, Opportunity, Prospect

`CRMNote` trong sơ đồ là class cơ sở ở `crm/utils.py`. Doctype con `CRM Note` cũng có Python class cùng tên ở `crm_note/crm_note.py`, đó là bảng `notes` của ba doctype này. `Opportunity.party_name` là Dynamic Link theo `opportunity_from`, sơ đồ vẽ hai trường hợp Lead và Prospect.

```mermaid
classDiagram
    class CRMNote {
        +add_note()
        +edit_note()
        +delete_note()
    }
    class SellingController
    class TransactionBase
    class Lead {
        +string lead_name
        +string company_name
        +string email_id
        +string status
        +string customer
        +string lead_owner
        +bool disabled
        +validate()
        +before_insert()
        +after_insert()
        +on_update()
        +set_status()
        +update_prospect()
        +create_prospect_and_contact()
        +create_contact()
        +create_prospect()
    }
    class Opportunity {
        +string opportunity_from
        +string party_name
        +string status
        +string sales_stage
        +float opportunity_amount
        +date expected_closing
        +date lost_on
        +validate()
        +after_insert()
        +on_update()
        +set_status()
        +update_prospect()
        +update_lead_status()
        +make_new_lead_if_required()
        +declare_enquiry_lost()
        +has_active_quotation()
    }
    class OpportunityItem {
        +string item_code
        +float qty
        +float rate
        +float amount
    }
    class OpportunityLostReasonDetail {
        +string lost_reason
    }
    class CompetitorDetail {
        +string competitor
    }
    class Prospect {
        +string company_name
        +string customer_group
        +string territory
        +string prospect_owner
        +validate()
        +validate_leads()
        +on_update()
        +after_insert()
        +link_with_lead_contact_and_address()
    }
    class ProspectLead {
        +string lead
        +string lead_name
        +string status
        +string email
    }
    class ProspectOpportunity {
        +string opportunity
        +float amount
        +string stage
        +date expected_closing
    }
    class Customer
    class SalesStage
    CRMNote <|-- Lead
    SellingController <|-- Lead
    CRMNote <|-- Opportunity
    TransactionBase <|-- Opportunity
    CRMNote <|-- Prospect
    Opportunity *-- OpportunityItem : items
    Opportunity *-- OpportunityLostReasonDetail : lost_reasons
    Opportunity *-- CompetitorDetail : competitors
    Prospect *-- ProspectLead : leads
    Prospect *-- ProspectOpportunity : opportunities
    ProspectLead --> Lead : lead
    ProspectOpportunity --> Opportunity : opportunity
    Opportunity --> Lead : party_name
    Opportunity --> Prospect : party_name
    Opportunity --> SalesStage : sales_stage
    Lead --> Customer : customer
```

### Contract

`Contract.party_name` là Dynamic Link theo `party_type` (Customer, Supplier, Employee), nên không vẽ quan hệ tới party.

```mermaid
classDiagram
    class Contract {
        +string party_type
        +string party_name
        +bool is_signed
        +string status
        +string fulfilment_status
        +date start_date
        +date end_date
        +string document_type
        +validate()
        +before_submit()
        +on_cancel()
        +before_update_after_submit()
        +update_contract_status()
        +update_fulfilment_status()
        +validate_signature_unchanged()
        +validate_document_party()
    }
    class ContractFulfilmentChecklist {
        +bool fulfilled
        +string requirement
        +string amended_from
    }
    class ContractTemplate {
        +string title
        +string contract_terms
        +bool requires_fulfilment
    }
    class ContractTemplateFulfilmentTerms {
        +string requirement
    }
    Contract *-- ContractFulfilmentChecklist : fulfilment_terms
    Contract --> ContractTemplate : contract_template
    ContractTemplate *-- ContractTemplateFulfilmentTerms : fulfilment_terms
```

### Appointment và Email Campaign

`Appointment.party` và `EmailCampaign.recipient` là Dynamic Link. Sơ đồ vẽ `party` tới Lead và `recipient` tới Lead làm ví dụ.

```mermaid
classDiagram
    class Appointment {
        +datetime scheduled_time
        +string status
        +string customer_email
        +string appointment_with
        +string party
        +string calendar_event
        +bool created_through_portal
        +bool email_verified
        +validate()
        +before_insert()
        +after_insert()
        +on_update()
        +validate_available_time_slot()
        +link_customer_lead()
        +auto_assign()
        +create_calendar_event()
    }
    class AppointmentBookingSettings {
        +int number_of_agents
        +int appointment_duration
        +bool enable_scheduling
        +string holiday_list
    }
    class AppointmentBookingSlots {
        +string day_of_week
    }
    class Campaign {
        +string campaign_name
        +string naming_series
        +string description
    }
    class CampaignEmailSchedule {
        +string email_template
        +int send_after_days
    }
    class EmailCampaign {
        +string campaign_name
        +string email_campaign_for
        +string recipient
        +string sender
        +date start_date
        +date end_date
        +string status
        +validate()
        +get_end_date()
        +refresh_end_date()
        +validate_email_campaign_already_exists()
        +update_status()
    }
    class Lead
    AppointmentBookingSettings *-- AppointmentBookingSlots : availability_of_slots
    Appointment --> Lead : party
    Campaign *-- CampaignEmailSchedule : campaign_schedules
    EmailCampaign --> Campaign : campaign_name
    EmailCampaign --> Lead : recipient
```

## Sequence diagram

### Lưu Lead

Lead có thể tự tạo Contact theo CRM Settings và luôn đồng bộ dòng tương ứng trên Prospect. `Lead.validate` không gọi `super().validate()`, nên không chạy validate của `SellingController`.

```mermaid
sequenceDiagram
    actor User
    participant L as Lead
    participant CS as CRM Settings
    participant Ct as Contact
    participant PL as Prospect Lead
    User->>L: insert()
    L->>CS: before_insert() đọc auto_creation_of_contact
    opt auto_creation_of_contact
        L->>Ct: create_contact() hoặc lấy Contact của customer có sẵn
    end
    L->>L: validate() gọi set_full_name(), set_lead_name(), set_title(), set_status()
    L->>CS: check_email_id_is_unique() đọc allow_lead_duplication_based_on_emails
    L->>L: validate_email_id()
    L->>Ct: after_insert() gọi link_to_contact()
    L->>PL: on_update() gọi update_prospect()
```

Nguồn: [lead.py:109](../../apps/erpnext/erpnext/crm/doctype/lead/lead.py#L109), [lead.py:91](../../apps/erpnext/erpnext/crm/doctype/lead/lead.py#L91), [lead.py:214](../../apps/erpnext/erpnext/crm/doctype/lead/lead.py#L214)

### Lead sang Customer

Mapper tạo Customer nháp từ Lead; lúc Customer được insert, Lead mới chuyển sang Converted.

```mermaid
sequenceDiagram
    actor User
    participant M as lead/mapper.py
    participant L as Lead
    participant C as Customer
    participant QO as Quotation và Opportunity
    User->>M: make_customer(source_name, target_doc)
    M->>L: validate_lead_is_enabled() đọc disabled
    M->>C: _make_customer() gọi get_mapped_doc()
    M->>C: set_missing_values() đặt customer_type, customer_name, customer_group
    M->>C: get_default_address(), get_default_contact()
    M-->>User: Customer nháp
    User->>C: insert()
    C->>C: validate_lead_not_converted()
    C->>L: after_insert() gọi update_lead_status(), db_set status Converted
    C->>L: update_prospect()
    C->>QO: link_lead_records()
```

Nguồn: [mapper.py:16](../../apps/erpnext/erpnext/crm/doctype/lead/mapper.py#L16), [mapper.py:21](../../apps/erpnext/erpnext/crm/doctype/lead/mapper.py#L21), [customer.py:361](../../apps/erpnext/erpnext/selling/doctype/customer/customer.py#L361)

### Lead sang Prospect rồi Customer

Một Lead chỉ thuộc một Prospect. Prospect có thể sinh Opportunity hoặc Customer; khi Prospect có đúng một Lead chưa chuyển đổi, Customer nhận luôn `lead_name`.

```mermaid
sequenceDiagram
    actor User
    participant L as Lead
    participant P as Prospect
    participant CA as Contact và Address
    participant CU as crm/utils.py
    participant C as Customer
    User->>L: create_prospect_and_contact(data)
    L->>L: check_permission("write")
    opt data.create_contact
        L->>CA: create_contact(), link_to_contact()
    end
    opt data.create_prospect
        L->>P: create_prospect() gọi save()
        P->>P: validate_leads() chặn Lead trùng ở Prospect khác
        P->>CU: after_insert() gọi copy_comments, link_communications, link_open_events
        P->>CA: on_update() gọi link_with_lead_contact_and_address()
    end
    User->>P: make_customer(source_name, target_doc)
    P->>P: validate_not_converted()
    P->>C: get_mapped_doc() với set_missing_values
    P-->>User: Customer nháp
```

Nguồn: [lead.py:260](../../apps/erpnext/erpnext/crm/doctype/lead/lead.py#L260), [lead.py:303](../../apps/erpnext/erpnext/crm/doctype/lead/lead.py#L303), [prospect.py:121](../../apps/erpnext/erpnext/crm/doctype/prospect/prospect.py#L121)

### Lưu Opportunity

Opportunity tự tạo Lead từ `contact_email` khi chưa có party và giữ đồng bộ với Lead và Prospect.

```mermaid
sequenceDiagram
    actor User
    participant O as Opportunity
    participant L as Lead
    participant Q as Quotation
    participant P as Prospect
    participant CU as crm/utils.py
    User->>O: insert()
    O->>L: validate() gọi make_new_lead_if_required()
    O->>O: validate_opportunity_from(), validate_party(), validate_party_contact_and_address()
    O->>O: map_fields(), validate_qty()
    opt bản đã lưu và status đổi
        O->>Q: validate_status() gọi get_quotation_status()
    end
    O->>O: set_lost_on(), set_exchange_rate(), calculate_totals()
    opt opportunity_from là Lead
        O->>L: after_insert() gọi set_status(update=True)
        O->>CU: link_open_tasks(), link_open_events()
    end
    opt opportunity_from là Lead hoặc Prospect
        O->>CU: carry_forward_communication()
    end
    O->>P: on_update() gọi update_prospect(), remove_from_previous_prospect()
    opt status đổi
        O->>L: update_lead_status()
    end
```

Nguồn: [opportunity.py:133](../../apps/erpnext/erpnext/crm/doctype/opportunity/opportunity.py#L133), [opportunity.py:116](../../apps/erpnext/erpnext/crm/doctype/opportunity/opportunity.py#L116), [opportunity.py:275](../../apps/erpnext/erpnext/crm/doctype/opportunity/opportunity.py#L275)

### Opportunity sang Quotation

Mapper tạo Quotation nháp, liên kết về Opportunity qua `prevdoc_docname` trên dòng, hoặc qua `opportunity` trên header khi Opportunity không có dòng. Trạng thái Opportunity đổi khi Quotation submit.

```mermaid
sequenceDiagram
    actor User
    participant M as opportunity/mapper.py
    participant Op as Opportunity
    participant T as taxes service
    participant Q as Quotation
    User->>M: make_quotation(source_name, target_doc)
    M->>Q: get_mapped_doc() map opportunity_from sang quotation_to
    M->>Q: set_missing_values() đặt conversion_rate
    M->>T: _get_default_taxes_and_charges()
    M->>Q: run_method("set_missing_values"), run_method("calculate_taxes_and_totals")
    alt Opportunity không có items
        M->>Q: đặt quotation.opportunity
    else có items
        M->>Q: Quotation Item giữ prevdoc_docname
    end
    M-->>User: Quotation nháp
    User->>Q: submit()
    Q->>Op: on_submit() gọi update_opportunity("Quotation")
    Op->>Op: set_status() status_map dùng has_active_quotation
```

Nguồn: [mapper.py:16](../../apps/erpnext/erpnext/crm/doctype/opportunity/mapper.py#L16), [quotation.py:350](../../apps/erpnext/erpnext/selling/doctype/quotation/quotation.py#L350)

### Declare Lost cho Opportunity

Khi còn Quotation đang hoạt động thì không đánh dấu Lost được.

```mermaid
sequenceDiagram
    actor User
    participant O as Opportunity
    participant Q as Quotation
    participant L as Lead
    User->>O: declare_enquiry_lost(lost_reasons_list, competitors, detailed_reason)
    O->>Q: has_active_quotation() gọi get_linked_quotations()
    alt còn Quotation hoạt động
        O-->>User: throw Cannot declare as Lost
    else không còn
        O->>O: đặt status Lost, thay lost_reasons, competitors
        O->>O: save() gọi validate_status(), set_lost_on()
        O->>L: on_update() gọi update_lead_status()
    end
```

Nguồn: [opportunity.py:367](../../apps/erpnext/erpnext/crm/doctype/opportunity/opportunity.py#L367), [opportunity.py:190](../../apps/erpnext/erpnext/crm/doctype/opportunity/opportunity.py#L190)

### Email sang Opportunity

Từ một Communication, người dùng tạo Opportunity; nếu mail chưa gắn Lead thì tìm theo email hoặc số điện thoại, không có thì tạo Lead mới.

```mermaid
sequenceDiagram
    actor User
    participant OM as opportunity/mapper.py
    participant LM as lead/mapper.py
    participant Comm as Communication
    participant L as Lead
    participant O as Opportunity
    User->>OM: make_opportunity_from_communication(communication, company)
    OM->>Comm: has_permission(), get_doc()
    alt reference_doctype là Opportunity
        OM-->>User: trả reference_name
    else chưa có Opportunity
        opt reference_doctype khác Lead
            OM->>LM: make_lead_from_communication()
            LM->>L: tìm theo sender, phone_no hoặc insert() Lead mới
            LM->>Comm: link_communication_to_document()
        end
        OM->>O: insert() với opportunity_from Lead
        OM->>Comm: link_communication_to_document()
        OM-->>User: tên Opportunity
    end
```

Nguồn: [mapper.py:147](../../apps/erpnext/erpnext/crm/doctype/opportunity/mapper.py#L147), [mapper.py:121](../../apps/erpnext/erpnext/crm/doctype/lead/mapper.py#L121)

### Vòng đời Contract

Contract submit được và vẫn ký hoặc tích điều khoản sau submit; job daily tính lại status và đánh dấu Lapsed.

```mermaid
sequenceDiagram
    actor User
    participant Sch as Scheduler
    participant CF as contract.py
    participant Ct as Contract
    User->>Ct: insert()
    Ct->>Ct: validate() gọi set_missing_values(), validate_dates(), validate_signature()
    Ct->>Ct: validate_document_party() gọi get_document_party()
    Ct->>Ct: update_contract_status(), update_fulfilment_status()
    User->>Ct: submit()
    Ct->>Ct: before_submit() đặt signed_by_company
    User->>Ct: save() sau submit
    Ct->>Ct: before_update_after_submit() gọi validate_signature_unchanged(), validate_fulfilment_terms_unchanged()
    Ct->>Ct: update_contract_status(), update_fulfilment_status()
    Sch->>CF: update_status_for_contracts()
    loop mỗi Contract is_signed và docstatus 1
        CF->>CF: get_status(start_date, end_date)
        CF->>Ct: set_value status
    end
    CF->>Ct: set_lapsed_fulfilment_status()
```

Nguồn: [contract.py:53](../../apps/erpnext/erpnext/crm/doctype/contract/contract.py#L53), [contract.py:80](../../apps/erpnext/erpnext/crm/doctype/contract/contract.py#L80), [contract.py:263](../../apps/erpnext/erpnext/crm/doctype/contract/contract.py#L263)

### Đặt lịch qua portal

Guest đặt lịch tạo Appointment trạng thái Unverified; chỉ khi bấm link xác minh thì mới gắn party, phân công agent và tạo Event. Job `hourly_maintenance` xử lý các lịch hết hạn xác minh.

```mermaid
sequenceDiagram
    actor Guest
    participant Sch as Scheduler
    participant W as www/book_appointment
    participant A as Appointment
    participant ABS as Appointment Booking Settings
    participant L as Lead
    participant E as Event
    participant Mail as frappe.sendmail
    Guest->>W: create_appointment(date, time, tz, contact)
    W->>A: insert() với created_through_portal bằng 1
    A->>A: before_insert() đặt status Unverified
    A->>ABS: validate() gọi validate_schedule(), validate_available_time_slot()
    A->>Mail: after_insert() gọi send_confirmation_email()
    Guest->>W: get_context() với key trong link xác minh
    W->>A: verify_appointment() đặt email_verified, status Open, save()
    A->>ABS: validate_available_time_slot() gọi lock_booking_capacity()
    A->>L: on_update() gọi link_auto_assign_and_create_calendar_event(), link_customer_lead(), create_lead_and_link()
    A->>A: auto_assign() gọi get_free_agent(), assign_agent()
    A->>E: create_calendar_event()
    A->>Mail: send_appointment_confirmed_email()
    A->>E: update_event_and_assignments_status()
    Sch->>A: handle_expired_unverified_appointments() đóng hoặc xóa theo cấu hình
```

Nguồn: [index.py:114](../../apps/erpnext/erpnext/www/book_appointment/index.py#L114), [index.py:60](../../apps/erpnext/erpnext/www/book_appointment/verify/index.py#L60), [appointment.py:182](../../apps/erpnext/erpnext/crm/doctype/appointment/appointment.py#L182), [appointment.py:465](../../apps/erpnext/erpnext/crm/doctype/appointment/appointment.py#L465)

### Gửi Email Campaign

Job `daily_maintenance` gửi các bước Campaign rơi vào hôm nay. Khi người nhận hủy đăng ký, hook `Email Unsubscribe` cập nhật lại trạng thái.

```mermaid
sequenceDiagram
    participant Sch as Scheduler
    participant EF as email_campaign.py
    participant EC as Email Campaign
    participant Ca as Campaign
    participant Comm as Communication
    participant Mail as frappe.sendmail
    participant U as Email Unsubscribe
    participant EGM as Email Group Member
    Sch->>EF: send_email_to_leads_or_contacts()
    EF->>EC: set_email_campaign_status() gọi refresh_end_date(), update_status()
    loop mỗi Email Campaign đang chạy
        EF->>Ca: get_cached_doc()
        loop mỗi campaign_schedules
            opt scheduled_date là hôm nay và không is_step_sent
                EF->>EF: send_mail(entry, email_campaign)
                EF->>Comm: make() với send_email False
                EF->>Mail: sendmail với queue_separately và communication
            end
        end
    end
    U->>EF: unsubscribe_recipient()
    alt email_campaign_for là Email Group
        EF->>EGM: set_value unsubscribed
    else Lead hoặc Contact
        EF->>EC: set_value status Unsubscribed
    end
```

Nguồn: [email_campaign.py:132](../../apps/erpnext/erpnext/crm/doctype/email_campaign/email_campaign.py#L132), [email_campaign.py:190](../../apps/erpnext/erpnext/crm/doctype/email_campaign/email_campaign.py#L190), [email_campaign.py:272](../../apps/erpnext/erpnext/crm/doctype/email_campaign/email_campaign.py#L272)

### Đồng bộ từ Frappe CRM

App Frappe CRM gọi API để tạo Prospect hoặc Customer từ CRM Deal; lỗi tạo chứng từ được ghi log thay vì trả về lỗi cho caller.

```mermaid
sequenceDiagram
    actor CRM as Frappe CRM
    participant API as frappe_crm_api.py
    participant CS as CRM Settings
    participant P as Prospect
    participant C as Customer
    participant Ct as Contact và Address
    CRM->>API: create_prospect_against_crm_deal()
    API->>CS: validate_frappe_crm_sync()
    opt chưa có Prospect cùng company_name
        API->>P: insert()
    end
    API->>Ct: create_contacts(), create_address()
    CRM->>API: create_customer(customer_data)
    API->>CS: validate_frappe_crm_sync()
    opt chưa có Customer cùng customer_name
        API->>C: insert() với ignore_permissions theo is_crm_installed()
    end
    API->>Ct: create_contacts(), create_address() trong savepoint crm_customer_links
    API-->>CRM: customer_name
```

Nguồn: [frappe_crm_api.py:9](../../apps/erpnext/erpnext/crm/frappe_crm_api.py#L9), [frappe_crm_api.py:143](../../apps/erpnext/erpnext/crm/frappe_crm_api.py#L143)

## Giới hạn

- Không vẽ: Market Segment, Opportunity Type, Opportunity Lost Reason, Sales Stage, Competitor (danh mục, chỉ nêu qua quan hệ), CRM Settings (cấu hình), Frappe CRM Allowed User, Lost Reason Detail.
- `Availability Of Slots` có cấu trúc giống `Appointment Booking Slots`, nhưng field `availability_of_slots` của Appointment Booking Settings có `options` là `Appointment Booking Slots`. Grep trong erpnext không thấy nơi nào trỏ `options` tới doctype này, chưa xác nhận nó còn được dùng ngoài erpnext.
- Appointment tạo tay (không qua portal) không vẽ riêng: `before_insert` gọi `link_customer_lead`, `after_insert` gọi `auto_assign` và `create_calendar_event` khi đã có `party`, ngược lại gửi mail xác nhận.
- `opportunity/mapper.py` còn `make_request_for_quotation`, `make_supplier_quotation`, `make_customer` chưa vẽ; `lead/mapper.py` còn `make_opportunity`, `make_quotation`; `prospect.py` còn `make_opportunity`.
- `ContractPartyAccess` và hai hook `has_permission`, `get_permission_query_conditions` của Contract giới hạn quyền theo role và User Permission, không vẽ vì không phải luồng nghiệp vụ.
- Các hook khác chưa vẽ: `link_communications_with_prospect`, `update_modified_timestamp`, `link_events_with_prospect`, `update_lead_phone_numbers`, `auto_close_opportunity`, `open_leads_opportunities_based_on_todays_event`.
- Trong `make_quotation` của Opportunity, `field_map` có `"name": "enq_no"` nhưng `quotation.json` không có field `enq_no`, nên không vẽ. Chưa kiểm tra đó có phải field tùy chỉnh hay field cũ.
- Prospect không có field `crm_deal` trong `prospect.json` dù `create_prospect_against_crm_deal` gán `prospect.crm_deal`. Chưa xác nhận field này do app Frappe CRM thêm.
- `send_mail` trả `comm` sau khối `try`; nếu `make()` lỗi thì `comm` chưa được gán. Lỗi đó được khối `except` ở `send_email_to_leads_or_contacts` ghi log. Đây là nhận định từ đọc code, chưa chạy thử.
- Phần `www/book_appointment/index.py` chỉ đọc `create_appointment`; các hàm tính slot đọc lướt. `crm/report/` và `crm/doctype/utils.py` không đọc.
- Thứ tự `after_insert` trước `on_update` dựa trên vòng đời Frappe, không đọc lại trong `frappe/model/document.py`.
