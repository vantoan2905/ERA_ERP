# Module EDI

Module lưu các bảng mã chuẩn (Code List) và từng mã (Common Code), nạp từ file genericode XML, đồng thời ánh xạ mã với bản ghi ERPNext qua `applies_to`. Trong `erpnext/` chưa có module nghiệp vụ nào gọi các hàm tra mã; hook chỉ nạp JS cho list view và form.

## Phạm vi

Đọc được 2 doctype trong `edi/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Danh mục mã | `Code List`, `Common Code` | Class |
| Import genericode | `code_list_import.py`, `code_list_import.js`, `common_code.py` | Sequence: Tải file, Tạo Common Code |
| Tra mã | `code_list.py` (`get_codes_for`, `get_docnames_for`, `get_default_code`) | Không vẽ, xem Giới hạn |

## Class diagram

```mermaid
classDiagram
    class CodeList {
        +string title
        +string version
        +string canonical_uri
        +string publisher
        +string publisher_id
        +string url
        +validate()
        +on_trash()
        +from_genericode()
        +get_codes_for()
        +get_docnames_for()
        +get_default_code()
    }
    class CommonCode {
        +string code_list
        +string common_code
        +string title
        +string additional_data
        +string canonical_uri
        +validate()
        +validate_distinct_references()
        +from_genericode()
    }
    class DynamicLink {
        +string link_doctype
        +string link_name
    }
    CodeList --> CommonCode : default_common_code
    CommonCode --> CodeList : code_list
    CommonCode *-- DynamicLink : applies_to
```

## Sequence diagram

### Tải file genericode

Bước đầu đọc file, tạo hoặc cập nhật Code List theo `CanonicalVersionUri`, lưu file private rồi trả về danh sách cột để hộp thoại chọn cột. Không chấp nhận URL từ xa.

```mermaid
sequenceDiagram
    actor User
    participant JS as code_list_import.js
    participant CLI as code_list_import.py
    participant CL as Code List
    participant File as File
    User->>JS: erpnext.edi.import_genericode
    JS->>CLI: import_genericode()
    CLI->>CLI: has_permission(Code List, create)
    CLI->>CLI: get_uploaded_genericode_file
    alt URL không phải file cục bộ
        CLI-->>User: Importing Code Lists from remote URLs is not allowed
    else hợp lệ
        CLI->>CLI: import_genericode_content: parse_genericode_content
        alt docname đã tồn tại
            CLI->>CL: get_doc, throw nếu name khác CanonicalVersionUri
        else chưa có
            CLI->>CL: new_doc, name = CanonicalVersionUri
        end
        CLI->>CL: from_genericode(root), save()
        CLI->>File: save_file(is_private=1)
        CLI->>CLI: get_genericode_columns_and_examples(root)
        CLI-->>JS: code_list, file, columns, example_values, filterable_columns
    end
```

Nguồn: [code_list_import.py:29](../../apps/erpnext/erpnext/edi/doctype/code_list/code_list_import.py#L29), [code_list_import.py:105](../../apps/erpnext/erpnext/edi/doctype/code_list/code_list_import.py#L105)

### Tạo Common Code

Người dùng chọn cột mã, tiêu đề, mô tả và bộ lọc; server tạo hoặc cập nhật mỗi dòng thành một Common Code. Việc này chạy đồng bộ trong request, có báo tiến độ.

```mermaid
sequenceDiagram
    actor User
    participant JS as code_list_import.js
    participant CLI as code_list_import.py
    participant Mod as common_code.py
    participant File as File
    participant CC as Common Code
    User->>JS: chọn cột và filter
    JS->>CLI: process_genericode_import(code_list_name, file_name, code_column, ...)
    CLI->>CLI: has_permission(Common Code, Code List), unescape cột
    CLI->>Mod: import_genericode(code_list, file_name, column_map, filters)
    Mod->>File: get_doc, check_permission(read), get_content
    Mod->>Mod: parse_genericode_content, get_filtered_rows
    loop mỗi Row
        Mod->>Mod: get_row_code, throw nếu thiếu mã
        Mod->>CC: get_common_code: lấy bản đã có hoặc new_doc
        Mod->>CC: from_genericode(column_map, row), save()
        CC->>CC: validate_distinct_references
        Mod-->>JS: publish_progress
    end
    Mod-->>JS: total_elements
```

Nguồn: [code_list_import.py:161](../../apps/erpnext/erpnext/edi/doctype/code_list/code_list_import.py#L161), [common_code.py:89](../../apps/erpnext/erpnext/edi/doctype/common_code/common_code.py#L89)

## Giới hạn

- `get_codes_for`, `get_docnames_for`, `get_default_code`, `resolve_code_list` ([code_list.py:117](../../apps/erpnext/erpnext/edi/doctype/code_list/code_list.py#L117)) chỉ là truy vấn một bước và không có nơi gọi trong `erpnext/` ngoài test; có thể do app khác dùng, chưa xác nhận. `resolve_code_list` nhận tên document hoặc canonical URI; với URI thì lấy version mới nhất.
- `import_genericode_from_url` chỉ dành cho code backend tin cậy và không có whitelist; không vẽ vì không có nơi gọi trong `erpnext/` ngoài test.
- `CodeList.on_trash` xóa toàn bộ Common Code của list; không vẽ vì chỉ là một vòng lặp.
- Phần giao diện của `code_list_import.js` chỉ đọc đến các lệnh gọi server.
