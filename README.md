# 🔍 SchemaPilot

<div align="center">

**Lightweight JSON Schema Intelligent Validation & Testing Engine**

**轻量级JSON Schema智能验证与测试引擎**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-orange.svg)]()

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

<a name="english"></a>
## 🇺🇸 English

### 🎉 Project Introduction

**SchemaPilot** is a lightweight, zero-dependency CLI tool designed for JSON Schema validation, API response testing, and batch data quality verification. In modern API development, ensuring data consistency and compliance is crucial. SchemaPilot helps developers quickly validate JSON data structures, automatically generate schemas, and test API endpoints.

**Key Differentiators:**
- 🚀 **Zero Dependencies**: Pure Python standard library, no external packages required
- 🎯 **Smart Schema Generation**: Automatically infer types and formats from JSON data
- 🔌 **API Testing**: Built-in HTTP client with response validation
- 📊 **Beautiful Reports**: Generate HTML/Markdown/JSON reports
- ⚡ **Lightweight**: Single file, <100KB, instant startup

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| **JSON Schema Validation** | Full draft-07 support with detailed error reporting |
| **Schema Generation** | Auto-generate schemas from JSON with format detection |
| **API Testing** | Test endpoints and validate responses against schemas |
| **Batch Validation** | Validate multiple files with comprehensive reporting |
| **Report Generation** | Export results as HTML, Markdown, or JSON |
| **Zero Dependencies** | Runs on Python 3.8+ with no external packages |

### 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/gitstq/SchemaPilot.git
cd SchemaPilot

# Validate JSON against schema
python schemapilot.py validate -d data.json -s schema.json

# Generate schema from JSON
python schemapilot.py generate -d data.json -o schema.json

# Test API endpoint
python schemapilot.py test -u https://api.example.com/users

# Batch validation with HTML report
python schemapilot.py batch -f "data/*.json" -s schema.json -o report.html --format html
```

### 📖 Usage

#### Validate Command
```bash
schemapilot validate -d <data_file> -s <schema_file> [options]

Options:
  -d, --data       JSON data file to validate (required)
  -s, --schema     JSON Schema file (required)
  -o, --output     Output file for report
  --format         Report format: json, html, markdown
```

#### Generate Command
```bash
schemapilot generate -d <data_file> [options]

Options:
  -d, --data       JSON data file (required)
  -o, --output     Output schema file
  -t, --title      Schema title
```

#### Test Command
```bash
schemapilot test -u <url> [options]

Options:
  -u, --url        API URL to test (required)
  -s, --schema     Schema file for response validation
  -m, --method     HTTP method (default: GET)
  -H, --header     HTTP headers
  -b, --body       Request body
```

### 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

<a name="简体中文"></a>
## 🇨🇳 简体中文

### 🎉 项目介绍

**SchemaPilot** 是一款轻量级、零依赖的CLI工具，专为JSON Schema验证、API响应测试和批量数据质量验证而设计。

**核心优势：**
- 🚀 **零依赖**：纯Python标准库，无需外部包
- 🎯 **智能Schema生成**：从JSON数据自动推断类型和格式
- 🔌 **API测试**：内置HTTP客户端，支持响应验证
- 📊 **精美报告**：生成HTML/Markdown/JSON格式报告
- ⚡ **轻量级**：单文件，瞬间启动

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| **JSON Schema验证** | 完整的draft-07支持，详细的错误报告 |
| **Schema生成** | 从JSON自动生成Schema，支持格式检测 |
| **API测试** | 测试端点并根据Schema验证响应 |
| **批量验证** | 验证多个文件并生成综合报告 |
| **报告生成** | 将结果导出为HTML、Markdown或JSON |
| **零依赖** | 在Python 3.8+上运行，无需外部包 |

### 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/gitstq/SchemaPilot.git
cd SchemaPilot

# 验证JSON文件
python schemapilot.py validate -d data.json -s schema.json

# 从JSON生成Schema
python schemapilot.py generate -d data.json -o schema.json

# 测试API端点
python schemapilot.py test -u https://api.example.com/users

# 批量验证并生成HTML报告
python schemapilot.py batch -f "data/*.json" -s schema.json -o report.html --format html
```

### 📖 使用指南

#### 验证命令
```bash
schemapilot validate -d <数据文件> -s <schema文件> [选项]

选项：
  -d, --data       要验证的JSON数据文件（必需）
  -s, --schema     JSON Schema文件（必需）
  -o, --output     报告输出文件
  --format         报告格式：json, html, markdown
```

#### 生成命令
```bash
schemapilot generate -d <数据文件> [选项]

选项：
  -d, --data       JSON数据文件（必需）
  -o, --output     输出Schema文件
  -t, --title      Schema标题
```

#### 测试命令
```bash
schemapilot test -u <url> [选项]

选项：
  -u, --url        要测试的API URL（必需）
  -s, --schema     用于响应验证的Schema文件
  -m, --method     HTTP方法（默认：GET）
  -H, --header     HTTP头部
  -b, --body       请求体
```

### 📄 开源协议

MIT许可证 - 详见[LICENSE](LICENSE)文件。

---

<a name="繁體中文"></a>
## 繁體中文
### 🎉 專案介紹

**SchemaPilot** 是一款輕量級、零依賴的CLI工具，專為JSON Schema驗證、API回應測試和批次資料品質驗證而設計。

**核心優勢：**
- 🚀 **零依賴**：純Python標準庫，無需外部套件
- 🎯 **智慧Schema生成**：從JSON資料自動推斷類型和格式
- 🔌 **API測試**：內建HTTP客戶端，支援回應驗證
- 📊 **精美報告**：生成HTML/Markdown/JSON格式報告
- ⚡ **輕量級**：單檔案，瞬間啟動

### ✨ 核心特性

| 特性 | 描述 |
|------|------|
| **JSON Schema驗證** | 完整的draft-07支援，詳細的錯誤報告 |
| **Schema生成** | 從JSON自動生成Schema，支援格式檢測 |
| **API測試** | 測試端點並根據Schema驗證回應 |
| **批次驗證** | 驗證多個檔案並生成綜合報告 |
| **報告生成** | 將結果匯出為HTML、Markdown或JSON |
| **零依賴** | 在Python 3.8+上執行，無需外部套件 |

### 🚀 快速開始

```bash
# 克隆倉庫
git clone https://github.com/gitstq/SchemaPilot.git
cd SchemaPilot

# 驗證JSON檔案
python schemapilot.py validate -d data.json -s schema.json

# 從JSON生成Schema
python schemapilot.py generate -d data.json -o schema.json

# 測試API端點
python schemapilot.py test -u https://api.example.com/users

# 批次驗證並生成HTML報告
python schemapilot.py batch -f "data/*.json" -s schema.json -o report.html --format html
```

### 📖 使用指南

#### 驗證命令
```bash
schemapilot validate -d <資料檔案> -s <schema檔案> [選項]

選項：
  -d, --data       要驗證的JSON資料檔案（必需）
  -s, --schema     JSON Schema檔案（必需）
  -o, --output     報告輸出檔案
  --format         報告格式：json, html, markdown
```

#### 生成命令
```bash
schemapilot generate -d <資料檔案> [選項]

選項：
  -d, --data       JSON資料檔案（必需）
  -o, --output     輸出Schema檔案
  -t, --title      Schema標題
```

#### 測試命令
```bash
schemapilot test -u <url> [選項]

選項：
  -u, --url        要測試的API URL（必需）
  -s, --schema     用於回應驗證的Schema檔案
  -m, --method     HTTP方法（預設：GET）
  -H, --header     HTTP頭部
  -b, --body       請求體
```

### 📄 開源協議

MIT許可證 - 詳見[LICENSE](LICENSE)檔案。
