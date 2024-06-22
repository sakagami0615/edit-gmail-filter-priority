import os
from datetime import datetime
from functools import partial
from tkinter import messagebox

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QMainWindow, QTableWidgetItem, QVBoxLayout, QWidget

from app.common.adjuster import FilterXmlAdjuster
from app.data.filter_data import FilterData
from app.ui.table_widget import DraggableTableWidget

XML_DIRPATH = "./xml_file"
TITLE = "Gmail filter table view"

HEADER = ["priority", "category", "condition", "label", "process"]
WIDTHS = [None, None, 500, None, None]


class Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self._filter_data = FilterData()
        self._table = None
        self._curr_xml_path = None
        self._init_ui()

    def _init_ui(self):
        """UI作成"""
        self._create_layout()
        self._create_menubar()
        self.resize(self.width(), self.height())

    def _export_filter_xml(self) -> None:
        """並び替えたテーブルデータをxmlで出力"""
        if self._table is None:
            return

        def export_xml_path(xml_path):
            base, ext = os.path.splitext(xml_path)
            return datetime.now().strftime(f"{base}(tooledit_%Y%m%d-%H%M%S){ext}")

        xml_path = export_xml_path(self._curr_xml_path)
        priority_list = [
            int(self._table.item(row, 0).text()) - 1 for row in range(self._table.rowCount())
        ]
        self._filter_data.sort_entry_list(priority_list)
        self._filter_data.export_xml(xml_path)

        # NOTE: ["]を[']に変換したり、閉じタグを追加したりする
        FilterXmlAdjuster().minor_adjustment(xml_path)

        messagebox.showinfo(
            "Export xml successfully!", f"下記パスにxmlを保存しました。\n{xml_path}"
        )

    def _create_table(self, xml_path: str) -> None:
        """テーブルのUIを作成"""
        # 今あるテーブルを削除
        if self._table:
            self._layout.removeWidget(self._table)

        if not os.path.exists(xml_path):
            messagebox.showerror(
                "Import xml failure...",
                f"下記パスにxmlがありません。\n一度[Refresh]をクリックしてメニューバーを更新してください。\n{xml_path}",
            )
            return

        # データ読み込み
        self._curr_xml_path = xml_path
        self._filter_data.import_xml(xml_path)
        table_data = self._filter_data.to_table_data()

        # テーブル作成
        self._table = DraggableTableWidget(HEADER, len(table_data), len(HEADER), WIDTHS, False, table_data)

        # テーブル更新時のアクションをセット
        self._table.cellChanged.connect(self._set_undo_redo_action_enable)
        self._table.horizontalHeader().sectionClicked.connect(self._set_undo_redo_action_enable)

        # テーブルをレイアウトに追加
        self._layout.addWidget(self._table)

        # ウィンドウサイズの調整
        self.resize(self._table.sizeHint().width(), self.height())

        # Undo/Redoボタンの設定
        self._connect_undo_redo_action()
        self._set_undo_redo_action_enable()

    def _create_layout(self) -> None:
        """レイアウト作成"""
        # テーブルをレイアウトに追加
        self._widget = QWidget()
        self._layout = QVBoxLayout(self._widget)

        # メインウィンドウの設定
        self.setCentralWidget(self._widget)
        self.setWindowTitle(TITLE)

    def _create_load_action(self) -> None:
        """ファイル読み込みのアクション作成
        xml_fileフォルダ内にあるファイルを読み込むアクションボタンを作成する。
        """
        # 今あるアクションメニューをクリア
        self._load_menu.clear()
        self._load_actions = []

        # xml_fileフォルダ内にあるファイルを読み込むアクションボタンを作成
        for xml_name in os.listdir(XML_DIRPATH):
            if os.path.splitext(xml_name)[-1] != ".xml":
                continue

            xml_path = os.path.join(XML_DIRPATH, xml_name)
            self._load_actions.append(QAction(f"Load XML: {xml_name}"))
            self._load_actions[-1].triggered.connect(partial(self._create_table, xml_path))
            self._load_menu.addAction(self._load_actions[-1])

        # フォルダ内を再度確認する[Refresh]アクションを作成
        self._refresh_action = QAction("Refresh")
        self._refresh_action.triggered.connect(self._create_load_action)
        self._load_menu.addAction(self._refresh_action)

    def _create_export_action(self) -> None:
        """ファイル読み込みのアクション作成"""
        self._export_action = QAction("Export XML")
        self._export_action.triggered.connect(self._export_filter_xml)
        self._export_menu.addAction(self._export_action)

    def _create_edit_action(self) -> None:
        """ファイルエディットのアクション作成"""
        self._undo_action = QAction("Undo")
        self._edit_menu.addAction(self._undo_action)
        self._redo_action = QAction("Redo")
        self._edit_menu.addAction(self._redo_action)
        self._set_undo_redo_action_enable()

    def _connect_undo_redo_action(self) -> None:
        """Undo/Redoの処理をアクションボタンに接続"""
        self._undo_action.triggered.connect(self._table.undo)
        self._undo_action.setShortcut("Ctrl+Z")
        self._redo_action.triggered.connect(self._table.redo)
        self._redo_action.setShortcut("Ctrl+R")

    def _set_undo_redo_action_enable(self) -> None:
        """Undo/Redoのアクションボタンの活性/非活性切り替え
        テーブルの有無、Undo/RedoのStatus数で切り替える。
        """
        if self._table is None:
            self._undo_action.setEnabled(False)
            self._redo_action.setEnabled(False)
            return

        if self._table.n_undo > 0:
            self._undo_action.setEnabled(True)
        else:
            self._undo_action.setEnabled(False)

        if self._table.n_redo > 0:
            self._redo_action.setEnabled(True)
        else:
            self._redo_action.setEnabled(False)

    def _create_menubar(self) -> None:
        """メニューバー作成"""
        self._menubar = self.menuBar()
        self._edit_menu = self._menubar.addMenu("Edit")
        self._load_menu = self._menubar.addMenu("Load")
        self._export_menu = self._menubar.addMenu("Export")
        self._create_edit_action()
        self._create_load_action()
        self._create_export_action()
