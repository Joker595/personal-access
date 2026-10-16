# Personal Access

适合个人服务器和少量受邀用户的统一身份部署：Casdoor + SQLite、step-ca +
嵌入式数据库、OpenSSH 用户证书，以及 OIDC 应用接入示例。

用户的唯一身份是 `issuer + sub`。邮箱修改不迁移数据；密码、通行密钥和可选邮件码
属于同一个用户。通行密钥可以系统同步，撤销对象是凭据，不能据此精确识别物理设备。

- `compose.yaml`：固定 Casdoor 4.20.0 和 step-ca 0.30.2 镜像摘要；默认只绑定本机端口。
- `scripts/bootstrap.py` / `seal-bootstrap.py`：生成私有实例配置并封存初始化；禁止开放注册。
- `ssh/` 与 `scripts/ssh-*.sh`：一小时 SSH 证书、逐服务器账号授权和撤销，sudo 独立管理。
- `scripts/backup.py` / `restore.py`：停写后加密备份、7 日 + 4 周保留、离线恢复。
- `examples/`：OAuth2 Proxy 门禁；业务多用户隔离仍需应用自行实现。
- [部署与运维](docs/DEPLOYMENT.md)、[Flightwatch 迁移](docs/FLIGHTWATCH.md)、[验证记录](docs/VALIDATION.md)。

真实配置、数据库、密码、邮件授权码和 CA 私钥仅存在部署环境的 `runtime/`。
不要把运行目录、数据库备份或配置截图提交到 GitHub。

当前状态为联调阶段，生产切换和真实 iPhone/Mac/Windows 验收以验证记录为准。
