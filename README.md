
# PC Power Log

## 概要

PCの稼働状況（起動・シャットダウン時刻）を記録し、月単位でCSVファイルとして出力するPythonスクリプトです。Windowsのイベントログを解析し、勤務時間や稼働時間の可視化に利用できます。

## 特徴

- Windowsイベントログから電源ON/OFFの履歴を自動抽出
- 月ごとのCSVファイル出力（例: `2026年3月.csv`）
- コマンドラインから簡単に実行可能

## 使い方

1. 必要なPythonバージョン: 3.8以降
2. 依存パッケージ: 標準ライブラリのみ（追加インストール不要）
3. コマンド例:

```powershell
python pc_power_log.py --csv 2026年3月.csv
```

- `--csv` オプションで出力ファイル名を指定します。
- 実行ディレクトリにCSVファイルが生成されます。

## 出力例

| 日付       | 起動時刻   | シャットダウン時刻 | 稼働時間 |
|------------|------------|-------------------|----------|
| 2026/03/01 | 08:15:23   | 19:02:10          | 10:46:47 |
| ...        | ...        | ...               | ...      |

## ファイル構成

- `pc_power_log.py` : メインスクリプト
- `2026年3月.csv` : 出力例（実行後に生成）

## GitLabへのプッシュ手順

1. 本README.mdとスクリプトをリポジトリに追加
2. 以下のコマンドでコミット・プッシュ

```powershell
git add README.md pc_power_log.py
git commit -m "Add: READMEとメインスクリプトを追加 (Add README and main script)"
git remote add origin https://kbit-repo.net/gitlab/shimatani/pc_power_log.git
git push -u origin main
```

※ 既にリモートリポジトリが設定済みの場合は `git remote add` は不要です。

## ライセンス

本ツールはMITライセンスで公開しています。
