# Cangjie central repository crawler
import json, os, sys, time, urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

REMOTE = "https://pkg.cangjie-lang.cn"
VERSION = "cangjie-v1"
PAGE_SIZE = 100
WORKERS = 20
RETRIES = 3
SLEEP = 0.03

def http_get(url, retries=RETRIES):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (LibPool indexer)"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            last = e
            time.sleep(0.5 * (attempt + 1))
    raise last


def fetch_page(page_num):
    url = f"{REMOTE}/v1/artifact/searchPackages?pageNum={page_num}&pageSize={PAGE_SIZE}"
    data = http_get(url)
    if data.get("code") != 200:
        raise RuntimeError(f"Package API error on page {page_num}: {data.get('msg')}")
    results = data["data"]["results"]
    total = data["data"]["totalRecords"]
    return results, total


def fetch_packages():
    """Enumerate the package registry and fail if pagination is incomplete."""
    pkgs = []
    expected_total = None
    page_num = 1
    while True:
        results, total = fetch_page(page_num)
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError(f"Package count changed while fetching: {expected_total} -> {total}")
        pkgs.extend(results)
        print(f"  page {page_num}: {len(pkgs)}/{expected_total}")
        if len(pkgs) >= expected_total or not results:
            break
        page_num += 1
        time.sleep(SLEEP)

    unique = {}
    for pkg in pkgs:
        key = (pkg.get("group", "default"), pkg["name"])
        unique[key] = pkg
    if len(pkgs) != expected_total or len(unique) != expected_total:
        raise RuntimeError(
            f"Incomplete package listing: expected {expected_total}, "
            f"received {len(pkgs)} records / {len(unique)} unique packages"
        )
    print(f"Total unique packages: {len(unique)}")
    return list(unique.values())


def fetch_versions(group, name):
    url = f"{REMOTE}/v1/artifact/package/versions?name={urllib.parse.quote(name)}&group={urllib.parse.quote(group)}"
    data = http_get(url)
    if data.get("code") == 200:
        return data["data"]["versions"]
    return []


def make_md(pkg, versions):
    name = pkg["name"]
    group = pkg.get("group", "default")
    display = f"{group}::{name}" if group != "default" else name
    desc = (pkg.get("description") or "").strip()
    license_ = (pkg.get("license") or "").strip()
    homepage = (pkg.get("homepage") or "").strip()
    docs = (pkg.get("documentation") or "").strip()
    repo = (pkg.get("repository") or "").strip()
    latest = (pkg.get("latestVersion") or "").strip()
    dl = pkg.get("downloadCount", 0)
    publisher = ((pkg.get("publisher") or {}).get("nickname") or "").strip()
    tags = []
    low = (desc + " " + name).lower()
    if any(k in low for k in ("web", "http", "server", "api")): tags.append("web")
    if "test" in low: tags.append("testing")
    if any(k in low for k in ("ui", "gui", "interface")): tags.append("ui")
    if any(k in low for k in ("database", "sql", "db")): tags.append("database")
    if any(k in low for k in ("json", "yaml", "toml", "xml", "serialize")): tags.append("serialization")
    if "log" in low: tags.append("logging")
    if any(k in low for k in ("crypto", "encrypt", "hash")): tags.append("crypto")
    if any(k in low for k in ("net", "socket", "tcp", "udp")): tags.append("networking")
    if any(k in low for k in ("math", "algorithm", "sort")): tags.append("algorithm")
    if not tags: tags.append("library")
    tag_str = ", ".join(tags)

    lines = []
    lines.append(f"# {display}")
    lines.append("")
    lines.append(f"**Tag**: {tag_str}")
    lines.append("")
    lines.append("## 简介")
    lines.append("")
    lines.append(desc if desc else f"Cangjie 中心仓中的 {display} 包。")
    lines.append("")
    lines.append("## 官网")
    lines.append("")
    if homepage: lines.append(f"- 主页: {homepage}")
    if docs: lines.append(f"- 文档: {docs}")
    if repo: lines.append(f"- 源码仓库: {repo}")
    if not (homepage or docs or repo):
        lines.append(f"- 中心仓页面: https://pkg.cangjie-lang.cn/package/{display}")
    lines.append("")
    lines.append("## 历史版本号")
    lines.append("")
    if versions:
        for v in versions:
            vnum = v.get("version", "")
            lines.append(f"- {vnum}")
    elif latest:
        lines.append(f"- {latest}")
    else:
        lines.append("(无版本信息)")
    lines.append("")
    lines.append("## 获取地址")
    lines.append("")
    lines.append(f"- 中心仓页面: https://pkg.cangjie-lang.cn/package/{display}")
    lines.append(f"- cjpm 安装: `cjpm install {display}`")
    lines.append(f"- 中央仓库: https://pkg.cangjie-lang.cn/")
    lines.append(f"- 下载量: {dl}")
    if publisher:
        lines.append(f"- 发布者: {publisher}")
    if license_:
        lines.append(f"- 许可证: {license_}")
    lines.append("")
    return "\n".join(lines)


def process_pkg(pkg):
    name = pkg["name"]
    group = pkg.get("group", "default")
    versions = fetch_versions(group, name)
    md = make_md(pkg, versions)
    path = Path(".") / VERSION / group / name / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(md, encoding="utf-8")
    return name, group


def write_readme(pkgs):
    groups = {}
    for p in pkgs:
        g = p.get("group", "default")
        groups.setdefault(g, []).append(p)
    lines = []
    lines.append("# Cangjie 库索引")
    lines.append("")
    lines.append("本目录收录来自仓颉中心仓 (cjpm) 的 Cangjie 库索引，按包组织：")
    lines.append("")
    lines.append(f"- 大版本目录：`{VERSION}`")
    lines.append("- 包路径：`<group>/<name>/<name>.md`")
    lines.append("- 收录来源：`pkg.cangjie-lang.cn` 中心仓 API")
    lines.append(f"- 当前共收录 {len(pkgs)} 个 Cangjie 包。")
    lines.append("")
    lines.append("## 数据源")
    lines.append("")
    lines.append("- 中心仓：https://pkg.cangjie-lang.cn/")
    lines.append("- 文档：https://cangjie-lang.cn/docs")
    lines.append("- cjpm 包管理器：仓颉官方")
    lines.append("")
    lines.append("## 收录清单")
    lines.append("")
    for g in sorted(groups.keys()):
        pkgs_g = sorted(groups[g], key=lambda x: x["name"])
        lines.append(f"### {g} ({len(pkgs_g)} 个)")
        lines.append("")
        for p in pkgs_g:
            display = f"{g}::{p['name']}" if g != "default" else p["name"]
            latest = p.get("latestVersion", "")
            desc = (p.get("description") or "")[:80]
            lines.append(f"- `{display}` {latest}  —  {desc}")
        lines.append("")
    Path(VERSION).mkdir(parents=True, exist_ok=True)
    readme = Path(VERSION) / "README.md"
    readme.write_text("\n".join(lines), encoding="utf-8")
    return readme


def main():
    print("Fetching package list by page...")
    pkgs = fetch_packages()

    print(f"Fetching versions + writing {len(pkgs)} md files with {WORKERS} workers...")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(process_pkg, p): p for p in pkgs}
        for f in as_completed(futures):
            try:
                name, group = f.result()
            except Exception as e:
                p = futures[f]
                print(f"  FAIL {p.get('group')}::{p.get('name')}: {e}", file=sys.stderr)
            done += 1
            if done % 100 == 0 or done == len(pkgs):
                print(f"  {done}/{len(pkgs)} done")

    print("Writing README...")
    readme = write_readme(pkgs)
    print(f"Wrote {readme}")
    print("Done.")


if __name__ == "__main__":
    main()
