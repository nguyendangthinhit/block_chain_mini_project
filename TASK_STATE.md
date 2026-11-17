# TASK STATE – Mini project "Lost and Found Registry" (DS 441 A)

Trạng thái riêng của `mini_project/`, độc lập với dự án NFT bên ngoài (không ghi vào `.claude/mykit/instruction/TASK_STATE.md`).

Đề bài: `24_29210258195_Nguyen_Dang_Thinh.pdf`. User chọn: contract deploy qua Remix (hoặc `deploy_contract.py`),
backend Python web3.py (Flask) + UI HTML/JS, tự đủ trong `mini_project/`, xong thì push git.

## Tiến độ (cập nhật 2026-11-17)
- [x] Contract `contracts/LostAndFoundRegistry.sol`: đã kiểm tra 11 kịch bản bằng solcjs (EVM paris) + Ganache in-process, tất cả PASS
- [x] Backend `app.py`, `blockchain_client.py`, `registry_service.py`, `deploy_contract.py`, `demo_workflow.py` (mới kiểm tra cú pháp)
- [x] UI `templates/index.html`, `static/app.js`, `static/style.css`
- [x] pytest `tests/` (contract + API), README, requirements.txt, .gitignore
- [x] Đã xoá `web3.py` (file mẫu trùng tên thư viện, nội dung đã chuyển vào `blockchain_client.py`)
- [ ] Chạy pytest / app / demo bằng web3.py trên Ganache (BỊ CHẶN, xem dưới)
- [ ] Ảnh chụp màn hình + điền kết quả test vào README
- [x] Code review tĩnh: không có lỗi chặn; đã sửa thông báo tx revert, lỗi 500/400/405, account cũ trong UI, thứ tự event, thêm test giới hạn độ dài
- [x] Đã bỏ Docker (2026-11-17): user xác nhận không cần, chỉ chạy bằng Python + Ganache có sẵn. README viết lại chi tiết (setup, demo, test, xử lý lỗi)
- [x] Repo riêng: `git init` trong `mini_project/`, push lên https://github.com/nguyendangthinhit/block_chain_mini_project (`main`)
- [ ] Trên máy khác: `pip install -r requirements.txt`, `python deploy_contract.py`, `python app.py`, `python -m pytest -v`, chụp màn hình, điền kết quả test vào README
- [ ] Chờ user chạy lệnh cài `requirements.txt` + kiểm tra `from web3 import Web3` sau khi gỡ chặn

## Blocker
Windows Smart App Control chặn DLL native của web3.py (`ckzg`, `cytoolz`, `regex`, `bitarray`) và interpreter
Python 3.12/3.13 của uv. Docker Desktop không khởi động (WSL hỏng: `Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG`). User test trên máy khác. `.venv` (Python 3.11) có web3 6.20.3 nhưng
không import được. Cần chạy trên máy/môi trường không bị chặn (tắt Smart App Control, cài WSL, hoặc máy khác).
