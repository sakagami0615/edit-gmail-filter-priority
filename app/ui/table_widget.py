from dataclasses import dataclass
from typing import Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem

from app.common.decorator import override
from app.data.check_point import CheckPoint


@dataclass
class State:
    texts: list[list[str]]
    #set_sorting_enabled: bool
    sort_indicator_section: int
    sort_indicator_order: int


class DraggableTableWidget(QTableWidget):
    """ドラッグアンドドロップで行を入れ替え可能なTableWidget"""
    def __init__(
        self, header: list[str], n_rows: int, n_columns: int, row_widths: list[Union[int, None]], edit_enable: bool = True, init_texts: list[list[str]] = []
    ):
        super().__init__(n_rows, n_columns)
        self.setHorizontalHeaderLabels(header)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self._header = header
        self._n_rows = n_rows
        self._n_columns = n_columns
        self._row_widths = row_widths
        self._edit_enable = edit_enable

        # Undo/Redo用のデータ保存処理
        self._check_point = CheckPoint()

        # セルソート時のアクション追加
        self.horizontalHeader().sectionPressed.connect(self._sort_action)

        # データの挿入
        self._set_table_texts(init_texts)

    @property
    def header(self):
        return self._header

    @property
    def n_rows(self):
        return self._n_rows

    @property
    def n_columns(self):
        return self._n_columns

    @property
    def row_widths(self):
        return self._row_widths

    @property
    def n_undo(self):
        return self._check_point.n_undo

    @property
    def n_redo(self):
        return self._check_point.n_redo

    @override
    def dropEvent(self, event: QDropEvent) -> None:
        """ドラッグアンドドロップで行を入れ替えるイベント関数"""
        if event.source() == self:
            target_row = self.indexAt(event.pos()).row()
            selected_rows = self.selectionModel().selectedRows()
            if not selected_rows:
                return
            source_row = selected_rows[0].row()
            self.swap(source_row, target_row)

    def _set_table_texts(self, table_texts: list[list[str]], is_sorting: bool = False):
        """テーブルデータをセットする"""
        for row_idx, row_data in enumerate(table_texts):
            for col_idx, item in enumerate(row_data):
                table_item = QTableWidgetItem(item)
                table_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if not self._edit_enable:
                    table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)  # セルを編集不可に設定
                self.setItem(row_idx, col_idx, table_item)

        # テーブルの設定(サイズとか)
        self.adjust_columns()
        self.adjust_rows()
        self.adjust_setting(is_sorting)

    def _get_state(self) -> State:
        """現在のテーブル情報(データ、ソート情報)を取得"""
        texts = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            texts.append(row_data)
        return State(texts, self.horizontalHeader().sortIndicatorSection(), self.horizontalHeader().sortIndicatorOrder())

    def _set_state(self, state: State) -> None:
        """テーブル情報(データ、ソート情報)をセットする"""
        self.setRowCount(0)
        self.setRowCount(len(state.texts))
        self.setSortingEnabled(False)

        # テーブル値をセット
        is_sorting = True if state.sort_indicator_section > 0 else False
        self._set_table_texts(state.texts, is_sorting)

        # ソート情報をセット
        self.horizontalHeader().setSortIndicator(state.sort_indicator_section, state.sort_indicator_order)

    def _sort_action(self) -> None:
        """列名クリック時のソートアクション関数"""
        self.save()
        self.setSortingEnabled(True)

    def save(self) -> None:
        """現在のテーブル情報(データ、ソート情報)を保存する"""
        curr_state = self._get_state()
        self._check_point.resist_state(curr_state)

    def undo(self) -> None:
        """テーブル情報(データ、ソート情報)をUndoする"""
        curr_state = self._get_state()
        next_state = self._check_point.undo_state(curr_state)
        self._set_state(next_state)

    def redo(self) -> None:
        """テーブル情報(データ、ソート情報)をRedoする"""
        curr_state = self._get_state()
        next_state = self._check_point.redo_state(curr_state)
        self._set_state(next_state)

    def swap(self, source_row: int, target_row: int) -> None:
        """指定した行のデータを入れ替える"""
        if source_row == target_row:
            return

        # バックアップ
        self.save()

        # 保存元の行のデータ
        source_data = [self.takeItem(source_row, col) for col in range(self.columnCount())]
        target_data = [self.takeItem(target_row, col) for col in range(self.columnCount())]

        # 行のデータを入れ替える
        for col in range(self.columnCount()):
            self.setItem(target_row, col, source_data[col])
            self.setItem(source_row, col, target_data[col])

        # テーブル関連の更新
        self.adjust_columns()
        self.adjust_rows()
        self.adjust_setting()

    def adjust_columns(self) -> None:
        """テーブルの列幅を調整する"""
        # カラムの幅を自動調整
        self.resizeColumnsToContents()
        # 特定のカラム幅を固定
        for idx, row_width in enumerate(self._row_widths):
            if row_width is not None:
                self.setColumnWidth(idx, row_width)

    def adjust_rows(self) -> None:
        """テーブルの行幅を調整する"""
        # 行の高さを自動調整
        self.resizeRowsToContents()

    def adjust_setting(self, is_sorting: bool = False) -> None:
        """テーブル情報を調整する"""
        # サイズのポリシー設定
        self.setSizeAdjustPolicy(QAbstractItemView.AdjustToContents)
        # ソート設定
        self.setSortingEnabled(is_sorting)
