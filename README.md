# Cangjie 库索引

本仓库收录来自仓颉中心仓 (cjpm) 的 Cangjie 编程语言库索引。

- 仓库地址：https://github.com/LibPool/Cangjie
- 大版本目录：`cangjie-v1`（仓颉语言目前为 1.x 大版本）
- 收录来源：仓颉中心仓 `pkg.cangjie-lang.cn` API
- 当前共收录 693 个 Cangjie 包

## 收录的中央仓库

| 中央仓库 | 地址 | 说明 |
| --- | --- | --- |
| 仓颉中心仓 (cjpm) | https://pkg.cangjie-lang.cn/ | 仓颉官方中心仓，按 group::name 组织包 |
| 仓颉官网 | https://cangjie-lang.cn/ | 语言文档与生态入口 |
| Cangjie-TPC | https://gitcode.com/Cangjie-TPC | 第三方包集合 |
| Cangjie-SIG | https://gitcode.com/Cangjie-SIG | 社区特别兴趣小组 |

## 索引结构

```
cangjie-v1/
├── README.md          # 按 group 列出的完整清单
├── default/           # 默认 group 的包
│   ├── flume4cj/
│   │   └── flume4cj.md
│   └── ...
├── fountain/          # 命名 group 的包
│   └── ...
```

每个 `<name>.md` 包含：一级标题、Tag、简介、官网、历史版本号、获取地址。

## 生成方式

```bash
python tools/generate_index.py
```

数据来自仓颉中心仓 API，可通过上述命令重新生成。