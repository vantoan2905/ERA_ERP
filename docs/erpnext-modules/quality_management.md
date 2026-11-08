# Module Quality Management

Lưu mục tiêu chất lượng, quy trình dạng cây, đánh giá định kỳ, hành động khắc phục, biên bản họp và phản hồi. Phần lớn là tài liệu nội bộ, không phải chứng từ submit được và không ghi sổ. Module chỉ nối với phần còn lại qua Link tới `User`, `UOM`, `Customer` và các job trong `hooks.py`.

## Phạm vi

Đọc được 16 doctype trong `quality_management/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
| --- | --- | --- |
| Mục tiêu và đánh giá | `Quality Goal`, `Quality Goal Objective`, `Quality Review`, `Quality Review Objective` | Class diagram. Sequence: Tạo Quality Review định kỳ |
| Quy trình | `Quality Procedure`, `Quality Procedure Process`, `Non Conformance` | Class diagram. Sequence: Đồng bộ cây Quality Procedure |
| Hành động | `Quality Action`, `Quality Action Resolution` | Class diagram |
| Họp | `Quality Meeting`, `Quality Meeting Agenda`, `Quality Meeting Minutes` | Class diagram |
| Phản hồi | `Quality Feedback`, `Quality Feedback Parameter`, `Quality Feedback Template`, `Quality Feedback Template Parameter` | Class diagram. Sequence: Tạo Quality Feedback từ template |

## Class diagram

```mermaid
classDiagram
    class NestedSet
    class QualityGoal {
        +string goal
        +string frequency
        +string date
        +string weekday
        +string procedure
    }
    class QualityGoalObjective {
        +string objective
        +string target
        +string uom
    }
    class QualityProcedure {
        +string quality_procedure_name
        +string parent_quality_procedure
        +bool is_group
        +string process_owner
        +check_for_incorrect_child()
        +set_parent()
        +add_child_to_parent()
        +remove_child_from_old_parent()
    }
    class QualityProcedureProcess {
        +string process_description
        +string procedure
    }
    class QualityReview {
        +string goal
        +string procedure
        +date date
        +string status
        +set_objectives()
        +validate_objectives()
        +set_status()
    }
    class QualityReviewObjective {
        +string objective
        +string target
        +string status
    }
    class QualityAction {
        +string corrective_preventive
        +string goal
        +string procedure
        +string review
        +string feedback
        +string status
    }
    class QualityActionResolution {
        +string problem
        +string status
        +string responsible
        +date completion_by
    }
    class QualityMeeting {
        +string status
    }
    class QualityMeetingAgenda {
        +string agenda
    }
    class QualityMeetingMinutes {
        +string minute
        +string document_type
        +string document_name
    }
    class QualityFeedback {
        +string template
        +string document_type
        +string document_name
        +set_parameters()
        +validate_parameters()
    }
    class QualityFeedbackParameter {
        +string parameter
        +string rating
        +string feedback
    }
    class QualityFeedbackTemplate {
        +string template
    }
    class QualityFeedbackTemplateParameter {
        +string parameter
    }
    class NonConformance {
        +string subject
        +string procedure
        +string status
    }

    NestedSet <|-- QualityProcedure
    QualityGoal *-- QualityGoalObjective : objectives
    QualityProcedure *-- QualityProcedureProcess : processes
    QualityReview *-- QualityReviewObjective : reviews
    QualityAction *-- QualityActionResolution : resolutions
    QualityMeeting *-- QualityMeetingAgenda : agenda
    QualityMeeting *-- QualityMeetingMinutes : minutes
    QualityFeedback *-- QualityFeedbackParameter : parameters
    QualityFeedbackTemplate *-- QualityFeedbackTemplateParameter : parameters
    QualityGoal --> QualityProcedure : procedure
    QualityProcedure --> QualityProcedure : parent_quality_procedure
    QualityProcedureProcess --> QualityProcedure : procedure
    QualityReview --> QualityGoal : goal
    QualityReview --> QualityProcedure : procedure
    QualityAction --> QualityGoal : goal
    QualityAction --> QualityProcedure : procedure
    QualityAction --> QualityReview : review
    QualityAction --> QualityFeedback : feedback
    QualityFeedback --> QualityFeedbackTemplate : template
    NonConformance --> QualityProcedure : procedure
```

## Sequence diagram

### Tạo Quality Review định kỳ

Job `daily_maintenance` duyệt từng `Quality Goal` theo `frequency` và tạo review. Trạng thái review được tính từ các dòng objective khi `validate`.

```mermaid
sequenceDiagram
    participant Sched as Scheduler
    participant Job as quality_review.py
    participant Goal as Quality Goal
    participant QR as Quality Review
    Sched->>Job: review()
    Job->>Goal: get_list(frequency, date, weekday)
    loop mỗi Quality Goal
        alt Daily, hoặc Weekly đúng weekday
            Job->>Job: create_review(goal)
        else Monthly và is_review_date(goal_date, today)
            Job->>Job: create_review(goal)
        else Quarterly, is_review_date(goal_date, today) và get_quarter(month)
            Job->>Job: create_review(goal)
        end
        opt chưa có review cùng goal và date
            Job->>QR: insert()
            QR->>QR: validate()
            QR->>Goal: set_objectives()
            QR->>QR: set_status()
        end
    end
```

Nguồn: [quality_review.py:75](../../apps/erpnext/erpnext/quality_management/doctype/quality_review/quality_review.py#L75), [quality_review.py:98](../../apps/erpnext/erpnext/quality_management/doctype/quality_review/quality_review.py#L98), [quality_review.py:32](../../apps/erpnext/erpnext/quality_management/doctype/quality_review/quality_review.py#L32)

### Đồng bộ cây Quality Procedure

`parent_quality_procedure` và bảng con `processes` là hai cách biểu diễn cùng một cây, nên mỗi lần lưu phải đồng bộ hai chiều.

```mermaid
sequenceDiagram
    actor User
    participant QP as Quality Procedure
    participant NS as NestedSet
    participant Child as Procedure con
    participant Parent as Procedure cha
    User->>QP: save()
    QP->>QP: before_save() gọi check_for_incorrect_child()
    QP->>NS: on_update()
    QP->>QP: set_parent()
    opt dòng process có con chưa có cha
        QP->>Child: set_parent_of_child(procedure, parent) rồi save()
    end
    QP->>QP: remove_parent_from_old_child()
    opt con đã bị bỏ khỏi processes
        QP->>Child: set_parent_of_child(procedure, None) rồi save()
    end
    QP->>QP: add_child_to_parent()
    opt có cha mới chưa chứa procedure này
        QP->>Parent: append(processes) rồi save()
    end
    QP->>QP: remove_child_from_old_parent()
    opt đã đổi cha
        QP->>Parent: remove(row) rồi save()
    end
```

Nguồn: [quality_procedure.py:39](../../apps/erpnext/erpnext/quality_management/doctype/quality_procedure/quality_procedure.py#L39), [quality_procedure.py:52](../../apps/erpnext/erpnext/quality_management/doctype/quality_procedure/quality_procedure.py#L52)

### Tạo Quality Feedback từ template

Thông số phản hồi được chép từ template, và mọi thông số người dùng sửa phải có trong template. Thiếu `document_name` thì mặc định là người dùng hiện tại.

```mermaid
sequenceDiagram
    actor User
    participant Form as Form Quality Feedback
    participant QF as Quality Feedback
    participant Tpl as Quality Feedback Template
    User->>Form: chọn template
    Form->>QF: set_parameters()
    QF->>Tpl: get_doc(parameters)
    User->>QF: save()
    QF->>QF: validate()
    alt chưa có parameters
        QF->>QF: set_parameters()
        QF->>Tpl: get_doc(parameters)
    else đã có parameters
        QF->>QF: validate_parameters()
        QF->>QF: get_parameters_to_validate()
    end
```

Nguồn: [quality_feedback.py:30](../../apps/erpnext/erpnext/quality_management/doctype/quality_feedback/quality_feedback.py#L30), [quality_feedback.py:38](../../apps/erpnext/erpnext/quality_management/doctype/quality_feedback/quality_feedback.py#L38)

## Giới hạn

- `Quality Goal` có `validate` rỗng. `Quality Meeting` và `Non Conformance` không có logic Python. `Quality Action` chỉ đặt `status` trong `validate` từ các dòng `resolutions`. Vì vậy các doctype này không có sequence.
- Không có mã tự sinh `Quality Action` từ `Quality Review` hay `Quality Feedback`: các field `review`, `feedback` chỉ là Link điền tay trên những gì đã đọc được trong `.py` và `.js` của `quality_action`.
- `get_children` và `add_node` của `Quality Procedure` phục vụ tree view, không vẽ. Báo cáo `report/review`, thư mục `sidebar`, `workspace`, `onboarding_step` chưa đọc nội dung.
- Bước `chọn template` là mô tả thao tác form, không phải tên hàm. Trigger đọc từ `quality_feedback.js`.
