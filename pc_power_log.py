"""
PC電源ON/OFF ログ抽出スクリプト (v4 - PCInfo版)
=================================================
Panasonic Let's Note の PCInfo ログから Power ON/OFF 時刻を抽出し、
日付ごとに「最初の起動（≒出社）」「最後のシャットダウン（≒帰宅）」を一覧表示します。

データソース:
  C:\\Program Files (x86)\\Panasonic\\pcinfo\\Log\\pcinfo_*_YYYYMM.txt
  - Power ON (Start) 行 + 直後の日時行 → 起動時刻
  - Power OFF 行 + 直後の日時行         → シャットダウン時刻
  - 月別ファイルで長期間保持（イベントログのように上書き消去されない）

使い方:
  管理者権限は不要です。
  今月分
  > python pc_power_log.py

  過去月
  > python pc_power_log.py --year 2026 --month 2

  CSV出力
  > python pc_power_log.py --csv 2026年3月.csv

  詳細表示
  > python pc_power_log.py --detail

必要ライブラリ: なし（標準ライブラリのみ）
動作環境: Windows 10 / 11 (Panasonic Let's Note), Python 3.8+
"""

import sys
import re
import argparse
import glob
from datetime import datetime
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# PCInfo ログのディレクトリ
# ---------------------------------------------------------------------------
PCINFO_LOG_DIR = r"C:\Program Files (x86)\Panasonic\pcinfo\Log"


def parse_args():
    parser = argparse.ArgumentParser(
        description="PCInfoログからPC起動/シャットダウン時刻を抽出します"
    )
    parser.add_argument(
        "--year", type=int, default=None,
        help="対象年（省略時: 今年）"
    )
    parser.add_argument(
        "--month", type=int, default=None,
        help="対象月（省略時: 今月）"
    )
    parser.add_argument(
        "--csv", type=str, default=None,
        help="CSV出力先ファイルパス（省略時: 画面出力のみ）"
    )
    parser.add_argument(
        "--detail", action="store_true",
        help="全イベントの詳細を表示する"
    )
    parser.add_argument(
        "--logdir", type=str, default=PCINFO_LOG_DIR,
        help=f"PCInfoログのディレクトリ（デフォルト: {PCINFO_LOG_DIR}）"
    )
    return parser.parse_args()


def find_log_file(logdir: str, year: int, month: int) -> str | None:
    """
    PCInfoログファイルを探す。
    ファイル名パターン: pcinfo_*_YYYYMM.txt
    """
    ym = f"{year}{month:02d}"
    pattern = str(Path(logdir) / f"pcinfo_*_{ym}.txt")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None


def parse_pcinfo_log(filepath: str) -> list[dict]:
    """
    PCInfoログを読み込み、Power ON/OFF イベントを抽出する。

    ログ形式:
      Power ON (Start) ===== ETM:... / BAT1:... / ...
      2026/03/02 08:48:26
      ...
      Power OFF ===== ETM:...
      2026/03/02 18:27:24
    """
    events = []
    datetime_pattern = re.compile(r"^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("Power ON") or line.startswith("Power OFF"):
            event_type = "boot" if line.startswith("Power ON") else "shutdown"
            label = "起動" if event_type == "boot" else "停止"

            # 次の行から日時を取得
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                m = datetime_pattern.match(next_line)
                if m:
                    dt_str = m.group(1)
                    try:
                        dt = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")
                        events.append({
                            "datetime": dt,
                            "date": dt.strftime("%Y-%m-%d"),
                            "time": dt.strftime("%H:%M:%S"),
                            "type": event_type,
                            "label": label,
                            "weekday": ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()],
                        })
                    except ValueError:
                        pass
            i += 2
        else:
            i += 1

    return events


def build_daily_summary(events: list[dict]) -> dict[str, dict]:
    """日付ごとに集計する。"""
    daily = defaultdict(list)
    for ev in events:
        daily[ev["date"]].append(ev)

    summary = {}
    for date in sorted(daily.keys()):
        entries = sorted(daily[date], key=lambda x: x["datetime"])
        weekday = entries[0]["weekday"]

        boots = [e for e in entries if e["type"] == "boot"]
        shutdowns = [e for e in entries if e["type"] == "shutdown"]

        first_boot = boots[0]["time"] if boots else ""
        last_shutdown = shutdowns[-1]["time"] if shutdowns else ""

        detail_parts = [f"{e['label']} {e['time']}" for e in entries]

        summary[date] = {
            "weekday": weekday,
            "first_boot": first_boot,
            "last_shutdown": last_shutdown,
            "boot_count": len(boots),
            "shutdown_count": len(shutdowns),
            "detail": " / ".join(detail_parts),
        }

    return summary


def print_summary(summary: dict[str, dict], year: int, month: int, detail: bool):
    """画面にテーブル形式で表示する"""
    print(f"\n{'='*74}")
    print(f"  PC電源ログ  {year}年{month}月  (PCInfo)")
    print(f"{'='*74}")
    print(f"{'日付':<12} {'曜日':^4} {'起動（出社目安）':^18} {'停止（帰宅目安）':^18} {'回数':^6}")
    print(f"{'-'*74}")

    for date, info in summary.items():
        boot_display = info["first_boot"] if info["first_boot"] else "---"
        shutdown_display = info["last_shutdown"] if info["last_shutdown"] else "---"
        count = f"{info['boot_count']}/{info['shutdown_count']}"
        wd = info["weekday"]
        marker = " *" if wd in ("土", "日") else ""
        print(f"{date:<12} {wd:^4} {boot_display:^18} {shutdown_display:^18} {count:^6}{marker}")
        if detail:
            print(f"             └─ {info['detail']}")

    print(f"{'-'*74}")
    print(f"  * = 土日  |  回数 = 起動回数/停止回数")
    print()


def export_csv(summary: dict[str, dict], filepath: str):
    """CSV形式で出力する"""
    import csv
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["日付", "曜日", "最初の起動", "最後のシャットダウン",
                         "起動回数", "停止回数", "詳細"])
        for date, info in summary.items():
            writer.writerow([
                date,
                info["weekday"],
                info["first_boot"],
                info["last_shutdown"],
                info["boot_count"],
                info["shutdown_count"],
                info["detail"],
            ])
    print(f"CSVを保存しました: {filepath}")


def list_available_months(logdir: str):
    """利用可能なログ月を一覧表示する"""
    pattern = str(Path(logdir) / "pcinfo_*.txt")
    files = sorted(glob.glob(pattern))
    if not files:
        return []

    months = []
    ym_pattern = re.compile(r"_(\d{6})\.txt$")
    for f in files:
        m = ym_pattern.search(f)
        if m:
            ym = m.group(1)
            months.append(f"{ym[:4]}年{int(ym[4:]):02d}月")
    return months


def main():
    args = parse_args()
    now = datetime.now()
    year = args.year if args.year else now.year
    month = args.month if args.month else now.month

    logdir = args.logdir

    # ログファイルを探す
    filepath = find_log_file(logdir, year, month)
    if not filepath:
        print(f"PCInfoログが見つかりません: {year}年{month}月")
        print(f"検索先: {logdir}")
        available = list_available_months(logdir)
        if available:
            print(f"\n利用可能な月: {', '.join(available)}")
        else:
            print(f"\nPCInfoログが存在しません。Panasonic Let's Note 専用の機能です。")
        sys.exit(1)

    print(f"PCInfoログを読み込み中...")
    print(f"  ファイル: {filepath}")

    events = parse_pcinfo_log(filepath)
    if not events:
        print("Power ON/OFF イベントが見つかりませんでした。")
        sys.exit(0)

    boot_count = sum(1 for e in events if e["type"] == "boot")
    shutdown_count = sum(1 for e in events if e["type"] == "shutdown")
    print(f"  起動: {boot_count} 件 / 停止: {shutdown_count} 件")

    summary = build_daily_summary(events)
    print_summary(summary, year, month, detail=args.detail)

    if args.csv:
        export_csv(summary, args.csv)


if __name__ == "__main__":
    main()