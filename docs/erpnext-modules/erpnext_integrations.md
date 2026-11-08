# Module ERPNext Integrations

Module hiện chỉ có một tích hợp thực sự là Plaid: liên kết tài khoản ngân hàng và tự nhập giao dịch thành `Bank Transaction` của `accounts`. Ngoài ra có `utils.py` với vài hàm tiện ích.

## Phạm vi

Đọc được 1 doctype trong `erpnext_integrations/doctype/`.

| Nhóm chức năng | Doctype/file chính | Sơ đồ |
|---|---|---|
| Cấu hình và kết nối Plaid | `Plaid Settings`, `plaid_connector.py` | Class |
| Liên kết ngân hàng | `plaid_settings.py`, `plaid_settings.js`, `accounts/doctype/bank/bank.js` | Sequence: Liên kết ngân hàng, Làm mới liên kết |
| Đồng bộ giao dịch | `plaid_settings.py` | Sequence: Đồng bộ giao dịch |
| Tiện ích | `utils.py` | Không vẽ, xem Giới hạn |

## Class diagram

`PlaidConnector` là class Python thường, không phải doctype. `Bank`, `Bank Account`, `Bank Transaction` thuộc `accounts`; quan hệ với chúng không phải Link từ Plaid Settings mà qua các hàm trong `plaid_settings.py`.

```mermaid
classDiagram
    class PlaidSettings {
        +bool enabled
        +bool automatic_sync
        +string plaid_client_id
        +string plaid_secret
        +string plaid_env
        +bool enable_european_access
        +get_link_token()
    }
    class PlaidConnector {
        +string access_token
        +get_access_token()
        +get_token_request()
        +get_link_token()
        +get_transactions()
    }
    class Bank {
        +string bank_name
        +string plaid_access_token
    }
    class BankAccount {
        +string bank
        +string account
        +string integration_id
        +date last_integration_date
        +bool is_company_account
    }
    class BankTransaction {
        +date date
        +string bank_account
        +float deposit
        +float withdrawal
        +string transaction_id
    }
    PlaidConnector ..> PlaidSettings : settings
    PlaidSettings ..> PlaidConnector : get_link_token
    BankAccount --> Bank : bank
    BankTransaction --> BankAccount : bank_account
```

## Sequence diagram

### Liên kết ngân hàng

Form Plaid Settings mở Plaid Link; sau khi người dùng chọn ngân hàng, server đổi public token lấy access token, tạo `Bank` và mỗi tài khoản Plaid tạo một `Account` cùng một `Bank Account`.

```mermaid
sequenceDiagram
    actor User
    participant JS as plaid_settings.js
    participant PS as plaid_settings.py
    participant PC as PlaidConnector
    participant API as Plaid API
    participant Bank as Bank
    participant Acc as Account, Bank Account
    User->>JS: Link a new bank account
    JS->>PS: frm.call(get_link_token)
    PS->>PC: PlaidSettings.get_link_token()
    PC->>API: LinkToken.create
    API-->>JS: link_token
    User->>API: đăng nhập trong Plaid Link
    API-->>JS: public token và response
    JS->>User: plaid_success: hỏi Company
    JS->>PS: add_institution(token, response)
    PS->>PC: get_access_token(token)
    PC->>API: Item.public_token.exchange
    PS->>Bank: insert hoặc save plaid_access_token
    JS->>PS: add_bank_accounts(response, bank, company)
    PS->>PS: throw nếu company không có group account Bank
    loop mỗi account trong response
        PS->>PS: add_account_type, add_account_subtype nếu thiếu
        alt get_existing_bank_account không thấy
            PS->>Acc: insert Account, insert Bank Account, savepoint plaid_bank_account
        else đã có
            PS->>Acc: cập nhật Bank Account, savepoint plaid_update_account
        end
    end
```

Nguồn: [plaid_settings.py:60](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L60), [plaid_settings.py:91](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L91)

### Đồng bộ giao dịch

Job `hourly_maintenance` hoặc nút Sync Now enqueue một job cho mỗi Bank Account đã liên kết. Mỗi giao dịch có savepoint riêng, và chỉ giao dịch không pending, chưa tồn tại mới được tạo và submit.

```mermaid
sequenceDiagram
    participant Sch as Scheduler hoặc Sync Now
    participant PS as plaid_settings.py
    participant Q as RQ queue
    participant PC as PlaidConnector
    participant API as Plaid API
    participant BT as Bank Transaction
    participant BA as Bank Account
    Sch->>PS: automatic_synchronization()
    opt enabled và automatic_sync
        PS->>PS: enqueue_synchronization()
        loop mỗi Bank Account có integration_id
            PS->>Q: enqueue sync_transactions(bank, bank_account)
        end
    end
    Q->>PS: sync_transactions
    PS->>BA: last_integration_date, mặc định lùi 12 tháng
    PS->>PC: get_transactions(start_date, end_date, account_id)
    PC->>API: Transactions.get theo offset
    API-->>PS: transactions
    loop mỗi giao dịch, thứ tự đảo
        PS->>PS: savepoint(plaid_sync_txn)
        PS->>BT: new_bank_transaction: insert, submit, add_tag
        opt exception
            PS->>PS: rollback về savepoint, log_error, bỏ qua giao dịch
        end
    end
    opt có giao dịch mới
        PS->>BA: set_value last_integration_date
    end
```

Nguồn: [plaid_settings.py:353](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L353), [plaid_settings.py:219](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L219), [plaid_settings.py:294](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L294)

### Làm mới liên kết

Khi Plaid báo `ITEM_LOGIN_REQUIRED`, `get_transactions` chỉ ghi log. Người dùng làm mới từ form Bank bằng link token ở chế độ update.

```mermaid
sequenceDiagram
    actor User
    participant JS as bank.js
    participant PS as plaid_settings.py
    participant PC as PlaidConnector
    participant API as Plaid API
    participant Acc as Bank Account
    User->>JS: Refresh Plaid Link
    JS->>PS: get_link_token_for_update(bank)
    PS->>PS: get_decrypted_password(Bank, plaid_access_token)
    PS->>PC: get_link_token(update_mode=True)
    PC->>API: LinkToken.create với access_token
    API-->>JS: link_token
    User->>API: xác thực lại trong Plaid Link
    API-->>JS: response
    JS->>PS: update_bank_account_ids(response)
    PS->>PS: get_company(bank_account_name)
    PS->>Acc: add_bank_accounts(response, bank, company)
```

Nguồn: [plaid_settings.py:378](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L378), [plaid_settings.py:407](../../apps/erpnext/erpnext/erpnext_integrations/doctype/plaid_settings/plaid_settings.py#L407)

## Giới hạn

- `utils.py` không vẽ: `validate_webhooks_request` và `get_webhook_address` không có nơi gọi trong `erpnext/`; `get_webhook_address` trỏ tới `erpnext_integrations.connectors`, thư mục này không tồn tại trong cây mã hiện tại. `get_tracking_url` chỉ render URL theo Parcel Service.
- Bên trong Plaid Link phía trình duyệt và các bước `Bank Transaction.on_submit` không đọc sâu. Phần giao diện của `plaid_settings.js`, `bank.js` chỉ đọc đến các lệnh gọi server.
- `get_plaid_configuration` được whitelist nhưng `plaid_settings.js` và `bank.js` không gọi; form lấy token bằng `frm.call("get_link_token")`.
- Chưa chắc: `PlaidConnector.get_token_request` đưa `self.settings.plaid_secret` trực tiếp vào request khi không ở chế độ update, trong khi hàm khởi tạo dùng `get_password`. Với field Password, giá trị đọc trực tiếp có thể là chuỗi che; chưa chạy thử với Plaid.
- Hàm `enqueue_synchronization` có `has_permission` nên khi scheduler chạy cũng phải qua kiểm tra quyền; chưa xác nhận session user của scheduler trong site này.
